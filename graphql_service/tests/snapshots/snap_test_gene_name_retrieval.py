# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc

"""Test data for gene name retrieval tests"""

from __future__ import unicode_literals

from snapshottest import Snapshot


snapshots = Snapshot()

snapshots["test_no_externaldb_source_id 1"] = {
    "gene": {
        "metadata": {
            "name": {
                "accession_id": "A0A1D5TR86",
                "source": None,
                "url": None,
                "value": "Sulfotransferase [Source:UniProtKB/TrEMBL;Acc:A0A1D5TR86]",
            }
        },
        "stable_id": "TraesCS2A02G142502",
    }
}

snapshots["test_no_externaldb_source_name 1"] = {
    "gene": {
        "metadata": {
            "name": {
                "accession_id": "A0A1D5TR86",
                "source": None,
                "url": "http://purl.uniprot.org/uniprot/A0A1D5TR86",
                "value": "Sulfotransferase [Source:UniProtKB/TrEMBL;Acc:A0A1D5TR86]",
            }
        },
        "stable_id": "TraesCS2A02G142503",
    }
}

snapshots["test_no_xref_acc_id 1"] = {
    "gene": {
        "metadata": {
            "name": {
                "accession_id": None,
                "source": {
                    "description": "Universal Protein Resource using Persistent URL system",
                    "id": "UniProtKB/TrEMBL",
                    "name": "UniProtKB/TrEMBL",
                    "release": None,
                    "url": "https://www.uniprot.org/",
                },
                "url": None,
                "value": "Sulfotransferase [Source:UniProtKB/TrEMBL;Acc:A0A1D5TR86]",
            }
        },
        "stable_id": "TraesCS2A02G142500",
    }
}

snapshots["test_no_xref_description 1"] = {
    "gene": {
        "metadata": {
            "name": {
                "accession_id": "A0A1D5TR86",
                "source": {
                    "description": "Universal Protein Resource using Persistent URL system",
                    "id": "UniProtKB/TrEMBL",
                    "name": "UniProtKB/TrEMBL",
                    "release": None,
                    "url": "https://www.uniprot.org/",
                },
                "url": "http://purl.uniprot.org/uniprot/A0A1D5TR86",
                "value": None,
            }
        },
        "stable_id": "TraesCS2A02G142501",
    }
}
