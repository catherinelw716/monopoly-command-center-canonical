"""Pre-submit reconciliation guardrail for NFL Monopoly.

Compares proposed Catherine/Amanda wagers with the latest authoritative model side
while enforcing Sly-line provenance. Opposite-side wagers are permitted only as
explicit, timestamped overrides. This module does not alter NFL probabilities or stake
sizes; it prevents stale decision state from silently overriding the final model view.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict


def _load(path: str | Path) -> Dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _freeze_index(freeze: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    rows = freeze.get("games", [])
    out = {}
    for row in rows:
        gid = row.get("game") or row.get("game_id")
        if not gid:
            raise ValueError("Sly freeze row missing game/game_id")
        if gid in out:
            raise ValueError(f"duplicate Sly game: {gid}")
        out[gid] = row
    return out


def _model_index(model: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    rows = model.get("games") or model.get("recommendations") or model.get("model_game_results") or []
    out = {}
    for row in rows:
        gid = row.get("game") or row.get("game_id")
        if not gid:
            raise ValueError("model row missing game/game_id")
        side = row.get("pick") or row.get("model_pick") or row.get("recommended_pick")
        if not side:
            raise ValueError(f"model row missing pick for {gid}")
        out[gid] = {**row, "pick": side}
    return out


def _team_from_pick(pick: str) -> str:
    text = str(pick).strip().upper()
    if not text:
        return ""
    return text.split()[0]


def reconcile(freeze: Dict[str, Any], model: Dict[str, Any], portfolio: Dict[str, Any]) -> Dict[str, Any]:
    freeze_idx = _freeze_index(freeze)
    model_idx = _model_index(model)
    entries = portfolio.get("entries") or portfolio.get("portfolios") or {}
    if not entries:
        raise ValueError("portfolio must contain entries or portfolios")

    rows = []
    hard_errors = []
    override_count = 0

    for entry, bets in entries.items():
        for bet in bets:
            gid = bet.get("game") or bet.get("game_id")
            pick = bet.get("pick") or bet.get("side_display")
            if not gid or not pick:
                hard_errors.append(f"{entry}: wager missing game/pick")
                continue
            if gid not in freeze_idx:
                hard_errors.append(f"{entry} {gid}: not present in canonical Sly freeze")
                continue
            if gid not in model_idx:
                hard_errors.append(f"{entry} {gid}: missing authoritative model recommendation")
                continue

            freeze_row = freeze_idx[gid]
            model_row = model_idx[gid]
            model_pick = str(model_row["pick"])
            proposed_team = _team_from_pick(str(pick))
            model_team = _team_from_pick(model_pick)
            status = "ALIGNED" if proposed_team == model_team else "OVERRIDE"

            # If portfolio carries an explicit Sly line, it must match the canonical freeze.
            proposed_home_spread = bet.get("sly_home_spread")
            canonical_home_spread = freeze_row.get("sly_home_spread")
            line_status = "CANONICAL"
            if proposed_home_spread is not None and canonical_home_spread is not None:
                if float(proposed_home_spread) != float(canonical_home_spread):
                    line_status = "LINE_MISMATCH"
                    hard_errors.append(
                        f"{entry} {gid}: proposed sly_home_spread={proposed_home_spread} "
                        f"!= canonical {canonical_home_spread}"
                    )

            override_reason = bet.get("override_reason")
            override_timestamp = bet.get("override_timestamp")
            if status == "OVERRIDE":
                override_count += 1
                if not override_reason or not override_timestamp:
                    hard_errors.append(
                        f"{entry} {gid}: opposite-side wager requires override_reason and override_timestamp"
                    )

            rows.append({
                "entry": entry,
                "game": gid,
                "proposed_pick": pick,
                "model_pick": model_pick,
                "status": status,
                "line_status": line_status,
                "canonical_sly_pick_display": freeze_row.get("sly_pick_display"),
                "canonical_sly_home_spread": canonical_home_spread,
                "amount": bet.get("amount") or bet.get("wager"),
                "model_grade": model_row.get("grade") or model_row.get("confidence"),
                "model_rank": model_row.get("rank"),
                "override_reason": override_reason,
                "override_timestamp": override_timestamp,
            })

    return {
        "status": "PASS" if not hard_errors else "BLOCK",
        "season": freeze.get("season"),
        "week": freeze.get("week"),
        "canonical_sly_freeze_type": freeze.get("freeze_type"),
        "rows": rows,
        "summary": {
            "wagers": len(rows),
            "aligned": sum(r["status"] == "ALIGNED" for r in rows),
            "overrides": override_count,
            "line_mismatches": sum(r["line_status"] == "LINE_MISMATCH" for r in rows),
            "hard_errors": len(hard_errors),
        },
        "hard_errors": hard_errors,
        "guardrail": (
            "Final submission is blocked when a wager is missing from the canonical Sly freeze, "
            "uses a conflicting frozen line, lacks an authoritative model row, or opposes the final "
            "model side without an explicit reason and timestamp."
        ),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sly-freeze", required=True)
    ap.add_argument("--model", required=True)
    ap.add_argument("--portfolio", required=True)
    ap.add_argument("--output", required=True)
    args = ap.parse_args()

    result = reconcile(_load(args.sly_freeze), _load(args.model), _load(args.portfolio))
    Path(args.output).write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    if result["status"] != "PASS":
        raise SystemExit(2)


if __name__ == "__main__":
    main()
