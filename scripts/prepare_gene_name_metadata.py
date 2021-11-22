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

import argparse, re, json
from mysql.connector import MySQLConnection, Error
import common.utils


def retrieve_gene_name_metadata(sp_production_name, sp_assembly_name, mysql_cursor):

    species_genes_sql = get_species_genes_sql()
    mysql_cursor.execute(species_genes_sql.format(sp_production_name))
    genes = mysql_cursor.fetchall()

    gene_names = []

    extractor, backup_extractor = [extract_info_from_description_column, extract_info_using_display_xref_id] \
        if sp_production_name == 'triticum_aestivum' \
        else [extract_info_using_display_xref_id, extract_info_from_description_column]

    for gene in genes:

        gene_name_info = {'gene_stable_id': gene.get('stable_id'),
                          'gene_description': gene.get('description'),
                          # maps to metadata->name->accession_id
                          'xref_primary_acc': None,
                          # Extra info
                          'xref_display_label': None,
                          # maps to metadata->name->value
                          'xref_description': None,
                          # maps to metadata->name->source->id
                          'external_db_name': None,
                          # maps to metadata->name->source->name
                          'external_db_display_name': None,
                          # maps to metadata->name->source->release
                          'external_db_release': None
                          }

        gene_name_info = extractor(gene, gene_name_info)
        if gene_name_info.get('external_db_name') is None: gene_name_info = backup_extractor(gene, gene_name_info)

        # Add all the possible information retrieved. Also add if no 'display_xref_id' and 'description'.
        gene_names.append(gene_name_info)

    with open(sp_production_name + "_" + sp_assembly_name + "_gene_names.json", "w") as write_file:
        json.dump(gene_names, write_file)


def extract_info_from_description_column(gene, gene_name_info):

    if gene.get('description') is not None:
        # Search for content starting with 'Source' within square brackets
        match = re.search(r'\[Source.*?\]', gene.get('description'))
        if match:
            gene_name_info['xref_description'] = gene.get('description')
            # Remove square brackets
            match_string = match[0][1:-1]
            matched_string_elements = match_string.split(';')
            for element in matched_string_elements:
                key, value = element.split(':')
                if key == 'Source':
                    gene_name_info['external_db_name'] = value
                    # Get correct source if source information has extra information like in 'Projected genes'
                    if value.startswith('Projected from'):
                        gene_name_info['external_db_name'] = value.split()[-1]

                    # ExternalDBDisplayName(Source Name) will be same as ExternalDBName(Source ID) when
                    # we extract source from description
                    gene_name_info['external_db_display_name'] = gene_name_info['external_db_name']
                if key == 'Acc':
                    gene_name_info['xref_primary_acc'] = value
    return gene_name_info


def extract_info_using_display_xref_id(gene, gene_name_info):

    species_display_xref_sql = get_species_display_xref_sql()
    if gene.get('display_xref_id') is not None:
        # Get display_xref and external db details if 'display_xref_id' exists
        mysql_cursor.execute(species_display_xref_sql.format(gene.get('stable_id')))
        gene_name_info = mysql_cursor.fetchone()

    return gene_name_info


def get_species_genes_sql():

    return '''
    select stable_id, display_xref_id, description from gene 
    join seq_region using (seq_region_id) 
    join coord_system using (coord_system_id) 
    join meta using (species_id) 
    where meta_key='species.production_name' and meta_value="{}"
    '''

def get_species_display_xref_sql():

    return '''
    select gene.stable_id as gene_stable_id, gene.description as gene_description, 
    xref.dbprimary_acc as xref_primary_acc, xref.display_label as xref_display_label, 
    xref.description as xref_description, external_db.db_name as external_db_name, 
    external_db.db_release as external_db_release, external_db.db_display_name as external_db_display_name 
    from gene inner join xref on gene.display_xref_id = xref.xref_id 
    inner join external_db on xref.external_db_id = external_db.external_db_id 
    where gene.stable_id="{}"
    '''


if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description='Create a JSON file with Gene Name Metadata'
    )

    parser.add_argument(
        '--config_file',
        help='File path to the config file containing MySQL credentials and species information',
        default='../load.conf'
    )
    parser.add_argument(
        '--section_name',
        help='Section of the config file containing required credentials'
    )

    args = parser.parse_args()

    config = common.utils.load_config(args.config_file)

    conn = MySQLConnection(
        host=config.get(args.section_name, 'host'),
        user=config.get(args.section_name, 'user'),
        password="",
        database=config.get(args.section_name, 'database'),
        port=config.get(args.section_name, 'port')
    )

    mysql_cursor = conn.cursor(dictionary=True)

    sp_production_name = config.get(args.section_name, 'production_name')
    sp_assembly_name = config.get(args.section_name, 'assembly')

    retrieve_gene_name_metadata(sp_production_name, sp_assembly_name, mysql_cursor)
