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
- [ ] User reviews Task 2 before Task 3 begins

- [ ] Task 3: Refresh football probability/model layer
- [ ] Task 4: Apply Weeks 1–3 learnings to adaptive layers
- [ ] Task 5: Complete external/context research
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
