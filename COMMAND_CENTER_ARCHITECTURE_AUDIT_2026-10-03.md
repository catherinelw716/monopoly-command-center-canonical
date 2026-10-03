# Command Center architecture audit — 2026-10-03

## Executive finding

The recurring update failures are caused by propagation architecture, not by missing source data. The live app currently combines a remote legacy HTML application, server-side replacement of native `games` / `sourceData` arrays, and several post-render DOM patches. The same source can therefore exist in multiple representations and a later render can erase a DOM-only update.

## Current data flow

1. `server.js` downloads the legacy base app.
2. It replaces the base app's native `games` and `sourceData` arrays with Week 4 state.
3. It merges the versioned SportsLine screenshot snapshot at runtime.
4. It injects `game-detail-ui-patch.html`, `mobile-patch.html`, `mobile-nav-fix.html`, and `week4-sportsline-integration-patch.html`.
5. Those patches decorate/rewrite specific rendered components after page load and again after some navigation events.

## Audit by source

### Sly
- Canonical contest values exist in the Week 4 state/freeze.
- They appear throughout the native game objects.
- Risk: source-specific lines must never overwrite them.
- Status: **controlled**.

### SportsLine
- Canonical screenshot snapshot: `week4-sportsline-2026-10-03-1611ET.json`.
- `server.js` merges spread/SIM metadata into runtime game/source objects.
- Money % currently lives in the deep-dive UI patch rather than the canonical SportsLine JSON.
- Numeric SIM % is only populated where verified.
- Risk: money % is still a second storage location and can drift from the source snapshot.
- Status: **partially normalized; migration needed**.

### Gridiron
- Canonical screenshot snapshot: `week4-gridiron-2026-10-03.json`.
- The same 15-game values are currently duplicated in `game-detail-ui-patch.html` and `mobile-patch.html` because the legacy app does not yet consume a unified source object directly.
- Decision Board re-renders previously erased one-time Gridiron decoration; the current board patch now uses repeated application + `MutationObserver`.
- Risk: duplicate source tables can drift.
- Mitigation added now: CI compares both hard-coded representations with the canonical JSON and fails if any game/line/% differs.
- Status: **visible but duplicated; highest-priority normalization target**.

### Lucas
- No verified Week 4 source supplied.
- Correct behavior is unavailable/unverified, not inference.
- Status: **controlled missingness**.

### Recommendations / portfolio
- Runtime `server.js` currently patches Week 4 ranking and portfolio after loading `week4-current-data.json`.
- Risk: the base JSON and runtime state can differ, so reading the file alone does not necessarily reproduce the live board.
- Status: **runtime-authoritative; should be consolidated later**.

## View audit

| View | Current implementation | Primary risk | Current control |
|---|---|---|---|
| Today | SportsLine patch rewrites summary/KPIs | stale summary after later changes | view contract + future QA |
| Recommended plays | native/legacy component + decorations | rerender can erase DOM decorations | observer/reapply logic |
| All Games | native games component + mobile patch | matching cards/rows is DOM-structure dependent | broad selectors + observer |
| Source table | SportsLine rebuilds rows; Gridiron patches column after | patch ordering | repeat application + source QA |
| Game deep dive | SportsLine panel + Gridiron panel | source duplicated in UI patch | canonical snapshot comparison QA |
| Analysis | SportsLine patch rewrites analysis | can lag later source/recommendation changes | dependency map |
| Portfolio | SportsLine patch rewrites portfolio | ranking/sizing and portfolio can diverge | portfolio included in contract |
| Lab | source provenance panel | source timestamp may lag | provenance requirement |

## Immediate controls added

- `COMMAND_CENTER_DATA_CONTRACT.md`: declares canonical source and view propagation requirements.
- `command-center-view-map.json`: machine-readable view dependency map.
- `command-center-consistency-qa.js`: checks the 15-game sets, SportsLine/ GridIron coverage, duplicate Gridiron values, required selectors/components and grade rules.
- `.github/workflows/command-center-consistency.yml`: runs consistency QA whenever relevant source/state/UI files change.

## Required migration sequence

1. Move SportsLine money % into the versioned SportsLine snapshot rather than a UI lookup table.
2. Move Gridiron into normalized runtime `game.sources.gridiron` / `sourceData` and remove both duplicated hard-coded UI maps.
3. Create one render helper for source summaries used by Decision Board, source table and deep dive.
4. Move current recommendation/portfolio reconciliation out of imperative `server.js` patches into a versioned canonical Week 4 UI state.
5. Add live DOM smoke tests for one representative game and 15/15 row coverage before deploy is called complete.

Until that migration is complete, a source update is not considered finished unless the consistency workflow passes and the required surfaces in `COMMAND_CENTER_DATA_CONTRACT.md` have been checked.
