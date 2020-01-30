import mysql.connector
from configparser import ConfigParser


def connect_mysql(config):
    "Get a MySQL connection"

    connection = mysql.connector.connect(
        host=config['host'],
        port=config['port'],
        user=config['user'],
        database=config['db']
    )
    return connection


def load_config(filename):
    "Load a config, return a ConfigParser object"

    cp = ConfigParser()
    cp.read(filename)
    return cp
