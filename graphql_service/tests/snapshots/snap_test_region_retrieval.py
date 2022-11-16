# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot


snapshots = Snapshot()

snapshots["test_region_retrieval_by_name 1"] = {
    "region": {"code": "chromosome", "length": 114364328, "name": "13"}
}

snapshots["test_regions_retrieval_by_genome_id 1"] = {
    "regions": [{"code": "chromosome", "length": 114364328, "name": "13"}]
}
