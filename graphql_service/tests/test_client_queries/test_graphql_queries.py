import glob
import os

import pytest
from starlette.testclient import TestClient
import json

# If MONGO_HOST is not set, skip the entire file before importing APP
# to avoid: KeyError: "Missing information in configuration file - 'MONGO_HOST'
if not os.getenv("MONGO_HOST"):
    pytest.skip(
        "Skipping GraphQL tests because no MONGO_HOST is configured",
        allow_module_level=True,
    )

# import our ASGI application
from graphql_service.server import APP

# Directory where all your .graphql files live
QUERIES_DIR = os.path.join(os.path.dirname(__file__), "queries")


def load_all_graphql_queries(directory):
    """
    Walks the given directory, finds all files ending in .graphql,
    and returns a list of (filename, query_string) tuples.
    """
    pattern = os.path.join(directory, "*.graphql")
    file_paths = sorted(glob.glob(pattern))
    queries = []
    for path in file_paths:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        # just use the basename (e.g. "GenePageMeta.graphql") as an identifier
        filename = os.path.basename(path)
        queries.append((filename, content))
    return queries


# Pre‐load the queries once
ALL_QUERIES = load_all_graphql_queries(QUERIES_DIR)


@pytest.mark.parametrize("filename, query_string", ALL_QUERIES)
def test_each_graphql_file_returns_no_errors(filename, query_string):
    """
    For each .graphql file, post the string as a GraphQL request
    and assert that there are no errors in the response JSON.
    """
    client = TestClient(APP)

    # Build the GraphQL payload
    payload = {"query": query_string}

    response = client.post("/", json=payload)
    data = response.json()

    # First, make sure we got a 200
    assert response.status_code == 200, (
        f"{filename} returned HTTP {response.status_code} "
        f"instead of 200. Full response: {data}"
    )

    # Next, assert there is no "errors" key (or that it’s empty).
    assert not data.get("errors"), (
        f"{filename} returned errors:\n"
        f"{json.dumps(data.get('errors', []), indent=2)}"
    )
