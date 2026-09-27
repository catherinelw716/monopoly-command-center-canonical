"""Robust V2-0009 household optimizer.

This layer keeps expected household prize share as the headline tournament metric but
makes uncertainty, future viability, and immediate per-entry downside decision-relevant
when choosing a portfolio. It does not impose an arbitrary bankroll cap.

Candidate portfolios are evaluated under:
- conservative / median / aggressive field-policy scenarios; and
- progressively shrunken NFL probability edges (100%, 75%, 50%, 25%).

For each edge-shrink state, the optimizer also simulates the current week and measures
10% CVaR capital retention for Catherine and Amanda separately. The lower of the two
entry-level retention ratios is used as the immediate downside score. This prevents the
household objective from treating one entry as disposable merely because the other entry
survives.

A contextual tiebreak layer may rank/select games whose frozen V2 market edge is below
a configured materiality threshold. Context never changes P(cover/push/loss), never
boosts the edge used for wager sizing, and never displaces a material market-derived V2
edge. If context selects the opposite side of a near-neutral game, portfolio evaluation
uses the frozen model probabilities for that chosen side, preserving the cost of that
choice.

The primary robust utility for a scenario is:
    expected_household_prize_share
      * (1 - future_minimum_failure_risk)
      * current_week_entry_cvar_retention

The optimizer maximizes the worst such utility across field scenarios and probability
shrink states, then uses average robust utility, base expected prize share, lower
failure risk, stronger current-week capital retention, and lower deployment as
successive tie breakers.
"""
from __future__ import annotations

from typing import Dict, Mapping, Sequence

import numpy as np

from benchmark_strategies import Candidate, ranked_candidates
from monopoly_simulator import GameProbability, RegularSeasonRules
from monopoly_tournament_optimizer import (
    FieldScenario,
    FieldState,
    OptimizerConfig,
    _allocate_edge_weighted,
    _sample_household_current_week,
    build_joint_candidate,
    default_field_scenarios,
    evaluate_portfolio_across_scenarios,
    prepare_field_paths,
)


def shrink_probabilities(
    probs: Mapping[str, GameProbability], factor: float
) -> Dict[str, GameProbability]:
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


def _entry_cvar_ratio(values: np.ndarray, starting_balance: int, alpha: float = 0.10) -> float:
    if not 0.0 < alpha <= 0.5:
        raise ValueError("alpha must be in (0, 0.5]")
    arr = np.asarray(values, dtype=float)
    cutoff = float(np.quantile(arr, alpha))
    tail = arr[arr <= cutoff]
    cvar = float(tail.mean()) if tail.size else cutoff
    return max(0.0, min(1.0, cvar / float(starting_balance)))


def _current_week_downside(
    balances: Mapping[str, int],
    bets_by_entry,
    game_probabilities: Mapping[str, GameProbability],
    rules: RegularSeasonRules,
    cfg: OptimizerConfig,
    seed: int,
    alpha: float = 0.10,
) -> Dict[str, object]:
    endings = _sample_household_current_week(
        balances, bets_by_entry, game_probabilities, rules, cfg.simulations, seed
    )
    ratios = {
        entry: _entry_cvar_ratio(endings[entry], int(balances[entry]), alpha)
        for entry in endings
    }
    return {
        "alpha": float(alpha),
        "entry_cvar_retention": ratios,
        "minimum_entry_cvar_retention": min(ratios.values()),
    }


def _scenario_utility(row: Mapping[str, float], retention: float) -> float:
    return (
        float(row["expected_household_prize_share"])
        * (1.0 - float(row["future_minimum_failure_risk"]))
        * float(retention)
    )


def _contextual_ranked_candidates(
    game_probabilities: Mapping[str, GameProbability],
    contextual_preferences: Mapping[str, Mapping[str, object]],
    material_edge_threshold: float,
) -> list[Candidate]:
    """Preserve material V2 edges; use context only to order near-neutral games.

    Near-neutral candidates receive zero allocation edge so context can affect which
    mandatory/diversification positions are selected without manufacturing stake size.
    The true frozen probabilities for the context-selected side are still retained and
    used later by the portfolio simulator.
    """
    base = ranked_candidates(game_probabilities)
    material: list[Candidate] = []
    neutral: list[tuple[float, Candidate]] = []
    for c in base:
        if float(c.edge_per_dollar) >= float(material_edge_threshold):
            material.append(c)
            continue
        pref = contextual_preferences.get(c.game_id, {})
        side = str(pref.get("preferred_side", c.side))
        if side not in {"home", "away"}:
            raise ValueError(f"invalid contextual preferred_side for {c.game_id}: {side}")
        gp = game_probabilities[c.game_id]
        if side == "home":
            p_win, p_push, p_loss = gp.p_home_cover, gp.p_push, gp.p_home_loss
        else:
            p_win, p_push, p_loss = gp.p_home_loss, gp.p_push, gp.p_home_cover
        candidate = Candidate(c.game_id, side, 0.0, p_win, p_push, p_loss)
        score = float(pref.get("context_score", 0.0))
        neutral.append((score, candidate))
    material.sort(key=lambda c: (-c.edge_per_dollar, c.game_id))
    neutral.sort(key=lambda x: (-x[0], x[1].game_id))
    return material + [c for _, c in neutral]


def _build_joint_candidate_with_context(
    balances: Mapping[str, int],
    game_probabilities: Mapping[str, GameProbability],
    rules: RegularSeasonRules,
    c_fraction: float,
    a_fraction: float,
    c_games: int,
    a_games: int,
    overlap_mode: str,
    contextual_preferences: Mapping[str, Mapping[str, object]],
    material_edge_threshold: float,
):
    ranked = _contextual_ranked_candidates(
        game_probabilities, contextual_preferences, material_edge_threshold
    )
    if overlap_mode not in {"shared", "hybrid", "split"}:
        raise ValueError("overlap_mode must be shared, hybrid, or split")
    if overlap_mode == "shared":
        c_pool = ranked
        a_pool = ranked
    elif overlap_mode == "split":
        c_pool = ranked[0::2] + ranked[1::2]
        a_pool = ranked[1::2] + ranked[0::2]
    else:
        top = ranked[:1]
        rest = ranked[1:]
        c_pool = top + rest[0::2] + rest[1::2]
        a_pool = top + rest[1::2] + rest[0::2]
    return {
        "Catherine": _allocate_edge_weighted(
            int(balances["Catherine"]), c_pool, c_games, c_fraction, rules
        ),
        "Amanda": _allocate_edge_weighted(
            int(balances["Amanda"]), a_pool, a_games, a_fraction, rules
        ),
    }


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
    current_week_cvar_alpha: float = 0.10,
    contextual_preferences: Mapping[str, Mapping[str, object]] | None = None,
    material_edge_threshold: float = 0.01,
) -> Dict[str, object]:
    cfg = cfg or OptimizerConfig()
    scenarios = tuple(scenarios or default_field_scenarios())
    prepared = prepare_field_paths(field_state, scenarios, cfg)
    prob_sets = {float(f): shrink_probabilities(game_probabilities, float(f)) for f in edge_shrink_factors}
    contextual_preferences = contextual_preferences or {}

    best = None
    evaluated = 0
    for cf in fractions:
        for af in fractions:
            for cg in game_counts:
                for ag in game_counts:
                    for mode in overlap_modes:
                        if contextual_preferences:
                            bets = _build_joint_candidate_with_context(
                                balances, game_probabilities, rules, cf, af, cg, ag, mode,
                                contextual_preferences, material_edge_threshold,
                            )
                        else:
                            bets = build_joint_candidate(
                                balances, game_probabilities, rules, cf, af, cg, ag, mode
                            )
                        stress_metrics = {}
                        scenario_utilities = []
                        weighted_utilities = []
                        base_metrics = None
                        base_downside = None
                        for idx, factor in enumerate(edge_shrink_factors):
                            factor = float(factor)
                            downside = _current_week_downside(
                                balances, bets, prob_sets[factor], rules, cfg,
                                seed=cfg.seed + 5000 + idx * 100,
                                alpha=current_week_cvar_alpha,
                            )
                            retention = float(downside["minimum_entry_cvar_retention"])
                            m = evaluate_portfolio_across_scenarios(
                                balances, bets, prob_sets[factor], rules, field_state,
                                scenarios, cfg, prepared_field_paths=prepared,
                            )
                            if factor == 1.0:
                                base_metrics = m
                                base_downside = downside
                            weighted = m["weighted"]
                            weighted_utility = _scenario_utility(weighted, retention)
                            weighted_utilities.append(weighted_utility)
                            per_scenario = {
                                name: {
                                    **row,
                                    "current_week_entry_cvar_retention": retention,
                                    "robust_prize_utility": _scenario_utility(row, retention),
                                }
                                for name, row in m["by_scenario"].items()
                            }
                            scenario_utilities.extend(x["robust_prize_utility"] for x in per_scenario.values())
                            stress_metrics[f"edge_{factor:.2f}"] = {
                                "current_week_downside": downside,
                                "weighted": {**weighted, "current_week_entry_cvar_retention": retention, "robust_prize_utility": weighted_utility},
                                "by_scenario": per_scenario,
                            }

                        assert base_metrics is not None and base_downside is not None
                        evaluated += 1
                        robust_floor = min(scenario_utilities)
                        robust_average = sum(weighted_utilities) / len(weighted_utilities)
                        base_prize = base_metrics["weighted"]["expected_household_prize_share"]
                        base_failure = base_metrics["weighted"]["future_minimum_failure_risk"]
                        base_retention = float(base_downside["minimum_entry_cvar_retention"])
                        key = (
                            robust_floor,
                            robust_average,
                            base_prize,
                            -base_failure,
                            base_retention,
                            -base_metrics["household_outlay"],
                        )
                        if best is None or key > best["_key"]:
                            best = {
                                "_key": key,
                                "bets_by_entry": bets,
                                "parameters": {"c_fraction": cf, "a_fraction": af, "c_games": cg, "a_games": ag, "overlap_mode": mode},
                                "robust_floor_utility": robust_floor,
                                "robust_average_utility": robust_average,
                                "base_metrics": base_metrics,
                                "base_current_week_downside": base_downside,
                                "stress_metrics": stress_metrics,
                                "edge_shrink_factors": list(edge_shrink_factors),
                                "current_week_cvar_alpha": float(current_week_cvar_alpha),
                                "contextual_tiebreak_enabled": bool(contextual_preferences),
                                "material_edge_threshold": float(material_edge_threshold),
                            }
    assert best is not None
    best.pop("_key", None)
    best["evaluated_candidates"] = evaluated
    best["objective"] = (
        "maximize worst-case expected household prize share multiplied by probability "
        "of avoiding future-minimum failure and by minimum per-entry current-week "
        "10% CVaR capital retention across field scenarios and edge-shrink states; "
        "use context only to rank/select sub-threshold near-neutral games"
    )
    return best
