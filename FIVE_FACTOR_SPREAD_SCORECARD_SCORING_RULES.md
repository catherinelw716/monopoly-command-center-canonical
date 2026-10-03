# Five-Factor Spread Scorecard — Preregistered Scoring Rules

**Version:** 1.0.1  
**Status:** Locked before Week 4 score generation  
**Purpose:** Exact deterministic scoring contract. No team/matchup-specific exceptions are allowed, and thresholds may not be changed after viewing Week 4 rankings unless a genuine implementation defect is documented and versioned.

## Global invariants

- Grade the immutable Sly contest spread only.
- Five factors, each 0–20 per side; neutral = 10/10.
- Every directional factor pair sums to 20; overall side totals therefore sum to 100.
- Equal factor weights: 20% each.
- Higher total is the Five-Factor lean; 50–50 is `N / No Edge`.
- The score is a heuristic score, **not** a cover probability.
- Source quality changes verification status/caps, never Sly.

Team-side spread convention: negative = favorite, positive = underdog.

For the final lean side: `supports >=12`, `neutral 9–11`, `opposes <=8`, `strongly_opposes <=6`.

## 1. Line Movement

For team T:

```text
movementTowardTeam = openingSpread(T) - currentSpread(T)
```

Thus `-2 → -7` is +5 toward that team; `-7 → -2` is -5 away from that team.

| Absolute movement | Supported | Opponent |
|---:|---:|---:|
| <0.50 | 10 | 10 |
| 0.50–0.99 | 12 | 8 |
| 1.00–1.49 | 14 | 6 |
| 1.50–1.99 | 16 | 4 |
| 2.00–2.99 | 18 | 2 |
| >=3.00 | 20 | 0 |

Use one designated primary market source for opener/current. Cross-check sources are retained, not averaged. If trusted cross-checks disagree on movement direction by >=0.5 points, cap the directional score at 14/6. Missing opener/current => 10/10 `unavailable`. Key-number crossings receive no extra Line Movement points.

## 2. ATS Trends

Components:
- H2H ATS last five meetings where available: 40%
- Current-season ATS: 35%
- Recent ATS, target last ten decisions: 25%

Pushes are excluded from win rate: `wins / (wins + losses)`.

| ATS win rate | Raw rating |
|---:|---:|
| >=70% | 20 |
| 65–69.9% | 18 |
| 60–64.9% | 16 |
| 55–59.9% | 14 |
| 52–54.9% | 12 |
| 48–51.9% | 10 |
| 45–47.9% | 8 |
| 40–44.9% | 6 |
| 35–39.9% | 4 |
| 30–34.9% | 2 |
| <30% | 0 |

Sample shrinkage toward 10:

```text
adjustedRating = 10 + (rawRating - 10) * sampleMultiplier
```

Multipliers: 1 decision .25; 2 .40; 3 .60; 4 .80; >=5 1.00.

H2H deviation gets a further recency multiplier: <=2 seasons 1.00; 3–5 seasons .75; >5 seasons .50.

Unavailable components are removed and remaining weights renormalized. If either team has only one usable component, factor status is `degraded` and directional strength is capped at 14/6.

After computing each team's weighted trend index:

| Absolute index difference | Better team | Opponent |
|---:|---:|---:|
| <1 | 10 | 10 |
| 1–2.9 | 12 | 8 |
| 3–4.9 | 14 | 6 |
| 5–6.9 | 16 | 4 |
| 7–8.9 | 18 | 2 |
| >=9 | 20 | 0 |

If either team has no usable ATS components, matchup Trends is 10/10 `unavailable`.

## 3. Money / Handle

Valid evidence must explicitly be **money %, handle %, or share of dollars wagered**. Bets %, tickets %, pick %, public %, or count of wagers never qualify.

Required: source, capture timestamp, exact reference spread, and both side percentages (or an unambiguous complement).

| Larger handle share | Larger-money side | Opponent |
|---:|---:|---:|
| <51% | 10 | 10 |
| 51–54.9% | 12 | 8 |
| 55–59.9% | 14 | 6 |
| 60–64.9% | 16 | 4 |
| 65–69.9% | 18 | 2 |
| >=70% | 20 | 0 |

Reference-line penalty: if money reference differs from Sly by >=1 point **or the interval between the two lines touches/crosses a configured key boundary (+/-3, 6, 7, 10, 14), including exact-key-to-hook cases such as -3 to -3.5**, cap directional strength at 14/6 and mark `degraded`.

Freshness at scorecard capture: <=6h fresh; >6–24h stale and capped at 14/6; >24h unavailable. Unverified semantics => unavailable.

## 4. Defense

Primary metric: current-season defensive EPA/play rank using one common source/methodology. Lower rank = better.

| Rank | Quality value |
|---:|---:|
| 1–5 | +5 |
| 6–10 | +3 |
| 11–22 | 0 |
| 23–27 | -3 |
| 28–32 | -5 |

Spread multiplier uses absolute Sly spread: 0–2.5=.5; 3–6.5=1.0; 7–9.5=1.5; >=10=2.0.

```text
defenseSupport = qualityValue * spreadMultiplier
```

Compare the two teams' support values:

| Absolute difference | Better-defense side | Opponent |
|---:|---:|---:|
| <1 | 10 | 10 |
| 1–2.9 | 12 | 8 |
| 3–4.9 | 14 | 6 |
| 5–6.9 | 16 | 4 |
| 7–8.9 | 18 | 2 |
| >=9 | 20 | 0 |

If comparable ranks are unavailable for either team, Defense = 10/10 `unavailable`.

## 5. NFL Key Numbers

| Key | Configured frequency | Hook strength |
|---:|---:|---:|
| 3 | ~15% | 6 |
| 7 | ~9% | 5 |
| 6 | ~8% | 4 |
| 10 | ~5% | 3 |
| 14 | ~5% | 3 |

These frequencies are heuristic configuration inputs, not a claim that this app independently re-estimated them.

### Intrinsic hook value

Evaluate **every** configured key exactly 0.5 from the absolute Sly spread (so 6.5 is assessed against both 6 and 7).

For a favorite: `-(key-0.5)` is favorable, `-(key+0.5)` unfavorable. For an underdog: `+(key+0.5)` is favorable, `+(key-0.5)` unfavorable. Add/subtract that key's hook strength and cap total intrinsic advantage at +/-10.

Exact +/- key has zero **intrinsic** directional advantage.

### Market-relative Sly value — v1.0.1 clarification

The approved feature spec requires Sly-vs-current-market position around keys to matter. Therefore, even when Sly lands exactly on a key, it may receive market-relative value.

For each key, if the numeric interval between the team's Sly spread and current market spread touches/crosses either `+key` or `-key`, add `ceil(hookStrength/2)` if Sly is the better number for that team and subtract it if Sly is worse. `Sly better` is deterministic: the team's Sly spread is numerically greater than its market spread.

Examples around 3:
- Sly favorite -2.5, market -3.5 => intrinsic +6 and relative +3 => 19/1.
- Sly dog +3.5, market +2.5 => 19/1.
- Sly dog +3, market +2.5 => intrinsic 0, relative +3 => 13/7.
- Sly favorite -3, market -3.5 => 13/7.
- Sly favorite -3.5, market -2.5 => 1/19, favoring the dog.

Missing current market retains intrinsic scoring but marks Key Numbers `degraded`.

## Overall grade

`overallScore = lineMovement + trends + money + defense + keyNumbers`

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
| 50 | N |

### Display caps

Most restrictive cap wins; raw score is never rewritten.

1. Money unavailable => max B+
2. Fewer than 4 `verified` factors => max B
3. Fewer than 3 `verified` factors => max C+
4. Two or more strongly opposing factors (lean-side score <=6) => max B
5. Only 0–2 available (`verified + degraded`) factors => `INSUFFICIENT DATA`

Statuses: `verified`, `degraded`, `unavailable`.

## Correlation disclosure

Line Movement and Money both describe market behavior and can be correlated. They remain separate equal-weight challenger factors in v1.0.1 for interpretability; they are not independent evidence. Prospective results will determine whether later versions combine or reduce their weight.

## Change control

After Week 4 outputs are generated:
- do not change thresholds because a preferred team grades poorly;
- do not change thresholds because a later result disagrees with the framework;
- bug fixes require a documented defect, version bump, and full affected recomputation;
- future reweighting requires prospective multi-week evidence.
