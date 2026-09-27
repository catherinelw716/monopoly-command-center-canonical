# V2-0009 — Benchmark Strategy Harness

Status: **IMPLEMENTED / CONTROL LAYER**

Purpose: establish simple, auditable portfolio policies that the future Catherine/Amanda joint optimizer must outperform. These are controls, not recommendations.

## Why this layer exists

A complex optimizer can appear impressive simply because there is no clear comparison. V2-0009 therefore evaluates candidate optimization logic against fixed benchmark policies before field-scenario or continuation-value complexity is allowed to count as improvement.

## Implemented controls

1. **minimum_4x100** — strongest four model sides, $100 each.
2. **equal_top4_30pct** — 30% of each entry's bankroll, equally across the strongest four sides.
3. **flat_20pct_positive** — deploy 20% across positive-edge games, filling to four if fewer than four are positive.
4. **flat_30pct_positive** — same at 30%.
5. **flat_40pct_positive** — same at 40%.
6. **fractional_kelly_quarter** — quarter-Kelly-style control using P(win)-P(loss), with a 50% aggregate bankroll cap and contest minimums enforced.
7. **diversified_pair_30pct** — deliberately low-overlap household control: ranked opportunities alternate between Catherine and Amanda.
8. **identical_top4_30pct** — deliberately high-correlation control: both entries play the same strongest four games.

The existing V1 heuristic portfolio is retained as a separate fixed-policy comparator when the relevant week's V2 probabilities are available. It is not generalized into a fake formula.

## Probability isolation

The harness consumes frozen P(cover/push/loss) inputs. It never changes those probabilities because of bankroll, standings, desired variance, or household strategy.

For even-money Monopoly settlement, per-dollar expected net for a side is:

`P(win) - P(loss)`

Push probability contributes zero net.

## Shared outcomes

Both household entries are simulated against the same sampled NFL result for a shared game. Same-side overlap therefore creates positive household outcome correlation; opposite sides create anti-correlation except on pushes.

## Current one-week metrics

Before the field model exists, benchmark evaluation reports:
- expected entry and household ending balance
- 5th / 50th / 95th percentile ending balances
- P(balance increases / decreases / is unchanged)
- P(zero balance)
- P(any household entry increases)
- P(both household entries increase)
- total deployment
- game-overlap share
- same-side overlap share

Rank movement, P(any cash), P(top 3), and expected prize value are intentionally **not fabricated at this stage**. Those require the next field-scenario layer.

## Promotion rule

A future joint optimizer is not considered better merely because it has higher expected weekly bankroll. It must be compared against these controls under the same probabilities, same field scenarios, and same random outcomes, with household prize equity as the eventual primary objective.

## Next phase

Build the field-scenario ensemble from observed Week 1–2 behavior without estimating one falsely precise opponent policy. Then run these same controls and candidate joint policies against every scenario.
