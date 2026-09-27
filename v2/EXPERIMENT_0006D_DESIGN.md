# V2-0006D — Global Hybrid Robustness / Wider-Offset Replication

Status: preregistered before execution. Research-only.

## Purpose
V2-0006C advanced the **global hybrid key-number correction**: normal market-based cover/loss probabilities plus an empirical exact-margin correction to push probability on integer spreads. 0006D asks whether that frozen architecture replicates outside the 2020–2025 development/evaluation era and whether its probability curve behaves sensibly over larger Sly-vs-market differences.

## Important interpretation
This is a **backward temporal replication**, not a sacred future holdout: the architecture was discovered using later seasons. It is useful evidence about era robustness but cannot substitute for prospective 2026 shadow validation.

## Frozen architecture
- Normal market-residual lattice cover/loss baseline.
- On integer target spreads only, replace normal push mass with global historical exact signed final-margin frequency.
- Rescale normal loss/cover probabilities proportionally to sum to `1 - P(push)`.
- Half-point lines remain exactly normal.
- No football/PBP features.
- No market-fair-spread conditioning.
- No game-total conditioning.

The only hyperparameter policy retained from 0006C is nested selection between shrinkage equivalent counts **25 and 75** using the last training season. No new hyperparameter values are introduced.

## Historical replication window
- Load seasons 2006–2019.
- Outer held-out seasons: 2010–2019, each trained only on earlier seasons.
- No data from 2020+ enters this execution.

## Target offsets
Evaluate target spread offsets from closing market from **-3.0 to +3.0 in 0.5-point steps**:
`[-3.0, -2.5, -2.0, -1.5, -1.0, -0.5, 0, +0.5, +1.0, +1.5, +2.0, +2.5, +3.0]`.

These are probability-shape tests only; they do not assert historical Sly availability.

## Primary metric / replication gate
Per-game mean **3-class Brier on integer target lines**.

Primary difference = normal Brier − global-hybrid Brier.

Replication gate requires:
1. positive mean season-level difference; and
2. season-bootstrap 95% CI lower bound > 0.

## Safety / calibration diagnostics
- per-game Brier over all 13 target offsets
- integer-line log loss
- all-offset log loss
- predicted vs observed integer push rate
- exact 3 and 7 push calibration
- predicted vs observed cover/push probability by target-line offset
- number of held-out seasons with positive integer-Brier improvement

## Decision rule
- If the hybrid replicates robustly, retain it as V2's historical key-number probability challenger and move to prospective 2026 shadow/calibration plus stale-line data collection.
- If it fails badly in the older era, do not silently discard the modern result; document era instability and require prospective evidence before relying on the hybrid.
- No production promotion from 0006D alone.
