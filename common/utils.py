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

from configparser import ConfigParser
import argparse

def load_config(filename):
    'Load a config, return a ConfigParser object'

    cp = ConfigParser(default_section='MONGO DB')
    cp.read(filename)
    return cp


def parse_args():
    '''
    Common parameter parsing for data loading scripts
    '''
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
        default='/hps/nobackup2/production/ensembl/ensprod/search_dumps/release-100/vertebrates/json/'
    )
    parser.add_argument(
        '--species',
        help='The production name for a (sic) Ensembl species',
        default='homo_sapiens'
    )
    return parser.parse_args()


def format_cross_refs(xrefs):
    '''
    "metadata" is all the things that we do not want to model better
    Convert a list of xrefs into schema-compliant sub-documents
    '''

    # GO xrefs (or associated xrefs) are a different format inline
    json_xrefs = []
    for x in xrefs:
        doc = None
        if 'db_display' not in x:
            # This may be a GO xref
            doc = {
                'id': x['primary_id'],
                'name': x['display_id'],
                'description': '',
                'source': {
                    'name': x['dbname'],
                    'id': x['dbname']
                }
            }
        else:
            doc = {
                'id': x['primary_id'],
                'name': x['display_id'],
                'description': x['description'],
                'source': {
                    'name': x['db_display'],
                    'id': x['dbname']
                }
            }
        json_xrefs.append(doc)
    return json_xrefs


def format_slice(region_name, region_type, default_region, strand, assembly,
                 start, end):
    '''
    Creates regular slices with locations and regions

    region_name: The string representing a region (perhaps chromosome 1)
    region_type: What kind of thing is the region? e.g. chromosome, plasmid
    default_region[Boolean]: Is this a good default region, i.e. not a patch
    strand[int]: Forward = 1, Reverse = -1, 0 = No idea or not relevant
    assembly: A string naming the assembly the region is from
    start[int]: Start coordinate, usually low to high except when circular
    end[int]: End coordinate
    '''
    return {
        'region': {
            'name': region_name,
            'strand': {
                'code': 'forward' if strand > 0 else 'reverse',
                'value': strand
            },
            'assembly': assembly
        },
        'location': {
            'start': int(start),
            'end': int(end),
            'length': int(end) - int(start) + 1,
            'location_type': region_type
        },
        'default': default_region
    }


def format_exon(exon_stable_id, version, region_name, region_strand,
                exon_start, exon_end, region_type, default_region, assembly):
    '''
    Turn transcript-borne information into an Exon entity

    exon_stable_id: Unversioned stable ID
    version: Version of exon
    region_name: The string representing a region (perhaps "1")
    region_strand: Forward = 1, Reverse = -1, 0 = No idea or not relevant
    exon_start: Start coordinate, usually low to high except when circular
    exon_end: End coordinate
    region_type: What kind of thing is the region? e.g. chromosome, plasmid
    default_region: Is this a good default region, i.e. not a patch
    assembly: A string naming the assembly the region is from
    '''
    default_region = True
    return {
        'type': 'Exon',
        'stable_id': f'{exon_stable_id}.{str(version)}',
        'unversioned_stable_id': exon_stable_id,
        'version': version,
        'slice': format_slice(region_name, region_type, default_region,
                              region_strand, assembly, exon_start, exon_end)
    }


def splicify_exons(exons, transcript_id, phase_lookup):
    '''
    Given formatted exon data, and a phase lookup, return a spliced exon
    wrapper for each element with start and end phases. Exons MUST be in
    coding order
    '''

    splicing = []
    i = 0
    for exon in exons:
        (start_phase, end_phase) = phase_lookup[transcript_id][exon['stable_id']]
        splicing.append({
            'start_phase': start_phase,
            'end_phase': end_phase,
            'index': i,
            'exon': exon
        })
        i += 1
    return splicing


def format_utr(
        transcript, relative_cds_start, relative_cds_end, absolute_cds_start,
        absolute_cds_end, downstream
):
    '''
    From one transcript's exons generate an inferred UTR
    downstream  - Boolean, False = 5', True = 3'
    '''
    # Presumably broken crossing ori in circular case,
    if (downstream and transcript['strand'] == 1):
        utr_type = '3_prime_utr'
        start = absolute_cds_end + 1
        end = transcript['end']
        relative_start = relative_cds_end + 1
        relative_end = transcript['end'] - transcript['start'] + 1
    elif (downstream and transcript['strand'] == -1):
        utr_type = '3_prime_utr'
        start = absolute_cds_end - 1
        end = transcript['start']
        relative_start = relative_cds_end - 1
        relative_end = 1
    elif (downstream is False and transcript['strand'] == 1):
        utr_type = '5_prime_utr'
        start = transcript['start']
        end = absolute_cds_start - 1
        relative_start = 1
        relative_end = relative_cds_start -1
    else:
        # reverse stranded 5'
        utr_type = '5_prime_utr'
        start = transcript['end']
        end = absolute_cds_start + 1
        relative_start = 1
        relative_end = relative_cds_start + 1

    return {
        'type': utr_type,
        'start': start,
        'end': end,
        'relative_start': relative_start,
        'relative_end':  relative_end
    }


def format_cdna(transcript):
    '''
    With the transcript and exon coordinates, and strand, compute the CDNA
    length and so on.
    '''
    strand = transcript['strand']

    if strand == 1:
        start = transcript['start']
        end = transcript['end']
        relative_start = 1
        relative_end = 0
        for exon in transcript['exons']:
            relative_end += exon['end'] - exon['start'] + 1

    # Needs sequence too. Add it soon!
    return {
        'start': start,
        'end': end,
        'relative_start': relative_start,
        'relative_end': relative_end,
    }


def format_protein(protein):
    '''
    Create a protein representation from limited data
    '''

    return {
        'type': 'protein',
        'stable_id': protein['id'],
        'unversioned_stable_id': protein['id'] + '.' + protein['version'],
        'version': protein['version'],
        # for foreign key behaviour
        'transcript_id': protein['transcript_id'],
        'so_term': 'polypeptide' # aka SO:0000104
    }


def flush_buffer(mongo_client, buffer):
    'Check if a buffer needs flushing, and insert documents when it does'
    if len(buffer) > 1000:
        print('Pushing 1000 documents into Mongo')
        mongo_client.collection().insert_many(buffer)
        print('Done')
        buffer = []
    return buffer
