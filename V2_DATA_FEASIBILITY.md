# V2 Data Feasibility Audit

Status: Phase 1 research artifact. No production picks or V1 behavior are changed by this document.

## Executive conclusion

V2 is feasible with a mostly open-source football-data spine plus one optional/paid historical-odds component.

- **Open / feasible now:** schedules/results, closing market fields, play-by-play, team/player stats, rosters, weekly rosters, injuries, depth charts, snap counts/participation, and game context via nflverse/nflreadpy.
- **Feasible prospectively now:** exact Sly lines/timestamps, Friday and Sunday market snapshots, SportsLine, Gridiron, Lucas, and Command Center outputs can be frozen each week in our own ledger.
- **Historical gap:** exact reconstruction of Friday→Sunday sportsbook movement requires timestamped historical odds. nflverse closing-line fields are not enough for stale-line backtesting.
- **Paid options:** The Odds API historical featured-market snapshots (from June 2020; 10-minute snapshots initially, 5-minute snapshots from September 2022) or SportsDataIO pregame line-movement history.

The correct implementation is therefore two-track:
1. build the full historical fundamentals/closing-market dataset now;
2. treat exact intra-week stale-line testing as a separate dataset, using a paid historical feed if authorized or a prospective ledger if not.

---

## Source audit

### 1. nflverse / nflreadpy — APPROVED CORE SOURCE
Python package: `nflreadpy`.

Confirmed available loaders include:
- `load_schedules`
- `load_pbp`
- `load_team_stats`
- `load_player_stats`
- `load_rosters`
- `load_rosters_weekly`
- `load_snap_counts`
- `load_injuries`
- `load_depth_charts`
- `load_participation`
- `load_nextgen_stats`

Key coverage notes:
- play-by-play: 1999+
- injuries: 2009+
- depth charts: 2001+
- participation: 2016+
- schedules/market fields cover historical game lines/results
- depth-chart data from 2025+ includes an explicit load timestamp (`dt`), useful for point-in-time work
- injury data includes `date_modified`, official report status, and practice status

Use cases:
- team strength / EPA features
- QB rolling features
- early-season priors
- opponent adjustment
- personnel availability research
- game results / margin target
- market-only closing-line baseline

Limitations:
- schedule betting fields are not a full timestamped intra-week market archive
- historical injury/depth records require explicit leakage checks; a season-level file being historical does not automatically mean every field is an exact as-of snapshot for every past timestamp

### 2. The Odds API — OPTIONAL HISTORICAL INTRA-WEEK ODDS
Historical featured-market snapshots:
- available from June 6, 2020
- 10-minute intervals initially
- 5-minute intervals from September 2022
- paid usage plans only

Use case:
- reconstruct Friday market at/after Sly freeze
- reconstruct Sunday pre-kick market
- measure post-freeze movement
- estimate multi-book dispersion and price-path features without hindsight

Decision:
- not required for the first market/fundamentals model
- required if we want a proper historical backtest of the unique Sly stale-line advantage rather than only prospective testing

### 3. SportsDataIO — OPTIONAL ALTERNATIVE HISTORICAL ODDS
Their NFL betting feeds expose opening price, line-movement changes and closing price with timestamps. Historical betting line movement is retained even though ordinary historical records are not general point-in-time revision archives.

Use case:
- same as The Odds API for stale-line reconstruction
- potential sportsbook-level market history and consensus

Decision:
- viable alternative to The Odds API; provider choice should be based on cost, historical bookmaker coverage, granularity, and export limits before purchase

### 4. NFL/team official injury reports — PRODUCTION AUTHORITY
Use as the authoritative current status source for live weekly refreshes.

Historical structured injury features can come from nflverse, while production QA should cross-check material player statuses against official reports before lock.

### 5. SportsLine / Gridiron / Lucas — PROSPECTIVE EXTERNAL-EVIDENCE LEDGER
Do not attempt to reverse-engineer unavailable historical proprietary predictions.

Starting immediately, each external signal should be stored with:
- source
- game
- timestamp
- side
- exact reference line
- probability / grade / LIKE-LEAN signal
- source-native market type (ATS / ML / total)
- Sly line at decision time
- result at source line
- result at Sly line
- closing-line value where available

These become meta-model candidates only after enough prospective observations exist.

---

## Historical research windows

### Core fundamentals model
Recommended initial research range: **2012–2025**.

Why not automatically use all 1999+ PBP?
- league style, rules, fourth-down behavior, passing efficiency and home-field effects have changed materially
- more recent windows better represent the current game
- longer history can still be tested as a challenger / prior-estimation source

Candidate window experiment:
- 2012+
- 2016+
- 2020+
- exponentially decayed long-history model

Window length is a tunable research choice and must be selected inside walk-forward validation.

### Injury/personnel model
Reliable structured injury availability begins 2009; participation/snap-enhanced work is strongest from roughly 2016+.

### Exact stale-line model
- 2020+ with The Odds API if purchased
- otherwise prospective only from our own immutable weekly snapshots

### Sacred holdout
Reserve at least one recent completed season as an outer holdout after architecture/hyperparameters are selected. The current 2026 season remains live prospective/shadow evidence and is not used to retroactively choose Week 3 architecture.

---

## Dataset layers

### Bronze / raw
Immutable copies of source tables by retrieval date/version.

Suggested tables:
- `games_raw`
- `pbp_raw`
- `team_stats_raw`
- `player_stats_raw`
- `rosters_weekly_raw`
- `injuries_raw`
- `depth_charts_raw`
- `snap_counts_raw`
- `participation_raw`
- `market_snapshots_raw` (optional paid/prospective)
- `sly_lines_raw`
- `external_sources_raw`
- `pool_standings_raw`

### Silver / normalized
Canonical IDs, team abbreviations, timestamps and sign conventions.

Required invariant:
**positive modeled margin = home team expected win margin**.

Store spreads separately using an explicit convention:
- `home_spread`: sportsbook home-team handicap; negative means home favorite
- `sly_home_spread`: Sly handicap in the same convention

Never infer signs from display strings after normalization.

### Gold / point-in-time feature rows
One row per `game_id × prediction_timestamp`.

Planned snapshots:
- `FRIDAY_FREEZE`
- `SUNDAY_FINAL` (or pre-kick final for non-Sunday games)

A gold row may use only source records with timestamps <= its prediction timestamp.

Primary target columns:
- `home_margin = home_score - away_score`
- ATS cover/push/loss at Sly line

---

## Point-in-time leakage contract

For a prediction timestamp T:

### Allowed
- games completed before T
- stats from games completed before T
- injury/depth information timestamped <= T
- market quotes timestamped <= T
- Sly line already issued <= T
- external-source prediction published <= T

### Forbidden
- final score of target game
- closing line if close occurred after T
- injury status updated after T
- Sunday market in a Friday row
- season-end aggregates containing the target game
- rolling features that include current/future week
- retroactively corrected source values where the original as-of value cannot be reconstructed

If point-in-time reconstruction is impossible for a feature, either:
1. exclude it from historical training; or
2. use it only in prospective shadow evaluation.

Never silently approximate future-known information as historical knowledge.

---

## Feasibility decisions

### Green — build now
- schedules/results
- PBP-derived EPA/success/explosiveness
- rolling offense/defense features
- QB features from prior games
- rest/home/division/game-context fields
- closing-market baseline
- discrete final-margin distribution
- walk-forward framework
- calibration harness
- Sly/external/pool prospective ledgers

### Yellow — build with explicit point-in-time QA
- injuries
- depth charts
- snap-weighted personnel
- weather
- projected starter changes

### Red until data source is authorized
- retrospective Friday→Sunday sportsbook paths for years where we do not possess timestamped historical odds

---

## Phase 1 exit criteria

Data feasibility is complete when:
1. a reproducible historical raw ingestion script exists;
2. normalized game IDs/team signs are defined;
3. point-in-time schema is machine-readable;
4. leakage QA tests exist;
5. a first historical sample can be built without any proprietary historical-odds dependency;
6. exact stale-line features are isolated behind an optional data-provider interface rather than fabricated.

The initial scaffold in `/v2/` implements these contracts. Production V1 remains untouched.
