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

args = parser.parse_args()

data = open(args.species + "_" + args.assembly + "_sources.txt", "a")
gene_names = open(args.species + "_" + args.assembly + "_gene_names.txt", "a")

select_all_query = "SELECT stable_id, display_xref_id, description FROM gene"
select_display_xref_query = "select gene.display_xref_id as gene_display_xref_id, " \
                            "gene.description as gene_description, " \
                            "gene.stable_id as gene_stable_id, " \
                            "xref.dbprimary_acc as xref_primary_id, " \
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

mysql_cursor.execute(select_all_query)
genes = mysql_cursor.fetchall()
matches = {}
for gene in genes:

    if gene.get('display_xref_id') is not None:
        mysql_cursor.execute(select_display_xref_query.format(gene.get('stable_id')))
        json.dump(mysql_cursor.fetchone(), gene_names)
    elif gene.get('description') is not None:

        # Search for content starting with 'Source' within square brackets
        match = re.search(r'\[Source.*?\]', gene.get('description'))
        if match:
            # Remove square brackets
            match_string = match[0][1:-1]
            matched_string_elements = match_string.split(';')
            for element in matched_string_elements:
                key, value = element.split(':')
                if key == 'Source':
                    #print(value)
                    data.write(value+'\n')
data.close()
