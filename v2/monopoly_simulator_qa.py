"""Deterministic QA for the V2-0009 Monopoly state-transition engine."""
from __future__ import annotations

from monopoly_simulator import (
    Bet,
    GameProbability,
    RegularSeasonRules,
    settle_week,
    simulate_household_week,
    validate_bets,
)


RULES = RegularSeasonRules(
    minimum_games=4,
    minimum_wager=100,
    wager_increment=100,
    cover_multiplier=1.0,
    loss_multiplier=-1.0,
    push_multiplier=0.0,
)


def expect_error(fn, text: str) -> None:
    try:
        fn()
    except Exception:
        return
    raise AssertionError(text)


def main() -> None:
    four = [
        Bet("g1", "home", 100),
        Bet("g2", "away", 100),
        Bet("g3", "home", 100),
        Bet("g4", "away", 100),
    ]
    validate_bets(10000, four, RULES)

    expect_error(lambda: validate_bets(10000, four[:3], RULES), "3-game slate must fail")
    expect_error(
        lambda: validate_bets(10000, [Bet("g1", "home", 150), *four[1:]], RULES),
        "non-$100 increment must fail",
    )
    expect_error(
        lambda: validate_bets(300, four, RULES),
        "outlay above balance must fail",
    )

    result = settle_week(
        10000,
        four,
        {"g1": "home_cover", "g2": "home_cover", "g3": "push", "g4": "home_loss"},
        RULES,
    )
    # g1 home wins, g2 away loses, g3 pushes, g4 away wins -> +100 overall.
    assert result.net_change == 100, result
    assert result.ending_balance == 10100, result
    assert (result.wins, result.losses, result.pushes) == (2, 1, 1), result

    probs = {
        gid: GameProbability(gid, 0.5, 0.0, 0.5)
        for gid in ["g1", "g2", "g3", "g4"]
    }
    c_bets = [Bet(gid, "home", 100) for gid in probs]
    a_bets = [Bet(gid, "away", 100) for gid in probs]
    sim = simulate_household_week(
        {"Catherine": 10000, "Amanda": 10000},
        {"Catherine": c_bets, "Amanda": a_bets},
        probs,
        RULES,
        simulations=2000,
        seed=716,
    )
    # With exact opposite sides and no pushes, every $100 gain by one entry is a
    # $100 loss by the other. Household ending balance must therefore be constant.
    assert sim["household"]["mean"] == 20000.0, sim
    assert sim["household"]["p05"] == 20000.0, sim
    assert sim["household"]["p95"] == 20000.0, sim

    print("Monopoly simulator QA passed: rule validation, settlement, and shared-game correlation.")


if __name__ == "__main__":
    main()
