#!/usr/bin/env bash
# Runs "PRD Cross-Corpus Comparison" unattended: one Section 7 item per fresh
# Claude Code session, in auto mode, until every item is done or one is blocked.
# It never pushes. At the end it prints a summary and shows a macOS notification.
#
# Usage, from the repo root, with the project's Python environment present (venv/):
#   git fetch origin && git checkout analysis/cross-corpus-comparison
#   caffeinate -i "docs/plans for loop/run-loop-cross-corpus.sh"
# (caffeinate keeps the Mac awake while it runs; Ctrl+C stops it.)

set -u
cd "$(git rev-parse --show-toplevel)" || exit 1

BRANCH="analysis/cross-corpus-comparison"
PRD="docs/plans for loop/PRD Cross-Corpus Comparison.md"
PROGRESS="docs/plans for loop/progress-cross-corpus-comparison.md"
RUNLOG="$HOME/prd-loop-cross-corpus-$(date +%Y%m%d-%H%M).log"
MAX_ITERATIONS=16

if [ "$(git branch --show-current)" != "$BRANCH" ]; then
  echo "Check out $BRANCH first." >&2
  exit 1
fi
if [ ! -d runs ] || [ ! -x venv/bin/python ]; then
  echo "Expected runs/ and venv/bin/python in the repo root." >&2
  exit 1
fi

PROMPT='You are running unattended: nobody can answer questions, and you must never push.
Read "docs/plans for loop/PRD Cross-Corpus Comparison.md" and "docs/plans for loop/progress-cross-corpus-comparison.md". Follow the hard rules in Section 0, and read docs/analysis-plan.md where the item needs the method.
Do exactly one item: the next unfinished item in Section 7 (the PRD, plan, runner, code and reference outputs are already committed, so item A1 is just recording the starting status).
Where a Section 6 gate has a default, apply it and record it. Never run the production analysis in the foreground: start analysis/run_production.sh in the background and poll, as Section 5.3 says.
Commit the item and add its progress-log entry using the Section 9 template, then stop.
End your reply with exactly one of these lines:
STATUS: CONTINUE   (the item is committed and pytest shows no failure beyond the A1 baseline)
STATUS: BLOCKED    (you stopped on a DEFERRED question, a failing gate or control, or a gate without a default; say why above)
STATUS: ALL_DONE   (item E11 is complete, or was already complete when you started)'

status="STOPPED after $MAX_ITERATIONS iterations"
for i in $(seq 1 "$MAX_ITERATIONS"); do
  echo "=== Iteration $i, $(date '+%Y-%m-%d %H:%M') ===" | tee -a "$RUNLOG"
  out=$(claude -p "$PROMPT" --permission-mode auto --permission-prompts none 2>>"$RUNLOG")
  printf '%s\n' "$out" | tee -a "$RUNLOG"
  case "$out" in
    *"STATUS: CONTINUE"*) ;;
    *"STATUS: ALL_DONE"*) status="ALL DONE"; break ;;
    *"STATUS: BLOCKED"*)  status="BLOCKED (see the last progress-log entry)"; break ;;
    *) status="STOPPED: no status line in the reply (see $RUNLOG)"; break ;;
  esac
done

{
  echo
  echo "===== PRD loop result: $status ====="
  echo
  echo "Commits on $BRANCH since main:"
  git log --oneline main..HEAD
  echo
  echo "Last progress-log entry:"
  awk '/^## /{buf=""} {buf=buf $0 "\n"} END{printf "%s", buf}' "$PROGRESS"
  echo
  echo "Full transcript: $RUNLOG"
} | tee -a "$RUNLOG"

osascript -e "display notification \"$status\" with title \"PRD loop finished\"" >/dev/null 2>&1 || true
