# ADR-0015: Fixed regret mass does not transfer

**Status:** Accepted 2026-08-19.

## Decision

Reject `safe-solver-incumbent-v1` as a transferable quality-per-millisecond
rule. Do not retune its DCFR variant, raw pseudo-regret mass, or three-iteration
budget on the revealed holdout.

Retain two architectural controls:

1. initialize from the blueprint so the first average policy is an exact no-op;
2. retain a monotone incumbent and deploy only a candidate with certified
   frontier feasibility and a larger target-free objective.

Stop treating feasibility-only CFR convergence as the primary route to the
sum-margin optimum. The next solver must expose the frontier constraints and
secondary objective directly. Fixed CFR/LCFR/CFR+/DCFR remain baselines, and a
future warm prior must be dimensionless or derived from measured update scale
rather than expressed as an unnormalized regret mass.

## Evidence

The rule was frozen in commit `3776496` before holdout evaluation. Its canonical
document digest is
`403980953b1cfbb4c5cdb50a5ffcdd892f30bdaa9abfe87292ffe9504c147450`.
The held-in screen used blueprint iterations 20 and 1,000; the holdout used the
untouched 100 and 3,000 regimes for both LCFR and CFR+.

| Metric | Screen | Frozen holdout |
|---|---:|---:|
| Public boundaries | 16 | 16 |
| Boundaries improved by incumbent | 3 | 1 |
| Aggregate sum-margin capture | 34.0688% | 2.51385% |
| Hidden BR capture, diagnostic | 22.1516% | 2.88280% |
| Mean decision compute | 2.839 ms | 2.844 ms |
| Sum-margin per millisecond | `2.94501e-4` | `2.25286e-6` |

Target-free quality per millisecond falls by 130.72 times. All holdout
improvement comes from the root of the 100-iteration CFR+ blueprint. The other
15 boundaries retain the blueprint.

At checkpoint 1, the warm-started average policy is safe at all 16 boundaries
because it is the blueprint no-op. Only 1/16 current policies is safe and 14/16
raw current policies harm the full-game opponent-BR target. At checkpoint 3,
only 1/16 average and 1/16 current policies are safe; 14/16 raw averages and
13/16 raw current policies are harmful. The incumbent therefore succeeds as a
safety mechanism while the fixed search rule fails as an improvement mechanism.

## Interpretation

The terminate/follow gadget minimizes positive frontier violation. Once the
resolver reaches the safe face, ordinary zero-sum value is indifferent among
strategies with very different summed margins. Before reaching that face, a
raw regret prior controls movement in units tied to reach, utility, tree shape,
and accumulated updates. A fixed mass is not a transferable computation budget
or trust-region radius.

The holdout failure is thus consistent with both measured bottlenecks:

- short-horizon CFR steps frequently leave the exact safe set;
- feasibility convergence does not select the desired point within that set.

## Opposing evidence

- The holdout contains only four Kuhn2 blueprints. It rejects this frozen rule,
  not every normalized warm-start scheme.
- The `1e-10` gate is an exact-lab standard. A production system may use a
  conservative nonzero error allowance, but that allowance must be charged to
  strategy risk rather than silently called safe.
- Three iterations deliberately favors latency. Larger screened budgets recover
  much more objective value, reaching 88.64% sum-margin capture around 246 ms
  in the reference Python runner.
- Exact certification and incumbent monitoring are not yet scalable. They are
  teacher operations whose approximate replacements still need error bounds.

## Consequences

The next exact-lab solver should optimize summed frontier margins subject to
individual frontier constraints, using response generation or a primal-dual
method. Its work units and stopping criteria must report feasibility residual,
objective regret, and time separately. A scalable design should support warm
starts, active constraints, and incumbent reuse across decisions.

No neural-frontier or multiplayer claim advances from v1. In six-player poker,
multiple opponents create conflicting constraint sets; demonstrating direct
constraint handling in two-player exact games remains the prerequisite.

## Cheapest falsifying experiment

Implement a restricted constrained master problem that begins at the blueprint,
adds opponent best-response constraints on demand, and compares every master
update with the exact normal-form sum-margin optimum. If its anytime frontier
objective per millisecond does not beat the best blueprint-warm CFR incumbent,
the LP/constraint-generation direction is not justified for online search.

## Kill criterion

Do not run another raw regret-mass sweep as the primary experiment. Reopen that
family only if the new parameter is derived as a dimensionless equivalent-update
or trust-region quantity and is frozen before evaluation on unseen blueprint
strengths.
