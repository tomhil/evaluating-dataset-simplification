"""Content-addition scorers for M5.

Each scorer maps a (target_sentence, [source_sentences]) pair to a groundedness
score in [0, 1], where low = the target sentence is not supported by the source.

* ``TransformersNLI`` - off-the-shelf NLI entailment, aggregated as the max
  entailment probability over source sentences (network download on first use).
* ``LexicalGrounding`` - deterministic offline stand-in (content-word overlap),
  used for tests, smoke runs, and the ``heuristic_only`` fallback.
* AlignScore and SummaC are optional plugins loaded lazily via
  :func:`optional_scorers`; if their package/checkpoint is absent the scorer is
  skipped and the module records which scorers actually ran.
"""

from __future__ import annotations

import re
from typing import Callable, Protocol

import numpy as np

from .cache import Cache, content_hash

_TOK = re.compile(r"[A-Za-z0-9]+")

# Premise batch size for TransformersNLI. Bounds peak GPU memory independently
# of how many sentences a source document has.
NLI_BATCH = 32


class SentenceScorer(Protocol):
    name: str

    def score(self, target_sents: list[str], source_sents: list[str]) -> list[float]:
        """Return one groundedness score per target sentence."""


class LexicalGrounding:
    """Fraction of a target sentence's content words present in the source."""

    name = "lexical_grounding"

    def __init__(self, stopwords: frozenset[str] | None = None):
        from .nlp import _STOPWORDS

        self._stop = stopwords or _STOPWORDS

    def _content(self, text: str) -> set[str]:
        return {
            w.lower()
            for w in _TOK.findall(text)
            if w.lower() not in self._stop and not w.isdigit()
        }

    def score(self, target_sents: list[str], source_sents: list[str]) -> list[float]:
        src = set()
        for s in source_sents:
            src |= self._content(s)
        out = []
        for t in target_sents:
            ct = self._content(t)
            out.append(len(ct & src) / len(ct) if ct else 1.0)
        return out


class TransformersNLI:
    """NLI entailment probability, max-aggregated over source sentences."""

    name = "nli"

    def __init__(self, model: str, cache: Cache | None = None, device: str = "auto"):
        import torch

        from .embeddings import resolve_device
        from transformers import (
            AutoModelForSequenceClassification,
            AutoTokenizer,
        )

        self._torch = torch
        self._tok = AutoTokenizer.from_pretrained(model)
        self._model = AutoModelForSequenceClassification.from_pretrained(model)
        self._model.eval()
        # deberta-large is ~4x faster on mps/cuda than cpu, and M5 issues
        # (#target x #source) forward passes per pair, so the device matters.
        self.device = resolve_device(device)
        self._model.to(self.device)
        self._cache = cache
        self._model_name = model
        # Locate the entailment label index robustly.
        id2label = {int(k): v.lower() for k, v in self._model.config.id2label.items()}
        self._entail_idx = next(
            (i for i, lab in id2label.items() if "entail" in lab), len(id2label) - 1
        )

    def score(self, target_sents: list[str], source_sents: list[str]) -> list[float]:
        if not source_sents:
            return [0.0] * len(target_sents)
        out: list[float] = []
        for t in target_sents:
            key = content_hash(self._model_name, "||".join(source_sents), t)
            if self._cache is not None:
                cached = self._cache.get_json(key)
                if cached is not None:
                    out.append(float(cached))
                    continue
            probs = self._entail_probs(premises=source_sents, hypothesis=t)
            val = float(np.max(probs)) if len(probs) else 0.0
            if self._cache is not None:
                self._cache.put_json(key, val)
            out.append(val)
        return out

    def _entail_probs(self, premises: list[str], hypothesis: str) -> np.ndarray:
        """Entailment probability of ``hypothesis`` under each premise.

        Premises are scored in fixed-size chunks. A long-document corpus can put
        hundreds of source sentences in one call (eLife averages ~605), and
        encoding them as a single batch exhausts GPU memory. Chunking changes no
        arithmetic -- the caller still takes the max over every premise -- and
        cuts padding waste, since each batch pads only to its own longest pair.
        """
        torch = self._torch
        out: list[np.ndarray] = []
        for start in range(0, len(premises), NLI_BATCH):
            chunk = premises[start : start + NLI_BATCH]
            enc = self._tok(
                chunk,
                [hypothesis] * len(chunk),
                return_tensors="pt",
                truncation=True,
                padding=True,
                max_length=256,
            ).to(self.device)
            with torch.no_grad():
                logits = self._model(**enc).logits
                probs = torch.softmax(logits, dim=-1)[:, self._entail_idx]
            out.append(probs.cpu().numpy())
        if not out:
            return np.zeros(0)
        return np.concatenate(out)


def get_primary_scorer(config, cache: Cache) -> SentenceScorer:
    backend = config.run.nli_backend
    if backend == "lexical":
        return LexicalGrounding()
    if backend == "nli":
        return TransformersNLI(
            config.run.nli_model, cache=cache, device=config.run.device
        )
    raise ValueError(f"unknown nli_backend '{backend}'")


def optional_scorers(config, cache: Cache) -> tuple[list[SentenceScorer], list[str]]:
    """Load the optional AlignScore/SummaC scorers if requested and importable.

    Returns (loaded_scorers, skipped_notes).
    """

    loaded: list[SentenceScorer] = []
    skipped: list[str] = []
    if config.run.alignscore:
        s, note = _try_load(_load_alignscore)
        (loaded if s else skipped).append(s or note)
    if config.run.summac:
        s, note = _try_load(_load_summac)
        (loaded if s else skipped).append(s or note)
    return loaded, [n for n in skipped if isinstance(n, str)]


def _try_load(loader: Callable[[], SentenceScorer]):
    try:
        return loader(), None
    except Exception as exc:  # pragma: no cover - optional deps
        return None, f"{loader.__name__} unavailable: {exc}"


def _load_alignscore() -> SentenceScorer:  # pragma: no cover - optional dep
    from alignscore import AlignScore  # type: ignore

    class _AlignScoreScorer:
        name = "alignscore"

        def __init__(self):
            self._m = AlignScore(
                model="roberta-base",
                batch_size=32,
                device="cpu",
                ckpt_path=None,
                evaluation_mode="nli_sp",
            )

        def score(self, target_sents, source_sents):
            ctx = " ".join(source_sents)
            return [float(x) for x in self._m.score(contexts=[ctx] * len(target_sents), claims=list(target_sents))]

    return _AlignScoreScorer()


def _load_summac() -> SentenceScorer:  # pragma: no cover - optional dep
    from summac.model_summac import SummaCConv  # type: ignore

    class _SummaCScorer:
        name = "summac_conv"

        def __init__(self):
            self._m = SummaCConv(models=["vitc"], bins="percentile", granularity="sentence", device="cpu")

        def score(self, target_sents, source_sents):
            doc = " ".join(source_sents)
            res = self._m.score([doc] * len(target_sents), list(target_sents))
            return [float(x) for x in res["scores"]]

    return _SummaCScorer()
