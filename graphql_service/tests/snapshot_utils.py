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
from common.crossrefs import XrefResolver

from graphql_service.ariadne_app import prepare_executable_schema
from graphql_service.resolver.data_loaders import BatchLoaders
from graphql_service.tests.fixtures.human_brca2 import (
    build_gene,
    build_transcripts,
    build_products,
    build_region,
    build_assembly,
    build_organism,
    build_species,
)
from graphql_service.tests.fixtures.wheat import build_wheat_genes
from common.db import FakeMongoDbClient


def prepare_mongo_instance():
    mongo_client = FakeMongoDbClient()
    database = mongo_client.mongo_db
    collection1 = database.create_collection('uuid_to_collection_mapping')
    collection1.insert_many(
        [
            {
                "uuid": "homo_sapiens_GCA_000001405_28",
                "collection": "collection2",
                "is_current": True,
                "load_date": "2023-06-29T17:00:41.510Z"
            },
            {
                "uuid": "triticum_aestivum_GCA_900519105_1",
                "collection": "collection2",
                "is_current": True,
                "load_date": "2023-06-29T17:00:41.736Z"
            }
        ]
    )

    collection2 = database.create_collection('collection2')
    collection2.insert_one(build_gene())
    collection2.insert_many(build_transcripts())
    collection2.insert_many(build_products())
    collection2.insert_one(build_region())
    collection2.insert_one(build_assembly())
    collection2.insert_one(build_organism())
    collection2.insert_one(build_species())
    collection2.insert_many(build_wheat_genes())

    return mongo_client


def prepare_context_provider(mongo_client, xref):

    # Dataloader should be bound to every request.
    # mongo_client and xrefs are created only once but
    # loaders is created for every request as this inner function closure
    # is assigned to context_value which gets evaluated at the beginning
    # of every request.
    def context_provider():
        context = {
            "mongo_db_client": mongo_client,
            "XrefResolver": xref,
            "loaders": BatchLoaders()
        }
        return context
    return context_provider

def setup_test():
    """
    Run setup scripts once per module
    This is the one to use in other modules
    """
    executable_schema = prepare_executable_schema()

    mongo_client = prepare_mongo_instance()
    xref = XrefResolver(internal_mapping_file="docs/xref_LOD_mapping.json")
    context = prepare_context_provider(mongo_client, xref)

    return executable_schema, context
