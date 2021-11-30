#
#    See the NOTICE file distributed with this work for additional information
#    regarding copyright ownership.
#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
#        http://www.apache.org/licenses/LICENSE-2.0
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.
#

import argparse
import json
import common.utils

from common.mysql import MySQLClient


def dump_proteins(config, section_name):
    mysql_client = MySQLClient(config, section_name)

    translation_query = """SELECT ifnull(t.stable_id,t.transcript_id) AS transcript_id,
    ifnull(tl.stable_id,tl.translation_id) AS id,
    tl.version AS version,
    'translation' AS ensembl_object_type
    FROM transcript t
    JOIN translation tl USING (transcript_id)
    JOIN seq_region s USING (seq_region_id)
    JOIN coord_system c USING (coord_system_id)
    JOIN meta USING (species_id) 
    WHERE c.name = 'chromosome' AND c.version = %s AND meta_key='species.production_name' AND meta_value=%s"""

    domain_query = """SELECT ifnull(tl.stable_id, tl.translation_id) AS translation_id,
    pf.hit_name AS name,
    pf.hit_description AS description,
    pf.seq_start AS start,
    pf.seq_end AS end,
    pf.score as score,
    pf.evalue as evalue,
    pf.hit_start as hit_start,
    pf.hit_end as hit_end,
    a.program as program,
    a.db AS dbname,
    a.program_version as program_version,
    a.db_version as dbversion,
    i.interpro_ac,
    ix.display_label AS interpro_name,
    ix.description AS interpro_description,
    'protein_feature' AS ensembl_object_type
    FROM transcript t
    JOIN translation tl USING (transcript_id)
    JOIN protein_feature pf USING (translation_id)
    JOIN analysis a ON (a.analysis_id = pf.analysis_id)
    LEFT JOIN interpro i ON (pf.hit_name = i.id)
    LEFT JOIN xref ix ON (i.interpro_ac = ix.dbprimary_acc)
    LEFT JOIN external_db idx ON (ix.external_db_id=idx.external_db_id and idx.db_name='Interpro')
    JOIN seq_region s USING (seq_region_id)
    JOIN coord_system c USING (coord_system_id)
    JOIN meta USING (species_id)
    WHERE c.name = 'chromosome' AND c.version = %s AND a.db in ('Pfam', 'PANTHER') AND meta_key='species.production_name' AND meta_value=%s"""

    xrefs_query = """SELECT ifnull(tl.stable_id, tl.translation_id) AS id, x.xref_id, x.dbprimary_acc, x.display_label, e.db_name, e.db_display_name, x.description, x.info_type, x.info_text
    FROM transcript t
    JOIN translation tl USING (transcript_id)
    JOIN object_xref ox ON (tl.translation_id = ox.ensembl_id AND ox.ensembl_object_type = 'Translation')
    JOIN xref x USING (xref_id)
    JOIN external_db e USING (external_db_id)
    JOIN seq_region s USING (seq_region_id)
    JOIN coord_system c USING (coord_system_id)
    LEFT JOIN ontology_xref oox USING (object_xref_id)
    JOIN meta USING (species_id)
    WHERE c.name = 'chromosome' AND c.version = %s AND oox.object_xref_id is null AND meta_key='species.production_name' AND meta_value=%s"""

    def group_by_id(list_of_dicts, key):
        result = {}
        for item in list_of_dicts:
            if item[key] in result:
                result[item[key]].append(item)
            else:
                result[item[key]] = [item]
        return result

    with mysql_client.connection.cursor(dictionary=True) as cursor:
        assembly = config.get(section_name, 'assembly')
        species = config.get(section_name, 'production_name')

        cursor.execute(translation_query, (assembly, species))
        translations = cursor.fetchall()

        cursor.execute(domain_query, (assembly, species))
        domains = cursor.fetchall()

        cursor.execute(xrefs_query, (assembly, species))
        xrefs = cursor.fetchall()

        def to_json_dump_format(xref):
            return {
                "primary_id": xref["dbprimary_acc"],
                "display_id": xref["display_label"],
                "dbname": xref["db_name"],
                "db_display": xref["db_display_name"],
                "description": xref["description"],
                "info_type": xref["info_type"],
                "info_text": xref["info_text"]
            }

        indexed_domains = group_by_id(domains, 'translation_id')
        indexed_xrefs = group_by_id(xrefs, 'id')

        formatted_xrefs = {translation_id: list(map(to_json_dump_format, xref_group)) for translation_id, xref_group
                             in indexed_xrefs.items()}

        outpath = f'./{species}_{assembly}_translations.json'

        with open(outpath, 'w+') as outhandle:
            for translation in translations:
                translation["protein_features"] = indexed_domains.get(translation["id"], [])
                translation["xrefs"] = formatted_xrefs.get(translation["id"], [])
                json.dump(translation, outhandle)
                outhandle.write('\n')


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Dump protein domain information from MySQL into a local JSON file'
    )
    parser.add_argument(
        '--config_file',
        help='File path containing MySQL config',
        default='../load.conf'
    )
    parser.add_argument(
        '--section_name',
        help='Species-specific section of config file'
    )
    ARGS = parser.parse_args()
    CONFIG = common.utils.load_config(ARGS.config_file)
    dump_proteins(CONFIG, ARGS.section_name)
