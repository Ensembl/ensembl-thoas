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

from graphql_service.resolver.exceptions import GenomeNotFoundError


from yagrc import reflector as yagrc_reflector

from common.utils import release_database_name

logger = logging.getLogger(__name__)


def release_version_key(version):
    """Return numeric release components, or None for an invalid mapping."""
    if not isinstance(version, str) or not re.fullmatch(
        r"[0-9]+(?:\.[0-9]+)*", version
    ):
        return None
    return tuple(int(part) for part in version.split("."))


def highest_release_mapping(mappings):
    """Keep version and name together when selecting the highest valid release."""
    valid = [
        m for m in mappings if release_version_key(m.get("release_version")) is not None
    ]
    return max(
        valid, key=lambda m: release_version_key(m["release_version"]), default=None
    )


def mapping_database_name(mapping, database_names):
    """Prefer the version database, then the name from the same mapping."""
    if mapping is None:
        return None
    for release in (mapping["release_version"], mapping.get("release_name")):
        if release is None or str(release).strip() == "":
            continue
        database = release_database_name(release)
        if database in database_names:
            return database
    return None


def genome_mapping_cache_key(uuid):
    # Cache resolved database names separately from legacy release-version values.
    return f"genome_mapping:database:{uuid}"


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
                cached_database = await self.async_cache.get(
                    genome_mapping_cache_key(uuid)
                )
                if cached_database:
                    chosen_db = cached_database.decode("utf-8")
                    return self.async_mongo_client[chosen_db]
            except redis.RedisError as e:
                logger.warning(f"[MongoDbClient] Redis cache read failed: {e}")
        return None

    async def get_async_database_conn(self, uuid):
        cached_connection = await self.get_cached_connection(uuid)
        if cached_connection is not None:
            return cached_connection

        chosen_db = None
        try:
            mappings = (
                await self.async_mongo_client["metadata"]["genome_mapping"]
                .find(
                    {"genome_uuid": uuid},
                    {"release_version": 1, "release_name": 1, "_id": 0},
                )
                .to_list(length=None)
            )
            mapping = highest_release_mapping(mappings)
            if mapping is not None:
                chosen_db = mapping_database_name(
                    mapping, await self.async_mongo_client.list_database_names()
                )
        except pymongo.errors.PyMongoError as exc:
            logger.warning("MongoDB genome mapping lookup failed for %s: %s", uuid, exc)

        if not chosen_db:
            logger.warning("[get_database_conn] Release not found")
            raise GenomeNotFoundError({"genome_id": uuid})

        if self.redis_cache_enabled and self.async_cache:
            try:
                await self.async_cache.set(
                    genome_mapping_cache_key(uuid),
                    chosen_db,
                    ex=self.redis_expiry,
                )
            except redis.RedisError as e:
                logger.warning(f"[MongoDbClient] Redis cache set failed: {e}")

        logger.debug("[get_database_conn] Connected to '%s' MongoDB", chosen_db)
        return self.async_mongo_client[chosen_db]

    def get_database_conn(self, uuid, release_version=None):
        chosen_db = None

        if release_version:
            chosen_db = release_database_name(release_version)
            return self.mongo_client[chosen_db]

        # Try cache if enabled
        if self.redis_cache_enabled and self.cache:
            try:
                cached_database = self.cache.get(genome_mapping_cache_key(uuid))
                if cached_database:
                    logger.debug(
                        f"[MongoDbClient] Using cached database: {cached_database}"
                    )
                    chosen_db = cached_database.decode("utf-8")
                    return self.mongo_client[chosen_db]
            except redis.RedisError as e:
                logger.warning(f"[MongoDbClient] Redis cache read failed: {e}")

        chosen_db = None
        try:
            with self.mongo_client["metadata"]["genome_mapping"].find(
                {"genome_uuid": uuid},
                {"release_version": 1, "release_name": 1, "_id": 0},
            ) as mappings:
                mapping = highest_release_mapping(mappings)
            if mapping is not None:
                chosen_db = mapping_database_name(
                    mapping, self.mongo_client.list_database_names()
                )
        except pymongo.errors.PyMongoError as exc:
            logger.warning("MongoDB genome mapping lookup failed for %s: %s", uuid, exc)

        if chosen_db:
            if self.redis_cache_enabled and self.cache:
                try:
                    self.cache.set(
                        genome_mapping_cache_key(uuid),
                        chosen_db,
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
                {},
                {"genome_uuid": 1, "release_version": 1, "release_name": 1, "_id": 0},
            ) as mappings:
                for mapping in mappings:
                    uuid = mapping.get("genome_uuid")
                    version = mapping.get("release_version")
                    version_key = release_version_key(version)
                    if not uuid or version_key is None:
                        continue
                    if uuid not in latest or version_key > release_version_key(
                        latest[uuid]["release_version"]
                    ):
                        latest[uuid] = mapping

            database_names = self.mongo_client.list_database_names()
            for uuid, mapping in latest.items():
                chosen_db = mapping_database_name(mapping, database_names)
                if chosen_db is None:
                    continue
                self.cache.set(
                    genome_mapping_cache_key(uuid), chosen_db, ex=self.redis_expiry
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

    def get_database_conn(self, uuid, release_version=None):
        # Return the test database without resolving a release.
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
