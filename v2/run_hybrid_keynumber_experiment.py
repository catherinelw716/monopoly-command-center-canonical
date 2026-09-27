"""V2-0006C: hybrid exact-margin push correction.

Research-only. Keeps the normal cover/loss relationship and replaces only
integer-line push mass with a walk-forward empirical exact-margin estimate.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from statistics import NormalDist

import nflreadpy as nfl
import numpy as np
import pandas as pd
import polars as pl

from build_historical_dataset import normalize_schedule_core
from run_first_experiment import bootstrap_mean_ci

OFFSETS = np.array([-1.5, -1.0, -0.5, 0.0, 0.5, 1.0, 1.5], dtype=float)
MIN_TRAIN_SEASONS = 4
NORMAL = NormalDist()
SPREAD_BW = [1.5, 2.5, 4.0, 6.0]
SHRINK = [25.0, 75.0]
EPS = 1e-12


def load_games(start_season: int, end_season: int) -> pd.DataFrame:
    parts: list[pl.DataFrame] = []
    for season in range(start_season, end_season + 1):
        print(f"[data] season {season}: schedules")
        raw = nfl.load_schedules([season])
        g = normalize_schedule_core(raw)
        if "game_type" in g.columns:
            g = g.filter(pl.col("game_type") == "REG")
        g = g.filter(pl.col("home_margin").is_not_null() & pl.col("home_spread_closing").is_not_null())
        parts.append(g)
    df = pl.concat(parts, how="diagonal_relaxed").sort(["season", "week", "gameday", "game_id"]).to_pandas()
    df["home_margin"] = pd.to_numeric(df["home_margin"], errors="coerce").astype(float)
    df["home_spread_closing"] = pd.to_numeric(df["home_spread_closing"], errors="coerce").astype(float)
    df["market_fair_margin"] = -df["home_spread_closing"]
    df["market_residual"] = df["home_margin"] - df["market_fair_margin"]
    return df


def outcome_class(home_margin: float, target_spread: float) -> int:
    ats = float(home_margin + target_spread)
    if math.isclose(ats, 0.0, abs_tol=1e-9):
        return 1
    return 2 if ats > 0 else 0


def normal_probs(mu: float, sigma: float, target_spread: float, delta: float) -> np.ndarray:
    sigma = max(float(sigma), 1e-6)
    m = float(mu + delta)
    integer_line = math.isclose(target_spread, round(target_spread), abs_tol=1e-9)
    if integer_line:
        zlo = (-0.5 - m) / sigma
        zhi = (0.5 - m) / sigma
        loss = NORMAL.cdf(zlo)
        push = NORMAL.cdf(zhi) - NORMAL.cdf(zlo)
        cover = 1.0 - NORMAL.cdf(zhi)
    else:
        z = -m / sigma
        loss = NORMAL.cdf(z)
        push = 0.0
        cover = 1.0 - loss
    p = np.array([loss, push, cover], dtype=float)
    return p / p.sum()


def hybrid_from_normal(normal_p: np.ndarray, p_push: float) -> np.ndarray:
    p_push = float(np.clip(p_push, 0.0, 1.0))
    nonpush = float(normal_p[0] + normal_p[2])
    if nonpush <= EPS:
        return np.array([(1 - p_push) / 2, p_push, (1 - p_push) / 2], dtype=float)
    loss_share = float(normal_p[0] / nonpush)
    cover_share = float(normal_p[2] / nonpush)
    return np.array([(1 - p_push) * loss_share, p_push, (1 - p_push) * cover_share], dtype=float)


def brier3(p: np.ndarray, cls: int) -> float:
    y = np.zeros(3, dtype=float)
    y[cls] = 1.0
    return float(np.sum((p - y) ** 2))


def logloss3(p: np.ndarray, cls: int) -> float:
    return float(-math.log(max(float(p[cls]), 1e-12)))


def empirical_push(
    train_margin: np.ndarray,
    weights: np.ndarray,
    target_spread: float,
    normal_push: float,
    shrink: float,
) -> float:
    required_margin = -float(target_spread)
    hits = np.isclose(train_margin, required_margin, atol=1e-9)
    numerator = float(weights[hits].sum()) + float(shrink) * float(normal_push)
    denominator = float(weights.sum()) + float(shrink)
    return numerator / max(denominator, EPS)


def evaluate(
    train: pd.DataFrame,
    test: pd.DataFrame,
    model: str,
    params: tuple[float | None, float] | None = None,
) -> pd.DataFrame:
    train_margin = train["home_margin"].to_numpy(float)
    train_fair = train["market_fair_margin"].to_numpy(float)
    resid = train["market_residual"].to_numpy(float)
    mu = float(np.mean(resid))
    sigma = float(np.std(resid, ddof=1))
    rows = []

    for _, r in test.iterrows():
        q_fair = float(r["market_fair_margin"])
        for delta in OFFSETS:
            target_spread = float(r["home_spread_closing"] + delta)
            cls = outcome_class(float(r["home_margin"]), target_spread)
            pn = normal_probs(mu, sigma, target_spread, float(delta))
            is_integer = math.isclose(target_spread, round(target_spread), abs_tol=1e-9)

            if model == "normal" or not is_integer:
                p = pn
            else:
                assert params is not None
                hs, shrink = params
                if model == "global_hybrid":
                    weights = np.ones(len(train), dtype=float)
                elif model == "spread_hybrid":
                    assert hs is not None
                    weights = np.exp(-0.5 * ((train_fair - q_fair) / float(hs)) ** 2)
                else:
                    raise ValueError(model)
                pp = empirical_push(train_margin, weights, target_spread, float(pn[1]), float(shrink))
                p = hybrid_from_normal(pn, pp)

            rows.append({
                "season": int(r["season"]),
                "week": int(r["week"]),
                "game_id": r["game_id"],
                "home_team": r["home_team"],
                "away_team": r["away_team"],
                "home_margin": float(r["home_margin"]),
                "home_spread_closing": float(r["home_spread_closing"]),
                "market_fair_margin": q_fair,
                "delta": float(delta),
                "target_spread": target_spread,
                "integer_target": bool(is_integer),
                "actual_class": ["loss", "push", "cover"][cls],
                "p_loss": float(p[0]),
                "p_push": float(p[1]),
                "p_cover": float(p[2]),
                "brier3": brier3(p, cls),
                "logloss3": logloss3(p, cls),
                "model": model,
            })
    return pd.DataFrame(rows)


def per_game_metric(detail: pd.DataFrame, integer_only: bool) -> pd.DataFrame:
    d = detail[detail["integer_target"]].copy() if integer_only else detail.copy()
    return d.groupby(["season", "game_id", "model"], as_index=False).agg(
        brier3=("brier3", "mean"), logloss3=("logloss3", "mean"), n_targets=("brier3", "size")
    )


def tune(train: pd.DataFrame, model: str):
    seasons = sorted(int(x) for x in train["season"].unique())
    val_season = seasons[-1]
    inner_train = train[train["season"] < val_season].copy()
    inner_val = train[train["season"] == val_season].copy()
    if model == "global_hybrid":
        candidates = [(None, s) for s in SHRINK]
    elif model == "spread_hybrid":
        candidates = [(h, s) for h in SPREAD_BW for s in SHRINK]
    else:
        raise ValueError(model)

    scores = {}
    best = None
    best_score = float("inf")
    for params in candidates:
        d = evaluate(inner_train, inner_val, model, params)
        pg = per_game_metric(d, integer_only=True)
        score = float(pg["brier3"].mean())
        scores[str(params)] = score
        if score < best_score:
            best_score = score
            best = params
    assert best is not None
    return best, {"validation_season": val_season, "scores": scores, "selected": list(best)}


def summarize(detail: pd.DataFrame) -> dict:
    pgi = per_game_metric(detail, integer_only=True)
    pga = per_game_metric(detail, integer_only=False)
    di = detail[detail["integer_target"]].copy()
    close = detail[np.isclose(detail["delta"], 0.0)].copy()
    return {
        "n_games": int(detail["game_id"].nunique()),
        "integer_per_game_brier3": float(pgi["brier3"].mean()),
        "integer_per_game_logloss3": float(pgi["logloss3"].mean()),
        "all_offset_per_game_brier3": float(pga["brier3"].mean()),
        "all_offset_per_game_logloss3": float(pga["logloss3"].mean()),
        "integer_push_pred": float(di["p_push"].mean()),
        "integer_push_obs": float((di["actual_class"] == "push").mean()),
        "closing_brier3": float(close["brier3"].mean()),
    }


def key_diag(detail: pd.DataFrame) -> list[dict]:
    a = detail["target_spread"].abs()
    out = []
    for key in [3.0, 3.5, 7.0, 7.5]:
        x = detail[np.isclose(a, key)]
        if x.empty:
            continue
        out.append({
            "abs_target_spread": key,
            "n": int(len(x)),
            "brier3": float(x["brier3"].mean()),
            "pred_push": float(x["p_push"].mean()),
            "obs_push": float((x["actual_class"] == "push").mean()),
        })
    return out


def run(df: pd.DataFrame):
    seasons = sorted(int(x) for x in df["season"].unique())
    test_seasons = [s for i, s in enumerate(seasons) if i >= MIN_TRAIN_SEASONS]
    folds = []
    details = []

    for s in test_seasons:
        train = df[df["season"] < s].copy()
        test = df[df["season"] == s].copy()
        pg, tg = tune(train, "global_hybrid")
        ps, ts = tune(train, "spread_hybrid")
        print(f"[fold {s}] global={pg} spread={ps}")
        dn = evaluate(train, test, "normal")
        dg = evaluate(train, test, "global_hybrid", pg)
        ds = evaluate(train, test, "spread_hybrid", ps)
        details.extend([dn, dg, ds])
        sn, sg, ss = summarize(dn), summarize(dg), summarize(ds)
        folds.append({
            "test_season": s,
            "global_params": list(pg),
            "spread_params": list(ps),
            "global_tuning": tg,
            "spread_tuning": ts,
            "normal": sn,
            "global_hybrid": sg,
            "spread_hybrid": ss,
            "normal_minus_spread_integer_brier": sn["integer_per_game_brier3"] - ss["integer_per_game_brier3"],
            "normal_minus_global_integer_brier": sn["integer_per_game_brier3"] - sg["integer_per_game_brier3"],
            "global_minus_spread_integer_brier": sg["integer_per_game_brier3"] - ss["integer_per_game_brier3"],
            "normal_minus_spread_all_brier": sn["all_offset_per_game_brier3"] - ss["all_offset_per_game_brier3"],
        })
        print(
            f"  integer Brier normal={sn['integer_per_game_brier3']:.5f} "
            f"global={sg['integer_per_game_brier3']:.5f} spread={ss['integer_per_game_brier3']:.5f}"
        )

    detail = pd.concat(details, ignore_index=True)
    dn = detail[detail["model"] == "normal"].copy()
    dg = detail[detail["model"] == "global_hybrid"].copy()
    ds = detail[detail["model"] == "spread_hybrid"].copy()

    primary = [f["normal_minus_spread_integer_brier"] for f in folds]
    global_delta = [f["normal_minus_global_integer_brier"] for f in folds]
    cond_delta = [f["global_minus_spread_integer_brier"] for f in folds]
    safety = [f["normal_minus_spread_all_brier"] for f in folds]

    pm = float(np.mean(primary)); pci = bootstrap_mean_ci(primary, seed=716, reps=10000)
    gm = float(np.mean(global_delta)); gci = bootstrap_mean_ci(global_delta, seed=717, reps=10000)
    cm = float(np.mean(cond_delta)); cci = bootstrap_mean_ci(cond_delta, seed=718, reps=10000)
    sm = float(np.mean(safety)); sci = bootstrap_mean_ci(safety, seed=719, reps=10000)

    if pm > 0 and pci[0] > 0 and sm >= -0.00025:
        if cm > 0 and cci[0] > 0:
            verdict = "PASS SPREAD-CONDITIONED HYBRID: targeted empirical push correction robustly improves integer-line Brier and spread-conditioning robustly beats global hybrid. Advance spread-conditioned hybrid to calibration/robustness testing."
        elif gm > 0 and gci[0] > 0:
            verdict = "PASS HYBRID; CONDITIONING NOT PROVEN: empirical push correction robustly improves integer-line Brier, but spread-conditioning does not robustly beat the global hybrid. Prefer the simpler global hybrid for next-stage validation."
        else:
            verdict = "MIXED HYBRID RESULT: spread-conditioned hybrid cleared primary gate but simpler global evidence is inconsistent. Retain as challenger only and expand robustness testing before model selection."
    else:
        verdict = "FAIL HYBRID GATE: targeted empirical push correction did not robustly improve integer-line Brier without unacceptable overall deterioration. Retain normal as probability baseline and treat key-number mass as a separate price/decision feature."

    result = {
        "experiment": "V2-0006C",
        "verdict": verdict,
        "heldout_seasons": [f["test_season"] for f in folds],
        "n_unique_heldout_games": int(ds["game_id"].nunique()),
        "primary": {
            "mean_normal_minus_spread_integer_brier": pm,
            "season_bootstrap_95pct": pci,
            "mean_normal_minus_global_integer_brier": gm,
            "global_season_bootstrap_95pct": gci,
            "mean_global_minus_spread_integer_brier": cm,
            "conditioning_season_bootstrap_95pct": cci,
            "mean_normal_minus_spread_all_offset_brier": sm,
            "all_offset_season_bootstrap_95pct": sci,
        },
        "aggregate": {
            "normal": summarize(dn),
            "global_hybrid": summarize(dg),
            "spread_hybrid": summarize(ds),
        },
        "key_numbers": {
            "normal": key_diag(dn),
            "global_hybrid": key_diag(dg),
            "spread_hybrid": key_diag(ds),
        },
        "folds": folds,
        "limitations": [
            "Closing market is a research fair-line baseline, not a historical Sly Friday snapshot.",
            "Integer-line Brier is the preregistered primary because the hybrid is identical to normal on half-point targets.",
            "Alternate target offsets test probability shape and do not assert historical availability.",
            "No 2026 outcomes are used.",
        ],
    }
    return result, detail


def write_report(result: dict, detail: pd.DataFrame, out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "results.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    detail.to_csv(out_dir / "predictions.csv", index=False)
    p = result["primary"]
    lines = [
        "# V2-0006C Hybrid Key-Number Experiment",
        "",
        f"**Verdict:** {result['verdict']}",
        "",
        "| Model | Integer Brier3 | Integer log loss | All-offset Brier3 | Push pred / obs | Closing Brier3 |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for key, label in [("normal", "Normal"), ("global_hybrid", "Global hybrid"), ("spread_hybrid", "Spread-conditioned hybrid")]:
        x = result["aggregate"][key]
        lines.append(
            f"| {label} | {x['integer_per_game_brier3']:.5f} | {x['integer_per_game_logloss3']:.5f} | {x['all_offset_per_game_brier3']:.5f} | {x['integer_push_pred']:.2%} / {x['integer_push_obs']:.2%} | {x['closing_brier3']:.5f} |"
        )
    lines += [
        "",
        f"Primary normal-minus-spread integer Brier: **{p['mean_normal_minus_spread_integer_brier']:+.6f}**, 95% CI **[{p['season_bootstrap_95pct'][0]:+.6f}, {p['season_bootstrap_95pct'][1]:+.6f}]**.",
        f"Normal-minus-global integer Brier: **{p['mean_normal_minus_global_integer_brier']:+.6f}**, 95% CI **[{p['global_season_bootstrap_95pct'][0]:+.6f}, {p['global_season_bootstrap_95pct'][1]:+.6f}]**.",
        f"Global-minus-spread integer Brier: **{p['mean_global_minus_spread_integer_brier']:+.6f}**, 95% CI **[{p['conditioning_season_bootstrap_95pct'][0]:+.6f}, {p['conditioning_season_bootstrap_95pct'][1]:+.6f}]**.",
        f"Safety normal-minus-spread all-offset Brier: **{p['mean_normal_minus_spread_all_offset_brier']:+.6f}**, 95% CI **[{p['all_offset_season_bootstrap_95pct'][0]:+.6f}, {p['all_offset_season_bootstrap_95pct'][1]:+.6f}]**.",
        "",
        "No production model or wager changes are made by this experiment alone.",
    ]
    (out_dir / "REPORT.md").write_text("\n".join(lines), encoding="utf-8")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--start-season", type=int, default=2016)
    ap.add_argument("--end-season", type=int, default=2025)
    ap.add_argument("--out-dir", type=Path, default=Path("v2/results/hybrid_keynumber"))
    args = ap.parse_args()
    if args.end_season >= 2026:
        raise SystemExit("2026+ intentionally excluded")
    df = load_games(args.start_season, args.end_season)
    result, detail = run(df)
    write_report(result, detail, args.out_dir)
    print(json.dumps({
        "verdict": result["verdict"],
        "primary": result["primary"],
        "aggregate": result["aggregate"],
        "key_numbers": result["key_numbers"],
    }, indent=2))


if __name__ == "__main__":
    main()
