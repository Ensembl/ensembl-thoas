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
import graphql_service.resolver.gene_model as model
import pytest
import graphql_service.resolver.data_loaders as data_loader
import asyncio
from common.crossrefs import xref_resolver


class Info(object):
    """
    Proxy for the Info objects produced by graphql
    """

    def __init__(self, collection):
        self.collection = collection
        self.context = {
            'stuff': 'Nonsense',
            'mongo_db': self.collection,
            'data_loader': data_loader.DataLoaderCollection(self.collection),
            'xref_resolver': xref_resolver(from_file='common/tests/mini_identifiers.json')
        }


@pytest.fixture
def basic_data():
    collection = mongomock.MongoClient().db.collection
    collection.insert_many([
        {'genome_id': 1, 'type': 'Gene', 'name': 'banana', 'stable_id': 'ENSG001'},
        {'genome_id': 1, 'type': 'Gene', 'name': 'durian', 'stable_id': 'ENSG002'},
    ])
    return Info(collection)


@pytest.fixture
def transcript_data():
    collection = mongomock.MongoClient().db.collection
    collection.insert_many([
        {'genome_id': 1, 'type': 'Transcript', 'name': 'kumquat', 'stable_id': 'ENST001', 'gene': 'ENSG001'},
        {'genome_id': 1, 'type': 'Transcript', 'name': 'grape', 'stable_id': 'ENST002', 'gene': 'ENSG001'},
        {'genome_id': 1, 'type': 'Gene', 'name': 'banana', 'stable_id': 'ENSG001'}
    ])
    return Info(collection)


@pytest.fixture
def slice_data():
    collection = mongomock.MongoClient().db.collection
    collection.insert_many([
        {
            'genome_id': 1,
            'type': 'Gene',
            'name': 'banana',
            'stable_id': 'ENSG001',
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
            'stable_id': 'ENSG002',
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

    result = model.resolve_gene(
        None,
        basic_data,
        bySymbol={'symbol': 'banana', 'genome_id': 1}
    )
    assert result['name'] == 'banana'

    result = model.resolve_gene(
        None,
        basic_data,
        bySymbol={'symbol': 'very not here', 'genome_id': 1}
    )

    assert not result

    result = model.resolve_gene(
        None,
        basic_data,
        byId={'stable_id': 'ENSG001', 'genome_id': 1}
    )

    assert result['name'] == 'banana'

    result = model.resolve_gene(
        None,
        basic_data,
        byId={'stable_id': 'ENSG999', 'genome_id': 1}
    )

    assert not result


def test_resolve_genes(basic_data):

    result = model.resolve_genes(None, basic_data, genome_id=1)

    for hit in result:
        assert hit['type'] == 'Gene'
        assert hit['name'] == 'banana' or hit['name'] == 'durian'


def test_resolve_transcripts(transcript_data):

    result = model.resolve_transcripts(None, transcript_data, genome_id=1)
    for hit in result:
        assert hit['type'] == 'Transcript'
        assert hit['name'] == 'kumquat' or hit['name'] == 'grape'


def test_resolve_transcript(transcript_data):

    result = model.resolve_transcript(
        None,
        transcript_data,
        byId={'stable_id': 'ENST001', 'genome_id': 1}
    )

    assert result['name'] == 'kumquat'
    assert result['stable_id'] == 'ENST001'

    result = model.resolve_transcript(
        None,
        transcript_data,
        byId={'stable_id': 'FAKEYFAKEYFAKEY', 'genome_id': 1}
    )
    assert not result


def test_resolve_gene_transcripts(transcript_data):

    result = model.resolve_gene_transcripts(
        {'stable_id': 'ENSG001', 'genome_id': 1},
        transcript_data
    )
    data = asyncio.get_event_loop().run_until_complete(result)

    for hit in data:
        assert hit['type'] == 'Transcript'
        assert hit['name'] in ['kumquat', 'grape']


def test_resolve_slice(slice_data):

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
    assert hit['stable_id'] == 'ENSG001'

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
        assert hit['stable_id'] in ['ENSG001', 'ENSG002']


def test_url_generation(basic_data):
    xref = {
        'id': 'some_molecule',
        'name': 'Chemsitry rocks',
        'description': 'Chemistry is the best',
        'source': {
            'id': 'ChEBI',
            'name': 'Chemical Entities of Biological Interest'
        }
    }

    result = model.insert_urls(
        {
            'cross_references': [
                xref
            ]
        },
        basic_data
    )

    for key in xref.keys():
        assert result[0][key] == xref[key], 'Original structure retained'

    assert result[0]['url'] == 'https://www.ebi.ac.uk/chebi/searchId.do?chebiId=CHEBI:some_molecule'
    assert result[0]['source']['url'] == 'https://www.ebi.ac.uk/chebi/'
