# ADR-0017: Constrained generation v1 misses the rate gate

**Status:** Accepted 2026-08-19.

## Decision

Reject the frozen five-update `constrained-generation-v1` rule as the online
quality-per-millisecond winner. Do not promote the post-reveal six-update
result, change the stopping point, or weaken the comparison gate on this
holdout.

Retain dynamic row/column generation as the exact sum-margin teacher and as a
promising solver architecture. It removes resolver normal-form enumeration,
transfers much more reliably than the earlier fixed regret mass, and reaches
the exact objective. Its v1 scheduling and reference traversal do not yet beat
the frozen CFR control at the declared deadline.

## Frozen evidence

The preregistration is commit `58f2e66`; the immutable rule digest is
`3ffa9bc62d0f5bd6d6cde4e56bad53f4bc95dbcc02324b714250e187bc5c32f1`.
The fresh holdout contains CFR and DCFR blueprints at iterations 50, 300, and
10,000, for 24 public boundaries. Both frozen methods saw identical cases.

| Metric | Generation v1, update 5 | Frozen CFR v1, checkpoint 3 |
|---|---:|---:|
| Positive/selected incumbents | 21/24 | 3/24 |
| Aggregate sum-margin capture | 63.0223% | 29.9909% |
| Hidden BR capture, diagnostic | 36.8192% | 9.32717% |
| Mean decision compute | 7.328 ms | 2.884 ms |
| Sum-margin per millisecond | `2.50896e-4` | `3.03383e-4` |

Generation obtains 2.10 times the objective capture but uses 2.54 times the
latency, leaving its primary rate at 82.70% of frozen CFR. It therefore fails
the preregistered head-to-head gate by 17.30%.

## Gate adjudication

| Frozen gate | Result | Verdict |
|---|---:|---|
| Maximum deployed frontier violation `<= 1e-10` | `8.33e-17` | Pass |
| Maximum converged exact-objective gap `<= 1e-8` | `1.50e-11` | Pass |
| Update-five aggregate capture `>= 50%` | 63.0223% | Pass |
| Holdout rate at least one third of screen | 88.3057% | Pass |
| Beat frozen CFR target-free rate | 82.6995% of CFR | **Fail** |

The rule transfers rather than collapsing: its holdout rate is 0.883 times its
screen rate, compared with the earlier CFR v1's 130.72-fold screen-to-original-
holdout fall. That is useful architectural evidence but does not override the
declared winner criterion.

## Post-reveal diagnostics

Update six captures 95.7683% at `3.32388e-4` per millisecond, 9.56% above the
frozen checkpoint-three CFR rate. It is not a valid v1 result. The fifth round
prices a new column after evaluating its candidate; that column cannot affect
the incumbent until the sixth restricted-master solve. Two weak 50-iteration
CFR boundaries account for 96.13% of the aggregate update-five-to-six gain.

This reveals a phase-scheduling defect. At a known deadline, final-round
pricing creates future work without improving the returned policy, while a
newly priced column waits a full round before consumption. Update count is
therefore a poor compute currency even inside this direct solver.

All 24 boundaries converge by update nine, match the exact objective, capture
94.5012% of the hidden diagnostic, and reach `3.01467e-4` sum-margin per
millisecond. Exact completion is only 0.63% below frozen CFR checkpoint three,
but online selection is based on the frozen deadline, not hindsight.

The frozen CFR arm itself has a post-reveal checkpoint-one rate of
`4.78815e-4`, above its checkpoint-three rate, while capturing only 27.6467%.
Both algorithms reinforce the same point: strategy quality per millisecond is
nonmonotone, and work-unit endpoints matter.

## Opposing evidence

- Reference Python timing may overstate dynamic traversal and object-conversion
  costs relative to a flat C++ implementation.
- The rate gap is only 17.3%, and a post-reveal adjacent phase beats CFR. This
  makes the architecture worth improving, but makes retuning risk especially
  high.
- Sum-margin is still a Kuhn2 teacher objective. Higher capture need not imply
  a proportional six-player hold'em EV gain.
- Exact frontier certification remains unavailable at poker scale.
- The frozen CFR comparator selects only three boundaries; a different latency
  budget may rationally prefer generation's much larger absolute improvement.

## Consequences

The next solver experiment must use phase-aware time checkpoints rather than
integer update counts. Separate `master -> conversion -> separation ->
incumbent` (quality-producing work) from `dual pricing` (future-option work),
and never charge terminal pricing to a policy it cannot improve. Test immediate
cheap re-solves after column insertion and reuse response/value caches.

Any v2 stopping rule must be frozen on development cases and evaluated on new
blueprint regimes. The revealed update-six point may motivate the mechanism but
cannot serve as its holdout evidence. If phase-aware generation still cannot
beat CFR, retain it offline and move to a primal-feasible first-order method.

No multiplayer or neural-frontier claim advances from this result.
