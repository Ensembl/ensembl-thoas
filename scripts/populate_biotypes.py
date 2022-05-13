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


def create_transcript_biotypes(input_tsv, feature_type="transcript"):
    biotype_valuesets = {}
    with open(input_tsv) as handle:
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
    # Coalesce legacy biotypes
    for biotype in LNCRNA_LEGACY_TYPES:
        if feature_type == "transcript":
            biotype_valuesets[biotype] = biotype_valuesets['lncrna']
        elif feature_type == "gene":
            biotype_valuesets[biotype] = biotype_valuesets['lncrna_gene']
    with open(feature_type + "_biotype.json", "w+") as handle:
        json.dump(biotype_valuesets, handle, indent=4)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Script for populating biotypes from https://docs.google.com/spreadsheets/d/1dwMV8xiIPKZrThdV5V1cPBusciEufFdq1PBBFRL05Lw/edit#gid=888403877")
    parser.add_argument('--input_tsv', help="File containing biotype info from the google doc")
    parser.add_argument('--feature_type', help="Either gene or transcript")
    args = parser.parse_args()
    create_transcript_biotypes(args.input_tsv, args.feature_type)
