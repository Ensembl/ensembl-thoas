# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc

from snapshottest import Snapshot

snapshots = Snapshot()

snapshots['test_slice_retrieval 1'] = {
    'slice': {
        'genes': [],
        'transcripts': [
            {
                "stable_id": "ENST00000528762.1"
            }
        ]
    }
}
