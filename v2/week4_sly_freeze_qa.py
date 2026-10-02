"""Deterministic audit of the user-supplied official Week 4 Sly sheet."""
from __future__ import annotations

from sly_freeze import load_sly_freeze


EXPECTED = {
    "ARI @ NYG": ("ARI", "NYG", 2.5, "SUN 1:00PM", "ARI -2.5"),
    "ATL @ NO": ("ATL", "NO", -2.5, "MON 8:15PM", "ATL +2.5"),
    "TEN @ BAL": ("TEN", "BAL", -11.5, "SUN 1:00PM", "BAL -11.5"),
    "NE @ BUF": ("NE", "BUF", -7.0, "SUN 1:00PM", "BUF -7"),
    "DET @ CAR": ("DET", "CAR", 3.5, "SUN 8:20PM", "DET -3.5"),
    "NYJ @ CHI": ("NYJ", "CHI", -3.5, "SUN 1:00PM", "CHI -3.5"),
    "JAX @ CIN": ("JAX", "CIN", -2.5, "SUN 1:00PM", "CIN -2.5"),
    "DAL @ HOU": ("DAL", "HOU", -3.0, "SUN 1:00PM", "DAL +3"),
    "DEN @ SF": ("DEN", "SF", -3.0, "SUN 4:25PM", "DEN +3"),
    "GB @ TB": ("GB", "TB", 3.5, "SUN 1:00PM", "GB -3.5"),
    "IND @ WAS": ("IND", "WAS", 3.5, "SUN 9:30AM", "IND -3.5"),
    "KC @ LV": ("KC", "LV", 4.5, "SUN 4:25PM", "KC -4.5"),
    "LAC @ SEA": ("LAC", "SEA", -7.0, "SUN 4:25PM", "LAC +7"),
    "LAR @ PHI": ("LAR", "PHI", 3.5, "SUN 1:00PM", "LAR -3.5"),
    "MIA @ MIN": ("MIA", "MIN", -10.5, "SUN 4:05PM", "MIA +10.5"),
}


def main() -> None:
    freeze = load_sly_freeze(2026, 4)
    assert freeze.freeze_date_local == "2026-10-02"
    assert len(freeze.games) == 15, len(freeze.games)

    actual = {
        g.game: (g.away, g.home, g.sly_home_spread, g.game_time_et, g.sly_pick_display)
        for g in freeze.games
    }
    assert actual == EXPECTED, f"Week 4 Sly freeze drifted:\nactual={actual}\nexpected={EXPECTED}"

    assert len(freeze.excluded_or_missing) == 1
    excluded = freeze.excluded_or_missing[0]
    assert excluded.get("game") == "PIT @ CLE"
    assert "blank" in str(excluded.get("reason", "")).lower()
    assert "PIT @ CLE" not in actual

    print("Week 4 Sly freeze QA passed: 15 exact games + PIT @ CLE excluded")


if __name__ == "__main__":
    main()
