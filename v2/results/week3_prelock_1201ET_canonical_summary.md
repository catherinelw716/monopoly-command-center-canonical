# Week 3 V2 Pre-Lock Canonical Summary — 2026-09-27 12:01 ET

Status: `PRELOCK_CANONICAL_RESEARCH`

## Market snapshot

Source snapshot: `v2/season_2026/week_03_current_market_2026-09-27_1201ET.json`

Material frozen-V2 price edges at this snapshot:

1. MIN -1.5 at TB — market about MIN -2.5; edge_per_dollar 0.060329
2. CLE +2.5 vs CAR — market about CAR -2 / CLE +2; edge_per_dollar 0.033713
3. WAS +7.5 vs SEA — market about SEA -7 / WAS +7; edge_per_dollar 0.033713
4. BUF -7 vs LAC — market about BUF -7.5; edge_per_dollar 0.033235
5. NE +3 at JAX — market about JAX -2.5 / NE +2.5; edge_per_dollar 0.027639

Market-equal games remain effectively neutral in the frozen V2 probability layer; contextual ranking may select them but must not manufacture allocation edge.

## 1,200-simulation robust pre-lock optimizer result

Parameters:
- Catherine deployment fraction: 0.10
- Amanda deployment fraction: 0.10
- Catherine games: 6
- Amanda games: 6
- Overlap mode: hybrid
- Household outlay: $2,100
- Base modeled future-minimum failure risk: 0.2197222222

### Catherine
- MIN -1.5 at TB — $400
- CLE +2.5 vs CAR — $200
- BUF -7 vs LAC — $200
- KC -10.5 at MIA — $100
- DEN +2.5 vs LAR — $100
- PIT +3.5 vs CIN — $100

Total: $1,100

### Amanda
- MIN -1.5 at TB — $300
- WAS +7.5 vs SEA — $200
- NE +3 at JAX — $200
- ARI +8.5 at SF — $100
- DAL +3.5 vs BAL — $100
- IND +1.5 vs HOU — $100

Total: $1,000

## Interpretation / guardrails

- The prior 11:20 ET $3,500 four-game-per-entry confirmation is stale after the 12:01 ET market movement.
- MIN -1.5 is now the strongest frozen-V2 price-derived edge and is intentionally shared by both entries.
- CLE +2.5 and WAS +7.5 replace the previously favored CAR -2.5 and SEA -7.5 sides because the live market moved through Sly’s number in the opposite direction.
- BUF -7 and NE +3 remain genuine price-derived edges, but receive smaller stakes in this robust multi-edge allocation because MIN/CLE/WAS now compete for edge capital.
- KC, DEN, PIT, ARI, DAL, and IND are supporting/contextual positions at the minimum wager; they should not be presented as equal-conviction plays.
- Weather and injuries remain contextual analysis fields and do not alter the frozen probability model directly.
- This file records the research optimizer output; it is not an automatic wager submission.

## Provenance

GitHub Actions run: `36331741690`
Job: `108654871675`
Run completed successfully on 2026-09-27 at approximately 12:04:50 ET.
