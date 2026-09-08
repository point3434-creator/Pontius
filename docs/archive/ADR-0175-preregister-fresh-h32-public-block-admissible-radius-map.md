# ADR-0175: Preregister a fresh h32 public-block admissible-radius map

- Status: accepted preregistration
- Date: 2026-08-21
- Depends on: ADR-0148, ADR-0154, ADR-0173, ADR-0174
- Config: `experiments/configs/h32-fresh-public-block-radius-v1.json`

## Question

ADR-0174 found that scale-1 public-node blocks for acting seats 1 and 2 were
already cap-bound, without a best-response action switch. On new target
beliefs, is there a nonzero geometric scale window in which either unsafe
direction, or their exact union, completes the immutable-blueprint envelope?
If so, what certified value and exact recertification rate occur in that
window?

This is an off-clock mechanism audit. It maps a radius before designing a live
15-second scheduler; it does not spend 204 certificates inside a street.

## Fresh targets

Use two source average-64 blueprints and previously unlabeled seat-0 blocker
shifts:

| Target | Board | Frozen target SHA-256 |
|---|---|---|
| `panel_2/balanced/local_blocker_seat0_x2` | `2c 3s 5d Js Qc` | `401170b656dd96b831cfac4bc1b9995d41c055e8c9d4aa590ba80dbcf98754c9` |
| `panel_3/blocker_heavy/local_blocker_seat0_x2` | `4h 7h 9s Jd Kc` | `8a09af83e457b77bd6639e4899d05e3c627020ccbe7791af41ebc58cef027a78` |

Select the seat-0 hand with the existing label-free maximum-overlap, then
strength, then canonical-hand rule, and double only that hand's positive unary
likelihood. The selected hands are `7s 8c` and `2s 3c`. Source, target,
descriptor, hand-axis, and checkpoint identities are frozen before any target
policy step or quality label.

## Frozen directions and grid

Run one resident DCFR step from the numerically identical warm blueprint.
Construct the six public-node blocks exactly as ADR-0173: the
lexicographically first changed infoset per acting seat is a label-free anchor,
and its block contains every changed hand at the same acting seat and exact
public history.

Measure only these directions, in order:

1. acting-seat 1's block;
2. acting-seat 2's block; and
3. the exact union of those two blocks.

For each direction, use `geometric_halving_scales(numerical_floor=1e-10)`:
34 descending scales from 1 through `2^-33`. At every scale, interpolate from
the same generated candidate and independently recertify against the same
immutable target blueprint. Never reanchor, chain, infer union safety from
constituents, or infer one scale's safety from another.

This produces 204 exact scale labels: two targets, three directions, and 34
scales.

## Measurements

At each scale record the verifier classification (`blueprint_cap`,
`objective_lower_bound`, or `complete`), stop seat, cap or objective excess,
response-action flips, construction time, exact certificate time, GPU memory,
and changed-infoset width. For a complete row also record minimum cap margin,
raw and normalized NashConv reduction, positive certified value, and value per
certificate second.

Per direction report the largest and smallest complete grid scales, complete
count, binding-count split, stop-sequence transitions, and the scale with
maximum positive certified value using larger-scale order as the tie-break.
These are descriptive measurements, not acceptance gates. Do not assume the
trace is monotone.

## Outcome-neutral gates

Require the frozen counts, clean committed execution, accepted parents,
source/target/blueprint identities, numerical warm identity, six coherent
blocks per target, exact direction reconstruction, exact shared grid,
immutable anchors, independent certificates, blueprint emission, finite
accounting, a 60-second ceiling per search step and certificate, the 12 GB GPU
pool ceiling, 1 GB physical-free floor, and a broad 1,200-second audit ceiling.

Do not gate on whether any scale completes, the largest or smallest admissible
scale, binding constraint, response seat, value, rate, trace monotonicity, or
whether any hypothetical live sequence fits 15 seconds.

## Interpretation boundary

A complete scale establishes only an exact one-shot certificate for its frozen
target, direction, scale, anchor, and epoch. It does not authorize deployment
or composition. Two constructed targets are not a population, and this audit
makes no strategy-quality claim. The immutable blueprint is the only emitted
policy.

If a stable useful window exists, a later holdout may test one deterministic
scale-selection rule inside the 15-second street ledger. If no grid scale
completes, or completed value is negligible, stop scaling this generator and
redirect work to opportunity selection or a different direction family.
