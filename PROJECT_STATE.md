# NFL Monopoly — Canonical Project State / Handoff

Read this file first when continuing the project in a new conversation.

**Repo:** `catherinelw716/monopoly-command-center-canonical`  
**Live Command Center:** https://monopoly-command-center-canonical.onrender.com/  
**V2 research service:** https://monopoly-v2-research.onrender.com/  
**V2 ablation service:** https://monopoly-v2-ablation.onrender.com/  
**Last updated:** 2026-09-27

## Working rules
- When Catherine says **Proceed**, execute the agreed next step.
- Keep V1 production behavior separate from V2 research.
- Never treat a successful Render deploy as proof that UI behavior is correct.
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

V2 architecture is defined in `V2_MODEL_SPEC.md`:
1. point-in-time data spine
2. market fair-line engine
3. football residual model
4. discrete margin distribution
5. calibration/uncertainty
6. external-source reliability
7. Monopoly simulator
8. joint Catherine/Amanda decision layer

Prediction quality and pool-allocation logic remain separate. Standings must not change an NFL cover probability.

## V2 research infrastructure
Completed files include:
- `V2_MODEL_SPEC.md`
- `V2_DATA_FEASIBILITY.md`
- `v2/data_contract.json`
- `v2/build_historical_dataset.py`
- `v2/build_baseline_features.py`
- `v2/qa_checks.py`
- `v2/experiment_registry.csv`
- `v2/external_source_ledger.csv`
- `v2/run_first_experiment.py`
- `v2/research_requirements.txt`
- `v2/EXPERIMENT_001_002_RESULTS.md`
- `v2/run_diagnostic_ablation.py`
- `v2/DIAGNOSTIC_ABLATION_RESULTS.md`
- `.github/workflows/v2-research-ci.yml`

Important QA finding: nflverse `spread_line` has the opposite sign convention from conventional sportsbook display. V2 normalizes it to conventional home-team perspective before modeling.

## First V2 walk-forward experiment — COMPLETE
Historical seasons: 2016–2025. Held-out seasons: 2020–2025. Held-out games: 1,615. No 2026 outcomes used.

Comparison: closing-market baseline vs leakage-safe Ridge residual model using lagged 4-game/8-game PBP efficiency plus basic context.

Results:
- Market margin MAE: **9.764**
- Ridge margin MAE: **9.831**
- Market RMSE: **12.637**
- Ridge RMSE: **12.710**
- Preliminary market ATS Brier: **0.2500**
- Preliminary Ridge Brier: **0.2516**
- Ridge selected-side hit rate: **51.01%**
- Market-minus-Ridge MAE delta: **-0.0665**
- Season-bootstrap 95% interval: **[-0.1733, +0.0313]**

Decision: **market-only remains the research champion baseline; reject the first Ridge feature specification as evidence of incremental predictive value.**

## V2 diagnostic football-feature ablation — COMPLETE
The follow-up ablation tested whether a smaller/cleaner football feature set could rescue the residual-model hypothesis before adding more complexity.

Variants:
- roll8_all: MAE improvement **-0.0366**, 95% CI [-0.1159,+0.0366], selected-side hit 52.09%
- passing_only: -0.0475, CI [-0.1597,+0.0228], hit 50.51%
- roll4_all: -0.0539, CI [-0.1216,+0.0117], hit 51.52%
- epa_success_no_rest: -0.0646, CI [-0.1707,+0.0268], hit 50.82%
- roll4_plus_roll8: -0.0665, CI [-0.1733,+0.0315], hit 51.01%
- epa_success_with_rest: -0.0665, CI [-0.1733,+0.0315], hit 51.01%

**Decision:** No tested compact rolling football feature family beat the closing-market baseline on average. Market-only remains the V2 fair-margin research champion. Bayesian and gradient-boosting challengers on this same feature family are deferred rather than used to mine for an edge.

### Post-hoc diagnostic signals — NOT model rules
The best variant (`roll8_all`) showed some positive subgroups:
- Weeks 1–5: n=471; MAE gain +0.0619; selected-side hit 55.19%
- Home favorites: n=963; MAE gain +0.0589; selected-side hit 53.55%
- Closing spreads 3–3.5: n=393; MAE gain +0.0524; selected-side hit 55.76%

These patterns were discovered after inspecting the results and are therefore **hypothesis-generating only**. Do not tune V2 around them without a separately preregistered test on untouched/prospective data.

See `v2/DIAGNOSTIC_ABLATION_RESULTS.md`, `DECISIONS_LOG.md`, and `v2/experiment_registry.csv`.

## Immediate next V2 step
Registered experiment **V2-0006** is now the next priority:

### Discrete empirical margin / key-number probability model
Goal: stop trying to beat the closing market on generic final-margin prediction and instead improve the conversion from a fair market line into **P(cover), P(push), P(loss)** at an exact target spread.

Research focus:
1. empirical integer margin distribution rather than normal approximation
2. conditioning by fair spread / spread magnitude
3. conditioning by game total where sample supports it
4. explicit probability mass at key margins such as 3 and 7
5. strict walk-forward construction so the margin distribution for each test season uses prior seasons only
6. compare against the normal-residual probability baseline using ATS Brier/log loss and push/key-number calibration
7. preserve market-only fair line as the starting mean unless a future football feature challenger actually earns incremental value

If the discrete model improves exact-line probabilities, that becomes a much more relevant foundation for Monopoly because Sly's frozen line frequently differs from the later market at key numbers.

## Future reminders
1. **Historical intra-week odds:** revisit paid timestamped history when rigorous Friday-Sly-freeze to Sunday-market testing is reached. Do not block core research on this now.
2. **Full pool-rule audit:** revisit playoff/minimum/elimination/end-of-season details before the final simulator.

## New-conversation bootstrap
Catherine can say:
> **Continue NFL Monopoly. Load the canonical project state from the GitHub repo first.**

Then read, in order:
1. `PROJECT_STATE.md`
2. `DECISIONS_LOG.md`
3. `V2_MODEL_SPEC.md` for V2 work
4. `v2/experiment_registry.csv` and the latest V2 result file
5. relevant UI/source files for app changes
