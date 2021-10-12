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
            'genome_id': 1 # This should be added by the top-level resolver on query
        }


@pytest.fixture(name='basic_data')
def fixture_basic_data():
    'Some fake genes'
    collection = mongomock.MongoClient().db.collection
    collection.insert_many([
        {'genome_id': 1, 'type': 'Gene', 'symbol': 'banana', 'stable_id': 'ENSG001.1', 'unversioned_stable_id': 'ENSG001'},
        {'genome_id': 1, 'type': 'Gene', 'symbol': 'durian', 'stable_id': 'ENSG002.2', 'unversioned_stable_id': 'ENSG002'},
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
            'genome_id': 1,
            'type': 'Gene',
            'symbol': 'banana',
            'stable_id': 'ENSG001.1',
            'unversioned_stable_id': 'ENSG001',
            'slice': {
                'region': {
                    'name': 'chr1'
                },
                'location': {
                    'start': 10,
                    'end': 100
                }
            }
        },
        {
            'genome_id': 1,
            'type': 'Gene',
            'symbol': 'durian',
            'stable_id': 'ENSG002.2',
            'unversioned_stable_id': 'ENSG002',
            'slice': {
                'region': {
                    'name': 'chr1'
                },
                'location': {
                    'start': 110,
                    'end': 200
                }
            }
        }
    ])
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

    with pytest.raises(model.FeatureNotFoundError) as feature_not_found_error:
        result = model.resolve_gene(
            None,
            basic_data,
            byId={'stable_id': 'BROKEN BROKEN BROKEN', 'genome_id': 1}
        )
    assert not result
    assert feature_not_found_error.value.message == "Failed to find gene with stable " \
                                                    "id 'BROKEN BROKEN BROKEN' for genome '1'"
    assert feature_not_found_error.value.extensions['code'] == 'GENE_NOT_FOUND'
    assert feature_not_found_error.value.extensions['stable_id'] == 'BROKEN BROKEN BROKEN'
    assert feature_not_found_error.value.extensions['genome_id'] == 1
    feature_not_found_error = None

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

    with pytest.raises(model.FeatureNotFoundError) as feature_not_found_error:
        result = model.resolve_genes(
            None,
            basic_data,
            bySymbol={'symbol': 'very not here', 'genome_id': 1}
        )
    assert not result
    assert feature_not_found_error.value.message == "Failed to find gene with symbol 'very not here' for genome '1'"
    assert feature_not_found_error.value.extensions['code'] == 'GENE_NOT_FOUND'
    assert feature_not_found_error.value.extensions['symbol'] == 'very not here'
    assert feature_not_found_error.value.extensions['genome_id'] == 1

def test_resolve_transcript_by_id(transcript_data):
    'Test fetching of transcripts by stable ID'
    result = model.resolve_transcript(
        None,
        transcript_data,
        byId={'stable_id': 'ENST001.1', 'genome_id': 1}
    )

    assert result['symbol'] == 'kumquat'
    assert result['stable_id'] == 'ENST001.1'

def test_resolve_transcript_by_id_not_found(transcript_data):
    result = None
    with pytest.raises(model.FeatureNotFoundError) as feature_not_found_error:
        result = model.resolve_transcript(
            None,
            transcript_data,
            byId={'stable_id': 'FAKEYFAKEYFAKEY', 'genome_id': 1}
        )
    assert not result
    assert feature_not_found_error.value.message == "Failed to find transcript with stable " \
                                                    "id 'FAKEYFAKEYFAKEY' for genome '1'"
    assert feature_not_found_error.value.extensions['code'] == 'TRANSCRIPT_NOT_FOUND'
    assert feature_not_found_error.value.extensions['stable_id'] == 'FAKEYFAKEYFAKEY'
    assert feature_not_found_error.value.extensions['genome_id'] == 1

def test_resolve_transcript_by_symbol(transcript_data):
    'Test fetching of transcripts by symbol'
    result = model.resolve_transcript(
        None,
        transcript_data,
        bySymbol={'symbol': 'kumquat', 'genome_id': 1}
    )
    assert result['stable_id'] == 'ENST001.1'

def test_resolve_transcript_by_symbol_not_found(transcript_data):
    result = None
    with pytest.raises(model.FeatureNotFoundError) as feature_not_found_error:
        result = model.resolve_transcript(
            None,
            transcript_data,
            bySymbol={'symbol': 'some not existing symbol', 'genome_id': 1}
        )
    assert feature_not_found_error.value.message == "Failed to find transcript with symbol " \
                                                    "'some not existing symbol' for genome '1'"
    assert feature_not_found_error.value.extensions['code'] == 'TRANSCRIPT_NOT_FOUND'
    assert feature_not_found_error.value.extensions['symbol'] == 'some not existing symbol'
    assert feature_not_found_error.value.extensions['genome_id'] == 1


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
        genome_id=1,
        region='chr1',
        start=10,
        end=11,
    )
    assert not result

    context = slice_data.context
    result = model.query_region(
        {
            'genome_id': 1,
            'slice.region.name': 'chr1',
            'slice.location.start': 1,
            'slice.location.end': 120,
            'mongo_db': context["mongo_db"]
        },
        'Gene'
    )
    hit = result.next()
    assert hit['stable_id'] == 'ENSG001.1'

    result = model.query_region(
        {
            'genome_id': 1,
            'slice.region.name': 'chr1',
            'slice.location.start': 5,
            'slice.location.end': 205,
            'mongo_db': context["mongo_db"]
        },
        'Gene'
    )
    for hit in result:
        assert hit['stable_id'] in ['ENSG001.1', 'ENSG002.2']


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
    assert result[0]['assignment_method']['description'] == 'A reference made by an external resource of annotation to an Ensembl feature that Ensembl imports without modification'


@pytest.mark.asyncio
async def test_resolve_transcript_products(transcript_data):
    'Check the DataLoader for products is working via transcript. Requires event loop for DataLoader'
    result = await model.resolve_product_by_pgc(
        {'product_id': 'ENSP001.1', 'genome_id':1},
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
