# Week 4 Friday Context / Red-Team Review — 2026-10-02

Status: `FRIDAY_CONTEXT_REVIEW`

This review is downstream of the frozen V2 probability layer. Context may change ranking/portfolio preference among weak or disputed edges, but it does not change P(cover/push/loss).

## Canonical Sly freeze

Source: `v2/season_2026/week_04_sly_freeze.json`

The user-supplied Sly sheet contains 15 Sunday/Monday official spreads. PIT @ CLE is present as the already-Thursday game but has no Sly spread in the Friday sheet and is excluded rather than inferred.

## Market-source disagreement matters

Two Friday market snapshots are preserved:

1. VegasInsider consensus, updated 12:30 PM ET.
2. Action Network live odds/public-betting view observed around 1:03 PM ET.

The sources do not agree on every spread. Therefore, do not convert a single-source half-point difference into false certainty.

### Stronger / more actionable Friday Sly-price candidates

**SEA -7 vs LAC**
- Sly: SEA -7.
- Action and Gridiron-style aggregate: SEA about -7.5; VegasInsider consensus showed -7.
- Frozen V2 using Action line: material edge_per_dollar about 3.32%.
- Chargers injury context is adverse: WR Ladd McConkey went from limited Wednesday to DNP Thursday; multiple Chargers defenders/linemen are also on the report.
- Seattle's Thursday report improved in several areas, including Grey Zabel, Jarran Reed and Leonard Williams moving to full participation, while Julian Love remained limited.
- Friday interpretation: **positive candidate, but confirm Sunday line/inactives before final sizing.**

**HOU -3 vs DAL**
- Sly: HOU -3.
- Action and another aggregate show HOU around -3.5; VegasInsider consensus showed -3.
- Frozen V2 using Action line: material edge_per_dollar about 3.21%.
- Houston may regain WR Nico Collins; Thursday reports still had him limited. Dallas has secondary/defensive injuries, including Cobie Durant out of practice and other defensive players limited/DNP.
- Friday interpretation: **positive candidate if the broader market remains -3.5 and Collins trends toward playing.**

**DEN +3 at SF**
- Sly: DEN +3.
- Action/another aggregate: DEN +2.5; VegasInsider consensus: +3.
- Frozen V2 using Action line: material edge_per_dollar about 2.76%.
- San Francisco is dealing with substantial WR/defensive injury volume; Brandin Cooks was elevated amid the WR shortage. Extreme heat around the mid-90s is also forecast for Levi's Stadium, relevant to game context but not baked into the model.
- Friday interpretation: **watch/positive; source disagreement prevents a stronger price-edge label yet.**

### Model edge but contextual downgrade

**NE +7 at BUF**
- Sly: NE +7.
- Action: NE +6.5; VegasInsider: +7; another aggregate: +7.5.
- Action-based frozen V2 therefore points to NE +7, but the market sources materially disagree.
- New England has important injury concerns: Christian Barmore, Christian Gonzalez and Morgan Moses were DNP Thursday; Drake Maye was full participation. Buffalo QB Josh Allen is clear, though CB Christian Benford is out.
- Friday interpretation: **do not treat the Action-only half-point as a clean stale-price edge. Keep on watch rather than automatic play.**

### Contextual candidate with market disagreement

**IND -3.5 vs WAS (London)**
- Sly: IND -3.5.
- Action and NFL.com showed IND -3.5; VegasInsider consensus and another aggregate showed IND -4.5.
- Therefore the 1-point stale-price signal is not cross-source robust at Friday midday.
- Washington QB Jayden Daniels has been ruled out; Marcus Mariota will start. Washington also has Sam Cosmi and Nick Cross out, while several others remain on the report. Indianapolis has some injury uncertainty around Keenan Allen and Mo Alie-Cox, with Jonathan Taylor and Charvarius Ward returning to full participation Thursday.
- Friday interpretation: **high-priority contextual watch. Upgrade materially if the market consolidates at IND -4/-4.5 while Sly remains -3.5.**

## Friday decision state

Do **not** set final wagers yet. The Friday model has done its job: identify where Sly may be stale and where the market is effectively equal.

Current candidate order for continued work:
1. SEA -7 — strongest blend of price evidence + current injury context.
2. HOU -3 — positive price candidate, dependent on market confirmation / Collins status.
3. DEN +3 — positive half-point candidate, but market disagreement remains.
4. IND -3.5 — contextual upside because Daniels is out; price edge is source-dependent.
5. NE +7 — Action-based value exists, but source disagreement and Patriots injuries reduce confidence.

All other games are currently market-equal in the frozen V2 layer and should only rise through contextual evidence, not through the model's tiny residual directional bias.

## Next execution steps

1. Ingest Friday final injury designations as they become official.
2. Capture SportsLine / Gridiron / Lucas source-native Week 4 takes only when their exact reference lines and timestamps are available.
3. Run the joint Catherine/Amanda optimizer using Week 3 bankroll state and the Friday candidate set; treat disputed market edges with shrink/stress, not as certain edge.
4. Sunday morning, capture a distinct `PRE_KICK_FINAL` market snapshot, re-run frozen V2, check weather/inactives, and reconcile proposed wagers to the final authoritative model.
5. Any opposite-side wager must be recorded as an explicit override with reason and timestamp.
