"""Torch device selection for the optional model-based metrics.

Moved here from ``profiler/embeddings.py`` when the SBERT embedder was removed
(October 2026 metric revision, gate G5). Used by M8's BERTScore, the models in
``profiler/model_metrics.py``, and nothing else.
"""

from __future__ import annotations


def resolve_device(requested: str = "auto") -> str:
    """Map 'auto' onto the best available torch device.

    An explicit value is honoured as given so a run can be pinned to cpu for
    cross-machine reproducibility.
    """
    if requested != "auto":
        return requested
    try:
        import torch
    except ImportError:
        return "cpu"
    if torch.cuda.is_available():
        return "cuda"
    if torch.backends.mps.is_available():
        return "mps"
    return "cpu"
