# Implementation Plan: Week 4 Full Refresh

## Overview
Execute the approved Week 4 refresh as a gated pipeline. Each step must complete and be reviewed before the next begins. The official Sly Week 4 sheet is the immutable target-line source; all market/model/context/optimizer/UI work remains downstream of it.

## Architecture decisions
- `v2/season_2026/week_04_sly_freeze.json` is the only canonical Week 4 Sly line source.
- Prior-week outcomes update evaluation, source tracking, optimizer/risk logic, and execution safeguards; they do not opportunistically refit the frozen V2 probability challenger.
- Market, football probability, contextual-source, tournament-optimization, and UI layers stay separate and timestamped.
- Any proposed wager opposite the latest authoritative model requires an explicit override reason and timestamp.

## Task list
1. Freeze and audit official Sly slate.
2. Build complete Week 4 market-history dataset.
3. Refresh football probability/model layer across all eligible games.
4. Apply Weeks 1–3 learnings to adaptive evaluation/decision/optimizer layers.
5. Complete external/context research for every game.
6. Generate four-source consensus and contradiction layer.
7. Run adversarial Week 4 model review.
8. Run Catherine/Amanda Monopoly optimizer with Week 3 bankroll/field state.
9. Run pre-submit reconciliation gate.
10. Refresh Command Center end-to-end.
11. QA the Friday refresh across data/model/UI surfaces.
12. Capture and execute a separate Sunday PRE_KICK_FINAL refresh.

## Checkpoints
- Checkpoint A after Tasks 1–7: full 15-game data/model board ready for review.
- Checkpoint B after Tasks 8–9: Catherine/Amanda portfolio and reconciliation ready for review.
- Checkpoint C after Tasks 10–11: Command Center Friday build ready for review.

## Risks and mitigations
| Risk | Impact | Mitigation |
|---|---|---|
| Sly line drift across files | High | Canonical loader + exact Week 4 audit assertions + CI validation |
| Market-source disagreement | High | Preserve source/timestamp provenance and stress disputed edges |
| Outcome chasing from Week 3 | High | Keep V2 architecture frozen; update only evaluation/decision layers |
| Stale earlier context overrides final model | High | Pre-submit ALIGNED/OVERRIDE reconciliation |
| UI shows stale Week 3 state | High | End-to-end canonical Week 4 refresh + cross-view QA |

## Review protocol
Do not proceed to the next numbered task until the user reviews the completed current task.
