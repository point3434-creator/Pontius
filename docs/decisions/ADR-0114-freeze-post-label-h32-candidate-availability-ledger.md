# ADR-0114: Freeze post-label h32 candidate-availability ledger

**Status:** Frozen before executing the deterministic replay; strategic labels
are already known and no holdout claim is made

**Date:** 2026-08-20

## Decision

Replay fixed-envelope selection on the original and fresh h32 boards after
restricting each target to candidates that physically exist by warm-search
iterations `0,1,2,4,8`.

This is not a new strategy experiment. ADR-0113 already observed that all four
full-pool non-blueprint selections across the two boards are current-one/two
interpolations, hence constructible after iteration two. The replay exists to:

1. mechanically reproduce full-pool selection from the stage-two set;
2. verify candidate-availability bookkeeping and source-vector integrity; and
3. charge the exact recorded iterations 3-8 and four late full-teacher
   evaluations that a two-step stop would avoid.

It runs zero CFR steps, policy evaluations, best responses, tensor
contractions, or GPU work.

## Frozen availability

- iteration 0: average-32 and current-48 controls;
- iteration 1: warm average one and current one;
- iteration 2: warm average/current two and the three current-one/current-two
  interpolations;
- iteration 4: warm average/current four; and
- iteration 8: warm average/current eight.

Stage sizes must be exactly `2,4,9,11,13`, nested, and exhaustive. Behavioral
interpolation cannot be charged before iteration two because its second
endpoint does not yet exist.

## Frozen sources

| Source | SHA-256 |
|---|---|
| ADR-0106 original-board fixed-envelope corpus | `1898c24a6c0232059a19c2151f29537a574ba85d8ec9a3641c117eda9b9087af` |
| ADR-0101 original-board search timing | `b432eda21d1978b1dd576a9f4e7451250f1d53dcf9a88a6efa739d681ecb6f33` |
| ADR-0113 fresh-board corpus and timing | `af0a725f89d18eaf98e924fa0423176a8a8be6f6e477234fa492304101db3cf9` |

The frozen replay implementation is
`src/pontius/h32_candidate_availability_replay.py`, SHA-256
`bdb1b86db792d49e503915c399dbcc0cc3d03b3760acf8410d9ca2562de672ce`.
The config SHA-256 is
`ed3812df2fccaa519e9abd9dc9ef921585597898f134e0e5cdd94d8aad4b2363`.
The two focused protocol tests, SHA-256
`282993225c20ef059fcd55c031de50a0c04e3963b6e8dca42c5be8d6efb911c2`,
pass before freeze.

## Frozen gates

The ledger passes only if:

- all three source artifacts retain successful frozen status and exact hashes;
- there are two board sources, four targets per board, and 13 candidates per
  target;
- availability stages are nested with the frozen sizes and exhaust all 13
  candidates;
- the full stage exactly reproduces each source artifact's selected digest;
- every deviation vector sums to NashConv within `1e-12` and every quality and
  cost is finite;
- new training, evaluation, and contraction counts are all zero; and
- replay wall time is at most five seconds.

Stage-two identity is deliberately not a mechanism gate, despite being
structurally anticipated from known selected IDs. Recording it as an outcome
keeps the distinction between source integrity and scheduler disposition.

## Cost semantics

For each target, charge:

`search_cumulative(8) - search_cumulative(2)`

plus the recorded complete evaluation walls of average/current iterations four
and eight. These are historical full-teacher bills, not projected partial-
verifier bills. The ledger separately reports avoided warm steps and does not
pretend the old and fresh evaluator backends have identical cost.

## Decision rule

If every mechanism gate passes and step two reproduces all eight selected
digests, iteration two becomes the measured candidate-availability ceiling for
the current two-board one-bet h32 corpus. It becomes the customer for the next
resident-CFR systems audit, but not a universal poker stopping rule.

If any target changes selection after iteration two, retain the full eight-step
ladder and localize which late candidate supplies unique safe value.
