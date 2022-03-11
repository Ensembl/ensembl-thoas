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

from mongoengine import StringField, IntField, EmbeddedDocument, EmbeddedDocumentField, ListField

from scripts.mongoengine_documents.base import ThoasDocument, Sequence, ExternalDB


class OntologyTerm(EmbeddedDocument):
    accession_id = StringField()
    value = StringField()
    url = StringField()
    source = EmbeddedDocumentField(ExternalDB)


class Metadata(EmbeddedDocument):
    ontology_terms = ListField(EmbeddedDocumentField(OntologyTerm))


class Region(ThoasDocument):
    type = StringField(default="Region")
    region_id = StringField()
    name = StringField()
    length = IntField()
    topology = StringField()
    metadata = EmbeddedDocumentField(Metadata)
    sequence = EmbeddedDocumentField(Sequence)
    code = StringField()
    assembly_id = StringField()
