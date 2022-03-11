from mongoengine import IntField, StringField, BooleanField

from scripts.mongoengine_documents.base import ThoasDocument


class Assembly(ThoasDocument):
    type = StringField(default="Assembly")
    default = BooleanField()
    assembly_id = StringField()
    name = StringField()
    accession_id = StringField()
    accessioning_body = StringField()
    species = StringField()


class Species(ThoasDocument):
    type = StringField(default="Species")
    species_id = StringField()
    scientific_name = StringField()
    taxon_id = IntField()


class Genome(ThoasDocument):
    type = StringField(default="Genome")
    genome_id = StringField()
    name = StringField()
    assembly = StringField()
    species = StringField()
