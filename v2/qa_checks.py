"""V2 dataset integrity and leakage checks.

Run after build_historical_dataset.py. These tests are intentionally strict:
missing/ambiguous fields fail loudly rather than being silently treated as
neutral evidence.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import polars as pl


class QAFailure(RuntimeError):
    pass


def require_columns(df: pl.DataFrame, cols: list[str], table: str) -> None:
    missing = [c for c in cols if c not in df.columns]
    if missing:
        raise QAFailure(f"{table}: missing required columns: {missing}")


def assert_unique(df: pl.DataFrame, cols: list[str], table: str) -> None:
    require_columns(df, cols, table)
    dupes = df.group_by(cols).len().filter(pl.col("len") > 1)
    if dupes.height:
        raise QAFailure(f"{table}: duplicate keys for {cols}; sample={dupes.head(5).to_dicts()}")


def check_games_core(df: pl.DataFrame) -> list[str]:
    notes: list[str] = []
    require_columns(df, ["game_id", "season", "week", "home_team", "away_team"], "games_core")
    assert_unique(df, ["game_id"], "games_core")

    same_team = df.filter(pl.col("home_team") == pl.col("away_team"))
    if same_team.height:
        raise QAFailure("games_core: home_team equals away_team")

    if "home_margin" in df.columns and {"home_score", "away_score"}.issubset(df.columns):
        bad_margin = df.filter(
            pl.col("home_margin") != (pl.col("home_score") - pl.col("away_score"))
        )
        if bad_margin.height:
            raise QAFailure("games_core: home_margin arithmetic mismatch")

    if "spread_line" in df.columns:
        notes.append(
            "spread_line exists but remains SOURCE-NATIVE; do not map it to home_spread until sign semantics are empirically validated."
        )

    return notes


def check_timestamp_order(df: pl.DataFrame, source_col: str, snapshot_col: str, table: str) -> None:
    require_columns(df, [source_col, snapshot_col], table)
    bad = df.filter(
        pl.col(source_col).is_not_null()
        & pl.col(snapshot_col).is_not_null()
        & (pl.col(source_col) > pl.col(snapshot_col))
    )
    if bad.height:
        raise QAFailure(
            f"{table}: leakage — {source_col} occurs after {snapshot_col}; sample={bad.head(5).to_dicts()}"
        )


def check_gold_snapshot(df: pl.DataFrame) -> list[str]:
    notes: list[str] = []
    require_columns(
        df,
        [
            "game_id",
            "snapshot_name",
            "snapshot_timestamp",
            "kickoff_timestamp",
            "sly_home_spread",
            "sly_issued_timestamp",
        ],
        "gold_snapshot",
    )
    assert_unique(df, ["game_id", "snapshot_name", "snapshot_timestamp"], "gold_snapshot")

    bad_after_kick = df.filter(pl.col("snapshot_timestamp") >= pl.col("kickoff_timestamp"))
    if bad_after_kick.height:
        raise QAFailure("gold_snapshot: snapshot_timestamp must be strictly pre-kick")

    bad_sly = df.filter(pl.col("sly_issued_timestamp") > pl.col("snapshot_timestamp"))
    if bad_sly.height:
        raise QAFailure("gold_snapshot: Sly line issued after prediction snapshot")

    timestamp_pairs = [
        ("market_snapshot_timestamp", "snapshot_timestamp"),
        ("sportsline_timestamp", "snapshot_timestamp"),
        ("gridiron_timestamp", "snapshot_timestamp"),
        ("lucas_timestamp", "snapshot_timestamp"),
        ("home_injury_asof", "snapshot_timestamp"),
        ("away_injury_asof", "snapshot_timestamp"),
    ]
    for src, snap in timestamp_pairs:
        if src in df.columns:
            check_timestamp_order(df, src, snap, "gold_snapshot")

    if "snapshot_name" in df.columns:
        allowed = {"FRIDAY_FREEZE", "PRE_KICK_FINAL"}
        seen = set(df.select("snapshot_name").drop_nulls().to_series().to_list())
        unknown = seen - allowed
        if unknown:
            raise QAFailure(f"gold_snapshot: unknown snapshot_name values {sorted(unknown)}")

    if "sportsline_side" in df.columns and "sportsline_reference_spread" in df.columns:
        incomplete = df.filter(
            pl.col("sportsline_side").is_not_null()
            & pl.col("sportsline_reference_spread").is_null()
        )
        if incomplete.height:
            raise QAFailure("gold_snapshot: SportsLine side exists without native reference spread")

    if "gridiron_probability" in df.columns:
        bad_prob = df.filter(
            pl.col("gridiron_probability").is_not_null()
            & ((pl.col("gridiron_probability") < 0) | (pl.col("gridiron_probability") > 1))
        )
        if bad_prob.height:
            raise QAFailure("gold_snapshot: Gridiron probability outside [0,1]")

    if "home_cover" in df.columns and "ats_margin_home" in df.columns:
        bad_cover = df.filter(
            pl.col("ats_margin_home").is_not_null()
            & (
                (pl.col("home_cover") != (pl.col("ats_margin_home") > 0))
                & (pl.col("ats_margin_home") != 0)
            )
        )
        if bad_cover.height:
            raise QAFailure("gold_snapshot: home_cover inconsistent with ats_margin_home")

    notes.append("Gold leakage checks passed for every timestamped source column present.")
    return notes


def run_qa(data_dir: Path) -> dict:
    report = {"status": "PASS", "checks": [], "notes": [], "errors": []}

    try:
        games_path = data_dir / "staging" / "games_core.parquet"
        if not games_path.exists():
            raise QAFailure(f"missing {games_path}; run build_historical_dataset.py first")
        games = pl.read_parquet(games_path)
        report["notes"].extend(check_games_core(games))
        report["checks"].append("games_core_integrity")

        gold_path = data_dir / "gold" / "game_snapshots.parquet"
        if gold_path.exists():
            gold = pl.read_parquet(gold_path)
            report["notes"].extend(check_gold_snapshot(gold))
            report["checks"].append("gold_point_in_time_leakage")
        else:
            report["notes"].append(
                "Gold snapshot table does not exist yet; point-in-time leakage tests will activate when feature engineering creates it."
            )
    except Exception as exc:
        report["status"] = "FAIL"
        report["errors"].append(f"{type(exc).__name__}: {exc}")

    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", type=Path, default=Path("v2/data"))
    parser.add_argument("--report", type=Path, default=Path("v2/data/qa_report.json"))
    args = parser.parse_args()

    report = run_qa(args.data_dir)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    if report["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
