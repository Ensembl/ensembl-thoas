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
import logging
import os
from typing import Optional

from ariadne.asgi import GraphQL
from ariadne.asgi.handlers import GraphQLHTTPHandler
from ariadne.contrib.tracing.apollotracing import ApolloTracingExtension
from ariadne.explorer import ExplorerGraphiQL, render_template, escape_default_query
from ariadne.explorer.template import read_template
from ariadne.types import ExtensionList
from pymongo import monitoring
from starlette import applications, middleware
from starlette.middleware.cors import CORSMiddleware

from dotenv import load_dotenv
from common import crossrefs, db, extensions, utils, logger
from grpc_service import grpc_model
from graphql_service.ariadne_app import (
    prepare_executable_schema,
    prepare_context_provider,
)


load_dotenv("connections.conf")

DEBUG_MODE = os.getenv("DEBUG_MODE", False) == "True"
EXTENSIONS: Optional[
    ExtensionList
] = None  # mypy will throw an incompatible type error without this type cast

# Including the execution time in the response
EXTENSIONS = [extensions.QueryExecutionTimeExtension]

if DEBUG_MODE:
    log = logging.getLogger()
    log.setLevel(logging.DEBUG)
    logging.basicConfig(level=logging.DEBUG)

    monitoring.register(logger.CommandLogger(log))

    # Apollo Tracing extension will display information about which resolvers are used and their duration
    # https://ariadnegraphql.org/docs/apollo-tracing
    EXTENSIONS.append(ApolloTracingExtension)


utils.check_config_validity(os.environ)
MONGO_DB_CLIENT = db.MongoDbClient(os.environ)

GRPC_SERVER = db.GRPCServiceClient(os.environ)
GRPC_STUB = GRPC_SERVER.get_grpc_stub()
GRPC_MODEL = grpc_model.GRPC_MODEL(GRPC_STUB)

EXECUTABLE_SCHEMA = prepare_executable_schema()

RESOLVER = crossrefs.XrefResolver(internal_mapping_file="docs/xref_LOD_mapping.json")

CONTEXT_PROVIDER = prepare_context_provider(
    {
        "mongo_db_client": MONGO_DB_CLIENT,
        "XrefResolver": RESOLVER,
        "grpc_model": GRPC_MODEL,
    }
)

starlette_middleware = [
    middleware.Middleware(
        CORSMiddleware, allow_origins=["*"], allow_methods=["GET", "POST"]
    )
]

# The original HTML file can be found under
# [venv]/ariadne/explorer/templates/graphiql.html
CUSTOM_GRAPHIQL_HTML = read_template(
    os.path.dirname(os.path.realpath(__file__)) + "/templates/custom_graphiql.html"
)

DEFAULT_QUERY = """
#
# Welcome to Ensembl Core GraphQL API!
#
# This is an in-browser tool for writing, validating, and testing GraphQL queries.
#
# Type queries on the left side of the screen, and you'll see intelligent typeaheads
# aware of the current GraphQL type schema. Live syntax and validation errors
# are highlighted as you type.
#
# GraphQL queries typically start with a "{" character. Lines starting with "#" are comments.
#
# Here's an example query:
#
# {
#   field(arg: "value") {
#     subField
#   }
# }
#
# In the example below, we've named the query "ENSG00000139618", which is optional.
#
# Keyboard shortcuts:
#
#   Prettify query: Shift + Ctrl + P (or press the prettify button)
#   Merge fragments: Shift + Ctrl + M (or press the merge button)
#   Run Query: Ctrl + Enter (or press the play button)
#   Auto Complete: Ctrl + Space (or just start typing)
#
# Try running the query below to fetch gene information:
#
query ENSG00000139618 {
  gene(
    by_id: {genome_id: "a7335667-93e7-11ec-a39d-005056b38ce3", stable_id: "ENSG00000139618"}
  ) {
    alternative_symbols
    name
    so_term
    stable_id
    transcripts {
      stable_id
      symbol
    }
  }
}

# Feel free to modify the query or add new ones to explore other data!
"""


class CustomExplorerGraphiQL(ExplorerGraphiQL):
    """
    We can customize the GraphiQL interface in Ariadne by overriding the ExplorerGraphiQL class
    which is responsible for rendering the default GraphiQL UI
    """

    def __init__(
        self,
        title: str = "Ensembl Core API",
        explorer_plugin: bool = True,
        default_query: str = DEFAULT_QUERY,
    ):
        super().__init__()
        self.parsed_html = render_template(
            CUSTOM_GRAPHIQL_HTML,
            {
                "title": title,
                "enable_explorer_plugin": explorer_plugin,
                "default_query": escape_default_query(default_query),
            },
        )


APP = applications.Starlette(debug=DEBUG_MODE, middleware=starlette_middleware)
APP.mount(
    "/",
    GraphQL(
        EXECUTABLE_SCHEMA,
        debug=DEBUG_MODE,
        context_value=CONTEXT_PROVIDER,
        http_handler=GraphQLHTTPHandler(
            extensions=EXTENSIONS,
        ),
        explorer=CustomExplorerGraphiQL(),
    ),
)
