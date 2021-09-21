# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot


snapshots = Snapshot()

snapshots['test_transcript_splicing 1'] = {
    'transcript': {
        'spliced_exons': [
            {
                'exon': {
                    'stable_id': 'ENSE00002145385.1'
                },
                'index': 1
            },
            {
                'exon': {
                    'stable_id': 'ENSE00002167182.1'
                },
                'index': 2
            }
        ]
    }
}

snapshots['test_transcript_retrieval 1'] = {
    'transcript': {
        'gene': {
            'stable_id': 'ENSG00000139618.15',
            'symbol': 'BRCA2',
            'unversioned_stable_id': 'ENSG00000139618'
        },
        'product_generating_contexts': [
            {
                'cds': {
                    'end': 32398770,
                    'nucleotide_length': 82309,
                    'protein_length': 27436,
                    'relative_end': 83297,
                    'relative_start': 988,
                    'start': 32316461
                },
                'phased_exons': [
                    {
                        'end_phase': 0,
                        'exon': {
                            'slice': {
                                'location': {
                                    'end': 32371100,
                                    'length': 130,
                                    'start': 32370971
                                },
                                'region': {
                                    'name': '13'
                                },
                                'strand': {
                                    'code': 'forward'
                                }
                            },
                            'stable_id': 'ENSE00002145385.1'
                        },
                        'index': 1,
                        'start_phase': 0
                    },
                    {
                        'end_phase': 0,
                        'exon': {
                            'slice': {
                                'location': {
                                    'end': 32375406,
                                    'length': 64,
                                    'start': 32375343
                                },
                                'region': {
                                    'name': '13'
                                },
                                'strand': {
                                    'code': 'forward'
                                }
                            },
                            'stable_id': 'ENSE00002167182.1'
                        },
                        'index': 2,
                        'start_phase': 0
                    }
                ],
                'product_type': 'protein'
            }
        ],
        'slice': {
            'location': {
                'end': 32400266,
                'length': 84793,
                'start': 32315474
            },
            'region': {
                'name': '13'
            },
            'strand': {
                'code': 'forward'
            }
        },
        'so_term': 'protein_coding',
        'stable_id': 'ENST00000380152.7',
        'symbol': 'BRCA2-201',
        'unversioned_stable_id': 'ENST00000380152',
        'version': 7
    }
}
