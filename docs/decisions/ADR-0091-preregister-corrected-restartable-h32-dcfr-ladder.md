# ADR-0091: Preregister corrected restartable h32 DCFR ladder

**Status:** Accepted after the frozen ADR-0089 source-reuse rejection and
balanced iteration-two distance diagnostic, before any h32 quality above
iteration two

**Date:** 2026-08-20

## Decision

Run the ADR-0089 learning curve again with one correction: quality reuse is
declared per policy, not per checkpoint. The frozen configuration is
`experiments/configs/leaf-adjoint-checkpoint-ladder-v2.json`, SHA-256
`b8332fe1de5a9701bc268ebf47dcdebfc1f3e62fdc045dd401866b17c7232e8a`.
The additive runner is
`src/pontius/leaf_adjoint_checkpoint_ladder_audit_v2.py`, SHA-256
`5562abf4fad803a12a794c31e3e057b679546480a8f2cd8f23f65d0d931b01b3`.
The result target is
`experiments/results/leaf-adjoint-checkpoint-ladder-v2.json`.

Keep the game, solver, range families, checkpoint ladder, iteration-16 JSON
restart, resource ceilings, final CPU/GPU crosscheck, and strategy-quality gate
from ADR-0089 unchanged. Do not edit or reinterpret the rejected v1 runner or
configuration.

## Why a successor is required

ADR-0089 correctly stopped because its iteration-two current policy was not
byte-identical to the immutable policy whose ADR-0087 NashConv row it intended
to reuse. The maximum probability difference was only `2.94e-14` in the
balanced diagnostic, but policy closeness is not value identity and a policy
digest is not a CFR-state digest.

The correction is live evaluation, not a tolerance. Iteration-two current
quality is measured on the literal live policy. The observed distance to the
old policy is reported for both families but has no pass/fail threshold and
cannot authorize source reuse.

## Frozen per-policy measurement matrix

| Iteration | Current quality | Average quality |
|---:|---|---|
| 1 | ADR-0087 reuse on exact digest | ADR-0087 reuse on exact digest |
| 2 | live | ADR-0087 reuse on exact digest |
| 4 | live | live |
| 8 | live | live |
| 16 | live | live |
| 32 | live | live |

This is exactly nine live six-seat profile evaluations and three immutable
quality rows per range family. The live and reused sets must form a disjoint
partition of all twelve checkpoint-policy pairs. The result records and gates
both counts.

The three reused rows must match both pinned lineages:

- their live policy digest must match the ADR-0085 policy artifact; and
- `_copied_quality_row` must independently match that digest to the ADR-0087
  quality artifact.

Any mismatch rejects the run. No fallback silently changes a reuse point to a
live point after execution begins.

## Frozen trajectory and restart

For balanced and blocker-heavy h32 factor beliefs on board
`2c 7d 9h Js Qc`, run one cold alternating DCFR trajectory through iteration
32. Save complete Float64 regret and strategy-sum states at iterations
`1, 2, 4, 8, 16, 32`.

At iteration 16:

1. serialize the complete checkpoint to canonical JSON;
2. restore it into a pristine solver bound to the same resident workspace and
   GPU operator;
3. immediately re-export and require exact state-digest identity; and
4. continue iterations 17-32 only from the restored solver.

Every wide checkpoint is emitted with ADR-0091 config and implementation
provenance at construction time. The successor does not rewrite checkpoint
metadata or hashes after the restart comparison.

The existing h4 and h7 cold restart controls remain the first execution gate:
four rows must show exactly zero accumulator error plus current-policy,
average-policy, and final-state digest identity. A failure stops before h32.

## Frozen quality outputs

At every checkpoint and for current and average policies, retain:

- exact six-seat utilities, unilateral best-response values, deviation gains,
  NashConv, normalized NashConv, and zero-sum residual;
- policy digest and statistics;
- normalized improvement from uniform and improvement per cumulative training
  second; and
- for averages, marginal normalized improvement per incremental training
  second.

Report the best current and average checkpoint, every per-seat deviation
vector, every negative marginal interval, training cost, evaluation cost,
state size, resource peaks, and the literal iteration-two current-policy
distance to ADR-0085.

Do not require monotone current or average NashConv. Multiplayer alternating
DCFR has no such guarantee. Require only that final average normalized NashConv
improves over the independently measured iteration-two average by at least
`1e-4` in both families.

## Exactness, economic, and resource gates

Require:

- four exact small restart rows;
- two h32 rows with six checkpoints each;
- nine live and three exactly reused quality profiles per family;
- no training step or live six-seat quality evaluation above 60 seconds;
- host numeric peak at most 3 GB and CuPy pool total at most 4 GB;
- final seat-zero CPU/GPU utility, best-response, and deviation-gain errors at
  most `1e-9`;
- at least `3x` charged final GPU speedup in each family;
- every quality zero-sum residual at most `1e-9`;
- exactly 6,144 information sets and 12,288 hand-action entries;
- exact iteration-16 restart state identity;
- finite accumulators and quality values; and
- total pre-serialization wall time at most one hour.

The balanced and blocker-heavy iteration-two policy-distance values are
diagnostics only. They are deliberately absent from the gate set.

## Evidence boundary at freeze

Observed before this freeze:

- the frozen ADR-0089 execution reached and passed its four-row small restart
  gate, then rejected source reuse before a new wide quality point;
- balanced h32 iteration-one current and average policies are byte-identical to
  ADR-0085;
- balanced h32 iteration-two average is byte-identical;
- balanced h32 iteration-two current differs from ADR-0085 by maximum
  probability `2.94e-14`, mean policy TV `7.26e-17`, and 446 information rows;
- the restart serializer has exact h4 warm/cold unit evidence; and
- the ADR-0091 parser, per-policy matrix, mutation rejection, state-policy
  reconstruction, and literal distance diagnostic pass targeted tests.

Not observed before this freeze:

- blocker-heavy iteration-two live policy distance;
- any current or average h32 quality at iteration 4, 8, 16, or 32;
- any h32 restart state or checkpoint size from this trajectory;
- any later learning-curve slope or final CPU/GPU crosscheck; or
- whether the final-average improvement gate passes.

The immutable sources remain:

- ADR-0085 policy artifact SHA-256
  `58455716893afcff2cc19eb5000f0bb74b90fa6b49564f08762b9c9db2b023ee`;
- ADR-0087 quality artifact SHA-256
  `1ce5a4256a922c4cee88a5cc41953c159c89e283e7aa831a6aeca75066608747`;
- checkpoint serializer SHA-256
  `6f80342371bf280a03126af9043f061daaae27b4fb99f130edf3565f029af4c2`;
  and
- rejected v1 ladder runner SHA-256
  `4c24a7784057aa40a35f1743c81bf347f42ef22e9d3bedcfc8e096c60965da51`.

## Interpretation branches

- Any small restart failure rejects the serializer before wide execution.
- Any of the three declared reuse digests failing rejects the corrected run;
  numerical closeness cannot rescue it.
- A live iteration-two current NashConv close to ADR-0087 localizes the v1
  failure to identity semantics, but does not retroactively validate reuse.
- A failed iteration-16 state digest rejects restartability even if strategy
  quality improves.
- A final average that fails the `1e-4` improvement gate rejects more blind
  DCFR iterations as the next efficiency move while retaining the measured
  curve.
- A pass with sharply decaying marginal quality identifies an empirical stop
  and the value ceiling of faster sweeps.
- A pass with continuing material marginal gain authorizes native GPU fusion
  and replication across boards/range families.

## Scope and limitations

This is still one equal-stack, one-bet river abstraction on one board with two
constructed range families. Exact reduced-game NashConv measures unilateral
deviations, not coalition safety, full-NLHE exploitability, or blueprint
strength. Training and evaluation share terminal algebra, though the lineage
already includes dense small-axis identities and final CPU/GPU crosschecks.

Checkpoint JSON is a transparent laboratory state, not a production storage
format. Training bill is offline blueprint compute, not online decision
latency.

## Dissent protocol

**Confidence:** very high in the correction and restart contract; high that
the three declared reuse points remain exact; moderate that average quality
continues improving to iteration 32; low that either curve is monotone.

**Opposing evidence:** the iteration-two current difference is vastly smaller
than any practical action tolerance, so the additional live evaluation may
look pedantic. The project specifically needs literal labels for acceptance
and convergence measurements, making that cost justified.

**Largest risk:** a one-board curve gives a clean numerical answer that does
not generalize. Passing this audit authorizes replication and kernel work, not
a claim of poker strength.

**Cheapest falsification:** the already-gated h7 restart controls, followed by
the three exact reuse digests. Iteration-two current quality is the first live
wide value; iteration four is the first previously unseen strategy-quality
point.
