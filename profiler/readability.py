"""Readability primitives used by M3.

Surface formulas come from ``textstat`` (a pure-Python, offline-at-runtime
dependency). Length-invariant measures (Zipf frequency, rare-word rate, lexical
diversity) are implemented here so they are deterministic and do not depend on
formula libraries.
"""

from __future__ import annotations

import re
from functools import lru_cache

_VOWEL_GROUP = re.compile(r"[aeiouy]+", re.IGNORECASE)

SURFACE_MEASURES = ["fkgl", "dcrs", "cli", "fre", "ari", "smog"]


def _textstat():
    try:
        import textstat as _ts

        return _ts
    except ImportError as exc:  # pragma: no cover - environment dependent
        raise ImportError(
            "M3 readability requires 'textstat' (pip install textstat)"
        ) from exc


def surface_scores(text: str) -> dict[str, float | None]:
    """FKGL, Dale-Chall (DCRS), Coleman-Liau (CLI), Flesch Reading Ease (FRE),
    ARI, and SMOG for one text. ``None`` for empty text."""

    if not text or not text.strip():
        return {m: None for m in SURFACE_MEASURES}
    ts = _textstat()
    return {
        "fkgl": float(ts.flesch_kincaid_grade(text)),
        "dcrs": float(ts.dale_chall_readability_score(text)),
        "cli": float(ts.coleman_liau_index(text)),
        "fre": float(ts.flesch_reading_ease(text)),
        "ari": float(ts.automated_readability_index(text)),
        "smog": float(ts.smog_index(text)),
    }


def count_syllables(word: str) -> int:
    """Heuristic syllable count (vowel groups, silent-e adjustment)."""

    w = word.lower().strip()
    if not w:
        return 0
    groups = _VOWEL_GROUP.findall(w)
    n = len(groups)
    if w.endswith("e") and not w.endswith(("le", "ie", "ee", "ye")) and n > 1:
        n -= 1
    return max(1, n)


def syllables_per_word(words: list[str]) -> float | None:
    if not words:
        return None
    return sum(count_syllables(w) for w in words) / len(words)


@lru_cache(maxsize=1)
def _top3000() -> frozenset[str]:
    try:
        from wordfreq import top_n_list

        return frozenset(top_n_list("en", 3000))
    except ImportError:  # pragma: no cover - environment dependent
        return frozenset()


def mean_zipf(content_words: list[str]) -> float | None:
    """Mean Zipf frequency of content words (higher = more common/easier)."""

    if not content_words:
        return None
    try:
        from wordfreq import zipf_frequency
    except ImportError as exc:  # pragma: no cover - environment dependent
        raise ImportError("M3b requires 'wordfreq' (pip install wordfreq)") from exc
    vals = [zipf_frequency(w.lower(), "en") for w in content_words]
    return sum(vals) / len(vals)


def rare_word_rate(content_words: list[str]) -> float | None:
    """Proportion of content tokens outside the top-3000 frequency band."""

    if not content_words:
        return None
    top = _top3000()
    if not top:  # pragma: no cover - environment dependent
        raise ImportError("M3b rare_word_rate requires 'wordfreq'")
    outside = sum(1 for w in content_words if w.lower() not in top)
    return outside / len(content_words)


def mtld(tokens: list[str], threshold: float = 0.72) -> float | None:
    """Measure of Textual Lexical Diversity (McCarthy & Jarvis 2010).

    Length-robust unlike raw TTR. Returns ``None`` for texts too short to
    produce a single factor.
    """

    tokens = [t.lower() for t in tokens]
    if len(tokens) < 10:
        return None

    def _one_pass(seq: list[str]) -> float:
        factors = 0.0
        types: set[str] = set()
        count = 0
        for tok in seq:
            types.add(tok)
            count += 1
            ttr = len(types) / count
            if ttr <= threshold:
                factors += 1
                types = set()
                count = 0
        if count > 0:
            # Partial factor for the trailing segment.
            ttr = len(types) / count
            denom = 1 - threshold
            factors += (1 - ttr) / denom if denom > 0 else 0
        return len(seq) / factors if factors > 0 else float("nan")

    forward = _one_pass(tokens)
    backward = _one_pass(list(reversed(tokens)))
    vals = [v for v in (forward, backward) if v == v]  # drop NaN
    if not vals:
        return None
    return sum(vals) / len(vals)


def jargon_rate(content_words: list[str], terms: list[str]) -> float | None:
    """Rate of content tokens matching a configurable domain-term list.

    ``None`` when no term list is supplied (the measure is undefined, not zero).
    """

    if not terms:
        return None
    if not content_words:
        return None
    termset = {t.lower() for t in terms}
    hits = sum(1 for w in content_words if w.lower() in termset)
    return hits / len(content_words)
