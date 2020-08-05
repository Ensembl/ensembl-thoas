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
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot


snapshots = Snapshot()

snapshots['test_transcript_retrieval 1'] = {
    'transcript': {
        'slice': {
            'location': {
                'end': 32400266,
                'length': 84793,
                'start': 32315474
            },
            'region': {
                'name': '13',
                'strand': {
                    'code': 'forward'
                }
            }
        },
        'so_term': 'protein_coding',
        'splicing': [
            {
                'cds': {
                    'end': 32398770,
                    'nucleotide_length': 82309,
                    'protein_length': 27436,
                    'relative_end': 83297,
                    'relative_start': 988,
                    'start': 32316461
                },
                'product_type': 'protein',
                'spliced_exons': [
                    {
                        'end_phase': 0,
                        'exon': {
                            'relative_location': {
                                'end': 55627,
                                'length': 130,
                                'start': 55498
                            },
                            'slice': {
                                'location': {
                                    'end': 32371100,
                                    'length': 130,
                                    'start': 32370971
                                },
                                'region': {
                                    'name': '13',
                                    'strand': {
                                        'code': 'forward'
                                    }
                                }
                            },
                            'stable_id': 'ENSE00002145385.1'
                        },
                        'index': 0,
                        'start_phase': 0
                    },
                    {
                        'end_phase': 0,
                        'exon': {
                            'relative_location': {
                                'end': 59933,
                                'length': 64,
                                'start': 59870
                            },
                            'slice': {
                                'location': {
                                    'end': 32375406,
                                    'length': 64,
                                    'start': 32375343
                                },
                                'region': {
                                    'name': '13',
                                    'strand': {
                                        'code': 'forward'
                                    }
                                }
                            },
                            'stable_id': 'ENSE00002167182.1'
                        },
                        'index': 1,
                        'start_phase': 0
                    }
                ]
            }
        ],
        'stable_id': 'ENST00000380152.7',
        'unversioned_stable_id': 'ENST00000380152',
        'version': 7
    }
}
