# Five-Factor Spread Scorecard — Preregistered Scoring Rules

**Version:** 1.0  
**Status:** Locked design contract before Week 4 score generation  
**Purpose:** Define the exact deterministic scoring behavior that implementation must reproduce. These rules are game-agnostic and must not be changed after viewing Week 4 scorecard outputs unless a defect is found and documented prospectively.

## Global invariants

- The graded line is always the immutable Sly contest spread.
- Each factor contributes 0–20 points to each side.
- Neutral = 10/20 for each side.
- For every directional factor, the two side scores sum to 20.
- Five factor totals therefore sum to 100 across the two teams; the higher-scoring side is the Five-Factor lean.
- Factor weights are equal: 20% each.
- The score is a heuristic score, not a cover probability.
- No team, matchup, or Week 4-specific exception is permitted.
- Source quality changes factor confidence/caps; UI code never changes scores.

## Common side / line convention

For a team-side spread:
- negative = favorite, e.g. `KC -4.5`
- positive = underdog, e.g. `LV +4.5`

For every game, away and home spreads must be exact opposites.

### Factor state labels

For the eventual five-factor lean side:
- `supports` if side score >= 12
- `neutral` if side score is 9–11
- `opposes` if side score <= 8
- `strongly_opposes` if side score <= 6

## 1. Line Movement — 20 points

### Canonical movement calculation

For any team T:

```text
movementTowardTeam = openingSpread(T) - currentSpread(T)
```

Examples:
- `-2 -> -7`: `+5` = strong movement toward that favorite.
- `+7 -> +2`: `+5` = strong movement toward that team.
- `-7 -> -2`: `-5` = strong movement away from that favorite and therefore toward the opponent.
- `+2 -> +7`: `-5` = strong movement away from that team.

This definition also handles favorite flips without a special team-specific rule.

### Magnitude-to-score mapping

Use the absolute movement of the team the market moved toward:

| Absolute movement | Supported side | Opposite side |
|---:|---:|---:|
| < 0.50 | 10 | 10 |
| 0.50–0.99 | 12 | 8 |
| 1.00–1.49 | 14 | 6 |
| 1.50–1.99 | 16 | 4 |
| 2.00–2.99 | 18 | 2 |
| >= 3.00 | 20 | 0 |

### Source disagreement / missingness

- Scoring uses one designated primary market source record containing opener and current spread.
- Trusted cross-check sources are retained for quality control, not averaged into the primary line.
- If trusted cross-check sources disagree on movement direction by >= 0.5 points, cap the supported side at **14/20** and the opponent at **6/20**.
- If opener or current line is missing from the designated primary record, Line Movement = **10/10, Unavailable**.
- Key-number crossings are described here but receive no extra points here; Factor 5 owns key-number scoring.

## 2. ATS Trends — 20 points

### Inputs

For each team:
1. H2H ATS — last five meetings where available
2. Current-season ATS
3. Recent ATS — target last 10 decisions where available

Pushes are excluded from ATS win rate:

```text
atsWinRate = wins / (wins + losses)
```

If `wins + losses = 0`, that component is unavailable.

### Raw ATS rate rating

| ATS win rate | Raw component rating |
|---:|---:|
| >= 70% | 20 |
| 65–69.9% | 18 |
| 60–64.9% | 16 |
| 55–59.9% | 14 |
| 52–54.9% | 12 |
| 48–51.9% | 10 |
| 45–47.9% | 8 |
| 40–44.9% | 6 |
| 35–39.9% | 4 |
| 30–34.9% | 2 |
| < 30% | 0 |

### Sample-size shrinkage

Shrink each component toward neutral 10:

```text
adjustedRating = 10 + (rawRating - 10) * sampleMultiplier
```

| ATS decisions | Sample multiplier |
|---:|---:|
| 1 | 0.25 |
| 2 | 0.40 |
| 3 | 0.60 |
| 4 | 0.80 |
| >= 5 | 1.00 |

### H2H recency adjustment

Apply an additional multiplier to the H2H deviation from 10 based on the most recent H2H meeting:

| Most recent H2H meeting | Recency multiplier |
|---|---:|
| <= 2 seasons ago | 1.00 |
| 3–5 seasons ago | 0.75 |
| > 5 seasons ago | 0.50 |

### Trend component weights

- H2H ATS: 40%
- Current-season ATS: 35%
- Recent ATS: 25%

If a component is unavailable, renormalize the remaining weights to 100%.

If only one of the three components is available, the Trends factor is marked `degraded` and its eventual directional strength is capped at **14/20 vs 6/20**.

### Convert team trend indexes into matchup scores

Compute a 0–20 trend index for each team from the weighted adjusted component ratings. Then:

```text
trendDiff = awayTrendIndex - homeTrendIndex
```

| Absolute trend index difference | Better-trend team | Opponent |
|---:|---:|---:|
| < 1.0 | 10 | 10 |
| 1.0–2.9 | 12 | 8 |
| 3.0–4.9 | 14 | 6 |
| 5.0–6.9 | 16 | 4 |
| 7.0–8.9 | 18 | 2 |
| >= 9.0 | 20 | 0 |

If all three trend components are unavailable for both teams, Trends = **10/10, Unavailable**.

## 3. Money / Handle — 20 points

### Valid evidence contract

A Money-factor record is valid only if the source explicitly identifies the percentage as one of:
- money %
- handle %
- dollars wagered % / share of dollars

`bets %`, `tickets %`, `pick %`, `public %`, number of bets, or number of tickets are not valid substitutes.

Every valid record must include:
- source
- capture timestamp
- exact reference spread
- percentage for both sides, or source semantics that make the complement unambiguous

### Score mapping

Use the side receiving the larger verified handle share:

| Larger side handle share | Larger-money side | Opponent |
|---:|---:|---:|
| < 51% | 10 | 10 |
| 51–54.9% | 12 | 8 |
| 55–59.9% | 14 | 6 |
| 60–64.9% | 16 | 4 |
| 65–69.9% | 18 | 2 |
| >= 70% | 20 | 0 |

### Reference-line penalty

Compare the money observation’s reference spread to the Sly spread for the same side.

If either is true:
- absolute difference >= 1.0 point, or
- the difference crosses any configured key number (3, 6, 7, 10, 14),

then cap the supported side at **14/20** and opponent at **6/20**.

### Freshness

Relative to scorecard capture time:
- <= 6 hours old: fresh
- > 6 to 24 hours: stale; cap supported side at **14/20**
- > 24 hours: unusable for scoring; Money = **10/10, Unavailable**

If semantics cannot be verified as handle/money, Money = **10/10, Unavailable**.

## 4. Defense — 20 points

### Primary metric

Current-season **defensive EPA/play rank** through the latest completed week.

Lower rank number = better defense.

### Defensive quality value

| EPA/play rank | Quality value |
|---:|---:|
| 1–5 | +5 |
| 6–10 | +3 |
| 11–22 | 0 |
| 23–27 | -3 |
| 28–32 | -5 |

### Spread-magnitude multiplier

Use the absolute Sly spread:

| Absolute Sly spread | Multiplier |
|---:|---:|
| 0–2.5 | 0.50 |
| 3–6.5 | 1.00 |
| 7–9.5 | 1.50 |
| >= 10 | 2.00 |

For each team:

```text
defenseSupport = defensiveQualityValue * spreadMultiplier
```

Then compare the two teams:

```text
defenseDiff = awayDefenseSupport - homeDefenseSupport
```

### Defense difference to score

| Absolute defense support difference | Better-defense side | Opponent |
|---:|---:|---:|
| < 1.0 | 10 | 10 |
| 1.0–2.9 | 12 | 8 |
| 3.0–4.9 | 14 | 6 |
| 5.0–6.9 | 16 | 4 |
| 7.0–8.9 | 18 | 2 |
| >= 9.0 | 20 | 0 |

This makes defense matter more as the required margin grows. A top defense laying or catching a large number can materially support that side; a weak defense does the opposite.

If either team’s defensive rank is unavailable from the same methodology/cutoff, Defense = **10/10, Unavailable**. Do not mix incompatible defensive ranking methodologies within one matchup.

## 5. NFL Key Numbers — 20 points

### Configured key-number hierarchy

| Key number | Approx. configured frequency | Base hook strength |
|---:|---:|---:|
| 3 | 15% | 6 |
| 7 | 9% | 5 |
| 6 | 8% | 4 |
| 10 | 5% | 3 |
| 14 | 5% | 3 |

The frequency values are heuristic configuration inputs supplied for this challenger framework; the app is not claiming to have independently re-estimated them.

### Intrinsic Sly hook value

For a given team, inspect **every configured key number** that is exactly 0.5 points from the absolute Sly spread. This matters for overlapping cases such as 6.5, which sits halfway between keys 6 and 7.

For each matching key:

For a favorite:
- `-(key - 0.5)` gives the favorite `+baseHookStrength`
- `-(key + 0.5)` gives the favorite `-baseHookStrength`

For an underdog:
- `+(key + 0.5)` gives the underdog `+baseHookStrength`
- `+(key - 0.5)` gives the underdog `-baseHookStrength`

Sum all signed hook strengths for that side, then cap the intrinsic advantage at +/-10.

Example at 6.5 for a favorite:
- relative to key 6, `-6.5` is unfavorable to the favorite: `-4`
- relative to key 7, `-6.5` is favorable to the favorite: `+5`
- net intrinsic advantage = `+1`, so the factor begins `11/9` for favorite/dog before any market-relative adjustment.

Exact key numbers (e.g. `-3/+3`, `-7/+7`) contribute **0 directional advantage** for that key because both sides receive push protection but neither side has the hook advantage.

### Market-relative Sly boost

For each configured key number crossed between the Sly line and current market line for the same team, determine whether Sly is better or worse for that team.

If Sly is better for the team across the key, add:

```text
ceil(baseHookStrength / 2)
```

If Sly is worse for the team across the key, subtract the same amount.

Sum all applicable market-relative boosts with the intrinsic signed hook strengths. Cap final directional advantage at +/-10.

Final factor score for the evaluated side:

```text
10 + finalDirectionalAdvantage
```

Opponent receives:

```text
10 - finalDirectionalAdvantage
```

Examples around 3:
- Sly favorite `-2.5`, market `-3.5`: favorite receives intrinsic +6 plus market-relative +3 = 19/1.
- Sly dog `+3.5`, market `+2.5`: dog receives 19/1.
- Sly `-3/+3`: intrinsic key effect is neutral 10/10 unless Sly-vs-market crosses another configured key.
- Sly favorite `-3.5`, market `-2.5`: favorite receives intrinsic -6 plus market-relative -3 = 1/19, favoring the dog.

If current market is unavailable, retain intrinsic Sly hook scoring but mark the Key Numbers factor `degraded` because market-relative value cannot be assessed.

## Overall score and raw grade

For each side:

```text
overallScore = lineMovement + trends + money + defense + keyNumbers
```

Raw grade:

| Score | Raw grade |
|---:|---|
| 85–100 | A+ |
| 80–84 | A |
| 75–79 | A- |
| 70–74 | B+ |
| 65–69 | B |
| 60–64 | B- |
| 55–59 | C+ |
| 51–54 | C |
| 50 | N / No Edge |

Because factor pairs are complementary, the selected lean must be the side with the higher score. A tie is `N / No Edge`.

## Confidence / displayed-grade caps

These caps do not rewrite the raw score; they cap the displayed grade and are surfaced explicitly.

Apply all applicable caps; the most restrictive cap wins.

1. **Money unavailable** -> maximum displayed grade **B+**.
2. **Fewer than 4 verified factors** -> maximum displayed grade **B**.
3. **Fewer than 3 verified factors** -> maximum displayed grade **C+**.
4. **Two or more strongly opposing factors** (`side score <= 6`) -> maximum displayed grade **B**.
5. **Only 0–2 factors available at all** -> displayed state **INSUFFICIENT DATA** regardless of raw score.

### Factor verification status

- `verified`: complete source-backed input meeting freshness/reference requirements.
- `degraded`: real source-backed input is usable but subject to a configured cap/penalty (e.g. line-reference mismatch, stale-but-usable money, one-component Trends, or Key Numbers without a current-market comparison).
- `unavailable`: cannot be used as evidence; factor scores default to 10/10.

`verified factor count` includes only `verified`. `available factor count` includes `verified + degraded`.

## Alignment display

For the final lean side, count five factor states:
- supports: score >= 12
- neutral: 9–11
- opposes: <= 8
- strongly opposes: <= 6 (subset of opposes)

The UI must show the alignment count alongside the grade.

Examples:
- `4 support · 1 neutral · 0 oppose`
- `3 support · 0 neutral · 2 oppose`

## Correlation disclosure

Line Movement and Money both describe market behavior and can be correlated. They remain separate equal-weight challenger factors in v1.0 for interpretability, but the page must disclose that they are not independent evidence. Prospective results will determine whether future versions should reduce or combine their weight.

## Change-control rule

Once Week 4 scorecard outputs are generated under v1.0:
- do not change thresholds because a preferred team grades poorly;
- do not change thresholds because a game result later disagrees with the framework;
- bug fixes require a documented defect, a version bump, and recomputation of all affected games;
- any future reweighting must use prospective multi-week evidence and be versioned separately.
