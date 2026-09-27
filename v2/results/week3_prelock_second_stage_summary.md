# Week 3 Pre-lock Second-stage Sizing Summary

Snapshot: 2026-09-27 12:01 ET market refresh.

## Confirmed result
A coarse CRN sizing search first hit the 8% lower deployment boundary. A focused 3,000-simulation lower-bound confirmation then tested 5%, 6%, 7%, 8%, 10%, and 12% deployment across the leading 4/5/6-game structures.

Best robust configuration:
- Catherine: 6 games, 5% target deployment, $600 total
  - MIN -1.5 $100
  - CLE +2.5 $100
  - BUF -7 $100
  - KC -10.5 $100
  - DEN +2.5 $100
  - PIT +3.5 $100
- Amanda: 4 games, 5% target deployment, $500 total
  - MIN -1.5 $200
  - WAS +7.5 $100
  - NE +3 $100
  - ARI +8.5 $100
- Household outlay: $1,100
- Robust floor utility: 0.00297042
- Robust average utility: 0.00719055
- Base expected household prize share: 0.00970333
- Base P(any cash): 0.0692222
- Base future-minimum failure risk: 0.229889

## Interpretation
The low deployment is not a coarse-grid artifact. Under the current robust objective, the marginal tournament value of adding stake is smaller than the CVaR/future-bankroll penalty once the material price edges are already represented. The optimizer therefore prefers broad minimum exposure plus only a small increment on the strongest refreshed edge (MIN for Amanda).

This is a V2 research sizing result. It does not change the underlying football probabilities, and it should not be interpreted as saying the price edges are nonexistent; it says the current tournament-risk objective values preserving future optionality more than increasing Week 3 exposure.
