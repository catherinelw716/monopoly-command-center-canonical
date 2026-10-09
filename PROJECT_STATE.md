# NFL Monopoly — Canonical Project State / Handoff

## CURRENT STATE — 2026-10-09 · WEEK 5 · CATHERINE ONLY

**Live target:** https://monopoly-command-center-canonical.onrender.com/
**Canonical Week 5 data:** `week05-canonical-data.json`
**Immutable Week 5 Sly Friday freeze:** `v2/season_2026/week_05_sly_freeze.json`
**Official all-111-player Week 4 standings:** `week05-standings.json`
**Week 5 server / UI / challenger:** `server-week05.js`, `week05-command-center.html`, `week05-model.js`.
**Deployment notice:** GitHub update is not proof of live Render deployment; verify `/_version`, `/healthz`, and `/api/week5` after deployment. Current deployment status must be checked independently.

- User explicitly changed scope to **Catherine solo**. No joint Catherine/Amanda wagering, portfolio optimization, or exposure in active dashboards. Old household research is historical only.
- Commissioner Week 4 balance: Catherine **$12,800; rank #17 (+11 places)**, 111 active, leader $31,700, tied #10 $14,000.
- Catherine Week 4 submitted Oct 4: IND −3.5 $2,000 W; DET −3.5 $500 L; ARI −2.5 $500 L; LV +4.5 $500 W; LAR −3.5 $300 W; MIA +10.5 $200 W.
- IMPORTANT settlement: **Cover net +1× wager, loss −1×, push 0** (a cover receives total 2× *including returned stake*, not net +2×). Week4 outlay $4,000, record 4–2, net **+$2,000**, Week3 official bankroll **$10,800** → Week4 **$12,800**.
- Week 5 has 14 upcoming games plus already-completed TB @ DAL Thursday (TB 24–16). Sly's Thursday spread is not provided; never infer it.
- Oct9 ~5:53pm ET market consensus used as dated market snapshot; not a promise of executable prices.
- Frozen V2 challenger `V2-0006C-global-hybrid-r1` is **not promoted**; Week5 predictions derive from market-to-Sly price gaps plus frozen push model, not injury-adjusted football forecasts.
- No Week5 independently verified SportsLine exact-line ATS, GridironAI exact-line ATS, Lucas take, complete money handle/ATS trends/Defensive EPA series, or complete game-time weather forecasts. UI MUST label these missing and never transfer Week4 signals to Week5.
- Dedicated five-criteria page exists but grades MUST remain unverified until full inputs validated. Five factors remain Line Movement, ATS Trends, Money/Handle, Defensive EPA, and Key Numbers.
- Week5 draft portfolio is a local what-if calculator, not a validated prize-equity optimizer or final wager recommendation.
- The earlier October 1 snapshot below is preserved for V2 audit **but is superseded by this block for current player balances and scope**.

---

Read this file first when continuing the project in a new conversation.

**Repo:** `catherinelw716/monopoly-command-center-canonical`  
**Live Command Center:** https://monopoly-command-center-canonical.onrender.com/  
**V1 production and V2 research remain separate.**  
**Last updated:** 2026-10-01

## North star
Build the best possible NFL probability engine for **Sly's exact frozen spread**, validate it rigorously, then use those probabilities in a **Monopoly-specific joint Catherine/Amanda tournament optimizer**.

Do not let UI work, shadow-ledger plumbing, or rule-edge-case auditing displace the highest-priority unfinished model layer.

Before any substantial V2 task, check:
1. Does this advance prediction quality, prospective validation, source validation, or Monopoly optimization?
2. Is it the highest-priority unfinished layer?
3. Are we solving the model problem rather than polishing supporting infrastructure?

## Core pool rules
- Every entry started **Week 1 with $10,000**.
- Weekly ATS using Sly's frozen spreads.
- Cover = net +1x wager; loss = -1x; push = 0.
- Minimum 4 games per entry/week; minimum $100/game; $100 increments.
- TNF is optional and issued separately Thursday; remaining lines arrive Friday.
- Non-Thursday wagers are submitted together after Friday lines; bets can be changed before kickoff.
- Payouts: 1st 56%, 2nd 25%, 3rd 10%, 4th 2%, 5th 1%, commissioner 6%.

Confirmed later-season constraints exist but should **not dominate early-season optimization**:
- Week 18 qualification threshold: $3,000 remaining balance.
- Wild Card: 6 games x $500 minimum each.
- Divisional: 4 games x $750 minimum each.
- Conference Championship: 2 games x $1,500 minimum each.
- Super Bowl: $3,000 minimum.
- Only balance entering a playoff weekend is available to wager during that weekend.

See `v2/MONOPOLY_RULE_AUDIT.md`. Minor administrative edge cases remain parameterized until they become decision-relevant.

## Current household state after Week 3
- Catherine: **$10,800**, rank **#28**.
- Amanda: **$8,700**, rank **#65**.
- Household: **$19,500**.
- Week 3 household outlay: **$6,600**.
- Week 3 household net: **-$2,200**.
- Week 3 entry-bet record: **4-9 ATS**.
- Commissioner Week 3 leader: **$26,700**.
- Visible Week 3 top-5 floor: **$19,000**; visible top-10 floor: **$14,900**.
- Do not fabricate a complete Week 3 opponent ledger or active-entry count from the supplied screenshot. The optimizer may continue using the existing explicit field-scenario assumptions until a clean full-field replacement is available.

Historical outlay:
- Week 1 household outlay: $6,100.
- Week 2 household outlay: $7,800.
- Week 3 household outlay: $6,600.

## Prediction layer — current V2 status
**V1 remains production champion. V2 remains challenger/research.**

Prediction and allocation are hard-separated:
1. estimate P(cover/push/loss) at Sly's frozen spread;
2. separately optimize Monopoly allocation for Catherine/Amanda.

Standings never change NFL cover probabilities.

### Frozen V2 historical probability challenger
Current supported architecture:

**market-anchored normal cover/loss distribution + global empirical exact-margin push correction on integer spreads**

- rolling PBP residual Ridge features were tested and rejected;
- compact roll4/roll8/passing/EPA variants also failed to beat market;
- full discrete replacement was rejected;
- targeted integer push correction passed modern held-out testing and independent older-era replication;
- no SportsLine/Gridiron/Lucas mathematical weight yet.

Frozen artifact: `v2/model_artifacts/v2_global_hybrid_2016_2025.json`  
Model version: `V2-0006C-global-hybrid-r1`  
Artifact hash: `da2b587b06a91d05834a92ed5d2dc6cc42ba7d38069d8d0e7f73b94a71617026`

For detailed evidence read `v2/experiment_registry.csv`, `DECISIONS_LOG.md`, and the 0006 result files.

## Week 3 postmortem — SETTLED
See `v2/WEEK_03_POSTMORTEM.md` and `v2/results/week_03_postmortem.json`.

The authoritative Sep 27 12:01 PM ET pre-lock V2 decision layer finished **11-3 ATS** on 14 decision-eligible games. The top five finished **4-1** and the A/A- group finished **4-0**. This is one prospective week and is **not** sufficient to retrain, promote, inflate confidence, or escalate stakes.

The dominant failure was decision-state inconsistency:
- $2,900 of household outlay aligned with the final model and went 4-1 for +$1,500.
- $3,700 opposed the final model and went 0-8 for -$3,700.
- Opposite-side submitted positions were CAR -2.5, SEA -7.5, CIN -3.5, BAL -3.5, and LAR -2.5; the final model preferred CLE +2.5, WAS +7.5, PIT +3.5, DAL +3.5, and DEN +2.5.
- A same-stakes side-flip counterfactual using the timestamped final model would have produced +$5,200, a $7,400 swing versus actual Week 3. Treat this as an operational reconciliation lesson, not an outcome-chasing model claim.

External source Week 3 scorecards did not justify mathematical weighting:
- SportsLine exact ATS: 4-4.
- Gridiron exact-Sly directional takes, excluding 50/50: 4-4.
- Lucas: 2-5.

Frozen-line provenance defect preserved for audit: Amanda's submitted record shows **BUF -6** while the canonical Week 3 Sly/model freeze stores **BUF -7**. Both covered; settlement is unaffected. Week 4 must use a singular frozen-line source of truth.

## Week 4 execution controls — IMPLEMENTED
See `v2/WEEK_04_EXECUTION_PROTOCOL.md`.

New guardrail artifacts:
- `v2/pre_submit_reconciliation.py`
- `v2/pre_submit_reconciliation_qa.py`
- `.github/workflows/v2-pre-submit-reconciliation.yml`

Policy:
- one canonical committed Week 4 Sly freeze is the source of truth for all downstream layers;
- final authoritative model side is the decision baseline;
- proposed Catherine/Amanda wagers are marked `ALIGNED` or `OVERRIDE`;
- any opposite-side wager requires `override_reason` + `override_timestamp`;
- a conflicting frozen Sly line is a blocking `LINE_MISMATCH`;
- this control does not alter NFL probabilities or automatically increase/decrease stakes.

## V2-0010 prospective shadow — ACTIVE IN PARALLEL
Prospective validation infrastructure is implemented and QA-passed. It is supporting evidence collection, **not the primary development workstream**.

- FRIDAY_FREEZE and PRE_KICK_FINAL are separate immutable snapshots.
- Week 3 Sly Friday lines are preserved in `v2/season_2026/week_03_sly_freeze.json`.
- Do not fabricate a Friday market snapshot using later odds.
- Promotion guardrail remains >=100 settled prospective snapshots across >=6 distinct weeks plus calibration/integrity checks.
- Continue Week 4 shadow scoring unchanged; do not tune the architecture from Week 3 outcomes.

Do not spend substantial development time polishing the ledger unless a real QA defect appears.

## V2-0009 Monopoly tournament optimizer — PRIMARY WORKSTREAM / ROBUSTNESS LAYER IMPLEMENTED
The agreed field-scenario -> benchmark -> joint optimizer -> robustness milestone is implemented and CI-passing.

Implemented:
- `v2/MONOPOLY_RULE_AUDIT.md` — focused contest-rule audit.
- `v2/monopoly_contract.json` — machine-readable contest contract.
- `v2/monopoly_simulator.py` / QA — weekly bankroll transitions and shared-game household outcomes.
- `v2/historical_replay_wk1_wk2.json` / QA — audited historical replay.
- `v2/BENCHMARK_HARNESS_DESIGN.md` and `v2/benchmark_strategies.py` / QA — frozen simple controls.
- `v2/season_2026/week_02_field_state.json` — official aggregate Week-2 field anchors plus explicit unobserved-field assumptions.
- `v2/monopoly_tournament_optimizer.py` — conservative/median/aggressive field ensemble, season trajectories, future-minimum viability, rank/prize calculation, joint Catherine/Amanda optimizer.
- `v2/monopoly_robust_optimizer.py` — robust objective over field scenarios and probability-edge shrink states.
- `v2/monopoly_tournament_optimizer_qa.py` — deterministic field/optimizer QA.
- `v2/run_v2_0009_milestone.py` — benchmark, optimization, and robustness/red-team execution harness.
- `v2/run_week3_sunday_robust.py` — Sunday current-market robust evaluation harness.
- `v2/V2_0009_FIELD_OPTIMIZER_REVIEW.md` — original milestone findings.
- GitHub V2 CI passes all optimizer and pre-existing research checks.

Historical accounting guardrail:
- Catherine reconciles exactly in Weeks 1 and 2.
- Amanda's user-supplied wager ledger differs from commissioner authoritative balances by +$500 after Week 1 and +$100 after Week 2; keep those discrepancies explicit/quarantined rather than rewriting history.

### Field model policy
- Do **not** pretend the individual opponent ledger is known when only aggregate anchors are preserved.
- Interpolate a rank-preserving opponent envelope from official anchors only for simulation.
- Default field-policy ensemble is conservative / median / aggressive and equally weighted until more field transitions are observed.
- Field behavior changes tournament risk/allocation, never NFL probabilities.

### Robust objective decision — implemented
The red-team finding that pure expected prize value drove both entries to 100% deployment was addressed by making robustness and future viability decision-relevant **without imposing an arbitrary bankroll cap**.

The robust optimizer evaluates every candidate across:
- conservative / median / aggressive field scenarios; and
- 100% / 75% / 50% / 25% retained NFL directional edge.

For each stress state it uses viability-adjusted prize utility and entry-level current-week CVaR retention. It maximizes the worst stress-state utility, then uses average robust utility, base prize value, lower failure risk, stronger current-week capital retention, and lower deployment as tie-breakers.

Stake sizing remains a separate unresolved design problem. Week 3 strengthens the case for better final decision reconciliation; it does not by itself justify higher deployment.

## Source handling rules
### SportsLine
Preserve exact recommendation, grade/type, timestamp, and reference line. Total/ML outputs are not ATS votes.

### Gridiron
Preserve probability and native spread. **50/50 = NO TAKE.** A different reference spread is not an exact Sly-line vote.

### Lucas
Independent external source: LIKE / LEAN / NO TAKE.

### Cross-source display
Show Our Model, SportsLine, Gridiron, and Lucas explicitly, but do not mathematically treat correlated sources as independent votes.

## UI guardrails
- Do not reintroduce broad MutationObservers/repeating rewrite intervals or replacement Decision Boards.
- Preserve original navigation/cards.
- Avoid broad UI changes for targeted fixes.
- Never claim Render deployment proves rendered browser behavior.
- Do not use the word `ticket` in pool UX.

## Future reminders
1. **Historical intra-week odds access:** revisit paid timestamped odds when rigorous retrospective Friday-Sly-freeze -> Sunday-market testing becomes worth the cost. Do not reconstruct it from opener/close alone.
2. Minor playoff administrative edge cases should be confirmed only when they become material to optimizer output; do not let them derail current development.
3. When Week 4 Sly lines arrive, create the canonical `week_04_sly_freeze.json` first, then run model/optimizer/reconciliation from that single source.

## Durable context files
Read in this order in a new chat:
1. `PROJECT_STATE.md`
2. `DECISIONS_LOG.md`
3. `V2_MODEL_SPEC.md`
4. `v2/WEEK_03_POSTMORTEM.md`
5. `v2/WEEK_04_EXECUTION_PROTOCOL.md`
6. `v2/experiment_registry.csv`
7. `v2/V2_0009_FIELD_OPTIMIZER_REVIEW.md`
8. `v2/MONOPOLY_RULE_AUDIT.md` for rules, or `v2/SHADOW_VALIDATION_PROTOCOL.md` for shadow work
9. latest relevant result/design/source files

Catherine can bootstrap a new conversation with:
> **Continue NFL Monopoly. Load the canonical project state from the GitHub repo first.**
