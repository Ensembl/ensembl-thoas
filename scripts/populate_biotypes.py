'''
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
'''


import argparse
import csv
import json

# These are legacy biotypes that have been coalesced into 'lncrna'
LNCRNA_LEGACY_TYPES = ["3prime_overlapping_ncrna", "antisense", "bidirectional_promoter_lncrna", "lincrna",
     "macro_lncrna", "non_coding", "processed_transcript", "sense_intronic", "sense_overlapping"]

# The Perl API returns the values of this dict, while the google doc uses the keys
TRANSCRIPT_NAME_MAPPING = {
    'scrna_gene': 'scrna',
    'scarna_gene': 'scarna',
    'vault_rna_gene': 'vault_rna',
    'rrna_gene': 'rrna',
    'ribozyme_gene': 'ribozyme',
}


def create_biotypes(input_tsv, feature_type="transcript"):
    biotype_valuesets = {}
    with open(input_tsv, encoding='UTF-8') as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        for row in reader:
            biotype_description = row["description (longer description that can contain nuances)"]
            biotype_description_nullable = None if biotype_description == "" else biotype_description
            biotype_valuesets[row["value"]] = {"value": row["value"],
                                               "label": row["label"],
                                               "accession_id": row["Accession ID (Unique within Ensembl)"],
                                               "definition": row["definition of term (succinct - as few words as possible. )"],
                                               "description": biotype_description_nullable,
                                               }
            # Duplicate the biotype for values which are different for the Google doc and Perl API
            if feature_type == "transcript" and row['value'] in TRANSCRIPT_NAME_MAPPING:
                biotype_valuesets[TRANSCRIPT_NAME_MAPPING[row["value"]]] = biotype_valuesets[row['value']]
    # Duplicate valuesets for legacy biotypes which have been coalesced into 'lncrna'
    for biotype in LNCRNA_LEGACY_TYPES:
        if feature_type == "transcript":
            biotype_valuesets[biotype] = biotype_valuesets['lncrna']
        elif feature_type == "gene":
            biotype_valuesets[biotype] = biotype_valuesets['lncrna_gene']
    with open(feature_type + "_biotype.json", "w+", encoding='UTF-8') as handle:
        json.dump(biotype_valuesets, handle, indent=4)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Script for populating biotypes from https://docs.google.com/spreadsheets/d/1dwMV8xiIPKZrThdV5V1cPBusciEufFdq1PBBFRL05Lw/edit#gid=888403877")
    parser.add_argument('--input_tsv', help="File containing biotype info from the google doc")
    parser.add_argument('--feature_type', help="Either gene or transcript")
    args = parser.parse_args()
    create_transcript_biotypes(args.input_tsv, args.feature_type)
