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

# Define Query types for GraphQL
query = QueryType()
gene = ObjectType('Gene')
transcript = ObjectType('Transcript')
locus = ObjectType('Locus')


@query.field('gene')
def resolve_gene(_, info, bySymbol=None, byId=None):

    query = {
        'type': 'Gene',
    }
    if bySymbol:
        query['name'] = bySymbol['symbol']
        query['genome_id'] = bySymbol['genome_id']
    if byId:
        query['stable_id'] = byId['stable_id']
        query['genome_id'] = byId['genome_id']

    collection = info.context['mongo_db']

    result = collection.find_one(query)
    return(result)


# Open ended high cardinality queries are a bad idea, here is one
@query.field('genes')
def resolve_genes(_, info, genome_id):

    collection = info.context['mongo_db']

    result = collection.find({
        'type': 'Gene',
        'genome_id': genome_id
    })
    return result


@gene.field('cross_references')
def insert_urls(root, info, genome_id):
    '''
    root here is a transcript/gene/protein with cross references in the data
    model. Using the crossrefs package we can infer URLs to those resources
    and inject them into the response
    '''
    resolver = info.context['xref_resolver']
    xrefs = root['cross_references']
    return map(resolver.annotate_crossref, xrefs)


@query.field('transcripts')
def resolve_transcripts(_, info, genome_id):

    collection = info.context['mongo_db']
    result = collection.find({
        'type': 'Transcript',
        'genome_id': genome_id
    })
    return result


@query.field('transcript')
def resolve_transcript(root, info, bySymbol=None, byId=None):

    query = {
        'type': 'Transcript'
    }
    if bySymbol:
        query['name'] = bySymbol['symbol']
        query['genome_id'] = bySymbol['genome_id']
    if byId:
        query['stable_id'] = byId['stable_id']
        query['genome_id'] = byId['genome_id']

    collection = info.context['mongo_db']
    result = collection.find_one(query)
    return result


@gene.field('transcripts')
def resolve_gene_transcripts(gene, info):
    gene_stable_id = gene['stable_id']

    # Get a dataloader from info
    loader = info.context['data_loader'].gene_transcript_dataloader(gene['genome_id'])
    # Tell DataLoader to get this request done when it feels like it
    result = loader.load(
        key=gene_stable_id
    )
    return result


# Note that this kind of hard boundary search is not often appropriate for
# genomics. Most usefully we will want any entities overlapping this range
# rather than entities entirely within the range
@query.field('slice')
def resolve_slice(_, info, genome_id, region, start, end):

    # Caution team, this is global, and might contaminate a second slice
    # in the same query, depending on the graph descent method
    info.context['slice.genome_id'] = genome_id
    info.context['slice.region.name'] = region
    info.context['slice.start'] = start
    info.context['slice.end'] = end
    return None


@locus.field('genes')
def resolve_slice_genes(_, info):
    return query_region(info.context, 'Gene')


@locus.field('transcripts')
def resolve_slice_transcripts(_, info):
    return query_region(info.context, 'Transcript')


def query_region(context, feature_type):
    query = {
        'genome_id': context['slice.genome_id'],
        'type': feature_type,
        'slice.region.name': context['slice.region.name'],
        'slice.location.start': {'$gt': context['slice.location.start']},
        'slice.location.end': {'$lt': context['slice.location.end']}
    }
    return context["mongo_db"].find(query)
