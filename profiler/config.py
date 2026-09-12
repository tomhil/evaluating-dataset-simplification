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
]

# Modules that require English-language processing (parsing, readability
# formulas tuned to English, entailment models). On a non-English corpus these
# must raise rather than emit invalid output (PRD s2).
ENGLISH_ONLY_MODULES = {"readability", "elaboration"}

KNOWN_ADAPTERS = {"jsonl", "hf", "filedir"}


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
    # (kappa 0.767 vs 0.462; see scripts/validate_deletion_split.py) but that
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
        sample_size=run_raw.get("sample_size", 1000),
        seed=int(run_raw.get("seed", 13)),
        language=str(run_raw.get("language", "en")),
        cache_dir=str(run_raw.get("cache_dir", ".cache/")),
        output_dir=str(run_raw.get("output_dir", "runs/")),
        bootstrap_resamples=int(run_raw.get("bootstrap_resamples", 1000)),
        tau_sweep=list(run_raw.get("tau_sweep", [0.4, 0.5, 0.6, 0.7, 0.8])),
        nli_threshold=float(run_raw.get("nli_threshold", 0.5)),
        jargon_terms=list(run_raw.get("jargon_terms", []) or []),
        embedder=str(run_raw.get("embedder", "sbert")),
        embed_model=str(
            run_raw.get("embed_model", "sentence-transformers/all-MiniLM-L6-v2")
        ),
        nli_backend=str(run_raw.get("nli_backend", "nli")),
        nli_model=str(run_raw.get("nli_model", "microsoft/deberta-large-mnli")),
        device=str(run_raw.get("device", "auto")),
        m6_tau=float(run_raw.get("m6_tau", 0.5)),
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
    for t in cfg.run.tau_sweep:
        if not 0.0 <= float(t) <= 1.0:
            raise ConfigError(f"tau values must be in [0,1]; got {t}")

    # Language gating: requesting an English-only module on a non-English
    # corpus is a loud error, not a silent drop (PRD s2).
    if not cfg.language.lower().startswith("en"):
        conflicting = [m for m in cfg.modules if m in ENGLISH_ONLY_MODULES]
        if conflicting:
            raise ConfigError(
                f"modules {conflicting} require language=en but language="
                f"'{cfg.language}'. Remove them or set language=en."
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
