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
import mongomock
import grpc
import logging
from ensembl.production.metadata.grpc import ensembl_metadata_pb2_grpc

logger = logging.getLogger(__name__)


class MongoDbClient:
    """
    A pymongo wrapper class to take care of configuration and collection
    management
    """

    def __init__(self, config):
        """
        Note that config here is a configparser object
        """
        self.config = config
        # self.mongo_db = MongoDbClient.connect_mongo(self.config)
        self.mongo_client = MongoDbClient.connect_mongo(self.config)

    def get_collection_conn(self, uuid):

        lookup_service_collection = self.config.get("mongo_lookup_service_collection")
        # print(lookup_service_collection)
        query = {"uuid": uuid, "is_current": True}

        # Find the data collection corresponding to the given UUID
        # Returns None if no data collection is found in lookup_service_collection
        # Returns None if the `lookup_service_collection` collection doesn't exist in the database
        data_collection = self.mongo_db[lookup_service_collection].find_one(query)
        # print(data_collection)

        # Fallback to the collection in the configuration file if no data collection is found for the given UUID
        if not data_collection:
            data_collection_name = self.config.get("mongo_default_collection")
            print(f"Falling back to the default collection '{data_collection_name}' for '{uuid}' UUID")
        else:
            data_collection_name = data_collection.get("collection")
            print(f"Using '{data_collection_name}' collection for '{uuid}' UUID")

        data_collection_connection = self.mongo_db[data_collection_name]

        return data_collection_connection

    def get_database_conn(self, grpc_model, uuid):
        # default value is 'mongo_default_db' that is in the config
        chosen_db = self.config.get('mongo_default_db')

        grpc_response = grpc_model.get_release_by_genome_uuid(uuid)
        if grpc_response:
            # replacing '.' with '_' to avoid
            # "pymongo.errors.InvalidName: database names cannot contain the character '.'" error ¯\_(ツ)_/¯
            release_version = str(grpc_response.release_version).replace('.', '_')
            chosen_db = 'release_' + release_version

        logger.debug(f"[get_database_conn] Connected to '{chosen_db}' MongoDB (ignored for now)")
        # Ignoring the code snippet above (falling back to 'mongo_default_db') for now
        # TODO: delete the line below once the DB is setup properly
        chosen_db = self.config.get('mongo_default_db')
        data_database_connection = self.mongo_client[chosen_db]

        return data_database_connection


    @staticmethod
    def connect_mongo(config):
        "Get a MongoDB connection"

        host = config.get("mongo_host").split(",")
        port = int(config.get("mongo_port"))
        user = config.get("mongo_user")
        password = config.get("mongo_password")
        # dbname = config.get("mongo_default_db")

        client = pymongo.MongoClient(
            host,
            port,
            username=user,
            password=password,
            read_preference=pymongo.ReadPreference.SECONDARY_PREFERRED,
        )
        try:
            # make sure the connection is established successfully
            client.server_info()
            print(f"Connected to MongoDB, Host: {host}")
        except Exception as exc:
            raise "Connection to mongo Failed" from exc

        return client


class FakeMongoDbClient:
    """
    Sets up a mongomock collection for thoas code to test with
    """
    def __init__(self):
        mongo_client = mongomock.MongoClient()
        self.mongo_db = mongo_client.db

    def get_collection_conn(self, uuid):
        lookup_service_collection = 'uuid_to_collection_mapping'
        query = {"uuid": uuid, "is_current": True}
        data_collection = self.mongo_db[lookup_service_collection].find_one(query)

        # Fallback to the default collection if no collection found in the mappings
        # for the given UUID
        if not data_collection:
            data_collection_name = 'collection1'
            print(f"Falling back to the default collection '{data_collection_name}' for '{uuid}' UUID")
        else:
            data_collection_name = data_collection.get("collection")
            print(f"Using '{data_collection_name}' collection for '{uuid}' UUID")

        data_collection_connection = self.mongo_db[data_collection_name]
        return data_collection_connection


class GRPCServiceClient:
    def __init__(self, config):

        host = config.get("grpc_host")
        port = config.get("grpc_port")

        # instantiate a channel
        self.channel = grpc.insecure_channel(
            "{}:{}".format(host, port), options=(("grpc.enable_http_proxy", 0),)
        )

        # bind the client and the server
        self.stub = ensembl_metadata_pb2_grpc.EnsemblMetadataStub(self.channel)

    def get_grpc_stub(self):
        return self.stub
