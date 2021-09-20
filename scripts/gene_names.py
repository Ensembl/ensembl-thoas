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


parser = argparse.ArgumentParser(description='Create Genome Store to use with Species selector')
parser.add_argument('--host', help='DB server host',  required=True)
parser.add_argument('--user', help='DB user', required=True)
parser.add_argument('--port', help='DB port', required=True)
parser.add_argument('--species', help='Species name(Production name)', required=True)
parser.add_argument('--assembly', help='Assembly name',  required=True)
parser.add_argument('--database', help='Database name',  required=True)
parser.add_argument('--collection', help='Is it a collection',  default=False)

args = parser.parse_args()

if args.collection:
    species_genes = "select stable_id display_xref_id, description from gene " \
                       "join seq_region using (seq_region_id) " \
                       "join coord_system using (coord_system_id) " \
                       "join meta using (species_id) " \
                       "where meta_key='species.production_name' and meta_value='{}'"
else:
    species_genes = "SELECT stable_id, display_xref_id, description FROM gene"


species_display_xref = "select gene.stable_id as gene_stable_id, " \
                            "gene.description as gene_description, " \
                            "xref.dbprimary_acc as xref_primary_acc, " \
                            "xref.display_label as xref_display_label, " \
                            "xref.description as xref_description, " \
                            "external_db.db_name as external_db_name, " \
                            "external_db.db_release as external_db_release, " \
                            "external_db.db_display_name as external_db_display_name " \
                            "from gene " \
                            "inner join xref " \
                            "on gene.display_xref_id = xref.xref_id " \
                            "inner join external_db " \
                            "on xref.external_db_id = external_db.external_db_id " \
                            "where gene.stable_id='{}'"

conn = MySQLConnection(
            host=args.host,
            user=args.user,
            password="",
            database=args.database,
            port=args.port
        )

mysql_cursor = conn.cursor(dictionary=True)

mysql_cursor.execute(species_genes.format(args.species)) if args.collection else mysql_cursor.execute(species_genes)

genes = mysql_cursor.fetchall()
gene_names = []
for gene in genes:

    gene_name_info = {'gene_stable_id': gene.get('stable_id'),
                      'gene_description': gene.get('description'),
                      'xref_primary_acc': None,
                      'xref_display_label': None,
                      'xref_description': None,
                      'external_db_name': None,
                      'external_db_display_name': None,
                      'external_db_release': None
                      }

    if gene.get('display_xref_id') is not None:

        # Get display_xref and external db details if 'display_xref_id' exists
        mysql_cursor.execute(species_display_xref.format(gene.get('stable_id')))

        # Add to list
        gene_names.append(mysql_cursor.fetchone())

    # If no 'display_xref_id' but we have gene 'description', get as much info as possible from the gene description
    elif gene.get('description') is not None:

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
                if key == 'Acc':
                    gene_name_info['xref_primary_acc'] = value

        # Add to list
        gene_names.append(gene_name_info)
    else:

        # If no 'display_xref_id' and no 'description', just add stable_id
        gene_names.append(gene_name_info)


with open(args.species + "_" + args.assembly + "_gene_names.json", "w") as write_file:
    json.dump(gene_names, write_file)

