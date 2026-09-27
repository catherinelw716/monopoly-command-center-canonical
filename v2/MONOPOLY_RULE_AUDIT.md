# NFL Monopoly — Simulator Rule Audit

Status: **ACTIVE — sufficient to begin V2-0009 core simulator build**

Purpose: preserve the contest mechanics that materially affect the optimizer without letting edge-case rule auditing derail the V2 roadmap.

## A. Confirmed core rules

### Season start / weekly wagering
- **Every entry started Week 1 with $10,000.** This is the season starting bankroll, not a playoff rule.
- ATS only, using Sly's frozen spreads.
- Cover = net **+1x wager**.
- Loss = net **-1x wager**.
- Push = **0** net.
- Minimum **4 games per entry per week**.
- Minimum **$100 per game**.
- Wager increment = **$100**.
- Thursday game is optional and issued separately.
- Remaining non-Thursday lines are issued Friday and submitted together.
- Bets can be changed before kickoff under the existing operating rules.

### Payout structure
- 1st: **56%**
- 2nd: **25%**
- 3rd: **10%**
- 4th: **2%**
- 5th: **1%**
- Commissioner: **6%**

### Confirmed later-season / playoff constraints
These are real contest constraints, but they should **not dominate the current early-season optimizer design**.
- Week 18 qualification threshold: **$3,000 remaining balance**.
- Wild Card: **6 games × $500 minimum each**.
- Divisional: **4 games × $750 minimum each**.
- Conference Championship: **2 games × $1,500 minimum each**.
- Super Bowl: **$3,000 minimum**.
- Only the balance available entering a playoff weekend can be wagered during that weekend.

### Household optimization policy
- Catherine and Amanda are separate entries but optimized jointly at the household level.
- Number of games, total deployment, wager sizes, and overlap are optimizer outputs, not fixed heuristics.
- Standings affect portfolio risk, not NFL cover probabilities.

## B. Modeling priority

The current V2-0009 build should focus first on the mechanics that matter now:
1. current balance and rank;
2. weekly Sly-line cover/push/loss probabilities;
3. $100 wager increments and four-game minimum;
4. field balance distribution / observed field behavior;
5. Catherine/Amanda shared NFL outcome correlation;
6. top-heavy final payout objective;
7. preserving sufficient future bankroll to remain viable.

The playoff minimum schedule belongs in the season-state transition model, but it is a **future constraint**, not the central driver of Week 3 recommendations.

## C. Details that can remain parameterized until they become decision-relevant

Do not stop the core simulator build to interrogate these now. Keep them explicit parameters/TODOs rather than inventing rules:
- exact tie-break procedure for equal final balances;
- precise administrative handling of an entry that cannot satisfy a future playoff minimum;
- playoff submission timing differences, if any;
- whether any uncommon edge-case exception exists around pushes or late changes.

Before these details can materially change an optimizer recommendation, confirm them with Catherine.

## D. Build sequence

Proceed with V2-0009 now:
1. create the machine-readable contest/state contract using the confirmed rules above;
2. build and unit-test weekly bankroll transitions;
3. replay known Week 1–2 Catherine/Amanda results to verify accounting;
4. represent the observed field balance distribution and historical behavior;
5. build the joint Monte Carlo season simulator;
6. benchmark candidate allocation policies and then optimize Catherine/Amanda jointly.

Rule auditing is now a supporting control, not the primary workstream.
