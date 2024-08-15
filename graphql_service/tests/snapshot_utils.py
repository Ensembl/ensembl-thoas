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
    gene_coll = database.create_collection("gene")
    gene_coll.insert_one(build_gene())
    transcript_coll = database.create_collection("transcript")
    transcript_coll.insert_many(build_transcripts())
    protein_coll = database.create_collection("protein")
    protein_coll.insert_many(build_products())
    region_coll = database.create_collection("region")
    region_coll.insert_one(build_region())
    assembly_coll = database.create_collection("assembly")
    assembly_coll.insert_one(build_assembly())
    organism_coll = database.create_collection("organism")
    organism_coll.insert_one(build_organism())
    species_coll = database.create_collection("species")
    species_coll.insert_one(build_species())
    # wheat_gene_coll = database.create_collection('gene')
    gene_coll.insert_many(build_wheat_genes())

    return mongo_client


def prepare_context_provider(mongo_client, xref, grpc_model):

    # Dataloader should be bound to every request.
    # mongo_client and xrefs are created only once but
    # loaders is created for every request as this inner function closure
    # is assigned to context_value which gets evaluated at the beginning
    # of every request.
    def context_provider():
        context = {
            "mongo_db_client": mongo_client,
            "XrefResolver": xref,
            "grpc_model": grpc_model,
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
    grpc_model = "fake_grpc_model"  # TODO: find a way to test/mock gRPC
    context = prepare_context_provider(mongo_client, xref, grpc_model)

    return executable_schema, context
