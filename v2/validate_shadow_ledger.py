"""Validate V2 prospective shadow ledger integrity and timing rules."""
from __future__ import annotations

import argparse
import json

from shadow_ledger import read_events, validate_chain


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ledger", default="v2/shadow/shadow_ledger.jsonl")
    args = ap.parse_args()
    events = read_events(args.ledger)
    result = validate_chain(events)
    prediction_count = sum(1 for e in events if e.get("event_type") == "prediction_capture")
    settlement_count = sum(1 for e in events if e.get("event_type") == "result_settlement")
    correction_count = sum(1 for e in events if e.get("event_type") == "correction")
    result.update({
        "prediction_events": prediction_count,
        "settlement_events": settlement_count,
        "correction_events": correction_count,
    })
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
