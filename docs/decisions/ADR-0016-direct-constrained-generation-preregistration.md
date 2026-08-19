# ADR-0016: Preregister direct constrained generation v1

**Status:** Frozen before fresh holdout, 2026-08-19.

## Decision

Advance a blueprint-started restricted-master algorithm to a fresh holdout at a
fixed budget of five master updates. Generate violated opponent-frontier rows
with an exact dynamic counterfactual best response. Price the best missing pure
resolver column with one LP-dual-weighted dynamic best response. Retain the
blueprint unless an independently checked candidate is frontier-feasible and
strictly improves summed guaranteed margin.

This is a direct implementation of the target-free safe sum-margin objective,
not another terminate/follow gadget equilibrium solve. The normal-form oracle
and full-game best-response target remain excluded teachers and diagnostics.

## Derivation

For active frontier-response rows `r = (I, q)`, restricted columns `j`, margins
`M[r,j]`, strategy weights `x_j`, and auxiliary entry margins `m_I`, solve:

```text
maximize  sum_I m_I
subject to m_I <= sum_j M[(I,q),j] x_j  for active (I,q)
           sum_j x_j = 1
           x_j, m_I >= 0
```

The LP dual gives nonnegative response-row weights `y_(I,q)` and an effective
simplex multiplier `lambda`. A missing resolver plan has reduced cost
`sum_(I,q) y_(I,q) M[(I,q),j] - lambda`. Because the weighted margins equal a
constant plus resolver utility in one synthetic game, a dynamic best response
prices the best column without enumerating the resolver normal form.

Response separation converts the current restricted mixture to a
realization-equivalent behavioral policy and computes the opponent's dynamic
counterfactual best response. Any frontier entry whose auxiliary margin exceeds
its realized worst-case margin contributes a new row.

## Screen evidence

The held-in screen uses the same 16 LCFR/CFR+ boundaries at blueprint
iterations 20 and 1,000 used to select the earlier CFR control.

| Metric | Direct generation, update 5 | Frozen CFR v1, update 3 |
|---|---:|---:|
| Positive incumbents | 15/16 | 3/16 |
| Aggregate sum-margin capture | 84.1691% | 34.0688% |
| Hidden BR capture, diagnostic | 71.5120% | 22.1516% |
| Mean decision compute | 7.270 ms | 2.839 ms |
| Sum-margin per millisecond | `2.84122e-4` | `2.94501e-4` |

The direct solver obtains 2.47 times the objective capture but is 3.52% behind
the unusually strong screened CFR rate. Full convergence takes at most ten
updates, reaches 100% exact sum-margin capture, and uses a mean 10.587 ms. The
selected five-update point is the screen maximum for target-free quality per
millisecond.

The Python screen spends more time in response separation and resolver pricing
than in simplex solve. This supports a flat-tree/C++ traversal and cache path;
it does not support optimizing the LP backend first.

## Fresh holdout and gates

The untouched holdout is frozen as CFR and DCFR blueprints at iterations 50,
300, and 10,000: 24 public boundaries. The same cases will also run the already
frozen DCFR/mass-10/three-iteration CFR rule.

The canonical frozen rule digest is
`3ffa9bc62d0f5bd6d6cde4e56bad53f4bc95dbcc02324b714250e187bc5c32f1`.

Reject v1 without retuning if any claimed incumbent violates a frontier by more
than `1e-10`, if a converged solve differs from the exact objective by more than
`1e-8`, if update-five aggregate capture is below 50%, if its rate is below one
third of the screen rate, or if it fails to beat frozen CFR v1 on target-free
sum-margin per millisecond.

## Opposing evidence

- The screen is still two-player Kuhn and exact certification is exponential
  in the current teacher implementation.
- The first two updates generally remain blueprint no-ops; this creates a
  latency floor that a more genuinely primal-feasible update may remove.
- Intermediate restricted-master candidates can be unsafe. Monotone incumbent
  retention prevents deployment but does not eliminate wasted traversal.
- Dynamic pricing avoids resolver normal-form enumeration, but the synthetic
  game expands with active response rows. It is not yet a poker-scale proof.
- Screen timing is standard-library Python. Only paired reference rates and the
  location of cost are meaningful.

## Consequences

No neural, multiplayer, or runtime deployment claim advances before the frozen
holdout. If v1 transfers, the next optimization target is shared traversal and
incremental response/value caching, followed by controlled frontier-value
error. If it fails, retain the exact algorithm as a teacher and investigate a
primal-feasible first-order method rather than tuning this holdout.
