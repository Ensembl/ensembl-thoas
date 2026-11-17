"""Regression tests for Mongo-only genome routing in MongoDbClient."""

from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import mongomock
import mongomock_motor
import pytest
from pymongo.errors import OperationFailure
from redis.exceptions import ConnectionError as RedisConnectionError

from common.db import MongoDbClient, genome_mapping_cache_key
from graphql_service.resolver.exceptions import GenomeNotFoundError


def make_client():
    """
    Build a MongoDbClient without running __init__, so nothing connects.

    Returns the client and a sync mongomock client that shares its storage,
    which tests use to seed data.
    """
    sync_mongo = mongomock.MongoClient()
    client = MongoDbClient.__new__(MongoDbClient)
    client.mongo_client = mongomock_motor.AsyncMongoMockClient(
        mock_mongo_client=sync_mongo
    )
    client.redis_cache_enabled = True
    client.redis_expiry = 6600
    return client, sync_mongo


@pytest.fixture
def routing():
    """Use real mock collections but avoid opening network connections."""
    client, sync_mongo = make_client()
    cache = AsyncMock()
    cache.get.return_value = None
    client.cache = cache
    collection = client.mongo_client.metadata.genome_mapping

    async def insert(documents):
        await collection.insert_many(documents)

    async def create_database(name):
        sync_mongo[name].data.insert_one({"test": True})

    async def lookup(uuid="genome-1"):
        return await client.get_database_conn(uuid)

    return SimpleNamespace(
        client=client,
        cache=cache,
        collection=collection,
        insert=insert,
        lookup=lookup,
        create_database=create_database,
    )


class FakePipeline:
    """Records `set` calls the way a redis.asyncio pipeline buffers them."""

    def __init__(self):
        self.set = Mock()
        self.executed = False

    async def __aenter__(self):
        return self

    async def __aexit__(self, *_exc_info):
        return False

    async def execute(self):
        self.executed = True


def make_warmup_client():
    client, sync_mongo = make_client()
    pipeline = FakePipeline()
    client.cache = Mock()
    client.cache.pipeline.return_value = pipeline
    return client, sync_mongo, pipeline


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "versions,expected",
    [
        (["110.9", "110.1", "110.10"], "110.10"),
        (["99.99", "110.1", "109.100"], "110.1"),
    ],
)
async def test_highest_numeric_release_wins(routing, versions, expected):
    await routing.insert(
        [
            {
                "genome_uuid": "genome-1",
                "release_version": version,
                "release_name": str(i),
            }
            for i, version in enumerate(versions)
        ]
        + [{"genome_uuid": "other", "release_version": "999.1"}]
    )
    await routing.create_database("release_" + expected.replace(".", "_"))
    database = await routing.lookup()
    assert database.name == "release_" + expected.replace(".", "_")
    routing.cache.set.assert_called_once_with(
        genome_mapping_cache_key("genome-1"), database.name, ex=6600
    )


@pytest.mark.asyncio
async def test_missing_mapping_raises_not_found(routing):
    with pytest.raises(GenomeNotFoundError):
        await routing.lookup()
    routing.cache.set.assert_not_called()


@pytest.mark.asyncio
async def test_invalid_mappings_raise_not_found(routing):
    await routing.insert(
        [
            {"genome_uuid": "genome-1", "release_version": version}
            for version in [None, "", "latest", "110.bad", 110.1]
        ]
    )
    with pytest.raises(GenomeNotFoundError):
        await routing.lookup()
    routing.cache.set.assert_not_called()


@pytest.mark.asyncio
async def test_mapping_read_failure_raises_not_found(routing, monkeypatch):
    monkeypatch.setattr(
        routing.collection, "find", Mock(side_effect=OperationFailure("denied"))
    )
    with pytest.raises(GenomeNotFoundError):
        await routing.lookup()
    routing.cache.set.assert_not_called()


@pytest.mark.asyncio
async def test_cache_hit_bypasses_mongo(routing, monkeypatch):
    routing.cache.get.return_value = b"release_108_2"
    find = Mock(side_effect=AssertionError("Mongo should not be queried"))
    monkeypatch.setattr(routing.collection, "find", find)
    assert (await routing.lookup()).name == "release_108_2"
    routing.cache.get.assert_called_once_with(genome_mapping_cache_key("genome-1"))
    find.assert_not_called()


@pytest.mark.asyncio
async def test_redis_failure_does_not_prevent_mongo_mapping(routing):
    routing.cache.get.side_effect = RedisConnectionError("unavailable")
    routing.cache.set.side_effect = RedisConnectionError("unavailable")
    await routing.insert([{"genome_uuid": "genome-1", "release_version": "110.1"}])
    await routing.create_database("release_110_1")
    assert (await routing.lookup()).name == "release_110_1"


@pytest.mark.asyncio
async def test_disabled_cache_still_uses_mongo(routing):
    routing.client.redis_cache_enabled = False
    await routing.insert([{"genome_uuid": "genome-1", "release_version": "110.1"}])
    await routing.create_database("release_110_1")
    assert (await routing.lookup()).name == "release_110_1"
    routing.cache.get.assert_not_called()
    routing.cache.set.assert_not_called()


@pytest.mark.asyncio
async def test_explicit_release_bypasses_mapping_and_cache():
    client, _ = make_client()
    client.cache = AsyncMock()
    database = await client.get_database_conn("genome-1", "108.1")
    assert database.name == "release_108_1"
    client.cache.get.assert_not_called()


@pytest.mark.asyncio
async def test_warmup_uses_highest_mapping_and_refreshes_with_expiry():
    client, sync_mongo, pipeline = make_warmup_client()
    sync_mongo.metadata.genome_mapping.insert_many(
        [
            {"genome_uuid": "one", "release_version": "110.9"},
            {"genome_uuid": "one", "release_version": "110.10"},
            {"genome_uuid": "one", "release_version": "bad"},
            {"genome_uuid": "two", "release_version": "111.1"},
            {"genome_uuid": "invalid"},
            {"release_version": "111.2"},
        ]
    )
    sync_mongo.release_110_10.data.insert_one({"test": True})
    sync_mongo.release_111_1.data.insert_one({"test": True})
    await client.warmup_cache_from_mongo()
    assert pipeline.executed
    assert pipeline.set.call_count == 2
    pipeline.set.assert_any_call(
        genome_mapping_cache_key("one"), "release_110_10", ex=6600
    )
    pipeline.set.assert_any_call(
        genome_mapping_cache_key("two"), "release_111_1", ex=6600
    )


@pytest.mark.asyncio
@pytest.mark.parametrize("version_exists", [False, True])
async def test_version_database_preferred_then_release_name(routing, version_exists):
    await routing.insert(
        [{"genome_uuid": "genome-1", "release_version": "110.1", "release_name": "1"}]
    )
    await routing.create_database("release_1")
    if version_exists:
        await routing.create_database("release_110_1")
    expected = "release_110_1" if version_exists else "release_1"
    assert (await routing.lookup()).name == expected
    routing.cache.set.assert_called_once_with(
        genome_mapping_cache_key("genome-1"), expected, ex=6600
    )


@pytest.mark.asyncio
async def test_missing_databases_raise_not_found(routing):
    await routing.insert(
        [{"genome_uuid": "genome-1", "release_version": "110.1", "release_name": "1"}]
    )
    with pytest.raises(GenomeNotFoundError):
        await routing.lookup()
    routing.cache.set.assert_not_called()


@pytest.mark.asyncio
async def test_fallback_uses_name_from_highest_mapping(routing):
    await routing.insert(
        [
            {
                "genome_uuid": "genome-1",
                "release_version": "110.1",
                "release_name": "1",
            },
            {
                "genome_uuid": "genome-1",
                "release_version": "110.2",
                "release_name": "2",
            },
        ]
    )
    await routing.create_database("release_1")
    await routing.create_database("release_2")
    assert (await routing.lookup()).name == "release_2"


@pytest.mark.asyncio
async def test_warmup_caches_fallback_and_skips_missing_databases():
    client, sync_mongo, pipeline = make_warmup_client()
    sync_mongo.metadata.genome_mapping.insert_many(
        [
            {"genome_uuid": "one", "release_version": "110.1", "release_name": "1"},
            {"genome_uuid": "two", "release_version": "110.2", "release_name": "2"},
        ]
    )
    sync_mongo.release_1.data.insert_one({"test": True})
    await client.warmup_cache_from_mongo()
    pipeline.set.assert_called_once_with(
        genome_mapping_cache_key("one"), "release_1", ex=6600
    )


@pytest.mark.asyncio
async def test_database_list_failure_does_not_cache(routing, monkeypatch):
    await routing.insert(
        [{"genome_uuid": "genome-1", "release_version": "110.1", "release_name": "1"}]
    )
    monkeypatch.setattr(
        routing.client.mongo_client,
        "list_database_names",
        AsyncMock(side_effect=OperationFailure("denied")),
    )
    with pytest.raises(GenomeNotFoundError):
        await routing.lookup()
    routing.cache.set.assert_not_called()


@pytest.mark.asyncio
async def test_missing_release_name_and_version_database_raise_not_found(routing):
    await routing.insert([{"genome_uuid": "genome-1", "release_version": "110.1"}])
    with pytest.raises(GenomeNotFoundError):
        await routing.lookup()
    routing.cache.set.assert_not_called()
