# V2-0006D — Global Hybrid Robustness Replication Results

Status: COMPLETE. Research-only; no production V1 change.

## Verdict
**REPLICATION PASS.** The frozen global hybrid key-number architecture robustly improved integer-line probability quality in the independent older-era replication and also improved the broader ±3-point line-offset safety metric.

This strengthens the historical case for the global hybrid, but 0006D is a backward temporal replication rather than a sacred future holdout. Prospective 2026 shadow evidence remains required.

## Design
- Historical input seasons: 2006–2019 only.
- Outer held-out seasons: 2010–2019.
- 2,560 unique held-out regular-season games.
- No 2020+ outcomes entered the execution.
- Global hybrid architecture was frozen from V2-0006C.
- Nested shrinkage selection retained only the already-approved 25/75 policy.
- Target-line offsets expanded to -3.0 through +3.0 in 0.5-point increments.

## Primary replication
Mean normal-minus-global-hybrid integer-line 3-class Brier improvement: **+0.00062694**.

Season-bootstrap 95% CI: **[+0.00038959, +0.00087642]**.

Positive held-out seasons: **10 / 10**.

This clears the preregistered replication gate.

## Broader safety metric
Mean normal-minus-hybrid all-offset Brier improvement: **+0.00031866**.

Season-bootstrap 95% CI: **[+0.00019789, +0.00045035]**.

Thus the key-number correction remained beneficial across the wider synthetic ±3-point target-line range rather than improving only the narrow original offsets.

## Aggregate metrics

| Model | Integer Brier3 | Integer log loss | All-offset Brier3 | All-offset log loss | Integer push predicted / observed |
|---|---:|---:|---:|---:|---:|
| Normal | 0.522726 | 0.806094 | 0.507332 | 0.746025 | 2.884% / 3.269% |
| Global hybrid | **0.522099** | **0.800249** | **0.507014** | **0.743060** | 2.637% / 3.269% |

The aggregate push-rate average includes many integer target values whose true mass is small; exact key-number diagnostics are more informative for the structural mechanism.

## Key-number example
At exact |target spread| = 3:
- normal predicted push: **2.895%**
- global hybrid predicted push: **7.391%**
- observed push: **8.586%**

The hybrid again captures substantially more of the real 3-point final-margin mass than the normal lattice model.

## Combined interpretation with 0006C
Modern held-out period (2020–2025): global hybrid robustly beat normal on integer-line Brier with 95% CI above zero; five of six seasons improved.

Older replication period (2010–2019): global hybrid robustly beat normal with 95% CI above zero; ten of ten seasons improved.

The same narrow mechanism—empirical exact-margin push correction while preserving normal cover/loss structure—therefore shows stability across both periods.

## Decision
1. Retain **market-anchored normal cover/loss + global empirical integer push correction** as the leading V2 historical probability architecture.
2. Do not resurrect rejected rolling football residual features.
3. Do not add spread conditioning or total to the key-number layer; those additions did not earn complexity.
4. Stop retrospective architecture iteration on this component unless a registered QA issue emerges.
5. Advance to **prospective 2026 shadow validation**, with predictions frozen before outcomes.
6. Begin/continue point-in-time Sly/market snapshot capture so the uniquely Monopoly-specific stale-line edge can eventually be evaluated honestly.
7. This historical evidence still does not promote V2 into production; V1 remains production champion until the remaining V2/Monopoly gates are satisfied.
