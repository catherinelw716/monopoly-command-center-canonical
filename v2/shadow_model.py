"""Frozen V2 prospective shadow probability utilities.

Implements the global-hybrid architecture that passed V2-0006C and the
independent-era V2-0006D replication.  This module intentionally contains no
football-feature residual adjustment and no external-source weighting.
"""
from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from statistics import NormalDist
from typing import Any

import numpy as np

NORMAL = NormalDist()
EPS = 1e-12
MODEL_VERSION = "V2-0006C-global-hybrid-r1"


def _is_integer_line(x: float) -> bool:
    return math.isclose(float(x), round(float(x)), abs_tol=1e-9)


def normal_probs(residual_mu: float, residual_sigma: float, target_home_spread: float, delta_from_market: float) -> np.ndarray:
    """Return [home loss, push, home cover] at an exact target spread.

    `delta_from_market` is target_home_spread - market_home_spread using
    conventional sportsbook home-team sign convention.
    """
    sigma = max(float(residual_sigma), 1e-6)
    m = float(residual_mu + delta_from_market)
    if _is_integer_line(target_home_spread):
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
        return np.array([(1.0 - p_push) / 2.0, p_push, (1.0 - p_push) / 2.0], dtype=float)
    loss_share = float(normal_p[0] / nonpush)
    cover_share = float(normal_p[2] / nonpush)
    return np.array([(1.0 - p_push) * loss_share, p_push, (1.0 - p_push) * cover_share], dtype=float)


def canonical_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def artifact_hash(core: dict[str, Any]) -> str:
    return hashlib.sha256(canonical_json(core).encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class ShadowModel:
    model_version: str
    training_start_season: int
    training_end_season: int
    n_training_games: int
    residual_mu: float
    residual_sigma: float
    push_shrink: float
    margin_counts: dict[str, int]
    artifact_hash: str

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "ShadowModel":
        core = {k: v for k, v in d.items() if k not in {"artifact_hash", "generated_at_utc"}}
        expected = artifact_hash(core)
        supplied = str(d.get("artifact_hash", ""))
        if supplied and supplied != expected:
            raise ValueError(f"Model artifact hash mismatch: supplied={supplied} expected={expected}")
        return cls(
            model_version=str(d["model_version"]),
            training_start_season=int(d["training_start_season"]),
            training_end_season=int(d["training_end_season"]),
            n_training_games=int(d["n_training_games"]),
            residual_mu=float(d["residual_mu"]),
            residual_sigma=float(d["residual_sigma"]),
            push_shrink=float(d["push_shrink"]),
            margin_counts={str(k): int(v) for k, v in d["margin_counts"].items()},
            artifact_hash=expected,
        )

    @classmethod
    def load(cls, path: str | Path) -> "ShadowModel":
        return cls.from_dict(json.loads(Path(path).read_text(encoding="utf-8")))

    def predict(self, market_home_spread: float, sly_home_spread: float) -> dict[str, Any]:
        market_home_spread = float(market_home_spread)
        sly_home_spread = float(sly_home_spread)
        delta = sly_home_spread - market_home_spread
        pn = normal_probs(self.residual_mu, self.residual_sigma, sly_home_spread, delta)
        ph = pn.copy()

        if _is_integer_line(sly_home_spread):
            required_home_margin = int(round(-sly_home_spread))
            hits = int(self.margin_counts.get(str(required_home_margin), 0))
            empirical_push = (hits + self.push_shrink * float(pn[1])) / (self.n_training_games + self.push_shrink)
            ph = hybrid_from_normal(pn, empirical_push)

        return {
            "model_version": self.model_version,
            "artifact_hash": self.artifact_hash,
            "market_home_spread": market_home_spread,
            "sly_home_spread": sly_home_spread,
            "home_line_advantage": delta,
            "integer_sly_line": _is_integer_line(sly_home_spread),
            "normal": {
                "p_home_loss": float(pn[0]),
                "p_push": float(pn[1]),
                "p_home_cover": float(pn[2]),
                "p_away_cover": float(pn[0]),
                "p_away_loss": float(pn[2]),
            },
            "hybrid": {
                "p_home_loss": float(ph[0]),
                "p_push": float(ph[1]),
                "p_home_cover": float(ph[2]),
                "p_away_cover": float(ph[0]),
                "p_away_loss": float(ph[2]),
            },
        }


def build_artifact_from_games(df, push_shrink: float, start_season: int, end_season: int) -> dict[str, Any]:
    """Build a frozen artifact from the normalized historical games DataFrame."""
    margins = df["home_margin"].to_numpy(float)
    residuals = df["market_residual"].to_numpy(float)
    counts: dict[str, int] = {}
    for x in margins:
        if math.isclose(float(x), round(float(x)), abs_tol=1e-9):
            key = str(int(round(float(x))))
            counts[key] = counts.get(key, 0) + 1

    core = {
        "model_version": MODEL_VERSION,
        "training_start_season": int(start_season),
        "training_end_season": int(end_season),
        "n_training_games": int(len(df)),
        "residual_mu": float(np.mean(residuals)),
        "residual_sigma": float(np.std(residuals, ddof=1)),
        "push_shrink": float(push_shrink),
        "margin_counts": dict(sorted(counts.items(), key=lambda kv: int(kv[0]))),
    }
    out = dict(core)
    out["artifact_hash"] = artifact_hash(core)
    out["generated_at_utc"] = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    return out
