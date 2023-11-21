# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot


snapshots = Snapshot()

snapshots['test_version_retrieval 1'] = {
    'version': {
        'api': {
            'major': '0',
            'minor': '2',
            'patch': '0-beta'
        }
    }
}
