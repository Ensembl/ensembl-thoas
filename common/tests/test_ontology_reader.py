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

import common.ontology_reader

def test_ontology_loading():
    'Instantiate and lightly use an SoOntologyReader'
    ontology_reader = common.ontology_reader.OboOntologyReader('common/tests/test_so.owl')
    assert ontology_reader
    assert ontology_reader.get_term_by_label('gene')


def test_ontology_term_summary():
    'Check the content of a term from summarise_term()'
    ontology_reader = common.ontology_reader.OboOntologyReader(
        ontology='common/tests/test_so.owl',
        source_name='Sequence Ontology',
        source_url='sequenceontology.org'
    )
    term = ontology_reader.get_term_by_label('gene')
    summary = ontology_reader.summarise_term(term)

    assert summary['accession_id'] == 'SO:0000704'
    assert summary['value'] == 'gene'
    # SO terms do not have versions
    assert not summary['version']
    assert summary['url'] == 'http://purl.obolibrary.org/obo/SO_0000704'
    assert summary['description'] == 'A region (or regions) that includes all of the sequence elements necessary to encode a functional transcript. A gene may include regulatory regions, transcribed regions and/or other functional sequence regions.'
    assert summary['source']['name'] == 'Sequence Ontology'
    assert summary['source']['url'] == 'sequenceontology.org'
