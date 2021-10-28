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
async def test_gene_retrieval_by_id(snapshot):
    'Test retrieval of a gene from the grapqhl api by id'
    query = """{
      gene(byId: { genome_id: "homo_sapiens_GCA_000001405_28", stable_id: "ENSG00000139618.15" }) {
        symbol
        name
        stable_id
        unversioned_stable_id
        version
        so_term
        metadata {
          biotype {
            label
            definition
            description
            value
          }
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
        transcripts {
          stable_id
        }
        slice {
          region {
            name
            code
            length
            topology
            assembly {
              type
              default
              id
              name
              accession_id
              accessioning_body
              species
            }
            metadata {
              ontology_terms {
                accession_id
                value
                url
                source {
                  name
                  url
                  description
                }
              }
            }
          }
          location {
            start
            end
          }
          strand {
            code
          }
        }
      }
    }"""

    query_data = {'query': query}
    (success, result) = await graphql(executable_schema, query_data, context_value=context)
    assert success
    snapshot.assert_match(result['data'])

@pytest.mark.asyncio
async def test_gene_retrieval_by_symbol(snapshot):
    'Test retrieval of a gene from the graphql api by its symbol'
    query = """{
      genes_by_symbol(bySymbol: { genome_id: "homo_sapiens_GCA_000001405_28", symbol: "BRCA2" }) {
        symbol
        stable_id
      }
    }"""
    query_data = {'query': query}
    (success, result) = await graphql(executable_schema, query_data, context_value=context)
    assert success
    snapshot.assert_match(result['data']['genes_by_symbol'][0])
