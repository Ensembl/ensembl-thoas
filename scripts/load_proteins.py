import argparse
import json


import common.utils
from common.mongo import MongoDbClient
from common.mysql import MySQLClient


def load_proteins(config, section_name):
    mysql_client = MySQLClient(config, section_name)

    translation_query = """SELECT ifnull(t.stable_id,t.transcript_id) AS transcript_id,
    ifnull(tl.stable_id,tl.translation_id) AS id,
    tl.version AS version,
    'translation' AS ensembl_object_type
    FROM transcript t
    JOIN translation tl USING (transcript_id)
    JOIN seq_region s USING (seq_region_id)
    JOIN coord_system c USING (coord_system_id)
    WHERE c.species_id = 1 
    """  # TODO: is the species_id always 1?

    domain_query = """SELECT
    ifnull(tl.stable_id, tl.translation_id) AS translation_id,
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
    WHERE c.species_id = 1 AND a.db in ('Pfam', 'PANTHER')"""

    xrefs_query = """SELECT ifnull(tl.stable_id, tl.translation_id) AS id, x.xref_id, x.dbprimary_acc, x.display_label, e.db_name, e.db_display_name, x.description, x.info_type, x.info_text
      FROM transcript t
      JOIN translation tl USING (transcript_id)
      JOIN object_xref ox         ON (tl.translation_id = ox.ensembl_id AND ox.ensembl_object_type = 'Translation')
      JOIN xref x                 USING (xref_id)
      JOIN external_db e          USING (external_db_id)
      JOIN seq_region s           USING (seq_region_id)
      JOIN coord_system c         USING (coord_system_id)
      LEFT JOIN ontology_xref oox USING (object_xref_id)
      WHERE c.species_id = 1 AND oox.object_xref_id is null"""

    def group_by_id(list_of_dicts, key):
        result = {}
        for item in list_of_dicts:
            if item[key] in result:
                result[item[key]].append(item)
            else:
                result[item[key]] = [item]
        return result # TODO use Pandas here?

    with mysql_client.connection.cursor(dictionary=True) as cursor:
        cursor.execute(translation_query)
        translations = cursor.fetchall()

        cursor.execute(domain_query)
        domains = cursor.fetchall()

        cursor.execute(xrefs_query)
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

        indexed_xrefs = {translation_id: list(map(to_json_dump_format, xref_group)) for translation_id, xref_group in
                         indexed_xrefs.items()}

        for translation in translations:
            translation["protein_features"] = indexed_domains.get(translation["id"], [])
            translation["xrefs"] = indexed_xrefs.get(translation["id"], [])

        species = config.get(section_name, 'production_name')
        assembly = config.get(section_name, 'assembly')
        outpath = f'./{species}_{assembly}_translations.json'
        with open(outpath, 'w+') as outhandle:
            json.dump(translations, outhandle)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Load protein domain information from MySQL into MongoDB'
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
    MONGO_CLIENT = MongoDbClient(CONFIG)
    load_proteins(CONFIG, ARGS.section_name)
