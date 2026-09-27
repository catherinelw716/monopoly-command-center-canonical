"""Build immutable V2 historical raw/staging datasets from nflverse.

This script intentionally stops before model training. Its job is to create a
reproducible football-data spine that can later feed point-in-time feature
engineering and walk-forward validation.

Usage:
    python v2/build_historical_dataset.py --start-season 2012 --end-season 2025 --output-dir v2/data

Dependencies:
    pip install nflreadpy polars pyarrow
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

import polars as pl
import nflreadpy as nfl


DEFAULT_START = 2012
DEFAULT_END = 2025


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def write_table(df: pl.DataFrame, path: Path) -> dict:
    """Write a source table as parquet and return compact manifest metadata."""
    ensure_dir(path.parent)
    df.write_parquet(path)
    return {
        "path": str(path),
        "rows": df.height,
        "columns": df.width,
        "column_names": df.columns,
    }


def safe_load(name: str, loader: Callable[[], pl.DataFrame]) -> tuple[pl.DataFrame | None, str | None]:
    """Load a source without hiding failures in the manifest."""
    try:
        df = loader()
        if not isinstance(df, pl.DataFrame):
            raise TypeError(f"{name} returned {type(df)!r}, expected polars.DataFrame")
        return df, None
    except Exception as exc:  # surfaced in manifest; not silently neutralized
        return None, f"{type(exc).__name__}: {exc}"


def add_build_metadata(df: pl.DataFrame, build_timestamp: str) -> pl.DataFrame:
    return df.with_columns(pl.lit(build_timestamp).alias("v2_retrieved_at_utc"))


def normalize_schedule_core(schedules: pl.DataFrame) -> pl.DataFrame:
    """Create a canonical game/result table while preserving raw source columns elsewhere.

    nflverse schedule schemas can evolve, so this only selects columns that are
    present and derives targets defensively.
    """
    wanted = [
        "game_id",
        "season",
        "game_type",
        "week",
        "gameday",
        "weekday",
        "gametime",
        "away_team",
        "home_team",
        "away_score",
        "home_score",
        "location",
        "roof",
        "surface",
        "temp",
        "wind",
        "away_rest",
        "home_rest",
        "spread_line",
        "away_moneyline",
        "home_moneyline",
        "total_line",
        "result",
        "total",
    ]
    present = [c for c in wanted if c in schedules.columns]
    out = schedules.select(present)

    if {"home_score", "away_score"}.issubset(out.columns):
        out = out.with_columns(
            (pl.col("home_score") - pl.col("away_score")).alias("home_margin")
        )

    # nflverse spread_line semantics should be validated in QA before using this
    # column as the V2 normalized home spread. We keep it source-native here.
    return out


def build_raw_tables(seasons: list[int], output_dir: Path) -> dict:
    build_ts = utc_now_iso()
    raw_dir = output_dir / "raw"
    staging_dir = output_dir / "staging"
    ensure_dir(raw_dir)
    ensure_dir(staging_dir)

    loaders: dict[str, Callable[[], pl.DataFrame]] = {
        "schedules": lambda: nfl.load_schedules(seasons),
        "pbp": lambda: nfl.load_pbp(seasons),
        "team_stats_week": lambda: nfl.load_team_stats(seasons, summary_level="week"),
        "player_stats_week": lambda: nfl.load_player_stats(seasons, summary_level="week"),
        "rosters_weekly": lambda: nfl.load_rosters_weekly(seasons),
        "injuries": lambda: nfl.load_injuries(seasons),
        "depth_charts": lambda: nfl.load_depth_charts(seasons),
        "snap_counts": lambda: nfl.load_snap_counts(seasons),
    }

    # Participation has narrower historical coverage. Requesting the full season
    # range may legitimately fail for early years; that failure is recorded.
    if max(seasons) >= 2016:
        participation_seasons = [s for s in seasons if s >= 2016]
        loaders["participation"] = lambda: nfl.load_participation(participation_seasons)

    manifest: dict = {
        "schema_version": "0.1.0",
        "build_timestamp_utc": build_ts,
        "seasons": seasons,
        "sources": {},
        "errors": {},
        "notes": [
            "Raw tables are source-native plus retrieval timestamp.",
            "No historical point-in-time market path is fabricated here.",
            "Closing/schedule line fields are baseline research inputs only until sign semantics pass QA.",
        ],
    }

    loaded: dict[str, pl.DataFrame] = {}
    for name, loader in loaders.items():
        print(f"Loading {name} ...")
        df, err = safe_load(name, loader)
        if err:
            manifest["errors"][name] = err
            print(f"  FAILED: {err}")
            continue
        assert df is not None
        df = add_build_metadata(df, build_ts)
        loaded[name] = df
        meta = write_table(df, raw_dir / f"{name}.parquet")
        manifest["sources"][name] = meta
        print(f"  {df.height:,} rows")

    if "schedules" in loaded:
        core = normalize_schedule_core(loaded["schedules"])
        manifest["sources"]["games_core"] = write_table(
            core, staging_dir / "games_core.parquet"
        )

    with (output_dir / "manifest.json").open("w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    return manifest


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--start-season", type=int, default=DEFAULT_START)
    parser.add_argument("--end-season", type=int, default=DEFAULT_END)
    parser.add_argument("--output-dir", type=Path, default=Path("v2/data"))
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.end_season < args.start_season:
        raise SystemExit("--end-season must be >= --start-season")
    seasons = list(range(args.start_season, args.end_season + 1))
    manifest = build_raw_tables(seasons, args.output_dir)
    print("\nBuild complete")
    print(f"Sources written: {len(manifest['sources'])}")
    print(f"Load errors: {len(manifest['errors'])}")
    if manifest["errors"]:
        print("Review manifest.json before feature engineering.")


if __name__ == "__main__":
    main()
