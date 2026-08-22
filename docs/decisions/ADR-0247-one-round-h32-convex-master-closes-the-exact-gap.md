# ADR-0247: One-round h32 convex master closes the exact gap

- Status: accepted optimizer result; quality experiment authorization granted
- Date: 2026-08-22
- Implements: ADR-0246
- Clean preregistration commit: `a5b1e98d7593a7f443ba722136d5743d8f882b4f`
- Result: `experiments/results/h32-one-round-convex-master-v1.json`
- Result SHA-256: `6e09c69c5447b3313ae3db36f96eb9af81b779dd3e60b4851f7a6e8a3172d8ab`

## Result

The frozen h32 prototype passed every recorded provenance, topology, row-
identity, sparse-master, exact-oracle, memory, immutable-emission, and process
gate. The initial source-response master did not solve the complete problem:
its candidate violated two opponent epigraphs and the envelope. The one allowed
multi-cut round added the exact response rows for seats 4 and 5, resolved once,
and then closed the complete one-seat epigraph.

| Witness | Initial master | After one multi-cut round |
|---|---:|---:|
| Restricted lower bound `L` | `0.03606141790374194` | `0.03704032080499536` |
| Exact candidate objective | `0.03699431926539898` | `0.03704032080499919` |
| Maximum epigraph violation | `7.27031876067357e-4` | `2.42340869593960e-15` |
| Maximum cap violation | `8.30012321304790e-5` | `1.02522157430229e-15` |
| Exact cap feasible | no | yes |

The final cap-feasible candidate became the independently evaluated incumbent
`U`. The verified timeout gap is
`U - L = 3.83720832886070e-15`, far below the frozen `1e-8` ceiling. The
restricted lower bound increased monotonically. The exact row counts by seat
are `[1, 1, 1, 1, 2, 2]`; no approximate row was removed.

This is positive identification for the optimizer: on this frozen one-seat
h32 program, the source row library is insufficient, exactly two new response
facets are needed, and one multi-cut round is sufficient. It is not a claim
that the resulting policy improves poker strength.

## Numerical and topology controls

The post-bet continuation passed the compiled path-single-visit predicate and
exposed the frozen 16 public nodes, 512 information sets, 1,024 behavioral
policy variables, and six epigraph variables. The raw guard was the
game-derived `3e-9`.

Both sparse masters passed independently checked primal and dual conditions.
The maximum master primal residual was `7.47e-16`; the maximum dual residual
family was `6.94e-18`. HiGHS needed three and four dual-simplex iterations,
with solve times `6.83 ms` and `6.88 ms`. Candidate reconstruction required no
projection. Maximum source-row, generated-cut-row, and candidate profile-
equivalence errors were respectively `4.49e-16`, `2.43e-15`, and `8.88e-15`,
all far below their frozen `2e-11` ceilings.

The two generated opponent libraries remain well separated: their effective
condition numbers are `2.69` and `4.61`, with minimum normalized row
separations `0.70` and `0.42`. Conditioning is diagnostic only; both exact rows
remain in each library.

## Cap-tolerance audit correction

The frozen runner contained one threshold-plumbing defect. Its
`cap_feasible` Boolean reused the `1e-9` epigraph separation tolerance instead
of the distinct preregistered `2e-11` envelope numerical allowance. This is the
same semantic-knob conflation class that the project treats as unsafe even
when the current branch is unaffected.

The result does not require a rerun or a looser claim. The exact final maximum
cap violation was serialized before inspection as
`1.02522157430229e-15`. The pinned result control independently compares that
number with the preregistered `2e-11` envelope allowance; it passes by a factor
of about `19,508`. The initial candidate fails under either threshold, while
the final candidate passes under both, so no branch, row, bound, timing, or
promotion decision changes. Future runners must pass separate cap and
epigraph allowances explicitly; this one-off frozen runner is not reused as an
emission authority.

## Boundary and retreat interpretation

The final optimizer is boundary-seeking as expected: its maximum exact cap
violation is a positive `1.03e-15` reassociation residual and seats 2 and 4 are
reported active at the runner's diagnostic tolerance. This supports the
preregistered engineering rule that a raw LP endpoint must not be emitted.

The factor-`0.5` retreat was constructed only as a diagnostic and was neither
certified nor emitted. Its simplex-mass error was `2.22e-16`. Accounting
conservatively for the exact endpoint residual still restores more than
`1.49999948e-9` of guard slack by convexity. A later quality trial must
independently certify the retreated policy and may not treat this theoretical
diagnostic as emission authority.

## Wall clock and memory

The measured resident live ledger was `8,718.73 ms`, leaving `6,281.27 ms` of
the hard 15-second street boundary. Its principal measured components were:

- one warm step: `1,473.06 ms`;
- eleven source-row passes: `2,640.05 ms`;
- both sparse master solves together: `13.71 ms`;
- two all-seat exact response oracles: `3,185.16 ms`;
- two generated response rows: `356.75 ms`; and
- the frozen `50 ms` retreat/envelope plus `1,000 ms` emission reserves.

The corrected conservative ledger, including the initial-master reserve
omitted by ADR-0244, was `13,967.62 ms` and also passed. Thus this result does
not depend on optimistic measured timing.

The CuPy pool again peaked at `5,661,330,944` bytes and physical free memory
never fell below `9,629,073,408` bytes. Memory remains nonbinding for this
one-seat scope.

## Decision

Accept the h32 one-round optimizer result and the convex/cutting-plane path for
one-seat continuation work. The result answers the former idea's feasibility
question positively: full-axis direction generation can cross response kinks,
recover the exact one-seat optimum, and close a verified bound inside the hard
street ledger on the frozen target.

Authorize only a new clean preregistration for strategy quality. That trial
should compare the independently certified factor-`0.5` retreat against the
immutable blueprint and the accepted live fallback under the complete street
ledger. It must use distinct cap and epigraph allowances, retain the exact
certificate as sole emission authority, and preserve the no-composition and
single-seat boundaries. No candidate from this optimizer artifact is emitted.

## Claims boundary

This result establishes one-target optimizer convergence, exact row
generation, verified bounds, and live engineering feasibility. It makes no
strategy-quality, population, general-target, multi-seat, multiplayer-safe,
deployment, composition, cross-street, or broad poker-strength claim.
