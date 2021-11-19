from mysql.connector import MySQLConnection


class MySQLClient:
    def __init__(self, config, section_name):
        self.connection = MySQLConnection(
            host=config.get(section_name, 'host'),
            user=config.get(section_name, 'user'),
            database=config.get(section_name, 'database'),
            port=config.get(section_name, 'port')
        )
