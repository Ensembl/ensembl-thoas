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

from common.crossrefs import xref_resolver
import os
import pytest


@pytest.fixture
def resolver():
    '''
    Pre-load data from file
    '''

    data_folder = 'common/tests'
    test_data = data_folder + '/mini_identifiers.json'

    resolver = xref_resolver(
        from_file=os.path.normpath(test_data)
    )
    return resolver


def test_populate_crossrefs(resolver):
    '''
    Test instantiation of xref_resolver with a small subset of realistic
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


def test_annotate_function(resolver):
    response = resolver.annotate_crossref({
        'id': '1',
        'source': {
            'id': 'CHEBI'
        }
    })
    assert response['id'] == '1'
    assert response['source']['id'] == 'CHEBI'
    assert response['url'] == 'https://www.ebi.ac.uk/chebi/searchId.do?chebiId=CHEBI:1'
    assert response['source']['url'] == 'https://www.ebi.ac.uk/chebi/'
