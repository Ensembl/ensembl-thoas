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


def load_gene_info(db):
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
    with gzip.open('../../graphql-source-data/homo_sapiens_genes.json.gz') as file:
        print('Chunk')
        for gene in ijson.items(file, 'item'):
            # if gene['source'] != 'ensembl':
                # pass
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
                        },
                    }
                },
                'transcripts': [
                    [transcript['id'] for transcript in gene['transcripts']]
                ],
                'genome_id': genome['id']
            })

            # Sort out some transcripts while we can see them
            for transcript in gene['transcripts']:
                exon_list = []
                for exon in transcript['exons']:
                    exon_list.append(
                        format_exon(
                            exon['id'],
                            exon['seq_region_name'],
                            int(exon['strand']),
                            int(exon['start']),
                            int(exon['end'])
                        )
                    )
                transcript_buffer.append({
                    'type': 'Transcript',
                    'gene': gene['id'],
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
                    'exons': [
                        exon for exon in exon_list
                    ],
                    'genome_id': genome['id']
                })

            if len(gene_buffer) > 1000:
                print('Pushing 1000 genes into Mongo')
                db.collection().insert_many(gene_buffer)
                print('Done')
                gene_buffer = []

            if len(transcript_buffer) > 1000:
                print('Loading 1000 transcripts into Mongo')
                db.collection().insert_many(transcript_buffer)
                transcript_buffer = []


def format_exon(exon_stable_id, region_name, region_strand, exon_start,
                exon_end):
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


if __name__ == '__main__':
    db = mongo_db_thing(load_config('../mongo.conf'))
    load_gene_info(db)
    create_index(db)
