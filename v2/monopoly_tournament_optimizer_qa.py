"""Deterministic QA for the V2-0009 field ensemble and joint optimizer."""
from __future__ import annotations

import math

from monopoly_simulator import GameProbability, RegularSeasonRules, validate_bets
from monopoly_tournament_optimizer import (
    FieldState,
    OptimizerConfig,
    build_joint_candidate,
    default_field_scenarios,
    evaluate_benchmark_set,
    evaluate_portfolio_across_scenarios,
    optimize_joint_household,
    synthesize_opponent_balances,
)


def fixture():
    state = FieldState(
        active_entries=125,
        eliminated_entries=2,
        median_balance=9500,
        top10_floor=16665,
        top5_floor=19400,
        leader_balance=31300,
        catherine_balance=11400,
        catherine_rank=30,
        amanda_balance=10300,
        amanda_rank=44,
        lower_tail_floor_assumption=400,
    )
    rules = RegularSeasonRules(4, 100, 100, 1.0, -1.0, 0.0)
    probs = {
        "g1": GameProbability("g1", 0.60, 0.00, 0.40),
        "g2": GameProbability("g2", 0.42, 0.00, 0.58),
        "g3": GameProbability("g3", 0.55, 0.00, 0.45),
        "g4": GameProbability("g4", 0.52, 0.00, 0.48),
        "g5": GameProbability("g5", 0.51, 0.00, 0.49),
        "g6": GameProbability("g6", 0.50, 0.00, 0.50),
        "g7": GameProbability("g7", 0.48, 0.00, 0.52),
        "g8": GameProbability("g8", 0.50, 0.04, 0.46),
    }
    balances = {"Catherine": 11400, "Amanda": 10300}
    cfg = OptimizerConfig(simulations=120, seed=716, regular_weeks_after_current=2)
    return state, rules, probs, balances, cfg


def main():
    state, rules, probs, balances, cfg = fixture()
    opponents = synthesize_opponent_balances(state)
    assert len(opponents) == 123
    assert opponents.max() == 31300
    assert opponents.min() == 400
    assert all(opponents[i] >= opponents[i + 1] for i in range(len(opponents) - 1))

    scenarios = default_field_scenarios()
    assert math.isclose(sum(s.mixture_weight for s in scenarios), 1.0)
    assert scenarios[0].mean_deployment < scenarios[1].mean_deployment < scenarios[2].mean_deployment

    candidate = build_joint_candidate(balances, probs, rules, 0.35, 0.35, 4, 4, "hybrid")
    for e, bets in candidate.items():
        validate_bets(balances[e], bets, rules)
    g1_amounts = [b.amount for bets in candidate.values() for b in bets if b.game_id == "g1"]
    assert g1_amounts and max(g1_amounts) > 100

    m1 = evaluate_portfolio_across_scenarios(balances, candidate, probs, rules, state, cfg=cfg)
    m2 = evaluate_portfolio_across_scenarios(balances, candidate, probs, rules, state, cfg=cfg)
    assert m1["weighted"] == m2["weighted"], (m1["weighted"], m2["weighted"])
    for v in m1["weighted"].values():
        assert 0.0 <= v <= 1.0

    bench = evaluate_benchmark_set(balances, probs, rules, state, cfg=cfg)
    names = {x["strategy"] for x in bench}
    assert "minimum_4x100" in names
    assert "fractional_kelly_quarter" in names
    assert "identical_top4_30pct" in names

    opt = optimize_joint_household(
        balances,
        probs,
        rules,
        state,
        cfg=cfg,
        fractions=(0.20, 0.40),
        game_counts=(4, 5),
        overlap_modes=("shared", "hybrid"),
    )
    assert opt["evaluated_candidates"] == 32
    assert opt["parameters"]["overlap_mode"] in {"shared", "hybrid"}
    for e, bets in opt["bets_by_entry"].items():
        validate_bets(balances[e], bets, rules)
    assert opt["metrics"]["weighted"]["expected_household_prize_share"] >= 0.0
    print("V2-0009 tournament optimizer QA passed")


if __name__ == "__main__":
    main()
