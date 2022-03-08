import json

from mongoengine import connect, disconnect

from scripts.load_genome import load_genome_info
from scripts.mongoengine_documents.genome import Assembly, Species, Genome


def test_load_genome_info():
    connect('mongoenginetest', host='mongomock://localhost')
    load_genome_info('plasmodium_falciparum_genome.json')

    assembly_json = json.loads(Assembly.objects.to_json())
    species_json = json.loads(Species.objects.to_json())
    genome_json = json.loads(Genome.objects.to_json())
    assert len(assembly_json) == len(species_json) == len(genome_json) == 1

    # No need to test for ids
    del assembly_json[0]['_id']
    del species_json[0]['_id']
    del genome_json[0]['_id']

    assert assembly_json == [{"_cls": "ThoasDocument.Assembly",
                              "type": "Assembly",
                              "default": True,
                              "assembly_id": "ASM276v2",
                              "name": "ASM276v2",
                              "accession_id": "GCA_000002765.2",
                              "accessioning_body": "EGA",
                              "species": "plasmodium_falciparum"}]

    assert species_json == [{'_cls': 'ThoasDocument.Species',
                             'scientific_name': 'Plasmodium falciparum 3D7',
                             'species_id': 'plasmodium_falciparum',
                             'taxon_id': 5833,
                             'type': 'Species'}]

    assert genome_json == [{'_cls': 'ThoasDocument.Genome',
                            'assembly': 'ASM276v2',
                            'genome_id': 'plasmodium_falciparum_GCA_000002765_2',
                            'name': 'ASM276v2',
                            'species': 'plasmodium_falciparum',
                            'type': 'Genome'}]

    # TODO test for create_indices?

    disconnect()
