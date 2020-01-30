from graphene import ObjectType, String, Schema, List, NonNull, Field
import graphql

data = {
    'brca2': {
        'name': 'brca2',
        'stable_id': 'ENSG001',
        'transcripts': [
            'ENST001', 'ENST002'
        ]
    },
    'foxp2': {
        'name': 'foxp2',
        'stable_id': 'ENSG002',
        'transcripts': [
            'ENST001'
        ]
    }
}

transcript_data = {
    'ENST001': {
        'gene_ids': ['ENSG001', 'ENSG002'],
        'stable_id': 'ENST001',
        'exons': [
            {'stable_id': 'ENSE001'},
            {'stable_id': 'ENSE002'}
        ]
    },
    'ENST002': {
        'gene_ids': ['ENSG001'],
        'stable_id': 'ENST002',
        'exons': [
            {'stable_id': 'ENSE001'}
        ]
    }
}


class Exon(ObjectType):
    stable_id = String()


class Transcript(ObjectType):
    stable_id = String()
    so_term = String()
    exons = List(NonNull(Exon))


class Gene(ObjectType):
    stable_id = String()
    name = String()
    so_term = String()
    transcripts = List(NonNull(Transcript))

    def resolve_transcripts(gene, info):
        print(gene)
        list_o_transcripts = [{'stable_id': 'ENST0005'}]
        for thing in transcript_data:
            if gene['stable_id'] in transcript_data[thing]['gene_ids']:
                list_o_transcripts.append(transcript_data[thing])
        return list_o_transcripts


class Query(ObjectType):
    gene = Field(Gene(name=String()))
    genes = List(Gene)
    transcripts = List(Transcript)
    transcript = Field(Transcript(stable_id=String()))

    def resolve_gene(_, info, name):
        return [data[i] for i in name]

    def resolve_genes(_, info):
        return [data[key] for key in data]

    def resolve_transcripts(_, info):
        print('weeeee')
        return [transcript_data[key] for key in transcript_data]

    def resolve_transcript(_, info, stable_id):
        print(stable_id)
        return transcript_data[stable_id]


q1 = '''{
        genes {
            name
        }
    }'''


q2 = '''{
        transcript(stable_id:"ENST001") {
            stable_id
        }
    }'''

q3a = '''query :{
        gene(name:"brca2") {
            name
            stable_id
        }
    }'''

q3 = '''{
        gene(name:"brca2") {
            name
            stable_id
            transcripts {
                stable_id
            }
        }
    }'''

q4 = '''{
        transcripts {
            stable_id
        }
    }'''


schema = Schema(query=Query)
print(graphql.print_schema(schema))

result = schema.execute(q4)
print(result.data)
