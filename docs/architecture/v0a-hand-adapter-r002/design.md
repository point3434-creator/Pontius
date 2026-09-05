# One-hand file adapter: design r002

Status: proposed, not an implementation, source opening or invocation authority.
Input: this packet's brief.md; base 7a387e995e3b37232d2379332927247a4d49c64e.
Tier C. This is a narrow host-side interface, not a new poker engine.

## Goals, coverage and deliberate exclusions

Meet the brief's six criteria with a strict scenario decoder and one CLI entry.
The existing driver is intentionally limited to two fixtures and an empty policy;
the artifact codec already accepts portable nonempty policies. This adapter joins
file inputs to the existing APIs without copying or modifying their semantics.

Coverage is the closed schema below, its literal-card adapter, the named public
CLI path and its final acceptance conjunction. The finite controls are declared
in the acceptance section. They are not a proof over every legal poker history,
all filesystem schedules, arbitrary resource usage or adversarial Python mutation.

No training, policy selection, random deals, opponent strategy, interactive play,
multi-hand campaign, benchmark, GPU dependency, new trace schema, transaction
implementation, source-analysis framework or operating/rehearsal mode is designed.
The CLI executes declared correctness cases only under scoped test authority;
choosing that mode does not authorize experimental use or revive a consumed owner.

## Components and dependency direction

New package `pontius.hand_scenario`, with inert __init__.py and codec.py:

- `decode_scenario(raw: bytes) -> HandScenario`, a pure byte-to-value operation.
- `ScenarioError(ValueError)`, a typed all-or-nothing admission refusal.
- `HandScenario`, a frozen value carrying one exact existing Fixture and an
  immutable ordered tuple of expected controlled-action rows.

The codec performs no file I/O, runtime dispatch, clocking, imports selected by
input, network or subprocess operation. Its internal imports are only
`pontius.holdem_cards`, `pontius.v0a.model` and `pontius.v0a.replay`. Standard-library
imports are only __future__, dataclasses and json. It is explicitly host-side:
the unchanged runtime, policy and blueprint codec never import it or receive it.

`tools/v0a_hand_adapter.py` owns source preflight, input reads, one host call,
readback/verification and stdout. Internal imports are exactly
`pontius.hand_scenario.codec`, `pontius.blueprint_artifact.codec`,
`pontius.v0a.replay` and `pontius.v0a.trace`, delayed until source preflight passes.
Allowed direct standard-library imports: __future__, argparse, hashlib, io, json,
os, pathlib, re, stat, subprocess, sys and tarfile. No parent re-export, dynamic
module loader, callback, plugin, runtime-to-host edge or dependency installation.

## Closed scenario schema

Decode exact bytes as strict UTF-8 JSON, no BOM. Reject duplicate member names
at every depth (including escaped aliases), unknown/missing fields, floats,
nonfinite values, malformed encoding, trailing data and excessive nesting with
ScenarioError. Standard JSON whitespace and object ordering are permitted.
Never coerce a bool to an integer or traverse a foreign object graph.

The root has exactly these members:

| Member | Admitted value |
| --- | --- |
| version | `pontius-v0a-hand-scenario-v1` |
| case_id | the correctness identifier specified below |
| button, controlled_seat | exact integers 0 through 5 |
| starting_stacks | exactly six exact positive chip integers, each at least big_blind |
| small_blind, big_blind | exact positive integers, small_blind strictly less than big_blind |
| board | exactly five literal card strings in reveal order |
| hands | exactly six arrays, seat order, each exactly two literal card strings |
| opponent_actions | ordered array of the closed action records below; empty is permitted |
| expected | the closed expectation object below |

case_id is `v0a-hand-adapter-correctness-` followed by a nonempty suffix made
only of ASCII letters, digits, underscores and hyphens.

Cards are exactly two ASCII characters: rank in `23456789TJQKA`, suit in `cdhs`.
All 17 cards across board and hands must be distinct. Two-card private-hand order
has no semantic meaning; board order does. Reject duplicate cards before any host
is constructed. No undeclared opponent/future data is admitted in policy keys.

An opponent action has exactly street, seat, kind and raise_to. Street is one of
preflop/flop/turn/river; seat is an exact integer 0..5 other than controlled_seat.
Kind is fold/check/call/raise. A raise has a positive chip integer raise_to; every
other kind has JSON null. Street regression, wrong acting seat, illegal sizing,
missing actions and extra actions are semantic refusals through the real host
and independent reader, not repaired or truncated by the decoder.

The expected object has exactly payouts, pots and controlled_actions. Payouts
is six nonnegative exact chip integers. Pots is a nonempty array of positive
exact chip integers in the existing settlement's layer order. Controlled_actions
is an ordered array of objects with exactly street, kind, raise_to and
selection_reason; its action domains are as above, and selection_reason is
table_hit or passive_default. An empty array is permitted for a scenario with
no controlled turn. Its length becomes Fixture.expected_controlled_actions.
Expected actions/pots/payouts are declared by the scenario author, never calculated
by running the policy or copying its observed output. Incorrect expectations fail
the case; the adapter cannot rewrite them.

All chip integers are less than 10**640, and sum(starting_stacks) is also less
than 10**640. Every payout and sum(pots) must be at most that starting total;
their actual settlement equality is checked after replay. Limit integer tokens
to 640 decimal digits before conversion, then apply exact ranges. This carries
the existing codec's minimum-decimal-conversion compatibility boundary through
aggregate chip values; it is not an operational bankroll or memory budget.
Do not change process-global conversion settings. Catch conversion/nesting
errors as ScenarioError. Fixed tokens/IDs/cards are ASCII; no normalization.

## Literal cards across the sealed fixture boundary

The scenario file describes the actual cards to be dealt, not template cards.
Fixture.deal applies a disclosed suit permutation derived from seed_label. The
adapter must undo that representation transform when constructing the Fixture:

1. Use case_id as the fixture name and hand_id. Derive seed_label as
   `pontius-v0a-hand-adapter-v1/` followed by case_id, with no random seed or run ID.
2. Obtain the existing permutation_for_label result; invert its mapping from
   original `cdhs` suits to renamed suits. Rewrite only the literal card suits
   into Fixture.hand_text and Fixture.board_text using that inverse.
3. Construct exact ScriptedAction/Fixture values with the admitted script and
   expectations. Verify Fixture.deal's complete card values equal the literal
   file cards (private pairs compared unordered). Refuse any disagreement.

This does not change the existing suit algorithm or poker rules. Labels changing
the inherited permutation cannot change the file's actual deal. The policy is
decoded independently and its complete keys refer to actual, visible card values.
The full fixture/deal stays with ReplayHost and the independent reader; only
the sealed host emits public events and the controlled hand to HandRuntime.
Do not pass the fixture, script, expectations or the opposing cards to the policy.

## CLI, source identity and file boundary

The one entry is Windows-only under Python -B -P. Required arguments are
--scenario, --blueprint, --run-id and --run-root. It has no mode switch: the
existing trace mode is correctness, clock kind monotonic_ns. The run ID is
`pontius-v0a-hand-replay-v1-correctness-adapter-` followed by a nonempty ASCII
letter/digit/underscore/hyphen suffix. Other namespaces/modes refuse; this remains
non-evidentiary even when successful.

Require absolute D-local, non-reparse regular input files and an existing empty
non-reparse run-root directory whose basename equals run-id. Reject UNC paths,
parent traversal and a reparse component anywhere in each path. Run-root's only
adapter-created file is trace.jsonl, written by the existing TraceWriter through
ReplayHost. Inputs are read once to immutable bytes, hashed and decoded before
host construction or trace creation. Never overwrite, move or delete input/output.
Caller keeps the input bytes for later verification. This is no standalone
archive guarantee or defense against a concurrent writer; require no concurrent
writer or sync during the invocation, as the existing driver does.

Before importing pontius, reject a preloaded pontius module and establish the
actual source identity using an absolute regular/non-reparse PONTIUS_GIT. Scrub
GIT_*, PYTHON* and PONTIUS_* variables from the Git child. Every initial and final
Git identity/object command must explicitly use --no-replace-objects, after the
scrub and before the subcommand. This covers HEAD resolution, commit/tree reads,
base comparisons, inventories, blob reads and final revalidation. A caller's
GIT_NO_REPLACE_OBJECTS value must not be the mechanism: the scrub removes it.
Use the same raw-object mode in every phase; replacement refs cannot define an
executed-source identity. Read Git objects without checkout changes, hooks or
subprocess shell interpretation. Resolve HEAD once to
a full commit; inspect source blobs and a source inventory from that same commit,
not a caller-selected source path, mutable branch lookup or caller-provided hash.
Derive inventories from raw ls-tree data and bytes from cat-file blob using those
object IDs, under --no-replace-objects. Git archive output is not a raw identity
oracle: attributes may transform or omit its content. Ordinary checkout content
or filtered/archive views cannot substitute for the requested raw blob bytes.

Require the inherited src/pontius package to equal the pinned base, with exactly
the two new hand_scenario paths permitted as additions. Require the new adapter
and original driver bytes in the checkout to equal that commit's blobs; require
the original driver also to equal the base blob. All actual src/pontius files and
directories are non-reparse; reject missing, extra, modified or cached files.
The two new source files and adapter must be tracked in the resolved commit.
Pin every inherited package blob against the base; do not weaken the old driver's
af90155 preflight or call it on the enlarged package. No inherited byte changes.

Source manifest rows cover every executed-package source under src/pontius,
the new adapter and the unchanged original driver. Compute lowercase SHA-256
rows from the verified raw bytes, with two spaces, relative POSIX paths, LF,
and whole-row byte sorting, as in the workflow. Pass the actual resolved commit
and this manifest to ReplayHost and independently to the reader. Set the import
path to that checked snapshot/src; verify the four imported internal module
origins there. Revalidate source bytes and the resolved HEAD before a success
summary. A Git-consistent candidate is not by itself source adoption or authority.

This exact package check addresses accidental checkout/import drift, not a
malicious edit of the adapter and its check together. No broader integrity proof
is claimed. Tests freeze candidate source before CLI invocation, so a temporary
working overlay does not get a fabricated zero source identity or bypass flag.

## One execution and one acceptance boundary

After admission, call the existing ReplayHost once with the admitted fixture and
decoded policy, mode correctness and clock kind monotonic_ns. Persist trace.jsonl
through that host. Never retry, synthesize success or substitute a mailbox, clock,
settlement oracle or writer in the actual CLI.

Success is a conjunction, evaluated in this order:

1. The real host receipt reports passed and accounting_complete as exact True.
2. The persisted regular/non-reparse trace exists. Its raw bytes equal the host's
   returned trace and its SHA-256 equals the host receipt's trace hash.
3. verify_successful_trace accepts those persisted bytes against the separately
   held fixture, policy, actual source commit/manifest, correctness mode and
   monotonic clock kind. Both verified and host receipt run IDs equal --run-id.
4. Parse those same bytes with parse_trace and compare the complete ordered
   decision projection (street, kind, raise_to, selection_reason) to the scenario's
   expected.controlled_actions. The independent reader already compares declared
   payouts, pots and decision count with independent chip-depth/legal replay.
5. Source revalidation passes. Print exactly one JSON summary line and exit 0.

Summary fields: passed=true, evidentiary=false, mode=correctness, run_id, case_id,
source_commit, source_manifest_sha256, scenario_sha256 (raw input),
blueprint_artifact_sha256 (raw input), blueprint_sha256 (decoded policy),
trace_sha256, semantic_sha256, trace_path, actions (the verified projection),
table_hits, passive_fallbacks, payouts and final_stacks. Derive all hand values
from the persisted, accepted trace/reader, never from expectations or an unchecked
host object. JSON is UTF-8, sorted keys, compact separators, finite values, final LF.
No summary file, timing comparison, win-rate field or second report protocol.

Any admission/host/IO/source/readback/replay/expectation failure prints a typed
REFUSED category to stderr, exits nonzero and prints no success line. Retain any
trace/prefix exactly, even when the host trace itself says passed but the adapter's
additional checks fail. This distinguishes host completion from adapter acceptance;
do not rewrite a valid or failed trace. An output-write failure is also nonzero.
No exception from a failed phase can be replaced by a successful later phase.

## Acceptance map for implementation

Use fresh correctness-only IDs/data, not rehearsal or rejected research output.
Handwritten inputs and independently declared actions/chip arithmetic are the
oracles; tests exercise public decode and the real CLI/host/reader.

- Literal-card controls cover all 24 inherited suit permutations using fresh
  value-free labels; assert exact actual cards from fixed textual/numeric pairs,
  not just encode/decode agreement. Cover reversed private-card order, all four
  suits and duplicate-card refusal. Ground-truth card values are independently
  written, not emitted by the new conversion.
- A nonempty artifact selects a declared raise-to-6 at seat 3 from a 1/2-blind,
  six-by-200 preflop state; opponents 4,5,0,1,2 fold. Expected pot 5, payouts
  (0,0,0,5,0,0), final stacks (200,199,198,203,200,200), exactly one table_hit.
  Literal hands in seat order are As/Ad, Kh/Kd, Ts/8s, 2c/5c, Ah/3h, 4s/6s;
  board is 7c,8d,9h,Js,Qc. The fresh artifact's controlled private key is (0,12),
  not the old codec fixture's suit-permuted key (1,13). An independently authored
  nonmatching policy yields passive default in a separate appropriately declared
  case. An illegal matching raise refuses with no accepted action.
- A fresh showdown case uses 1/2 blinds, six-by-200 stacks, button 0 and controlled
  seat 3. Hands are Kh/Kd, Qh/Qd, Jh/Jd, As/Ad, Th/Td, 8h/8d; board is
  2c,5d,7h,9s,Kc. Everyone calls preflop (big blind checks), then checks every
  street. Seat 0 wins the 12-chip pot with three kings; payouts are
  (12,0,0,0,0,0), final stacks (210,198,198,198,198,198). The policy table hits
  the first controlled call; the next three controlled checks are passive defaults.
  This exercises street reveals, private-card separation and four decisions.
  Through the actual CLI, prove changing policy/scenario bytes changes bound raw
  identities and behavior without editing Python. A complete policy file is read,
  not selected through an extra Python fixture switch.
- Schema-derived corruptions cover every field/type family, duplicate names at
  every object level, unknown/missing fields, bool/integer confusion, floats,
  Unicode/BOM/encoding, card overlap, wrong lengths, enums, nullability, 640-digit
  boundaries including aggregate overflow, trailing data and deep nesting.
  Run scalar controls at normal settings and -X int_max_str_digits=640 on both slots.
- Wrong actor, illegal script size, street regression, missing/extra script rows,
  incorrect expected action/reason/count/pot/payout and incomplete hands cannot
  succeed. Changed expectations are not silently regenerated from actual output.
- Real file/CLI controls cover an existing output root, wrong namespace/root,
  missing/reparse input, missing Git, changed/extra source and import shadowing.
  Assert no output on pre-run refusal and preservation of every existing byte.
- In a disposable repository, HEAD names original commit O while refs/replace/O
  names commit R with changed adapter or scenario-code bytes; materialize those
  changed bytes without moving HEAD. The actual CLI must refuse before constructing
  a host, creating a trace or printing success. Also cover replacement of a source
  blob. Initial and final identity operations must retain raw-object mode. A
  replacement ref alone need not refuse if the actual bytes still match raw O;
  the protected fact is raw source identity, not a ban on unrelated refs.
- Controlled test seams after host completion and after trace persistence may
  corrupt the receipt or bytes, or alter one returned decision. The actual host,
  real file writes and independent reader execute. A deliberately bad success
  bypass must be detected by an independent exit/stdout/retained-trace check; the
  injector may not prevent the bad behavior before that check can observe it.
  State which schedules ran and limits; no OS allocator/timing claim follows.
- Invoke the real repository boundary gate against the exact proposed paths.
  Refuse an extra scenario sibling, forbidden incoming/outgoing edge, runtime
  access to the host-side scenario and an extra tool origin. Keep old gate failures.

Focused snapshot checks are the new decoder/adapter and boundary suites, floor
3.11.15 first then 3.14.6. After CLEAN review, use their union with unchanged
blueprint, v0a and direct CPU hard-gate suites, registration --check and the source
boundary gate; do not run guarded scientific profiles or install dependencies.
Use the current Windows fixture controls; no new ownership-fixture waiver.

## Alternatives, mistakes and stop rules

Rejected: modifying the sealed driver/runtime (unnecessary coupling and seal
changes); another launcher limited to the old two controls (no new capability);
an interactive/sampled opponent host (a larger game/operating boundary); and a
general schema/runner framework (more surface than this one format needs).

Easy mistakes are silently permuting literal cards, using full-deal data for
policy matching, accepting on host hashes alone, ignoring a stale expected action,
printing success after final verification fails, and broadening registration into
analyzer repair. Each invariant is applied at its decoder, caller, persisted-byte
reader and output boundaries where relevant, not just at one helper.

The only proposed capability is a declared one-hand correctness adapter. It
makes data-driven policy/hand development possible; it supplies neither a trained
policy nor the later operational launcher or H32 bridge. The brief's budgets and
stop rules bind. If the described seams need a sealed-core change, a third round,
extra module or wider authority, return before implementation expands. Design
review assesses feasibility and contract clarity; no executed behavior is claimed.

