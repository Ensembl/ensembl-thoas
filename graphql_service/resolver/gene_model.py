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
LOCUS_TYPE = ObjectType('Locus')
PGC_TYPE = ObjectType('ProductGeneratingContext')
PRODUCT_TYPE = ObjectType('Product')
GENE_METADATA_TYPE = ObjectType('GeneMetadata')


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
    #unpack cursor into a list. We're guaranteed relatively small results
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
    annotated_xrefs = map(resolver.annotate_crossref, xrefs) # might contain None values due to caught exceptions
    xrefs_with_nulls_removed = filter(lambda x: x is not None, annotated_xrefs)
    return list(xrefs_with_nulls_removed)

@GENE_METADATA_TYPE.field('name')
def insert_gene_name_urls(gene_metadata, info):
    '''
    A gene metadata of a gene is given as argument.
    Using the gene name metadata info we can infer URLs to those resources
    and inject them into the response
    '''

    resolver = info.context['XrefResolver']
    gene_name_metadata = gene_metadata.get('name')

    if gene_name_metadata:
        annotated_gene_names = resolver.annotate_gene_names(gene_name_metadata)
        return annotated_gene_names

    return None


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

# Note that this kind of hard boundary search is not often appropriate for
# genomics. Most usefully we will want any entities overlapping this range
# rather than entities entirely within the range
@QUERY_TYPE.field('slice')
def resolve_slice(_, info, genome_id, region, start, end):
    '''
    Slice on its own only defines parameters for searching for different
    types. Stash the parameters for nested calls
    '''
    # Caution team, this is global, and might contaminate a second slice
    # in the same query, depending on the graph descent method
    info.context['genome_id'] = genome_id
    info.context['slice.region.name'] = region
    info.context['slice.start'] = start
    info.context['slice.end'] = end


@LOCUS_TYPE.field('genes')
def resolve_slice_genes(_, info):
    'Pass the resolved slice parameters to a query'
    return query_region(info.context, 'Gene')


@LOCUS_TYPE.field('transcripts')
def resolve_slice_transcripts(_, info):
    'Pass the resolved slice parameters to a query'
    return query_region(info.context, 'Transcript')


def query_region(context, feature_type):
    '''
    Query backend for a feature type using slice parameters:
    genome_id
    region name
    start coordinate
    end coordinate
    '''
    query = {
        'genome_id': context['genome_id'],
        'type': feature_type,
        'slice.region.name': context['slice.region.name'],
        'slice.location.start': {'$gt': context['slice.location.start']},
        'slice.location.end': {'$lt': context['slice.location.end']}
    }
    return context["mongo_db"].find(query)


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
    loader = info.context['data_loader'].transcript_product_dataloader(pgc['genome_id'])
    products = await loader.load(
        key=pgc['product_id']
    )
    # Data loader returns a list because most data-loads are one-many
    # ID mappings
    return products[0]


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
            message = 'Failed to find gene with symbol '\
                     f"'{symbol}' for genome '{genome_id}'"
            self.extensions['symbol'] = symbol
            self.extensions['genome_id'] = genome_id
        if byId:
            stable_id = byId['stable_id']
            genome_id = byId['genome_id']
            message = 'Failed to find gene with stable id '\
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
        message = 'Failed to find product with stable id '\
            f"'{stable_id}' for genome '{genome_id}'"
        self.extensions['stable_id'] = stable_id
        self.extensions['genome_id'] = genome_id
        super().__init__(message, extensions=self.extensions)
