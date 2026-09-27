"""Core state-transition engine for V2-0009 Monopoly optimization.

This module intentionally contains no NFL prediction logic. It consumes already-frozen
home-side cover/push/loss probabilities and applies contest rules to bankroll states.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, Mapping, Sequence
import json
import math
import random
from pathlib import Path


@dataclass(frozen=True)
class GameProbability:
    game_id: str
    p_home_cover: float
    p_push: float
    p_home_loss: float

    def validate(self) -> None:
        vals = (self.p_home_cover, self.p_push, self.p_home_loss)
        if any((not math.isfinite(v) or v < 0 or v > 1) for v in vals):
            raise ValueError(f"invalid probabilities for {self.game_id}: {vals}")
        if abs(sum(vals) - 1.0) > 1e-9:
            raise ValueError(f"probabilities must sum to 1 for {self.game_id}: {vals}")


@dataclass(frozen=True)
class Bet:
    game_id: str
    side: str  # 'home' or 'away'
    amount: int

    def validate(self) -> None:
        if self.side not in {"home", "away"}:
            raise ValueError(f"invalid side for {self.game_id}: {self.side}")
        if not isinstance(self.amount, int):
            raise ValueError("wager amount must be an integer number of Monopoly dollars")


@dataclass(frozen=True)
class RegularSeasonRules:
    minimum_games: int
    minimum_wager: int
    wager_increment: int
    cover_multiplier: float
    loss_multiplier: float
    push_multiplier: float


@dataclass(frozen=True)
class EntryWeekResult:
    starting_balance: int
    ending_balance: int
    net_change: int
    total_outlay: int
    wins: int
    losses: int
    pushes: int


def load_regular_rules(contract_path: str | Path) -> RegularSeasonRules:
    data = json.loads(Path(contract_path).read_text(encoding="utf-8"))
    r = data["weekly_regular_season"]
    return RegularSeasonRules(
        minimum_games=int(r["minimum_games_per_entry"]),
        minimum_wager=int(r["minimum_wager_per_game"]),
        wager_increment=int(r["wager_increment"]),
        cover_multiplier=float(r["cover_net_multiplier"]),
        loss_multiplier=float(r["loss_net_multiplier"]),
        push_multiplier=float(r["push_net_multiplier"]),
    )


def validate_bets(balance: int, bets: Sequence[Bet], rules: RegularSeasonRules) -> None:
    if balance < 0:
        raise ValueError("balance cannot be negative")
    if len(bets) < rules.minimum_games:
        raise ValueError(f"requires at least {rules.minimum_games} games")
    game_ids = [b.game_id for b in bets]
    if len(set(game_ids)) != len(game_ids):
        raise ValueError("an entry may have at most one position per game")

    outlay = 0
    for bet in bets:
        bet.validate()
        if bet.amount < rules.minimum_wager:
            raise ValueError(f"wager below minimum on {bet.game_id}")
        if bet.amount % rules.wager_increment != 0:
            raise ValueError(f"wager must be in ${rules.wager_increment} increments")
        outlay += bet.amount

    if outlay > balance:
        raise ValueError("total wagers cannot exceed current balance")


def _bet_outcome(home_outcome: str, side: str) -> str:
    if home_outcome == "push":
        return "push"
    if side == "home":
        return "cover" if home_outcome == "home_cover" else "loss"
    return "loss" if home_outcome == "home_cover" else "cover"


def settle_week(
    balance: int,
    bets: Sequence[Bet],
    home_outcomes: Mapping[str, str],
    rules: RegularSeasonRules,
) -> EntryWeekResult:
    validate_bets(balance, bets, rules)
    wins = losses = pushes = 0
    net = 0.0
    for bet in bets:
        if bet.game_id not in home_outcomes:
            raise KeyError(f"missing outcome for {bet.game_id}")
        outcome = _bet_outcome(home_outcomes[bet.game_id], bet.side)
        if outcome == "cover":
            wins += 1
            net += bet.amount * rules.cover_multiplier
        elif outcome == "loss":
            losses += 1
            net += bet.amount * rules.loss_multiplier
        else:
            pushes += 1
            net += bet.amount * rules.push_multiplier

    ending = int(round(balance + net))
    if ending < 0:
        raise AssertionError("validated wagers should never produce a negative balance")
    return EntryWeekResult(
        starting_balance=balance,
        ending_balance=ending,
        net_change=int(round(net)),
        total_outlay=sum(b.amount for b in bets),
        wins=wins,
        losses=losses,
        pushes=pushes,
    )


def sample_home_outcome(prob: GameProbability, rng: random.Random) -> str:
    prob.validate()
    u = rng.random()
    if u < prob.p_home_cover:
        return "home_cover"
    if u < prob.p_home_cover + prob.p_push:
        return "push"
    return "home_loss"


def simulate_household_week(
    balances: Mapping[str, int],
    bets_by_entry: Mapping[str, Sequence[Bet]],
    game_probabilities: Mapping[str, GameProbability],
    rules: RegularSeasonRules,
    simulations: int = 10000,
    seed: int = 716,
) -> Dict[str, object]:
    """Simulate one week with shared NFL outcomes across household entries.

    Catherine and Amanda therefore cannot receive independent outcomes on the same game.
    Opposite-side positions are automatically anti-correlated except on pushes.
    """
    if simulations <= 0:
        raise ValueError("simulations must be positive")
    for entry, bets in bets_by_entry.items():
        if entry not in balances:
            raise KeyError(f"missing balance for {entry}")
        validate_bets(int(balances[entry]), bets, rules)
        for bet in bets:
            if bet.game_id not in game_probabilities:
                raise KeyError(f"missing probability for {bet.game_id}")
            game_probabilities[bet.game_id].validate()

    rng = random.Random(seed)
    ending_by_entry: Dict[str, list[int]] = {e: [] for e in bets_by_entry}
    household_endings: list[int] = []
    any_entry_increase = 0
    both_entries_increase = 0

    used_games = sorted({b.game_id for bets in bets_by_entry.values() for b in bets})
    entries = list(bets_by_entry)
    for _ in range(simulations):
        outcomes = {
            gid: sample_home_outcome(game_probabilities[gid], rng)
            for gid in used_games
        }
        household_total = 0
        entry_increased: list[bool] = []
        for entry, bets in bets_by_entry.items():
            result = settle_week(int(balances[entry]), bets, outcomes, rules)
            ending_by_entry[entry].append(result.ending_balance)
            household_total += result.ending_balance
            entry_increased.append(result.ending_balance > int(balances[entry]))
        household_endings.append(household_total)
        if any(entry_increased):
            any_entry_increase += 1
        if len(entries) == 2 and all(entry_increased):
            both_entries_increase += 1

    def summary(values: Iterable[int], starting_value: int) -> Dict[str, float]:
        vals = sorted(values)
        n = len(vals)
        mean = sum(vals) / n
        return {
            "mean": mean,
            "p05": float(vals[max(0, int(0.05 * n) - 1)]),
            "p50": float(vals[int(0.50 * (n - 1))]),
            "p95": float(vals[min(n - 1, int(0.95 * n))]),
            "p_increase": sum(v > starting_value for v in vals) / n,
            "p_decrease": sum(v < starting_value for v in vals) / n,
            "p_unchanged": sum(v == starting_value for v in vals) / n,
            "p_zero": sum(v == 0 for v in vals) / n,
        }

    household_start = sum(int(balances[e]) for e in bets_by_entry)
    return {
        "simulations": simulations,
        "seed": seed,
        "entries": {
            entry: summary(vals, int(balances[entry]))
            for entry, vals in ending_by_entry.items()
        },
        "household": summary(household_endings, household_start),
        "p_any_entry_increase": any_entry_increase / simulations,
        "p_both_entries_increase": (
            both_entries_increase / simulations if len(entries) == 2 else None
        ),
        "shared_game_outcomes": True,
    }
