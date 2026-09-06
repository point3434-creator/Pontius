# One-hand reactive table host: design r001

Status: proposal only. Task: v0a-table-host-design/r001. Tier C.
Base: 1329c2c201bbf2f396946f2ebf460ee944ae4ece. No source implementation yet.

## Components and future reuse

One new tool contains a strict input decoder, a pure table/seat-controller layer,
a child connection and the CLI result renderer. Separate named classes/functions
for these responsibilities; no terminal I/O inside table or opponent selection.
The host imports public game/card/model/trace payload helpers after source checks.
It does not instantiate HandRuntime, import a replay fixture/host or call policy
lookup to predict Pontius's answer. The actual child action drives the host.

Future terminal controllers and sessions can reuse this table layer. A future
neural engine requires its own versioned runtime integration; no general policy
plug-in framework or training collector is introduced here.

## Input and finite domain

CLI: --table, --blueprint and --session-id only, no abbreviated flags. File paths
are absolute regular non-reparse D-local paths with regular non-reparse ancestors.
Read and own bytes once before launch; reject path/source changes on final check.
Table size is at most 16384 bytes; blueprint size at most 1048576 bytes. Read one
byte beyond each cap to detect overflow. These bound this correctness interface;
they are not measured operating budgets or a change to the artifact format.

Table JSON has exactly version, button, controlled_seat, starting_stacks,
small_blind, big_blind, private_hands, board_runout and opponents. Version is
pontius-v0a-table-input-v1. There is no hand ID, timestamp, expected result,
future action script, code path, model path or arbitrary controller object.
Admit strict UTF-8, no BOM/CR/duplicate keys/nonfinite/float/extra members; integers
have at most seven decimal digits and exact bool is never an integer. All chip
values are positive, at most 1000000 and starting chip sum is at most 1000000.
The existing six-seat kernel additionally requires every stack >= big blind and
0 < small blind < big blind. Exact integers identify button/controlled seat 0..5.

private_hands is six two-card arrays and board_runout five cards, all 17 distinct
exact IDs 0..51. Validate with owned tuples and SixSeatHoldemDeal. opponents has
six entries: null at the controlled seat, otherwise one of passive, fold_to_bet,
min_raise_once or shove_once. No missing or extra slot. The owned raw table hash
identifies the input. The blueprint uses the unchanged public codec; invalid
matches remain runtime failures, never host-side policy repair.

Host session ID is pontius-v0a-table-host-v1-correctness- plus 1..48 ASCII letters,
digits, underscores or hyphens. Derive child ID as the existing event-interface
correctness prefix plus table- and that suffix. Every event uses that child ID.
Only the named finite correctness tests are admitted by this source task.

## Table state and opponent decisions

NoLimitBettingState is the authoritative host table. Construct it from the table
input, separately from the bot. Keep OneSeatCardState per seat for observations;
the complete deal remains only in the dealer. A selector receives its own seat
view, immutable public betting state and kernel-derived legal decision, not the
table/connection/deal object. Controllers cannot emit events or change stacks.

passive chooses check, else call, else fold. fold_to_bet checks if possible,
otherwise folds. min_raise_once raises to the legal minimum on its first action
of each street if raising is legal; all other choices are passive. shove_once
raises to the legal maximum on its first action of the hand if legal; all other
choices are passive. Determine first action from that seat's existing public
history; posted blinds are not actions. No local mutable strategy counters,
strength evaluation, hidden opponents or future board inspection is needed.

After ready is validated, send hand_started with only the bot's two cards. For
each event, first derive the host's state after the event and before any bot
action. That state determines whether precisely one action is expected. Apply
the received action once, immediately after schema/identity/legality validation;
append an applied-action record before any subsequent protocol step can fail.
Wait for its matching event_result before selecting the next opponent action.
Diagnostics never count as instructions. When no bot action is expected, require
an accepted event_result with null decision/failure and reject any action frame.

When an opponent acts, choose from its current observation, apply through the
host kernel, and send the corresponding opponent_action event. Only non-controlled
seat actions are sent this way. Bot actions are never echoed as opponent events.
Use contiguous event indexes from zero and contiguous bot action indexes from one;
maintain the controlled street-action index, reset only on a real street change.

On a complete nonterminal betting round before river, advance exactly one street,
update permitted card views and send only newly public board cards. Repeat even
when all live players are all-in and the next street has no actionable seats.
At a completed river, derive showdown strengths from the dealer's actual cards,
advance the host to showdown and send those ranks for exactly the live seats.
On a fold terminal, send no ranks or extra reveal. No future board is inspected
by an opponent selector. Limit each hand to 256 events and 256 applied actions;
exhaustion is a typed host limit failure before another event/action is applied.

## Source and process boundary

Before importing Pontius, validate Windows CPython with -B -P, actual absolute
regular non-reparse sys.executable, absolute PONTIUS_GIT, actual HEAD and raw Git
blobs. Inherit exact src/pontius and the three sealed tools from the base above;
the only new inventoried source is tools/v0a_table_host.py. Validate working bytes,
directory population, absence of caches/reparse paths and delayed module origins.
Never follow replace refs, filters or archive conversions. No source hash inferred
from filenames. Registration files are outside the runtime source inventory.

The child event adapter remains byte-identical; its own inventory contains all
src/pontius plus its three named tools, so the new host tool is outside that
inventory. Compute its expected source-manifest hash from exactly that subset.
Require ready source_commit to equal actual host HEAD, its source manifest to
equal this independent computation, and both policy hashes to equal the owned
artifact and decoded policy hashes. Revalidate source and the two input files
before successful host completion; changed data or failed reads reject success.

Create an unnamed, non-inheritable Windows job using ctypes and set only
JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE; do not permit breakaway. The host remains
outside its own job. Launch one fixed cooperative bootstrap using the validated
interpreter, -B -P -S -c, no shell, CREATE_NO_WINDOW and close_fds=True. This
bootstrap imports only os/sys, waits for exactly one release byte, then executes
the fixed admitted event-tool path through runpy with its fixed CLI arguments.
No arbitrary script, executable or bootstrap text comes from table input.

Assign the child to the job before sending the release byte. Use the live owned
CPython Popen._handle only for AssignProcessToJobObject, not a reopened PID. This
one Windows CPython handle dependency is explicit and covered on both slots.
The child cannot execute bot code or create its Git descendants before release.
Do not claim the OS created the child inside the job atomically: the cooperative
bootstrap is the pre-assignment gate. On failed assignment, never release it;
kill and reap the blocked child. Missing APIs or incompatible outer job policy
are typed refusals, not a fallback to uncontained execution.

Create the child with binary unbuffered stdin/stdout/stderr pipes. Its cwd is the
snapshot root. Clear the environment and restore only Windows essentials,
TEMP/TMP, required user/profile paths and validated PONTIUS_GIT; no inherited
GIT_ or PYTHON overrides. -S prevents site startup hooks; the event tool itself
admits/imports its snapshot source. No extra Pontius module is preloaded.

Use one daemon stdout reader, one daemon stderr reader and one serialized daemon
stdin writer. Read bounded byte chunks; a stdout LF frame is at most 16384 bytes.
Queue at most eight complete frames and one pending write; overflow is a retained
failure. Capture raw stdout up to 2097152 bytes and stderr up to 65536 bytes.
An over-limit stream sets a truncation flag and fails; it is never reported as a
complete transcript. Thread errors enter a shared first-failure record. Only the
main table loop mutates game state or applies actions.

After job assignment, each startup/event/closing exchange has one absolute
60-second monotonic deadline that covers writes and reads together. A hand has
an absolute 300-second limit from child launch; use the earlier deadline.
Partial bytes and unrelated frames never reset either deadline. Reaping and
each cleanup/join phase have a five-second bound. These are diagnostic host
watchdogs, not new action-clock budgets or scheduling guarantees; the child's
14-second work cutoff and 15-second response wall stay unchanged.

On the first host failure, retain its code, stop sending events, terminate the
job, wait for the root process and query until job ActiveProcesses is zero or
cleanup expires. Join readers/writer after pipe closure caused by termination;
all waits are bounded. On success, require child exit zero, pipe EOF, no residual
frame/partial bytes, no truncation and no active descendant before closing the
job handle. Close owned handles in finally; kill-on-close remains the final
containment backstop. A cleanup failure is secondary to the original cause and
prevents success. Do not retry the child or reapply any accepted action.

Windows basis: Microsoft Job Objects and Nested Jobs document descendant job
inheritance, kill-on-close and nested-job limits:
https://learn.microsoft.com/en-us/windows/win32/procthread/job-objects
https://learn.microsoft.com/en-us/windows/win32/procthread/nested-jobs
The cooperative gate and cleanup effectiveness require native tests; documentation
alone is not claimed as an executed lifecycle result.

## Wire acceptance and terminal result

Decode stdout as strict UTF-8 LF JSON with no CR, duplicate/extra/missing members,
BOM or nonfinite numbers. Floats are permitted only in the inherited timing
fields and must have exact float type, be finite and nonnegative. Exact integers
are required elsewhere, never bool. All frames have the exact protocol/session
and member sets frozen by ADR-0495's design; preserve those shapes verbatim.
Bound integer tokens to 640 digits, nesting to the finite known schema, and
validate every consumed field before arithmetic or table mutation.

Only ready may appear first. For each event, allow the one expected action then
its matching decided event_result, or the accepted event_result without action.
Reject duplicate/missing/unsolicited actions, any failure result and any terminal
frame before the host reaches terminal. Retain raw failure frames even when their
shape is invalid; do not need to interpret malformed diagnostics to reject them.

For a decided result, require the exact public DecisionRecord payload shape and
valid enum/type domains. Require matching hand/event/action/street/seat IDs,
selected action, blueprint hash, host-computed public state-before/state-after
hashes and visible-card hash. Preparation must be producer_absent, empty artifacts
and zero credit. Require no failure, completed timing, null interruption, exact
nonnegative timestamps, elapsed = emission - start, last observation = emission,
both cutoff/deadline flags false and elapsed <= 15000000000. Require finite
nonnegative response components whose sum differs from elapsed/1e9 by <= 2e-9.
This is a consistency tolerance for public float fields, not a new timing credit;
no host measurement certifies the child's response clock or proves a work cutoff.
selection_reason/spine_reason are diagnostic admitted enums; do not rerun policy.

Require exactly one successful hand_result and then one completed session_result.
hand_result must have complete/accounting_complete true, interrupted count zero,
empty secondary failures, null primary failure, finite nonnegative preparation
and terminal totals and evidentiary false. rank_source is not_required for fold
and host_supplied for showdown. Its exact payouts, final_stacks and ordered pot
amount/eligible-seat lists must equal the host kernel's settlement projection.
session_result requires the inherited accounting_scope, accounting_complete true,
finite nonnegative publication duration, null/empty failure fields and evidentiary
false. A good hand_result cannot override a later failed session, exit or cleanup.

The host writes one LF JSON result to stdout, with exactly version, session_id,
status, failure_reason, secondary_failures, input_sha256, blueprint_artifact_sha256,
blueprint_sha256, source_commit, applied_actions, settlement, child_exit_code,
child_stdout_base64, child_stderr_base64 and capture_truncated. Version is
pontius-v0a-table-result-v1; status is completed or failed. Applied-action rows
contain contiguous index, seat, street, action and origin (bot or opponent).
Settlement is null unless the complete host acceptance conjunction succeeds;
otherwise it contains payouts, final_stacks and pots. Failed reports preserve
all successfully applied actions; they never suggest rollback or hand completion.
Hashes not established before refusal are null, child_exit_code is null before
launch or when reaping fails. Raw captured prefixes are Base64, not decoded or
silently truncated text. capture_truncated is an exact bool for either stream.

Host failure vocabulary: input_invalid, source_invalid, process_start_failed,
containment_failed, transport_failed, protocol_invalid, action_invalid,
state_mismatch, settlement_mismatch, child_failed, host_limit, cleanup_failed,
output_failed. Retain first occurrence before cleanup and ordered later distinct
occurrences. A malformed child result is protocol_invalid; a valid failed child
result/nonzero exit is child_failed. A failed report write yields nonzero exit
and bounded stderr refusal if possible. Successful complete output and exit zero
are both required by the caller. No persisted trace, strength or timing result
is claimed. Raw transcript capture supports debugging, not an independent trace
certificate. No hard liveness claim is made for an arbitrary blocked output peer.

## Finite controls and falsifiers

New fixtures are fold_table.json, showdown_table.json, sidepot_table.json and
empty_blueprint.json. Existing event-adapter fold blueprint is reused unchanged.
All tables use button 0, controlled seat 3, blinds 1/2 and board [0,5,10,19,24].
Default six hole pairs by seat are [48,49], [44,45], [40,41], [36,37], [32,33],
[28,29]. This board gives no straight or flush; those pairs rank AA > KK > QQ >
JJ > TT > 99. No expected ranks, actions or payouts appear in the input fixtures.

Fold control swaps seat 0/3 hole pairs, uses six stacks of 200, the existing
fold blueprint and five fold_to_bet opponents. Bot raises to 8; all others fold.
Uncalled excess is returned: pot/payout to seat 3 is 5, final stacks
[200,199,198,203,200,200]. The revealed board remains empty.

Showdown control uses the default pairs, six stacks of 200, empty blueprint and
five passive opponents. All contribute 2 and check through the board. Seat 0
wins 12; final stacks [210,198,198,198,198,198]. Every street is revealed once.

Side-pot control uses default pairs, stacks [4,8,12,12,12,12], empty blueprint,
shove_once at seat 4 and passive elsewhere. After the bot's first call, seat 4
raises to 12 and all six eventually commit their full stacks. The bot responds
again on the same street. Pots are 24 for seats 0..5, 20 for seats 1..5 and 16
for seats 2..5; AA, KK and QQ win them respectively. Payouts/final stacks are
[24,20,16,0,0,0]. All-in streets reveal without artificial check actions.

Additional finite test variations: swap two hidden opponent pairs while keeping
the bot observation unchanged; a policy change from raise to call changes actual
opponent action choices; tie/odd-chip settlement with separately hand-calculated
expectations; each opponent rule's unavailable-raise fallback and first-action
boundary. Test source/input drift, false hashes, cached/wrong imports, bad types,
illegal/missing/duplicate actions, post-action failure and mismatched state/pots.

Use real native pipes/job membership for launch gate, child plus Git-like
grandchild lifetime, stalls before/after partial output, reader/writer failure,
output overflow, timeout and cleanup refusal. Controlled schedules may affect
only the fixed test bootstrap, queue/I/O trigger, native API failure result,
child output fields or monotonic watchdog source; native ownership, process exit,
pipe bytes and kernel action effects claimed by each test must remain real.
Do not substitute a fake successful job for containment evidence. No sleep-based
performance claim; use bounded synchronization barriers and explicit failure
observations. A wrong consumer that double-applies, accepts wrong state/payout,
ignores closing failure or exposes the complete deal must fail the independent
control. Future implementation receipts, not this design, establish coverage.

## Alternatives, risks and stop boundaries

An in-process host would avoid pipes but fail to exercise the new usable external
boundary. A generic policy framework would postpone completion without a second
engine. A new src/pontius package would violate the accepted source inventory.
The additive tool is the smallest compatible next integration surface.

Native ownership/pipe cancellation, schema drift, and shared-kernel oracle bias
are the main risks. Actual 3.11/3.14 checks and independent arithmetic controls
are required. The transport is not a throughput-ready training worker. No new
operating owner, human session, random population, policy tuning or cleanup of
historical work is admitted. Exact source-opening and review budgets are in the
companion proposal. Stop rather than silently widening a failed boundary.
