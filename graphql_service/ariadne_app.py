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

import ariadne
from graphql_service.resolver.gene_model import (
    QUERY_TYPE, GENE_TYPE, TRANSCRIPT_TYPE, PGC_TYPE,
    PRODUCT_TYPE, SLICE_TYPE, REGION_TYPE, GENE_METADATA_TYPE
)

def prepare_executable_schema():
    """
    Combine schema definitions with corresponding resolvers
    """
    schema = ariadne.load_schema_from_path('common/schemas')
    return ariadne.make_executable_schema(
        schema,
        QUERY_TYPE,
        GENE_TYPE,
        TRANSCRIPT_TYPE,
        PGC_TYPE,
        PRODUCT_TYPE,
        GENE_METADATA_TYPE,
        SLICE_TYPE,
        REGION_TYPE
    )

def prepare_context_provider(context):
    """
    Returns function for injecting context to graphql executors.
    The context will contain a pre-configured DB client and other goodies.
    """
    def context_provider(request):
        context['request'] = request
        return context
    return context_provider
