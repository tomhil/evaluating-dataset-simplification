"""`sample_pairs` moved to profiler.sampling unchanged and is re-exported by run."""

from profiler import run, sampling
from profiler.types import Pair
from tests.conftest import make_config


def test_reexported_from_run():
    assert run.sample_pairs is sampling.sample_pairs


def test_seeded_sample_is_stable():
    pairs = [Pair(str(i), "s", "t") for i in range(50)]
    cfg = make_config(sample_size=7)
    a = sampling.sample_pairs(pairs, cfg)
    assert len(a) == 7 and a == sampling.sample_pairs(pairs, cfg)
    assert [p.id for p in a] == sorted((p.id for p in a), key=int)
    assert sampling.sample_pairs(pairs, make_config(sample_size=None)) is pairs
