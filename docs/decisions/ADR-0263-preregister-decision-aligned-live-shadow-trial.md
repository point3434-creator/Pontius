# ADR-0263: Preregister decision-aligned live-shadow trial

- Status: accepted preregistration before any decision-aligned warm step, candidate, or strategy label
- Date: 2026-08-22
- Follows: ADR-0262
- Config: `experiments/configs/h32-decision-aligned-live-shadow-v1.json`
- Config SHA-256: `b6ee5d33cc5ec8fe230f023cdbb1df0468f93beff96bacbcd90ff492b153caf7`
- Runner SHA-256: `6c3bf1ed050caf0a4f7b6e5249e2fe33b2ea3069a18f48cf0d05eeaaef627a77`
- Setup adapter SHA-256: `ad53a43e9d8db2fe5f45c159c3d7d2899c47abc51cbf234c4db7464578c08e89`
- Control SHA-256: `6ec0c34b65364674bf1f0f457bd9f694193fbce4b7fcee301854a3f6c82b8e69`

## Question

Does the sealed one-round convex half-retreat execute safely, within the full
15-second ledger, and with material certified value when its one-seat axis is
the player actually facing the current call/fold decision?

This is the first strategy-label run on the six ADR-0262 post-call identities.
It is a prospective shadow measurement with immutable-blueprint external
emission, not deployment authority.

## Frozen targets and setup

Use all six ADR-0262 targets in manifest order. No marginal TV, Latin value,
cap slack, response signature, cut count, timing, family, board, or position may
select, omit, or reorder a target. Every target observes the fixed public
history from ADR-0261: checks before one bettor, that bettor's bet, and the first
responder's call. The second responder is current, and three opponents remain
downstream.

The historical convex engine remains byte-for-byte unchanged. A separately
pinned setup adapter reconstructs the deeper posterior and continuation, checks
the manifest prefix, observed responder and action, current-player identity,
fold/call root, and remaining-responder count, then returns the same resident
objects the core consumes. Install that setup only for this bounded campaign
and restore the historical setup in a `finally` path. Controls require
restoration after success and failure and reject nested or preexisting setup
replacement. The result must prove the adapter was active during the campaign
and restored afterward.

## Frozen algorithm and safety authority

Inherit ADR-0257/0259 without numerical change:

- warm-start the restricted immutable blueprint and run exactly one resident
  DCFR warm step;
- extract six profile rows and five opponent fixed-response rows;
- solve the complete current-player behavioral master;
- run one exact all-seat separation oracle;
- classify already-resident response rows only under the `2e-11` identity and
  `1e-8` residual controls;
- add every genuinely new violating opponent response in one multi-cut round;
- resolve at most once, with no second separation round;
- retreat exactly halfway from blueprint to the bounded endpoint; and
- grant safety authority only to the independent exact all-seat oracle on that
  factor-`0.5` retreat.

The current-decision axis must have exactly one acting public node, 32 h32
information sets, and 64 policy variables. This count change follows from the
label-blind topology; every tolerance, guard, retreat factor, materiality floor,
and timing rule remains unchanged.

The raw guard is `1e-10 × layout.game.payoff_span = 3e-9`. Cap allowance stays
`2e-11`, epigraph separation allowance `1e-9`, quality allowance `1e-10`, and
the required interior slack remains
`(1 - 0.5) × 3e-9 - 2e-11 = 1.48e-9`.

## Barrier, ledger, and no-op path

Construct and freeze all six algorithmic candidates before opening any final
retreat label. After that campaign-wide barrier, reconstruct one pinned context
at a time and run exactly one final retreat oracle per target. Reconstruction
is measured and identity-gated but excluded from the live ledger because the
live path retains its resident context.

Charge warm step, initial rows, all master solves, first separation oracle, cut
extraction, at least 50 ms for retreat/envelope work, the final exact oracle,
and 1,000 ms emission reserve. Require both measured live time and the unchanged
conservative floor `13,967.615699994712 ms` to fit 15,000 ms. Preserve the
12-GB GPU-pool ceiling and 1-GB physical-free floor.

Every candidate remains shadow-only. The actual externally emitted policy is
the immutable restricted blueprint on all six targets, whether the candidate
passes or abstains.

## Process result versus value-transfer result

Keep two questions separate.

The process passes only if every provenance, identity, adapter, topology,
numerical, oracle, cut-accounting, memory, deadline, barrier, reconstruction,
certificate, abstention, emission, label-count, finite, and null-claim gate
passes. Negative strategy value does not convert a valid execution into a
process failure.

Call material value transferred only under the unchanged breadth threshold:
at least four of six retreats are shadow-accepted with exact positive value
strictly above `0.001`, both range families are represented, and every schedule
fits. A transfer pass authorizes only a separate post-fold preregistration. A
clean process pass below that threshold is accepted as an execution but rejects
the transfer claim. A process failure rejects the run.

## Claims boundary

The targets have fresh posterior identities but retained boards and source
blueprints; every observed response is a call. No fresh regret-vertex fallback
is evaluated. The bounded endpoint is not claimed globally optimal, and only
the exact half-retreat oracle is authoritative. No candidate is externally
emitted. Make no fallback-dominance, IID population, deployment, composition,
cross-street, exploitation, multiplayer-global-safety, or poker-strength claim.

## Decision

Commit the adapter, runner, config, controls, this ADR, roadmap, and generated
status from a clean tree. Run the six-target GPU campaign exactly once. Do not
pilot a target, inspect a partial label, add a cut round, change the retreat, or
substitute a history after execution begins.
