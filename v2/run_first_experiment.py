"""V2 Experiment 001/002: market-only baseline vs Ridge football-residual challenger.

This is a research experiment, not production logic.

Design:
- Historical regular-season games only through the requested end season.
- Closing market spread is used ONLY as the fair-market research baseline.
  It does not simulate Friday/Sly information availability.
- Football features are rolling PBP aggregates shifted by one completed team game.
- Outer evaluation is walk-forward by season.
- Ridge alpha is selected inside each training window using the last training
  season as an inner validation season.
- No 2026 games are used.

The first experiment answers one narrow question:
    Do simple, leakage-safe football residual features improve out-of-sample
    fair-margin prediction beyond the closing market baseline?

Probability/Brier outputs here use an explicitly PRELIMINARY normal residual
approximation. They are diagnostics only; V2's discrete-margin/calibration
layer is a later registered experiment.
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
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.metrics import log_loss, mean_absolute_error, mean_squared_error
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from build_baseline_features import add_lagged_rolls, aggregate_team_games, to_game_rows
from build_historical_dataset import normalize_schedule_core


ALPHAS = [0.1, 1.0, 10.0, 100.0]
MIN_TRAIN_SEASONS = 4
NORMAL = NormalDist()


def rmse(y_true, y_pred) -> float:
    return float(math.sqrt(mean_squared_error(y_true, y_pred)))


def clip_probs(p: np.ndarray) -> np.ndarray:
    return np.clip(p, 1e-5, 1 - 1e-5)


def build_lightweight_history(start_season: int, end_season: int) -> pl.DataFrame:
    """Load one PBP season at a time so memory does not scale with raw PBP history."""
    schedule_parts: list[pl.DataFrame] = []
    team_game_parts: list[pl.DataFrame] = []

    for season in range(start_season, end_season + 1):
        print(f"[data] season {season}: schedules")
        schedules_raw = nfl.load_schedules([season])
        schedules = normalize_schedule_core(schedules_raw)
        schedule_parts.append(schedules)

        print(f"[data] season {season}: pbp")
        pbp = nfl.load_pbp([season])
        team_games = aggregate_team_games(pbp, schedules)
        team_game_parts.append(team_games)
        del pbp, schedules_raw

    games = pl.concat(schedule_parts, how="diagonal_relaxed")
    team_games = pl.concat(team_game_parts, how="diagonal_relaxed").sort(
        ["team", "gameday", "game_id"]
    )
    team_features = add_lagged_rolls(team_games)
    baseline = to_game_rows(team_features, games)
    return baseline


def feature_columns(df: pd.DataFrame) -> list[str]:
    cols = [c for c in df.columns if c.startswith("diff_")]
    for c in [
        "home_spread_closing",
        "total_line",
        "rest_diff",
        "home_prior_games_count",
        "away_prior_games_count",
    ]:
        if c in df.columns:
            cols.append(c)
    # Stable order + no duplicates.
    return list(dict.fromkeys(cols))


def make_ridge(alpha: float, features: list[str]) -> Pipeline:
    prep = ColumnTransformer(
        [
            (
                "num",
                Pipeline(
                    [
                        ("impute", SimpleImputer(strategy="median")),
                        ("scale", StandardScaler()),
                    ]
                ),
                features,
            )
        ],
        remainder="drop",
    )
    return Pipeline([("prep", prep), ("ridge", Ridge(alpha=alpha))])


def choose_alpha(train: pd.DataFrame, features: list[str]) -> tuple[float, dict]:
    seasons = sorted(train["season"].unique())
    if len(seasons) < 3:
        return 10.0, {"reason": "insufficient inner seasons", "scores": {}}
    validation_season = seasons[-1]
    inner_train = train[train["season"] < validation_season]
    inner_val = train[train["season"] == validation_season]
    scores = {}
    for alpha in ALPHAS:
        model = make_ridge(alpha, features)
        model.fit(inner_train[features], inner_train["market_residual"])
        pred = model.predict(inner_val[features])
        scores[str(alpha)] = rmse(inner_val["market_residual"], pred)
    best = min(ALPHAS, key=lambda a: scores[str(a)])
    return best, {"validation_season": int(validation_season), "scores": scores}


def fold_metrics(test: pd.DataFrame, market_margin: np.ndarray, ridge_margin: np.ndarray,
                 residual_pred: np.ndarray, sigma: float) -> tuple[dict, pd.DataFrame]:
    y_margin = test["home_margin"].to_numpy(float)
    ats_margin = test["ats_margin_home_closing"].to_numpy(float)
    nonpush = ats_margin != 0
    y_home_cover = (ats_margin[nonpush] > 0).astype(int)

    market_prob = np.full(nonpush.sum(), 0.5)
    ridge_prob_all = np.array([NORMAL.cdf(float(x) / sigma) for x in residual_pred])
    ridge_prob = clip_probs(ridge_prob_all[nonpush])

    selected_home = ridge_prob >= 0.5
    selected_hit = np.where(selected_home, y_home_cover == 1, y_home_cover == 0)

    metrics = {
        "n_games": int(len(test)),
        "pushes": int((~nonpush).sum()),
        "market_margin_mae": float(mean_absolute_error(y_margin, market_margin)),
        "ridge_margin_mae": float(mean_absolute_error(y_margin, ridge_margin)),
        "market_margin_rmse": rmse(y_margin, market_margin),
        "ridge_margin_rmse": rmse(y_margin, ridge_margin),
        "market_brier": float(np.mean((market_prob - y_home_cover) ** 2)),
        "ridge_brier_precal": float(np.mean((ridge_prob - y_home_cover) ** 2)),
        "market_logloss": float(log_loss(y_home_cover, market_prob, labels=[0, 1])),
        "ridge_logloss_precal": float(log_loss(y_home_cover, ridge_prob, labels=[0, 1])),
        "ridge_selected_side_hit_rate": float(selected_hit.mean()),
        "sigma_precal": float(sigma),
    }

    detail = test[["season", "week", "game_id", "home_team", "away_team", "home_margin", "home_spread_closing"]].copy()
    detail["market_pred_margin"] = market_margin
    detail["ridge_pred_margin"] = ridge_margin
    detail["ridge_pred_residual"] = residual_pred
    detail["ats_margin_home_closing"] = ats_margin
    detail["ridge_home_cover_prob_precal"] = ridge_prob_all
    detail["is_push"] = ~nonpush
    detail["selected_side"] = np.where(ridge_prob_all >= 0.5, detail["home_team"], detail["away_team"])
    detail["selected_edge"] = np.abs(ridge_prob_all - 0.5)
    detail["selected_hit"] = np.where(
        detail["is_push"], np.nan,
        np.where(ridge_prob_all >= 0.5, ats_margin > 0, ats_margin < 0).astype(float),
    )
    return metrics, detail


def bootstrap_mean_ci(values: list[float], seed: int = 716, reps: int = 10000) -> list[float]:
    arr = np.asarray(values, dtype=float)
    if len(arr) == 0:
        return [float("nan"), float("nan")]
    rng = np.random.default_rng(seed)
    means = np.empty(reps)
    for i in range(reps):
        means[i] = rng.choice(arr, size=len(arr), replace=True).mean()
    return [float(np.quantile(means, 0.025)), float(np.quantile(means, 0.975))]


def edge_bucket_report(detail: pd.DataFrame) -> list[dict]:
    d = detail[~detail["is_push"]].copy()
    bins = [-1e-9, 0.02, 0.04, 0.06, 1.0]
    labels = ["0–2 pp", "2–4 pp", "4–6 pp", "6+ pp"]
    d["edge_bucket"] = pd.cut(d["selected_edge"], bins=bins, labels=labels, include_lowest=True)
    out = []
    for label in labels:
        x = d[d["edge_bucket"] == label]
        out.append({
            "bucket": label,
            "n": int(len(x)),
            "selected_side_hit_rate": None if len(x) == 0 else float(x["selected_hit"].mean()),
            "avg_predicted_edge": None if len(x) == 0 else float(x["selected_edge"].mean()),
        })
    return out


def run_experiment(df_pl: pl.DataFrame) -> tuple[dict, pd.DataFrame]:
    df = df_pl.to_pandas()
    required = ["season", "week", "game_id", "home_margin", "home_spread_closing"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"baseline table missing {missing}")

    df = df[df["home_margin"].notna() & df["home_spread_closing"].notna()].copy()
    df["market_pred_margin"] = -df["home_spread_closing"].astype(float)
    df["market_residual"] = df["home_margin"].astype(float) - df["market_pred_margin"]
    df["ats_margin_home_closing"] = df["home_margin"].astype(float) + df["home_spread_closing"].astype(float)

    features = feature_columns(df)
    if not features:
        raise ValueError("no model features discovered")

    seasons = sorted(int(x) for x in df["season"].unique())
    test_seasons = [s for i, s in enumerate(seasons) if i >= MIN_TRAIN_SEASONS]
    folds = []
    details = []

    for test_season in test_seasons:
        train = df[df["season"] < test_season].copy()
        test = df[df["season"] == test_season].copy()
        if train["season"].nunique() < MIN_TRAIN_SEASONS or test.empty:
            continue

        alpha, alpha_meta = choose_alpha(train, features)
        model = make_ridge(alpha, features)
        model.fit(train[features], train["market_residual"])
        residual_pred = model.predict(test[features])
        market_margin = test["market_pred_margin"].to_numpy(float)
        ridge_margin = market_margin + residual_pred

        # Preliminary probability scale only. Calibration/discrete margin modeling
        # is intentionally deferred to later registered experiments.
        train_resid_pred = model.predict(train[features])
        sigma = float(np.std(train["market_residual"].to_numpy(float) - train_resid_pred, ddof=1))
        sigma = max(sigma, 1.0)

        metrics, detail = fold_metrics(test, market_margin, ridge_margin, residual_pred, sigma)
        metrics.update({
            "test_season": int(test_season),
            "train_seasons": [int(x) for x in sorted(train["season"].unique())],
            "alpha": float(alpha),
            "alpha_selection": alpha_meta,
        })
        folds.append(metrics)
        details.append(detail)
        print(f"[fold {test_season}] market MAE={metrics['market_margin_mae']:.3f} ridge MAE={metrics['ridge_margin_mae']:.3f} alpha={alpha}")

    if not folds:
        raise ValueError("no walk-forward folds were produced")

    all_detail = pd.concat(details, ignore_index=True)
    mae_delta = [f["market_margin_mae"] - f["ridge_margin_mae"] for f in folds]
    rmse_delta = [f["market_margin_rmse"] - f["ridge_margin_rmse"] for f in folds]
    brier_delta = [f["market_brier"] - f["ridge_brier_precal"] for f in folds]

    summary = {
        "experiment": "V2-EXP-001-002",
        "purpose": "market-only closing-line baseline vs leakage-safe Ridge football-residual challenger",
        "important_limitations": [
            "Closing market lines are used as a research fair-market baseline; this is NOT a Friday/Sly stale-line backtest.",
            "Brier/log-loss probabilities use an uncalibrated normal residual approximation and are diagnostic only.",
            "No injuries, QB starter model, external sources, public betting, or intra-week line path are included yet.",
            "No 2026 outcomes are used.",
        ],
        "features": features,
        "folds": folds,
        "aggregate": {
            "test_seasons": [f["test_season"] for f in folds],
            "n_test_games": int(sum(f["n_games"] for f in folds)),
            "mean_market_margin_mae": float(np.mean([f["market_margin_mae"] for f in folds])),
            "mean_ridge_margin_mae": float(np.mean([f["ridge_margin_mae"] for f in folds])),
            "mean_mae_improvement_market_minus_ridge": float(np.mean(mae_delta)),
            "mae_improvement_95pct_season_bootstrap": bootstrap_mean_ci(mae_delta),
            "mean_market_margin_rmse": float(np.mean([f["market_margin_rmse"] for f in folds])),
            "mean_ridge_margin_rmse": float(np.mean([f["ridge_margin_rmse"] for f in folds])),
            "mean_rmse_improvement_market_minus_ridge": float(np.mean(rmse_delta)),
            "mean_market_brier": float(np.mean([f["market_brier"] for f in folds])),
            "mean_ridge_brier_precal": float(np.mean([f["ridge_brier_precal"] for f in folds])),
            "mean_brier_improvement_market_minus_ridge": float(np.mean(brier_delta)),
            "brier_improvement_95pct_season_bootstrap": bootstrap_mean_ci(brier_delta),
            "pooled_selected_side_hit_rate": float(all_detail.loc[~all_detail["is_push"], "selected_hit"].mean()),
        },
        "edge_buckets_precal": edge_bucket_report(all_detail),
    }

    lo, hi = summary["aggregate"]["mae_improvement_95pct_season_bootstrap"]
    mean_delta = summary["aggregate"]["mean_mae_improvement_market_minus_ridge"]
    if mean_delta > 0 and lo > 0:
        verdict = "PROMISING: Ridge improved margin MAE in this first walk-forward test, with season-bootstrap CI above zero. Continue to discrete-margin/calibration challengers; do not promote to production yet."
    elif mean_delta > 0:
        verdict = "MIXED/PROMISING: average margin MAE improved, but the season-bootstrap interval includes zero. More folds/features/robustness testing are required."
    else:
        verdict = "NO EVIDENCE OF IMPROVEMENT: the first Ridge residual challenger did not beat the market baseline on average margin MAE. Keep market as champion and diagnose/ablate before adding complexity."
    summary["verdict"] = verdict
    return summary, all_detail


def write_report(summary: dict, detail: pd.DataFrame, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "results.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    detail.to_csv(out_dir / "predictions.csv", index=False)

    a = summary["aggregate"]
    lines = [
        "# V2 First Walk-Forward Experiment",
        "",
        f"**Verdict:** {summary['verdict']}",
        "",
        "## Aggregate results",
        "",
        "| Metric | Market-only | Ridge residual | Difference (market − Ridge) |",
        "|---|---:|---:|---:|",
        f"| Margin MAE | {a['mean_market_margin_mae']:.3f} | {a['mean_ridge_margin_mae']:.3f} | {a['mean_mae_improvement_market_minus_ridge']:+.3f} |",
        f"| Margin RMSE | {a['mean_market_margin_rmse']:.3f} | {a['mean_ridge_margin_rmse']:.3f} | {a['mean_rmse_improvement_market_minus_ridge']:+.3f} |",
        f"| ATS Brier (pre-calibration) | {a['mean_market_brier']:.4f} | {a['mean_ridge_brier_precal']:.4f} | {a['mean_brier_improvement_market_minus_ridge']:+.4f} |",
        "",
        f"Test games: **{a['n_test_games']}** across seasons {a['test_seasons']}.",
        f"Pooled selected-side ATS hit rate (pushes excluded, preliminary): **{a['pooled_selected_side_hit_rate']:.1%}**.",
        "",
        "## Season folds",
        "",
        "| Season | N | Alpha | Market MAE | Ridge MAE | Market Brier | Ridge Brier* |",
        "|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for f in summary["folds"]:
        lines.append(
            f"| {f['test_season']} | {f['n_games']} | {f['alpha']:.1f} | {f['market_margin_mae']:.3f} | {f['ridge_margin_mae']:.3f} | {f['market_brier']:.4f} | {f['ridge_brier_precal']:.4f} |"
        )
    lines.extend([
        "",
        "## Preliminary edge buckets",
        "",
        "These are **not calibrated production edges**. They are used only to diagnose whether larger Ridge signals correspond to better ATS outcomes.",
        "",
        "| Predicted edge | N | Selected-side hit rate | Mean edge |",
        "|---|---:|---:|---:|",
    ])
    for b in summary["edge_buckets_precal"]:
        hit = "—" if b["selected_side_hit_rate"] is None else f"{b['selected_side_hit_rate']:.1%}"
        edge = "—" if b["avg_predicted_edge"] is None else f"{b['avg_predicted_edge']:.1%}"
        lines.append(f"| {b['bucket']} | {b['n']} | {hit} | {edge} |")
    lines.extend([
        "",
        "## Guardrails / limitations",
        "",
        "- Closing market spread is the baseline here. This does **not** claim historical Friday/Sly availability.",
        "- `*` Ridge Brier/log-loss uses a preliminary normal residual approximation. V2 discrete-margin modeling and calibration come later.",
        "- This experiment intentionally excludes injuries, QB starter modeling, external models, public betting and line-path features.",
        "- 2026 is excluded so Week 3 cannot influence model selection.",
        "",
    ])
    (out_dir / "REPORT.md").write_text("\n".join(lines), encoding="utf-8")

    # Simple HTML for the isolated Render research service.
    report_text = (out_dir / "REPORT.md").read_text(encoding="utf-8")
    escaped = report_text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    html = f"""<!doctype html><html><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>V2 Research Results</title><style>body{{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;background:#0b1220;color:#e5e7eb;max-width:1100px;margin:0 auto;padding:24px;line-height:1.5}}pre{{white-space:pre-wrap;background:#111827;border:1px solid #243044;border-radius:12px;padding:18px;overflow:auto}}a{{color:#93c5fd}}</style></head><body><h1>V2 Research — First Experiment</h1><pre>{escaped}</pre><p><a href='results.json'>results.json</a> · <a href='predictions.csv'>predictions.csv</a></p></body></html>"""
    (out_dir / "index.html").write_text(html, encoding="utf-8")


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--start-season", type=int, default=2016)
    p.add_argument("--end-season", type=int, default=2025)
    p.add_argument("--out-dir", type=Path, default=Path("v2/results/first_experiment"))
    args = p.parse_args()
    if args.end_season >= 2026:
        raise SystemExit("First V2 architecture experiment intentionally excludes 2026 outcomes")
    if args.end_season - args.start_season + 1 <= MIN_TRAIN_SEASONS:
        raise SystemExit("Need more seasons than MIN_TRAIN_SEASONS for walk-forward testing")

    df = build_lightweight_history(args.start_season, args.end_season)
    summary, detail = run_experiment(df)
    write_report(summary, detail, args.out_dir)
    print(json.dumps(summary["aggregate"], indent=2))
    print(summary["verdict"])


if __name__ == "__main__":
    main()
