import mongomock

from graphql_service.resolver.data_loaders import DataLoaderCollection


def test_gene_transcript_dataloader():
    """
    Test that the dataloader correctly caches and queries in bulk
    """
    collection = mongomock.MongoClient().db.collection
    collection.insert_many([
        {'type': 'Transcript', 'gene': 'ENSG001'},
        {'type': 'Transcript', 'gene': 'ENSG001'},
        {'type': 'Transcript', 'gene': 'ENSG002'},
        {'type': 'Transcript', 'gene': 'ENSG002'},
        {'type': 'Transcript', 'gene': 'ENSG002'},
    ])

    loaders = DataLoaderCollection(collection)
    gt_loader = loaders.gene_transcript_dataloader(max_batch_size=1)

    # Test effective 0 batch size
    docs = gt_loader.load(key='ENSG001')

    assert len(docs) == 2

    # Test large batch size
    gt_loader = loaders.gene_transcript_dataloader(max_batch_size=1000)
    docs = gt_loader.load(key='ENSG002')
    assert len(docs) == 3

    # Test bad request
    docs = gt_loader.load(key='ENSG999')
