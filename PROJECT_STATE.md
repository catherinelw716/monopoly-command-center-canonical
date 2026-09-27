# NFL Monopoly — Canonical Project State / Handoff

Read this file first when continuing the project in a new conversation.

**Repo:** `catherinelw716/monopoly-command-center-canonical`  
**Live Command Center:** https://monopoly-command-center-canonical.onrender.com/  
**V2 research is isolated from production.**  
**Last updated:** 2026-09-27

## Working rules
- When Catherine says **Proceed**, execute the agreed next step.
- Keep V1 production behavior separate from V2 research.
- Never treat a successful Render deploy as proof that UI behavior or model logic is correct; inspect actual output/QA.
- Avoid broad UI changes for targeted fixes.
- Preserve source data when rolling back UI regressions.
- Do not use the word **ticket** in pool UX.
- Use `DECISIONS_LOG.md` for durable rationale and `v2/experiment_registry.csv` for model-research status.

## Core pool rules
- Weekly ATS using Sly's frozen spreads.
- Cover = net +1x wager; loss = -1x; push = 0.
- Minimum 4 games per entry/week; minimum $100/game.
- TNF is optional and issued separately Thursday; remaining lines arrive Friday.
- Payout structure: 1st 56%, 2nd 25%, 3rd 10%, 4th 2%, 5th 1%, commissioner 6%.

Before the final season simulator, reconfirm any additional playoff qualification, escalating minimum, elimination, and end-of-season rules.

## Current household state after Week 2
- Catherine: $11,400, rank #30.
- Amanda: $10,300, rank #44.
- Combined: $21,700.
- Week 2 top-10 floor: $16,665; top-5 floor: $19,400.
- Week 1 household outlay: $6,100.
- Week 2 household outlay: $7,800.
- Week 2 household overlap rose to roughly 73%; do not interpret that as a rule against overlap. Require stronger evidence for shared exposure.

## Source rules
### SportsLine
Preserve exact recommendation, grade, timestamp, and reference line. Total/ML outputs are not ATS votes.

### Gridiron
Preserve exact probability and reference spread. **50/50 = NO TAKE.** A different reference spread is not an exact Sly-line vote.

### Lucas
Independent source with LIKE / LEAN / NO TAKE.

### Cross-source table
Show **Our Model, SportsLine, Gridiron, Lucas** explicitly. V2 must not mathematically assume those are independent votes.

The exact Week 3 screenshot transcription is preserved in `source-screenshot-data-patch.html`; read that file before changing source data.

## UI guardrails
Do not reintroduce whole-document MutationObservers, repeating rewrite intervals, replacement Decision Boards, or broad mobile table rewrites. Preserve original interactive navigation/cards. Lucas should appear beside the other sources, deep dives should be visually structured, and cross-source consensus should appear after Lucas.

## V1 / V2 model status
**V1 remains production champion. V2 is research-only.**

V2 prediction and allocation remain hard-separated:
1. estimate P(cover/push/loss) at Sly's frozen spread
2. use those probabilities in the separate Monopoly tournament optimizer for Catherine/Amanda

Standings must never change the NFL cover probability itself.

### Current leading V2 historical probability architecture
The historically supported challenger is now:

**market-anchored normal cover/loss distribution + global empirical exact-margin push correction on integer spreads**

Rules:
- market remains the fair-margin anchor
- half-point spreads remain the normal market-based distribution
- on integer target spreads, estimate exact signed final-margin push probability from historical outcomes with shrinkage toward the normal push estimate
- retain the normal model's relative cover/loss odds and rescale them around the corrected push mass
- no rolling PBP football residual adjustment
- no spread-conditioning in the push layer
- no total input in the push layer
- no SportsLine/Gridiron/Lucas mathematical weight yet

This architecture is frozen for prospective validation unless a separately registered QA problem appears.

## V2 research sequence / evidence

### V2-0001 / 0002 — market vs football residual — COMPLETE
Historical seasons 2016–2025; held-out 2020–2025; 1,615 games.
- Market margin MAE: **9.764**
- Ridge football-residual MAE: **9.831**
- Market RMSE: **12.637**
- Ridge RMSE: **12.710**
- preliminary market ATS Brier: **0.2500**
- preliminary Ridge Brier: **0.2516**
- Ridge selected-side hit: **51.01%**
- market-minus-Ridge MAE delta: **-0.0665**, 95% CI **[-0.1733,+0.0313]**

Decision: market-only remains fair-margin research champion; reject first Ridge specification.

### V2-0003 — compact football-feature ablation — COMPLETE
No tested roll4/roll8/passing/EPA-success variant beat closing market on average. Best `roll8_all` still worsened MAE by 0.0366; 95% CI [-0.1159,+0.0366].

Post-hoc Weeks 1–5 / home-favorite / 3–3.5 patterns are diagnostic only and must not be used as model rules without preregistered untouched validation.

Decision: defer Bayesian/boosting complexity on the same feature family.

### V2-0006A — residual empirical discrete model — INVALID QA
Residual recentering washed out absolute key-number mass. At exact spread 3 it predicted only ~2.25% pushes versus 9.61% observed.

Decision: do not use 0006A as promotion evidence; correct the model form.

### V2-0006B — full absolute discrete model — COMPLETE
The corrected absolute-margin model represented 3/7 much better but full replacement of the normal cover/loss distribution worsened aggregate Brier.

- Normal per-game Brier: **0.515859**
- spread-conditioned full discrete: **0.517467**
- normal-minus-discrete: **-0.001606**, 95% CI **[-0.003717,+0.000573]**
- integer push predicted: normal **3.103%**, discrete **3.778%**, observed **4.020%**
- exact 3 push: normal **3.108%**, discrete **8.079%**, observed **9.613%**
- exact 7 push: normal **3.105%**, discrete **5.662%**, observed **4.825%**

Decision: reject full discrete replacement but retain the key-number signal; test a targeted hybrid.

### V2-0006C — targeted hybrid key-number model — COMPLETE / PASS
The hybrid changes only integer-line push mass and preserves normal conditional cover/loss odds.

Global hybrid vs normal:
- integer-line Brier improvement: **+0.000711**
- season-bootstrap 95% CI: **[+0.000289,+0.001098]**
- broader all-offset metric also improved
- five of six held-out 2020–2025 seasons improved

Spread-conditioned hybrid was numerically similar but did not robustly beat global (direct CI crossed zero).

Decision: prefer simpler **global hybrid**.

### V2-0006D — independent older-era robustness replication — COMPLETE / PASS
Architecture frozen from 0006C. Data 2006–2019 only; outer held-out 2010–2019; 2,560 games; offsets expanded to ±3 points.

- integer-line Brier improvement: **+0.000627**
- season-bootstrap 95% CI: **[+0.000390,+0.000876]**
- positive held-out seasons: **10/10**
- all-offset improvement: **+0.000319**
- all-offset 95% CI: **[+0.000198,+0.000450]**
- exact spread 3 push: normal **2.895%**, hybrid **7.391%**, observed **8.586%**

Decision: historical replication passed. Freeze the global hybrid architecture and stop retrospective model-form tuning on this component.

Relevant result files:
- `v2/EXPERIMENT_001_002_RESULTS.md`
- `v2/DIAGNOSTIC_ABLATION_RESULTS.md`
- `v2/EXPERIMENT_0006_DESIGN.md`
- `v2/EXPERIMENT_0006B_DESIGN.md`
- `v2/EXPERIMENT_0006B_RESULTS.md`
- `v2/EXPERIMENT_0006C_DESIGN.md`
- `v2/EXPERIMENT_0006C_RESULTS.md`
- `v2/EXPERIMENT_0006D_DESIGN.md`
- `v2/EXPERIMENT_0006D_RESULTS.md`

## V2-0010 prospective shadow — ACTIVE
The prospective infrastructure is now implemented and QA-passed.

### Frozen model artifact
`v2/model_artifacts/v2_global_hybrid_2016_2025.json`

- model version: `V2-0006C-global-hybrid-r1`
- artifact hash: `da2b587b06a91d05834a92ed5d2dc6cc42ba7d38069d8d0e7f73b94a71617026`
- training seasons: 2016–2025
- training games: 2,639
- residual mean: 0.0375142099
- residual sigma: 12.7173713390
- selected global push shrink: 75

The artifact was independently regenerated on Render and the logged artifact hash matched the committed artifact.

### Shadow infrastructure
- `v2/SHADOW_VALIDATION_PROTOCOL.md`
- `v2/shadow_model.py`
- `v2/fit_shadow_model.py`
- `v2/shadow_ledger.py`
- `v2/capture_shadow_snapshot.py`
- `v2/validate_shadow_ledger.py`
- `v2/settle_shadow_results.py`
- `v2/score_shadow_ledger.py`
- `v2/shadow_pipeline_qa.py`
- `v2/shadow_event_schema.json`
- `v2/shadow_snapshot_template.json`
- `v2/shadow/README.md`

The ledger is append-only JSONL with a SHA-256 hash chain. Prediction events are rejected at/after kickoff. FRIDAY_FREEZE and PRE_KICK_FINAL are unique per-game snapshot keys. Results are separate settlement events. CI verifies probability integrity, timing rejection, duplicate rejection, and tamper detection.

No reconstructed historical prediction rows were inserted. The live ledger will begin only with a genuinely prospective capture.

### Promotion guardrail
Do not consider replacing V1's probability layer before at least:
- **100 settled prospective snapshots**, and
- **6 distinct NFL weeks**, and
- intact ledger integrity, and
- hybrid Brier improvement over the frozen normal baseline without material log-loss/calibration deterioration.

This floor is not a guarantee of power; continue shadowing if uncertainty remains.

## Immediate next V2 operating step
At the next valid slate:
1. capture Sly's frozen spread and a timestamped market observation in a **FRIDAY_FREEZE** batch
2. include V1 and SportsLine/Gridiron/Lucas context exactly as observed when available
3. before each kickoff, capture a separate **PRE_KICK_FINAL** batch at the unchanged Sly spread and latest verified market line
4. append results only after games are final
5. run `score_shadow_ledger.py`; do not retune architecture from individual results

This is now an operating evidence-collection phase, not another retrospective model-search phase.

## Future reminders
1. **Historical intra-week odds:** revisit paid timestamped history when rigorous Friday-Sly-freeze to Sunday-market testing is reached. Do not fabricate this from opener/close data.
2. **Full pool-rule audit:** revisit playoff/minimum/elimination/end-of-season details before the final Catherine/Amanda tournament simulator.

## New-conversation bootstrap
Catherine can say:
> **Continue NFL Monopoly. Load the canonical project state from the GitHub repo first.**

Then read, in order:
1. `PROJECT_STATE.md`
2. `DECISIONS_LOG.md`
3. `V2_MODEL_SPEC.md` for architecture/background
4. `v2/experiment_registry.csv`
5. latest relevant V2 result/design file or `v2/SHADOW_VALIDATION_PROTOCOL.md`
6. relevant UI/source files for app changes
