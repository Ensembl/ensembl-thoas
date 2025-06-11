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
from typing import Optional, List, Dict, Callable
from typing import AsyncIterator, TypedDict
from starlette.requests import Request

from ariadne.asgi import GraphQL
from ariadne.asgi.handlers import GraphQLHTTPHandler
from ariadne.contrib.tracing.apollotracing import ApolloTracingExtension
from ariadne.explorer import ExplorerGraphiQL, render_template, escape_default_query
from ariadne.explorer.template import read_template
from ariadne.types import ExtensionList
from pymongo import monitoring
from starlette import applications, middleware
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.errors import ServerErrorMiddleware
from starlette.middleware.gzip import GZipMiddleware

from dotenv import load_dotenv
from starlette.routing import Route

from ariadne.contrib.tracing.opentelemetry import OpenTelemetryExtension

from common import crossrefs, db, extensions, utils, logger
from grpc_service import grpc_model
from graphql_service.ariadne_app import (
    prepare_executable_schema,
)

import contextlib

from starlette.applications import Starlette

# from starlette.requests import Request
# from starlette.responses import PlainTextResponse
# from starlette.routing import Route
from common.db import MongoDbClient

from opentelemetry import trace

# from opentelemetry.instrumentation.requests import RequestsInstrumentor
# # from opentelemetry.instrumentation.pymongo import PymongoInstrumentor
from opentelemetry.instrumentation.starlette import StarletteInstrumentor
# from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

load_dotenv("connections.conf")

DEBUG_MODE = os.getenv("DEBUG_MODE", "false").lower() == "true"
ENABLE_INTROSPECTION = os.getenv("ENABLE_INTROSPECTION", "true").lower() == "true"

EXTENSIONS: Optional[ExtensionList] = (
    None  # mypy will throw an incompatible type error without this type cast
)

# Including the execution time in the response
EXTENSIONS = [
    extensions.QueryExecutionTimeExtension,
    OpenTelemetryExtension
]

if DEBUG_MODE:
    log = logging.getLogger()
    log.setLevel(logging.DEBUG)
    logging.basicConfig(level=logging.DEBUG)

    monitoring.register(logger.CommandLogger(log))

    # Apollo Tracing extension will display information about which resolvers are used and their duration
    # https://ariadnegraphql.org/docs/apollo-tracing
    EXTENSIONS.append(ApolloTracingExtension)


utils.check_config_validity(os.environ)
# MONGO_DB_CLIENT = db.MongoDbClient(os.environ)

GRPC_SERVER = db.GRPCServiceClient(os.environ)
GRPC_STUB = GRPC_SERVER.get_grpc_stub()
GRPC_REFLECTOR = GRPC_SERVER.get_grpc_reflector()
GRPC_MODEL = grpc_model.GRPC_MODEL(GRPC_STUB, GRPC_REFLECTOR)

EXECUTABLE_SCHEMA = prepare_executable_schema()

RESOLVER = crossrefs.XrefResolver(internal_mapping_file="docs/xref_LOD_mapping.json")


def prepare_context_provider(context: Dict) -> Callable[[Request], Dict]:
    """
    Returns function for injecting context to graphql executors.

    context: The context objects that we want to inject to the graphql
    executors.  The `context_provider` method is a closure, so the
    `context` variable will be the same Python object for every request.
    This means that it should only contain objects that we want to share
    between requests, for example Mongo client, XrefResolver
    """

    async def context_provider(request: Request) -> Dict:
        mongo_db_client = request.state.db_client
        await mongo_db_client
        """We must return a new object with every request,
        otherwise the requests will pollute each other's state"""
        #        mongo_db_client = context["mongo_db_client"]
        xref_resolver = context["XrefResolver"]
        grpc_model = context["grpc_model"]
        return {
            "request": request,
            "mongo_db_client": mongo_db_client,
            "XrefResolver": xref_resolver,
            "grpc_model": grpc_model,
        }

    return context_provider


CONTEXT_PROVIDER = prepare_context_provider(
    {
        "XrefResolver": RESOLVER,
        "grpc_model": GRPC_MODEL,
    }
)

starlette_middleware: List[Middleware] = [
    # Enables Cross-Origin Resource Sharing (CORS) for all origins and allows GET and POST methods.
    Middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["GET", "POST"]),
    # Compresses responses using gzip if they are at least 1000 bytes.
    # The 'minimum_size' parameter sets the smallest response size (in bytes) that will be gzipped.
    Middleware(GZipMiddleware, minimum_size=1000),
    # Handles uncaught exceptions and, if debug is False, returns a friendly error page instead of a traceback.
    Middleware(ServerErrorMiddleware, debug=DEBUG_MODE),
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


class State(TypedDict):
    db_client: MongoDbClient


@contextlib.asynccontextmanager
async def lifespan(app: Starlette) -> AsyncIterator[State]:
    async with MongoDbClient(os.environ) as client:
        print("Lifespan start")
        yield {"db_client": client}
        print("Lifespan end")


# async def homepage(request: Request) -> PlainTextResponse:
#    client = request.state.http_client
#    response = await client.get("https://www.example.com")
#    return PlainTextResponse(response.text)

# TRACER
trace.set_tracer_provider(
    TracerProvider(resource=Resource.create({SERVICE_NAME: "thoas-local-dev"}))
)

tracer = trace.get_tracer(__name__)

otlp_exporter = OTLPSpanExporter()

otlp_span_processor = BatchSpanProcessor(otlp_exporter)

# Create a BatchSpanProcessor and add the exporter to it
# span_processor = BatchSpanProcessor(jaeger_exporter, max_export_batch_size=10)
console_processor = BatchSpanProcessor(ConsoleSpanExporter())
# provider.add_span_processor(processor)
# provider.add_span_processor(span_processor)
# add to the tracer
# trace.get_tracer_provider().add_span_processor(span_processor)
# trace.get_tracer_provider().add_span_processor(console_processor)
trace.get_tracer_provider().add_span_processor(otlp_span_processor)

APP = applications.Starlette(
    debug=DEBUG_MODE, middleware=starlette_middleware, lifespan=lifespan
)
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
        introspection=ENABLE_INTROSPECTION,
    ),
)

StarletteInstrumentor.instrument_app(APP)
