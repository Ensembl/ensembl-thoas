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

config = load_config(os.getenv('GQL_CONF'))

mongo_client = mongo.MongoDbClient(config)

executable_schema = prepare_executable_schema()

# Initialise all data loaders
data_loader = DataLoaderCollection(mongo_client.collection())

resolver = XrefResolver(mapping_file='docs/xref_LOD_mapping.json')

context_provider = prepare_context_provider({
    'mongo_db': mongo_client.collection(),
    'data_loader': data_loader,
    'XrefResolver': resolver
})

app = GraphQL(executable_schema, debug=True, context_value=context_provider)
