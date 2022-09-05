# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot


snapshots = Snapshot()

expected_protein = {
    "product": {
        "external_references": [
            {"accession_id": "Q9NFB6", "source": {"name": "UniProtKB/TrEMBL"}}
        ],
        "family_matches": [
            {
                "evalue": 5.1e-63,
                "hit_location": {"end": 157, "length": 157, "start": 1},
                "relative_location": {"end": 762, "length": 161, "start": 602},
                "score": 212.5,
                "sequence_family": {
                    "accession_id": "PF03011",
                    "description": "PFEMP",
                    "name": "PF03011",
                    "source": {"name": "Pfam"},
                    "url": "http://pfam.xfam.org/family/PF03011",
                },
                "via": {
                    "accession_id": "IPR004258",
                    "source": {"name": "InterProScan"},
                    "url": "https://www.ebi.ac.uk/interpro/entry/InterPro/IPR004258",
                },
            }
        ],
        "length": 100,
        "sequence": {
            "alphabet": {"accession_id": "test_protein_accession_id"},
            "checksum": "ca80cf1d4af7cc47aa28f8427d0d8bc6",
        },
        "stable_id": "ENSP00000369497.3",
        "unversioned_stable_id": "ENSP00000369497",
        "version": 3,
    }
}
snapshots["test_protein_retrieval_separate_arguments 1"] = expected_protein

snapshots["test_protein_retrieval_by_id_input 1"] = expected_protein

snapshots["test_protein_retrieval_by_transcript 1"] = {
    "transcript": {
        "product_generating_contexts": [
            {"product": {"stable_id": "ENSP00000369497.3"}, "product_type": "protein"}
        ]
    }
}
