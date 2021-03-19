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

from unittest import mock
from unittest.mock import MagicMock

from common.utils import *
from common.mongo import FakeMongoDbClient
from common.refget_postgresql import MockRefgetDB as RefgetDB


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
    slice_dict = format_slice('test', True, 1, 'GRCh38', 100, 200)

    assert slice_dict['region']['name'] == 'test'
    assert slice_dict['strand']['code'] == 'forward'
    assert slice_dict['strand']['value'] == 1
    assert slice_dict['region']['assembly'] == 'GRCh38'
    assert slice_dict['location']['start'] == 100
    assert slice_dict['location']['end'] == 200
    assert slice_dict['default'] is True

    slice_dict = format_slice('test', False, -1, 'GRCh38', 100, 200)

    assert slice_dict['region']['name'] == 'test'
    assert slice_dict['strand']['code'] == 'reverse'
    assert slice_dict['strand']['value'] == -1
    assert slice_dict['region']['assembly'] == 'GRCh38'
    assert slice_dict['location']['start'] == 100
    assert slice_dict['location']['end'] == 200
    assert slice_dict['default'] is False


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
        region_strand=1,
        default_region=True,
        assembly='GRCh38'
    )

    assert exon['type'] == 'Exon'
    assert exon['stable_id'] == 'ENSE123.1'
    assert exon['unversioned_stable_id'] == 'ENSE123'
    assert exon['version'] == 1
    assert exon['slice']['region']['name'] == 'chr1'
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
                'region': {
                    'name': '13'
                },
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
                'region': {
                    'name': '13'
                },
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
                'region': {
                    'name': '13'
                },
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
                'region': {
                    'name': '13'
                },
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
                'region': {
                    'name': '13'
                },
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
                'region': {
                    'name': '13'
                },
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
                'region': {
                    'name': '13'
                },
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
                'region': {
                    'name': '13'
                },
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
                'region': {
                    'name': '13'
                },
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
                'region': {
                    'name': '13'
                },
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
        'id': 'ENSP001',
        'version': 2,
        'transcript_id': 'ENST001',
        'xrefs': [],
        'protein_features': []
    }
    refget = RefgetDB()
    result = format_protein(
        protein=protein,
        genome_id='tralalala',
        product_length=10,
        refget=refget
    )

    assert result['type'] == 'Protein'
    assert result['unversioned_stable_id'] == 'ENSP001'
    assert result['stable_id'] == 'ENSP001.2'
    assert result['version'] == 2
    assert result['so_term'] == 'polypeptide'
    assert result['transcript_id'] == 'ENST001'
    assert result['genome_id'] == 'tralalala'
    assert result['length'] == 10


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
