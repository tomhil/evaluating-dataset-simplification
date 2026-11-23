#!/usr/bin/env bash
# Production run of the cross-corpus comparison (PRD items D7 and D9).
# Runs in a few minutes; start it in the background and poll, because one
# Claude Code tool call is capped at 10 minutes:
#   nohup analysis/run_production.sh >/dev/null 2>&1 &
#   cat analysis/out/EXIT_STATUS    # "<exit code> <seconds>" once finished
# Exit code 0 = ok; 2-5 = a gate stopped the run (see analysis/run.py).
set -u
cd "$(git rev-parse --show-toplevel)" || exit 1
OUT="${1:-analysis/out}"
PY="${PYTHON:-venv/bin/python}"
mkdir -p "$OUT"
rm -f "$OUT/EXIT_STATUS"
start=$(date +%s)
"$PY" -m analysis.run --runs runs --out "$OUT" --profile production --seed 13 --check-seed 14 >"$OUT/run.log" 2>&1
status=$?
echo "$status $(( $(date +%s) - start ))" >"$OUT/EXIT_STATUS"
exit "$status"
