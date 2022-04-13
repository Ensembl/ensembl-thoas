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
from unittest.mock import Mock

import mongomock
import requests
from starlette.datastructures import State

from common.crossrefs import XrefResolver

from graphql_service.ariadne_app import prepare_executable_schema
from graphql_service.tests.fixtures.human_brca2 import build_gene, build_transcripts, build_products, build_region, \
    build_assembly
from graphql_service.tests.fixtures.wheat import build_wheat_genes

def prepare_db():
    'Fill a mock database with data and provide a collection accessor'

    mocked_mongo_collection = mongomock.MongoClient().db.collection
    try:
        xref_resolver = XrefResolver(internal_mapping_file='docs/xref_LOD_mapping.json')
    except requests.exceptions.ConnectionError:
        print('No network available, tests will fail')
        xref_resolver = None

    request_mock = Mock()
    request_mock.state = State()
    context = {
        'mongo_db': mocked_mongo_collection,
        'XrefResolver': xref_resolver,
        'request': request_mock
    }

    mocked_mongo_collection.insert_one(build_gene())
    mocked_mongo_collection.insert_many(build_transcripts())
    mocked_mongo_collection.insert_many(build_products())
    mocked_mongo_collection.insert_one(build_region())
    mocked_mongo_collection.insert_one(build_assembly())
    mocked_mongo_collection.insert_many(build_wheat_genes())
    return context


def setup_test():
    '''
    Run setup scripts once per module
    This is the one to use in other modules
    '''
    context = prepare_db()
    executable_schema = prepare_executable_schema()
    return executable_schema, context
