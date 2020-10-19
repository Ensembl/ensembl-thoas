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

import owlready2


class OntologyReader():
    '''
    A very bland class for reading ontologies and
    accessing terms in a sensible way
    '''
    def __init__(self, ontology):
        self.ontology = owlready2.get_ontology(ontology).load()

    def get_term_by_accession(self, accession):
        'Accession interface. See subclass implementation'
        hits = self.ontology.search(id=accession)
        print(hits)
        return hits[0]

    def get_term_by_label(self, label):
        'Get terms using the label, e.g. "protein_coding"'
        hits = self.ontology.search(label=label)
        print(hits)
        return hits[0]



class SoOntologyReader(OntologyReader):
    '''
    Customized to access the sequence ontology
    Sample exerpt from Sequence Ontology to help with finding predicates:

        <owl:Class rdf:about="http://purl.obolibrary.org/obo/SO_0000704">
            <rdfs:subClassOf rdf:resource="http://purl.obolibrary.org/obo/SO_0001411"/>
            <rdfs:subClassOf>
                <owl:Restriction>
                    <owl:onProperty rdf:resource="http://purl.obolibrary.org/obo/so#member_of"/>
                    <owl:someValuesFrom rdf:resource="http://purl.obolibrary.org/obo/SO_0005855"/>
                </owl:Restriction>
            </rdfs:subClassOf>
            <obo:IAO_0000115 rdf:datatype="http://www.w3.org/2001/XMLSchema#string">A region (or regions) that includes all of the sequence elements necessary to encode a functional transcript. A gene may include regulatory regions, transcribed regions and/or other functional sequence regions.</obo:IAO_0000115>
            <oboInOwl:hasDbXref rdf:datatype="http://www.w3.org/2001/XMLSchema#string">http://en.wikipedia.org/wiki/Gene</oboInOwl:hasDbXref>
            <oboInOwl:hasExactSynonym rdf:datatype="http://www.w3.org/2001/XMLSchema#string">INSDC_feature:gene</oboInOwl:hasExactSynonym>
            <oboInOwl:hasOBONamespace rdf:datatype="http://www.w3.org/2001/XMLSchema#string">sequence</oboInOwl:hasOBONamespace>
            <oboInOwl:id rdf:datatype="http://www.w3.org/2001/XMLSchema#string">SO:0000704</oboInOwl:id>
            <oboInOwl:inSubset rdf:resource="http://purl.obolibrary.org/obo/so#SOFA"/>
            <rdfs:comment rdf:datatype="http://www.w3.org/2001/XMLSchema#string">This term is mapped to MGED. Do not obsolete without consulting MGED ontology. A gene may be considered as a unit of inheritance.</rdfs:comment>
            <rdfs:label rdf:datatype="http://www.w3.org/2001/XMLSchema#string">gene</rdfs:label>
        </owl:Class>
        <owl:Axiom>
            <owl:annotatedSource rdf:resource="http://purl.obolibrary.org/obo/SO_0000704"/>
            <owl:annotatedProperty rdf:resource="http://purl.obolibrary.org/obo/IAO_0000115"/>
            <owl:annotatedTarget rdf:datatype="http://www.w3.org/2001/XMLSchema#string">A region (or regions) that includes all of the sequence elements necessary to encode a functional transcript. A gene may include regulatory regions, transcribed regions and/or other functional sequence regions.</owl:annotatedTarget>
            <oboInOwl:hasDbXref rdf:datatype="http://www.w3.org/2001/XMLSchema#string">SO:immuno_workshop</oboInOwl:hasDbXref>
        </owl:Axiom>
        <owl:Axiom>
            <owl:annotatedSource rdf:resource="http://purl.obolibrary.org/obo/SO_0000704"/>
            <owl:annotatedProperty rdf:resource="http://www.geneontology.org/formats/oboInOwl#hasDbXref"/>
            <owl:annotatedTarget rdf:datatype="http://www.w3.org/2001/XMLSchema#string">http://en.wikipedia.org/wiki/Gene</owl:annotatedTarget>
            <rdfs:label rdf:datatype="http://www.w3.org/2001/XMLSchema#string">wiki</rdfs:label>
        </owl:Axiom>
    '''

    @staticmethod
    def get_term_name(term):
        'Accepts an OWL Term and gets the "name" from it in an unintuitive way'

        return term.IAO_0000115[0]

    def summarise_term(self, term):
        'Turns an ontology term into something usable'

        return {
            'accession_id': term.id[0],
            'name': term.label[0],
            'description': self.get_term_name(term)
        }
