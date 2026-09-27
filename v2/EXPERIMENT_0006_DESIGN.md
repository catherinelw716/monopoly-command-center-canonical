# V2-0006 — Discrete Margin / Key-Number Experiment

Status: preregistered before execution. Research-only; no production changes.

## Question
Does a discrete empirical NFL margin-residual model improve probability quality relative to a normal residual approximation when translating a market fair line into exact ATS cover / push / loss probabilities?

## Data
- Regular-season games only.
- Seasons 2012–2025 available for development; first execution uses 2016–2025 for consistency with V2-0001/0002/0003.
- No 2026 outcomes.
- Closing market spread is a research fair-line baseline only; this is **not** a historical Friday/Sly stale-line backtest.
- `home_spread_closing` uses V2 conventional home-team notation (negative = home favorite).
- Market-predicted home margin = `-home_spread_closing`.
- Market residual = actual home margin − market-predicted home margin = actual home ATS margin at the closing spread.

## Models
### Baseline A — Normal lattice approximation
Fit the training residual mean and standard deviation. For integer target spreads, approximate push mass with a ±0.5-point continuity cell around zero. For half-point target spreads, push probability is zero.

### Baseline B — Global empirical residual distribution
Use the unconditional training residual distribution. This captures NFL scoring discreteness/key-number mass without conditioning on market spread or total.

### Challenger — Conditional empirical kernel distribution
Weight historical training residuals by similarity to the target game's market-predicted margin and game total. Gaussian kernels are used for spread/total similarity, with shrinkage toward the global empirical distribution.

Kernel hyperparameters are selected only inside the training window using the last training season as inner validation. Candidate grid is frozen before execution:
- spread bandwidth: 2.5, 5.0, 10.0 points
- total bandwidth: 7.5, 15.0 points
- global shrinkage equivalent count: 25, 75

No football/PBP features enter this experiment.

## Walk-forward validation
Outer test seasons begin only after four complete prior seasons are available. Each outer test season is predicted from earlier seasons only. Hyperparameter tuning occurs inside each outer training window.

## Exact-line evaluation
For each game, evaluate the distribution at target spread offsets relative to closing market:

`[-1.5, -1.0, -0.5, 0.0, +0.5, +1.0, +1.5]`

For a target offset `d`, target home spread = closing home spread + `d`. The realized outcome is cover / push / loss at that exact target spread.

These alternate target lines are used to test the shape/calibration of the margin distribution. They do **not** claim those prices were historically available to Monopoly players.

## Primary metric
Per-game average 3-class Brier score across the seven target offsets, then averaged by held-out season. This prevents the seven correlated target lines for one NFL game from being treated as seven independent games.

Primary comparison: conditional empirical challenger vs normal baseline.

Promotion evidence requires:
1. positive mean season-level Brier improvement (normal minus challenger), and
2. season-bootstrap 95% interval above zero.

If the challenger improves only versus normal but not versus global empirical, the result is evidence for **discreteness**, not for conditional spread/total modeling.

## Secondary metrics
- challenger vs global empirical 3-class Brier
- 3-class log loss
- closing-line (`offset=0`) Brier/log loss
- non-push binary cover Brier
- predicted vs observed push rate on integer target spreads
- key-number groups around target absolute spreads 3/3.5 and 7/7.5
- probability curve versus target-line advantage

Subgroup findings are diagnostic unless explicitly preregistered for later untouched validation.

## Interpretation guardrails
- This experiment estimates outcome distributions around a closing-market fair line; it does not validate historical Sly-to-Sunday line movement.
- Synthetic offsets test probability shape, not historical availability.
- No subgroup result can override a failed aggregate promotion gate.
- No production V1/V2 pick logic changes from this experiment alone.
