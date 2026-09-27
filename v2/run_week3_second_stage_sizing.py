"""Second-stage Week 3 sizing optimizer using common random numbers.

The game set is frozen from the 15-run stability/red-team pass. This script answers
only the sizing question: how much total deployment should each entry use once game
selection is held fixed?

All candidate allocations are evaluated on the same simulated NFL draws, field paths,
and continuation paths for a given stress state. This sharply reduces Monte Carlo noise
in pairwise sizing comparisons.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict

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

# Frozen from the 15-run stability pass. Supporting games carry no manufactured edge;
# they remain at the contest minimum and only the material-price-edge anchor is scaled.
FROZEN_GAMES = {
    "Catherine": (
        ("LAC @ BUF", "home"),   # BUF -7 anchor
        ("CAR @ CLE", "away"),   # CAR -2.5
        ("KC @ MIA", "away"),    # KC -10.5
        ("ARI @ SF", "away"),    # ARI +8.5
    ),
    "Amanda": (
        ("NE @ JAX", "away"),    # NE +3 anchor
        ("SEA @ WAS", "away"),   # SEA -7.5
        ("MIN @ TB", "away"),    # MIN -1.5
        ("LAR @ DEN", "home"),   # DEN +2.5
    ),
}

DEPLOYMENT_FRACTIONS = (0.05, 0.075, 0.10, 0.125, 0.15, 0.175, 0.20, 0.25, 0.30, 0.35)
EDGE_SHRINK_FACTORS = (1.00, 0.75, 0.50, 0.25)


def round_to_increment(x: float, increment: int) -> int:
    return int(round(x / increment) * increment)


def build_fixed_portfolio(balances: Dict[str, int], c_fraction: float, a_fraction: float, minimum: int, increment: int):
    out = {}
    for entry, fraction in (("Catherine", c_fraction), ("Amanda", a_fraction)):
        balance = int(balances[entry])
        target = round_to_increment(balance * fraction, increment)
        target = max(target, 4 * minimum)
        target = min(target, balance)
        support_total = 3 * minimum
        anchor_amount = target - support_total
        if anchor_amount < minimum:
            anchor_amount = minimum
            target = 4 * minimum
        games = FROZEN_GAMES[entry]
        bets = [Bet(games[0][0], games[0][1], int(anchor_amount))]
        bets.extend(Bet(gid, side, minimum) for gid, side in games[1:])
        out[entry] = tuple(bets)
    return out


def main() -> None:
    state = load_field_state(STATE)
    rules = load_regular_rules(RULES)
    _, probs, ranking = load_probs(SNAPSHOT, MODEL)
    balances = {"Catherine": state.catherine_balance, "Amanda": state.amanda_balance}
    scenarios = default_field_scenarios()

    # Higher-resolution than the selection-stage optimizer. The same cfg seed and the
    # deterministic per-game seeding inside _sample_household_current_week create CRN.
    cfg = OptimizerConfig(simulations=3000, seed=716)
    prepared = prepare_field_paths(state, scenarios, cfg)
    prob_sets = {f: shrink_probabilities(probs, f) for f in EDGE_SHRINK_FACTORS}

    rows = []
    for cf in DEPLOYMENT_FRACTIONS:
        for af in DEPLOYMENT_FRACTIONS:
            bets = build_fixed_portfolio(
                balances, cf, af, rules.minimum_wager, rules.wager_increment
            )
            stress = []
            base_metrics = None
            base_downside = None
            for idx, factor in enumerate(EDGE_SHRINK_FACTORS):
                pset = prob_sets[factor]
                downside = _current_week_downside(
                    balances,
                    bets,
                    pset,
                    rules,
                    cfg,
                    seed=cfg.seed + 5000 + idx * 100,
                    alpha=0.10,
                )
                retention = float(downside["minimum_entry_cvar_retention"])
                metrics = evaluate_portfolio_across_scenarios(
                    balances,
                    bets,
                    pset,
                    rules,
                    state,
                    scenarios,
                    cfg,
                    prepared_field_paths=prepared,
                )
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
            floor_utility = min(x["utility"] for x in stress)
            avg_utility = sum(x["utility"] for x in stress) / len(stress)
            weighted = base_metrics["weighted"]
            row = {
                "c_fraction": cf,
                "a_fraction": af,
                "bets_by_entry": serialize_bets(bets),
                "outlay_by_entry": base_metrics["outlay_by_entry"],
                "household_outlay": base_metrics["household_outlay"],
                "robust_floor_utility": floor_utility,
                "robust_average_utility": avg_utility,
                "base_expected_household_prize_share": weighted["expected_household_prize_share"],
                "base_p_any_cash": weighted["p_any_cash"],
                "base_future_minimum_failure_risk": weighted["future_minimum_failure_risk"],
                "base_current_week_downside": base_downside,
                "stress": stress,
            }
            rows.append(row)

    # Primary: worst-state utility. Secondary: average utility, lower failure risk,
    # then lower outlay. Because every candidate shares the same random draws, these
    # comparisons are much less sensitive to Monte Carlo realization noise.
    rows.sort(
        key=lambda r: (
            r["robust_floor_utility"],
            r["robust_average_utility"],
            -r["base_future_minimum_failure_risk"],
            -r["household_outlay"],
        ),
        reverse=True,
    )

    result = {
        "status": "WEEK3_SECOND_STAGE_SIZING_CRN",
        "simulations": cfg.simulations,
        "seed": cfg.seed,
        "deployment_grid": list(DEPLOYMENT_FRACTIONS),
        "edge_shrink_factors": list(EDGE_SHRINK_FACTORS),
        "frozen_games": {
            k: [{"game_id": gid, "side": side} for gid, side in v]
            for k, v in FROZEN_GAMES.items()
        },
        "probability_ranking": ranking,
        "best": rows[0],
        "top10": rows[:10],
        "all_candidates": rows,
        "guardrails": [
            "Game selection is frozen before sizing; this stage cannot swap games.",
            "Supporting games remain at the $100 contest minimum because they have no material frozen V2 price edge.",
            "Incremental dollars are assigned only to BUF -7 for Catherine and NE +3 for Amanda.",
            "Common random numbers are used across all sizing candidates through identical seeds and precomputed field paths.",
            "Sizing is stress-tested across conservative/median/aggressive field scenarios and 100/75/50/25% retained directional model edge.",
            "This is a V2 research sizing result, not automatic wager execution."
        ],
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps({"best": result["best"], "top10": result["top10"]}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
