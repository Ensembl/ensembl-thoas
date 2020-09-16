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
    # Note that assignment_method description is inferred on the fly
    # assert first_result['assignment_method']['description']

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

    assert doc_list[0]['accession_id'] == 'GO:0098781'
    assert doc_list[0]['source']['name'] == 'GO'
    assert doc_list[0]['source']['id'] == 'GO'


def test_slice_formatting():
    '''
    Ensure slices are correctly generated from parameters
    '''
    slice_dict = format_slice('test', 'test place', True, 1, 'GRCh38', 100, 200)

    assert slice_dict['region']['name'] == 'test'
    assert slice_dict['region']['strand']['code'] == 'forward'
    assert slice_dict['region']['strand']['value'] == 1
    assert slice_dict['region']['assembly'] == 'GRCh38'
    assert slice_dict['location']['start'] == 100
    assert slice_dict['location']['end'] == 200
    assert slice_dict['default'] is True
    assert slice_dict['location']['location_type'] == 'test place'

    slice_dict = format_slice('test', 'test place', False, -1, 'GRCh38', 100, 200)

    assert slice_dict['region']['name'] == 'test'
    assert slice_dict['region']['strand']['code'] == 'reverse'
    assert slice_dict['region']['strand']['value'] == -1
    assert slice_dict['region']['assembly'] == 'GRCh38'
    assert slice_dict['location']['start'] == 100
    assert slice_dict['location']['end'] == 200
    assert slice_dict['default'] is False
    assert slice_dict['location']['location_type'] == 'test place'


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
        region_type='chromosome',
        default_region=True,
        assembly='GRCh38',
        transcript={
            'start': 1,
            'end': 200,
            'strand': 1
        }
    )

    assert exon['type'] == 'Exon'
    assert exon['stable_id'] == 'ENSE123.1'
    assert exon['unversioned_stable_id'] == 'ENSE123'
    assert exon['version'] == 1
    assert exon['slice']['region']['name'] == 'chr1'
    assert exon['relative_location']['start'] == 100
    assert exon['relative_location']['end'] == 200
    assert exon['relative_location']['length'] == 101
    # forego further enumeration of slice properties


def test_phase_calculation():
    '''
    Check that phases and rank are calculated correctly for a given ordered
    list of exons.
    '''
    exon_list = [
        {'start': 1, 'end': 10, 'stable_id': 'ENSE01', 'unversioned_stable_id': 'ENSE01', 'rank': 1},
        {'start': 21, 'end': 30, 'stable_id': 'ENSE02', 'unversioned_stable_id': 'ENSE02', 'rank': 2}
    ]

    phase_lookup = {
        'ENST01': {
            'ENSE01': (-1, 0),
            'ENSE02': (0, -1)
        }
    }

    splicing = phase_exons(exon_list, 'ENST01', phase_lookup)
    for i in range(0, len(splicing)):
        assert splicing[i]['index'] == i + 1
        stable_id = exon_list[i]['stable_id']
        assert splicing[i]['exon']['stable_id'] == stable_id

        assert (
            splicing[i]['start_phase'], splicing[i]['end_phase']
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
        {'start': 1, 'end': 10, 'stable_id': 'ENSE01', 'unversioned_stable_id': 'ENSE01', 'rank': 1},
        {'start': 21, 'end': 30, 'stable_id': 'ENSE02', 'unversioned_stable_id': 'ENSE02', 'rank': 2}
    ]

    splicing = splicify_exons(exon_list, transcript)
    print(splicing[0])
    assert len(splicing) == 2
    assert splicing[0]['index'] == 1
    assert splicing[0]['exon'] == exon_list[0]
    assert splicing[0]['relative_location'] == {
        'start': 1,
        'end': 10,
        'length': 10
    }
    print(splicing[1])
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
    assert utr['relative_start'] == 1
    assert utr['relative_end'] == 1

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
    assert utr['relative_start'] == 10
    assert utr['relative_end'] == 10

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
    assert utr['relative_start'] == 1
    assert utr['relative_end'] == 2

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
    assert utr['relative_start'] == 4
    assert utr['relative_end'] == 10


def test_cdna_formatting():
    '''
    cDNA representation
    '''
    transcript = {
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

    cdna = format_cdna(transcript)
    assert cdna['start'] == 1
    assert cdna['end'] == 100
    assert cdna['relative_start'] == 1
    assert cdna['relative_end'] == 40


def test_protein_formatting():
    '''
    Verify protein document structure
    '''
    
    protein = {
        'id': 'ENSP001',
        'version': 2,
        'transcript_id': 'ENST001',
        'xrefs': []
    }

    result = format_protein(protein)
    assert result['type'] == 'Product'
    assert result['unversioned_stable_id'] == 'ENSP001'
    assert result['stable_id'] == 'ENSP001.2'
    assert result['version'] == 2
    assert result['so_term'] == 'polypeptide'
    assert result['transcript_id'] == 'ENST001'


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
