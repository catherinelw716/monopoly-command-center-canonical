# NFL Monopoly — Simulator Rule Audit

Status: **ACTIVE — rule confirmation before V2-0009 simulator build**

Purpose: lock the exact contest mechanics before writing the Monopoly tournament simulator or Catherine/Amanda joint optimizer. No simulator assumption should be inferred from conventional survivor/ATS pools.

## A. Confirmed rules already in the canonical project

### Weekly wagering
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

### Household optimization policy
- Catherine and Amanda are separate entries but optimized jointly at the household level.
- Number of games, total deployment, wager sizes, and overlap are optimizer outputs, not fixed heuristics.
- Standings affect portfolio risk, not NFL cover probabilities.

## B. Previously recorded details that require user confirmation before encoding

These appeared in prior project work, but are deliberately **not yet treated as simulator truth** until Catherine confirms them:

- Starting bankroll per entry: **$10,000**.
- Week 18 / playoff qualification threshold: **$3,000 remaining balance**.
- Wild Card round minimum: **6 games × $500 each**.
- Divisional round minimum: **4 games × $750 each**.
- Conference Championship minimum: **2 games × $1,500 each**.
- Super Bowl minimum: **$3,000**.
- Previously recorded operating interpretation: only the balance available entering a playoff weekend can be wagered during that weekend.

## C. Still missing / must be explicitly locked

### Regular season / qualification
- Exact meaning of the $3,000 Week 18 threshold: qualification for what, and measured at what timestamp?
- Whether an entry below the threshold is eliminated immediately or simply ineligible for postseason wagering.
- Whether Week 18 itself is part of the regular-season bankroll race before qualification is assessed.
- Whether any regular-season minimum changes later in the year.

### Playoffs
- Whether every qualifying entry continues independently through all NFL playoff rounds.
- Whether balances carry forward unchanged from regular season into Wild Card and then round to round.
- Whether a player may wager **more** than the stated playoff minimums.
- Whether the listed playoff minimum is per game, total round deployment, or mandatory on every game in the round.
- Whether all games in a playoff round must be wagered or only a minimum number.
- Whether losing below a future-round minimum causes elimination.
- What happens to an entry whose balance is insufficient to meet the required round minimum.
- Whether pushes preserve the full stake and count toward required deployment.

### Timing / submission
- Whether playoff lines are issued using the same Thursday/Friday process or a different schedule.
- Whether wagers can be changed until kickoff during the playoffs.
- Whether each game's bet locks individually at kickoff.

### Ranking / payouts
- Exact final ranking variable: ending Monopoly balance after the Super Bowl?
- Tie-break procedure for equal final balances.
- Whether payout percentages are applied to the real-money entry pool and whether ties split positions/payouts in any special way.
- Whether non-qualifying/eliminated balances remain in published standings but cannot win.

### Field / simulator mechanics
- Exact number of entries at season start and whether late entries are possible.
- Whether every entry begins with the same bankroll.
- Whether there are any rebuy, reset, borrowing, negative-balance, or zero-balance rules.
- Whether a wager can ever exceed current available balance.
- Whether the pool permits an entry to wager its entire balance.

## D. Build gate

Do **not** begin the production V2-0009 simulator until Sections B and C are resolved enough to encode the contest deterministically.

Once the rules are locked:
1. convert them into a machine-readable simulator contract;
2. add unit tests for every bankroll transition and qualification/elimination rule;
3. replay known historical seasons/weekly balances to verify accounting;
4. only then build the field-policy model and Catherine/Amanda Monte Carlo optimizer.
