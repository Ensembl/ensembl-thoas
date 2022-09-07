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
from typing import Dict, Callable

import ariadne
from graphql import GraphQLSchema
from starlette.requests import Request

from graphql_service.resolver.gene_model import (
    QUERY_TYPE,
    GENE_TYPE,
    TRANSCRIPT_TYPE,
    PGC_TYPE,
    PRODUCT_TYPE,
    SLICE_TYPE,
    REGION_TYPE,
    GENE_METADATA_TYPE,
)


def prepare_executable_schema() -> GraphQLSchema:
    """
    Combine schema definitions with corresponding resolvers
    """
    schema = ariadne.load_schema_from_path("common/schemas")
    return ariadne.make_executable_schema(
        schema,
        QUERY_TYPE,
        GENE_TYPE,
        TRANSCRIPT_TYPE,
        PGC_TYPE,
        PRODUCT_TYPE,
        GENE_METADATA_TYPE,
        SLICE_TYPE,
        REGION_TYPE,
    )


def prepare_context_provider(context: Dict) -> Callable[[Request], Dict]:
    """
    Returns function for injecting context to graphql executors.

    context: The context objects that we want to inject to the graphql
    executors.  The `context_provider` method is a closure, so the
    `context` variable will be the same Python object for every request.
    This means that it should only contain objects that we want to share
    between requests, for example Mongo client, XrefResolver
    """

    def context_provider(request: Request) -> Dict:
        """We must return a new object with every request,
        otherwise the requests will pollute each other's state"""
        return {"request": request, **context}

    return context_provider
