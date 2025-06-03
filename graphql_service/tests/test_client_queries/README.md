### Context

GraphQL always returns `200` regardless of the actual response content:

> GraphQL’s "official" approach is to always return HTTP 200 even when the response payload  
> contains an `"errors"` array. The idea is that the GraphQL response itself is a valid JSON document,  
> and the client inspects `"errors"` to decide what to do next.

This makes it tricky to know whether a query actually succeeded or not.

### How it works

`test_graphql_queries.py` automatically picks up every `.graphql` file in the `queries/` directory and, for each one:

1. Reads the file's contents as a GraphQL query.  
2. Uses Starlette's `TestClient` to send that query to our running ASGI app.  
3. Confirms that the HTTP response is `200 OK`.  
4. Verifies that the JSON response does not contain an `"errors"` array (this is what really catches failures).

In other words, it "smoke-tests" all of our example queries to make sure none of them fail at runtime.

> The example queries in the `queries/` directory are the ones used by the Ensembl client.

You can run this test specifically by running:
```bash
pytest graphql_service/tests/test_client_queries/test_graphql_queries.py
```

> Please note that tests in `test_graphql_queries.py` are skipped if `MONGO_HOST` environment variable is not set
> It will be nice to alter testing process and make it run against a real Mongo DB ... Todo