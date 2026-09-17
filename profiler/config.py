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
    "deletion_profile",
    "linguistic_features",
    "pair_similarity",
]

# Modules that require English-language processing (parsing, readability
# formulas tuned to English, entailment models). On a non-English corpus these
# must raise rather than emit invalid output (PRD s2).
ENGLISH_ONLY_MODULES = {"readability", "elaboration", "linguistic_features"}

KNOWN_ADAPTERS = {"jsonl", "hf", "filedir"}

# Backend names are validated at load. get_embedder raised on an unknown name
# only when M4 started -- after the full-corpus M1-M3 pass -- and
# get_primary_scorer only at M5, after M4's embeddings. A typo cost hours.
KNOWN_EMBEDDERS = {"sbert", "hashing"}
KNOWN_NLI_BACKENDS = {"nli", "lexical"}
KNOWN_DEVICES = {"auto", "cpu", "mps", "cuda"}

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
    tau_sweep: list[float] = field(default_factory=lambda: [0.4, 0.5, 0.6, 0.7, 0.8])
    nli_threshold: float = 0.5
    jargon_terms: list[str] = field(default_factory=list)
    # Model backends. 'sbert'/'nli' use real models (network download on first
    # use); 'hashing'/'lexical' are deterministic offline stand-ins for tests
    # and smoke runs.
    embedder: str = "sbert"
    embed_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    nli_backend: str = "nli"
    nli_model: str = "microsoft/deberta-large-mnli"
    # Torch device for the SBERT/NLI backends. 'auto' picks mps/cuda when
    # available, else cpu. Purely a speed knob: same model, same math.
    device: str = "auto"
    # Primary tau used for the alignment that feeds M5/M6 (M4 itself sweeps).
    # Stays 0.5. 0.7 measures better against SWiPE's human deletion labels
    # (kappa 0.754 vs 0.410; see scripts/validate_deletion_split.py) but that
    # calibration is Wikipedia prose with MiniLM and does not transfer: on XSum
    # it raises the deletion rate to 0.983 and leaves only 13 of 60 documents
    # with the deleted/retained contrast M6 needs. The threshold is
    # genre-dependent, so each config sets its own and the default stays where
    # every committed result was produced.
    m6_tau: float = 0.5
    # M5 optional scorers. NLI always runs (unless heuristic_only); these gate
    # the fragile extras.
    alignscore: bool = False
    summac: bool = False
    heuristic_only: bool = False
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


def _num_list(value: Any, name: str) -> list[float]:
    """Coerce a list-of-floats run field (``tau_sweep``).

    A scalar raised ``TypeError: 'int' object is not iterable`` from ``list()``.
    """

    if isinstance(value, (str, bytes)) or not isinstance(value, (list, tuple)):
        raise ConfigError(f"run.{name} must be a list of numbers; got {value!r}")
    return [_num(v, name, float, "a list of numbers") for v in value]


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
    run = RunConfig(
        sample_size=_opt_int(run_raw.get("sample_size", 1000), "sample_size"),
        seed=_num(run_raw.get("seed", 13), "seed", int, "an integer"),
        language=str(run_raw.get("language", "en")),
        cache_dir=str(run_raw.get("cache_dir", ".cache/")),
        output_dir=str(run_raw.get("output_dir", "runs/")),
        bootstrap_resamples=_num(
            run_raw.get("bootstrap_resamples", 1000), "bootstrap_resamples", int, "an integer"
        ),
        tau_sweep=_num_list(run_raw.get("tau_sweep", [0.4, 0.5, 0.6, 0.7, 0.8]), "tau_sweep"),
        nli_threshold=_num(run_raw.get("nli_threshold", 0.5), "nli_threshold", float, "a number"),
        jargon_terms=list(run_raw.get("jargon_terms", []) or []),
        embedder=str(run_raw.get("embedder", "sbert")),
        embed_model=str(
            run_raw.get("embed_model", "sentence-transformers/all-MiniLM-L6-v2")
        ),
        nli_backend=str(run_raw.get("nli_backend", "nli")),
        nli_model=str(run_raw.get("nli_model", "microsoft/deberta-large-mnli")),
        device=str(run_raw.get("device", "auto")),
        m6_tau=_num(run_raw.get("m6_tau", 0.5), "m6_tau", float, "a number"),
        alignscore=bool(run_raw.get("alignscore", False)),
        summac=bool(run_raw.get("summac", False)),
        heuristic_only=bool(run_raw.get("heuristic_only", False)),
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
    if not cfg.run.tau_sweep:
        raise ConfigError("run.tau_sweep must not be empty")
    for t in cfg.run.tau_sweep:
        if not 0.0 <= float(t) <= 1.0:
            raise ConfigError(f"tau values must be in [0,1]; got {t}")
    # These two were unvalidated while tau_sweep was. Out of range they produce
    # no error and no obvious wrong number: m6_tau above 1 labels every source
    # sentence deleted, so M6's contrast vanishes and every effect size goes
    # null; nli_threshold above 1 makes M5's not-entailed rate exactly 1.0.
    for name, value in (
        ("m6_tau", cfg.run.m6_tau),
        ("nli_threshold", cfg.run.nli_threshold),
    ):
        if not 0.0 <= float(value) <= 1.0:
            raise ConfigError(f"{name} must be in [0,1]; got {value}")

    for name, value, known in (
        ("embedder", cfg.run.embedder, KNOWN_EMBEDDERS),
        ("nli_backend", cfg.run.nli_backend, KNOWN_NLI_BACKENDS),
        ("device", cfg.run.device, KNOWN_DEVICES),
    ):
        if value not in known:
            raise ConfigError(
                f"unknown run.{name} '{value}'; known: {sorted(known)}"
            )

    # M5 and M6 read M4's alignment out of the shared context and raise if it is
    # absent -- but only after the full-corpus M1-M3 pass, which is hours on a
    # long-document corpus. Catch it at load instead.
    requested = set(cfg.modules)
    needs_alignment = requested & {"elaboration", "deletion_profile"}
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
