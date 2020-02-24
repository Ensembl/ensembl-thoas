import mongomock
import graphql_service.resolver.gene_model as model
import pytest
import graphql_service.resolver.data_loaders as data_loader
import asyncio


class Info(object):
    """
    Proxy for the Info objects produced by graphql
    """

    def __init__(self, collection):
        self.collection = collection
        self.context = {
            "stuff": "Nonsense",
            "mongo_db": self.collection,
            "data_loader": data_loader.DataLoaderCollection(self.collection)
        }


@pytest.fixture
def basic_data():
    collection = mongomock.MongoClient().db.collection
    collection.insert_many([
        {'type': 'Gene', 'name': 'banana', 'stable_id': 'ENSG001'},
        {'type': 'Gene', 'name': 'durian', 'stable_id': 'ENSG002'},
    ])
    return Info(collection)


@pytest.fixture
def transcript_data():
    collection = mongomock.MongoClient().db.collection
    collection.insert_many([
        {'type': 'Transcript', 'name': 'kumquat', 'stable_id': 'ENST001', 'gene': 'ENSG001'},
        {'type': 'Transcript', 'name': 'grape', 'stable_id': 'ENST002', 'gene': 'ENSG001'},
        {'type': 'Gene', 'name': 'banana', 'stable_id': 'ENSG001'}
    ])
    return Info(collection)


@pytest.fixture
def slice_data():
    collection = mongomock.MongoClient().db.collection
    collection.insert_many([
        {
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
        name='banana'
    )
    assert result["name"] == 'banana'

    result = model.resolve_gene(
        None,
        basic_data,
        name='very not here'
    )

    assert not result

    result = model.resolve_gene(
        None,
        basic_data,
        stable_id='ENSG001'
    )

    assert result["name"] == "banana"

    result = model.resolve_gene(
        None,
        basic_data,
        stable_id='ENSG99999'
    )

    assert not result


def test_resolve_genes(basic_data):

    result = model.resolve_genes(None, basic_data)

    for hit in result:
        assert hit["type"] == 'Gene'
        assert hit["name"] == 'banana' or hit["name"] == 'durian'


def test_resolve_transcripts(transcript_data):

    result = model.resolve_transcripts(None, transcript_data)
    for hit in result:
        assert hit["type"] == 'Transcript'
        assert hit["name"] == 'kumquat' or hit["name"] == 'grape'


def test_resolve_transcript(transcript_data):

    result = model.resolve_transcript(None, transcript_data, 'ENST001')

    assert result["name"] == 'kumquat'
    assert result["stable_id"] == 'ENST001'

    result = model.resolve_transcript(None, transcript_data, 'HUH?')
    assert not result


def test_resolve_gene_transcripts(transcript_data):

    result = model.resolve_gene_transcripts({"stable_id": "ENSG001"}, transcript_data)
    data = asyncio.get_event_loop().run_until_complete(result)

    for hit in data:
        assert hit["type"] == 'Transcript'
        assert hit["name"] in ['kumquat', 'grape']


def test_resolve_slice(slice_data):

    result = model.resolve_slice(None, slice_data, 'chr1', 10, 11, 'Gene')
    assert result

    result = model.resolve_slice(None, slice_data, 'chr1', 5, 105, 'Gene')
    for hit in result:
        assert hit["stable_id"] == 'ENSG001'

    result = model.resolve_slice(None, slice_data, 'chr1', 5, 205, 'Gene')
    for hit in result:
        assert hit["stable_id"] in ['ENSG001', 'ENSG002']


def test_locus_resolver():

    result = model.resolve_feature_slice({'type': 'herb'})
    assert result == 'herb'
