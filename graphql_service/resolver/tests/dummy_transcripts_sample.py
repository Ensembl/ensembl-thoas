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

# This will be used for testing

dummy_transcripts_sample = [
    {
        "metadata": {"biotype": {"label": "protein_coding", "value": "protein_coding"}},
        "relative_location": {"length": 310067},
        "stable_id": "tr_stable_id_1",
        "symbol": "PrCo Tr",
    },
    {
        "metadata": {"biotype": {"label": "protein_coding", "value": "protein_coding"}},
        "relative_location": {
            "length": 293802,
        },
        "product_generating_contexts": [
            {
                "cdna": {"length": 2826, "type": "CDNA"},
                "cds": {
                    "nucleotide_length": 1155,
                    "protein_length": 384,  # translation length comes from this field
                },
                "default": "True",
            }
        ],
        "stable_id": "tr_stable_id_2",
        "symbol": "PrCo + TranslationLength",
    },
    {
        "metadata": {
            "biotype": {"label": "retained_intron", "value": "retained_intron"}
        },
        "relative_location": {
            "length": 14501,
        },
        "stable_id": "tr_stable_id_3",
        "symbol": "Retained Intron",
    },
    {
        "metadata": {
            "biotype": {
                "label": "nonsense_mediated_decay",
                "value": "nonsense_mediated_decay",
            }
        },
        "relative_location": {
            "length": 343625,
        },
        "stable_id": "tr_stable_id_4",
        "symbol": "Nonsense Mediated Decay",
    },
    {
        "metadata": {
            "biotype": {"label": "protein_coding", "value": "protein_coding"},
            "canonical": {
                "definition": "A single, representative transcript identified at every locus",
                "label": "Ensembl canonical",
                "value": "True",
            },
            "mane": {
                "definition": "The MANE Select is a default transcript per human gene that is representative of biology, well-supported, expressed and highly-conserved.",
                "label": "MANE Select",
                "value": "select",
            },
        },
        "relative_location": {
            "length": 349649,
        },
        "stable_id": "tr_stable_id_5",
        "symbol": "MANE SE and Cano + PrCo",
    },
    {  # We stopped here
        "metadata": {"biotype": {"label": "non_stop_decay", "value": "non_stop_decay"}},
        "relative_location": {
            "length": 344123,
        },
        "stable_id": "tr_stable_id_6",
        "symbol": "NonStop Decay",
    },
    {
        "metadata": {"biotype": {"label": "IG_12345", "value": "IG_12345"}},
        "relative_location": {
            "length": 436651,
        },
        "stable_id": "tr_stable_id_7",
        "symbol": "Starts w IG_",
    },
    {
        "metadata": {
            "biotype": {
                "label": "polymorphic_pseudogene",
                "value": "polymorphic_pseudogene",
            }
        },
        "relative_location": {
            "length": 578118,
        },
        "stable_id": "tr_stable_id_8",
        "symbol": "Polymorp PseuGene",
    },
    {
        "metadata": {"biotype": {"label": "protein_coding", "value": "protein_coding"}},
        "relative_location": {
            "length": 343570,
        },
        "product_generating_contexts": [
            {
                "cdna": {"length": 2345, "type": "CDNA"},
                "cds": {
                    "nucleotide_length": 1234,
                    "protein_length": 411,
                },
                "default": "True",  # hmmm?
            }
        ],
        "stable_id": "tr_stable_id_9",
        "symbol": "PrCo + TranslationLength",
    },
    {
        "metadata": {"biotype": {"label": "protein_coding", "value": "protein_coding"}},
        "relative_location": {
            "length": 436710,
        },
        "stable_id": "tr_stable_id_10",
        "symbol": "PrCo Tr",
    },
    {
        "metadata": {
            "biotype": {"label": "retained_intron", "value": "retained_intron"}
        },
        "relative_location": {
            "length": 56466,
        },
        "stable_id": "tr_stable_id_11",
        "symbol": "Retained Intron",
    },
    {
        "metadata": {
            "biotype": {
                "label": "protein_coding_CDS_not_defined",
                "value": "protein_coding_CDS_not_defined",
            }
        },
        "relative_location": {
            "length": 59393,
        },
        "stable_id": "tr_stable_id_12",
        "symbol": "PrCo CDS not defined",
    },
]
