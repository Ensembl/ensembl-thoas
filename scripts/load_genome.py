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

import json
import gzip
from common.utils import load_config
from common.mongo import mongo_db_thing


def load_genome_info(db):
    with gzip.open('../human_genome.json.gz') as file:
        content = next(file)
        doc = json.loads(content)

        db.collection().insert_one({
            'type': 'assembly',
            'default': True,
            'id': doc['assembly']['name'],
            'name': doc['assembly']['default'],
            'accession_id': doc['assembly']['accession'],
            'accessioning_body': 'EGA',
            'species': doc['organism']['name']
        })

        db.collection().insert_one({
            'type': 'species',
            'id': doc['organism']['name'],
            'scientific_name': doc['organism']['scientific_name'],
            'taxon_id': doc['organism']['species_taxonomy_id']
        })


if __name__ == '__main__':
    db = mongo_db_thing(load_config('../mongo.conf'))
    load_genome_info(db)
