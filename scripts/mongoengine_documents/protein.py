from mongoengine import StringField, IntField, ListField, EmbeddedDocumentField, EmbeddedDocument, FloatField

from scripts.mongoengine_documents.base import ThoasDocument, ExternalReference, Sequence, ExternalDB, Location


class SequenceFamily(EmbeddedDocument):
    source = EmbeddedDocumentField(ExternalDB)
    accession_id = StringField()
    name = StringField()
    url = StringField()
    description = StringField()


class ClosestDataProvider(EmbeddedDocument):
    source = EmbeddedDocumentField(ExternalDB)
    accession_id = StringField()
    url = StringField()


class FamilyMatch(EmbeddedDocument):
    sequence_family = EmbeddedDocumentField(SequenceFamily)
    via = EmbeddedDocumentField(ClosestDataProvider)
    relative_location = EmbeddedDocumentField(Location)
    hit_location = EmbeddedDocumentField(Location)
    score = FloatField()
    evalue = FloatField()


class Protein(ThoasDocument):
    type = StringField()
    unversioned_stable_id = StringField()
    stable_id = StringField()
    version = IntField()
    transcript_id = StringField()
    genome_id = StringField()
    so_term = StringField()
    external_references = ListField(EmbeddedDocumentField(ExternalReference))
    sequence = EmbeddedDocumentField(Sequence)
    sequence_checksum = StringField()
    family_matches = ListField(EmbeddedDocumentField(FamilyMatch))
    length = IntField()


