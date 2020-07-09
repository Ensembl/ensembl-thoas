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
import pymongo

from common.utils import load_config, parse_args
from common.mongo import MongoDbClient


def load_genome_info(mongo_client, source_file):
    '''
    Load assembly, species and organism information from a JSON file
    and create a new collection to put them in. Run before load_genes.py
    '''
    with open(source_file) as file:
        content = next(file)
        doc = json.loads(content)

        mongo_client.collection().insert_one({
            'type': 'Assembly',
            'default': True,
            'id': doc['assembly']['name'],
            'name': doc['assembly']['default'],
            'accession_id': doc['assembly']['accession'],
            'accessioning_body': 'EGA',
            'species': doc['organism']['name']
        })

        mongo_client.collection().insert_one({
            'type': 'Species',
            'id': doc['organism']['name'],
            'scientific_name': doc['organism']['scientific_name'],
            'taxon_id': doc['organism']['species_taxonomy_id']
        })

        # "Genome" (name to be used quietly), represents the sum of related
        # information that people will want to use together. It allows users
        # remember less between interactions, and ask shorter queries
        mongo_client.collection().insert_one({
            'type': 'Genome',
            'id': doc['organism']['name'] + '_' + doc['assembly']['accession'].replace('.', '_'),
            'name': doc['assembly']['default'],
            'assembly': doc['assembly']['name'],
            'species': doc['organism']['name'],
        })


def create_index(mongo_client):
    '''
    Add indexes to MongoDB
    '''
    mongo_client.collection().create_index([
        ('type', pymongo.ASCENDING), ('id', pymongo.ASCENDING), ('default', pymongo.ASCENDING)
    ], name='assemblies')
    mongo_client.collection().create_index([
        ('scientific_name', pymongo.ASCENDING)
    ], name='species_by_name')
    mongo_client.collection().create_index([
        ('taxon_id', pymongo.ASCENDING)
    ], name='species_by_taxon')


if __name__ == '__main__':

    ARGS = parse_args()

    MONGO_CLIENT = MongoDbClient(load_config(ARGS.config_file))

    if ARGS.collection:
        JSON_FILE = ARGS.data_path + ARGS.collection + '/' + ARGS.species + '/' + ARGS.species + '/' + ARGS.assembly + '_genome.json'
    else:
        JSON_FILE = ARGS.data_path + ARGS.species + '/' + ARGS.species + '/'+ ARGS.assembly + '_genome.json'

    load_genome_info(MONGO_CLIENT, JSON_FILE)
    create_index(MONGO_CLIENT)
