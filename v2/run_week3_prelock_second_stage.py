"""Refreshed Week 3 second-stage sizing optimizer for the 12:01 ET pre-lock market.

Uses common random numbers and the refreshed price-edge set. Candidate game identity is
held fixed within each entry structure while game count and deployment vary. Incremental
stake is allocated only across material price-edge games, proportional to frozen V2 edge.
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
SNAPSHOT = ROOT / "v2/season_2026/week_03_current_market_2026-09-27_1201ET.json"
MODEL = ROOT / "v2/model_artifacts/v2_global_hybrid_2016_2025.json"
STATE = ROOT / "v2/season_2026/week_02_field_state.json"
RULES = ROOT / "v2/monopoly_contract.json"
OUTPUT = ROOT / "v2/results/week3_prelock_second_stage.json"

# Candidate order starts with refreshed material price edges, then contextual support.
# Material sides are determined by Sly-vs-live price value, not by stale pre-refresh context.
CANDIDATES = {
    "Catherine": (
        ("MIN @ TB", "away", "MIN -1.5", True),
        ("CAR @ CLE", "home", "CLE +2.5", True),
        ("LAC @ BUF", "home", "BUF -7", True),
        ("KC @ MIA", "away", "KC -10.5", False),
        ("LAR @ DEN", "home", "DEN +2.5", False),
        ("CIN @ PIT", "home", "PIT +3.5", False),
    ),
    "Amanda": (
        ("MIN @ TB", "away", "MIN -1.5", True),
        ("SEA @ WAS", "home", "WAS +7.5", True),
        ("NE @ JAX", "away", "NE +3", True),
        ("ARI @ SF", "away", "ARI +8.5", False),
        ("BAL @ DAL", "home", "DAL +3.5", False),
        ("HOU @ IND", "home", "IND +1.5", False),
    ),
}

DEPLOYMENT_FRACTIONS = (0.08, 0.10, 0.12, 0.15, 0.18, 0.20, 0.25, 0.30)
GAME_COUNTS = (4, 5, 6)
EDGE_SHRINK_FACTORS = (1.00, 0.75, 0.50, 0.25)


def _edge_for_candidate(gid: str, side: str, probs) -> float:
    gp = probs[gid]
    home_edge = gp.p_home_cover - gp.p_home_loss
    return max(0.0, home_edge if side == "home" else -home_edge)


def build_portfolio(
    balances: Mapping[str, int], rules, probs,
    c_fraction: float, a_fraction: float, c_games: int, a_games: int,
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
        amounts = np.full(n_games, rules.minimum_wager, dtype=int)
        remainder = target - minimum_total

        material_idx = [i for i, (_, _, _, material) in enumerate(selected) if material]
        edges = np.array([_edge_for_candidate(selected[i][0], selected[i][1], probs) for i in material_idx], dtype=float)
        if remainder > 0 and material_idx:
            weights = np.ones(len(material_idx))/len(material_idx) if edges.sum() <= 1e-12 else edges/edges.sum()
            units = remainder // rules.wager_increment
            raw = weights * units
            extra = np.floor(raw).astype(int)
            left = int(units - extra.sum())
            if left > 0:
                order = np.argsort(-(raw-extra))
                extra[order[:left]] += 1
            for j, idx in enumerate(material_idx):
                amounts[idx] += int(extra[j] * rules.wager_increment)

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

    cfg = OptimizerConfig(simulations=5000, seed=716)
    prepared = prepare_field_paths(state, scenarios, cfg)
    prob_sets = {f: shrink_probabilities(probs, f) for f in EDGE_SHRINK_FACTORS}

    rows = []
    for cg in GAME_COUNTS:
        for ag in GAME_COUNTS:
            for cf in DEPLOYMENT_FRACTIONS:
                for af in DEPLOYMENT_FRACTIONS:
                    bets = build_portfolio(balances, rules, probs, cf, af, cg, ag)
                    stress=[]; weighted_utils=[]; base_metrics=None; base_downside=None
                    for idx, factor in enumerate(EDGE_SHRINK_FACTORS):
                        pset = prob_sets[factor]
                        downside = _current_week_downside(
                            balances, bets, pset, rules, cfg,
                            seed=cfg.seed + 5000 + idx*100, alpha=0.10,
                        )
                        retention = float(downside["minimum_entry_cvar_retention"])
                        metrics = evaluate_portfolio_across_scenarios(
                            balances, bets, pset, rules, state, scenarios, cfg,
                            prepared_field_paths=prepared,
                        )
                        weighted_utils.append(_scenario_utility(metrics["weighted"], retention))
                        if factor == 1.0:
                            base_metrics=metrics; base_downside=downside
                        for scenario_name,m in metrics["by_scenario"].items():
                            stress.append({"edge_shrink_factor":factor,"field_scenario":scenario_name,
                                "utility":_scenario_utility(m,retention)})
                    w=base_metrics["weighted"]
                    rows.append({
                        "c_games":cg,"a_games":ag,"c_fraction":cf,"a_fraction":af,
                        "bets_by_entry":serialize_bets(bets),
                        "outlay_by_entry":base_metrics["outlay_by_entry"],
                        "household_outlay":base_metrics["household_outlay"],
                        "robust_floor_utility":min(x["utility"] for x in stress),
                        "robust_average_utility":float(np.mean(weighted_utils)),
                        "base_expected_household_prize_share":w["expected_household_prize_share"],
                        "base_p_any_cash":w["p_any_cash"],
                        "base_p_top3":w["p_top3"],
                        "base_p_first":w["p_first"],
                        "base_future_minimum_failure_risk":w["future_minimum_failure_risk"],
                        "base_current_week_downside":base_downside,
                    })

    def key(r):
        return (r["robust_floor_utility"],r["robust_average_utility"],r["base_expected_household_prize_share"],-r["base_future_minimum_failure_risk"],-r["household_outlay"])
    rows.sort(key=key,reverse=True)
    by_pair=[]
    for cg in GAME_COUNTS:
        for ag in GAME_COUNTS:
            subset=[r for r in rows if r["c_games"]==cg and r["a_games"]==ag]
            by_pair.append(max(subset,key=key))
    by_pair.sort(key=key,reverse=True)

    result={
        "status":"WEEK3_PRELOCK_SECOND_STAGE_CRN",
        "snapshot":"week_03_current_market_2026-09-27_1201ET.json",
        "simulations":cfg.simulations,"seed":cfg.seed,
        "deployment_grid":list(DEPLOYMENT_FRACTIONS),"game_counts_tested":list(GAME_COUNTS),
        "edge_shrink_factors":list(EDGE_SHRINK_FACTORS),
        "best_overall":rows[0],"best_by_game_count_pair":by_pair,"top20":rows[:20],
        "probability_ranking":ranking,
        "guardrails":[
            "Frozen NFL probabilities unchanged except refreshed market input.",
            "Common random numbers used across candidate allocations.",
            "Incremental stake allocated only across refreshed material price-edge games, proportional to frozen V2 edge.",
            "Contextual/supporting positions remain at $100 minimum.",
            "Game count and deployment are outputs, not fixed assumptions."
        ]}
    OUTPUT.parent.mkdir(parents=True,exist_ok=True)
    OUTPUT.write_text(json.dumps(result,indent=2,sort_keys=True),encoding="utf-8")
    print(json.dumps({"best_overall":rows[0],"best_by_game_count_pair":by_pair},indent=2,sort_keys=True))

if __name__ == "__main__":
    main()
