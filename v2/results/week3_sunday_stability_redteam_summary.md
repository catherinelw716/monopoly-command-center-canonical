# Week 3 Sunday V2 stability / red-team summary

Date: 2026-09-27

## Test design
The contextual V2 optimizer was rerun across 15 combinations: five RNG seeds (716, 1716, 2716, 3716, 4716) and three small contextual-score perturbations (-0.15, 0, +0.15). Frozen NFL probabilities were unchanged. Context continued to operate only below the 1.0% material-edge threshold and never created allocation edge.

## Stable game-selection findings
The two material market edges were completely stable:
- Catherine — BUF -7 vs LAC: selected in 15/15 runs (100%). Median amount when selected $1,900; range $1,900-$3,500.
- Amanda — NE +3 at JAX: selected in 15/15 runs (100%). Median amount when selected $700; range $700-$3,200.

The strongest contextual supporting games were also selected in 15/15 runs at the $100 minimum:
- Catherine — CAR -2.5 at CLE
- Catherine — KC -10.5 at MIA
- Catherine — ARI +8.5 at SF
- Amanda — SEA -7.5 at WAS
- Amanda — MIN -1.5 at TB
- Amanda — DEN +2.5 vs LAR

BAL/DAL appeared for Catherine in only 40% of runs and should be treated as a fragile extra slot rather than a stable recommendation. Other lower-tier supporting slots below the printed 40% threshold are also fragile.

## Stake/deployment instability
Stake sizing was not stable enough to canonize the prior single-run $800 BUF / $500 NE amounts.

Across the 15 runs:
- Household outlay: mean $4,600; median $4,200; p10 $3,200; p90 $7,500; range $3,200-$7,500.
- Most common parameter set (40% of runs): Catherine 20% deployment / 4 games; Amanda 10% / 4 games; split mode.
- Next most common (20%): Catherine 20%; Amanda 20%; four games each; split mode.
- All top parameter configurations used split mode, but deployment fraction and exact game count varied materially.

This means the optimizer currently has a stable view of WHICH material-edge games matter, but not yet a sufficiently stable view of HOW MUCH to wager on them.

## Metric stability
Across the 15 runs:
- Expected household prize share: mean 0.01307; median 0.01205; range 0.01096-0.01805.
- P(any cash): mean 0.07733; median 0.07467; range 0.06933-0.08933.
- Future-minimum failure risk: mean 0.25893; median 0.26667; range 0.22400-0.31067.
- Robust floor utility: mean 0.003258; median 0.003226; range 0.002349-0.004064.

## Red-team conclusion
Game selection is substantially more robust than stake sizing. BUF -7 and NE +3 survive every seed/context perturbation and remain the only material V2 market-price edges. The six strongest contextual minimum positions listed above also survive every run, but their $100 sizing reflects contest/minimum-game portfolio construction rather than model edge.

The prior single-run ~10% household deployment should NOT be treated as a stable optimizer conclusion. The next V2-0009 engineering step is to reduce Monte Carlo / selection noise in sizing before using exact wager amounts. A principled approach is to evaluate a fixed candidate set with common random numbers and substantially more simulations in a second-stage sizing pass, while preserving the current game-selection and probability guardrails.
