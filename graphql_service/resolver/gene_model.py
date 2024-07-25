"""
.. See the NOTICE file distributed with this work for additional information
   regarding copyright ownership.
   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at
       http://www.apache.org/licenses/LICENSE-2.0
   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
"""
import configparser
import logging
from typing import Dict, Optional, List, Any, Mapping

from ariadne import QueryType, ObjectType
from ensembl.production.metadata.api.models import Genome
from graphql import GraphQLResolveInfo, GraphQLError
from pymongo.database import Database, Collection

from common import utils
from graphql_service.resolver.data_loaders import BatchLoaders

from graphql_service.resolver.exceptions import (
    GeneNotFoundError,
    TranscriptNotFoundError,
    ProductNotFoundError,
    FieldNotFoundError,
    RegionNotFoundError,
    AssemblyNotFoundError,
    SliceLimitExceededError,
    RegionsFromAssemblyNotFound,
    OrganismFromAssemblyNotFound,
    AssembliesFromOrganismNotFound,
    SpeciesFromOrganismNotFound,
    OrganismsFromSpeciesNotFound,
    RegionFromSliceNotFoundError,
    InputFieldArgumentNumberError,
    GenomeNotFoundError,
    MissingArgumentException,
    DatabaseNotFoundError,
    CollectionNotFoundError,
)
from grpc_service.grpc_model import GRPC_MODEL

logger = logging.getLogger(__name__)

# Define Query types for GraphQL
# Don't forget to import these into ariadne_app.py if you add a new type

QUERY_TYPE = QueryType()
GENE_TYPE = ObjectType("Gene")
TRANSCRIPT_TYPE = ObjectType("Transcript")
PGC_TYPE = ObjectType("ProductGeneratingContext")
PRODUCT_TYPE = ObjectType("Product")
GENE_METADATA_TYPE = ObjectType("GeneMetadata")
SLICE_TYPE = ObjectType("Slice")
REGION_TYPE = ObjectType("Region")
ASSEMBLY_TYPE = ObjectType("Assembly")
ORGANISM_TYPE = ObjectType("Organism")
SPECIES_TYPE = ObjectType("Species")
TRANSCRIPT_PAGE_TYPE = ObjectType("TranscriptsPage")
GENOME_TYPE = ObjectType("Genome")


@QUERY_TYPE.field("gene")
def resolve_gene(
    _,
    info: GraphQLResolveInfo,
    byId: Optional[Dict[str, str]] = None,  # pylint: disable=invalid-name
    by_id: Optional[Dict[str, str]] = None,
) -> Dict:
    "Load Gene via stable_id"

    if by_id is None:
        by_id = byId

    if not by_id:
        raise MissingArgumentException(
            "You must provide 'by_id' or 'byId' (deprecated) argument."
        )

    # this is needed for mypy to pass
    assert by_id

    query = {
        "type": "Gene",
        "$or": [
            {"stable_id": by_id["stable_id"]},
            {"unversioned_stable_id": by_id["stable_id"]},
        ],
        "genome_id": by_id["genome_id"],
    }

    set_db_conn_for_uuid(info, by_id["genome_id"])
    connection_db = get_db_conn(info)
    gene_collection = connection_db["gene"]

    logger.info("[resolve_gene] Getting Gene from DB: '%s'", connection_db.name)
    try:
        result = gene_collection.find_one(query)
    except Exception as db_exp:
        logging.error("Exception: %s", db_exp)
        raise (DatabaseNotFoundError(db_name=connection_db.name)) from db_exp

    if not result:
        raise GeneNotFoundError(by_id=by_id)

    return result


@QUERY_TYPE.field("genes")
def resolve_genes(_, info: GraphQLResolveInfo, by_symbol: Dict[str, str]) -> List:
    """
    Load Genes via potentially ambiguous symbol
    Or
    If no Symbol is specified, get all related genes (this feature might be removed later)
    """

    query = {
        "genome_id": by_symbol["genome_id"],
        "type": "Gene",
        "symbol": by_symbol.get("symbol"),  # this makes symbol optional
    }

    set_db_conn_for_uuid(info, by_symbol["genome_id"])
    connection_db = get_db_conn(info)
    gene_collection = connection_db["gene"]
    logger.info("[resolve_genes] Getting Gene from DB: '%s'", connection_db.name)

    try:
        result = gene_collection.find(query)
    except Exception as db_exp:
        logging.error("Exception: %s", db_exp)
        raise (DatabaseNotFoundError(db_name=connection_db.name)) from db_exp

    # unpack cursor into a list. We're guaranteed relatively small results
    result = list(result)
    if len(result) == 0:
        raise GeneNotFoundError(by_symbol=by_symbol)
    return result


@GENE_TYPE.field("external_references")
@TRANSCRIPT_TYPE.field("external_references")
@PRODUCT_TYPE.field("external_references")
def insert_crossref_urls(feature: Dict, info: GraphQLResolveInfo) -> List[Dict]:
    """
    A gene/transcript with cross-references in the data model is given as
    argument. Using the crossrefs package we can infer URLs to those resources
    and inject them into the response
    """
    resolver = info.context["XrefResolver"]
    xrefs = feature["external_references"]
    annotated_xrefs = map(
        resolver.annotate_crossref, xrefs
    )  # might contain None values due to caught exceptions
    xrefs_with_nulls_removed = filter(lambda x: x is not None, annotated_xrefs)
    return list(xrefs_with_nulls_removed)


@GENE_METADATA_TYPE.field("name")
def insert_gene_name_urls(gene_metadata: Dict, info: GraphQLResolveInfo) -> Dict:
    """
    A gene metadata of a gene is given as argument.
    Using the gene name metadata info we can infer URLs to those resources
    and inject them into the response
    """

    xref_resolver = info.context["XrefResolver"]
    name_metadata = gene_metadata["name"]

    source_id = name_metadata.get("source", {}).get("id")

    # If a gene doesn't have a source id, we cant find any information about the source and also the gene name URL
    if source_id is None:
        name_metadata["source"] = None
        name_metadata["url"] = None
        return name_metadata

    # Try to generate the gene name url
    name_metadata["url"] = xref_resolver.find_url_using_ens_xref_db_name(
        name_metadata.get("accession_id"), source_id
    )
    # Try to get gene name's source url and source description
    id_org_ns_prefix = xref_resolver.translate_xref_db_name_to_id_org_ns_prefix(
        source_id
    )
    name_metadata["source"]["url"] = xref_resolver.source_information_retriever(
        id_org_ns_prefix, "resourceHomeUrl"
    )
    # Source descrption is mostly null in the Ensembl database. So, trying to get it from id.org
    name_metadata["source"]["description"] = xref_resolver.source_information_retriever(
        id_org_ns_prefix, "description"
    )

    return name_metadata


@QUERY_TYPE.field("transcript")
def resolve_transcript(
    _,
    info: GraphQLResolveInfo,
    bySymbol: Optional[Dict[str, str]] = None,  # pylint: disable=invalid-name
    by_symbol: Optional[Dict[str, str]] = None,
    byId: Optional[Dict[str, str]] = None,  # pylint: disable=invalid-name
    by_id: Optional[Dict[str, str]] = None,
) -> Dict:
    "Load Transcripts by symbol or stable_id"

    if by_symbol is None:
        by_symbol = bySymbol
    if by_id is None:
        by_id = byId

    # in case the user provides both arguments or none
    if sum(map(bool, [by_symbol, by_id])) != 1:
        # ask them to provide at least one argument
        if not by_symbol and not by_id:
            raise MissingArgumentException(
                "You must provide either 'by_symbol' or 'by_id' argument."
            )
        # or in case they provided both, ask them to provide one only
        raise InputFieldArgumentNumberError(1)

    # this is needed for mypy to pass
    assert by_id or by_symbol

    query: Dict[str, Any] = {"type": "Transcript"}
    genome_id = None
    if by_symbol:
        query["symbol"] = by_symbol.get("symbol")  # this makes symbol optional
        query["genome_id"] = by_symbol["genome_id"]
        genome_id = by_symbol["genome_id"]
    if by_id:
        query["$or"] = [
            {"stable_id": by_id["stable_id"]},
            {"unversioned_stable_id": by_id["stable_id"]},
        ]
        query["genome_id"] = by_id["genome_id"]
        genome_id = by_id["genome_id"]

    assert genome_id

    set_db_conn_for_uuid(info, genome_id)
    connection_db = get_db_conn(info)
    transcript_collection = connection_db["transcript"]
    logger.info(
        "[resolve_transcript] Getting Transcript from DB: '%s'", connection_db.name
    )

    try:
        transcript = transcript_collection.find_one(query)
    except Exception as db_exp:
        logging.error("Exception: %s", db_exp)
        raise (DatabaseNotFoundError(db_name=connection_db.name)) from db_exp

    if not transcript:
        raise TranscriptNotFoundError(by_symbol=by_symbol, by_id=by_id)
    return transcript


@QUERY_TYPE.field("version")
def resolve_api(
    _: None,
    info: GraphQLResolveInfo,  # the second argument must be named `info` to avoid a NameError
) -> Dict[str, Dict[str, str]]:
    """
    Resolve the API version.
    Fetches the version details from INI configuration file and returns it.
    """
    try:
        version_details = get_version_details()
        return {"api": version_details}
    except Exception as exp:
        logging.error("Error resolving API version: %s", exp)
        raise


@GENE_TYPE.field("transcripts")
async def resolve_gene_transcripts(gene: Dict, info: GraphQLResolveInfo) -> List[Dict]:
    "Use a DataLoader to get transcripts for the parent gene"

    data_loader = get_data_loader(info)

    gene_primary_key = gene["gene_primary_key"]
    # Get a dataloader from info
    loader = data_loader.transcript_loader
    # Tell DataLoader to get this request done when it feels like it
    transcripts = await loader.load(key=gene_primary_key)
    return transcripts


@GENE_TYPE.field("transcripts_page")
async def resolve_gene_transcripts_page(
    gene: Dict, _: GraphQLResolveInfo, page: int, per_page: int
):
    "This resolver passes required fields down to child resolvers"

    return {
        "gene_primary_key": gene["gene_primary_key"],
        "page": page,
        "per_page": per_page,
    }


@TRANSCRIPT_PAGE_TYPE.field("transcripts")
async def resolve_transcripts_page_transcripts(
    transcripts_page: Dict, info: GraphQLResolveInfo
) -> List[Dict]:
    "Load a page of transcripts"
    query = {
        "type": "Transcript",
        "gene_foreign_key": transcripts_page["gene_primary_key"],
    }
    page, per_page = transcripts_page["page"], transcripts_page["per_page"]

    connection_db = get_db_conn(info)
    transcript_collection = connection_db["transcript"]
    logger.info(
        "[resolve_transcripts_page_transcripts] Getting Transcript from DB: '%s'",
        connection_db.name,
    )

    results = (
        transcript_collection.find(query)
        .sort([("stable_id", 1)])
        .skip((page - 1) * per_page)
        .limit(per_page)
    )
    return list(results)


@TRANSCRIPT_PAGE_TYPE.field("page_metadata")
async def resolve_transcripts_page_metadata(
    transcripts_page: Dict, info: GraphQLResolveInfo
) -> Dict:
    query = {
        "type": "Transcript",
        "gene_foreign_key": transcripts_page["gene_primary_key"],
    }

    connection_db = get_db_conn(info)
    transcript_collection = connection_db["transcript"]
    logger.info(
        "[resolve_transcripts_page_metadata] Getting Transcript from DB: '%s'",
        connection_db.name,
    )

    return {
        "total_count": transcript_collection.count_documents(query),
        "page": transcripts_page["page"],
        "per_page": transcripts_page["per_page"],
    }


@TRANSCRIPT_TYPE.field("product_generating_contexts")
async def resolve_transcript_pgc(transcript: Dict, _: GraphQLResolveInfo) -> List[Dict]:
    pgcs = []
    for pgc in transcript["product_generating_contexts"]:
        pgc["genome_id"] = transcript["genome_id"]
        pgcs.append(pgc)
    return pgcs


@TRANSCRIPT_TYPE.field("gene")
async def resolve_transcript_gene(transcript: Dict, info: GraphQLResolveInfo) -> Dict:
    query = {
        "type": "Gene",  # TODO: no need to select a type if we have collection per type anyway
        "genome_id": transcript["genome_id"],
        "stable_id": transcript["gene"],
    }

    connection_db = get_db_conn(info)
    gene_collection = connection_db["gene"]
    logger.info(
        "[resolve_transcript_gene] Getting Gene from DB: '%s'", connection_db.name
    )

    gene = gene_collection.find_one(query)
    if not gene:
        raise GeneNotFoundError(
            by_id={
                "genome_id": transcript["genome_id"],
                "stable_id": transcript["gene"],
            }
        )
    return gene


@QUERY_TYPE.field("overlap_region")
def resolve_overlap(
    _,
    info: GraphQLResolveInfo,
    genomeId: Optional[str] = None,  # pylint: disable=invalid-name
    regionName: Optional[str] = None,  # pylint: disable=invalid-name
    start: Optional[int] = None,
    end: Optional[int] = None,
    by_slice: Optional[Dict[str, Any]] = None,
) -> Dict:
    """
    Query Mongo for genes and transcripts lying between start and end
    """

    if by_slice:
        genome_id = by_slice["genome_id"]
        region_name = by_slice["region_name"]
        start = by_slice["start"]
        end = by_slice["end"]
    else:
        genome_id = genomeId
        region_name = regionName

    if not by_slice and (not genome_id and not region_name and not start and not end):
        raise MissingArgumentException(
            "You must provide 'by_slice' or all four 'genomeId' (deprecated), 'regionName' (deprecated), 'start' (deprecated) and 'end' (deprecated) arguments."
        )

    # this is needed for mypy to pass
    assert genome_id and region_name and start and end

    # Thoas only contains "chromosome"-type regions
    region_id = "_".join([genome_id, region_name, "chromosome"])

    set_db_conn_for_uuid(info, genome_id)
    connection_db = get_db_conn(info)
    logger.info(
        "[resolve_overlap] Getting Gene and Transcript Overlap from DB: '%s'",
        connection_db.name,
    )

    return {
        "genes": overlap_region(
            connection_db, genome_id, region_id, start, end, "Gene"
        ),
        "transcripts": overlap_region(
            connection_db, genome_id, region_id, start, end, "Transcript"
        ),
    }


def overlap_region(
    connection: Database,
    genome_id: str,
    region_id: str,
    start: int,
    end: int,
    feature_type: str,
) -> List[Dict]:
    """
    Query backend for a feature type using slice parameters:
    region id
    start coordinate
    end coordinate
    feature type
    """
    query = {
        "type": feature_type,
        "genome_id": genome_id,
        "slice.region_id": region_id,
        # A query region does not intersect a slice if, and only if, either the start of the slice is greater than the
        # end of the query region, or the end of the slice is less than the start of the query region.  Therefore, the
        # query region does intersect a slice if, and only if, the start of the slice is less than the end of the query
        # region and the end of the slice is greater than the start of the query region.
        "slice.location.start": {"$lte": end},
        "slice.location.end": {"$gte": start},
    }
    max_results_size = 1000
    feature_type_collection = connection[feature_type.lower()]
    print(
        f"[INFO] Getting Overlap Region from DB: '{connection.name}', Collection: '{feature_type.lower()}'"
    )
    results = list(feature_type_collection.find(query).limit(max_results_size))
    if len(results) == max_results_size:
        raise SliceLimitExceededError(max_results_size)
    return results


@PGC_TYPE.field("three_prime_utr")
def resolve_three_prime_utr(pgc: Dict, _: GraphQLResolveInfo) -> Optional[Dict]:
    "Convert stored 3` UTR to GraphQL compatible form"
    return pgc["3_prime_utr"]


@PGC_TYPE.field("five_prime_utr")
def resolve_utr(pgc: Dict, _: GraphQLResolveInfo) -> Optional[Dict]:
    "Convert stored 5` UTR to GraphQL compatible form"
    return pgc["5_prime_utr"]


@QUERY_TYPE.field("product")
def resolve_product_by_id(
    _,
    info: GraphQLResolveInfo,
    genome_id: Optional[str] = None,
    stable_id: Optional[str] = None,
    by_id: Optional[Dict[str, str]] = None,
) -> Dict:
    "Fetch a product by stable_id, this is almost always a protein"

    if by_id:
        genome_id = by_id["genome_id"]
        stable_id = by_id["stable_id"]

    if not by_id and (not genome_id and not stable_id):
        raise MissingArgumentException(
            "You must provide 'by_id' or both 'genome_id' (deprecated) and 'stable_id' (deprecated) arguments."
        )

    # this is needed for mypy to pass
    assert genome_id and stable_id

    query = {
        "genome_id": genome_id,
        # TODO: search by unversioned_stable_id as well?
        "stable_id": stable_id,
        "type": {"$in": ["Protein", "MatureRNA"]},
    }

    set_db_conn_for_uuid(info, genome_id)
    connection_db = get_db_conn(info)
    protein_collection = connection_db["protein"]
    logger.info(
        "[resolve_product_by_id] Getting Protein from DB: '%s'", connection_db.name
    )
    # NB: 'MatureRNA' will be added in the future, with collection per type approach
    # with have two options (TBD)
    # 1. Keep it collection per type: collection for 'Protein' and another one for 'MatureRNA'
    #    and changing the code logic
    # 2. Put all products in one collection
    result = protein_collection.find_one(query)

    if not result:
        raise ProductNotFoundError(stable_id, genome_id)
    return result


@PRODUCT_TYPE.field("product_generating_context")
def resolve_pgc_for_product(product: Dict, info: GraphQLResolveInfo) -> Optional[Dict]:
    pipeline = [
        {
            "$match": {
                "stable_id": product.get("stable_id"),
                "genome_id": product.get("genome_id"),
            }
        },
        {
            "$lookup": {
                "from": "transcript",
                "localField": "transcript_id",
                "foreignField": "unversioned_stable_id",
                "as": "transcript",
            }
        },
        {"$unwind": {"path": "$transcript"}},
    ]

    # get db connection
    set_db_conn_for_uuid(info, product.get("genome_id"))
    connection_db = get_db_conn(info)
    protein_collection = connection_db["protein"]
    logger.info(
        "[resolve_pgc_for_product] Getting Protein from DB: '%s'", connection_db.name
    )

    results = list(protein_collection.aggregate(pipeline))

    result = results[0]

    pgcs = result.get("transcript", None).get("product_generating_contexts", None)

    if not pgcs or len(pgcs) == 0:
        return None

    # get the specific pgc for product
    pgc = [
        pgc
        for pgc in pgcs
        if pgc.get("product_foreign_key") == product.get("product_primary_key")
    ]

    if pgc[0]:
        return pgc[0]

    return None


@PGC_TYPE.field("product")
async def resolve_product_by_pgc(pgc: Dict, info: GraphQLResolveInfo) -> Optional[Dict]:
    "Fetch product that is referenced by the Product Generating Context"
    # product_id may not exist or the value can be null
    if "product_id" not in pgc or pgc["product_id"] is None:
        return None

    data_loader = get_data_loader(info)
    loader = data_loader.product_loader

    products = await loader.load(key=pgc["product_foreign_key"])
    # Data loader returns a list because most data-loads are one-many
    # ID mappings

    if not products:
        raise FieldNotFoundError(
            field_type="product_foreign_key",
            key_dict={"product_foreign_key": pgc["product_foreign_key"]},
        )
    return products[0]


@SLICE_TYPE.field("region")
async def resolve_region_from_slice(
    slc: Dict, info: GraphQLResolveInfo
) -> Optional[Dict]:
    "Fetch a region that is referenced by a slice"
    if slc["region_id"] is None:
        return None
    region_id = slc["region_id"]

    data_loader = get_data_loader(info)

    loader = data_loader.region_loader

    regions = await loader.load(key=region_id)

    if not regions:
        raise RegionFromSliceNotFoundError(region_id=region_id)
    return regions[0]


@REGION_TYPE.field("assembly")
async def resolve_assembly_from_region(
    region: Dict, info: GraphQLResolveInfo
) -> Optional[Dict]:
    "Fetch an assembly referenced by a region"
    if region["assembly_id"] is None:
        return None
    assembly_id = region["assembly_id"]

    query = {"type": "Assembly", "assembly_id": region["assembly_id"]}

    connection_db = get_db_conn(info)
    assembly_collection = connection_db["assembly"]
    logger.info(
        "[resolve_assembly_from_region] Getting Assembly from DB: '%s'",
        connection_db.name,
    )
    assembly = assembly_collection.find_one(query)

    if not assembly:
        raise AssemblyNotFoundError(assembly_id)
    return assembly


@ASSEMBLY_TYPE.field("regions")
async def resolve_regions_from_assembly(
    assembly: Dict, info: GraphQLResolveInfo
) -> List[Dict]:
    data_loader = get_data_loader(info)
    loader = data_loader.region_by_assembly_loader

    regions = await loader.load(key=assembly["assembly_id"])

    if not regions:
        raise RegionsFromAssemblyNotFound(assembly["assembly_id"])
    return regions


@ASSEMBLY_TYPE.field("organism")
async def resolve_organism_from_assembly(
    assembly: Dict, info: GraphQLResolveInfo
) -> Optional[Dict]:
    data_loader = get_data_loader(info)
    loader = data_loader.organism_loader

    organisms = await loader.load(key=assembly["organism_foreign_key"])
    if not organisms:
        raise OrganismFromAssemblyNotFound(assembly["organism_foreign_key"])
    return organisms[0]


@ORGANISM_TYPE.field("assemblies")
async def resolve_assemblies_from_organism(
    organism: Dict, info: GraphQLResolveInfo
) -> List[Dict]:
    data_loader = get_data_loader(info)
    loader = data_loader.assembly_by_organism_loader

    assemblies = await loader.load(key=organism["organism_primary_key"])
    if not assemblies:
        raise AssembliesFromOrganismNotFound(organism["organism_primary_key"])
    return assemblies


@ORGANISM_TYPE.field("species")
async def resolve_species_from_organism(
    organism: Dict, info: GraphQLResolveInfo
) -> List[Dict]:
    data_loader = get_data_loader(info)
    loader = data_loader.species_loader

    species = await loader.load(key=organism["species_foreign_key"])
    if not species:
        raise SpeciesFromOrganismNotFound(species_id=organism["species_foreign_key"])
    return species[0]


@SPECIES_TYPE.field("organisms")
async def resolve_organisms_from_species(
    species: Dict, info: GraphQLResolveInfo
) -> List[Dict]:
    data_loader = get_data_loader(info)
    loader = data_loader.organism_by_species_loader

    organisms = await loader.load(key=species["species_primary_key"])
    if not organisms:
        raise OrganismsFromSpeciesNotFound(species_id=species["species_primary_key"])
    return organisms


@QUERY_TYPE.field("region")
async def resolve_region(_, info: GraphQLResolveInfo, by_name: Dict[str, str]) -> Dict:
    query = {
        "type": "Region",
        "genome_id": by_name["genome_id"],
        "name": by_name["name"],
    }

    set_db_conn_for_uuid(info, by_name["genome_id"])
    connection_db = get_db_conn(info)
    region_collection = connection_db["region"]
    logger.info("[resolve_region] Getting Region from DB: '%s'", connection_db.name)

    result = region_collection.find_one(query)
    if not result:
        raise RegionNotFoundError(genome_id=by_name["genome_id"], name=by_name["name"])
    return result


@QUERY_TYPE.field("genomes")
def resolve_genomes(
    _, info: GraphQLResolveInfo, by_keyword: Dict[str, str] = None
) -> List:
    """
    Resolve the genomes based on provided keyword arguments.
    Under the hood, this resolver might execute and combine 3 different queries based on the requested data:
    - The default `get_genome_by_specific_keyword()` gRPC call (Metadata DB)
    - If `assembly` is requested, `fetch_assembly_data()` is triggered fetching data from Mongo DB
    - If `dataset` is requested, `fetch_dataset_data()` is triggered which triggers `get_datasets_list_by_uuid()`
        gRPC call to fetch dataset info (Metadata DB)

    Args:
        info (GraphQLResolveInfo): GraphQL resolve information containing query details.
        by_keyword (Dict[str, str]): Dictionary containing keyword arguments for fetching genomes.

    Returns:
        List: A list of genomes matching the provided keyword.

    Raises:
        MissingArgumentException: If 'by_keyword' argument is not provided.
        GraphQLError: If not exactly one field in 'by_keyword' is provided.
        GenomeNotFoundError: If no genomes are found matching the provided keyword.
    """
    if not by_keyword:
        raise MissingArgumentException("You must provide 'by_keyword' argument.")

    # Check if exactly one field is provided
    provided_count = sum(1 for value in by_keyword.values() if value)
    if provided_count != 1:
        raise GraphQLError("Exactly one of the fields must be provided")

    grpc_model = info.context["grpc_model"]

    if by_keyword:
        for key in [
            "tolid",
            "assembly_accession_id",
            "assembly_name",
            "ensembl_name",
            "common_name",
            "scientific_name",
            "scientific_parlance_name",
            "species_taxonomy_id",
        ]:
            # if one of the keys is provided
            if by_keyword.get(key):
                # Fetch genomes data from metadata using gRPC
                result = grpc_model.get_genome_by_specific_keyword(
                    **{key: by_keyword.get(key)},
                    release_version=by_keyword.get("release_version"),
                )
                genomes = list(result)

                if not genomes:
                    raise GenomeNotFoundError(by_keyword)

                # Check if the assembly and dataset fields are requested in the query
                fields_to_check = ["assembly", "dataset"]
                is_assembly_present, is_dataset_present = utils.check_requested_fields(
                    info, fields_to_check
                )

                combined_results = []
                for genome in genomes:
                    set_db_conn_for_uuid(info, genome.genome_uuid)
                    connection_db = get_db_conn(info)
                    # logging.debug("Collections in the database:", connection_db.list_collection_names())
                    assembly_collection = connection_db["assembly"]
                    # logging.debug("assembly_collection.name:", assembly_collection.name)

                    assembly_data = (
                        fetch_assembly_data(assembly_collection, genome.assembly.name)
                        if is_assembly_present
                        else None
                    )
                    dataset_data = (
                        fetch_dataset_data(grpc_model, genome.genome_uuid)
                        if is_dataset_present
                        else None
                    )

                    combined_results.append(
                        create_genome_response(genome, dataset_data, assembly_data)
                    )

                return combined_results

    return []


@QUERY_TYPE.field("genome")
def resolve_genome(_, info: GraphQLResolveInfo, by_genome_uuid: Dict[str, str]) -> Dict:
    grpc_model = info.context["grpc_model"]

    genome = grpc_model.get_genome_by_genome_uuid(
        by_genome_uuid.get("genome_uuid"), by_genome_uuid.get("release_version")
    )
    if not genome.genome_uuid:
        raise GenomeNotFoundError(by_genome_uuid)

    # Check if the assembly and dataset fields are requested in the query
    fields_to_check = ["assembly", "dataset"]
    is_assembly_present, is_dataset_present = utils.check_requested_fields(
        info, fields_to_check
    )

    set_db_conn_for_uuid(info, genome.genome_uuid)
    connection_db = get_db_conn(info)
    # logging.debug("Collections in the database:", connection_db.list_collection_names())
    assembly_collection = connection_db["assembly"]
    # logging.debug("assembly_collection.name:", assembly_collection.name)

    assembly_data = (
        fetch_assembly_data(assembly_collection, genome.assembly.name)
        if is_assembly_present
        else None
    )
    dataset_data = (
        fetch_dataset_data(grpc_model, genome.genome_uuid)
        if is_dataset_present
        else None
    )
    genome = create_genome_response(genome, dataset_data, assembly_data)

    return genome


def create_genome_response(
    genome: Genome,
    dataset_data: Optional[List] = None,
    assembly_data: Optional[Mapping[Any, Any]] = None,
) -> Dict:
    """
    Create a response dictionary for a genome with optional assembly and dataset data.

    Args:
        genome (Genome): The genome object containing genome-related information.
        assembly_data (Optional[Dict[str, Any]]): Optional dictionary containing assembly data.
        dataset_data (Optional[List]): Optional list of dataset objects containing dataset information.

    Returns:
        Dict: A dictionary containing the genome response data.
    """
    datasets_response = []
    if dataset_data:
        for dataset in dataset_data:
            datasets_response.append(
                {
                    "dataset_id": dataset.dataset_uuid,
                    "name": dataset.dataset_label,
                    "version": dataset.dataset_version,
                    "release": dataset.release_version,
                    "type": dataset.dataset_type_topic,
                    "source": dataset.dataset_source_type,
                    "dataset_type": dataset.dataset_type_name,
                    "release_date": dataset.release_date,
                    "release_type": dataset.release_type,
                }
            )

    response = {
        "genome_id": genome.genome_uuid,
        "assembly_accession": genome.assembly.accession,
        "scientific_name": genome.organism.scientific_name,
        "release_number": genome.release.release_version,
        "release_date": genome.release.release_date,
        "taxon_id": genome.taxon.taxonomy_id,
        "tol_id": genome.assembly.tol_id,
        "parlance_name": genome.organism.scientific_parlance_name,
        "genome_tag": genome.assembly.url_name if not None else genome.assembly.tol_id,
        "is_reference": genome.assembly.is_reference,
        "assembly": assembly_data,
        "dataset": datasets_response,
    }
    return response


def fetch_assembly_data(assembly_collection: Collection, assembly_id: str) -> Mapping:
    """
    Fetch assembly data from a collection using the assembly ID.

    Args:
        assembly_collection (Collection): The collection to search for the assembly data.
        assembly_id (str): The ID of the assembly to fetch.

    Returns:
        Mapping: The assembly data if found.

    Raises:
        CollectionNotFoundError: If there is an issue accessing the collection.
        AssemblyNotFoundError: If the assembly with the given ID is not found.
    """
    query = {"assembly_id": assembly_id}
    try:
        assembly = assembly_collection.find_one(query)
    except Exception as coll_exp:
        logging.error("Exception: %s", coll_exp)
        raise (
            CollectionNotFoundError(collection_name=assembly_collection.name)
        ) from coll_exp

    if not assembly:
        raise AssemblyNotFoundError(assembly_id)
    return assembly


def fetch_dataset_data(grpc_model: GRPC_MODEL, genome_uuid: str) -> List:
    """
    Fetch dataset data using a gRPC model based on the genome UUID.

    Args:
        grpc_model (GRPC_MODEL): The gRPC model to use for fetching the dataset data.
        genome_uuid (str): The UUID of the genome for which to fetch dataset data.

    Returns:
        List: A list of datasets associated with the given genome UUID.
    """
    result = grpc_model.get_datasets_list_by_uuid(genome_uuid)
    datasets = list(result.datasets)
    return datasets


def get_version_details() -> Dict[str, str]:
    """
    Fetch version details from a 'version_config.ini' file.
    Returns a dictionary with keys 'major', 'minor', and 'patch'.
    If the file or keys are not found, default values are used.
    """
    config = configparser.ConfigParser()

    try:
        if not config.read("version_config.ini"):
            raise FileNotFoundError("INI file not found.")

        version_data = config["version"]
        return {
            "major": version_data["major"],
            "minor": version_data["minor"],
            "patch": version_data["patch"],
        }
    except FileNotFoundError:
        logging.error("Version config file not found. Using default values.")
    except KeyError:
        logging.error(
            "Version section or keys not found in INI file. Using default values."
        )
    except Exception as exp:
        logging.error("Error reading INI file: %s. Using default values.", exp)

    return {"major": "0", "minor": "1", "patch": "0-beta"}


def set_db_conn_for_uuid(info, uuid):
    # IMPORTANT:
    # This function must be called from all the root level(@QUERY_TYPE) resolvers.
    #
    # Child resolvers need to know their query's GenomeUUID or the Mongo db details
    # to fetch the data from.
    # The only way to pass the GenomeUUID or the connection details to the child resolvers
    # is through Context in GraphQLResolveInfo.
    #
    # This method finds the Mongo db for the requested Genome UUID and stores it
    # in the Context so that the root resolver and all its child resolvers can use it to
    # fetch the data from the relevant Mongo db.
    #
    # A single request can have multiple queries and each of those queries could be requesting
    # information for different Genome UUID. This means a single request can have multiple
    # queries with each query needing to fetch data from different Mongo dbs.
    #
    # As Context is shared between the queries of a single request, we are using info.path
    # to differentiate different queries of a request and set Mongo connection details
    # per query. This way, in an async execution, child resolvers of the 1st query can avoid
    # connecting to Mongo dbs of the 2nd query of the same request.
    #
    # These connection details in the Context will be available only for this request
    # and will not be shared with the next request because the next request will have
    # its own copy of the new dynamic context
    # See: https://ariadnegraphql.org/docs/types-reference#dynamic-context-value

    grpc_model = info.context["grpc_model"]
    # we pass the gRPC model instance and genome_uuid to get the release version used to infer Mongo DB's name
    db_conn = info.context["mongo_db_client"].get_database_conn(grpc_model, uuid)

    conn = {"db_conn": db_conn, "data_loader": BatchLoaders(db_conn)}

    parent_key = get_path_parent_key(info)
    info.context.setdefault(parent_key, conn)


def get_db_conn(info):
    parent_key = get_path_parent_key(info)
    return info.context[parent_key]["db_conn"]


def get_data_loader(info):
    parent_key = get_path_parent_key(info)
    return info.context[parent_key]["data_loader"]


def get_path_parent_key(info):
    path_keys = info.path.as_list()
    parent_key = path_keys[0]
    return parent_key
