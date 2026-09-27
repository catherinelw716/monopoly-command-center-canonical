"""Fit the frozen V2 global-hybrid artifact for prospective shadow use.

The architecture is frozen. The only tuned quantity is the previously allowed
shrinkage choice from V2-0006C (25 or 75), selected using the final historical
season as an inner validation fold exactly as in the registered research code.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from run_hybrid_keynumber_experiment import load_games, tune
from shadow_model import build_artifact_from_games


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--start-season", type=int, default=2016)
    ap.add_argument("--end-season", type=int, default=2025)
    ap.add_argument("--out", default="v2/model_artifacts/v2_global_hybrid_2016_2025.json")
    args = ap.parse_args()

    df = load_games(args.start_season, args.end_season)
    selected, tuning = tune(df, "global_hybrid")
    _, shrink = selected
    artifact = build_artifact_from_games(df, float(shrink), args.start_season, args.end_season)
    artifact["historical_tuning"] = tuning

    # Recompute the artifact hash after adding frozen tuning provenance.
    from shadow_model import artifact_hash
    core = {k: v for k, v in artifact.items() if k not in {"artifact_hash", "generated_at_utc"}}
    artifact["artifact_hash"] = artifact_hash(core)

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(artifact, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print(json.dumps({
        "status": "ok",
        "output": str(out),
        "model_version": artifact["model_version"],
        "artifact_hash": artifact["artifact_hash"],
        "training_seasons": [args.start_season, args.end_season],
        "n_training_games": artifact["n_training_games"],
        "residual_mu": artifact["residual_mu"],
        "residual_sigma": artifact["residual_sigma"],
        "selected_push_shrink": artifact["push_shrink"],
        "tuning": tuning,
    }, indent=2))
    # Full canonical artifact is emitted as a single audit line so a build log
    # can be independently compared with the committed frozen artifact.
    print("SHADOW_MODEL_ARTIFACT=" + json.dumps(artifact, sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    main()
