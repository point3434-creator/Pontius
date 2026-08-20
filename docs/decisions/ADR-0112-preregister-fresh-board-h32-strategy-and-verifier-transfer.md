# ADR-0112: Preregister fresh-board h32 strategy and verifier transfer

**Status:** Preregistered; board, source training, targets, candidates,
certificate semantics, comparison orders, telemetry, and gates frozen before
any h32 strategy or quality measurement on the new board

**Date:** 2026-08-20

## Decision

Run the first genuinely fresh-board h32 strategic transfer audit.

Train new balanced and blocker-heavy DCFR blueprints from iteration zero on
board `4h 6s Td Qh As`, which appears in none of the prior wide artifacts.
Then apply two support-preserving target beliefs per family, generate the same
complete 13-policy search portfolio used by ADR-0108, evaluate every policy's
six-seat unilateral vector exactly through the accepted resident backend, and
replay the fixed-envelope verifier under two declared seat orders.

This is a strategic replication, not a speed optimization. It asks whether
the generator, acceptance semantics, predecessor-seat mechanism, and resident
economics transfer together when the board and all learned policies are new.

No strategy outcome is a gate. A run in which every target retains the
blueprint can and should pass if it was generated and measured correctly.

## Freshness boundary

The board is frozen as `4h 6s Td Qh As`. The disclosed earlier boards are:

- the original h32 board `2c 7d 9h Js Qc`; and
- ADR-0109's h7 mechanism-control board `3s 8c Th Kd Ac`.

The new board was selected and committed before any h32 axis construction,
training step, target search, policy value, or best-response value was run on
it. The audit regenerates its hand axes from the frozen seed; it imports no
policy or quality vector from the old board.

## Frozen source training

For each of `balanced` and `blocker_heavy`:

1. construct the six-seat, 32-hands-per-seat factor belief and one-bet river
   public tree from scratch;
2. run single-trajectory alternating DCFR for 64 iterations through the
   transferred-GPU leaf-adjoint solver;
3. serialize full restart states at iterations 32, 48, and 64;
4. retain average-32, current-48, and average-64 policies; and
5. exactly evaluate average-64 under the source belief.

The average-64 policy is the immutable episode blueprint. Average-32 and
current-48 are provenance controls, not alternative anchors. Source quality is
reported but not thresholded.

## Frozen target matrix

Each source family receives:

1. `local_blocker_seat5_x2`: double the likelihood of one deterministically
   selected high-overlap hand on seat 5; and
2. `all_seat_strength_1_to2`: apply the monotone showdown-strength likelihood
   used by ADR-0099 to every seat.

The local perturbation deliberately moves from historical seat 3 to seat 5.
The recorded mechanistic prediction is that the dominant cap pressure moves
from the old predecessor seat 2 toward new predecessor seat 4. This is a
hypothesis, not a gate.

All likelihoods remain in `[1,2]`, preserve support, and leave the private-hand
axes unchanged. Root marginal total variation is measured after construction.

## Frozen candidate portfolio

Warm-start target-belief DCFR from the source average-64 blueprint using regret
mass `0.1 * payoff_span`. Run eight iterations and record full restart states
at `1,2,4,8`.

The 13 candidates, in fixed arrival order, are:

1. source average-32;
2. source current-48;
3. target warm averages 1, 2, and 4;
4. target warm currents 1, 2, 4, and 8;
5. target warm average 8; and
6. behavioral current-1/current-2 interpolations at `0.25`, `0.50`, and
   `0.75`.

All 13 plus the blueprint are evaluated for all six seats. This intentionally
constructs an exact teacher corpus before simulating early stops; it prevents
either seat order from receiving more strategic information than the other.

## Certificate semantics

ADR-0111 is load-bearing. Each target carries:

- immutable average-64 blueprint digest;
- public-root, target-belief, and empty deployed-prefix digests;
- exact six-seat blueprint vector, cap vector, raw guard, and payoff span; and
- explicit expiration after the next public transition.

The selected candidate never becomes a safety anchor. Every target is a
one-shot decision. Nothing in this experiment claims that four local
certificates compose into an episode-root guarantee.

## Frozen verifier comparison

Replay the same fixed-blueprint envelope and candidate order under:

1. fixed seat order `0,1,2,3,4,5`; and
2. ascending absolute blueprint cap, ties by seat.

Because the guard is common, the second order is equivalent to ascending
blueprint deviation gain. It is legal because it uses only the already
certified blueprint vector, never a candidate label. It is **not** called a
learned selector and is not adopted from this single board even if it wins.

For each order report evaluated seats and three bills: probability compilation
plus prefix seats, one resident-cache charge, and the full one-shot decision
bill including target construction and blueprint evaluation. Both early-stop
replays must select the same digest as unconstrained full-pool fixed-envelope
selection.

## Exactness control

On the balanced local-blocker target, evaluate the blueprint once through both
the transferred-GPU incumbent and the resident backend. Compare all six
utilities, best-response values, deviation gains, and literal action maps.

This is an external at-scale cross-check on the new board. The resident teacher
cannot validate itself merely through zero-sum conservation.

## Frozen implementation

| File | SHA-256 |
|---|---|
| `src/pontius/fresh_h32_strategy_transfer_audit.py` | `aafffcf191ff0b8b9262004efc48c61ded4d3c1506f60acfbd473d78f79271f2` |
| `experiments/configs/fresh-h32-strategy-transfer-audit-v1.json` | `764a80adadeb57f09e9236514b603e4c83570c6e335b1a98ec166be40df2cfca` |
| `tests/test_fresh_h32_strategy_transfer_audit.py` | `00cbf5c2749ca68bc8ddbbc90c8c3b6d6470df70c67fe1ba117430cdfa511f81` |

The accepted ADR-0110 parent artifact is pinned at
`29504e25bffac5409a401c3e780d328ef143461eb9b63cd72fb1f790960ef491`.
Every directly reused solver, evaluator, checkpoint, acceptance, interpolation,
resident, and sparse-incidence module is independently pinned in the config.

The complete repository suite passes 502/502 before freeze, including the five
new protocol tests and four live CuPy tests.

## Frozen gates

The result passes only if:

1. every frozen source and environment identity reproduces;
2. counts are exactly two source families, 128 source steps, six source
   checkpoints, four targets, 32 target-search steps, 16 target checkpoints,
   52 candidates, 56 resident profiles, 336 resident seat rows, and six legacy
   cross-check seats;
3. both source games contain 6,144 information sets and 12,288 hand-action
   entries;
4. board freshness, checkpoint digests, target axes, support, and likelihood
   bounds reproduce;
5. warm-start and interpolation identities remain within their frozen
   tolerances;
6. every quality vector sums correctly and every profile is zero-sum within
   `1e-9`;
7. legacy and resident utilities, responses, and gains agree within `1e-9`,
   with exact best-response action-map identity;
8. both partial orders reproduce the full-pool selection and the selected
   policy stays inside every blueprint cap;
9. every certificate carries the ADR-0111 non-reanchoring scope;
10. all states, policies, and quality values are finite;
11. per-step, per-profile, target-compile, cache-compile, per-seat, host, GPU,
    and total-runtime resource ceilings hold; and
12. total wall time is at most 9,000 seconds.

There is no gate on NashConv, improvement, selected candidate, headroom
capture, predecessor-seat movement, order speed, or strategy transfer.

## Questions answered

The audit reports, independently:

1. whether fresh average-64 blueprints reach useful quality on a new board;
2. whether sparse local adaptation again yields fixed-envelope-safe value;
3. whether dense belief shifts remain negative controls;
4. whether interpolation again repairs harmful endpoints;
5. whether moving the blocker target moves cap pressure to the new predecessor;
6. whether absolute-cap seat ordering reduces verified work on unseen targets;
7. whether ADR-0110's resident exactness and phase economics transfer at h32;
   and
8. the strategy-quality gain per search and verification millisecond on every
   candidate rung.

## Pre-freeze development disclosure

One complete h4 control was run on the new board before freeze. It exercised 64
source steps, the moved seat-5 target, eight warm steps, all 13 candidates, 14
resident profiles, the legacy cross-check, both verifier orders, and certificate
serialization.

It produced source zero-sum residual `1.11e-16`, legacy/resident maximum
best-response error `2.22e-16`, exact full-pool selection identity, 34 fixed
versus 23 absolute-cap seat reads, and finite output. These small-axis values
validate orchestration only. They neither set a quality threshold nor disclose
an h32 result.

## Recorded hypotheses

**Moderate confidence:** at least one local-blocker target selects a safe
non-blueprint candidate; the dense targets retain the blueprint more often.

**Low-to-moderate confidence:** interpolation again recovers value unavailable
at either endpoint.

**Low confidence:** seat 4 becomes the modal maximum-cap-excess seat among
infeasible local candidates.

**Low confidence:** ascending absolute cap reduces total seat reads. Absolute
blueprint gain is only a candidate-blind proxy for violation probability, so a
negative result would be unsurprising.

## Decision branches

- If mechanism or exactness gates fail, reject the artifact and repair before
  interpreting strategy.
- If strategy transfer is positive, the resident fixed-envelope stack has its
  first fresh-board customer and the next strategic risk is public-action or
  street width.
- If strategy transfer is cleanly negative, widen or diversify the generator
  before further verifier optimization.
- If resident economics regress materially, profile the fresh rank/feature
  distribution before changing kernels.
- Do not adopt a seat-order rule from this one board. A second unseen board is
  required before any deployment choice.

## Dissent protocol

**Confidence:** very high in exactness and certificate semantics; high in
orchestration after the complete h4 control; moderate in h32 runtime; low to
moderate in every strategic transfer hypothesis.

**Opposing evidence:** the original h32 results may be board-specific, and the
fresh h7 resident control already showed mixed seat-level speed. A strategically
negative or economically mixed result is credible evidence, not a failed
experiment.

**Largest risk:** one fresh board can reject a universal claim but cannot
establish population-level transfer. The output remains a second point, not a
board distribution.

**Cheapest falsification:** the balanced local-blocker target is first. Its
legacy cross-check can reject exactness, and its fully measured portfolio can
reject strategic and predecessor hypotheses before pooled claims are made.
