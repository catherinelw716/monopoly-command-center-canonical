# Week 4 Friday Model-Layer Audit

Status: `STEP_3_COMPLETE`

## What was run

The full 15-game Week 4 Sly slate was evaluated with the frozen prospective V2 probability model `V2-0006C-global-hybrid-r1` using the audited Step-2 market-history inputs.

For every game, the model was run separately against:
- VegasInsider Friday consensus;
- Action Network Friday line;
- the opening spread as a movement diagnostic only.

The model always evaluates cover/push/loss at **Sly's exact frozen spread**. Integer Sly numbers retain the empirical push correction from the frozen artifact.

## Interpretation guardrails

- A Sly line equal to the current market is `MARKET_EQUAL`. The frozen model's tiny residual directional bias (~0.2% EV) is diagnostic only and must not be promoted as a betting edge.
- When current sources disagree, their forecasts remain separate. No synthetic market number is manufactured.
- Opening-line outputs are not current predictions. They show what the Sly number would have looked like against the opener and help explain how the market evolved.
- Weeks 1-3 results did **not** refit this frozen probability model. Prospective validation remains intact.

## Friday model states

### Source-sensitive, same direction
- `DAL @ HOU`: HOU -3 is market-equal on VegasInsider but 0.5 points better than Action's HOU -3.5. Direction remains HOU across both source-specific model runs.
- `LAC @ SEA`: SEA -7 is market-equal on VegasInsider but 0.5 points better than Action's SEA -7.5. Direction remains SEA across both source-specific model runs.

### Source-disputed direction
- `NE @ BUF`: VegasInsider is market-equal at BUF -7; Action's BUF -6.5 makes Sly NE +7 favorable. No robust side is declared.
- `DEN @ SF`: VegasInsider is market-equal at SF -3; Action's SF -2.5 makes Sly DEN +3 favorable. No robust side is declared.
- `IND @ WAS`: VegasInsider's IND -4.5 makes Sly IND -3.5 materially favorable; Action is market-equal at IND -3.5. No cross-source robust side is declared.

### Market-equal on both preserved Friday sources
ARI @ NYG, ATL @ NO, TEN @ BAL, DET @ CAR, NYJ @ CHI, JAX @ CIN, GB @ TB, KC @ LV, LAR @ PHI, MIA @ MIN.

## Legacy V1 / M1-M5 audit finding

The versioned repository does **not** contain a generic, reproducible Week-4 V1 policy that can be rerun from raw market inputs. The preserved Week-3 V1 artifact explicitly identifies itself as a fixed legacy heuristic comparator and says not to derive a generic V1 policy formula from one slate. The older Command Center patches also contain hard-coded Week-3 rankings/grades rather than a reusable model implementation.

Therefore Step 3 does **not** fabricate fresh Week-4 V1 or M1-M5 probabilities. The reproducible Week-4 probability database is the frozen V2 layer above. Any legacy heuristic/source/context logic that should adapt from Weeks 1-3 belongs in Step 4 and must be made explicit/reproducible before it is allowed to influence Week-4 recommendations.

## Artifacts

- `v2/run_week4_friday_model_layer.py`
- `v2/results/week_04_friday_model_layer.json`
- `v2/week4_friday_model_layer_qa.py`
- `.github/workflows/v2-week4-model-layer.yml`
