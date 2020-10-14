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
from aiodataloader import DataLoader


class DataLoaderCollection():
    """
    A collection of bulk data aggregators for "joins" in GraphQL
    They're part of a class so they can be initialised in one go
    outside of the static methods they will be called in.

    Can't currently support multiple genome_ids in the same query.
    Limitations in the DataLoader design as stateless function
    with fixed arguments mean we can't inject genome_id on calling
    .load(). Needs a better solution, or better sandboxing of
    data loaders.
    """

    def __init__(self, db_collection):
        'Accepts a MongoDB collection object to provide data'
        self.collection = db_collection
        self.genome_id = None

    async def batch_transcript_load(self, keys):
        '''
        Load many transcripts to satisfy a bunch of `await`s
        DataLoader will aggregate many single ID requests into 'keys' so we can
        perform bulk fetches
        '''
        query = {
            'type': 'Transcript',
            'genome_id': self.genome_id,
            'gene': {
                '$in': sorted(keys)
            }
        }

        data = await self.query_mongo(query)
        return self.collate_dataloader_output('gene', keys, data)

    async def batch_product_load(self, keys):
        '''
        Load a bunch of products/proteins by ID
        '''
        query = {
            'type': 'Protein',
            'genome_id': self.genome_id,
            'stable_id': {
                '$in': keys
            }
        }
        data = await self.query_mongo(query)
        return self.collate_dataloader_output('stable_id', keys, data)

    @staticmethod
    def collate_dataloader_output(foreign_key, original_ids, docs):
        '''
        Query identifier values are in no particular order and so are the query
        results. We must collect them together and return them in the order
        initially requested for graphql to unite the results with the async routines
        that requested them.

        The return value is therefore a list of lists ordered by the original foreign key
        values, created by building a dictionary of 1..n documents keyed by foreign key and
        selecting out dict items by the original foreign_key list.
        '''

        grouped_docs = defaultdict(list)
        for doc in docs:
            grouped_docs[doc[foreign_key]].append(doc)

        return [grouped_docs[fk] for fk in original_ids]


    def gene_transcript_dataloader(self, genome_id, max_batch_size=1000):
        'Factory for DataLoaders for Transcripts fetched via Genes'
        # How do we get temporary state into class methods with a fixed signature?
        # I didn't want to fork DataLoader in order to add arbitrary arguments
        # There is a danger of cross-contamination here if genome_id changes in
        # the same thread, but I'm not sure how to do this better.
        self.genome_id = genome_id
        return DataLoader(
            batch_load_fn=self.batch_transcript_load,
            max_batch_size=max_batch_size
        )

    def transcript_product_dataloader(self, genome_id, max_batch_size=1000):
        'Factory for DataLoaders for Products fetched via Transcripts'

        self.genome_id = genome_id
        return DataLoader(
            batch_load_fn=self.batch_product_load,
            max_batch_size=max_batch_size
        )

    async def query_mongo(self, query):
        '''
        Query function that exists solely to satisfy the vagueries of Python async.
        batch_transcript_load expects a list of results, and *must* call a single
        function in order to be valid.
        '''
        return list(self.collection.find(query))
