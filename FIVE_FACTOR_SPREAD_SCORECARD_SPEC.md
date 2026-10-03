# Spec: Five-Factor Spread Scorecard

**Status:** Draft for human review  
**Feature:** Standalone challenger analysis page for every Monopoly-eligible NFL spread  
**Proposed route:** `/spread-scorecard`

## Objective

Build a separate Command Center page that evaluates every eligible game spread using five transparent betting heuristics:

1. Line movement
2. ATS trends
3. Verified money/handle percentage
4. Defense
5. NFL key numbers

The page must answer, in plain English: **Which side do these five factors favor, how strongly, and why?**

This is a challenger analysis only. It must not silently alter V2, the main recommendation ranking, or Catherine/Amanda wager sizing. Its value is in showing where this independent five-factor framework agrees or disagrees with the existing Command Center.

### Primary user story

As Catherine, I want to scan all eligible games, see a five-factor grade for the Sly spread, and understand the underlying evidence in plain English so I can compare this heuristic framework with the main recommendation system.

## Core Rules

- The spread being graded is always the **immutable Sly contest spread**.
- Market opener/current lines are evidence only; they never overwrite Sly.
- `money %` means **monetary handle percentage**, not bets %, tickets %, or number of wagers.
- If verified money % is unavailable, show `Unavailable` and do not substitute ticket %.
- Every source-specific percentage or line must retain its source, timestamp, and reference spread.
- Missing data must be explicit; never render `undefined`, `null`, inferred values, or silent defaults as if verified.
- The overall grade is a **heuristic score**, not a calibrated cover probability.
- The scorecard remains separate from V2 and the optimizer until prospective evidence justifies integration.

## Five Factors

### 1. Line Movement

**Purpose:** Capture directional information from the market from opener to current spread.

**Raw fields:**
- opening spread
- current spread
- opening timestamp/source
- current timestamp/source
- movement in points
- favorite at open
- favorite currently
- source disagreement flag

**Interpretation:**
- Favorite moves from -2 to -7 -> strong favorite-side signal.
- Favorite moves from -7 to -2 -> strong underdog-side signal.
- Favorite flip -> strong signal toward the newly favored team, subject to source consistency.

**Scoring for the favored side:**
- <0.5 points: 10/20 (neutral)
- 0.5: 12/20
- 1.0: 14/20
- 1.5: 16/20
- 2.0-2.5: 18/20
- >=3.0: 20/20

The opposite side receives the complementary score out of 20. Key-number crossings may be called out in the explanation but are not double-counted here; Factor 5 owns key-number scoring.

### 2. ATS Trends

**Purpose:** Capture how the teams have historically performed against the spread, while avoiding treating stale H2H records as decisive.

**Displayed components:**
- Head-to-head ATS, last 5 meetings where available
- Current-season ATS
- Recent ATS form

**Initial weighting inside the Trends factor:**
- H2H ATS: 40%
- Current-season ATS: 35%
- Recent ATS: 25%

**Data-quality rules:**
- Show sample size with every ATS record.
- H2H older than five seasons receives a stale-data warning and reduced confidence.
- Do not present 1-0 or similarly tiny samples as strong evidence.
- Early-season overlap between current-season and recent ATS must be disclosed; this is a heuristic factor, not an independence claim.

**Factor output:** 0-20 for each side, with 10/20 neutral.

### 3. Money / Handle %

**Purpose:** Capture where actual dollars are concentrated on the spread.

**Required fields:**
- team/side
- handle %
- sportsbook/data source
- exact reference spread
- capture timestamp
- optional bets/tickets % as display-only context, clearly labeled separately

**Never acceptable:** substituting bets %, ticket %, number of bets, or public-pick percentage for money %.

**Initial score bands for the side receiving the money:**
- 50%: 10/20
- 51-54%: 11-12/20
- 55-59%: 14/20
- 60-64%: 16/20
- 65-69%: 18/20
- >=70%: 20/20

The opposite side receives the complementary score.

**Reference-line penalty:**
- If the handle % is tied to a line materially different from Sly, show the mismatch.
- If the mismatch crosses a key number or differs by >=1 point, cap the factor strength until a matching/near-matching handle observation is available.

### 4. Defense

**Purpose:** Use defensive quality as context for whether a team can create or preserve enough margin to cover the Sly spread.

**Primary metric:** defensive EPA/play rank.

**Optional secondary context:** defensive success-rate rank, if available from a reliable current-season source.

**Displayed fields:**
- each team's defensive rank
- metric name and through-week date
- spread magnitude
- plain-English interpretation

**Spread-aware interpretation:**
- Top-5 defense laying a large spread is positive evidence for the favorite.
- Weak defense laying a large spread is a meaningful negative.
- Elite defense catching a large number can support the underdog's ability to stay within the spread.
- Defense matters less near pick'em and more as the spread grows.

**Initial defensive tiers:**
- ranks 1-5: strong positive
- 6-10: moderate positive
- 11-22: near neutral
- 23-27: moderate negative
- 28-32: strong negative

The magnitude of the score adjustment increases for spreads of 7+ and 10+.

### 5. NFL Key Numbers

**Purpose:** Measure whether Sly gives a side protection or disadvantage around common NFL final margins.

**Configured key-number frequencies for this heuristic:**
- 3: ~15%
- 7: ~9%
- 6: ~8%
- 10: ~5%
- 14: ~5%

These values are configuration inputs for the challenger framework, not claims that the current app has independently re-estimated the historical frequencies.

**Examples:**
- Favorite -2.5 around 3 -> strong positive
- Underdog +3.5 around 3 -> strong positive
- Favorite -3.5 around 3 -> negative
- Underdog +2.5 around 3 -> negative
- Exact +/-3 -> useful but less valuable than the favorable hook

The same structure applies around 7, 6, 10, and 14, with strength scaled by the configured frequency.

**Important:** The strongest key-number signal occurs when Sly gives a better side of the number than the current market.

## Scoring Model

Each side receives a score from 0-20 for each factor. A neutral factor is 10/20 for both sides; directional scores complement to 20.

```text
sideTotal = lineMovement + trends + money + defense + keyNumbers
```

Maximum = 100. The higher-scoring side is the five-factor lean.

### Alignment

Each factor is also classified:
- `supports`: side score >=12
- `neutral`: side score 9-11
- `opposes`: side score <=8

The page must show both total score and factor alignment so a high score caused by a few extreme factors is distinguishable from broad agreement.

### Grade bands

- A+: 85-100
- A: 80-84
- A-: 75-79
- B+: 70-74
- B: 65-69
- B-: 60-64
- C+: 55-59
- C: 51-54
- N / No Edge: 50

### Grade caps / confidence rules

- Missing verified money data -> maximum displayed grade B+.
- Fewer than 4 verified factors -> maximum grade B.
- Two or more strongly opposing factors -> maximum grade B unless a documented rule later changes this.
- Stale or mismatched source data reduces confidence and must be visible.
- The grade must never be labeled as a cover probability.

## Canonical Data Shape

Each normalized game receives one scorecard object:

```js
game.fiveFactor = {
  lineMovement: {
    sideScores: { away: 10, home: 10 },
    lean: 'neutral',
    raw: {},
    source: '',
    capturedAt: '',
    explanation: ''
  },
  trends: { /* same contract */ },
  money: { /* same contract */ },
  defense: { /* same contract */ },
  keyNumbers: { /* same contract */ },
  overall: {
    awayScore: 0,
    homeScore: 0,
    lean: '',
    grade: '',
    alignment: { supports: 0, neutral: 0, opposes: 0 },
    completeness: 0,
    confidenceCap: null,
    plainEnglish: ''
  }
}
```

The UI must render this normalized object; it must not independently recalculate grades in DOM patches.

## Page UX

### Top summary

A ranked table for all eligible games:

| Rank | Five-Factor Lean | Grade | Line | Trends | Money | Defense | Key # |
|---|---|---|---|---|---|---|---|

Each factor cell shows a concise directional state such as `KC +`, `Neutral`, or `LV -`, plus the underlying score on hover/tap or in the game section.

### Game cards

Each game gets one plain-English card containing:
- Sly spread
- opener and current market
- overall five-factor lean, score, grade, and alignment
- one section for each of the five factors
- raw evidence and source/timestamp
- `Why this side` paragraph
- `What argues against it` paragraph
- comparison badge versus the main Command Center: `AGREES`, `DISAGREES`, or `MAIN SYSTEM NO TAKE`

### Plain-English example

> **KC -4.5 — Five-Factor Grade A-**
>
> Four of the five signals favor Kansas City. The market moved toward KC, verified money is concentrated on KC at a comparable spread, and Kansas City has the stronger defensive profile. The key-number setup is mostly neutral at -4.5. This is a broad-agreement heuristic play rather than a stale-line bargain.

## Source / Freshness Requirements

- Sly: immutable canonical freeze.
- Opening/current market: versioned source-backed market snapshot.
- ATS trends: source-backed team/game history with sample size.
- Money: source explicitly labeled as money/handle %, with exact reference spread.
- Defense: current-season defensive EPA/play ranking through latest completed week.
- Key numbers: deterministic calculation from Sly and market spreads.

Every source-backed field carries `source`, `capturedAt`, and `referenceLine` where applicable.

## Testing Strategy

### Existing runtime command

```bash
npm start
```

### Planned focused QA

```bash
node five-factor-scorecard-qa.js
node command-center-consistency-qa.js
```

### Required assertions

- All eligible games have one `game.fiveFactor` object.
- All five factors are populated or explicitly `Unavailable`.
- No ticket/bets percentage can satisfy the money-factor schema.
- Every money % has a reference spread and source.
- Sly line is never overwritten.
- Side scores are deterministic and each factor pair sums to 20 when directional/neutral scoring is valid.
- Overall score is the exact sum of the five factor scores.
- Grade caps are enforced for missing/unverified data.
- No rendered output contains `undefined`, `null`, or `[object Object]`.
- `/spread-scorecard` shows all eligible games and matches the canonical normalized object.

## Code Style

Keep data normalization/scoring separate from rendering.

```js
function scoreMoneyFactor({ awayMoneyPct, homeMoneyPct, referenceLine }) {
  // Return raw inputs, both side scores, lean, data-quality flags, and explanation.
  // Do not mutate the canonical Sly spread and do not infer missing handle data.
  return {
    sideScores: { away: 10, home: 10 },
    lean: 'neutral',
    referenceLine,
    explanation: 'Verified handle is balanced.'
  };
}
```

## Project Structure

Proposed implementation files:

```text
five-factor-scorecard-engine.js      deterministic scoring rules
five-factor-scorecard-data.json      normalized/versioned current snapshot
five-factor-scorecard-page.html      presentation only
five-factor-scorecard-qa.js          data + scoring + render-contract QA
server-v7.js                          route/state integration only
COMMAND_CENTER_DATA_CONTRACT.md       add scorecard canonical-source rules
```

If the runtime architecture changes before implementation, preserve the same separation of source data, scoring, and rendering.

## Boundaries

### Always do
- Preserve Sly as immutable.
- Preserve source/reference-line/timestamp provenance.
- Distinguish money % from bets/tickets %.
- Show missing data honestly.
- Keep the five-factor scorecard separate from V2 and optimizer inputs.
- Run focused QA plus Command Center consistency QA before deploy.

### Ask first
- Change factor weights away from equal 20-point maximums.
- Change Trends subweights.
- Replace defensive EPA/play with another primary defensive metric.
- Feed the five-factor grade into the main recommendation model or optimizer.
- Change the configured key-number frequencies.

### Never do
- Infer money % from ticket %.
- Treat the grade as a calibrated cover probability.
- Let UI code become the sole source of factor values.
- Silently use a source's spread as the Sly contest line.
- Retroactively tune thresholds merely to improve this week's preferred games.

## Success Criteria

1. Every eligible game is ranked on `/spread-scorecard` using the same five deterministic factors.
2. A user can understand the recommendation without knowing model jargon.
3. Money and ticket percentages are never conflated.
4. Each factor shows raw evidence, direction, score, source, and timestamp.
5. The overall grade is reproducible from the canonical data object.
6. The page explicitly shows agreement/disagreement with the main Command Center without changing that system.
7. Missing or stale data visibly lowers confidence rather than disappearing.
8. Automated QA fails on schema drift, source mismatch, undefined rendering, or grade miscalculation.
9. Weekly outputs can be stored prospectively so the framework can later be evaluated and recalibrated without outcome-driven rewriting.

## Known Risks

- Line movement and money % are correlated, so equal weighting may double-count related market information.
- ATS trends, especially H2H, can be noisy or stale because personnel/coaching changes.
- Early-season current/recent ATS samples overlap heavily.
- Defensive ranking choice can materially change the factor; EPA/play is the initial primary metric for transparency and predictive relevance.
- Key-number frequencies vary by era/rules environment; configured values should be treated as heuristic inputs until separately validated.
- A simple five-factor score may be useful for explanation while still being weaker than a calibrated predictive model. Prospective tracking is mandatory before promotion into bankroll sizing.

## Open Questions

No blocking product questions remain from the approved concept. The next gated step is to create the implementation plan and task breakdown after human review of this spec.
