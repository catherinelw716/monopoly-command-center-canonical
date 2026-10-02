"""Week 4 Friday Catherine/Amanda optimizer.

Uses the frozen Week 4 probability layer and Step-7 red-team controls. It does not
change NFL probabilities. Friday output is provisional: source-sensitive edges are
stress-tested to zero and source-disputed games are not promoted into sizing edges.
"""
from __future__ import annotations

import json
from pathlib import Path

from benchmark_strategies import portfolio_overlap
from monopoly_simulator import GameProbability, load_regular_rules
from monopoly_tournament_optimizer import (
    OptimizerConfig,
    default_field_scenarios,
    evaluate_benchmark_set,
    evaluate_portfolio_across_scenarios,
    load_field_state,
    serialize_bets,
)
from monopoly_robust_optimizer import _current_week_downside, optimize_robust_household

ROOT = Path(__file__).resolve().parents[1]
MODEL = ROOT / "v2/results/week_04_friday_model_layer.json"
SLY = ROOT / "v2/season_2026/week_04_sly_freeze.json"
FIELD = ROOT / "v2/season_2026/week_03_field_state.json"
RULES = ROOT / "v2/monopoly_contract.json"
OUT = ROOT / "v2/results/week_04_friday_optimizer.json"

CONTEXTUAL_PREFERENCES = {
    "ATL @ NO": {"preferred_side": "home", "context_score": 0.30},
    "JAX @ CIN": {"preferred_side": "home", "context_score": 0.29},
    "KC @ LV": {"preferred_side": "home", "context_score": 0.28},
    "ARI @ NYG": {"preferred_side": "home", "context_score": 0.18},
    "LAR @ PHI": {"preferred_side": "home", "context_score": 0.12},
    "TEN @ BAL": {"preferred_side": "home", "context_score": 0.08},
    "DET @ CAR": {"preferred_side": "home", "context_score": 0.04},
    "NYJ @ CHI": {"preferred_side": "home", "context_score": 0.03},
    "GB @ TB": {"preferred_side": "away", "context_score": 0.02},
    "MIA @ MIN": {"preferred_side": "home", "context_score": 0.01},
    "IND @ WAS": {"preferred_side": "away", "context_score": -0.50},
    "DEN @ SF": {"preferred_side": "away", "context_score": -0.60},
    "NE @ BUF": {"preferred_side": "away", "context_score": -0.70},
    "DAL @ HOU": {"preferred_side": "home", "context_score": 1.00},
    "LAC @ SEA": {"preferred_side": "home", "context_score": 1.00},
}


def side_to_home_probs(row: dict, source: str) -> GameProbability:
    gid = row["game_id"]
    home = gid.split(" @ ")[1]
    r = row[source]
    if r["side"] == home:
        ph, pl = float(r["p_cover"]), float(r["p_loss"])
    else:
        ph, pl = float(r["p_loss"]), float(r["p_cover"])
    pp = float(r["p_push"])
    # Checked-in model rows are rounded to six decimals, so normalize the tiny
    # serialization drift before sending them into the strict simulator contract.
    total = ph + pp + pl
    return GameProbability(gid, ph / total, pp / total, pl / total)


def neutralize(gp: GameProbability) -> GameProbability:
    nonpush = 1.0 - gp.p_push
    return GameProbability(gp.game_id, nonpush / 2.0, gp.p_push, nonpush / 2.0)


def load_probability_states():
    d = json.loads(MODEL.read_text(encoding="utf-8"))
    vi, action, base, zero = {}, {}, {}, {}
    for row in d["games"]:
        gid = row["game_id"]
        vi_gp = side_to_home_probs(row, "vi")
        action_gp = side_to_home_probs(row, "action")
        vi[gid] = vi_gp
        action[gid] = action_gp
        if row["state"] == "SOURCE_SENSITIVE_SAME_DIRECTION":
            base[gid] = action_gp
        else:
            base[gid] = neutralize(vi_gp)
        zero[gid] = neutralize(base[gid])
    return base, zero, vi, action


def label_bets(serialized: dict) -> dict:
    sly = json.loads(SLY.read_text(encoding="utf-8"))
    rows = {g["game"]: g for g in sly["games"]}
    out = {}
    for entry, bets in serialized.items():
        labeled = []
        for b in bets:
            g = rows[b["game_id"]]
            team = g["home"] if b["side"] == "home" else g["away"]
            hs = float(g["sly_home_spread"])
            spread = hs if b["side"] == "home" else -hs
            sign = "+" if spread > 0 else ""
            labeled.append({**b, "label": f"{team} {sign}{spread:g}"})
        out[entry] = labeled
    return out


def compact_metrics(m: dict) -> dict:
    w = m["weighted"]
    return {
        "expected_household_prize_share": w["expected_household_prize_share"],
        "p_any_cash": w["p_any_cash"],
        "p_top3": w["p_top3"],
        "p_first": w["p_first"],
        "p_both_cash": w["p_both_cash"],
        "future_minimum_failure_risk": w["future_minimum_failure_risk"],
        "household_outlay": m["household_outlay"],
        "outlay_by_entry": m["outlay_by_entry"],
        "overlap": m["overlap"],
    }


def main() -> None:
    base, zero, vi, action = load_probability_states()
    state = load_field_state(FIELD)
    rules = load_regular_rules(RULES)
    balances = {"Catherine": state.catherine_balance, "Amanda": state.amanda_balance}
    scenarios = default_field_scenarios()
    cfg = OptimizerConfig(simulations=600, seed=716)

    best = optimize_robust_household(
        balances,
        base,
        rules,
        state,
        scenarios=scenarios,
        cfg=cfg,
        fractions=(0.05, 0.08, 0.10, 0.12, 0.15),
        game_counts=(4, 5),
        overlap_modes=("shared", "hybrid", "split"),
        edge_shrink_factors=(1.00, 0.75, 0.50, 0.25, 0.00),
        current_week_cvar_alpha=0.10,
        contextual_preferences=CONTEXTUAL_PREFERENCES,
        material_edge_threshold=0.01,
    )
    serialized = serialize_bets(best["bets_by_entry"])

    states = {
        "base_action_edge": base,
        "zero_edge": zero,
        "vegasinsider_full": vi,
        "action_full": action,
    }
    stress = {}
    for i, (name, probs) in enumerate(states.items()):
        m = evaluate_portfolio_across_scenarios(
            balances, best["bets_by_entry"], probs, rules, state, scenarios, cfg
        )
        downside = _current_week_downside(
            balances,
            best["bets_by_entry"],
            probs,
            rules,
            cfg,
            seed=cfg.seed + 9100 + i * 100,
            alpha=0.10,
        )
        stress[name] = {**compact_metrics(m), "current_week_cvar": downside}

    benchmarks_raw = evaluate_benchmark_set(
        balances,
        base,
        rules,
        state,
        scenarios=scenarios,
        cfg=OptimizerConfig(simulations=600, seed=716),
    )
    benchmarks = [{"strategy": r["strategy"], **compact_metrics(r)} for r in benchmarks_raw]

    result = {
        "season": 2026,
        "week": 4,
        "snapshot_type": "FRIDAY_PROVISIONAL_HOUSEHOLD_OPTIMIZER",
        "status": "STEP_8_COMPLETE_PROVISIONAL_NOT_SUBMISSION",
        "balances": balances,
        "field_state_source": "v2/season_2026/week_03_field_state.json",
        "probability_policy": {
            "frozen_model": "V2-0006C-global-hybrid-r1",
            "sizing_edges": ["HOU -3", "SEA -7"],
            "source_sensitive_zero_edge_stress": True,
            "source_disputed_games_neutralized_for_friday_candidate_generation": [
                "NE @ BUF", "DEN @ SF", "IND @ WAS"
            ],
            "source_disputed_full_states_still_evaluated": [
                "vegasinsider_full", "action_full"
            ],
            "market_equal_fillers": "minimum-wager only unless Sunday creates a validated edge",
        },
        "optimizer_grid": {
            "simulations": cfg.simulations,
            "fractions": [0.05, 0.08, 0.10, 0.12, 0.15],
            "game_counts": [4, 5],
            "overlap_modes": ["shared", "hybrid", "split"],
            "edge_shrink_factors": [1.0, 0.75, 0.5, 0.25, 0.0],
        },
        "provisional_best": {
            "parameters": best["parameters"],
            "bets_by_entry": label_bets(serialized),
            "robust_floor_utility": best["robust_floor_utility"],
            "robust_average_utility": best["robust_average_utility"],
            "base_metrics": compact_metrics(best["base_metrics"]),
            "base_current_week_downside": best["base_current_week_downside"],
            "evaluated_candidates": best["evaluated_candidates"],
            "overlap": portfolio_overlap(best["bets_by_entry"]),
        },
        "explicit_selected_portfolio_stress": stress,
        "benchmark_comparison": benchmarks,
        "guardrails": [
            "This is a Friday provisional optimizer output, not a submission recommendation.",
            "No stake escalation is permitted from Week 3's 11-3 model result.",
            "HOU and SEA incremental edge must survive the zero-edge stress comparison before meaningful concentration is justified.",
            "Source-disputed games are not promoted to Friday sizing edges; Sunday may change this after a fresh market snapshot.",
            "All no-edge filler positions are contest-compliance/diversification positions, not validated ATS edges.",
            "Step 9 reconciliation remains mandatory before any portfolio can be treated as submission-ready.",
        ],
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
