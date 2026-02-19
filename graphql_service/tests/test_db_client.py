import mongomock_motor


class FakeAsyncMongoDbClient:
    def __init__(self):
        self.async_mongo_client = mongomock_motor.AsyncMongoMockClient()
        self.mongo_db = self.async_mongo_client.db
        self.redis_cache_enabled = False

    async def get_async_database_conn(self, _grpc_model, _uuid):
        # we pretend that we did a gRPC call and got the chosen db
        return self.async_mongo_client["db"]
