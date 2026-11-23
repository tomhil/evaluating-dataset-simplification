"""Controls, sensitivity and stability checks (plan sections 5 and 6)."""

from __future__ import annotations

import math

import numpy as np
import pandas as pd

from . import catalog as cat
from . import stats as st


def beating_labelings(values: dict[str, float]) -> list[list[str]]:
    """The relabelings whose |theta| is at least the observed one, each given
    as the corpora it calls SUM. The observed labeling is always among them."""

    vals = {c: values[c] for c in cat.LABELLED if c in values and np.isfinite(values[c])}
    obs = st.theta(vals, cat.FAMILY, cat.DOMAIN_OF, "SIMP", "SUM")[0]
    out = []
    for lab in st.stratified_labelings(list(vals), cat.FAMILY, cat.DOMAIN_OF):
        if abs(st.theta(vals, lab, cat.DOMAIN_OF, "SIMP", "SUM")[0]) >= abs(obs) - 1e-12 * max(1, abs(obs)):
            out.append(sorted(c for c in vals if lab[c] == "SUM"))
    return out


def sesoi_sensitivity(t2: pd.DataFrame, sigma: dict[str, float], frames, delta_of) -> pd.DataFrame:
    """Outcome counts and, for the paired pre-specified features, replicability
    counts under SESOI 0.05 / 0.1 / 0.2 suite SD."""

    rows = []
    lab = t2[t2["corpus"].isin(cat.LABELLED) & ~t2["structural"]]
    for s in (0.05, 0.1, 0.2):
        oc = [st.outcome(lo, hi, s * sigma[f]) for lo, hi, f in zip(lab["hl_lo90"], lab["hl_hi90"], lab["feature"])]
        counts = pd.Series(oc).value_counts()
        row = {"sesoi": s, **{k: int(counts.get(k, 0)) for k in ("up", "down", "equiv", "unclear")}}
        for pid, name, kind, _ in cat.CONFIRMATORY:
            if kind != "paired":
                continue
            f = next(x for x in cat.PAIRED if x.name == name)
            for fam in ("SIMP", "SUM"):
                ps_up, ps_dn = [], []
                for c in cat.LABELLED:
                    if cat.FAMILY[c] != fam:
                        continue
                    d = delta_of(frames[c], f)
                    ps_up.append(st.wilcoxon_p(d, s * sigma[name], "greater"))
                    ps_dn.append(st.wilcoxon_p(d, -s * sigma[name], "less"))
                row[f"{pid}_{fam}_up"] = st.partial_conjunction_count(ps_up)
                row[f"{pid}_{fam}_down"] = st.partial_conjunction_count(ps_dn)
        rows.append(row)
    return pd.DataFrame(rows)


def seed_stability(res_a: dict, res_b: dict) -> dict:
    """Agreement of two full runs that differ only in the seed. Differences of
    effect sizes are in suite SD units."""

    sig = res_a["sigma"]
    a, b = res_a["t2"], res_b["t2"]
    m = a.merge(b, on=["corpus", "feature"], suffixes=("_a", "_b"))
    t3 = res_a["t3"].merge(res_b["t3"], on=["metric", "kind"], suffixes=("_a", "_b"))
    s3 = t3["metric"].map(sig)
    t4 = res_a["t4"].merge(res_b["t4"], on=["metric", "view"], suffixes=("_a", "_b"))
    ok = t4["p_a"].notna() & t4["p_b"].notna()
    okd = t4["p_domain_a"].notna() & t4["p_domain_b"].notna()
    conf = t3["confirmatory_a"]
    crossing = t4.loc[ok & ((t4["p_a"] <= 0.05) != (t4["p_b"] <= 0.05)), ["metric", "view", "p_a", "p_b"]]
    return {
        "paired_outcomes_identical_share": float((m["outcome_a"] == m["outcome_b"]).mean()),
        "theta_and_exact_p_identical": bool(np.allclose(t3["theta_a"], t3["theta_b"], equal_nan=True)
                                            and np.allclose(t3["p_exact_a"], t3["p_exact_b"], equal_nan=True)),
        "max_abs_diff_theta_ci_bound_sd": float(np.nanmax(np.r_[(t3["theta_lo_a"] - t3["theta_lo_b"]).abs() / s3,
                                                                 (t3["theta_hi_a"] - t3["theta_hi_b"]).abs() / s3])),
        "prespecified_holm_identical": bool(np.allclose(t3.loc[conf, "p_holm_a"], t3.loc[conf, "p_holm_b"])),
        "max_abs_diff_omega2_task": float((t4["omega2_task_a"] - t4["omega2_task_b"]).abs().max()),
        "max_abs_diff_partition_p": float((t4.loc[ok, "p_a"] - t4.loc[ok, "p_b"]).abs().max()),
        "max_abs_diff_domain_p": float((t4.loc[okd, "p_domain_a"] - t4.loc[okd, "p_domain_b"]).abs().max())
        if okd.any() else math.nan,
        "partition_p_crossing_0.05": int(len(crossing)),
        "crossing": "; ".join(f"{r.metric}/{r.view} ({r.p_a:.3f} vs {r.p_b:.3f})" for r in crossing.itertuples()),
        "largest_partition_p_moves": "; ".join(
            f"{r.metric}/{r.view} ({r.p_a:.3f} vs {r.p_b:.3f})"
            for r in t4.loc[ok].assign(dp=(t4["p_a"] - t4["p_b"]).abs()).nlargest(6, "dp").itertuples()),
        "profiles": {k: {"p": [v["partition"]["p"], res_b["profiles"][k]["partition"]["p"]],
                         "p_domain": [v["partition"]["p_domain"], res_b["profiles"][k]["partition"]["p_domain"]],
                         "omega2_task": [v["partition"]["omega2_task"], res_b["profiles"][k]["partition"]["omega2_task"]],
                         "omega2_domain": [v["partition"]["omega2_domain"],
                                           res_b["profiles"][k]["partition"]["omega2_domain"]]}
                     for k, v in res_a["profiles"].items() if k in res_b["profiles"]},
    }


SEED_TOL = 0.05  # plan v3, 6: a T4 row is seed-stable when its p, p_domain and omega^2 move by at most this


def attach_seed(t4a: pd.DataFrame, t4b: pd.DataFrame, seed: int) -> pd.DataFrame:
    """Add the check seed's omega^2 and p-values to T4 and flag seed-stable rows:
    |dp|, |dp_domain|, |d omega^2| <= SEED_TOL (NaN on both sides counts as equal)
    and omega^2_task vs omega^2_domain ordered the same way under both seeds."""

    cols = ["omega2_task", "omega2_domain", "p", "p_domain"]
    b = t4b[["metric", "view"] + cols].rename(columns={c: f"{c}_s{seed}" for c in cols})
    m = t4a.merge(b, on=["metric", "view"], how="left")
    ok = pd.Series(True, index=m.index)
    for c in cols:
        x, y = m[c].astype(float), m[f"{c}_s{seed}"].astype(float)
        same_nan = x.isna() & y.isna()
        ok &= same_nan | ((x - y).abs() <= SEED_TOL)
    order_a = m["omega2_task"] > m["omega2_domain"]
    order_b = m[f"omega2_task_s{seed}"] > m[f"omega2_domain_s{seed}"]
    m["seed_stable"] = ok & (order_a == order_b)
    return m


def positive_control(frames, cells: pd.DataFrame) -> dict:
    """XSum vs CNN/DailyMail on novel n-grams, against Narayan et al. (2018)."""

    pc = cat.POSITIVE_CONTROL
    xa = st.finite(frames[pc["a"]][pc["metric"]])
    xb = st.finite(frames[pc["b"]][pc["metric"]])
    n1a = st.finite(1 - frames[pc["a"]]["coverage"])
    n1b = st.finite(1 - frames[pc["b"]]["coverage"])
    a12 = st.vargha_delaney(xa, xb)
    return {"metric": pc["metric"], "a": pc["a"], "b": pc["b"], "median_a": float(np.median(xa)),
            "median_b": float(np.median(xb)), "mean_a": float(xa.mean()), "mean_b": float(xb.mean()),
            "novel_1gram_mean_a": float(n1a.mean()), "novel_1gram_mean_b": float(n1b.mean()),
            "a12": a12, "a12_min": pc["a12_min"], "pass": bool(a12 >= pc["a12_min"]),
            "published": pc["published"]}


def oracle_sentence_diagnostic(frames) -> pd.DataFrame:
    """How much of the oracle's FKGL change is sentence length.

    FKGL = 0.39 * words/sentence + 11.8 * syllables/word - 15.59, so a change
    in words per sentence can be backed out as
        (dFKGL - 11.8 * dSyllablesPerWord) / 0.39.
    It is approximate (textstat rounds FKGL and counts syllables its own way),
    so it is first checked on target - source, where M1 measures the true change
    in mean sentence length: ``validation_rho`` and ``validation_median_err``.
    """

    rows = []
    for c, df in frames.items():
        if "oracle_fkgl" not in df.columns:
            continue
        implied_ts = ((df["tgt_fkgl"] - df["src_fkgl"]) - 11.8 * (df["tgt_syllables_per_word"]
                                                                  - df["src_syllables_per_word"])) / 0.39
        true_ts = df["mean_tgt_sent_len"] - df["mean_src_sent_len"]
        ok = implied_ts.notna() & true_ts.notna()
        rho = float(implied_ts[ok].corr(true_ts[ok], method="spearman")) if ok.sum() > 20 else math.nan
        implied_os = ((df["oracle_fkgl"] - df["src_fkgl"]) - 11.8 * (df["oracle_syllables_per_word"]
                                                                    - df["src_syllables_per_word"])) / 0.39
        rows.append({"corpus": c, "family": cat.FAMILY.get(c, "-"),
                     "validation_rho": rho,
                     "validation_median_err": float((implied_ts[ok] - true_ts[ok]).median()),
                     "median_src_sent_len": float(df["mean_src_sent_len"].median()),
                     "median_implied_oracle_minus_source_wps": float(implied_os.median()),
                     "median_true_target_minus_source_wps": float(true_ts.median()),
                     "median_oracle_minus_source_fkgl": float((df["oracle_fkgl"] - df["src_fkgl"]).median())})
    return pd.DataFrame(rows)
