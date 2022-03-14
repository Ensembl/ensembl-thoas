"""   See the NOTICE file distributed with this work for additional information
   regarding copyright ownership.
   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at
       http://www.apache.org/licenses/LICENSE-2.0
   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License."""

from mongoengine import Document, StringField, EmbeddedDocumentField, EmbeddedDocument, IntField, BooleanField


class ThoasDocument(Document):
    meta = {'allow_inheritance': True}


class ExternalDB(EmbeddedDocument):
    name = StringField()
    external_db_id = StringField()
    description = StringField()
    url = StringField()
    release = StringField()


class ExternalMethod(EmbeddedDocument):
    type = StringField()
    description = StringField()


class ExternalReference(EmbeddedDocument):
    accession_id = StringField()
    name = StringField()
    description = StringField()
    assignment_method = EmbeddedDocumentField(ExternalMethod)
    url = StringField()
    source = EmbeddedDocumentField(ExternalDB)


class Alphabet(EmbeddedDocument):
    accession_id = StringField()
    label = StringField()
    value = StringField()
    definition = StringField()
    description = StringField()


class Sequence(EmbeddedDocument):
    alphabet = EmbeddedDocumentField(Alphabet)
    checksum = StringField()


class Location(EmbeddedDocument):
    start = IntField()
    end = IntField()
    length = IntField()


class Strand(EmbeddedDocument):
    code = StringField()
    value = IntField()


class Slice(EmbeddedDocument):
    region_id = StringField()
    location = EmbeddedDocumentField(Location)
    strand = EmbeddedDocumentField(Strand)
    default = BooleanField()
    genome_id = StringField()
