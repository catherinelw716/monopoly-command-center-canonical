"""Stability/red-team harness for the Week 3 Sunday V2 contextual optimizer.

Purpose: distinguish stable recommendations from fragile last-slot artifacts without
changing the frozen NFL probability layer. The harness varies simulation seed and
perturbs only contextual tiebreak scores for sub-threshold games.
"""
from __future__ import annotations

import json
from collections import Counter, defaultdict
from copy import deepcopy
from pathlib import Path

import numpy as np

from monopoly_simulator import load_regular_rules
from monopoly_tournament_optimizer import OptimizerConfig, load_field_state, serialize_bets
from monopoly_robust_optimizer import optimize_robust_household
from run_week3_sunday_robust import load_probs

ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT = ROOT / "v2/season_2026/week_03_current_market_2026-09-27_1120ET.json"
MODEL = ROOT / "v2/model_artifacts/v2_global_hybrid_2016_2025.json"
STATE = ROOT / "v2/season_2026/week_02_field_state.json"
RULES = ROOT / "v2/monopoly_contract.json"
CONTEXT = ROOT / "v2/season_2026/week_03_context_tiebreak.json"
OUTPUT = ROOT / "v2/results/week3_sunday_stability_redteam.json"

SEEDS = (716, 1716, 2716, 3716, 4716)
PERTURBATIONS = (-0.15, 0.0, 0.15)
MATERIAL_EDGE_THRESHOLD = 0.01


def perturb_context(base: dict, delta: float, run_index: int) -> dict:
    """Deterministically nudge contextual scores while preserving side labels.

    The +/-0.15 perturbation is intentionally small relative to the 0-3 ordinal
    context scale. Direction alternates by game so this tests ordering fragility
    rather than uniformly boosting or suppressing all context.
    """
    out = deepcopy(base)
    rows = sorted(out["games"], key=lambda x: x["game_id"])
    for i, row in enumerate(rows):
        sign = 1 if ((i + run_index) % 2 == 0) else -1
        row["context_score"] = float(row.get("context_score", 0.0)) + sign * delta
    out["games"] = rows
    out["perturbation"] = delta
    return out


def context_map(doc: dict) -> dict:
    return {
        row["game_id"]: {
            "side": row["preferred_side"],
            "score": float(row.get("context_score", 0.0)),
            "weather_flag": row.get("weather_flag", "unknown"),
        }
        for row in doc["games"]
    }


def main() -> None:
    state = load_field_state(STATE)
    rules = load_regular_rules(RULES)
    _, probs, ranking = load_probs(SNAPSHOT, MODEL)
    base_context = json.loads(CONTEXT.read_text(encoding="utf-8"))
    balances = {"Catherine": state.catherine_balance, "Amanda": state.amanda_balance}

    material = {
        row["game_id"]: row
        for row in ranking
        if float(row["edge_per_dollar"]) >= MATERIAL_EDGE_THRESHOLD
    }

    runs = []
    selection_counts = Counter()
    side_counts = Counter()
    amount_values = defaultdict(list)
    parameter_counts = Counter()
    metric_values = defaultdict(list)

    run_index = 0
    for seed in SEEDS:
        for delta in PERTURBATIONS:
            perturbed = perturb_context(base_context, delta, run_index)
            cmap = context_map(perturbed)
            cfg = OptimizerConfig(simulations=300, seed=seed)
            opt = optimize_robust_household(
                balances,
                probs,
                rules,
                state,
                cfg=cfg,
                fractions=(0.10, 0.20, 0.35, 0.50),
                game_counts=(4, 5, 6),
                current_week_cvar_alpha=0.10,
                context_preferences=cmap,
                contextual_edge_threshold=MATERIAL_EDGE_THRESHOLD,
            )
            bets = serialize_bets(opt["bets_by_entry"])
            base = opt["base_metrics"]
            params = opt["parameters"]
            parameter_counts[(params["c_fraction"], params["a_fraction"], params["c_games"], params["a_games"], params["overlap_mode"])] += 1

            for entry, rows in bets.items():
                for row in rows:
                    key = (entry, row["game_id"])
                    selection_counts[key] += 1
                    side_counts[(entry, row["game_id"], row["side"])] += 1
                    amount_values[key].append(int(row["amount"]))

            metric_values["household_outlay"].append(base["household_outlay"])
            metric_values["expected_household_prize_share"].append(base["weighted"]["expected_household_prize_share"])
            metric_values["p_any_cash"].append(base["weighted"]["p_any_cash"])
            metric_values["future_minimum_failure_risk"].append(base["weighted"]["future_minimum_failure_risk"])
            metric_values["robust_floor_utility"].append(opt["robust_floor_utility"])

            runs.append({
                "seed": seed,
                "context_perturbation": delta,
                "parameters": params,
                "bets_by_entry": bets,
                "household_outlay": base["household_outlay"],
                "expected_household_prize_share": base["weighted"]["expected_household_prize_share"],
                "p_any_cash": base["weighted"]["p_any_cash"],
                "future_minimum_failure_risk": base["weighted"]["future_minimum_failure_risk"],
                "robust_floor_utility": opt["robust_floor_utility"],
            })
            run_index += 1

    n = len(runs)
    stability = []
    for entry in ("Catherine", "Amanda"):
        game_ids = sorted({gid for e, gid in selection_counts if e == entry})
        for gid in game_ids:
            vals = amount_values[(entry, gid)]
            side_rows = [(k[2], v) for k, v in side_counts.items() if k[0] == entry and k[1] == gid]
            dominant_side = max(side_rows, key=lambda x: x[1])[0]
            stability.append({
                "entry": entry,
                "game_id": gid,
                "dominant_side": dominant_side,
                "selection_rate": selection_counts[(entry, gid)] / n,
                "median_amount_when_selected": float(np.median(vals)),
                "min_amount_when_selected": int(min(vals)),
                "max_amount_when_selected": int(max(vals)),
                "material_market_edge": gid in material,
            })
    stability.sort(key=lambda x: (x["entry"], -x["selection_rate"], -x["median_amount_when_selected"], x["game_id"]))

    def summarize(values):
        a = np.asarray(values, dtype=float)
        return {
            "mean": float(a.mean()),
            "p10": float(np.quantile(a, 0.10)),
            "p50": float(np.quantile(a, 0.50)),
            "p90": float(np.quantile(a, 0.90)),
            "min": float(a.min()),
            "max": float(a.max()),
        }

    result = {
        "status": "WEEK3_SUNDAY_STABILITY_REDTEAM",
        "runs": n,
        "seeds": list(SEEDS),
        "context_perturbations": list(PERTURBATIONS),
        "material_edge_threshold": MATERIAL_EDGE_THRESHOLD,
        "material_market_edges": list(material.values()),
        "parameter_frequency": [
            {
                "c_fraction": k[0], "a_fraction": k[1], "c_games": k[2], "a_games": k[3],
                "overlap_mode": k[4], "count": v, "rate": v / n,
            }
            for k, v in parameter_counts.most_common()
        ],
        "selection_stability": stability,
        "metric_stability": {k: summarize(v) for k, v in metric_values.items()},
        "runs_detail": runs,
        "guardrails": [
            "Frozen NFL probabilities are unchanged across all runs.",
            "Context perturbation applies only to sub-1% edge tiebreak ordering.",
            "Context never creates allocation edge and never displaces material market edges.",
            "This harness tests recommendation stability, not predictive calibration."
        ],
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
