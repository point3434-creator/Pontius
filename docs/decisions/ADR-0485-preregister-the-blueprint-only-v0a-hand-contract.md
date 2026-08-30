# ADR-0485: Preregister the blueprint-only v0a hand contract

- Status: accepted prospective contract preregistration and explicit bootstrap-sequencing clarification; only the additive CPU blueprint-hand source contract is opened, an outer ActionClockLedger measures through offline-host delivery without altering the sealed V2 spine, operating budgets and an authoritative replay population remain unadmitted until a separate measured closure, and no source seal, rehearsal, owner invocation, integration result, timing result, or strategy result is asserted
- Date: 2026-08-30
- Follows: ADR-0484
- Base-Commit: ca0b2e41bbf5d9fc1649de20379299331de6591a
- Brief-Blob: 8ef19c830eb929037c9cdd99e52cb0f0b56ddb28 at docs/briefs/v0a-increment-1-brief.md
- Legacy-Baseline-Blob: 5fe6ee47f3380b65887b528efef05b72c8e6ac0a at docs/architecture/dependency-baseline.toml
- Invocation-Authority: none; reserved identities must remain absent on disk
- Front-Door-Kind: controller-v1
- Front-Door-Research: ADR-0280
- Front-Door-Process: ADR-0485
- Front-Door-Contract: ADR-0307
- Front-Door-Revoked: ADR-0281, ADR-0468, ADR-0472, ADR-0475
- Front-Door-Active-Next: Build and review only the additive blueprint-only v0a increment-one source against ADR-0485 and the ADR-0484 brief, then source-seal it and rehearse under separate non-evidentiary identities; freeze measured operating budgets and the authoritative replay schedule in a separate append-only closure before requesting any one-shot invocation authority. Preserve the exact legal kernels, historical replay, and legacy dependency baseline. H32 and producer instrumentation remain increment two, the campaign remains increment three, and the compiled lane remains parked under ADR-0483. Separately continue evidence Tasks 4-9 before orchestration Tasks 3-10, then 11b and 12, with their capability approvals intact
- Front-Door-Blockers: v0a source, source seal, rehearsal, measured operating-budget closure, authoritative replay population, and invocation authorization do not exist; v7 is permanently consumed and the compiled calibration is incomplete and parked; no production source-local base producer, refresh cadence, exponent admission, or width bound exists; no selected topology, complete reduced compiled-calibration result, population-25 result, actual-45 numerical result, global resolver-certificate integration, complete resolver iteration, known certificate count per action, or 15-second action result exists; no repeated-actor multiway existence result, off-tree opponent-action result, cross-street belief and certificate handoff, certified full-width river strategy bridge, trained blueprint, integrated bot, production action width, or poker-strength result exists; broad-suite execution, capability approvals, and the holistic-audit backlog remain open

## Question

What exact source contract can join the preserved complete-hand fixtures to
the governing per-action clock without exposing hidden cards, changing sealed
code, silently recovering from an invalid blueprint, or mistaking an internal
controller return for external delivery?

## Decision

Preregister the blueprint-only increment-one source contract below. This is
an engineering integration boundary, not an executable experiment authority.
The only new runtime namespace is `pontius.v0a`. No resolver candidate,
action abstraction, training, h32 machinery, GPU work, network adapter, or
subprocess belongs to this increment.

This candidate includes the prospective sequencing clarification to ADR-0482
authorized by the controller's 2026-08-30 ruling on contradictory or circular
process requirements. The same day's CodeRabbit retirement is recorded in
[the workflow amendment](../workflow-amendment-2026-08-30.md), which preserves
the original workflow bytes and all other gates. These rulings resolve those
process decisions; they are not authorization for a ceremonial commit. Until
the reviewed decision is authorized and committed, this remains an isolated
candidate, not an accepted mainline opening.

## Bootstrap sequencing and budgets

ADR-0482 requires measured provenance for frozen operating bounds and a lane
budget at the first preregistration. ADR-0484 requires these contracts before
implementation, while an end-to-end rehearsal requires sealed implementation.
No v0a rehearsal measurements exist. Neither the historical replay's timings
nor the provisional eight lifecycles/six weeks resolves that dependency.

For this new lane only, distinguish a contract/source opening from an
operational opening:

1. This decision freezes semantics and permits source construction and its
   ordinary isolated correctness tests. It admits no experimental owner.
2. The candidate receives the workflow's two independent Tier-C reviews and
   source seal. The existing three-round review circuit breaker applies.
3. The sealed workflow is rehearsed on the synthetic controls below, using
   rehearsal-only paths and identities. Logs are non-evidentiary.
4. A separate append-only decision binds the measured operating ceilings,
   authoritative fixture schedule/population, and lane lifecycle/calendar
   budget, with identified scaled rehearsal measurements as provenance.
5. A subsequent explicit authorization may admit exactly one invocation of
   that closed contract. Absence of step 4 is an unconditional no-invocation
   gate, not permission to run without a budget.

The bootstrap ends at its first source seal and completed rehearsal report:
it cannot authorize a production run or become a sequence of successor
owners. A changed source needs fresh review and sealing; exhausted review
rounds require the existing controller checkpoint. Two consecutive owner
deaths on infrastructure, lifecycle, or authorization grounds still trigger
the mandatory stand-down, wherever such owners are subsequently admitted.
The first operational budget takes effect at step 4 and counts every later
owner in this lane, including failed ones; it cannot reset on a successor.

Eight lifecycles or six weeks remains a nonbinding planning proposal, not a
measurement or frozen limit. No laboratory wall, memory ceiling, file-size
ceiling, authoritative hand count, or authoritative action count is invented
here. Implementation safety limits must be declared, measured in rehearsal,
and bound by step 4 before operation; absence of a required limit blocks it.
The 15,000 ms action wall and 1,000 ms emission reserve are inherited normative
requirements from ADR-0307. They are not new measurements and cannot be relaxed
by rehearsal. The two synthetic hands below are correctness/rehearsal coverage,
not a statistically meaningful or authorized campaign population.

Rehearsal values may inform operational cost provenance only. They may not
become correctness acceptance evidence, a performance fit, a ranking, a
candidate choice, a quality claim, or a substitute for an authorized result.
No earlier parking verdict, consumed identity, or v7 closure changes.

## Components and permitted dependencies

Use small modules under `src/pontius/v0a/`:

| Module | Responsibility |
| --- | --- |
| `__init__.py` | Inert package surface; no execution or optional imports |
| `model.py` | Frozen event, action-envelope, receipt, record, and outcome values |
| `clock.py` | One monotonic witness and the outer authoritative ledger adapter |
| `runtime.py` | Visible-state transitions, blueprint selection, and emission |
| `trace.py` | Strict canonical serialization, parsing, and semantic replay checks |
| `replay.py` | Explicit-deal fixture host, isolated mailbox, and terminal verifier |

`model`, `clock`, and `runtime` cannot import `replay` or hold its host object.
The policy-selection function receives only an immutable blueprint,
`OneSeatCardState`, `NoLimitBettingState`, and its exact legal decision.
It receives no event iterator, seed, fixture configuration, mailbox, runtime
object, arbitrary callback, complete-deal object, or closure containing them.
This is separation of trusted components, not a sandbox against malicious
Python introspection.

Allowed external internal-module imports are `action_clock`,
`preparation_bank`, `legal_decision_spine_v2`, `no_limit_betting`,
`holdem_cards`, and `immutable_blueprint`; only `replay` may additionally use
the public `river` evaluator and the complete-deal type. Other imports are
standard library or declared siblings. No new cycle or legacy outgoing edge
is permitted. Existing package-initialization behavior remains unchanged and
must still work with the base CPU dependencies and no optional packages.

The ADR-0290 explicit-deal fixtures and event discipline are reused as
controls. Five-axis belief updates and full-width policy distributions are
explicitly deferred: increment one selects directly from the immutable
blueprint and claims no new belief integration. Do not describe this as a
revalidation of all ADR-0290 behavior.

## Event and privacy contract

The host owns the complete deal and future schedule. The runtime accepts one
event at a time. Every event has exactly `schema_version`, `kind`, `hand_id`,
`event_index`, and the variant fields below. Schema is the literal
`pontius-v0a-event-v1`; IDs are nonempty ASCII strings, indices are exact
nonnegative integers, and an event cannot supply a clock timestamp.

| Kind | Variant fields and constraints |
| --- | --- |
| `hand_started` | `button`, `controlled_seat`, six `starting_stacks`, `small_blind`, `big_blind`, and `private_cards`; event index zero; only the controlled two cards |
| `opponent_action` | `street`, `seat`, and `action`; exact current actor, never the controlled seat |
| `street_revealed` | `street` and `cards`; immediately next street, completed betting round, exactly 3/1/1 newly public cards |
| `showdown_result` | `strengths`; six entries, exact live-seat hand ranks and null for folded seats; only after betting terminates at showdown |

Cards are the existing integers 0 through 51; a private pair is ascending and
contains two distinct cards. Board order is reveal order. Reject booleans as
integers, duplicates, known-card overlap, invalid seat/street values, wrong
hand IDs, repeated/skipped indices, premature reveals, and events after
completion. An event index advances once per accepted host input; controlled
actions have separate contiguous indices and are never injected as inputs.
A new hand requires a fresh runtime, never a reset of the current one.

An action has exactly `kind` and `raise_to`. Kinds are `fold`, `check`,
`call`, and `raise`; only `raise` has an exact positive integer `raise_to`,
interpreted as total contribution on the current street. Other kinds require
null. The unchanged betting kernel decides legality.

Once a processed event makes the controlled seat act, the runtime completes
that decision or returns a terminal failure before accepting another event.
At a fold terminal, no showdown event is accepted and `settle()` takes no
strength vector. At a showdown terminal, policy selection is permanently
disabled before terminal strengths enter a separate settlement path.
The host independently recomputes strengths from its complete deal and checks
production settlement against the chip-depth payout oracle. A claimed
showdown result or payout supplied by the runtime is never its own oracle.

The mailbox is a separate value-only object with no reference to the dealer,
future schedule, event iterator, or complete deal. A policy has no mailbox
reference. Hidden-card tests exercise the real runtime with distinct hidden
completions of the same visible prefix and require identical decisions;
data-flow controls also reject passing the host or complete deal to selection.

## Blueprint outcomes

Bind the immutable blueprint at hand initialization by its canonical digest.
Before every decision validate the complete current context, derive the exact
key, and call the unchanged `action_for` API. A missing match selects check,
else call, else fold. An illegal matching entry or invalid decision context
terminates with a typed failure and emits no action for that input.
An entry for a different state is just a miss, not a special stale category.

Pass `candidate=None` and the validated blueprint action as `fallback` to
`LegalDecisionSpineV2.emit_controlled_action`. Record the table hit/miss
separately from the spine's no-candidate reason. There is no alternate
strategy or recovery choice to disagree with the state committed by V2.
A later h32 increment must separately bind candidate commit/delivery
consistency; this blueprint-only contract does not settle that question.

## Authoritative clock and emission boundary

Use one validated monotonic-nanosecond witness callable for both ledgers.
It invokes `time.monotonic_ns` in ordinary runs, returns an exact nonnegative
integer, rejects reversal, and retains its last returned sample. Tests may
inject the same interface with a deterministic clock. Never latch/replay a
sample, accept an event timestamp, reconstruct a start by subtracting a
rounded duration, or read a private field of a sealed ledger.

The outer `ActionClockLedger` is the sole runtime response authority. The
unchanged V2 ledger remains controller diagnostics; its time is neither
summed with nor substituted for the outer time. This is an explicit
prospective host-adapter boundary, not a claim that ADR-0308 already measured
external delivery.

The outer `start_transition_boundary()` is the first runtime operation at
host dispatch, before input validation, visible-card construction, V2
transition work, or policy work. Save the witness sample immediately after
that call. Once the resulting actor is known,
`finish_transition_boundary()` classifies the full event interval as response
or preparation and binds the resulting public betting-state digest. No
caller backdates or resets an active action. Terminal event validation is
post-hand verification, not additional decision time.

Before and after blueprint work, inspect the outer ledger. Also establish a
ready-to-emit checkpoint after all adapter decision/context validation and
immutable action-envelope construction, before calling V2 emission. Inspect
the outer ledger there: decision work completed beyond the 14,000 ms cutoff
produces `work_cutoff_exceeded` and rejects the hand even if delivery remains
within 15,000 ms. No new policy choice or decision work follows that checkpoint.
The unchanged V2 emission legality/application path and mailbox acknowledgement
are emission work, permitted to use the remaining reserve. An endpoint between
14 and 15 seconds alone is not a work-cutoff violation. There is no
noncooperative-worker cancellation or OS scheduling guarantee in this scope.

Delivery is synchronous acceptance of a prebuilt immutable action envelope
by the host-owned in-memory mailbox. No disk or network operation lies
between the V2 return and mailbox delivery. The mailbox accepts a particular
`(hand_id, action_index)` at most once; retrying a failed or ambiguous delivery
is forbidden. After acknowledgement, immediately call outer `finish_action`
and save the witness sample before any other ledger read. If that call fails,
acceptance remains known: retain the full decision record with interrupted
timing below, never substitute an earlier sample for a delivery observation.

Name that timestamp `emission_observed_ns`: it is the measured post-delivery
observation, a conservative endpoint that includes delivery and acknowledgement,
not the claimed nanosecond of a memory write or a network receipt. Require
`(emission_observed_ns - wall_start_ns) / 1_000_000_000` to equal the outer
snapshot's elapsed seconds. Integer subtraction supplies exact recorded
nanoseconds; the existing ledger supplies deadline/accounting semantics.
An endpoint greater than 15,000,000,000 ns after start is a deadline violation.
Exactly the inherited boundary is interpreted as the ledger interprets it;
tests cover both boundaries and one nanosecond on either side.

The emitted action stands even if the deadline was crossed. Record the
violation and terminate the hand unsuccessfully; a legal fallback cannot
erase it. Serialize and write the decision trace only after delivery and
clock closure, before dispatch of the next event. This post-delivery work
must be measured as uncredited preparation or post-terminal bookkeeping,
never disappear from the hand's accounting or extend the next action's wall.
If a clock failure prevents that measurement, report incomplete accounting
under the failure contract below; no further input or successful hand is allowed.

Keep the outer ledger open after betting terminates, independently of V2's
internal finalization. Close every non-response interval through public
`finish_transition_boundary`, `abort_transition_boundary`, or
`stop_preparation_work`, as applicable. Classify each returned
`PreparationWorkInterval` exactly once, by whether betting was already terminal
at that interval's entry. Ordered sums of its public `compute_seconds` values
form pre-terminal preparation or post-terminal bookkeeping, with no overlap
and no witness-subtraction substitute. A transition that first terminates
betting belongs to the pre-terminal category; subsequent settlement and trace
work belongs to the post-terminal category. Responses remain separate.

The terminal row's two compute totals cover all completed intervals through
the pre-publication cut: after settlement/verification and every preceding
trace-row write, before construction/serialization of that terminal row. They
do not claim to include the terminal row's own future publication. Measure
that construction, serialization, and write in one final outer preparation
interval; its returned public duration is retained separately in the host
outcome as `terminal_publication_compute_seconds`. Finish that interval before
outer `finalize()`. On a failed hand, no further input is accepted; terminal
reporting can still be attempted if the clock remains valid and all active
intervals were honestly closed. Never query or repair a known-broken clock.

The host completion receipt has exactly `run_id`, `hand_id`, `trace_sha256`,
`terminal_publication_compute_seconds`, `accounting_complete`, `passed`, and
`failure_reason`, plus `secondary_failures`. The latter is an ordered array
of later typed failure codes, empty when none occur; it preserves reporting
failures without replacing the first cause. Trace digest hashes the entire
completed file, including its
terminal LF; it is null if complete publication was not established. Duration
is the final public interval output, or null if it could not be closed. Host
success requires the successful terminal, complete publication, the measured
publication interval, and outer finalization. Failure retains the primary
typed cause and forbids host success even if a syntactically complete terminal
was already written. The receipt is returned after these operations, outside
the trace it describes; persisting or transporting that receipt is separately
declared host reporting, not another hand action or a self-measuring trace.
Trace-only replay validates the hand semantics and pre-publication accounting;
it cannot establish host completion without the corresponding receipt.

## Decision records and trace contract

JSON uses UTF-8, no BOM, sorted keys, compact separators, finite numbers, and
one LF per record. Parsing rejects duplicate, unknown, and missing keys,
wrong exact types, bad digests, invalid enums, and inconsistent cross-record
identities. Digests are lowercase SHA-256 of the specified canonical bytes.
Decoded arrays become immutable tuples. No executable object is deserialized.

The trace is a header, ordered event/decision/failure records, then exactly
one terminal record. Each row has `schema_version`, `record_type`, `run_id`,
and a contiguous `record_index`; schema is `pontius-v0a-trace-v1`.

| Record type | Additional exact fields |
| --- | --- |
| `header` | `mode`, `source_commit`, `source_manifest_sha256`, `configuration_sha256`, `blueprint_sha256`, `clock_kind` |
| `event` | `event` containing one exact event object above |
| `decision` | `hand_id`, `event_index`, `action_index`, `street_action_index`, `seat`, `street`, `state_before_sha256`, `state_after_sha256`, `visible_cards_sha256`, `blueprint_sha256`, `selected_action`, `selection_reason`, `spine_reason`, `timing`, `preparation_use`, `failure_reason` |
| `failure` | `hand_id`, `event_index`, `action_index`, `code`, `delivery_status`, `delivered_action`, `timing` |
| `terminal` | `hand_id`, `complete`, `passed`, `failure_reason`, `event_count`, `decision_count`, `interrupted_response_count`, `accounting_complete`, `settlement`, `semantic_sha256`, `trace_prefix_sha256`, `preparation_compute_seconds`, `post_terminal_compute_seconds` |

`mode` is `correctness`, `rehearsal`, or `authorized`; the last is refused
until an independently verified later authorization exists. `clock_kind` is
`monotonic_ns` or `deterministic_test`; the latter cannot support a live timing
claim. In rehearsal/authorized mode source commit is the exact source-sealed
commit. In correctness mode it is the disposable snapshot's captured base
commit, and the manifest binds the actual tested files including overlays;
this does not claim that those overlaid bytes were committed or source-sealed.
The SHA-256 manifest binds lexicographically sorted
`<lowercase-file-sha256><two spaces><relative-posix-path><LF>` rows for the
declared source/configuration dependency closure, not mutable result bytes.
The configuration digest binds the host's full sealed schedule but only the
opaque digest, not the schedule or seed, enters the runtime metadata.

Hand/action indices and nanoseconds are exact nonnegative integers; action
indices start at one. `selection_reason` is `table_hit` or `passive_default`.
`spine_reason` is the unchanged V2 enum spelling. State digests are from
`public_betting_state_sha256`; visible-card identity hashes a canonical JSON
object with exactly `controlled_seat`, `private_cards`, `street`, and `board`
from the current `OneSeatCardState`, with no hidden cards. The before state
is the decision context; the after state is the state for the delivered action.
The schema's `private_cards` maps to that sealed type's `private_hand` attribute.

`timing` has exactly `status`, `interruption_reason`, `wall_start_ns`,
`last_valid_observation_ns`, `emission_observed_ns`, `elapsed_ns`,
`response_compute_seconds`, `response_uninstrumented_seconds`,
`work_cutoff_crossed`, and `deadline_crossed`. Its two variants are:

- `status=completed`: interruption reason is null; all measurements are
  present; the last valid observation equals the emission observation;
  cutoff/deadline flags are exact booleans. Seconds are finite nonnegative
  outputs of the closing outer ledger snapshot, not caller measurements.
- `status=interrupted`: interruption reason is the actual typed failure;
  retain the valid wall start and the witness's last valid observation at
  failure, at or after that start. Emission, elapsed, and both final response
  seconds fields are null. A cutoff/deadline flag is true only if an earlier
  valid outer snapshot established it; otherwise null, never a false claim
  that the unfinished interval stayed within bounds. No invalid/reversed
  sample becomes a valid observation and the clock is not retried to repair it.

The difference between last valid observation and start is only an observed
prefix, not a completed response duration or a delivery timestamp. If no
valid response start was established, a failure row has null timing instead.
A failure after a valid response start retains its timing even before delivery;
if delivery was accepted, it also has the required full decision row, with
identical timing and preserved action/context/state/policy bindings. Never
replace that decision row with only a failure row. A later write failure does
not invalidate already completed timing. Nanoseconds are process-local;
cross-run comparisons never compare absolute epochs. Completed work-cutoff
state includes the before/after-work checks above.

`preparation_use` has exactly `producer_status`, `artifact_sha256s`, and
`credited_seconds`, respectively `producer_absent`, an empty array, and zero.
Absence of credits does not imply absence of pre-action compute: report the
uncredited categories and final publication under the closing contract above.
The initial policy is an offline
artifact, not online preparation credit. `failure_reason` is null on success
or one code below. A delivered but late action still has a decision record.

`settlement` is null on unsuccessful/incomplete hands; otherwise it has exact
fields `payouts`, `final_stacks`, and `pots`. The first two are six-element
nonnegative integer arrays; each pot has `amount` and sorted unique eligible
`seats`. Pot order is the production kernel's contribution-depth order.
The independent oracle, not serialization agreement, establishes correctness.

`semantic_sha256` hashes one canonical JSON object with exactly `events`,
`decisions`, and `settlement`. Events are the ordered accepted event payloads,
without their trace-row envelopes. Decisions are ordered projections with
exactly `hand_id`, `event_index`, `action_index`, `street_action_index`, `seat`,
`street`, `state_before_sha256`, `state_after_sha256`, `visible_cards_sha256`,
`blueprint_sha256`, `selected_action`, `selection_reason`, `spine_reason`, and
`preparation_use`. Settlement is the exact object above or null. The projection
includes no header, failure/terminal row, run ID, record index, timing, or
timing-dependent failure reason. Schedule-bound hand IDs stay fixed across
reruns; distinct run IDs are mandatory and do not change these semantic bytes.
Source/configuration/policy identities and each run's row bindings are validated
independently; excluding them from a projection never permits mismatched inputs.
Runtime and replay use this exact projection, and a separately written checker
replays legal transitions and compares selected actions/payouts. A failed
prefix may have a semantic digest but cannot satisfy successful replay.
`trace_prefix_sha256` hashes all exact preceding LF-terminated row bytes.
A missing/duplicate terminal, discontinuity, wrong count, mismatched binding,
illegal transition, changed policy, or digest mismatch rejects the trace.
Only a terminal with `complete=true`, `passed=true`, and complete accounting
admits success. Successful reruns with distinct run IDs must have identical
semantic bytes/digests. Naturally varying timing is validated structurally and
against its recorded walls, never byte-compared or stripped of failure status.

Trace files use create-new semantics under an explicit run root; existing
destinations, unsafe links, or path escape reject without overwrite. Writes
are bounded by limits established at measured closure. No governance writer
or generalized transaction engine is introduced. A write failure after
delivery leaves the action delivered, returns an in-memory typed failure and
the retained record, stops further input, and leaves any incomplete file
unaccepted. Do not claim the failed destination durably recorded its own
failure. The run host retains the outcome through its independent reporting
path; if that also fails, durability is explicitly unestablished.

## Failure vocabulary

Freeze these codes: `invalid_event`, `event_order`, `invalid_decision_context`,
`invalid_blueprint_entry`, `clock_invalid`, `clock_reversed`,
`work_cutoff_exceeded`, `action_deadline_exceeded`, `delivery_rejected`,
`delivery_ambiguous`, `trace_write_failed`, `trace_invalid`,
`settlement_mismatch`, `source_binding_mismatch`, and `authority_absent`.
Input/blueprint failures emit no action from that input. Clock, delivery, or
write failures preserve any already delivered action and its known receipt.
`delivery_status` is `not_attempted`, `rejected`, `accepted`, or `unknown`;
an exception after publication without an unambiguous receipt is `unknown`,
never a safe retry. `delivered_action` is null unless acceptance is known.
Failure records may have null `hand_id`, `event_index`, or `action_index`
when malformed input has not established that identity. The terminal may
likewise have null `hand_id` if no valid hand-start event was accepted.
`event_count` counts accepted input events; a rejected input is represented
by a failure row, never smuggled into the valid event stream. `decision_count`
counts known delivered actions. An ambiguous delivery forces an incomplete
terminal and cannot make this count evidence of nondelivery.
`interrupted_response_count` counts response attempts with a valid start but
no completed post-delivery outer snapshot, counting a duplicated
decision/failure timing object only once by action identity. A failure before
a controlled context establishes that identity is one interrupted input
boundary, reported once by event identity rather than dropped from accounting.
An interrupted response or unknown delivery forces `complete=false`,
`passed=false`, and `accounting_complete=false`. The two terminal compute
totals are complete ordered aggregates of public interval outputs through the
defined pre-publication cut; each is null if that category's measurement could
not be completed, never zero or a prefix presented as its complete total.
Terminal publication is accounted separately in the host receipt, not added
back into the row that preceded it. Other failures that prevent accounting
also set `accounting_complete=false`. Already valid per-action measurements
remain available; failure recovery does not query broken clocks or fabricate
the unobserved remainder.
Terminate on the first failure; retain the primary cause and do not turn
cleanup into success. If work-cutoff and deadline flags both arise during
the same attempted response, the terminal reason is
`action_deadline_exceeded`, with both flags retained. A later trace-write
failure is also returned separately in the host outcome and never overwrites
the earlier primary cause.

## Synthetic controls and future source seal

Preserve the semantic fixtures A and B in ADR-0287 as explicit chance outcomes
and independent expected payouts, without invoking its historical owner.
The replay host supplies A's passive four-street hand and B's all-in side-pot
hand through the new event interface. These are engineering controls only.
Use seed labels `pontius-v0a-hand-replay-v1/control-A` and
`pontius-v0a-hand-replay-v1/control-B`. To derive a seed-bound deal variant,
hash the UTF-8 label with SHA-256, read its first eight bytes as an unsigned
big-endian integer, take modulo 24, and select that zero-based lexicographic
permutation of `cdhs`. Rename every suit in the explicit fixture by that
same permutation, preserving ranks, seat order, actions, and expected payouts.
This is disclosed deterministic suit renaming, not random sampling or a
fresh research population. The source seal binds the materialized bytes.

Additional correctness cases cover repeated controlled actions on one street,
fold terminals, tied pots and odd chips, malformed events, hidden completions,
table misses and illegal hits, input/output delays, cutoff crossings,
clock failure both before delivery and immediately after real mailbox acceptance,
duplicate delivery, write failure after delivery, truncated traces, and
semantic/digest tampering. Distinct run IDs on identical successful schedules
must produce equal semantic bytes. Each has an explicit expected outcome;
no case silently becomes a skip because the host lacks an archive or GPU.
Delay controls distinguish decision work crossing 14 seconds from lawful use
of the emission reserve, and both from an endpoint past 15 seconds. A terminal
control injects positive settlement and final-publication work, verifies the
disjoint public-ledger totals and receipt, and makes publication-clock failure
reject host success even when the trace contains a complete terminal row.

Source sealing binds the full new package, tests, approved boundary-policy
changes, exact fixture/configuration bytes, dependency closure, schema,
entry-point argv, and independent reader. Review uses the frozen commit and
blob-derived manifest. No source hash, size limit, schedule count, or passing
result is filled with a guessed value in this preregistration.

Reserved protocol ID is `pontius-v0a-hand-replay-v1`. A production attempt,
journal, result, and consumed-launch identity must stay absent until their
separate operational closure and authorization. Rehearsals use only
`pontius-v0a-hand-replay-v1-rehearsal-<unique-id>` in a disjoint run root;
unit correctness runs use `pontius-v0a-hand-replay-v1-correctness-<unique-id>`.
The future owner must reject a mode/root/identity mismatch before any lifecycle
write. No historical owner or consumed marker is used to prove that rejection.

## Change boundary and acceptance map

This documentation round changes only this new ADR, the new prospective
workflow amendment, and generated `STATUS.md`. The accepted original workflow
and charter remain byte-for-byte unchanged.
It changes no runtime, test, configuration, capability, historical source,
retained result, or lifecycle file. Implementation after accepted opening may
touch only the revised brief's permitted paths, with these constraints:

- Add explicit `pontius.v0a` origins and the import policy above to the
  stabilization boundary checker and add focused boundary tests. Never
  regenerate `docs/architecture/dependency-baseline.toml` to absorb them.
- Register `tests/test_v0a_hand_replay.py` in the inventory declaration and
  regenerate inventory/profile bytes through the authorized writer. Refresh
  only mechanically affected census expectations; no capability is granted.
- Add the CPU clone-safe suite to CI without demoting any current hard gate.
  CI remains an early-warning layer, not the complete acceptance procedure.
- Keep the exact betting/card/blueprint/timing kernels and historical replay
  untouched. The new host depends on their public interfaces only.

| Brief criterion | Required implementation evidence |
| --- | --- |
| 1: complete hand and settlement | Both semantic controls; independent chip-depth/odd-chip oracle; exact conservation |
| 2: action wall and emission | Real ingress/mailbox path with deterministic delayed operations; fresh same-street clocks; both cutoff edges; ordinary-clock smoke |
| 3: hidden-card isolation | Real selection path under alternative hidden completions; forbidden object/closure checks |
| 4: blueprint outcomes | Separate miss/passive, legal hit, illegal hit, and invalid-context controls |
| 5: records | Exact typed schema round trip; action/source/context identity; accepted delivery followed by clock failure retains a full decision; honest credits and interrupted accounting |
| 6: fail closed | Wrong actor/street/index/card and delivery/write failure schedules through production paths |
| 7: replay | Independent legal replay; exact semantic bytes across distinct run IDs; terminal/digest checks; completed/interrupted timing validation |
| 8: CPU and interpreters | Fresh disposable snapshots on actual 3.11 and 3.14 with no optional dependency requirement |
| 9: CI | New direct CPU gate and unchanged existing hard gates |
| 10: boundaries | New v0a allowlist positives/negatives; unchanged legacy baseline blob; no new cycle |

The implementation's Tier-C sequence is deterministic RED before source
changes, focused snapshot GREEN, immutable freeze, two independent cold
adversarial reviews, permitted broader gates, explicit per-commit
authorization, ceremonial commit and push. Slice a candidate above roughly
3,000 changed lines by coherent contracts with their tests, not by separating
all source from all tests. The estimated 2,500-4,000 lines is planning context,
not an experimentally measured admission limit.

No tests run from the primary checkout. Use fresh disposable D:-local
snapshots, `-B -P`, exact snapshot `PYTHONPATH`, scrubbed environments, and
absolute bound Git. Record the actual executable, implementation, and full
version before payload import; never substitute 3.14 for missing 3.11.
Historical and design capability approvals remain the orchestration plans'
gates. This decision authorizes no guarded broad profile or historical owner.

## Continuity

The complete inherited trust chain from ADR-0310 through ADR-0476, including
its machine-checked continuity directives and historical continuity strings,
remains binding. ADR-0477 through ADR-0482 retain the stabilization decisions;
ADR-0483 parks the compiled lane and ADR-0484 splits the v0a increments.
No native-simplex robustness result, sizing result, compiled result, or
historical timing result is reopened or relabeled here. Evidence Tasks 4-9
still precede orchestration Tasks 3-10, then 11b and 12. Generator extraction
is not silently inserted into that order by this decision.

## Kill criteria

Reject source that exposes hidden data to policy selection, changes a sealed
kernel or legacy baseline, admits an invalid blueprint as passive recovery,
substitutes the V2 internal stop for external delivery, erases a late emission,
retries ambiguous publication, fabricates credits, accepts an incomplete
trace, requires optional GPU dependencies, or widens the permitted namespace.
Reject operation without the append-only measured closure and independent
one-shot authorization. Neither budget exhaustion nor a failed result can
be repaired by editing a sealed fixture, expectation, clock, or owner.

## Claims boundary

This decision establishes proposed/accepted contracts according to its
approval boundary, not executed behavior. No new source, rehearsal receipt,
authoritative complete hand, 15-second action result, preparation benefit,
policy quality, live transport, OS deadline guarantee, full-width strategy,
trained blueprint, or poker-strength result exists by virtue of this file.
H32 remains increment two under a fresh preregistration; replay-campaign
claims remain increment three. The compiled lane stays parked and v7 stays
permanently consumed.
