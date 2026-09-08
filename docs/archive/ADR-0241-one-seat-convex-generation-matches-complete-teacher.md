# ADR-0241: One-seat convex generation matches complete teacher

- Status: accepted finite control; h4 cut-extraction differential authorized
- Date: 2026-08-22
- Implements: ADR-0240
- Clean preregistration commit: `2aa3cb97dc776ac456b39fc9fa752783b947f343`
- Result: `experiments/results/one-seat-convex-keystone-v1.json`
- Result SHA-256: `c9734813feddee76ddcbac7917544c7bf869dfbc76b8365233f04065985155fb`

## Result

The one-seat sequence-form row generator passed every frozen gate on its first
clean invocation. Both acting-seat programs converged and matched their
independently enumerated complete mixed-normal-form teachers.

| Acting seat | Iterations | Generated target-row counts | Master `L` | Certified `U` | Reported `U - L` | Teacher error |
|---:|---:|---:|---:|---:|---:|---:|
| 0 | 5 | `[1, 5]` | `0.00489742898189629` | `0.00489742898189660` | `3.12e-16` | `1.30e-17` |
| 1 | 3 | `[3, 1]` | `0.00364642884444329` | `0.00364642884444250` | `0` | `3.47e-17` |

The acting seat's invariant gain needs one row. Thus seat 0 used five of the
opponent's 64 pure-response rows; seat 1 used three of the opponent's 64 rows.
The complete teacher enumerated all 64 acting plans and all 64 opponent plans
for each trial.

Seat 1's printed restricted-master lower bound is `7.9e-16` above the certified
incumbent due to Float64 simplex/evaluation reassociation. This is eight orders
of magnitude below the preregistered `1e-9` identity ceiling and was handled by
the frozen rule: reject a material negative gap, otherwise clamp `U - L` to
zero. The discrepancy is disclosed rather than treated as exact ordering.

Maximum sequence-form realization-equivalence error was `1.81e-16`. Maximum
interior-retreat Jensen error was `1.06e-16`. The independently evaluated
incumbents matched their reported upper bounds exactly. The deliberately
truncated mutation arm did not converge, retained a cap-feasible independently
evaluated incumbent, and reported the correct bound orientation. The
three-player mutation arm added both violated opponent rows in one iteration.

The repeated-actor topology control rejected the behavioral-coordinate
shortcut as required. The sequence-form solver nevertheless matched the full
teacher, which is the intended discrimination between the general formulation
and the sufficient shortcut.

## Conditioning and cost

No exact response signature recurred as an unresolved violation, and no
numerically similar row was deleted. The largest reported effective row
condition number was `139.13`; the corresponding minimum normalized separation
was `0.64`. These are control diagnostics, not h4 or h32 conditioning evidence.

The complete artifact took `1.5374 s`. Generated solves took `16.09 ms` and
`9.67 ms`; the exhaustive teachers took `665.15 ms` and `667.60 ms`. These
small-game timings do not price the open-axis contraction, exact response
oracle, or final certificate on continuation topology.

## Interpretation

The finite theorem and implementation survive their keystone:

1. fixed-response rows are exact in sequence-form coordinates even when the
   acting seat appears twice on a path;
2. all-opponent epigraph separation reaches the complete one-seat optimum
   without enumerating every row;
3. the restricted master supplies a usable lower bound while an independently
   certified feasible policy supplies the upper bound; and
4. sequence-form retreat restores interior cap slack without cell tracking.

This closes the mathematical and small-control question. It does not establish
that the method is practical on the continuation tree. The remaining unknown
is now correctly isolated: extracting a fixed response tape's full open acting
axis, with external posterior hand keys, at h4 and then h32 scale.

## Decision

Accept the ADR-0240 keystone and authorize one label-free h4 open-axis cut-
extraction differential. Compare every extracted coefficient against direct
exact fixed-tape perturbation controls, include repeated-actor sequence-form
and post-bet behavioral-shortcut cases, report coefficient construction cost,
conditioning, persistent bytes, and exact response-oracle cost, and preserve
exact-response-signature-only deduplication.

Only an h4 identity pass may reopen the corrected ADR-0238 external-axis path
as an h32 row extractor. h32 cut count, extraction latency, master latency,
independent final-certificate latency, memory headroom, and the 15-second ledger
remain unmeasured.

## Claims boundary

This is a finite algebra and optimizer control. The observed reduction in
small-game NashConv is not accepted as a strategy-quality result. No
multiplayer-safe, deployment, composition, cross-street, h4, h32, population,
or broad poker-strength claim is made.
