# Week 3 Postmortem — 2026 NFL Monopoly

## Settled household result

- Catherine: 2-4 ATS, -$600, ending bankroll $10,800, rank #28.
- Amanda: 2-5 ATS, -$1,600, ending bankroll $8,700, rank #65.
- Household: -$2,200 on $6,600 of Week 3 outlay; ending bankroll $19,500.

## Final pre-lock model scorecard

The authoritative current-market V2 layer was timestamped Sep 27 at 12:01 PM ET, before the Sunday slate.

Excluding PHI @ CHI, which the UI marked LOCKED rather than decision-eligible, the model finished **11-3 ATS (78.6%)**. The top five finished **4-1**, and the A/A- group finished **4-0**.

This is strong prospective evidence for the snapshot, but it is still one week. It does not justify retraining, promotion, confidence inflation, or larger stakes by itself.

## The most important Week 3 finding: execution diverged from the final model

Of the $6,600 household outlay:

- $2,900 was placed on the same side as the final pre-lock model. Those wagers went 4-1 and produced **+$1,500**.
- $3,700 was placed on the opposite side from the final pre-lock model. Those eight entry wagers went **0-8** and produced **-$3,700**.

The opposing unique sides were CAR -2.5, SEA -7.5, CIN -3.5, BAL -3.5 and LAR -2.5. The final model preferred CLE +2.5, WAS +7.5, PIT +3.5, DAL +3.5 and DEN +2.5, respectively; every one of those final-model sides covered.

A same-stakes counterfactual that preserves every actual wager amount but flips only wagers that opposed the timestamped final model would have produced **+$5,200** for the household, ending at **$26,900**, a **$7,400 swing** versus actual Week 3 results.

That counterfactual is useful because the model snapshot existed before kickoff; it is not permission to outcome-chase. Its operational lesson is that the system needs a formal reconciliation step between the latest authoritative model view and the sides actually submitted.

## External source scorecard

Using only source signals that were actually eligible for an ATS comparison at their captured reference line:

- SportsLine captured exact ATS recommendations: **4-4**.
- Gridiron exact-Sly-line directional takes, excluding 50/50 no-takes: **4-4**.
- Lucas: **2-5** overall; LIKE 1-3, LEAN 1-2.

Week 3 therefore does not provide evidence to add mathematical SportsLine, Gridiron or Lucas weighting to V2. These remain contextual sources.

## Red-team interpretation

The biggest Week 3 failure was not the final V2 side-ranking layer. It was **decision-state inconsistency**: earlier external/context conclusions remained influential even after the authoritative pre-lock model had moved to the opposite side on several games.

Two examples are especially important:

1. CAR -2.5 had strong earlier four-source/context support, but the final 12:01 layer ranked CLE +2.5 #2 with an A- grade. The household still put $1,500 on CAR.
2. SEA -7.5 had been an earlier PLAY, but the final layer ranked WAS +7.5 #3 with an A- grade. The household still put $700 on SEA.

This means Week 4 should not simply produce more research. It should ensure that the **latest decision state actually governs the final submission** unless we deliberately override it and record why.

## Data-quality issue to resolve

The user's final wager record shows Amanda at **BUF -6**, while the Sep 27 12:01 authoritative model layer stored **BUF -7**. Buffalo won by eight, so both covered and settlement is unaffected. But this is a frozen-line provenance defect: Week 4 must have one canonical Sly-line source of truth, and every model/output layer should read from it rather than carrying its own copy.

## Week 4 actions

1. Add a pre-submit reconciliation table: final model side vs proposed Catherine/Amanda side, with explicit ALIGNED / OVERRIDE status.
2. Require an override reason and timestamp whenever we knowingly bet against the final authoritative model.
3. Continue prospective shadow scoring unchanged; do not retrain on Week 3 alone.
4. Keep SportsLine, Gridiron and Lucas contextual until a larger prospective sample supports any weighting.
5. Resolve frozen-line provenance so Sly's exact line is singular and immutable across model, Games, Analysis and Portfolio views.
6. Keep stake sizing separate from side quality. Week 3 supports better reconciliation, not automatic wager escalation.

See `v2/results/week_03_postmortem.json` for the machine-readable scorecard.
