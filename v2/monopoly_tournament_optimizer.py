"""V2-0009 field-scenario ensemble, benchmark evaluation, and joint optimizer.

This module is deliberately downstream of the frozen NFL probability layer. It never
changes P(cover/push/loss) from standings, bankroll, or desired variance.

The opponent field model is a scenario ensemble, not a claim that we know individual
opponent policies. Known Week-2 distribution anchors are preserved; unobserved parts
of the field are interpolated and explicitly stress-testable.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, Mapping, Sequence
import hashlib
import json
import math

import numpy as np

from monopoly_simulator import Bet, GameProbability, RegularSeasonRules, validate_bets
from benchmark_strategies import BenchmarkPortfolio, build_household_benchmarks, portfolio_overlap, ranked_candidates

PRIZE_SHARES = np.array([0.56, 0.25, 0.10, 0.02, 0.01], dtype=float)


@dataclass(frozen=True)
class FieldState:
    active_entries: int
    eliminated_entries: int
    median_balance: int
    top10_floor: int
    top5_floor: int
    leader_balance: int
    catherine_balance: int
    catherine_rank: int
    amanda_balance: int
    amanda_rank: int
    lower_tail_floor_assumption: int = 400


@dataclass(frozen=True)
class FieldScenario:
    name: str
    mixture_weight: float
    mean_deployment: float
    deployment_sd: float
    mean_games: float
    games_sd: float
    common_week_sd: float


@dataclass(frozen=True)
class OptimizerConfig:
    simulations: int = 3000
    seed: int = 716
    regular_weeks_after_current: int = 15
    future_household_mean_deployment: float = 0.30
    future_household_deployment_sd: float = 0.10
    future_household_mean_games: float = 5.0
    future_household_games_sd: float = 1.0
    future_household_win_prob: float = 0.50
    playoff_minimum_total: int = 3000
    week18_qualification_minimum: int = 3000


def load_field_state(path: str | Path) -> FieldState:
    d = json.loads(Path(path).read_text(encoding="utf-8"))
    a = d["observed_anchors"]
    h = d["household"]
    assumptions = d.get("explicit_assumptions", {})
    return FieldState(
        active_entries=int(d["active_entries"]),
        eliminated_entries=int(d.get("eliminated_entries", 0)),
        median_balance=int(a["median_balance"]),
        top10_floor=int(a["top10_floor"]),
        top5_floor=int(a["top5_floor"]),
        leader_balance=int(a["leader_balance"]),
        catherine_balance=int(h["Catherine"]["balance"]),
        catherine_rank=int(h["Catherine"]["rank"]),
        amanda_balance=int(h["Amanda"]["balance"]),
        amanda_rank=int(h["Amanda"]["rank"]),
        lower_tail_floor_assumption=int(assumptions.get("lower_tail_floor_assumption", 400)),
    )


def default_field_scenarios() -> tuple[FieldScenario, ...]:
    """Broad policy ensemble. Equal weights avoid fake precision from two observed weeks."""
    return (
        FieldScenario("conservative", 1 / 3, 0.22, 0.08, 4.5, 0.8, 0.025),
        FieldScenario("median", 1 / 3, 0.36, 0.12, 5.5, 1.0, 0.035),
        FieldScenario("aggressive", 1 / 3, 0.52, 0.16, 6.5, 1.3, 0.050),
    )


def _interp_by_rank(anchors: Sequence[tuple[int, float]], n: int) -> np.ndarray:
    xs = np.array([x for x, _ in anchors], dtype=float)
    ys = np.array([y for _, y in anchors], dtype=float)
    ranks = np.arange(1, n + 1, dtype=float)
    return np.interp(ranks, xs, ys)


def synthesize_opponent_balances(state: FieldState, lower_tail_floor: int | None = None) -> np.ndarray:
    """Construct a rank-preserving field envelope from observed distribution anchors.

    This is not a reconstructed commissioner ledger. It is an interpolation used only
    because the canonical handoff preserves aggregate Week-2 anchors rather than every
    opponent balance. Catherine/Amanda ranks are removed from the envelope.
    """
    n = state.active_entries
    if n < 3:
        raise ValueError("field must contain Catherine, Amanda, and at least one opponent")
    floor = int(lower_tail_floor if lower_tail_floor is not None else state.lower_tail_floor_assumption)
    median_rank = (n + 1) // 2
    anchors = sorted({
        1: float(state.leader_balance),
        5: float(state.top5_floor),
        10: float(state.top10_floor),
        state.catherine_rank: float(state.catherine_balance),
        state.amanda_rank: float(state.amanda_balance),
        median_rank: float(state.median_balance),
        n: float(floor),
    }.items())
    full = _interp_by_rank(anchors, n)
    full = np.minimum.accumulate(full)
    keep = np.ones(n, dtype=bool)
    keep[state.catherine_rank - 1] = False
    keep[state.amanda_rank - 1] = False
    return np.rint(full[keep] / 100.0) * 100.0


def _draw_policy_inputs(shape: tuple[int, ...], scenario: FieldScenario, rng: np.random.Generator) -> tuple[np.ndarray, np.ndarray]:
    deployment = np.clip(rng.normal(scenario.mean_deployment, scenario.deployment_sd, size=shape), 0.05, 0.95)
    games = np.rint(rng.normal(scenario.mean_games, scenario.games_sd, size=shape)).astype(int)
    games = np.clip(games, 4, 12)
    return deployment, games


def _regular_week_step(
    balances: np.ndarray,
    scenario: FieldScenario,
    rng: np.random.Generator,
    common_p: np.ndarray | None = None,
) -> np.ndarray:
    shape = balances.shape
    deploy, games = _draw_policy_inputs(shape, scenario, rng)
    if common_p is None:
        p = np.clip(0.5 + rng.normal(0.0, scenario.common_week_sd, size=(shape[0], 1)), 0.35, 0.65)
    else:
        p = np.asarray(common_p, dtype=float)
        if p.ndim == 1:
            p = p[:, None]
    p = np.broadcast_to(p, shape)
    wins = rng.binomial(games, p)
    outlay = balances * deploy
    viable = balances >= 400
    outlay = np.where(viable, np.maximum(400.0, outlay), 0.0)
    outlay = np.minimum(outlay, balances)
    net = outlay * ((2.0 * wins - games) / games)
    next_bal = np.maximum(0.0, balances + net)
    return np.rint(next_bal / 100.0) * 100.0


def _playoff_round_step(
    balances: np.ndarray,
    scenario: FieldScenario,
    games: int,
    minimum_total: int,
    rng: np.random.Generator,
) -> tuple[np.ndarray, np.ndarray]:
    eligible = balances >= minimum_total
    deploy = np.clip(rng.normal(scenario.mean_deployment, scenario.deployment_sd, size=balances.shape), 0.05, 0.95)
    outlay = np.where(eligible, np.maximum(float(minimum_total), balances * deploy), 0.0)
    outlay = np.minimum(outlay, balances)
    p = np.clip(0.5 + rng.normal(0.0, scenario.common_week_sd, size=(balances.shape[0], 1)), 0.35, 0.65)
    p = np.broadcast_to(p, balances.shape)
    wins = rng.binomial(games, p)
    net = outlay * ((2.0 * wins - games) / games)
    next_bal = np.where(eligible, np.maximum(0.0, balances + net), balances)
    return np.rint(next_bal / 100.0) * 100.0, eligible


def simulate_field_paths(
    opponent_balances: np.ndarray,
    scenario: FieldScenario,
    cfg: OptimizerConfig,
    include_current_week: bool = True,
    seed_offset: int = 0,
) -> Dict[str, np.ndarray]:
    rng = np.random.default_rng(cfg.seed + seed_offset)
    trials = cfg.simulations
    balances = np.broadcast_to(opponent_balances[None, :], (trials, len(opponent_balances))).copy()
    weeks = cfg.regular_weeks_after_current + (1 if include_current_week else 0)
    for _ in range(weeks):
        balances = _regular_week_step(balances, scenario, rng)
    qualified = balances >= cfg.week18_qualification_minimum
    ever_failed = ~qualified.copy()
    for games in (6, 4, 2, 1):
        balances, eligible = _playoff_round_step(balances, scenario, games, cfg.playoff_minimum_total, rng)
        ever_failed |= ~eligible
    return {"final_balances": balances, "future_minimum_failure": ever_failed}


def _sample_household_current_week(
    balances: Mapping[str, int],
    bets_by_entry: Mapping[str, Sequence[Bet]],
    game_probabilities: Mapping[str, GameProbability],
    rules: RegularSeasonRules,
    simulations: int,
    seed: int,
) -> Dict[str, np.ndarray]:
    entries = tuple(bets_by_entry)
    if len(entries) != 2:
        raise ValueError("joint optimizer currently expects exactly two household entries")
    for e in entries:
        validate_bets(int(balances[e]), bets_by_entry[e], rules)
    used = sorted({b.game_id for bets in bets_by_entry.values() for b in bets})
    outcome_code: Dict[str, np.ndarray] = {}
    for gid in used:
        gp = game_probabilities[gid]
        gp.validate()
        gid_key = int.from_bytes(hashlib.sha256(gid.encode("utf-8")).digest()[:8], "big")
        rng = np.random.default_rng(seed + (gid_key % 1_000_000_000))
        u = rng.random(simulations)
        outcome_code[gid] = np.where(u < gp.p_home_cover, 1, np.where(u < gp.p_home_cover + gp.p_push, 0, -1))
    endings: Dict[str, np.ndarray] = {}
    for e in entries:
        net = np.zeros(simulations, dtype=float)
        for b in bets_by_entry[e]:
            home = outcome_code[b.game_id]
            signed = home if b.side == "home" else -home
            net += signed * b.amount
        endings[e] = np.rint((int(balances[e]) + net) / 100.0) * 100.0
    return endings


def _simulate_household_continuation(
    current_week_endings: Mapping[str, np.ndarray],
    scenario: FieldScenario,
    cfg: OptimizerConfig,
    seed_offset: int,
) -> Dict[str, object]:
    entries = tuple(current_week_endings)
    balances = np.column_stack([current_week_endings[e] for e in entries]).astype(float)
    rng = np.random.default_rng(cfg.seed + seed_offset)
    cont_scenario = FieldScenario(
        "household_continuation",
        1.0,
        cfg.future_household_mean_deployment,
        cfg.future_household_deployment_sd,
        cfg.future_household_mean_games,
        cfg.future_household_games_sd,
        scenario.common_week_sd,
    )
    for _ in range(cfg.regular_weeks_after_current):
        balances = _regular_week_step(balances, cont_scenario, rng)
    qualified = balances >= cfg.week18_qualification_minimum
    failed = ~qualified.copy()
    for games in (6, 4, 2, 1):
        balances, eligible = _playoff_round_step(balances, cont_scenario, games, cfg.playoff_minimum_total, rng)
        failed |= ~eligible
    return {"entries": entries, "final_balances": balances, "future_minimum_failure": failed}


def _rank_and_prize(household_final: np.ndarray, field_final: np.ndarray, rng: np.random.Generator) -> Dict[str, np.ndarray]:
    trials, entries = household_final.shape
    if entries != 2 or field_final.shape[0] != trials:
        raise ValueError("shape mismatch")
    eps_field = rng.uniform(-0.49, 0.49, size=field_final.shape)
    eps_house = rng.uniform(-0.49, 0.49, size=household_final.shape)
    fj = field_final + eps_field
    hj = household_final + eps_house
    ranks = np.empty_like(hj, dtype=int)
    for j in range(entries):
        ranks[:, j] = 1 + np.sum(fj > hj[:, j, None], axis=1) + (hj[:, 1 - j] > hj[:, j]).astype(int)
    payout = np.zeros_like(hj, dtype=float)
    for pos, share in enumerate(PRIZE_SHARES, start=1):
        payout += (ranks == pos) * share
    return {"ranks": ranks, "payout_share": payout}


def prepare_field_paths(
    field_state: FieldState,
    scenarios: Sequence[FieldScenario],
    cfg: OptimizerConfig,
    lower_tail_floor: int | None = None,
) -> Dict[str, Dict[str, np.ndarray]]:
    opponents = synthesize_opponent_balances(field_state, lower_tail_floor)
    return {
        sc.name: simulate_field_paths(opponents, sc, cfg, include_current_week=True, seed_offset=1000 + i * 100)
        for i, sc in enumerate(scenarios)
    }


def evaluate_portfolio_across_scenarios(
    balances: Mapping[str, int],
    bets_by_entry: Mapping[str, Sequence[Bet]],
    game_probabilities: Mapping[str, GameProbability],
    rules: RegularSeasonRules,
    field_state: FieldState,
    scenarios: Sequence[FieldScenario] | None = None,
    cfg: OptimizerConfig | None = None,
    lower_tail_floor: int | None = None,
    prepared_field_paths: Mapping[str, Mapping[str, np.ndarray]] | None = None,
) -> Dict[str, object]:
    cfg = cfg or OptimizerConfig()
    scenarios = tuple(scenarios or default_field_scenarios())
    if not math.isclose(sum(s.mixture_weight for s in scenarios), 1.0, abs_tol=1e-9):
        raise ValueError("scenario mixture weights must sum to 1")
    opponents = synthesize_opponent_balances(field_state, lower_tail_floor)
    prepared = dict(prepared_field_paths or prepare_field_paths(field_state, scenarios, cfg, lower_tail_floor))
    current_paths = _sample_household_current_week(
        balances, bets_by_entry, game_probabilities, rules, cfg.simulations, cfg.seed + 11
    )
    scenario_metrics: Dict[str, Dict[str, float]] = {}
    weighted = {
        "expected_household_prize_share": 0.0,
        "p_any_cash": 0.0,
        "p_top3": 0.0,
        "p_first": 0.0,
        "p_both_cash": 0.0,
        "future_minimum_failure_risk": 0.0,
    }
    for i, sc in enumerate(scenarios):
        field = prepared[sc.name]
        hh = _simulate_household_continuation(current_paths, sc, cfg, seed_offset=2000 + i * 100)
        final = hh["final_balances"]
        rr = _rank_and_prize(final, field["final_balances"], np.random.default_rng(cfg.seed + 3000 + i))
        ranks = rr["ranks"]
        payout = rr["payout_share"]
        household_prize = payout.sum(axis=1)
        any_cash = np.any(ranks <= 5, axis=1)
        top3 = np.any(ranks <= 3, axis=1)
        first = np.any(ranks == 1, axis=1)
        both_cash = np.all(ranks <= 5, axis=1)
        fail = np.any(hh["future_minimum_failure"], axis=1)
        m = {
            "expected_household_prize_share": float(household_prize.mean()),
            "p_any_cash": float(any_cash.mean()),
            "p_top3": float(top3.mean()),
            "p_first": float(first.mean()),
            "p_both_cash": float(both_cash.mean()),
            "future_minimum_failure_risk": float(fail.mean()),
            "household_final_p05": float(np.quantile(final.sum(axis=1), 0.05)),
            "household_final_p50": float(np.quantile(final.sum(axis=1), 0.50)),
            "household_final_p95": float(np.quantile(final.sum(axis=1), 0.95)),
        }
        scenario_metrics[sc.name] = m
        for k in weighted:
            weighted[k] += sc.mixture_weight * m[k]
    overlap = portfolio_overlap(bets_by_entry)
    outlays = {e: int(sum(b.amount for b in bets)) for e, bets in bets_by_entry.items()}
    return {
        "weighted": weighted,
        "by_scenario": scenario_metrics,
        "outlay_by_entry": outlays,
        "household_outlay": int(sum(outlays.values())),
        "overlap": overlap,
        "field_model": {
            "opponents": int(len(opponents)),
            "lower_tail_floor": int(lower_tail_floor if lower_tail_floor is not None else field_state.lower_tail_floor_assumption),
            "scenarios": [asdict(s) for s in scenarios],
        },
    }


def _allocate_edge_weighted(
    balance: int,
    candidates: Sequence,
    n_games: int,
    fraction: float,
    rules: RegularSeasonRules,
) -> tuple[Bet, ...]:
    n_games = max(rules.minimum_games, min(n_games, len(candidates)))
    target = int(math.floor(balance * fraction / rules.wager_increment) * rules.wager_increment)
    target = max(target, rules.minimum_games * rules.minimum_wager)
    target = min(target, balance)
    selected = list(candidates[:n_games])
    amounts = np.full(n_games, rules.minimum_wager, dtype=int)
    remainder = target - int(amounts.sum())
    if remainder < 0:
        raise ValueError("target cannot satisfy minimum positions")
    edges = np.array([max(0.0, float(c.edge_per_dollar)) for c in selected], dtype=float)
    weights = np.ones(n_games) / n_games if edges.sum() <= 1e-12 else edges / edges.sum()
    units = remainder // rules.wager_increment
    raw = weights * units
    extra_units = np.floor(raw).astype(int)
    left = int(units - extra_units.sum())
    if left > 0:
        order = np.argsort(-(raw - extra_units))
        extra_units[order[:left]] += 1
    amounts += extra_units * rules.wager_increment
    return tuple(Bet(c.game_id, c.side, int(a)) for c, a in zip(selected, amounts))


def build_joint_candidate(
    balances: Mapping[str, int],
    game_probabilities: Mapping[str, GameProbability],
    rules: RegularSeasonRules,
    c_fraction: float,
    a_fraction: float,
    c_games: int,
    a_games: int,
    overlap_mode: str,
) -> Dict[str, tuple[Bet, ...]]:
    ranked = ranked_candidates(game_probabilities)
    if overlap_mode not in {"shared", "hybrid", "split"}:
        raise ValueError("overlap_mode must be shared, hybrid, or split")
    if overlap_mode == "shared":
        c_pool = ranked
        a_pool = ranked
    elif overlap_mode == "split":
        c_pool = ranked[0::2] + ranked[1::2]
        a_pool = ranked[1::2] + ranked[0::2]
    else:
        top = ranked[:1]
        rest = ranked[1:]
        c_pool = top + rest[0::2] + rest[1::2]
        a_pool = top + rest[1::2] + rest[0::2]
    return {
        "Catherine": _allocate_edge_weighted(int(balances["Catherine"]), c_pool, c_games, c_fraction, rules),
        "Amanda": _allocate_edge_weighted(int(balances["Amanda"]), a_pool, a_games, a_fraction, rules),
    }


def optimize_joint_household(
    balances: Mapping[str, int],
    game_probabilities: Mapping[str, GameProbability],
    rules: RegularSeasonRules,
    field_state: FieldState,
    scenarios: Sequence[FieldScenario] | None = None,
    cfg: OptimizerConfig | None = None,
    fractions: Sequence[float] = (0.20, 0.35, 0.50),
    game_counts: Sequence[int] = (4, 5, 6),
    overlap_modes: Sequence[str] = ("shared", "hybrid", "split"),
) -> Dict[str, object]:
    cfg = cfg or OptimizerConfig()
    scenarios = tuple(scenarios or default_field_scenarios())
    prepared = prepare_field_paths(field_state, scenarios, cfg)
    best: Dict[str, object] | None = None
    evaluated = 0
    for cf in fractions:
        for af in fractions:
            for cg in game_counts:
                for ag in game_counts:
                    for mode in overlap_modes:
                        bets = build_joint_candidate(balances, game_probabilities, rules, cf, af, cg, ag, mode)
                        metrics = evaluate_portfolio_across_scenarios(
                            balances, bets, game_probabilities, rules, field_state, scenarios, cfg,
                            prepared_field_paths=prepared,
                        )
                        evaluated += 1
                        score = metrics["weighted"]["expected_household_prize_share"]
                        worst = min(x["expected_household_prize_share"] for x in metrics["by_scenario"].values())
                        failure = metrics["weighted"]["future_minimum_failure_risk"]
                        key = (score, worst, -failure, -metrics["household_outlay"])
                        if best is None or key > best["_key"]:
                            best = {
                                "_key": key,
                                "bets_by_entry": bets,
                                "parameters": {
                                    "c_fraction": cf,
                                    "a_fraction": af,
                                    "c_games": cg,
                                    "a_games": ag,
                                    "overlap_mode": mode,
                                },
                                "metrics": metrics,
                            }
    assert best is not None
    best.pop("_key", None)
    best["evaluated_candidates"] = evaluated
    return best


def evaluate_benchmark_set(
    balances: Mapping[str, int],
    game_probabilities: Mapping[str, GameProbability],
    rules: RegularSeasonRules,
    field_state: FieldState,
    scenarios: Sequence[FieldScenario] | None = None,
    cfg: OptimizerConfig | None = None,
    extra_portfolios: Sequence[BenchmarkPortfolio] = (),
) -> list[Dict[str, object]]:
    cfg = cfg or OptimizerConfig()
    scenarios = tuple(scenarios or default_field_scenarios())
    prepared = prepare_field_paths(field_state, scenarios, cfg)
    rows: list[Dict[str, object]] = []
    portfolios = list(build_household_benchmarks(balances, game_probabilities, rules)) + list(extra_portfolios)
    for p in portfolios:
        m = evaluate_portfolio_across_scenarios(
            balances, p.bets_by_entry, game_probabilities, rules, field_state, scenarios, cfg,
            prepared_field_paths=prepared,
        )
        rows.append({"strategy": p.name, "metadata": p.metadata, **m})
    rows.sort(key=lambda r: r["weighted"]["expected_household_prize_share"], reverse=True)
    return rows


def serialize_bets(bets_by_entry: Mapping[str, Sequence[Bet]]) -> Dict[str, list[dict[str, object]]]:
    return {e: [asdict(b) for b in bets] for e, bets in bets_by_entry.items()}
