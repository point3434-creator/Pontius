# Paired local evaluation loop: design

## Goals and comparison unit

The complete unit is a matched pair of independently reset one-hand sessions: one
baseline-rules-v1, one blueprint-v1. Both use the same canonical session input and
the accepted empty blueprint. A pair's chip delta is baseline controlled-seat net
chips minus blueprint controlled-seat net chips. There is no stack carry between
trials. A policy can therefore go all-in without removing later comparison units.

This first version reports exact integer sums and rational means over the complete
fixed matrix. It supplies no confidence interval, statistical significance, general
win-rate estimate, opponent-strength assertion or policy-selection recommendation.
Scripted opponents are explicit scenarios. Actual result collection requires a later
preregistration and invocation authorization; a correctness name grants neither.

## Population before outcomes

A canonical request supplies one retained external 32-byte seed, one to four deals,
one to four ordered five-opponent lineups, seat_start and initial_button, plus resource
caps. Allowed opponent strings are passive, fold_to_bet, min_raise_once and shove_once.
Repeated lineups refuse. The runner creates no entropy and offers no seed search.

For each deal index d, use the unchanged seeded generator's deal_for_hand(seed, d).
Keep its six private pairs in their original physical seats and its board unchanged.
For each lineup l and rotation r=0..5, controlled seat s=(seat_start+r)%6 and button
b=(initial_button+d)%6. Assign lineup[j] to seat (s+1+j)%6 for j=0..4, and null to s.
Thus all six relative positions and private pairs are covered; rotating button along
with the controlled seat would defeat this and is forbidden. Changing seat_start
only changes execution order, not the comparison population.

Enumerate pairs in d, l, r order. Let p be the zero-based pair ordinal. Even pairs
execute baseline then blueprint; odd pairs reverse that order. Input bytes are
identical inside each pair. This balances execution order without selecting outcomes.
Each trial starts with six 200-chip stacks and blinds 1/2. A one-hand session always
uses the existing v1 input schema, including when the selected strategy uses v2 wire.

Create the complete plan and one input per pair before any poker child. Retain the
request, seed-derived deals and input hashes locally. Plan/input publication errors
stop before play. A fixed seed is reproducibility, not proof of randomness quality.
The generated full deals never enter the provider observation or public summary.

## Source and native process boundary

Two new stdlib-only tools own the wrapper. v0a_evaluation_contract.py owns strict
request parsing, deterministic matrix expansion, report observation and arithmetic.
v0a_evaluation.py owns source admission, fixed loaders, retained files, process and CLI.
The old generator, host, session and all src/pontius bytes stay unchanged.

Before loading helpers or deriving cards, verify current tracked raw bytes for both
new tools and the entire inherited engine source closure. Old dependencies must also
equal their exact B blobs. The new tool bytes bind to the current candidate commit.
No preloaded pontius or helper aliases; no PATH Git; no import overlay. Validate native
regular non-reparse paths and repeat identity checks before/after every trial.

The parent raw-loads only three fixed verified tools into fresh private module aliases:
the pure contract, accepted generator and accepted host. It calls the generator's
deal_for_hand and host.Job only. It never constructs host.Source, host.Table or
Session, calls a private game loader, or imports pontius. Host module import is inert
stdlib definition loading; the separate session subprocess starts with a clean module
table and performs its own complete public admission. This avoids copying native Job
ownership code or weakening session admission to accommodate a preloaded evaluator.

Launch the current interpreter with -B -P and the unchanged session CLI in JSON/auto
mode. Cwd is the exact D-local snapshot; PYTHONPATH is its src, Git is absolute native
C:\Program Files\Git\cmd\git.exe, and environment follows the accepted allowlist.
Create the session process suspended, assign the accepted kill-on-close Job, then
resume it. Do not launch if Job creation/assignment/resume or source admission fails.
The Job contains session descendants, including nested host children. No breakaway.

Drain raw stdout/stderr concurrently into create-new files, with per-trial caps.
Stop the Job on overflow, deadline, interrupt or wrapper failure; preserve bytes
already captured and record the actual exit or explicit unknown. Wait for zero active
Job processes before successful cleanup. A cleanup failure remains a failure even if
the session produced a success report. Every resource is registered before the next
fallible operation; preserve primary and secondary causes.

## Whole-run budget and retained progression

The caller supplies total_budget_ms and trial_budget_ms. Neither is an admitted
operating budget or a performance claim. Correctness tests use literal finite caps;
a future population must justify its operational budget before execution.

Start one monotonic total deadline before plan generation. Before every trial,
require its complete trial_budget_ms plus the fixed cleanup reserve to fit. Check
again after source/input validation immediately before creating the suspended child.
The trial deadline includes startup, child execution, capture and validation; the
same total deadline also covers plan creation, reduction and publication commit
verification of both closed/read-back final files. Postcommit guard release and CLI
return may occur later; no visibility-by-deadline guarantee is made.
There is no reset when changing strategies, seats, lineups or deals. Deadline crossing
cannot be relabeled complete by a later report. Cleanup may continue after the budget
only to stop owned resources, retain an incomplete outcome or release the already
committed publication guard, never to launch more payload work.
Blocking OS/filesystem operations prevent a universal hard wall claim.

The output root is absent and create-new, disjoint from source and request paths.
Reservation consumes it. Copy request bytes, save planned inputs/identities, then
write/flush intent before each launch. Every trial gets its own raw captures and
result record. Stop on the first incomplete, stopped, failed or refused trial; do
not run a replacement arm or continue collecting selected successes. Missing final
publication leaves a retained incomplete root, never implicit success. No resume,
retry, root cleanup or adoption of an old result is provided.

Final result names every planned trial, including unstarted trials. Before either
final file, create an empty .publication-pending guard; its presence blocks consumers.
Create/write/flush/close/readback both result and completion, revalidate identities
and source, then check the shared deadline. All must pass before publication commits.
Any earlier error, interrupt or late check permanently leaves guard and files intact.
Only after commit remove the empty guard once as postcommit visibility release. This
single ephemeral-resource removal grants no retained-file or root cleanup permission.
Release errors do not revoke commit: a remaining guard blocks consumption; an absent
guard exposes the already verified files. No retry/recovery or guard recreation.
All consumers use read_completed: absent guard plus strict stable files, schema,
identity, hash/size binding and all-complete result. Neither CLI exit nor marker bytes
alone suffice. Preparation timestamps do not claim to measure later verification.
The source contract's transition table states the precise commit/visibility boundary.

## Facts, metrics and missing observations

Accept a trial for paired scoring only when exit is zero, captures are complete,
the exact session/hand schema and identities match, one hand completed, settlement
is consistent with session final stacks, and cleanup/source/input checks pass.
Check integer chip conservation and host-applied action ordinals/seats. Reuse the
host's successful report as the engine authority; do not claim a second poker solver.

Executed actions come from host applied_actions with origin bot, not provider proposals
or merely selected actions. Baseline fallback selections come from versioned decisions
with selection_origin blueprint_fallback. Link selections to applied bot actions by
per-hand controlled-action ordinal and exact action equality; retain unassigned applied
actions. Legacy table_hit/passive_default choices are separate counters, not provider
fallbacks. Missing or invalid decision records never become zero fallback use.

Raw child output is base64-encoded LF JSON frames. A failed capture may include rows
the host never validated. Record a strictly parsed observed prefix separately as
unverified/incomplete; do not treat valid-looking rows as a successful hand. Extract
only version/schema/identity-valid observations and preserve missing coverage.

Deduplicate timing observations by child hand ID and action_index because a decision
and its failure can carry the same timing. Keep work cutoff and action deadline flags
separate. A host_limit or outer timeout is not an action-clock deadline observation.
Cause lists give presence, not the number of all underlying incidents. Separate
trial status, hand/session causes, action failures and transport/capture deficiencies.
The exact action_failures channel retains event decision/failure causes, deduplicated
by hand/event/action/code with source labels. Failed-prefix observations stay explicitly
unverified even when schema-valid. Propagated child_failed cannot replace the underlying
observed delivery_rejected, and absent/invalid rows cannot prove zero action failures.
The source contract maps each output to its observation authority and unknown state.

All planned pairs must complete for the global comparative result. Otherwise chips
comparison and means are null, with completed-pair diagnostic rows retained. Never
silently divide by only the surviving rows or use zero for unobserved outcomes.
Reports omit hole cards and board runouts; raw inputs remain local retained artifacts.

## Alternatives and project fit

Carried multi-hand matches are useful product sessions but create policy-dependent
dropout and stack histories, so they are not the first comparison unit. Directly
calling Session would entangle admission/module state and native ownership; public
subprocesses preserve the existing boundary. A second poker simulator would duplicate
the established engine and oracle. New opponent policies and neural/self-play systems
would mix evaluation plumbing with behavior changes; they remain later increments.

The failure risks are population/order drift, selection bias from dropped failures,
mislabeling missing records, and orphaned descendants. Each has a direct fixture or
native-boundary check in the source contract. There is no redesign of game code,
action timing or transport, and no machine-enforced scientific authorization claim.
This asset makes future comparisons possible after separate authorization; it does
not itself open a population, infer an operating ceiling or promise a stronger bot.
