"""Replay audited Weeks 1-2 through the V2 Monopoly bankroll engine.

The commissioner standings remain authoritative for official balances. This test verifies
that wager-ledger math reproduces the audited ledger exactly and that known commissioner
reconciliation differences remain explicit rather than being silently rewritten.
"""
from __future__ import annotations

import json
from pathlib import Path

from monopoly_simulator import Bet, load_regular_rules, settle_week


ROOT = Path(__file__).resolve().parent


def main() -> None:
    rules = load_regular_rules(ROOT / "monopoly_contract.json")
    fixture = json.loads((ROOT / "historical_replay_wk1_wk2.json").read_text(encoding="utf-8"))

    observed_differences = []
    for week in fixture["weeks"]:
        home_outcomes = week["home_outcomes"]
        for entry, state in week["entries"].items():
            bets = [Bet(game_id=g, side=s, amount=int(a)) for g, s, a in state["bets"]]
            result = settle_week(
                int(state["official_start"]),
                bets,
                home_outcomes,
                rules,
            )
            expected = int(state["ledger_expected_end"])
            official = int(state["commissioner_end"])
            assert result.ending_balance == expected, (
                week["week"], entry, result.ending_balance, expected
            )
            observed_differences.append({
                "week": week["week"],
                "entry": entry,
                "ledger_expected_end": expected,
                "commissioner_end": official,
                "difference": official - expected,
            })

    expected_differences = {
        (1, "Catherine"): 0,
        (1, "Amanda"): 500,
        (2, "Catherine"): 0,
        (2, "Amanda"): 100,
    }
    for row in observed_differences:
        key = (row["week"], row["entry"])
        assert row["difference"] == expected_differences[key], (row, expected_differences[key])

    print("Historical replay QA passed.")
    for row in observed_differences:
        print(
            f"Week {row['week']} {row['entry']}: ledger={row['ledger_expected_end']} "
            f"commissioner={row['commissioner_end']} diff={row['difference']:+d}"
        )


if __name__ == "__main__":
    main()
