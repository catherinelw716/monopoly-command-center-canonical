# V2 Diagnostic Feature Ablation Results

Date: 2026-09-27
Status: COMPLETE — research only; no production change.

## Question
After the first broad Ridge residual challenger failed to beat the closing-market baseline, can a smaller/cleaner football feature set add stable out-of-sample predictive information?

## Validation
- Seasons loaded: 2016–2025
- Held-out walk-forward test seasons: 2020–2025
- Closing market spread retained as the research baseline
- Football features use shifted prior-game PBP only
- Ridge regularization chosen inside each historical training window
- No 2026 outcomes used
- Positive `MAE improvement` means the Ridge residual model lowered margin MAE versus market

## Results

| Variant | Feature count | MAE improvement vs market | 95% season-bootstrap CI | Selected-side ATS hit |
|---|---:|---:|---:|---:|
| roll8_all | 13 | **-0.0366** | [-0.1159, +0.0366] | 52.09% |
| passing_only | 8 | -0.0475 | [-0.1597, +0.0228] | 50.51% |
| roll4_all | 13 | -0.0539 | [-0.1216, +0.0117] | 51.52% |
| epa_success_no_rest | 20 | -0.0646 | [-0.1707, +0.0268] | 50.82% |
| roll4_plus_roll8 | 21 | -0.0665 | [-0.1733, +0.0315] | 51.01% |
| epa_success_with_rest | 21 | -0.0665 | [-0.1733, +0.0315] | 51.01% |

**Verdict:** No compact football feature set beat the closing-market baseline on average. Market-only remains the V2 research champion.

## Diagnostic subgroup observations for the best variant (`roll8_all`)

These results are **post-hoc diagnostics only**. They are not promotion evidence and must not be used to tune production without a separately preregistered validation test.

### Season phase
- Weeks 1–5: n=471; MAE gain **+0.0619**; selected-side hit 55.19%
- Weeks 6–10: n=427; MAE gain -0.0608; selected-side hit 49.04%
- Weeks 11+: n=717; MAE gain -0.0830; selected-side hit 51.85%

### Home favorite / underdog
- Home favorite: n=963; MAE gain **+0.0589**; selected-side hit 53.55%
- Home underdog: n=652; MAE gain -0.1734; selected-side hit 49.92%

### Closing spread magnitude
- 0 to 2.5: n=378; MAE gain -0.0025; selected-side hit 53.32%
- 3 to 3.5: n=393; MAE gain **+0.0524**; selected-side hit 55.76%
- 4 to 6.5: n=377; MAE gain -0.0306; selected-side hit 51.34%
- 7 to 9.5: n=269; MAE gain -0.0999; selected-side hit 49.81%
- 10+: n=198; MAE gain -0.1899; selected-side hit 47.12%

## Interpretation

The broad conclusion is stronger after ablation: simple rolling efficiency adjustments do not improve on the closing market overall. The apparent early-season/home-favorite/key-3 subgroup performance is interesting, but because those patterns were discovered after examining the data, they are vulnerable to multiple-comparison noise.

Do **not** retrofit V2 around those subgroups. If we later want to test them, create a preregistered challenger and validate on untouched/prospective data.

## Research decision

1. Keep market-only as the V2 fair-margin research champion.
2. Do not advance Bayesian/boosting complexity simply to search for an edge in the same noisy feature family.
3. Prioritize registered experiment **V2-0006: discrete empirical margin / key-number probability modeling**.
4. Preserve the uniquely Monopoly-specific stale-line hypothesis (Sly frozen line vs later market) as a separate structural edge to test when point-in-time historical odds are available or prospectively.
5. Continue treating external sources as benchmarks until prospective samples support incremental weighting.
