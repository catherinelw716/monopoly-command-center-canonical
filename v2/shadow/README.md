# Prospective Shadow Ledger

The live append-only ledger is created at `v2/shadow/shadow_ledger.jsonl` when the first valid prospective snapshot is captured.

Do not pre-populate this directory with reconstructed historical predictions. A valid `prediction_capture` must have been recorded before the scheduled kickoff and must preserve the point-in-time Sly and market observations used by the model.

Operational scripts:
- `v2/capture_shadow_snapshot.py` — append FRIDAY_FREEZE or PRE_KICK_FINAL prediction events
- `v2/validate_shadow_ledger.py` — verify timing, schema, duplicate-snapshot rules, and SHA-256 hash chain
- `v2/settle_shadow_results.py` — append final results without changing prediction events
- `v2/score_shadow_ledger.py` — compute prospective Brier/log-loss/calibration summaries after settlement

Protocol: `v2/SHADOW_VALIDATION_PROTOCOL.md`.
