from mongoengine import StringField, IntField, EmbeddedDocumentField, EmbeddedDocument, BooleanField, ListField

from scripts.mongoengine_documents.base import ThoasDocument, Location, ExternalReference, Sequence, Slice


class UTR(EmbeddedDocument):
    type = StringField()
    start = IntField()
    end = IntField()
    length = IntField()
    sequence_checksum = StringField()


class Exon(EmbeddedDocument):
    type = StringField()
    stable_id = StringField()
    unversioned_stable_id = StringField()
    version = IntField()
    so_term = StringField() # TODO Try to set this to "exon"
    slice = EmbeddedDocumentField(Slice)


class PhasedExon(EmbeddedDocument):
    start_phase = IntField()
    end_phase = IntField()
    index = IntField()
    exon = EmbeddedDocumentField(Exon)


class CDS(EmbeddedDocument):
    start = IntField()
    end = IntField()
    relative_start = IntField()
    relative_end = IntField()
    nucleotide_length = IntField()
    protein_length = IntField()
    sequence = EmbeddedDocumentField(Sequence)
    sequence_checksum = StringField()
    product_id = StringField()


class CDNA(EmbeddedDocument):
    start = IntField()
    end = IntField()
    relative_start = IntField()
    relative_end = IntField()
    length = IntField()
    type = StringField()
    sequence = EmbeddedDocumentField(Sequence)
    sequence_checksum = StringField()


class ProductGeneratingContext(EmbeddedDocument):
    product_type = StringField()
    five_prime_utr = EmbeddedDocumentField(UTR)
    three_prime_utr = EmbeddedDocumentField(UTR)  # TODO update resolvers, which expect '3_prime_utr'
    cds = EmbeddedDocumentField(CDS)
    product_id = StringField()
    phased_exons = ListField(EmbeddedDocumentField(PhasedExon))
    default = BooleanField()
    cdna = EmbeddedDocumentField(CDNA)


class Intron(EmbeddedDocument):
    type = StringField()
    index = IntField()
    slice = EmbeddedDocumentField(Slice)
    so_term = StringField()  # TODO default to "intron"??
    relative_location = EmbeddedDocumentField(Location)
    sequence_checksum = StringField()


class SplicedExon(EmbeddedDocument):
    index = IntField()
    exon = EmbeddedDocumentField(Exon)
    relative_location = EmbeddedDocumentField(Location)


class TranscriptMetadataElement(EmbeddedDocument):
    value = StringField()
    label = StringField()
    definition = StringField()
    description = StringField()


class TranscriptMetadata(EmbeddedDocument):
    appris = EmbeddedDocumentField(TranscriptMetadataElement)
    tsl = EmbeddedDocumentField(TranscriptMetadataElement)
    mane = EmbeddedDocumentField(TranscriptMetadataElement)  # TODO do something different for this one, like in the graphql schema?
    gencode_basic = EmbeddedDocumentField(TranscriptMetadataElement)
    biotype = EmbeddedDocumentField(TranscriptMetadataElement)
    canonical = EmbeddedDocumentField(TranscriptMetadataElement)


class Transcript(ThoasDocument):
    type = StringField()
    gene = StringField()
    stable_id = StringField()
    unversioned_stable_id = StringField()
    version = IntField()
    so_term = StringField()
    symbol = StringField()
    description = StringField()
    relative_location = EmbeddedDocumentField(Location)
    slice = EmbeddedDocumentField(Slice)
    genome_id = StringField()
    external_references = ListField(EmbeddedDocumentField(ExternalReference))
    product_generating_contexts = ListField(EmbeddedDocumentField(ProductGeneratingContext))
    introns = ListField(EmbeddedDocumentField(Intron))
    spliced_exons = ListField(EmbeddedDocumentField(SplicedExon))
    metadata = EmbeddedDocumentField(TranscriptMetadata)

