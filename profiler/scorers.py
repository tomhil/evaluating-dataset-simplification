"""Optional sentence-level scorers for M5.

Each scorer maps a (target_sentences, source_sentences) pair to one
groundedness score per target sentence, where low = the target sentence is not
supported by the source.

AlignScore and SummaC-Conv are optional plugins loaded lazily via
:func:`optional_scorers`; if their package/checkpoint is absent the scorer is
skipped and the module records which scorers actually ran. (The NLI scorer and
its offline content-word stand-in were removed in the October 2026 metric
revision.)
"""

from __future__ import annotations

import functools
import warnings

from typing import Callable, Protocol

from .cache import Cache


class SentenceScorer(Protocol):
    name: str

    def score(self, target_sents: list[str], source_sents: list[str]) -> list[float]:
        """Return one groundedness score per target sentence."""


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
    """Load an optional scorer, returning ``(scorer, note)``.

    The note goes into ``metrics.json`` via M5's ``notes``, and that file is
    contractually byte-identical across runs of one config and free of absolute
    paths. Interpolating ``str(exc)`` broke both: a checkpoint-not-found message
    embeds an HF cache path, and a CUDA message embeds a driver version, so two
    machines -- or one machine before and after a download -- produced different
    bytes. Record the exception *type*, which is stable, and let the full text
    go to stderr where it is useful for debugging.
    """

    try:
        return loader(), None
    except Exception as exc:  # pragma: no cover - optional deps
        warnings.warn(
            f"{loader.__name__} unavailable: {type(exc).__name__}: {exc}",
            RuntimeWarning,
            stacklevel=2,
        )
        return None, (
            f"{loader.__name__} unavailable ({type(exc).__name__}); "
            f"scorer skipped. See stderr for details."
        )


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


# SummaC-Conv's 1-D convolution layer is trained. Without start_file it keeps
# torch's random initialisation, so scores are neither SummaC-Conv's nor
# reproducible; "default" makes summac load its released weights
# (summac_conv_vitc_sent_perc_e.bin, fetched into the working directory on
# first use), which require percentile bins and the vitc model.
SUMMAC_CONV_KWARGS = {
    "models": ["vitc"],
    "bins": "percentile",
    "granularity": "sentence",
    "start_file": "default",
}


@functools.lru_cache(maxsize=None)
def summac_conv_model(device: str = "cpu"):
    """One SummaC-Conv instance per device, shared by M5's sentence-level
    scorer and its document-level faithfulness, so the vitc model is loaded
    once rather than twice."""

    from summac.model_summac import SummaCConv  # type: ignore

    return SummaCConv(**SUMMAC_CONV_KWARGS, device=device)


def _load_summac() -> SentenceScorer:
    class _SummaCScorer:
        name = "summac_conv"

        def __init__(self):
            self._m = summac_conv_model("cpu")

        def score(self, target_sents, source_sents):
            doc = " ".join(source_sents)
            res = self._m.score([doc] * len(target_sents), list(target_sents))
            return [float(x) for x in res["scores"]]

    return _SummaCScorer()
