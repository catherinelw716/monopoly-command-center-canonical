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
- [ ] Week 4 External Context QA workflow passes
- [ ] User reviews Task 5 before Task 6 begins

- [ ] Task 6: Generate four-source/contradiction layer
- [ ] Task 7: Run adversarial model review

## Checkpoint A
- [ ] Full 15-game data/model board reviewed

- [ ] Task 8: Run Catherine/Amanda Monopoly optimizer
- [ ] Task 9: Run pre-submit reconciliation gate

## Checkpoint B
- [ ] Portfolio and sizing reviewed

- [ ] Task 10: Refresh Command Center end-to-end
- [ ] Task 11: QA Friday refresh

## Checkpoint C
- [ ] Command Center Friday build reviewed

- [ ] Task 12: Sunday PRE_KICK_FINAL refresh
