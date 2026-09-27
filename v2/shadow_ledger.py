"""Append-only, hash-chained event ledger for V2 prospective validation."""
from __future__ import annotations

import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

GENESIS_HASH = "0" * 64
SCHEMA_VERSION = "1.0"


def canonical_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def parse_utc(value: str) -> datetime:
    s = str(value).strip()
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    dt = datetime.fromisoformat(s)
    if dt.tzinfo is None:
        raise ValueError(f"Timestamp must be timezone-aware: {value}")
    return dt.astimezone(timezone.utc)


def iso_utc(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def compute_row_hash(event_without_hash: dict[str, Any]) -> str:
    return hashlib.sha256(canonical_json(event_without_hash).encode("utf-8")).hexdigest()


def finalize_event(event: dict[str, Any], prev_hash: str) -> dict[str, Any]:
    x = dict(event)
    x["schema_version"] = SCHEMA_VERSION
    x["prev_hash"] = prev_hash
    x.pop("row_hash", None)
    x["row_hash"] = compute_row_hash(x)
    return x


def read_events(path: str | Path) -> list[dict[str, Any]]:
    p = Path(path)
    if not p.exists():
        return []
    out: list[dict[str, Any]] = []
    for i, line in enumerate(p.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON on ledger line {i}: {exc}") from exc
    return out


def validate_probability_triplet(d: dict[str, Any], prefix: str) -> None:
    vals = [float(d["p_home_loss"]), float(d["p_push"]), float(d["p_home_cover"])]
    if any(v < -1e-12 or v > 1 + 1e-12 for v in vals):
        raise ValueError(f"{prefix} contains probability outside [0,1]: {vals}")
    if not math.isclose(sum(vals), 1.0, abs_tol=1e-8):
        raise ValueError(f"{prefix} probabilities do not sum to 1: {vals}")


def validate_event_semantics(event: dict[str, Any]) -> None:
    et = event.get("event_type")
    if et == "prediction_capture":
        snap = event.get("snapshot_type")
        if snap not in {"FRIDAY_FREEZE", "PRE_KICK_FINAL"}:
            raise ValueError(f"Invalid snapshot_type: {snap}")
        captured = parse_utc(event["captured_at_utc"])
        kickoff = parse_utc(event["game"]["kickoff_utc"])
        observed = parse_utc(event["market"]["observed_at_utc"])
        if captured >= kickoff:
            raise ValueError(f"Prediction capture is not pre-kickoff for {event['game']['game_id']}")
        if observed >= kickoff:
            raise ValueError(f"Market observation is not pre-kickoff for {event['game']['game_id']}")
        if observed > captured:
            raise ValueError(f"Market observation occurs after ledger capture for {event['game']['game_id']}")
        validate_probability_triplet(event["v2"]["normal"], "v2.normal")
        validate_probability_triplet(event["v2"]["hybrid"], "v2.hybrid")
        sly = float(event["lines"]["sly_home_spread"])
        ppush = float(event["v2"]["hybrid"]["p_push"])
        is_integer = math.isclose(sly, round(sly), abs_tol=1e-9)
        if not is_integer and not math.isclose(ppush, 0.0, abs_tol=1e-12):
            raise ValueError(f"Half-point Sly line should have zero push mass: {sly} -> {ppush}")
    elif et == "result_settlement":
        if "home_margin" not in event.get("result", {}):
            raise ValueError("Settlement missing result.home_margin")
    elif et == "correction":
        if not event.get("supersedes_event_id"):
            raise ValueError("Correction missing supersedes_event_id")
        if not str(event.get("reason", "")).strip():
            raise ValueError("Correction missing reason")
    else:
        raise ValueError(f"Unknown event_type: {et}")


def validate_chain(events: Iterable[dict[str, Any]]) -> dict[str, Any]:
    prev = GENESIS_HASH
    count = 0
    seen_ids: set[str] = set()
    prediction_keys: set[tuple[Any, ...]] = set()
    for idx, event in enumerate(events, start=1):
        count += 1
        if event.get("schema_version") != SCHEMA_VERSION:
            raise ValueError(f"Line {idx}: unsupported schema_version={event.get('schema_version')}")
        if event.get("prev_hash") != prev:
            raise ValueError(f"Line {idx}: prev_hash mismatch")
        row_hash = event.get("row_hash")
        core = dict(event)
        core.pop("row_hash", None)
        expected = compute_row_hash(core)
        if row_hash != expected:
            raise ValueError(f"Line {idx}: row_hash mismatch")
        event_id = str(event.get("event_id", ""))
        if not event_id or event_id in seen_ids:
            raise ValueError(f"Line {idx}: missing or duplicate event_id={event_id}")
        seen_ids.add(event_id)
        validate_event_semantics(event)
        if event.get("event_type") == "prediction_capture":
            key = (
                int(event["season"]), int(event["week"]), event["game"]["game_id"], event["snapshot_type"]
            )
            if key in prediction_keys:
                raise ValueError(f"Line {idx}: duplicate prediction snapshot key {key}; use a correction event instead")
            prediction_keys.add(key)
        prev = str(row_hash)
    return {"status": "ok", "events": count, "tip_hash": prev}


def append_events(path: str | Path, new_events: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    p = Path(path)
    existing = read_events(p)
    state = validate_chain(existing)
    prev = state["tip_hash"]
    finalized: list[dict[str, Any]] = []
    for event in new_events:
        x = finalize_event(event, prev)
        validate_event_semantics(x)
        finalized.append(x)
        prev = x["row_hash"]

    # Validate the complete prospective chain before touching disk.
    validate_chain(existing + finalized)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a", encoding="utf-8") as f:
        for event in finalized:
            f.write(canonical_json(event) + "\n")
    return finalized
