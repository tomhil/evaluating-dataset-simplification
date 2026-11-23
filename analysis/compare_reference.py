"""Compare a run's outputs with the reference run (PRD item D7).

    python -m analysis.compare_reference analysis/out analysis/reference

Deterministic quantities (per-corpus estimates, outcomes, theta, exact p,
Holm and BH adjustments, location/scale/shape shares, gate, consistency,
positive control) must agree to 1e-9; any difference fails. Seed-dependent
quantities (bootstrap intervals, resampled distances, and the partitions and
Monte-Carlo p-values built on them) are identical when numpy's random streams
match across machines; otherwise their differences are reported, not failed,
because the run's own seed check already measures that variation. Writes
COMPARE_REFERENCE.md into the run directory; exit 0 when the deterministic
quantities agree, 1 otherwise.
"""

from __future__ import annotations

import json
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

EXACT = 1e-9

SPECS = [
    # file, key columns, exact columns, {random column: tolerance kind}
    ("gate.csv", ["corpus", "metric", "stat"], ["recomputed", "ok"], {}),
    ("consistency.csv", ["corpus", "column"], ["max_abs_diff", "nan_mismatch", "status"], {}),
    ("identities.csv", ["corpus"], None, {}),
    ("T2_paired.csv", ["corpus", "feature"],
     ["n", "mean", "hl", "hl_lo90", "hl_hi90", "outcome", "sign_share", "rank_biserial", "p_zero", "p_up",
      "p_down", "std_mean", "std_hl", "defined_rate", "structural", "q_zero_BY"],
     {"mean_lo": "ci_raw", "mean_hi": "ci_raw"}),
    ("T2b_pair_metric_cells.csv", ["corpus", "metric"], None, {}),
    ("T3_synthesis.csv", ["metric", "kind"],
     ["theta", "theta_std", "p_exact", "rank", "n_labelings", "contrast_biomedical", "contrast_legal",
      "contrast_encyclopedia", "contrast_news", "domains_agree", "loo_min", "loo_max", "loo_sign_stable",
      "theta_no_subdoc", "p_no_subdoc", "SIMP_mean", "SUM_mean", "SIMP_pi_lo", "SIMP_pi_hi", "SUM_pi_lo",
      "SUM_pi_hi", "SIMP_n_up", "SIMP_n_down", "SUM_n_up", "SUM_n_down", "q_BH", "p_holm", "confirmatory"],
     {"theta_lo": "ci_theta", "theta_hi": "ci_theta"}),
    ("T4_distributions.csv", ["metric", "view"],
     ["n_common", "n_corpora", "model_based_level", "share_location", "share_scale", "share_shape", "n_labelings"],
     {"floor_rms": "sd", "between_rms": "sd", "omega2_task": "omega", "omega2_domain": "omega",
      "p": "p", "p_domain": "p", "dwiki_swipe": "sd", "xsum_cnndm": "sd", "swipe_vs_gold": "sd"}),
    ("S1_oracle_synthesis.csv", ["metric", "kind"], ["theta", "p_exact", "rank"], {}),
]


def _equal(a: pd.Series, b: pd.Series) -> pd.Series:
    if pd.api.types.is_numeric_dtype(a) and pd.api.types.is_numeric_dtype(b):
        x, y = a.to_numpy(float), b.to_numpy(float)
        both_nan = np.isnan(x) & np.isnan(y)
        return pd.Series(both_nan | (np.abs(x - y) <= EXACT * np.maximum(1.0, np.abs(y))), index=a.index)
    return a.astype(str) == b.astype(str)


def compare(run_dir: Path, ref_dir: Path) -> tuple[bool, list[str]]:
    lines, ok_all = [], True
    sigma = pd.read_csv(ref_dir / "T1_metric_structure.csv").set_index("metric")["sigma"]
    for fname, keys, exact, rand in SPECS:
        a, b = pd.read_csv(run_dir / fname), pd.read_csv(ref_dir / fname)
        if fname == "gate.csv":  # sources differ by machine (metrics.json vs results/); values must not
            a, b = a.drop(columns="source", errors="ignore"), b.drop(columns="source", errors="ignore")
            ok = bool(a["ok"].all()) and bool(b["ok"].all())
            m = a.merge(b, on=keys, suffixes=("_run", "_ref"))
            same = _equal(m["recomputed_run"], m["recomputed_ref"]).all() and len(m) == len(b)
            lines.append(f"- {fname}: all checks pass in both: {ok}; recomputed values identical on "
                         f"{len(m)} shared checks: {bool(same)}")
            ok_all &= ok and bool(same)
            continue
        m = a.merge(b, on=keys, how="outer", suffixes=("_run", "_ref"), indicator=True)
        if (m["_merge"] != "both").any():
            lines.append(f"- {fname}: row sets differ ({int((m['_merge'] != 'both').sum())} rows)")
            ok_all = False
            continue
        cols = exact if exact is not None else [c for c in b.columns if c not in keys]
        bad = [c for c in cols if c in b.columns and not _equal(m[f"{c}_run"], m[f"{c}_ref"]).all()]
        worst = {}
        for c, kind in rand.items():
            if c not in b.columns:
                continue
            x, y = m[f"{c}_run"].to_numpy(float), m[f"{c}_ref"].to_numpy(float)
            d = np.abs(x - y)
            if kind in ("ci_raw", "ci_theta"):
                metric_col = "feature" if "feature" in m.columns else "metric"
                d = d / m[metric_col].map(sigma).to_numpy(float)
            worst[c] = float(np.nanmax(d)) if np.isfinite(d).any() else 0.0
        status = "deterministic columns identical" if not bad else "DIFFERS: " + ", ".join(bad)
        if worst:
            same = all(v <= EXACT for v in worst.values())
            status += ("; seed-dependent columns identical (random streams match)" if same else
                       "; seed-dependent columns differ (informational, not a failure; see the run's own seed "
                       "check): " + ", ".join(f"{k} {v:.3f}" for k, v in worst.items()))
        lines.append(f"- {fname}: {len(m)} rows; {status}")
        ok_all &= not bad
        if fname == "T4_distributions.csv":
            ok_rows = m["p_run"].notna() & m["p_ref"].notna()
            cross = m[ok_rows & ((m["p_run"] <= 0.05) != (m["p_ref"] <= 0.05))]
            lines.append(f"  - task p crossing 0.05 between run and reference: {len(cross)}"
                         + (" (" + "; ".join(f"{r.metric}/{r.view}" for r in cross.itertuples()) + ")" if len(cross)
                            else ""))
    pa = json.loads((run_dir / "C_positive_control.json").read_text())
    pb = json.loads((ref_dir / "C_positive_control.json").read_text())
    same_pc = all(abs(pa[k] - pb[k]) <= EXACT for k in ("a12", "mean_a", "mean_b", "median_a", "median_b"))
    lines.append(f"- C_positive_control.json: identical: {same_pc}; pass in run: {pa['pass']}")
    ok_all &= same_pc and bool(pa["pass"])
    return ok_all, lines


def main() -> None:
    warnings.simplefilter("ignore", pd.errors.PerformanceWarning)
    run_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("analysis/out")
    ref_dir = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("analysis/reference")
    ok, lines = compare(run_dir, ref_dir)
    text = "\n".join([f"# Comparison of `{run_dir}` with `{ref_dir}`", "", *lines, "",
                      f"**Result: {'AGREES' if ok else 'DIFFERS'}** (deterministic quantities compared to {EXACT})", ""])
    (run_dir / "COMPARE_REFERENCE.md").write_text(text, encoding="utf-8")
    print(text)
    raise SystemExit(0 if ok else 1)


if __name__ == "__main__":
    main()
