def build_gene():
    'Mock representation of human BRCA2 gene'
    gene = {
        'type': 'Gene',
        'name': 'BRCA2',
        'description': 'BRCA2 DNA repair associated [Source:HGNC Symbol;Acc:HGNC:1101]',
        'stable_id': 'ENSG00000139618.15',
        'unversioned_stable_id': 'ENSG00000139618',
        'version': 15,
        'so_term': 'protein_coding',
        'genome_id': 'homo_sapiens_GCA_000001405_28',
        'slice': {
            'region': {
                'name': '13',
                'strand': {
                    'code': 'forward',
                    'value': 1
                }
            },
            'location': {
                'start': 32315086,
                'end': 32400266,
                'length': 85181,
                'location_type': 'chromosome'
            },
            'default': True
        }
    }
    return gene

def build_transcripts():
    'Mock representation of two transcripts of human BRCA2 gene'
    brca2_201 = {
        'type': 'Transcript',
        'name': 'BRCA2-201',
        'description': None,
        'gene': 'ENSG00000139618.15',
        'stable_id': 'ENST00000380152.7',
        'unversioned_stable_id': 'ENST00000380152',
        'version': 7,
        'so_term': 'protein_coding',
        'genome_id': 'homo_sapiens_GCA_000001405_28',
        'slice': {
            'region': {
                'name': '13',
                'strand': {
                    'code': 'forward',
                    'value': 1
                },
                'location': {
                    'start': 32315474,
                    'end': 32400266,
                    'length': 84793,
                    'location_type': 'chromosome'
                },
                'default': True
            }
        }
    }
    brca2_203 = {
        'type': 'Transcript',
        'name': 'BRCA2-203',
        'description': None,
        'gene': 'ENSG00000139618.15',
        'stable_id': 'ENST00000528762.1',
        'unversioned_stable_id': 'ENST00000528762',
        'version': 1,
        'so_term': 'nonsense_mediated_decay',
        'genome_id': 'homo_sapiens_GCA_000001405_28',
        'slice': {
            'region': {
                'name': '13',
                'strand': {
                    'code': 'forward',
                    'value': 1
                },
                'location': {
                    'start': 32370971,
                    'end': 32379495,
                    'length': 8525,
                    'location_type': 'chromosome'
                },
                'default': True
            }
        }
    }
    return [brca2_201, brca2_203]
