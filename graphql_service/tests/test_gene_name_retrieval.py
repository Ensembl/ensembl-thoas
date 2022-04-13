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

"""End-to-end testing of gene name metadata queries"""

from string import Template
from ariadne import graphql
import pytest
from .snapshot_utils import setup_test

executable_schema, context = setup_test()


def get_generic_query_template():

    query = """{
          gene(byId: { genome_id: "triticum_aestivum_GCA_900519105_1", stable_id: "$stable_id" }) {
            stable_id
            metadata {
              name{
                accession_id
                value
                url
                source{
                  id
                  name
                  description
                  url
                  release
                }
              }
            }
          }
        }"""

    template = Template(query)

    return template


@pytest.mark.asyncio
async def test_no_xref_acc_id(snapshot):
    template = get_generic_query_template()
    query = template.substitute(stable_id='TraesCS2A02G142500')
    query_data = {'query': query}
    (success, result) = await graphql(executable_schema, query_data, context_value=context)
    assert success
    print(result)
    snapshot.assert_match(result['data'])

@pytest.mark.asyncio
async def test_no_xref_description(snapshot):
    template = get_generic_query_template()
    query = template.substitute(stable_id='TraesCS2A02G142501')
    query_data = {'query': query}
    (success, result) = await graphql(executable_schema, query_data, context_value=context)
    assert success
    snapshot.assert_match(result['data'])

@pytest.mark.asyncio
async def test_no_externaldb_source_id(snapshot):
    template = get_generic_query_template()
    query = template.substitute(stable_id='TraesCS2A02G142502')
    query_data = {'query': query}
    (success, result) = await graphql(executable_schema, query_data, context_value=context)
    assert success
    snapshot.assert_match(result['data'])

@pytest.mark.asyncio
async def test_no_externaldb_source_name(snapshot):
    template = get_generic_query_template()
    query = template.substitute(stable_id='TraesCS2A02G142503')
    query_data = {'query': query}
    (success, result) = await graphql(executable_schema, query_data, context_value=context)
    assert success
    snapshot.assert_match(result['data'])
