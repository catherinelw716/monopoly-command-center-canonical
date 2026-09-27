# V2-0006C — Hybrid Key-Number Push Correction

Status: preregistered before execution. Research-only; no production changes.

## Motivation
V2-0006B showed two things simultaneously:
1. replacing the full normal cover/loss distribution with a discrete empirical distribution worsened aggregate 3-class Brier; and
2. absolute integer-margin modeling materially improved push calibration, especially at exact spreads 3 and 7.

The next hypothesis is therefore deliberately narrow: **retain the normal market-based cover/loss relationship, but replace only integer-line push mass with an empirically learned exact-margin probability.**

## Models
### Baseline — Normal lattice
Same normal market-residual probability model used in 0006A/0006B.

### Baseline hybrid — Global exact-margin push
For integer target spreads only:
- estimate push probability from the historical frequency of the exact signed home final margin required to push that target line;
- shrink the empirical push rate toward the normal model's push probability;
- retain the normal model's relative loss/cover odds and rescale them to sum to `1 - P(push)`.

For half-point target lines, the model is exactly the normal baseline because push probability is structurally zero.

### Challenger hybrid — Spread-conditioned exact-margin push
Same hybrid structure, but estimate exact-margin push probability with Gaussian weighting based on similarity between the historical game's market fair home margin and the query game's market fair home margin.

No game-total input is used because 0006B did not establish incremental value for total.

## Frozen hyperparameter grid
For the spread-conditioned hybrid:
- spread bandwidth: 1.5, 2.5, 4.0, 6.0 points
- shrinkage equivalent count toward normal push probability: 25, 75

For the global hybrid:
- shrinkage equivalent count: 25, 75

Parameters are selected only within the training window using the last training season.

## Data / validation
- Regular-season games, 2016–2025.
- No 2026 outcomes.
- Outer walk-forward by season after four complete prior seasons.
- Same seven target offsets around closing market: `[-1.5, -1.0, -0.5, 0, +0.5, +1.0, +1.5]`.
- Alternate target lines test probability shape only; they do not claim historical Sly availability.

## Primary metric
**Per-game mean 3-class Brier across integer target lines only**, then season-level comparison.

Primary comparison: normal baseline minus spread-conditioned hybrid. Positive improvement favors the hybrid.

Promotion evidence requires:
1. mean season-level Brier improvement > 0; and
2. season-bootstrap 95% CI lower bound > 0.

This integer-line primary is preregistered because the hybrid is structurally identical to normal on half-point lines and is specifically intended to correct integer push/key-number probability.

## Safety metric
Per-game mean 3-class Brier across **all seven offsets** must not materially deteriorate. Because half-point predictions are unchanged, a successful integer correction should be neutral-to-positive overall.

## Secondary metrics
- 3-class log loss on integer target lines
- overall seven-offset Brier/log loss
- integer push predicted vs observed
- exact 3- and 7-point push calibration
- exact 3/3.5 and 7/7.5 Brier
- closing-line Brier
- global-hybrid vs spread-conditioned-hybrid comparison

## Interpretation
- If the hybrid robustly beats normal on integer-line Brier without degrading overall probability quality, retain it as the V2 key-number probability layer for later calibration/robustness testing.
- If global hybrid performs as well as spread-conditioned hybrid, prefer global for simplicity.
- If neither hybrid clears the aggregate integer-line gate, retain normal as the research probability baseline and treat key-number information as a separate decision/price feature rather than embedding it in the probability distribution.
- No production promotion from this experiment alone.
