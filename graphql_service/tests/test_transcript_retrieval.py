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
async def test_transcript_retrieval_by_id_camel_case(snapshot):
    """
    Test retrieval of a transcript from the graphql api by id
    Gets the expected test result from snapshottest
    """
    query = """{
        transcript(byId: { genome_id: "homo_sapiens_GCA_000001405_28", stable_id: "ENST00000380152.7" }) {
            stable_id
            unversioned_stable_id
            symbol
            version
            so_term
            slice {
                region {
                    name
                }
                location {
                    start
                    end
                    length
                }
                strand {
                    code
                }
            }
            gene {
                stable_id
                unversioned_stable_id
                symbol
            }
            product_generating_contexts {
                product_type
                cds {
                    start
                    end
                    relative_start
                    relative_end
                    protein_length
                    nucleotide_length
                }
                phased_exons {
                    start_phase
                    end_phase
                    index
                    exon {
                        stable_id
                        slice {
                            region {
                                name
                            }
                            location {
                                start
                                end
                                length
                            }
                            strand {
                                code
                            }
                        }
                    }
                }
            }
        }
    }"""
    query_data = {"query": query}
    (success, result) = await graphql(
        executable_schema, query_data, context_value=context
    )
    assert success
    assert result["data"]["transcript"]
    snapshot.assert_match(result["data"])


@pytest.mark.asyncio
async def test_transcript_retrieval_by_id_snake_case(snapshot):
    query = """{
        transcript(by_id: { genome_id: "homo_sapiens_GCA_000001405_28", stable_id: "ENST00000380152.7" }) {
            stable_id
            symbol
        }
    }"""
    query_data = {"query": query}
    (success, result) = await graphql(
        executable_schema, query_data, context_value=context
    )
    assert success
    assert result["data"]["transcript"]
    snapshot.assert_match(result["data"]["transcript"])


@pytest.mark.asyncio
async def test_transcript_retrieval_by_symbol_camel_case(snapshot):
    query = """{
        transcript(bySymbol: { genome_id: "homo_sapiens_GCA_000001405_28", symbol: "BRCA2-201" }) {
            stable_id
            symbol
        }
    }"""
    query_data = {"query": query}
    (success, result) = await graphql(
        executable_schema, query_data, context_value=context
    )
    assert success
    assert result["data"]["transcript"]
    snapshot.assert_match(result["data"]["transcript"])


@pytest.mark.asyncio
async def test_transcript_retrieval_by_symbol_snake_case(snapshot):
    query = """{
        transcript(by_symbol: { genome_id: "homo_sapiens_GCA_000001405_28", symbol: "BRCA2-201" }) {
            stable_id
            symbol
        }
    }"""
    query_data = {"query": query}
    (success, result) = await graphql(
        executable_schema, query_data, context_value=context
    )
    assert success
    assert result["data"]["transcript"]
    snapshot.assert_match(result["data"]["transcript"])


@pytest.mark.asyncio
async def test_transcript_splicing(snapshot):
    """
    Run a graphql query checking transcript spliced exons
    """
    query = """
    {
        transcript(byId: { genome_id: "homo_sapiens_GCA_000001405_28", stable_id: "ENST00000380152.7" }) {
            spliced_exons {
                index
                exon {
                    stable_id
                }
            }
        }
    }"""
    (success, result) = await graphql(
        executable_schema,
        {"query": query},
        context_value=context
    )
    assert success
    assert result["data"]["transcript"]
    snapshot.assert_match(result["data"])
