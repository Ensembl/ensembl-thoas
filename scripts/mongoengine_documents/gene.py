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
    type = StringField(default="Gene")
    stable_id = StringField()
    unversioned_stable_id = StringField()
    version = IntField()
    so_term = StringField()
    symbol = StringField()
    # If we don't specify a max_length for strings in a list then mongoengine will refuse to write the data with this
    # message: "AttributeError: 'str' object has no attribute 'to_mongo'"
    alternative_symbols = ListField(StringField(max_length=120))
    name = StringField()
    slice = EmbeddedDocumentField(Slice)
    # Again, we need to specify a max_length for a list of strings
    transcripts = ListField(ListField(StringField(max_length=120)))  # TODO Why the doubly-nested list??
    genome_id = StringField()
    external_references = ListField(EmbeddedDocumentField(ExternalReference))
    metadata = EmbeddedDocumentField(GeneMetadata)
