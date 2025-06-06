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
from pymongo import AsyncMongoClient
import mongomock
import grpc
import redis

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
        print("Creating PyMongo obj")
        """
        Note that config here is a configparser object
        """
        self.config = config

        # Setup Redis connection and caching toggle
        self.redis_cache_enabled = (
            self.config.get("GRPC_ENABLE_CACHE", "true").lower() == "true"
        )
        self.redis_host = self.config.get("REDIS_HOST", "localhost")
        self.redis_port = int(self.config.get("REDIS_PORT", 6379))
        self.redis_expiry = int(self.config.get("REDIS_EXPIRY_SECONDS", 6600))

        try:
            self.cache = redis.StrictRedis(host=self.redis_host, port=self.redis_port)
            self.cache.ping()  # Check Redis connection
            logger.info(f"[MongoDbClient] Redis caching enabled")
        except redis.RedisError as e:
            logger.warning(f"[MongoDbClient] Redis not available: {e}")
            self.cache = None
            self.redis_cache_enabled = False

    def __await__(self):
        async def closure():
            print("DB await")
            return self

        return closure().__await__()

    async def __aenter__(self):
        print("DB enter")
        await self

        host = self.config.get("MONGO_HOST").split(",")
        port = int(self.config.get("MONGO_PORT"))
        user = self.config.get("MONGO_USER")
        password = self.config.get("MONGO_PASSWORD")

        client = AsyncMongoClient(
            host=host,
            port=port,
            username=user,
            password=password,
        )
        self.mongo_client = client
        await client.aconnect()
        return self

    async def __aexit__(self, *args):
        print("DB exit")


    async def get_database_conn(self, grpc_model, uuid, release_version):
        grpc_response = None
        chosen_db = None

        if release_version:
            chosen_db = process_release_version(release_version)
#            await self.mongo_client
            return self.mongo_client[chosen_db]

        # Try cache if enabled
        if self.redis_cache_enabled and self.cache:
            try:
                cached_version = self.cache.get(uuid)
                if cached_version:
                    logger.debug(
                        f"[MongoDbClient] Using cached version: {cached_version}"
                    )
                    chosen_db = process_release_version(cached_version.decode("utf-8"))
#                    await self.mongo_client
                    return self.mongo_client[chosen_db]
            except redis.RedisError as e:
                logger.warning(f"[MongoDbClient] Redis cache read failed: {e}")

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

            if self.redis_cache_enabled and self.cache:
                try:
                    self.cache.set(
                        uuid, grpc_response.release_version, ex=self.redis_expiry
                    )
                except redis.RedisError as e:
                    logger.warning(f"[MongoDbClient] Redis cache set failed: {e}")

        else:
            logger.warning("[get_database_conn] Release not found")
            raise GenomeNotFoundError({"genome_id": uuid})

        if chosen_db is not None:
            logger.debug("[get_database_conn] Connected to '%s' MongoDB", chosen_db)
#            await self.mongo_client
            data_database_connection = self.mongo_client[chosen_db]
            return data_database_connection
        raise GenomeNotFoundError({"genome_id": uuid})



class FakeMongoDbClient:
    """
    Sets up a mongomock collection for thoas code to test with
    """

    def __init__(self):
        self.mongo_client = mongomock.MongoClient()
        self.mongo_db = self.mongo_client.db
        self.redis_cache_enabled = False

    def get_database_conn(self, grpc_model, uuid, release_version):
        # we pretend that we did a gRPC call and got the chosen db
        chosen_db = "db"
        return self.mongo_client[chosen_db]


class GRPCServiceClient:
    def __init__(self, config):

        host = config.get("GRPC_HOST")
        port = config.get("GRPC_PORT")

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
