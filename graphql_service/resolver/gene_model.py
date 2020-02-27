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

from ariadne import QueryType, ObjectType, UnionType

# Define Query types for GraphQL
query = QueryType()
gene = ObjectType('Gene')
transcript = ObjectType('Transcript')
locus = UnionType('RegionResult')


@query.field('gene')
def resolve_gene(_, info, name=None, stable_id=None):

    query = {
        "type": "Gene"
    }
    if name:
        query['name'] = name
    if stable_id:
        query['stable_id'] = stable_id

    collection = info.context['mongo_db']

    result = collection.find_one(query)
    return(result)


# Open ended high cardinality queries are a bad idea, here is one
@query.field('genes')
def resolve_genes(_, info):

    collection = info.context['mongo_db']

    result = collection.find({
        "type": "Gene"
    })
    return result


@query.field('transcripts')
def resolve_transcripts(_, info):

    collection = info.context['mongo_db']
    result = collection.find({
        'type': 'Transcript'
    })
    return result


@query.field('transcript')
def resolve_transcript(root, info, stable_id):

    collection = info.context['mongo_db']
    result = collection.find_one({
        'type': 'Transcript',
        'stable_id': stable_id
    })
    return result


@gene.field('transcripts')
def resolve_gene_transcripts(gene, info):
    gene_stable_id = gene['stable_id']

    # Get a dataloader from info
    loader = info.context['data_loader'].gene_transcript_dataloader()
    # Tell DataLoader to get this request done when it feels like it
    result = loader.load(
        key=gene_stable_id
    )
    return result


# Note that this kind of hard boundary search is not often appropriate for
# genomics. Most usefully we will want any entities overlapping this range
# rather than entities entirely within the range
@query.field('slice')
def resolve_slice(_, info, region, start, end, feature_type):
    collection = info.context['mongo_db']
    result = collection.find({
        'type': feature_type,
        'slice.region.name': region,
        'slice.location.start': {'$gt': start},
        'slice.location.end': {'$lt': end}
    })
    return result


@locus.type_resolver
def resolve_feature_slice(obj, *_):
    return obj['type']
