# NFL Monopoly — Canonical Project State / Handoff

**Purpose:** Durable source of truth for continuing this project across ChatGPT conversations. Read this file first in any new conversation before making changes or recommendations.

**Repo:** `catherinelw716/monopoly-command-center-canonical`

**Canonical live app:** https://monopoly-command-center-canonical.onrender.com/

**Last updated:** 2026-09-27

---

## 1. User intent and working style

Catherine wants a rigorous NFL Monopoly ATS decision system and Command Center. The goal is not merely to pick winners; it is to maximize season-long household tournament equity across Catherine and Amanda's two entries under the Monopoly rules.

Working preferences:
- When Catherine says **"Proceed"**, execute the agreed next step rather than re-explaining it.
- Keep responses direct and implementation-oriented.
- Do not invoke a separate "Deep Research" workflow. Normal web research/investigation is acceptable and often necessary.
- Never claim a UI change is verified merely because Render deployed successfully. Deployment != rendered behavior.
- Do not use the word **"ticket"** in pool UX.
- Do not make broad UI changes when Catherine asks for a targeted fix.
- Preserve useful work when rolling back regressions; do not remove data just to remove broken UI behavior.

---

## 2. Pool rules

- Weekly ATS pool using **Sly's frozen spreads**.
- Cover: stake returned + equal winnings = **net +1x wager**.
- Loss: **net -1x wager**.
- Push: **0 net**.
- Minimum **4 games per entry per week**.
- Minimum **$100 per game**.
- Wagers in practice should be treated in $100 increments unless rules prove otherwise.
- Thursday: TNF spread issued separately; betting TNF optional.
- Friday: remaining spreads issued and frozen.
- Non-Thursday bets submitted together after Friday lines.
- Bets can be changed before kickoff.
- Standings are visible before the week's games.
- Approx. 110+ participants historically/currently.
- Payouts: 1st 56%, 2nd 25%, 3rd 10%, 4th 2%, 5th 1%, Commissioner 6%.

**Reminder for future phase:** Before final Monopoly simulator implementation, reconfirm any additional playoff/end-of-season/elimination/minimum-wager rules not already encoded.

---

## 3. Household / current field state

After Week 2 (2026):
- Catherine: **$11,400**, rank **#30**.
- Amanda: **$10,300**, rank **#44**.
- Combined bankroll: **$21,700**.
- Week 2 top-10 floor: **$16,665**.
- Week 2 top-5 floor: **$19,400**.

Historical outlay:
- Week 1 household: $6,100 total; Catherine $3,000; Amanda $3,100.
- Week 2 household: $7,800 total; Catherine $3,600; Amanda $4,200.
- Week 2 shared exposure had risen to ~73%; lesson is not "never overlap" but to require stronger evidence for large shared exposure.

Field learning:
- Early standings are highly mobile.
- Do not chase leaders simply because rank moves are large.
- Field/standings information should alter deployment/tournament risk, not NFL cover probabilities.

---

## 4. Current production model / V1 status

V1 remains the **production champion** while V2 is built in parallel.

Legacy/V1 architecture evolved around M1-M5 style reasoning:
- price / Sly-vs-market
- key-number value
- market dispersion / uncertainty
- line path / movement
- independent model evidence
- injuries/news timing and red-team review

Strengths of V1:
- Sly-vs-market framing
- key-number awareness
- source provenance
- line/reference-spread discipline
- injury/news timing
- missing-data discipline
- adversarial red team

Weaknesses motivating V2:
- qualitative rather than learned weights
- grades are not calibrated probabilities
- external sources can be mistakenly treated like independent votes
- insufficient historical walk-forward backtesting
- portfolio sizing still partly heuristic
- production UI has at times layered new source information around an older hard-coded "Our Model" rather than refreshing the underlying model

Do **not** silently replace V1 with V2. V2 must pass promotion gates.

---

## 5. Source handling rules

### SportsLine
- Preserve exact recommendation, grade, timestamp, and reference line.
- ATS picks count as ATS evidence.
- Total or moneyline simulations do **not** count as ATS votes.

### Gridiron
- Preserve exact cover percentages and reference spread.
- **50/50 = NO TAKE.**
- A prediction at a different reference spread must not be treated as an exact Sly-line ATS vote.

### Lucas
- Independent external source, not part of M1-M5.
- Signals: LIKE / LEAN / NO TAKE.
- Preserve exact Sly-side reference when supplied.

### Cross-source consensus
- Human-facing table should explicitly show all four sources: **Our Model, SportsLine, Gridiron, Lucas**.
- Mathematical V2 modeling should NOT assume these are independent votes.
- Non-ATS SportsLine outputs and mismatched Gridiron reference lines remain visible as context but are excluded from exact-line ATS vote counts.

---

## 6. Week 3 screenshot-derived external source data

This data was supplied directly by Catherine and should not be lost during UI rollback.

### LAC @ BUF
- SportsLine: BUF -7, Grade B, ATS, 6 picks, projected LAC 21 / BUF 31.
- Gridiron: LAC +7 51%, BUF -7 49%, exact ref BUF -7.

### CAR @ CLE
- SportsLine: CAR -2.5, Grade B, ATS, 6 picks, projected CAR 24 / CLE 21.
- Gridiron: CAR -2.5 54%, CLE +2.5 46%, exact.

### NYJ @ DET
- SportsLine: OVER 48.5, Grade B, TOTAL, 14 picks, projected NYJ 23 / DET 36.
- Gridiron: NYJ +6.5 51%, DET -6.5 49%, exact ref DET -6.5.

### HOU @ IND
- SportsLine: OVER 42.5, Grade C, TOTAL, 11 picks, projected HOU 24 / IND 23.
- Gridiron: HOU -1.5 51%, IND +1.5 49%, exact.

### NE @ JAX
- SportsLine: JAX -3, Grade C, ATS, 9 picks, projected NE 20 / JAX 25.
- Gridiron: NE +3 46%, JAX -3 54%, exact.

### KC @ MIA
- SportsLine: KC -10.5, Grade A, ATS, 7 picks, projected KC 32 / MIA 16.
- Gridiron: KC -11.5 53%, MIA +11.5 47%; **reference mismatch** vs Sly KC -10.5.

### TEN @ NYG
- SportsLine: OVER 37.5, Grade C, TOTAL, 3 picks, projected TEN 20 / NYG 22.
- Gridiron: TEN PK 57%, NYG PK 43%; **reference mismatch** vs Sly TEN +2.5.

### CIN @ PIT
- SportsLine: PIT +153, Grade B, MONEYLINE, 5 picks, projected CIN 22 / PIT 20.
- Gridiron: CIN -3.5 50%, PIT +3.5 50%, exact but **NO TAKE**.

### SEA @ WAS
- SportsLine: SEA -7.5, Grade A, ATS, 4 picks, projected SEA 27 / WAS 15.
- Gridiron: SEA -7 50%, WAS +7 50%; mismatch and **NO TAKE**.

### ARI @ SF
- SportsLine: SF -8.5, Grade B, ATS, 6 picks, projected ARI 20 / SF 30.
- Gridiron: ARI +8.5 51%, SF -8.5 49%, exact.

### MIN @ TB
- SportsLine: OVER 42.5, Grade C, TOTAL, 4 picks, projected MIN 24 / TB 22.
- Gridiron: MIN -1.5 50%, TB +1.5 50%, exact but **NO TAKE**.

### BAL @ DAL
- SportsLine: DAL +147, Grade C, MONEYLINE, 2 picks, projected BAL 28 / DAL 26.
- Gridiron: BAL -3 53%, DAL +3 47%; mismatch vs Sly BAL -3.5.

### LV @ NO
- SportsLine: NO -3, Grade A, ATS, 6 picks, projected LV 19 / NO 27.
- Gridiron: LV +3 51%, NO -3 49%, exact.

### LAR @ DEN
- SportsLine: DEN +2.5, Grade B, ATS, 3 picks, projected LAR 21 / DEN 22.
- Gridiron: LAR -2.5 49%, DEN +2.5 51%, exact.

### PHI @ CHI
- SportsLine: UNDER 42.5, Grade C, TOTAL, 5 picks, projected PHI 23 / CHI 17.
- Gridiron: PHI -3 46%, CHI +3 54%; mismatch vs Sly PHI -4.5.

Lucas Week 3:
- LIKE: CAR -2.5, LAR -2.5, PHI -4.5, DET -6.5.
- LEAN: CIN -3.5, MIN -1.5, TEN +2.5.
- All other games NO TAKE.

---

## 7. UI/UX regression lessons

Important: previous broad DOM patches caused mobile navigation and Decision Board regressions.

Do not reintroduce:
- whole-document MutationObservers that continuously rewrite the page
- repeating DOM rewrite intervals
- replacement Slate Decision Boards that hide the original interactive cards/buttons
- broad mobile table-to-card redesigns unless explicitly requested

Preferred approach:
- targeted, bounded patches
- preserve existing navigation and interaction patterns
- source-data patches should update existing fields/cards only
- verify mobile navigation after every UI change

Catherine specifically wants:
- Today / Analysis / Games / Lab / Portfolio mobile navigation to work
- original Slate Decision Board button/card treatment preserved
- Lucas shown in game tables and Games source cards like other sources
- game-analysis deep dives visually structured, not plain text
- source tables visually distinguish grades/signals
- Cross-source consensus displayed **after Lucas** and includes all four sources explicitly

---

## 8. V2 redesign — canonical plan

See `V2_MODEL_SPEC.md` for the formal specification.

Core architecture:

1. **Point-in-time data spine**
2. **Market fair-line engine**
3. **Football residual model**
4. **Discrete NFL margin distribution**
5. **Calibration + uncertainty layer**
6. **External-source reliability layer**
7. **Monopoly tournament simulator**
8. **Joint Catherine/Amanda portfolio optimizer**

Key principle:
- Prediction layer estimates P(cover/push/loss) at Sly's frozen spread.
- Tournament layer decides games, amounts, total deployment, and overlap.
- Standings/tournament state must never alter the underlying NFL cover probability.

Candidate predictive challengers:
- market-only baseline
- ridge / elastic-net residual regression
- Bayesian hierarchical residual model
- gradient-boosting challenger

Complexity must beat simpler models out of sample.

V2 probabilities must be calibrated before being used for wager sizing.

---

## 9. V2 QA / promotion philosophy

Use strict walk-forward / rolling-origin testing, never random game-level train/test splits.

Required QA:
- point-in-time timestamp integrity
- no future information
- correct spread sign convention
- exact reference spreads for sources
- missing remains missing
- deterministic feature builds
- calibration fit only on training folds
- feature-family ablations
- regression checks on every refresh

Promotion gates:
1. data/leakage integrity
2. predictive performance vs market-only/V1
3. calibration and robustness
4. Monopoly tournament-value improvement
5. prospective shadow performance

V1 remains champion until V2 clears all gates.

---

## 10. V2 implementation status

Completed:
- `V2_MODEL_SPEC.md`
- `V2_DATA_FEASIBILITY.md`
- `v2/data_contract.json`
- `v2/build_historical_dataset.py`
- `v2/build_baseline_features.py`
- `v2/qa_checks.py`
- `v2/experiment_registry.csv`
- `v2/external_source_ledger.csv`
- `.github/workflows/v2-research-ci.yml`

Important QA discovery:
- nflverse `spread_line` sign convention differs from conventional sportsbook display. In V2 normalized convention, **home favorite is negative**. Normalize nflverse schedule `spread_line` as `home_spread = -spread_line` after schema/semantic QA.

Next V2 milestone:
- materialize historical dataset
- pass dataset QA
- fit market-only baseline
- fit ridge football-residual challenger
- run strict walk-forward comparison
- produce calibration + QA report

---

## 11. Future items Catherine explicitly asked to be reminded about

### A. Historical intra-week odds
For rigorous retrospective testing of the uniquely Monopoly-specific **Friday Sly freeze -> Sunday market movement** edge, we may need paid timestamped historical odds access (e.g. The Odds API historical snapshots or SportsDataIO line history).

Do NOT block the rest of V2 on this. Build/test the general prediction engine first and evaluate the stale-line component prospectively if necessary.

### B. Full Monopoly rule audit
Before finalizing the season simulator, reconfirm any pool rules not already captured, especially:
- playoff qualification rules
- playoff minimum wager requirements / escalation
- elimination mechanics
- any end-of-season special rules

Surface these reminders when those phases are reached.

---

## 12. New-conversation bootstrap instructions

In a new ChatGPT conversation, Catherine can simply say:

> **"Continue NFL Monopoly. Load the canonical project state from the GitHub repo first."**

Before answering substantively, fetch/read:
1. `PROJECT_STATE.md`
2. `V2_MODEL_SPEC.md` if the task involves V2
3. relevant current repo files for any code/UI work

Do not rely only on conversational memory or prior-chat summaries when these files are available.

After any material project change, update this file so it remains the current handoff source of truth.
