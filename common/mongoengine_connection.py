from configparser import NoOptionError
from mongoengine import connect

from scripts.documents import ThoasObject


def create_mongoengine_connection(config, collection_name=None):
    host = config.get('MONGO DB', 'host')
    port = config.getint('MONGO DB', 'port')
    username = config.get('MONGO DB', 'user')
    password = config.get('MONGO DB', 'password')
    db = config.get('MONGO DB', 'db')

    connect(db=db, username=username, password=password, host=host, authentication_source='admin', port=port)

    try:
        collection_name = config.get('MONGO DB', 'collection')
        print(f'Using MongoDB collection name {collection_name} from config file')
    except NoOptionError as no_option_error:
        if not collection_name:
            raise IOError("Unable to find a MongoDB collection name") from no_option_error
        collection_name = collection_name
        print(f'Using MongoDB collection name {collection_name}')

    def _get_collection_name():
        return collection_name
    ThoasObject._get_collection_name = _get_collection_name


