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

import csv
import ijson
import pymongo

import common.utils
from common.mongo import MongoDbClient

def create_index(mongo_client):
    '''
    Create indexes for searching useful things on genes, transcripts etc.
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


def load_gene_info(mongo_client, json_file, cds_info, assembly_name, phase_info):
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
    protein_buffer = []


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
    # at least until there's a process for alt-alleles etc.
    default_region = True
    print('Loaded assembly ' + assembly['name'])


    required_keys = ('name', 'description')
    with open(json_file) as file:
        print('Chunk')
        for gene in ijson.items(file, 'item'):

            for key in required_keys:
                if key not in gene:
                    gene[key] = None

            try:
                gene_xrefs = common.utils.format_cross_refs(gene['xrefs'])
            except KeyError:
                gene_xrefs = []

            json_gene = {

                'type': 'Gene',
                'stable_id': common.utils.get_stable_id(gene["id"], gene["version"]),
                'unversioned_stable_id': gene['id'],
                'version': gene['version'],
                'so_term': gene['biotype'],
                'symbol': gene['name'],
                # Note that the description comes the long way via xref
                # pipeline and includes a [source: string]
                'name': gene['description'],
                'slice': common.utils.format_slice(
                    region_name=gene['seq_region_name'],
                    region_type=gene['coord_system']['name'],
                    default_region=default_region,
                    strand=int(gene['strand']),
                    assembly=assembly['id'],
                    start=int(gene['start']),
                    end=int(gene['end'])
                ),
                'transcripts': [
                    [common.utils.get_stable_id(transcript["id"], transcript["version"]) \
                        for transcript in gene['transcripts']]
                ],
                'genome_id': genome['id'],
                'external_references': gene_xrefs
            }
            gene_buffer.append(json_gene)

            # Sort out some transcripts while we can see them
            for transcript in gene['transcripts']:
                transcript_buffer.append(format_transcript(
                    transcript=transcript,
                    gene=gene,
                    region_type=gene['coord_system']['name'],
                    region_name=gene['seq_region_name'],
                    genome_id=genome['id'],
                    cds_info=cds_info,
                    phase_info=phase_info,
                    default_region=default_region,
                    assembly=assembly['id']
                ))

            # Add products
            for transcript in gene['transcripts']:
                if 'translations' in transcript:
                    for product in transcript['translations']:
                        # Add mature RNA here
                        if product['ensembl_object_type'] == 'translation':
                            protein_buffer.append(common.utils.format_protein(product, genome['id']))

            gene_buffer = common.utils.flush_buffer(mongo_client, gene_buffer)
            transcript_buffer = common.utils.flush_buffer(mongo_client, transcript_buffer)
            protein_buffer = common.utils.flush_buffer(mongo_client, protein_buffer)

    # Flush buffers at end of gene data
    if len(gene_buffer) > 0:
        mongo_client.collection().insert_many(gene_buffer)
    if len(transcript_buffer) > 0:
        mongo_client.collection().insert_many(transcript_buffer)
    if len(protein_buffer) > 0:
        mongo_client.collection().insert_many(protein_buffer)


def format_transcript(
        transcript, gene, region_type, region_name, genome_id,
        cds_info, phase_info, default_region, assembly
):
    '''
    Transform and supplement transcript information
    Args:
    transcript - directly from JSON file
    gene - the parent gene data
    region_type - a shortcut to having to look up the region again
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
                region_strand=int(exon['strand']),
                region_type=region_type,
                default_region=default_region,
                assembly=assembly
            )
        )

    try:
        transcript_xrefs = common.utils.format_cross_refs(transcript['xrefs'])
    except KeyError:
        transcript_xrefs = []

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
                'end':gene['end'],
                'strand':gene['strand']
            },
            child_params={
                'start': transcript['start'],
                'end': transcript['end']
            }
        ),
        'slice': common.utils.format_slice(
            region_name=region_name,
            region_type=region_type,
            default_region=default_region,
            strand=int(transcript['strand']),
            assembly=assembly,
            start=int(transcript['start']),
            end=int(transcript['end'])
        ),
        'genome_id': genome_id,
        'external_references': transcript_xrefs,
        'product_generating_contexts': [],
        'spliced_exons': common.utils.splicify_exons(ordered_formatted_exons, transcript)
    }

    # Now for the tricky stuff around CDS
    if transcript['id'] in cds_info:
        relative_cds_start = cds_info[transcript['id']]['relative_start']
        relative_cds_end = cds_info[transcript['id']]['relative_end']
        cds_start = cds_info[transcript['id']]['start']
        cds_end = cds_info[transcript['id']]['end']
        spliced_length = cds_info[transcript['id']]['spliced_length']

        # Insert multiple product handling here when we know what it will look like
        # Pick the first to be default
        defaults = [False] * (len(transcript['translations']) - 1)
        defaults.append(True)

        for translation in transcript['translations']:
            new_transcript['product_generating_contexts'].append(
                {
                    'product_type': 'Protein', # probably
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
                        'protein_length': spliced_length // 3
                    },
                    # Infer the "products" in the resolver. This is a join.
                    'product_id': common.utils.get_stable_id(translation["id"], translation["version"]),
                    'phased_exons': common.utils.phase_exons(ordered_formatted_exons, transcript['id'], phase_info),
                    # We'll know default later when it becomes relevant
                    'default': defaults.pop(),
                    'cdna': common.utils.format_cdna(transcript)
                }
            )

    return new_transcript


def preload_cds_coords(production_name, assembly):
    '''
    CDS coords will be pre-loaded into a file from the Perl API. Otherwise
    hideous calculation required to get the relative coordinates
    '''
    cds_buffer = {}

    with open(production_name + '_' + assembly + '.csv') as file:
        reader = csv.reader(file)
        next(reader, None) # skip header line
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

    with open(production_name + '_' + assembly + '_phase.csv') as file:
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


if __name__ == '__main__':

    ARGS = common.utils.parse_args()

    MONGO_CLIENT = MongoDbClient(common.utils.load_config(ARGS.config_file))
    if ARGS.collection:
        JSON_FILE = f'{ARGS.data_path}{ARGS.collection}/{ARGS.species}/{ARGS.species}_genes.json'
    else:
        JSON_FILE = f'{ARGS.data_path}{ARGS.species}/{ARGS.species}_genes.json'
    ASSEMBLY = ARGS.assembly
    print("Loading CDS data")
    CDS_INFO = preload_cds_coords(ARGS.species, ARGS.assembly)
    print(f'Propagated {len(CDS_INFO)} CDS elements')
    PHASE_INFO = preload_exon_phases(ARGS.species, ARGS.assembly)
    print("Loading gene info into Mongo")
    load_gene_info(MONGO_CLIENT, JSON_FILE, CDS_INFO, ASSEMBLY, PHASE_INFO)
    create_index(MONGO_CLIENT)
