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

from collections import defaultdict
from typing import List, Dict

from aiodataloader import DataLoader
from pymongo.collection import Collection


class BatchLoaders:
    """A collection of bulk data aggregators for "joins" in GraphQL"""

    def __init__(self, mongo_client):
        self.mongo_client = mongo_client
        self.transcript_loader = DataLoader(batch_load_fn=self.batch_transcript_load)
        self.product_loader = DataLoader(batch_load_fn=self.batch_product_load)
        self.region_loader = DataLoader(batch_load_fn=self.batch_region_load)

    async def batch_transcript_load(self, keys: List[str]) -> List[List]:
        """
        Load many transcripts to satisfy a bunch of `await`s
        DataLoader will aggregate many single ID requests into 'keys' so we can
        perform bulk fetches
        """
        query = {
            "type": "Transcript",
            "gene_foreign_key": {"$in": sorted(keys)},
        }

        data = await self.query_mongo(query)
        return self.collate_dataloader_output("gene_foreign_key", keys, data)

    async def batch_product_load(self, keys: List[str]) -> List[List]:
        """
        Load a bunch of products/proteins by ID
        """
        query = {
            "type": "Protein",
            "product_primary_key": {"$in": keys},
        }
        data = await self.query_mongo(query)
        return self.collate_dataloader_output("product_primary_key", keys, data)

    async def batch_region_load(self, keys: List[str]) -> List[List]:
        query = {"type": "Region", "region_id": {"$in": keys}}
        data = await self.query_mongo(query)
        return self.collate_dataloader_output("region_id", keys, data)

    @staticmethod
    def collate_dataloader_output(
        foreign_key: str, original_ids: List[str], docs: List[Dict]
    ) -> List[List]:
        """
        Query identifier values are in no particular order and so are the query
        results. We must collect them together and return them in the order
        initially requested for graphql to unite the results with the async routines
        that requested them.

        The return value is therefore a list of lists ordered by the original foreign key
        values, created by building a dictionary of 1..n documents keyed by foreign key and
        selecting out dict items by the original foreign_key list.
        """

        grouped_docs = defaultdict(list)
        for doc in docs:
            grouped_docs[doc[foreign_key]].append(doc)

        return [grouped_docs[fk] for fk in original_ids]

    async def query_mongo(self, query: Dict) -> List[Dict]:
        """
        Query function that exists solely to satisfy the vagaries of Python async.
        batch_transcript_load expects a list of results, and *must* call a single
        function in order to be valid.
        """
        return list(self.mongo_client.find(query))
