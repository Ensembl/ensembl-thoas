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

from common.utils import format_cross_refs, format_slice, format_exon


def test_xref_formatting():
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
    Slice = format_slice('test', 'test place', True, 1, 'GRCh38', 100, 200)

    assert Slice['region']['name'] == 'test'
    assert Slice['region']['strand']['code'] == 'forward'
    assert Slice['region']['strand']['value'] == 1
    assert Slice['region']['assembly'] == 'GRCh38'
    assert Slice['location']['start'] == 100
    assert Slice['location']['end'] == 200
    assert Slice['default'] is True
    assert Slice['location']['location_type'] == 'test place'

    Slice = format_slice('test', 'test place', False, -1, 'GRCh38', 100, 200)

    assert Slice['region']['name'] == 'test'
    assert Slice['region']['strand']['code'] == 'reverse'
    assert Slice['region']['strand']['value'] == -1
    assert Slice['region']['assembly'] == 'GRCh38'
    assert Slice['location']['start'] == 100
    assert Slice['location']['end'] == 200
    assert Slice['default'] is False
    assert Slice['location']['location_type'] == 'test place'


def test_exon_formatting():
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
