"""Build the first leakage-safe V2 football feature table.

Inputs (created by build_historical_dataset.py):
    v2/data/raw/pbp.parquet
    v2/data/staging/games_core.parquet

Output:
    v2/data/gold/baseline_games.parquet

This first baseline deliberately uses only prior completed-game PBP aggregates.
It does NOT use injuries, external sources, public betting, or intra-week market
movement yet. The purpose is to establish a clean market + football residual
baseline before adding more feature families.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import polars as pl


ROLL_WINDOWS = (4, 8)


def require(df: pl.DataFrame, columns: list[str], name: str) -> None:
    missing = [c for c in columns if c not in df.columns]
    if missing:
        raise ValueError(f"{name}: missing columns {missing}")


def aggregate_team_games(pbp: pl.DataFrame, games: pl.DataFrame) -> pl.DataFrame:
    """Create one row per team-game with offense and defense PBP metrics."""
    require(
        pbp,
        ["game_id", "posteam", "defteam", "epa", "play_type"],
        "pbp",
    )
    require(games, ["game_id", "season", "week", "gameday", "home_team", "away_team"], "games")

    cols = pbp.columns
    exprs = [
        pl.col("epa").mean().alias("off_epa"),
        pl.len().alias("off_plays"),
    ]
    if "success" in cols:
        exprs.append(pl.col("success").mean().alias("off_success_rate"))
    if "qb_dropback" in cols:
        exprs.append(
            pl.when(pl.col("qb_dropback") == 1)
            .then(pl.col("epa"))
            .otherwise(None)
            .mean()
            .alias("off_pass_epa")
        )
    else:
        exprs.append(
            pl.when(pl.col("play_type") == "pass")
            .then(pl.col("epa"))
            .otherwise(None)
            .mean()
            .alias("off_pass_epa")
        )
    if "rush_attempt" in cols:
        exprs.append(
            pl.when(pl.col("rush_attempt") == 1)
            .then(pl.col("epa"))
            .otherwise(None)
            .mean()
            .alias("off_rush_epa")
        )
    else:
        exprs.append(
            pl.when(pl.col("play_type") == "run")
            .then(pl.col("epa"))
            .otherwise(None)
            .mean()
            .alias("off_rush_epa")
        )

    usable = pbp.filter(
        pl.col("posteam").is_not_null()
        & pl.col("defteam").is_not_null()
        & pl.col("epa").is_not_null()
        & pl.col("play_type").is_in(["pass", "run"])
    )

    offense = usable.group_by(["game_id", "posteam"]).agg(exprs).rename({"posteam": "team"})

    def_exprs = [
        pl.col("epa").mean().alias("def_epa_allowed"),
        pl.len().alias("def_plays"),
    ]
    if "success" in cols:
        def_exprs.append(pl.col("success").mean().alias("def_success_allowed"))
    if "qb_dropback" in cols:
        def_exprs.append(
            pl.when(pl.col("qb_dropback") == 1)
            .then(pl.col("epa"))
            .otherwise(None)
            .mean()
            .alias("def_pass_epa_allowed")
        )
    else:
        def_exprs.append(
            pl.when(pl.col("play_type") == "pass")
            .then(pl.col("epa"))
            .otherwise(None)
            .mean()
            .alias("def_pass_epa_allowed")
        )
    if "rush_attempt" in cols:
        def_exprs.append(
            pl.when(pl.col("rush_attempt") == 1)
            .then(pl.col("epa"))
            .otherwise(None)
            .mean()
            .alias("def_rush_epa_allowed")
        )
    else:
        def_exprs.append(
            pl.when(pl.col("play_type") == "run")
            .then(pl.col("epa"))
            .otherwise(None)
            .mean()
            .alias("def_rush_epa_allowed")
        )

    defense = usable.group_by(["game_id", "defteam"]).agg(def_exprs).rename({"defteam": "team"})

    team_games = offense.join(defense, on=["game_id", "team"], how="inner")

    schedule_meta = games.select(
        ["game_id", "season", "week", "gameday", "home_team", "away_team"]
    )
    team_games = team_games.join(schedule_meta, on="game_id", how="left")

    return team_games.sort(["team", "gameday", "game_id"])


def add_lagged_rolls(team_games: pl.DataFrame) -> pl.DataFrame:
    """Add rolling features shifted by one team game to prevent target leakage."""
    metric_cols = [
        c
        for c in [
            "off_epa",
            "off_success_rate",
            "off_pass_epa",
            "off_rush_epa",
            "def_epa_allowed",
            "def_success_allowed",
            "def_pass_epa_allowed",
            "def_rush_epa_allowed",
        ]
        if c in team_games.columns
    ]

    exprs: list[pl.Expr] = []
    for metric in metric_cols:
        for window in ROLL_WINDOWS:
            exprs.append(
                pl.col(metric)
                .shift(1)
                .rolling_mean(window_size=window, min_samples=min(3, window))
                .over("team")
                .alias(f"{metric}_roll{window}")
            )

    # Prior-game counts are useful for early-season shrinkage/uncertainty.
    exprs.append(pl.cum_count("game_id").over("team").alias("prior_games_count"))

    return team_games.with_columns(exprs)


def to_game_rows(team_features: pl.DataFrame, games: pl.DataFrame) -> pl.DataFrame:
    """Join lagged team features onto home/away target-game rows."""
    feature_cols = [
        c
        for c in team_features.columns
        if c.endswith("_roll4") or c.endswith("_roll8") or c == "prior_games_count"
    ]

    base_cols = [
        c
        for c in [
            "game_id",
            "season",
            "game_type",
            "week",
            "gameday",
            "home_team",
            "away_team",
            "home_score",
            "away_score",
            "home_margin",
            "nflverse_spread_line_source",
            "home_spread_closing",
            "home_spread_odds",
            "away_spread_odds",
            "total_line",
            "home_rest",
            "away_rest",
            "roof",
            "surface",
            "temp",
            "wind",
        ]
        if c in games.columns
    ]
    game_rows = games.select(base_cols)

    home = team_features.select(
        ["game_id", "team"] + feature_cols
    ).rename(
        {"team": "home_team"}
        | {c: f"home_{c}" for c in feature_cols}
    )
    away = team_features.select(
        ["game_id", "team"] + feature_cols
    ).rename(
        {"team": "away_team"}
        | {c: f"away_{c}" for c in feature_cols}
    )

    game_rows = game_rows.join(home, on=["game_id", "home_team"], how="left")
    game_rows = game_rows.join(away, on=["game_id", "away_team"], how="left")

    diffs: list[pl.Expr] = []
    for c in feature_cols:
        hc, ac = f"home_{c}", f"away_{c}"
        if hc in game_rows.columns and ac in game_rows.columns and c != "prior_games_count":
            diffs.append((pl.col(hc) - pl.col(ac)).alias(f"diff_{c}"))
    if {"home_rest", "away_rest"}.issubset(game_rows.columns):
        diffs.append((pl.col("home_rest") - pl.col("away_rest")).alias("rest_diff"))

    if diffs:
        game_rows = game_rows.with_columns(diffs)

    # Keep regular-season completed games for the first model-development table.
    if "game_type" in game_rows.columns:
        game_rows = game_rows.filter(pl.col("game_type") == "REG")
    if "home_margin" in game_rows.columns:
        game_rows = game_rows.filter(pl.col("home_margin").is_not_null())

    return game_rows.sort(["season", "week", "gameday", "game_id"])


def build(data_dir: Path) -> pl.DataFrame:
    pbp_path = data_dir / "raw" / "pbp.parquet"
    games_path = data_dir / "staging" / "games_core.parquet"
    if not pbp_path.exists() or not games_path.exists():
        raise FileNotFoundError("Run v2/build_historical_dataset.py before baseline feature construction")

    pbp = pl.read_parquet(pbp_path)
    games = pl.read_parquet(games_path)

    team_games = aggregate_team_games(pbp, games)
    team_features = add_lagged_rolls(team_games)
    baseline = to_game_rows(team_features, games)

    out_dir = data_dir / "gold"
    out_dir.mkdir(parents=True, exist_ok=True)
    team_features.write_parquet(out_dir / "team_game_features.parquet")
    baseline.write_parquet(out_dir / "baseline_games.parquet")
    return baseline


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", type=Path, default=Path("v2/data"))
    args = parser.parse_args()
    df = build(args.data_dir)
    print(f"Wrote {df.height:,} leakage-safe baseline game rows to {args.data_dir / 'gold' / 'baseline_games.parquet'}")
    print("Rows intentionally use only shifted prior-game football features.")


if __name__ == "__main__":
    main()
