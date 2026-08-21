# ADR-0172: Fresh six-atom unions fit but do not recover material value

- Status: accepted corrected result
- Date: 2026-08-21
- Implements: ADR-0171 over the unchanged ADR-0169 matrix
- Clean successor preregistration commit: `a30b557`
- Result: `experiments/results/h32-fresh-union-value-v2.json`
- Result SHA-256: `ae3252327f2e1054c7dddb5c71f81bdf32e77ff2b300824e8b97e8d358d3a81e`

## Corrected mechanism result

Every corrected and unchanged gate passed. Both exact warm-start digests differed
from their source-policy digests, while the numerical distances were negligible:

- maximum action-probability error: `2.220446049250313e-16`;
- maximum mean information-set total variation: `3.2926493658661576e-17`.

Those are far below the inherited `1e-12` and `1e-13` gates and confirm
ADR-0170's diagnosis. The successor changed no target, candidate, solver step,
certificate, deadline, selector, or scientific outcome gate.

The two street ledgers, including the frozen one-second emission reserve, were
`13,608.86 ms` and `14,725.03 ms`. All six attempted union certificates finished
before the 14-second cutoff. Peak GPU-pool total was `8,214,049,792` bytes and
physical free memory remained at least `7,032,799,232` bytes. The immutable
blueprint was emitted on both targets.

## Panel 1 balanced

All three frozen unions completed and reduced raw NashConv:

| Candidate | Certificate | Street completion | Positive certified value |
|---|---:|---:|---:|
| full six atoms | 1,632.81 ms | 9,511.60 ms | `5.9949339e-8` |
| prefix four | 1,631.87 ms | 11,153.11 ms | `5.9916105e-8` |
| prefix two | 1,435.57 ms | 12,599.03 ms | `3.6357609e-8` |

The shadow selector chose the full-six union, but the emitted policy remained
the blueprint. Its value rate was `3.6715e-8` raw NashConv per certificate
second and `6.3028e-9` per elapsed street second.

All six post-ledger singleton atoms completed. Their certified values summed to
the full union value within numerical allowance (`1.000000071` of union value),
the best singleton supplied `0.60647` of union value, and the scalar six-way
interaction residual was only `4.25e-15`. On this target, the restricted
six-atom union is effectively additive.

## Panel 2 blocker-heavy

The full-six, prefix-four, and prefix-two unions all stopped at seat 3's
blueprint cap. Acting-seat 1's singleton stopped at the same cap; the other five
singletons completed with only tiny values. The fail-closed shadow selector and
emitted policy both remained the blueprint.

This gives a clean cap-bound diagnosis rather than opportunity exhaustion:
there were no objective-bound atomic stops, and removing later atoms did not
rescue the prefix containing acting-seat 1.

## Reproduction of the rejected run

All labels common to v1 and v2 reproduced within `1.77e-15` maximum complete
NashConv difference. The exact decision-signature diagnostic is false only
because the corrected run's faster second search left enough guarded time to
attempt `union_prefix_two`; v1 stopped before starting it. That additional union
hit the same seat-3 cap as the two larger unions. Timing-dependent attempt count
was deliberately not an outcome gate.

## Interpretation

The experiment rejects the simple repair suggested by the ADR-0168
retrospective: unioning one lexicographic atom per seat is not enough to recover
material bundle value. On one fresh target it is safe and nearly perfectly
additive but microscopic; on the other, one cap-bound atom poisons every frozen
union that contains it.

The comparison does not prove that broad coordination caused ADR-0168's
canonical bundle gains, because those were different targets and the analysis
was retrospective. It does narrow the next hypothesis: useful value, if it is
repeatable, likely lives in wider same-seat or topology-coherent changed sets,
not in arbitrary unions of six isolated infosets.

This remains a two-target holdout measurement, not a population estimate or a
deployment-quality claim. No certificate composes, no anchor moves, and no
shadow policy was emitted.

## Decision

Accept the corrected prospective measurement. Retain exact union
recertification and the 15-second fail-closed ledger, but do not invest further
in this six-singleton library or reorder it from these outcomes.

The next prospective candidate library should preserve more of the generated
policy's topology: freeze deterministic same-seat blocks and response-switch-
aware public-subtree blocks before new labels, measure changed-set width and
certificate cost, and compare certified value per street second. Every block
and union still requires its own blueprint-anchored exact recertification.
