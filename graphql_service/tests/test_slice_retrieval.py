# """
#    See the NOTICE file distributed with this work for additional information
#    regarding copyright ownership.
#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
#        http://www.apache.org/licenses/LICENSE-2.0
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.
# """
import pytest
from ariadne import graphql

from .snapshot_utils import setup_test

executable_schema, context = setup_test()


@pytest.mark.asyncio
async def test_slice_retrieval(snapshot):
    "Test searching for genes & transcripts by slice"

    # The start/end parameters in this query only contain the brca2_203 transcript
    query = """query {
      overlap_region(
          genomeId: "homo_sapiens_GCA_000001405_28"
          regionName: "13"
          start: 32379496,
          end: 32400266
      )
      {
        genes {
          stable_id
        }
        transcripts {
          stable_id
        }
      }
    }"""

    query_data = {"query": query}
    (success, result) = await graphql(
        executable_schema, query_data, context_value=context
    )
    assert success
    snapshot.assert_match(result["data"])
