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

import pytest
import mongomock
from graphql import GraphQLError

import graphql_service.resolver.gene_model as model
import graphql_service.resolver.data_loaders as data_loader
from common.crossrefs import XrefResolver


class Info():
    '''
    Proxy for the Info objects produced by graphql
    '''

    def __init__(self, collection):
        self.collection = collection
        self.context = {
            'stuff': 'Nonsense',
            'mongo_db': self.collection,
            'data_loader': data_loader.DataLoaderCollection(self.collection),
            'XrefResolver': XrefResolver(from_file='common/tests/mini_identifiers.json'),
            'genome_id': 1  # This should be added by the top-level resolver on query
        }


@pytest.fixture(name='basic_data')
def fixture_basic_data():
    'Some fake genes'
    collection = mongomock.MongoClient().db.collection
    collection.insert_many([
        {'genome_id': 1, 'type': 'Gene', 'symbol': 'banana', 'stable_id': 'ENSG001.1',
         'unversioned_stable_id': 'ENSG001'},
        {'genome_id': 1, 'type': 'Gene', 'symbol': 'durian', 'stable_id': 'ENSG002.2',
         'unversioned_stable_id': 'ENSG002'},
    ])
    return Info(collection)


@pytest.fixture(name='transcript_data')
def fixture_transcript_data():
    'Some fake transcripts'
    collection = mongomock.MongoClient().db.collection
    collection.insert_many([
        {
            'genome_id': 1,
            'type': 'Gene',
            'symbol': 'banana',
            'stable_id': 'ENSG001.1',
            'unversioned_stable_id': 'ENSG001'
        },
        {
            'genome_id': 1,
            'type': 'Transcript',
            'symbol': 'kumquat',
            'stable_id': 'ENST001.1',
            'unversioned_stable_id': 'ENST001',
            'gene': 'ENSG001.1',
            'product_generating_contexts': [
                {
                    'product_type': 'Protein',
                    'product_id': 'ENSP001.1'
                }
            ]
        },
        {
            'genome_id': 1,
            'type': 'Transcript',
            'symbol': 'grape',
            'stable_id': 'ENST002.2',
            'unversioned_stable_id': 'ENST002',
            'gene': 'ENSG001.1',
            'product_generating_contexts': []
        },
        {
            'genome_id': 1,
            'type': 'Protein',
            'stable_id': 'ENSP001.1'
        }
    ])
    return Info(collection)


@pytest.fixture(name='region_data')
def fixture_region_data():
    collection = mongomock.MongoClient().db.collection
    collection.insert_many([
        {"type": "Region", "region_id": "plasmodium_falciparum_GCA_000002765_2_13", "name": "13"},
        {"type": "Region", "region_id": "plasmodium_falciparum_GCA_000002765_2_14", "name": "14"}
    ])
    return Info(collection)


@pytest.fixture(name='slice_data')
def fixture_slice_data():
    '''
    Test genes with slices
    '''
    collection = mongomock.MongoClient().db.collection
    collection.insert_many([
        {
            'genome_id': "test_genome_id",
            'type': 'Gene',
            'symbol': 'banana',
            'stable_id': 'ENSG001.1',
            'unversioned_stable_id': 'ENSG001',
            'slice': {
                'region_id': 'test_genome_chr1_chromosome',
                'location': {
                    'start': 10,
                    'end': 100
                }
            }
        },
        {
            'genome_id': "test_genome_id",
            'type': 'Gene',
            'symbol': 'durian',
            'stable_id': 'ENSG002.2',
            'unversioned_stable_id': 'ENSG002',
            'slice': {
                'region_id': 'test_genome_chr1_chromosome',
                'location': {
                    'start': 110,
                    'end': 200
                }
            }
        }
    ])

    too_many_results = []

    for i in range(1001):
        too_many_results.append({
            'genome_id': "test_genome_id",
            'type': 'Gene',
            'symbol': 'banana',
            'stable_id': "test_stable_id." + str(i),
            'unversioned_stable_id': "test_stable_id." + str(i),
            'slice': {
                'region_id': 'test_genome_chr1_chromosome',
                'location': {
                    'start': 210,
                    'end': 300
                }
            }
        })
    collection.insert_many(too_many_results)

    return Info(collection)


def test_resolve_gene(basic_data):
    'Test the querying of Mongo by gene symbol'

    result = model.resolve_gene(
        None,
        basic_data,
        byId={'stable_id': 'ENSG001.1', 'genome_id': 1}
    )

    assert result['symbol'] == 'banana'
    result = None

    with pytest.raises(GraphQLError) as graphql_error:
        result = model.resolve_gene(
            None,
            basic_data,
            byId={'stable_id': 'BROKEN BROKEN BROKEN', 'genome_id': 1}
        )
    assert not result
    assert graphql_error.value.extensions['code'] == 'GENE_NOT_FOUND'
    assert graphql_error.value.extensions['stable_id'] == 'BROKEN BROKEN BROKEN'
    assert graphql_error.value.extensions['genome_id'] == 1
    graphql_error = None

    # Check unversioned query resolves as well
    result = model.resolve_gene(
        None,
        basic_data,
        byId={'stable_id': 'ENSG001', 'genome_id': 1}
    )

    assert result['symbol'] == 'banana'


def test_resolve_gene_by_symbol(basic_data):
    'Test querying by gene symbol which can be ambiguous'

    result = model.resolve_genes(
        None,
        basic_data,
        bySymbol={'symbol': 'banana', 'genome_id': 1}
    )
    assert isinstance(result, list)
    assert result[0]['symbol'] == 'banana'
    result = None

    with pytest.raises(GraphQLError) as graphql_error:
        result = model.resolve_genes(
            None,
            basic_data,
            bySymbol={'symbol': 'very not here', 'genome_id': 1}
        )
    assert not result
    assert graphql_error.value.extensions['code'] == 'GENE_NOT_FOUND'
    assert graphql_error.value.extensions['symbol'] == 'very not here'
    assert graphql_error.value.extensions['genome_id'] == 1

    graphql_error = None


def test_resolve_transcript(transcript_data):
    'Test fetching of transcripts by stable ID'
    result = model.resolve_transcript(
        None,
        transcript_data,
        byId={'stable_id': 'ENST001.1', 'genome_id': 1}
    )

    assert result['symbol'] == 'kumquat'
    assert result['stable_id'] == 'ENST001.1'

    result = model.resolve_transcript(
        None,
        transcript_data,
        byId={'stable_id': 'FAKEYFAKEYFAKEY', 'genome_id': 1}
    )
    assert not result


@pytest.mark.asyncio
async def test_resolve_gene_transcripts(transcript_data):
    'Check the DataLoader for transcripts is working via gene. Requires event loop for DataLoader'
    result = await model.resolve_gene_transcripts(
        {'stable_id': 'ENSG001.1', 'genome_id': 1},
        transcript_data
    )

    for hit in result:
        assert hit['type'] == 'Transcript'
        assert hit['symbol'] in ['kumquat', 'grape']


@pytest.mark.asyncio
async def test_resolve_gene_from_transcript(transcript_data):
    'Check the DataLoader for gene is working via transcript. Requires event loop for DataLoader'
    result = await model.resolve_transcript_gene(
        {'gene': 'ENSG001.1', 'genome_id': 1},
        transcript_data
    )

    assert result['type'] == 'Gene'
    assert result['stable_id'] == 'ENSG001.1'
    assert result['symbol'] == 'banana'


def test_resolve_slice(slice_data):
    'Check features can be found via coordinates'
    result = model.resolve_slice(
        None,
        slice_data,
        genome_id="test_genome",
        region_name='chr1',
        start=10,
        end=11,
    )
    assert {hit['stable_id'] for hit in result['genes']} == {'ENSG001.1'}


query_region_expectations = [
    (1, 5, set()),  # No overlaps
    (40, 50, {'ENSG001.1'}),  # search region contained in a single feature
    (5, 105, {'ENSG001.1'}),  # search region contains a feature
    (5, 15, {'ENSG001.1'}),  # search region contains start of a feature but not the end
    (95, 105, {'ENSG001.1'}),  # search region contains end of a feature but not the start
    (5, 205, {'ENSG001.1', 'ENSG002.2'}),  # search region contains two features
    (50, 150, {'ENSG001.1', 'ENSG002.2'})  # search region overlaps two features
]


@pytest.mark.parametrize("start,end,expected_ids", query_region_expectations)
def test_query_region(start, end, expected_ids, slice_data):
    context = slice_data.context
    result = model.query_region(
        context=context,
        region_id='test_genome_chr1_chromosome',
        start=start,
        end=end,
        feature_type='Gene'
    )
    assert {hit['stable_id'] for hit in result} == expected_ids


def test_query_region_too_many_results(slice_data):
    context = slice_data.context
    result = None
    with pytest.raises(model.SliceLimitExceededError) as slice_limit_exceeded_error:
        result = model.query_region(
            context=context,
            region_id='test_genome_chr1_chromosome',
            start=205,
            end=305,
            feature_type='Gene'
        )
    assert not result
    assert slice_limit_exceeded_error.value.message == "Slice query met size limit of 1000"
    assert slice_limit_exceeded_error.value.extensions['code'] == "SLICE_RESULT_LIMIT_EXCEEDED"


@pytest.mark.asyncio
async def test_resolve_region_happy_case(region_data):
    slc = {
        'region_id': 'plasmodium_falciparum_GCA_000002765_2_13',
        'location':
            {
                'start': 624785,
                'end': 626011,
                'length': 1227
            },
        'strand':
            {
                'code': 'forward',
                'value': 1
            },
        'default': True
    }
    result = await model.resolve_region(slc, region_data)
    assert result['region_id'] == 'plasmodium_falciparum_GCA_000002765_2_13'


@pytest.mark.asyncio
async def test_resolve_region_region_not_exist(region_data):
    slc = {
        'region_id': 'some_non_existing_region_id',
    }
    result = None
    with pytest.raises(model.RegionNotFoundError) as region_error:
        result = await model.resolve_region(slc, region_data)
    assert not result
    assert region_error.value.extensions['region_id'] == 'some_non_existing_region_id'


def test_url_generation(basic_data):
    'Check URLs are attached to cross references'
    xref = {
        'accession_id': 'some_molecule',
        'name': 'Chemistry rocks',
        'assignment_method': {
            'type': 'DIRECT'
        },
        'description': 'Chemistry is the best',
        'source': {
            'id': 'ChEBI',
            'name': 'Chemical Entities of Biological Interest',
            'description': None,
            'release': 10
        }
    }

    result = model.insert_crossref_urls(
        {
            'external_references': [
                xref
            ]
        },
        basic_data
    )

    for key, value in xref.items():
        assert result[0][key] == value, 'Original structure retained'

    assert result[0]['url'] == 'https://www.ebi.ac.uk/chebi/searchId.do?chebiId=CHEBI:some_molecule'
    assert result[0]['source']['url'] == 'https://www.ebi.ac.uk/chebi/'
    assert result[0]['assignment_method'][
               'description'] == 'A reference made by an external resource of annotation to an Ensembl feature that Ensembl imports without modification'


@pytest.mark.asyncio
async def test_resolve_transcript_products(transcript_data):
    'Check the DataLoader for products is working via transcript. Requires event loop for DataLoader'
    result = await model.resolve_product_by_pgc(
        {'product_id': 'ENSP001.1', 'genome_id': 1},
        transcript_data
    )

    assert result['type'] == 'Protein'
    assert result['stable_id'] == 'ENSP001.1'


@pytest.mark.asyncio
async def test_resolve_nested_products(transcript_data):
    'Test products inside transcripts inside the gene'
    gene_result = model.resolve_gene(
        None, transcript_data, byId={'genome_id': 1, 'stable_id': 'ENSG001.1'}
    )
    assert gene_result

    transcript_result = await model.resolve_gene_transcripts(gene_result, transcript_data)
    for i in transcript_result:
        for pgc in i['product_generating_contexts']:
            pgc['genome_id'] = 1
            product_result = await model.resolve_product_by_pgc(pgc, transcript_data)
            if 'stable_id' in product_result:
                assert product_result['stable_id'] == 'ENSP001.1'
