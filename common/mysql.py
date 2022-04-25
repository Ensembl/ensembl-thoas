"""Helper class for creating a MySQL connection"""

from mysql.connector import MySQLConnection, DataError


class MySQLClient:
    def __init__(self, config, section_name):
        self.connection = MySQLConnection(
            host=config.get(section_name, 'host'),
            user=config.get(section_name, 'user'),
            database=config.get(section_name, 'database'),
            port=config.get(section_name, 'port')
        )

    def get_attribute_id_from_code(self, attribute_code):
        attribute_id_query = """SELECT attrib_type_id FROM attrib_type WHERE code = %s"""
        with self.connection.cursor() as cursor: # TODO why dictionary?
            cursor.execute(attribute_id_query, (attribute_code,))
            attribute_ids = cursor.fetchall()
            if len(attribute_ids) != 1:
                raise DataError(f'Could not find unique id for attribute with code {attribute_code}')
            return attribute_ids[0][0]

