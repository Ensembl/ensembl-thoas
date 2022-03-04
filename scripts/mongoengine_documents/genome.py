from mongoengine import EmbeddedDocument, IntField, StringField, EmbeddedDocumentField, BooleanField, ListField

from scripts.mongoengine_documents.base import ThoasDocument


class Assembly(ThoasDocument):
    type = StringField()
    default = BooleanField()
    # This changes the name of the 'id' field to 'assembly_id' because mongoengine is unhappy with a field called 'id'
    # TODO update resolvers to use 'assembly_id'
    assembly_id = StringField()
    name = StringField()
    accession_id = StringField()
    accessioning_body = StringField()
    species = StringField()


class Species(ThoasDocument):
    type = StringField()
    # TODO update resolvers to use 'species_id'
    species_id = StringField()
    scientific_name = StringField()
    taxon_id = IntField()


class Genome(ThoasDocument):
    type = StringField()
    # TODO update resolvers to use 'genome_id'
    genome_id = StringField()
    name = StringField()
    assembly = StringField()
    species = StringField()
