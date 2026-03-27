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
import re
import time

import pymongo
import mongomock
import grpc
import redis
import redis.asyncio as redis_async
from pymongo import AsyncMongoClient

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
        self.async_mongo_client = MongoDbClient.connect_async_mongo(self.config)

        # Setup Redis connection and caching toggle
        self.redis_cache_enabled = (
            self.config.get("GRPC_ENABLE_CACHE", "true").lower() == "true"
        )
        self.redis_host = self.config.get("REDIS_HOST", "localhost")
        self.redis_port = int(self.config.get("REDIS_PORT", 6379))
        self.redis_expiry = int(self.config.get("REDIS_EXPIRY_SECONDS", 6600))
        self.warmup_cache_on_start = (
            self.config.get("WARMUP_CACHE_ON_START", "false").lower() == "true"
        )

        try:
            self.cache = redis.StrictRedis(host=self.redis_host, port=self.redis_port)
            self.async_cache = redis_async.Redis(
                host=self.redis_host, port=self.redis_port
            )
            self.cache.ping()  # Check Redis connection
            logger.debug(f"[MongoDbClient] Redis caching enabled")

            if self.redis_cache_enabled and self.warmup_cache_on_start:
                self.warmup_cache_from_mongo()

        except redis.RedisError as e:
            logger.warning(f"[MongoDbClient] Redis not available: {e}")
            self.cache = None
            self.async_cache = None
            self.redis_cache_enabled = False

    async def get_cached_connection(self, uuid):
        if self.redis_cache_enabled and self.async_cache:
            try:
                cached_version = await self.async_cache.get(uuid)
                if cached_version:
                    chosen_db = process_release_version(cached_version.decode("utf-8"))
                    return self.async_mongo_client[chosen_db]
            except redis.RedisError as e:
                logger.warning(f"[MongoDbClient] Redis cache read failed: {e}")
        return None

    async def get_async_database_conn(self, async_grpc_model, uuid):
        cached_connection = await self.get_cached_connection(uuid)
        if cached_connection is not None:
            return cached_connection

        try:
            grpc_response = await async_grpc_model.get_release_by_genome_uuid(uuid)
        except Exception as grpc_exp:
            raise FailedToConnectToGrpc(
                f"Internal server error: Couldn't connect to gRPC Host, {str(grpc_exp)}"
            )

        if not grpc_response or not grpc_response.release_version:
            logger.warning("[get_database_conn] Release not found")
            raise GenomeNotFoundError({"genome_id": uuid})

        chosen_db = process_release_version(grpc_response.release_version)
        if self.redis_cache_enabled and self.async_cache:
            try:
                await self.async_cache.set(
                    uuid, grpc_response.release_version, ex=self.redis_expiry
                )
            except redis.RedisError as e:
                logger.warning(f"[MongoDbClient] Redis cache set failed: {e}")

        if not chosen_db:
            raise GenomeNotFoundError({"genome_id": uuid})

        logger.debug("[get_database_conn] Connected to '%s' MongoDB", chosen_db)
        return self.async_mongo_client[chosen_db]

    def get_database_conn(self, grpc_model, uuid, release_version):
        grpc_response = None
        chosen_db = None

        if release_version:
            chosen_db = process_release_version(release_version)
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
            data_database_connection = self.mongo_client[chosen_db]
            return data_database_connection
        raise GenomeNotFoundError({"genome_id": uuid})

    def warmup_cache_from_mongo(self):
        if not self.redis_cache_enabled or not self.cache:
            return

        started = time.time()
        total_keys = 0

        try:
            # ex: ["release_110_1", "release_110_2", ..]
            release_dbs = [
                db_name
                for db_name in self.mongo_client.list_database_names()
                if re.compile(r"^release_\d+_\d+$").match(db_name)
            ]

            logger.info(
                "Starting genome id-> release version redis warm-up from MongoDB"
            )

            for db_name in release_dbs:
                # release_115_4 -> 115.4
                # we could diretly store release_115_4 but sync resolvers use process_release_version
                # to get db name
                release_version = db_name[len("release_") :].replace("_", ".")
                genome_collection = self.mongo_client[db_name]["genome"]

                db_keys = 0
                cursor = genome_collection.find({})
                try:
                    for genome in cursor:
                        genome_id = genome.get("genome_id")
                        if not genome_id:
                            continue

                        # set only if there is no entry
                        self.cache.set(genome_id, release_version, nx=True)
                        db_keys += 1
                finally:
                    cursor.close()

                total_keys += db_keys
                logger.debug(
                    "[warmup_cache_from_mongo] Stored %d entries from %s",
                    db_keys,
                    db_name,
                )

            time_taken = time.time() - started
            logger.info(
                "[warmup_cache_from_mongo] Redis warm-up completed: %d keys in %.2fs",
                total_keys,
                time_taken,
            )
        except Exception as ex:
            logger.warning("[warmup_cache_from_mongo] Redis warm-up failed: %s", ex)

    async def close(self):
        if self.async_cache:
            try:
                await self.async_cache.aclose()
            except Exception as exc:
                logger.warning("Failed to close async redis cache client: %s", exc)

        if self.cache:
            try:
                self.cache.close()
            except Exception as exc:
                logger.warning("Failed to close redis cache client: %s", exc)

        if self.async_mongo_client:
            try:
                await self.async_mongo_client.aclose()
            except Exception as exc:
                logger.warning("Failed to close async mongo client: %s", exc)

        if self.mongo_client:
            try:
                self.mongo_client.close()
            except Exception as exc:
                logger.warning("Failed to close mongo client: %s", exc)

    @staticmethod
    def connect_mongo(config):
        "Create a MongoDB connection"

        host = config.get("MONGO_HOST").split(",")
        port = int(config.get("MONGO_PORT"))
        user = config.get("MONGO_USER")
        password = config.get("MONGO_PASSWORD")

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
            logger.debug(f"Connected to MongoDB, Host: {host}")
        except Exception as exc:
            raise Exception("Connection to MongoDB failed") from exc

        return client

    @staticmethod
    def connect_async_mongo(config):
        """Create async MongoDB connection"""
        host = config.get("MONGO_HOST").split(",")
        port = int(config.get("MONGO_PORT"))
        user = config.get("MONGO_USER")
        password = config.get("MONGO_PASSWORD")

        client = AsyncMongoClient(
            host=host,
            port=port,
            username=user,
            password=password,
            read_preference=pymongo.ReadPreference.SECONDARY_PREFERRED,
        )
        logger.debug(f"Async MongoDB client created for host: {host}")
        return client


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

    def close(self):
        try:
            self.channel.close()
        except Exception as exc:
            logger.warning("Failed to close grpc client: %s", exc)


class AsyncGRPCServiceClient:
    def __init__(self, config):

        host = config.get("GRPC_HOST")
        port = config.get("GRPC_PORT")
        target = "{}:{}".format(host, port)

        # yagrc is synchronous and requires a standard grpc.insecure_channel
        with grpc.insecure_channel(
            target, options=(("grpc.enable_http_proxy", 0),)
        ) as sync_channel:
            self.reflector = yagrc_reflector.GrpcReflectionClient()
            self.reflector.load_protocols(
                sync_channel, symbols=["ensembl_metadata.EnsemblMetadata"]
            )

        self.aio_channel = grpc.aio.insecure_channel(
            target, options=(("grpc.enable_http_proxy", 0),)
        )

        # dynamically retrieve the client stub class for service
        stub_class = self.reflector.service_stub_class(
            "ensembl_metadata.EnsemblMetadata"
        )

        # bind the client and the server
        self.stub = stub_class(self.aio_channel)

    def get_grpc_stub(self):
        return self.stub

    def get_grpc_reflector(self):
        return self.reflector

    async def close(self):
        try:
            await self.aio_channel.close()
        except Exception as exc:
            logger.warning("Failed to close async grpc client: %s", exc)
