# NFL Monopoly — Canonical Project State / Handoff

Read this file first when continuing the project in a new conversation.

**Repo:** `catherinelw716/monopoly-command-center-canonical`  
**Live Command Center:** https://monopoly-command-center-canonical.onrender.com/  
**V1 production and V2 research remain separate.**  
**Last updated:** 2026-09-27

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

## Current household state after Week 2
- Catherine: **$11,400**, rank **#30**.
- Amanda: **$10,300**, rank **#44**.
- Household: **$21,700**.
- Week 2 active field: 125 entries; 2 eliminated.
- Week 2 median: $9,500; top-10 floor $16,665; top-5 floor $19,400; leader $31,300.
- Week 1 household outlay: $6,100.
- Week 2 household outlay: $7,800.
- Week 2 household overlap was roughly 73%; this is not a rule against overlap. Shared exposure should require strong enough edge to justify concentration.

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

## V2-0010 prospective shadow — ACTIVE IN PARALLEL
Prospective validation infrastructure is implemented and QA-passed. It is supporting evidence collection, **not the primary development workstream**.

- FRIDAY_FREEZE and PRE_KICK_FINAL are separate immutable snapshots.
- Week 3 Sly Friday lines are preserved in `v2/season_2026/week_03_sly_freeze.json`.
- Do not fabricate a Friday market snapshot using later odds.
- Promotion guardrail remains >=100 settled prospective snapshots across >=6 distinct weeks plus calibration/integrity checks.

Do not spend substantial development time polishing the ledger unless a real QA defect appears.

## V2-0009 Monopoly tournament optimizer — PRIMARY WORKSTREAM / ACTIVE
This is now the highest-priority unfinished V2 layer.

Implemented:
- `v2/MONOPOLY_RULE_AUDIT.md` — focused contest-rule audit.
- `v2/monopoly_contract.json` — machine-readable contest contract.
- `v2/monopoly_simulator.py` — weekly bankroll transitions and shared-game Catherine/Amanda simulation.
- `v2/monopoly_simulator_qa.py` — wager-rule, settlement, and same-game correlation tests.
- `v2/historical_replay_wk1_wk2.json` — compact audited historical fixture.
- `v2/monopoly_historical_replay_qa.py` — replays actual Weeks 1–2 ledger math while preserving known commissioner reconciliation differences.
- GitHub V2 CI passes these tests.

Historical accounting guardrail:
- Catherine reconciles exactly in Weeks 1 and 2.
- Amanda's user-supplied wager ledger differs from commissioner authoritative balances by +$500 after Week 1 and +$100 after Week 2; keep those discrepancies explicit/quarantined rather than rewriting history.

### Immediate next V2-0009 steps
1. represent the Week 2 official field state and observed field volatility;
2. build conservative / median / aggressive field-policy scenarios without pretending opponent behavior is known exactly;
3. extend the simulator from one-week bankroll transitions to season trajectories with future viability constraints;
4. simulate Catherine and Amanda jointly with shared NFL outcomes;
5. benchmark simple policies: minimum/flat, fixed 20/30/40%, independent-entry allocation, legacy V1 heuristic;
6. optimize number of games, $100-increment wagers, total deployment, and overlap for expected household final prize value;
7. report P(any cash), P(top3), P(1st), P(both cash), future-minimum failure risk, ending-balance distribution, and household correlation.

Do not impose a fixed weekly game count or bankroll percentage. Those are optimizer outputs.

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

## Durable context files
Read in this order in a new chat:
1. `PROJECT_STATE.md`
2. `DECISIONS_LOG.md`
3. `V2_MODEL_SPEC.md`
4. `v2/experiment_registry.csv`
5. `v2/MONOPOLY_RULE_AUDIT.md` for optimizer work, or `v2/SHADOW_VALIDATION_PROTOCOL.md` for shadow work
6. latest relevant result/design/source files

Catherine can bootstrap a new conversation with:
> **Continue NFL Monopoly. Load the canonical project state from the GitHub repo first.**
