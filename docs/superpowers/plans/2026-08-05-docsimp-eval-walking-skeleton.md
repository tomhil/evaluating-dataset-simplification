# docsimp-eval Walking Skeleton Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A runnable `docsimp-eval` that loads document-pair datasets, computes the family A metrics, and writes a Markdown comparison report with flagged example pairs.

**Architecture:** A dataset is a sequence of `DocumentPair` objects produced by a loader. A metric is an object that consumes that sequence and returns a `MetricResult` holding per-pair values plus a corpus summary. The runner applies every requested metric to every dataset; the reporter arranges the results into per-family tables and selects outlier pairs for display. Metrics never see each other, and nothing in the pipeline assigns a score.

**Tech Stack:** Python 3.11+, uv, pytest, pydantic (config validation), PyYAML, textstat (readability), spaCy (sentence splitting and parsing), matplotlib (distribution plots), `datasets` (HF Hub loaders).

## Global Constraints

- Python 3.11 or newer; dependencies managed by uv via `pyproject.toml`.
- Package name `docsimp_eval`, CLI entry point `docsimp-eval`.
- **No scores.** No function may return a normalized "quality" value, a family score, or a composite. Metrics return measured quantities only.
- **No thresholds for judgement.** Outliers are defined relative to a dataset's own distribution, never against a fixed constant.
- Compression ratio carries no preferred direction.
- English only; no LLM calls; metrics must be deterministic.
- Tests never hit the network and never require a real corpus — they run against committed fixtures.
- Licence: MIT.
- When a task says "append to" a file, put any new imports in that file's existing import block at the top — not at the point of use, where the snippet shows them.

---

## File Structure

| File | Responsibility |
|---|---|
| `pyproject.toml` | Package metadata, deps, CLI entry point |
| `src/docsimp_eval/schema.py` | `DocumentPair`, `MetricResult` — the two types everything else speaks |
| `src/docsimp_eval/loaders/__init__.py` | Loader registry, `get_loader(name)` |
| `src/docsimp_eval/loaders/jsonl.py` | Load document pairs from a JSONL file |
| `src/docsimp_eval/loaders/eurlex_sum.py` | EUR-Lex-Sum (English) via HF Hub |
| `src/docsimp_eval/metrics/base.py` | `Metric` protocol, metric registry |
| `src/docsimp_eval/metrics/family_a.py` | Compression, readability, lexical, syntactic metrics |
| `src/docsimp_eval/context.py` | Descriptive context (unscored corpus facts) |
| `src/docsimp_eval/ranking.py` | Rank datasets within a metric row |
| `src/docsimp_eval/flagging.py` | Select distribution-tail pairs, build excerpts |
| `src/docsimp_eval/plots.py` | Per-metric distribution figures |
| `src/docsimp_eval/report.py` | Assemble the Markdown report |
| `src/docsimp_eval/config.py` | YAML run configuration |
| `src/docsimp_eval/runner.py` | Apply metrics to datasets |
| `src/docsimp_eval/cli.py` | `run` and `fetch` commands |

---

### Task 1: Project scaffolding, schema, and JSONL loader

**Files:**
- Create: `pyproject.toml`, `src/docsimp_eval/__init__.py`, `src/docsimp_eval/schema.py`, `src/docsimp_eval/loaders/__init__.py`, `src/docsimp_eval/loaders/jsonl.py`
- Create: `tests/fixtures/mini.jsonl`, `tests/test_jsonl_loader.py`

**Interfaces:**
- Consumes: nothing
- Produces: `DocumentPair(id: str, source: str, target: str, source_level: str | None, target_level: str | None, domain: str | None)`; `load_jsonl(path: Path) -> list[DocumentPair]`; `get_loader(name: str) -> Callable[..., list[DocumentPair]]`

- [ ] **Step 1: Create the package manifest**

`pyproject.toml`:

```toml
[project]
name = "docsimp-eval"
version = "0.1.0"
description = "Profile datasets for fitness for document-level text simplification"
requires-python = ">=3.11"
dependencies = [
    "pydantic>=2.7",
    "pyyaml>=6.0",
    "textstat>=0.7.3",
    "spacy>=3.7",
    "matplotlib>=3.8",
    "datasets>=2.19",
]

[project.scripts]
docsimp-eval = "docsimp_eval.cli:main"

[project.optional-dependencies]
dev = ["pytest>=8.0"]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/docsimp_eval"]

[tool.pytest.ini_options]
testpaths = ["tests"]
```

- [ ] **Step 2: Create the test fixture**

`tests/fixtures/mini.jsonl` (three pairs; the third is deliberately near-identical so later tasks have an outlier to find):

```
{"id": "p1", "source": "The committee promulgated a comprehensive regulatory framework. It subsequently entered into force.", "target": "The committee made new rules. The rules then started."}
{"id": "p2", "source": "Notwithstanding the aforementioned provisions, member states retain discretion.", "target": "Even so, member states can still decide for themselves."}
{"id": "p3", "source": "This sentence is unchanged.", "target": "This sentence is unchanged."}
```

- [ ] **Step 3: Write the failing test**

`tests/test_jsonl_loader.py`:

```python
from pathlib import Path

import pytest

from docsimp_eval.loaders.jsonl import load_jsonl

FIXTURE = Path(__file__).parent / "fixtures" / "mini.jsonl"


def test_loads_all_pairs():
    pairs = load_jsonl(FIXTURE)
    assert len(pairs) == 3
    assert pairs[0].id == "p1"
    assert pairs[0].source.startswith("The committee promulgated")
    assert pairs[0].target.startswith("The committee made new rules")


def test_optional_fields_default_to_none():
    pairs = load_jsonl(FIXTURE)
    assert pairs[0].source_level is None
    assert pairs[0].domain is None


def test_missing_required_field_names_the_line():
    bad = FIXTURE.parent / "bad.jsonl"
    bad.write_text('{"id": "x", "source": "only source"}\n', encoding="utf-8")
    try:
        with pytest.raises(ValueError, match="line 1"):
            load_jsonl(bad)
    finally:
        bad.unlink()
```

- [ ] **Step 4: Run the test to verify it fails**

Run: `uv run pytest tests/test_jsonl_loader.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'docsimp_eval'`

- [ ] **Step 5: Write the schema**

`src/docsimp_eval/schema.py`:

```python
"""The two types every component in the pipeline speaks."""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class DocumentPair:
    """One source document and its simplified counterpart."""

    id: str
    source: str
    target: str
    source_level: str | None = None
    target_level: str | None = None
    domain: str | None = None


@dataclass(frozen=True)
class MetricResult:
    """Measured values for one metric over one dataset.

    Deliberately carries no notion of a good value. `direction` records
    only whether the quantity has a conventional reading, and is used for
    ordering the display -- never for grading.
    """

    metric: str
    family: str
    label: str
    summary: float
    per_pair: dict[str, float] = field(default_factory=dict)
    direction: str | None = None  # "higher", "lower", or None for no direction
```

`src/docsimp_eval/__init__.py`:

```python
from docsimp_eval.schema import DocumentPair, MetricResult

__all__ = ["DocumentPair", "MetricResult"]
```

- [ ] **Step 6: Write the JSONL loader**

`src/docsimp_eval/loaders/jsonl.py`:

```python
import json
from pathlib import Path

from docsimp_eval.schema import DocumentPair

OPTIONAL_FIELDS = ("source_level", "target_level", "domain")


def load_jsonl(path: Path) -> list[DocumentPair]:
    """Load document pairs from a JSONL file, one object per line."""
    pairs: list[DocumentPair] = []
    with Path(path).open(encoding="utf-8") as handle:
        for lineno, line in enumerate(handle, start=1):
            line = line.strip()
            if not line:
                continue
            record = json.loads(line)
            missing = {"id", "source", "target"} - record.keys()
            if missing:
                raise ValueError(
                    f"{path}: line {lineno} is missing {sorted(missing)}"
                )
            pairs.append(
                DocumentPair(
                    id=str(record["id"]),
                    source=record["source"],
                    target=record["target"],
                    **{f: record.get(f) for f in OPTIONAL_FIELDS},
                )
            )
    return pairs
```

`src/docsimp_eval/loaders/__init__.py`:

```python
from collections.abc import Callable

from docsimp_eval.loaders.jsonl import load_jsonl

_LOADERS: dict[str, Callable[..., list]] = {"jsonl": load_jsonl}


def get_loader(name: str) -> Callable[..., list]:
    if name not in _LOADERS:
        raise KeyError(f"unknown loader {name!r}; available: {sorted(_LOADERS)}")
    return _LOADERS[name]


def register_loader(name: str, loader: Callable[..., list]) -> None:
    _LOADERS[name] = loader


__all__ = ["get_loader", "register_loader", "load_jsonl"]
```

- [ ] **Step 7: Run the tests to verify they pass**

Run: `uv sync --extra dev && uv run pytest tests/test_jsonl_loader.py -v`
Expected: 3 passed

- [ ] **Step 8: Commit**

```bash
git add pyproject.toml src/docsimp_eval tests/
git commit -m "feat: add document-pair schema and JSONL loader"
```

---

### Task 2: Metric protocol, registry, and compression ratio

**Files:**
- Create: `src/docsimp_eval/metrics/__init__.py`, `src/docsimp_eval/metrics/base.py`, `src/docsimp_eval/metrics/family_a.py`
- Create: `tests/test_family_a_compression.py`

**Interfaces:**
- Consumes: `DocumentPair`, `MetricResult` from Task 1
- Produces: `Metric` protocol with `name: str`, `family: str`, `label: str`, `direction: str | None`, `compute(pairs: Sequence[DocumentPair]) -> MetricResult`; `metrics_for_families(families: Sequence[str]) -> list[Metric]`; `CompressionRatio`

- [ ] **Step 1: Write the failing test**

`tests/test_family_a_compression.py`:

```python
from docsimp_eval.metrics.family_a import CompressionRatio
from docsimp_eval.schema import DocumentPair

PAIRS = [
    DocumentPair(id="half", source="a b c d", target="a b"),
    DocumentPair(id="same", source="a b", target="a b"),
]


def test_ratio_is_target_over_source_in_words():
    result = CompressionRatio().compute(PAIRS)
    assert result.per_pair["half"] == 0.5
    assert result.per_pair["same"] == 1.0


def test_summary_is_the_mean():
    assert CompressionRatio().compute(PAIRS).summary == 0.75


def test_compression_declares_no_preferred_direction():
    assert CompressionRatio().direction is None


def test_empty_source_yields_zero_not_a_crash():
    result = CompressionRatio().compute([DocumentPair(id="e", source="", target="x")])
    assert result.per_pair["e"] == 0.0
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `uv run pytest tests/test_family_a_compression.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'docsimp_eval.metrics'`

- [ ] **Step 3: Write the metric protocol and registry**

`src/docsimp_eval/metrics/base.py`:

```python
from collections.abc import Sequence
from typing import Protocol, runtime_checkable

from docsimp_eval.schema import DocumentPair, MetricResult


@runtime_checkable
class Metric(Protocol):
    name: str
    family: str
    label: str
    direction: str | None

    def compute(self, pairs: Sequence[DocumentPair]) -> MetricResult: ...


_REGISTRY: dict[str, list[Metric]] = {}


def register(metric: Metric) -> Metric:
    _REGISTRY.setdefault(metric.family, []).append(metric)
    return metric


def metrics_for_families(families: Sequence[str]) -> list[Metric]:
    selected: list[Metric] = []
    for family in families:
        if family not in _REGISTRY:
            raise KeyError(
                f"no metrics registered for family {family!r}; "
                f"available: {sorted(_REGISTRY)}"
            )
        selected.extend(_REGISTRY[family])
    return selected


def mean(values: Sequence[float]) -> float:
    return sum(values) / len(values) if values else 0.0
```

- [ ] **Step 4: Write the compression metric**

`src/docsimp_eval/metrics/family_a.py`:

```python
"""Family A -- did simplification actually happen?"""

from collections.abc import Sequence

from docsimp_eval.metrics.base import mean, register
from docsimp_eval.schema import DocumentPair, MetricResult


class CompressionRatio:
    """Target length over source length, in words.

    Carries no direction: whether heavy compression is desirable depends on
    where the reader draws the line between simplification and summarization.
    """

    name = "compression_ratio"
    family = "A"
    label = "Compression ratio (target/source words)"
    direction = None

    def compute(self, pairs: Sequence[DocumentPair]) -> MetricResult:
        per_pair = {}
        for pair in pairs:
            source_words = len(pair.source.split())
            per_pair[pair.id] = (
                len(pair.target.split()) / source_words if source_words else 0.0
            )
        return MetricResult(
            metric=self.name,
            family=self.family,
            label=self.label,
            summary=mean(list(per_pair.values())),
            per_pair=per_pair,
            direction=self.direction,
        )


register(CompressionRatio())
```

`src/docsimp_eval/metrics/__init__.py`:

```python
from docsimp_eval.metrics import family_a  # noqa: F401  (registers metrics)
from docsimp_eval.metrics.base import Metric, metrics_for_families

__all__ = ["Metric", "metrics_for_families"]
```

- [ ] **Step 5: Run the tests to verify they pass**

Run: `uv run pytest tests/test_family_a_compression.py -v`
Expected: 4 passed

- [ ] **Step 6: Commit**

```bash
git add src/docsimp_eval/metrics tests/test_family_a_compression.py
git commit -m "feat: add metric protocol, registry, and compression ratio"
```

---

### Task 3: Readability delta

**Files:**
- Modify: `src/docsimp_eval/metrics/family_a.py`
- Create: `tests/test_family_a_readability.py`

**Interfaces:**
- Consumes: `register`, `mean`, `MetricResult` from Task 2
- Produces: `ReadabilityDelta` (metric name `readability_delta`)

- [ ] **Step 1: Write the failing test**

`tests/test_family_a_readability.py`:

```python
from docsimp_eval.metrics.family_a import ReadabilityDelta
from docsimp_eval.schema import DocumentPair

SIMPLIFIED = DocumentPair(
    id="simplified",
    source=(
        "The promulgation of comprehensive regulatory frameworks necessitates "
        "extensive interdepartmental consultation prior to implementation."
    ),
    target="The team asked other teams first. Then they made the rules.",
)
UNCHANGED = DocumentPair(id="unchanged", source="The cat sat.", target="The cat sat.")


def test_delta_is_negative_when_target_is_easier():
    result = ReadabilityDelta().compute([SIMPLIFIED])
    assert result.per_pair["simplified"] < 0


def test_delta_is_zero_for_identical_text():
    result = ReadabilityDelta().compute([UNCHANGED])
    assert result.per_pair["unchanged"] == 0.0


def test_lower_is_the_declared_direction():
    assert ReadabilityDelta().direction == "lower"
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `uv run pytest tests/test_family_a_readability.py -v`
Expected: FAIL — `ImportError: cannot import name 'ReadabilityDelta'`

- [ ] **Step 3: Add the metric**

Append to `src/docsimp_eval/metrics/family_a.py`:

```python
import textstat


class ReadabilityDelta:
    """Flesch-Kincaid grade level of the target minus that of the source.

    Negative means the target reads at a lower grade level. English only --
    FKGL does not transfer across languages.
    """

    name = "readability_delta"
    family = "A"
    label = "Readability delta (FKGL target - source)"
    direction = "lower"

    def compute(self, pairs: Sequence[DocumentPair]) -> MetricResult:
        per_pair = {
            pair.id: textstat.flesch_kincaid_grade(pair.target)
            - textstat.flesch_kincaid_grade(pair.source)
            for pair in pairs
        }
        return MetricResult(
            metric=self.name,
            family=self.family,
            label=self.label,
            summary=mean(list(per_pair.values())),
            per_pair=per_pair,
            direction=self.direction,
        )


register(ReadabilityDelta())
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `uv run pytest tests/test_family_a_readability.py -v`
Expected: 3 passed

- [ ] **Step 5: Commit**

```bash
git add src/docsimp_eval/metrics/family_a.py tests/test_family_a_readability.py
git commit -m "feat: add readability delta metric"
```

---

### Task 4: Lexical complexity shift

**Files:**
- Modify: `src/docsimp_eval/metrics/family_a.py`
- Create: `tests/test_family_a_lexical.py`

**Interfaces:**
- Consumes: `register`, `mean` from Task 2
- Produces: `RareWordRateShift` (metric name `rare_word_rate_shift`), `TypeTokenRatioShift` (metric name `type_token_ratio_shift`)

- [ ] **Step 1: Write the failing test**

`tests/test_family_a_lexical.py`:

```python
from docsimp_eval.metrics.family_a import RareWordRateShift, TypeTokenRatioShift
from docsimp_eval.schema import DocumentPair

PAIR = DocumentPair(
    id="p",
    source="The magistrate promulgated an ordinance.",
    target="The judge made a rule.",
)


def test_rare_word_rate_falls_when_long_words_are_replaced():
    result = RareWordRateShift().compute([PAIR])
    assert result.per_pair["p"] < 0


def test_rare_word_rate_shift_is_zero_for_identical_text():
    same = DocumentPair(id="s", source="a rule", target="a rule")
    assert RareWordRateShift().compute([same]).per_pair["s"] == 0.0


def test_type_token_ratio_handles_empty_target():
    empty = DocumentPair(id="e", source="a b c", target="")
    assert TypeTokenRatioShift().compute([empty]).per_pair["e"] == -1.0
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `uv run pytest tests/test_family_a_lexical.py -v`
Expected: FAIL — `ImportError: cannot import name 'RareWordRateShift'`

- [ ] **Step 3: Add the metrics**

Append to `src/docsimp_eval/metrics/family_a.py`:

```python
import re

WORD = re.compile(r"[A-Za-z']+")
RARE_WORD_MIN_SYLLABLES = 3


def _words(text: str) -> list[str]:
    return [match.group().lower() for match in WORD.finditer(text)]


def _rare_word_rate(text: str) -> float:
    words = _words(text)
    if not words:
        return 0.0
    rare = sum(
        1 for word in words if textstat.syllable_count(word) >= RARE_WORD_MIN_SYLLABLES
    )
    return rare / len(words)


def _type_token_ratio(text: str) -> float:
    words = _words(text)
    return len(set(words)) / len(words) if words else 0.0


class RareWordRateShift:
    """Change in the share of polysyllabic words from source to target."""

    name = "rare_word_rate_shift"
    family = "A"
    label = "Rare-word rate shift (target - source)"
    direction = "lower"

    def compute(self, pairs: Sequence[DocumentPair]) -> MetricResult:
        per_pair = {
            pair.id: _rare_word_rate(pair.target) - _rare_word_rate(pair.source)
            for pair in pairs
        }
        return MetricResult(
            metric=self.name,
            family=self.family,
            label=self.label,
            summary=mean(list(per_pair.values())),
            per_pair=per_pair,
            direction=self.direction,
        )


class TypeTokenRatioShift:
    """Change in vocabulary diversity from source to target.

    No direction: a lower ratio can mean simpler word choice or merely a
    shorter document, and the tool does not adjudicate which.
    """

    name = "type_token_ratio_shift"
    family = "A"
    label = "Type-token ratio shift (target - source)"
    direction = None

    def compute(self, pairs: Sequence[DocumentPair]) -> MetricResult:
        per_pair = {
            pair.id: _type_token_ratio(pair.target) - _type_token_ratio(pair.source)
            for pair in pairs
        }
        return MetricResult(
            metric=self.name,
            family=self.family,
            label=self.label,
            summary=mean(list(per_pair.values())),
            per_pair=per_pair,
            direction=self.direction,
        )


register(RareWordRateShift())
register(TypeTokenRatioShift())
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `uv run pytest tests/test_family_a_lexical.py -v`
Expected: 3 passed

- [ ] **Step 5: Commit**

```bash
git add src/docsimp_eval/metrics/family_a.py tests/test_family_a_lexical.py
git commit -m "feat: add lexical complexity shift metrics"
```

---

### Task 5: Syntactic simplification via spaCy

**Files:**
- Create: `src/docsimp_eval/nlp.py`
- Modify: `src/docsimp_eval/metrics/family_a.py`
- Create: `tests/test_family_a_syntax.py`

**Interfaces:**
- Consumes: `register`, `mean` from Task 2
- Produces: `get_nlp() -> spacy.Language`; `MeanSentenceLengthShift` (`mean_sentence_length_shift`), `ParseDepthShift` (`parse_depth_shift`)

- [ ] **Step 1: Write the failing test**

`tests/test_family_a_syntax.py`:

```python
from docsimp_eval.metrics.family_a import MeanSentenceLengthShift, ParseDepthShift
from docsimp_eval.schema import DocumentPair

SPLIT = DocumentPair(
    id="split",
    source="The report, which the committee approved after long debate, was published.",
    target="The committee approved the report. It was published.",
)


def test_sentence_length_falls_when_a_sentence_is_split():
    result = MeanSentenceLengthShift().compute([SPLIT])
    assert result.per_pair["split"] < 0


def test_parse_depth_falls_when_a_clause_is_unnested():
    result = ParseDepthShift().compute([SPLIT])
    assert result.per_pair["split"] < 0


def test_summary_matches_single_pair_value():
    result = ParseDepthShift().compute([SPLIT])
    assert result.summary == result.per_pair["split"]
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `uv run pytest tests/test_family_a_syntax.py -v`
Expected: FAIL — `ImportError: cannot import name 'MeanSentenceLengthShift'`

- [ ] **Step 3: Add the spaCy singleton**

`src/docsimp_eval/nlp.py`:

```python
"""Shared spaCy pipeline.

Loaded once and reused: model load dominates runtime on small corpora.
The parser is required for depth; the NER component is disabled as unused.
"""

import functools

import spacy

MODEL = "en_core_web_sm"


@functools.lru_cache(maxsize=1)
def get_nlp() -> "spacy.Language":
    try:
        return spacy.load(MODEL, disable=["ner", "lemmatizer"])
    except OSError as error:
        raise RuntimeError(
            f"spaCy model {MODEL!r} is not installed. Run:\n"
            f"    uv run python -m spacy download {MODEL}"
        ) from error
```

- [ ] **Step 4: Add the metrics**

Append to `src/docsimp_eval/metrics/family_a.py`:

```python
from docsimp_eval.nlp import get_nlp


def _token_depth(token) -> int:
    depth = 0
    while token.head is not token:
        depth += 1
        token = token.head
    return depth


def _mean_sentence_length(text: str) -> float:
    sentences = [sent for sent in get_nlp()(text).sents]
    if not sentences:
        return 0.0
    return mean([len(sent) for sent in sentences])


def _mean_parse_depth(text: str) -> float:
    depths = [
        max((_token_depth(token) for token in sent), default=0)
        for sent in get_nlp()(text).sents
    ]
    return mean(depths)


class MeanSentenceLengthShift:
    """Change in mean sentence length, in tokens."""

    name = "mean_sentence_length_shift"
    family = "A"
    label = "Mean sentence length shift (tokens, target - source)"
    direction = "lower"

    def compute(self, pairs: Sequence[DocumentPair]) -> MetricResult:
        per_pair = {
            pair.id: _mean_sentence_length(pair.target)
            - _mean_sentence_length(pair.source)
            for pair in pairs
        }
        return MetricResult(
            metric=self.name,
            family=self.family,
            label=self.label,
            summary=mean(list(per_pair.values())),
            per_pair=per_pair,
            direction=self.direction,
        )


class ParseDepthShift:
    """Change in mean maximum dependency-tree depth per sentence."""

    name = "parse_depth_shift"
    family = "A"
    label = "Parse depth shift (target - source)"
    direction = "lower"

    def compute(self, pairs: Sequence[DocumentPair]) -> MetricResult:
        per_pair = {
            pair.id: _mean_parse_depth(pair.target) - _mean_parse_depth(pair.source)
            for pair in pairs
        }
        return MetricResult(
            metric=self.name,
            family=self.family,
            label=self.label,
            summary=mean(list(per_pair.values())),
            per_pair=per_pair,
            direction=self.direction,
        )


register(MeanSentenceLengthShift())
register(ParseDepthShift())
```

- [ ] **Step 5: Install the model and run the tests**

Run: `uv run python -m spacy download en_core_web_sm && uv run pytest tests/test_family_a_syntax.py -v`
Expected: 3 passed

- [ ] **Step 6: Commit**

```bash
git add src/docsimp_eval/nlp.py src/docsimp_eval/metrics/family_a.py tests/test_family_a_syntax.py
git commit -m "feat: add syntactic simplification metrics"
```

---

### Task 6: Descriptive context

**Files:**
- Create: `src/docsimp_eval/context.py`, `tests/test_context.py`

**Interfaces:**
- Consumes: `DocumentPair` from Task 1
- Produces: `DatasetContext(n_pairs: int, median_source_words: float, median_target_words: float, domains: tuple[str, ...], target_levels: tuple[str, ...])`; `describe(pairs: Sequence[DocumentPair]) -> DatasetContext`

- [ ] **Step 1: Write the failing test**

`tests/test_context.py`:

```python
from docsimp_eval.context import describe
from docsimp_eval.schema import DocumentPair

PAIRS = [
    DocumentPair(id="a", source="one two three", target="one", domain="legal"),
    DocumentPair(id="b", source="one two three four five", target="one two", domain="legal"),
]


def test_counts_pairs():
    assert describe(PAIRS).n_pairs == 2


def test_reports_median_lengths():
    context = describe(PAIRS)
    assert context.median_source_words == 4.0
    assert context.median_target_words == 1.5


def test_collects_distinct_domains():
    assert describe(PAIRS).domains == ("legal",)


def test_empty_dataset_does_not_crash():
    context = describe([])
    assert context.n_pairs == 0
    assert context.median_source_words == 0.0
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `uv run pytest tests/test_context.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'docsimp_eval.context'`

- [ ] **Step 3: Write the module**

`src/docsimp_eval/context.py`:

```python
"""Descriptive corpus facts.

Context for reading the metrics, never a judgement of its own: a small
corpus is not an unfit corpus.
"""

import statistics
from collections.abc import Sequence
from dataclasses import dataclass

from docsimp_eval.schema import DocumentPair


@dataclass(frozen=True)
class DatasetContext:
    n_pairs: int
    median_source_words: float
    median_target_words: float
    domains: tuple[str, ...]
    target_levels: tuple[str, ...]


def _median(values: list[int]) -> float:
    return float(statistics.median(values)) if values else 0.0


def _distinct(values: Sequence[str | None]) -> tuple[str, ...]:
    return tuple(sorted({value for value in values if value is not None}))


def describe(pairs: Sequence[DocumentPair]) -> DatasetContext:
    return DatasetContext(
        n_pairs=len(pairs),
        median_source_words=_median([len(pair.source.split()) for pair in pairs]),
        median_target_words=_median([len(pair.target.split()) for pair in pairs]),
        domains=_distinct([pair.domain for pair in pairs]),
        target_levels=_distinct([pair.target_level for pair in pairs]),
    )
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `uv run pytest tests/test_context.py -v`
Expected: 4 passed

- [ ] **Step 5: Commit**

```bash
git add src/docsimp_eval/context.py tests/test_context.py
git commit -m "feat: add descriptive dataset context"
```

---

### Task 7: Ranking datasets within a metric row

**Files:**
- Create: `src/docsimp_eval/ranking.py`, `tests/test_ranking.py`

**Interfaces:**
- Consumes: nothing
- Produces: `rank(values: dict[str, float]) -> dict[str, int]` — dense ranking by descending value, ties share a rank

- [ ] **Step 1: Write the failing test**

`tests/test_ranking.py`:

```python
from docsimp_eval.ranking import rank


def test_highest_value_ranks_first():
    assert rank({"a": 0.1, "b": 0.9}) == {"a": 2, "b": 1}


def test_ties_share_a_rank():
    assert rank({"a": 0.5, "b": 0.5, "c": 0.1}) == {"a": 1, "b": 1, "c": 3}


def test_single_dataset_ranks_first():
    assert rank({"only": 0.3}) == {"only": 1}


def test_empty_input_returns_empty():
    assert rank({}) == {}
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `uv run pytest tests/test_ranking.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'docsimp_eval.ranking'`

- [ ] **Step 3: Write the module**

`src/docsimp_eval/ranking.py`:

```python
"""Order datasets within one metric row.

Ranking is presentational: it puts the extremes where the eye finds them.
Rank 1 means the largest value, not the best dataset -- several metrics
have no better direction at all.
"""


def rank(values: dict[str, float]) -> dict[str, int]:
    ordered = sorted(values.items(), key=lambda item: item[1], reverse=True)
    ranks: dict[str, int] = {}
    previous_value: float | None = None
    previous_rank = 0
    for position, (name, value) in enumerate(ordered, start=1):
        if previous_value is not None and value == previous_value:
            ranks[name] = previous_rank
        else:
            ranks[name] = position
            previous_rank = position
            previous_value = value
    return ranks
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `uv run pytest tests/test_ranking.py -v`
Expected: 4 passed

- [ ] **Step 5: Commit**

```bash
git add src/docsimp_eval/ranking.py tests/test_ranking.py
git commit -m "feat: rank datasets within a metric row"
```

---

### Task 8: Flagging distribution-tail pairs

**Files:**
- Create: `src/docsimp_eval/flagging.py`, `tests/test_flagging.py`

**Interfaces:**
- Consumes: `DocumentPair` (Task 1), `MetricResult` (Task 1)
- Produces: `FlaggedPair(pair_id: str, value: float, tail: str, source_excerpt: str, target_excerpt: str)`; `flag_outliers(result: MetricResult, pairs: Sequence[DocumentPair], k: int, excerpt_chars: int) -> list[FlaggedPair]`

- [ ] **Step 1: Write the failing test**

`tests/test_flagging.py`:

```python
from docsimp_eval.flagging import flag_outliers
from docsimp_eval.schema import DocumentPair, MetricResult

PAIRS = [DocumentPair(id=str(i), source="s" * 50, target="t" * 50) for i in range(5)]
RESULT = MetricResult(
    metric="m",
    family="A",
    label="M",
    summary=0.3,
    per_pair={"0": 0.0, "1": 0.2, "2": 0.3, "3": 0.4, "4": 1.0},
)


def test_returns_both_tails():
    flagged = flag_outliers(RESULT, PAIRS, k=1, excerpt_chars=10)
    tails = {f.tail for f in flagged}
    assert tails == {"low", "high"}


def test_picks_the_most_extreme_values():
    flagged = flag_outliers(RESULT, PAIRS, k=1, excerpt_chars=10)
    by_tail = {f.tail: f.pair_id for f in flagged}
    assert by_tail["low"] == "0"
    assert by_tail["high"] == "4"


def test_excerpts_are_truncated_with_an_ellipsis():
    flagged = flag_outliers(RESULT, PAIRS, k=1, excerpt_chars=10)
    assert flagged[0].source_excerpt.endswith("…")
    assert len(flagged[0].source_excerpt) == 11


def test_no_pair_is_flagged_in_both_tails():
    flagged = flag_outliers(RESULT, PAIRS, k=5, excerpt_chars=10)
    assert len({f.pair_id for f in flagged}) == len(flagged)
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `uv run pytest tests/test_flagging.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'docsimp_eval.flagging'`

- [ ] **Step 3: Write the module**

`src/docsimp_eval/flagging.py`:

```python
"""Select the pairs sitting at the extremes of a metric's distribution.

Outliers are defined against the corpus itself, never against a fixed
threshold -- the tool has no opinion about what a good value would be.
"""

from collections.abc import Sequence
from dataclasses import dataclass

from docsimp_eval.schema import DocumentPair, MetricResult


@dataclass(frozen=True)
class FlaggedPair:
    pair_id: str
    value: float
    tail: str  # "low" or "high"
    source_excerpt: str
    target_excerpt: str


def _excerpt(text: str, limit: int) -> str:
    collapsed = " ".join(text.split())
    if len(collapsed) <= limit:
        return collapsed
    return collapsed[:limit] + "…"


def flag_outliers(
    result: MetricResult,
    pairs: Sequence[DocumentPair],
    k: int,
    excerpt_chars: int,
) -> list[FlaggedPair]:
    if not result.per_pair:
        return []
    by_id = {pair.id: pair for pair in pairs}
    ordered = sorted(result.per_pair.items(), key=lambda item: item[1])
    take = min(k, len(ordered) // 2 or 1)
    selected = [(pid, value, "low") for pid, value in ordered[:take]]
    seen = {pid for pid, _, _ in selected}
    for pid, value in reversed(ordered[-take:]):
        if pid not in seen:
            selected.append((pid, value, "high"))
    return [
        FlaggedPair(
            pair_id=pid,
            value=value,
            tail=tail,
            source_excerpt=_excerpt(by_id[pid].source, excerpt_chars),
            target_excerpt=_excerpt(by_id[pid].target, excerpt_chars),
        )
        for pid, value, tail in selected
        if pid in by_id
    ]
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `uv run pytest tests/test_flagging.py -v`
Expected: 4 passed

- [ ] **Step 5: Commit**

```bash
git add src/docsimp_eval/flagging.py tests/test_flagging.py
git commit -m "feat: flag distribution-tail pairs per metric"
```

---

### Task 9: Runner

**Files:**
- Create: `src/docsimp_eval/runner.py`, `tests/test_runner.py`

**Interfaces:**
- Consumes: `Metric`, `metrics_for_families` (Task 2), `describe`/`DatasetContext` (Task 6), `DocumentPair` (Task 1)
- Produces: `DatasetRun(name: str, pairs: list[DocumentPair], context: DatasetContext, results: dict[str, MetricResult])`; `run_metrics(datasets: dict[str, list[DocumentPair]], families: Sequence[str]) -> list[DatasetRun]`

- [ ] **Step 1: Write the failing test**

`tests/test_runner.py`:

```python
from docsimp_eval.runner import run_metrics
from docsimp_eval.schema import DocumentPair

DATASETS = {
    "alpha": [DocumentPair(id="a", source="one two three four", target="one two")],
    "beta": [DocumentPair(id="b", source="one two", target="one two")],
}


def test_produces_one_run_per_dataset():
    runs = run_metrics(DATASETS, families=["A"])
    assert [run.name for run in runs] == ["alpha", "beta"]


def test_each_run_carries_every_family_a_metric():
    runs = run_metrics(DATASETS, families=["A"])
    assert "compression_ratio" in runs[0].results
    assert "readability_delta" in runs[0].results


def test_context_is_attached():
    runs = run_metrics(DATASETS, families=["A"])
    assert runs[0].context.n_pairs == 1
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `uv run pytest tests/test_runner.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'docsimp_eval.runner'`

- [ ] **Step 3: Write the module**

`src/docsimp_eval/runner.py`:

```python
from collections.abc import Sequence
from dataclasses import dataclass

from docsimp_eval.context import DatasetContext, describe
from docsimp_eval.metrics import metrics_for_families
from docsimp_eval.schema import DocumentPair, MetricResult


@dataclass(frozen=True)
class DatasetRun:
    name: str
    pairs: list[DocumentPair]
    context: DatasetContext
    results: dict[str, MetricResult]


def run_metrics(
    datasets: dict[str, list[DocumentPair]],
    families: Sequence[str],
) -> list[DatasetRun]:
    metrics = metrics_for_families(families)
    runs = []
    for name, pairs in datasets.items():
        results = {metric.name: metric.compute(pairs) for metric in metrics}
        runs.append(
            DatasetRun(
                name=name,
                pairs=list(pairs),
                context=describe(pairs),
                results=results,
            )
        )
    return runs
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `uv run pytest tests/test_runner.py -v`
Expected: 3 passed

- [ ] **Step 5: Commit**

```bash
git add src/docsimp_eval/runner.py tests/test_runner.py
git commit -m "feat: add metric runner"
```

---

### Task 10: Markdown report

**Files:**
- Create: `src/docsimp_eval/report.py`, `tests/test_report.py`

**Interfaces:**
- Consumes: `DatasetRun` (Task 9), `rank` (Task 7), `flag_outliers`/`FlaggedPair` (Task 8)
- Produces: `render_report(runs: Sequence[DatasetRun], flagged_examples: int, excerpt_chars: int) -> str`

- [ ] **Step 1: Write the failing test**

`tests/test_report.py`:

```python
from docsimp_eval.report import render_report
from docsimp_eval.runner import run_metrics
from docsimp_eval.schema import DocumentPair

RUNS = run_metrics(
    {
        "alpha": [
            DocumentPair(id="a1", source="one two three four five six", target="one two"),
            DocumentPair(id="a2", source="same text here", target="same text here"),
        ],
        "beta": [DocumentPair(id="b1", source="one two three", target="one two three")],
    },
    families=["A"],
)


def test_report_has_a_family_a_section():
    report = render_report(RUNS, flagged_examples=1, excerpt_chars=40)
    assert "## Family A" in report


def test_every_dataset_is_a_column():
    report = render_report(RUNS, flagged_examples=1, excerpt_chars=40)
    assert "| alpha | beta |" in report


def test_metric_rows_carry_values_and_ranks():
    report = render_report(RUNS, flagged_examples=1, excerpt_chars=40)
    assert "Compression ratio" in report
    assert "(1)" in report


def test_report_states_that_no_score_is_produced():
    report = render_report(RUNS, flagged_examples=1, excerpt_chars=40)
    assert "no fitness score" in report.lower()


def test_flagged_section_shows_excerpts():
    report = render_report(RUNS, flagged_examples=1, excerpt_chars=40)
    assert "Flagged pairs" in report
    assert "a1" in report or "a2" in report
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `uv run pytest tests/test_report.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'docsimp_eval.report'`

- [ ] **Step 3: Write the module**

`src/docsimp_eval/report.py`:

```python
"""Assemble the Markdown comparison report."""

from collections.abc import Sequence

from docsimp_eval.flagging import flag_outliers
from docsimp_eval.ranking import rank
from docsimp_eval.runner import DatasetRun

PREAMBLE = (
    "This report produces **no fitness score**. Each row is a measured "
    "quantity; the parenthesised number is that dataset's rank within the "
    "row by magnitude, which marks the extremes for the eye and asserts "
    "nothing about quality. Several metrics have no better direction at all."
)


def _table(header: str, rows: list[list[str]], columns: Sequence[str]) -> list[str]:
    lines = [f"| {header} | " + " | ".join(columns) + " |"]
    lines.append("|" + "---|" * (len(columns) + 1))
    lines.extend("| " + " | ".join(row) + " |" for row in rows)
    return lines


def _context_section(runs: Sequence[DatasetRun]) -> list[str]:
    names = [run.name for run in runs]
    rows = [
        ["Documents", *[str(run.context.n_pairs) for run in runs]],
        ["Median source words", *[f"{run.context.median_source_words:.0f}" for run in runs]],
        ["Median target words", *[f"{run.context.median_target_words:.0f}" for run in runs]],
        ["Domains", *[", ".join(run.context.domains) or "—" for run in runs]],
    ]
    return ["## Descriptive context", "", *_table("", rows, names), ""]


def _family_section(runs: Sequence[DatasetRun], family: str) -> list[str]:
    names = [run.name for run in runs]
    metric_names = [
        name for name, result in runs[0].results.items() if result.family == family
    ]
    rows = []
    for metric_name in metric_names:
        values = {run.name: run.results[metric_name].summary for run in runs}
        ranks = rank(values)
        label = runs[0].results[metric_name].label
        direction = runs[0].results[metric_name].direction
        suffix = "" if direction else " *(no direction)*"
        rows.append(
            [label + suffix, *[f"{values[n]:.3f} ({ranks[n]})" for n in names]]
        )
    return [f"## Family {family}", "", *_table("Metric", rows, names), ""]


def _flagged_section(
    runs: Sequence[DatasetRun], flagged_examples: int, excerpt_chars: int
) -> list[str]:
    lines = ["## Flagged pairs", ""]
    for run in runs:
        lines.append(f"### {run.name}")
        lines.append("")
        for metric_name, result in run.results.items():
            flagged = flag_outliers(
                result, run.pairs, k=flagged_examples, excerpt_chars=excerpt_chars
            )
            if not flagged:
                continue
            lines.append(f"**{result.label}**")
            lines.append("")
            for item in flagged:
                lines.append(
                    f"- `{item.pair_id}` ({item.tail} tail, {item.value:.3f})"
                )
                lines.append(f"  - source: {item.source_excerpt}")
                lines.append(f"  - target: {item.target_excerpt}")
            lines.append("")
    return lines


def render_report(
    runs: Sequence[DatasetRun],
    flagged_examples: int,
    excerpt_chars: int,
) -> str:
    if not runs:
        return "# docsimp-eval report\n\nNo datasets were evaluated.\n"
    families = sorted({result.family for result in runs[0].results.values()})
    lines = ["# docsimp-eval report", "", PREAMBLE, ""]
    lines.extend(_context_section(runs))
    for family in families:
        lines.extend(_family_section(runs, family))
    lines.extend(_flagged_section(runs, flagged_examples, excerpt_chars))
    return "\n".join(lines) + "\n"
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `uv run pytest tests/test_report.py -v`
Expected: 5 passed

- [ ] **Step 5: Commit**

```bash
git add src/docsimp_eval/report.py tests/test_report.py
git commit -m "feat: render markdown comparison report"
```

---

### Task 11: Configuration and CLI

**Files:**
- Create: `src/docsimp_eval/config.py`, `src/docsimp_eval/cli.py`, `configs/mini.yaml`
- Create: `tests/test_config.py`, `tests/test_cli.py`

**Interfaces:**
- Consumes: `run_metrics` (Task 9), `render_report` (Task 10), `get_loader` (Task 1)
- Produces: `RunConfig`, `load_config(path: Path) -> RunConfig`, `main(argv: list[str] | None = None) -> int`

- [ ] **Step 1: Write the failing config test**

`tests/test_config.py`:

```python
from pathlib import Path

import pytest

from docsimp_eval.config import load_config

VALID = """
datasets:
  - name: mini
    loader: jsonl
    path: tests/fixtures/mini.jsonl
metrics:
  families: [A]
report:
  flagged_examples: 2
  excerpt_chars: 100
"""


def test_parses_a_valid_config(tmp_path: Path):
    path = tmp_path / "c.yaml"
    path.write_text(VALID, encoding="utf-8")
    config = load_config(path)
    assert config.datasets[0].name == "mini"
    assert config.metrics.families == ["A"]
    assert config.report.flagged_examples == 2


def test_report_settings_have_defaults(tmp_path: Path):
    path = tmp_path / "c.yaml"
    path.write_text(
        "datasets:\n  - name: m\n    loader: jsonl\n    path: x.jsonl\n", encoding="utf-8"
    )
    config = load_config(path)
    assert config.report.flagged_examples == 5
    assert config.metrics.families == ["A"]


def test_unknown_key_is_rejected(tmp_path: Path):
    path = tmp_path / "c.yaml"
    path.write_text(VALID + "\nnonsense: 1\n", encoding="utf-8")
    with pytest.raises(ValueError):
        load_config(path)
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `uv run pytest tests/test_config.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'docsimp_eval.config'`

- [ ] **Step 3: Write the config module**

`src/docsimp_eval/config.py`:

```python
from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, ValidationError


class DatasetConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    loader: str
    path: str | None = None
    split: str | None = None
    language: str | None = None


class MetricsConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    families: list[str] = ["A"]


class ReportConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    flagged_examples: int = 5
    excerpt_chars: int = 400


class RunConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    datasets: list[DatasetConfig]
    metrics: MetricsConfig = MetricsConfig()
    report: ReportConfig = ReportConfig()


def load_config(path: Path) -> RunConfig:
    raw = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    try:
        return RunConfig.model_validate(raw)
    except ValidationError as error:
        raise ValueError(f"{path}: invalid configuration\n{error}") from error
```

- [ ] **Step 4: Write the failing CLI test**

`tests/test_cli.py`:

```python
from pathlib import Path

from docsimp_eval.cli import main

CONFIG = """
datasets:
  - name: mini
    loader: jsonl
    path: {path}
metrics:
  families: [A]
report:
  flagged_examples: 1
  excerpt_chars: 60
"""


def test_run_writes_a_report(tmp_path: Path):
    fixture = Path(__file__).parent / "fixtures" / "mini.jsonl"
    config = tmp_path / "c.yaml"
    config.write_text(CONFIG.format(path=fixture), encoding="utf-8")
    out = tmp_path / "reports"

    exit_code = main(["run", "--config", str(config), "--out", str(out)])

    assert exit_code == 0
    report = (out / "report.md").read_text(encoding="utf-8")
    assert "# docsimp-eval report" in report
    assert "mini" in report


def test_missing_config_returns_nonzero(tmp_path: Path):
    assert main(["run", "--config", str(tmp_path / "nope.yaml")]) == 1
```

- [ ] **Step 5: Run the test to verify it fails**

Run: `uv run pytest tests/test_cli.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'docsimp_eval.cli'`

- [ ] **Step 6: Write the CLI**

`src/docsimp_eval/cli.py`:

```python
import argparse
from pathlib import Path

from docsimp_eval.config import RunConfig, load_config
from docsimp_eval.loaders import get_loader
from docsimp_eval.report import render_report
from docsimp_eval.runner import run_metrics


def _load_datasets(config: RunConfig) -> dict[str, list]:
    datasets = {}
    for entry in config.datasets:
        loader = get_loader(entry.loader)
        if entry.loader == "jsonl":
            datasets[entry.name] = loader(Path(entry.path))
        else:
            datasets[entry.name] = loader(split=entry.split, language=entry.language)
    return datasets


def _run(args: argparse.Namespace) -> int:
    config_path = Path(args.config)
    if not config_path.exists():
        print(f"config not found: {config_path}")
        return 1
    config = load_config(config_path)
    datasets = _load_datasets(config)
    runs = run_metrics(datasets, families=config.metrics.families)
    report = render_report(
        runs,
        flagged_examples=config.report.flagged_examples,
        excerpt_chars=config.report.excerpt_chars,
    )
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "report.md").write_text(report, encoding="utf-8")
    print(f"wrote {out_dir / 'report.md'}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="docsimp-eval")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run", help="profile the configured datasets")
    run_parser.add_argument("--config", required=True)
    run_parser.add_argument("--out", default="reports")
    run_parser.set_defaults(func=_run)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 7: Add the example config**

`configs/mini.yaml`:

```yaml
# Smallest possible run: the committed test fixture.
datasets:
  - name: mini
    loader: jsonl
    path: tests/fixtures/mini.jsonl

metrics:
  families: [A]

report:
  flagged_examples: 2
  excerpt_chars: 200
```

- [ ] **Step 8: Run the full suite**

Run: `uv run pytest -v`
Expected: all tests pass

- [ ] **Step 9: Run the tool end to end**

Run: `uv run docsimp-eval run --config configs/mini.yaml --out reports/`
Expected: `wrote reports/report.md`, containing a Family A table with `mini` as its only column, and pair `p3` (the identical pair) in the flagged section.

- [ ] **Step 10: Commit**

```bash
git add src/docsimp_eval/config.py src/docsimp_eval/cli.py configs/ tests/test_config.py tests/test_cli.py
git commit -m "feat: add YAML config and CLI"
```

---

### Task 12: EUR-Lex-Sum loader

**Files:**
- Create: `src/docsimp_eval/loaders/eurlex_sum.py`, `tests/test_eurlex_loader.py`
- Modify: `src/docsimp_eval/loaders/__init__.py`
- Create: `configs/eurlex.yaml`

**Interfaces:**
- Consumes: `DocumentPair` (Task 1), `register_loader` (Task 1)
- Produces: `load_eurlex_sum(split: str | None = "test", language: str | None = "en") -> list[DocumentPair]`

EUR-Lex-Sum is on the HF Hub as `dennlinger/eur-lex-sum`, configured per language, with `reference` (the legal act) and `summary` fields.

- [ ] **Step 1: Write the failing test**

Tests must not hit the network, so the HF call is stubbed.

`tests/test_eurlex_loader.py`:

```python
from docsimp_eval.loaders import eurlex_sum


def test_maps_hf_fields_to_document_pairs(monkeypatch):
    fake_rows = [
        {"celex_id": "32019R0001", "reference": "long legal act", "summary": "short summary"},
        {"celex_id": "32019R0002", "reference": "another act", "summary": "another summary"},
    ]
    monkeypatch.setattr(eurlex_sum, "_fetch", lambda split, language: fake_rows)

    pairs = eurlex_sum.load_eurlex_sum(split="test", language="en")

    assert [p.id for p in pairs] == ["32019R0001", "32019R0002"]
    assert pairs[0].source == "long legal act"
    assert pairs[0].target == "short summary"


def test_tags_the_domain_as_legal(monkeypatch):
    monkeypatch.setattr(
        eurlex_sum,
        "_fetch",
        lambda split, language: [{"celex_id": "x", "reference": "a", "summary": "b"}],
    )
    assert eurlex_sum.load_eurlex_sum().pop().domain == "legal"


def test_non_english_is_rejected_in_v1(monkeypatch):
    import pytest

    with pytest.raises(ValueError, match="English"):
        eurlex_sum.load_eurlex_sum(language="de")
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `uv run pytest tests/test_eurlex_loader.py -v`
Expected: FAIL — `ImportError: cannot import name 'eurlex_sum'`

- [ ] **Step 3: Write the loader**

`src/docsimp_eval/loaders/eurlex_sum.py`:

```python
"""EUR-Lex-Sum (Aumiller, Chouhan & Gertz, EMNLP 2022) via the HF Hub.

Source is the full legal act, target the human-written summary. Included as
a full candidate corpus: whether its compression puts it outside the task is
for the reader to judge from the report.
"""

from docsimp_eval.schema import DocumentPair

DATASET = "dennlinger/eur-lex-sum"
DOMAIN = "legal"


def _fetch(split: str, language: str) -> list[dict]:
    from datasets import load_dataset

    return list(load_dataset(DATASET, language, split=split))


def load_eurlex_sum(
    split: str | None = "test", language: str | None = "en"
) -> list[DocumentPair]:
    language = language or "en"
    if language != "en":
        raise ValueError(
            f"v1 is English only; got language={language!r}. Readability "
            "metrics such as FKGL do not transfer across languages."
        )
    rows = _fetch(split or "test", language)
    return [
        DocumentPair(
            id=str(row["celex_id"]),
            source=row["reference"],
            target=row["summary"],
            domain=DOMAIN,
        )
        for row in rows
    ]
```

- [ ] **Step 4: Register the loader**

Modify `src/docsimp_eval/loaders/__init__.py` — replace the `_LOADERS` definition with:

```python
from docsimp_eval.loaders.eurlex_sum import load_eurlex_sum
from docsimp_eval.loaders.jsonl import load_jsonl

_LOADERS: dict[str, Callable[..., list]] = {
    "jsonl": load_jsonl,
    "eurlex_sum": load_eurlex_sum,
}
```

- [ ] **Step 5: Add the config**

`configs/eurlex.yaml`:

```yaml
datasets:
  - name: eurlex_sum
    loader: eurlex_sum
    split: test
    language: en

metrics:
  families: [A]

report:
  flagged_examples: 5
  excerpt_chars: 400
```

- [ ] **Step 6: Run the tests**

Run: `uv run pytest -v`
Expected: all tests pass

- [ ] **Step 7: Smoke-test against the real corpus**

Run: `uv run docsimp-eval run --config configs/eurlex.yaml --out reports/`
Expected: downloads the English test split, writes `reports/report.md`. Sanity-check that compression ratio is well below 1 (legal acts are far longer than their summaries) and that the flagged pairs read plausibly.

- [ ] **Step 8: Commit**

```bash
git add src/docsimp_eval/loaders tests/test_eurlex_loader.py configs/eurlex.yaml
git commit -m "feat: add EUR-Lex-Sum loader"
```

---

## What this plan deliberately leaves out

- **Families B and C** — separate plans. Family B needs document alignment, which is a substantial component in its own right; family C needs embedding models.
- **Distribution plots** — the README promises them; they belong with family B, once there are enough metrics for a figure to beat a table.
- **Remaining loaders** — D-Wikipedia, Newsela, Wiki-auto, Cochrane, Cochrane-auto. EUR-Lex-Sum proves the loader interface; the rest are mechanical and better added alongside the metrics that motivate them.
- **`docsimp-eval fetch`** — the README documents it. Add it with the loaders that need pre-downloading.

Update the README status table as each plan lands.
