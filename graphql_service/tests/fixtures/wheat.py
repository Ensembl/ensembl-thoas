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

def build_with_no_xref_acc_id():
    gene = {
        'type': 'Gene',
        'stable_id': 'TraesCS2A02G142500',
        'genome_id': 'triticum_aestivum_GCA_900519105_1',
        'metadata': {
            'name': {
                'accession_id': None,
                'value': 'Sulfotransferase [Source:UniProtKB/TrEMBL;Acc:A0A1D5TR86]',
                'url': None,
                'source': {
                    'id': 'UniProtKB/TrEMBL',
                    'name': 'UniProtKB/TrEMBL',
                    'description': None,
                    'url': None,
                    'release': None
                }
            }
        }
    }
    return gene


def build_with_no_xref_description():
    gene = {
        'type': 'Gene',
        'stable_id': 'TraesCS2A02G142501',
        'genome_id': 'triticum_aestivum_GCA_900519105_1',
        'metadata': {
            'name': {
                'accession_id': 'A0A1D5TR86',
                'value': None,
                'url': None,
                'source': {
                    'id': 'UniProtKB/TrEMBL',
                    'name': 'UniProtKB/TrEMBL',
                    'description': None,
                    'url': None,
                    'release': None
                }
            }
        }
    }
    return gene


def build_with_no_externaldb_source_id():
    gene = {
        'type': 'Gene',
        'stable_id': 'TraesCS2A02G142502',
        'genome_id': 'triticum_aestivum_GCA_900519105_1',
        'metadata': {
            'name': {
                'accession_id': 'A0A1D5TR86',
                'value': 'Sulfotransferase [Source:UniProtKB/TrEMBL;Acc:A0A1D5TR86]',
                'url': None,
                'source': {
                    'id': None,
                    'name': 'UniProtKB/TrEMBL',
                    'description': None,
                    'url': None,
                    'release': None
                }
            }
        }
    }
    return gene

def build_with_no_externaldb_source_name():
    gene = {
        'type': 'Gene',
        'stable_id': 'TraesCS2A02G142503',
        'genome_id': 'triticum_aestivum_GCA_900519105_1',
        'metadata': {
            'name': {
                'accession_id': 'A0A1D5TR86',
                'value': 'Sulfotransferase [Source:UniProtKB/TrEMBL;Acc:A0A1D5TR86]',
                'url': None,
                'source': {
                    'id': 'UniProtKB/TrEMBL',
                    'name': None,
                    'description': None,
                    'url': None,
                    'release': None
                }
            }
        }
    }
    return gene