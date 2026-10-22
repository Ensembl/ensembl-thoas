"""Regression tests for Mongo-only genome routing, shared by sync/async paths."""

from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import mongomock
import mongomock_motor
import pytest
from pymongo.errors import OperationFailure
from redis.exceptions import ConnectionError as RedisConnectionError

from common.db import MongoDbClient, genome_mapping_cache_key
from graphql_service.resolver.exceptions import GenomeNotFoundError


@pytest.fixture(params=[False, True], ids=["sync", "async"])
def routing(request):
    """Use real mock collections but avoid opening network connections."""
    is_async = request.param
    client = MongoDbClient.__new__(MongoDbClient)
    client.mongo_client = mongomock.MongoClient()
    client.async_mongo_client = mongomock_motor.AsyncMongoMockClient()
    client.redis_cache_enabled = True
    client.redis_expiry = 6600
    cache = AsyncMock() if is_async else Mock()
    cache.get.return_value = None
    client.cache = cache
    client.async_cache = cache
    mongo = client.async_mongo_client if is_async else client.mongo_client
    collection = mongo.metadata.genome_mapping

    async def insert(documents):
        if is_async:
            await collection.insert_many(documents)
        else:
            collection.insert_many(documents)

    async def create_database(name):
        if is_async:
            await mongo[name].data.insert_one({"test": True})
        else:
            mongo[name].data.insert_one({"test": True})

    async def lookup(uuid="genome-1"):
        if is_async:
            return await client.get_async_database_conn(uuid)
        return client.get_database_conn(uuid, None)

    return SimpleNamespace(
        client=client,
        cache=cache,
        collection=collection,
        insert=insert,
        lookup=lookup,
        create_database=create_database,
    )


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


def test_explicit_release_bypasses_mapping_and_cache():
    client = MongoDbClient.__new__(MongoDbClient)
    client.mongo_client = mongomock.MongoClient()
    assert client.get_database_conn("genome-1", "108.1").name == "release_108_1"


def test_warmup_uses_highest_mapping_and_refreshes_with_expiry():
    client = MongoDbClient.__new__(MongoDbClient)
    client.mongo_client = mongomock.MongoClient()
    client.redis_cache_enabled = True
    client.redis_expiry = 6600
    client.cache = Mock()
    client.mongo_client.metadata.genome_mapping.insert_many(
        [
            {"genome_uuid": "one", "release_version": "110.9"},
            {"genome_uuid": "one", "release_version": "110.10"},
            {"genome_uuid": "one", "release_version": "bad"},
            {"genome_uuid": "two", "release_version": "111.1"},
            {"genome_uuid": "invalid"},
            {"release_version": "111.2"},
        ]
    )
    client.mongo_client.release_110_10.data.insert_one({"test": True})
    client.mongo_client.release_111_1.data.insert_one({"test": True})
    client.warmup_cache_from_mongo()
    assert client.cache.set.call_count == 2
    client.cache.set.assert_any_call(
        genome_mapping_cache_key("one"), "release_110_10", ex=6600
    )
    client.cache.set.assert_any_call(
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


def test_warmup_caches_fallback_and_skips_missing_databases():
    client = MongoDbClient.__new__(MongoDbClient)
    client.mongo_client = mongomock.MongoClient()
    client.redis_cache_enabled = True
    client.redis_expiry = 6600
    client.cache = Mock()
    client.mongo_client.metadata.genome_mapping.insert_many(
        [
            {"genome_uuid": "one", "release_version": "110.1", "release_name": "1"},
            {"genome_uuid": "two", "release_version": "110.2", "release_name": "2"},
        ]
    )
    client.mongo_client.release_1.data.insert_one({"test": True})
    client.warmup_cache_from_mongo()
    client.cache.set.assert_called_once_with(
        genome_mapping_cache_key("one"), "release_1", ex=6600
    )


@pytest.mark.asyncio
async def test_database_list_failure_does_not_cache(routing, monkeypatch):
    await routing.insert(
        [{"genome_uuid": "genome-1", "release_version": "110.1", "release_name": "1"}]
    )
    mongo = (
        routing.client.async_mongo_client
        if isinstance(routing.cache, AsyncMock)
        else routing.client.mongo_client
    )
    monkeypatch.setattr(
        mongo, "list_database_names", Mock(side_effect=OperationFailure("denied"))
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
