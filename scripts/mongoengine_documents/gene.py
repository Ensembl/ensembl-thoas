from mongoengine import EmbeddedDocument, StringField, EmbeddedDocumentField, BooleanField, ListField, IntField

from scripts.mongoengine_documents.base import ThoasDocument, Location, Strand, Slice, ExternalReference, ExternalDB


class GeneBiotypeMetadata(EmbeddedDocument):
    value = StringField()
    label = StringField()
    definition = StringField()
    description = StringField()


class GeneNameMetadata(EmbeddedDocument):
    accession_id = StringField()
    value = StringField()
    url = StringField()
    source = EmbeddedDocumentField(ExternalDB)


class GeneMetadata(EmbeddedDocument):
    biotype = EmbeddedDocumentField(GeneBiotypeMetadata)
    name = EmbeddedDocumentField(GeneNameMetadata)


class Gene(ThoasDocument):
    type = StringField()
    stable_id = StringField()
    unversioned_stable_id=StringField()
    version = IntField()
    so_term = StringField()
    symbol = StringField()
    alternative_symbols = ListField(StringField)
    name = StringField()
    slice = EmbeddedDocumentField(Slice)
    transcripts = ListField(ListField(StringField))  # TODO Why the doubly-nested list??
    genome_id = StringField()
    external_references = ListField(EmbeddedDocumentField(ExternalReference))
    metadata = EmbeddedDocumentField(GeneMetadata)
