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
import pytest
from graphql_service.resolver.data_loaders import BatchLoaders


@pytest.mark.asyncio
async def test_batch_transcript_load():
    """
    Try the batch loader outside of the async event process
    """

    collection = mongomock.MongoClient().db.collection
    collection.insert_many(
        [
            {
                "genome_id": "1",
                "type": "Transcript",
                "gene": "ENSG001.1",
                "gene_foreign_key": "1_ENSG001.1",
            },
            {
                "genome_id": "1",
                "type": "Transcript",
                "gene": "ENSG001.1",
                "gene_foreign_key": "1_ENSG001.1",
            },
            {
                "genome_id": "1",
                "type": "Transcript",
                "gene": "ENSG002.2",
                "gene_foreign_key": "1_ENSG002.2",
            },
            {
                "genome_id": "1",
                "type": "Transcript",
                "gene": "ENSG002.2",
                "gene_foreign_key": "1_ENSG002.2",
            },
            {
                "genome_id": "1",
                "type": "Transcript",
                "gene": "ENSG002.2",
                "gene_foreign_key": "1_ENSG002.2",
            },
        ]
    )

    loaders = BatchLoaders(collection)

    response = await loaders.batch_transcript_load(["1_ENSG001.1"])

    assert len(response) == 1
    # There are two hits that match the one requested ID
    assert len(response[0]) == 2

    response = await loaders.batch_transcript_load(["1_ENSG001.1", "1_ENSG002.2"])
    # This broadly proves that data emerges in lists ordered
    # by the input IDs
    assert len(response) == 2
    assert len(response[0]) == 2
    assert len(response[1]) == 3
    assert response[1][0]["gene"] == "ENSG002.2"

    # Try for absent data
    response = await loaders.batch_transcript_load(["nonsense"])

    # No results in the structure that is returned
    assert not response[0]


@pytest.mark.asyncio
async def test_batch_product_load():
    """
    Batch load some test products
    """

    collection = mongomock.MongoClient().db.collection
    collection.insert_many(
        [
            {
                "genome_id": "1",
                "type": "Protein",
                "stable_id": "ENSP001.1",
                "product_primary_key": "1_ENSP001.1",
            },
            {
                "genome_id": "1",
                "type": "Protein",
                "stable_id": "ENSP002.1",
                "product_primary_key": "1_ENSP002.1",
            },
        ]
    )

    loader = BatchLoaders(collection)

    response = await loader.batch_product_load(["1_ENSP001.1"])

    assert response[0][0]["stable_id"] == "ENSP001.1"
