# V2-0006B — Corrected Absolute-Margin Results

Status: COMPLETE. Research-only; no production changes.

## Verdict
**FAIL AGGREGATE GATE for full discrete replacement.** The spread-conditioned absolute-margin model did not robustly beat the normal lattice baseline on the preregistered per-game 3-class Brier metric.

This is **not** a rejection of key-number/discrete information. The corrected model materially improved push calibration, including the exact 3- and 7-point margins that V2-0006A failed to represent. The result instead says that replacing the entire normal cover/loss distribution with the empirical discrete distribution is too aggressive.

## Held-out design
- 1,615 regular-season games.
- Outer held-out seasons: 2020–2025.
- Training data: prior seasons only.
- No 2026 outcomes.
- Seven exact-line offsets per game: -1.5, -1.0, -0.5, 0, +0.5, +1.0, +1.5 relative to closing market.
- Per-game mean across offsets was used before season-level comparison.
- Closing market is a research fair-line baseline, not a historical Sly-Friday reconstruction.

## Aggregate results

| Model | Per-game Brier3 | Log loss | Closing Brier3 | Closing non-push binary Brier | Integer push predicted | Integer push observed |
|---|---:|---:|---:|---:|---:|---:|
| Normal lattice | **0.515859** | 0.761612 | **0.519105** | **0.249954** | 3.103% | 4.020% |
| Spread-conditioned discrete | 0.517467 | 0.760819 | 0.521229 | 0.251251 | **3.778%** | 4.020% |
| Spread+total discrete | 0.517103 | **0.760478** | 0.520859 | 0.251077 | 3.743% | 4.020% |

Primary normal-minus-spread-only Brier difference: **-0.001606**. Season-bootstrap 95% CI: **[-0.003717, +0.000573]**. A positive value would favor the discrete model; this gate therefore failed.

Adding total improved spread-only Brier by **+0.000364**, but the season-bootstrap 95% CI **[-0.000337, +0.000879]** includes zero. Total has not earned incremental weight.

## Key-number QA
The corrected absolute-margin model fixed the structural defect discovered in V2-0006A.

| Exact absolute spread | Normal predicted push | Spread-conditioned predicted push | Observed push |
|---:|---:|---:|---:|
| 3 | 3.108% | **8.079%** | **9.613%** |
| 7 | 3.105% | **5.662%** | **4.825%** |

Half-point lines correctly have zero push probability.

This is important evidence that NFL integer final-margin mass must be represented when valuing moves across key numbers, even though the full discrete model should not replace the normal cover/loss distribution.

## Line-advantage calibration
The spread-conditioned discrete model's average predicted cover curve tracked observed cover rates in the expected monotonic direction. Examples:
- market -1.5 points: predicted cover 42.06%, observed 42.41%
- market -1.0: 43.88% vs 44.58%
- market -0.5: 45.33% vs 46.07%
- market 0: 47.68% vs 48.61%
- market +0.5: 49.96% vs 50.65%
- market +1.0: 52.21% vs 53.07%
- market +1.5: 53.72% vs 54.74%

The consistent underprediction of cover at these offsets is a calibration issue to address later; it is not permission to manually shift probabilities after seeing the test set.

## Decision
1. Do **not** promote the full spread-conditioned or spread+total discrete distributions.
2. Preserve the normal market-based cover/loss structure as the research baseline.
3. Advance a preregistered **hybrid key-number model** that changes only integer-line push mass using historical absolute final-margin frequencies, while retaining the normal model's conditional cover/loss split.
4. Do not add total to the hybrid unless a later registered experiment proves incremental value.
5. V2 remains research-only and V1 remains production champion.
