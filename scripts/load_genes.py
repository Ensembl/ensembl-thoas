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

import ijson
import gzip
from common.utils import load_config
from common.mongo import mongo_db_thing
import csv
import argparse


def create_index(db):
    db.collection().create_index([
        ('name', 'genome_id')
    ], name='names_of_things')
    db.collection().create_index([
        ('genome_id', 'stable_id', 'type')
    ], name='stable_id')
    db.collection().create_index([
        ('genome_id', 'type')
    ], name='feature_type')
    db.collection().create_index([
        ('genome_id', 'slice.region.name', 'slice.location.start', 'slice.location.end')
    ], name='location_index')
    db.collection().create_index([
        ('genome_id', 'gene')
    ], name='gene_foreign_key')
    db.collection().create_index([
        ('genome_id', 'transcript')
    ], name='transcript_foreign_key')


def load_gene_info(db, json_file, cds_info):
    """
    Reads from "custom download" gene JSON dumps and converts to suit
    Core Data Modelling schema.
    """
    gene_buffer = []
    transcript_buffer = []

    assembly = db.collection().find_one({
        'type': 'Assembly',
        'name': 'GRCh38'
    })

    genome = db.collection().find_one({
        'type': 'Genome',
        'name': 'GRCh38'
    })

    print('Loaded assembly ' + assembly['name'])
    required_keys = ('name', 'description')
    with gzip.open(json_file) as file:
        print('Chunk')
        for gene in ijson.items(file, 'item'):

            for key in required_keys:
                if key not in gene:
                    gene[key] = None

            gene_buffer.append({
                'type': 'Gene',
                'stable_id': gene['id'],
                'so_term': gene['biotype'],
                'name': gene['name'],
                # Note that the description comes the long way via xref pipeline
                # and includes a [source: string]
                'description': gene['description'],
                'slice': {
                    'type': 'Slice',
                    'location': {
                        # For some reason, positions are strings in the file
                        'start': int(gene['start']),
                        'end': int(gene['end']),
                        # more complex when circular!
                        'length': int(gene['end']) - int(gene['start']) + 1,
                        'location_type': gene['coord_system']['name']
                    },
                    'region': {
                        'name': gene['seq_region_name'],
                        'assembly': assembly['id'],
                        'strand': {
                            'code': 'forward' if int(gene['strand']) > 0 else 'reverse',
                            'value': gene['strand']
                        }
                    }
                },
                'transcripts': [
                    [transcript['id'] for transcript in gene['transcripts']]
                ],
                'genome_id': genome['id']
            })

            # Sort out some transcripts while we can see them
            for transcript in gene['transcripts']:
                transcript_buffer.append(format_transcript(
                    transcript=transcript,
                    gene_id=gene['id'],
                    region_type=gene['coord_system']['name'],
                    region_name=,gene['seq_region_name']
                    region_strand=gene['strand'],
                    assembly_id=assembly['id'],
                    genome_id=genome['id'],
                    cds_info=cds_info
                ))

            if len(gene_buffer) > 1000:
                print('Pushing 1000 genes into Mongo')
                db.collection().insert_many(gene_buffer)
                print('Done')
                gene_buffer = []

            if len(transcript_buffer) > 1000:
                print('Loading 1000 transcripts into Mongo')
                db.collection().insert_many(transcript_buffer)
                transcript_buffer = []


def format_transcript(
    transcript, gene_id, region_type, region_name, region_strand, assembly_id,
    genome_id, cds_info
):
    'Transform and supplement transcript information'

    exon_list = []
    for exon in transcript['exons']:
        exon_list.append(
            format_exon(
                exon_stable_id=exon['id'],
                region_name=exon['seq_region_name'],
                region_strand=int(exon['strand']),
                exon_start=int(exon['start']),
                exon_end=int(exon['end']),
                location_type=region_type
            )
        )

    new_transcript = {
        'type': 'Transcript',
        'gene': gene_id,
        'stable_id': transcript['id'],
        'so_term': transcript['biotype'],
        'name': transcript['name'] if 'name' in transcript else None,
        'description': transcript['description'] if 'description' in transcript else None,
        'slice': {
            'type': 'Slice',
            'location': {
                'start': int(transcript['start']),
                'end': int(transcript['end']),
                'length': int(transcript['end']) - int(transcript['start']) + 1,
                'location_type': region_type
            },
            'region': {
                'name': region_name,
                'assembly': assembly_id,
                'strand': {
                    'code': 'forward' if int(region_strand) > 0 else 'reverse',
                    'value': region_strand
                }
            }
        },
        'exons': exon_list,
        'genome_id': genome_id,
        'cds': {
            'relative_slice': {
                'location': {
                    'start': cds_info[transcript['id']]['relative_start'],
                    'end': cds_info[transcript['id']]['relative_end'],
                    'length': (
                        cds_info[transcript['id']]['spliced_length']
                    )
                }
            }
        }
    }
    return new_transcript


def format_exon(exon_stable_id, region_name, region_strand, exon_start,
                exon_end, location_type):
    'Turn transcript-borne information into an Exon entity'
    return {
        'type': 'Exon',
        'stable_id': exon_stable_id,
        'slice': {
            'region': {
                'name': region_name,
                'strand': {
                    'code': 'forward' if region_strand > 0 else 'reverse',
                    'value': region_strand
                },
                'assembly': 'GRCh38'
            },
            'location': {
                'start': exon_start,
                'end': exon_end,
                'length': exon_end - exon_start + 1,
                'location_type': 'chromosome'
            },
            'default': True
        }
    }


def format_metadata():
    '"metadata" is all the things that we do not want to model better'
    pass


def preload_CDS_coords(production_name):
    '''
    CDS coords will be pre-loaded into a file from the Perl API. Otherwise
    hideous calculation required to get the relative coordinates
    '''
    cds_buffer = {}

    with open(production_name + '.csv') as file:
        reader = csv.reader(file)
        for row in reader:
            cds_buffer[row[0]] = {
                'start': row[1],
                'end': row[2],
                'relative_start': row[3],
                'relative_end': row[4],
                'spliced_length': row[5]
            }
    return cds_buffer


def parse_args():
    parser = argparse.ArgumentParser(
        description='Load JSON Search dumps into MongoDB for GraphQL'
    )
    parser.add_argument(
        '--config_file',
        help='File path containing MongoDB credentials',
        default='../mongo.conf'
    )
    parser.add_argument(
        '--data_path',
        help='Path to JSON files from the "Gene search" dumps',
        default='/hps/nobackup2/production/ensembl/ensprod/search_dumps/release-99/vertebrates/json/'
    )
    parser.add_argument(
        '--species',
        help='The production name for a (sic) Ensembl species',
        default='homo_sapiens'
    )
    return parser.parse_args()

if __name__ == '__main__':

    args = parse_args()

    db = mongo_db_thing(load_config(args.config_file))
    json_file = args.data_path + args.species + '.csv'
    print("Loading CDS data")
    cds_info = preload_CDS_coords(args.species)
    print(f'Propagated {len(cds_info)} CDS elements'
    print("Loading gene info into Mongo")
    load_gene_info(db, json_file, cds_info)
    create_index(db)
