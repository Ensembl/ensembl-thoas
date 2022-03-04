from mongoengine import EmbeddedDocument, IntField, StringField, EmbeddedDocumentField, BooleanField, ListField

from scripts.mongoengine_documents.base import ThoasDocument


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
    default = BooleanField


class Gene(ThoasDocument):
    transcripts = ListField(ListField(StringField))  # TODO Why the doubly-nested list??
