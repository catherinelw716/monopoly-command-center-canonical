"""Run the uncertainty-aware V2-0009 optimizer on the current Week 3 Sunday market snapshot."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from monopoly_simulator import GameProbability, load_regular_rules
from monopoly_tournament_optimizer import load_field_state, serialize_bets
from monopoly_robust_optimizer import optimize_robust_household
from shadow_model import ShadowModel

ROOT = Path(__file__).resolve().parents[1]


def load_probs(snapshot_path: Path, model_path: Path):
    snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
    model = ShadowModel.load(model_path)
    probs = {}
    rows = []
    for g in snapshot["games"]:
        pred = model.predict(g["market_home_spread"], g["sly_home_spread"])["hybrid"]
        gp = GameProbability(g["game_id"], pred["p_home_cover"], pred["p_push"], pred["p_home_loss"])
        probs[g["game_id"]] = gp
        home_edge = gp.p_home_cover - gp.p_home_loss
        suggested_side = "home" if home_edge >= 0 else "away"
        rows.append({
            "game_id": g["game_id"],
            "sly_home_spread": g["sly_home_spread"],
            "market_home_spread": g["market_home_spread"],
            "home_line_advantage": g["sly_home_spread"] - g["market_home_spread"],
            "p_home_cover": gp.p_home_cover,
            "p_push": gp.p_push,
            "p_home_loss": gp.p_home_loss,
            "suggested_side": suggested_side,
            "edge_per_dollar": abs(home_edge),
            "market_note": g.get("market_note", ""),
        })
    rows.sort(key=lambda x: x["edge_per_dollar"], reverse=True)
    return snapshot, probs, rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--simulations", type=int, default=1200)
    ap.add_argument("--output", default="v2/results/week3_sunday_robust.json")
    args = ap.parse_args()

    state = load_field_state(ROOT / "v2/season_2026/week_02_field_state.json")
    rules = load_regular_rules(ROOT / "v2/monopoly_contract.json")
    snapshot, probs, ranking = load_probs(
        ROOT / "v2/season_2026/week_03_current_market_2026-09-27_1100ET.json",
        ROOT / "v2/model_artifacts/v2_global_hybrid_2016_2025.json",
    )
    balances = {"Catherine": state.catherine_balance, "Amanda": state.amanda_balance}
    from monopoly_tournament_optimizer import OptimizerConfig
    cfg = OptimizerConfig(simulations=args.simulations, seed=716)
    opt = optimize_robust_household(
        balances,
        probs,
        rules,
        state,
        cfg=cfg,
        fractions=(0.10, 0.20, 0.35, 0.50, 0.65, 0.80, 1.00),
        game_counts=(4, 5, 6),
    )
    base = opt["base_metrics"]
    result = {
        "status": "WEEK3_SUNDAY_ROBUST_RESEARCH",
        "snapshot_metadata": {k: v for k, v in snapshot.items() if k != "games"},
        "probability_ranking": ranking,
        "optimizer": {
            "objective": opt["objective"],
            "evaluated_candidates": opt["evaluated_candidates"],
            "parameters": opt["parameters"],
            "bets_by_entry": serialize_bets(opt["bets_by_entry"]),
            "robust_floor_utility": opt["robust_floor_utility"],
            "robust_average_utility": opt["robust_average_utility"],
            "base_expected_household_prize_share": base["weighted"]["expected_household_prize_share"],
            "base_p_any_cash": base["weighted"]["p_any_cash"],
            "base_p_top3": base["weighted"]["p_top3"],
            "base_p_first": base["weighted"]["p_first"],
            "base_future_minimum_failure_risk": base["weighted"]["future_minimum_failure_risk"],
            "household_outlay": base["household_outlay"],
            "overlap": base["overlap"],
            "stress_metrics": opt["stress_metrics"],
        },
        "guardrails": [
            "Prediction layer uses frozen market-anchored hybrid model only; standings do not alter cover probabilities.",
            "Current-market snapshot is Sunday research evidence, not a reconstructed Friday freeze.",
            "Robust optimizer has no arbitrary bankroll-percentage cap; deployment remains an output.",
            "External sources/injury news are red-team context and are not hard-coded into V2 probabilities."
        ],
    }
    out = ROOT / args.output
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
