# ADR-0019: Phase v2 wins paired but fails its transfer gate

**Status:** Accepted 2026-08-19.

## Decision

Formally reject the frozen six-candidate `constrained-generation-phase-v2`
rule because it fails one preregistered gate: absolute sum-margin per
millisecond retains only 32.74% of development, below the frozen 50% minimum.
Do not waive or rewrite that gate after reveal.

Accept the nonduplicated phase implementation as the new exact-lab efficiency
control. On identical fresh cases it beats the better frozen CFR checkpoint by
5.18 times in target-free quality per millisecond, captures 9.93 times as much
of the exact objective, remains safe, and does not change candidate strategies.
This accepts a mechanical implementation improvement, not the frozen v2 rule
as a transferable stopping policy or poker runtime.

## Frozen evidence

The preregistration is commit `c7d096b`; its immutable digest is
`ffee077d5af33d13ed1e4819f3af8834187407d77aa950fa5b6f001dfa1ccb4e`.
The fresh holdout crosses CFR, LCFR, CFR+, and DCFR blueprints at iterations 75,
700, and 5,000 for 48 public boundaries.

| Metric | Phase v2 | Better frozen CFR checkpoint |
|---|---:|---:|
| Checkpoint | candidate-ready 6 | checkpoint 3 |
| Positive/selected boundaries | 44/48 | 5/48 |
| Aggregate sum-margin capture | 81.2623% | 8.18700% |
| Hidden BR capture, diagnostic | 59.6536% | 9.61820% |
| Mean charged milliseconds | 5.453 | 2.848 |
| Sum-margin per millisecond | `1.51755e-4` | `2.92707e-5` |

Under the frozen candidate-ready accounting, v2 is 5.1845 times the best CFR
rate. Charging pricing that an executable fixed-six loop already performed to
discover earlier convergence gives 5.593 ms and `1.47968e-4`, still 5.0552
times CFR. The conclusion is not sensitive to that accounting distinction.

## Gate adjudication

| Frozen gate | Result | Verdict |
|---|---:|---|
| Maximum selected frontier violation `<= 1e-10` | `1.11e-16` | Pass |
| Maximum exact-objective overshoot `<= 1e-8` | `3.05e-16` | Pass |
| Aggregate sum-margin capture `>= 75%` | 81.2623% | Pass |
| Holdout rate at least half of development | 32.7363% | **Fail** |
| Beat frozen CFR checkpoint 3 | 5.1845x | Pass |
| Beat better CFR checkpoint 1 or 3 | checkpoint 3; 5.1845x | Pass |

One failed gate rejects the frozen rule despite the paired win.

## Why absolute rate did not transfer

Mean exact safe-improvement headroom is `0.0010184` per holdout boundary versus
`0.0027321` across development, only 37.28% as large. Candidate runtime stays
nearly flat and capture remains high. Raw margin per millisecond therefore
falls mainly because the new blueprints offer less margin to capture, not
because the solver becomes proportionally less efficient.

Opportunity-normalized capture per candidate millisecond retains 87.82% of its
development value. Under executable fixed-loop accounting it retains 92.10%.
Those diagnostics do not rescue the frozen gate, but they show that absolute
cross-dataset rate mixes two variables:

1. solver efficiency conditional on an opportunity; and
2. how much safe improvement the sampled blueprints contain.

Raw quality per millisecond remains the deployment objective and the right
paired comparison on identical cases. It is a poor standalone transfer gate
when the opportunity distribution changes substantially.

## Candidate-ready accounting correction

The matrix's candidate-ready curve is a counterfactual stop-at-that-phase
diagnostic. If a case already paid pricing to prove convergence, subtracting
that price does not describe the cost of executing the fixed maximum-update
loop. The matrix now labels this explicitly and retains `anytime_summary` as
the executable fixed-loop accounting. Both views fail transfer and dominate
CFR, so no verdict changes.

## Opposing evidence

- Exact headroom is unavailable online; normalized capture cannot itself be a
  deployable stopping signal.
- A fivefold Kuhn2 paired advantage may disappear when active constraints and
  pricing scenarios grow in multiplayer poker.
- One-pass safety still uses exact opponent separation, which will require
  conservative approximation at scale.
- Timings remain Python single-run measurements.
- The fresh iteration counts may simply produce unusually low improvement
  opportunity; a robust scheduler must detect that rather than rely on a
  favorable benchmark mix.

## Consequences

The next experiment is not another fixed update count. Use the exact objective
only as a hidden label to learn or design a target-free opportunity estimator
from early safe-generation traces: initial pricing reduced cost, restricted
master movement, constraint additions, incumbent gain, phase cost, reach, and
uncertainty. The scheduler should skip or stop low-headroom boundaries and
spend saved computation on higher-value current or speculative states.

Future preregistration must report two separate transfer gates:

- opportunity-normalized capture per millisecond; and
- paired absolute margin/ms against controls on identical cases.

Raw absolute margin/ms remains the final winner criterion. No neural,
multiplayer, or runtime-deployment claim advances yet.
