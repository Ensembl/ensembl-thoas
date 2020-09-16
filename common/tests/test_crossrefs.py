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
import pytest
from common.crossrefs import XrefResolver


@pytest.fixture(name='resolver')
def fixture_resolver():
    '''
    Pre-load data from file
    '''

    data_folder = 'common/tests'
    test_data = data_folder + '/mini_identifiers.json'

    resolver = XrefResolver(
        from_file=os.path.normpath(test_data)
    )
    return resolver


def test_populate_crossrefs(resolver):
    '''
    Test instantiation of XrefResolver with a small subset of realistic
    data
    '''

    assert len(resolver.namespace.keys()) > 0

    # Can't test URI fetching nicely


def test_source_url(resolver):
    '''
    Test URLs for sources of crossrefs, as well as nice names for the source
    '''

    response = resolver.source_url_generator('chebi')

    assert response == 'https://www.ebi.ac.uk/chebi/'

    response = resolver.source_url_generator('bogus')
    assert response is None


def test_crossref_url(resolver):
    '''
    Test URLs for xrefs based on a source
    '''

    response = resolver.url_generator('17790', 'chebi')
    assert response == 'https://www.ebi.ac.uk/chebi/searchId.do?chebiId=CHEBI:17790'

    response = resolver.url_generator('17790', 'place_of_quiet_reflection')
    assert response is None

    response = resolver.url_generator('LRG_357', 'lrg')
    assert response == 'ftp://ftp.ebi.ac.uk/pub/databases/lrgex/LRG_357.xml'


def test_identifier_resolution(resolver):
    '''
    Verify data being loaded from file, and resolves Ensembl xref dbnames
    '''

    response = resolver.translate_dbname('ChEMBL')
    assert response == 'chembl.target'


def test_combined_resolution(resolver):
    '''
    Perform combined Ensembl dbname mapping and xref resolution
    '''

    response = resolver.url_from_ens_dbname('17790', 'CHEBI')
    assert response == 'https://www.ebi.ac.uk/chebi/searchId.do?chebiId=CHEBI:17790'

    # Check manual override works for sources with overrides
    response = resolver.url_from_ens_dbname('80', 'DBASS3')
    assert response == 'http://www.dbass.soton.ac.uk/DBASS3/viewlist.aspx?filter=gene&id=80'


def test_annotate_function(resolver):
    '''
    Test the addition of URLs to cross references
    '''
    response = resolver.annotate_crossref({
        'accession_id': '1',
        'source': {
            'id': 'CHEBI'
        },
        'assignment_method': {
            'type': 'DIRECT'
        }
    })
    assert response['accession_id'] == '1'
    assert response['source']['id'] == 'CHEBI'
    assert response['url'] == 'https://www.ebi.ac.uk/chebi/searchId.do?chebiId=CHEBI:1'
    assert response['source']['url'] == 'https://www.ebi.ac.uk/chebi/'
    assert response['assignment_method']['description'] == 'A reference made by an external resource of annotation to an Ensembl feature that Ensembl imports without modification'


def test_description_generation(resolver):
    'Test the addition of a description field to xref assignment data'
    description = resolver.describe_info_type('DIRECT')
    assert description == 'A reference made by an external resource of annotation to an Ensembl feature that Ensembl imports without modification'

    with pytest.raises(KeyError, match='Illegal xref info_type NOTAPPROVED used'):
        description = resolver.describe_info_type('NOTAPPROVED')
