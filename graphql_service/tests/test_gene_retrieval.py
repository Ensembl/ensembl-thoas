"""
   See the NOTICE file distributed with this work for additional information
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

import pytest
import mongomock
from ariadne import graphql

from common.crossrefs import XrefResolver
from graphql_service.ariadne_app import prepare_executable_schema
from graphql_service.resolver.data_loaders import DataLoaderCollection
from graphql_service.tests.fixtures.human_brca2 import build_gene, build_transcripts

mocked_mongo_collection = mongomock.MongoClient().db.collection
data_loader = DataLoaderCollection(mocked_mongo_collection)
xref_resolver = XrefResolver(mapping_file='docs/xref_LOD_mapping.json')

executable_schema = prepare_executable_schema()
context = {
    'mongo_db': mocked_mongo_collection,
    'data_loader': data_loader,
    'XrefResolver': xref_resolver
}

def prepare_db():
    'Fill mock database with data'
    transcripts = build_transcripts()
    gene = build_gene()
    mocked_mongo_collection.insert_one(gene)
    for transcript in transcripts:
        mocked_mongo_collection.insert_one(transcript)
    # mocked_mongo_collection.insert_many(transcripts)

def setup_module():
    'Run setup scripts once per module'
    prepare_db()

@pytest.mark.asyncio
async def test_gene_retrieval_by_id(snapshot):
    'Test retrieval of a gene from the grapqhl api by id'
    query = """{
      gene(byId: { genome_id: "homo_sapiens_GCA_000001405_28", stable_id: "ENSG00000139618.15" }) {
        name
        description
        stable_id
        unversioned_stable_id
        version
        so_term
        transcripts {
          stable_id
        }
        slice {
          region {
            name
            strand {
              code
            }
          }
          location {
            start
            end
          }
        }
      }
    }"""

    query_data = {'query': query}
    (success, result) = await graphql(executable_schema, query_data, context_value=context)
    assert success
    snapshot.assert_match(result['data'])

@pytest.mark.asyncio
async def test_gene_retrieval_by_symbol(snapshot):
    'Test retrieval of a gene from the graphql api by its symbol'
    query = """{
      gene(bySymbol: { genome_id: "homo_sapiens_GCA_000001405_28", symbol: "BRCA2" }) {
        name
        stable_id
      }
    }"""
    query_data = {'query': query}
    (success, result) = await graphql(executable_schema, query_data, context_value=context)
    assert success
    snapshot.assert_match(result['data'])
