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

import copy

from graphql_service.resolver.transcript_order import sort_gene_transcripts
from graphql_service.resolver.tests.dummy_transcripts_sample import (
    dummy_transcripts_sample,
)


def test_sort_prioritizes_designation_and_translation_length():
    """Verify canonical/MANE and translation length priorities using the sample."""
    # The dummy fixture encodes multiple transcript biotypes and lengths; copying
    # prevents accidental mutations leaking between tests.
    transcripts = copy.deepcopy(dummy_transcripts_sample)

    ordered_ids = [tr["stable_id"] for tr in sort_gene_transcripts(transcripts)]
    expected_ids = [
        "tr_stable_id_5",  # MANE Select & canonical always first
        "tr_stable_id_9",  # Protein coding with longer translation beats peers
        "tr_stable_id_2",
        "tr_stable_id_10",
        "tr_stable_id_1",
        "tr_stable_id_4",
        "tr_stable_id_6",
        "tr_stable_id_7",
        "tr_stable_id_8",
        "tr_stable_id_12",
        "tr_stable_id_11",
        "tr_stable_id_3",
    ]

    assert ordered_ids == expected_ids


def test_sort_prefers_translation_length_then_transcript_length():
    """Ensure translation length is used before transcript genomic length."""
    # Two protein_coding transcripts where only protein length differs.
    protein_rich = {
        "metadata": {"biotype": {"value": "protein_coding"}},
        "relative_location": {"length": 100},
        "product_generating_contexts": [
            {"cds": {"protein_length": 500}},
        ],
        "stable_id": "protein_rich",
    }
    protein_poor = copy.deepcopy(protein_rich)
    protein_poor["product_generating_contexts"][0]["cds"]["protein_length"] = 300
    protein_poor["stable_id"] = "protein_poor"

    # Removing translation info makes the raw transcript length decide.
    translation_less = copy.deepcopy(protein_rich)
    translation_less["product_generating_contexts"] = []
    translation_less["relative_location"]["length"] = 200
    translation_less["stable_id"] = "translation_less"

    ordered = sort_gene_transcripts(
        [translation_less, protein_poor, protein_rich]
    )

    assert [tr["stable_id"] for tr in ordered] == [
        "protein_rich",
        "protein_poor",
        "translation_less",
    ]


def test_sort_honors_display_rank_override():
    """Confirm that display_rank bypasses biological ordering."""
    # When display_rank is present it should fully determine the ordering.
    ranked = [
        {
            "stable_id": "low_rank",
            "display_rank": 1,
            "metadata": {"biotype": {"value": "protein_coding"}},
            "relative_location": {"length": 10},
        },
        {
            "stable_id": "high_rank",
            "display_rank": 99,
            "metadata": {"biotype": {"value": "retained_intron"}},
            "relative_location": {"length": 10},
        },
    ]

    assert [tr["stable_id"] for tr in sort_gene_transcripts(ranked)] == [
        "high_rank",
        "low_rank",
    ]
