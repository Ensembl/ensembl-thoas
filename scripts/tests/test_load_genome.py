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

import os

from mongoengine import connect, disconnect

from scripts.load_genome import load_genome_info
from scripts.mongoengine_documents.genome import Assembly, Species, Genome


def test_load_genome_info():
    connect('mongoenginetest', host='mongomock://localhost')
    path_to_parent_dir = os.path.dirname(os.path.realpath(__file__))
    load_genome_info(os.path.join(path_to_parent_dir, "plasmodium_falciparum_genome.json"))

    assert Assembly.objects.count() == Species.objects.count() == Genome.objects.count() == 1
    assembly_json = Assembly.objects[0].to_mongo()
    species_json = Species.objects[0].to_mongo()
    genome_json = Genome.objects[0].to_mongo()

    # id assignment is handled by mongoengine
    del assembly_json['_id']
    del species_json['_id']
    del genome_json['_id']

    assert assembly_json == {"_cls": "ThoasDocument.Assembly",
                             "type": "Assembly",
                             "default": True,
                             "assembly_id": "ASM276v2",
                             "name": "ASM276v2",
                             "accession_id": "GCA_000002765.2",
                             "accessioning_body": "EGA",
                             "species": "plasmodium_falciparum"}

    assert species_json == {'_cls': 'ThoasDocument.Species',
                            'scientific_name': 'Plasmodium falciparum 3D7',
                            'species_id': 'plasmodium_falciparum',
                            'taxon_id': 5833,
                            'type': 'Species'}

    assert genome_json == {'_cls': 'ThoasDocument.Genome',
                           'assembly': 'ASM276v2',
                           'genome_id': 'plasmodium_falciparum_GCA_000002765_2',
                           'name': 'ASM276v2',
                           'species': 'plasmodium_falciparum',
                           'type': 'Genome'}

    disconnect()
