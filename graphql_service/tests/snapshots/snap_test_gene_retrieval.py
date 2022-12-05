# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot


snapshots = Snapshot()

snapshots["test_gene_retrieval_by_id_camel_case 1"] = {
    "gene": {
        "metadata": {
            "biotype": {
                "definition": "Transcipt that contains an open reading frame (ORF).",
                "description": None,
                "label": "Protein coding",
                "value": "protein_coding",
            },
            "name": {
                "accession_id": "HGNC:1101",
                "source": {
                    "description": "HUGO Genome Nomenclature Committee",
                    "id": "HGNC",
                    "name": "HGNC Symbol",
                    "release": None,
                    "url": "https://www.genenames.org",
                },
                "url": "https://www.genenames.org/data/gene-symbol-report/#!/hgnc_id/HGNC:1101",
                "value": "BRCA2 DNA repair associated",
            },
        },
        "name": "BRCA2 DNA repair associated [Source:HGNC Symbol;Acc:HGNC:1101]",
        "slice": {
            "location": {"end": 32400266, "start": 32315086},
            "region": {
                "assembly": {
                    "accession_id": "GCA_000001405.28",
                    "accessioning_body": "EGA",
                    "default": True,
                    "id": "GRCh38.p13",
                    "name": "GRCh38",
                },
                "code": "chromosome",
                "length": 114364328,
                "metadata": {
                    "ontology_terms": [
                        {
                            "accession_id": "SO:0000340",
                            "source": {
                                "description": "The Sequence Ontology is a set of terms and relationships used to describe the features and attributes of biological sequence. ",
                                "name": "Sequence Ontology",
                                "url": "www.sequenceontology.org",
                            },
                            "url": "www.sequenceontology.org/browser/current_release/term/SO:0000340",
                            "value": "chromosome",
                        }
                    ]
                },
                "name": "13",
                "topology": "linear",
            },
            "strand": {"code": "forward"},
        },
        "so_term": "protein_coding",
        "stable_id": "ENSG00000139618.15",
        "symbol": "BRCA2",
        "transcripts": [
            {"stable_id": "ENST00000380152.7"},
            {"stable_id": "ENST00000528762.1"},
        ],
        "unversioned_stable_id": "ENSG00000139618",
        "version": 15,
    }
}

snapshots["test_gene_retrieval_by_id_snake_case 1"] = {
    "stable_id": "ENSG00000139618.15",
    "symbol": "BRCA2",
}

snapshots["test_gene_retrieval_by_symbol 1"] = [
    {"stable_id": "ENSG00000139618.15", "symbol": "BRCA2"}
]

snapshots["test_transcript_pagination 1"] = {
    "gene": {
        "transcripts_page": {
            "page_metadata": {"page": 2, "per_page": 1, "total_count": 2},
            "transcripts": [{"stable_id": "ENST00000528762.1"}],
        }
    }
}

snapshots["test_transcript_pagination_filters"] = {
    "gene": {
        "transcripts_page": {
            "page_metadata": {"page": 1, "per_page": 2, "total_count": 1},
            "transcripts": [{"stable_id": "ENST00000380152.7"}],
        }
    }
}

snapshots["test_transcript_pagination_filters 1"] = {
    "gene": {
        "transcripts_page": {
            "page_metadata": {"page": 1, "per_page": 2, "total_count": 1},
            "transcripts": [{"stable_id": "ENST00000380152.7"}],
        }
    }
}
