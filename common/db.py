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
import asyncio
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

        # create MongoDB client
        self.mongo_client = MongoDbClient.connect_mongo(self.config)

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
        self.cache = None

        try:
            if self.redis_cache_enabled:
                self.cache = redis_async.Redis(
                    host=self.redis_host, port=self.redis_port
                )
                logger.debug("[MongoDbClient] Redis caching enabled")

            else:
                logger.debug("[MongoDbClient] Redis caching disabled")
                self.cache = None
        except redis.RedisError as e:
            logger.warning(f"[MongoDbClient] Redis not available: {e}")
            self.cache = None
            self.redis_cache_enabled = False

    # Get a cached MongoDB connection if available in Redis
    async def get_cached_connection(self, uuid):
        if self.redis_cache_enabled and self.cache:
            try:
                cached_database = await self.cache.get(genome_mapping_cache_key(uuid))
                if cached_database:
                    chosen_db = cached_database.decode("utf-8")
                    return self.mongo_client[chosen_db]
            except redis.RedisError as e:
                logger.warning(f"[MongoDbClient] Redis cache read failed: {e}")
        return None

    # Get a MongoDB connection for the specified genome UUID and optional release version.
    # If a release version is provided, it directly resolves the corresponding database.
    # Otherwise, it checks the Redis cache and falls back to the genome mapping collection.
    async def get_database_conn(self, uuid, release_version=None):
        chosen_db = None

        if release_version:
            chosen_db = release_database_name(release_version)
            return self.mongo_client[chosen_db]

        cached_connection = await self.get_cached_connection(uuid)
        if cached_connection is not None:
            return cached_connection

        try:
            mappings = (
                await self.mongo_client["metadata"]["genome_mapping"]
                .find(
                    {"genome_uuid": uuid},
                    {"release_version": 1, "release_name": 1, "_id": 0},
                )
                .to_list(length=None)
            )
            mapping = highest_release_mapping(mappings)
            if mapping is not None:
                chosen_db = mapping_database_name(
                    mapping, await self.mongo_client.list_database_names()
                )
        except pymongo.errors.PyMongoError as exc:
            logger.warning("MongoDB genome mapping lookup failed for %s: %s", uuid, exc)

        if not chosen_db:
            logger.warning("[get_database_conn] Release not found")
            raise GenomeNotFoundError({"genome_id": uuid})

        if self.redis_cache_enabled and self.cache:
            try:
                await self.cache.set(
                    genome_mapping_cache_key(uuid),
                    chosen_db,
                    ex=self.redis_expiry,
                )
            except redis.RedisError as e:
                logger.warning(f"[MongoDbClient] Redis cache set failed: {e}")

        logger.debug("[get_database_conn] Connected to '%s' MongoDB", chosen_db)
        return self.mongo_client[chosen_db]

    async def warmup_cache_from_mongo(self):
        if not self.redis_cache_enabled or not self.cache:
            return

        started = time.time()
        total_keys = 0

        try:
            logger.info("Starting genome mapping Redis warm-up from MongoDB")
            latest = {}
            mappings = self.mongo_client["metadata"]["genome_mapping"].find(
                {},
                {"genome_uuid": 1, "release_version": 1, "release_name": 1, "_id": 0},
            )
            # The cursor closes itself once fully iterated
            async for mapping in mappings:
                uuid = mapping.get("genome_uuid")
                version = mapping.get("release_version")
                version_key = release_version_key(version)
                if not uuid or version_key is None:
                    continue
                if uuid not in latest or version_key > release_version_key(
                    latest[uuid]["release_version"]
                ):
                    latest[uuid] = mapping

            database_names = await self.mongo_client.list_database_names()

            # Use a Redis pipeline to batch set genome mapping cache keys
            async with self.cache.pipeline() as pipe:
                for uuid, mapping in latest.items():
                    chosen_db = mapping_database_name(mapping, database_names)
                    if chosen_db is None:
                        continue
                    pipe.set(
                        genome_mapping_cache_key(uuid), chosen_db, ex=self.redis_expiry
                    )
                    total_keys += 1
                # Execute the pipeline to set all keys in Redis at once
                await pipe.execute()

            time_taken = time.time() - started
            logger.info(
                "[warmup_cache_from_mongo] Redis warm-up completed: %d keys in %.2fs",
                total_keys,
                time_taken,
            )
        except Exception as ex:
            logger.warning("[warmup_cache_from_mongo] Redis warm-up failed: %s", ex)

    async def connect(self):
        # Test connection to MongoDB
        try:
            await self.mongo_client.admin.command("ping")
            logger.debug("[MongoDbClient] Connected to MongoDB")
        except pymongo.errors.PyMongoError as exc:
            logger.error("[MongoDbClient] MongoDB connection failed: %s", exc)
            raise

        # Test connection to Redis if caching is enabled
        if self.redis_cache_enabled and self.cache:
            try:
                await self.cache.ping()
                logger.debug("[MongoDbClient] Connected to Redis")
                if self.warmup_cache_on_start:
                    await self.warmup_cache_from_mongo()
            except redis.RedisError as exc:
                logger.error("[MongoDbClient] Redis connection failed: %s", exc)
                self.redis_cache_enabled = False
                self.cache = None

    async def close(self):
        if self.cache:
            try:
                await self.cache.aclose()
            except Exception as exc:
                logger.warning("Failed to close async redis cache client: %s", exc)

        if self.mongo_client:
            try:
                await self.mongo_client.aclose()
            except Exception as exc:
                logger.warning("Failed to close mongo client: %s", exc)

    @staticmethod
    def connect_mongo(config):
        """Create MongoDB connection"""
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


METADATA_SERVICE = "ensembl_metadata.EnsemblMetadata"
GRPC_CHANNEL_OPTIONS = (("grpc.enable_http_proxy", 0),)


def load_metadata_reflector(target):
    """Load the metadata service protocols over a short-lived sync channel."""
    # yagrc only supports synchronous channels; this runs once at startup
    with grpc.insecure_channel(target, options=GRPC_CHANNEL_OPTIONS) as channel:
        reflector = yagrc_reflector.GrpcReflectionClient()
        reflector.load_protocols(channel, symbols=[METADATA_SERVICE])
    return reflector


class GRPCServiceClient:

    def __init__(self, channel, reflector):

        self.channel = channel
        self.reflector = reflector

        stub_class = self.reflector.service_stub_class(METADATA_SERVICE)
        self.stub_class = stub_class(self.channel)

        self.stub = self.stub_class

    @classmethod
    async def create(cls, config):
        """Run reflection off the event loop, then bind an aio channel to this loop."""
        host = config.get("GRPC_HOST")
        port = config.get("GRPC_PORT")
        target = "{}:{}".format(host, port)

        reflector = await asyncio.to_thread(load_metadata_reflector, target)
        channel = grpc.aio.insecure_channel(target, options=GRPC_CHANNEL_OPTIONS)
        return cls(channel, reflector)

    def get_grpc_stub(self):
        return self.stub

    def get_grpc_reflector(self):
        return self.reflector

    async def close(self):
        try:
            await self.channel.close()
        except Exception as exc:
            logger.warning("Failed to close async grpc client: %s", exc)
