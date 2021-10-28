# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot


snapshots = Snapshot()

snapshots['test_gene_retrieval_by_symbol 1'] = {
    'gene': {
        'stable_id': 'ENSG00000139618.15',
        'symbol': 'BRCA2'
    }
}

snapshots['test_gene_retrieval_by_id 1'] = {
    'gene': {
        'name': 'BRCA2 DNA repair associated [Source:HGNC Symbol;Acc:HGNC:1101]',
        'slice': {
            'location': {
                'end': 32400266,
                'start': 32315086
            },
            'region': {
                'name': '13',
                'length': 114364328,
                'code': 'chromosome',
                'topology': 'linear',
                'assembly': {
                    'type': 'Assembly',
                    'id': 'GRCh38.p13',
                    'default': True,
                    'name': "GRCh38",
                    'accession_id': 'GCA_000001405.28',
                    'accessioning_body': 'EGA',
                    'species': 'homo_sapiens'
                },
                'metadata': {
                    'ontology_terms': [
                        {
                            'accession_id': 'SO:0000340',
                            'value': 'chromosome',
                            'url': 'www.sequenceontology.org/browser/current_release/term/SO:0000340',
                            'source': {
                                'name': 'Sequence Ontology',
                                'url': 'www.sequenceontology.org',
                                'description': 'The Sequence Ontology is a set of terms and relationships used to describe the features and attributes of biological sequence. '
                            }
                        }
                    ]
                }
            },
            'strand': {
                'code': 'forward'
            }
        },
        'so_term': 'protein_coding',
        'stable_id': 'ENSG00000139618.15',
        'symbol': 'BRCA2',
        'transcripts': [
            {
                'stable_id': 'ENST00000380152.7'
            },
            {
                'stable_id': 'ENST00000528762.1'
            }
        ],
        'unversioned_stable_id': 'ENSG00000139618',
        'version': 15,
         'metadata': {
            'biotype': {
                'label': 'Protein coding',
                'definition': 'Transcipt that contains an open reading frame (ORF).',
                'description': None,
                'value': 'protein_coding'
            },
            'name': {
                'accession_id': 'HGNC:1101',
                'value': 'BRCA2 DNA repair associated',
                'url': 'https://www.genenames.org/data/gene-symbol-report/#!/hgnc_id/HGNC:1101',
                'source': {
                    'id': 'HGNC Symbol',
                    'name': 'HGNC',
                    'description': 'The HGNC is responsible for approving unique symbols and names for human loci, including protein coding genes, ncRNA genes and pseudogenes, to allow unambiguous scientific communication.',
                    'url': 'https://www.genenames.org/',
                    'release': None
                }
            }
        },
    }
}

snapshots['test_gene_retrieval_by_symbol 1'] = {
    'stable_id': 'ENSG00000139618.15',
    'symbol': 'BRCA2'
}
