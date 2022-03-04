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

from mysql.connector import DataError

import common.utils
from common.mongoengine_connection import create_mongoengine_connection
from common.utils import format_region, get_genome_id
from common.file_parser import MockChromosomeChecksum
from common.mysql import MySQLClient


from scripts.mongoengine_documents.region import Region


def load_regions(config, section_name, chr_checksums_path):

    # TODO get the assembly_id properly
    assembly_id = "ASM276v2"

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
            raise DataError('Could not find unique circular attribute id')
        circular_attribute_id = circular_attribute_result[0]['attrib_type_id']

        cursor.execute(region_query, (circular_attribute_id, species, max_regions))
        region_results = cursor.fetchall()

        genome_id = get_genome_id(region_results[0]['species_name'], region_results[0]['accession_id'])
        chromosome_checksums = MockChromosomeChecksum(genome_id, chr_checksums_path)

        formatted_results = [format_region(result, assembly_id, genome_id, chromosome_checksums) for result in region_results]

        if len(formatted_results) == max_regions:
            raise DataError(f"Unexpectedly large number of regions met threshold of {max_regions}")

        Region.objects.insert(formatted_results)


if __name__ == "__main__":
    ARGS = common.utils.parse_args()

    CONFIG = common.utils.load_config(ARGS.config_file)
    create_mongoengine_connection(CONFIG, ARGS.mongo_collection)
    load_regions(CONFIG, ARGS.section_name, ARGS.chr_checksums_path)
