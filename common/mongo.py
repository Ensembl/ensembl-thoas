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

import pymongo
import mongomock
from pymongo.event_loggers import CommandLogger


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
            print(f'Using injected MongoDB collection with name {self.collection_name}')

    @staticmethod
    def connect_mongo(config):
        'Get a MongoDB connection'

        host = config.get('MONGO DB', 'host')
        port = config.getint('MONGO DB', 'port')
        user = config.get('MONGO DB', 'user')
        password = config.get('MONGO DB', 'password')
        dbname = config.get('MONGO DB', 'db')

        client = pymongo.MongoClient(
            host,
            port,
            username=user,
            password=password,
            read_preference=pymongo.ReadPreference.SECONDARY_PREFERRED
        )
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
        self.mongo_db = mongomock.MongoClient().db
        self.collection_name = 'test'

    def collection(self):
        return self.mongo_db[self.collection_name]
