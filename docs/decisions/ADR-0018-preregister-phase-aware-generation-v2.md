# ADR-0018: Preregister phase-aware constrained generation v2

**Status:** Frozen before fresh holdout, 2026-08-19.

## Decision

Advance one mechanical efficiency correction to a fresh holdout: return the
incumbent at the sixth candidate-ready phase, before terminal pricing. Use one
dynamic opponent best response for safety separation. Remove two duplicate
laboratory audits from charged online work: rerunning the same response oracle
and rechecking normal-form-to-behavioral realization against every active row.

The exact normal-form teacher still checks objective capture after construction,
and the deployed behavioral policy still receives one exact worst-case
frontier separation. The change removes duplicated computation; it does not
relax the safety gate or alter the sequence of candidate strategies.

## Phase contract

A candidate-ready checkpoint contains:

```text
restricted-master build and solve
    -> mixed-to-behavioral conversion
    -> one opponent response separation and safety certificate
    -> monotone incumbent update
    -> return point
```

Dual pricing follows only when another candidate cycle will be attempted. Work
spent pricing after a return point cannot improve that returned policy and is
not charged to it. The sixth checkpoint therefore consumes pricing from rounds
one through five, but performs no sixth pricing call.

V1 remains reproducible because all former verification and pricing defaults
remain enabled. V2 selects the explicit nonduplicated phase contract.

## Development evidence

Both prior matrices are now revealed development data: 40 boundaries total.
The fixed sixth candidate-ready checkpoint is the pooled quality-per-millisecond
maximum.

| Development subset | Sum capture | Hidden BR capture | Mean candidate ms | Sum margin/ms |
|---|---:|---:|---:|---:|
| Original LCFR/CFR+ screen | 86.1473% | 74.4648% | 5.325 | `3.97046e-4` |
| Revealed CFR/DCFR set | 95.7683% | 86.2449% | 5.518 | `5.06366e-4` |
| Pooled | 92.3114% | 81.2621% | 5.440 | `4.63568e-4` |

On the weaker subset, the phase-correct v2 rate is about 35% above the frozen
CFR screen rate. On the other subset it is about 67% above frozen CFR
checkpoint three and about 5.8% above the stronger post-reveal checkpoint-one
diagnostic. These are development comparisons, not claims of transfer.

Response separation falls from roughly 2.6 ms to 1.5 ms at six updates, and
policy conversion falls from roughly 0.8 ms to 0.3 ms. Strategy capture is
bit-for-bit unchanged at a given candidate index.

## Fresh holdout and gates

The untouched holdout crosses all four blueprint update rules—CFR, LCFR, CFR+,
and DCFR—with unseen iteration counts 75, 700, and 5,000. It contains 48 public
boundaries. The frozen DCFR/mass-10 CFR control runs checkpoints one and three
on exactly the same cases.

The canonical frozen rule digest is
`ffee077d5af33d13ed1e4819f3af8834187407d77aa950fa5b6f001dfa1ccb4e`.

V2 must retain at least 75% aggregate sum-margin capture and half its pooled
development rate. It must violate no selected frontier by more than `1e-10`,
must not exceed the exact objective by more than `1e-8`, and must beat both
frozen CFR checkpoint three and the better of CFR checkpoints one and three on
target-free sum-margin per millisecond. No parameter changes follow reveal.

## Opposing evidence

- Six master solves remain a discrete work count, not a real deadline policy.
- Removing redundant audits is safe only because one behavioral-policy
  separation remains mandatory and the exact teacher continues to test the
  implementation.
- Timings are single-run standard-library Python measurements and can shift
  with host load.
- The holdout is still two-player Kuhn; active-row growth and pricing-game size
  may dominate in poker.
- A fixed checkpoint cannot exploit easy/hard boundary variation as well as a
  calibrated phase-cost scheduler.

## Consequences

Passing v2 would accept the nonduplicated phase contract as the new exact-lab
control, not as a poker runtime. The next work would fit a conservative
phase-cost predictor at 5/20/50 ms and then attack specialized traversal/cache
reuse. Failing v2 would keep the correctness implementation but reject this
fixed checkpoint before any neural-frontier experiment.
