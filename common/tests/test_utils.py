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

from common.utils import *
from common.mongo import FakeMongoDbClient
from common.refget_postgresql import MockRefgetDB as RefgetDB
from common.file_parser import MockChromosomeChecksum as ChromosomeChecksum


def test_stable_id():
    '''
    Ensure correct formatting depending on arguments
    '''
    assert get_stable_id(iid='Test', version=None) == 'Test'
    assert get_stable_id(iid='Test', version=10) == 'Test.10'
    assert get_stable_id(iid='Test', version='10') == 'Test.10'


def test_xref_formatting():
    '''
    Ensure that cross refs documents are appropriately converted to CDM standard
    '''
    doc_list = format_cross_refs([])

    assert len(doc_list) == 0

    doc_list = format_cross_refs([
        {
            'primary_id': 'HGNC:1101',
            'display_id': 'BRCA2',
            'description': 'BRCA2 DNA repair associated',
            'db_display': 'HGNC symbol',
            'dbname': 'HGNC',
            'info_type': 'DIRECT',
            'info_text': 'stuff'
        }
    ])

    first_result = doc_list[0]
    assert first_result['accession_id'] == 'HGNC:1101'
    assert first_result['name'] == 'BRCA2'
    assert first_result['description'] == 'BRCA2 DNA repair associated'
    assert first_result['source']['name'] == 'HGNC symbol'
    assert first_result['source']['id'] == 'HGNC'
    assert first_result['assignment_method']['type'] == 'DIRECT'
    # Note that assignment_method description is inferred on the fly and cannot be tested
    # without the full resolver chain

    doc_list = format_cross_refs([
        {
            'primary_id': 'GO:0098781',
            'display_id': 'ncRNA transcription',
            'description': 'The transcription of non (protein) coding RNA from a DNA template. Source: GOC:dos',
            'dbname': 'NOTGO',
            'info_type': 'PROJECTION',
            'info_text': 'Projected from homo_sapiens'
        }
    ])
    assert doc_list[0]['accession_id'] == 'GO:0098781'
    assert doc_list[0]['source']['name'] == 'NOTGO'
    assert doc_list[0]['source']['id'] == 'NOTGO'

    doc_list = format_cross_refs([
        {
            'primary_id': 'GO:0098781',
            'display_id': 'ncRNA transcription',
            'description': 'The transcription of non (protein) coding RNA from a DNA template. Source: GOC:dos',
            'dbname': 'GO',
            'info_type': 'PROJECTION',
            'info_text': 'Projected from homo_sapiens'
        }
    ])

    assert len(doc_list) == 0


def test_slice_formatting():
    '''
    Ensure slices are correctly generated from parameters
    '''
    slice_dict = format_slice('test_name', 'test_code', True, 1, 100, 200, 'test_genome')

    assert slice_dict['region_id'] == 'test_genome_test_name_test_code'
    assert slice_dict['strand']['code'] == 'forward'
    assert slice_dict['strand']['value'] == 1
    assert slice_dict['location']['start'] == 100
    assert slice_dict['location']['end'] == 200
    assert slice_dict
    assert slice_dict['default'] is True

    slice_dict = format_slice('test_name', 'test_code', False, -1, 100, 200, 'test_genome')

    assert slice_dict['region_id'] == 'test_genome_test_name_test_code'
    assert slice_dict['strand']['code'] == 'reverse'
    assert slice_dict['strand']['value'] == -1
    assert slice_dict['location']['start'] == 100
    assert slice_dict['location']['end'] == 200
    assert slice_dict['default'] is False


def test_format_region():
    '''
    Ensure that regions are correctly created from the gene
    '''
    test_mysql_result = {
        'seq_region_id': 559,
        'length': 4641652,
        'name': 'test_name',
        'code': 'chromosome',
        'circularity': '1',
        'species_name': 'test_species',
        'accession_id': 'GCA_000005845.2'
    }

    genome_id = get_genome_id(test_mysql_result['species_name'], test_mysql_result['accession_id'])
    chromosome_checksums = ChromosomeChecksum(genome_id, '/test_path/')
    region = format_region(test_mysql_result, "test_assembly_id", genome_id, chromosome_checksums)


    assert region == {
        "type": "Region",
        "region_id": "test_species_GCA_000005845_2_test_name_chromosome",
        "name": "test_name",
        "assembly_id": "test_assembly_id",
        "code": "chromosome",
        "length": 4641652,
        "topology": "circular",
        "sequence": {
            "alphabet": {
                "accession_id": "test_dna_accession_id",
                "value": "test",
                "label": "test",
                "definition": "Test - IUPAC notation for dna sequence",
                "description": None
            },
            "checksum": "3t6fit96jy015frnh465do005hd885jtki"
        },
        "metadata": {
            "ontology_terms": [
                {
                    "accession_id": "SO:0000340",
                    "value": "chromosome",
                    "url": "www.sequenceontology.org/browser/current_release/term/SO:0000340",
                    "source": {
                        "name": "Sequence Ontology",
                        "url": "www.sequenceontology.org",
                        "description": "The Sequence Ontology is a set of terms and relationships used to describe the features and attributes of biological sequence. "
                    }
                }
            ]
        }
    }


def test_exon_formatting():
    '''
    Verify exon structure from input variables
    '''
    exon = format_exon(
        exon={
            'id': 'ENSE123',
            'version': 1,
            'start': 100,
            'end': 200,
        },
        region_name='chr1',
        region_code='test_code',
        region_strand=1,
        default_region=True,
        genome_id='test_genome'
    )

    assert exon['type'] == 'Exon'
    assert exon['stable_id'] == 'ENSE123.1'
    assert exon['unversioned_stable_id'] == 'ENSE123'
    assert exon['version'] == 1
    assert exon['slice']['region_id'] == 'test_genome_chr1_test_code'
    # forego further enumeration of slice properties


def test_phase_calculation():
    '''
    Check that phases and rank are calculated correctly for a given ordered
    list of exons.
    '''
    exon_list = [
        {'start': 1, 'end': 10, 'stable_id': 'ENSE01', 'unversioned_stable_id': 'ENSE01'},
        {'start': 21, 'end': 30, 'stable_id': 'ENSE02', 'unversioned_stable_id': 'ENSE02'}
    ]

    phase_lookup = {
        'ENST01': {
            'ENSE01': (-1, 0),
            'ENSE02': (0, -1)
        }
    }

    phased_exons = phase_exons(exon_list, 'ENST01', phase_lookup)
    for i, phased_exon in enumerate(phased_exons):
        assert phased_exon['index'] == i + 1
        stable_id = exon_list[i]['stable_id']
        assert phased_exon['exon']['stable_id'] == stable_id

        assert (
                   phased_exon['start_phase'], phased_exon['end_phase']
               ) == (
                   phase_lookup['ENST01'][stable_id]
               )


def test_splice_formatting():
    '''
    Spliced exons are exons in a wrapper containing index and relative location.
    Check the emitted format
    '''
    # truncated transcript for simplicity
    transcript = {
        'start': 1,
        'end': 30,
        'strand': 1
    }

    exon_list = [
        {
            'slice': {
                'location': {'start': 1, 'end': 10}
            },
            'stable_id': 'ENSE01',
            'unversioned_stable_id': 'ENSE01'
        },
        {
            'slice': {
                'location': {'start': 21, 'end': 30}
            },
            'stable_id': 'ENSE02',
            'unversioned_stable_id': 'ENSE02'
        }
    ]

    splicing = splicify_exons(exon_list, transcript)

    assert len(splicing) == 2
    assert splicing[0]['index'] == 1
    assert splicing[0]['exon'] == exon_list[0]
    assert splicing[0]['relative_location'] == {
        'start': 1,
        'end': 10,
        'length': 10
    }
    assert splicing[1]['index'] == 2
    assert splicing[1]['exon'] == exon_list[1]
    assert splicing[1]['relative_location'] == {
        'start': 21,
        'end': 30,
        'length': 10
    }


def test_utr_formatting():
    '''
    Verify UTRs are correctly formatted depending on up/down/reverse/forward settings
    '''

    # remember that regular start and end apply to the CDS in genomic coordinates, i.e.
    # low to high irrespective of reading frame. Relative coords are relative to the
    # parent object, in this case the transcript. It conveniently starts at 1 to make
    # data creation easier
    forward_cds = {
        'start': 2,
        'end': 10,
        'relative_start': 2,
        'relative_end': 10,
        'transcript': {
            'strand': 1,
            'start': 1,
            'end': 10
        },
        'downstream': False
    }
    utr = format_utr(
        transcript=forward_cds['transcript'],
        absolute_cds_start=forward_cds['start'],
        absolute_cds_end=forward_cds['end'],
        downstream=forward_cds['downstream']
    )

    assert utr['type'] == '5_prime_utr'
    assert utr['start'] == 1
    assert utr['end'] == 1

    forward_end_cds = {
        'start': 1,
        'end': 9,
        'relative_start': 1,
        'relative_end': 9,
        'transcript': {
            'strand': 1,
            'start': 1,
            'end': 10
        },
        'downstream': True
    }

    utr = format_utr(
        transcript=forward_end_cds['transcript'],
        absolute_cds_start=forward_end_cds['start'],
        absolute_cds_end=forward_end_cds['end'],
        downstream=forward_end_cds['downstream']
    )
    assert utr['type'] == '3_prime_utr'
    assert utr['start'] == 10
    assert utr['end'] == 10

    forward_non_utr = {
        'start': 1,
        'end': 10,
        'relative_start': 1,
        'relative_end': 10,
        'transcript': {
            'strand': 1,
            'start': 1,
            'end': 10
        },
        'downstream': False
    }

    utr = format_utr(
        transcript=forward_non_utr['transcript'],
        absolute_cds_start=forward_non_utr['start'],
        absolute_cds_end=forward_non_utr['end'],
        downstream=forward_non_utr['downstream']
    )

    assert utr is None

    utr = format_utr(
        transcript=forward_non_utr['transcript'],
        absolute_cds_start=forward_non_utr['start'],
        absolute_cds_end=forward_non_utr['end'],
        downstream=True
    )
    assert utr is None

    reverse_cds = {
        'start': 1,
        'end': 8,
        'relative_start': 1,
        'relative_end': 8,
        'transcript': {
            'strand': -1,
            'start': 1,
            'end': 10
        },
        'downstream': False
    }

    utr = format_utr(
        transcript=reverse_cds['transcript'],
        absolute_cds_start=reverse_cds['start'],
        absolute_cds_end=reverse_cds['end'],
        downstream=reverse_cds['downstream']
    )
    assert utr['type'] == '5_prime_utr'
    assert utr['start'] == 9
    assert utr['end'] == 10

    reverse_cds_downstream = {
        'start': 8,
        'end': 10,
        'relative_start': 3,
        'relative_end': 10,
        'transcript': {
            'strand': -1,
            'start': 1,
            'end': 10
        },
        'downstream': True
    }

    utr = format_utr(
        transcript=reverse_cds_downstream['transcript'],
        absolute_cds_start=reverse_cds_downstream['start'],
        absolute_cds_end=reverse_cds_downstream['end'],
        downstream=reverse_cds_downstream['downstream']
    )
    assert utr['type'] == '3_prime_utr'
    assert utr['start'] == 1
    assert utr['end'] == 7


def test_infer_introns():
    '''
    Exons are used to infer the presence of introns
    '''

    transcript = {
        'start': 10,
        'end': 100,
        'strand': 1
    }

    exons = [
        {
            'stable_id': 'ENSE01.1',
            'slice': {
                'location': {
                    'start': 10,
                    'end': 30
                },
                'region_id': "test_genome_13",
                'strand': {
                    'value': 1
                }
            }
        },
        {
            'stable_id': 'ENSE02.1',
            'slice': {
                'location': {
                    'start': 40,
                    'end': 60
                },
                'region_id': "test_genome_13",
                'strand': {
                    'value': 1
                }
            }
        },
        {
            'stable_id': 'ENSE03.1',
            'slice': {
                'location': {
                    'start': 90,
                    'end': 100
                },
                'region_id': "test_genome_13",
                'strand': {
                    'value': 1
                }
            }
        }
    ]

    introns = infer_introns(exons, transcript)
    target_introns = [
        {
            'type': 'Intron',
            'index': 1,
            'slice': {
                'region_id': "test_genome_13",
                'location': {
                    'start': 31,
                    'end': 39,
                    'length': 9
                },
                'strand': {
                    'value': 1
                }
            },
            'relative_location': {
                'start': 22,
                'end': 30,
                'length': 9
            },
            'checksum': None,
            'so_term': 'intron'
        },
        {
            'type': 'Intron',
            'index': 2,
            'slice': {
                'region_id': "test_genome_13",
                'location': {
                    'start': 61,
                    'end': 89,
                    'length': 29
                },
                'strand': {
                    'value': 1
                }
            },
            'relative_location': {
                'start': 52,
                'end': 80,
                'length': 29
            },
            'checksum': None,
            'so_term': 'intron'
        }
    ]
    assert len(introns) == len(target_introns)
    for test_intron, target_intron in zip(introns, target_introns):
        assert test_intron == target_intron

    reverse_transcript = {
        'start': 10,
        'end': 100,
        'strand': -1
    }
    reverse_exons = [
        {
            'stable_id': 'ENSE03.1',
            'slice': {
                'location': {
                    'start': 90,
                    'end': 100
                },
                'region_id': "test_genome_13",
                'strand': {
                    'value': -1
                }
            }
        },
        {
            'stable_id': 'ENSE02.1',
            'slice': {
                'location': {
                    'start': 40,
                    'end': 60
                },
                'region_id': "test_genome_13",
                'strand': {
                    'value': -1
                }
            }
        },
        {
            'stable_id': 'ENSE01.1',
            'slice': {
                'location': {
                    'start': 10,
                    'end': 30
                },
                'region_id': "test_genome_13",
                'strand': {
                    'value': -1
                }
            }
        }
    ]

    target_reverse_introns = [
        {
            'type': 'Intron',
            'index': 1,
            'slice': {
                'region_id': "test_genome_13",
                'location': {
                    'start': 61,
                    'end': 89,
                    'length': 29
                },
                'strand': {
                    'value': -1
                }
            },
            'relative_location': {
                'start': 12,
                'end': 40,
                'length': 29
            },
            'checksum': None,
            'so_term': 'intron'
        },
        {
            'type': 'Intron',
            'index': 2,
            'slice': {
                'region_id': "test_genome_13",
                'location': {
                    'start': 31,
                    'end': 39,
                    'length': 9
                },
                'strand': {
                    'value': -1
                }
            },
            'relative_location': {
                'start': 62,
                'end': 70,
                'length': 9
            },
            'checksum': None,
            'so_term': 'intron'
        }
    ]
    reverse_introns = infer_introns(reverse_exons, reverse_transcript)

    for test_intron, target_intron in zip(reverse_introns, target_reverse_introns):
        assert test_intron == target_intron



def test_cdna_formatting():
    '''
    cDNA representation
    '''
    transcript = {
    'id': 1,
    'version': 0.1,
        'start': 1,
        'end': 100,
        'exons': [
            {
                'start': 1,
                'end': 20
            },
            {
                'start': 81,
                'end': 100
            }
        ]
    }
    refget = RefgetDB()
    cdna = format_cdna(transcript,refget)
    assert cdna['start'] == 1
    assert cdna['end'] == 100
    assert cdna['relative_start'] == 1
    assert cdna['relative_end'] == 100
    assert cdna['length'] == 40


def test_protein_formatting():
    '''
    Verify protein document structure
    '''

    protein = {
        "transcript_id": "CAB89209",
        "id": "CAB89209",
        "version": 2,
        "ensembl_object_type": "translation",
        "protein_features": [
            {
                "translation_id": "CAB89209",
                "name": "PF03011",
                "description": "PFEMP",
                "start": 602,
                "end": 762,
                "score": 212.5,
                "evalue": 5.1e-63,
                "hit_start": 1,
                "hit_end": 157,
                "program": "InterProScan",
                "dbname": "Pfam",
                "program_version": "5.48-83.0",
                "dbversion": "33.1",
                "interpro_ac": "IPR004258",
                "interpro_name": "DBL",
                "interpro_description": "Duffy-binding-like domain",
                "ensembl_object_type": "protein_feature"
            }
        ],
        "xrefs": [
            {
                "primary_id": "Q9NFB6",
                "display_id": "Q9NFB6",
                "dbname": "Uniprot/SPTREMBL",
                "db_display": "UniProtKB/TrEMBL",
                "description": None,
                "info_type": "null",
                "info_text": ""
            }
        ]
    }

    refget = RefgetDB()
    result = format_protein(
        protein=protein,
        genome_id='tralalala',
        refget=refget
    )

    expected = {
        'type': 'Protein',
        'unversioned_stable_id': 'CAB89209',
        'stable_id': 'CAB89209.2',
        'version': 2,
        'transcript_id': 'CAB89209',
        'genome_id': 'tralalala',
        'so_term': 'polypeptide',
        'external_references': [
            {
                'accession_id': 'Q9NFB6',
                'name': 'Q9NFB6',
                'description': None,
                'assignment_method': {
                    'type': 'null'
                },
                'source': {
                    'name': 'UniProtKB/TrEMBL',
                    'id': 'Uniprot/SPTREMBL',
                    'description': None,
                    'release': None
                }
            }
        ],
        'family_matches': [
            {
                'sequence_family': {
                    'source': {
                        'name': 'Pfam',
                        'description': 'Pfam is a database of protein families that includes their annotations and multiple sequence alignments generated using hidden Markov models.',
                        'url': 'http://pfam.xfam.org/',
                        'release': '33.1'
                    },
                    "accession_id": "PF03011",
                    "url": "http://pfam.xfam.org/family/PF03011",
                    "description": "PFEMP",
                    'name': 'PF03011'
                },
                'via': {
                    'source': {
                        'name': 'InterProScan',
                        'description': 'InterPro provides functional analysis of proteins by classifying them into families and predicting domains and important sites.',
                        'url': 'https://www.ebi.ac.uk/interpro',
                        'release': '5.48-83.0'
                    },
                    'accession_id': 'IPR004258',
                    'url': 'https://www.ebi.ac.uk/interpro/entry/InterPro/IPR004258',
                },
                'relative_location': {
                    'start': 602,
                    'end': 762,
                    'length': 161
                },
                'score': 212.5,
                'evalue': 5.1e-63,
                'hit_location': {
                    'start': 1,
                    'end': 157,
                    'length': 157
                }
            }
        ],
        'length': 10,
        'sequence': {
            'alphabet': {
                'accession_id': 'test_protein_accession_id',
                'value': 'test',
                'label': 'test',
                'definition': 'Test - IUPAC notation for protein sequence',
                'description': None
            },
            'checksum': '1f47b55923e2d23090f894c439974b55'
        },
        'sequence_checksum': '1f47b55923e2d23090f894c439974b55'
    }

    assert result == expected


def test_relative_coords():
    '''
    Test relative coords function w.r.t. parent feature
    Inputs are Ensembl-style always ascending values irrespective of strand
    '''

    rel_coords = calculate_relative_coords(
        parent_params={
            'start': 10,
            'end': 30,
            'strand': 1
        },
        child_params={
            'start': 15,
            'end': 26
        }
    )

    assert rel_coords['start'] == 6
    assert rel_coords['end'] == 17
    assert rel_coords['length'] == 12

    rel_coords_reverse = calculate_relative_coords(
        parent_params={
            'start': 10,
            'end': 30,
            'strand': -1
        },
        child_params={
            'start': 15,
            'end': 26
        }
    )

    assert rel_coords_reverse['start'] == 5
    assert rel_coords_reverse['end'] == 16
    assert rel_coords_reverse['length'] == 12

    rel_coords = calculate_relative_coords(
        parent_params={
            'start': 1,
            'end': 10,
            'strand': -1
        },
        child_params={
            'start': 1,
            'end': 10
        }
    )

    assert rel_coords['start'] == 1
    assert rel_coords['end'] == 10


def test_flush_buffer():
    '''
    A large number of documents need to be bundled up for performant loading
    Sometimes errors can occur involving document size that we need to debug
    so we must check the debugging is sane
    '''

    mongo = FakeMongoDbClient()

    # empty buffer means no action
    result = flush_buffer(mongo, [])
    assert not result

    test_data = [{'test': 'a'} for _ in range(10)]
    result = flush_buffer(mongo, test_data, flush_threshold=9)
    assert not result

    result = mongo.collection().find()
    assert mongo.collection().count_documents({}) == 10

    # Struggled to meaningfully test exception behaviour
