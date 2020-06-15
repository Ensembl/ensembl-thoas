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

from common.utils import format_cross_refs, format_slice, format_exon, splicify_exons


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
            'dbname': 'HGNC'
        }
    ])

    assert doc_list[0]['id'] == 'HGNC:1101'
    assert doc_list[0]['name'] == 'BRCA2'
    assert doc_list[0]['description'] == 'BRCA2 DNA repair associated'
    assert doc_list[0]['source']['name'] == 'HGNC symbol'
    assert doc_list[0]['source']['id'] == 'HGNC'

    doc_list = format_cross_refs([
        {
            'primary_id': 'GO:0098781',
            'display_id': 'ncRNA transcription',
            'description': 'The transcription of non (protein) coding RNA from a DNA template. Source: GOC:dos',
            'dbname': 'GO'
        }
    ])

    assert doc_list[0]['id'] == 'GO:0098781'
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
        exon_stable_id='ENSE123',
        version=1,
        region_name='chr1',
        region_strand=1,
        exon_start=100,
        exon_end=200,
        region_type='chromosome',
        default_region=True,
        assembly='GRCh38'
    )

    assert exon['type'] == 'Exon'
    assert exon['stable_id'] == 'ENSE123.1'
    assert exon['unversioned_stable_id'] == 'ENSE123'
    assert exon['version'] == 1
    assert exon['slice']['region']['name'] == 'chr1'
    # forego further enumeration of slice properties


def test_splicifying():
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

    splicing = splicify_exons(exon_list, 'ENST01', phase_lookup)
    for i in range(0, len(splicing)):
        assert splicing[i]['index'] == i
        stable_id = exon_list[i]['stable_id']
        assert splicing[i]['exon']['stable_id'] == stable_id

        assert (
            splicing[i]['start_phase'], splicing[i]['end_phase']
        ) == (
            phase_lookup['ENST01'][stable_id]
        )
