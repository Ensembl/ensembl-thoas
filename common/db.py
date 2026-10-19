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


def release_version_key(version):
    """Return numeric release components, or None for an invalid mapping."""
    if not isinstance(version, str) or not re.fullmatch(
        r"[0-9]+(?:\.[0-9]+)*", version
    ):
        return None
    return tuple(int(part) for part in version.split("."))


def highest_mapping_release(mappings):
    """Ignore malformed mappings and select by numeric rather than string order."""
    versions = [mapping.get("release_version") for mapping in mappings]
    valid_versions = [v for v in versions if release_version_key(v) is not None]
    return max(valid_versions, key=release_version_key, default=None)


def genome_mapping_cache_key(uuid):
    # Avoid legacy bare-UUID warm-up entries, which could have no expiry.
    return f"genome_mapping:{uuid}"


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
                cached_version = await self.async_cache.get(
                    genome_mapping_cache_key(uuid)
                )
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

        release_version = None
        try:
            mappings = (
                await self.async_mongo_client["metadata"]["genome_mapping"]
                .find({"genome_uuid": uuid}, {"release_version": 1, "_id": 0})
                .to_list(length=None)
            )
            release_version = highest_mapping_release(mappings)
        except pymongo.errors.PyMongoError as exc:
            logger.warning("MongoDB genome mapping lookup failed for %s: %s", uuid, exc)

        if release_version is None:
            logger.debug("No usable MongoDB mapping for %s; falling back to gRPC", uuid)
            try:
                grpc_response = await async_grpc_model.get_release_by_genome_uuid(uuid)
                release_version = (
                    grpc_response.release_version if grpc_response else None
                )
            except Exception as grpc_exp:
                raise FailedToConnectToGrpc(
                    f"Internal server error: Couldn't connect to gRPC Host, {str(grpc_exp)}"
                ) from grpc_exp

        if not release_version:
            logger.warning("[get_database_conn] Release not found")
            raise GenomeNotFoundError({"genome_id": uuid})

        chosen_db = process_release_version(release_version)
        if self.redis_cache_enabled and self.async_cache:
            try:
                await self.async_cache.set(
                    genome_mapping_cache_key(uuid),
                    release_version,
                    ex=self.redis_expiry,
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
                cached_version = self.cache.get(genome_mapping_cache_key(uuid))
                if cached_version:
                    logger.debug(
                        f"[MongoDbClient] Using cached version: {cached_version}"
                    )
                    chosen_db = process_release_version(cached_version.decode("utf-8"))
                    return self.mongo_client[chosen_db]
            except redis.RedisError as e:
                logger.warning(f"[MongoDbClient] Redis cache read failed: {e}")

        release_version = None
        try:
            with self.mongo_client["metadata"]["genome_mapping"].find(
                {"genome_uuid": uuid}, {"release_version": 1, "_id": 0}
            ) as mappings:
                release_version = highest_mapping_release(mappings)
        except pymongo.errors.PyMongoError as exc:
            logger.warning("MongoDB genome mapping lookup failed for %s: %s", uuid, exc)

        if release_version is None:
            logger.debug("No usable MongoDB mapping for %s; falling back to gRPC", uuid)
            try:
                grpc_response = grpc_model.get_release_by_genome_uuid(uuid)
                release_version = (
                    grpc_response.release_version if grpc_response else None
                )
            except Exception as grpc_exp:
                raise FailedToConnectToGrpc(
                    "Internal server error: Couldn't connect to gRPC Host"
                ) from grpc_exp

        if release_version:
            chosen_db = process_release_version(release_version)

            if self.redis_cache_enabled and self.cache:
                try:
                    self.cache.set(
                        genome_mapping_cache_key(uuid),
                        release_version,
                        ex=self.redis_expiry,
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
            logger.info("Starting genome mapping Redis warm-up from MongoDB")
            latest = {}
            with self.mongo_client["metadata"]["genome_mapping"].find(
                {}, {"genome_uuid": 1, "release_version": 1, "_id": 0}
            ) as mappings:
                for mapping in mappings:
                    uuid = mapping.get("genome_uuid")
                    version = mapping.get("release_version")
                    version_key = release_version_key(version)
                    if not uuid or version_key is None:
                        continue
                    if uuid not in latest or version_key > release_version_key(
                        latest[uuid]
                    ):
                        latest[uuid] = version

            for uuid, version in latest.items():
                self.cache.set(
                    genome_mapping_cache_key(uuid), version, ex=self.redis_expiry
                )
                total_keys += 1

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
