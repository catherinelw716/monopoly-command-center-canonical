"""Step 8B: Week 4 Friday sizing calibration / red-team pass.

This does not change NFL probabilities. It asks a narrower question than the robust
optimizer: conditional on the Friday probability state, what happens as household
capital deployment is deliberately increased?  Each deployment band is optimized
across game-count and overlap structure, while the Step-7 uncertainty stresses remain
in force.
"""
from __future__ import annotations

import json
from pathlib import Path

from monopoly_tournament_optimizer import OptimizerConfig, default_field_scenarios, load_field_state, serialize_bets
from monopoly_simulator import load_regular_rules
from monopoly_robust_optimizer import optimize_robust_household
from run_week4_friday_optimizer import (
    CONTEXTUAL_PREFERENCES,
    EDGE_SHRINK_FACTORS,
    FIELD,
    GAME_COUNTS,
    OVERLAP_MODES,
    RULES,
    SLY,
    label_bets,
    load_probability_states,
    compact_metrics,
)

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "v2/results/week_04_sizing_calibration.json"

# Same fraction is applied to both entries in each band so the comparison is easy to
# interpret at the household level.  Actual wager totals are still rounded to $100.
DEPLOYMENT_BANDS = (0.10, 0.15, 0.20, 0.25, 0.30, 0.35)


def summarize(best: dict, starting_household: int) -> dict:
    bets = label_bets(serialize_bets(best["bets_by_entry"]))
    metrics = compact_metrics(best["base_metrics"])
    outlay = int(metrics["household_outlay"])
    return {
        "bets_by_entry": bets,
        "parameters": best["parameters"],
        "household_outlay": outlay,
        "household_deployment_fraction": outlay / starting_household,
        "outlay_by_entry": metrics["outlay_by_entry"],
        "overlap": metrics["overlap"],
        "expected_household_prize_share": metrics["expected_household_prize_share"],
        "p_any_cash": metrics["p_any_cash"],
        "p_top3": metrics["p_top3"],
        "p_first": metrics["p_first"],
        "future_minimum_failure_risk": metrics["future_minimum_failure_risk"],
        "minimum_entry_cvar_retention": best["base_current_week_downside"]["minimum_entry_cvar_retention"],
        "robust_floor_utility": best["robust_floor_utility"],
        "robust_average_utility": best["robust_average_utility"],
    }


def main() -> None:
    base, zero, vi, action = load_probability_states()
    state = load_field_state(FIELD)
    rules = load_regular_rules(RULES)
    balances = {"Catherine": state.catherine_balance, "Amanda": state.amanda_balance}
    starting_household = sum(balances.values())
    scenarios = default_field_scenarios()
    cfg = OptimizerConfig(simulations=1200, seed=716)

    rows = []
    for band in DEPLOYMENT_BANDS:
        best = optimize_robust_household(
            balances,
            base,
            rules,
            state,
            scenarios=scenarios,
            cfg=cfg,
            fractions=(band,),
            game_counts=GAME_COUNTS,
            overlap_modes=OVERLAP_MODES,
            edge_shrink_factors=EDGE_SHRINK_FACTORS,
            current_week_cvar_alpha=0.10,
            contextual_preferences=CONTEXTUAL_PREFERENCES,
            material_edge_threshold=0.01,
        )
        row = {"target_per_entry_fraction": band, **summarize(best, starting_household)}
        rows.append(row)

    # Marginal changes are deliberately descriptive, not a new optimization objective.
    for i, row in enumerate(rows):
        if i == 0:
            row["marginal_vs_prior_band"] = None
            continue
        prev = rows[i - 1]
        added = row["household_outlay"] - prev["household_outlay"]
        row["marginal_vs_prior_band"] = {
            "additional_outlay": added,
            "delta_expected_prize_share": row["expected_household_prize_share"] - prev["expected_household_prize_share"],
            "delta_p_any_cash": row["p_any_cash"] - prev["p_any_cash"],
            "delta_p_top3": row["p_top3"] - prev["p_top3"],
            "delta_p_first": row["p_first"] - prev["p_first"],
            "delta_future_minimum_failure_risk": row["future_minimum_failure_risk"] - prev["future_minimum_failure_risk"],
            "delta_minimum_entry_cvar_retention": row["minimum_entry_cvar_retention"] - prev["minimum_entry_cvar_retention"],
        }

    # A separate portfolio set at each band under zero-edge uncertainty.  This prevents
    # a higher-deployment band from looking attractive only because Friday's half-point
    # HOU/SEA signal is assumed to be real.
    zero_edge_rows = []
    for band in DEPLOYMENT_BANDS:
        best = optimize_robust_household(
            balances,
            zero,
            rules,
            state,
            scenarios=scenarios,
            cfg=cfg,
            fractions=(band,),
            game_counts=GAME_COUNTS,
            overlap_modes=OVERLAP_MODES,
            edge_shrink_factors=(1.0,),
            current_week_cvar_alpha=0.10,
            contextual_preferences=CONTEXTUAL_PREFERENCES,
            material_edge_threshold=0.01,
        )
        zero_edge_rows.append({"target_per_entry_fraction": band, **summarize(best, starting_household)})

    result = {
        "season": 2026,
        "week": 4,
        "snapshot_type": "FRIDAY_SIZING_CALIBRATION",
        "status": "STEP_8B_COMPLETE_PROVISIONAL_NOT_SUBMISSION",
        "balances": balances,
        "household_balance": starting_household,
        "simulations": cfg.simulations,
        "deployment_bands": list(DEPLOYMENT_BANDS),
        "base_state_band_comparison": rows,
        "zero_edge_band_comparison": zero_edge_rows,
        "interpretation_rules": [
            "Do not choose a band from expected prize share alone.",
            "Look for diminishing marginal tournament upside relative to CVaR and future-minimum risk.",
            "No-edge filler positions remain $100 unless a validated sizing edge emerges.",
            "Most incremental capital should flow to HOU/SEA under the Friday base state because they are the only sizing edges.",
            "If higher deployment is attractive only under the Action-derived HOU/SEA edge and not under zero-edge stress, treat that as fragile.",
            "Sunday PRE_KICK_FINAL reruns this calibration with fresh market/injury/weather inputs."
        ],
    }
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
