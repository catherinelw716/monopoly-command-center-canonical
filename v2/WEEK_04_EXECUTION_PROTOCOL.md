# Week 4 Execution Protocol — NFL Monopoly

Status: **ACTIVE PRE-WEEK PREP**

This protocol implements the operational lesson from the Week 3 postmortem without changing the frozen NFL probability architecture.

## 1. Canonical Sly line source

For Week 4, there must be exactly one committed `week_04_sly_freeze.json` source of truth once Sly's lines are supplied.

Every downstream model, optimizer, Games view, Analysis view and Portfolio view must read the same `sly_home_spread` from that file. No UI patch or downstream artifact may carry a conflicting copied line.

If the submitted wager screenshot later differs from the canonical freeze, preserve the discrepancy explicitly rather than silently rewriting history.

## 2. Snapshot sequence

1. Capture Sly's frozen lines.
2. Capture `FRIDAY_FREEZE` market/model snapshot where point-in-time evidence is available.
3. Run the frozen V2 probability layer.
4. Run the Monopoly optimizer separately from prediction.
5. Refresh injuries/news/weather/external context as appropriate.
6. Capture `PRE_KICK_FINAL` before kickoff.
7. Generate proposed Catherine/Amanda portfolios.
8. Run `pre_submit_reconciliation.py` before treating the portfolio as final.

The final authoritative model state is the baseline for reconciliation. Earlier recommendations remain history/context and cannot silently override it.

## 3. Reconciliation statuses

Each proposed wager receives one of two directional statuses:

- `ALIGNED` — proposed team matches the final authoritative model side.
- `OVERRIDE` — proposed team is the opposite side.

An `OVERRIDE` is allowed only when both `override_reason` and `override_timestamp` are recorded. This is an audit requirement, not a ban on human judgment.

The reconciliation step also validates the canonical Sly spread. A conflicting `sly_home_spread` is a blocking `LINE_MISMATCH`.

## 4. What can justify an override

Examples include newly verified late injury/inactive information, a documented source update after the model snapshot, or a deliberate tournament-diversification decision. The reason must identify what changed or why the portfolio objective warrants the decision.

External sources remain contextual. Week 3 SportsLine and Gridiron exact ATS samples were each 4-4 and Lucas was 2-5; that one week does not support mathematical weighting into V2.

## 5. Stake sizing remains separate

Week 3 does not justify larger wagers because the final model happened to perform well. The optimizer's uncertainty/risk objective remains a separate design problem. Reconciliation controls **which side we knowingly submit**, not how much to wager.

## 6. Current bankroll entering Week 4

- Catherine: $10,800, rank #28.
- Amanda: $8,700, rank #65.
- Household: $19,500.

These standings may affect tournament allocation but may never change NFL cover probabilities.

## 7. Field-state caution

The supplied Week 3 standings screenshot is sufficient to confirm the household balances/ranks and visible upper-field anchors, but the full active-entry count / complete distribution is not preserved in the current artifact. Do not fabricate a complete Week 3 field ledger. Keep the existing field-scenario assumptions until sufficient official Week 3 aggregate anchors are captured for a clean replacement.

## 8. Week 4 success criterion

Before final submission, there should be no unexplained difference between:
- canonical Sly line,
- final model side,
- proposed Catherine/Amanda side,
- recorded override state.

This closes the decision-state inconsistency exposed in Week 3 while preserving human agency and model/optimizer separation.
