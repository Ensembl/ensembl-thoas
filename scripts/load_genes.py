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

from common.utils import load_config, parse_args, format_cross_refs, \
    format_slice, format_exon, format_utr, format_cdna, format_protein, \
    flush_buffer, splicify_exons
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


def load_gene_info(mongo_client, json_file, cds_info, phase_info):
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
        'name': 'GRCh38'
    })

    genome = mongo_client.collection().find_one({
        'type': 'Genome',
        'name': 'GRCh38'
    })
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

            json_gene = {

                'type': 'Gene',
                'stable_id': f'{gene["id"]}.{str(gene["version"])}',
                'unversioned_stable_id': gene['id'],
                'version': gene['version'],
                'so_term': gene['biotype'],
                'name': gene['name'],
                # Note that the description comes the long way via xref
                # pipeline and includes a [source: string]
                'description': gene['description'],
                'slice': format_slice(
                    region_name=gene['seq_region_name'],
                    region_type=gene['coord_system']['name'],
                    default_region=default_region,
                    strand=int(gene['strand']),
                    assembly=assembly['id'],
                    start=int(gene['start']),
                    end=int(gene['end'])
                ),
                'transcripts': [
                    [transcript['id'] for transcript in gene['transcripts']]
                ],
                'genome_id': genome['id'],
                'cross_references': format_cross_refs(gene['xrefs'])
            }
            gene_buffer.append(json_gene)

            # Sort out some transcripts while we can see them
            for transcript in gene['transcripts']:
                transcript_buffer.append(format_transcript(
                    transcript=transcript,
                    gene_id=f'{gene["id"]}.{str(gene["version"])}',
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
                for product in transcript['translations']:
                    if product['ensembl_object_type'] == 'Translation':
                        protein_buffer.append(format_protein(product))

            gene_buffer = flush_buffer(mongo_client, gene_buffer)
            transcript_buffer = flush_buffer(mongo_client, transcript_buffer)
            protein_buffer = flush_buffer(mongo_client, protein_buffer)

    # Flush buffers at end of gene data
    if len(gene_buffer) > 0:
        mongo_client.collection().insert_many(gene_buffer)
    if len(transcript_buffer) > 0:
        mongo_client.collection().insert_many(transcript_buffer)
    if len(protein_buffer) > 0:
        mongo_client.collection().insert_many(protein_buffer)


def format_transcript(
        transcript, gene_id, region_type, region_name, genome_id,
        cds_info, phase_info, default_region, assembly
):
    '''
    Transform and supplement transcript information
    Args:
    transcript - directly from JSON file
    gene_id - the parent gene stable_id
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
    exon_list = []
    for exon in transcript['exons']:
        exon_list.append(
            format_exon(
                exon_stable_id=exon['id'],
                version=exon['version'],
                region_name=exon['seq_region_name'],
                region_strand=int(exon['strand']),
                exon_start=int(exon['start']),
                exon_end=int(exon['end']),
                region_type=region_type,
                default_region=default_region,
                assembly=assembly
            )
        )

    new_transcript = {
        'type': 'Transcript',
        'gene': gene_id,
        'stable_id': f'{transcript["id"]}.{str(transcript["version"])}',
        'unversioned_stable_id': transcript['id'],
        'version': transcript['version'],
        'so_term': transcript['biotype'],
        'name': transcript['name'] if 'name' in transcript else None,
        'description': transcript['description'] if 'description' in transcript else None,
        'slice': format_slice(
            region_name=region_name,
            region_type=region_type,
            default_region=default_region,
            strand=int(transcript['strand']),
            assembly=assembly,
            start=int(transcript['start']),
            end=int(transcript['end'])
        ),
        'exons': exon_list,
        'genome_id': genome_id,
        'cross_references': format_cross_refs(transcript['xrefs'])
    }

    # Now for the tricky stuff around CDS
    if transcript['id'] in cds_info:
        relative_cds_start = cds_info[transcript['id']]['relative_start']
        relative_cds_end = cds_info[transcript['id']]['relative_end']
        cds_start = cds_info[transcript['id']]['start']
        cds_end = cds_info[transcript['id']]['end']

        new_transcript['splicing'] = {
            '__typename': 'ProteinCodingSplicing',
            'product_type': 'Protein',
            '5_prime_utr': format_utr(
                transcript, relative_cds_start, relative_cds_end, cds_start,
                cds_end, downstream=False
            ),
            '3_prime_utr': format_utr(
                transcript, relative_cds_start, relative_cds_end, cds_start,
                cds_end, downstream=True
            ),
            'cds': {
                'start': cds_start,
                'end': cds_end,
                'relative_start': relative_cds_start,
                'relative_end': relative_cds_end,
                'nucleotide_length': cds_info[transcript['id']]['spliced_length'],
                'protein_length': cds_info[transcript['id']]['spliced_length'] // 3
            },
            'cdna': format_cdna(transcript),
            'protein_ids': [translation['id'] for translation in transcript['translations']],
            'spliced_exons': splicify_exons(exon_list, transcript['id'], phase_info)
        }

    return new_transcript


def preload_cds_coords(production_name):
    '''
    CDS coords will be pre-loaded into a file from the Perl API. Otherwise
    hideous calculation required to get the relative coordinates
    '''
    cds_buffer = {}

    with open(production_name + '.csv') as file:
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


def preload_exon_phases(production_name):
    '''
    Phases are hard to calculate on the fly. They are instead dumped into a
    pile of splicing information. Turn it into a lookup structure.
    LIMITED TO SINGLE PRODUCTS PER TRANSCRIPT
    '''

    phase_lookup = {}

    with open(production_name + '_phase.csv') as file:
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

    ARGS = parse_args()

    MONGO_CLIENT = MongoDbClient(load_config(ARGS.config_file))
    JSON_FILE = ARGS.data_path + ARGS.species + '/' + ARGS.species + '_genes.json'
    print("Loading CDS data")
    CDS_INFO = preload_cds_coords(ARGS.species)
    print(f'Propagated {len(CDS_INFO)} CDS elements')
    PHASE_INFO = preload_exon_phases(ARGS.species)
    print("Loading gene info into Mongo")
    load_gene_info(MONGO_CLIENT, JSON_FILE, CDS_INFO, PHASE_INFO)
    create_index(MONGO_CLIENT)
