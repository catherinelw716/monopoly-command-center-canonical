# V2-0006C — Hybrid Key-Number Push Correction Results

Status: COMPLETE. Research-only; no production V1 change.

## Verdict
**PASS HYBRID; CONDITIONING NOT PROVEN.** A targeted empirical exact-margin push correction robustly improved probability quality on integer target lines while also improving the all-offset safety metric. Conditioning the push estimate on market fair spread did not robustly outperform the simpler global exact-margin hybrid, so the simpler global hybrid advances.

## Held-out design
- Regular-season games 2016–2025; outer held-out seasons 2020–2025.
- 1,615 unique held-out games.
- No 2026 outcomes.
- Normal market-residual lattice model is unchanged baseline.
- Hybrid changes only push mass at integer target lines; half-point lines are exactly the normal baseline.
- Push mass comes from historical exact signed final-margin frequency with shrinkage toward the normal push estimate.
- Seven target offsets around closing market were evaluated; integer-line Brier was preregistered as primary because half-point predictions are structurally unchanged.

## Primary results

### Spread-conditioned hybrid vs normal
Mean normal-minus-hybrid integer-line Brier improvement: **+0.0007502**.

Season-bootstrap 95% CI: **[+0.0002911, +0.0011872]**.

This clears the preregistered primary gate.

### Global hybrid vs normal
Mean normal-minus-global-hybrid integer-line Brier improvement: **+0.0007108**.

Season-bootstrap 95% CI: **[+0.0002889, +0.0010985]**.

The simpler global hybrid also robustly clears the gate.

### Does spread conditioning add value?
Global-minus-spread-conditioned improvement: **+0.0000394** with 95% CI **[-0.0000417, +0.0001109]**.

The interval includes zero. **Spread conditioning has not earned extra complexity.** Prefer the global hybrid.

### All-offset safety metric
Normal-minus-spread-hybrid all-offset Brier: **+0.0003954**, 95% CI **[+0.0001569, +0.0005976]**.

Thus the targeted correction improved, rather than degraded, the broader seven-offset probability score.

## Aggregate probability metrics

| Model | Integer Brier3 | Integer log loss | All-offset Brier3 | All-offset log loss | Closing Brier3 |
|---|---:|---:|---:|---:|---:|
| Normal | 0.534331 | 0.830950 | 0.515859 | 0.761612 | 0.519105 |
| Global hybrid | **0.533619** | **0.825353** | **0.515491** | **0.758710** | **0.518545** |
| Spread-conditioned hybrid | 0.533578 | 0.825032 | 0.515463 | 0.758483 | 0.518602 |

The spread-conditioned model is numerically slightly better on some aggregate metrics, but the direct global-vs-conditioned season comparison is not statistically robust. Simplicity therefore wins.

## Season stability
Integer Brier, normal vs global hybrid:
- 2020: 0.53345 → 0.53294 (improved)
- 2021: 0.52860 → 0.52870 (small deterioration)
- 2022: 0.53572 → 0.53434 (improved)
- 2023: 0.54189 → 0.54093 (improved)
- 2024: 0.53003 → 0.52888 (improved)
- 2025: 0.53625 → 0.53588 (improved)

Five of six held-out seasons improved.

## Key-number calibration
The spread-conditioned version (used here only to confirm the mechanism) predicted:
- exact |spread| 3 push: **7.93%** vs **9.61% observed**
- exact |spread| 7 push: **5.45%** vs **4.82% observed**

The normal baseline predicted only about **3.11%** at both key numbers. This confirms the structural value of representing NFL final-margin mass without replacing the normal cover/loss distribution.

## Decision
1. Advance the **global hybrid key-number correction** as the V2 research probability challenger because it robustly improves the normal baseline and is simpler than the conditioned alternative.
2. Do not add spread conditioning or game total to the push layer; neither has earned incremental complexity.
3. Keep market-based normal cover/loss structure. The empirical component changes only integer-line push mass.
4. Do not add the rejected football residual features.
5. Next stage: frozen-model robustness/calibration validation across a wider historical window and prospective 2026 shadow use. No production promotion yet.
