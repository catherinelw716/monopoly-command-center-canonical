# Week 4 Adaptive Layer — Weeks 1–3 Learnings

Status: Step 4 complete. This layer adapts process, source interpretation and optimizer stress behavior without retraining the frozen V2 NFL probability model.

## What changed for Week 4

1. **Frozen V2 remains frozen.** Week 3's 11–3 prospective result is retained as evaluation evidence only. It does not change coefficients, confidence calibration or stake sizing by itself.
2. **External sources remain zero-weight in the prediction equation.** Week 3 exact-line scorecards were SportsLine 4–4, Gridiron 4–4 and Lucas 2–5. Weeks 1–2 do not have a canonical exact-line prospective source ledger, so no retrospective source record is manufactured.
3. **Market disagreement now changes edge interpretation.** Week 4 model outputs are classified as MARKET_EQUAL, SOURCE_SENSITIVE or SOURCE_DISPUTED. A single favorable live source cannot create a fully confirmed stale-line edge.
4. **Final-decision reconciliation is mandatory.** The latest timestamped model snapshot is the baseline. Opposite-side wagers require an explicit OVERRIDE reason/evidence/timestamp; a Sly-line mismatch is blocking.
5. **Optimizer stress behavior is tougher.** Source-sensitive edges must survive a zero-edge stress case; source-disputed games are evaluated under each preserved market source separately; finalist portfolios must report overlap, downside/CVaR retention and future-minimum failure risk.
6. **Historical deployment is diagnostic, not a fixed target.** Household outlay was $6,100 in Week 1, $7,800 in Week 2 and $6,600 in Week 3. Same-side household overlap was about 42.6%, 73.1% and 45.5%, respectively. These observations inform comparisons but do not become a bankroll-percentage rule.
7. **Legacy V1 / M1–M5 are not fabricated.** The repo contains hard-coded Week 3 UI outputs and a fixed legacy V1 portfolio comparator, but no generic reproducible Week 4 implementation. Until those formulas are recovered or redesigned, they remain legacy diagnostics rather than invented Week 4 model rows.

## Why this is the right adaptation

The main Week 3 failure was execution-state divergence: $2,900 of wagers aligned with the final pre-lock model went 4–1 for +$1,500, while $3,700 placed opposite the final model went 0–8 for -$3,700. That is strong evidence for improving reconciliation and auditability, but only one week of evidence for the model itself.

The adaptive layer therefore changes **how evidence is interpreted and acted on**, not the underlying NFL probability coefficients. This preserves the prospective V2 experiment while fixing the operational behavior that failed in Week 3.

## Week 4 handoff to Step 5

Step 5 should now refresh injuries, QB status, roster/news, weather, SportsLine, Gridiron and Lucas for all 15 games. Those contextual inputs remain separate from the frozen V2 probabilities, but they can affect confidence, red-team flags, and later explicit OVERRIDE rationale.
