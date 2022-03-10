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
