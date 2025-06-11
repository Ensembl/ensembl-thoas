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

import logging
from collections import defaultdict
from typing import List, Dict, Optional, Tuple

from aiodataloader import DataLoader
from common.db import MongoDbClient
import pickle

logger = logging.getLogger(__name__)


class BatchLoaders:
    """A collection of bulk data aggregators for "joins" in GraphQL"""

    def __init__(self, database_conn, mongo_client: MongoDbClient):
        self.database_conn = database_conn
        self.mongo_client = mongo_client

        self.gene_loader = DataLoader(batch_load_fn=self.batch_gene_load)
        self.transcript_loader = DataLoader(
            batch_load_fn=self.batch_transcript_by_gene_load
        )
        self.product_loader = DataLoader(batch_load_fn=self.batch_product_load)
        self.region_loader = DataLoader(batch_load_fn=self.batch_region_load)
        self.region_by_assembly_loader = DataLoader(
            batch_load_fn=self.batch_region_by_assembly_load
        )
        self.organism_loader = DataLoader(batch_load_fn=self.batch_organism_load)
        self.assembly_by_organism_loader = DataLoader(
            batch_load_fn=self.batch_assembly_by_organism_load
        )
        self.species_loader = DataLoader(batch_load_fn=self.batch_species_load)
        self.organism_by_species_loader = DataLoader(
            batch_load_fn=self.batch_organism_by_species_load
        )

    async def batch_gene_load(self, keys: Tuple[str, str]) -> List[Optional[Dict]]:
        print(f"^^^^^^^^ keys ---> {keys}")
        query = {
            "type": "Gene",
            "$or": [
                {"stable_id": keys[0][1]},
                {"unversioned_stable_id": keys[0][1]},
            ],
            "genome_id": keys[0][0],
        }
        print(f"^^^^^^^^ query ---> {query}")

        data = await self.query_mongo(query=query, doc_type="gene")
        print(f" **** data: {data}")
        return data

    async def batch_transcript_by_gene_load(self, keys: List[str]) -> List[List]:
        """
        Load many transcripts to satisfy a bunch of `await`s
        DataLoader will aggregate many single ID requests into 'keys' so we can
        perform bulk fetches
        """
        query = {
            "type": "Transcript",
            "gene_foreign_key": {"$in": sorted(keys)},
        }

        data = await self.query_mongo(query=query, doc_type="transcript")
        return self.collate_dataloader_output("gene_foreign_key", keys, data)

    async def batch_product_load(self, keys: List[str]) -> List[List]:
        """
        Load a bunch of products/proteins by ID
        """
        query = {
            "type": "Protein",
            "product_primary_key": {"$in": sorted(keys)},
        }
        data = await self.query_mongo(query=query, doc_type="protein")
        return self.collate_dataloader_output("product_primary_key", keys, data)

    async def batch_region_load(self, keys: List[str]) -> List[List]:
        query = {"type": "Region", "region_id": {"$in": sorted(keys)}}
        data = await self.query_mongo(query=query, doc_type="region")
        return self.collate_dataloader_output("region_id", keys, data)

    async def batch_region_by_assembly_load(self, keys: List[str]) -> List[List]:
        query = {"type": "Region", "assembly_id": {"$in": sorted(keys)}}
        data = await self.query_mongo(query=query, doc_type="region")
        return self.collate_dataloader_output("assembly_id", keys, data)

    async def batch_organism_load(self, keys: List[str]) -> List[List]:
        query = {"type": "Organism", "organism_primary_key": {"$in": sorted(keys)}}
        data = await self.query_mongo(query=query, doc_type="organism")
        return self.collate_dataloader_output("organism_primary_key", keys, data)

    async def batch_assembly_by_organism_load(self, keys: List[str]) -> List[List]:
        query = {"type": "Assembly", "organism_foreign_key": {"$in": sorted(keys)}}
        data = await self.query_mongo(query=query, doc_type="assembly")
        return self.collate_dataloader_output("organism_foreign_key", keys, data)

    async def batch_species_load(self, keys: List[str]) -> List[List]:
        query = {"type": "Species", "species_primary_key": {"$in": sorted(keys)}}
        data = await self.query_mongo(query=query, doc_type="species")
        return self.collate_dataloader_output("species_primary_key", keys, data)

    async def batch_organism_by_species_load(self, keys: List[str]) -> List[List]:
        query = {"type": "Organism", "species_foreign_key": {"$in": sorted(keys)}}
        data = await self.query_mongo(query=query, doc_type="organism")
        return self.collate_dataloader_output("species_foreign_key", keys, data)

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

    async def query_mongo(self, query: Dict, doc_type) -> List[Dict]:
        """
        Query function that exists solely to satisfy the vagaries of Python async.
        batch_transcript_load expects a list of results, and *must* call a single
        function in order to be valid.
        """

        # The mongo db connection also gives access to the redis cache
        # connection
        if self.mongo_client.redis_cache_enabled:
            cache = self.mongo_client.cache

            # We use pickle to get a binary representation of the query object.
            # Then we prepend doc_type and use this as a key
            query_bin = pickle.dumps(query)
            doc_type_bin = (doc_type + ":").encode("utf-8")
            key = doc_type_bin + query_bin

            # If we find the key, we return the associated result.
            # If not, we fall through
            data = cache.get(key)

            if data is not None:
                logger.debug("Found cache entry for key: %s", key)
                # We recreate the object for the result
                return pickle.loads(data)

            logger.debug(f"No cache entry found for key: %s", key)

        db = self.database_conn[doc_type]
        assert db is not None

        # the collection name is the doc_type
        logger.info(
            "Getting '%s' from DB: '%s', collection '%s'",
            doc_type,
            self.database_conn.name,
            doc_type,
        )

        # We need to fetch the full result because batch_transcript_load expects
        # this, but also since we may want to cache it
        cursor = db.find(query)
        result = await cursor.to_list()

        if self.mongo_client.redis_cache_enabled:
            logger.debug(f"Storing result for key: %s", key)

            # The result is a list of documents. We use pickle to serialize this
            cache.set(key, pickle.dumps(result), ex=self.mongo_client.redis_expiry)

        return result
