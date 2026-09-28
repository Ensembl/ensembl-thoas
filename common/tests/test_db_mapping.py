"""Regression tests for Mongo-first genome routing, shared by sync/async paths."""

from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import mongomock
import mongomock_motor
import pytest
from pymongo.errors import OperationFailure
from redis.exceptions import ConnectionError as RedisConnectionError

from common.db import MongoDbClient, genome_mapping_cache_key
from graphql_service.resolver.exceptions import (
    FailedToConnectToGrpc,
    GenomeNotFoundError,
)


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
    grpc = Mock()
    grpc.get_release_by_genome_uuid = AsyncMock() if is_async else Mock()
    grpc.get_release_by_genome_uuid.return_value = SimpleNamespace(
        release_version="109.1"
    )
    mongo = client.async_mongo_client if is_async else client.mongo_client
    collection = mongo.metadata.genome_mapping

    async def insert(documents):
        if is_async:
            await collection.insert_many(documents)
        else:
            collection.insert_many(documents)

    async def lookup(uuid="genome-1"):
        if is_async:
            return await client.get_async_database_conn(grpc, uuid)
        return client.get_database_conn(grpc, uuid, None)

    return SimpleNamespace(
        client=client,
        cache=cache,
        grpc=grpc,
        collection=collection,
        insert=insert,
        lookup=lookup,
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
    database = await routing.lookup()
    assert database.name == "release_" + expected.replace(".", "_")
    routing.grpc.get_release_by_genome_uuid.assert_not_called()
    routing.cache.set.assert_called_once_with(
        genome_mapping_cache_key("genome-1"), expected, ex=6600
    )


@pytest.mark.asyncio
async def test_missing_mapping_falls_back_to_grpc(routing):
    database = await routing.lookup()
    assert database.name == "release_109_1"
    routing.grpc.get_release_by_genome_uuid.assert_called_once_with("genome-1")
    routing.cache.set.assert_called_once_with(
        genome_mapping_cache_key("genome-1"), "109.1", ex=6600
    )


@pytest.mark.asyncio
async def test_invalid_mappings_fall_back_to_grpc(routing):
    await routing.insert(
        [
            {"genome_uuid": "genome-1", "release_version": version}
            for version in [None, "", "latest", "110.bad", 110.1]
        ]
    )
    assert (await routing.lookup()).name == "release_109_1"
    routing.grpc.get_release_by_genome_uuid.assert_called_once()


@pytest.mark.asyncio
async def test_mapping_read_failure_falls_back(routing, monkeypatch):
    monkeypatch.setattr(
        routing.collection, "find", Mock(side_effect=OperationFailure("denied"))
    )
    assert (await routing.lookup()).name == "release_109_1"
    routing.grpc.get_release_by_genome_uuid.assert_called_once()


@pytest.mark.asyncio
async def test_cache_hit_bypasses_mongo_and_grpc(routing, monkeypatch):
    routing.cache.get.return_value = b"108.2"
    find = Mock(side_effect=AssertionError("Mongo should not be queried"))
    monkeypatch.setattr(routing.collection, "find", find)
    assert (await routing.lookup()).name == "release_108_2"
    routing.cache.get.assert_called_once_with(genome_mapping_cache_key("genome-1"))
    routing.grpc.get_release_by_genome_uuid.assert_not_called()
    find.assert_not_called()


@pytest.mark.asyncio
async def test_redis_failure_does_not_prevent_mongo_mapping(routing):
    routing.cache.get.side_effect = RedisConnectionError("unavailable")
    routing.cache.set.side_effect = RedisConnectionError("unavailable")
    await routing.insert([{"genome_uuid": "genome-1", "release_version": "110.1"}])
    assert (await routing.lookup()).name == "release_110_1"
    routing.grpc.get_release_by_genome_uuid.assert_not_called()


@pytest.mark.asyncio
async def test_disabled_cache_still_uses_mongo(routing):
    routing.client.redis_cache_enabled = False
    await routing.insert([{"genome_uuid": "genome-1", "release_version": "110.1"}])
    assert (await routing.lookup()).name == "release_110_1"
    routing.cache.get.assert_not_called()
    routing.cache.set.assert_not_called()
    routing.grpc.get_release_by_genome_uuid.assert_not_called()


@pytest.mark.asyncio
async def test_missing_grpc_release_preserves_not_found(routing):
    routing.grpc.get_release_by_genome_uuid.return_value = SimpleNamespace(
        release_version=""
    )
    with pytest.raises(GenomeNotFoundError):
        await routing.lookup()
    routing.cache.set.assert_not_called()


@pytest.mark.asyncio
async def test_grpc_failure_preserves_connection_error(routing):
    routing.grpc.get_release_by_genome_uuid.side_effect = RuntimeError("unavailable")
    with pytest.raises(FailedToConnectToGrpc):
        await routing.lookup()
    routing.cache.set.assert_not_called()


def test_explicit_release_bypasses_mapping_and_cache():
    client = MongoDbClient.__new__(MongoDbClient)
    client.mongo_client = mongomock.MongoClient()
    grpc = Mock()
    assert client.get_database_conn(grpc, "genome-1", "108.1").name == "release_108_1"
    grpc.get_release_by_genome_uuid.assert_not_called()


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
    client.warmup_cache_from_mongo()
    assert client.cache.set.call_count == 2
    client.cache.set.assert_any_call(genome_mapping_cache_key("one"), "110.10", ex=6600)
    client.cache.set.assert_any_call(genome_mapping_cache_key("two"), "111.1", ex=6600)
