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

# Sorting logic shamelessly stolen from:
# https://github.com/Ensembl/ensembl-dauphin-style-compiler/blob/master/backend-server/app/data/v16/gene/transcriptorder.py

# from tests.dummy_transcripts_sample import dummy_transcripts_sample

def _transcript_value(transcript):
    """Return a sortable tuple representing the priority of a transcript.

    This function assigns a multi-level score to a transcript based on:
      1. Transcript designation (e.g., MANE select, canonical)
      2. Transcript biotype (e.g., protein coding, NMD)
      3. Translation length
      4. Transcript genomic length (sum of block sizes)

    The returned tuple is later used as the sorting key to determine which
    transcript within a gene should appear first.

    Args:
        transcript: A dictionary representing a transcript

    Returns:
        tuple: A tuple of the form
            (designation_value, biotype_value, translation_length, transcript_length)
        Higher values correspond to higher transcript priority.
    """
    # --- Transcript designation scoring ---
    # Priority:
    #   2 = MANE Select or Canonical
    #   1 = Other MANE designations
    #   0 = No special designation
    transcript_metadata = transcript.get("metadata", {})
    # print(transcript_metadata)
    is_canonical = "canonical" in transcript_metadata
    mane_meta = transcript_metadata.get("mane", {})
    is_mane_select = (
            isinstance(mane_meta, dict)
            and mane_meta.get("value", "").lower() == "select"
    )

    if is_canonical or is_mane_select:
        designation_value = 2
    elif any(key.startswith("mane") for key in transcript_metadata):
        designation_value = 1
    else:
        designation_value = 0

    # --- Transcript biotype scoring ---
    # Priority order:
    #   5 = protein_coding
    #   4 = nonsense_mediated_decay
    #   3 = non_stop_decay
    #   2 = immunoglobulin transcripts (IG_*)
    #   1 = polymorphic pseudogenes
    #   0 = all others
    biotype = transcript_metadata.get("biotype").get("value") # the value here is the actual string confusing, I know...
    if biotype == "protein_coding":
        biotype_value = 5
    elif biotype == "nonsense_mediated_decay":
        biotype_value = 4
    elif biotype == "non_stop_decay":
        biotype_value = 3
    elif biotype.startswith("IG_"):
        biotype_value = 2
    elif biotype == "polymorphic_pseudogene":
        biotype_value = 1
    else:
        biotype_value = 0

    # Translation length contributes to priority, favoring longer translations.
    if transcript.get("product_generating_contexts") and transcript.get("product_generating_contexts")[0].get('cds'):
        # TODO: Check how to properly calculate protein length (no [0]?)
        translation_length = transcript.get("product_generating_contexts")[0].get('cds').get('protein_length')
    else:
        translation_length = 0

    # Transcript length
    transcript_length = transcript.get("relative_location").get("length")

    return (
        designation_value,
        biotype_value,
        int(translation_length),
        transcript_length,
    )


def sort_gene_transcripts(transcripts):
    """Sort transcripts of a single gene by transcript priority.

    This function sorts a list of transcript dictionaries using one of two
    strategies:

    1. If the transcripts contain a ``display_rank`` field, then this field
       overrides all other logic and transcripts are sorted in descending
       order of ``display_rank``. This allows external or precomputed ranking
       to take full priority.

    2. Otherwise, transcripts are sorted using the internal scoring function
       ``_transcript_value``, which ranks transcripts based on biological
       criteria (designation, biotype, translation length, etc.).

    Args:
        transcripts (list of dict): A non-empty list of transcript dictionaries.

    Returns:
        list of dict: The transcripts sorted according to either ``display_rank``
        or biological priority.
    """
    if 'display_rank' in transcripts[0]:
    # Or we can check if EVERY transcript has a display_rank, use that ordering
    # if all('display_rank' in tr for tr in transcripts):
        return sorted(transcripts, key=lambda x: x['display_rank'], reverse=True)

    return sorted(transcripts, key=_transcript_value, reverse=True)


# sorted_transcripts = sort_gene_transcripts(transcripts_sample_mapk10)
# print([tr["symbol"] for tr in sorted_transcripts])
# print(sorted_transcripts)

# ---

def generate_transcript_score_report(transcripts):
    """
    Generate a formatted report of transcript scores.
    For presentation/debugging purposes only.
    """
    report = []

    for transcript in transcripts:
        stable_id = transcript.get("stable_id", "")
        symbol = transcript.get("symbol", "Unknown")

        # Get the score using your original function
        scores = _transcript_value(transcript)

        report.append({
            "stable_id": stable_id,
            "symbol": symbol,
            "designation_score": scores[0],
            "biotype_score": scores[1],
            "translation_length": scores[2],
            "transcript_length": scores[3],
            "total_tuple": scores
        })

    return report

def main():
    # Generate and display report
    report = generate_transcript_score_report("dummy_transcripts_sample")

    # Show sorted order
    print("\n" + "=" * 85)
    print("SORTED ORDER (highest to lowest):")
    print("=" * 85)
    sorted_report = sorted(report, key=lambda x: x['total_tuple'], reverse=True)
    for i, item in enumerate(sorted_report, 1):
        print(f"{i:2}. {item['stable_id']:<20} {item['symbol']:<30} "
              f"Score: {item['total_tuple']}")


if __name__ == "__main__":
    main()
