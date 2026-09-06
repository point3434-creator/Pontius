# Watch-first table session: design r002

Status: proposed design only. Task: v0a-table-session-design/r002. Tier C.
Base: fa28d191143586dee682b2726fb8cac253ab49f5. No source or operating authority.

## Components and reuse

One new tool separates source admission, schedule validation, a one-hand caller,
session transitions, immutable display projections and terminal rendering. Reuse
the sealed host through its public Source, OwnedInput, TableInput, Table, Failures,
ChildConnection, WireConsumer and HostRefusal definitions, plus checked_path,
decode_json, require and constants INPUT_VERSION and PROTOCOL. Use public attributes
and methods only; no monkeypatch/subclass replacement of production host behavior.

The session caller composes the same ready/start/exchange/next/complete/final-check/
finish sequence as the host CLI. It adds cross-hand transitions and display calls,
not another betting engine, wire interpreter, native owner or policy selector.
No terminal operation occurs inside a bot action-selection call. Each hand gets a
new Table, Failures, ChildConnection and WireConsumer. A single admitted Source and
its Modules are reused: Source construction after Pontius import would refuse.
Check Source again at every hand boundary and at the inherited pre-success cut.

## CLI and owned schedule

CLI flags: --session, --blueprint and --session-id required; --auto optional;
--format text|json defaults to text. No abbreviations. JSON requires --auto, with
no stdin reads. Text starts the first hand after admission, then prompts between
hands unless --auto. --help prints ordinary help without importing host/game code
or launching a child. Invalid CLI syntax exits 2 with argparse usage on stderr;
it does not claim a session result. All accepted invocations follow the result rules.

Session and blueprint paths are absolute regular non-reparse D-local paths with
regular non-reparse ancestors. Own bytes and identities via the inherited OwnedInput:
session at most 16384 bytes, blueprint at most 1048576 bytes. Keep them open only for
the inherited bounded reads; retain owned raw bytes and identity checks. Revalidate
both before every launch, after each hand and before final session success/stop.

Session JSON has exactly version, button, controlled_seat, starting_stacks,
small_blind, big_blind, opponents and hands. Version is pontius-v0a-table-session-v1.
hands is an ordered list of 1..16 objects, each exactly private_hands and board_runout.
No hand supplies stacks, button, policy, expected results, paths or code. Other fields
have the exact inherited TableInput domains. Decode strict UTF-8 with no BOM/CR,
duplicate/extra members, floats/nonfinite or bool-as-integer; depth <=8, integer
tokens <=7 digits. Validate every deal before launching the first hand. Each has
17 distinct exact card IDs 0..51 under the existing SixSeatHoldemDeal contract.

For validation, construct each inherited table input from common configuration,
the current starting stacks/button and that hand's deal. Its version remains
INPUT_VERSION. Canonical derived table bytes are compact sorted-key UTF-8 JSON plus
one LF, created in memory. They are not written to temporary table files. Validate
each eventual carried-stack configuration again with TableInput before use.
Decode the single owned blueprint with the admitted modules.codec; reuse its immutable
value/digest and pass the original owned artifact path to each fresh real child.

Session ID: pontius-v0a-table-session-v1-correctness- plus 1..40 ASCII letters,
digits, underscores or hyphens. For one-based hand ordinal k, derive the host-style
ID pontius-v0a-table-host-v1-correctness-<suffix>-h<k:02d>. Derive its child ID using
the unchanged event-interface correctness prefix plus table-<suffix>-h<k:02d>.
The suffix remains inside the inherited 48-character maximum. Never reuse a hand ID
inside a session. These source-correctness IDs grant no operating invocation.

## Source admission before loading the host

Require Windows CPython, -B -P, absolute regular non-reparse sys.executable and
PONTIUS_GIT, snapshot-root cwd and the new tool at its exact cwd/tools path. Use
absolute Git, --no-replace-objects/--no-optional-locks, scrub inherited Git/Python/
Pontius overrides, bound Git commands at 30 seconds and never resolve Git via PATH.

Before any host/game import, bind actual HEAD, this new tool's raw HEAD blob and
working bytes, and tools/v0a_table_host.py to both its current raw blob and sealed
blob 0faa101f9be9940f9ae935df51f8c79e2eeb2b15 at the base above. Check regular paths
and ancestors before/after reading, with identity/content equality. Reject preloaded
Pontius modules or the fixed host module alias. Do not accept arbitrary module paths.

Execute only those verified host source bytes with compile/exec in a fresh
types.ModuleType named pontius_v0a_table_session_host, registered in sys.modules
for dataclass resolution. Set __file__ to the admitted host path and __package__
to the empty string. Do not invoke an import loader that might read a .pyc cache.
This is the sole fixed sibling-source execution; it is not a general plugin loader.
Then construct Source and call Source.load once. Its existing raw full-package,
four-tool and delayed module-origin checks remain authoritative and unchanged.
The new tool does not directly import Pontius or access a private host/CPython field.

Revalidate HEAD/new-tool bytes, fixed host binding, inherited Source and both inputs
at every prelaunch/posthand/final boundary. Do not trust a prior hand's validation
after a terminal prompt. A changed input, source or failed read stops before another
launch and cannot leave the final session marked successfully completed/stopped.

## Hand and session state transitions

Session owns initial stacks, current stacks/button, next ordinal, completed hand
records and at most one active hand. The complete schedule stays in this dealer layer.
Before each hand: check admission and stack eligibility, then create derived input,
fresh Table/Failures/connection/consumer and wait for matching ready. Run the inherited
public loop; consumer.exchange applies actual bot actions exactly once. Append-only
Table.applied_actions remain the source of semantic action history on every path.

consumer.complete supplies only provisional settlement. Perform all final source/input
checks, invoke connection.finish with the appropriate success flag, and require an
empty failure ledger, actual child exit 0 and complete capture before accepting it.
A constructor HostRefusal may carry its already cleaned connection; retain its real
capture/exit just as the sealed CLI does. Always call finish for an owned connection,
including renderer errors and observable KeyboardInterrupt. Preserve the host's typed
HostRefusal/Failures outcomes, including construction and finish; never inspect an
exception's cause to relabel an inherited failure. The sealed owner may consume an
interrupt and expose only its phase or cleanup_failed. The caller cannot recover
that cause and must report the inherited failure with exit 1. No new signal observer,
handler, global cancellation hook or sealed-host change is introduced.
Append interrupted only for KeyboardInterrupt actually escaping to this caller.
Keep the earliest observed failure before later distinct cleanup/interruption faults;
never create another child after the hand is unsuccessful. Always retain the actual
connection captures, exit and action prefix regardless of the typed classification.

After full success, append the complete hand record, carry its verified final_stacks
and advance button=(button+1)%6. This commit precedes rendering the settled result;
a later display failure does not erase the successfully completed hand. An unfinished
hand has settlement null and never updates carried stacks or button. Preserve its
entire applied prefix, including actions applied before a diagnostic rejection.

After rendering a completed hand: schedule exhaustion takes precedence and yields
completed. Otherwise any current stack < big_blind yields stopped/insufficient_stacks.
Otherwise automatic mode proceeds or text mode prompts. No child/job remains active
while waiting between hands. Enter or n starts the next hand; q or EOF stops normally.
Read at most 8 bytes for one input line. Accept only LF or CRLF variants of empty,
lowercase n or q, and empty bytes for EOF. Any other/overlong command stops with
command_invalid, without draining additional input or launching. Input read errors
are input_failed. Ctrl+C observed here appends interrupted and never resumes. No retry.

Stop state includes the last completed stacks/button and count, not a hypothetical
completion of the interrupted hand. No rebuys, seat removal, stack reset, automatic
restart or attempt to run a below-minimum six-seat table. The inherited per-exchange
60-second and whole-hand 300-second diagnostic watchdogs remain unchanged. Rendering
time consumes the existing whole-hand wall; between-hand prompts own no child wall.
No new operating timing credit or liveness guarantee for a blocked output peer.

## Visible updates and text behavior

Use a frozen display value composed only of primitive values/tuples: hand ordinal,
button, bot seat, bot's two formatted cards, street, currently visible formatted
board, six current stacks and a tuple of newly applied actions. Each action copies
index, seat, street, kind, raise_to and origin from the accepted host row. No Table,
deal, schedule, connection, mutable record, opponent hole cards or future board is
passed to the renderer. Format cards through admitted modules.cards.format_card.

Emit a hand heading/own cards before the first exchange. After each successful
exchange, project the bot's current public view and only actions beyond the display
cursor. Render street/board changes and actual actions in index order; the cursor
advances before attempting publication so partial writes are never retried. Do not
call next_event while an update is being rendered. A later exchange failure retains
the remaining applied prefix in the failed hand record; print those remaining rows
as applied-before-failure only after cleanup, if the output stream remains usable.
Never print provisional payouts, raw transcripts, diagnostic paths or future cards
in normal text. Display final payouts/stacks only after successful hand acceptance.

Normal text includes hand k/N, button and bot seat, cards, public street/action lines,
settled payouts/stacks, between-hand prompt and a final completed/stopped/failed line.
Use ordinary ASCII text and existing card formatting; no terminal escape/control
sequences or screen-clearing. Error text identifies the typed reason and says the
hand/session stopped. Text ordering/visibility are normative; decorative wording is
not a byte-stable certificate. Each encoded line <=4096 bytes, total text <=4194304
bytes. Publish each line once using os.write and require the exact requested count.
Short/failed output means output_failed and no further ordinary output attempts.

## Structured result and failure meaning

The session runner returns a result independent of rendering. JSON mode suppresses
all live text/prompts and emits one compact sorted-key UTF-8 LF JSON result at end.
Closed root members: version, session_id, status, stop_reason, failure_reason,
secondary_failures, source_commit, input_sha256, blueprint_artifact_sha256,
blueprint_sha256, requested_hands, completed_hands, next_button, carried_stacks, hands.
Version is pontius-v0a-table-session-result-v1. Hashes are established SHA-256 or null;
source_commit is actual HEAD or null; requested_hands is an integer 1..16 or null
before schedule admission. next_button and carried_stacks are null before admission,
then the current integer button and six integer stacks, initially from configuration.
completed_hands starts at 0; hands starts empty. IDs are strings, hashes lowercase
hex strings, failure/stop reasons strings or null, secondary_failures a string list.

Each hands entry has exactly ordinal, button, starting_stacks and result. result has
version pontius-v0a-table-session-hand-result-v1 and the existing table-result member
set and field semantics from ADR-0497/0498, with the derived host-style session ID,
raw child captures, retained actions,
actual exit and capture flag. Its input_sha256 binds the canonical derived table bytes,
not an invented on-disk file. This caller constructs the same projection from public
host values; it does not claim the sealed CLI emitted it. This new version additionally
admits interrupted as a failure reason; output_failed already belongs to the host.
Per-hand status remains completed or failed. ordinal is one-based, button an integer
0..5 and starting_stacks a six-integer list matching that hand's validated input.
The session-level interrupted status distinguishes deliberate cancellation. No hand
entry exists until its validated configuration/Table exists; a later launch failure
produces one failed entry. At most one failed entry exists, always last.

status is completed, stopped, failed or interrupted. completed means every requested
hand completed, no stop/failure and final revalidation passed. stopped means a clean
quit/eof/insufficient_stacks stop between hands, final revalidation passed and no failure.
stop_reason is respectively null, quit/eof/insufficient_stacks, or null for failures.
failed/interrupted have a non-null failure_reason; no failed hand settlement is carried.
Set status interrupted exactly when the first failure is interrupted; an interrupt
after an earlier failure remains secondary and status failed. First failure wins;
later distinct failures are ordered secondary_failures. Inherit the host vocabulary and allow
command_invalid, input_failed and interrupted at session level. No failure is silently
converted to a clean stop. A drift check after a chosen quit makes the session failed.

An observable interrupt before hand acceptance marks that hand failed with its prefix,
subject to the first-failure rule. An observable interrupt after acceptance preserves
that completed hand and appends interrupted to the session. Internally consumed
interrupts retain the host's classification and cannot be advertised as recognized
cancellation. In particular, finish converting an interrupt to cleanup_failed means
failed/cleanup_failed and exit 1, unless another failure was already primary.
No failed hand carries settlement, including this case. CLI exit: 0 for completed/
stopped, 1 for failed, 130 for interrupted;
CLI syntax errors remain 2. Constructing/encoding/publishing the final JSON is capped
at 67108864 bytes including LF. One os.write must return the full length; otherwise
exit 1 and emit only bounded stderr "REFUSED output_failed" if possible. Never retry
the JSON or claim a full receipt from a short write. Text final publication failure
also exits 1. Session output is a diagnostic summary, not an evidence/training store.

## Finite controls, falsifiers and alternatives

two_hands.json repeats the sealed passive showdown deal twice, initial six stacks
200, button 0, controlled seat 3, blinds 1/2, five passive opponents and the unchanged
empty blueprint. Each hand has board [0,5,10,19,24] and hole pairs [48,49], [44,45],
[40,41], [36,37], [32,33], [28,29] by seat. Every seat contributes 2 and seat 0 wins 12.
Expected completed stacks: [210,198,198,198,198,198], then
[220,196,196,196,196,196]. Buttons 0 then 1, next button 2. First preflop actor changes
from seat 3 to seat 4; the second hand's bot acts as the big blind. Require independently
enumerated full action histories, distinct child IDs and actual child exits.

below_blind.json repeats the sealed side-pot deal twice with initial stacks
[4,8,12,12,12,12], button 0, bot seat 3, shove_once seat 4 and passive elsewhere.
Only hand one runs: pots 24/20/16 yield [24,20,16,0,0,0], then a clean insufficient_stacks
stop with completed_hands=1 and next_button=1. No second process is created.
Inputs contain no expected actions or payouts. Existing empty blueprint fixture is reused.

Other finite controls: empty/n/q/EOF/invalid/overlong between-hand commands; automatic
versus interactive game-result equality; hidden-pair/future-hand permutations leave
earlier visible output identical; refusal on source/blueprint/schedule drift between
hands; malformed/late child failure retains prior completed hands and active prefix;
controlled observable KeyboardInterrupt and renderer failure after a real action invoke
real cleanup; actual native root/descendant handles establish exit before any prompt
or next launch; partial terminal publication is not retried. Use inherited transport
as production, never fake its successful resource effects. Timing triggers may be
injected at the explicit command/render/public-exchange seams, not replace action or
cleanup contracts. Additionally schedule an asynchronous KeyboardInterrupt while the
unchanged finish performs its real wait/cleanup, with an actual child still owned.
Assert the inherited cleanup_failed classification, exit 1, retained actions, null
settlement, unchanged carried stacks/button and no next launch; retain native root/
descendant handles and independently establish termination. Pair with a genuine
non-interrupt native cleanup fault and the same real termination oracle. A test may
cause that fault by closing the actual public job resource at a declared boundary;
it may not replace finish, process wait, job membership, termination or their outcomes.
Also cover an earlier protocol/output failure followed by observable cancellation,
and observable cancellation followed by a cleanup fault: primary/secondary ordering
and exits must differ as specified. Constructor HostRefusal retains its inherited
phase/secondary reasons even if its exception cause was KeyboardInterrupt. No cause
introspection or blanket cleanup_failed-to-interrupted conversion is permitted.
No new native implementation or broad duplicate native suite.

A reset-stack, stationary-button, early-next-launch, provisional-settlement or leaked-
deal consumer must fail independent controls. Real CLI schedules and captured terminal
I/O establish the externally visible behavior. Pure projections alone are insufficient.

Chosen route: in-process composition of fixed admitted public host definitions.
Launching its CLI only supplies end-of-hand JSON and adds another lifetime boundary;
copying/replacing the host duplicates a sealed mechanism. A human seat adds action
input and human-wait semantics the controller explicitly deferred. No generic policy
framework, learner, terminal UI dependency, persistent session store or operating
owner belongs here. Source admission, mutation/cleanup ordering and private projection
are the principal review risks; the companion proposal freezes the exact opening.
