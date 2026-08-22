"""Text processing: tokenization, sentence splitting, and (optionally) parsing.

Two implementations share one interface:

* ``SpacyProcessor`` wraps ``en_core_web_sm`` and exposes the full feature set
  (dependency distance, parse-tree depth, POS, passive/subordinate detection).
* ``SimpleProcessor`` is a dependency-free regex fallback used when spaCy is
  unavailable and injected directly in tests. It provides tokenization,
  sentence splitting and stopword-based content-word detection, but reports
  ``has_parser = False`` so syntactic features degrade to ``None`` rather than
  producing invalid numbers.

Modules always go through :func:`get_processor`; nothing imports spaCy directly.
"""

from __future__ import annotations

import re
import warnings
from dataclasses import dataclass
from functools import lru_cache
from typing import Protocol

_WORD_RE = re.compile(r"[A-Za-z0-9]+(?:['-][A-Za-z0-9]+)*")
_SENT_RE = re.compile(r"[^.!?]+[.!?]*", re.DOTALL)

# A compact stopword list for the fallback content-word filter. The spaCy
# processor uses its own is_stop / POS instead.
_STOPWORDS = frozenset(
    """a an the and or but if then else of to in on at by for with without from
    into onto up down over under again further once here there all any both each
    few more most other some such no nor not only own same so than too very s t
    can will just don should now is are was were be been being have has had do
    does did doing this that these those i you he she it we they them his her its
    our their my your as about above below between out off through during before
    after who whom which what whose when where why how""".split()
)


@dataclass
class Token:
    text: str
    lemma: str
    pos: str
    is_content: bool
    dep: str = ""
    head_i: int = -1
    i: int = -1


class Processor(Protocol):
    has_parser: bool

    def sentences(self, text: str) -> list[str]: ...

    def words(self, text: str) -> list[str]: ...

    def content_words(self, text: str) -> list[str]: ...

    def analyze_sentence(self, sent: str) -> list[Token]: ...


class SimpleProcessor:
    """Regex-based, dependency-free processor. No syntactic parsing."""

    has_parser = False

    def sentences(self, text: str) -> list[str]:
        return [s.strip() for s in _SENT_RE.findall(text) if s.strip()]

    def words(self, text: str) -> list[str]:
        return _WORD_RE.findall(text)

    def content_words(self, text: str) -> list[str]:
        return [w for w in self.words(text) if w.lower() not in _STOPWORDS and not w.isdigit()]

    def analyze_sentence(self, sent: str) -> list[Token]:
        toks = []
        for i, w in enumerate(self.words(sent)):
            is_content = w.lower() not in _STOPWORDS and not w.isdigit()
            toks.append(
                Token(text=w, lemma=w.lower(), pos="", is_content=is_content, i=i)
            )
        return toks


class SpacyProcessor:
    """spaCy-backed processor exposing the full syntactic feature set."""

    has_parser = True

    def __init__(self, model: str = "en_core_web_sm"):
        import spacy

        self._nlp = spacy.load(model, disable=["ner"])

    def sentences(self, text: str) -> list[str]:
        doc = self._nlp(text)
        return [s.text.strip() for s in doc.sents if s.text.strip()]

    def words(self, text: str) -> list[str]:
        return [t.text for t in self._nlp(text) if not t.is_space and not t.is_punct]

    def content_words(self, text: str) -> list[str]:
        out = []
        for t in self._nlp(text):
            if t.is_space or t.is_punct or t.is_stop:
                continue
            if t.pos_ in {"NOUN", "PROPN", "VERB", "ADJ", "ADV"}:
                out.append(t.text)
        return out

    def analyze_sentence(self, sent: str) -> list[Token]:
        doc = self._nlp(sent)
        toks = []
        for t in doc:
            if t.is_space:
                continue
            toks.append(
                Token(
                    text=t.text,
                    lemma=t.lemma_.lower(),
                    pos=t.pos_,
                    is_content=(
                        (not t.is_stop)
                        and (not t.is_punct)
                        and t.pos_ in {"NOUN", "PROPN", "VERB", "ADJ", "ADV"}
                    ),
                    dep=t.dep_,
                    head_i=t.head.i,
                    i=t.i,
                )
            )
        return toks


@lru_cache(maxsize=4)
def get_processor(language: str = "en", prefer_spacy: bool = True) -> Processor:
    """Return a processor for ``language``.

    Attempts spaCy first (required for the syntactic M3b features); falls back to
    :class:`SimpleProcessor` with a warning if the model cannot be loaded. Cached
    so a single model is shared across modules within a run.
    """

    if prefer_spacy:
        try:
            return SpacyProcessor()
        except Exception as exc:  # pragma: no cover - environment dependent
            warnings.warn(
                f"spaCy model unavailable ({exc}); falling back to SimpleProcessor. "
                "Syntactic M3b features (dependency distance, parse depth, "
                "passive/subordinate rates) will be reported as null.",
                RuntimeWarning,
                stacklevel=2,
            )
    return SimpleProcessor()
