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

from ariadne import QueryType, ObjectType
from graphql import GraphQLError

# Define Query types for GraphQL
# Don't forget to import these into ariadne_app.py if you add a new type
QUERY_TYPE = QueryType()
GENE_TYPE = ObjectType('Gene')
TRANSCRIPT_TYPE = ObjectType('Transcript')
PGC_TYPE = ObjectType('ProductGeneratingContext')
PRODUCT_TYPE = ObjectType('Product')
SLICE_TYPE = ObjectType('Slice')


@QUERY_TYPE.field('gene')
def resolve_gene(_, info, byId=None):
    'Load Gene via stable_id'

    query = {
        'type': 'Gene',
        '$or': [
            {'stable_id': byId['stable_id']},
            {'unversioned_stable_id': byId['stable_id']}
        ],
        'genome_id': byId['genome_id']
    }

    collection = info.context['mongo_db']
    result = collection.find_one(query)
    if not result:
        raise GeneNotFoundError(byId=byId)
    return result


@QUERY_TYPE.field('genes_by_symbol')
def resolve_genes(_, info, bySymbol=None):
    'Load Genes via potentially ambiguous symbol'

    query = {
        'genome_id': bySymbol['genome_id'],
        'type': 'Gene',
        'symbol': bySymbol['symbol']
    }

    collection = info.context['mongo_db']

    result = collection.find(query)
    # unpack cursor into a list. We're guaranteed relatively small results
    result = list(result)
    if len(list(result)) == 0:
        raise GeneNotFoundError(bySymbol=bySymbol)
    return list(result)


@GENE_TYPE.field('external_references')
@TRANSCRIPT_TYPE.field('external_references')
@PRODUCT_TYPE.field('external_references')
def insert_crossref_urls(feature, info):
    '''
    A gene/transcript with cross references in the data model is given as
    argument. Using the crossrefs package we can infer URLs to those resources
    and inject them into the response
    '''
    resolver = info.context['XrefResolver']
    xrefs = feature['external_references']
    annotated_xrefs = map(resolver.annotate_crossref, xrefs)  # might contain None values due to caught exceptions
    xrefs_with_nulls_removed = filter(lambda x: x is not None, annotated_xrefs)
    return list(xrefs_with_nulls_removed)


@QUERY_TYPE.field('transcript')
def resolve_transcript(_, info, bySymbol=None, byId=None):
    'Load Transcripts by symbol or stable_id'
    query = {
        'type': 'Transcript'
    }
    if bySymbol:
        query['name'] = bySymbol['symbol']
        query['genome_id'] = bySymbol['genome_id']
    if byId:
        query['$or'] = [
            {'stable_id': byId['stable_id']},
            {'unversioned_stable_id': byId['stable_id']}
        ]
        query['genome_id'] = byId['genome_id']

    collection = info.context['mongo_db']
    transcript = collection.find_one(query)
    return transcript


@GENE_TYPE.field('transcripts')
async def resolve_gene_transcripts(gene, info):
    'Use a DataLoader to get transcripts for the parent gene'

    gene_stable_id = gene['stable_id']
    # Get a dataloader from info
    loader = info.context['data_loader'].gene_transcript_dataloader(gene['genome_id'])
    # Tell DataLoader to get this request done when it feels like it
    transcripts = await loader.load(
        key=gene_stable_id
    )
    return transcripts


@TRANSCRIPT_TYPE.field('product_generating_contexts')
async def resolve_transcript_pgc(transcript, info):
    pgcs = []
    for pgc in transcript['product_generating_contexts']:
        pgc['genome_id'] = transcript['genome_id']
        pgcs.append(pgc)
    return pgcs


@TRANSCRIPT_TYPE.field('gene')
async def resolve_transcript_gene(transcript, info):
    'Use a DataLoader to get the parent gene of a transcript'
    query = {
        'type': 'Gene',
        'genome_id': transcript['genome_id'],
        'stable_id': transcript['gene']
    }
    collection = info.context['mongo_db']
    gene = collection.find_one(query)
    return gene


# Note that this kind of hard boundary search is not often appropriate for
# genomics. Most usefully we will want any entities overlapping this range
# rather than entities entirely within the range
@QUERY_TYPE.field('slice')
def resolve_slice(_, info, genome_id, region_name, start, end):
    '''
    Query Mongo for genes and transcripts lying between start and end
    '''
    # Thoas only contains "chromosome"-type regions
    region_id = "_".join([genome_id, region_name, "chromosome"])
    return {
        "genes": query_region(info.context, region_id, start, end, 'Gene'),
        "transcripts": query_region(info.context, region_id, start, end, 'Transcript')
    }


def query_region(context, region_id, start, end, feature_type):
    '''
    Query backend for a feature type using slice parameters:
    region id
    start coordinate
    end coordinate
    feature type
    '''
    query = {
        'type': feature_type,
        'slice.region_id': region_id,
        'slice.location.start': {'$gt': start},
        'slice.location.end': {'$lt': end}
    }
    max_results_size = 1000
    results = list(context["mongo_db"].find(query).limit(max_results_size))
    if len(results) == max_results_size:
        raise SliceLimitExceededError(max_results_size)
    return results


@PGC_TYPE.field('three_prime_utr')
def resolve_three_prime_utr(pgc, _):
    'Convert stored 3` UTR to GraphQL compatible form'
    return pgc['3_prime_utr']


@PGC_TYPE.field('five_prime_utr')
def resolve_utr(pgc, _):
    'Convert stored 5` UTR to GraphQL compatible form'
    return pgc['5_prime_utr']


@QUERY_TYPE.field('product')
def resolve_product_by_id(_, info, genome_id, stable_id):
    'Fetch a product by stable_id, this is almost always a protein'

    query = {
        'genome_id': genome_id,
        'stable_id': stable_id,
        'type': {
            '$in': ['Protein', 'MatureRNA']
        }
    }

    collection = info.context['mongo_db']
    result = collection.find_one(query)

    if not result:
        raise ProductNotFoundError(genome_id, stable_id)
    return result


@PGC_TYPE.field('product')
async def resolve_product_by_pgc(pgc, info):
    'Fetch product that is referenced by the Product Generating Context'

    if pgc['product_id'] is None:
        return
    loader = info.context['data_loader'].transcript_product_dataloader(pgc['genome_id'])
    products = await loader.load(
        key=pgc['product_id']
    )
    # Data loader returns a list because most data-loads are one-many
    # ID mappings
    return products[0]


@SLICE_TYPE.field('region')
async def resolve_region(slc, info):
    'Fetch a region that is referenced by a slice'
    if slc['region_id'] is None:
        return
    region_id = slc['region_id']

    query = {
        'type': 'Region',
        'region_id': region_id
    }

    collection = info.context['mongo_db']
    result = collection.find_one(query)

    if not result:
        raise RegionNotFoundError(region_id)
    return result


class GeneNotFoundError(GraphQLError):
    '''
    Custom error to be raised if gene is not found
    '''
    extensions = {"code": "GENE_NOT_FOUND"}

    def __init__(self, bySymbol=None, byId=None):
        message = None
        if bySymbol:
            symbol = bySymbol['symbol']
            genome_id = bySymbol['genome_id']
            message = 'Failed to find gene with symbol ' \
                      f"'{symbol}' for genome '{genome_id}'"
            self.extensions['symbol'] = symbol
            self.extensions['genome_id'] = genome_id
        if byId:
            stable_id = byId['stable_id']
            genome_id = byId['genome_id']
            message = 'Failed to find gene with stable id ' \
                      f"'{stable_id}' for genome '{genome_id}'"
            self.extensions['stable_id'] = stable_id
            self.extensions['genome_id'] = genome_id
        super().__init__(message, extensions=self.extensions)


class ProductNotFoundError(GraphQLError):
    '''
    Custom error to be raised if gene is not found
    '''
    extensions = {"code": "PRODUCT_NOT_FOUND"}

    def __init__(self, genome_id, stable_id):
        message = 'Failed to find product with stable id ' \
                  f"'{stable_id}' for genome '{genome_id}'"
        self.extensions['stable_id'] = stable_id
        self.extensions['genome_id'] = genome_id
        super().__init__(message, extensions=self.extensions)


class RegionNotFoundError(GraphQLError):
    '''
    Custom error to be raised if region is not found
    '''
    extensions = {"code": "REGION_NOT_FOUND"}

    def __init__(self, region_id):
        message = 'Failed to find region with region_id ' \
                  f"'{region_id}'"
        self.extensions['region_id'] = region_id
        super().__init__(message, extensions=self.extensions)


class SliceLimitExceededError(GraphQLError):
    '''
    Custom error to be raised if number of slice results exceeds limit
    '''
    extensions = {"code": "SLICE_RESULT_LIMIT_EXCEEDED"}

    def __init__(self, max_results_size):
        message = f'Slice query met size limit of {max_results_size}'
        super().__init__(message, extensions=self.extensions)
