# V2 Experiments 001–002 — First Walk-Forward Results

**Run date:** 2026-09-27  
**Research service:** `monopoly-v2-research` (isolated from production)  
**Historical seasons loaded:** 2016–2025  
**Held-out test seasons:** 2020–2025  
**Held-out games:** 1,615  
**2026 outcomes used:** No

## Question

Does a simple leakage-safe football residual model using lagged play-by-play efficiency improve prediction beyond the closing NFL market spread?

This is deliberately a narrow first test. It is **not** a Friday/Sly stale-line backtest and it does not yet include injuries, QB starter modeling, public betting, SportsLine, Gridiron, Lucas, or intra-week market path.

## Models

### Market baseline
- Predicted home margin = negative of the normalized closing home spread.
- This is the minimum hurdle for V2.

### Ridge residual challenger
- Target: `actual_home_margin - market_predicted_home_margin`.
- Features: lagged prior-game PBP efficiency only, using 4-game and 8-game rolling windows plus basic market/rest context.
- Features are shifted by one completed team game to prevent target-game leakage.
- Ridge alpha is selected inside each outer training window using the last available training season as an inner validation season.

## Aggregate results

| Metric | Market baseline | Ridge residual | Market − Ridge |
|---|---:|---:|---:|
| Margin MAE | **9.764** | 9.831 | **-0.067** |
| Margin RMSE | **12.637** | 12.710 | **-0.074** |
| ATS Brier* | **0.2500** | 0.2516 | **-0.0016** |
| Ridge selected-side ATS hit rate* | — | 51.01% | — |

`*` ATS probability outputs are preliminary diagnostics using an uncalibrated normal residual approximation. They are **not** production-quality cover probabilities and do not substitute for the registered discrete-margin/calibration experiments.

### Robustness

Market-minus-Ridge margin-MAE improvement by season averaged **-0.0665 points**.

Season-level bootstrap 95% interval: **[-0.1733, +0.0313]**.

Preliminary Brier improvement averaged **-0.00155**, with season bootstrap 95% interval **[-0.00482, +0.00112]**.

Interpretation: the first Ridge specification does **not** provide evidence that naive rolling PBP efficiency improves on the closing market baseline.

## Season folds

| Test season | Market MAE | Ridge MAE | Selected alpha |
|---:|---:|---:|---:|
| 2020 | **9.830** | 10.119 | 100.0 |
| 2021 | 10.781 | **10.694** | 100.0 |
| 2022 | **8.742** | 8.785 | 100.0 |
| 2023 | **9.901** | 10.084 | 0.1 |
| 2024 | 9.610 | **9.574** | 100.0 |
| 2025 | **9.722** | 9.730 | 100.0 |

Ridge improved MAE in 2021 and 2024, but worsened it in the other four held-out seasons. The selected alpha was strongly regularized (100) in five of six folds, another signal that the market leaves little stable linear residual signal in this first feature set.

## Decision

**Market-only remains the research champion baseline.**

**Reject this first Ridge specification as a production challenger.**

This is a useful result, not a failure of the V2 plan. It supports the original design principle that the market is a formidable prior and that football features must earn incremental weight out of sample.

## Next registered diagnostic

Before adding Bayesian or boosting complexity, run V2-0003 / ablations:

1. roll4 only
2. roll8 only
3. roll4 + roll8
4. passing-efficiency family only
5. total EPA/success family only
6. remove rest/context
7. early-season vs later-season subgroup analysis
8. favorite/dog and spread-magnitude subgroup analysis

If none of these demonstrate stable incremental value, keep the predictive core more market-centric and move next to the discrete-margin/key-number layer, where the edge may be in **pricing Sly's exact stale number** rather than forecasting final margin better than the closing market.

## Guardrail

Do not use this result to tune Week 3 2026 recommendations retrospectively. V1 remains production champion; V2 remains research-only.
