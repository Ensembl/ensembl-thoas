from mysql.connector import MySQLConnection


def load_proteins(config, section_name):
    mysql_client = MySQLConnection(
            host=config.get(section_name, 'host'),
            user=config.get(section_name, 'user'),
            database=config.get(section_name, 'database'),
            port=config.get(section_name, 'port')
        )

