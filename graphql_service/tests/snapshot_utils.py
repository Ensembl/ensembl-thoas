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

import mongomock
import requests
from common.crossrefs import XrefResolver

from graphql_service.ariadne_app import prepare_executable_schema
from graphql_service.resolver.data_loaders import DataLoaderCollection
from graphql_service.tests.fixtures.human_brca2 import build_gene, build_transcripts, build_products, build_region, \
    build_assembly
from graphql_service.tests.fixtures.wheat import build_with_no_xref_acc_id, build_with_no_xref_description, \
    build_with_no_externaldb_source_id, build_with_no_externaldb_source_name

def prepare_db():
    'Fill a mock database with data and provide a collection accessor'

    mocked_mongo_collection = mongomock.MongoClient().db.collection
    data_loader = DataLoaderCollection(mocked_mongo_collection)
    try:
        xref_resolver = XrefResolver(internal_mapping_file='docs/xref_LOD_mapping.json')
    except requests.exceptions.ConnectionError:
        print('No network available, tests will fail')
        xref_resolver = None

    context = {
        'mongo_db': mocked_mongo_collection,
        'data_loader': data_loader,
        'XrefResolver': xref_resolver
    }

    mocked_mongo_collection.insert_one(build_gene())
    mocked_mongo_collection.insert_many(build_transcripts())
    mocked_mongo_collection.insert_many(build_products())
    mocked_mongo_collection.insert_one(build_region())
    mocked_mongo_collection.insert_one(build_assembly())
    mocked_mongo_collection.insert_one(build_with_no_xref_acc_id())
    mocked_mongo_collection.insert_one(build_with_no_xref_description())
    mocked_mongo_collection.insert_one(build_with_no_externaldb_source_id())
    mocked_mongo_collection.insert_one(build_with_no_externaldb_source_name())
    return context


def setup_test():
    '''
    Run setup scripts once per module
    This is the one to use in other modules
    '''
    context = prepare_db()
    executable_schema = prepare_executable_schema()
    return executable_schema, context
