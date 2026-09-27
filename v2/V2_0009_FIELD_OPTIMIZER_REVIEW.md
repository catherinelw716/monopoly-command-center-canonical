# V2-0009 — Field Ensemble / Joint Optimizer Milestone Review

Status: **IMPLEMENTED / RED-TEAM HOLD AT OBJECTIVE DECISION**  
Date: 2026-09-27

## Scope completed

The agreed V2-0009 milestone is now implemented end to end:

1. Week-2 field state represented from the canonical aggregate anchors without fabricating an individual commissioner ledger.
2. Conservative / median / aggressive field-policy scenarios implemented as an explicit ensemble.
3. Season trajectories implemented through the remaining regular season and confirmed $3,000 late-season/playoff viability constraints.
4. Catherine and Amanda simulated jointly with shared NFL outcomes on overlapping games.
5. Frozen benchmark controls evaluated against the same field paths and random process.
6. Joint optimizer searches entry-specific deployment, game count, $100-increment stake allocation, and household overlap.
7. Rank/prize metrics now exist: expected household prize share, P(any cash), P(top 3), P(1st), P(both cash), future-minimum failure risk, ending-balance distribution, deployment, and overlap.
8. Deterministic optimizer QA is in V2 CI and passes together with the existing simulator, historical replay, benchmark, shadow-ledger, and data-pipeline checks.

Primary implementation files:
- `v2/season_2026/week_02_field_state.json`
- `v2/season_2026/week_03_optimizer_proxy.json`
- `v2/monopoly_tournament_optimizer.py`
- `v2/monopoly_tournament_optimizer_qa.py`
- `v2/run_v2_0009_milestone.py`

## Field ensemble assumptions

The canonical handoff preserves aggregate Week-2 anchors, not all 125 individual opponent balances. The simulator therefore interpolates an opponent balance envelope from known anchors rather than pretending reconstructed balances are factual.

Default field scenarios are intentionally broad and equally weighted while only two weeks of pool behavior exist:

| Scenario | Mean deployment | Mean games | Common-week volatility |
|---|---:|---:|---:|
| Conservative | 22% | 4.5 | 2.5 pp |
| Median | 36% | 5.5 | 3.5 pp |
| Aggressive | 52% | 6.5 | 5.0 pp |

The field model is a tournament-risk model only. It never changes NFL cover probabilities.

## Benchmark layer

The preregistered simple controls remain frozen:
- minimum 4x$100
- equal top-4 at 30%
- flat 20% / 30% / 40% over positive-edge games
- quarter-Kelly control
- deliberately diversified 30% household pair
- identical top-4 30% pair
- fixed Week-3 legacy V1 portfolio comparator

In the 600-simulation-per-scenario CI execution, the strongest frozen control was `diversified_pair_30pct`, with expected household prize share about **0.01249**. This number is a mechanics/proxy diagnostic, not production evidence.

## Proxy execution input — important limitation

Week 3 does not have a valid contemporaneous robust multi-book V2 market-fair snapshot preserved for this optimizer exercise. To execute the mechanics without inventing a Friday snapshot, `week_03_optimizer_proxy.json` uses the existing canonical current-line snapshot only as a **single-source execution proxy**.

This proxy is explicitly:
- not a V2-0010 prospective prediction snapshot;
- not the robust multi-book fair market required by the V2 probability specification;
- not sufficient for a Week-3 wager recommendation;
- not promotion evidence for either the prediction layer or the optimizer.

Most proxy market lines equal Sly. The dominant apparent stale-price difference is PHI @ CHI, where the proxy current line is CHI +3.5 while Sly is CHI +4.5. This causes the reduced market-anchored probability model to concentrate heavily on that one proxy edge.

## Red-team sequence and result

The first optimizer search allowed deployment through 50% of bankroll. The selected solution hit the 50% upper boundary on both entries. That was treated as a search-design defect rather than a conclusion.

The search was widened to 80%. The selected solution again hit the upper boundary on both entries, with substantially greater modeled future-minimum failure risk.

The final search was widened to the actual contest boundary of 100%. The selected proxy solution was:
- Catherine: 100% deployment, 4 games, shared household game set;
- Amanda: 100% deployment, 4 games, shared household game set;
- overlap mode: `shared`;
- modeled expected household prize share: **0.03551**;
- modeled P(any cash): **0.16611**;
- modeled future-minimum failure risk: **0.47222**.

The exact proxy stakes concentrate nearly the entire bankroll on PHI @ CHI because of the one-point proxy stale-line edge. They are **not** a recommendation and should never be copied into the Command Center as such.

### Stress tests of the selected proxy corner

The all-in corner remained directionally favored by the pure expected-prize objective across the tested assumptions:

| Stress | Expected household prize share | P(any cash) | Future-minimum failure risk |
|---|---:|---:|---:|
| Equal scenario weights | 0.03551 | 0.16611 | 0.47222 |
| Conservative-heavy field | 0.04280 | 0.18183 | 0.47433 |
| Aggressive-heavy field | 0.02934 | 0.15333 | 0.46983 |
| Lower-tail floor $5,000 | 0.03372 | 0.15444 | 0.47222 |
| NFL edge shrunk to 25% | 0.03461 | 0.16167 | 0.49333 |

These are low-resolution Monte Carlo diagnostics from a proxy execution, not calibrated production estimates.

## Adversarial conclusion

The search no longer has an artificial deployment ceiling: it reaches the actual 100% contest boundary. Therefore the all-in result is not an unfinished grid-search problem.

However, it also does **not** demonstrate that the complex joint optimizer has earned deployment. A post-hoc simple 100%-deployment/shared/top-4 control is contained within the optimizer search and collapses to the same corner. The apparent gain over the frozen 20/30/40% controls is therefore primarily a statement about the current **objective + uncertainty treatment**, not evidence that sophisticated two-entry portfolio logic itself adds value.

The red team identifies three reasons the current proxy optimum cannot be promoted:

1. **Probability-input uncertainty is not internalized by the objective.** Probability shrinkage is currently a stress diagnostic; it does not make the optimizer pay for uncertainty when selecting stakes.
2. **Expected prize value alone strongly rewards tail variance in a top-heavy contest.** The same run accepts roughly 47% household future-minimum failure risk to raise modeled top-tail prize equity.
3. **The Week-3 probability input is only a single-source execution proxy.** The dominant edge is therefore not strong enough evidence to support real stake sizing.

## Genuine decision point

V2-0009 has reached the point where coding more search range is not the right next action. The next design choice must be explicit:

- preserve pure expected household prize value as the sole optimization objective, knowingly permitting very high ruin/viability risk when the model thinks tail upside compensates for it; **or**
- make robustness/uncertainty decision-relevant inside the optimizer (for example, optimize a robust/lower-confidence objective or constrain acceptable future-minimum failure risk) while retaining expected household prize value as the headline metric.

Do not impose an arbitrary risk cap silently. This choice changes the definition of the optimizer and should be recorded as a product/model decision.

Separately, actual Week-3 stake recommendations still require a valid point-in-time V2 probability input. The proxy run must not be treated as that input.
