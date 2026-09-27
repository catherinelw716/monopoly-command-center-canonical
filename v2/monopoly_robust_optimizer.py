"""Robust V2-0009 household optimizer.

This layer keeps expected household prize share as the headline tournament metric but
makes uncertainty and future viability decision-relevant when choosing a portfolio.
It does not impose an arbitrary bankroll cap.

Candidate portfolios are evaluated under:
- conservative / median / aggressive field-policy scenarios; and
- progressively shrunken NFL probability edges (100%, 75%, 50%, 25%).

The primary robust utility for a scenario is:
    expected_household_prize_share * (1 - future_minimum_failure_risk)

The optimizer maximizes the worst such utility across field scenarios and probability
shrink states, then uses average robust utility, base expected prize share, lower
failure risk, and lower deployment as successive tie breakers.
"""
from __future__ import annotations

from typing import Dict, Mapping, Sequence

from monopoly_simulator import GameProbability, RegularSeasonRules
from monopoly_tournament_optimizer import (
    FieldScenario,
    FieldState,
    OptimizerConfig,
    build_joint_candidate,
    default_field_scenarios,
    evaluate_portfolio_across_scenarios,
    prepare_field_paths,
)


def shrink_probabilities(
    probs: Mapping[str, GameProbability], factor: float
) -> Dict[str, GameProbability]:
    """Shrink non-push directional edge toward 50/50 while preserving push mass."""
    factor = float(factor)
    if not 0.0 <= factor <= 1.0:
        raise ValueError("factor must be between 0 and 1")
    out: Dict[str, GameProbability] = {}
    for gid, gp in probs.items():
        nonpush = 1.0 - gp.p_push
        if nonpush <= 0:
            out[gid] = gp
            continue
        cond_home = gp.p_home_cover / nonpush
        shrunk_home = 0.5 + factor * (cond_home - 0.5)
        out[gid] = GameProbability(
            gid,
            nonpush * shrunk_home,
            gp.p_push,
            nonpush * (1.0 - shrunk_home),
        )
    return out


def _scenario_utility(row: Mapping[str, float]) -> float:
    return float(row["expected_household_prize_share"]) * (
        1.0 - float(row["future_minimum_failure_risk"])
    )


def optimize_robust_household(
    balances: Mapping[str, int],
    game_probabilities: Mapping[str, GameProbability],
    rules: RegularSeasonRules,
    field_state: FieldState,
    scenarios: Sequence[FieldScenario] | None = None,
    cfg: OptimizerConfig | None = None,
    fractions: Sequence[float] = (0.10, 0.20, 0.35, 0.50, 0.65, 0.80, 1.00),
    game_counts: Sequence[int] = (4, 5, 6),
    overlap_modes: Sequence[str] = ("shared", "hybrid", "split"),
    edge_shrink_factors: Sequence[float] = (1.00, 0.75, 0.50, 0.25),
) -> Dict[str, object]:
    cfg = cfg or OptimizerConfig()
    scenarios = tuple(scenarios or default_field_scenarios())
    prepared = prepare_field_paths(field_state, scenarios, cfg)
    prob_sets = {float(f): shrink_probabilities(game_probabilities, float(f)) for f in edge_shrink_factors}

    best: Dict[str, object] | None = None
    evaluated = 0
    for cf in fractions:
        for af in fractions:
            for cg in game_counts:
                for ag in game_counts:
                    for mode in overlap_modes:
                        bets = build_joint_candidate(
                            balances, game_probabilities, rules, cf, af, cg, ag, mode
                        )
                        stress_metrics: Dict[str, object] = {}
                        scenario_utilities: list[float] = []
                        weighted_utilities: list[float] = []
                        base_metrics = None
                        for factor in edge_shrink_factors:
                            m = evaluate_portfolio_across_scenarios(
                                balances,
                                bets,
                                prob_sets[float(factor)],
                                rules,
                                field_state,
                                scenarios,
                                cfg,
                                prepared_field_paths=prepared,
                            )
                            if float(factor) == 1.0:
                                base_metrics = m
                            weighted = m["weighted"]
                            weighted_utility = _scenario_utility(weighted)
                            weighted_utilities.append(weighted_utility)
                            per_scenario = {
                                name: {
                                    **row,
                                    "viability_adjusted_prize_utility": _scenario_utility(row),
                                }
                                for name, row in m["by_scenario"].items()
                            }
                            scenario_utilities.extend(
                                x["viability_adjusted_prize_utility"] for x in per_scenario.values()
                            )
                            stress_metrics[f"edge_{float(factor):.2f}"] = {
                                "weighted": {
                                    **weighted,
                                    "viability_adjusted_prize_utility": weighted_utility,
                                },
                                "by_scenario": per_scenario,
                            }

                        assert base_metrics is not None
                        evaluated += 1
                        robust_floor = min(scenario_utilities)
                        robust_average = sum(weighted_utilities) / len(weighted_utilities)
                        base_prize = base_metrics["weighted"]["expected_household_prize_share"]
                        base_failure = base_metrics["weighted"]["future_minimum_failure_risk"]
                        key = (
                            robust_floor,
                            robust_average,
                            base_prize,
                            -base_failure,
                            -base_metrics["household_outlay"],
                        )
                        if best is None or key > best["_key"]:
                            best = {
                                "_key": key,
                                "bets_by_entry": bets,
                                "parameters": {
                                    "c_fraction": cf,
                                    "a_fraction": af,
                                    "c_games": cg,
                                    "a_games": ag,
                                    "overlap_mode": mode,
                                },
                                "robust_floor_utility": robust_floor,
                                "robust_average_utility": robust_average,
                                "base_metrics": base_metrics,
                                "stress_metrics": stress_metrics,
                                "edge_shrink_factors": list(edge_shrink_factors),
                            }
    assert best is not None
    best.pop("_key", None)
    best["evaluated_candidates"] = evaluated
    best["objective"] = (
        "maximize worst-case expected household prize share multiplied by probability "
        "of avoiding future-minimum failure across field scenarios and edge-shrink states"
    )
    return best
