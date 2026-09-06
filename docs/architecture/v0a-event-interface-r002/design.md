# One-hand event interface: design r002

Status: proposal only. Base: 5f90279ab3d7d78fe790b115a697c52262280c0d.
Task: v0a-event-interface-design/r002. Tier C. No implementation exists here.

## Components and receipt boundary

Add tools/v0a_event_adapter.py only. It owns source/policy admission, a closed
event decoder, a small tool-local HandRuntime subclass, a pipe mailbox and the
one-hand loop. Existing src/pontius and both older tools remain unchanged.

The local receipt boundary is the first operation of dispatch_frame(raw), called
immediately after one complete LF-terminated binary stdin frame is returned.
Binary framing/transport wait precedes this boundary. UTF-8 decode, JSON parsing,
schema validation and event construction follow the boundary and are charged.
This does not identify when bytes first entered an OS buffer. Never batch-decode
future events. Read the next frame only after the current event's result output.

The input syntax admits at most 16384 bytes including the final LF. Read at most
16385 bytes; the bridge performs length/LF checks after opening its boundary,
and rejects an overlong or unterminated frame without decoding it.
This is a proposed format-domain restriction, not a measured memory/time capacity
or an operating quota. A peer can still stall before LF; there is no watchdog.

## Closed wire contract

CLI arguments: --blueprint (absolute D-local regular/non-reparse file) and
--session-id. The ID is pontius-v0a-event-interface-v1-correctness- followed by
1..64 ASCII letters, digits, underscores or hyphens. There is no mode switch,
output path, scenario, expected-results input or policy replacement command.
Every input hand_id must equal this ID. Only declared correctness-test use is
proposed; the namespace does not grant arbitrary data or operating authority.

Input is one strict UTF-8 JSON object per LF frame, with no BOM, CR, duplicate
member, extra object member, trailing value, float or nonfinite number. Object
member order/ordinary JSON whitespace have no significance within the frame cap.
Exact integers have at most 640 decimal digits; bool is never an integer.
During hand_started admission also require sum(starting_stacks) < 10**640.
The existing model imposes positivity and six seats. This total-chip bound makes
all derived chip balances, contributions, pots and payouts serializable at the
minimum int_max_str_digits=640 setting; bounding each input stack alone cannot.
Check the sum before inherited processing, within the same receipt boundary.
Do not recover after an invalid frame or EOF before completion.

The four exact member sets are the existing event payloads:

- hand_started: kind, schema_version, hand_id, event_index, button,
  controlled_seat, starting_stacks, small_blind, big_blind, private_cards.
- opponent_action: kind, schema_version, hand_id, event_index, street, seat,
  action; action contains exactly kind and raise_to.
- street_revealed: kind, schema_version, hand_id, event_index, street, cards.
- showdown_result: kind, schema_version, hand_id, event_index, strengths.

schema_version is pontius-v0a-event-v1. Cards are existing numeric card IDs
0..51, not a new card notation. Convert JSON arrays into owned exact tuples;
then construct and re-admit the existing model types. Strengths have six slots,
each null, an exact integer or a nonempty tuple of exact integers; the runtime
enforces live-seat participation and comparability. All existing model and
runtime constraints apply. Accept no timestamp, full deal, future board,
opponent-private hand, extra action instruction or opaque Python object.

Output frames use canonical UTF-8 JSON, sorted keys, finite values and LF.
Every frame has protocol=pontius-v0a-event-interface-v1, session_id and type:

- ready: source_commit, source_manifest_sha256, blueprint_artifact_sha256,
  blueprint_sha256, evidentiary=false. The first is the actual source commit;
  all three SHA-256 values are exactly 64 lowercase hexadecimal characters.
  blueprint_artifact_sha256 hashes the admitted immutable raw artifact bytes;
  blueprint_sha256 identifies the decoded policy. Emitted after admission.
- action: hand_id, action_index, seat, street and action (kind, raise_to),
  copied from the immutable ActionEnvelope. There is no final decision/timing
  at this pre-acknowledgement point.
- event_result: event_index (null if admission failed), status, decision and
  failure. The latter two are the existing payload-helper output or null.
  A decision inside this result is diagnostic, not another
  instruction to act. A failed result may describe an already-delivered action.
- hand_result: complete, settlement, rank_source, evidentiary=false,
  preparation_compute_seconds, post_terminal_compute_seconds,
  interrupted_response_count, accounting_complete, failure_reason,
  secondary_failures. This is the outcome at the pre-publication cut below.
  complete is true only for a settled, successful hand at that cut; settlement
  is the existing settlement_payload then, otherwise null. rank_source is
  host_supplied for successful showdown, not_required for fold, otherwise null.
- session_result: status, terminal_publication_compute_seconds,
  accounting_complete, failure_reason, secondary_failures, accounting_scope,
  evidentiary=false. status is completed or failed. accounting_scope is exactly
  runtime_begin_to_final_publication. This closing report is sent after finalizing.

Each accounting_complete and complete is an exact bool. Compute seconds are the
finite nonnegative public API values, or null when unavailable, never fabricated
zero. interrupted_response_count is an exact nonnegative integer. failure_reason
is the first retained typed code or null; secondary_failures is an ordered array
of later codes, preserving distinct occurrences. The code vocabulary is exactly
the pinned model.FailureCode values. For this tool, trace_write_failed names a
host-frame serialization/write failure, source_binding_mismatch names source
revalidation failure, and invalid_event includes premature EOF. Other runtime
codes retain their meaning. No exception text or raw input enters these fields.
Before runtime admission, only a typed stderr refusal and nonzero exit are
required; no fabricated runtime accounting or protocol success follows. Ledger-state
incompleteness can have no typed clock cause: report null and incomplete, never
invent a clock occurrence. No frame contains passed/trace-verified/strength claims.

The consumer acts only on type=action and deduplicates (hand_id, action_index).
Successful hand_result, completed session_result and process exit 0 together
establish transport-session completion under the exact closing predicate below.
Any failure emits a typed REFUSED reason on stderr when possible and exits
nonzero. The caller retains stdout/stderr/exit together, including partial bytes.
No earlier action/result is withdrawn by a later failure. A failed stderr write
does not turn failure into zero exit. The process exits after the one hand.

## Ingress bridge and authoritative clock

A direct decode-then-HandRuntime.dispatch wrapper omits JSON admission time.
Public begin_host_accounting/owned_bookkeeping count host preparation and cannot
retroactively make it response time. Do not use them to conceal this interval.

The tool-local subclass mirrors only the dispatch timing/admission/error shell
at runtime.py:536, replacing the model-admission block with the strict raw-frame
decoder followed by model.admit_event. Its first timing operation opens the
inherited outer start_transition_boundary, before inspecting raw input. The same
boundary and its real start pass to inherited _process. All betting, card,
selection, cutoff, emission, settlement and failure-record logic remain inherited.
It never calls super().dispatch afterward, creates a second authority ledger,
reads ledger-private state, calls _begin_action_at or supplies event timestamps.

Pin runtime.py blob 1c855b3b5e8f2d057105128733f43279b9f73990. The named private
dependencies are _dead, _complete, _outer, _witness, _boundary_open,
_known_cutoff, _known_deadline, _reject, _clock_reject, _process,
_release_boundary, _retain_error, _from_failure and _HandFailure, plus the
public methods used by the unchanged dispatch shell. No other private runtime
surface is opened. A decoder type/value/encoding/depth failure enters the same
INVALID_EVENT failure and closure path; raw input is never rendered as code.
The shell's initializing and failure paths must match the pinned implementation.

This private coupling is deliberate and limited: roughly one dispatch shell
avoids copying the full runtime or changing sealed source. Source binding and
observable clock/failure tests protect this dependency. A changed inherited
runtime pin stops this tool; no general compatibility framework is introduced.

Decision work ends at the inherited ready checkpoint: >=14,000,000,000 ns is a
work-cutoff violation. Emission may occupy the reserve; >15,000,000,000 ns is a
deadline violation. Do no policy choice or context validation inside the mailbox.
Serialization of an already fixed ActionEnvelope is emission work. Preserve
inherited failures and their handling of an action emitted before a late fault.

## Local delivery and terminal semantics

ADR-0485 currently specifies an in-memory mailbox. The prospective source opening
must explicitly admit this different endpoint for the new tool only: a single
synchronous os.write to binary-mode stdout for a prebuilt action frame. Set
the standard descriptors to binary mode before ready; do not use buffered text
output or a separate flush for action publication. Local delivery is
known only when that write returns the full byte count. Return an exact matching
DeliveryReceipt then; the inherited runtime closes the action immediately after
receipt admission. It does not acknowledge that the caller parsed/applied it.

Own/deduplicate the action identity before the write. A short write or exception
is ambiguous and is not retried, completed with another write, or relabeled as
known non-delivery. Never write an action after a pre-delivery refusal. Broken
pipes, blocked output and process death provide no arbitrary-peer liveness
guarantee; a synchronous write may finish late, which cannot retract its bytes.
The runtime must retain the resulting delivered/unknown state and timing failure.

The action frame precedes the completed DecisionRecord. Publish event_result
after dispatch returns, using the existing payload helpers. Measure required
non-response output/bookkeeping with the runtime's public ownership APIs; never
hold a preparation interval open across dispatch. Read/idle is separate from
agent work. Stop on any failed dispatch or required host operation.

On a fold terminal, settle directly. At showdown, the host supplies comparable
terminal ranks only after betting closes; the runtime disables policy selection
before accepting those ranks. Report the kernel settlement conditional on them.
No new evaluator verifies a hidden deal and no independent-trace claim follows.
A late publication/closure error remains failure even if hand_result was seen.
There is no trace file, archive owner or replacement for verify_successful_trace.

## Accounting cut and closing report

After immutable source/policy admission and runtime construction, call public
begin_host_accounting before constructing/publishing ready. The declared totals
cover that runtime scope; earlier process/import/policy bootstrap, binary framing
and idle transport wait are outside it. They claim no full-process cost or
preparation credit. There is no producer or carry-forward credit. Record this
scope explicitly in session_result; it never removes work after event receipt
from the response wall or grants extra action time.

Use required owned_bookkeeping intervals for ready and each event_result, then
for settlement and final source revalidation. Preserve every public interval's
existing pre-terminal/post-terminal classification. After these operations,
capture accounting() and closure_failures for hand_result. Their two totals end
at this pre-publication cut, before hand_result construction/serialization/write.
Cut-time success requires hand_complete, a settlement, complete accounting and
no failure. A required-operation failure prevents further input or ordinary work.

Publish hand_result once inside owned_publication(publication, body_failure=...).
Its interval includes frame construction, serialization and the single full-count
binary os.write. There is no buffered flush and no stdout close at this point.
This public duration stays separate from the two cut-time totals. A failed hand
may attempt measured terminal reporting only while runtime.measurable remains
true; otherwise skip it and report failure through the closing report if possible.
owned_publication has no required flag: gate apparently successful publication on
measurable both before entry and inside the context after entry, and independently
retain whether the complete frame was written. An entry fault cannot permit an
unmeasured successful hand_result merely because the context body still executes.

Exit that interval, call finalize_accounting, then read closure_failures and
accounting again. Do not infer closure from absence of an exception: the APIs can
record failure and return normally. terminal_publication_compute_seconds is the
sole returned duration when len(publication) == 1, otherwise null. The final
accounting_complete comes from the post-finalization accounting().complete.
No query or repair of a failed witness is allowed; use only the public reports.

Construct and emit session_result as separately declared closing-report transport
outside the closed hand accounting, following ADR-0485's host-receipt boundary.
Do not measure a receipt for this receipt. A completed status requires successful
cut-time hand_result, independently known full terminal publication, exactly one
valid publication duration, final complete accounting and no retained failure.
Exit 0 additionally requires one full-count write of session_result and no later
required host error. Short/failed output is not retried. Failure to deliver the
closing report leaves completion unestablished; retain nonzero exit and stderr
diagnostics when possible, even if an earlier frame claimed completion.

All protocol writes use binary unbuffered os.write; descriptor setup precedes
ready. Do not add an explicit stdout close that can hide the closing report.
The caller retains the bytes and exit outcome. Failure reports preserve the
first cause followed by later genuine causes; an earlier delivered action and
its valid timing remain binding. No partial output proves its own durable receipt.

## Source and import admission

Adapt the existing adapter's small raw-object preflight into this tool, pinned
to base 5f90279. Cover every src/pontius blob, both existing v0a tools and this
new tool. Require inherited bytes to equal base, the new tool to be the sole
addition in that inventory, and executed files/directories to be regular and
non-reparse with no extra/cached package source. Use absolute PONTIUS_GIT,
scrubbed children, --no-replace-objects and --no-optional-locks for every Git
read, raw ls-tree/cat-file blobs, and the workflow's whole-row-sorted SHA manifest.
Admission precedes pontius imports; reject preloaded modules and origin drift.
The new tool must itself be tracked in the frozen candidate. No bypass flag.
Recheck HEAD/source at completion. This detects accidental source/import drift;
it does not defend against maliciously rewriting this tool and its checker.

Read the policy once into immutable bytes and decode with the existing codec.
No reload, table search or missing-policy fallback. Source/policy setup occurs
before ready/hand receipt. No concurrent source writer or synchronization is
admitted. Keeping all new production code in tools preserves the old adapter's
exact package-source inventory, which is an acceptance requirement.

## Acceptance examples and falsifiers

Use fresh correctness IDs and declared test inputs, never research artifacts.
The fixed examples are independently authored expectations, not generated goldens.

- Fold case: button 0, controlled seat 3, six stacks of 200, blinds 1/2, private
  cards Ac/Ad (48,49). A nonempty exact preflop blueprint raises to 8. Only after
  receiving that action, the caller sends folds from seats 4,5,0,1,2 in order.
  Pot is 5, payout (0,0,0,5,0,0), final stacks (200,199,198,203,200,200).
- Showdown case: same blinds/stacks/button/seat, controlled 3c/3d (4,5), board
  2h/5s/7d/Th/Ks (2,15,21,34,47). All seats call preflop (big blind checks),
  then check each street. Declared ranks in seat order are (4,5,3,0,2,1),
  consistent with test-only hands QQ, AA, JJ, 33, 99, 88 on that board.
  Seat 1 receives 12; final stacks (198,210,198,198,198,198). The runtime never
  receives those opposing private hands. A preflop table call and three missing
  postflop keys exercise one table hit and three passive checks.
- Repeated-action case: the fold case's first raise-to-8 is followed by seat 4
  raising to 16, then folds from 5,0,1,2. The bot calls on a fresh wall. Board
  (0,13,22,31,47) is revealed in street chunks and both live seats check each
  street. Host ranks (null,null,null,0,1,null) award seat 4 the 35-chip pot,
  consistent with test-only Kc/Kd against the bot's Ac/Ad. Final stacks are
  (200,199,198,184,219,200). Five bot decisions: one hit and four defaults.
  Existing all-in/side-pot suites remain regression evidence.
- Exercise malformed families: every missing/extra field, bool/numeric confusion,
  floats/constants, duplicate members, invalid UTF-8/BOM/CR, byte cap +/-1, missing
  LF, depth failure, card overlaps, wrong actor/street/index, premature showdown,
  caller-controlled action, extra hidden/future data, stale/illegal policy and EOF.
- At int_max_str_digits=640, accept a legal 640-digit total and serialize its
  independently expected settlement. Reject total == 10**640 and greater during
  hand-start admission, including six individually valid 640-digit stacks. Also
  reject 641-digit input tokens. No global decimal-limit relaxation is permitted.
- Independently enumerate exact fields for ready and all other output types,
  including the raw artifact digest; reject missing, unknown or mistyped members.
  Observe positive non-action preparation, terminal bookkeeping and separate
  publication duration through real public accounting and the child output.
  A deliberately omitted cost or fabricated zero must fail the consumer check.
  Inject entry/closing publication faults and a finalizer fault retained without
  an exception; require incomplete accounting and failed/nonzero completion.
  Distinguish a valid duration from full write success. Cover failed/short final
  receipt delivery, unavailable/null measurements and ordered reporting faults.
- Use the real child pipe and inherited runtime. A fresh test caller must wait
  for action/result output before constructing/sending the next event. Show that
  changing admitted policy bytes changes the response without Python edits.
- Controlled delay between receipt and decoding must enter the response wall.
  Check 14s and 15s and one ns on each side, repeated actions and non-action
  preparation, decoder failure/cleanup faults, and no ledger/sample backdating.
  Use deterministic test clocks only in tests; production uses the real witness.
- Observe actual pipe bytes/counts independently for full, short and failed
  delivery; post-write clock failure cannot erase known delivery. A deliberately
  bad duplicate write, late clock start or false zero exit must fail the consumer
  check. Inject only the named delay/fault, not the runtime/OS outcome oracle.
- Check changed/extra source, raw commit/blob replacement and import origin;
  the real boundary checker must reject an extra tool or forbidden import. The
  existing hand-adapter CLI and source checks still pass at the new source tree.

Acceptance uses fresh D-local snapshots, 3.11.15 then 3.14.6, -B -P,
snapshot-root cwd/src and scrubbed environment with absolute PONTIUS_GIT.
The companion proposal names the finite suites and stop conditions. No test,
timing observation or feasibility execution is claimed by this design.
