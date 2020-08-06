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
    parser = base_parse_args()
    parser.add_argument(
        '--data_path',
        help='Path to JSON files from the "Gene search" dumps'
    )
    parser.add_argument(
        '--collection',
        help='If the assembly is kept in a collection by Ensembl, specify the collection name'
    )
    return parser.parse_args()


def base_parse_args():
    'Base argument setup'
    parser = argparse.ArgumentParser(
        description='Load JSON Search dumps into MongoDB for GraphQL'
    )
    parser.add_argument(
        '--config_file',
        help='File path containing MongoDB credentials',
        default='../mongo.conf'
    )
    parser.add_argument(
        '--species',
        help='The production name for a (sic) Ensembl species',
        default='homo_sapiens'
    )
    parser.add_argument(
        '--assembly',
        help='The assembly name for an Ensembl species',
        default='GRCh38'
    )
    return parser


def wrapper_parse_args():
    '''
    Very common parameter parsing for data loading scripts
    '''
    parser = base_parse_args()
    parser.add_argument(
        '--base_data_path',
        help='Path to JSON files, excluding release and division folders',
        default='/hps/nobackup2/production/ensembl/ensprod/search_dumps/'
    )
    parser.add_argument(
        '--release',
        help='The current release of Ensembl. Not the EG release'
    )
    return parser.parse_args()


def get_stable_id(iid, version):
    'Get a stable_id with or without a version'
    stable_id = f'{iid}.{str(version)}' if version else iid
    return stable_id


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


def format_exon(exon, region_name, region_strand, region_type, default_region, assembly, transcript):
    '''
    Turn transcript-borne information into an Exon entity

    exon: The exon to format, containing start, end, version, stable_id
    region_name: The string representing a region (perhaps "1")
    region_strand: Forward = 1, Reverse = -1, 0 = No idea or not relevant
    region_type: What kind of thing is the region? e.g. chromosome, plasmid
    default_region: Is this a good default region, i.e. not a patch
    assembly: A string naming the assembly the region is from
    transcript: The transcript that contains this exon
    '''

    relative_location = calculate_relative_coords(
        parent_params={
            'start': transcript['start'],
            'end': transcript['end'],
            'strand': transcript['strand']
        },
        child_params={
            'start': exon['start'],
            'end': exon['end']
        }
    )
    return {
        'type': 'Exon',
        'stable_id': get_stable_id(exon['stable_id'], exon['version']),
        'unversioned_stable_id': exon['stable_id'],
        'version': exon['version'],
        'slice': format_slice(region_name, region_type, default_region,
                              region_strand, assembly, exon['start'], exon['end']),
        'relative_location': relative_location
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
        (start_phase, end_phase) = phase_lookup[transcript_id][exon['unversioned_stable_id']]
        splicing.append({
            'start_phase': start_phase,
            'end_phase': end_phase,
            'index': i,
            'exon': exon
        })
        i += 1
    return splicing


def format_utr(
        transcript, absolute_cds_start, absolute_cds_end, downstream
):
    '''
    From one transcript's exons generate an inferred UTR
    downstream  - Boolean, False = 5', True = 3'
    Note the arguments are CDS coords, not UTR coords, lots of offsets needed
    '''
    if (
            downstream
            and transcript['end'] == absolute_cds_end
            and transcript['strand'] == 1
            or (
                downstream is False
                and transcript['start'] == absolute_cds_start
                and transcript['strand'] == 1
            )
            or (
                downstream
                and transcript['start'] == absolute_cds_start
                and transcript['strand'] == -1
            )
            or (
                downstream is False
                and transcript['end'] == absolute_cds_end
                and transcript['strand'] == -1
            )
        ):
        # No UTR here: Move along.
        return None

    # Presumably broken crossing ori in circular case,
    if (downstream and transcript['strand'] == 1):
        utr_type = '3_prime_utr'
        start = absolute_cds_end + 1
        end = transcript['end']
        relative_start = absolute_cds_end - transcript['start'] + 2
        relative_end = transcript['end'] - transcript['start'] + 1
    elif (downstream and transcript['strand'] == -1):
        utr_type = '3_prime_utr'
        start = transcript['start']
        end = absolute_cds_start - 1
        relative_start = transcript['end'] - absolute_cds_start + 2
        # i.e. first base of transcript in e! coords is the end of a reverse
        # stranded 3' UTR
        relative_end = transcript['end'] - transcript['start'] + 1
    elif (downstream is False and transcript['strand'] == 1):
        utr_type = '5_prime_utr'
        start = transcript['start']
        end = absolute_cds_start - 1
        relative_start = 1
        relative_end = absolute_cds_start - transcript['start']
    else:
        # reverse stranded 5'
        utr_type = '5_prime_utr'
        start = absolute_cds_end + 1
        end = transcript['end']
        relative_start = 1
        relative_end = transcript['end'] - absolute_cds_end

    return {
        'type': utr_type,
        'start': start,
        'end': end,
        'relative_start': relative_start,
        'relative_end':  relative_end
    }


def format_cdna(transcript):
    '''
    With the transcript and exon coordinates, compute the CDNA
    length and so on.
    '''

    start = transcript['start']
    end = transcript['start']

    relative_start = 1
    relative_end = 0 # temporarily
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
        'type': 'Protein',
        'unversioned_stable_id': protein['id'],
        'stable_id': get_stable_id(protein['id'], protein['version']),
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


def calculate_relative_coords(parent_params, child_params):
    '''
    Calculates a tuple of relative start, relative end and length from genomic coords
    of the parent feature and its child. Coords respect reading frame, i.e. a reverse
    stranded feature will have relative coords going from low to high.
    The input coordinates are always low-to-high in the forward stranded sense

    parent_params = {
        'start': ...,
        'end': ...,
        'strand': ...
    }

    child_params = {
        'start': ...,
        'end': ...
    }
    '''

    relative_location = {
        'length': child_params['end'] - child_params['start'] + 1
    }

    if parent_params['strand'] == 1:
        # i.e. 5' offset
        relative_start = child_params['start'] - parent_params['start'] + 1
        relative_end = child_params['end'] - parent_params['start'] + 1
    else:
        relative_start = parent_params['end'] - child_params['end'] + 1
        relative_end = parent_params['end'] - child_params['start'] + 1

    relative_location['start'] = relative_start
    relative_location['end'] = relative_end
    return relative_location
