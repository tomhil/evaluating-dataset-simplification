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

import functools

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

    def words_fast(self, text: str) -> list[str]:
        """Same tokens as :meth:`words`, without running the pipeline.

        For callers that need only token strings -- n-gram counts, token
        totals -- and none of the POS/dependency annotation. Token boundaries
        are set by the tokenizer, and ``is_space``/``is_punct`` are lexeme
        attributes, so no pipeline component can change this result. Verified
        against :meth:`words` on 10,217 sentences from PLOS, Cochrane,
        CNN/DailyMail and XSum: zero mismatches.

        This exists because ``_ext_oracle_k`` and ``_lead_k`` call it once per
        *source sentence*, which is a cache miss per sentence: profiling ten
        PLOS articles showed 2,844 full pipeline runs taking 8.3 of the
        oracle's 8.6 seconds.
        """
        ...

    def content_words(self, text: str) -> list[str]: ...

    def analyze_sentence(self, sent: str) -> list[Token]: ...

    def release(self) -> None:
        """Drop any cached parses. Part of the contract: run.py calls it."""
        ...


class SimpleProcessor:
    """Regex-based, dependency-free processor. No syntactic parsing."""

    has_parser = False

    def sentences(self, text: str) -> list[str]:
        return [s.strip() for s in _SENT_RE.findall(text) if s.strip()]

    def words(self, text: str) -> list[str]:
        return _WORD_RE.findall(text)

    def words_fast(self, text: str) -> list[str]:
        # No pipeline to skip.
        return self.words(text)

    def content_words(self, text: str) -> list[str]:
        return [w for w in self.words(text) if w.lower() not in _STOPWORDS and not w.isdigit()]

    def release(self) -> None:
        """No cache to drop; present so callers need not know which processor."""

    def analyze_sentence(self, sent: str) -> list[Token]:
        toks = []
        for i, w in enumerate(self.words(sent)):
            is_content = w.lower() not in _STOPWORDS and not w.isdigit()
            toks.append(
                Token(text=w, lemma=w.lower(), pos="", is_content=is_content, i=i)
            )
        return toks


_DOC_CACHE = 64


class SpacyProcessor:
    """spaCy-backed processor exposing the full syntactic feature set."""

    has_parser = True

    def __init__(self, model: str = "en_core_web_sm"):
        import spacy

        self._nlp = spacy.load(model, disable=["ner"])
        # Each accessor used to run the full pipeline, so M3 parsed the same
        # document about twenty times per pair -- on the full corpus, not the
        # sample.
        #
        # The cache is shared with analyze_sentence, which runs once per
        # sentence, so it has to hold a document *and* its sentences to be
        # useful: at 8 slots a document of 7+ sentences evicted itself before
        # being reused. Replaying M3's per-pair sequence on a 20-sentence source
        # and 10-sentence target: 8 slots gave 54 pipeline runs per pair, 64
        # gave 32. Bound to the instance rather than module-level, so a corpus
        # sweep retains a working set rather than one Doc per document.
        # Keyed on the text itself and bound to this instance. Note the cache
        # holds spaCy Doc objects, which are large on long sources, and
        # get_processor is itself module-level lru_cached -- so without
        # release() the working set survives for the process lifetime, through
        # M4-M6, long after M3 has finished with it. run.py calls release()
        # between modules.
        # One cache, shared by the document-level accessors and
        # analyze_sentence. Splitting it into separate document and sentence
        # caches was tried on the hypothesis that long sources evict their own
        # Doc: measured on 15 PLOS articles (6,800 words each) it made no
        # difference (36.4s split vs 36.0s shared) and lowered the document hit
        # rate, because _lead_k and _ext_oracle_k call words() per *sentence*,
        # so sentence-level lookups land in the document cache either way. On
        # D-Wikipedia the split was slower (108s vs 92s). Keeping it simple.
        self._doc = functools.lru_cache(maxsize=_DOC_CACHE)(self._parse)

    def _parse(self, text: str):
        return self._nlp(text)

    def release(self) -> None:
        """Drop cached parses. Safe to call at any point; costs a re-parse."""
        self._doc.cache_clear()

    def sentences(self, text: str) -> list[str]:
        doc = self._doc(text)
        return [s.text.strip() for s in doc.sents if s.text.strip()]

    def words(self, text: str) -> list[str]:
        return [t.text for t in self._doc(text) if not t.is_space and not t.is_punct]

    def words_fast(self, text: str) -> list[str]:
        return [
            t.text
            for t in self._nlp.tokenizer(text)
            if not t.is_space and not t.is_punct
        ]

    def content_words(self, text: str) -> list[str]:
        out = []
        for t in self._doc(text):
            if t.is_space or t.is_punct or t.is_stop:
                continue
            if t.pos_ in {"NOUN", "PROPN", "VERB", "ADJ", "ADV"}:
                out.append(t.text)
        return out

    def analyze_sentence(self, sent: str) -> list[Token]:
        doc = self._doc(sent)
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

    Raises for any language other than English. This argument used to be
    accepted and ignored -- every call returned ``en_core_web_sm`` -- so the
    documented "non-English corpora get M1/M2/M4" path would have segmented,
    tokenised and stopword-filtered other languages as English and published
    the results without comment.
    """

    lang = (language or "en").lower().split("-")[0].split("_")[0]
    if lang != "en":
        raise ValueError(
            f"unsupported language '{language}': the only processor is English "
            f"(en_core_web_sm). Using it on other text invalidates segmentation, "
            f"tokenisation and stopword handling for every module."
        )

    if prefer_spacy:
        try:
            return SpacyProcessor()
        except Exception as exc:  # pragma: no cover - environment dependent
            warnings.warn(
                f"spaCy model unavailable ({exc}); falling back to SimpleProcessor. "
                "SimpleProcessor splits sentences on every period, so decimals and "
                "abbreviations ('OR 0.61, 95% CI 0.46 to 0.79') each become several "
                "sentences -- the exact behaviour _normalise_for_textstat exists to "
                "undo. All six M3a formulas and M1's sentence counts will read "
                "easier than the text is. "
                "Syntactic M3b features (dependency distance, parse depth, "
                "passive/subordinate rates) will be reported as null.",
                RuntimeWarning,
                stacklevel=2,
            )
    return SimpleProcessor()
