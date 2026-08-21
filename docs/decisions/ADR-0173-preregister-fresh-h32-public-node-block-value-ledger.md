# ADR-0173: Preregister a fresh h32 public-node block value ledger

- Status: accepted preregistration
- Date: 2026-08-21
- Depends on: ADR-0148, ADR-0154, ADR-0168, ADR-0172
- Config: `experiments/configs/h32-fresh-public-block-value-v1.json`

## Question

ADR-0172 showed that unioning one changed hand/infoset per seat is either
microscopic and additive or cap-bound. On new target beliefs, does preserving a
complete changed hand-axis slice at one public decision node recover materially
more exactly certified value, and can that wider unit still fit the 15-second
street boundary?

## Fresh targets

Use two source average-64 blueprints but previously unlabeled seat-2 blocker
shifts:

| Target | Board | Frozen target SHA-256 |
|---|---|---|
| `panel_3/balanced/local_blocker_seat2_x2` | `4h 7h 9s Jd Kc` | `1014d3b5e6a6aaebce7189788612c94dafe8f2b826da76e2ed568b1abc2bdef5` |
| `panel_1/blocker_heavy/local_blocker_seat2_x2` | `5c 8c 8d Jc As` | `c9e24a106f970d3732b73c3a3325fd9b7f0fdbb0303d9621a5f1d0473301e718` |

Select the seat-2 hand by the existing label-free maximum-overlap, then
strength, then canonical-hand rule and double only that hand's positive unary
likelihood. The selected hands are `5c Ac` and `5s 8s`. Source, target,
descriptor, hand-axis, and checkpoint identities are frozen before any target
policy step or quality label.

## Topology-coherent blocks

Run one resident DCFR step from the numerically identical warm blueprint. For
each acting seat, select the lexicographically first changed infoset exactly as
ADR-0159 did. Use that atom only as a label-independent public-node anchor.

A seat's public-node block contains every changed infoset with:

1. the same acting seat as its anchor; and
2. the exact same public history as its anchor.

Thus the candidate retains the generated policy's changes across the whole
changed hand-axis slice at that public node. Membership does not depend on
probability magnitude, quality, response action, cap slack, or any ADR-0172
outcome. Require six nonempty, disjoint, coordinate-coherent blocks but do not
gate on their observed widths.

Construct these scale-1.0 unions in frozen order:

1. `public_blocks_all_six`: blocks for seats `(0,1,2,3,4,5)`;
2. `public_blocks_prefix_four`: blocks for `(0,1,2,3)`; and
3. `public_blocks_prefix_two`: blocks for `(0,1)`.

Each block union receives its own exact certificate against the immutable
target blueprint. Block safety is never composed into union safety.

## Street ledger and diagnostics

Charge one full warm step, changed-set/anchor/block extraction, all three union
policy constructions, and attempted union certificates to the street. Retain
the 15,000 ms decision boundary, 1,000 ms emission reserve, 1,250 ms start
guard, ascending response-seat order, and fixed blueprint envelope.

The shadow selector chooses maximum positive certified value among complete
unions finishing by the 14-second cutoff, with frozen order as tie-break. Emit
the immutable blueprint regardless.

After the emission point, exactly recertify each of the six constituent blocks
alone. These twelve labels are ineligible for the live selector. Record binding
constraint, block width, certified value, best/sum block fractions, complete
union with stopped constituent, and a six-way scalar interaction residual only
when all required labels are complete.

## Corrected warm-start control

Inherit ADR-0148 and ADR-0171 from the outset. Gate maximum warm-start
probability error at `1e-12` and mean information-set total variation at
`1e-13`. Do not repeat the invalid exact-digest gate.

## Outcome-neutral gates

Require two target rows, two search steps, twelve coherent blocks, six frozen
union-library rows, twelve post-ledger block labels, and two blueprint labels.
Also require all source/target/blueprint identities, numerical warm identity,
exact union-key reconstruction, immutable anchors, clean committed execution,
deadline discipline, fail-closed selection, post-ledger ineligibility,
blueprint emission, finite accounting, the 12 GB pool ceiling, 1 GB physical-
free floor, and the broad 1,200-second audit ceiling.

Do not gate on block width, attempt count, certificate completion, stop reason,
value, interaction, shadow decision, or whether a widened synchronous
certificate overruns the emission boundary. A late result is ineligible and is
evidence that this acceptance unit is incompatible with the current scheduler.

## Interpretation boundary

A fitting positive block union would establish value capture only on its frozen
target. A late union would identify block width as a wall-clock failure. A cap-
bound union with admissible constituent blocks would support acceptance-unit
interaction; a matching stopped constituent would localize the unsafe block.

Two constructed targets are not a population. No result authorizes deployment,
reanchoring, certificate composition, or selection from the post-ledger labels.
