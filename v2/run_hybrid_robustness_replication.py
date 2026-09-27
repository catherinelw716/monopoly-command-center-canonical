"""V2-0006D: backward temporal robustness replication for the global hybrid.

Research-only. Architecture frozen from V2-0006C. Evaluates 2010-2019 held-out
seasons with wider synthetic target-line offsets from -3 to +3 points.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from statistics import NormalDist

import nflreadpy as nfl
import numpy as np
import pandas as pd
import polars as pl

from build_historical_dataset import normalize_schedule_core
from run_first_experiment import bootstrap_mean_ci

OFFSETS = np.arange(-3.0, 3.0 + 0.001, 0.5)
MIN_TRAIN_SEASONS = 4
SHRINK = [25.0, 75.0]
NORMAL = NormalDist()
EPS = 1e-12


def load_games(start_season: int, end_season: int) -> pd.DataFrame:
    parts: list[pl.DataFrame] = []
    for season in range(start_season, end_season + 1):
        print(f"[data] season {season}: schedules")
        raw = nfl.load_schedules([season])
        g = normalize_schedule_core(raw)
        if "game_type" in g.columns:
            g = g.filter(pl.col("game_type") == "REG")
        g = g.filter(pl.col("home_margin").is_not_null() & pl.col("home_spread_closing").is_not_null())
        parts.append(g)
    df = pl.concat(parts, how="diagonal_relaxed").sort(["season", "week", "gameday", "game_id"]).to_pandas()
    df["home_margin"] = pd.to_numeric(df["home_margin"], errors="coerce").astype(float)
    df["home_spread_closing"] = pd.to_numeric(df["home_spread_closing"], errors="coerce").astype(float)
    df["market_fair_margin"] = -df["home_spread_closing"]
    df["market_residual"] = df["home_margin"] - df["market_fair_margin"]
    return df


def outcome_class(home_margin: float, target_spread: float) -> int:
    ats = float(home_margin + target_spread)
    if math.isclose(ats, 0.0, abs_tol=1e-9):
        return 1
    return 2 if ats > 0 else 0


def normal_probs(mu: float, sigma: float, target_spread: float, delta: float) -> np.ndarray:
    sigma = max(float(sigma), 1e-6)
    m = float(mu + delta)
    integer = math.isclose(target_spread, round(target_spread), abs_tol=1e-9)
    if integer:
        zlo = (-0.5 - m) / sigma
        zhi = (0.5 - m) / sigma
        loss = NORMAL.cdf(zlo)
        push = NORMAL.cdf(zhi) - NORMAL.cdf(zlo)
        cover = 1.0 - NORMAL.cdf(zhi)
    else:
        z = -m / sigma
        loss = NORMAL.cdf(z)
        push = 0.0
        cover = 1.0 - loss
    p = np.array([loss, push, cover], dtype=float)
    return p / p.sum()


def hybrid_probs(normal_p: np.ndarray, train_margin: np.ndarray, target_spread: float, shrink: float) -> np.ndarray:
    required_margin = -float(target_spread)
    empirical_hits = float(np.isclose(train_margin, required_margin, atol=1e-9).sum())
    n = float(len(train_margin))
    p_push = (empirical_hits + shrink * float(normal_p[1])) / (n + shrink)
    nonpush = float(normal_p[0] + normal_p[2])
    if nonpush <= EPS:
        return np.array([(1 - p_push) / 2, p_push, (1 - p_push) / 2], dtype=float)
    loss_share = float(normal_p[0] / nonpush)
    cover_share = float(normal_p[2] / nonpush)
    return np.array([(1 - p_push) * loss_share, p_push, (1 - p_push) * cover_share], dtype=float)


def brier3(p: np.ndarray, cls: int) -> float:
    y = np.zeros(3, dtype=float); y[cls] = 1.0
    return float(np.sum((p - y) ** 2))


def logloss3(p: np.ndarray, cls: int) -> float:
    return float(-math.log(max(float(p[cls]), 1e-12)))


def evaluate(train: pd.DataFrame, test: pd.DataFrame, model: str, shrink: float | None = None) -> pd.DataFrame:
    resid = train["market_residual"].to_numpy(float)
    train_margin = train["home_margin"].to_numpy(float)
    mu = float(np.mean(resid)); sigma = float(np.std(resid, ddof=1))
    rows = []
    for _, r in test.iterrows():
        for delta in OFFSETS:
            target = float(r["home_spread_closing"] + delta)
            integer = math.isclose(target, round(target), abs_tol=1e-9)
            cls = outcome_class(float(r["home_margin"]), target)
            pn = normal_probs(mu, sigma, target, float(delta))
            if model == "global_hybrid" and integer:
                assert shrink is not None
                p = hybrid_probs(pn, train_margin, target, shrink)
            else:
                p = pn
            rows.append({
                "season": int(r["season"]), "week": int(r["week"]), "game_id": r["game_id"],
                "home_team": r["home_team"], "away_team": r["away_team"],
                "delta": float(delta), "target_spread": target, "integer_target": bool(integer),
                "actual_class": ["loss", "push", "cover"][cls],
                "p_loss": float(p[0]), "p_push": float(p[1]), "p_cover": float(p[2]),
                "brier3": brier3(p, cls), "logloss3": logloss3(p, cls), "model": model,
            })
    return pd.DataFrame(rows)


def per_game(detail: pd.DataFrame, integer_only: bool) -> pd.DataFrame:
    d = detail[detail["integer_target"]].copy() if integer_only else detail.copy()
    return d.groupby(["season", "game_id", "model"], as_index=False).agg(
        brier3=("brier3", "mean"), logloss3=("logloss3", "mean")
    )


def tune_shrink(train: pd.DataFrame) -> tuple[float, dict]:
    seasons = sorted(int(x) for x in train["season"].unique())
    val_season = seasons[-1]
    inner_train = train[train["season"] < val_season].copy()
    val = train[train["season"] == val_season].copy()
    scores = {}
    for shrink in SHRINK:
        d = evaluate(inner_train, val, "global_hybrid", shrink)
        scores[str(shrink)] = float(per_game(d, True)["brier3"].mean())
    best = min(SHRINK, key=lambda x: scores[str(x)])
    return best, {"validation_season": val_season, "scores": scores, "selected": best}


def summary(detail: pd.DataFrame) -> dict:
    pgi = per_game(detail, True); pga = per_game(detail, False)
    di = detail[detail["integer_target"]]
    return {
        "n_games": int(detail["game_id"].nunique()),
        "integer_brier3": float(pgi["brier3"].mean()),
        "integer_logloss3": float(pgi["logloss3"].mean()),
        "all_offset_brier3": float(pga["brier3"].mean()),
        "all_offset_logloss3": float(pga["logloss3"].mean()),
        "integer_push_pred": float(di["p_push"].mean()),
        "integer_push_obs": float((di["actual_class"] == "push").mean()),
    }


def key_diag(detail: pd.DataFrame) -> list[dict]:
    a = detail["target_spread"].abs()
    out = []
    for key in [3.0, 3.5, 7.0, 7.5]:
        x = detail[np.isclose(a, key)]
        if x.empty: continue
        out.append({
            "abs_target_spread": key, "n": int(len(x)), "brier3": float(x["brier3"].mean()),
            "pred_push": float(x["p_push"].mean()), "obs_push": float((x["actual_class"] == "push").mean()),
        })
    return out


def curve(detail: pd.DataFrame) -> list[dict]:
    out = []
    for delta, x in detail.groupby("delta"):
        out.append({
            "delta": float(delta), "n": int(len(x)),
            "pred_cover": float(x["p_cover"].mean()), "obs_cover": float((x["actual_class"] == "cover").mean()),
            "pred_push": float(x["p_push"].mean()), "obs_push": float((x["actual_class"] == "push").mean()),
        })
    return sorted(out, key=lambda z: z["delta"])


def run(df: pd.DataFrame):
    seasons = sorted(int(x) for x in df["season"].unique())
    test_seasons = [s for i, s in enumerate(seasons) if i >= MIN_TRAIN_SEASONS]
    folds, parts = [], []
    for s in test_seasons:
        train = df[df["season"] < s].copy(); test = df[df["season"] == s].copy()
        shrink, tuning = tune_shrink(train)
        dn = evaluate(train, test, "normal")
        dh = evaluate(train, test, "global_hybrid", shrink)
        sn, sh = summary(dn), summary(dh)
        folds.append({
            "test_season": s, "shrink": shrink, "tuning": tuning, "normal": sn, "global_hybrid": sh,
            "normal_minus_hybrid_integer_brier": sn["integer_brier3"] - sh["integer_brier3"],
            "normal_minus_hybrid_all_brier": sn["all_offset_brier3"] - sh["all_offset_brier3"],
        })
        parts.extend([dn, dh])
        print(f"[fold {s}] shrink={shrink} integer normal={sn['integer_brier3']:.5f} hybrid={sh['integer_brier3']:.5f}")

    detail = pd.concat(parts, ignore_index=True)
    normal = detail[detail["model"] == "normal"].copy(); hybrid = detail[detail["model"] == "global_hybrid"].copy()
    d_int = [f["normal_minus_hybrid_integer_brier"] for f in folds]
    d_all = [f["normal_minus_hybrid_all_brier"] for f in folds]
    mean_int = float(np.mean(d_int)); ci_int = bootstrap_mean_ci(d_int, seed=716, reps=10000)
    mean_all = float(np.mean(d_all)); ci_all = bootstrap_mean_ci(d_all, seed=717, reps=10000)
    positive = int(sum(x > 0 for x in d_int))
    if mean_int > 0 and ci_int[0] > 0:
        verdict = "REPLICATION PASS: frozen global hybrid robustly improved integer-line Brier in the independent older-era replication. Retain as V2 historical probability challenger and advance to prospective 2026 shadow validation."
    elif mean_int > 0:
        verdict = "REPLICATION MIXED: global hybrid improved average integer-line Brier but the season-bootstrap interval includes zero. Retain as challenger only; prospective 2026 evidence is required."
    else:
        verdict = "REPLICATION FAIL: global hybrid did not improve older-era integer-line Brier. Document era instability and do not rely on the hybrid without prospective evidence."
    result = {
        "experiment": "V2-0006D", "verdict": verdict,
        "heldout_seasons": [f["test_season"] for f in folds], "n_unique_games": int(hybrid["game_id"].nunique()),
        "offsets": OFFSETS.tolist(),
        "primary": {
            "mean_normal_minus_hybrid_integer_brier": mean_int, "season_bootstrap_95pct": ci_int,
            "positive_heldout_seasons": positive, "total_heldout_seasons": len(folds),
            "mean_normal_minus_hybrid_all_offset_brier": mean_all, "all_offset_bootstrap_95pct": ci_all,
        },
        "aggregate": {"normal": summary(normal), "global_hybrid": summary(hybrid)},
        "key_numbers": {"normal": key_diag(normal), "global_hybrid": key_diag(hybrid)},
        "line_advantage_curve": curve(hybrid), "folds": folds,
        "limitations": [
            "This is backward temporal replication; architecture was discovered using later seasons and therefore this is not a sacred future holdout.",
            "Closing market is a research fair-line baseline, not historical Sly Friday data.",
            "Synthetic offsets test probability shape, not historical line availability.",
            "No 2020+ outcomes enter this execution.",
        ],
    }
    return result, detail


def write_report(result: dict, detail: pd.DataFrame, out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "results.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    detail.to_csv(out_dir / "predictions.csv", index=False)
    p = result["primary"]; a = result["aggregate"]
    lines = [
        "# V2-0006D Global Hybrid Robustness Replication", "", f"**Verdict:** {result['verdict']}", "",
        f"Held-out seasons: {result['heldout_seasons']}; games: **{result['n_unique_games']}**.", "",
        "| Model | Integer Brier3 | Integer log loss | All-offset Brier3 | Push pred / obs |",
        "|---|---:|---:|---:|---:|",
    ]
    for k, label in [("normal", "Normal"), ("global_hybrid", "Global hybrid")]:
        x = a[k]
        lines.append(f"| {label} | {x['integer_brier3']:.5f} | {x['integer_logloss3']:.5f} | {x['all_offset_brier3']:.5f} | {x['integer_push_pred']:.2%} / {x['integer_push_obs']:.2%} |")
    lines += [
        "", f"Primary normal-minus-hybrid integer Brier: **{p['mean_normal_minus_hybrid_integer_brier']:+.6f}**, 95% CI **[{p['season_bootstrap_95pct'][0]:+.6f}, {p['season_bootstrap_95pct'][1]:+.6f}]**.",
        f"Positive seasons: **{p['positive_heldout_seasons']}/{p['total_heldout_seasons']}**.",
        f"All-offset safety difference: **{p['mean_normal_minus_hybrid_all_offset_brier']:+.6f}**, 95% CI **[{p['all_offset_bootstrap_95pct'][0]:+.6f}, {p['all_offset_bootstrap_95pct'][1]:+.6f}]**.",
        "", "This replication does not replace prospective 2026 shadow validation.",
    ]
    (out_dir / "REPORT.md").write_text("\n".join(lines), encoding="utf-8")


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--start-season", type=int, default=2006); ap.add_argument("--end-season", type=int, default=2019); ap.add_argument("--out-dir", type=Path, default=Path("v2/results/hybrid_robustness")); args = ap.parse_args()
    if args.end_season >= 2020: raise SystemExit("0006D intentionally excludes 2020+ outcomes")
    df = load_games(args.start_season, args.end_season)
    result, detail = run(df); write_report(result, detail, args.out_dir)
    print(json.dumps({"verdict": result["verdict"], "primary": result["primary"], "aggregate": result["aggregate"], "key_numbers": result["key_numbers"], "line_advantage_curve": result["line_advantage_curve"]}, indent=2))

if __name__ == "__main__": main()
