"""Deterministic QA for V2-0009 benchmark strategies."""
from __future__ import annotations

from benchmark_strategies import (
    build_household_benchmarks,
    diversified_pair,
    evaluate_benchmarks,
    fractional_kelly,
    portfolio_overlap,
    ranked_candidates,
)
from monopoly_simulator import GameProbability, RegularSeasonRules, validate_bets


RULES = RegularSeasonRules(
    minimum_games=4,
    minimum_wager=100,
    wager_increment=100,
    cover_multiplier=1.0,
    loss_multiplier=-1.0,
    push_multiplier=0.0,
)


def make_slate() -> dict[str, GameProbability]:
    # Eight games with descending home-edge strength. No pushes needed for allocation QA.
    probs = {}
    edges = [0.20, 0.16, 0.12, 0.08, 0.06, 0.04, 0.02, 0.00]
    for i, edge in enumerate(edges, start=1):
        p_home = 0.5 + edge / 2
        p_loss = 0.5 - edge / 2
        probs[f"g{i}"] = GameProbability(f"g{i}", p_home, 0.0, p_loss)
    return probs


def main() -> None:
    probs = make_slate()
    balances = {"Catherine": 11400, "Amanda": 10300}

    ranked = ranked_candidates(probs)
    assert [x.game_id for x in ranked[:4]] == ["g1", "g2", "g3", "g4"]
    assert all(x.side == "home" for x in ranked)

    portfolios = build_household_benchmarks(balances, probs, RULES)
    names = [p.name for p in portfolios]
    expected = {
        "minimum_4x100",
        "equal_top4_30pct",
        "flat_20pct_positive",
        "flat_30pct_positive",
        "flat_40pct_positive",
        "fractional_kelly_quarter",
        "diversified_pair_30pct",
        "identical_top4_30pct",
    }
    assert set(names) == expected, names

    for portfolio in portfolios:
        for entry, bets in portfolio.bets_by_entry.items():
            validate_bets(balances[entry], bets, RULES)
            assert all(b.amount % 100 == 0 for b in bets)
            assert sum(b.amount for b in bets) <= balances[entry]

    minp = next(p for p in portfolios if p.name == "minimum_4x100")
    assert sum(b.amount for b in minp.bets_by_entry["Catherine"]) == 400
    assert sum(b.amount for b in minp.bets_by_entry["Amanda"]) == 400

    identical = next(p for p in portfolios if p.name == "identical_top4_30pct")
    ident_overlap = portfolio_overlap(identical.bets_by_entry)
    assert ident_overlap["game_overlap_share"] == 1.0, ident_overlap
    assert ident_overlap["same_side_share"] == 1.0, ident_overlap

    diversified = diversified_pair(balances, probs, RULES, 0.30)
    div_overlap = portfolio_overlap(diversified)
    assert div_overlap["game_overlap_share"] == 0.0, div_overlap
    assert div_overlap["same_side_share"] == 0.0, div_overlap

    kelly = fractional_kelly(11400, probs, RULES, 0.25, 0.50)
    validate_bets(11400, kelly, RULES)
    assert sum(b.amount for b in kelly) <= 5700

    # Same outcome seed for every benchmark makes comparisons reproducible.
    reports = evaluate_benchmarks(balances, probs, RULES, simulations=3000, seed=716)
    assert len(reports) == len(expected)
    by_name = {r["strategy"]: r for r in reports}
    assert by_name["minimum_4x100"]["household_outlay"] == 800
    assert by_name["identical_top4_30pct"]["overlap"]["same_side_share"] == 1.0
    assert by_name["diversified_pair_30pct"]["overlap"]["game_overlap_share"] == 0.0
    for report in reports:
        hh = report["household"]
        assert hh["p05"] <= hh["p50"] <= hh["p95"]
        assert report["starting_household_balance"] == 21700

    print("Benchmark strategy QA passed: controls, wager validity, overlap, Kelly cap, and reproducible simulation.")


if __name__ == "__main__":
    main()
