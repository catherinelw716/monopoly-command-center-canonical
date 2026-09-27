# V2-0010 — Prospective 2026 Shadow Validation Protocol

Status: **REGISTERED / ACTIVE**

Purpose: evaluate the frozen V2 global-hybrid probability architecture prospectively at the actual Sly spread and at point-in-time market snapshots without retroactive prediction edits.

## Frozen challenger

V2 model form is frozen from V2-0006C/0006D:

1. Market is the fair-margin anchor.
2. Normal residual distribution supplies conditional cover/loss odds.
3. Half-point Sly lines use the normal distribution unchanged.
4. Integer Sly lines replace only the normal push mass with a global empirical exact-margin push estimate, shrunk toward the normal push estimate.
5. Cover/loss probabilities are rescaled around the corrected push mass while preserving their normal-model ratio.
6. No PBP residual adjustment, spread conditioning, total conditioning, public-betting weight, or external-source mathematical weight is permitted during V2-0010 unless a separately registered QA defect requires a code correction.

## Required snapshots

Each game can have two prediction captures. They are separate observations and must never overwrite each other.

### FRIDAY_FREEZE
Capture after Sly's Friday line is known and as close as practical to the Friday market observation used for evaluation.

Required fields:
- season / week / game ID
- away / home teams
- scheduled kickoff timestamp
- Sly home-team spread using conventional sportsbook sign (`-` favorite, `+` underdog)
- point-in-time market home-team spread
- market source / provenance
- exact market observation timestamp
- V2 normal probabilities at Sly
- V2 global-hybrid probabilities at Sly
- model artifact/version metadata

Optional but strongly preferred at capture time:
- V1 side / confidence / probability if available
- SportsLine native side, grade/type, reference line, timestamp
- Gridiron side, probability, reference line, timestamp
- Lucas LIKE/LEAN/NO TAKE and side
- notes describing unresolved injury/news uncertainty

### PRE_KICK_FINAL
Capture the same fields again after the final research refresh but **before kickoff**. Sly's line remains frozen; only the point-in-time market/context may change.

This snapshot is the primary prospective measurement of stale-line value because it compares Sly's frozen number with the most information-rich pregame market state available before kickoff.

## Immutability rules

The ledger is append-only JSONL with a SHA-256 hash chain.

- Never edit or delete a prior prediction event.
- A correction must be appended as a new `correction` event that references the prior event ID and explains the error.
- Outcomes are appended as separate `result_settlement` events; prediction rows are never rewritten with results.
- A prediction capture at or after the scheduled kickoff is rejected by the capture script.
- Every event includes `prev_hash` and `row_hash`; the validator fails if any historical line was changed, reordered, or removed.
- Git history is an additional audit trail, not a substitute for the ledger hash chain.

## Prospective metrics

Evaluate FRIDAY_FREEZE and PRE_KICK_FINAL separately.

Primary challenger metric:
- 3-class Brier score at **Sly's exact line** for `[loss, push, cover]`.

Secondary metrics:
- 3-class log loss at Sly's exact line
- V2 hybrid vs V2 normal paired Brier delta
- cover calibration by probability bin
- push calibration on integer Sly lines
- exact-3 and exact-7 push calibration
- stale-line advantage (`Sly home spread - market home spread`) versus realized cover/push/loss
- Friday-to-prekick market movement
- V1 directional / confidence comparison where V1 was captured before kickoff
- source-native ATS performance for SportsLine/Gridiron/Lucas only at each source's documented reference line

Do **not** count SportsLine total/ML recommendations as ATS predictions. Do **not** treat Gridiron 50/50 as a take. Do **not** silently translate a source prediction from a different reference spread to Sly's line.

## Promotion guardrail

No production replacement decision may be made from one or two weeks.

Minimum prospective evidence before considering a V2 probability-layer promotion:
- at least **100 settled game snapshots** at the designated evaluation snapshot, and
- at least **6 distinct NFL weeks**, and
- no integrity failure in the hash-chain ledger, and
- V2 hybrid must outperform the normal probability baseline on mean 3-class Brier, with no material deterioration in log loss or obvious calibration failure.

The 100-game / 6-week floor is a decision guardrail, not a guarantee of statistical power. If uncertainty remains large, continue shadowing.

## What is explicitly not allowed during V2-0010

- changing model architecture because of a bad week
- adding weights to SportsLine/Gridiron/Lucas based on a small prospective sample
- reconstructing a missed Friday snapshot from Sunday closing odds
- backfilling a prediction after kickoff and labeling it prospective
- changing Sly's frozen spread to match the market
- using standings or Monopoly strategy to alter NFL cover probabilities

## Pool layer separation

V2-0010 validates the **NFL probability layer only**. Catherine/Amanda wager allocation remains a separate tournament-optimization problem. The eventual optimizer may use these probabilities, standings, field behavior, payout structure, overlap, and bankroll constraints, but those variables cannot feed back into P(cover/push/loss).
