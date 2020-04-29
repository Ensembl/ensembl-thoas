'''
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
'''

import json
from common.utils import load_config, parse_args
from common.mongo import mongo_db_thing


def load_genome_info(db, source_file):
    with open(source_file) as file:
        content = next(file)
        doc = json.loads(content)

        db.collection().insert_one({
            'type': 'Assembly',
            'default': True,
            'id': doc['assembly']['name'],
            'name': doc['assembly']['default'],
            'accession_id': doc['assembly']['accession'],
            'accessioning_body': 'EGA',
            'species': doc['organism']['name']
        })

        db.collection().insert_one({
            'type': 'Species',
            'id': doc['organism']['name'],
            'scientific_name': doc['organism']['scientific_name'],
            'taxon_id': doc['organism']['species_taxonomy_id']
        })

        # "Genome" (name to be used quietly), represents the sum of related
        # information that people will want to use together. It allows users
        # remember less between interactions, and ask shorter queries
        db.collection().insert_one({
            'type': 'Genome',
            'id': doc['organism']['name'] + '_' + doc['assembly']['accession'].replace('.', '_'),
            'name': 'GRCh38',
            'assembly': doc['assembly']['name'],
            'species': doc['organism']['name'],
        })


def create_index(db):
    db.collection().create_index([
        ('type'), ('id'), ('default')
    ], name='assemblies')
    db.collection().create_index([
        ('scientific_name')
    ], name='species_by_name')
    db.collection().create_index([
        ('taxon_id')
    ], name='species_by_taxon')


if __name__ == '__main__':

    args = parse_args()

    db = mongo_db_thing(load_config(args.config_file))
    json_file = args.data_path + args.species + '/' + args.species + '_genome.json'

    load_genome_info(db, json_file)
    create_index(db)
