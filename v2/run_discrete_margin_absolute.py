"""V2-0006B: corrected absolute-margin discrete probability experiment.

Research-only. Models exact integer final margins rather than mixing/recentering
market residuals, so NFL key-number mass at 3 and 7 is preserved.
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

OFFSETS = np.array([-1.5, -1.0, -0.5, 0.0, 0.5, 1.0, 1.5], dtype=float)
MIN_TRAIN_SEASONS = 4
NORMAL = NormalDist()
SPREAD_BW = [1.5, 2.5, 4.0, 6.0]
TOTAL_BW = [7.5, 15.0]
SHRINK = [25.0, 75.0]
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
    if "total_line" not in df.columns:
        df["total_line"] = np.nan
    df["total_line"] = pd.to_numeric(df["total_line"], errors="coerce")
    return df


def outcome_class(home_margin: float, target_spread: float) -> int:
    v = float(home_margin + target_spread)
    if math.isclose(v, 0.0, abs_tol=1e-9):
        return 1  # push
    return 2 if v > 0 else 0  # loss, push, cover


def normal_probs(mu: float, sigma: float, target_spread: float, delta: float) -> np.ndarray:
    sigma = max(float(sigma), 1e-6)
    m = float(mu + delta)
    integer_line = math.isclose(target_spread, round(target_spread), abs_tol=1e-9)
    if integer_line:
        zlo = (-0.5 - m) / sigma
        zhi = (0.5 - m) / sigma
        loss = NORMAL.cdf(zlo)
        push = NORMAL.cdf(zhi) - NORMAL.cdf(zlo)
        cover = 1.0 - NORMAL.cdf(zhi)
    else:
        z = (0.0 - m) / sigma
        loss = NORMAL.cdf(z)
        push = 0.0
        cover = 1.0 - loss
    p = np.array([loss, push, cover], dtype=float)
    return p / p.sum()


def brier3(p: np.ndarray, cls: int) -> float:
    y = np.zeros(3, dtype=float)
    y[cls] = 1.0
    return float(np.sum((p - y) ** 2))


def logloss3(p: np.ndarray, cls: int) -> float:
    return float(-math.log(max(float(p[cls]), 1e-12)))


def training_arrays(train: pd.DataFrame):
    fair = train["market_fair_margin"].to_numpy(float)
    total = train["total_line"].to_numpy(float)
    margin = train["home_margin"].to_numpy(float)
    resid = train["market_residual"].to_numpy(float)
    total_med = float(np.nanmedian(total)) if np.isfinite(np.nanmedian(total)) else 44.0
    total = np.where(np.isfinite(total), total, total_med)
    return fair, total, margin, resid, total_med


def query_weights(
    train_fair: np.ndarray,
    train_total: np.ndarray,
    q_fair: float,
    q_total: float,
    hs: float,
    ht: float | None,
) -> np.ndarray:
    z = ((train_fair - q_fair) / hs) ** 2
    if ht is not None:
        z = z + ((train_total - q_total) / ht) ** 2
    return np.exp(-0.5 * z)


def discrete_probs(
    train_margin: np.ndarray,
    w: np.ndarray,
    target_spread: float,
    normal_prior: np.ndarray,
    shrink: float,
) -> np.ndarray:
    ats = train_margin + target_spread
    counts = np.array([
        float(w[ats < -1e-9].sum()),
        float(w[np.isclose(ats, 0.0, atol=1e-9)].sum()),
        float(w[ats > 1e-9].sum()),
    ])
    p = (counts + shrink * normal_prior) / (float(w.sum()) + shrink)
    p = np.clip(p, 1e-12, 1.0)
    return p / p.sum()


def evaluate(
    train: pd.DataFrame,
    test: pd.DataFrame,
    model: str,
    params: tuple[float, float | None, float] | None = None,
) -> pd.DataFrame:
    fair, total, margin, resid, total_med = training_arrays(train)
    mu = float(np.mean(resid))
    sigma = float(np.std(resid, ddof=1))
    rows = []

    for _, r in test.iterrows():
        q_fair = float(r["market_fair_margin"])
        q_total = float(r["total_line"]) if pd.notna(r["total_line"]) else total_med
        if model != "normal":
            assert params is not None
            hs, ht, shrink = params
            w = query_weights(fair, total, q_fair, q_total, hs, ht)
        for delta in OFFSETS:
            target_spread = float(r["home_spread_closing"] + delta)
            cls = outcome_class(float(r["home_margin"]), target_spread)
            prior = normal_probs(mu, sigma, target_spread, float(delta))
            if model == "normal":
                p = prior
            else:
                p = discrete_probs(margin, w, target_spread, prior, float(shrink))
            rows.append({
                "season": int(r["season"]),
                "week": int(r["week"]),
                "game_id": r["game_id"],
                "home_team": r["home_team"],
                "away_team": r["away_team"],
                "home_margin": float(r["home_margin"]),
                "home_spread_closing": float(r["home_spread_closing"]),
                "market_fair_margin": q_fair,
                "total_line": None if pd.isna(r["total_line"]) else float(r["total_line"]),
                "delta": float(delta),
                "target_spread": target_spread,
                "actual_class": ["loss", "push", "cover"][cls],
                "p_loss": float(p[0]),
                "p_push": float(p[1]),
                "p_cover": float(p[2]),
                "brier3": brier3(p, cls),
                "logloss3": logloss3(p, cls),
                "model": model,
            })
    return pd.DataFrame(rows)


def per_game(detail: pd.DataFrame) -> pd.DataFrame:
    return detail.groupby(["season", "game_id", "model"], as_index=False).agg(
        brier3=("brier3", "mean"), logloss3=("logloss3", "mean")
    )


def tune(train: pd.DataFrame, mode: str):
    seasons = sorted(int(x) for x in train["season"].unique())
    val_season = seasons[-1]
    inner_train = train[train["season"] < val_season].copy()
    inner_val = train[train["season"] == val_season].copy()
    candidates = []
    if mode == "spread_only":
        for hs in SPREAD_BW:
            for shrink in SHRINK:
                candidates.append((hs, None, shrink))
    elif mode == "spread_total":
        for hs in SPREAD_BW:
            for ht in TOTAL_BW:
                for shrink in SHRINK:
                    candidates.append((hs, ht, shrink))
    else:
        raise ValueError(mode)

    best = None
    best_score = float("inf")
    scores = {}
    for params in candidates:
        d = evaluate(inner_train, inner_val, mode, params)
        score = float(per_game(d)["brier3"].mean())
        key = str(params)
        scores[key] = score
        if score < best_score:
            best_score = score
            best = params
    assert best is not None
    return best, {"validation_season": val_season, "scores": scores, "selected": list(best)}


def summarize(detail: pd.DataFrame) -> dict:
    pg = per_game(detail)
    closing = detail[np.isclose(detail["delta"], 0.0)].copy()
    nonpush = closing[closing["actual_class"] != "push"].copy()
    y = (nonpush["actual_class"] == "cover").astype(float).to_numpy()
    denom = nonpush["p_cover"].to_numpy(float) + nonpush["p_loss"].to_numpy(float)
    p = nonpush["p_cover"].to_numpy(float) / np.maximum(denom, EPS)
    integer = np.isclose(detail["target_spread"], np.round(detail["target_spread"]))
    di = detail[integer]
    return {
        "n_games": int(pg["game_id"].nunique()),
        "mean_per_game_brier3": float(pg["brier3"].mean()),
        "mean_per_game_logloss3": float(pg["logloss3"].mean()),
        "closing_brier3": float(closing["brier3"].mean()),
        "closing_logloss3": float(closing["logloss3"].mean()),
        "closing_nonpush_binary_brier": float(np.mean((p - y) ** 2)),
        "integer_push_pred": float(di["p_push"].mean()),
        "integer_push_obs": float((di["actual_class"] == "push").mean()),
    }


def key_diag(detail: pd.DataFrame) -> list[dict]:
    a = detail["target_spread"].abs()
    out = []
    for key in [3.0, 3.5, 7.0, 7.5]:
        x = detail[np.isclose(a, key)]
        if x.empty:
            continue
        out.append({
            "abs_target_spread": key,
            "n": int(len(x)),
            "brier3": float(x["brier3"].mean()),
            "pred_push": float(x["p_push"].mean()),
            "obs_push": float((x["actual_class"] == "push").mean()),
        })
    return out


def line_curve(detail: pd.DataFrame) -> list[dict]:
    out = []
    for delta, x in detail.groupby("delta"):
        out.append({
            "delta": float(delta),
            "pred_cover": float(x["p_cover"].mean()),
            "obs_cover": float((x["actual_class"] == "cover").mean()),
            "pred_push": float(x["p_push"].mean()),
            "obs_push": float((x["actual_class"] == "push").mean()),
            "n": int(len(x)),
        })
    return sorted(out, key=lambda z: z["delta"])


def run(df: pd.DataFrame):
    seasons = sorted(int(x) for x in df["season"].unique())
    test_seasons = [s for i, s in enumerate(seasons) if i >= MIN_TRAIN_SEASONS]
    folds = []
    details = []

    for s in test_seasons:
        train = df[df["season"] < s].copy()
        test = df[df["season"] == s].copy()
        p1, t1 = tune(train, "spread_only")
        p2, t2 = tune(train, "spread_total")
        print(f"[fold {s}] spread_only={p1} spread_total={p2}")

        dn = evaluate(train, test, "normal")
        d1 = evaluate(train, test, "spread_only", p1)
        d2 = evaluate(train, test, "spread_total", p2)
        details.extend([dn, d1, d2])
        sn, s1, s2 = summarize(dn), summarize(d1), summarize(d2)
        folds.append({
            "test_season": s,
            "spread_only_params": list(p1),
            "spread_total_params": list(p2),
            "spread_only_tuning": t1,
            "spread_total_tuning": t2,
            "normal": sn,
            "spread_only": s1,
            "spread_total": s2,
            "normal_minus_spread_only_brier": sn["mean_per_game_brier3"] - s1["mean_per_game_brier3"],
            "normal_minus_spread_total_brier": sn["mean_per_game_brier3"] - s2["mean_per_game_brier3"],
            "spread_only_minus_spread_total_brier": s1["mean_per_game_brier3"] - s2["mean_per_game_brier3"],
        })
        print(
            f"  Brier normal={sn['mean_per_game_brier3']:.4f} "
            f"spread={s1['mean_per_game_brier3']:.4f} spread+total={s2['mean_per_game_brier3']:.4f}"
        )

    detail = pd.concat(details, ignore_index=True)
    dnorm = detail[detail["model"] == "normal"].copy()
    dspread = detail[detail["model"] == "spread_only"].copy()
    dtotal = detail[detail["model"] == "spread_total"].copy()

    delta_primary = [f["normal_minus_spread_only_brier"] for f in folds]
    delta_total = [f["spread_only_minus_spread_total_brier"] for f in folds]
    primary_mean = float(np.mean(delta_primary))
    primary_ci = bootstrap_mean_ci(delta_primary, seed=716, reps=10000)
    total_mean = float(np.mean(delta_total))
    total_ci = bootstrap_mean_ci(delta_total, seed=717, reps=10000)

    if primary_mean > 0 and primary_ci[0] > 0:
        if total_mean > 0 and total_ci[0] > 0:
            verdict = "PASS ABSOLUTE DISCRETE MARGIN + TOTAL: discrete final-margin modeling robustly beat normal, and total added robust incremental value. Advance to calibration/robustness; no production promotion yet."
        else:
            verdict = "PASS ABSOLUTE DISCRETE MARGIN; TOTAL NOT PROVEN: spread-conditioned integer-margin model robustly beat normal, but adding total did not robustly improve it. Retain simpler spread-conditioned discrete model for next stage."
    else:
        verdict = "FAIL AGGREGATE GATE: absolute discrete margin model did not robustly beat the normal baseline. Do not promote; inspect calibration/key-number diagnostics before choosing next model form."

    result = {
        "experiment": "V2-0006B",
        "verdict": verdict,
        "heldout_seasons": [f["test_season"] for f in folds],
        "n_unique_heldout_games": int(dspread["game_id"].nunique()),
        "offsets": OFFSETS.tolist(),
        "primary": {
            "mean_normal_minus_spread_only_brier": primary_mean,
            "season_bootstrap_95pct": primary_ci,
            "mean_spread_only_minus_spread_total_brier": total_mean,
            "spread_total_season_bootstrap_95pct": total_ci,
        },
        "aggregate": {
            "normal": summarize(dnorm),
            "spread_only": summarize(dspread),
            "spread_total": summarize(dtotal),
        },
        "key_numbers": {
            "normal": key_diag(dnorm),
            "spread_only": key_diag(dspread),
            "spread_total": key_diag(dtotal),
        },
        "line_advantage_curve": line_curve(dspread),
        "folds": folds,
        "limitations": [
            "Closing market is a research fair-line baseline, not a historical Sly Friday snapshot.",
            "Alternate offsets test distribution shape, not historical line availability.",
            "No 2026 outcomes are used.",
            "Key-number diagnostics cannot override the aggregate promotion gate.",
        ],
    }
    return result, detail


def write_report(result: dict, detail: pd.DataFrame, out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "results.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    detail.to_csv(out_dir / "predictions.csv", index=False)
    p = result["primary"]
    lines = [
        "# V2-0006B Corrected Absolute-Margin Experiment",
        "",
        f"**Verdict:** {result['verdict']}",
        "",
        f"Held-out games: **{result['n_unique_heldout_games']}** across {result['heldout_seasons']}.",
        "",
        "## Aggregate",
        "",
        "| Model | Per-game Brier3 | Log loss | Closing Brier3 | Closing binary Brier | Integer push pred / obs |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for key, label in [("normal", "Normal"), ("spread_only", "Discrete spread-conditioned"), ("spread_total", "Discrete spread+total")]:
        x = result["aggregate"][key]
        lines.append(
            f"| {label} | {x['mean_per_game_brier3']:.4f} | {x['mean_per_game_logloss3']:.4f} | {x['closing_brier3']:.4f} | {x['closing_nonpush_binary_brier']:.4f} | {x['integer_push_pred']:.2%} / {x['integer_push_obs']:.2%} |"
        )
    lines += [
        "",
        "## Promotion comparisons",
        "",
        f"- Normal minus spread-conditioned Brier: **{p['mean_normal_minus_spread_only_brier']:+.5f}**, 95% season-bootstrap CI **[{p['season_bootstrap_95pct'][0]:+.5f}, {p['season_bootstrap_95pct'][1]:+.5f}]**.",
        f"- Spread-only minus spread+total Brier: **{p['mean_spread_only_minus_spread_total_brier']:+.5f}**, 95% season-bootstrap CI **[{p['spread_total_season_bootstrap_95pct'][0]:+.5f}, {p['spread_total_season_bootstrap_95pct'][1]:+.5f}]**.",
        "",
        "0006A was not used as promotion evidence because it failed the absolute-margin/key-number QA requirement.",
    ]
    (out_dir / "REPORT.md").write_text("\n".join(lines), encoding="utf-8")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--start-season", type=int, default=2016)
    ap.add_argument("--end-season", type=int, default=2025)
    ap.add_argument("--out-dir", type=Path, default=Path("v2/results/discrete_margin_absolute"))
    args = ap.parse_args()
    if args.end_season >= 2026:
        raise SystemExit("2026+ intentionally excluded")
    df = load_games(args.start_season, args.end_season)
    result, detail = run(df)
    write_report(result, detail, args.out_dir)
    print(json.dumps({
        "verdict": result["verdict"],
        "primary": result["primary"],
        "aggregate": result["aggregate"],
        "key_numbers": result["key_numbers"],
        "line_advantage_curve": result["line_advantage_curve"],
    }, indent=2))


if __name__ == "__main__":
    main()
