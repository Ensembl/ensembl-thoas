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

import os

from ariadne.asgi import GraphQL
from common.utils import load_config
from common.crossrefs import XrefResolver
import common.mongo as mongo
from graphql_service.ariadne_app import prepare_executable_schema, prepare_context_provider
from graphql_service.resolver.data_loaders import DataLoaderCollection

print(os.environ)

CONFIG = load_config(os.getenv('GQL_CONF'))

MONGO_CLIENT = mongo.MongoDbClient(CONFIG)

EXECUTABLE_SCHEMA = prepare_executable_schema()

# Initialise all data loaders
DATA_LOADER = DataLoaderCollection(MONGO_CLIENT.collection())

RESOLVER = XrefResolver(mapping_file='docs/xref_LOD_mapping.json')

CONTEXT_PROVIDER = prepare_context_provider({
    'mongo_db': MONGO_CLIENT.collection(),
    'data_loader': DATA_LOADER,
    'XrefResolver': RESOLVER
})

APP = GraphQL(EXECUTABLE_SCHEMA, debug=True, context_value=CONTEXT_PROVIDER)
