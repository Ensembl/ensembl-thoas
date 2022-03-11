"""   See the NOTICE file distributed with this work for additional information
   regarding copyright ownership.
   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at
       http://www.apache.org/licenses/LICENSE-2.0
   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License."""

from scripts.prepare_gene_name_metadata import extract_info_from_description_column


def test_extract_info_from_description_column():
    gene = {
        'stable_id': 'TraesCS7D02G209800',
        'description': 'Transcription factor PERIANTHIA [Source:Projected from Arabidopsis thaliana (AT1G68640) UniProtKB/Swiss-Prot;Acc:Q9SX27]',
        'xref_primary_acc': None,
        'xref_display_label': None,
        'xref_description': None,
        'external_db_name': None,
        'external_db_display_name': None,
        'external_db_release': None
    }

    gene_name_info = {
        'gene_stable_id': gene.get('stable_id'),
        'gene_description': gene.get('description'),
        'xref_primary_acc': None,
        'xref_display_label': None,
        'xref_description': None,
        'external_db_name': None,
        'external_db_display_name': None,
        'external_db_release': None
    }

    expected = {
        "gene_stable_id": "TraesCS7D02G209800",
        "gene_description": "Transcription factor PERIANTHIA [Source:Projected from Arabidopsis thaliana (AT1G68640) UniProtKB/Swiss-Prot;Acc:Q9SX27]",
        "xref_primary_acc": "Q9SX27",
        "xref_display_label": None,
        "xref_description": "Transcription factor PERIANTHIA [Source:Projected from Arabidopsis thaliana (AT1G68640) UniProtKB/Swiss-Prot;Acc:Q9SX27]",
        "external_db_name": "UniProtKB/Swiss-Prot",
        "external_db_display_name": "UniProtKB/Swiss-Prot",
        "external_db_release": None
    }

    actual = extract_info_from_description_column(gene, gene_name_info)
    assert actual == expected
