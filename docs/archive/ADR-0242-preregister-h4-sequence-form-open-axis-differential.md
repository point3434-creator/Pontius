# ADR-0242: Preregister h4 sequence-form open-axis differential

- Status: accepted preregistration before the h4 open-axis run
- Date: 2026-08-22
- Follows: ADR-0241
- Config: `experiments/configs/h4-sequence-form-open-axis-v1.json`
- Config SHA-256: `ac94319ad03e8dc8d6fc0b9d425f5e8a399552c38cfbfba3455da796cd06a2d1`
- Primitive SHA-256: `131928a4fd8aeb12dd7d2ca03ebabc44e06af5ddf666d8ad900f07e0e1e5aaee`
- Implementation SHA-256: `f5ee2a888bfb6f2dfde9bda681961f78b0f7007c05b91a67435c2e9a5c44628e`
- Primitive control SHA-256: `074e056f5558df76b078fa4f325f5f4f084d6dea783df9a71b297a97fa3cfb87`
- Runner control SHA-256: `b1851e3c84a56bd2a456f57c8789ab49466898de3b822cbcd68c39676c6058c7`

## Question

Can one target-omitted leaf contraction extract an exact fixed-response payoff
row over an acting seat's complete sequence-form realization axis, including a
topology where that seat acts twice on one path? Does the same row reduce to the
behavioral-coordinate shortcut on a post-bet path-single-visit continuation?
Can the fixed-response splice use explicit external posterior hand axes without
the ADR-0239 embedded-key defect?

This is a label-free coefficient identity and cost differential. It does not
run a one-seat optimizer, certificate, candidate search, or strategy label.

## Frozen coefficient construction

For each terminal public node, run the accepted target-omitted leaf contraction
with acting seat `i` omitted and payoff seat `j`'s terminal automata. Assign the
resulting acting-hand payoff vector to the last seat-`i` public edge on that
terminal path. Summing terminal vectors by `(public node, hand, action)` yields
the coefficient of the corresponding last-action sequence realization
variable. A terminal path on which seat `i` never acts contributes to the
affine constant.

This grouping is exact for full sequence form even when seat `i` acts twice.
When the compiled topology proves that no seat appears twice on any path, every
acting parent realization has mass one and the same coefficients are also
affine in the full behavioral axis.

The acting seat's gain row is its invariant source best-response value minus
its profile-payoff row. Every opponent gain row is the source best-response-
tape payoff row minus its profile-payoff row. The response tape remains fixed
at both source and endpoint; selector changes are outside this coefficient
identity.

## Frozen h4 workload

Use the balanced six-player h4 belief on board `2c 7d 9h Js Qc`, axis seed
`20260819`, three mixture components, pot `12`, stack `30`, and bet `3`. Use the
deterministic key-hash source policy and an endpoint that replaces every acting
row by the frozen `(public_node + hand_index + 1) mod actions` vertex.

Run exactly two layouts:

1. `full_repeated_actor`: the 385-node full one-bet tree, acting seat 0, 32
   acting public nodes and 256 sequence entries per payoff row. The compiled
   path-single-visit gate must fail.
2. `post_bet_single_visit`: the 63-node continuation after `p0:check/p1:bet`,
   acting seat 2, one acting public node and eight entries per payoff row. The
   compiled path-single-visit gate must pass.

For each layout, extract exactly six source-profile payoff rows and five source
opponent-response payoff rows. Construct six gain rows without approximate
deduplication. Use maximum feature width 96 and the existing h4 sparse CPU
contraction; this trial does not invoke CUDA.

## Frozen independent teacher

Materialize the exact compatible h4 joint deal axis through the accepted public
tensor evaluator. Directly evaluate source and endpoint profile utilities. For
each opponent, overwrite that opponent with its exact source best-response map
and directly evaluate the fixed response at both source and endpoint. Compare:

- every profile row at source and endpoint;
- every fixed-response row at source and endpoint;
- every derived gain row at source and endpoint; and
- the acting seat's source/endpoint best-response invariance.

The dense teacher shares game/payoff semantics with the sparse extractor but
does not call the new terminal-to-last-sequence assembly.

## External-axis mutation

Reverse every explicit h4 hand axis while leaving the embedded layout axes
unchanged. Construct a hand-distinguishing deterministic response map. The new
splice must rebuild every information key with the explicit external hand and
public history, produce zero selected-action errors, and differ from the old
embedded-key splice in at least one entry. Require exact response-key coverage;
missing, extra, unavailable, or shape-mismatched rows fail closed.

## Frozen gates and measurements

Require all profile, fixed-response, gain, acting-BR-invariance, and zero-sum
errors to be at most `2e-11`. Require exact layout and sequence-entry counts,
six-plus-five pass counts, the two opposite topology classifications, the
external-axis mutation, clean Git provenance, parent pass, finite telemetry,
zero labels/certificates, at most 1 MB for the six retained gain rows per
layout, and at most 60 seconds total control time.

Report without promotion thresholds:

- response-oracle milliseconds;
- coefficient contraction, assembly, and wall milliseconds;
- direct-teacher milliseconds;
- coefficient entries and retained bytes;
- numerical rank, effective condition number, and minimum normalized row
  separation for the six gain rows;
- maximum contraction middle rank, scratch estimate, and GPU-pool field; and
- layout, workspace, sparse-operator, and terminal-automaton bytes.

Numerical row similarity is diagnostic only. No exact row may be removed in
this differential.

## Promotion rule

If every frozen gate passes, authorize one corrected external-axis h32 row-
extraction preflight. That successor may reuse ADR-0238's cross-payoff algebra
but must use the explicit-axis splice and the sequence-form/behavioral topology
gate from this line. It must measure actual resident GPU pass cost, response-
oracle cost, row bytes, conditioning, memory headroom, and the 15-second ledger
before constructing or optimizing any candidate.

If either topology disagrees with the dense teacher, the external-axis mutation
does not discriminate the old splice, or any approximate row deletion is
needed, reject this extractor and do not reopen h32.

## Claims boundary

A pass establishes only h4 coefficient identity and authorizes a label-free
h32 extraction preflight. h4 CPU timing is not an h32 latency prediction. No
strategy-quality, multiplayer-safe, optimization-quality, deployment,
composition, cross-street, population, or broad poker-strength claim is made.

## Decision

Commit the primitive, differential, config, controls, this ADR, roadmap, and
generated status from one clean tree before the first frozen h4 invocation.
Run once and follow the frozen promotion branch without changing tolerances or
selecting coefficient rows from the result.
