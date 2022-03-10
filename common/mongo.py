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
from configparser import NoOptionError

from mongoengine import connect

from scripts.mongoengine_documents.base import ThoasDocument


class MongoDbClient:
    '''
    A pymongo wrapper class to take care of configuration and collection
    management
    '''

    def __init__(self, config, collection_name=None):
        '''
        Note that config here is a configparser object
        '''
        self.mongo_db = MongoDbClient.connect_mongo(config)
        try:
            self.collection_name = config.get('MONGO DB', 'collection')
            print(f'Using MongoDB collection with name {self.collection_name} from config file')
        except NoOptionError as no_option_error:
            if not collection_name:
                raise IOError("Unable to find a MongoDB collection name") from no_option_error
            self.collection_name = collection_name
            print(f'Using MongoDB collection name {self.collection_name}')

        # We need to monkey-patch _get_collection_name so that all subclasses of ThoasDocument get written to the same
        # collection
        def _get_collection_name():
            return self.collection_name
        ThoasDocument._get_collection_name = _get_collection_name

    @staticmethod
    def connect_mongo(config):
        'Get a MongoDB connection'

        host = config.get('MONGO DB', 'host')
        port = config.getint('MONGO DB', 'port')
        user = config.get('MONGO DB', 'user')
        password = config.get('MONGO DB', 'password')
        dbname = config.get('MONGO DB', 'db')

        # TODO put back read preference
        client = connect(db=dbname, username=user, password=password, host=host, authentication_source='admin', port=port)

        print('connected to MongoDB ' + host)
        return client[dbname]

    def collection(self):
        '''
        Get the currently set default collection to run queries against
        '''
        return self.mongo_db[self.collection_name]


class FakeMongoDbClient:
    '''
    Sets up a mongomock collection for thoas code to test with
    '''

    def __init__(self):
        'Override default setup'
        conn = connect('test_db', host='mongomock://localhost')
        self.mongo_db = conn['test_db']
        self.collection_name = 'test'

        def _get_collection_name():
            return self.collection_name
        ThoasDocument._get_collection_name = _get_collection_name

    def collection(self):
        return self.mongo_db[self.collection_name]
