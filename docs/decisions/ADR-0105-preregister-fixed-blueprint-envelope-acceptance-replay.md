# ADR-0105: Preregister fixed-blueprint-envelope acceptance replay

**Status:** Preregistered; implementation and workload frozen before replay

**Date:** 2026-08-20

## Context

ADR-0103 found policies that were safe relative to the exact blueprint but were
rejected after current one became the incumbent. The incumbent-relative Pareto
contract requires every later candidate to improve aggregate NashConv and never
increase any seat's deviation gain relative to the latest incumbent. That rule
is sufficient for unilateral safety, but ADR-0104 showed it is path-dependent
and stronger than the declared no-worse-than-blueprint contract.

This is a post-label semantics audit. Every strategy-quality vector already
exists in the frozen ADR-0099, ADR-0101, and ADR-0103 artifacts. The audit will
perform zero policy construction, CFR iterations, tensor contractions, or exact
best-response evaluations. It cannot create new strategy evidence; it can test
whether a replacement acceptance contract is deterministic, source-faithful,
and mechanically safe on the complete measured corpus.

## Frozen inputs

The exact source artifacts are:

| Source | Artifact SHA-256 |
|---|---|
| ADR-0099 h32 warm search | `150362ea770c80190c8124148fa66e0a376d98d1bd01b790f3d11e5ad9b5d8a9` |
| ADR-0101 h32 candidate stream | `b432eda21d1978b1dd576a9f4e7451250f1d53dcf9a88a6efa739d681ecb6f33` |
| ADR-0103 current interpolation | `ba0fdd6ea8dfd67de3f74c9026588d3555525d362a74ad1f03295f35281cb8c0` |

The frozen implementation is
`src/pontius/h32_acceptance_semantics_replay.py`, SHA-256
`edadd8f66a28ea03223d696be0611d4ba0ca6cc1b3b3b50f2bcb0bb666acc404`.
The frozen config is
`experiments/configs/h32-acceptance-semantics-replay-v1.json`, SHA-256
`44c9cee58abe0167dfc87b5f4c9649ad2ad8c96db3ee930e715453f6bf87d809`.

Seven synthetic and immutability tests pass before the real replay. They do not
load candidate quality labels; the source-hash test reads only file bytes. The
complete repository suite passes 486/486 before freeze.

## Contracts under comparison

### Legacy incumbent-relative Pareto

Starting from the blueprint, accept a candidate only when:

1. raw NashConv improves by more than the `3e-9` raw guard; and
2. no candidate deviation gain exceeds the latest incumbent's corresponding
   gain by more than that guard.

The audit must exactly reproduce the recorded canonical unilateral incumbent
from all three source artifacts before any comparison is trusted.

### Fixed blueprint envelope

For one target belief:

1. Freeze six caps at the exact blueprint deviation gains plus the raw guard.
2. Mark a policy feasible only if all six gains remain inside those caps.
3. Include the blueprint in every observed candidate set.
4. Find the minimum raw NashConv among feasible observed policies.
5. If the blueprint is within one raw guard of that minimum, retain the
   blueprint. This is the natural abstention rule.
6. Otherwise form a tie band containing every feasible non-blueprint policy no
   more than one raw guard above the minimum and select the lexicographically
   smallest policy SHA-256.
7. On a stream, recompute this canonical choice over the complete observed set
   after every arrival. Do not compare only with the latest selected policy.

The contract is deterministic and set-valued before the digest tie break. It
may spend safety margin created by another candidate, but it can never cross a
source blueprint cap. It certifies unilateral deviation gains only. It is not a
coalition, collusion, or equilibrium certificate.

## Frozen candidate pools

Each of four target rows—two range families by two belief shifts—gets four
pools:

1. the three-candidate ADR-0099 frozen search stream;
2. the eight-candidate ADR-0101 full interleaved current/average stream;
3. the five-candidate ADR-0103 current-one-to-current-two interpolation stream;
   and
4. every measured candidate row from all three artifacts, deduplicated by
   policy SHA-256 with exact-quality agreement required.

The union must contain 13 unique policies per target. Source duplicates are a
correctness control: equal policy digests must agree in NashConv and all six
deviation gains to `1e-15` absolute error.

## Frozen order screen

Both contracts are replayed under 67 orders per target and pool:

- canonical source order;
- reverse order;
- policy-digest order; and
- 64 deterministic seeded permutations.

The fixed envelope must return one final policy digest across every order. Path
dependence in the legacy contract is reported but is not required: this audit
must not manufacture a failure in the control.

## Frozen gates

The result passes only if:

1. all three source hashes and successful frozen statuses reproduce;
2. all 12 source target rows reduce to four matching stable target descriptors;
3. blueprint policy digests and quality vectors agree across sources;
4. stream candidate counts are exactly 3, 8, and 5, and each union has 13
   unique policies;
5. source-duplicate quality error is at most `1e-15`;
6. every acceptance vector sums to raw NashConv within `1e-12` and raw divided
   by span reproduces normalized NashConv within `1e-15`;
7. the canonical legacy replay exactly reproduces every recorded source final
   unilateral incumbent and value within `1e-15`;
8. all 67 fixed-envelope orders select the same final policy in every one of
   the 16 target/pool rows;
9. every selected policy remains inside all six frozen blueprint caps;
10. synthetic below-guard abstention, digest tie, reversed tie, and cap-breach
    controls all pass;
11. the new-strategy-evaluation count is exactly zero; and
12. total replay time is at most 10 seconds.

No gate requires a particular candidate, quality improvement, headroom capture,
advantage over the legacy rule, or observed legacy path dependence. Those
labels are already known in part and remain outcomes.

## Questions answered

The audit will report:

1. whether the fixed-envelope implementation is actually order-independent;
2. whether its selected policies satisfy the declared source safety vector;
3. how often the incumbent-relative contract changes final policy with order;
4. what each source-only pool and the complete measured union select; and
5. the exact objective difference between canonical legacy selection and the
   fixed envelope.

## Decision rule

If every mechanism gate passes, the fixed blueprint envelope becomes the
acceptance semantics for the successor h32 policy-delta verifier. The complete
six-seat deviation-gain vector and the blueprint cap vector must travel with
every certificate.

If source replay, order invariance, cap compliance, abstention, or tie behavior
fails, retain incumbent-relative Pareto and repair the semantics before any
verifier optimization.

## Dissent protocol

**Confidence:** very high that the fixed envelope expresses the declared
unilateral blueprint-safety constraint; high that the replay can test its
implementation honestly; moderate that this is the right eventual product
contract.

**Opposing evidence:** incumbent-relative Pareto preserves every coordinate of
improvement already earned. The fixed envelope can knowingly give some of that
margin back, even while remaining safer than the blueprint and improving total
NashConv.

**Largest risk:** treating six independent unilateral caps as protection from
coordinated opponents. This ADR makes no such claim.

**Cheapest falsification:** the frozen zero-evaluation replay itself. Any order
dependence or cap violation rejects the successor contract immediately.
