"""The full pipeline must not abort on a corpus it finds awkward.

A run is three or more hours on a long-document corpus, and a crash in M6
throws away M1-M5 as well: nothing is written until every module has finished.
That happened for real -- `histogram` raised "Too many bins for data range" on
values equal to within float rounding, and the ValueError propagated out of
`run()`.

Unit tests did not catch it because the input was unremarkable; it was the
*combination* of a small corpus and a degenerate feature distribution. So this
file runs the whole six-module pipeline over corpora chosen to be awkward in
different ways, and asserts two things each time: it completes, and the
metrics.json it wrote is valid strict JSON -- no bare Infinity or NaN literals,
which `json.dumps` emits by default and strict parsers reject.

Offline backends throughout (hashing embedder, lexical scorer), so this costs
seconds and downloads nothing.
"""

from __future__ import annotations

import json

import pytest
import yaml

from profiler.config import load_config
from profiler.run import run

_LONG_SENTENCE = "word " * 1200

CORPORA: dict[str, list[dict]] = {
    # Targets that segment to fewer sentences than any formula wants.
    "single_word_targets": [
        {"source": "The cat sat on the mat. It was warm there.", "target": "Cat."}
    ] * 4,
    # Zero change: every delta is exactly 0, every feature has zero variance.
    "identical_source_and_target": [
        {"source": "The cat sat on the mat. It was warm.",
         "target": "The cat sat on the mat. It was warm."}
    ] * 4,
    # One sentence long enough to have overflowed a recursive tree walk.
    "one_huge_sentence": [
        {"source": _LONG_SENTENCE + ".", "target": "Short summary here."}
    ] * 3,
    # The minimum corpus a bootstrap can be asked for.
    "two_pairs_only": [
        {"source": "Alpha beta gamma delta. Epsilon zeta.", "target": "Alpha beta."},
        {"source": "Eta theta iota kappa. Lambda mu nu.", "target": "Eta theta."},
    ],
    "unicode_heavy": [
        {"source": "Café naïve résumé. 100 µg/mL at 37°C. Ürün çok iyi.",
         "target": "Café résumé. 100 µg/mL."}
    ] * 4,
    # No terminators at all: one "sentence" by any segmenter.
    "no_punctuation": [
        {"source": "the cat sat on the mat it was warm there and quiet",
         "target": "cat sat"}
    ] * 4,
    # Decimals, which the textstat normalisation exists to protect.
    "numbers_only": [
        {"source": "1.0 2.0 3.0. 4.0 5.0 6.0. 7.0 8.0.", "target": "1.0 2.0."}
    ] * 4,
    # Expansion rather than compression, which inverts every ratio's direction.
    "target_longer_than_source": [
        {"source": "Short.",
         "target": "A much longer target with many more words than the source has."}
    ] * 4,
}


def _strict_load(text: str):
    """json.loads that refuses Infinity/NaN, which json.dumps emits by default."""

    def reject(constant):
        raise ValueError(f"non-finite literal in metrics.json: {constant}")

    return json.loads(text, parse_constant=reject)


@pytest.mark.parametrize("name", sorted(CORPORA))
def test_pipeline_completes_on_an_awkward_corpus(name, tmp_path):
    rows = CORPORA[name]
    corpus = tmp_path / f"{name}.jsonl"
    with corpus.open("w", encoding="utf-8") as fh:
        for i, r in enumerate(rows):
            fh.write(json.dumps({"id": f"{name}{i}", **r}) + "\n")

    cfg_path = tmp_path / f"{name}.yaml"
    cfg_path.write_text(
        yaml.safe_dump(
            {
                "dataset": {
                    "adapter": "jsonl",
                    "path": str(corpus),
                    "source_field": "source",
                    "target_field": "target",
                },
                "run": {
                    "language": "en",
                    "sample_size": 10,
                    "embedder": "hashing",
                    "nli_backend": "lexical",
                    "bootstrap_resamples": 30,
                    "cache_dir": str(tmp_path / "cache"),
                    "dataset_label": name,
                    "tau_sweep": [0.4, 0.5],
                    "m6_tau": 0.4,
                },
                "modules": [
                    "length",
                    "abstractiveness",
                    "readability",
                    "alignment",
                    "elaboration",
                    "deletion_profile",
                ],
            }
        )
    )

    out = run(load_config(cfg_path), output_dir=tmp_path / f"out_{name}")

    metrics = _strict_load((out / "metrics.json").read_text())
    assert metrics["n_full"] == len(rows)
    # Every requested module must have produced a section, not been skipped.
    assert set(metrics["modules"]) == {
        "length", "abstractiveness", "readability",
        "alignment", "elaboration", "deletion_profile",
    }
    assert (out / "report.md").exists()


def test_a_degenerate_feature_distribution_does_not_abort_m6(tmp_path):
    """The specific shape that aborted a real run.

    M6's centroid_sim came back with min 0.4999999999999999 and max
    0.5000000000000001 -- a positive range 2.2e-16 wide, which numpy cannot
    divide into 20 finite bins. Identical pairs reproduce that class of input.
    """
    from profiler.stats import histogram

    h = histogram([0.5, 0.4999999999999999, 0.5000000000000001], bins=20)
    assert sum(h["counts"]) == h["n"] == 3
    assert _strict_load(json.dumps(h))
