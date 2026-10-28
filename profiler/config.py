"""Configuration loading and validation.

The config is a small typed tree parsed from YAML. Validation is strict and
fails loudly: an unknown adapter, an unknown module, or a missing required
field raises ``ConfigError`` rather than being silently defaulted.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

ALL_MODULES = [
    "length",
    "abstractiveness",
    "readability",
    "alignment",
    "elaboration",
    "linguistic_features",
    "pair_similarity",
]

# Modules that require English-language processing (parsing, readability
# formulas tuned to English, entailment models). On a non-English corpus these
# must raise rather than emit invalid output (PRD s2).
ENGLISH_ONLY_MODULES = {"readability", "elaboration", "linguistic_features"}

KNOWN_ADAPTERS = {"jsonl", "hf", "filedir"}

# The device name is validated at load: an unknown backend name used to raise
# only when its model loaded, hours into a run on a long-document corpus.
KNOWN_DEVICES = {"auto", "cpu", "mps", "cuda"}

# Run keys and modules removed in the October 2026 metric revision (the
# "Removed" list in docs/metrics.md). A config that still sets one is rejected
# at load rather than silently ignored, so nobody believes a removed metric,
# threshold or backend still shapes the run. The value is what to do instead.
REVISION = "the October 2026 metric revision"
REMOVED_RUN_KEYS = {
    "tau_sweep": "M4's sentence alignment and its tau sweep were removed",
    "m6_tau": "M4's alignment and module M6 (deletion_profile) were removed",
    "embedder": "M4's SBERT sentence alignment was removed",
    "embed_model": "M4's SBERT sentence alignment was removed",
    "nli_backend": (
        "M5's NLI scorer was removed; set run.stand_ins: true for the offline "
        "stand-ins it used to select"
    ),
    "nli_model": "M5's NLI scorer was removed",
    "nli_threshold": "M5's not-entailed rate and its threshold were removed",
    "heuristic_only": (
        "M5's content-word fallback was removed; set run.stand_ins: true for "
        "the offline stand-ins it used to select"
    ),
    "jargon_terms": "M3b's jargon_rate and M6 were removed",
}
REMOVED_MODULES = {
    "deletion_profile": "module M6 (deletion_profile) was removed",
}

# The only language with a processor. get_processor ignored its argument and
# always loaded en_core_web_sm, so the documented "non-English corpora get
# M1/M2/M4" path would have applied English segmentation, tokenisation and
# stopword lists to non-English text and reported the numbers without comment.
SUPPORTED_LANGUAGES = {"en"}


class ConfigError(ValueError):
    """Raised for any invalid or inconsistent configuration."""


@dataclass
class DatasetConfig:
    adapter: str
    # Adapter-specific fields are kept in ``options`` verbatim; each adapter
    # documents what it reads.
    name: str | None = None
    split: str | None = None
    source_field: str | None = None
    target_field: str | None = None
    path: str | None = None
    src_dir: str | None = None
    tgt_dir: str | None = None
    options: dict = field(default_factory=dict)


@dataclass
class RunConfig:
    sample_size: int | None = 1000
    seed: int = 13
    language: str = "en"
    cache_dir: str = ".cache/"
    output_dir: str = "runs/"
    bootstrap_resamples: int = 1000
    # Torch device for the model-based metrics. 'auto' picks mps/cuda when
    # available, else cpu. Purely a speed knob: same model, same math.
    device: str = "auto"
    # M5 optional sentence-level scorers; summac also gates document-level
    # SummaC.
    alignscore: bool = False
    summac: bool = False
    # Deterministic offline stand-ins for the model-based metrics (M3d's SLE
    # and coherence, M5's document-level SummaC and rhetorical roles), for
    # tests and smoke runs: no model download. Stand-in values exercise the
    # plumbing only; they are flagged in notes and in the *_run records and are
    # not the published metrics. A scorer requested with run.summac still uses
    # the real model.
    stand_ins: bool = False
    # Model-based literature metrics that load their own checkpoints: M3's
    # m3d_model_based block (SLE, BERT coherence) and M5's rhetorical roles.
    # On by default; false skips them with a note and null keys (no download).
    # SummaC has its own switch above.
    model_metrics: bool = True
    # Names used to construct the run directory / report titles.
    dataset_label: str = "dataset"


@dataclass
class Config:
    dataset: DatasetConfig
    run: RunConfig
    modules: list[str]
    raw: dict = field(default_factory=dict)

    @property
    def language(self) -> str:
        return self.run.language

    def active_modules(self) -> list[str]:
        """Modules to run, after language gating.

        On non-English corpora the English-only modules are *not* silently
        dropped: if the user explicitly requested one, that is an error the
        caller surfaces. This method only returns the language-valid subset;
        :func:`validate` is what raises on the conflict.
        """
        if self.language.lower().startswith("en"):
            return list(self.modules)
        return [m for m in self.modules if m not in ENGLISH_ONLY_MODULES]


def _opt_int(value: Any, name: str) -> int | None:
    """Coerce a nullable integer field, raising ConfigError on junk."""

    if value is None:
        return None
    return _num(value, name, int, "an integer or null")


def _num(value: Any, name: str, cast, expected: str):
    """Coerce a numeric run field, reporting failure as a ConfigError.

    Every numeric field went through a bare ``int()``/``float()``, so junk
    raised ValueError or TypeError from inside the parser rather than a
    ConfigError naming the field -- and ``profiler.__main__`` catches neither,
    so the user saw a traceback. PyYAML makes this easy to hit: YAML 1.1 needs
    ``1.0e+3``, so ``seed: 1e3`` arrives as the *string* ``"1e3"``.
    """

    try:
        return cast(value)
    except (TypeError, ValueError):
        raise ConfigError(f"run.{name} must be {expected}; got {value!r}") from None


def _require(d: dict, key: str, where: str) -> Any:
    if key not in d or d[key] is None:
        raise ConfigError(f"missing required field '{key}' in {where}")
    return d[key]


def load_config(path: str | Path) -> Config:
    path = Path(path)
    if not path.exists():
        raise ConfigError(f"config file not found: {path}")
    with path.open() as fh:
        raw = yaml.safe_load(fh)
    if not isinstance(raw, dict):
        raise ConfigError("config root must be a mapping")
    return parse_config(raw)


def parse_config(raw: dict) -> Config:
    ds_raw = _require(raw, "dataset", "config")
    if not isinstance(ds_raw, dict):
        raise ConfigError("'dataset' must be a mapping")

    adapter = str(_require(ds_raw, "adapter", "dataset")).lower()
    if adapter not in KNOWN_ADAPTERS:
        raise ConfigError(
            f"unknown adapter '{adapter}'; known: {sorted(KNOWN_ADAPTERS)}"
        )

    known_ds_keys = {
        "adapter",
        "name",
        "split",
        "source_field",
        "target_field",
        "path",
        "src_dir",
        "tgt_dir",
    }
    dataset = DatasetConfig(
        adapter=adapter,
        name=ds_raw.get("name"),
        split=ds_raw.get("split"),
        source_field=ds_raw.get("source_field"),
        target_field=ds_raw.get("target_field"),
        path=ds_raw.get("path"),
        src_dir=ds_raw.get("src_dir"),
        tgt_dir=ds_raw.get("tgt_dir"),
        options={k: v for k, v in ds_raw.items() if k not in known_ds_keys},
    )

    run_raw = raw.get("run", {}) or {}
    if not isinstance(run_raw, dict):
        raise ConfigError("'run' must be a mapping")
    removed = [k for k in REMOVED_RUN_KEYS if k in run_raw]
    if removed:
        raise ConfigError(
            "run key(s) removed in "
            + REVISION
            + "; delete them from the config: "
            + "; ".join(f"run.{k} ({REMOVED_RUN_KEYS[k]})" for k in removed)
        )
    run = RunConfig(
        sample_size=_opt_int(run_raw.get("sample_size", 1000), "sample_size"),
        seed=_num(run_raw.get("seed", 13), "seed", int, "an integer"),
        language=str(run_raw.get("language", "en")),
        cache_dir=str(run_raw.get("cache_dir", ".cache/")),
        output_dir=str(run_raw.get("output_dir", "runs/")),
        bootstrap_resamples=_num(
            run_raw.get("bootstrap_resamples", 1000), "bootstrap_resamples", int, "an integer"
        ),
        device=str(run_raw.get("device", "auto")),
        alignscore=bool(run_raw.get("alignscore", False)),
        summac=bool(run_raw.get("summac", False)),
        stand_ins=bool(run_raw.get("stand_ins", False)),
        model_metrics=bool(run_raw.get("model_metrics", True)),
        dataset_label=str(
            run_raw.get("dataset_label")
            or dataset.name
            or dataset.path
            or "dataset"
        ),
    )

    modules = raw.get("modules")
    if modules is None:
        modules = list(ALL_MODULES)
    if not isinstance(modules, list) or not modules:
        raise ConfigError("'modules' must be a non-empty list")
    gone = [m for m in modules if isinstance(m, str) and m in REMOVED_MODULES]
    if gone:
        raise ConfigError(
            "module(s) removed in "
            + REVISION
            + "; delete them from 'modules': "
            + "; ".join(f"{m} ({REMOVED_MODULES[m]})" for m in gone)
        )
    unknown = [m for m in modules if m not in ALL_MODULES]
    if unknown:
        raise ConfigError(
            f"unknown module(s) {unknown}; known: {ALL_MODULES}"
        )

    cfg = Config(dataset=dataset, run=run, modules=list(modules), raw=raw)
    validate(cfg)
    return cfg


def validate(cfg: Config) -> None:
    if cfg.run.sample_size is not None and cfg.run.sample_size <= 0:
        raise ConfigError("run.sample_size must be positive or null")
    if cfg.run.bootstrap_resamples <= 0:
        raise ConfigError("run.bootstrap_resamples must be positive")
    if cfg.run.device not in KNOWN_DEVICES:
        raise ConfigError(
            f"unknown run.device '{cfg.run.device}'; known: {sorted(KNOWN_DEVICES)}"
        )

    # M5 reads M4's sentence lists out of the shared context and raises if they
    # are absent -- but only after the full-corpus M1-M3 pass, which is hours on a
    # long-document corpus. Catch it at load instead.
    requested = set(cfg.modules)
    needs_alignment = requested & {"elaboration"}
    if needs_alignment and "alignment" not in requested:
        raise ConfigError(
            f"modules {sorted(needs_alignment)} read M4's alignment and cannot "
            f"run without it. Add 'alignment' to modules."
        )

    # Language: there is one processor and it is English. Loading a non-English
    # config used to succeed for M1/M2/M4 and then silently apply English
    # segmentation, tokenisation and stopwords, so every length ratio,
    # sentence count and alignment rested on wrong segmentation with no warning.
    # Refuse instead of reporting numbers that look fine and are not.
    lang = cfg.language.lower().split("-")[0].split("_")[0]
    if lang not in SUPPORTED_LANGUAGES:
        raise ConfigError(
            f"language '{cfg.language}' is not supported: the only processor is "
            f"English (en_core_web_sm), and using it on other languages "
            f"invalidates segmentation, tokenisation and stopword handling for "
            f"every module. Supported: {sorted(SUPPORTED_LANGUAGES)}."
        )

    # Adapter-specific required fields.
    ds = cfg.dataset
    if ds.adapter == "hf":
        _require({"name": ds.name}, "name", "dataset (hf adapter)")
        _require(
            {"source_field": ds.source_field},
            "source_field",
            "dataset (hf adapter)",
        )
        _require(
            {"target_field": ds.target_field},
            "target_field",
            "dataset (hf adapter)",
        )
    elif ds.adapter == "jsonl":
        _require({"path": ds.path}, "path", "dataset (jsonl adapter)")
        _require(
            {"source_field": ds.source_field},
            "source_field",
            "dataset (jsonl adapter)",
        )
        _require(
            {"target_field": ds.target_field},
            "target_field",
            "dataset (jsonl adapter)",
        )
    elif ds.adapter == "filedir":
        _require({"src_dir": ds.src_dir}, "src_dir", "dataset (filedir adapter)")
        _require({"tgt_dir": ds.tgt_dir}, "tgt_dir", "dataset (filedir adapter)")
