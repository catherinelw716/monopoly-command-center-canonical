# Five-Factor Spread Scorecard — Adversarial Review

**Date:** 2026-10-03  
**Status:** Passed with disclosed caveats; ready for challenger-page rendering  
**Scope:** Week 4 scorecard candidate generated under preregistered v1.0 rules

## Executive conclusion

The Week 4 five-factor challenger can proceed to UI, but it must remain separate from V2 and wager sizing. The review found no evidence that the Money factor is accidentally using ticket/bet percentage, and two high-leverage market-open examples were independently spot-checked against current Action Network matchup pages. The largest remaining methodological caveats are correlation between Line Movement and Money, small/stale ATS samples, and the fact that the defensive source labels the current snapshot as Week 4 while Sunday/Monday teams have three completed games.

## Findings

### 1. Money / handle semantics — PASS
DraftKings Network explicitly distinguishes **% Handle** (total money wagered) from **% Bets** (number of wagers). The scorecard uses only the spread-handle column. Bets/tickets remain separate and do not satisfy the Money-factor schema.

Spot checks during the review matched the scorecard direction and approximate captured values, including SEA/LAC and ARI/NYG. Handle is live and can move, so the stored snapshot timestamp remains authoritative for this Saturday version.

**Classification:** source semantics verified; freshness risk accepted and disclosed.

### 2. Line movement orientation — PASS
The Action Network matchup pages expose a distinct Open spread and current spread. The scorecard's away-side normalization was challenged on the two most extreme/high-leverage examples:

- ARI @ NYG: Action shows Arizona opening as a sizeable underdog and currently favored, so the large directional move is real rather than a sign/orientation bug.
- LAC @ SEA: Action shows LAC opening around +3 and currently around +7, which correctly grades as strong movement toward Seattle.

**Classification:** no orientation defect found in sampled extremes. All market lines remain evidence only and do not overwrite Sly.

### 3. ATS trends — ACCEPTED WITH CAUTION
The framework correctly shrinks tiny samples and downweights older H2H history. Current-season and recent ATS windows overlap heavily this early in the season, so Trends should be described as one heuristic factor rather than multiple independent confirmations.

**Classification:** accepted trade-off; page must show sample size/recency and the overlap warning.

### 4. Defense cutoff — ACCEPTED WITH DISCLOSURE
Yards Per Pass / nflverse is a coherent defensive EPA/play methodology, and the underlying team values/ranks used by the candidate are consistent with the source's current 2026 view. The source labels the table "Through Week 4" because Week 4 is in progress; Sunday/Monday teams in this slate still have three completed games. The Thursday PIT/CLE result may affect league-wide rank ordering even though PIT/CLE is excluded from the Monopoly slate.

For this challenger page, keep the current pregame defensive snapshot but label it as a **Week 4 pregame snapshot** and refresh it during PRE_KICK_FINAL. Do not claim it is a clean end-of-Week-3 league table.

**Classification:** source-timing caveat, not a scoring-code defect.

### 5. Key-number logic — PASS
The deterministic engine owns key-number scoring, including overlapping 6/7 behavior and Sly-vs-market comparisons. Line Movement does not add separate key-crossing points, preventing obvious direct double counting between Factors 1 and 5.

**Classification:** no defect found.

### 6. Correlation between Line Movement and Money — MATERIAL CAVEAT
These factors can reflect the same market information. They remain separate in v1.0 because that was preregistered for interpretability, but the page must explicitly say they are correlated and should not be read as two fully independent model votes.

**Classification:** accepted v1 design trade-off; prospective tracking required before any weight changes.

### 7. Main-system comparison — KEEP POST-HOC
The scorecard is allowed to show AGREES / DISAGREES / MAIN SYSTEM NO TAKE only after the five-factor score is computed. It must not use the main Command Center recommendation as a sixth input.

**Classification:** architecture requirement reaffirmed.

## Release gate

Approved for `/spread-scorecard` rendering provided that:

1. the page renders the canonical scorecard object without recalculating factor scores in the DOM;
2. source/timestamp/reference-line fields remain visible in each game's detail;
3. Money is labeled **Handle % (money)**, never just "public";
4. the correlation and defense-cutoff caveats are visible in methodology text;
5. the feature remains challenger-only and does not feed V2 or the optimizer;
6. render QA rejects missing factors and literal `undefined`, `null`, or `[object Object]` output;
7. Sunday PRE_KICK_FINAL refreshes the market, handle, and defense snapshot before the scorecard is treated as final.
