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

import logging
import pymongo
import mongomock
import grpc

from graphql_service.resolver.exceptions import (
    GenomeNotFoundError,
    FailedToConnectToGrpc,
)


from yagrc import reflector as yagrc_reflector


from common.utils import process_release_version

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
        self.mongo_client = MongoDbClient.connect_mongo(self.config)

    def get_database_conn(self, grpc_model, uuid, release_version):
        grpc_response = None
        chosen_db = None

        if release_version:
            chosen_db = process_release_version(release_version)
            return self.mongo_client[chosen_db]

        # Try to connect to gRPC
        try:
            grpc_response = grpc_model.get_release_by_genome_uuid(uuid)
        except Exception as grpc_exp:
            # TODO: check why "except graphql.error.graphql_error.GraphQLError as grpc_exp:" didn't catch the error
            logger.debug(
                "[get_database_conn] Couldn't connect to gRPC Host: %s", grpc_exp
            )
            raise FailedToConnectToGrpc(
                "Internal server error: Couldn't connect to gRPC Host"
            )

        if grpc_response and grpc_response.release_version:
            chosen_db = process_release_version(grpc_response.release_version)
        else:
            logger.warning("[get_database_conn] Release not found")
            raise GenomeNotFoundError({"genome_id": uuid})

        if chosen_db is not None:
            logger.debug("[get_database_conn] Connected to '%s' MongoDB", chosen_db)
            data_database_connection = self.mongo_client[chosen_db]
            return data_database_connection
        raise GenomeNotFoundError({"genome_id": uuid})

    @staticmethod
    def connect_mongo(config):
        "Get a MongoDB connection"

        host = config.get("mongo_host").split(",")
        port = int(config.get("mongo_port"))
        user = config.get("mongo_user")
        password = config.get("mongo_password")

        client = pymongo.MongoClient(
            host=host,
            port=port,
            username=user,
            password=password,
            read_preference=pymongo.ReadPreference.SECONDARY_PREFERRED,
        )
        try:
            # make sure the connection is established successfully
            client.server_info()
            print(f"Connected to MongoDB, Host: {host}")
        except Exception as exc:
            raise Exception("Connection to MongoDB failed") from exc

        return client


class FakeMongoDbClient:
    """
    Sets up a mongomock collection for thoas code to test with
    """

    def __init__(self):
        self.mongo_client = mongomock.MongoClient()
        self.mongo_db = self.mongo_client.db

    def get_database_conn(self, grpc_model, uuid, release_version):
        # we pretend that we did a gRPC call and got the chosen db
        chosen_db = "db"
        return self.mongo_client[chosen_db]


class GRPCServiceClient:
    def __init__(self, config):

        host = config.get("grpc_host")
        port = config.get("grpc_port")

        # instantiate a channel
        self.channel = grpc.insecure_channel(
            "{}:{}".format(host, port), options=(("grpc.enable_http_proxy", 0),)
        )

        # create reflector for querying server using reflection
        self.reflector = yagrc_reflector.GrpcReflectionClient()

        # use reflection to load service definitions and message types
        self.reflector.load_protocols(
            self.channel, symbols=["ensembl_metadata.EnsemblMetadata"]
        )

        # dynamically retrieve the client stub class for service
        stub_class = self.reflector.service_stub_class(
            "ensembl_metadata.EnsemblMetadata"
        )

        # bind the client and the server
        self.stub = stub_class(self.channel)

    def get_grpc_stub(self):
        return self.stub

    def get_grpc_reflector(self):
        return self.reflector
