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
from typing import Any, Optional

from ariadne.asgi import GraphQL
from ariadne.contrib.tracing.apollotracing import ApolloTracingExtension
from ariadne.types import Extension, Resolver, ContextValue
from graphql import GraphQLResolveInfo
from pymongo import monitoring
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware

from common.utils import load_config
from common.crossrefs import XrefResolver
from common import mongo
from graphql_service.ariadne_app import prepare_executable_schema, prepare_context_provider
from graphql_service.resolver.data_loaders import DataLoaderCollection

print(os.environ)

CONFIG = load_config(os.getenv('GQL_CONF'))

log = logging.getLogger()
log.setLevel(logging.DEBUG)
logging.basicConfig(level=logging.DEBUG, filename='thoas.log', filemode='w')


class CommandLogger(monitoring.CommandListener):

    def started(self, event):
        log.debug("Command {0.command_name} with request id "
                 "{0.request_id} started on server "
                 "{0.connection_id}".format(event))

        if event.command_name == "find":
            log.debug(f"The filter for command with {event.request_id} is {event.command['filter']}")

    def succeeded(self, event):
        log.debug("Command {0.command_name} with request id "
                 "{0.request_id} on server {0.connection_id} "
                 "succeeded in {0.duration_micros} "
                 "microseconds".format(event))

    def failed(self, event):
        log.debug("Command {0.command_name} with request id "
                 "{0.request_id} on server {0.connection_id} "
                 "failed in {0.duration_micros} "
                 "microseconds".format(event))


monitoring.register(CommandLogger())

MONGO_CLIENT = mongo.MongoDbClient(CONFIG)

EXECUTABLE_SCHEMA = prepare_executable_schema()

# Initialise all data loaders
DATA_LOADER = DataLoaderCollection(MONGO_CLIENT.collection())

LOADERS = {
    'products': DATA_LOADER.transcript_product_dataloader("homo_sapiens_GCA_000001405_28"),
    'regions': DATA_LOADER.slice_region_dataloader("homo_sapiens_GCA_000001405_28")
}

RESOLVER = XrefResolver(internal_mapping_file='docs/xref_LOD_mapping.json')

CONTEXT_PROVIDER = prepare_context_provider({
    'mongo_db': MONGO_CLIENT.collection(),
    'data_loader': DATA_LOADER,
    'XrefResolver': RESOLVER,
    'query_count': 0,
    'mongo_time': 0.0,
    'loaders': LOADERS
})


class MongoQueryTimeExecutionExtension(Extension):

    def request_finished(self, context: ContextValue):
        context["query_count"] = 0
        context["mongo_time"] = 0.0

    def format(self, context: ContextValue) -> Optional[dict]:
        return {
            "query_count": context["query_count"],
            "mongo_time": context["mongo_time"]
        }


starlette_middleware = [
    Middleware(CORSMiddleware, allow_origins=['*'], allow_methods=['GET', 'POST'])
]

APP = Starlette(debug=True, middleware=starlette_middleware)
APP.mount("/", GraphQL(EXECUTABLE_SCHEMA, debug=True, context_value=CONTEXT_PROVIDER, extensions=[MongoQueryTimeExecutionExtension, ApolloTracingExtension]))
