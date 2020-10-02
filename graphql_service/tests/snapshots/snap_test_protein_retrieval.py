# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot


snapshots = Snapshot()

snapshots['test_protein_retrieval_by_transcript 1'] = {
    'transcript': {
        'product_generating_contexts': [
            {
                'product': {
                    'stable_id': 'ENSP00000369497.3'
                },
                'product_type': 'protein'
            }
        ]
    }
}

snapshots['test_protein_retrieval 1'] = {
    'product': {
        'so_term': 'polypeptide',
        'stable_id': 'ENSP00000369497.3',
        'unversioned_stable_id': 'ENSP00000369497',
        'version': 3
    }
}
