import mongomock
import mongomock_motor


class FakeMongoDbClient:
    """
    Stands in for common.db.MongoDbClient in tests.

    Production code only sees the async client (`mongo_client`). Fixtures may
    seed data synchronously through `mongo_db` (or `sync_client`), which
    shares storage with the async client.
    """

    def __init__(self, databases_by_genome=None):
        self.sync_client = mongomock.MongoClient()  # for seeding fixtures only
        self.mongo_db = self.sync_client.db
        self.mongo_client = mongomock_motor.AsyncMongoMockClient(
            mock_mongo_client=self.sync_client
        )
        # Optional genome_id -> database name map, to test per-genome routing
        self.databases_by_genome = databases_by_genome or {}
        self.redis_cache_enabled = False
        self.cache = None

    async def get_database_conn(self, uuid, release_version=None):
        # Return the test database without resolving a release.
        return self.mongo_client[self.databases_by_genome.get(uuid, "db")]
