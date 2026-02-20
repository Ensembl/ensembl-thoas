import pytest
import pytest_asyncio
from ariadne import graphql

from graphql_service.ariadne_app import prepare_executable_schema
from graphql_service.tests.test_db_client import FakeAsyncMongoDbClient


@pytest_asyncio.fixture
async def async_setup():
    executable_schema = prepare_executable_schema()
    mongo_client = FakeAsyncMongoDbClient()

    def context_provider():
        return {
            "mongo_db_client": mongo_client,
            "grpc_model": "fake_grpc_model",
        }

    return executable_schema, context_provider


async def populate_data(context_value):
    db = context_value["mongo_db_client"].mongo_db
    # set up data , transcript ENST00000680071.1 is present in
    # a7335667-93e7-11ec-a39d-005056b38ce3 and 2b5fb047-5992-4dfb-b2fa-1fb4e18d1abb
    transcript_doc = {
        "type": "Transcript",
        "stable_id": "ENST00000680071.1",
        "unversioned_stable_id": "ENST00000680071",
        "version": 1,
        "symbol": "AHI1-232",
        "gene": "ENSG00000135541.22",
    }
    gene_doc = {
        "type": "Gene",
        "stable_id": "ENSG00000135541.22",
        "name": "Abelson helper integration site 1",
    }

    first_genome = "a7335667-93e7-11ec-a39d-005056b38ce3"
    second_genome = "2b5fb047-5992-4dfb-b2fa-1fb4e18d1abb"
    await db["transcript"].insert_many(
        [
            {**transcript_doc, "genome_id": first_genome},
            {**transcript_doc, "genome_id": second_genome},
        ]
    )
    await db["gene"].insert_many(
        [
            {**gene_doc, "genome_id": first_genome},
            {**gene_doc, "genome_id": second_genome},
        ]
    )


@pytest.mark.asyncio
async def test_transcript_search_happy_path(async_setup):
    executable_schema, context = async_setup
    context_value = context()
    await populate_data(context_value)

    query = """
    query AsyncQuery {
      transcript_search(
        search_payload: {
          query: "ENST00000680071.1", 
          genome_ids: [
            "a7335667-93e7-11ec-a39d-005056b38ce3",
          ],
          page: 1,
          per_page: 50
        }
      ) {
        meta {
          total_hits
          page
          per_page
        }
        matches {
          stable_id
          symbol
          gene {
            stable_id
            name
          }
        }
      }
    }
    """

    success, result = await graphql(
        executable_schema, {"query": query}, context_value=context_value
    )

    assert success
    assert result["data"]["transcript_search"]["meta"] == {
        "total_hits": 1,
        "page": 1,
        "per_page": 50,
    }
    assert result["data"]["transcript_search"]["matches"] == [
        {
            "stable_id": "ENST00000680071.1",
            "symbol": "AHI1-232",
            "gene": {
                "stable_id": "ENSG00000135541.22",
                "name": "Abelson helper integration site 1",
            },
        }
    ]


@pytest.mark.asyncio
async def test_transcript_search_invalid_query(async_setup):
    executable_schema, context = async_setup
    context_value = context()

    query = """
    query AsyncQuery {
      transcript_search(
        search_payload: {
          query: "INVALID_TRANSCRIPT_ID", 
          genome_ids: [
            "a7335667-93e7-11ec-a39d-005056b38ce3",
          ],
          page: 1,
          per_page: 50
        }
      ) {
        meta {
          total_hits
          page
          per_page
        }
        matches {
          stable_id
          symbol
          gene {
            stable_id
            name
          }
        }
      }
    }
    """

    success, result = await graphql(
        executable_schema, {"query": query}, context_value=context_value
    )

    assert success
    assert result["data"]["transcript_search"] == {
        "meta": {"total_hits": 0, "page": 1, "per_page": 50},
        "matches": [],
    }


@pytest.mark.asyncio
async def test_transcript_search_no_genome_ids(async_setup):
    executable_schema, context = async_setup
    context_value = context()

    query = """
    query AsyncQuery {
      transcript_search(
        search_payload: {
          query: "ENST00000680071.1", 
          genome_ids: [],
          page: 1,
          per_page: 50
        }
      ) {
        meta {
          total_hits
          page
          per_page
        }
        matches {
          stable_id
          symbol
          gene {
            stable_id
            name
          }
        }
      }
    }
    """

    success, result = await graphql(
        executable_schema, {"query": query}, context_value=context_value
    )

    assert success
    assert result["data"]["transcript_search"] == {
        "meta": {"total_hits": 0, "page": 1, "per_page": 50},
        "matches": [],
    }


@pytest.mark.asyncio
async def test_transcript_search_multiple_genome_ids(async_setup):
    executable_schema, context = async_setup
    context_value = context()
    await populate_data(context_value)

    query = """
    query AsyncQuery {
      transcript_search(
        search_payload: {
          query: "ENST00000680071.1", 
          genome_ids: [
            "a7335667-93e7-11ec-a39d-005056b38ce3",
            "2b5fb047-5992-4dfb-b2fa-1fb4e18d1abb",
            "3704ceb1-948d-11ec-a39d-005056b38ce3",
            "4c07817b-c7c5-463f-8624-982286bc4355",
            "7569f6f1-e742-4e50-a829-1e8f2dd6db87",
          ],
          page: 1,
          per_page: 50
        }
      ) {
        meta {
          total_hits
          page
          per_page
        }
        matches {
          stable_id
          symbol
          gene {
            stable_id
            name
          }
        }
      }
    }
    """

    success, result = await graphql(
        executable_schema, {"query": query}, context_value=context_value
    )

    assert success
    assert result["data"]["transcript_search"]["meta"] == {
        "total_hits": 2,
        "page": 1,
        "per_page": 50,
    }

    # basically same transcript-gene present in two genomes
    assert result["data"]["transcript_search"]["matches"] == [
        {
            "stable_id": "ENST00000680071.1",
            "symbol": "AHI1-232",
            "gene": {
                "stable_id": "ENSG00000135541.22",
                "name": "Abelson helper integration site 1",
            },
        },
        {
            "stable_id": "ENST00000680071.1",
            "symbol": "AHI1-232",
            "gene": {
                "stable_id": "ENSG00000135541.22",
                "name": "Abelson helper integration site 1",
            },
        },
    ]


@pytest.mark.asyncio
async def test_transcript_search_missing_fields(async_setup):
    executable_schema, context = async_setup
    context_value = context()

    query = """
    query AsyncQuery {
      transcript_search(
        search_payload: {
          query: "ENST00000680071.1",
          per_page: 50
        }
      ) {
        meta {
          total_hits
          page
          per_page
        }
        matches {
          stable_id
          symbol
          gene {
            stable_id
            name
          }
        }
      }
    }
    """

    success, result = await graphql(
        executable_schema, {"query": query}, context_value=context_value
    )

    assert success is False
    assert "errors" in result
    # {'errors': [
    #     {'message': "Field 'TranscriptIdGenomeIdsInput.genome_ids' of required type '[String!]!' was not provided.",
    #      'locations': [{'line': 4, 'column': 25}]},
    #     {'message': "Field 'TranscriptIdGenomeIdsInput.page' of required type 'Int!' was not provided.",
    #      'locations': [{'line': 4, 'column': 25}]}]}
    assert (
        "Field 'TranscriptIdGenomeIdsInput.genome_ids' of required type '[String!]!' was not provided."
        in result["errors"][0]["message"]
    )
    assert (
        "Field 'TranscriptIdGenomeIdsInput.page' of required type 'Int!' was not provided."
        in result["errors"][1]["message"]
    )
