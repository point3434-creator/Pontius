# ADR-0261: Preregister decision-aligned post-call posterior panel

- Status: accepted label-blind preregistration before any decision-aligned strategy label
- Date: 2026-08-22
- Follows: ADR-0260
- Config: `experiments/configs/h32-decision-aligned-posterior-manifest-v1.json`
- Config SHA-256: `e0870ac0da41222532b661f1b8f83c213082c24f858ab87750dfc91d25860eab`
- Runner SHA-256: `f5e5cd2c028811cb09dc9fd75fd03f8077b65a8c35e0c2ecf93ff0876f8d274e`
- Control SHA-256: `a5f739803440bbcdbc9dc88a3c862d3762d7055b8f4b26284fa5130966456e40`

## Question

Can six genuinely new post-call posterior identities be frozen so that the
one-seat convex axis belongs to the player currently facing a decision, while
retaining nontrivial downstream opponent response geometry?

This stage constructs beliefs, public continuations, and behavioral-axis
shapes only. It runs no warm step, convex master, exact response oracle,
certificate, quality evaluation, or strategy label.

## Why the Latin scope is not the live scope

Latin-E/F optimized the last responder after observing only checks and a bet.
That choice maximized the open-axis width: the last responder can be reached
through 16 public histories. It was a strong direction-diversity test, but the
last responder was not yet the player on the clock at the continuation root.

Waiting until the last responder actually becomes current would remove every
downstream opponent decision and make the local safety geometry nearly
terminal. Freeze the middle point instead: after the first responder calls,
the second responder is current and three opponents still act after it. The
acting player has one public node, 32 h32 information sets, and 64 behavioral
variables. That is the complete current-decision axis, not an artificial
truncation.

## Frozen panel

Reuse all six retained source boards and average-64 blueprints in their existing
manifest order. For source index and observed bettor `b = 0,...,5`, condition
on every check before `b`, the bet by `b`, and exactly one call by
`(b + 1) mod 6`. Declare `(b + 2) mod 6` as the acting player. This balances
source, bettor, observed responder, and current acting player exactly once.

The all-call rule is structural and fixed before any new posterior is built. It
is not chosen from marginal TV, Latin value, cap slack, cut count, timing, or
any opportunity label. Post-fold histories remain outside this first
integration panel.

Construct every posterior by multiplying the immutable source blueprint's
exact likelihood for every observed public action in order. Preserve the h32
hand axes. Each target ID, belief digest, and descriptor digest must be absent
from clean parent commit `f7cce5450e1b9d55b145d738cd6032820fe89abc`.

## Label-blind topology gates

For every target, compile the actual continuation and require:

- the public prefix is legal and ends at a decision node;
- the continuation root current player is the declared acting player;
- the root actions are exactly fold/call;
- four responders remain, comprising the current actor and three downstream
  opponents;
- the acting axis has exactly one public node, 32 information sets, and 64
  variables;
- no continuation root-to-terminal path visits the same seat twice; and
- the continuation topology is deal-invariant.

Also require clean Git, both pinned parent artifacts passed, ADR-0260's live-
shadow authorization decision, all checkpoint and blueprint identities,
unique and fresh target identities, nonzero marginal shift for the bettor,
observed responder, and acting player, exact hand axes, marginal split error at
most `1e-12`, finite output, CPU wall time below 600 seconds, zero strategy
labels, and null population claim.

## Decision rule

If every identity, balance, posterior, and topology gate passes, authorize only
a separate prospective live-shadow strategy preregistration. That later trial
must preserve the factor-`0.5` retreat, exact final certificate, `1.48e-9`
interior floor, complete 15-second ledger, campaign-wide candidate barrier,
and immediate immutable-blueprint fallback from ADR-0260.

If any gate fails, reject this panel before GPU strategy work. Do not substitute
a different observed action, source, bettor, or actor after seeing the failure.

## Claims boundary

The source boards and blueprints are retained; freshness applies to the deeper
post-call posterior identities. The six fixed contexts are not an IID sample.
This preregistration makes no strategy-quality, fallback-dominance, population,
deployment, composition, cross-street, global-optimality, or poker-strength
claim.

## Decision

Commit the runner, config, control, this ADR, roadmap, and generated status from
one clean tree. Invoke the CPU-only manifest exactly once. Do not construct a
decision-aligned convex candidate unless the sealed manifest passes.
