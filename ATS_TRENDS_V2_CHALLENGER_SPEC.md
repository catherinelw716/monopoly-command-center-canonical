# ATS Trends v2 Challenger — Preregistered Design

**Status:** Parallel challenger only. Does **not** modify the locked Week 4 Five-Factor v1 scorecard, V2 NFL model, or Monopoly optimizer.

## Why this exists
The v1 ATS Trends factor is transparent but has four methodological weaknesses:
1. H2H ATS receives too much weight (40%).
2. Current-season ATS and recent-10 ATS overlap, so some games are counted twice.
3. Binary cover/no-cover throws away cover-margin information.
4. Early-season ATS samples are tiny and can look more meaningful than they are.

v2 is designed to test whether a cleaner trend signal is more useful prospectively. It must not be promoted based on Week 4 rankings or outcomes.

## v2 inputs
For each team, v2 uses three **non-overlapping** components:

1. **Current-season ATS cover margin — 45%**
   - Every completed current-season game before the target matchup.
   - Cover margin = actual scoring margin from the team's perspective minus closing/reference spread from the team's perspective.
   - Positive means the team beat the spread; negative means it fell short.

2. **Prior-form ATS cover margin — 40%**
   - Target: last 8 completed games immediately preceding the current season.
   - This window must not contain any current-season game.

3. **H2H ATS — 15% maximum**
   - Last five prior meetings where available.
   - Binary W/L ATS record is allowed here because historic game-level cover margins may not always be available.
   - Age decay remains mandatory.

If a component is unavailable, remaining component weights are renormalized. If only one component is usable, the matchup factor is degraded and directional strength is capped at 14/6.

## Recency weighting for cover margins
Within each cover-margin sequence, observations are ordered oldest -> newest.

Use exponential half-life weighting:
- current season half-life: **4 games**
- prior-form half-life: **6 games**

For observation age `a` games from the most recent observation:

```text
weight = 0.5 ** (a / halfLife)
```

The weighted mean cover margin is:

```text
meanMargin = sum(weight_i * margin_i) / sum(weight_i)
```

## Sample shrinkage
Shrink cover-margin signals toward neutral before converting to a 0–20 rating.

```text
sampleMultiplier = min(1, n / targetN)
adjustedMeanMargin = meanMargin * sampleMultiplier
```

Targets:
- current season: `targetN = 8`
- prior form: `targetN = 8`

This means a three-game 2026 sample receives only 37.5% of its raw cover-margin signal.

## Margin-to-rating transform
Convert adjusted mean cover margin to a bounded 0–20 rating:

```text
rating = 10 + 10 * tanh(adjustedMeanMargin / 6)
```

Interpretation:
- 10 = neutral
- positive cover margin >10
- negative cover margin <10
- extreme historical margins asymptotically approach 20 or 0 rather than exploding.

## H2H treatment
H2H uses the existing v1 binary ATS-rate rating and sample shrinkage, but its maximum component weight is only 15%.

Age multiplier on H2H deviation from 10:
- most recent meeting <=2 seasons ago: 1.00
- 3–5 seasons: 0.75
- >5 seasons: 0.50

## Team trend index

```text
trendIndex = weighted average of available component ratings
```

Weights are 45% current-season margin / 40% prior-form margin / 15% H2H, renormalized over available components.

## Matchup score
Compare the two teams' trend indices using the same directional bands as Five-Factor v1 so that challenger results remain interpretable:

| Absolute index difference | Better team | Opponent |
|---:|---:|---:|
| <1 | 10 | 10 |
| 1–2.9 | 12 | 8 |
| 3–4.9 | 14 | 6 |
| 5–6.9 | 16 | 4 |
| 7–8.9 | 18 | 2 |
| >=9 | 20 | 0 |

## Data contract
A team-side input may contain:

```json
{
  "currentSeasonMargins": [1.5, -3.0, 7.5],
  "priorFormMargins": [-2.5, 4.0, 1.0, 6.5],
  "h2h": {"w": 3, "l": 2, "p": 0, "mostRecentSeasonsAgo": 1}
}
```

Margins must come from source-backed game results plus the contemporaneous reference spread used for the ATS decision. Do not infer them from a team's aggregate ATS record.

## Week 4 policy
The current Week 4 scorecard input has aggregate ATS W/L/P records but does **not** contain source-backed game-by-game cover margins. Therefore:
- v1 remains the published Week 4 factor;
- v2 code may be implemented and QA'd with synthetic fixtures;
- Week 4 v2 rankings must remain `DATA_PENDING` until source-backed margin sequences are added;
- never backfill margins by guessing or converting aggregate W/L records.

## Promotion rule
Do not replace v1 because v2 looks intuitively better or because one week's outcomes favor it. Track both prospectively across multiple weeks, then compare directional accuracy, calibration-like separation by score bands, stability, and incremental value versus the other Four/Five-Factor signals.
