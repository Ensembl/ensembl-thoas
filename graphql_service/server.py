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
from ariadne.contrib.tracing.apollotracing import ApolloTracingExtension
from ariadne.types import ExtensionList
from pymongo import monitoring
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware

from common.logger import CommandLogger
from common.utils import load_config
from common.crossrefs import XrefResolver
from common import mongo
from graphql_service.ariadne_app import prepare_executable_schema, prepare_context_provider

print(os.environ)

CONFIG = load_config(os.getenv('GQL_CONF'))

DEBUG_MODE = True
EXTENSIONS: Optional[ExtensionList] = None  # mypy will throw an incompatible type error without this type cast

if DEBUG_MODE:
    # This will write MongoDB transactions to `thoas.log`
    log = logging.getLogger()
    log.setLevel(logging.DEBUG)
    logging.basicConfig(level=logging.DEBUG, filename='thoas.log', filemode='w')

    monitoring.register(CommandLogger(log))

    # Apollo Tracing extension will display information about which resolvers are used and their duration
    # https://ariadnegraphql.org/docs/apollo-tracing
    # To see it in the GraphQL playground, make sure you have `"tracing.hideTracingResponse": false` in the playground
    # settings
    EXTENSIONS = [ApolloTracingExtension]

MONGO_CLIENT = mongo.MongoDbClient(CONFIG)

EXECUTABLE_SCHEMA = prepare_executable_schema()

RESOLVER = XrefResolver(internal_mapping_file='docs/xref_LOD_mapping.json')

CONTEXT_PROVIDER = prepare_context_provider({
    'mongo_db': MONGO_CLIENT.collection(),
    'XrefResolver': RESOLVER,
})

starlette_middleware = [
    Middleware(CORSMiddleware, allow_origins=['*'], allow_methods=['GET', 'POST'])
]

APP = Starlette(debug=True, middleware=starlette_middleware)
APP.mount("/", GraphQL(EXECUTABLE_SCHEMA, debug=True, context_value=CONTEXT_PROVIDER, extensions=EXTENSIONS))
