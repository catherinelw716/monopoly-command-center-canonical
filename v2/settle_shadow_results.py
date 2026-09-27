"""Append final results to the V2 shadow ledger without modifying predictions."""
from __future__ import annotations

import argparse
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

from shadow_ledger import append_events, iso_utc, parse_utc, read_events, validate_chain


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True, help="Settlement batch JSON")
    ap.add_argument("--ledger", default="v2/shadow/shadow_ledger.jsonl")
    args = ap.parse_args()

    payload = json.loads(Path(args.input).read_text(encoding="utf-8"))
    season = int(payload["season"])
    week = int(payload["week"])
    settled_at = str(payload.get("settled_at_utc") or iso_utc(datetime.now(timezone.utc)))
    parse_utc(settled_at)
    results = payload.get("results")
    if not isinstance(results, list) or not results:
        raise ValueError("results must be a non-empty list")

    existing = read_events(args.ledger)
    validate_chain(existing)
    known_games = {
        e["game"]["game_id"]
        for e in existing
        if e.get("event_type") == "prediction_capture" and int(e["season"]) == season and int(e["week"]) == week
    }
    already_settled = {
        e["game_id"]
        for e in existing
        if e.get("event_type") == "result_settlement" and int(e["season"]) == season and int(e["week"]) == week
    }

    events = []
    for r in results:
        game_id = str(r["game_id"])
        if game_id not in known_games:
            raise ValueError(f"Cannot settle game without a prospective prediction capture: {game_id}")
        if game_id in already_settled:
            raise ValueError(f"Game already settled in ledger: {game_id}")
        home_score = r.get("home_score")
        away_score = r.get("away_score")
        if "home_margin" in r:
            home_margin = float(r["home_margin"])
        elif home_score is not None and away_score is not None:
            home_margin = float(home_score) - float(away_score)
        else:
            raise ValueError(f"Need home_margin or both scores for {game_id}")

        events.append({
            "event_id": str(uuid.uuid4()),
            "event_type": "result_settlement",
            "captured_at_utc": settled_at,
            "season": season,
            "week": week,
            "game_id": game_id,
            "result": {
                "status": str(r.get("status", "FINAL")),
                "home_score": home_score,
                "away_score": away_score,
                "home_margin": home_margin,
            },
            "source": str(r.get("source", payload.get("source", "manual-final"))),
            "notes": str(r.get("notes", "")),
        })

    finalized = append_events(args.ledger, events)
    print(json.dumps({
        "status": "settled",
        "count": len(finalized),
        "tip_hash": finalized[-1]["row_hash"],
    }, indent=2))


if __name__ == "__main__":
    main()
