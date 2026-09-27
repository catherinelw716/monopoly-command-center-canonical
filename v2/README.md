# V2 Research Pipeline

This directory is intentionally isolated from the production Command Center.

**V1 remains the production champion. Nothing in `/v2/` is loaded by `server.js`.**

## Current phase

Phase 1 — point-in-time data feasibility and historical dataset construction.

Artifacts:
- `../V2_MODEL_SPEC.md` — model + Monopoly optimizer design
- `../V2_DATA_FEASIBILITY.md` — source coverage/gap audit
- `data_contract.json` — machine-readable signs, timestamps, leakage rules and Monopoly scoring
- `build_historical_dataset.py` — raw nflverse ingestion scaffold
- `qa_checks.py` — integrity/leakage checks

## Environment

Recommended Python 3.11+.

```bash
pip install nflreadpy polars pyarrow
```

`nflreadpy` is the Python nflverse reader and returns Polars DataFrames.

## Build historical source tables

```bash
python v2/build_historical_dataset.py \
  --start-season 2012 \
  --end-season 2025 \
  --output-dir v2/data
```

Expected output layout:

```text
v2/data/
  manifest.json
  raw/
    schedules.parquet
    pbp.parquet
    team_stats_week.parquet
    player_stats_week.parquet
    rosters_weekly.parquet
    injuries.parquet
    depth_charts.parquet
    snap_counts.parquet
    participation.parquet   # where historical coverage permits
  staging/
    games_core.parquet
```

The manifest records any loader failure rather than silently treating the source as neutral/missing evidence.

## Run QA

```bash
python v2/qa_checks.py --data-dir v2/data
```

The first pass verifies game-key integrity and target arithmetic. When the gold point-in-time table exists, the same QA script enforces timestamp/leakage contracts.

## Important research restrictions

1. **Do not train on source-native `spread_line` until its orientation/sign is empirically validated.** The staging table deliberately preserves it as source-native.
2. **Do not use closing lines in a historical Friday snapshot.** A closing line is future information unless it was already the live quote at that timestamp.
3. **Do not backfill unavailable SportsLine/Gridiron predictions.** External sources are prospective ledgers unless we possess attributable point-in-time archives.
4. **Do not reconstruct Friday→Sunday stale-line paths from only opener/close.** Exact path features require timestamped historical odds.
5. **Do not tune on 2026 Week 3 outcomes.** Architecture and hyperparameters must be frozen before using those results as prospective evidence.
6. **Missing evidence is missing.** It is never converted to a 50% probability or a neutral model vote.

## Next implementation stage

After the raw build passes QA:

1. validate nflverse spread sign/orientation against completed-game examples;
2. create game-level PBP aggregates;
3. create strictly lagged rolling team/QB features;
4. build `FRIDAY_FREEZE` / `PRE_KICK_FINAL` point-in-time rows where source timestamps permit;
5. fit the market-only baseline before adding football features;
6. establish the walk-forward evaluation harness.

Paid historical odds are not a blocker for steps 1–5. They are a blocker only for a true retrospective test of the unique Sly Friday→Sunday stale-line advantage.
