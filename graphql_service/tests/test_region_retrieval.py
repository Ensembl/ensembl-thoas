"""
   See the NOTICE file distributed with this work for additional information
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

import pytest
from ariadne import graphql

from .snapshot_utils import setup_test, add_loaders_to_context

executable_schema, context = setup_test()


@pytest.mark.asyncio
async def test_region_retrieval(snapshot):
    query = """{
      region (by_name: {genome_id: "homo_sapiens_GCA_000001405_28", name: "13"}) {
        name
        code
        length
      }
    }"""

    query_data = {"query": query}
    (success, result) = await graphql(
        executable_schema, query_data, context_value=add_loaders_to_context(context)
    )
    assert success
    snapshot.assert_match(result["data"])


@pytest.mark.asyncio
async def test_regions_retrieval(snapshot):
    query = """{
      regions (by_genome_id: {genome_id: "homo_sapiens_GCA_000001405_28"}) {
        name
        code
        length
      }
    }
    """
    query_data = {"query": query}
    (success, result) = await graphql(
        executable_schema, query_data, context_value=add_loaders_to_context(context)
    )
    assert success
    snapshot.assert_match(result["data"])
