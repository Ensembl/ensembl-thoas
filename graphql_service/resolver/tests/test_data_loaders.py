import mongomock
import asyncio
from graphql_service.resolver.data_loaders import DataLoaderCollection


def test_batch_transcript_load():
    """
    Try the batch loader outside of the async event process
    """

    collection = mongomock.MongoClient().db.collection
    collection.insert_many([
        {'type': 'Transcript', 'gene': 'ENSG001'},
        {'type': 'Transcript', 'gene': 'ENSG001'},
        {'type': 'Transcript', 'gene': 'ENSG002'},
        {'type': 'Transcript', 'gene': 'ENSG002'},
        {'type': 'Transcript', 'gene': 'ENSG002'},
    ])

    loader = DataLoaderCollection(collection)
    response = loader.batch_transcript_load(
        ['ENSG001']
    )
    data = asyncio.get_event_loop().run_until_complete(response)

    assert len(data) == 1
    assert len(data[0]) == 2

    response = loader.batch_transcript_load(
        ['ENSG001', 'ENSG002']
    )
    data = asyncio.get_event_loop().run_until_complete(response)

    # This broadly proves that data emerges in lists ordered
    # by the input IDs
    assert len(data) == 2
    assert len(data[0]) == 2
    assert len(data[1]) == 3
    assert data[1][0]["gene"] == "ENSG002"

    # Try for absent data
    response = loader.batch_transcript_load(
        ['nonsense']
    )
    data = asyncio.get_event_loop().run_until_complete(response)

    # No results in the structure that is returned
    assert not data[0]
