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

def build_gene():
    'Mock representation of human BRCA2 gene'
    gene = {
        'type': 'Gene',
        'symbol': 'BRCA2',
        'name': 'BRCA2 DNA repair associated [Source:HGNC Symbol;Acc:HGNC:1101]',
        'stable_id': 'ENSG00000139618.15',
        'unversioned_stable_id': 'ENSG00000139618',
        'version': 15,
        'so_term': 'protein_coding',
        'genome_id': 'homo_sapiens_GCA_000001405_28',
        'slice': {
            'region': {
                'name': '13'
            },
            'location': {
                'start': 32315086,
                'end': 32400266,
                'length': 85181,
                'location_type': 'chromosome'
            },
            'strand': {
                'code': 'forward',
                'value': 1
            },
            'default': True
        }
    }
    return gene

def build_transcripts():
    'Mock representation of two transcripts of human BRCA2 gene'
    brca2_201 = {
        'type': 'Transcript',
        'symbol': 'BRCA2-201',
        'gene': 'ENSG00000139618.15',
        'stable_id': 'ENST00000380152.7',
        'unversioned_stable_id': 'ENST00000380152',
        'version': 7,
        'so_term': 'protein_coding',
        'genome_id': 'homo_sapiens_GCA_000001405_28',
        'exons': build_exons(),
        'slice': {
            'region': {
                'name': '13'
            },
            'location': {
                'start': 32315474,
                'end': 32400266,
                'length': 84793,
                'location_type': 'chromosome'
            },
            'strand': {
                'code': 'forward',
                'value': 1
            },
            'default': True
        },
        'spliced_exons': [
            {
                'index': 1,
                'exon': {
                    'stable_id': 'ENSE00002145385.1',
                    'slice': {
                        'region': {
                            'name': '13'
                        },
                        'location': {
                            'end': 32371100,
                            'length': 130,
                            'start': 32370971
                        },
                        'strand': {
                            'code': 'forward'
                        }
                    }
                },
                'relative_location': {
                    'start': 55498,
                    'end': 55627,
                    'length': 130
                }
            },
            {
                'index': 2,
                'exon': {
                    'stable_id': 'ENSE00002167182.1',
                    'slice': {
                        'location': {
                            'start': 32375343,
                            'end': 32375406,
                            'length': 64
                        },
                        'region': {
                            'name': '13'
                        },
                        'strand': {
                            'code': 'forward'
                        }
                    }
                },
                'relative_location': {
                    'end': 59933,
                    'length': 64,
                    'start': 59870
                }
            }
        ],
        'product_generating_contexts': [
            {
                'product_type': 'protein',
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
                        'start_phase': 0,
                        'relative_location': {
                            'end': 55627,
                            'length': 130,
                            'start': 55498
                        }
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
                        'relative_location': {
                            'end': 59933,
                            'length': 64,
                            'start': 59870
                        },
                        'index': 2,
                        'start_phase': 0
                    }
                ],
                'product_id': 'ENSP00000369497.3'
            }
        ]
    }
    brca2_203 = {
        'type': 'Transcript',
        'symbol': 'BRCA2-203',
        'gene': 'ENSG00000139618.15',
        'stable_id': 'ENST00000528762.1',
        'unversioned_stable_id': 'ENST00000528762',
        'version': 1,
        'so_term': 'nonsense_mediated_decay',
        'genome_id': 'homo_sapiens_GCA_000001405_28',
        'exons': build_exons(),
        'slice': {
            'region': {
                'name': '13'
            },
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
    return [brca2_201, brca2_203]

def build_exons():
    'Build some exons'
    return [
        {
            'type': 'Exon',
            'stable_id': 'ENSE00002145385.1',
            'unversioned_stable_id': 'ENSE00002145385',
            'version': 1,
            'slice': {
                'region': {
                    'name': '13'
                },
                'strand': {
                    'code': 'forward',
                    'value': 1
                },
                'location': {
                    'start': 32370971,
                    'end': 32371100,
                    'length': 130,
                    'location_type': 'chromosome'
                }
            }
        },
        {
            'type': 'Exon',
            'stable_id': 'ENSE00002167182.1',
            'unversioned_stable_id': 'ENSE00002167182',
            'version': 1,
            'slice': {
                'region': {
                    'name': '13'
                },
                'strand': {
                    'code': 'forward',
                    'value': 1
                },
                'location': {
                    'start': 32375343,
                    'end': 32375406,
                    'length': 64,
                    'location_type': 'chromosome'
                }
            }
        },
    ]

def build_products():
    'Create protein products for fetching individually'

    product = {
        'type': 'Protein',
        'unversioned_stable_id': 'ENSP00000369497',
        'stable_id': 'ENSP00000369497.3',
        'version': 3,
        'so_term': 'polypeptide',
        'transcript_id': 'ENST00000380152.7',
        'protein_domains': [],
        'genome_id': 'homo_sapiens_GCA_000001405_28'
    }

    # Add mature product example once we know the shape of them
    # rna = {
    #     'type': 'MatureRNA',
    #     ...
    # }

    return [product]
