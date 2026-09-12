"""The bootstrap must not materialise a resamples x n index matrix.

M5 summarises one score per target sentence and M6 one row per source sentence
pooled across the sample, so n is sentences, not pairs. At eLife scale
(n ~ 600,000) a single `rng.integers(0, n, size=(1000, n))` is ~4.8GB, and
_summarize_features makes 22 such calls.

Chunking must not change any result: numpy fills a (R, n) draw in C order, so
drawing it in row blocks continues the same stream.
"""

import numpy as np

from profiler.stats import bootstrap_ci, summarize


def test_chunking_preserves_the_random_stream():
    """A block-wise draw must equal the monolithic one, element for element."""
    n, R = 400, 1000
    mono = np.random.default_rng(13).integers(0, n, size=(R, n))
    g = np.random.default_rng(13)
    blocks = [g.integers(0, n, size=(min(64, R - s), n)) for s in range(0, R, 64)]
    assert np.array_equal(mono, np.concatenate(blocks))


def test_ci_matches_the_known_previous_values():
    """Locks the output so a future rewrite cannot silently shift a CI."""
    vals = list(range(100))
    got = bootstrap_ci(vals, seed=13, resamples=200)
    # Captured from the pre-chunking implementation before this change.
    assert [round(x, 6) for x in got] == [44.42625, 55.4255]


def test_peak_allocation_is_bounded_by_the_chunk_not_n():
    """A large n must not allocate proportional to resamples x n."""
    import tracemalloc

    arr = list(np.random.default_rng(0).normal(size=60_000))
    tracemalloc.start()
    bootstrap_ci(arr, seed=13, resamples=200)
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    # Monolithic would be 200 * 60_000 * 8 = 96MB for the index alone.
    assert peak < 40_000_000, f"peak {peak/1e6:.0f}MB suggests an unchunked draw"


def test_degenerate_inputs_unchanged():
    assert bootstrap_ci([], seed=1) == [None, None]
    assert bootstrap_ci([5.0], seed=1) == [5.0, 5.0]


def test_summarize_still_agrees_with_bootstrap_ci():
    vals = [float(x) for x in range(50)]
    s = summarize(vals, seed=7, resamples=100)
    assert s.ci95 == bootstrap_ci(vals, seed=7, resamples=100)
