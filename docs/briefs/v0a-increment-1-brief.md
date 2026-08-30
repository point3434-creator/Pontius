# Task v0a-1 brief — Blueprint-only complete hand

Governed by docs/workflow.md (Stage 0) and ADR-0484. This brief bounds the
work and confers no experiment authority: increment one begins only with its
own preregistration and lifecycle under ADR-0482. Revised 2026-08-30 after
the controller's Stage-0 review, addressing four findings: the boundary-gate
classification gap, the blueprint outcome split, the reserve/emission
semantics, and the frozen-contract requirements below.

Tier: C — the runtime realizes ADR-0307/0308 action-clock semantics and
emits decision records that later acceptance evidence will consume.

Base: current master HEAD at lane opening (recorded in the preregistration).
Worktree: a fresh linked worktree on branch `v0a/increment-1`; the primary
checkout is never the execution host.

## Scope

May change:

- new structured subpackage `src/pontius/v0a/` (the flat root stays
  read-only sediment; `pontius/evidence/` is the precedent) holding the
  additive hand runtime, decision-record writer, and trace emission;
- new test file `tests/test_v0a_hand_replay.py`;
- the generator's `STABILIZATION_TEST_FILES` declaration plus regenerated
  `tests/test-inventory.json` / `tests/test-profiles.toml` and the honest
  census-expectation refresh the admission machinery demands;
- a narrowly scoped v0a origin classification and import policy in the
  stabilization boundary machinery, with its own boundary tests — the
  boundary gate currently rejects any new source module outside
  `pontius.evidence`, and the legacy dependency baseline is preserved
  byte-for-byte, never regenerated to absorb the new package;
- the CI workflow, adding the new suite's clone-safe subset as a gate.

Must not change: any sealed or retained byte; `reference_hand_replay.py`
(the historical loop remains a preserved reproduction oracle);
`legal_decision_spine`, `action_clock`, `preparation_bank`,
`no_limit_betting`, `holdem_cards`, `immutable_blueprint` (the runtime is
additive around them — consumed, not modified);
`docs/architecture/dependency-baseline.toml` (the legacy lock is preserved
byte-for-byte); generated governance files except through the authorized
regeneration above.

## Acceptance criteria

1. One complete six-player hand replays end to end from a sealed,
   seed-bound deal schedule: preflop through settlement, with exact
   integer-chip payouts independently recomputed against the
   `no_limit_betting` settlement rules, including at least one side-pot and
   one all-in configuration across the focused checks.
2. Every controlled action receives a fresh continuous 15,000 ms response
   wall that starts at its external event boundary — including subsequent
   state-transition work and blueprint lookup. Decision work completes by
   the 14,000 ms work cutoff; the observable emission event — the exact
   point the action leaves the runtime, defined by the preregistration —
   occurs by the 15,000 ms response deadline. Wall accounting comes from
   `ActionClockLedger`, not ad hoc timers, and no adapter work (trace
   writing included) may delay delivery outside the measured interval. A
   fallback emitted after the deadline is recorded as a deadline violation,
   never concealed by its own success.
3. The input boundary holds: the runtime consumes public events and the
   controlled seat's private cards only, and a test proves the deal
   oracle's complete deal is unreachable from every policy-selection path.
4. Action selection is immutable-blueprint lookup with the contract's
   exact outcome split: a missing match yields the blueprint's legal
   passive default (check, else call, else fold), while an illegal matching
   entry or an invalid decision context yields an explicit typed failure
   with no action emitted from that input — rejection never silently
   becomes passivity. "Stale" is not a third category: an entry keyed to
   another state is simply not a match. Every emitted action is legal in
   the exact betting state, and each outcome class carries its own
   acceptance check.
5. Every controlled action emits a schema-v1 decision record — state
   identity, policy identity, timing (wall start, emission, elapsed),
   selection reason, preparation use, failure reason — with preparation use
   recording honest absence (`producer_absent`; no fabricated producers).
6. Focused fail-closed checks pass: repeated actions on one street, side
   pots, all-ins, hidden-card isolation, malformed and out-of-order events.
7. The first working hand emits a replayable LF-canonical trace: re-running
   the sealed schedule reproduces the same decisions and settlement
   exactly, while naturally varying timing measurements are checked
   structurally (present, typed, within their walls), never byte-wise.
8. CPU-only: importing and running the increment requires no GPU or
   optional dependency; suites pass from disposable snapshots on genuine
   CPython 3.11 and 3.14.
9. The clone-safe test subset joins the CI wall and the wall stays green.
10. The stabilization boundary gate passes with the v0a package classified
    under its narrow policy, and the legacy dependency baseline remains
    byte-for-byte unchanged.

## Seam inventory

Action-clock/event-boundary semantics (ADR-0307/0308); settlement against
the `no_limit_betting` kernel; blueprint digest binding; the deal-oracle
isolation boundary; monotonic time sourcing; trace/decision-record file
writes (bounded, LF, no governance writer involvement); new-test admission
through the inventory generator (declaration, regeneration, census refresh);
CI workflow. No subprocess, no GPU, no network.

## Contracts the preregistration must freeze

Schema v1 above is a field outline, not yet a replay contract. The
preregistration freezes, before any implementation source:

- public event types and their ordering, and exactly how showdown and
  settlement information crosses the dealer boundary without exposing the
  complete deal to policy paths;
- hand and action identifiers, the selected action including its exact
  raise-to amount, and the source/policy/state bindings of every record;
- timing units and derivation: the authoritative clock's public snapshot
  exposes elapsed durations, not absolute timestamps, so the
  preregistration settles how records obtain their timing values from the
  ledger without inventing a second clock;
- typed failure outcomes, including the behavior when trace writing fails
  after an action has already been emitted — the delivered action stands,
  and the write failure surfaces as its own typed, recorded outcome;
- the round-trip replay check separating deterministic decisions and
  settlement (compared exactly) from naturally varying timing measurements
  (compared structurally).

## Size budget

Expected 2,500–4,000 new lines including tests. At or above ~3,000 changed
lines the candidate is reviewed as named slices from round one (runtime
slice, test slice) per the workflow's proactive-slicing rule.

## Rehearsal coverage and reserved identities

The preregistration carries rehearsal runs of the complete lifecycle over a
synthetic two-hand schedule under rehearsal-scoped identities
(`pontius-v0a-hand-replay-v1-rehearsal-*`), with no evidentiary standing.
Production lifecycle identities are reserved as
`pontius-v0a-hand-replay-v1`; rehearsal and production namespaces can never
collide. All frozen walls and budgets in the preregistration must carry
rehearsal measurements as provenance (ADR-0482).

## Lane breakers (provisional; binding numbers set at preregistration)

Two consecutive owner deaths on infrastructure, lifecycle, or authorization
grounds trigger a mandatory harness stand-down. Lane budget: eight
lifecycles or six weeks, whichever comes first, forces a lane checkpoint —
provisional per the controller's ruling, finalized from rehearsal
provenance.

## Forbidden claims

No poker-strength, decision-quality, or latency-distribution claim; no
"15-second action result" (that is increment three's campaign question); no
h32, resolver, GPU, or trained-policy involvement; no producer identity or
preparation-credit claim beyond honest absence; and neither this brief nor
the roadmap confers experiment authority.

## Test plan

RED targets before implementation: clock start at the event boundary (a
late-started clock must be detectable), the blueprint outcome split (a
missing match must go passive; an illegal matching entry must fail with no
emission — each its own RED), hidden-card isolation (a policy path reaching
the full deal must fail the test), malformed/out-of-order events (fail
closed), settlement mismatch against an independent recomputation, and
delay injection at the new adapter boundaries — not only inside the
existing ledger — proving that post-cutoff work and post-deadline emissions
surface as recorded violations rather than escaping the reported interval.
Focused GREEN in the new suite; full-suite regression for the
admission-touched inventory machinery; boundary-gate GREEN with the v0a
classification; disposable-snapshot GREEN on CPython 3.11 and 3.14; CI wall
green with the new gate.
