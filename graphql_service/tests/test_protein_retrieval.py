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


@pytest.mark.asyncio
async def test_protein_retrieval(snapshot):
    """
    Test retrieval of proteins from the graphql api by id
    Gets the expected test result from snapshottest
    """

    executable_schema, context = setup_test()
    query = """{
  product(genome_id: "homo_sapiens_GCA_000001405_28", stable_id: "ENSP00000369497.3") {
    stable_id
    unversioned_stable_id
    version
    length
    sequence {
      alphabet {
        accession_id
      }
      checksum
    }
    family_matches {
      sequence_family {
        source {
          name
        }
        name
        accession_id
        url
        description
      }
      via {
        source {
          name
        }
        accession_id
        url
      }
      relative_location {
        start
        end
        length
      }
      score
      evalue
      hit_location {
        start
        end
        length
      }
    }
    external_references {
      accession_id
      source {
        name
      }
    }
  }
}"""
    query_data = {'query': query}
    (success, result) = await graphql(executable_schema, query_data, context_value=context)
    assert success
    assert result['data']['product']
    snapshot.assert_match(result['data'])


@pytest.mark.asyncio
async def test_protein_retrieval_by_transcript(snapshot):
    """
    Test retrieval of proteins from the graphql api by transcript
    """
    executable_schema, context = setup_test()
    query = """{
        transcript(byId: {stable_id: "ENST00000380152.7", genome_id: "homo_sapiens_GCA_000001405_28"}) {
            product_generating_contexts {
                product_type
                product {
                    stable_id
                }

            }
        }
    }"""
    query_data = {'query': query}
    (success, result) = await graphql(executable_schema, query_data, context_value=context)
    assert success
    assert result['data']['transcript']
    snapshot.assert_match(result['data'])
