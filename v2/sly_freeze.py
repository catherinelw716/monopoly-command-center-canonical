"""Canonical Sly frozen-line loader.

All Week 4 downstream analysis should load Sly target lines through this module rather
than copying spreads into model, optimizer, or UI inputs.
"""
from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class SlyGame:
    game: str
    away: str
    home: str
    sly_pick_display: str
    sly_home_spread: float
    game_time_et: str


@dataclass(frozen=True)
class SlyFreeze:
    season: int
    week: int
    freeze_type: str
    freeze_date_local: str
    games: tuple[SlyGame, ...]
    excluded_or_missing: tuple[dict, ...]
    source_path: str

    def by_game(self) -> dict[str, SlyGame]:
        return {g.game: g for g in self.games}


def canonical_freeze_path(season: int, week: int, root: str | Path = ".") -> Path:
    return Path(root) / "v2" / f"season_{int(season)}" / f"week_{int(week):02d}_sly_freeze.json"


def _validate_games(games: Iterable[SlyGame]) -> tuple[SlyGame, ...]:
    rows = tuple(games)
    if not rows:
        raise ValueError("Sly freeze must contain at least one game")

    game_ids = [g.game for g in rows]
    if len(game_ids) != len(set(game_ids)):
        raise ValueError("duplicate game in Sly freeze")

    teams: list[str] = []
    for g in rows:
        expected_id = f"{g.away} @ {g.home}"
        if g.game != expected_id:
            raise ValueError(f"game orientation mismatch: {g.game} != {expected_id}")
        if g.away == g.home:
            raise ValueError(f"same team on both sides: {g.game}")
        if not g.game_time_et:
            raise ValueError(f"missing kickoff time: {g.game}")
        if not isinstance(g.sly_home_spread, float):
            raise ValueError(f"sly_home_spread must be normalized float: {g.game}")
        teams.extend([g.away, g.home])

    if len(teams) != len(set(teams)):
        raise ValueError("a team appears in more than one eligible Sly game")
    return rows


def load_sly_freeze(season: int, week: int, root: str | Path = ".") -> SlyFreeze:
    path = canonical_freeze_path(season, week, root)
    raw = json.loads(path.read_text(encoding="utf-8"))

    if int(raw["season"]) != int(season) or int(raw["week"]) != int(week):
        raise ValueError(f"season/week mismatch in {path}")
    if raw.get("freeze_type") != "SLY_FRIDAY_FREEZE_INPUT":
        raise ValueError(f"unexpected freeze_type in {path}")

    games = _validate_games(
        SlyGame(
            game=str(row["game"]),
            away=str(row["away"]),
            home=str(row["home"]),
            sly_pick_display=str(row["sly_pick_display"]),
            sly_home_spread=float(row["sly_home_spread"]),
            game_time_et=str(row["game_time_et"]),
        )
        for row in raw["games"]
    )

    return SlyFreeze(
        season=int(raw["season"]),
        week=int(raw["week"]),
        freeze_type=str(raw["freeze_type"]),
        freeze_date_local=str(raw["freeze_date_local"]),
        games=games,
        excluded_or_missing=tuple(raw.get("excluded_or_missing", [])),
        source_path=str(path),
    )
