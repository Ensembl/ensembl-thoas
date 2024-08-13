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

from unittest.mock import Mock

import pytest
from starlette.datastructures import State

import graphql_service.resolver.gene_model as model
from common.crossrefs import XrefResolver
from graphql_service.tests.snapshot_utils import prepare_mongo_instance


def create_graphql_resolve_info(database_client):
    """
    Factory for creating the mock  Info objects produced by graphql
    """
    info = Mock()
    attrs = {"as_list.return_value": ["test_feature"]}
    info.path = Mock(**attrs)
    request_mock = Mock()
    request_mock.state = State()
    info.context = {
        "stuff": "Nonsense",
        "mongo_db_client": database_client,
        "XrefResolver": XrefResolver(from_file="common/tests/mini_identifiers.json"),
        "request": request_mock,
        "grpc_model": "fake_grpc_model",  # TODO: find a way to test/mock gRPC
    }
    return info


@pytest.fixture(name="basic_data")
def fixture_basic_data():
    "Some fake genes"

    mongo_client = prepare_mongo_instance()
    database = mongo_client.mongo_db
    database.gene.insert_many(
        [
            {
                "genome_id": "1",
                "type": "Gene",
                "symbol": "banana",
                "stable_id": "ENSG001.1",
                "unversioned_stable_id": "ENSG001",
                "gene_primary_id": "1_ENSG001.1",
            },
            {
                "genome_id": "1",
                "type": "Gene",
                "symbol": "durian",
                "stable_id": "ENSG002.2",
                "unversioned_stable_id": "ENSG002",
                "gene_primary_id": "1_ENSG002.2",
            },
        ]
    )

    return mongo_client


@pytest.fixture(name="transcript_data")
def fixture_transcript_data():
    "Some fake transcripts"

    mongo_client = prepare_mongo_instance()
    database = mongo_client.mongo_db
    database.gene.insert_many(
        [
            {
                "genome_id": "1",
                "type": "Gene",
                "symbol": "banana",
                "stable_id": "ENSG001.1",
                "unversioned_stable_id": "ENSG001",
                "gene_primary_key": "1_ENSG001.1",
            }
        ]
    )

    database.transcript.insert_many(
        [
            {
                "genome_id": "1",
                "type": "Transcript",
                "symbol": "kumquat",
                "stable_id": "ENST001.1",
                "unversioned_stable_id": "ENST001",
                "gene": "ENSG001.1",
                "product_generating_contexts": [
                    {
                        "product_type": "Protein",
                        "product_id": "ENSP001.1",
                        "product_foreign_key": "1_ENSP001.1",
                    }
                ],
                "gene_foreign_key": "1_ENSG001.1",
            },
            {
                "genome_id": "1",
                "type": "Transcript",
                "symbol": "grape",
                "stable_id": "ENST002.2",
                "unversioned_stable_id": "ENST002",
                "gene": "ENSG001.1",
                "product_generating_contexts": [],
                "gene_foreign_key": "1_ENSG001.1",
            },
        ]
    )

    database.protein.insert_many(
        [
            {
                "genome_id": "1",
                "type": "Protein",
                "stable_id": "ENSP001.1",
                "product_primary_key": "1_ENSP001.1",
            },
        ]
    )
    return mongo_client


@pytest.fixture(name="region_data")
def fixture_region_data():
    mongo_client = prepare_mongo_instance()
    database = mongo_client.mongo_db
    database.region.insert_many(
        [
            {
                "type": "Region",
                "region_id": "plasmodium_falciparum_GCA_000002765_2_blah",
                "name": "blah",
                "genome_id": "plasmodium_falciparum_GCA_000002765_2",
            },
            {
                "type": "Region",
                "region_id": "plasmodium_falciparum_GCA_000002765_2_14",
                "name": "14",
                "genome_id": "plasmodium_falciparum_GCA_000002765_2",
            },
            {
                "type": "Region",
                "region_id": "plasmodium_falciparum_GCA_000002765_2_13",
                "name": "13",
                "genome_id": "plasmodium_falciparum_GCA_000002765_2",
            },
        ]
    )
    return mongo_client


@pytest.fixture(name="slice_data")
def fixture_slice_data():
    """
    Test genes with slices
    """
    mongo_client = prepare_mongo_instance()
    database = mongo_client.mongo_db
    database.gene.insert_many(
        [
            {
                "genome_id": "test_genome_id",
                "type": "Gene",
                "symbol": "banana",
                "stable_id": "ENSG001.1",
                "unversioned_stable_id": "ENSG001",
                "slice": {
                    "region_id": "test_genome_id_chr1_chromosome",
                    "location": {"start": 10, "end": 100},
                },
            },
            {
                "genome_id": "test_genome_id",
                "type": "Gene",
                "symbol": "durian",
                "stable_id": "ENSG002.2",
                "unversioned_stable_id": "ENSG002",
                "slice": {
                    "region_id": "test_genome_id_chr1_chromosome",
                    "location": {"start": 110, "end": 200},
                },
            },
        ]
    )

    too_many_results = []

    for i in range(1001):
        too_many_results.append(
            {
                "genome_id": "test_genome_id",
                "type": "Gene",
                "symbol": "banana",
                "stable_id": "test_stable_id." + str(i),
                "unversioned_stable_id": "test_stable_id." + str(i),
                "slice": {
                    "region_id": "test_genome_id_chr1_chromosome",
                    "location": {"start": 210, "end": 300},
                },
            }
        )
    database.gene.insert_many(too_many_results)

    return mongo_client


@pytest.fixture(name="genome_data")
def fixture_genome_data():
    mongo_client = prepare_mongo_instance()
    database = mongo_client.mongo_db
    database.assembly.insert_many(
        [
            {
                "type": "Assembly",
                "assembly_id": "test_assembly_id_1",
                "name": "banana assembly",
                "organism_foreign_key": "test_organism_id_1",
            },
            {
                "type": "Assembly",
                "assembly_id": "test_assembly_id_2",
                "name": "other banana assembly",
                "organism_foreign_key": "test_organism_id_1",
            },
        ]
    )

    database.organism.insert_many(
        [
            {
                "type": "Organism",
                "scientific_name": "banana",
                "organism_primary_key": "test_organism_id_1",
                "species_foreign_key": "test_species_id_1",
            },
            {
                "type": "Organism",
                "scientific_name": "other banana",
                "organism_primary_key": "test_organism_id_2",
                "species_foreign_key": "test_species_id_1",
            },
        ]
    )

    database.species.insert_many(
        [
            {
                "type": "Species",
                "scientific_name": "banana",
                "species_primary_key": "test_species_id_1",
            }
        ]
    )

    database.region.insert_many(
        [
            {
                "type": "Region",
                "region_id": "test_region_id_1",
                "assembly_id": "test_assembly_id_1",
                "name": "I",
            },
            {
                "type": "Region",
                "region_id": "test_region_id_2",
                "assembly_id": "test_assembly_id_1",
                "name": "II",
            },
        ]
    )
    return mongo_client


def test_resolve_gene(basic_data):
    "Test the querying of Mongo by gene symbol"

    info = create_graphql_resolve_info(basic_data)

    # Check we can resolve using byId camelCase
    result = model.resolve_gene(
        None, info, byId={"stable_id": "ENSG001.1", "genome_id": "1"}
    )
    assert result["symbol"] == "banana"
    result = None

    # Check we can resolve using by_id snake_case
    result = model.resolve_gene(
        None, info, by_id={"stable_id": "ENSG001.1", "genome_id": "1"}
    )
    assert result["symbol"] == "banana"
    result = None

    with pytest.raises(model.GeneNotFoundError) as gene_not_found_error:
        result = model.resolve_gene(
            None, info, byId={"stable_id": "BROKEN BROKEN BROKEN", "genome_id": "1"}
        )
    assert not result
    assert (
        gene_not_found_error.value.message
        == "Failed to find gene with ids: stable_id=BROKEN BROKEN BROKEN, genome_id=1"
    )
    assert gene_not_found_error.value.extensions["code"] == "GENE_NOT_FOUND"
    assert gene_not_found_error.value.extensions["stable_id"] == "BROKEN BROKEN BROKEN"
    assert gene_not_found_error.value.extensions["genome_id"] == "1"
    gene_not_found_error = None

    # Check unversioned query resolves as well
    result = model.resolve_gene(
        None, info, byId={"stable_id": "ENSG001", "genome_id": "1"}
    )

    assert result["symbol"] == "banana"


def test_resolve_gene_by_symbol(basic_data):
    "Test querying by gene symbol which can be ambiguous"

    info = create_graphql_resolve_info(basic_data)

    # Check we can resolve using by_symbol
    result = model.resolve_genes(
        None, info, by_symbol={"symbol": "banana", "genome_id": "1"}
    )
    assert isinstance(result, list)
    assert result[0]["symbol"] == "banana"
    result = None

    with pytest.raises(model.GeneNotFoundError) as gene_not_found_error:
        result = model.resolve_genes(
            None, info, by_symbol={"symbol": "very not here", "genome_id": "1"}
        )
    assert not result
    assert (
        gene_not_found_error.value.message
        == "Failed to find gene with ids: symbol=very not here, genome_id=1"
    )
    assert gene_not_found_error.value.extensions["code"] == "GENE_NOT_FOUND"
    assert gene_not_found_error.value.extensions["symbol"] == "very not here"
    assert gene_not_found_error.value.extensions["genome_id"] == "1"


def test_resolve_transcript_by_id(transcript_data):
    "Test fetching of transcripts by stable ID"

    info = create_graphql_resolve_info(transcript_data)
    result = model.resolve_transcript(
        None, info, byId={"stable_id": "ENST001.1", "genome_id": "1"}
    )

    assert result["symbol"] == "kumquat"
    assert result["stable_id"] == "ENST001.1"


def test_resolve_transcript_by_id_not_found(transcript_data):
    result = None
    info = create_graphql_resolve_info(transcript_data)
    with pytest.raises(model.TranscriptNotFoundError) as transcript_not_found_error:
        result = model.resolve_transcript(
            None, info, byId={"stable_id": "FAKEYFAKEYFAKEY", "genome_id": "1"}
        )
    assert not result
    assert (
        transcript_not_found_error.value.message
        == "Failed to find transcript with ids: stable_id=FAKEYFAKEYFAKEY, genome_id=1"
    )
    assert transcript_not_found_error.value.extensions["code"] == "TRANSCRIPT_NOT_FOUND"
    assert transcript_not_found_error.value.extensions["stable_id"] == "FAKEYFAKEYFAKEY"
    assert transcript_not_found_error.value.extensions["genome_id"] == "1"


def test_resolve_transcript_by_symbol(transcript_data):
    "Test fetching of transcripts by symbol"

    info = create_graphql_resolve_info(transcript_data)
    result = model.resolve_transcript(
        None, info, bySymbol={"symbol": "kumquat", "genome_id": "1"}
    )
    assert result["stable_id"] == "ENST001.1"


def test_resolve_transcript_by_symbol_not_found(transcript_data):
    info = create_graphql_resolve_info(transcript_data)
    with pytest.raises(model.TranscriptNotFoundError) as transcript_not_found_error:
        model.resolve_transcript(
            None,
            info,
            bySymbol={"symbol": "some not existing symbol", "genome_id": "1"},
        )
    assert (
        transcript_not_found_error.value.message
        == "Failed to find transcript with ids: symbol=some not existing symbol, genome_id=1"
    )
    assert transcript_not_found_error.value.extensions["code"] == "TRANSCRIPT_NOT_FOUND"
    assert (
        transcript_not_found_error.value.extensions["symbol"]
        == "some not existing symbol"
    )
    assert transcript_not_found_error.value.extensions["genome_id"] == "1"


@pytest.mark.asyncio
async def test_resolve_gene_transcripts(transcript_data):
    "Check the DataLoader for transcripts is working via gene. Requires event loop for DataLoader"

    info = create_graphql_resolve_info(transcript_data)

    # Finding the collection here as we are not using the base resolver
    model.set_db_conn_for_uuid(info, "1")

    result = await model.resolve_gene_transcripts(
        {"stable_id": "ENSG001.1", "genome_id": "1", "gene_primary_key": "1_ENSG001.1"},
        info,
    )

    for hit in result:
        assert hit["type"] == "Transcript"
        assert hit["symbol"] in ["kumquat", "grape"]


@pytest.mark.asyncio
async def test_resolve_gene_from_transcript(transcript_data):
    "Check the DataLoader for gene is working via transcript. Requires event loop for DataLoader"

    info = create_graphql_resolve_info(transcript_data)

    # Finding the collection here as we are not using the base resolver
    model.set_db_conn_for_uuid(info, "1")

    result = await model.resolve_transcript_gene(
        {"gene": "ENSG001.1", "genome_id": "1"}, info
    )

    assert result["type"] == "Gene"
    assert result["stable_id"] == "ENSG001.1"
    assert result["symbol"] == "banana"


def test_resolve_overlap(slice_data):
    "Check features can be found via coordinates"

    info = create_graphql_resolve_info(slice_data)

    # Finding the collection here as we are not using the base resolver
    model.set_db_conn_for_uuid(info, "test_genome_id")

    result = model.resolve_overlap(
        None,
        info,
        genomeId="test_genome_id",
        regionName="chr1",
        start=10,
        end=11,
        by_slice=None,
    )
    assert {hit["stable_id"] for hit in result["genes"]} == {"ENSG001.1"}


query_region_expectations = [
    (1, 5, set()),  # No overlaps if search region is to the left of all features
    (305, 310, set()),  # No overlaps if search region is to the right of all features
    (40, 50, {"ENSG001.1"}),  # search region contained in a single feature
    (5, 105, {"ENSG001.1"}),  # search region contains a feature
    (5, 15, {"ENSG001.1"}),  # search region contains start of a feature but not the end
    (
        95,
        105,
        {"ENSG001.1"},
    ),  # search region contains end of a feature but not the start
    (5, 205, {"ENSG001.1", "ENSG002.2"}),  # search region contains two features
    (50, 150, {"ENSG001.1", "ENSG002.2"}),  # search region overlaps two features
]


@pytest.mark.parametrize("start,end,expected_ids", query_region_expectations)
def test_overlap_region(start, end, expected_ids, slice_data):

    info = create_graphql_resolve_info(slice_data)

    # Finding the collection here as we are not using the base resolver
    model.set_db_conn_for_uuid(info, "test_genome_id")
    connection = model.get_db_conn(info)

    result = model.overlap_region(
        connection=connection,
        genome_id="test_genome_id",
        region_id="test_genome_id_chr1_chromosome",
        start=start,
        end=end,
        feature_type="Gene",
    )
    assert {hit["stable_id"] for hit in result} == expected_ids


def test_overlap_region_too_many_results(slice_data):

    info = create_graphql_resolve_info(slice_data)

    # Finding the collection here as we are not using the base resolver
    model.set_db_conn_for_uuid(info, "test_genome_id")
    connection = model.get_db_conn(info)

    result = None
    with pytest.raises(model.SliceLimitExceededError) as slice_limit_exceeded_error:
        result = model.overlap_region(
            connection=connection,
            genome_id="test_genome_id",
            region_id="test_genome_id_chr1_chromosome",
            start=205,
            end=305,
            feature_type="Gene",
        )
    assert not result
    assert (
        slice_limit_exceeded_error.value.message == "Slice query met size limit of 1000"
    )
    assert (
        slice_limit_exceeded_error.value.extensions["code"]
        == "SLICE_RESULT_LIMIT_EXCEEDED"
    )


@pytest.mark.asyncio
async def test_resolve_region_happy_case(region_data):
    slc = {
        "region_id": "plasmodium_falciparum_GCA_000002765_2_13",
        "location": {"start": 624785, "end": 626011, "length": 1227},
        "strand": {"code": "forward", "value": 1},
        "default": True,
    }
    info = create_graphql_resolve_info(region_data)

    # Finding the collection here as we are not using the base resolver
    model.set_db_conn_for_uuid(info, "plasmodium_falciparum_GCA_000002765_2")

    result = await model.resolve_region_from_slice(slc, info)
    assert result["region_id"] == "plasmodium_falciparum_GCA_000002765_2_13"


@pytest.mark.asyncio
async def test_resolve_region_region_not_exist(region_data):
    info = create_graphql_resolve_info(region_data)
    slc = {
        "region_id": "some_non_existing_region_id",
    }
    model.set_db_conn_for_uuid(info, "plasmodium_falciparum_GCA_000002765_2")

    result = None
    with pytest.raises(model.RegionFromSliceNotFoundError) as region_error:
        result = await model.resolve_region_from_slice(slc, info)
    assert not result
    assert region_error.value.extensions["region_id"] == "some_non_existing_region_id"


def test_url_generation(basic_data):
    "Check URLs are attached to cross references"
    xref = {
        "accession_id": "some_molecule",
        "name": "Chemistry rocks",
        "assignment_method": {"type": "DIRECT"},
        "description": "Chemistry is the best",
        "source": {
            "id": "ChEBI",
            "name": "Chemical Entities of Biological Interest",
            "description": None,
            "release": 10,
        },
    }

    info = create_graphql_resolve_info(basic_data)
    result = model.insert_crossref_urls({"external_references": [xref]}, info)

    for key, value in xref.items():
        assert result[0][key] == value, "Original structure retained"

    assert (
        result[0]["url"]
        == "https://www.ebi.ac.uk/chebi/searchId.do?chebiId=CHEBI:some_molecule"
    )
    assert result[0]["source"]["url"] == "https://www.ebi.ac.uk/chebi/"
    assert (
        result[0]["assignment_method"]["description"]
        == "A reference made by an external resource of annotation to an Ensembl feature that Ensembl imports without modification"
    )


@pytest.mark.asyncio
async def test_resolve_transcript_products(transcript_data):
    "Check the DataLoader for products is working via transcript. Requires event loop for DataLoader"

    info = create_graphql_resolve_info(transcript_data)

    # Finding the collection here as we are not using the base resolver
    model.set_db_conn_for_uuid(info, "1")

    result = await model.resolve_product_by_pgc(
        {
            "product_id": "ENSP001.1",
            "genome_id": "1",
            "product_foreign_key": "1_ENSP001.1",
        },
        info,
    )

    assert result["type"] == "Protein"
    assert result["stable_id"] == "ENSP001.1"


@pytest.mark.asyncio
async def test_resolve_transcript_products_product_not_exists(transcript_data):
    product = {
        "product_id": "some not existing id",
        "genome_id": "1",
        "product_foreign_key": "adsfadsfa",
    }
    info = create_graphql_resolve_info(transcript_data)

    # Finding the collection here as we are not using the base resolver
    model.set_db_conn_for_uuid(info, "1")

    result = None
    with pytest.raises(model.FieldNotFoundError) as field_not_found_error:
        result = await model.resolve_product_by_pgc(product, info)
    assert not result
    assert field_not_found_error.value.extensions["product_foreign_key"] == "adsfadsfa"


@pytest.mark.asyncio
async def test_resolve_nested_products(transcript_data):
    "Test products inside transcripts inside the gene"

    info = create_graphql_resolve_info(transcript_data)
    gene_result = model.resolve_gene(
        None, info, byId={"genome_id": "1", "stable_id": "ENSG001.1"}
    )
    assert gene_result

    transcript_result = await model.resolve_gene_transcripts(gene_result, info)
    for i in transcript_result:
        for pgc in i["product_generating_contexts"]:
            pgc["genome_id"] = "1"
            product_result = await model.resolve_product_by_pgc(pgc, info)
            if "stable_id" in product_result:
                assert product_result["stable_id"] == "ENSP001.1"


@pytest.mark.asyncio
async def test_resolve_assembly_from_region(genome_data):
    info = create_graphql_resolve_info(genome_data)

    # Finding the collection here as we are not using the base resolver
    model.set_db_conn_for_uuid(info, "1")

    region = {
        "type": "Region",
        "assembly_id": "test_assembly_id_1",
    }
    assembly_result = await model.resolve_assembly_from_region(region, info)
    assert remove_ids(assembly_result) == {
        "type": "Assembly",
        "assembly_id": "test_assembly_id_1",
        "name": "banana assembly",
        "organism_foreign_key": "test_organism_id_1",
    }


@pytest.mark.asyncio
async def test_resolve_assembly_from_region_not_exists(genome_data):
    info = create_graphql_resolve_info(genome_data)

    # Finding the collection here as we are not using the base resolver
    model.set_db_conn_for_uuid(info, "1")

    region = {
        "type": "Region",
        "region_id": "test_region_id_1",
        "assembly_id": "kjhbkjhgkhj",
        "name": "I",
    }

    result = None
    with pytest.raises(model.AssemblyNotFoundError) as assembly_not_found_error:
        result = await model.resolve_assembly_from_region(region, info)
    assert not result
    assert assembly_not_found_error.value.extensions["assembly_id"] == "kjhbkjhgkhj"


@pytest.mark.asyncio
async def test_resolve_regions_from_assembly(genome_data):
    info = create_graphql_resolve_info(genome_data)

    # Finding the collection here as we are not using the base resolver
    model.set_db_conn_for_uuid(info, "1")

    assembly = {
        "type": "Assembly",
        "assembly_id": "test_assembly_id_1",
    }
    regions_result = await model.resolve_regions_from_assembly(assembly, info)
    regions_result = sorted(regions_result, key=lambda r: r["assembly_id"])
    assert remove_ids(regions_result) == [
        {
            "type": "Region",
            "region_id": "test_region_id_1",
            "assembly_id": "test_assembly_id_1",
            "name": "I",
        },
        {
            "type": "Region",
            "region_id": "test_region_id_2",
            "assembly_id": "test_assembly_id_1",
            "name": "II",
        },
    ]


@pytest.mark.asyncio
async def test_resolve_regions_from_assembly_not_exists(genome_data):
    info = create_graphql_resolve_info(genome_data)

    # Finding the collection here as we are not using the base resolver
    model.set_db_conn_for_uuid(info, "1")

    assembly = {
        "type": "Assembly",
        "assembly_id": "blah blah",
    }

    result = None
    with pytest.raises(model.RegionsFromAssemblyNotFound) as regions_not_found_error:
        result = await model.resolve_regions_from_assembly(assembly, info)
    assert not result
    assert regions_not_found_error.value.extensions["assembly_id"] == "blah blah"


@pytest.mark.asyncio
async def test_resolve_organism_from_assembly(genome_data):
    info = create_graphql_resolve_info(genome_data)

    # Finding the collection here as we are not using the base resolver
    model.set_db_conn_for_uuid(info, "1")

    assembly = {"type": "Assembly", "organism_foreign_key": "test_organism_id_1"}

    organism_result = await model.resolve_organism_from_assembly(assembly, info)

    assert remove_ids(organism_result) == {
        "type": "Organism",
        "scientific_name": "banana",
        "organism_primary_key": "test_organism_id_1",
        "species_foreign_key": "test_species_id_1",
    }


@pytest.mark.asyncio
async def test_resolve_organism_from_assembly_not_exists(genome_data):
    info = create_graphql_resolve_info(genome_data)

    # Finding the collection here as we are not using the base resolver
    model.set_db_conn_for_uuid(info, "1")

    assembly = {"type": "Assembly", "organism_foreign_key": "blah blah"}

    result = None
    with pytest.raises(model.OrganismFromAssemblyNotFound) as organism_not_found_error:
        result = await model.resolve_organism_from_assembly(assembly, info)
    assert not result
    assert organism_not_found_error.value.extensions["organism_id"] == "blah blah"


@pytest.mark.asyncio
async def test_resolve_assemblies_from_organism(genome_data):
    info = create_graphql_resolve_info(genome_data)

    # Finding the collection here as we are not using the base resolver
    model.set_db_conn_for_uuid(info, "1")

    organism = {
        "type": "Organism",
        "scientific_name": "banana",
        "organism_primary_key": "test_organism_id_1",
        "species_foreign_key": "test_species_id_1",
    }

    assemblies_result = await model.resolve_assemblies_from_organism(organism, info)

    assert remove_ids(assemblies_result) == [
        {
            "type": "Assembly",
            "assembly_id": "test_assembly_id_1",
            "name": "banana assembly",
            "organism_foreign_key": "test_organism_id_1",
        },
        {
            "type": "Assembly",
            "assembly_id": "test_assembly_id_2",
            "name": "other banana assembly",
            "organism_foreign_key": "test_organism_id_1",
        },
    ]


@pytest.mark.asyncio
async def test_resolve_assemblies_from_organism_not_exists(genome_data):
    info = create_graphql_resolve_info(genome_data)
    # Finding the collection here as we are not using the base resolver
    model.set_db_conn_for_uuid(info, "1")

    organism = {
        "type": "Organism",
        "scientific_name": "banana",
        "organism_primary_key": "blah blah",
    }

    result = None
    with pytest.raises(
        model.AssembliesFromOrganismNotFound
    ) as assemblies_not_found_error:
        result = await model.resolve_assemblies_from_organism(organism, info)
    assert not result
    assert assemblies_not_found_error.value.extensions["organism_id"] == "blah blah"


@pytest.mark.asyncio
async def test_resolve_species_from_organism(genome_data):
    info = create_graphql_resolve_info(genome_data)

    # Finding the collection here as we are not using the base resolver
    model.set_db_conn_for_uuid(info, "1")

    organism = {
        "type": "Organism",
        "scientific_name": "banana",
        "organism_primary_key": "test_organism_id_1",
        "species_foreign_key": "test_species_id_1",
    }

    species_result = await model.resolve_species_from_organism(organism, info)

    assert remove_ids(species_result) == {
        "type": "Species",
        "scientific_name": "banana",
        "species_primary_key": "test_species_id_1",
    }


@pytest.mark.asyncio
async def test_resolve_species_from_organism_not_exists(genome_data):
    info = create_graphql_resolve_info(genome_data)

    # Finding the collection here as we are not using the base resolver
    model.set_db_conn_for_uuid(info, "1")

    organism = {
        "type": "Organism",
        "scientific_name": "banana",
        "species_foreign_key": "blah blah",
    }

    result = None
    with pytest.raises(model.SpeciesFromOrganismNotFound) as species_not_found_error:
        result = await model.resolve_species_from_organism(organism, info)
    assert not result
    assert species_not_found_error.value.extensions["species_id"] == "blah blah"


@pytest.mark.asyncio
async def test_resolve_organisms_from_species(genome_data):
    info = create_graphql_resolve_info(genome_data)

    # Finding the collection here as we are not using the base resolver
    model.set_db_conn_for_uuid(info, "1")

    species = {
        "type": "Species",
        "scientific_name": "banana",
        "species_primary_key": "test_species_id_1",
    }

    organisms_result = await model.resolve_organisms_from_species(species, info)

    assert remove_ids(organisms_result) == [
        {
            "type": "Organism",
            "scientific_name": "banana",
            "organism_primary_key": "test_organism_id_1",
            "species_foreign_key": "test_species_id_1",
        },
        {
            "type": "Organism",
            "scientific_name": "other banana",
            "organism_primary_key": "test_organism_id_2",
            "species_foreign_key": "test_species_id_1",
        },
    ]


@pytest.mark.asyncio
async def test_resolve_organisms_from_species_not_exists(genome_data):
    info = create_graphql_resolve_info(genome_data)

    # Finding the collection here as we are not using the base resolver
    model.set_db_conn_for_uuid(info, "1")

    species = {
        "type": "Species",
        "scientific_name": "banana",
        "species_primary_key": "blah blah",
    }
    result = None
    with pytest.raises(model.OrganismsFromSpeciesNotFound) as organisms_not_found_error:
        result = await model.resolve_organisms_from_species(species, info)
    assert not result
    assert organisms_not_found_error.value.extensions["species_id"] == "blah blah"


@pytest.mark.asyncio
async def test_resolve_region(region_data):
    info = create_graphql_resolve_info(region_data)

    result = await model.resolve_region(
        None,
        info,
        by_name={"genome_id": "plasmodium_falciparum_GCA_000002765_2", "name": "14"},
    )
    assert remove_ids(result) == {
        "genome_id": "plasmodium_falciparum_GCA_000002765_2",
        "name": "14",
        "region_id": "plasmodium_falciparum_GCA_000002765_2_14",
        "type": "Region",
    }


@pytest.mark.asyncio
async def test_resolve_region_no_results(region_data):
    info = create_graphql_resolve_info(region_data)

    result = None
    with pytest.raises(model.RegionNotFoundError) as region_not_found_error:
        result = await model.resolve_region(
            None, info, by_name={"genome_id": "yeti_genome", "name": "14"}
        )
    assert not result
    assert region_not_found_error.value.extensions == {
        "code": "REGION_NOT_FOUND",
        "genome_id": "yeti_genome",
        "name": "14",
    }


@pytest.mark.asyncio
async def test_resolve_gene_transcripts_page():
    gene = {
        "genome_id": "1",
        "type": "Gene",
        "symbol": "banana",
        "stable_id": "ENSG001.1",
        "unversioned_stable_id": "ENSG001",
        "gene_primary_key": "1_ENSG001.1",
    }
    result = await model.resolve_gene_transcripts_page(gene, None, 1, 2)
    assert result == {"gene_primary_key": "1_ENSG001.1", "page": 1, "per_page": 2}


@pytest.mark.asyncio
async def test_resolve_transcripts_page_transcripts(transcript_data):
    info = create_graphql_resolve_info(transcript_data)

    # Finding the collection here as we are not using the base resolver
    model.set_db_conn_for_uuid(info, "1")

    transcripts_page = {"gene_primary_key": "1_ENSG001.1", "page": 2, "per_page": 1}
    result = await model.resolve_transcripts_page_transcripts(transcripts_page, info)
    assert remove_ids(result) == [
        {
            "gene": "ENSG001.1",
            "gene_foreign_key": "1_ENSG001.1",
            "genome_id": "1",
            "product_generating_contexts": [],
            "stable_id": "ENST002.2",
            "symbol": "grape",
            "type": "Transcript",
            "unversioned_stable_id": "ENST002",
        }
    ]


@pytest.mark.asyncio
async def test_resolve_transcripts_page_transcripts_no_transcripts(transcript_data):
    info = create_graphql_resolve_info(transcript_data)

    # Finding the collection here as we are not using the base resolver
    model.set_db_conn_for_uuid(info, "1")

    transcripts_page = {"gene_primary_key": "1_ENSG001.1", "page": 3, "per_page": 1}
    result = await model.resolve_transcripts_page_transcripts(transcripts_page, info)
    assert result == []


@pytest.mark.asyncio
async def test_resolve_transcripts_page_metadata(transcript_data):
    info = create_graphql_resolve_info(transcript_data)

    # Finding the collection here as we are not using the base resolver
    model.set_db_conn_for_uuid(info, "1")

    transcripts_page = {"gene_primary_key": "1_ENSG001.1", "page": 2, "per_page": 1}
    result = await model.resolve_transcripts_page_metadata(transcripts_page, info)
    assert result == {"page": 2, "per_page": 1, "total_count": 2}


def remove_ids(test_output):
    if isinstance(test_output, dict):
        del test_output["_id"]
    elif isinstance(test_output, list):
        for output in test_output:
            del output["_id"]

    return test_output
