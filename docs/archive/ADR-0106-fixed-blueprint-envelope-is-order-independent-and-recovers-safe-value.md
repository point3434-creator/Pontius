# ADR-0106: Fixed blueprint envelope is order-independent and recovers safe value

**Status:** Fixed blueprint envelope accepted as the h32 policy-verifier
acceptance contract; incumbent-relative Pareto retained only as an optional
stronger monotonic mode

**Date:** 2026-08-20

## Result

The frozen ADR-0105 replay completed from clean commit `50e0f27` with every
gate passing. The canonical local artifact is
`experiments/results/h32-acceptance-semantics-replay-v1.json`:

- SHA-256:
  `1898c24a6c0232059a19c2151f29537a574ba85d8ec9a3641c117eda9b9087af`;
- size: 1,983,395 bytes;
- config SHA-256:
  `44c9cee58abe0167dfc87b5f4c9649ad2ad8c96db3ee930e715453f6bf87d809`;
  and
- implementation SHA-256:
  `edadd8f66a28ea03223d696be0611d4ba0ca6cc1b3b3b50f2bcb0bb666acc404`.

Measured wall time was 0.328 seconds. The audit constructed or evaluated zero
new strategies.

## Correctness result

The replay exercised 1,072 arrival-order rows: four targets by four candidate
pools by 67 orders. The fixed blueprint envelope selected one identical final
policy digest across every order in all 16 target/pool rows. Every selection
remained inside all six blueprint deviation-gain caps.

The provenance and arithmetic controls are unusually clean:

- all three source artifact hashes and successful statuses reproduce;
- all 12 source targets reduce to four identical stable descriptors;
- blueprint identity error: exactly zero;
- duplicate-policy quality error: exactly zero;
- maximum `sum(deviation gains) - NashConv` error: exactly zero at stored
  precision;
- maximum raw/normalized conversion error: exactly zero;
- all three canonical legacy streams reproduce their recorded final unilateral
  incumbents exactly; and
- below-guard blueprint abstention, forward and reversed digest ties, and a
  deliberately attractive cap-breaking candidate all behave as frozen.

This closes the implementation question. The fixed-envelope selector is a
canonical function of the measured candidate set, not its arrival order.

## Complete-union selections

The union contains 13 unique measured policies per target after exact digest
deduplication.

| Range family | Belief shift | Fixed-envelope selection | Normalized NashConv | Legacy canonical |
|---|---|---|---:|---|
| balanced | local blocker | alpha 0.75 | 0.002034368 | current 1 |
| balanced | all-seat strength | blueprint | 0.011344383 | blueprint |
| blocker-heavy | local blocker | alpha 0.50 | 0.001764632 | current 1 |
| blocker-heavy | all-seat strength | blueprint | 0.012979175 | blueprint |

Total normalized NashConv is:

- blueprints: `0.028442394522`;
- canonical incumbent-relative result: `0.028178213131`; and
- fixed-envelope result: `0.028122557798`.

The fixed envelope therefore produces safe reduction `0.000319836723`, versus
`0.000264181391` under the canonical incumbent-relative stream. It recovers an
additional `0.000055655332`, or 21.07% more reduction from the same already
evaluated candidate corpus.

The new rule does not weaken the dense negative. On both all-seat strength
shifts, search average one is the only non-blueprint policy inside every cap,
and it is within the abstention guard of the blueprint. All other 12 union
policies are cap-infeasible. Both contracts correctly retain the blueprint.

## Measured path dependence

Four of the 16 incumbent-relative pool rows change final policy with arrival
order: the interpolation and complete-union pools for each local target.

Across the 67 frozen orders, the balanced interpolation pool ends at:

- current one 20 times;
- alpha 0.75 18 times;
- alpha 0.25 16 times; and
- alpha 0.50 13 times.

The balanced complete union ends at current one 26 times, alpha 0.25 17 times,
alpha 0.75 15 times, and alpha 0.50 nine times.

The blocker-heavy interpolation pool ends at current one 26 times, alpha 0.25
21 times, and alpha 0.50 20 times. The complete union ends at current one 35
times, alpha 0.50 20 times, and alpha 0.25 12 times.

No numerical ambiguity causes these differences. They arise because the first
accepted policy changes the coordinate-wise comparison point. The rule is
path-dependent by construction, and the artifact now measures the effect over
real exact vectors rather than only a synthetic example.

## Safety geometry

For the balanced local target, six of 13 candidates are inside the fixed
envelope: search average one and two, current one, and alpha 0.25, 0.50, and
0.75. Alpha 0.75 remains `0.000146` raw below its tightest cap.

For the blocker-heavy local target, five candidates are feasible: search
average one and two, current one, and alpha 0.25 and 0.50. Alpha 0.50 remains
`0.0000216` raw below its tightest cap; alpha 0.75 breaches only seat two.

The fixed rule is doing exactly the intended constrained optimization: it
chooses the lowest-NashConv point inside the original six-dimensional box. It
does not merely prefer interpolations, and it rejects lower-NashConv policies
when their per-seat vector crosses a cap.

## Decision

1. Make the fixed blueprint envelope the acceptance contract for the successor
   h32 fixed-belief policy-delta verifier.
2. Every certificate must carry the blueprint policy digest, exact target
   descriptor, six blueprint deviation gains, raw guard, candidate deviation
   gains, scalar NashConv, and deterministic tie fields.
3. Treat candidate arrival as an observed set. Recompute the canonical optimum
   when the set changes; never make the final result depend on worker completion
   order.
4. Retain incumbent-relative Pareto as an explicitly named optional mode when
   an application values coordinate monotonicity more than aggregate strategy
   quality. Do not call it the default safety definition.
5. Preserve blueprint abstention inside the guard. Digest order resolves only
   meaningful non-blueprint tie bands; it cannot force a below-guard policy
   change.
6. Continue to reject both dense shift directions. Their failure is candidate
   generation, not acceptance semantics.
7. Build the policy-delta verifier against this fixed-envelope customer before
   optimizing the candidate generator further. The verifier must return the
   entire six-seat vector, not only a scalar sign.

## Architectural consequence

The acceptance product is now mathematically separated into two layers:

1. an evaluator or verifier supplies a bounded six-seat deviation-gain vector
   and scalar NashConv for each candidate; and
2. a deterministic fixed-envelope selector performs constrained choice over
   the verified set.

This separation matters for spare compute. A tight budget may verify current
one and stop. Additional compute may add alpha 0.50 or a larger portfolio. The
selector can incorporate those candidates without making the answer depend on
which verification completed first.

The next systems question is therefore precise: can a fixed-belief policy-delta
verifier reproduce the exact leaf-adjoint acceptance vector more cheaply than a
full exact candidate evaluation, with bounds tight enough to preserve the same
fixed-envelope selection across a portfolio?

## What this establishes—and what it does not

The result establishes order independence, exact source replay, deterministic
guard behavior, and unilateral blueprint-cap compliance over every h32 policy
vector measured so far.

It does not establish coalition safety, transfer across boards or deeper trees,
or online latency. The 21.07% uplift is corpus reuse, not new search quality,
and must not be counted as a new algorithmic strategy gain.

## Dissent protocol

**Confidence:** extremely high in the mechanical result; high that fixed
blueprint caps are the correct default contract for this verifier; moderate
that unilateral caps remain useful as the game widens.

**Opposing evidence:** fixed caps allow a selected policy to surrender some
seat-specific improvement previously held by another candidate. An
incumbent-relative product can honestly prefer the stronger monotonic promise.

**Largest risk:** a future implementation advertises the fixed envelope as
field or coalition safety. It is neither.

**Cheapest falsification:** when the policy-delta verifier arrives, compare its
selected digest against the exact leaf-adjoint teacher on the complete 13-policy
corpus under all 67 orders. A single cap, abstention, or selection mismatch
rejects it.
