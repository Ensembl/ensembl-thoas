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
                'name': '13'
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
        'version': 15
    }
}
