# V2-0006B — Corrected Absolute-Margin / Key-Number Experiment

Status: preregistered after V2-0006A QA failure and before 0006B execution.

## Why 0006A is not accepted
0006A modeled empirical **market residuals**. That preserves generic residual discreteness but can wash out the NFL's absolute final-margin mass at 3 and 7 when residuals from different fair spreads are mixed/recentered. Its key-number calibration exposed the problem: at target absolute spread 3, observed pushes were ~9.6% while the conditional residual model predicted only ~2.25%.

That is a model-form/implementation mismatch with the stated goal of modeling exact NFL key-number mass. 0006A is retained as a QA artifact but cannot answer the registered key-number question.

## Question
Does modeling the **integer final scoring margin directly**, conditional on market fair spread, improve exact ATS cover/push/loss probabilities versus a normal residual approximation? Does game total add stable incremental value beyond conditioning on the fair spread alone?

## Data and leakage rules
- Regular-season games only.
- 2016–2025 for direct comparability with prior V2 experiments.
- No 2026 outcomes.
- Closing spread is a research fair-line baseline only, not a historical Sly/Friday snapshot.
- Outer walk-forward by season after four prior complete seasons.
- Hyperparameters selected only within the training window using the last training season.

## Models
### Baseline A — Normal residual lattice
Same mandatory baseline as 0006A. Normal market residual distribution with an integer-line continuity cell for push probability.

### Baseline B — Spread-conditioned discrete margin
Estimate the empirical distribution of **actual integer home margin** using Gaussian weights on similarity between training market fair margin and query market fair margin.

### Challenger — Spread + total conditioned discrete margin
Same integer-margin model, adding Gaussian similarity weighting on the closing game total.

For each query/target line, weighted historical **actual final margins** are classified directly as cover/push/loss against that target spread. This preserves absolute mass at ±3, ±7, etc.

Both discrete models shrink toward the normal baseline to prevent sparse-condition overconfidence.

Frozen candidate grids:
- spread bandwidth: 1.5, 2.5, 4.0, 6.0 points
- total bandwidth for 2D challenger: 7.5, 15.0 points
- normal-prior shrinkage equivalent count: 25, 75

## Target lines
Evaluate offsets relative to closing market:
`[-1.5, -1.0, -0.5, 0.0, +0.5, +1.0, +1.5]`

Alternate lines test distribution shape only; they do not claim historical availability.

## Primary metric and gate
Per-game mean 3-class Brier across the seven target lines, then season-level walk-forward comparison.

Primary comparison: **best spread-conditioned discrete model vs normal baseline**.

Evidence for absolute discrete-margin modeling requires:
1. mean season Brier improvement > 0 (normal minus discrete), and
2. season-bootstrap 95% CI above zero.

Secondary comparison: spread+total model vs spread-only model. Total is retained only if its out-of-sample improvement is robust.

## Secondary diagnostics
- 3-class log loss
- closing-line Brier and log loss
- non-push binary cover Brier
- push calibration on integer target lines
- push calibration specifically at |spread| 3 and 7
- key-number Brier at 3 / 3.5 / 7 / 7.5
- predicted vs observed cover/push curve as target line improves/worsens relative to market

## Guardrails
- 0006A results do not tune 0006B beyond correcting the model-form mismatch; the bandwidth/shrinkage grid above is frozen before 0006B execution.
- No subgroup can override a failed aggregate gate.
- No production changes from this experiment alone.
