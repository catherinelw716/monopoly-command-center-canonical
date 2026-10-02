# Week 4 Friday — Step 8B Sizing Calibration Review

Status: **PROVISIONAL / NOT SUBMISSION-READY**

This pass does not change any NFL probabilities. It isolates the stake-sizing question after the original Step-8 optimizer selected a $1,400 household outlay. The calibration reran the tournament optimizer at fixed 10%, 15%, 20%, 25%, 30%, and 35% per-entry deployment bands, with the same Friday model state, field scenarios, edge-shrink stresses, CVaR control, and HOU/SEA-only sizing-edge policy. CI run `37065845070` passed.

## Base Friday state comparison

| Target band | Actual household outlay | Household % | Robust floor | Exp. household prize share | Future-minimum risk | Min entry 10% CVaR retention | Selected overlap |
|---|---:|---:|---:|---:|---:|---:|---:|
| 10% | $1,800 | 9.2% | 0.002344 | 0.008278 | 27.69% | 92.01% | 94.4% |
| 15% | $2,900 | 14.9% | 0.002439 | 0.008681 | 27.83% | 86.45% | 96.6% |
| 20% | $3,800 | 19.5% | **0.002493** | 0.009244 | 28.14% | 81.82% | 100.0% |
| 25% | $4,800 | 24.6% | 0.002362 | 0.010797 | 29.86% | 76.41% | 0.0% |
| 30% | $5,800 | 29.7% | 0.002274 | **0.011536** | 31.53% | 71.78% | 0.0% |
| 35% | $6,700 | 34.4% | 0.002135 | 0.010628 | 29.53% | 66.92% | 100.0% |

Simulation estimates are diagnostic, not precise probabilities. The structural signal is more important than small differences between adjacent bands.

## Working interpretation

The original $1,400 portfolio was too close to a capital-preservation floor. The 15–20% region increases deployment materially without the sharp deterioration in robust-floor utility seen above 20%. The **20% band is the current Friday working calibration point** because it has the strongest robust-floor utility of the tested base-state bands while keeping household outlay at $3,800, below prior-week household deployment levels.

At 20%, the Friday base-state portfolio was:

### Catherine — $2,100 total
- SEA -7 — $900
- HOU -3 — $900
- NO -2.5 — $100
- CIN -2.5 — $100
- LV +4.5 — $100

### Amanda — $1,700 total
- SEA -7 — $700
- HOU -3 — $700
- NO -2.5 — $100
- CIN -2.5 — $100
- LV +4.5 — $100

Only SEA and HOU are sizing positions. NO/CIN/LV remain contest-compliance/context fillers at the minimum wager and must not be presented as validated ATS edges.

## Red-team interpretation

The 25–30% bands increase raw simulated prize opportunity, but they do so by concentrating roughly $4,000–$5,000 of household capital into two Friday **source-sensitive** edges. At 25%, the optimizer effectively separates the entries and concentrates one heavily on HOU and the other on SEA; at 30%, that concentration becomes still larger. Given that VegasInsider made both HOU and SEA essentially market-equal while Action supplied the half-point advantage, that concentration is not supported strongly enough on Friday.

The 20% band is therefore not a final wager recommendation. It is the **provisional sizing target for the Sunday rerun**. If Sunday confirms broader-market stale value on HOU/SEA and/or creates a real IND -3.5 edge, the same calibration framework can justify moving above $3,800 and spreading the additional capital across more than two validated positions. If those edges disappear, deployment should contract.

## Zero-edge stress

The zero-edge calibration was also run across all six bands. As deployment rises, the optimizer increasingly changes overlap and spreads capital across nominal fillers because HOU/SEA no longer possess a sizing edge. That is a warning against using the high-deployment base portfolios mechanically: their attractiveness depends materially on treating Friday's HOU/SEA half-point signal as real.

## Step-8B conclusion

- $1,400 is retained as the conservative floor, not the preferred working deployment.
- $2,900–$3,800 is the defensible Friday sizing region from this calibration.
- **$3,800 / ~19.5% household deployment is the current working target for Sunday PRE_KICK_FINAL.**
- $4,800+ requires materially stronger Sunday confirmation or additional validated edges.
- Step 9 reconciliation should use the calibrated portfolio only after the user reviews this sizing adjustment.
