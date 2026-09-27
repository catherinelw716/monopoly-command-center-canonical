"""Score settled V2 shadow predictions without altering the ledger."""
from __future__ import annotations

import argparse
import json
import math
from collections import defaultdict
from statistics import mean

from shadow_ledger import read_events, validate_chain


def outcome_class(home_margin: float, home_spread: float) -> int:
    ats = float(home_margin) + float(home_spread)
    if math.isclose(ats, 0.0, abs_tol=1e-9):
        return 1
    return 2 if ats > 0 else 0


def brier3(p: list[float], cls: int) -> float:
    y = [0.0, 0.0, 0.0]
    y[cls] = 1.0
    return sum((p[i] - y[i]) ** 2 for i in range(3))


def logloss3(p: list[float], cls: int) -> float:
    return -math.log(max(float(p[cls]), 1e-12))


def pvec(d: dict) -> list[float]:
    return [float(d["p_home_loss"]), float(d["p_push"]), float(d["p_home_cover"])]


def summarize(rows: list[dict]) -> dict:
    if not rows:
        return {"n": 0}
    normal_brier = [r["normal_brier"] for r in rows]
    hybrid_brier = [r["hybrid_brier"] for r in rows]
    normal_logloss = [r["normal_logloss"] for r in rows]
    hybrid_logloss = [r["hybrid_logloss"] for r in rows]
    integer = [r for r in rows if r["integer_sly_line"]]
    key3 = [r for r in rows if math.isclose(abs(r["sly_home_spread"]), 3.0, abs_tol=1e-9)]
    key7 = [r for r in rows if math.isclose(abs(r["sly_home_spread"]), 7.0, abs_tol=1e-9)]

    def push_diag(x: list[dict]) -> dict:
        if not x:
            return {"n": 0}
        return {
            "n": len(x),
            "predicted_push": mean(r["hybrid_p_push"] for r in x),
            "observed_push": mean(1.0 if r["actual_class"] == "push" else 0.0 for r in x),
        }

    return {
        "n": len(rows),
        "normal_brier3": mean(normal_brier),
        "hybrid_brier3": mean(hybrid_brier),
        "normal_minus_hybrid_brier3": mean(n - h for n, h in zip(normal_brier, hybrid_brier)),
        "normal_logloss3": mean(normal_logloss),
        "hybrid_logloss3": mean(hybrid_logloss),
        "normal_minus_hybrid_logloss3": mean(n - h for n, h in zip(normal_logloss, hybrid_logloss)),
        "integer_push_calibration": push_diag(integer),
        "exact_3_push_calibration": push_diag(key3),
        "exact_7_push_calibration": push_diag(key7),
        "mean_abs_sly_market_delta": mean(abs(r["home_line_advantage"]) for r in rows),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ledger", default="v2/shadow/shadow_ledger.jsonl")
    args = ap.parse_args()

    events = read_events(args.ledger)
    integrity = validate_chain(events)
    superseded = {e["supersedes_event_id"] for e in events if e.get("event_type") == "correction"}
    settlements = {
        e["game_id"]: e
        for e in events
        if e.get("event_type") == "result_settlement"
    }

    scored: list[dict] = []
    for e in events:
        if e.get("event_type") != "prediction_capture" or e["event_id"] in superseded:
            continue
        game_id = e["game"]["game_id"]
        settle = settlements.get(game_id)
        if not settle:
            continue
        home_margin = float(settle["result"]["home_margin"])
        sly = float(e["lines"]["sly_home_spread"])
        cls = outcome_class(home_margin, sly)
        pn = pvec(e["v2"]["normal"])
        ph = pvec(e["v2"]["hybrid"])
        scored.append({
            "season": int(e["season"]),
            "week": int(e["week"]),
            "game_id": game_id,
            "snapshot_type": e["snapshot_type"],
            "sly_home_spread": sly,
            "market_home_spread": float(e["lines"]["market_home_spread"]),
            "home_line_advantage": float(e["lines"]["home_line_advantage"]),
            "integer_sly_line": bool(e["v2"]["integer_sly_line"]),
            "actual_class": ["loss", "push", "cover"][cls],
            "hybrid_p_push": float(e["v2"]["hybrid"]["p_push"]),
            "normal_brier": brier3(pn, cls),
            "hybrid_brier": brier3(ph, cls),
            "normal_logloss": logloss3(pn, cls),
            "hybrid_logloss": logloss3(ph, cls),
        })

    by_snapshot: dict[str, list[dict]] = defaultdict(list)
    for r in scored:
        by_snapshot[r["snapshot_type"]].append(r)

    # Friday-to-prekick movement for games with both snapshots.
    pairs: dict[str, dict[str, dict]] = defaultdict(dict)
    for e in events:
        if e.get("event_type") == "prediction_capture" and e["event_id"] not in superseded:
            pairs[e["game"]["game_id"]][e["snapshot_type"]] = e
    movements = []
    for game_id, p in pairs.items():
        if "FRIDAY_FREEZE" in p and "PRE_KICK_FINAL" in p:
            f = p["FRIDAY_FREEZE"]
            k = p["PRE_KICK_FINAL"]
            movements.append({
                "game_id": game_id,
                "friday_market_home_spread": float(f["lines"]["market_home_spread"]),
                "prekick_market_home_spread": float(k["lines"]["market_home_spread"]),
                "market_move_home": float(k["lines"]["market_home_spread"] - f["lines"]["market_home_spread"]),
                "sly_home_spread": float(f["lines"]["sly_home_spread"]),
            })

    report = {
        "integrity": integrity,
        "settled_games": len(settlements),
        "scored_prediction_events": len(scored),
        "promotion_guardrail": {
            "min_settled_snapshots": 100,
            "min_distinct_weeks": 6,
            "distinct_scored_weeks": len({(r["season"], r["week"]) for r in scored}),
        },
        "by_snapshot": {k: summarize(v) for k, v in sorted(by_snapshot.items())},
        "friday_to_prekick_market_movement": {
            "n_games": len(movements),
            "mean_abs_move": mean(abs(x["market_move_home"]) for x in movements) if movements else None,
        },
    }
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
