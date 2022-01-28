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

import os

from ariadne.asgi import GraphQL
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import Response

from common.utils import load_config
from common.crossrefs import XrefResolver
from common import mongo
from graphql_service.ariadne_app import prepare_executable_schema, prepare_context_provider
from graphql_service.metrics_view import metrics
from graphql_service.resolver.data_loaders import DataLoaderCollection
from prometheus_client import Counter

REQUESTS = Counter(
    "starlette_requests_total", "Total count of requests by method", ["method"]
)

print(os.environ)


class PrometheusMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        REQUESTS.labels(method=request.method).inc()

        return await call_next(request)


CONFIG = load_config(os.getenv('GQL_CONF'))

MONGO_CLIENT = mongo.MongoDbClient(CONFIG)

EXECUTABLE_SCHEMA = prepare_executable_schema()

# Initialise all data loaders
DATA_LOADER = DataLoaderCollection(MONGO_CLIENT.collection())

RESOLVER = XrefResolver(internal_mapping_file='docs/xref_LOD_mapping.json')

CONTEXT_PROVIDER = prepare_context_provider({
    'mongo_db': MONGO_CLIENT.collection(),
    'data_loader': DATA_LOADER,
    'XrefResolver': RESOLVER
})

starlette_middleware = [
    Middleware(CORSMiddleware, allow_origins=['*'], allow_methods=['GET', 'POST']),
    Middleware(PrometheusMiddleware)
]

APP = Starlette(debug=True, middleware=starlette_middleware)
APP.add_route("/metrics/", metrics)
APP.mount("/", GraphQL(EXECUTABLE_SCHEMA, debug=True, context_value=CONTEXT_PROVIDER))
