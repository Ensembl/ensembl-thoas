# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot


snapshots = Snapshot()

snapshots["test_genome_retrieval 1"] = {
    "gene": {
        "slice": {
            "region": {
                "assembly": {
                    "name": "GRCh38",
                    "organism": {
                        "assemblies": [{"name": "GRCh38"}],
                        "scientific_name": "Homo sapiens",
                        "species": {
                            "organisms": [{"scientific_name": "Homo sapiens"}],
                            "scientific_name": "Homo sapiens",
                        },
                    },
                    "regions": [{"name": "13"}],
                },
                "name": "13",
            }
        },
        "symbol": "BRCA2",
    }
}
