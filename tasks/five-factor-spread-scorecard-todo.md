# Five-Factor Spread Scorecard Tasks

Source spec: `FIVE_FACTOR_SPREAD_SCORECARD_SPEC.md`  
Implementation plan: `tasks/five-factor-spread-scorecard-plan.md`

This checklist is intentionally separate from the existing Week 4 `tasks/todo.md`. Do not close, overwrite, or reinterpret the unfinished Week 4 tasks while executing this feature.

## Phase 1 — Scoring contract

- [ ] Task 1: Create preregistered scorecard configuration
  - [ ] Define exact numeric rules for line movement, ATS trends, money, defense, key numbers, grade bands, alignment, and confidence caps
  - [ ] Keep all five factors at equal 20-point maximums
  - [ ] Ensure no team/game-specific exception appears in config
  - [ ] Verify neutral = 10/20 per factor

- [ ] Task 2: Build deterministic scoring engine with fixtures
  - [ ] Favorite -2 -> -7 fixture strongly favors favorite
  - [ ] Favorite -7 -> -2 fixture strongly favors underdog
  - [ ] Key-number hook fixtures score +3.5 / -2.5 correctly around 3
  - [ ] Money schema rejects bets/tickets-only records
  - [ ] Overall total/grade/alignment/caps are reproducible

### Checkpoint A
- [ ] Exact scoring rules committed before live Week 4 ranking is generated
- [ ] Engine fixture QA passes
- [ ] No outcome/team-specific tuning exists

## Phase 2 — Source-backed factor data

- [ ] Task 3: Normalize Week 4 market movement + key-number inputs
  - [ ] 15/15 eligible games have canonical Sly
  - [ ] Opener/current market records retain source and timestamp
  - [ ] Team-side movement direction is normalized without sign ambiguity
  - [ ] Source disagreements remain visible
  - [ ] Market line never overwrites Sly

- [ ] Task 4: Add ATS trend inputs
  - [ ] H2H ATS last 5 where available
  - [ ] Current-season ATS
  - [ ] Recent ATS form
  - [ ] Sample size/date range stored
  - [ ] Stale/tiny sample flags stored and used by confidence logic

- [ ] Task 5: Add verified handle % + defense rankings
  - [ ] Money records explicitly identify handle/money metric type
  - [ ] Every handle record has source, timestamp, exact reference spread
  - [ ] Tickets/bets may be display-only but never satisfy Money factor
  - [ ] Unverified/missing handle remains `Unavailable`
  - [ ] Defensive EPA/play rank captured with source and through-week marker
  - [ ] Existing SportsLine `money_pct` is not reused unless handle semantics/provenance are independently verified

### Checkpoint B
- [ ] All five factor inputs exist or are explicitly unavailable for 15/15 games
- [ ] Data-quality QA passes
- [ ] Money-vs-ticket semantics are proven, not assumed

## Phase 3 — Generate canonical scorecard

- [ ] Task 6: Generate Week 4 five-factor snapshot
  - [ ] 15/15 games receive one `fiveFactor` object
  - [ ] Each factor has raw evidence, side scores, lean, source, timestamp, quality flags, explanation
  - [ ] Overall score exactly equals factor sum
  - [ ] Grade caps are enforced
  - [ ] `whyThisSide` and `whatArguesAgainst` are generated from structured evidence
  - [ ] Main-system comparison is computed only after five-factor scoring

- [ ] Task 7: Run adversarial data/scoring review
  - [ ] Challenge spread sign/orientation
  - [ ] Challenge stale H2H usage
  - [ ] Challenge handle vs ticket semantics
  - [ ] Challenge money reference-line mismatch
  - [ ] Challenge defense rank orientation/methodology
  - [ ] Challenge key-number double counting
  - [ ] Challenge correlated line-movement + money signals
  - [ ] Fix upstream source/config/engine defects rather than patching UI

### Checkpoint C
- [ ] Canonical ranking exists independent of page code
- [ ] Focused scorecard QA passes
- [ ] Challenger remains isolated from V2 and optimizer

## Phase 4 — Page + runtime integration

- [ ] Task 8: Build `/spread-scorecard`
  - [ ] Ranked 15-game summary table
  - [ ] One plain-English card per game
  - [ ] Show Sly, opener/current market, total score/grade/alignment
  - [ ] Show all five factor sections with evidence/source/timestamp
  - [ ] Show `Why this side` and `What argues against it`
  - [ ] Show `AGREES`, `DISAGREES`, or `MAIN SYSTEM NO TAKE`
  - [ ] Renderer reads canonical scorecard only; no DOM scoring logic

- [ ] Task 9: Add nav + runtime/consistency QA
  - [ ] Direct `/spread-scorecard` route works independently of legacy tab switching
  - [ ] Desktop/mobile nav entry is persistent
  - [ ] `/healthz` validates 15 games + five factors + valid handle schema
  - [ ] `/_version` exposes scorecard version
  - [ ] `node five-factor-scorecard-qa.js` passes
  - [ ] `node command-center-consistency-qa.js` passes
  - [ ] Render-contract QA rejects `undefined`, `null`, `[object Object]`

### Checkpoint D
- [ ] Direct route verified before deploy
- [ ] All automated QA passes
- [ ] Three representative rendered games match canonical values exactly

## Phase 5 — Deploy + prospective tracking

- [ ] Task 10: Deploy and freeze prospective output
  - [ ] Deploy intended commit to canonical Render service
  - [ ] Confirm deploy reaches `live`
  - [ ] Verify live `/spread-scorecard`
  - [ ] Verify one favorite, one dog, one key-number-sensitive game, and one missing-data case
  - [ ] Verify live health/version endpoints
  - [ ] Freeze timestamped pre-kick scorecard snapshot before results influence evaluation

## Definition of Done

- [ ] 15/15 eligible games present
- [ ] Sly lines match canonical freeze exactly
- [ ] Five factors populated or explicitly unavailable
- [ ] Money handle is never conflated with tickets/bets
- [ ] All factor and overall scores deterministic from preregistered config
- [ ] Plain-English explanation comes from canonical factor evidence
- [ ] Main-system agreement is comparison-only
- [ ] No five-factor signal feeds V2/recommendation/optimizer
- [ ] Focused + global QA pass
- [ ] Live route verified
- [ ] Prospective pre-result snapshot stored
