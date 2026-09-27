# NFL Monopoly — Decisions Log

Append material model/product decisions here. `PROJECT_STATE.md` is the current-state handoff; this file preserves why major choices were made.

## 2026-09-27 — V1 remains Champion; V2 is Challenger
Decision: Do not replace production V1 merely because V2 exists. V2 must pass data-integrity, predictive, calibration/robustness, Monopoly-value, and prospective-shadow gates.

Why: The existing model has useful domain logic but insufficiently learned weights/calibration. Replacing it without evidence would trade one unvalidated system for another.

## 2026-09-27 — Separate prediction from portfolio optimization
Decision: V2 has two hard-separated layers:
1. NFL P(cover/push/loss) at Sly's frozen spread.
2. Monopoly tournament allocation across Catherine/Amanda.

Why: Standings/risk strategy should change wager size and diversification, never the underlying probability that an NFL side covers.

## 2026-09-27 — Market-anchored residual architecture
Decision: Start from robust multi-book fair market and model residual error rather than predicting games from scratch.

Why: Market is a strong information aggregator; football features must prove incremental predictive value beyond it.

## 2026-09-27 — Discrete margin model required
Decision: Model integer NFL scoring margins/key-number mass rather than assume all half-points have equal value.

Why: 3 and 7 are disproportionately common margins. Sly +3.5 vs market +3 is materially different from +5.5 vs +5.

## 2026-09-27 — External sources are benchmarks first, weights later
Decision: SportsLine, Gridiron, and Lucas remain explicit external sources but receive no automatic equal-vote mathematical weighting in V2.

Why: Signals are correlated and native reference lines differ. Weight must be earned prospectively as incremental value conditional on the core model.

## 2026-09-27 — No fixed weekly game count or bankroll percentage
Decision: Four-game minimum and $100 minimum are constraints, not optimization targets. Number of games, deployment %, and overlap are outputs of the tournament optimizer.

Why: Optimal concentration changes with slate quality, probability uncertainty, Catherine/Amanda standings, and field state.

## 2026-09-27 — Joint household objective
Decision: Optimize Catherine and Amanda jointly for expected household prize value, with P(any cash), P(top 3), P(1st), elimination risk, and correlation as diagnostics.

Why: Two entries belong to one household; independent optimization can create unnecessary duplication or miss beneficial overlap.

## 2026-09-27 — Strict walk-forward validation
Decision: No random game-level train/test split. Use only information available at each historical prediction timestamp.

Why: Prevent look-ahead leakage from future games, closing lines, injury news, or post-lock market information.

## 2026-09-27 — Feature ablation is mandatory
Decision: Team EPA, QB, injuries, travel/rest, weather, line path, public betting, and external models must each demonstrate incremental out-of-sample value.

Why: Plausible football narratives are not enough to justify model weight.

## 2026-09-27 — nflverse spread sign normalization
Decision: Preserve raw nflverse `spread_line`, but normalize V2 home-team sportsbook convention explicitly after QA: conventional home favorite is negative; nflverse schedule examples encode home favorite with positive `spread_line`.

Why: An unnoticed sign reversal would invalidate the model and ATS targets.

## 2026-09-27 — Friday freeze and pre-kick are separate snapshots
Decision: V2 maintains a FRIDAY_FREEZE state and PRE_KICK_FINAL state.

Why: Sly's frozen line creates a structural stale-price opportunity while the normal market continues to absorb information.

## 2026-09-27 — Do not fabricate historical stale-line testing
Decision: Exact Friday-to-Sunday historical line-path research requires timestamped market snapshots. If paid historical data is unavailable, test general model historically and stale-line behavior prospectively.

Why: Opening/closing lines cannot faithfully reconstruct the information set that existed at a specific Friday/Sunday timestamp.

## 2026-09-27 — Durable handoff context
Decision: `PROJECT_STATE.md` is the canonical new-chat bootstrap and should be updated after material changes. `DECISIONS_LOG.md` records major rationale.

Why: Conversation context can truncate or change across chats; repository-backed context is explicit, durable, and auditable.

## 2026-09-27 — First Ridge football-residual challenger rejected
Decision: Keep the closing-market model as the research champion baseline. Reject the first Ridge specification (lagged roll4/roll8 PBP efficiency + basic context) as evidence of incremental predictive value.

Evidence: 1,615 held-out regular-season games across 2020–2025. Market mean margin MAE 9.764 vs Ridge 9.831; market RMSE 12.637 vs Ridge 12.710; preliminary Brier 0.2500 vs Ridge 0.2516. Market-minus-Ridge MAE delta -0.0665 with season-bootstrap 95% interval [-0.1733,+0.0313]. Ridge selected-side hit rate was 51.01%.

Why: The football-residual feature set did not beat the market out of sample. This supports the market-anchored design and the rule that plausible football variables receive no weight until they demonstrate stable incremental value.

Next consequence: run registered roll-window/feature-family ablations before adding Bayesian or boosting complexity. If those also fail, keep the core more market-centric and focus V2 research on exact Sly price/key-number/discrete-margin value rather than trying to forecast final margin better than the closing market.
