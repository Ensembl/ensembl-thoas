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

from typing import Dict, Optional, List, Any, Union

from ariadne import QueryType, ObjectType
from graphql import GraphQLError, GraphQLResolveInfo

# Define Query types for GraphQL
# Don't forget to import these into ariadne_app.py if you add a new type
from graphql_service.resolver.data_loaders import DataLoaderCollection

QUERY_TYPE = QueryType()
GENE_TYPE = ObjectType("Gene")
TRANSCRIPT_TYPE = ObjectType("Transcript")
PGC_TYPE = ObjectType("ProductGeneratingContext")
PRODUCT_TYPE = ObjectType("Product")
GENE_METADATA_TYPE = ObjectType("GeneMetadata")
SLICE_TYPE = ObjectType("Slice")
REGION_TYPE = ObjectType("Region")


def get_root_key(info: GraphQLResolveInfo) -> Union[str, int]:
    """This is intended to be used inside a resolver to determine its root query.  For example, suppose we had a query
    like this:

    query {
      transcript(byId: {
        genome_id: "plasmodium_falciparum_GCA_000002765_2",
        stable_id: "CAD52290"
      }) {
        ...
      }
      gene(byId: {
        genome_id: "saccharomyces_cerevisiae_GCA_000146045_2"
        stable_id: "YHR055C"
      }) {
        ...
      }
    }

    Then this function will return "transcript" if it runs inside a resolver processing the transcript query, and "gene"
    if run inside a resolver processing the gene query.

    The keys are always unique within a graphql query.  If you want to run the same type of query more than once in the
    same GraphQL request then you need to define aliases.  Here is an example:

    query {
      firstGene: gene(byId: {
        genome_id: "saccharomyces_cerevisiae_GCA_000146045_2"
        stable_id: "snR41"
      }) {
        ...
      }
      secondGene: gene(byId: {
        genome_id: "homo_sapiens_GCA_000001405_28"
        stable_id: "ENSG00000127720.8"
      }) {
        ...
      }
    }
    In this case the keys that could be returned by this function are "firstGene" and "secondGene".
    """
    current = info.path
    parent = current.prev
    while parent is not None:
        current = parent
        parent = parent.prev
    return current.key


def create_dataloader_collection(genome_id: str, info: GraphQLResolveInfo) -> None:
    """This function ensures that all resolvers have access to a dataloader specific to their root query.
    This function must be run inside every root-level resolver method.

    For example, suppose that we are processing a query like this:

    query {
      firstGene: gene(byId: {
        genome_id: "saccharomyces_cerevisiae_GCA_000146045_2"
        stable_id: "snR41"
      }) {
        ...
      }
      secondGene: gene(byId: {
        genome_id: "homo_sapiens_GCA_000001405_28"
        stable_id: "ENSG00000127720.8"
      }) {
        ...
      }
    }
    Provided we run this function inside every root-level resolver, at the end of processing the query the value
    of info.context["request"].state will be
    {
      "firstGene": DataLoaderCollection(<mongo client>, "saccharomyces_cerevisiae_GCA_000146045_2"),
      "secondGene": DataLoaderCollection(<mongo client>, "homo_sapiens_GCA_000001405_28")
    }
    This ensures that we have a separate collection of dataloaders per-request and per-genome_id.
    """

    key = get_root_key(info)
    request_state = info.context["request"].state
    if hasattr(request_state, "dataloader_collections"):
        request_state.dataloader_collections[key] = DataLoaderCollection(
            info.context["mongo_db"], genome_id
        )
    else:
        request_state.dataloader_collections = {
            key: DataLoaderCollection(info.context["mongo_db"], genome_id)
        }


def get_dataloader_collection(info: GraphQLResolveInfo) -> DataLoaderCollection:
    key = get_root_key(info)
    return info.context["request"].state.dataloader_collections[key]


@QUERY_TYPE.field("gene")
def resolve_gene(
    _,
    info: GraphQLResolveInfo,
    byId: Optional[Dict[str, str]] = None,
    by_id: Optional[Dict[str, str]] = None,
) -> Dict:
    "Load Gene via stable_id"

    if by_id is None:
        by_id = byId

    assert by_id

    create_dataloader_collection(by_id["genome_id"], info)
    query = {
        "type": "Gene",
        "$or": [
            {"stable_id": by_id["stable_id"]},
            {"unversioned_stable_id": by_id["stable_id"]},
        ],
        "genome_id": by_id["genome_id"],
    }

    collection = info.context["mongo_db"]
    result = collection.find_one(query)
    if not result:
        raise GeneNotFoundError(by_id=by_id)
    return result


@QUERY_TYPE.field("genes_by_symbol")
def resolve_genes(
    _,
    info: GraphQLResolveInfo,
    bySymbol: Optional[Dict[str, str]] = None,
    by_symbol: Optional[Dict[str, str]] = None,
) -> List:
    "Load Genes via potentially ambiguous symbol"

    if by_symbol is None:
        by_symbol = bySymbol

    assert by_symbol

    create_dataloader_collection(by_symbol["genome_id"], info)

    query = {
        "genome_id": by_symbol["genome_id"],
        "type": "Gene",
        "symbol": by_symbol["symbol"],
    }

    collection = info.context["mongo_db"]

    result = collection.find(query)
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
    A gene/transcript with cross references in the data model is given as
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

    # If a gene does'nt have a source id, we cant find any information about the source and also the gene name URL
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
    bySymbol: Optional[Dict[str, str]] = None,
    by_symbol: Optional[Dict[str, str]] = None,
    byId: Optional[Dict[str, str]] = None,
    by_id: Optional[Dict[str, str]] = None,
) -> Dict:
    "Load Transcripts by symbol or stable_id"

    if by_symbol is None:
        by_symbol = bySymbol
    if by_id is None:
        by_id = byId

    assert by_id or by_symbol

    query: Dict[str, Any] = {"type": "Transcript"}
    genome_id = None
    if by_symbol:
        query["symbol"] = by_symbol["symbol"]
        query["genome_id"] = by_symbol["genome_id"]
        genome_id = by_symbol["genome_id"]
    if by_id:
        query["$or"] = [
            {"stable_id": by_id["stable_id"]},
            {"unversioned_stable_id": by_id["stable_id"]},
        ]
        query["genome_id"] = by_id["genome_id"]
        genome_id = by_id["genome_id"]

    assert genome_id is not None

    create_dataloader_collection(genome_id, info)

    collection = info.context["mongo_db"]
    transcript = collection.find_one(query)
    if not transcript:
        raise TranscriptNotFoundError(by_symbol=by_symbol, by_id=by_id)
    return transcript


@GENE_TYPE.field("transcripts")
async def resolve_gene_transcripts(gene: Dict, info: GraphQLResolveInfo) -> List[Dict]:
    "Use a DataLoader to get transcripts for the parent gene"

    gene_stable_id = gene["stable_id"]
    # Get a dataloader from info
    loader = get_dataloader_collection(info).gene_transcript_dataloader
    # Tell DataLoader to get this request done when it feels like it
    transcripts = await loader.load(key=gene_stable_id)
    return transcripts


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
        "type": "Gene",
        "genome_id": transcript["genome_id"],
        "stable_id": transcript["gene"],
    }
    collection = info.context["mongo_db"]
    gene = collection.find_one(query)
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
    genomeId: Optional[str] = None,
    regionName: Optional[str] = None,
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

    assert genome_id and region_name and start and end

    create_dataloader_collection(genome_id, info)

    # Thoas only contains "chromosome"-type regions
    region_id = "_".join([genome_id, region_name, "chromosome"])
    return {
        "genes": overlap_region(info.context, genome_id, region_id, start, end, "Gene"),
        "transcripts": overlap_region(
            info.context, genome_id, region_id, start, end, "Transcript"
        ),
    }


def overlap_region(
    context: Dict,
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
    results = list(context["mongo_db"].find(query).limit(max_results_size))
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

    assert genome_id and stable_id

    create_dataloader_collection(genome_id, info)

    query = {
        "genome_id": genome_id,
        "stable_id": stable_id,
        "type": {"$in": ["Protein", "MatureRNA"]},
    }

    collection = info.context["mongo_db"]
    result = collection.find_one(query)

    if not result:
        raise ProductNotFoundError(stable_id, genome_id)
    return result


@PGC_TYPE.field("product")
async def resolve_product_by_pgc(pgc: Dict, info: GraphQLResolveInfo) -> Optional[Dict]:
    "Fetch product that is referenced by the Product Generating Context"

    if pgc["product_id"] is None:
        return None
    loader = get_dataloader_collection(info).transcript_product_dataloader
    products = await loader.load(key=pgc["product_id"])
    # Data loader returns a list because most data-loads are one-many
    # ID mappings

    if not products:
        raise ProductNotFoundError(
            stable_id=pgc["product_id"], genome_id=pgc["genome_id"]
        )
    return products[0]


@SLICE_TYPE.field("region")
async def resolve_region(slc: Dict, info: GraphQLResolveInfo) -> Optional[Dict]:
    "Fetch a region that is referenced by a slice"
    if slc["region_id"] is None:
        return None
    region_id = slc["region_id"]

    loader = get_dataloader_collection(info).slice_region_dataloader

    regions = await loader.load(key=region_id)

    if not regions:
        raise RegionNotFoundError(region_id)
    return regions[0]


@REGION_TYPE.field("assembly")
async def resolve_assembly(region: Dict, info: GraphQLResolveInfo) -> Optional[Dict]:
    "Fetch an assembly referenced by a region"
    if region["assembly_id"] is None:
        return None
    assembly_id = region["assembly_id"]

    query = {"type": "Assembly", "id": region["assembly_id"]}

    collection = info.context["mongo_db"]
    result = collection.find_one(query)

    if not result:
        raise AssemblyNotFoundError(assembly_id)
    return result


class FieldNotFoundError(GraphQLError):
    """
    Custom error to be raised if a field cannot be found by id
    """

    def __init__(self, field_type: str, key_dict: Dict[str, str]):
        self.extensions = {"code": f"{field_type.upper()}_NOT_FOUND"}
        ids_string = ", ".join([f"{key}={val}" for key, val in key_dict.items()])
        message = f"Failed to find {field_type} with ids: {ids_string}"
        self.extensions.update(key_dict)
        super().__init__(message, extensions=self.extensions)


class FeatureNotFoundError(FieldNotFoundError):
    """
    Custom error to be raised if a gene or transcript cannot be found by id
    """

    def __init__(
        self,
        feature_type: str,
        bySymbol: Optional[Dict[str, str]] = None,
        byId: Optional[Dict[str, str]] = None,
    ):
        if bySymbol:
            super().__init__(
                feature_type,
                {"symbol": bySymbol["symbol"], "genome_id": bySymbol["genome_id"]},
            )
        if byId:
            super().__init__(
                feature_type,
                {"stable_id": byId["stable_id"], "genome_id": byId["genome_id"]},
            )


class GeneNotFoundError(FeatureNotFoundError):
    """
    Custom error to be raised if gene is not found
    """

    def __init__(
        self,
        by_symbol: Optional[Dict[str, str]] = None,
        by_id: Optional[Dict[str, str]] = None,
    ):
        super().__init__("gene", by_symbol, by_id)


class TranscriptNotFoundError(FeatureNotFoundError):
    """
    Custom error to be raised if transcript is not found
    """

    def __init__(
        self,
        by_symbol: Optional[Dict[str, str]] = None,
        by_id: Optional[Dict[str, str]] = None,
    ):
        super().__init__("transcript", by_symbol, by_id)


class ProductNotFoundError(FieldNotFoundError):
    """
    Custom error to be raised if product is not found
    """

    def __init__(self, stable_id: str, genome_id: str):
        super().__init__("product", {"stable_id": stable_id, "genome_id": genome_id})


class RegionNotFoundError(FieldNotFoundError):
    """
    Custom error to be raised if region is not found
    """

    def __init__(self, region_id: str):
        super().__init__("region", {"region_id": region_id})


class AssemblyNotFoundError(FieldNotFoundError):
    """
    Custom error to be raised in assembly is not found
    """

    def __init__(self, assembly_id: str):
        super().__init__("assembly", {"assembly_id": assembly_id})


class SliceLimitExceededError(GraphQLError):
    """
    Custom error to be raised if number of slice results exceeds limit
    """

    extensions = {"code": "SLICE_RESULT_LIMIT_EXCEEDED"}

    def __init__(self, max_results_size: int):
        message = f"Slice query met size limit of {max_results_size}"
        super().__init__(message, extensions=self.extensions)
