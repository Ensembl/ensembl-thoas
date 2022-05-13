"""
.. See the NOTICE file distributed with this work for additional information
   regarding copyright ownership.
   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at
       http://www.apache.org/licenses/LICENSE-2.0
   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
"""

import re
import csv
import os
import json
import warnings

import ijson
import pymongo


import common.utils
from common.transcript_metadata import TSL, APPRIS, MANE, GencodeBasic, Biotype, EnsemblCanonical
from common.mongo import MongoDbClient
from common.refget_postgresql import RefgetDB
from common.crossrefs import XrefResolver
from common.logger import ThoasLogging

lrg_detector = re.compile('^LRG')

def create_index(mongo_client):
    '''
    Create indexes for searching useful things on genes, transcripts etc. and enforcing uniqueness
    '''
    collection = mongo_client.collection()
    collection.create_index([
        ('name', pymongo.ASCENDING), ('genome_id', pymongo.ASCENDING)
    ], name='names_of_things')
    collection.create_index([
        ('genome_id', pymongo.ASCENDING),
        ('stable_id', pymongo.ASCENDING),
        ('type', pymongo.ASCENDING)
    ], name='stable_id')
    collection.create_index([
        ('genome_id', pymongo.ASCENDING), ('type', pymongo.ASCENDING)
    ], name='feature_type')
    collection.create_index([
        ('genome_id', pymongo.ASCENDING),
        ('slice.region.name', pymongo.ASCENDING),
        ('slice.location.start', pymongo.ASCENDING),
        ('slice.location.end', pymongo.ASCENDING)
    ], name='location_index')
    collection.create_index([
        ('genome_id', pymongo.ASCENDING), ('gene', pymongo.ASCENDING)
    ], name='gene_foreign_key')
    collection.create_index([
        ('genome_id', pymongo.ASCENDING), ('transcript', pymongo.ASCENDING)
    ], name='transcript_foreign_key')
    collection.create_index([
        ('cross_references.name', pymongo.ASCENDING),
        ('cross_references.source.id', pymongo.ASCENDING)
    ], name='cross_refs')
    collection.create_index([
        ('genome_id', pymongo.ASCENDING),
        ('protein_id', pymongo.ASCENDING)
    ], name='protein_fk')


def load_gene_info(mongo_client, json_file, cds_info, assembly, genome, phase_info, tr_metadata_info, metadata_classifier, gene_name_metadata, xref_resolver, refget, logger):
    """
    Reads from "custom download" gene JSON dumps and converts to suit
    Core Data Modelling schema.
    mongoclient = A connected pymongo client
    json_file = File containing gene data from production pipeline
    cds_info = CDS start and end coordinates indexed by transcript ID
    phase_info = Per exon start and end phases indexed by transcript and exon ID
    """
    gene_buffer = []
    transcript_buffer = []

    # at least until there's a process for alt-alleles etc.
    default_region = True
    print('Loaded assembly ' + assembly['name'])

    gene_biotype_classifiers = metadata_classifier['gene_biotype']

    required_keys = ('name', 'description')
    with open(json_file, encoding='UTF-8') as file:
        print('Chunk')
        for gene in ijson.items(file, 'item'):

            for key in required_keys:
                if key not in gene:
                    gene[key] = None
            # LRGs are difficult. They should probably be kept in another
            # Gene Set because they have little to do with Ensembl Genebuild
            if lrg_detector.search(gene['id']):
                continue

            try:
                gene_xrefs = common.utils.format_cross_refs(gene['xrefs'])
            except KeyError:
                gene_xrefs = []

            normalised_gene_biotype = gene['biotype'].lower()
            gene_metadata = {'biotype': gene_biotype_classifiers.get(normalised_gene_biotype)}

            # Gene biotypes in data dumps may be missing the "_gene" suffix
            if not gene_metadata['biotype']:
                gene_metadata['biotype'] = gene_biotype_classifiers.get(normalised_gene_biotype + "_gene")

            # infer biotype valueset if we can't find it in gene_biotype.json
                gene_metadata['biotype'] = {
                    "value": gene["biotype"].lower(),
                    "label": gene["biotype"].replace("_", " "),
                    "description": ""
                }

            try:
                gene_metadata['name'] = common.utils.get_gene_name_metadata(gene_name_metadata[gene['id']], xref_resolver, logger)
            except KeyError as ke:
                gene_metadata['name'] = None

            json_gene = {

                'type': 'Gene',
                'stable_id': common.utils.get_stable_id(gene["id"], gene["version"]),
                'unversioned_stable_id': gene['id'],
                'version': gene['version'],
                'so_term': gene['biotype'],
                'symbol': gene['name'],
                'alternative_symbols': gene['synonyms'] if 'synonyms' in gene else [],
                # Note that the description comes the long way via xref
                # pipeline and includes a [source: string]
                'name': re.sub(r'\[.*?\]', '', gene['description']).rstrip() if gene['description'] is not None else None,
                'slice': common.utils.format_slice(
                    region_name=gene['seq_region_name'],
                    region_code=gene['coord_system']['name'],
                    default_region=default_region,
                    strand=int(gene['strand']),
                    start=int(gene['start']),
                    end=int(gene['end']),
                    genome_id=genome['id']
                ),
                'transcripts': [
                    [common.utils.get_stable_id(transcript["id"], transcript["version"]) \
                     for transcript in gene['transcripts']]
                ],
                'genome_id': genome['id'],
                'external_references': gene_xrefs,
                'metadata' : gene_metadata
            }
            gene_buffer.append(json_gene)

            # Sort out some transcripts while we can see them
            for transcript in gene['transcripts']:
                transcript_buffer.append(format_transcript(
                    transcript=transcript,
                    gene=gene,
                    region_name=gene['seq_region_name'],
                    genome_id=genome['id'],
                    cds_info=cds_info,
                    phase_info=phase_info,
                    tr_metadata_info=tr_metadata_info,
                    refget=refget
                ))

            gene_buffer = common.utils.flush_buffer(mongo_client, gene_buffer)
            transcript_buffer = common.utils.flush_buffer(mongo_client, transcript_buffer)

    # Flush buffers at end of gene data
    if len(gene_buffer) > 0:
        mongo_client.collection().insert_many(gene_buffer)
    if len(transcript_buffer) > 0:
        mongo_client.collection().insert_many(transcript_buffer)


def get_genome_assembly(assembly_name, mongo_client):
    assembly = mongo_client.collection().find_one({
        'type': 'Assembly',
        'name': assembly_name
    })
    genome = mongo_client.collection().find_one({
        'type': 'Genome',
        'name': assembly_name
    })
    if not genome or not assembly:
        raise IOError(f'Failed to fetch {assembly_name} assembly and genome info from MongoDB')
    return assembly, genome


def format_transcript(
        transcript, gene, region_name, genome_id,
        cds_info, phase_info, tr_metadata_info, refget
):
    '''
    Transform and supplement transcript information
    Args:
    transcript - directly from JSON file
    gene - the parent gene data
    region_name - like 'chr1' or '1'
    genome_id - the assembly/species/data release combo for this data
    cds_info - data from file representing cds_start and cds_end in relative
               and absolute coordinates
    phase_info - data from file containing transcript IDs, exon IDs and per-
                 exon start and end phases
    default_region - boolean, is this the actual or alt allele
    assembly - contains assembly name and accession etc.
    '''

    default_region = True
    ordered_formatted_exons = []
    # verify that exons are all in rank order in case the source file isn't
    # There are no guarantees in the dumping pipeline for rank order
    for exon in sorted(transcript['exons'], key=common.utils.exon_sorter):
        ordered_formatted_exons.append(
            common.utils.format_exon(
                exon,
                region_name=region_name,
                region_code=exon['coord_system']['name'],
                region_strand=int(exon['strand']),
                default_region=default_region,
                genome_id=genome_id
            )
        )

    try:
        transcript_xrefs = common.utils.format_cross_refs(transcript['xrefs'])
    except KeyError:
        transcript_xrefs = []

    ####TODO: Type and release version

    new_transcript = {
        'type': 'Transcript',
        'gene': common.utils.get_stable_id(gene["id"], gene["version"]),
        'stable_id': common.utils.get_stable_id(transcript["id"], transcript["version"]),
        'unversioned_stable_id': transcript['id'],
        'version': transcript['version'],
        'so_term': transcript['biotype'],
        'symbol': transcript['name'] if 'name' in transcript else None,
        'description': transcript['description'] if 'description' in transcript else None,
        'relative_location': common.utils.calculate_relative_coords(
            parent_params={
                'start': gene['start'],
                'end': gene['end'],
                'strand': gene['strand']
            },
            child_params={
                'start': transcript['start'],
                'end': transcript['end']
            }
        ),
        'slice': common.utils.format_slice(
            region_name=region_name,
            region_code=transcript['coord_system']['name'],
            default_region=default_region,
            strand=int(transcript['strand']),
            start=int(transcript['start']),
            end=int(transcript['end']),
            genome_id=genome_id
        ),
        'genome_id': genome_id,
        'external_references': transcript_xrefs,
        'product_generating_contexts': [],
        'introns': common.utils.infer_introns(ordered_formatted_exons, transcript),
        'spliced_exons': common.utils.splicify_exons(ordered_formatted_exons, transcript),
        'metadata': tr_metadata_info[transcript['id']]
    }

    # Insert multiple product handling here when we know what it will look like
    # Pick the first to be default
    defaults = [False] * (len(transcript['translations']) - 1)
    defaults.append(True)

    # Now for the tricky stuff around CDS
    if transcript['id'] in cds_info:
        relative_cds_start = cds_info[transcript['id']]['relative_start']
        relative_cds_end = cds_info[transcript['id']]['relative_end']
        cds_start = cds_info[transcript['id']]['start']
        cds_end = cds_info[transcript['id']]['end']
        spliced_length = cds_info[transcript['id']]['spliced_length']
        cds_sequence_checksum, _ = refget.get_checksum_and_length(new_transcript['stable_id'], refget.cds)
        cds_sequence = common.utils.format_sequence(refget, cds_sequence_checksum, refget.cds)

        for translation in transcript['translations']:
            product_id = common.utils.get_stable_id(translation["id"], translation["version"])
            _, protein_length = refget.get_checksum_and_length(product_id, refget.pep)
            new_transcript['product_generating_contexts'].append(
                {
                    'product_type': 'Protein',  # probably
                    '5_prime_utr': common.utils.format_utr(
                        transcript, cds_start, cds_end, downstream=False
                    ),
                    '3_prime_utr': common.utils.format_utr(
                        transcript, cds_start, cds_end, downstream=True
                    ),
                    'cds': {
                        'start': cds_start,
                        'end': cds_end,
                        'relative_start': relative_cds_start,
                        'relative_end': relative_cds_end,
                        'nucleotide_length': spliced_length,
                        'protein_length': protein_length,
                        'sequence': cds_sequence,
                        'sequence_checksum': cds_sequence.get('checksum')
                    },
                    # Infer the "products" in the resolver. This is a join.
                    'product_id': product_id,
                    'phased_exons': common.utils.phase_exons(ordered_formatted_exons, transcript['id'], phase_info),
                    # We'll know default later when it becomes relevant
                    'default': defaults.pop(),
                    'cdna': common.utils.format_cdna(transcript=transcript, refget=refget)
                }
            )
    # cds_info has a list of all the coding transcripts. If not in that list, it is a non-coding transcript
    elif transcript['exons']:
        new_transcript['product_generating_contexts'].append(
            {
                'product_type': None,
                '5_prime_utr': None,
                '3_prime_utr': None,
                'cds': None,
                'product_id': None,
                'phased_exons': [],
                # We'll know default later when it becomes relevant
                'default': defaults.pop(),
                'cdna': common.utils.format_cdna(transcript=transcript, refget=refget, non_coding = True)
            }
        )

    return new_transcript


def load_product_info(mongo_client, product_filepath, genome_id, refget):
    protein_buffer = []
    with open(product_filepath, encoding='UTF-8') as protein_file:
        for line in protein_file:
            product = json.loads(line)
            protein_buffer.append(
                common.utils.format_protein(
                    protein=product,
                    genome_id=genome_id,
                    refget=refget)
            )
            protein_buffer = common.utils.flush_buffer(mongo_client, protein_buffer)
    if len(protein_buffer) > 0:
        mongo_client.collection().insert_many(protein_buffer)


def preload_cds_coords(production_name, assembly):
    '''
    CDS coords will be pre-loaded into a file from the Perl API. Otherwise
    hideous calculation required to get the relative coordinates
    '''
    cds_buffer = {}

    with open(production_name + '_' + assembly + '.csv', encoding='UTF-8') as file:
        reader = csv.reader(file)
        next(reader, None)  # skip header line
        for row in reader:
            cds_buffer[row[0]] = {
                'start': int(row[1]),
                'end': int(row[2]),
                'relative_start': int(row[3]),
                'relative_end': int(row[4]),
                'spliced_length': int(row[5])
            }
    return cds_buffer


def preload_exon_phases(production_name, assembly):
    '''
    Phases are hard to calculate on the fly. They are instead dumped into a
    pile of splicing information. Turn it into a lookup structure.
    LIMITED TO SINGLE PRODUCTS PER TRANSCRIPT
    '''

    phase_lookup = {}

    with open(production_name + '_' + assembly + '_phase.csv', encoding='UTF-8') as file:
        reader = csv.DictReader(file)
        for row in reader:
            transcript = row['transcript ID']
            if transcript not in phase_lookup:
                phase_lookup[transcript] = {
                    row['exon ID']: (int(row['start_phase']), int(row['end_phase']))
                }
            else:
                phase_lookup[transcript].update({
                    row['exon ID']: (int(row['start_phase']), int(row['end_phase']))
                })

    return phase_lookup

def get_transcript_meta(row):
    transcript_meta = {'appris': None, 'tsl': None, 'mane':None, 'gencode_basic':None, 'biotype':None, 'canonical':None}
    try:
        appris = APPRIS(row['appris'])
        if appris.parse_input():
            transcript_meta['appris'] = appris.to_json()
        tsl = TSL(row['TSL'])
        if tsl.parse_input():
            transcript_meta['tsl'] = tsl.to_json()
        if row['MANE_Select']:
            mane = MANE('select', row['MANE_Select'])
            transcript_meta['mane'] = mane.to_json()
        if row['MANE_Plus_Clinical']:
            mane = MANE('plus_clinical', row['MANE_Plus_Clinical'])
            transcript_meta['mane'] = mane.to_json()
        gencode_basic = GencodeBasic(row['gencode_basic'])
        if gencode_basic.parse_input():
            transcript_meta['gencode_basic'] = gencode_basic.to_json()
        biotype = Biotype(row["biotype"])
        if biotype.parse_input():
            transcript_meta['biotype'] = biotype.to_json()
        ensembl_canonical = EnsemblCanonical(row["Ensembl_Canonical"])
        if ensembl_canonical.parse_input():
            transcript_meta['canonical'] = ensembl_canonical.to_json()
    except Exception:
        pass
    return transcript_meta

def preload_transcript_meta(production_name, assembly):
    transcript_meta = {}
    with open(production_name + '_' + assembly + '_attrib.csv', encoding='UTF-8') as file:
        reader = csv.DictReader(file)
        for row in reader:
            stable_id = row['transcript ID']
            transcript_meta[stable_id] = get_transcript_meta(row)
    return transcript_meta


def preload_gene_name_metadata(production_name, assembly):
    gene_name_metadata = {}
    with open(production_name + "_" + assembly + "_gene_names.json", "r", encoding='UTF-8') as gene_name_metadata_file:
        gene_name_metadata_load = json.load(gene_name_metadata_file)
        for gene_name in gene_name_metadata_load:
            gene_name_metadata[gene_name['gene_stable_id']] = gene_name
    return gene_name_metadata


def preload_classifiers(classifier_path):
    meta_classifiers = {'appris': None, 'tsl': None, 'mane':None, 'gencode_basic':None, 'gene_biotype':None, 'canonical':None}
    for classifier in meta_classifiers:
        classifier_file = os.path.join(classifier_path, f"{classifier}.json")
        with open(classifier_file, encoding='UTF-8') as raw_classifier_file:
            classifier_items = json.load(raw_classifier_file)
        meta_classifiers[classifier] = classifier_items
    return meta_classifiers


if __name__ == '__main__':
    ARGS = common.utils.parse_args()
    CONFIG = common.utils.load_config(ARGS.config_file)
    SPECIES = ARGS.species
    MONGO_COLLECTION = ARGS.mongo_collection
    MONGO_CLIENT = MongoDbClient(CONFIG, MONGO_COLLECTION)
    if ARGS.collection:
        JSON_FILE = f'{ARGS.data_path}{ARGS.collection}/{ARGS.species}/{ARGS.species}_genes.json'
    else:
        JSON_FILE = f'{ARGS.data_path}{ARGS.species}/{ARGS.species}_genes.json'
    ASSEMBLY_NAME = ARGS.assembly
    CLASSIFIER_PATH = ARGS.classifier_path
    RELEASE = ARGS.release
    XREF_LOD_MAPPING_FILE = ARGS.xref_lod_mapping_file
    NV_RELEASE = int(RELEASE) - 53
    division = CONFIG.get(SPECIES, 'division')

    REFGET = RefgetDB(RELEASE, ASSEMBLY_NAME, CONFIG)
    if division in ['plants', 'protists', 'bacteria']:
        REFGET = RefgetDB(NV_RELEASE, ASSEMBLY_NAME, CONFIG)

    print("Loading CDS data")
    CDS_INFO = preload_cds_coords(ARGS.species, ARGS.assembly)
    print(f'Propagated {len(CDS_INFO)} CDS elements')
    PHASE_INFO = preload_exon_phases(ARGS.species, ARGS.assembly)
    print("Loading Transcript Metadata")
    TRANSCRIPT_METADATA = preload_transcript_meta(ARGS.species, ARGS.assembly)
    print("Loading Metadata Classifiers")
    METADATA_CLASSIFIER = preload_classifiers(CLASSIFIER_PATH)
    print("Loading Gene Name Metadata")
    GENE_NAME_METADATA = preload_gene_name_metadata(ARGS.species, ARGS.assembly)
    print("Loading e! xref db name to id.org prefix mappings")
    XREF_RESOLVER = XrefResolver(internal_mapping_file=XREF_LOD_MAPPING_FILE)
    URL_LOGGER = None
    ASSEMBLY, GENOME = get_genome_assembly(ASSEMBLY_NAME, MONGO_CLIENT)

    if ARGS.log_faulty_urls:
        URL_LOGGER = ThoasLogging(logging_file=f'url_log_{GENOME["id"]}', logger_name=f'url_logger_{GENOME["id"]}')

    print("Loading gene info into Mongo")

    load_gene_info(MONGO_CLIENT, JSON_FILE, CDS_INFO, ASSEMBLY, GENOME, PHASE_INFO, TRANSCRIPT_METADATA, METADATA_CLASSIFIER, GENE_NAME_METADATA, XREF_RESOLVER, REFGET, URL_LOGGER)

    TRANSLATIONS_FILE = f'{ARGS.species}_{ARGS.assembly}_translations.json'
    load_product_info(MONGO_CLIENT, TRANSLATIONS_FILE, GENOME['id'], REFGET)

    create_index(MONGO_CLIENT)
