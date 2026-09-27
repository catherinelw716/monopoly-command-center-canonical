"""Execute V2-0009: field ensemble -> benchmarks -> joint optimizer -> robustness."""
from __future__ import annotations

import argparse
import json
from dataclasses import replace
from pathlib import Path

from benchmark_strategies import BenchmarkPortfolio
from monopoly_simulator import Bet, GameProbability, load_regular_rules
from monopoly_tournament_optimizer import (
    OptimizerConfig,
    default_field_scenarios,
    evaluate_benchmark_set,
    evaluate_portfolio_across_scenarios,
    load_field_state,
    optimize_joint_household,
    serialize_bets,
)
from shadow_model import ShadowModel

ROOT = Path(__file__).resolve().parents[1]


def load_week3_probabilities(proxy_path: Path, model_path: Path):
    proxy = json.loads(proxy_path.read_text(encoding="utf-8"))
    model = ShadowModel.load(model_path)
    probs = {}
    for g in proxy["games"]:
        pred = model.predict(g["market_home_spread"], g["sly_home_spread"])["hybrid"]
        probs[g["game_id"]] = GameProbability(
            g["game_id"], pred["p_home_cover"], pred["p_push"], pred["p_home_loss"]
        )
    return proxy, probs


def load_v1_portfolio(path: Path) -> BenchmarkPortfolio:
    d = json.loads(path.read_text(encoding="utf-8"))
    bets = {
        entry: tuple(Bet(x["game"], x["side"], int(x["amount"])) for x in rows)
        for entry, rows in d["portfolios"].items()
    }
    return BenchmarkPortfolio(
        "legacy_v1_week3_fixed",
        bets,
        {"household_policy": "legacy_v1_fixed_comparator"},
    )


def reweight_scenarios(weights):
    return tuple(
        replace(s, mixture_weight=float(weights[s.name]))
        for s in default_field_scenarios()
    )


def shrink_probs(probs, factor):
    out = {}
    for gid, gp in probs.items():
        nonpush = 1.0 - gp.p_push
        if nonpush <= 0:
            out[gid] = gp
            continue
        cond_home = gp.p_home_cover / nonpush
        cond_home = 0.5 + factor * (cond_home - 0.5)
        out[gid] = GameProbability(
            gid,
            nonpush * cond_home,
            gp.p_push,
            nonpush * (1 - cond_home),
        )
    return out


def compact_metrics(m):
    return {
        "expected_household_prize_share": m["weighted"]["expected_household_prize_share"],
        "p_any_cash": m["weighted"]["p_any_cash"],
        "p_top3": m["weighted"]["p_top3"],
        "p_first": m["weighted"]["p_first"],
        "p_both_cash": m["weighted"]["p_both_cash"],
        "future_minimum_failure_risk": m["weighted"]["future_minimum_failure_risk"],
        "household_outlay": m["household_outlay"],
        "overlap": m["overlap"],
        "by_scenario": m["by_scenario"],
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--simulations", type=int, default=1200)
    ap.add_argument("--output", default="v2/results/v2_0009_milestone_results.json")
    args = ap.parse_args()

    state = load_field_state(ROOT / "v2/season_2026/week_02_field_state.json")
    rules = load_regular_rules(ROOT / "v2/monopoly_contract.json")
    proxy, probs = load_week3_probabilities(
        ROOT / "v2/season_2026/week_03_optimizer_proxy.json",
        ROOT / "v2/model_artifacts/v2_global_hybrid_2016_2025.json",
    )
    v1 = load_v1_portfolio(ROOT / "v2/season_2026/week_03_v1_heuristic_portfolio.json")
    balances = {"Catherine": state.catherine_balance, "Amanda": state.amanda_balance}
    cfg = OptimizerConfig(simulations=args.simulations, seed=716)
    scenarios = default_field_scenarios()

    benchmarks = evaluate_benchmark_set(
        balances,
        probs,
        rules,
        state,
        scenarios=scenarios,
        cfg=cfg,
        extra_portfolios=(v1,),
    )
    optimizer = optimize_joint_household(
        balances,
        probs,
        rules,
        state,
        scenarios=scenarios,
        cfg=cfg,
    )
    opt_bets = optimizer["bets_by_entry"]

    stresses = []
    scenario_sets = {
        "equal": {"conservative": 1 / 3, "median": 1 / 3, "aggressive": 1 / 3},
        "conservative_heavy": {"conservative": 0.50, "median": 0.30, "aggressive": 0.20},
        "aggressive_heavy": {"conservative": 0.20, "median": 0.30, "aggressive": 0.50},
    }
    for label, weights in scenario_sets.items():
        mm = evaluate_portfolio_across_scenarios(
            balances,
            opt_bets,
            probs,
            rules,
            state,
            scenarios=reweight_scenarios(weights),
            cfg=cfg,
        )
        stresses.append({"stress": f"scenario_weights:{label}", **compact_metrics(mm)})
    for floor in (400, 2000, 5000):
        mm = evaluate_portfolio_across_scenarios(
            balances,
            opt_bets,
            probs,
            rules,
            state,
            scenarios=scenarios,
            cfg=cfg,
            lower_tail_floor=floor,
        )
        stresses.append({"stress": f"lower_tail_floor:{floor}", **compact_metrics(mm)})
    for shrink in (0.50, 0.75, 1.00):
        mm = evaluate_portfolio_across_scenarios(
            balances,
            opt_bets,
            shrink_probs(probs, shrink),
            rules,
            state,
            scenarios=scenarios,
            cfg=cfg,
        )
        stresses.append({"stress": f"probability_edge_multiplier:{shrink:.2f}", **compact_metrics(mm)})

    result = {
        "status": "V2-0009_MILESTONE_EXECUTION",
        "evidence_quality": "optimizer mechanics evaluation; Week-3 market input is explicitly proxy-only, not production/prospective evidence",
        "simulations_per_scenario": args.simulations,
        "field_scenarios": [s.__dict__ for s in scenarios],
        "week3_proxy_metadata": {k: v for k, v in proxy.items() if k != "games"},
        "benchmark_ranking": [
            {"strategy": r["strategy"], **compact_metrics(r)} for r in benchmarks
        ],
        "optimizer": {
            "evaluated_candidates": optimizer["evaluated_candidates"],
            "parameters": optimizer["parameters"],
            "bets_by_entry": serialize_bets(opt_bets),
            **compact_metrics(optimizer["metrics"]),
        },
        "robustness_red_team": stresses,
        "guardrails": [
            "Do not treat proxy execution results as a Week-3 wager recommendation.",
            "Do not promote V2 prediction layer from this optimizer run.",
            "Opponent individual balances/policies remain scenario-modeled, not reconstructed facts.",
            "Primary optimizer objective is expected household prize share; scenario/worst-case diagnostics remain visible."
        ],
    }
    out = ROOT / args.output
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
