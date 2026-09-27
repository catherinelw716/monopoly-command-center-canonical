"""V2-0006: discrete empirical margin / key-number probability experiment.

Research-only. No production logic is changed.

This experiment compares:
1. Normal residual lattice approximation.
2. Global empirical residual distribution.
3. Conditional empirical residual distribution using market fair margin + total.

The target is exact ATS cover/push/loss probability around the closing-market
fair-line research baseline. Alternate offsets test distribution shape only;
they do not claim historical Monopoly availability.
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
EPS = 1e-12
NORMAL = NormalDist()

SPREAD_BW = [2.5, 5.0, 10.0]
TOTAL_BW = [7.5, 15.0]
SHRINK = [25.0, 75.0]


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
    df["home_spread_closing"] = df["home_spread_closing"].astype(float)
    df["home_margin"] = df["home_margin"].astype(float)
    df["market_pred_margin"] = -df["home_spread_closing"]
    df["market_residual"] = df["home_margin"] - df["market_pred_margin"]
    if "total_line" not in df.columns:
        df["total_line"] = np.nan
    df["total_line"] = pd.to_numeric(df["total_line"], errors="coerce")
    return df


def outcome_class(actual_home_margin: float, target_home_spread: float) -> int:
    ats = float(actual_home_margin + target_home_spread)
    if math.isclose(ats, 0.0, abs_tol=1e-9):
        return 1  # push
    return 2 if ats > 0 else 0  # loss, push, cover


def onehot(cls: int) -> np.ndarray:
    y = np.zeros(3, dtype=float)
    y[cls] = 1.0
    return y


def brier3(p: np.ndarray, cls: int) -> float:
    y = onehot(cls)
    return float(np.sum((p - y) ** 2))


def logloss3(p: np.ndarray, cls: int) -> float:
    return float(-math.log(max(float(p[cls]), 1e-12)))


def global_empirical_probs(train_resid: np.ndarray, delta: float) -> np.ndarray:
    shifted = train_resid + delta
    loss = np.mean(shifted < -1e-9)
    push = np.mean(np.isclose(shifted, 0.0, atol=1e-9))
    cover = 1.0 - loss - push
    return np.array([loss, push, cover], dtype=float)


def normal_probs(mu: float, sigma: float, target_spread: float, delta: float) -> np.ndarray:
    """Normal residual approximation with continuity cell for integer target lines."""
    sigma = max(float(sigma), 1e-6)
    m = float(mu + delta)
    integer_line = math.isclose(target_spread, round(target_spread), abs_tol=1e-9)
    if integer_line:
        z_lo = (-0.5 - m) / sigma
        z_hi = (0.5 - m) / sigma
        loss = NORMAL.cdf(z_lo)
        push = NORMAL.cdf(z_hi) - NORMAL.cdf(z_lo)
        cover = 1.0 - NORMAL.cdf(z_hi)
    else:
        z = (0.0 - m) / sigma
        loss = NORMAL.cdf(z)
        push = 0.0
        cover = 1.0 - loss
    p = np.array([loss, push, cover], dtype=float)
    return p / p.sum()


def kernel_weights(train: pd.DataFrame, q_margin: float, q_total: float, hs: float, ht: float) -> np.ndarray:
    spread = train["market_pred_margin"].to_numpy(float)
    total = train["total_line"].to_numpy(float)
    total_fill = np.nanmedian(total)
    if not np.isfinite(total_fill):
        total_fill = 44.0
    total = np.where(np.isfinite(total), total, total_fill)
    if not np.isfinite(q_total):
        q_total = total_fill
    z = ((spread - q_margin) / hs) ** 2 + ((total - q_total) / ht) ** 2
    return np.exp(-0.5 * z)


def conditional_probs(
    train: pd.DataFrame,
    q_margin: float,
    q_total: float,
    delta: float,
    hs: float,
    ht: float,
    shrink: float,
) -> np.ndarray:
    resid = train["market_residual"].to_numpy(float)
    w = kernel_weights(train, q_margin, q_total, hs, ht)
    shifted = resid + delta
    masks = [shifted < -1e-9, np.isclose(shifted, 0.0, atol=1e-9), shifted > 1e-9]
    weighted = np.array([float(w[m].sum()) for m in masks], dtype=float)
    global_p = global_empirical_probs(resid, delta)
    p = (weighted + shrink * global_p) / (float(w.sum()) + shrink)
    p = np.clip(p, 1e-9, 1.0)
    return p / p.sum()


def evaluate_model_on_rows(
    train: pd.DataFrame,
    test: pd.DataFrame,
    model: str,
    params: tuple[float, float, float] | None = None,
) -> pd.DataFrame:
    train_resid = train["market_residual"].to_numpy(float)
    mu = float(np.mean(train_resid))
    sigma = float(np.std(train_resid, ddof=1))
    rows = []

    for _, r in test.iterrows():
        game_scores = []
        for delta in OFFSETS:
            target_spread = float(r["home_spread_closing"] + delta)
            cls = outcome_class(float(r["home_margin"]), target_spread)
            if model == "normal":
                p = normal_probs(mu, sigma, target_spread, float(delta))
            elif model == "global_empirical":
                p = global_empirical_probs(train_resid, float(delta))
            elif model == "conditional":
                assert params is not None
                hs, ht, shrink = params
                p = conditional_probs(
                    train,
                    float(r["market_pred_margin"]),
                    float(r["total_line"]) if pd.notna(r["total_line"]) else float("nan"),
                    float(delta),
                    hs,
                    ht,
                    shrink,
                )
            else:
                raise ValueError(model)

            game_scores.append((brier3(p, cls), logloss3(p, cls)))
            rows.append({
                "season": int(r["season"]),
                "week": int(r["week"]),
                "game_id": r["game_id"],
                "home_team": r["home_team"],
                "away_team": r["away_team"],
                "home_spread_closing": float(r["home_spread_closing"]),
                "market_pred_margin": float(r["market_pred_margin"]),
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


def per_game_scores(detail: pd.DataFrame) -> pd.DataFrame:
    return (
        detail.groupby(["season", "game_id", "model"], as_index=False)
        .agg(brier3=("brier3", "mean"), logloss3=("logloss3", "mean"))
    )


def select_kernel_params(train: pd.DataFrame) -> tuple[tuple[float, float, float], dict]:
    seasons = sorted(int(x) for x in train["season"].unique())
    if len(seasons) < 3:
        return (5.0, 15.0, 75.0), {"reason": "insufficient inner seasons"}
    val_season = seasons[-1]
    inner_train = train[train["season"] < val_season].copy()
    inner_val = train[train["season"] == val_season].copy()
    scores: dict[str, float] = {}
    best = None
    best_score = float("inf")
    for hs in SPREAD_BW:
        for ht in TOTAL_BW:
            for shrink in SHRINK:
                params = (hs, ht, shrink)
                detail = evaluate_model_on_rows(inner_train, inner_val, "conditional", params)
                score = float(per_game_scores(detail)["brier3"].mean())
                key = f"hs={hs},ht={ht},shrink={shrink}"
                scores[key] = score
                if score < best_score:
                    best_score = score
                    best = params
    assert best is not None
    return best, {"validation_season": val_season, "scores": scores, "selected": list(best)}


def summarize_detail(detail: pd.DataFrame) -> dict:
    pergame = per_game_scores(detail)
    return {
        "n_games": int(pergame["game_id"].nunique()),
        "mean_per_game_brier3": float(pergame["brier3"].mean()),
        "mean_per_game_logloss3": float(pergame["logloss3"].mean()),
    }


def closing_metrics(detail: pd.DataFrame) -> dict:
    d = detail[np.isclose(detail["delta"], 0.0)].copy()
    nonpush = d[d["actual_class"] != "push"].copy()
    y_cover = (nonpush["actual_class"] == "cover").astype(float).to_numpy()
    p_cover_cond = nonpush["p_cover"].to_numpy(float)
    denom = nonpush["p_cover"].to_numpy(float) + nonpush["p_loss"].to_numpy(float)
    p_cover_binary = p_cover_cond / np.maximum(denom, EPS)
    return {
        "closing_brier3": float(d["brier3"].mean()),
        "closing_logloss3": float(d["logloss3"].mean()),
        "closing_nonpush_binary_brier": float(np.mean((p_cover_binary - y_cover) ** 2)),
    }


def push_calibration(detail: pd.DataFrame) -> dict:
    d = detail.copy()
    integer = np.isclose(d["target_spread"], np.round(d["target_spread"]))
    d = d[integer]
    observed = (d["actual_class"] == "push").astype(float)
    return {
        "n_integer_targets": int(len(d)),
        "predicted_push_rate": float(d["p_push"].mean()),
        "observed_push_rate": float(observed.mean()),
        "absolute_push_rate_error": float(abs(d["p_push"].mean() - observed.mean())),
    }


def line_advantage_curve(detail: pd.DataFrame) -> list[dict]:
    out = []
    for delta, x in detail.groupby("delta"):
        out.append({
            "delta": float(delta),
            "mean_predicted_cover": float(x["p_cover"].mean()),
            "mean_predicted_push": float(x["p_push"].mean()),
            "observed_cover": float((x["actual_class"] == "cover").mean()),
            "observed_push": float((x["actual_class"] == "push").mean()),
            "n": int(len(x)),
        })
    return sorted(out, key=lambda x: x["delta"])


def key_number_diagnostics(detail: pd.DataFrame) -> list[dict]:
    d = detail.copy()
    a = d["target_spread"].abs()
    d["key_group"] = np.select(
        [np.isclose(a, 3.0), np.isclose(a, 3.5), np.isclose(a, 7.0), np.isclose(a, 7.5)],
        ["3", "3.5", "7", "7.5"],
        default="other",
    )
    out = []
    for key in ["3", "3.5", "7", "7.5"]:
        x = d[d["key_group"] == key]
        if x.empty:
            continue
        out.append({
            "target_abs_spread": key,
            "n": int(len(x)),
            "brier3": float(x["brier3"].mean()),
            "predicted_push": float(x["p_push"].mean()),
            "observed_push": float((x["actual_class"] == "push").mean()),
        })
    return out


def run(df: pd.DataFrame) -> tuple[dict, pd.DataFrame]:
    seasons = sorted(int(x) for x in df["season"].unique())
    test_seasons = [s for i, s in enumerate(seasons) if i >= MIN_TRAIN_SEASONS]
    fold_summaries = []
    all_details = []

    for test_season in test_seasons:
        train = df[df["season"] < test_season].copy()
        test = df[df["season"] == test_season].copy()
        if train["season"].nunique() < MIN_TRAIN_SEASONS or test.empty:
            continue

        params, tuning = select_kernel_params(train)
        print(f"[fold {test_season}] selected kernel {params}")
        normal = evaluate_model_on_rows(train, test, "normal")
        empirical = evaluate_model_on_rows(train, test, "global_empirical")
        conditional = evaluate_model_on_rows(train, test, "conditional", params)
        all_details.extend([normal, empirical, conditional])

        s_norm = summarize_detail(normal)
        s_emp = summarize_detail(empirical)
        s_cond = summarize_detail(conditional)
        fold_summaries.append({
            "test_season": test_season,
            "kernel_params": list(params),
            "tuning": tuning,
            "normal": s_norm,
            "global_empirical": s_emp,
            "conditional": s_cond,
            "normal_minus_conditional_brier": s_norm["mean_per_game_brier3"] - s_cond["mean_per_game_brier3"],
            "global_empirical_minus_conditional_brier": s_emp["mean_per_game_brier3"] - s_cond["mean_per_game_brier3"],
        })
        print(
            f"  Brier normal={s_norm['mean_per_game_brier3']:.4f} "
            f"global={s_emp['mean_per_game_brier3']:.4f} conditional={s_cond['mean_per_game_brier3']:.4f}"
        )

    detail = pd.concat(all_details, ignore_index=True)
    norm_delta = [f["normal_minus_conditional_brier"] for f in fold_summaries]
    emp_delta = [f["global_empirical_minus_conditional_brier"] for f in fold_summaries]
    cond = detail[detail["model"] == "conditional"].copy()
    normal = detail[detail["model"] == "normal"].copy()
    empirical = detail[detail["model"] == "global_empirical"].copy()

    mean_norm_delta = float(np.mean(norm_delta))
    norm_ci = bootstrap_mean_ci(norm_delta, seed=716, reps=10000)
    mean_emp_delta = float(np.mean(emp_delta))
    emp_ci = bootstrap_mean_ci(emp_delta, seed=717, reps=10000)

    if mean_norm_delta > 0 and norm_ci[0] > 0:
        if mean_emp_delta > 0 and emp_ci[0] > 0:
            verdict = "PROMISING CONDITIONAL DISCRETE MODEL: challenger beat both normal and global empirical baselines with season-bootstrap intervals above zero. Advance to calibration/robustness; no production promotion yet."
        else:
            verdict = "DISCRETENESS HELPS, CONDITIONALITY NOT PROVEN: challenger beat normal robustly, but did not robustly beat global empirical. Retain empirical discreteness; do not claim spread/total conditioning adds stable value."
    else:
        verdict = "NO ROBUST DISCRETE CHALLENGER ADVANTAGE OVER NORMAL: keep the simpler probability baseline and revisit model form before promotion."

    result = {
        "experiment": "V2-0006",
        "verdict": verdict,
        "heldout_seasons": [f["test_season"] for f in fold_summaries],
        "n_unique_heldout_games": int(cond["game_id"].nunique()),
        "offsets": OFFSETS.tolist(),
        "primary": {
            "mean_normal_minus_conditional_brier": mean_norm_delta,
            "season_bootstrap_95pct": norm_ci,
            "mean_global_empirical_minus_conditional_brier": mean_emp_delta,
            "global_empirical_season_bootstrap_95pct": emp_ci,
        },
        "aggregate": {
            "normal": summarize_detail(normal) | closing_metrics(normal) | {"push_calibration": push_calibration(normal)},
            "global_empirical": summarize_detail(empirical) | closing_metrics(empirical) | {"push_calibration": push_calibration(empirical)},
            "conditional": summarize_detail(cond) | closing_metrics(cond) | {"push_calibration": push_calibration(cond)},
        },
        "conditional_line_advantage_curve": line_advantage_curve(cond),
        "conditional_key_number_diagnostics": key_number_diagnostics(cond),
        "folds": fold_summaries,
        "limitations": [
            "Closing market is a research fair-line baseline, not a historical Sly Friday snapshot.",
            "Alternate line offsets evaluate distribution shape; they do not assert those lines were historically available.",
            "Seven offsets for one game are reduced to a per-game mean before the primary season-level comparison.",
            "No 2026 outcomes are used.",
            "Key-number subgroup results are diagnostic and cannot override aggregate promotion gates.",
        ],
    }
    return result, detail


def write_report(result: dict, detail: pd.DataFrame, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "results.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    detail.to_csv(out_dir / "predictions.csv", index=False)

    p = result["primary"]
    agg = result["aggregate"]
    lines = [
        "# V2-0006 Discrete Margin / Key-Number Experiment",
        "",
        f"**Verdict:** {result['verdict']}",
        "",
        f"Held-out games: **{result['n_unique_heldout_games']}** across {result['heldout_seasons']}.",
        "",
        "## Aggregate probability quality",
        "",
        "| Model | Per-game 3-class Brier | 3-class log loss | Closing-line Brier | Closing non-push binary Brier | Push rate predicted / observed |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for key, label in [("normal", "Normal lattice"), ("global_empirical", "Global empirical"), ("conditional", "Conditional empirical")]:
        x = agg[key]
        pc = x["push_calibration"]
        lines.append(
            f"| {label} | {x['mean_per_game_brier3']:.4f} | {x['mean_per_game_logloss3']:.4f} | {x['closing_brier3']:.4f} | {x['closing_nonpush_binary_brier']:.4f} | {pc['predicted_push_rate']:.2%} / {pc['observed_push_rate']:.2%} |"
        )
    lines += [
        "",
        "## Primary comparisons",
        "",
        f"- Normal minus conditional Brier: **{p['mean_normal_minus_conditional_brier']:+.5f}**, season-bootstrap 95% CI **[{p['season_bootstrap_95pct'][0]:+.5f}, {p['season_bootstrap_95pct'][1]:+.5f}]**.",
        f"- Global empirical minus conditional Brier: **{p['mean_global_empirical_minus_conditional_brier']:+.5f}**, season-bootstrap 95% CI **[{p['global_empirical_season_bootstrap_95pct'][0]:+.5f}, {p['global_empirical_season_bootstrap_95pct'][1]:+.5f}]**.",
        "",
        "## Line-advantage curve (conditional model)",
        "",
        "| Target spread advantage vs market | Pred cover | Obs cover | Pred push | Obs push |",
        "|---:|---:|---:|---:|---:|",
    ]
    for x in result["conditional_line_advantage_curve"]:
        lines.append(
            f"| {x['delta']:+.1f} | {x['mean_predicted_cover']:.2%} | {x['observed_cover']:.2%} | {x['mean_predicted_push']:.2%} | {x['observed_push']:.2%} |"
        )
    lines += [
        "",
        "## Guardrails",
        "",
        "- Positive comparison values mean the conditional model lowered Brier score.",
        "- This is a probability-distribution experiment around the closing market, not a historical Sly stale-line backtest.",
        "- No production pick or wager logic changes from this experiment alone.",
    ]
    (out_dir / "REPORT.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--start-season", type=int, default=2016)
    ap.add_argument("--end-season", type=int, default=2025)
    ap.add_argument("--out-dir", type=Path, default=Path("v2/results/discrete_margin"))
    args = ap.parse_args()
    if args.end_season >= 2026:
        raise SystemExit("2026+ is intentionally excluded from this tuning experiment")
    df = load_games(args.start_season, args.end_season)
    result, detail = run(df)
    write_report(result, detail, args.out_dir)
    print(json.dumps({
        "verdict": result["verdict"],
        "primary": result["primary"],
        "aggregate": result["aggregate"],
        "line_advantage_curve": result["conditional_line_advantage_curve"],
        "key_numbers": result["conditional_key_number_diagnostics"],
    }, indent=2))


if __name__ == "__main__":
    main()
