# Command Center Data Contract

## Purpose

The Command Center must have one declared source of truth for each data concept and an explicit list of every view that consumes it. A data update is not complete until all required views pass consistency QA.

## Canonical inputs

| Concept | Canonical input | Rule |
|---|---|---|
| Contest line | `v2/season_2026/week_04_sly_freeze.json` / normalized `game.sly` | Immutable after Sly freeze; never overwritten by a market/source line. |
| Market/open/current | latest versioned market snapshot + normalized `game.open/current/diff` | Keep source provenance; do not silently collapse conflicting books. |
| Our recommendation | normalized `week4-current-data.json` after server reconciliation | Rank, lean, decision, confidence, rationale and wagers must agree across views. |
| SportsLine | `week4-sportsline-2026-10-03-1611ET.json` | Preserve spread, money %, SIM %, visible SIM pick/type/grade separately. Non-ATS SIMs are not ATS votes. |
| Gridiron | `week4-gridiron-2026-10-03.json` | Preserve displayed spread and both teams' cover %. Percentages apply to the displayed Gridiron line. |
| Gridiron scan grade | Derived from stronger cover % | A >=55%; B 52–54%; C 51%; N 50/50. Never replace the underlying % with the grade. |
| Lucas | Latest verified Lucas snapshot when supplied | Missing/unverified stays unavailable; never infer. |
| Injuries/news/weather | latest timestamped context snapshot | Context layer only unless a governed model explicitly consumes it. |
| Portfolio | latest optimizer/reconciliation output | Same pick/amount must appear in Today, Portfolio, Analysis and any recommendation card that shows sizing. |

## Required view propagation

A checkmark means the field must be visible or directly available in that view.

| Field | Today | Decision Board recommended | Decision Board all games | Source table | Game deep dive | Analysis | Portfolio | Lab/provenance |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Sly line | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Current market / DIFF | ✓* | ✓ | ✓ | ✓ | ✓ | ✓ |  | ✓ |
| Our rank / decision | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| SportsLine spread |  | ✓* | ✓* | ✓ | ✓ | ✓ |  | ✓ |
| SportsLine money % |  |  | ✓* | ✓ | ✓ | ✓* |  | ✓ |
| SportsLine SIM % |  | ✓* | ✓* | ✓ | ✓ | ✓ |  | ✓ |
| Gridiron spread |  | ✓ | ✓ | ✓ | ✓ | ✓* |  | ✓ |
| Gridiron cover % |  | ✓ | ✓ | ✓ | ✓ | ✓* |  | ✓ |
| Gridiron grade |  | ✓ | ✓ | ✓ | ✓ | ✓* |  | ✓ |
| Lucas |  | ✓* | ✓* | ✓ | ✓ | ✓* |  | ✓ |
| News/injuries | ✓* | ✓* | ✓* |  | ✓ | ✓ |  | ✓ |
| Weather |  | ✓* | ✓* |  | ✓ | ✓* |  | ✓ |
| Wager amount | ✓ | ✓ | ✓* |  | ✓* | ✓ | ✓ | ✓ |

`✓*` = compact/summary presentation is acceptable; the deep-dive/source-table representation remains authoritative for detail.

## Current component map

- **Today**: `#today`
- **Decision Board / recommended**: `#recommendedPlays`
- **Decision Board / all games**: `#games` and rendered game/card/row descendants
- **Source comparison**: `#sourceCompare`, `#sourceCompareBody`
- **Game deep dive**: `#gameHero`, `#slGameRead`, `#gridironGameRead`
- **Analysis**: `#analysis`
- **Portfolio**: `#portfolio`
- **Lab/provenance**: `#lab`

## Update protocol

1. Capture a versioned source snapshot.
2. Normalize it into the canonical game/source state; never create a second independent interpretation of the same data.
3. Check this matrix and update every required consumer.
4. Run `node command-center-consistency-qa.js`.
5. Do not deploy if QA fails.
6. After deploy, verify the live health/version endpoint and visually check one representative game in each major view.
7. Only then describe the update as complete.

## Anti-regression rules

- A source-specific spread must never overwrite Sly.
- A percentage must retain its reference line and source.
- A total or moneyline SIM must never be counted as ATS confirmation.
- Derived grades are display aids only; raw percentages remain visible.
- Week 3 data may appear only in explicitly historical/postmortem components during Week 4.
- DOM-only patches may decorate a canonical value but must not become the sole storage location for that value.
- Any duplicated hard-coded source table must be byte-for-value checked against the canonical snapshot by CI until it is eliminated.
