from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MARKET = ROOT / "v2/season_2026/week_04_market_history_2026-10-02_1433ET.json"
SLY = ROOT / "v2/season_2026/week_04_sly_freeze.json"


def main() -> None:
    market = json.loads(MARKET.read_text(encoding="utf-8"))
    sly = json.loads(SLY.read_text(encoding="utf-8"))

    assert market["season"] == 2026
    assert market["week"] == 4
    assert market["snapshot_type"] == "FRIDAY_MARKET_HISTORY"
    assert market["diff_definition"] == "current_home_spread - sly_home_spread"

    sly_by_game = {g["game"]: g for g in sly["games"]}
    market_by_game = {g["game_id"]: g for g in market["games"]}

    assert len(sly_by_game) == 15, len(sly_by_game)
    assert len(market_by_game) == 15, len(market_by_game)
    assert set(market_by_game) == set(sly_by_game)

    required = {
        "open_home_spread",
        "sly_home_spread",
        "vi_current_home_spread",
        "action_current_home_spread",
        "vi_diff_vs_sly",
        "action_diff_vs_sly",
        "home_spread_move_open_to_vi_current",
        "open_total",
        "vi_current_total",
        "key_number_event",
        "market_disagreement",
    }

    for game_id, row in market_by_game.items():
        missing = required - set(row)
        assert not missing, f"{game_id}: missing {sorted(missing)}"
        assert row["sly_home_spread"] == sly_by_game[game_id]["sly_home_spread"], game_id

        assert abs(
            row["vi_diff_vs_sly"]
            - (row["vi_current_home_spread"] - row["sly_home_spread"])
        ) < 1e-9, f"{game_id}: VI DIFF mismatch"
        assert abs(
            row["action_diff_vs_sly"]
            - (row["action_current_home_spread"] - row["sly_home_spread"])
        ) < 1e-9, f"{game_id}: Action DIFF mismatch"
        assert abs(
            row["home_spread_move_open_to_vi_current"]
            - (row["vi_current_home_spread"] - row["open_home_spread"])
        ) < 1e-9, f"{game_id}: open-to-current movement mismatch"

        for field in (
            "open_home_spread",
            "sly_home_spread",
            "vi_current_home_spread",
            "action_current_home_spread",
            "open_total",
            "vi_current_total",
        ):
            assert row[field] is not None, f"{game_id}: {field} unexpectedly null"

    completeness = market["completeness"]
    for key in (
        "eligible_sly_games",
        "games_with_open_spread",
        "games_with_sly_spread",
        "games_with_vi_current_spread",
        "games_with_action_current_spread",
        "games_with_open_total",
        "games_with_vi_current_total",
        "games_with_explicit_market_disagreement_flag",
    ):
        assert completeness[key] == 15, (key, completeness[key])

    assert completeness["excluded"] == [
        {
            "game_id": "PIT @ CLE",
            "reason": "No Sly Friday spread; Thursday game excluded from Week 4 Sly evaluation.",
        }
    ]

    # High-risk movement sanity checks: these are intentionally explicit because
    # sign/orientation errors would reverse downstream model interpretation.
    assert market_by_game["ARI @ NYG"]["open_home_spread"] == -7.0
    assert market_by_game["ARI @ NYG"]["vi_current_home_spread"] == 2.5
    assert market_by_game["IND @ WAS"]["open_home_spread"] == -1.5
    assert market_by_game["IND @ WAS"]["vi_current_home_spread"] == 4.5
    assert market_by_game["LAC @ SEA"]["open_home_spread"] == -3.0
    assert market_by_game["LAC @ SEA"]["vi_current_home_spread"] == -7.0

    print("Week 4 market-history QA passed: 15/15 Sly games have opening/current/total records with source-specific DIFFs.")


if __name__ == "__main__":
    main()
