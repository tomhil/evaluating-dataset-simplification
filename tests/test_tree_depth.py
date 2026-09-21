"""Parse-tree depth must not be bounded by Python's recursion limit.

Real corpora contain "sentences" that are flattened lists or tables -- SWiPE has
one of 2,340 tokens -- and a recursive walk up the dependency chain overflows
the interpreter's 1,000-frame stack long before the data runs out.
"""

import pytest

from profiler.modules.m3_readability import _tree_depth


def _chain(n: int, deepest_first: bool) -> dict[int, int]:
    """Node i attaches to i-1; node 0 is its own head (the root).

    Insertion order decides whether the walk is cheap or catastrophic. Iterating
    from the root outwards fills the memo bottom-up and never nests; iterating
    from the deepest node inwards recurses the full length of the chain before
    it finds anything cached. spaCy emits tokens in sentence order, which is the
    second case whenever the head chain runs right-to-left.
    """
    order = range(n - 1, -1, -1) if deepest_first else range(n)
    return {i: (i - 1 if i else 0) for i in order}


def test_deep_chain_does_not_overflow_the_stack():
    n = 5000  # comfortably past sys.getrecursionlimit()
    assert _tree_depth(_chain(n, deepest_first=True)) == n - 1


def test_deep_chain_root_first_order():
    n = 5000
    assert _tree_depth(_chain(n, deepest_first=False)) == n - 1


def test_shallow_tree_still_correct():
    # 0 is root; 1 and 2 hang off it; 3 hangs off 1.
    assert _tree_depth({0: 0, 1: 0, 2: 0, 3: 1}) == 2


def test_single_node_and_empty():
    assert _tree_depth({0: 0}) == 0
    assert _tree_depth({}) == 0


def test_cycle_terminates():
    """A malformed parse must return, not spin."""
    assert _tree_depth({0: 1, 1: 2, 2: 0}) is not None


def test_head_outside_the_map_is_treated_as_root():
    assert _tree_depth({5: 99, 6: 5}) == 1
