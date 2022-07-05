# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc

from snapshottest import Snapshot

snapshots = Snapshot()

snapshots["test_slice_retrieval 1"] = {
    "overlap_region": {
        "genes": [{"stable_id": "ENSG00000139618.15"}],
        "transcripts": [{"stable_id": "ENST00000380152.7"}],
    }
}
