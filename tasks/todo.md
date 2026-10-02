# Week 4 Refresh Tasks

- [x] Task 1: Freeze and audit official Sly slate
  - [x] Verify all 15 Sunday/Monday games against the supplied sheet
  - [x] Confirm home/away orientation, kickoff times, and spread signs
  - [x] Preserve PIT @ CLE as excluded because the Friday sheet has no spread
  - [x] Add canonical loader/validation so downstream work cannot silently substitute a different Sly line
  - [x] Add CI coverage for the canonical freeze

## Checkpoint: Task 1
- [x] Canonical freeze validation passes
- [x] User reviews Task 1 before Task 2 begins

- [x] Task 2: Build complete Week 4 market-history dataset
  - [x] Capture opening spread and opening total for all 15 eligible games
  - [x] Preserve Sly spread alongside source-specific Friday current lines
  - [x] Capture VegasInsider Friday consensus spread/total and Action Network Friday spread cross-check
  - [x] Calculate Current - Sly DIFF by source and opening-to-current movement
  - [x] Flag key-number movement and source disagreement rather than collapsing conflicting lines
  - [x] Add deterministic completeness/orientation/DIFF QA and dedicated CI

## Checkpoint: Task 2
- [x] 15/15 eligible games have complete Step-2 market-history records
- [x] Week 4 Market History QA workflow passes
- [x] User reviews Task 2 before Task 3 begins

- [x] Task 3: Refresh football probability/model layer
  - [x] Run frozen V2 against all 15 Sly lines using VegasInsider current market
  - [x] Run source-sensitivity pass using Action Network current market
  - [x] Preserve opening-line model output as movement diagnostic only
  - [x] Preserve empirical push correction on integer Sly lines
  - [x] Classify MARKET_EQUAL, SOURCE_SENSITIVE_SAME_DIRECTION, and SOURCE_DISPUTED_DIRECTION states
  - [x] Add reproducible runner, checked-in result database, deterministic QA, and dedicated CI
  - [x] Audit legacy V1/M1-M5 reproducibility and explicitly refuse to fabricate missing Week-4 model outputs

## Checkpoint: Task 3
- [x] 15/15 eligible games have fresh Week-4 model rows
- [x] Week 4 Model Layer QA workflow passes
- [x] User reviews Task 3 before Task 4 begins

- [x] Task 4: Apply Weeks 1–3 learnings to adaptive layers
  - [x] Preserve V2 coefficients and calibration; Week 3 result does not trigger retraining or stake escalation
  - [x] Record Week 3 prospective source scorecards with zero prediction weight
  - [x] Encode Week 1–3 household deployment and overlap as diagnostics, not fixed targets
  - [x] Add MARKET_EQUAL / SOURCE_SENSITIVE / SOURCE_DISPUTED interpretation policy
  - [x] Make final-model reconciliation and explicit OVERRIDE metadata mandatory
  - [x] Strengthen optimizer stress rules for source-sensitive/disputed edges, overlap, CVaR, and future-minimum risk
  - [x] Preserve legacy V1/M1-M5 as non-reproducible diagnostics rather than fabricating Week 4 outputs
  - [x] Add deterministic adaptive-state QA and dedicated CI

## Checkpoint: Task 4
- [x] Weeks 1–3 learnings encoded without contaminating frozen Week 4 probabilities
- [x] User reviews Task 4 before Task 5 begins

- [x] Task 5: Complete external/context research
  - [x] Capture official injury/QB context for all 15 eligible games
  - [x] Capture weather context/materiality for all 15 eligible games
  - [x] Preserve major Friday statuses including Daniels out, Jets skill/OL absences, Panthers starters out, 49ers injury volume, and Jefferson out
  - [x] Audit SportsLine public Week 4 access without inferring paywalled ATS picks
  - [x] Mark Gridiron Week 4 pickset unverified where no authoritative public table was found
  - [x] Mark Lucas Week 4 pickset unverified until supplied/verified
  - [x] Add deterministic context completeness/source-honesty QA and dedicated CI

## Checkpoint: Task 5
- [x] 15/15 eligible games have injury, QB, and weather context
- [x] Week 4 External Context QA workflow passes
- [x] User reviews Task 5 before Task 6 begins

- [x] Task 6: Generate four-source/contradiction layer
  - [x] Build 15-game Our Model / SportsLine / Gridiron / Lucas source table
  - [x] Count only verified ATS sides at known reference lines as source votes
  - [x] Preserve inaccessible SportsLine, unverified Gridiron, and unavailable Lucas as missing rather than NO TAKE votes
  - [x] Treat MARKET_EQUAL and SOURCE_DISPUTED model states as NO ROBUST TAKE
  - [x] Surface model-vs-market and context-vs-market contradictions without converting context into a fifth vote
  - [x] Preserve HOU -3 and SEA -7 as the only current robust model directions, both source-sensitive
  - [x] Add deterministic no-fake-consensus QA and dedicated CI

## Checkpoint: Task 6
- [x] 15/15 eligible games have a four-source/contradiction row
- [x] Week 4 Four Source QA workflow passes
- [x] User reviews Task 6 before Task 7 begins

- [x] Task 7: Run adversarial model review
  - [x] Challenge the board from market-maker, quant, statistician, methodology, personnel, injury/news, and portfolio-risk lenses
  - [x] Preserve frozen V2 probabilities and zero external-source weights
  - [x] Stress-test HOU -3 and SEA -7 as source-sensitive rather than broad-market edges
  - [x] Elevate IND -3.5 to high-priority Sunday market watch without converting context into a model vote
  - [x] Preserve NE-BUF and DEN-SF as source-disputed holds
  - [x] Define Sunday refresh triggers for all 15 games
  - [x] Add deterministic adversarial-review QA and dedicated CI

## Checkpoint A
- [x] Full 15-game data/model board assembled and adversarially reviewed
- [x] User reviews Checkpoint A before Task 8 begins

- [x] Task 8: Run Catherine/Amanda Monopoly optimizer
  - [x] Start from Catherine $10,800 / Amanda $8,700 and Week 3 field anchors
  - [x] Limit Friday sizing edges to conditional HOU -3 and SEA -7
  - [x] Stress HOU/SEA through a zero-edge case and 1.00/0.75/0.50/0.25/0.00 edge shrink
  - [x] Keep NE-BUF, DEN-SF and IND-WAS source-disputed rather than promoting them to Friday sizing edges
  - [x] Evaluate selected portfolio under VegasInsider-full and Action-full probability states
  - [x] Compare shared, hybrid, and split household overlap structures
  - [x] Compare against simple benchmark portfolios
  - [x] Report current-week CVaR retention and future-minimum failure risk
  - [x] Persist provisional Friday optimizer artifact and pass dedicated CI
- [ ] Task 9: Run pre-submit reconciliation gate

## Checkpoint B
- [ ] Portfolio and sizing reviewed

- [ ] Task 10: Refresh Command Center end-to-end
- [ ] Task 11: QA Friday refresh

## Checkpoint C
- [ ] Command Center Friday build reviewed

- [ ] Task 12: Sunday PRE_KICK_FINAL refresh
