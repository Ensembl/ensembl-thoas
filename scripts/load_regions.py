import argparse

from mysql.connector import DataError

import common.utils
from common.mysql import MySQLClient
from common.utils import format_region
from common.mongo import MongoDbClient


def load_regions(config, section_name, mongo_client):

    assembly = mongo_client.collection().find_one({
        'type': 'Assembly',
        'name': config.get(section_name, 'assembly')
    })
    assembly_id = assembly["id"]

    mysql_client = MySQLClient(config, section_name)

    circular_attribute_query = """SELECT attrib_type_id FROM attrib_type WHERE code = 'circular_seq'"""

    max_regions = 10000
    species = config.get(section_name, 'production_name')

    region_query = """SELECT distinct(gene.seq_region_id), 
                            seq_region.length as length, 
                            seq_region.name, 
                            coord_system.name as code, 
                            circular_regions.value as circularity, 
                            species_name.meta_value as species_name, 
                            accession.meta_value as accession_id  FROM gene
                      INNER JOIN seq_region USING (seq_region_id)
                      INNER JOIN coord_system USING (coord_system_id)
                      INNER JOIN (SELECT species_id, meta_value FROM meta WHERE meta_key = 'species.production_name') as species_name
                          USING (species_id)
                      INNER JOIN (SELECT species_id, meta_value FROM meta WHERE meta_key = 'assembly.accession') as accession
                          USING (species_id)
                      LEFT JOIN (SELECT seq_region_id, value FROM seq_region_attrib WHERE attrib_type_id = %s) as circular_regions
                          USING (seq_region_id)
                      WHERE species_name.meta_value = %s
                      AND coord_system.name = 'chromosome'                      
                      LIMIT %s"""

    with mysql_client.connection.cursor(dictionary=True) as cursor:
        cursor.execute(circular_attribute_query)
        circular_attribute_result = cursor.fetchall()
        if len(circular_attribute_result) != 1:
            raise DataError(f'Could not find unique circular attribute id')
        circular_attribute_id = circular_attribute_result[0]['attrib_type_id']

        cursor.execute(region_query, (circular_attribute_id, species, max_regions))
        region_results = cursor.fetchall()

        formatted_results = [format_region(result, assembly_id, species) for result in region_results]

        if len(formatted_results) == max_regions:
            raise DataError(f"Unexpectedly large number of regions met threshold of {max_regions}")
        mongo_client.collection().insert_many(formatted_results)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Load Region data from MySQL into MongoDB'
    )
    parser.add_argument(
        '--config_file',
        help='File path containing MySQL and MongoDB credentials',
        default='../load.conf'
    )
    parser.add_argument(
        '--section_name',
        help='Section of config file containing MySQL credentials'
    )
    ARGS = parser.parse_args()
    CONFIG = common.utils.load_config(ARGS.config_file)
    MONGO_CLIENT = MongoDbClient(CONFIG)
    load_regions(CONFIG, ARGS.section_name, MONGO_CLIENT)
