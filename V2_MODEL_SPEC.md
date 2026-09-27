# NFL Monopoly Command Center — V2 Model Specification

Status: Research/design only. V1 remains the production champion until V2 passes the promotion gates below.

## 1. Objective

V2 is not a generic NFL picker. It is a two-layer decision system:

1. **Prediction layer:** estimate the probability that each side covers **Sly's frozen spread**, including push probability and uncertainty.
2. **Tournament layer:** choose Catherine/Amanda wagers, amounts, overlap, and number of games to maximize **household season prize equity** under the actual Monopoly rules.

The central design rule is to keep these two problems separate. A game's predictive edge should not be distorted by standings strategy; standings strategy should act only in the portfolio optimizer.

---

## 2. Research conclusions that drive the design

### 2.1 Start from the market, not from scratch
NFL betting-market research generally finds that information content improves as the week progresses and that exploitable inefficiencies are difficult and unstable. Therefore V2 should treat the timestamped multi-book market as a strong prior/baseline, then ask whether team/player/context information predicts **residual error** beyond that market.

Implication: the model should predict a correction to the market's fair spread, not independently reinvent team strength every week.

### 2.2 Key numbers require a discrete margin model
NFL final margins are highly non-normal. Historical nflverse analyses show large mass at 3 and 7, so a half-point crossing 3 or 7 is not equivalent to a half-point elsewhere.

Implication: V2 must estimate a discrete/empirical margin distribution and derive P(cover), P(push), P(loss) at Sly's exact spread. A normal approximation may be retained only as a baseline.

### 2.3 Calibration matters more than labels
For wagering decisions, an honest 54% forecast is more useful than an uncalibrated "A" grade. Model selection must emphasize reliability/calibration, Brier/log loss, and monotonicity of edge buckets rather than hit rate alone.

### 2.4 External sources are not independent votes
SportsLine, Gridiron, Lucas, market movement, and our model may share information. Their agreement is useful for display and diagnosis, but should not be treated as four independent pieces of evidence in the prediction equation.

Implication: external-source influence must be learned prospectively as incremental value after controlling for the market/core model. Until enough data exists, the sources are context/benchmark inputs rather than hard-coded weights.

### 2.5 Monopoly requires a tournament optimizer, not Kelly alone
The goal is not to maximize ordinary bankroll growth. The bankroll is the scoring state of a top-heavy contest with public standings, minimum bets, possible elimination, playoff qualification/minimums, and two household entries.

Implication: V2 should optimize expected **household prize value** and report P(any cash), P(top 3), P(1st), survival/elimination risk, and final-balance distributions. Kelly/fractional Kelly can be a benchmark but not the production objective.

---

## 3. V2 architecture

### Layer A — Point-in-time data spine
Every observation must be reproducible at a specific prediction timestamp.

Required fields per game/snapshot:
- game_id, season, week, kickoff
- Sly frozen spread and timestamp
- multi-book spreads + prices/juice + timestamps
- market median/weighted consensus, dispersion, best/worst book
- opener and line path known **as of prediction time**
- total and moneyline context
- official injury/practice/game status known as of timestamp
- projected starter/depth chart state
- pregame team/player metrics only
- source provenance and freshness

Primary historical football data:
- nflverse/nflreadr schedules, play-by-play, team stats, player stats, depth charts, rosters, injuries, snap counts, NGS where useful.

Production injury truth:
- NFL/team official reports first; nflverse for structured historical ingestion.

Historical market requirement:
- exact stale-line research needs timestamped market snapshots. Paid historical feeds such as The Odds API or SportsDataIO can supply this. nflverse closing-line data is sufficient for market-baseline research but **not** sufficient to reconstruct Friday/Sunday stale-line states.
- If historical snapshots are unavailable, stale-line edge must be evaluated prospectively from our own saved snapshots rather than fabricated retrospectively.

External sources:
- SportsLine, Gridiron, Lucas captured with exact recommendation, exact reference line, timestamp, and confidence/grade.

### Layer B — Market fair-line engine
Goal: estimate the market's fair spread at each timestamp.

Candidate methodology:
1. Normalize team orientation/signs.
2. Preserve individual book points and spread prices.
3. Build robust consensus using median/trimmed aggregation, not one site's headline number.
4. Convert meaningful juice differences into a small fair-line-equivalent adjustment where estimable.
5. Record market dispersion as uncertainty.
6. Explicitly flag disagreement around key numbers.

Outputs:
- market_fair_spread
- market_range
- market_dispersion
- Sly_minus_market_price_edge
- key_number_edge
- market_confidence

This becomes both a baseline model and a feature set for the residual model.

### Layer C — Football residual model
Target: predict **actual margin minus market-implied margin**, using only information available at the prediction timestamp.

Feature families to research/test:

#### Team efficiency
- opponent-adjusted offensive EPA/play
- opponent-adjusted defensive EPA/play
- pass EPA/dropback and pass-defense EPA
- rush EPA/carry only if it adds out-of-sample value
- offensive/defensive success rate
- explosive-play rates
- early-down efficiency
- pressure/sack/coverage features where point-in-time coverage is reliable
- special-teams contribution if stable enough

#### Quarterback
- projected starter
- rolling EPA/dropback
- CPOE
- sack/pressure response
- prior-season carryover
- starter change / backup uncertainty

#### Personnel
- snap-weighted availability changes
- OL continuity
- high-value skill/coverage absences
- explicit QB injury/start status
- uncertainty penalty for questionable/game-time decisions

Important: subjective injury "point values" do not enter the trained model unless historical point-in-time features support them. Human injury analysis may remain a separate uncertainty override while historical coverage is incomplete.

#### Schedule/context
- home/away with current-era shrinkage
- rest differential
- bye/short week
- divisional game
- neutral/international site
- travel/time-zone features
- roof/surface
- extreme weather only if validated incrementally

#### Priors / early season
Current-season samples must be shrunk strongly toward prior-season/team/QB priors early in the year. The blending rate is learned by walk-forward validation; it is not manually fixed.

### Candidate models
V2 should test several challengers, not pick one algorithm in advance:

1. **Ridge/Elastic Net residual regression** — preferred interpretable baseline; robust to correlated EPA features.
2. **Bayesian hierarchical residual model** — team/QB latent effects, explicit shrinkage and uncertainty; strong candidate for production if computationally practical.
3. **Gradient-boosted residual model** — challenger for nonlinear interactions; must beat simpler models out of sample and survive ablation/stability checks.
4. **Market-only model** — mandatory baseline.
5. **Pure fundamentals model without market features** — diagnostic baseline to measure how much the market contributes.

Model complexity must earn promotion. If ridge matches or beats boosting, use ridge.

### Layer D — Discrete margin distribution
The mean fair spread is not enough. Convert predicted fair margin into a distribution that respects NFL scoring clusters.

Primary candidate:
- empirical residual distribution conditioned/smoothed by predicted spread magnitude and game total
- discrete probabilities on integer margins
- optional kernel smoothing across neighboring spread/total buckets

Challengers:
- normal residual model (baseline only)
- Student-t residual
- direct binary ATS classifier at the target line

Outputs for each side at Sly:
- P(cover)
- P(push)
- P(loss)
- expected Monopoly net value per $100 before portfolio effects
- uncertainty interval around P(cover)

### Layer E — Calibration and uncertainty
Calibration is mandatory before V2 probabilities can size wagers.

Methods to compare using nested walk-forward validation:
- no post-hoc calibration
- Platt/sigmoid calibration
- isotonic calibration

Diagnostics:
- reliability diagrams
- calibration intercept/slope
- Brier score and decomposition
- log loss
- expected calibration error as a secondary metric
- observed cover rate by predicted edge bucket
- block-bootstrap confidence intervals

A probability should not be displayed with precision beyond what the sample can support.

### Layer F — External evidence / source reliability
SportsLine, Gridiron and Lucas remain separate from the core model initially.

For every source prediction capture:
- game
- side
- exact reference spread
- stated probability/grade/signal
- timestamp
- whether reference equals Sly
- result at source line
- result at Sly line
- closing-line value

Source influence plan:
- Phase 1: zero hard-coded weight; display + benchmark only.
- Phase 2: after adequate prospective sample, estimate incremental value conditional on market/core forecast.
- Phase 3: if incremental value is stable, introduce a shrinkage-heavy meta-model/source adjustment.

No source receives more weight simply because its recent record is hot over a tiny sample.

---

## 4. Monopoly tournament optimizer

### State
At each weekly lock the optimizer receives:
- Catherine bankroll/rank
- Amanda bankroll/rank
- all available field bankrolls/ranks
- weeks remaining
- playoff qualification/minimum-wager requirements
- payout curve (1st 56%, 2nd 25%, 3rd 10%, 4th 2%, 5th 1%; commissioner 6%)
- candidate game outcome distributions at Sly
- prediction uncertainty
- public/field-behavior model

### Decision variables
For Catherine and Amanda separately:
- which games to wager
- wager amount in $100 increments
- total weekly deployment
- overlap between entries

Constraints:
- minimum 4 games
- minimum $100 per game
- cannot exceed available Monopoly balance
- playoff-specific minimum requirements when applicable
- no arbitrary fixed game count or fixed bankroll percentage

### Primary objective
Maximize simulated **expected household prize value**:

E[payout(Catherine final rank) + payout(Amanda final rank)]

Secondary diagnostics (not substitutes for the primary objective):
- P(at least one household entry cashes)
- P(at least one top-3)
- P(at least one wins)
- P(both cash)
- P(elimination / inability to satisfy future minimums)
- median and 5th/95th percentile final balances
- household wager overlap/correlation

### Field model
We do not know every competitor's exact decision process, so V2 must not pretend we do.

Use a scenario ensemble calibrated from observed pool behavior:
- conservative field policy
- median field policy
- aggressive field policy

Update the mixture weights weekly using actual balance transitions and any known wager sheets. Optimize for robustness across scenarios rather than a single guessed opponent model.

Historical pool behavior should inform **deployment and tournament risk**, not NFL cover probabilities.

### Two-entry logic
Catherine and Amanda are optimized jointly, not independently.

Overlap is allowed when a game's robust edge is strong enough. Diversification is valuable only when it increases household prize equity; "make the entries different" is not a rule.

The optimizer may rationally choose different risk profiles when the two ranks diverge.

---

## 5. Validation design

### Historical split philosophy
No random train/test split.

Use strict walk-forward / rolling-origin evaluation:
- train only on games completed before prediction date
- feature calculations are lagged and timestamped
- retrain/re-estimate as the historical clock moves forward
- use whole weeks/seasons for bootstrap resampling because observations within a week are dependent

Suggested research windows:
- fundamentals/closing-market research can use longer nflverse history
- exact intra-week stale-line testing requires timestamped historical odds (roughly 2020+ depending on provider)
- reserve a sacred recent holdout season after model selection
- 2026 remains live shadow/prospective evidence and is not used to tune V2 on Week 3 outcomes

### Required baselines
1. market-only fair spread
2. Sly-vs-current-market price rule
3. simple EPA/ridge model
4. pure fundamentals model
5. V1/M1–M5 champion
6. simple four-source consensus heuristic

### Predictive metrics
- fair-margin MAE/RMSE
- ATS Brier score at Sly
- ATS log loss
- calibration curve/intercept/slope
- cover rate by probability bucket
- error by spread bucket and key-number region
- CLV/market movement attribution where available

### Monopoly metrics
- expected household payout
- P(any cash)
- P(top 3)
- P(1st)
- elimination probability
- expected final balances
- lower-tail balance risk
- household correlation / overlap

Return/ATS hit rate may be shown, but never as the sole promotion metric.

---

## 6. Feature ablation and tuning

Every feature family must prove incremental value.

Run ablations for:
- market features
- team EPA family
- QB family
- injuries/personnel
- rest/travel/home field
- weather
- line path
- public betting
- independent models

Promotion rule: if removing a feature family does not degrade out-of-sample probabilistic performance within uncertainty, remove or heavily shrink that family.

Hyperparameters are tuned only inside training folds. The outer fold remains untouched.

Avoid dozens of unregistered experiments. Keep an experiment registry with hypothesis, feature set, training window, result, and decision to reduce researcher degrees of freedom.

---

## 7. QA / testing requirements

### Data tests
- team-code normalization
- home/away sign convention
- spread/juice parsing
- Sly frozen-line immutability
- timestamps <= prediction timestamp
- no postgame values in feature table
- duplicate game detection
- missingness explicit, never silently imputed as neutral
- reference-line mismatch detection for external sources

### Model tests
- deterministic retraining from fixed snapshot/seed
- no future rows in rolling features
- early-season prior behavior
- probability bounds and sum rules
- push probability on integer spreads
- calibration pipeline only fit on training folds
- feature ablation reproducibility

### Monopoly tests
- cover = +1x net stake; loss = -1x; push = 0
- minimum game/bet constraints
- no wager exceeds balance
- correct payout ordering
- playoff qualification/minimum enforcement
- balance transition conservation
- joint Catherine/Amanda simulation preserves shared-game outcomes (same real NFL game result for both entries)

### Regression tests
Every production refresh should compare against the prior snapshot and flag:
- rank/pick changes
- probability changes above threshold
- source/reference changes
- wager changes
- unaffected games that changed unexpectedly

---

## 8. Champion/challenger promotion gates

V1 remains production champion until V2 passes all gates.

### Gate 1 — integrity
- zero leakage/test-contract failures
- reproducible point-in-time dataset
- no unresolved sign/reference issues

### Gate 2 — prediction
- non-inferior or better than market-only on held-out probabilistic metrics
- better than V1 on at least one primary probabilistic metric without material degradation on the others
- calibration acceptable within bootstrap uncertainty

### Gate 3 — robustness
- gains persist across seasons/folds, not one hot period
- no single tiny subgroup drives the result
- feature ablations support the claimed drivers
- challenger remains stable under reasonable parameter perturbations

### Gate 4 — Monopoly value
- tournament optimizer using V2 probabilities improves expected household prize value versus V1/fixed-percentage/flat-stake baselines across plausible field-policy scenarios
- no unacceptable increase in elimination risk unless compensated by materially higher prize equity and explicitly surfaced

### Gate 5 — shadow live
- run V1 and V2 side-by-side prospectively for multiple weeks
- predictions frozen before outcomes
- no retroactive edits

Only after these gates should V2 become production.

---

## 9. Research backlog / experiments in order

### Phase 1 — data feasibility
1. Build historical nflverse game + play-by-play + roster/depth/injury table.
2. Audit historical market fields and determine whether paid point-in-time odds access is required.
3. Reconstruct immutable prediction timestamps and feature contracts.
4. Create prospective external-source ledger for SportsLine/Gridiron/Lucas.

### Phase 2 — prediction challengers
5. Market-only baseline.
6. Ridge residual model.
7. Bayesian hierarchical residual challenger.
8. Gradient-boosting challenger.
9. Early-season prior/blending experiment.
10. Conditional discrete margin model.
11. Calibration comparison.

### Phase 3 — ablation
12. QB incremental value.
13. personnel/injury incremental value.
14. rest/travel/home/division/weather incremental value.
15. line-path incremental value.
16. public-betting incremental value.
17. external-source incremental value once sample allows.

### Phase 4 — Monopoly simulator
18. Encode exact season/payout/playoff rules.
19. Build field-policy scenario model from historical pool balance transitions.
20. Build joint Catherine/Amanda Monte Carlo simulator.
21. Optimize weekly actions in $100 increments.
22. Compare against fixed 20/30/40%, flat-stake, V1, and independent-entry strategies.

### Phase 5 — shadow production
23. Freeze V2 before each weekly result.
24. Record all probability, source and portfolio outputs.
25. Review calibration/drift weekly but tune only on scheduled research cadence, not after individual losses.

---

## 10. Explicit non-goals

V2 will **not**:
- blindly average four source opinions
- treat line movement as automatically predictive
- chase public betting percentages without validated incremental value
- assign arbitrary point values to every injury
- tune weights from Weeks 1–2
- optimize hit rate instead of calibrated probability/tournament value
- use closing information in a historical Friday prediction
- impose exactly four/five games or a fixed 30% weekly deployment
- replace V1 before the challenger passes objective gates

---

## 11. Research references / sources consulted

- Gray & Gray, *Testing Market Efficiency: Evidence From The NFL Sports Betting Market*, Journal of Finance.
- Miller & Rapach, *An intra-week efficiency analysis of bookie-quoted NFL betting lines*, Journal of Empirical Finance.
- Shank, *NFL betting market efficiency, divisional rivals, and profitable strategies*.
- nflverse / nflreadr documentation for schedules, PBP, rosters, depth charts, injuries, and market fields.
- nflverse-derived historical margin analysis documenting key-number mass at 3 and 7.
- Walsh & Joshi, *Machine learning for sports betting: Should model selection be based on accuracy or calibration?*
- Chu, Wu & Swartz, *Modified Kelly criteria*.
- Scikit-learn probability calibration documentation (reliability curves, Brier/log loss).
- The Odds API historical snapshot documentation (5/10-minute historical market snapshots, paid endpoint).
- SportsDataIO line-movement/historical odds documentation.
- Recent open walk-forward NFL forecasting implementations used as methodology references, not trusted performance evidence.

Research references justify candidate approaches; no third-party reported performance is accepted as proof that the approach works for this pool.
