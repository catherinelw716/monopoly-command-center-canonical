"""Benchmark portfolio policies for V2-0009 Monopoly optimization.

These policies are intentionally simple. They are controls that the eventual joint
Catherine/Amanda optimizer must beat; they are not production recommendations.

All strategy selection consumes already-frozen P(cover/push/loss). Nothing in this
module changes NFL probabilities based on standings or bankroll.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, Mapping, Sequence
import math

from monopoly_simulator import Bet, GameProbability, RegularSeasonRules, simulate_household_week


@dataclass(frozen=True)
class Candidate:
    game_id: str
    side: str
    edge_per_dollar: float
    p_win: float
    p_push: float
    p_loss: float


@dataclass(frozen=True)
class BenchmarkPortfolio:
    name: str
    bets_by_entry: Dict[str, tuple[Bet, ...]]
    metadata: Dict[str, object]


def _round_down(amount: float, increment: int) -> int:
    if increment <= 0:
        raise ValueError("increment must be positive")
    return int(math.floor(amount / increment) * increment)


def ranked_candidates(game_probabilities: Mapping[str, GameProbability]) -> list[Candidate]:
    """Return the positive-EV side of every game, strongest first.

    At even-money Monopoly settlement, expected net per dollar is P(win)-P(loss).
    Pushes contribute zero. If both sides are exactly equal, home is used only as a
    deterministic tie-break; the edge remains zero.
    """
    out: list[Candidate] = []
    for gid, gp in game_probabilities.items():
        gp.validate()
        home_edge = gp.p_home_cover - gp.p_home_loss
        if home_edge >= 0:
            out.append(Candidate(gid, "home", home_edge, gp.p_home_cover, gp.p_push, gp.p_home_loss))
        else:
            out.append(Candidate(gid, "away", -home_edge, gp.p_home_loss, gp.p_push, gp.p_home_cover))
    return sorted(out, key=lambda c: (-c.edge_per_dollar, c.game_id))


def _target_outlay(balance: int, fraction: float, rules: RegularSeasonRules) -> int:
    if not 0 <= fraction <= 1:
        raise ValueError("deployment fraction must be between 0 and 1")
    minimum_total = rules.minimum_games * rules.minimum_wager
    if balance < minimum_total:
        raise ValueError("balance is too small to satisfy the regular-season minimum")
    target = _round_down(balance * fraction, rules.wager_increment)
    target = max(minimum_total, target)
    return min(balance, target)


def _even_allocate(
    balance: int,
    candidates: Sequence[Candidate],
    target_outlay: int,
    rules: RegularSeasonRules,
    desired_games: int | None = None,
) -> tuple[Bet, ...]:
    if len(candidates) < rules.minimum_games:
        raise ValueError("slate has fewer games than the contest minimum")
    max_affordable_games = target_outlay // rules.minimum_wager
    if max_affordable_games < rules.minimum_games:
        raise ValueError("target outlay cannot satisfy minimum games")
    if desired_games is None:
        n = min(len(candidates), max_affordable_games)
    else:
        n = min(len(candidates), max(desired_games, rules.minimum_games), max_affordable_games)
    selected = list(candidates[:n])

    base = _round_down(target_outlay / n, rules.wager_increment)
    base = max(base, rules.minimum_wager)
    amounts = [base] * n
    used = base * n
    remaining = target_outlay - used
    i = 0
    while remaining >= rules.wager_increment:
        amounts[i % n] += rules.wager_increment
        remaining -= rules.wager_increment
        i += 1

    # Rounding can make target_outlay unreachable exactly; never exceed it or balance.
    if sum(amounts) > target_outlay or sum(amounts) > balance:
        raise AssertionError("allocation exceeded target/balance")
    return tuple(Bet(c.game_id, c.side, int(a)) for c, a in zip(selected, amounts))


def minimum_top4(
    balance: int,
    game_probabilities: Mapping[str, GameProbability],
    rules: RegularSeasonRules,
) -> tuple[Bet, ...]:
    candidates = ranked_candidates(game_probabilities)
    return tuple(
        Bet(c.game_id, c.side, rules.minimum_wager)
        for c in candidates[: rules.minimum_games]
    )


def equal_top4(
    balance: int,
    game_probabilities: Mapping[str, GameProbability],
    rules: RegularSeasonRules,
    deployment_fraction: float = 0.30,
) -> tuple[Bet, ...]:
    candidates = ranked_candidates(game_probabilities)
    target = _target_outlay(balance, deployment_fraction, rules)
    return _even_allocate(balance, candidates, target, rules, desired_games=rules.minimum_games)


def flat_all_positive(
    balance: int,
    game_probabilities: Mapping[str, GameProbability],
    rules: RegularSeasonRules,
    deployment_fraction: float,
) -> tuple[Bet, ...]:
    """Spread a fixed bankroll fraction across positive-edge games.

    If fewer than four games have strictly positive model edge, fill the remaining
    mandatory positions with the next-best games. If the target deployment cannot
    support every positive-edge game at the minimum wager, retain the strongest ones.
    """
    ranked = ranked_candidates(game_probabilities)
    positive = [c for c in ranked if c.edge_per_dollar > 0]
    n_desired = max(rules.minimum_games, len(positive))
    target = _target_outlay(balance, deployment_fraction, rules)
    return _even_allocate(balance, ranked, target, rules, desired_games=n_desired)


def fractional_kelly(
    balance: int,
    game_probabilities: Mapping[str, GameProbability],
    rules: RegularSeasonRules,
    kelly_fraction: float = 0.25,
    max_total_fraction: float = 0.50,
) -> tuple[Bet, ...]:
    """Conservative Kelly-style benchmark for +1/-1/0 Monopoly payoffs.

    For an even-money bet with possible pushes, unconstrained Kelly fraction is
    approximated by P(win)-P(loss). We use only a fraction of that signal, impose
    the contest minimum, and cap aggregate deployment. This is a benchmark rather
    than an assertion that Kelly is optimal for the tournament objective.
    """
    if not 0 < kelly_fraction <= 1:
        raise ValueError("kelly_fraction must be in (0,1]")
    ranked = ranked_candidates(game_probabilities)
    if len(ranked) < rules.minimum_games:
        raise ValueError("slate has fewer games than the contest minimum")

    bets: list[Bet] = []
    for c in ranked:
        raw = balance * kelly_fraction * max(0.0, c.edge_per_dollar)
        amount = _round_down(raw, rules.wager_increment)
        if amount >= rules.minimum_wager:
            bets.append(Bet(c.game_id, c.side, amount))

    selected_ids = {b.game_id for b in bets}
    for c in ranked:
        if len(bets) >= rules.minimum_games:
            break
        if c.game_id not in selected_ids:
            bets.append(Bet(c.game_id, c.side, rules.minimum_wager))
            selected_ids.add(c.game_id)

    max_total = _target_outlay(balance, max_total_fraction, rules)
    # If raw Kelly exceeds the cap, shave weakest positions first in $100 increments.
    edge_by_game = {c.game_id: c.edge_per_dollar for c in ranked}
    while sum(b.amount for b in bets) > max_total:
        reducible = [b for b in bets if b.amount > rules.minimum_wager]
        if not reducible:
            break
        weakest = min(reducible, key=lambda b: (edge_by_game[b.game_id], b.game_id))
        idx = bets.index(weakest)
        bets[idx] = Bet(weakest.game_id, weakest.side, weakest.amount - rules.wager_increment)

    bets = sorted(bets, key=lambda b: (-edge_by_game[b.game_id], b.game_id))
    return tuple(bets)


def diversified_pair(
    balances: Mapping[str, int],
    game_probabilities: Mapping[str, GameProbability],
    rules: RegularSeasonRules,
    deployment_fraction: float = 0.30,
    entries: tuple[str, str] = ("Catherine", "Amanda"),
) -> Dict[str, tuple[Bet, ...]]:
    """Deliberately low-overlap control portfolio.

    Strongest games are alternated across entries. Each entry must still receive at
    least four games; overlap is introduced only if the slate is too small.
    """
    a, b = entries
    ranked = ranked_candidates(game_probabilities)
    if len(ranked) < rules.minimum_games:
        raise ValueError("slate has fewer games than the contest minimum")

    a_pool = ranked[0::2]
    b_pool = ranked[1::2]
    if len(a_pool) < rules.minimum_games:
        a_pool = ranked
    if len(b_pool) < rules.minimum_games:
        b_pool = ranked[1:] + ranked[:1]

    result: Dict[str, tuple[Bet, ...]] = {}
    for entry, pool in ((a, a_pool), (b, b_pool)):
        target = _target_outlay(int(balances[entry]), deployment_fraction, rules)
        result[entry] = _even_allocate(
            int(balances[entry]), pool, target, rules, desired_games=rules.minimum_games
        )
    return result


def portfolio_overlap(bets_by_entry: Mapping[str, Sequence[Bet]]) -> Dict[str, float]:
    """Household exposure overlap diagnostics.

    game_overlap_share matches the intuitive Command Center concept: the fraction of
    combined wager dollars sitting on games both household entries play. same_side_share
    is the fraction sitting on games where both also chose the same side.
    """
    entries = list(bets_by_entry)
    if len(entries) != 2:
        raise ValueError("overlap diagnostic currently expects exactly two entries")
    first, second = entries
    a = {x.game_id: x for x in bets_by_entry[first]}
    b = {x.game_id: x for x in bets_by_entry[second]}
    combined = sum(x.amount for x in a.values()) + sum(x.amount for x in b.values())
    if combined <= 0:
        return {"game_overlap_share": 0.0, "same_side_share": 0.0}

    shared_games = set(a) & set(b)
    shared_exposure = sum(a[g].amount + b[g].amount for g in shared_games)
    same_side = sum(
        a[g].amount + b[g].amount
        for g in shared_games
        if a[g].side == b[g].side
    )
    return {
        "game_overlap_share": shared_exposure / combined,
        "same_side_share": same_side / combined,
    }


def build_household_benchmarks(
    balances: Mapping[str, int],
    game_probabilities: Mapping[str, GameProbability],
    rules: RegularSeasonRules,
    entries: tuple[str, str] = ("Catherine", "Amanda"),
) -> list[BenchmarkPortfolio]:
    """Create the preregistered simple controls for the joint optimizer."""
    c, a = entries
    for entry in entries:
        if entry not in balances:
            raise KeyError(f"missing balance for {entry}")

    def independent(name: str, fn) -> BenchmarkPortfolio:
        bets = {entry: tuple(fn(int(balances[entry]))) for entry in entries}
        return BenchmarkPortfolio(name, bets, {"household_policy": "independent"})

    portfolios: list[BenchmarkPortfolio] = []
    portfolios.append(independent(
        "minimum_4x100",
        lambda bal: minimum_top4(bal, game_probabilities, rules),
    ))
    portfolios.append(independent(
        "equal_top4_30pct",
        lambda bal: equal_top4(bal, game_probabilities, rules, 0.30),
    ))
    for frac in (0.20, 0.30, 0.40):
        label = int(frac * 100)
        portfolios.append(independent(
            f"flat_{label}pct_positive",
            lambda bal, frac=frac: flat_all_positive(bal, game_probabilities, rules, frac),
        ))
    portfolios.append(independent(
        "fractional_kelly_quarter",
        lambda bal: fractional_kelly(bal, game_probabilities, rules, 0.25, 0.50),
    ))

    diversified = diversified_pair(balances, game_probabilities, rules, 0.30, entries)
    portfolios.append(BenchmarkPortfolio(
        "diversified_pair_30pct",
        diversified,
        {"household_policy": "deliberately_diversified"},
    ))

    # Explicit identical household control. With a common probability model this is
    # intentionally close to independent top-4 selection; keeping it named makes the
    # household-correlation benchmark auditable.
    c_bets = equal_top4(int(balances[c]), game_probabilities, rules, 0.30)
    chosen = [(b.game_id, b.side) for b in c_bets]
    ranked_map = {x.game_id: x for x in ranked_candidates(game_probabilities)}
    target_a = _target_outlay(int(balances[a]), 0.30, rules)
    same_candidates = [ranked_map[gid] for gid, _ in chosen]
    a_bets = _even_allocate(int(balances[a]), same_candidates, target_a, rules, desired_games=len(chosen))
    portfolios.append(BenchmarkPortfolio(
        "identical_top4_30pct",
        {c: tuple(c_bets), a: tuple(a_bets)},
        {"household_policy": "forced_identical_games"},
    ))
    return portfolios


def evaluate_benchmarks(
    balances: Mapping[str, int],
    game_probabilities: Mapping[str, GameProbability],
    rules: RegularSeasonRules,
    simulations: int = 20000,
    seed: int = 716,
) -> list[Dict[str, object]]:
    """Simulate every simple benchmark under the same random seed/outcome process."""
    results: list[Dict[str, object]] = []
    starting_household = sum(int(v) for v in balances.values())
    for portfolio in build_household_benchmarks(balances, game_probabilities, rules):
        sim = simulate_household_week(
            balances,
            portfolio.bets_by_entry,
            game_probabilities,
            rules,
            simulations=simulations,
            seed=seed,
        )
        overlap = portfolio_overlap(portfolio.bets_by_entry)
        outlays = {
            entry: sum(b.amount for b in bets)
            for entry, bets in portfolio.bets_by_entry.items()
        }
        results.append({
            "strategy": portfolio.name,
            "metadata": portfolio.metadata,
            "outlay_by_entry": outlays,
            "household_outlay": sum(outlays.values()),
            "overlap": overlap,
            "household": sim["household"],
            "entries": sim["entries"],
            "starting_household_balance": starting_household,
        })
    return results
