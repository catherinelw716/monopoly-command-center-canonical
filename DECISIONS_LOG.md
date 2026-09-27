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

## 2026-09-27 — Compact football-feature ablations also rejected
Decision: Keep the market-only fair-margin model as the V2 research champion. Do not advance Bayesian or gradient-boosting complexity on the same rolling PBP feature family. Prioritize discrete empirical margin/key-number probability modeling next.

Evidence: Six compact Ridge variants were tested under the same walk-forward framework. The best was `roll8_all`, but it still worsened average margin MAE by 0.0366 points versus market (season-bootstrap 95% CI [-0.1159,+0.0366]); selected-side ATS hit was 52.09%. Passing-only, roll4-only, combined roll4+8, and EPA/success variants all also failed to beat market on average.

Diagnostic-only observations: the best variant showed positive post-hoc MAE gains in Weeks 1–5 (+0.0619), home-favorite games (+0.0589), and closing spreads 3–3.5 (+0.0524), with corresponding selected-side hit rates of 55.19%, 53.55%, and 55.76%. These were discovered after inspecting the data and are explicitly not model-tuning evidence.

Why: Searching for more complexity after simpler versions fail would invite overfitting. V2's more promising structural advantage is likely accurate exact-line probability/value—especially around key numbers and Sly's frozen number—rather than generic attempts to out-predict the closing market on final margin.

## 2026-09-27 — Residual-based discrete-margin implementation rejected by QA
Decision: Mark V2-0006A invalid for promotion evidence rather than interpreting its failure as evidence that NFL discreteness is unhelpful.

Why: 0006A modeled recentered market residuals, which washed out absolute final-margin mass at key numbers. At exact spread 3 it predicted only about 2.25% pushes versus 9.61% observed. That violated the structural purpose of the experiment.

Consequence: rerun the registered question using actual integer final margins, not recentered residual mass.

## 2026-09-27 — Full empirical discrete replacement rejected; key-number signal retained
Decision: Do not replace the normal market-based cover/loss distribution with the full empirical discrete distribution. Preserve the evidence that exact integer scoring-margin mass improves push calibration.

Evidence: V2-0006B normal per-game Brier was 0.515859 versus 0.517467 for spread-conditioned discrete. Normal-minus-discrete difference -0.001606 with 95% CI [-0.003717,+0.000573]. However integer push calibration improved from 3.103% to 3.778% versus 4.020% observed; exact spread 3 improved from 3.108% predicted push to 8.079% versus 9.613% observed, and exact 7 from 3.105% to 5.662% versus 4.825% observed.

Consequence: test a narrow hybrid that changes only integer-line push mass while preserving normal conditional cover/loss odds.

## 2026-09-27 — Global hybrid key-number correction advances
Decision: The leading V2 historical probability architecture is now **market-based normal cover/loss plus a global empirical exact-margin correction to push probability on integer spreads**. Half-point spreads remain normal. Do not add spread-conditioning or total to this layer.

Evidence: V2-0006C global hybrid improved integer-line Brier versus normal by +0.000711 with season-bootstrap 95% CI [+0.000289,+0.001098], and improved the all-offset safety metric. The spread-conditioned version was numerically similar, but its direct advantage over global had a CI crossing zero; complexity was not earned. Five of six held-out 2020–2025 seasons improved.

Why: This targets the one structural defect that consistently showed evidence—NFL exact-margin/key-number mass—without degrading the market's stronger cover/loss information.

## 2026-09-27 — Global hybrid passes independent-era robustness replication
Decision: Freeze the global hybrid architecture for prospective 2026 shadow validation. Stop retrospective architecture tinkering on this component unless a preregistered QA problem emerges.

Evidence: V2-0006D evaluated 2,560 held-out games across 2010–2019 using no 2020+ outcomes and a wider ±3-point target range. Normal-minus-hybrid integer Brier improvement was +0.000627 with 95% CI [+0.000390,+0.000876]; all 10 held-out seasons improved. The all-offset improvement was +0.000319 with 95% CI [+0.000198,+0.000450].

Why: The same narrow mechanism replicated across a distinct historical era and larger line-offset range. Further retrospective tuning now risks converting validation into optimization.

Next consequence: V2-0010 is prospective-only. Freeze predictions before outcomes, capture Sly Friday and pre-kick market snapshots separately, and evaluate without retroactive model edits. V1 remains production champion.

## 2026-09-27 — V2-0010 shadow ledger is append-only and model artifact is frozen
Decision: Begin prospective shadow capture using a committed frozen artifact and an append-only SHA-256 hash-chained event ledger. Do not insert reconstructed historical prediction rows.

Frozen artifact: `v2/model_artifacts/v2_global_hybrid_2016_2025.json`
- model version: `V2-0006C-global-hybrid-r1`
- artifact hash: `da2b587b06a91d05834a92ed5d2dc6cc42ba7d38069d8d0e7f73b94a71617026`
- training seasons: 2016–2025
- training games: 2,639
- residual mean: 0.0375142
- residual sigma: 12.7173713
- global push shrink: 75

Integrity controls: prediction captures are rejected at/after kickoff; FRIDAY_FREEZE and PRE_KICK_FINAL are unique snapshot keys per game; final results are appended as separate settlement events; any historical event edit breaks the hash chain; deterministic CI QA verifies probability sums, integer/half-point push handling, duplicate rejection, timing rejection, and tamper detection.

Promotion guardrail: do not consider V2 probability-layer promotion before at least 100 settled prospective snapshots across at least 6 distinct NFL weeks, and only if hybrid Brier improves over the frozen normal baseline without material log-loss/calibration deterioration.

Why: After historical replication, the primary risk is no longer finding another retrospective variation—it is contaminating prospective evidence. The ledger makes the future evaluation auditable and keeps stale-line research point-in-time.
