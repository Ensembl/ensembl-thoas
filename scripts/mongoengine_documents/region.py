from mongoengine import StringField, IntField, EmbeddedDocument, EmbeddedDocumentField, ListField

from scripts.mongoengine_documents.base import ThoasDocument


class Source(EmbeddedDocument):
    name = StringField()
    url = StringField()
    description = StringField()


class OntologyTerm(EmbeddedDocument):
    accession_id = StringField()
    value = StringField()
    url = StringField()
    source = EmbeddedDocumentField(Source)


class Metadata(EmbeddedDocument):
    ontology_terms = ListField(EmbeddedDocumentField(OntologyTerm))


class Alphabet(EmbeddedDocument):
    accession_id = StringField()
    value = StringField()
    label = StringField()
    definition = StringField()
    description = StringField()  # TODO understand how to write null fields


class Sequence(EmbeddedDocument):
    alphabet = EmbeddedDocumentField(Alphabet)
    checksum = StringField()


class Region(ThoasDocument):
    type = StringField()  # TODO somehow turn this into a class variable with value "Region"
    region_id = StringField()
    name = StringField()
    length = IntField()
    topology = StringField()
    metadata = EmbeddedDocumentField(Metadata)
    sequence = EmbeddedDocumentField(Sequence)
    code = StringField()
    assembly_id = StringField()
