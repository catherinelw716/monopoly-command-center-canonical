"""Second-stage Week 3 game-count and sizing optimizer using common random numbers.

The stable candidate order is frozen from the 15-run stability/red-team pass. This
stage compares 4-, 5-, and 6-game structures and deployment levels without allowing
Monte Carlo noise to reshuffle game identity.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Mapping

import numpy as np

from monopoly_simulator import Bet, load_regular_rules
from monopoly_tournament_optimizer import (
    OptimizerConfig,
    default_field_scenarios,
    evaluate_portfolio_across_scenarios,
    load_field_state,
    prepare_field_paths,
    serialize_bets,
)
from monopoly_robust_optimizer import _current_week_downside, _scenario_utility, shrink_probabilities
from run_week3_sunday_robust import load_probs

ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT = ROOT / "v2/season_2026/week_03_current_market_2026-09-27_1120ET.json"
MODEL = ROOT / "v2/model_artifacts/v2_global_hybrid_2016_2025.json"
STATE = ROOT / "v2/season_2026/week_02_field_state.json"
RULES = ROOT / "v2/monopoly_contract.json"
OUTPUT = ROOT / "v2/results/week3_second_stage_sizing.json"

# Stability-tested order. First four are the stable core; fifth/sixth are marginal adds.
CANDIDATES = {
    "Catherine": (
        ("LAC @ BUF", "home", "BUF -7", True),
        ("CAR @ CLE", "away", "CAR -2.5", False),
        ("KC @ MIA", "away", "KC -10.5", False),
        ("ARI @ SF", "away", "ARI +8.5", False),
        ("BAL @ DAL", "home", "DAL +3.5", False),
        ("HOU @ IND", "home", "IND +1.5", False),
    ),
    "Amanda": (
        ("NE @ JAX", "away", "NE +3", True),
        ("SEA @ WAS", "away", "SEA -7.5", False),
        ("MIN @ TB", "away", "MIN -1.5", False),
        ("LAR @ DEN", "home", "DEN +2.5", False),
        ("CIN @ PIT", "home", "PIT +3.5", False),
        ("NYJ @ DET", "home", "DET -6.5", False),
    ),
}

DEPLOYMENT_FRACTIONS = (0.08, 0.10, 0.12, 0.15, 0.18, 0.20, 0.25, 0.30, 0.35)
GAME_COUNTS = (4, 5, 6)
EDGE_SHRINK_FACTORS = (1.00, 0.75, 0.50, 0.25)


def build_portfolio(
    balances: Mapping[str, int], rules, c_fraction: float, a_fraction: float,
    c_games: int, a_games: int,
) -> Dict[str, tuple[Bet, ...]]:
    out = {}
    for entry, fraction, n_games in (
        ("Catherine", c_fraction, c_games),
        ("Amanda", a_fraction, a_games),
    ):
        selected = CANDIDATES[entry][:n_games]
        balance = int(balances[entry])
        target = int(np.floor(balance * fraction / rules.wager_increment) * rules.wager_increment)
        minimum_total = n_games * rules.minimum_wager
        target = max(target, minimum_total)
        target = min(target, balance)
        amounts = [rules.minimum_wager] * n_games
        amounts[0] += target - minimum_total
        out[entry] = tuple(
            Bet(gid, side, int(amount))
            for (gid, side, _label, _material), amount in zip(selected, amounts)
        )
    return out


def main() -> None:
    state = load_field_state(STATE)
    rules = load_regular_rules(RULES)
    _, probs, ranking = load_probs(SNAPSHOT, MODEL)
    balances = {"Catherine": state.catherine_balance, "Amanda": state.amanda_balance}
    scenarios = default_field_scenarios()

    # Higher-resolution evaluation with common random numbers across every candidate.
    cfg = OptimizerConfig(simulations=3000, seed=716)
    prepared = prepare_field_paths(state, scenarios, cfg)
    prob_sets = {f: shrink_probabilities(probs, f) for f in EDGE_SHRINK_FACTORS}

    rows = []
    for cg in GAME_COUNTS:
        for ag in GAME_COUNTS:
            for cf in DEPLOYMENT_FRACTIONS:
                for af in DEPLOYMENT_FRACTIONS:
                    bets = build_portfolio(balances, rules, cf, af, cg, ag)
                    stress = []
                    base_metrics = None
                    base_downside = None
                    weighted_utilities = []
                    for idx, factor in enumerate(EDGE_SHRINK_FACTORS):
                        pset = prob_sets[factor]
                        downside = _current_week_downside(
                            balances, bets, pset, rules, cfg,
                            seed=cfg.seed + 5000 + idx * 100, alpha=0.10,
                        )
                        retention = float(downside["minimum_entry_cvar_retention"])
                        metrics = evaluate_portfolio_across_scenarios(
                            balances, bets, pset, rules, state, scenarios, cfg,
                            prepared_field_paths=prepared,
                        )
                        weighted_utilities.append(_scenario_utility(metrics["weighted"], retention))
                        if factor == 1.0:
                            base_metrics = metrics
                            base_downside = downside
                        for scenario_name, m in metrics["by_scenario"].items():
                            stress.append({
                                "edge_shrink_factor": factor,
                                "field_scenario": scenario_name,
                                "expected_household_prize_share": m["expected_household_prize_share"],
                                "future_minimum_failure_risk": m["future_minimum_failure_risk"],
                                "current_week_cvar_retention": retention,
                                "utility": _scenario_utility(m, retention),
                            })

                    assert base_metrics is not None and base_downside is not None
                    weighted = base_metrics["weighted"]
                    rows.append({
                        "c_games": cg,
                        "a_games": ag,
                        "c_fraction": cf,
                        "a_fraction": af,
                        "bets_by_entry": serialize_bets(bets),
                        "outlay_by_entry": base_metrics["outlay_by_entry"],
                        "household_outlay": base_metrics["household_outlay"],
                        "robust_floor_utility": min(x["utility"] for x in stress),
                        "robust_average_utility": float(np.mean(weighted_utilities)),
                        "base_expected_household_prize_share": weighted["expected_household_prize_share"],
                        "base_p_any_cash": weighted["p_any_cash"],
                        "base_p_top3": weighted["p_top3"],
                        "base_p_first": weighted["p_first"],
                        "base_future_minimum_failure_risk": weighted["future_minimum_failure_risk"],
                        "base_current_week_downside": base_downside,
                    })

    def key(r):
        return (
            r["robust_floor_utility"],
            r["robust_average_utility"],
            r["base_expected_household_prize_share"],
            -r["base_future_minimum_failure_risk"],
            -r["household_outlay"],
        )

    rows.sort(key=key, reverse=True)
    by_pair = []
    for cg in GAME_COUNTS:
        for ag in GAME_COUNTS:
            subset = [r for r in rows if r["c_games"] == cg and r["a_games"] == ag]
            by_pair.append(max(subset, key=key))
    by_pair.sort(key=key, reverse=True)

    result = {
        "status": "WEEK3_SECOND_STAGE_GAMECOUNT_SIZING_CRN",
        "simulations": cfg.simulations,
        "seed": cfg.seed,
        "deployment_grid": list(DEPLOYMENT_FRACTIONS),
        "game_counts_tested": list(GAME_COUNTS),
        "edge_shrink_factors": list(EDGE_SHRINK_FACTORS),
        "stable_candidate_order": {
            entry: [
                {"game_id": gid, "side": side, "label": label, "material_market_edge": material}
                for gid, side, label, material in games
            ]
            for entry, games in CANDIDATES.items()
        },
        "best_overall": rows[0],
        "best_by_game_count_pair": by_pair,
        "top20": rows[:20],
        "probability_ranking": ranking,
        "guardrails": [
            "Frozen NFL probabilities are unchanged.",
            "All candidates use common random numbers through identical seeds and precomputed field paths.",
            "The stable candidate order is frozen before sizing; this stage only chooses 4/5/6 depth and deployment.",
            "Supporting games remain at the $100 minimum because they have no material frozen V2 price edge.",
            "Incremental dollars go only to BUF -7 for Catherine and NE +3 for Amanda.",
            "Weather remains contextual analysis only and is not folded into frozen cover probabilities.",
        ],
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps({
        "best_overall": result["best_overall"],
        "best_by_game_count_pair": result["best_by_game_count_pair"],
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
