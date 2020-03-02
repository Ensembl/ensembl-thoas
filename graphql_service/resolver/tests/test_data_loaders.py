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
import asyncio
from resolver.data_loaders import DataLoaderCollection


def test_batch_transcript_load():
    """
    Try the batch loader outside of the async event process
    """

    collection = mongomock.MongoClient().db.collection
    collection.insert_many([
        {'genome_id': 1, 'type': 'Transcript', 'gene': 'ENSG001'},
        {'genome_id': 1, 'type': 'Transcript', 'gene': 'ENSG001'},
        {'genome_id': 1, 'type': 'Transcript', 'gene': 'ENSG002'},
        {'genome_id': 1, 'type': 'Transcript', 'gene': 'ENSG002'},
        {'genome_id': 1, 'type': 'Transcript', 'gene': 'ENSG002'},
    ])

    loader = DataLoaderCollection(collection)
    # This is normally set by calling gene_transcript_dataloader()
    loader.genome_id = 1

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
