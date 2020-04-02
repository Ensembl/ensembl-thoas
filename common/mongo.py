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

import pymongo


class mongo_db_thing():

    def __init__(self, config):
        '''
        Note that config here is a configparser object
        '''
        self.mongo_db = self.connect_mongo(config)
        self.default_collection = config.get('MONGO DB','collection')
        print('MongoDB default collection:' + self.default_collection)

    def connect_mongo(self, config):
        'Get a MongoDB connection'

        host = config.get('MONGO_DB','host')
        port = config.getint('MONGO_DB','port')
        user = config.get('MONGO_DB','user')
        password = config.get('MONGO_DB','password')
        db = config.get('MONGO_DB','db')

        client = pymongo.MongoClient(
            host,
            port,
            read_preference=pymongo.ReadPreference.SECONDARY_PREFERRED
        )
        client.admin.authenticate(user, password)
        print('connected to MongoDB ' + host)
        return client[db]

    def collection(self):
        return self.mongo_db[self.default_collection]
