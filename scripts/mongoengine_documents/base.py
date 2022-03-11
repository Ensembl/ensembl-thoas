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
