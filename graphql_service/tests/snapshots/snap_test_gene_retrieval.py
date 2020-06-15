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

snapshots['test_gene_retrieval_by_id 1'] = {
    'gene': {
        'description': 'BRCA2 DNA repair associated [Source:HGNC Symbol;Acc:HGNC:1101]',
        'name': 'BRCA2',
        'slice': {
            'location': {
                'end': 32400266,
                'start': 32315086
            },
            'region': {
                'name': '13',
                'strand': {
                    'code': 'forward'
                }
            }
        },
        'so_term': 'protein_coding',
        'stable_id': 'ENSG00000139618.15',
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

snapshots['test_gene_retrieval_by_symbol 1'] = {
    'gene': {
        'name': 'BRCA2',
        'stable_id': 'ENSG00000139618.15'
    }
}
