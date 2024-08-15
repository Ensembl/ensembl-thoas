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

from .snapshot_utils import setup_test

executable_schema, context = setup_test()


@pytest.mark.asyncio
async def test_version_retrieval(snapshot):
    """
    Test `version` query using
    """

    query = """{
      version {
         api {
          major
          minor
          patch
        }
      }
    }"""
    query_data = {"query": query}

    # Unlike 'context_value' in ariadne.asgi.GraphQL, 'context_value' of
    # ariadne.graphql is not callable. It needs to be evaluated explicitly
    # as context_value=context() when creating request

    (success, result) = await graphql(
        executable_schema, query_data, context_value=context()
    )
    assert success
    snapshot.assert_match(result["data"])
