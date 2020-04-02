
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

from ariadne.asgi import GraphQL
import ariadne
from common.utils import load_config
import common.mongo as mongo
import os
from graphql_service.resolver.gene_model import query, gene, transcript, locus
from graphql_service.resolver.data_loaders import DataLoaderCollection

config = load_config(os.environ['GQL_CONF'])
schema_file = config.get('MONGO DB','schema')

mongo_object = mongo.mongo_db_thing(config)


schema_data = ariadne.load_schema_from_path(schema_file)

schema = ariadne.make_executable_schema(
    schema_data,
    query,
    gene,
    transcript,
    locus
)

# Initialise all data loaders
data_loader = DataLoaderCollection(mongo_object.collection())


def context_function(request):
    """
    Inject a pre-configured DB client into the request context for
    static resolvers to find.
    Friends don't let friends write static methods that are supposed
    to talk to databases
    """
    return {
        'request': request,
        'mongo_db': mongo_object.collection(),
        'data_loader': data_loader
    }


app = GraphQL(schema, debug=True, context_value=context_function)
