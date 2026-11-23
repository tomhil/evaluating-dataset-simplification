# Progress log: Cross-Corpus Comparison

Loop log for `PRD Cross-Corpus Comparison.md`. One entry per iteration, using the template in Section 9 of the PRD.

Starting point: branch `analysis/cross-corpus-comparison`, one commit on `main` at `ed58b86`, made in a cloud
session on 2026-11-23. It holds the `analysis/` package (implementation of `docs/analysis-plan.md` v3), the
reference outputs of a production run on byte-identical copies of the 26 per-pair files in `runs/`
(`analysis/reference/`), the plan, this PRD, this log and `run-loop-cross-corpus.sh`. No tests for `analysis/` yet;
`analysis/out/` does not exist. The repository's own test suite was not run in the cloud session (no project
`venv`); item A1 records it.
