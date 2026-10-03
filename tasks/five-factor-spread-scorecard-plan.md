# Implementation Plan: Five-Factor Spread Scorecard

## Overview

Build `/spread-scorecard` as a standalone challenger-analysis page that grades every Monopoly-eligible Sly spread across five transparent factors: line movement, ATS trends, verified money/handle %, defense, and NFL key numbers. The page will rank all eligible games, show a 0-100 heuristic score and grade, and explain the case for and against each side in plain English.

This work is intentionally isolated from the existing Week 4 refresh plan in `tasks/plan.md`. It must not overwrite, close, or reinterpret unfinished tasks in that plan. The Five-Factor page remains observational/challenger-only and does not feed V2, the main recommendation ranking, or the Catherine/Amanda optimizer.

Source spec: `FIVE_FACTOR_SPREAD_SCORECARD_SPEC.md`.

## Architecture Decisions

1. **Sly remains immutable.** The only spread being graded is the canonical Sly contest spread. Market opener/current lines are evidence, never replacements.
2. **Raw data, scoring, and rendering are separate layers.** Source snapshots feed a normalized scorecard object; the UI renders that object and never recomputes factor scores.
3. **Scoring rules are preregistered before Week 4 results are viewed.** Exact rule tables for defense, trends, key numbers, movement, caps, and missing-data behavior must be committed before live scorecard rankings are generated.
4. **Money means handle.** A field cannot satisfy the Money factor unless the source explicitly identifies it as money/handle/dollars, with timestamp and reference spread. Bets/tickets may be shown as separate context but never substituted.
5. **Every factor retains provenance.** Source-backed inputs carry source, capture timestamp, reference line where applicable, and quality/staleness flags.
6. **Grade and confidence are distinct.** The numeric score determines the raw grade; completeness, stale data, line mismatch, and contradictions may cap the displayed grade/confidence.
7. **The page is a challenger, not a vote.** Agreement with the main Command Center is displayed after the scorecard is computed independently.
8. **Prospective tracking is required.** Store weekly scorecard outputs before games kick off so later evaluation can test the framework without retroactive tuning.

## Dependency Graph

```text
Approved feature spec
        │
        ▼
Scoring/config contract ───────────────┐
        │                              │
        ▼                              │
Source-backed Week 4 inputs            │
(market/trends/money/defense)          │
        │                              │
        └──────────────┬───────────────┘
                       ▼
              Normalization + engine
                       │
                       ▼
                Canonical snapshot
                       │
          ┌────────────┴────────────┐
          ▼                         ▼
      Focused QA                Page renderer
          │                         │
          └────────────┬────────────┘
                       ▼
             Runtime/nav integration
                       │
                       ▼
               End-to-end QA/deploy
                       │
                       ▼
              Prospective evaluation
```

## Phase 1 — Lock deterministic scoring before looking at outputs

### Task 1: Create preregistered scorecard configuration

**Description:** Convert the approved qualitative rules into one explicit deterministic configuration used by the engine and QA. This includes exact numeric mappings for ATS win rates/sample sizes, defense tiers by spread magnitude, key-number hooks/crossings, line-movement direction/magnitude, grade bands, alignment thresholds, and confidence caps.

**Acceptance criteria:**
- [ ] One versioned config defines all five factor rules and key-number frequencies.
- [ ] Neutral is 10/20 for each factor and no live-game-specific exceptions exist.
- [ ] Defense and key-number rules are fully numeric, not prose-only.
- [ ] Missing/stale/mismatched data behavior is deterministic.

**Verification:**
- [ ] Review config against `FIVE_FACTOR_SPREAD_SCORECARD_SPEC.md`.
- [ ] Confirm no team/game names appear in the scoring thresholds.
- [ ] Confirm configured factor maximums remain equal at 20 points each.

**Dependencies:** Approved spec.

**Files likely touched:**
- `five-factor-scorecard-config.json`
- `FIVE_FACTOR_SPREAD_SCORECARD_SPEC.md` only if clarification is required

**Estimated scope:** Small.

### Task 2: Build deterministic scoring engine with unit fixtures

**Description:** Implement pure functions for each factor and overall grading. Inputs are normalized source records; outputs include both side scores, lean, raw evidence, quality flags, explanation tokens, overall score, grade, alignment, completeness, and confidence cap.

**Acceptance criteria:**
- [ ] Each factor returns 0-20 per side and deterministic lean/quality metadata.
- [ ] Line movement correctly handles favorite strengthening, favorite weakening, and favorite flips.
- [ ] Money rejects ticket/bet-only records.
- [ ] Overall score, alignment, grade, and caps are reproducible from inputs.

**Verification:**
- [ ] Fixture: favorite -2 to -7 favors favorite strongly.
- [ ] Fixture: favorite -7 to -2 favors underdog strongly.
- [ ] Fixture: +3.5 / -2.5 key-number protection is scored in the intended direction.
- [ ] Fixture: missing handle % triggers the configured grade cap.

**Dependencies:** Task 1.

**Files likely touched:**
- `five-factor-scorecard-engine.js`
- `five-factor-scorecard-fixtures.json`
- `five-factor-scorecard-engine-qa.js`

**Estimated scope:** Medium.

### Checkpoint A — Scoring contract

- [ ] Exact scoring rules are inspectable before Week 4 game outputs are generated.
- [ ] Engine fixture QA passes.
- [ ] No output has been tuned to make a preferred Week 4 team rank higher.

## Phase 2 — Build trustworthy factor inputs

### Task 3: Build Week 4 source snapshot for market movement and key-number context

**Description:** Reuse canonical Sly and existing market-history data where trustworthy, but preserve source-specific opener/current lines and timestamps. Normalize each team-side line so movement direction is unambiguous. Key-number inputs are derived from Sly plus current/open market values, not manually entered scores.

**Acceptance criteria:**
- [ ] All 15 eligible games have immutable Sly plus source-backed opener/current market records or explicit unavailable flags.
- [ ] Movement is normalized per team and source disagreement is retained rather than averaged away.
- [ ] Key-number comparisons use Sly and source-specific market lines with no sign/orientation ambiguity.

**Verification:**
- [ ] 15/15 game identity/orientation audit.
- [ ] Automated check that no market line overwrites Sly.
- [ ] Spot-check at least one favorite-strengthening and one favorite-weakening example.

**Dependencies:** Task 1.

**Files likely touched:**
- `five-factor-scorecard-data-week04.json`
- existing market snapshot only if a corrected versioned snapshot is required
- `five-factor-scorecard-data-qa.js`

**Estimated scope:** Medium.

### Task 4: Add ATS trend inputs with sample-size/staleness metadata

**Description:** Capture H2H ATS, current-season ATS, and recent ATS for both teams in every eligible matchup. The snapshot must include sample size and date range so the Trends factor can downweight stale or tiny samples deterministically.

**Acceptance criteria:**
- [ ] Every game has H2H/current-season/recent ATS records or an explicit unavailable state.
- [ ] H2H includes meeting count and season/date range.
- [ ] Current-season/recent records explicitly expose overlap risk early in the season.
- [ ] No record is presented as strong evidence solely because of a 1-0 sample.

**Verification:**
- [ ] Completeness audit for all 15 games.
- [ ] Recalculate a sample ATS percentage from raw W-L-P counts.
- [ ] Confirm stale H2H flags propagate into score confidence.

**Dependencies:** Task 1.

**Files likely touched:**
- `five-factor-scorecard-data-week04.json`
- `five-factor-scorecard-data-qa.js`

**Estimated scope:** Small/Medium.

### Task 5: Add verified money/handle inputs and defensive rankings

**Description:** Capture spread money/handle % only from sources that explicitly identify dollar/handle share, preserving exact reference spread and timestamp. Separately capture current-season defensive EPA/play rank through the latest completed week, with source and through-week metadata.

**Acceptance criteria:**
- [ ] Money records use an explicit `metricType: handle` (or equivalent governed enum), never inferred from tickets.
- [ ] Every handle observation includes source, timestamp, side percentages, and reference spread.
- [ ] If verified handle is unavailable, the record is `Unavailable`; no substitute is inserted.
- [ ] All 32 teams represented in eligible games have current defensive EPA/play rank or explicit unavailable status.

**Verification:**
- [ ] Schema test rejects `metricType: tickets` as Money-factor evidence.
- [ ] Handle percentages sum to approximately 100 when source semantics require complementary sides.
- [ ] Defensive ranks are unique/valid within source methodology and carry a through-week marker.
- [ ] Existing SportsLine `money_pct` is not automatically trusted for this page unless its handle semantics and provenance are independently verified.

**Dependencies:** Task 1.

**Files likely touched:**
- `five-factor-scorecard-data-week04.json`
- `five-factor-scorecard-data-qa.js`

**Estimated scope:** Medium.

### Checkpoint B — Data integrity

- [ ] Every eligible game has five factor inputs or explicit unavailable states.
- [ ] Money-vs-ticket semantics are verified by schema and source provenance.
- [ ] Data-quality QA passes before any scorecard ranking is produced.

## Phase 3 — Generate canonical Week 4 scorecard

### Task 6: Normalize all inputs and generate the Week 4 scorecard snapshot

**Description:** Run the deterministic engine against the verified Week 4 source snapshot and materialize one `fiveFactor` object per game. Generate plain-English `whyThisSide` and `whatArguesAgainst` text from structured factor outputs, not hand-authored team-specific prose.

**Acceptance criteria:**
- [ ] 15/15 eligible games receive all five factor objects plus `overall`.
- [ ] Overall totals exactly equal component sums.
- [ ] Displayed grade respects all confidence caps.
- [ ] Plain-English explanation references only evidence present in the canonical object.
- [ ] Main-system agreement badge is computed after, not inside, five-factor scoring.

**Verification:**
- [ ] `node five-factor-scorecard-qa.js` passes.
- [ ] No `undefined`, `null`, or `[object Object]` in generated display fields.
- [ ] Independently recompute at least three game totals from raw factor scores.

**Dependencies:** Tasks 2-5.

**Files likely touched:**
- `five-factor-scorecard-engine.js`
- `five-factor-scorecard-data-week04.json`
- `five-factor-scorecard-week04.json`
- `five-factor-scorecard-qa.js`

**Estimated scope:** Medium.

### Task 7: Run adversarial data/scoring review

**Description:** Challenge the generated board for sign errors, stale trend misuse, line-reference mismatch, money/ticket confusion, defense-orientation mistakes, key-number double counting, correlated market factors, and misleading plain-English claims. Findings must be fixed in source/config/engine rather than patched in the UI.

**Acceptance criteria:**
- [ ] Every substantive issue is classified as data defect, scoring defect, accepted trade-off, or non-issue.
- [ ] No UI workaround is used to conceal an upstream data/scoring defect.
- [ ] Correlation between line movement and money is explicitly disclosed on the page/methodology.

**Verification:**
- [ ] Re-run focused engine/data/scorecard QA after any fix.
- [ ] Freeze a pre-page scorecard snapshot only after review passes.

**Dependencies:** Task 6.

**Files likely touched:**
- `five-factor-scorecard-week04.json`
- source/config/engine files only if review identifies a defect
- `FIVE_FACTOR_SPREAD_SCORECARD_SPEC.md` only for accepted design clarification

**Estimated scope:** Small/Medium.

### Checkpoint C — Scorecard ready for UI

- [ ] Canonical 15-game ranking exists independently of page code.
- [ ] Adversarial review completed.
- [ ] Scorecard is still isolated from V2/optimizer.

## Phase 4 — Build the standalone page

### Task 8: Build `/spread-scorecard` presentation

**Description:** Create a plain-English page with a ranked scan table followed by one card per eligible game. Each card shows Sly, opener/current market, overall lean/score/grade/alignment, five factor sections, raw evidence/source/timestamp, why the side is favored, what argues against it, and the main-system agreement badge.

**Acceptance criteria:**
- [ ] Top table shows all 15 eligible games and all five factor directions.
- [ ] Every game card explains the recommendation without requiring model jargon.
- [ ] Missing/unavailable data is visibly labeled and reflected in grade confidence.
- [ ] Page renderer reads only canonical scorecard objects; it does not calculate scores.

**Verification:**
- [ ] Desktop and mobile layout check.
- [ ] Representative game with five populated factors renders correctly.
- [ ] Representative game with an unavailable factor renders `Unavailable`, never blank/undefined.
- [ ] Compare three rendered cards byte-for-value with canonical snapshot fields.

**Dependencies:** Checkpoint C.

**Files likely touched:**
- `five-factor-scorecard-page.html`
- `server-v7.js`
- `COMMAND_CENTER_DATA_CONTRACT.md`

**Estimated scope:** Medium.

### Task 9: Add navigation, runtime health contract, and cross-view QA

**Description:** Add a direct, persistent navigation entry to `/spread-scorecard`, expose scorecard version/completeness in health/version diagnostics, and extend QA so the page cannot silently drift from canonical scorecard state.

**Acceptance criteria:**
- [ ] Direct `/spread-scorecard` URL works independently of legacy tab switching.
- [ ] Desktop/mobile navigation exposes the page persistently.
- [ ] Health check asserts 15 scorecard rows, five factor objects per game, and no invalid Money-factor metric types.
- [ ] Consistency QA compares rendered scorecard values to the canonical snapshot.

**Verification:**
- [ ] `node five-factor-scorecard-qa.js` passes.
- [ ] `node command-center-consistency-qa.js` passes.
- [ ] Runtime `/healthz` and `/_version` report scorecard state.

**Dependencies:** Task 8.

**Files likely touched:**
- `server-v7.js`
- `five-factor-scorecard-qa.js`
- `command-center-consistency-qa.js`
- `.github/workflows/command-center-consistency.yml` or a dedicated scorecard workflow

**Estimated scope:** Medium.

### Checkpoint D — Page ready for deployment

- [ ] All automated QA passes.
- [ ] Direct URL and navigation behavior verified.
- [ ] No scorecard value is calculated only in the DOM.

## Phase 5 — Deploy and learn prospectively

### Task 10: Deploy, verify live, and freeze prospective output

**Description:** Deploy the scorecard page, verify the live route and representative cards, then save the pre-kick weekly output for later calibration analysis.

**Acceptance criteria:**
- [ ] Render deployment reaches live status on the intended commit.
- [ ] Live `/spread-scorecard` returns the intended version and all eligible games.
- [ ] One favorite, one underdog, one key-number-sensitive game, and one missing-data case are verified live.
- [ ] Pre-kick scorecard snapshot is frozen before results are known/used for evaluation.

**Verification:**
- [ ] Live health/version endpoint passes.
- [ ] Live page matches canonical snapshot for sampled games.
- [ ] Prospective snapshot filename/version includes week and capture timestamp.

**Dependencies:** Checkpoint D.

**Files likely touched:**
- prospective snapshot file under `v2/results/` or a dedicated `five-factor/results/` path
- deployment metadata only if the project records it

**Estimated scope:** Small.

## QA / Definition of Done

The feature is complete only when all of the following are true:

- 15/15 eligible games are present.
- Sly lines exactly match the canonical freeze.
- Five factor objects exist per game or explicitly identify unavailable source evidence.
- Money-factor evidence is provably handle/money, not bets/tickets.
- Side scores and overall grade are deterministic from preregistered config.
- Defense and trend inputs expose source/date/sample-size context.
- Key-number scoring handles both hooks and exact numbers correctly.
- Page explanations are generated from the same canonical factor objects shown in the UI.
- Agreement/disagreement with the main system is displayed but does not alter either system.
- No `undefined`, `null`, `[object Object]`, stale Week 3 recommendation, or source-specific line masquerades as Sly.
- Focused scorecard QA and global Command Center consistency QA pass.
- Live deployment and direct route are verified after deploy.
- A pre-result prospective snapshot is stored for future backtesting.

## Risks and Mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| Money source is actually tickets, not handle | Critical | Strict metric-type schema; source wording/provenance required; unavailable rather than substitute |
| Line movement and money double-count the same market signal | High | Keep separate for transparency but disclose correlation; evaluate prospectively before optimizer use |
| H2H ATS is stale/noisy | High | Sample/date metadata, stale warnings, subweighting, confidence reduction |
| Defense metric changes across sources/weeks | Medium/High | Lock primary metric and source methodology; store through-week metadata |
| Key-number logic double-counted in movement | High | Movement magnitude score excludes key crossing bonus; Factor 5 owns key-number value |
| Early-season ATS sample overlap | Medium | Disclose overlap and reduce confidence on tiny samples |
| Page drifts from scoring data | High | Canonical snapshot + renderer-only UI + render-contract QA |
| Score looks like a probability | High | Label as heuristic grade everywhere; never append `%` to overall grade |
| Outcome-driven tuning | Critical | Preregister config, freeze weekly outputs before results, require explicit future version for rule changes |

## Open Questions / Deferred Decisions

No blocking product questions remain for implementation planning. The following are deliberately deferred until prospective evidence exists:

- Whether any factor deserves more than 20% weight.
- Whether H2H ATS should be reduced below 40% of the Trends factor.
- Whether another defensive metric should supplement/replace EPA/play.
- Whether the scorecard should ever feed V2, recommendation ranking, or optimizer sizing.

Any of those changes require explicit user approval and a new scorecard version; they must not be tuned silently after seeing outcomes.
