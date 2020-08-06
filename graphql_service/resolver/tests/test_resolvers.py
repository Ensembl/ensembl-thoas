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

import asyncio
import pytest
import mongomock
from graphql import GraphQLError

import graphql_service.resolver.gene_model as model
import graphql_service.resolver.data_loaders as data_loader
from common.crossrefs import XrefResolver


class Info():
    '''
    Proxy for the Info objects produced by graphql
    '''

    def __init__(self, collection):
        self.collection = collection
        self.context = {
            'stuff': 'Nonsense',
            'mongo_db': self.collection,
            'data_loader': data_loader.DataLoaderCollection(self.collection),
            'XrefResolver': XrefResolver(from_file='common/tests/mini_identifiers.json')
        }


@pytest.fixture(name='basic_data')
def fixture_basic_data():
    'Some fake genes'
    collection = mongomock.MongoClient().db.collection
    collection.insert_many([
        {'genome_id': 1, 'type': 'Gene', 'name': 'banana', 'stable_id': 'ENSG001.1', 'unversioned_stable_id': 'ENSG001'},
        {'genome_id': 1, 'type': 'Gene', 'name': 'durian', 'stable_id': 'ENSG002.2', 'unversioned_stable_id': 'ENSG002'},
    ])
    return Info(collection)


@pytest.fixture(name='transcript_data')
def fixture_transcript_data():
    'Some fake transcripts'
    collection = mongomock.MongoClient().db.collection
    collection.insert_many([
        {'genome_id': 1, 'type': 'Transcript', 'name': 'kumquat', 'stable_id': 'ENST001.1', 'unversioned_stable_id': 'ENST001', 'gene': 'ENSG001.1'},
        {'genome_id': 1, 'type': 'Transcript', 'name': 'grape', 'stable_id': 'ENST002.2', 'unversioned_stable_id': 'ENST002', 'gene': 'ENSG001.1'},
        {'genome_id': 1, 'type': 'Gene', 'name': 'banana', 'stable_id': 'ENSG001.1', 'unversioned_stable_id': 'ENSG001'}
    ])
    return Info(collection)


@pytest.fixture(name='slice_data')
def fixture_slice_data():
    '''
    Test genes with slices
    '''
    collection = mongomock.MongoClient().db.collection
    collection.insert_many([
        {
            'genome_id': 1,
            'type': 'Gene',
            'name': 'banana',
            'stable_id': 'ENSG001.1',
            'unversioned_stable_id': 'ENSG001',
            'slice': {
                'region': {
                    'name': 'chr1'
                },
                'location': {
                    'start': 10,
                    'end': 100
                }
            }
        },
        {
            'genome_id': 1,
            'type': 'Gene',
            'name': 'durian',
            'stable_id': 'ENSG002.2',
            'unversioned_stable_id': 'ENSG002',
            'slice': {
                'region': {
                    'name': 'chr1'
                },
                'location': {
                    'start': 110,
                    'end': 200
                }
            }
        }
    ])
    return Info(collection)


def test_resolve_gene(basic_data):
    'Test the querying of Mongo by gene symbol'
    result = model.resolve_gene(
        None,
        basic_data,
        bySymbol={'symbol': 'banana', 'genome_id': 1}
    )
    assert result['name'] == 'banana'
    result = None

    with pytest.raises(GraphQLError) as graphql_error:
        result = model.resolve_gene(
            None,
            basic_data,
            bySymbol={'symbol': 'very not here', 'genome_id': 1}
        )
    assert not result
    assert graphql_error.value.extensions['code'] == 'GENE_NOT_FOUND'
    graphql_error = None

    result = model.resolve_gene(
        None,
        basic_data,
        byId={'stable_id': 'ENSG001.1', 'genome_id': 1}
    )

    assert result['name'] == 'banana'
    result = None

    with pytest.raises(GraphQLError) as graphql_error:
        result = model.resolve_gene(
            None,
            basic_data,
            byId={'stable_id': 'BROKEN BROKEN BROKEN', 'genome_id': 1}
        )
    assert not result
    assert graphql_error.value.extensions['code'] == 'GENE_NOT_FOUND'
    graphql_error = None

    # Check unversioned query resolves as well
    result = model.resolve_gene(
        None,
        basic_data,
        byId={'stable_id': 'ENSG001', 'genome_id': 1}
    )

    assert result['name'] == 'banana'


def test_resolve_transcript(transcript_data):
    'Test fetching of transcripts by stable ID'
    result = model.resolve_transcript(
        None,
        transcript_data,
        byId={'stable_id': 'ENST001.1', 'genome_id': 1}
    )

    assert result['name'] == 'kumquat'
    assert result['stable_id'] == 'ENST001.1'

    result = model.resolve_transcript(
        None,
        transcript_data,
        byId={'stable_id': 'FAKEYFAKEYFAKEY', 'genome_id': 1}
    )
    assert not result


def test_resolve_gene_transcripts(transcript_data):
    'Check the DataLoader for transcripts is working via gene'
    result = model.resolve_gene_transcripts(
        {'stable_id': 'ENSG001.1', 'genome_id': 1},
        transcript_data
    )
    data = asyncio.get_event_loop().run_until_complete(result)

    for hit in data:
        assert hit['type'] == 'Transcript'
        assert hit['name'] in ['kumquat', 'grape']


def test_resolve_slice(slice_data):
    'Check features can be found via coordinates'
    result = model.resolve_slice(
        None,
        slice_data,
        genome_id=1,
        region='chr1',
        start=10,
        end=11,
    )
    assert not result

    context = slice_data.context
    result = model.query_region(
        {
            'slice.genome_id': 1,
            'slice.region.name': 'chr1',
            'slice.location.start': 1,
            'slice.location.end': 120,
            'mongo_db': context["mongo_db"]
        },
        'Gene'
    )
    hit = result.next()
    assert hit['stable_id'] == 'ENSG001.1'

    result = model.query_region(
        {
            'slice.genome_id': 1,
            'slice.region.name': 'chr1',
            'slice.location.start': 5,
            'slice.location.end': 205,
            'mongo_db': context["mongo_db"]
        },
        'Gene'
    )
    for hit in result:
        assert hit['stable_id'] in ['ENSG001.1', 'ENSG002.2']


def test_url_generation(basic_data):
    'Check URLs are attached to cross references'
    xref = {
        'id': 'some_molecule',
        'name': 'Chemsitry rocks',
        'description': 'Chemistry is the best',
        'source': {
            'id': 'ChEBI',
            'name': 'Chemical Entities of Biological Interest'
        }
    }

    result = model.insert_crossref_urls(
        {
            'cross_references': [
                xref
            ]
        },
        basic_data
    )

    for key, value in xref.items():
        assert result[0][key] == value, 'Original structure retained'

    assert result[0]['url'] == 'https://www.ebi.ac.uk/chebi/searchId.do?chebiId=CHEBI:some_molecule'
    assert result[0]['source']['url'] == 'https://www.ebi.ac.uk/chebi/'
