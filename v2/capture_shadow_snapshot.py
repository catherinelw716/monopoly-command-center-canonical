"""Capture one immutable V2 prospective snapshot batch.

Input JSON example:
{
  "season": 2026,
  "week": 4,
  "snapshot_type": "FRIDAY_FREEZE",
  "captured_at_utc": "2026-10-02T14:00:00Z",
  "market_source": "manual-consensus",
  "market_observed_at_utc": "2026-10-02T13:58:00Z",
  "games": [
    {
      "game_id": "2026_04_AWAY_HOME",
      "away_team": "AWAY",
      "home_team": "HOME",
      "kickoff_utc": "2026-10-04T17:00:00Z",
      "sly_home_spread": -3.5,
      "market_home_spread": -3.0,
      "v1": {},
      "external": {},
      "notes": ""
    }
  ]
}
"""
from __future__ import annotations

import argparse
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from shadow_ledger import append_events, iso_utc, parse_utc
from shadow_model import ShadowModel

DEFAULT_LEDGER = "v2/shadow/shadow_ledger.jsonl"
DEFAULT_MODEL = "v2/model_artifacts/v2_global_hybrid_2016_2025.json"


def now_utc() -> str:
    return iso_utc(datetime.now(timezone.utc))


def _required(d: dict[str, Any], key: str) -> Any:
    if key not in d:
        raise ValueError(f"Missing required field: {key}")
    return d[key]


def build_events(payload: dict[str, Any], model: ShadowModel) -> list[dict[str, Any]]:
    season = int(_required(payload, "season"))
    week = int(_required(payload, "week"))
    snapshot_type = str(_required(payload, "snapshot_type"))
    if snapshot_type not in {"FRIDAY_FREEZE", "PRE_KICK_FINAL"}:
        raise ValueError("snapshot_type must be FRIDAY_FREEZE or PRE_KICK_FINAL")

    captured_at = str(payload.get("captured_at_utc") or now_utc())
    # Parse once so malformed/non-UTC-aware timestamps fail before any write.
    parse_utc(captured_at)
    default_market_source = str(payload.get("market_source", "unspecified"))
    default_observed = payload.get("market_observed_at_utc")
    games = payload.get("games")
    if not isinstance(games, list) or not games:
        raise ValueError("games must be a non-empty list")

    batch_id = str(uuid.uuid4())
    events: list[dict[str, Any]] = []
    for g in games:
        game_id = str(_required(g, "game_id"))
        away = str(_required(g, "away_team"))
        home = str(_required(g, "home_team"))
        kickoff = str(_required(g, "kickoff_utc"))
        sly = float(_required(g, "sly_home_spread"))
        market = float(_required(g, "market_home_spread"))
        observed = str(g.get("market_observed_at_utc") or default_observed or captured_at)
        market_source = str(g.get("market_source") or default_market_source)
        parse_utc(kickoff)
        parse_utc(observed)

        pred = model.predict(market_home_spread=market, sly_home_spread=sly)
        events.append({
            "event_id": str(uuid.uuid4()),
            "event_type": "prediction_capture",
            "batch_id": batch_id,
            "captured_at_utc": captured_at,
            "season": season,
            "week": week,
            "snapshot_type": snapshot_type,
            "game": {
                "game_id": game_id,
                "away_team": away,
                "home_team": home,
                "kickoff_utc": kickoff,
            },
            "lines": {
                "sly_home_spread": sly,
                "market_home_spread": market,
                "home_line_advantage": float(sly - market),
            },
            "market": {
                "source": market_source,
                "observed_at_utc": observed,
                "notes": str(g.get("market_notes", payload.get("market_notes", ""))),
            },
            "v2": {
                "model_version": model.model_version,
                "artifact_hash": model.artifact_hash,
                "training_start_season": model.training_start_season,
                "training_end_season": model.training_end_season,
                "push_shrink": model.push_shrink,
                "normal": pred["normal"],
                "hybrid": pred["hybrid"],
                "integer_sly_line": bool(pred["integer_sly_line"]),
            },
            "v1": g.get("v1") or {},
            "external": g.get("external") or {},
            "metadata": {
                "input_source": str(payload.get("input_source", "manual")),
                "notes": str(g.get("notes", "")),
            },
        })
    return events


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True, help="Snapshot batch JSON")
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--ledger", default=DEFAULT_LEDGER)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    payload = json.loads(Path(args.input).read_text(encoding="utf-8"))
    model = ShadowModel.load(args.model)
    events = build_events(payload, model)

    if args.dry_run:
        print(json.dumps({"status": "dry-run", "events": events}, indent=2, sort_keys=True))
        return

    finalized = append_events(args.ledger, events)
    print(json.dumps({
        "status": "captured",
        "ledger": args.ledger,
        "count": len(finalized),
        "batch_id": finalized[0]["batch_id"],
        "first_event_id": finalized[0]["event_id"],
        "tip_hash": finalized[-1]["row_hash"],
    }, indent=2))


if __name__ == "__main__":
    main()
