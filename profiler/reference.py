"""Literature reference values (PRD s5) and interpretation guide (PRD s6).

These are reported values from the source papers, embedded verbatim so measured
numbers can be read against published corpora. They are NOT pipeline output.
"""

from __future__ import annotations

# Columns: corpus, task_as_labelled, compression, readability_delta
LITERATURE_TABLE = [
    ("XSum (Narayan et al. 2018)", "SUM", "0.054 (431 → 23.3 w)", "n/a"),
    ("CNN/DailyMail", "SUM", "≈0.08 (~700 → ~53 w)", "n/a"),
    # Cohan et al. report lengths, not a ratio; 0.067 is 203/3016 from their
    # Table 1, derived the same way as the CNN/DailyMail row above.
    ("PubMed (Cohan et al. 2018)", "SUM", "0.067 (3016 → 203 w)", "none (technical target)"),
    ("D-Wikipedia (Sun et al. 2021)", "DS", "0.55 (141.8 → 78.6 w)", "—"),
    ("SWiPE (Laban et al. 2023)", "DS", "≈1 (content-preserving)", "—"),
    (
        "PLOS (Goldsack et al. 2022)",
        "PLS",
        "0.033 (5366.7 → 175.6 w)",
        "FKGL 15.04→14.76; DCRS 11.06→10.91; CLI 16.39→15.90",
    ),
    (
        "eLife (Goldsack et al. 2022)",
        "PLS",
        "0.045 (7806.1 → 347.6 w)",
        "FKGL 15.57→10.92; DCRS 11.78→8.83; CLI 17.68→12.51",
    ),
    ("Cochrane (Devaraj et al. 2021)", "PLS", "0.53 (501 → 264 tok)", "FKGL 14.4→12.9"),
    # Basu et al. report the pair count (1,979) but no corpus-level compression
    # or readability delta, so both stay unfilled rather than invented.
    ("Med-EASi (Basu et al. 2023)", "DS", "—", "—"),
    ("PLABA (Attal et al. 2023)", "PLS / adaptation", "≥1 (expands)", "FKGL significantly lower"),
]

LITERATURE_ANCHORS = (
    "CELLS (Guo et al. 2022) found 62.8% of background-explanation pairs contain "
    "information not present in the source; XSum reports 36% novel unigrams."
)

# Columns: axis, metric_to_read, high_value, low_value
INTERPRETATION_GUIDE = [
    (
        "Deletion volume",
        "M1 compression_ratio",
        "high ratio → content-preserving rewriting",
        "low ratio → heavy content selection",
    ),
    (
        "Deletion basis",
        "M6 effect sizes",
        "salience features dominate → summarization-like selection",
        "difficulty/redundancy dominate → simplification-style adequacy",
    ),
    (
        "Readability change",
        "M3c share_attributable_corpus",
        "genuine rewriting for an audience",
        "apparent readability gain is a length artifact",
    ),
    (
        "Content preservation",
        "M4 source_coverage",
        "most source content survives",
        "selective retention",
    ),
    (
        "Content addition",
        "M5 not-entailed rate + manual sample",
        "elaboration present",
        "no added background",
    ),
    (
        "Rewriting depth",
        "M2 density, novel n-grams",
        "abstractive rewriting",
        "copying",
    ),
]

INTERPRETATION_NOTE = (
    "These axes are independent: a corpus can compress heavily *and* simplify "
    "genuinely *and* elaborate, and nothing in the metrics forces it into one of "
    "three boxes."
)
