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
import grpc
from ensembl.production.metadata import ensembl_metadata_pb2_grpc
from graphql_service.resolver.exceptions import GenomeNotFoundError


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
        self.mongo_db = MongoDbClient.connect_mongo(self.config)

    def get_collection_conn(self, uuid):

        mapping_collection = self.config.get("mongo_mapping_collection")
        # print(mapping_collection)
        query = {
            "uuid": uuid,
            "is_current": True
        }

        # Find the data collection corresponding to the given UUID
        data_collection = self.mongo_db[mapping_collection].find_one(query)
        # print(data_collection)

        # Fallback to the collection in the configuration file if no collection found in the mappings
        # for the given UUID
        data_collection_name = self.config.get("mongo_default_collection") if not data_collection \
            else data_collection.get("collection")

        print("Using '{}' collection for '{}' UUID".format(data_collection_name, uuid))

        data_collection_connection = self.mongo_db[data_collection_name]

        return data_collection_connection

    @staticmethod
    def connect_mongo(config):
        "Get a MongoDB connection"

        host = config.get("mongo_host").split(",")
        port = int(config.get("mongo_port"))
        user = config.get("mongo_user")
        password = config.get("mongo_password")
        dbname = config.get("mongo_db")

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
            print(f"Connected to MongoDB {host}")
        except Exception as exc:
            raise "Connection to mongo Failed" from exc

        return client[dbname]


class FakeMongoDbClient:
    """
    Sets up a mongomock collection for thoas code to test with
    """

    def __init__(self):
        "Override default setup"
        self.mongo_db = mongomock.MongoClient().db
        self.collection_name = "test"

    def collection(self):
        return self.mongo_db[self.collection_name]


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
