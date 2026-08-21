# ADR-0169: Preregister a fresh h32 exact-union value ledger

- Status: accepted preregistration
- Date: 2026-08-21
- Depends on: ADR-0111, ADR-0142 through ADR-0147, ADR-0154, ADR-0166,
  ADR-0168
- Config: `experiments/configs/h32-fresh-union-value-v1.json`

## Question

On previously unlabeled target beliefs, can a deterministic union of the six
structurally selected one-infoset edits recover positive exactly certified value
inside the same 15-second street ledger that made isolated atoms operational?

This is prospective target-level evidence. It may describe the two frozen
holdout targets but cannot estimate a board or target population, authorize
deployment, or validate a general scheduler policy.

## Fresh targets

Reuse two already-frozen source average-64 blueprints, but construct target
beliefs that have never had a policy step, strategy-quality evaluation, or
response certificate:

| Target | Board | Source family | Frozen target SHA-256 |
|---|---|---|---|
| `panel_1/balanced/local_blocker_seat4_x2` | `5c 8c 8d Jc As` | balanced | `08e0cc46cc259e29f138152d52f69f53e2fc5442487d29ee22007b9e615f1c36` |
| `panel_2/blocker_heavy/local_blocker_seat4_x2` | `2c 3s 5d Js Qc` | blocker-heavy | `cd2d7a0f10610ec0ac46999014475d3792f8eb4c345bd4c7eac42a446dbfa4d0` |

For seat 4, choose the hand by the existing label-free rule: maximum opponent
axis-card overlap, then maximum showdown strength, then smallest canonical
hand. Double only that hand's positive unary likelihood. The selected hands are
`3s Ad` on panel 1 and `5c 6d` on panel 2. Source, target, descriptor, hand-axis,
and source-checkpoint identities are frozen before any target label.

## Candidate generation and immutable anchor

Prepare topology, target belief, resident response context, target blueprint
quality, and warm-started solver off-clock. The episode anchor is always the
source average-64 blueprint evaluated on the new target belief. It never
reanchors.

Start the street clock immediately before one complete resident DCFR step.
Extract the step's current policy, enumerate its changed-infoset manifest, and
select the lexicographically first changed infoset owned by each acting seat.
Construct exactly these unions at scale 1.0:

1. `union_all_six`: seats `(0,1,2,3,4,5)`;
2. `union_prefix_four`: seats `(0,1,2,3)`; and
3. `union_prefix_two`: seats `(0,1)`.

This descending-cardinality order is structural and frozen before labels. Each
candidate must receive its own exact incremental response certificate against
the original blueprint. Atomic safety is never composed into union safety.

## Live 15-second ledger

Charge the warm step, manifest extraction, three union-policy constructions,
and every attempted union certificate to the street. Reserve 1,000 ms for
emission and decline to start another certificate when fewer than 1,250 ms
remain before the 14,000 ms cutoff. A certificate finishing after that cutoff
is recorded but is ineligible.

The shadow selector chooses maximum positive blueprint-minus-candidate
NashConv among complete, cutoff-usable unions, with frozen library order as the
tie-break. Regardless of that shadow result, emit the immutable blueprint.

Record certified value per certificate second and per elapsed street second.
Do not gate on how many unions are attempted, any stop reason, completion,
positive value, shadow selection, or whether the full ledger fits. Deadline
discipline and fail-closed eligibility are gates.

## Post-ledger rejection autopsy

Only after the emission point, exactly recertify all six singleton atoms against
the same anchor. These twelve labels across two targets are diagnostics and are
categorically ineligible for the live selector.

Report cap-bound versus objective-bound atoms, complete-atom value, the full
union's value fractions, whether a complete union contains a stopped
constituent, and the scalar interaction residual only when all seven required
policies have complete exact quality labels. A stopped singleton is assigned
zero certified value; its partial NashConv is never substituted for a complete
label.

## Outcome-neutral gates

Require two target rows, two warm steps, twelve selected atoms, six frozen
library rows, twelve post-ledger atomic labels, and two blueprint labels. Also
require every frozen source and target identity, immutable-anchor identity,
union-key identity, warm-start identity, clean committed execution, finite
accounting, exact deadline discipline, fail-closed shadow selection, post-ledger
ineligibility, blueprint emission, the frozen runtime, the 12 GB pool ceiling,
1 GB physical-free floor, and the broad 1,200-second audit ceiling.

The gate set deliberately excludes value and timing outcomes except broad
mechanism ceilings. A clean miss is informative and falls back to the
blueprint.

## Interpretation boundary

A positive complete union inside the cutoff would establish only that the
frozen end-to-end mechanism captured certified value on that target. Replication
across both targets would be stronger descriptive evidence, not a population
estimate. A stopped or late union would identify safety or wall clock as the
limiting layer. No outcome permits certificate composition, reanchoring, or
deployment.
