# ADR-0137: Target-identity successor passes without an action-width ranking

## Status

ADR-0136 executed once from clean commit `b52c452`.  All 13 successor gates and
all 20 immutable nested v1 gates passed.  The target-identity mechanism repair
is accepted.  The frozen top-level strategy-quality claim remains null.

## Evidence identity

The 31,927,679-byte artifact is
`experiments/results/h32-action-width-quality-v2.json`, SHA-256
`97ac74a9b76eee6ffa8155627ee2e13b16d7e11144894fa1bc1b1cf12fb44d99`.
Its configuration SHA-256 is
`fa372dbef73b03c9eb9ca90a687c11ee49d087d54fbf84d5afb7054cba518404`;
its additive implementation SHA-256 is
`1978491f7439ef137705ec7feca468b75f971e23dd62301c966010d0d1f26666`.

The nested immutable execution records v1 config SHA-256
`1431e57e2fc0e640a16aed0488a7f1070897a17740a33c273b5e1e9b9a44fa60`
and v1 implementation SHA-256
`a7072bec66e9febe179f1f1e42cd29f2e5c5efa4ef9809935d3f91071494b728`.
Strict Git metadata reports clean full commit
`b52c452ba7f49bb78360d383d8ba75a4ce1b98c0`.  The successor completed in
`936.0661 s`, below its 3,600-second ceiling.

## Mechanism result

The successor required ADR-0135 to be formally failed with exactly one false
gate, `target_identity`, and required all its other gates to be true.  Both
conditions reproduced.

For every balanced and blocker-heavy local-blocker and strength target:

- the exact shift-specific construction field set reproduced;
- the augmented parent contained exactly the seven declared measurement
  fields beyond that core;
- the core projection matched value-for-value;
- the target belief SHA-256 matched ADR-0113; and
- hand axes matched exactly.

All four corrected identity rows passed.  The immutable v1 rerun then passed
its parent, source, clean-state, h2, topology, step, deadline, cache, compact-
policy, phase-order, exact-quality, fixed-cap, GPU, and wall-time gates.

The h2 control again had exact embedded profile utility, quality error
`3.553e-15`, zero-sum residual `1.645e-15`, 378 canonical bases, and an exact
compact-policy round trip.

## Wall-clock and resident diagnostics

The balanced targets completed five one-size steps and two two-size steps.
The blocker-heavy targets completed six one-size steps and two two-size steps.
Maximum complete-step time was `24,170.529 ms`, maximum charged arm time was
`76,636.644 ms`, maximum cold-cache time was `28,344.919 ms`, and maximum
candidate seat time was `4,419.993 ms`; all are inside their frozen ceilings.

| Family | Arm | Persistent bytes | Total / maximum middle rank | Pool total | Headroom below 12 GB | Cold construction range |
|---|---|---:|---:|---:|---:|---:|
| balanced | one size | 4,232,121,372 | 10,590 / 105 | 4,298,440,192 | 7,701,559,808 | 3.835–3.980 s |
| balanced | two size | 4,019,771,708 | 20,648 / 105 | 4,086,369,280 | 7,913,630,720 | 27.408–28.345 s |
| blocker-heavy | one size | 3,468,378,036 | 9,966 / 99 | 3,526,922,240 | 8,473,077,760 | 3.262–3.352 s |
| blocker-heavy | two size | 3,294,601,492 | 19,432 / 99 | 3,353,434,624 | 8,646,565,376 | 22.356–22.626 s |

The one-size arm used 384 logical resident automata.  The two-size arm used 762
logical automata backed by 378 accepted scale-canonical bases.  Thus the
two-size representation again occupies fewer persistent bytes and pool bytes
despite roughly doubling logical middle-rank width; its cold construction is
substantially slower.  These are systems measurements, not a quality ranking.

## Frozen strategy diagnostics

Each of the eight arms emitted four unique compact candidates, for 32 total.
Every candidate was stopped by an immutable embedded-blueprint seat cap before
completing all six seats.  The fixed-envelope selector therefore chose the
embedded incumbent for both arms on all four targets:

- one-size blueprint abstentions: four;
- two-size blueprint abstentions: four;
- one-size selected normalized NashConv reduction: zero;
- two-size selected normalized NashConv reduction: zero; and
- two-minus-one selected normalized reduction: zero.

The same diagnostic pattern appeared in the formally failed v1 execution, but
outcome repetition is not a gate and did not contribute to v2 acceptance.

Do not translate zero-versus-zero into strategic equivalence.  The experiment
shows that this frozen, short-horizon candidate stream exposed no policy that
survived every incumbent seat cap on these four constructed targets.  It does
not show that a second size has no strategic value, that one size is optimal,
or that the arms have equal unconstrained quality.

The embedded immutable v1 record contains its generic conditional-claim string
because unchanged v1 code emits that string whenever its gates pass.  ADR-0136
explicitly declined to inherit it.  The authoritative v2 top-level field is
`strategy_quality_claim=null`, and its decision is
`accept_target_identity_repair_without_action_width_ranking`.

## Decision

Accept the corrected target-identity contract and the coherent execution of
the common-game wall-clock mechanism.  Preserve ADR-0135 as failed and preserve
this successor artifact unchanged.

Make no one-size-versus-two-size strategy-quality claim and make no production
action-abstraction change.  The measured bottleneck is now experimental, not
representational: the frozen warm candidate generator produces only cap-
violating proposals under both widths.

The next strategy-bearing experiment, if authorized, should be preregistered
against unseen boards or a causally new candidate generator before labels are
read.  Rebudgeting this same observed corpus or relaxing its immutable seat
caps would be post-outcome tuning and is not authorized by ADR-0137.

## Dissent

**Confidence:** very high that the target identity and all mechanism gates now
pass; high that the resident byte, rank, and timing accounting is coherent;
low that four abstaining targets identify the better action width.

**Opposing evidence:** two independent executions produced the same step
counts and all-abstention pattern despite ordinary timing variation.  That is
useful reproducibility evidence, but both executions share one board, one
incumbent, one generator, and one cap rule.

**Largest unknown:** whether the second size can create a cap-safe direction
with more planning time, a different causal generator, or unseen-board target
geometry.  This audit deliberately cannot distinguish those possibilities.

**Cheapest falsification:** freeze one unseen board and the same immutable
common-game verifier before generating any new policy.  A cap-safe candidate
from either arm would immediately falsify the idea that broad abstention is an
intrinsic property of the fixed action-width construction rather than this
observed corpus and horizon.
