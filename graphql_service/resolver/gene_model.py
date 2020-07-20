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
QUERY_TYPE = QueryType()
GENE_TYPE = ObjectType('Gene')
TRANSCRIPT_TYPE = ObjectType('Transcript')
LOCUS_TYPE = ObjectType('Locus')

@QUERY_TYPE.field('gene')
def resolve_gene(_, info, bySymbol=None, byId=None):
    'Load Genes via symbol or stable_id'

    query = {
        'type': 'Gene',
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

    result = collection.find_one(query)
    if not result:
        raise GeneNotFoundError(bySymbol, byId)
    return result

@GENE_TYPE.field('cross_references')
@TRANSCRIPT_TYPE.field('cross_references')
def insert_crossref_urls(feature, info):
    '''
    A gene/transcript with cross references in the data model is given as
    argument. Using the crossrefs package we can infer URLs to those resources
    and inject them into the response
    '''
    resolver = info.context['XrefResolver']
    xrefs = feature['cross_references']
    return list(map(resolver.annotate_crossref, xrefs))

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
    info.context['slice.genome_id'] = genome_id
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
        'genome_id': context['slice.genome_id'],
        'type': feature_type,
        'slice.region.name': context['slice.region.name'],
        'slice.location.start': {'$gt': context['slice.location.start']},
        'slice.location.end': {'$lt': context['slice.location.end']}
    }
    return context["mongo_db"].find(query)

class GeneNotFoundError(GraphQLError):
    '''
    Custom error to be raised if gene is not found
    '''
    extensions = {"code": "GENE_NOT_FOUND"}
    def __init__(self, bySymbol=None, byId=None):
        message = None
        if bySymbol:
            message = 'Failed to find gene with symbol '\
                     f"'{bySymbol['symbol']}' for genome '{bySymbol['genome_id']}'"
        if byId:
            message = 'Failed to find gene with stable id '\
                f"'{byId['stable_id']}' for genome '{byId['genome_id']}'"
        super().__init__(message, extensions=self.extensions)
