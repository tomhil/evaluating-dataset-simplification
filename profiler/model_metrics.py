"""Optional model-based literature metrics (M3's ``m3d_model_based`` block, and
M5's and M8's model-based additions).

Every model here follows the ``optional_scorers()`` pattern: imported lazily,
skipped with a note when it cannot load, recorded under a ``*_run`` key, and
emitting ``None`` -- never zero -- for its keys when skipped.

Under the offline smoke settings (``nli_backend: lexical``, or
``heuristic_only``) each metric uses a deterministic stand-in instead of its
model. Stand-in values exist to exercise the plumbing offline; they are flagged
in ``notes`` and in the ``*_run`` record (``"<name>:stand-in"``) and are not the
published metric.
"""

from __future__ import annotations

import re
import warnings
from typing import Callable

_TOK = re.compile(r"[A-Za-z0-9]+")

# Cripwell et al. (2023) released checkpoint for SLE.
SLE_CHECKPOINT = "liamcripwell/sle-base"
# Bommasani & Cardie (2020) use BERT's next-sentence prediction head.
NSP_MODEL = "bert-base-uncased"


def use_stand_ins(config) -> bool:
    """The existing offline smoke settings select the stand-ins."""

    return config.run.nli_backend == "lexical" or bool(config.run.heuristic_only)


def stand_in_reason(config) -> str:
    """Which smoke setting selected the stand-ins, for the notes."""

    return "heuristic_only" if config.run.heuristic_only else "nli_backend=lexical"


def disabled_note(what: str) -> str:
    return f"{what} not computed: run.model_metrics is false, so its model is not loaded; keys are null."


def try_load(name: str, loader: Callable[[], object]) -> tuple[object | None, str | None]:
    """Load an optional model, returning ``(model, note)``.

    Like ``scorers._try_load``: the note records only the exception type, so
    ``metrics.json`` stays byte-identical across machines; details go to stderr.
    """

    try:
        return loader(), None
    except Exception as exc:  # pragma: no cover - environment dependent
        warnings.warn(f"{name} unavailable: {type(exc).__name__}: {exc}", RuntimeWarning, stacklevel=2)
        return None, f"{name} unavailable ({type(exc).__name__}); its metrics are null. See stderr."


def _content(text: str) -> set[str]:
    from .nlp import _STOPWORDS

    return {w.lower() for w in _TOK.findall(text) if w.lower() not in _STOPWORDS and not w.isdigit()}


# --------------------------------------------------------------------------
# SLE (Cripwell et al. 2023): sentence-level simplicity estimate
# --------------------------------------------------------------------------
def load_sle(device: str = "auto"):  # pragma: no cover - model download
    """The released SLE checkpoint, loaded exactly as the reference
    ``sle.scorer.SLEScorer`` does (github.com/liamcripwell/sle): a one-logit
    sequence-classification head, inputs truncated at 128 tokens, the raw logit
    as the score. Loading it through ``transformers`` directly avoids the
    ``sle`` repo's pins (transformers==4.29.1, torch==1.13.1)."""

    import torch
    from transformers import AutoModelForSequenceClassification, AutoTokenizer

    from .embeddings import resolve_device

    dev = resolve_device(device)
    model = AutoModelForSequenceClassification.from_pretrained(SLE_CHECKPOINT, num_labels=1).to(dev).eval()
    tok = AutoTokenizer.from_pretrained(SLE_CHECKPOINT)

    def score(sentences, batch_size: int = 8) -> list[float]:
        out: list[float] = []
        sentences = list(sentences)
        for i in range(0, len(sentences), batch_size):
            batch = tok(sentences[i : i + batch_size], max_length=128, padding=True,
                        truncation=True, add_special_tokens=True, return_tensors="pt").to(dev)
            with torch.no_grad():
                logits = model(**batch, return_dict=True)["logits"]
            out += [float(x.item()) for x in logits]
        return out

    return score


def sle_stand_in(sentences: list[str]) -> list[float]:
    """Offline stand-in on SLE's 0-4 scale: shorter sentences score simpler."""

    return [4.0 - min(4.0, len(_TOK.findall(s)) / 10.0) for s in sentences]


# --------------------------------------------------------------------------
# Semantic coherence (Bommasani & Cardie 2020)
# --------------------------------------------------------------------------
def load_nsp(device: str = "auto"):  # pragma: no cover - model download
    import torch
    from transformers import BertForNextSentencePrediction, BertTokenizer

    from .embeddings import resolve_device

    dev = resolve_device(device)
    tok = BertTokenizer.from_pretrained(NSP_MODEL)
    model = BertForNextSentencePrediction.from_pretrained(NSP_MODEL).to(dev).eval()

    def is_next(first: str, second: str) -> bool:
        enc = tok(first, second, return_tensors="pt", truncation=True, max_length=512).to(dev)
        with torch.no_grad():
            logits = model(**enc).logits
        # Index 0 is "sentence B follows sentence A".
        return int(logits.argmax(dim=-1).item()) == 0

    return is_next


def nsp_stand_in(first: str, second: str) -> bool:
    """Offline stand-in: consecutive sentences 'follow' if they share a content word."""

    return bool(_content(first) & _content(second))


def coherence(sentences: list[str], is_next: Callable[[str, str], bool]) -> float | None:
    """SC(S) = mean over j >= 2 of 1[BERT predicts S_j follows S_{j-1}].

    Bommasani & Cardie average the model's next-sentence *prediction* (an
    indicator), not its probability. None below two sentences.
    """

    sents = [s for s in sentences if s.strip()]
    if len(sents) < 2:
        return None
    hits = sum(1 for a, b in zip(sents, sents[1:]) if is_next(a, b))
    return hits / (len(sents) - 1)


# --------------------------------------------------------------------------
# Document-level faithfulness (M5): SummaC precision/recall, QAFactEval
# --------------------------------------------------------------------------
# QAFactEval could not be installed (see the progress log): its build fails on
# this stack. Its keys stay None with this note until it is installed and wired.
QAFACTEVAL_DEFERRED = (
    "qafacteval_precision/recall not computed: QAFactEval is DEFERRED (its "
    "package fails to build against the core dependencies); keys are null."
)


def load_summac_doc(device: str = "auto"):  # noqa: ARG001 - see below
    """SummaC-Conv as M5's sentence scorer configures it (released weights),
    scoring whole documents: ``score(originals, generateds)`` gives one score
    per (original, generated).

    It reuses the sentence scorer's instance, which runs on cpu, so the model
    is loaded once per run; ``device`` is accepted for symmetry with the other
    loaders and ignored.
    """

    from .scorers import summac_conv_model

    model = summac_conv_model("cpu")
    return lambda original, generated: float(model.score([original], [generated])["scores"][0])


def summac_doc_stand_in(original: str, generated: str) -> float | None:
    """Offline stand-in: mean share of each generated sentence's content words
    found in the original (the lexical_grounding idea at document level)."""

    from .nlp import SimpleProcessor

    orig = _content(original)
    sents = [c for c in (_content(s) for s in SimpleProcessor().sentences(generated)) if c]
    if not sents:
        return None
    return sum(len(c & orig) / len(c) for c in sents) / len(sents)


# --------------------------------------------------------------------------
# Rhetorical roles (Goldsack et al. 2022): PubMed-RCT sentence labels
# --------------------------------------------------------------------------
# A public PubMed-RCT sentence classifier. Its repository ships no tokenizer;
# its vocabulary (31,090) is SciBERT's uncased one, which it was fine-tuned from.
RCT_MODEL = "gubartz/cls_scibert_pubmed_rct"
RCT_TOKENIZER = "allenai/scibert_scivocab_uncased"
RCT_LABELS = ("background", "objective", "methods", "results", "conclusions")
RCT_OFF_DOMAIN = (
    "rhetorical_roles uses a classifier trained on biomedical abstracts "
    "(PubMed-RCT); it is off-domain for news, Wikipedia and legal text."
)


def load_rct(device: str = "auto"):  # pragma: no cover - model download
    import torch
    from transformers import AutoModelForSequenceClassification, AutoTokenizer

    from .embeddings import resolve_device

    dev = resolve_device(device)
    tok = AutoTokenizer.from_pretrained(RCT_TOKENIZER)
    model = AutoModelForSequenceClassification.from_pretrained(RCT_MODEL).to(dev).eval()
    id2label = {int(k): v.lower() for k, v in model.config.id2label.items()}

    def classify(sentences, batch_size: int = 16) -> list[str]:
        out: list[str] = []
        sentences = list(sentences)
        for i in range(0, len(sentences), batch_size):
            enc = tok(sentences[i : i + batch_size], padding=True, truncation=True,
                      max_length=128, return_tensors="pt").to(dev)
            with torch.no_grad():
                pred = model(**enc).logits.argmax(dim=-1).tolist()
            out += [id2label[p] for p in pred]
        return out

    return classify


_RCT_CUES = (
    ("objective", re.compile(r"\b(aim|aimed|objective|purpose|we sought|to evaluate|to assess)\b", re.I)),
    ("conclusions", re.compile(r"\b(suggest|conclude|conclusion|implications?|in summary)\b", re.I)),
    ("methods", re.compile(r"\b(we (used|randomi[sz]ed|recruited|measured|collected)|participants|were assigned)\b", re.I)),
    ("results", re.compile(r"\d")),
)


def rct_stand_in(sentences) -> list[str]:
    """Offline stand-in: keyword cues, defaulting to background."""

    out = []
    for s in sentences:
        out.append(next((label for label, rx in _RCT_CUES if rx.search(s)), "background"))
    return out


def role_shares(labels: list[str]) -> dict[str, float | None]:
    """Share of sentences per PubMed-RCT label; None for an empty text."""

    if not labels:
        return dict.fromkeys(RCT_LABELS)
    return {lab: sum(1 for x in labels if x == lab) / len(labels) for lab in RCT_LABELS}


# --------------------------------------------------------------------------
# Reference-free summary quality (M8): BLANC, SUPERT, SummaQA -- all DEFERRED
# --------------------------------------------------------------------------
# None of the three installs against the core pins (torch>=2.0,
# transformers>=4.35, Python 3.13); the reasons are recorded in the progress log
# and the phase D PR. The PRD forbids reimplementing SummaQA and moving a core
# pin, so their keys are emitted as None with this note until a human installs
# them on the real-run machine.
M8_DEFERRED = {
    "blanc": "BLANC is DEFERRED: blanc 0.3.4 requires torch<2.0 and numpy<2.0, "
             "against the core pin torch>=2.0.",
    "supert": "SUPERT is DEFERRED: the official repository is not an installable "
              "package and pins torch==1.5.0 and pytorch-transformers==1.2.0.",
    "summaqa": "SummaQA is DEFERRED: the official repository requires "
               "transformers==2.1.1, against the core pin transformers>=4.35.",
}
