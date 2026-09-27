# Week 3 Sunday V2 contextual-tiebreak optimizer run

Date: 2026-09-27

## What changed
The V2 probability layer remains frozen and market-derived. A contextual tiebreak layer now applies only to games whose absolute V2 edge is below 1.0% per dollar. It can rank/select those near-neutral games using previously verified external-source alignment, injuries, and weather context, but:
- it never changes P(cover/push/loss);
- it never creates synthetic model edge;
- it never displaces a material V2 market-price edge;
- near-neutral contextual selections receive zero allocation edge, so extra dollars still flow only to material V2 edges.

Current-week 10% CVaR downside remains part of the robust objective.

## CI result
GitHub V2 Research CI passed after the contextual layer was enabled.

## Selected portfolio (400 simulations per scenario in CI)
- Catherine: ~10% deployment, 4 games, $1,100 total
  - BUF -7 vs LAC: $800 — material V2 price edge
  - CAR -2.5 at CLE: $100 — contextual tiebreak
  - KC -10.5 at MIA: $100 — contextual tiebreak
  - ARI +8.5 at SF: $100 — contextual tiebreak
- Amanda: ~10% deployment, 6 games, $1,000 total
  - NE +3 at JAX: $500 — material V2 price edge
  - SEA -7.5 at WAS: $100 — contextual tiebreak
  - MIN -1.5 at TB: $100 — contextual tiebreak
  - DEN +2.5 vs LAR: $100 — contextual tiebreak
  - PIT +3.5 vs CIN: $100 — lower-tier contextual diversification
  - DET -6.5 vs NYJ: $100 — lower-tier contextual diversification

Household outlay: $2,100
Overlap mode: split
Expected household prize share (base): ~0.012258
P(any cash): ~0.0775
Future-minimum failure risk: ~0.245833

## Material V2 market edges
- BUF -7 vs market about -7.5: edge per dollar ~0.033235
- NE +3 vs market about +2.5: edge per dollar ~0.027639

All other selected games remain near-neutral under the frozen probability layer and should be described as contextual/minimum-game/diversification choices, not V2 probability convictions.

## Weather policy and selected-game context
Weather remains outside the probability model and is displayed in every game analysis.
- LAC @ BUF: Highmark Stadium; sunny, ~65F, some wind. Moderate passing/kicking variance flag.
- CAR @ CLE: Huntington Bank Field; sunny, ~68F, some wind gusts. Low-moderate flag.
- KC @ MIA: Hard Rock Stadium; sunny/humid, ~85F. Heat/humidity flag, low wind disruption.
- ARI @ SF: Levi's Stadium; sunny, ~67F. Low weather risk.
- NE @ JAX: EverBank Stadium; mostly sunny/humid, ~84F. Heat/humidity flag, low wind disruption.
- SEA @ WAS: Northwest Stadium; heavy rain/wind, 30+ mph gusts, ~61F. Material weather risk.
- MIN @ TB: Raymond James Stadium; sunny/humid, ~84F. Heat/humidity flag.
- LAR @ DEN: Empower Field at Mile High; sunny, ~81F, small rain chance; altitude remains contextual.
- CIN @ PIT: Acrisure Stadium; sunny, ~69F, some wind gusts. Low-moderate flag.
- NYJ @ DET: Ford Field dome; indoor/climate controlled. Weather neutral.
