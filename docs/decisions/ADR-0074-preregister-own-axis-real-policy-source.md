# ADR-0074: Preregister canonical own-axis real-policy source

**Status:** Accepted before source policies, exact source utilities, NashConv, best-response profiles, policy ranks, or representation timing

**Date:** 2026-08-19

## Decision

Supersede ADR-0073 before execution. Generate real six-player policies directly
on the four- and seven-hand axes used by ADR-0067/0068, serialize those policy
tables as the objects of record, and only then freeze a representation and
clean-fringe read-path screen against the resulting artifact SHA-256.

The frozen source configuration is
`experiments/configs/real-policy-source-v1.json`. Its SHA-256 is
`af19bea7f779229087f2be92deb40065e9f1e52c1a0c504a2f6d641c5537939c`.
The result target is
`experiments/results/real-policy-source-v1.json`.

This stage may observe source-policy quality, policy change, and generation
cost. It may not compute root tensor ranks, choose a seat order, fit a selector,
or compare candidate evaluators. Source quality is metadata, never a gate.

## Why own-axis generation is now feasible

The generic recursive six-player solver costs about 28.9 seconds per DCFR
iteration on the prior four-hand calibration. Before any source policy or rank
was generated, a vectorized solver was implemented over the already validated
public-tree quotient. It preserves literal information sets and alternating
updates while evaluating chance/opponent reach and continuation values over a
contiguous joint-deal axis.

Iteration-level tests compare current policy, average policy, every regret, and
every strategy-sum accumulator against `TabularCFR`. They pass through three
iterations for CFR, LCFR, CFR+, and DCFR and include a six-player control.

Revealed engineering timings, used only to size the frozen ladders, were:

- four-hand balanced: 1,158 compatible deals and 28.49 ms for the first DCFR
  iteration;
- four-hand blocker-heavy: 588 deals and 22.84-24.41 ms across eight
  iterations;
- seven-hand balanced: 33,455 deals, 8.11 seconds to compile the literal
  terminal layout, 349.56 ms for one DCFR iteration, and approximately 206 MB
  of primary solver scratch; and
- seven-hand blocker-heavy: 17,538 deals, 4.20 seconds to compile, and
  194.07-221.22 ms across five iterations.

No policy table, utility, NashConv, response, tensor rank, or representation
timing was inspected during this calibration.

## Frozen source games and warm start

For each combination of hand width in `{4, 7}` and range family in
`{balanced, blocker_heavy}`:

1. reproduce the ADR-0067 public-policy-root hand axes and seed;
2. instantiate the frozen three-component nonnegative factor belief;
3. materialize only its compatible source-game deals;
4. compile the exact 385-node, 193-terminal public quotient;
5. initialize DCFR with a uniform pseudo-regret prior of exactly `1.0` utility
   unit; and
6. serialize the average policy at every frozen checkpoint.

Checkpoint zero is explicitly the current-policy fallback before any average
strategy contribution. It exists to anchor the rank curve at the uniform prior,
not to masquerade as a trained average.

The four-hand ladder is `{0, 1, 4, 16, 64, 256}`. The seven-hand ladder is
`{0, 1, 4, 16, 64}`. These geometric ladders measure early, middle, and sharper
finite policies without selecting a checkpoint by NashConv or later rank.
Consecutive mean information-set total variation is recorded for the future
candidate-size axis.

## Literal response objects

Checkpoint 16 is the declared mid-trajectory reference on both widths. Compute
one exact unilateral best response for each of the six target seats against
that average profile. Replace only the target seat and serialize all six
resulting complete profiles.

Each response object declares:

- `kind = literal_unilateral_best_response`;
- target seat and reference checkpoint;
- the exact source evaluation of the spliced profile; and
- explicit-public-state or policy-tape dispatch provenance.

The target's realized utility in the spliced profile must agree with the
baseline's independently computed best-response value within `1e-10`.
Response objects are realistic pure/off-path representation probes. They are
not required to compress in the successor.

## Canonical object and reproducibility semantics

Every profile stores its complete policy table in sorted information-key and
action order, plus a SHA-256 over that canonical Float64 JSON table. The source
artifact embeds solver, seed, axis, checkpoint, range/game digests, config and
implementation hashes, provenance, policy statistics, and exact evaluation
metadata.

The serialized table and its recorded SHA-256 are the experimental object.
Downstream audits load it and must not silently regenerate the solver policy.

The source run also executes an independent deterministic replay. On the
current single-threaded implementation, every checkpoint digest must be byte-
identical and the maximum probability disagreement must be at most `1e-12`.
A future native or parallel solver may replace digest identity with a declared
`1e-12` numerical replay diagnostic, but it cannot rewrite this artifact.

## Frozen gates

Require:

- maximum deterministic replay policy error at most `1e-12`;
- zero replay digest mismatches;
- maximum response-target value error at most `1e-10`;
- zero policy/action schema mismatches;
- source-profile zero-sum residual at most `1e-10`;
- all 22 checkpoint profiles; and
- all 24 unilateral-response profiles.

There is deliberately no NashConv, utility, entropy, purity, policy-TV, runtime,
rank, storage, or compression gate. The stage can fail only to construct the
declared objects faithfully.

## Successor representation and read-path screen

After this artifact passes, freeze a separate screen referencing its exact
SHA-256. Retain uniform, hashed-dense, and hashed-pure controls on identical
geometry so the rank table bridges to ADR-0068.

The decisive outputs are:

1. crown and cut ranks versus DCFR checkpoint;
2. complete 3/3 seat-partition and within-half order results;
3. clean-frontier size, delta-support frontier, rank histogram, and total
   batched feature width;
4. policy-TV versus consecutive-checkpoint and BR-sized candidates; and
5. a three-part bill for clean-fringe reads, recompose-then-contract, and the
   flat compatible-deal incumbent.

Each evaluator receives the same accounting: one-time compile/cache cost,
per-candidate marginal cost, and a break-even curve over reuse count. No single
reuse-four ratio is allowed to collapse that structure. The flat tape receives
the same compilation amortization as TT caches.

Average-policy provenance may dispatch to a compact value product only if the
measured rank/cap gates pass. Literal BR provenance remains an explicit-state
customer. No small-axis speed win authorizes a 32-hand runtime path; that path
must scale credibly in measured frontier rank/width after dense-free terminal
construction.

## Dissent protocol

**Confidence:** high that the vector solver preserves the reference trajectory;
high that artifact identity is reproducible; moderate that these finite DCFR
averages resemble a future blueprint; low that root rank improves monotonically
with source quality.

**Opposing evidence:** six-player CFR lacks the two-player convergence
guarantee, the hand axes are selected probes rather than full ranges, and a
finite average can sharpen non-monotonically. A late checkpoint can have worse
NashConv or higher/lower rank than an earlier one.

**Largest risk:** seeing a favorable rank at one checkpoint and promoting that
checkpoint as a strategy choice, or treating source NashConv as evidence about
full 6-max NLHE.

**Cheapest falsification:** deterministic replay or exact response-target value
identity fails. In that case no representation screen may consume the artifact.
