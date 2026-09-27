"""V2 diagnostic ablation after the first Ridge challenger failed to beat market.

Research-only. Does NOT change production.

Purpose:
- Hold the closing-market baseline fixed.
- Re-run season walk-forward Ridge residual models with smaller feature families.
- Identify whether any compact football feature subset adds stable information.
- Diagnose early/late season, favorite/dog, and spread-size behavior.

Important: closing lines are a research baseline only; this is not a Sly Friday
stale-line backtest. No 2026 outcomes are used.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error

from run_first_experiment import (
    ALPHAS,
    MIN_TRAIN_SEASONS,
    bootstrap_mean_ci,
    build_lightweight_history,
    choose_alpha,
    make_ridge,
)


def rmse(y_true, y_pred):
    return float(math.sqrt(mean_squared_error(y_true, y_pred)))


def existing(df: pd.DataFrame, cols: list[str]) -> list[str]:
    return [c for c in cols if c in df.columns]


def discover_feature_sets(df: pd.DataFrame) -> dict[str, list[str]]:
    diff4 = sorted(c for c in df.columns if c.startswith("diff_") and c.endswith("_roll4"))
    diff8 = sorted(c for c in df.columns if c.startswith("diff_") and c.endswith("_roll8"))
    market_context = existing(df, ["home_spread_closing", "total_line"])
    sample_context = existing(df, ["home_prior_games_count", "away_prior_games_count"])
    rest = existing(df, ["rest_diff"])

    pass4 = [c for c in diff4 if "pass_epa" in c]
    pass8 = [c for c in diff8 if "pass_epa" in c]
    epa_success4 = [c for c in diff4 if ("epa" in c or "success" in c)]
    epa_success8 = [c for c in diff8 if ("epa" in c or "success" in c)]

    sets = {
        "roll4_all": market_context + sample_context + rest + diff4,
        "roll8_all": market_context + sample_context + rest + diff8,
        "roll4_plus_roll8": market_context + sample_context + rest + diff4 + diff8,
        "passing_only": market_context + sample_context + pass4 + pass8,
        "epa_success_no_rest": market_context + sample_context + epa_success4 + epa_success8,
        "epa_success_with_rest": market_context + sample_context + rest + epa_success4 + epa_success8,
    }
    return {k: list(dict.fromkeys(v)) for k, v in sets.items() if v}


def fit_variant_walkforward(df: pd.DataFrame, features: list[str], variant: str):
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
        resid = model.predict(test[features])
        market_margin = test["market_pred_margin"].to_numpy(float)
        ridge_margin = market_margin + resid
        y = test["home_margin"].to_numpy(float)

        metrics = {
            "variant": variant,
            "test_season": int(test_season),
            "n_games": int(len(test)),
            "alpha": float(alpha),
            "alpha_selection": alpha_meta,
            "market_mae": float(mean_absolute_error(y, market_margin)),
            "ridge_mae": float(mean_absolute_error(y, ridge_margin)),
            "market_rmse": rmse(y, market_margin),
            "ridge_rmse": rmse(y, ridge_margin),
        }
        metrics["mae_delta_market_minus_ridge"] = metrics["market_mae"] - metrics["ridge_mae"]
        metrics["rmse_delta_market_minus_ridge"] = metrics["market_rmse"] - metrics["ridge_rmse"]
        folds.append(metrics)

        d = test[["season", "week", "game_id", "home_team", "away_team", "home_margin", "home_spread_closing"]].copy()
        d["variant"] = variant
        d["market_pred_margin"] = market_margin
        d["ridge_pred_margin"] = ridge_margin
        d["ridge_pred_residual"] = resid
        d["market_abs_error"] = np.abs(y - market_margin)
        d["ridge_abs_error"] = np.abs(y - ridge_margin)
        d["mae_gain"] = d["market_abs_error"] - d["ridge_abs_error"]
        d["ats_margin_home_closing"] = d["home_margin"] + d["home_spread_closing"]
        d["ridge_selected_home"] = resid >= 0
        d["ridge_selected_hit"] = np.where(
            d["ats_margin_home_closing"] == 0,
            np.nan,
            np.where(d["ridge_selected_home"], d["ats_margin_home_closing"] > 0, d["ats_margin_home_closing"] < 0),
        )
        details.append(d)

    all_detail = pd.concat(details, ignore_index=True)
    mae_deltas = [f["mae_delta_market_minus_ridge"] for f in folds]
    rmse_deltas = [f["rmse_delta_market_minus_ridge"] for f in folds]
    summary = {
        "variant": variant,
        "features": features,
        "n_features": len(features),
        "n_test_games": int(sum(f["n_games"] for f in folds)),
        "test_seasons": [f["test_season"] for f in folds],
        "mean_market_mae": float(np.mean([f["market_mae"] for f in folds])),
        "mean_ridge_mae": float(np.mean([f["ridge_mae"] for f in folds])),
        "mean_mae_improvement": float(np.mean(mae_deltas)),
        "mae_improvement_95pct_season_bootstrap": bootstrap_mean_ci(mae_deltas, seed=716 + len(features)),
        "mean_market_rmse": float(np.mean([f["market_rmse"] for f in folds])),
        "mean_ridge_rmse": float(np.mean([f["ridge_rmse"] for f in folds])),
        "mean_rmse_improvement": float(np.mean(rmse_deltas)),
        "pooled_selected_side_hit_rate": float(all_detail["ridge_selected_hit"].dropna().mean()),
        "folds": folds,
    }
    return summary, all_detail


def subgroup_report(detail: pd.DataFrame) -> dict:
    d = detail.copy()
    d["season_phase"] = np.where(d["week"] <= 5, "weeks_1_5", np.where(d["week"] <= 10, "weeks_6_10", "weeks_11_plus"))
    d["home_role"] = np.where(d["home_spread_closing"] < 0, "home_favorite", np.where(d["home_spread_closing"] > 0, "home_underdog", "pickem"))
    abs_spread = d["home_spread_closing"].abs()
    d["spread_bucket"] = pd.cut(abs_spread, [-0.01, 2.5, 3.5, 6.5, 9.5, 100], labels=["0_to_2.5", "3_to_3.5", "4_to_6.5", "7_to_9.5", "10_plus"])

    def one(group_col: str):
        out = []
        for key, x in d.groupby(group_col, observed=True):
            if len(x) == 0:
                continue
            out.append({
                "group": str(key),
                "n": int(len(x)),
                "mean_mae_gain": float(x["mae_gain"].mean()),
                "selected_side_hit_rate": float(x["ridge_selected_hit"].dropna().mean()) if x["ridge_selected_hit"].notna().any() else None,
            })
        return out

    return {
        "season_phase": one("season_phase"),
        "home_role": one("home_role"),
        "spread_bucket": one("spread_bucket"),
    }


def run(df_pl):
    df = df_pl.to_pandas()
    df = df[df["home_margin"].notna() & df["home_spread_closing"].notna()].copy()
    df["market_pred_margin"] = -df["home_spread_closing"].astype(float)
    df["market_residual"] = df["home_margin"].astype(float) - df["market_pred_margin"]

    feature_sets = discover_feature_sets(df)
    summaries = []
    detail_parts = []
    subgroup = {}

    for name, features in feature_sets.items():
        print(f"[variant] {name}: {len(features)} features")
        s, detail = fit_variant_walkforward(df, features, name)
        summaries.append(s)
        detail_parts.append(detail)
        subgroup[name] = subgroup_report(detail)
        lo, hi = s["mae_improvement_95pct_season_bootstrap"]
        print(f"  MAE improvement={s['mean_mae_improvement']:.4f} CI=[{lo:.4f},{hi:.4f}] hit={s['pooled_selected_side_hit_rate']:.3f}")

    ranked = sorted(summaries, key=lambda x: x["mean_mae_improvement"], reverse=True)
    best = ranked[0]
    lo, hi = best["mae_improvement_95pct_season_bootstrap"]
    if best["mean_mae_improvement"] > 0 and lo > 0:
        verdict = f"PROMISING COMPACT SIGNAL: {best['variant']} beat the market baseline on average MAE with a season-bootstrap CI above zero. Advance only this compact family to probability/discrete-margin testing; no production promotion."
    elif best["mean_mae_improvement"] > 0:
        verdict = f"WEAK/MIXED SIGNAL: {best['variant']} had the best average MAE improvement, but its season-bootstrap interval includes zero. Do not promote; use as a research challenger only."
    else:
        verdict = "NO COMPACT FOOTBALL FEATURE SET BEAT MARKET ON AVERAGE. Keep market-only as research champion and shift priority toward discrete margins/key numbers and Monopoly stale-line price capture."

    return {
        "experiment": "V2-DIAGNOSTIC-ABLATION-001",
        "purpose": "diagnose whether compact rolling football feature families add stable residual information beyond closing market",
        "limitations": [
            "Closing market is a research baseline, not a historical Sly/Friday snapshot.",
            "No 2026 outcomes are used.",
            "Subgroup results are diagnostic and not promotion evidence due multiple comparisons.",
            "This experiment evaluates fair-margin error and selected-side hit rate; calibrated ATS probabilities are a later registered stage.",
        ],
        "variants_ranked": ranked,
        "subgroups": subgroup,
        "verdict": verdict,
    }, pd.concat(detail_parts, ignore_index=True)


def write_report(result: dict, detail: pd.DataFrame, out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "results.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    detail.to_csv(out_dir / "predictions_by_variant.csv", index=False)

    lines = [
        "# V2 Diagnostic Ablation",
        "",
        f"**Verdict:** {result['verdict']}",
        "",
        "## Variant ranking",
        "",
        "| Variant | Features | Market MAE | Ridge MAE | Improvement | 95% season-bootstrap CI | Selected-side hit |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for s in result["variants_ranked"]:
        lo, hi = s["mae_improvement_95pct_season_bootstrap"]
        lines.append(
            f"| {s['variant']} | {s['n_features']} | {s['mean_market_mae']:.3f} | {s['mean_ridge_mae']:.3f} | {s['mean_mae_improvement']:+.3f} | [{lo:+.3f}, {hi:+.3f}] | {s['pooled_selected_side_hit_rate']:.1%} |"
        )
    lines += [
        "",
        "## Interpretation rules",
        "",
        "- Positive improvement means Ridge lowered MAE versus the closing-market baseline.",
        "- A subgroup result cannot promote a feature family; it is hypothesis-generating only.",
        "- If the best compact family still lacks robust improvement, V2 remains market-first rather than escalating model complexity.",
        "- This is not a Friday-to-Sunday stale-line test.",
    ]
    (out_dir / "REPORT.md").write_text("\n".join(lines), encoding="utf-8")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--start-season", type=int, default=2016)
    ap.add_argument("--end-season", type=int, default=2025)
    ap.add_argument("--out-dir", type=Path, default=Path("v2/results/diagnostic_ablation"))
    args = ap.parse_args()
    if args.end_season >= 2026:
        raise SystemExit("2026+ is intentionally excluded from this architecture/tuning experiment")
    df = build_lightweight_history(args.start_season, args.end_season)
    result, detail = run(df)
    write_report(result, detail, args.out_dir)
    best = result["variants_ranked"][0]["variant"]
    print(json.dumps({
        "verdict": result["verdict"],
        "ranking": [{"variant": x["variant"], "improvement": x["mean_mae_improvement"], "ci": x["mae_improvement_95pct_season_bootstrap"], "hit": x["pooled_selected_side_hit_rate"]} for x in result["variants_ranked"]],
        "best_variant_subgroups": {"variant": best, **result["subgroups"][best]},
    }, indent=2))


if __name__ == "__main__":
    main()
