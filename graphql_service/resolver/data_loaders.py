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

from aiodataloader import DataLoader
from collections import defaultdict


class DataLoaderCollection(object):
    """
    A collection of bulk data aggregators for "joins" in GraphQL
    They're part of a class so they can be initialised in one go
    outside of the static methods they will be called in
    """

    def __init__(self, db_collection):
        'Accepts a MongoDB collection object to provide data'
        self.collection = db_collection

    async def batch_transcript_load(self, keys):

        # DataLoader will aggregate many single ID requests into 'keys'
        query = {
            'type': 'Transcript',
            'genome_id': self.genome_id,
            'gene': {
                '$in': sorted(keys)
            }
        }

        data = await self.query_mongo(query)
        # Now the results must be returned in the order requested by 'keys'
        # Unpack the bulk query results into a list of lists
        grouped_docs = defaultdict(list)

        for doc in data:
            grouped_docs[doc['gene']].append(doc)

        return [grouped_docs[feature_id] for feature_id in keys]

    def gene_transcript_dataloader(self, genome_id, max_batch_size=1000):
        self.genome_id = genome_id
        return DataLoader(
            batch_load_fn=self.batch_transcript_load,
            max_batch_size=max_batch_size
        )

    async def query_mongo(self, query):
        return list(self.collection.find(query))
