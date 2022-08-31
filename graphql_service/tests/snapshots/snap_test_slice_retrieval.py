# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc

from snapshottest import Snapshot

snapshots = Snapshot()

expected_overlap = {
    "overlap_region": {
        "genes": [{"stable_id": "ENSG00000139618.15"}],
        "transcripts": [{"stable_id": "ENST00000380152.7"}],
    }
}
snapshots["test_slice_retrieval 1"] = expected_overlap

snapshots["test_slice_retrieval_by_slice_input 1"] = expected_overlap
