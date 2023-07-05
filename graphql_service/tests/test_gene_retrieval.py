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

from graphql_service.resolver.data_loaders import BatchLoaders
from .snapshot_utils import setup_test

executable_schema, context = setup_test()


@pytest.mark.asyncio
async def test_gene_retrieval_by_id_camel_case(snapshot):
    "Test `gene` query using byId camelCase"
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
              default
              id
              name
              accession_id
              accessioning_body
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

    query_data = {"query": query}
    (success, result) = await graphql(
        executable_schema, query_data, context_value=context
    )
    assert success
    snapshot.assert_match(result["data"])


@pytest.mark.asyncio
async def test_gene_retrieval_by_id_snake_case(snapshot):
    "Test `gene` query using by_id snake case"

    query = """{
      gene(by_id: { genome_id: "homo_sapiens_GCA_000001405_28", stable_id: "ENSG00000139618.15" }) {
        symbol
        stable_id
      }
    }"""
    query_data = {"query": query}
    (success, result) = await graphql(
        executable_schema, query_data, context_value=context
    )
    assert success
    snapshot.assert_match(result["data"]["gene"])


@pytest.mark.asyncio
async def test_gene_retrieval_by_symbol(snapshot):
    "Test `genes` query using by_symbol snake_case"

    query = """{
      genes(by_symbol: { genome_id: "homo_sapiens_GCA_000001405_28", symbol: "BRCA2" }) {
        symbol
        stable_id
      }
    }"""
    query_data = {"query": query}
    (success, result) = await graphql(
        executable_schema, query_data, context_value=context
    )
    assert success
    snapshot.assert_match(result["data"]["genes"])


@pytest.mark.asyncio
async def test_transcript_pagination(snapshot):
    """
    Run a query checking pagination
    """
    query = """
    {
        gene(by_id:{
          genome_id:"homo_sapiens_GCA_000001405_28",
          stable_id: "ENSG00000139618.15"
        }) {
            transcripts_page(page: 2, per_page:1) {
                transcripts {
                    stable_id
                }
                page_metadata {
                    total_count
                    page
                    per_page
                }
            }
        }
    }
    """
    query_data = {"query": query}
    (success, result) = await graphql(
        executable_schema, query_data, context_value=context
    )
    assert success
    snapshot.assert_match(result["data"])
