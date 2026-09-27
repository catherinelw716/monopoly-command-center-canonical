"""Deterministic QA for the V2 prospective shadow pipeline.

Uses synthetic fixture values only to test mechanics; no synthetic records are
written to the production shadow ledger.
"""
from __future__ import annotations

import copy
import tempfile
from pathlib import Path

from capture_shadow_snapshot import build_events
from shadow_ledger import append_events, read_events, validate_chain
from shadow_model import ShadowModel, artifact_hash


def fixture_model() -> ShadowModel:
    core = {
        "model_version": "QA-fixture",
        "training_start_season": 2016,
        "training_end_season": 2025,
        "n_training_games": 1000,
        "residual_mu": 0.0,
        "residual_sigma": 13.0,
        "push_shrink": 25.0,
        "margin_counts": {"3": 90, "7": 55, "-3": 85, "-7": 50},
    }
    d = dict(core)
    d["artifact_hash"] = artifact_hash(core)
    return ShadowModel.from_dict(d)


def main() -> None:
    model = fixture_model()
    payload = {
        "season": 2099,
        "week": 1,
        "snapshot_type": "FRIDAY_FREEZE",
        "captured_at_utc": "2099-09-01T12:00:00Z",
        "market_source": "qa-fixture",
        "market_observed_at_utc": "2099-09-01T11:59:00Z",
        "games": [
            {
                "game_id": "2099_01_AAA_BBB",
                "away_team": "AAA",
                "home_team": "BBB",
                "kickoff_utc": "2099-09-03T17:00:00Z",
                "sly_home_spread": -3.0,
                "market_home_spread": -2.5,
            },
            {
                "game_id": "2099_01_CCC_DDD",
                "away_team": "CCC",
                "home_team": "DDD",
                "kickoff_utc": "2099-09-03T20:00:00Z",
                "sly_home_spread": 3.5,
                "market_home_spread": 3.0,
            },
        ],
    }
    events = build_events(payload, model)
    assert len(events) == 2
    integer = events[0]["v2"]
    halfpoint = events[1]["v2"]
    assert integer["hybrid"]["p_push"] > integer["normal"]["p_push"]
    assert halfpoint["hybrid"]["p_push"] == 0.0
    assert abs(sum(halfpoint["hybrid"][k] for k in ["p_home_loss", "p_push", "p_home_cover"]) - 1.0) < 1e-9

    with tempfile.TemporaryDirectory() as td:
        ledger = Path(td) / "shadow.jsonl"
        finalized = append_events(ledger, events)
        result = validate_chain(read_events(ledger))
        assert result["events"] == 2
        assert result["tip_hash"] == finalized[-1]["row_hash"]

        tampered = read_events(ledger)
        tampered[0] = copy.deepcopy(tampered[0])
        tampered[0]["lines"]["market_home_spread"] = -9.5
        failed = False
        try:
            validate_chain(tampered)
        except ValueError:
            failed = True
        assert failed, "Tamper detection must fail closed"

        # Duplicate same game/snapshot must also fail closed.
        failed = False
        try:
            append_events(ledger, events[:1])
        except ValueError:
            failed = True
        assert failed, "Duplicate snapshot key must be rejected"

    # Post-kickoff capture must fail semantic validation when appended.
    late = copy.deepcopy(payload)
    late["captured_at_utc"] = "2099-09-04T12:00:00Z"
    late_events = build_events(late, model)
    with tempfile.TemporaryDirectory() as td:
        failed = False
        try:
            append_events(Path(td) / "late.jsonl", late_events)
        except ValueError:
            failed = True
        assert failed, "Post-kickoff prospective capture must be rejected"

    print("Shadow pipeline QA passed: probabilities, timing guard, duplicate guard, and hash tamper detection.")


if __name__ == "__main__":
    main()
