# Paired evaluation source contract

Normative only upon adoption of ADR-0508. Base B is
e043f81ecec3ac16128720b42c3312bb41a4ed67. This opens a correctness-only source
increment; implementation, source acceptance and population execution are distinct.

## Exact source surface

Create tools/v0a_evaluation.py and tools/v0a_evaluation_contract.py. The first owns
CLI/admission/native orchestration and retained publication; the second owns pure
canonical schemas, matrix planning and observable-report reduction. No src addition.
Create tests/test_v0a_evaluation_contract.py, tests/test_v0a_evaluation_runner.py,
tests/test_v0a_evaluation_boundary.py and tests/fixtures/evaluation/controls.json.

The six current-file exceptions below are limited prospective supersessions of
CLAUDE rule 1. Verify each B blob before its first edit; no other current file changes.

- tools/check_stabilization_boundaries.py
  B blob: 9cc2ae8d8e82ccc77648ade4eb79ae9c34c88a9f.
  Register two exact tool origins and their bounded imports/loaders only.
- tools/generate_test_inventory.py
  B blob: 2ac1413b0f89fa848f1ee5df0814b58dcbfa15b8.
  Register three new CPU suites only.
- tests/test-inventory.json
  B blob: c28445aa4b77a98cfd706672d955be4570b98a15.
  Mechanical regeneration, preserving old IDs/records.
- tests/test-profiles.toml
  B blob: 4469bf813b2e97116667c206784a7bc212f6eef5.
  Mechanical new membership, preserving old order/grants.
- tests/test_inventory_and_profiles.py
  B blob: e71a24322878361fb2feb44437d9210cff79c89e.
  New registration expectations and mechanically derived census values only.
- .github/workflows/ci.yml
  B blob: 3d873a2f75ff1b155bf3533583eddf971eb7790a.
  Three explicit CPU suite steps; preserve old gates.

All game/provider/source-admission code, old source pins, policies, fixtures and
historical decisions remain byte-identical. In particular preserve:

- tools/v0a_seeded_deals.py: 2963004e38c6e66f76ae9ce3bd474063eee870fe.
- tools/v0a_table_session.py: a5e058260fa56e29f06e38074d59dc55f420c5ee.
- tools/v0a_table_host.py: 6ec8a162b053158203663c48e82314b10750f962.

The old session's literal host pin is unchanged. No tests/test_v0a_table_session.py
exception is opened. Historical rehearsal owners remain consumed/closed; no source
manifest or correctness identifier transfers a scientific or operational authority.

## Public request and matrix

CLI: -B -P tools/v0a_evaluation.py --request ABS --output-root ABS
--evaluation-id pontius-v0a-evaluation-v1-correctness-SUFFIX.
SUFFIX is 1..16 ASCII letters/digits/underscore/hyphen. No default seed, random API,
resume, force, retry, policy loading, table overlay or alternative output-root option.
The source snapshot cwd is D-local; the output root must be absent, non-reparse and
disjoint from source and request. A source-valid invocation consumes its new root.

Canonical UTF-8 compact sorted-key JSON plus one LF, no BOM/CR/duplicate/unknown keys,
no floats, bool-as-int or nonfinite constants. Request cap 4,096 bytes, depth at most
4, integer tokens at most 8 digits. Its exact field set is:

version seed deal_count lineups seat_start initial_button total_budget_ms trial_budget_ms

- version = pontius-v0a-evaluation-request-v1.
- seed = 64 lowercase hex characters, externally saved before any evaluation cards.
- deal_count: exact int 1..4. seat_start and initial_button: exact int 0..5.
- lineups: list of 1..4 distinct lists, each five strings from the existing four
  opponent policies. List order is meaningful; do not sort lineups or their members.
- trial_budget_ms: exact int 1..3,600,000; total_budget_ms: exact int 1..86,400,000,
  with total_budget_ms >= trial_budget_ms + 5,000. No operating adequacy is inferred.

For d=0..deal_count-1, l in request lineup order, r=0..5: p=6*(d*L+l)+r,
s=(seat_start+r)%6, b=(initial_button+d)%6. Generator deal_for_hand(seed,d) fixes
physical private pairs and board. For j=0..4, opponents[(s+1+j)%6]=lineups[l][j];
opponents[s]=null. All stacks are 200, small_blind=1, big_blind=2.
Canonical pair input uses version pontius-v0a-table-session-v1 and exactly one hands
entry. Both strategies consume the same saved pair input bytes. Never rotate the
button with r, rotate the cards, carry stacks or change a lineup inside a pair.

Pair order is d/l/r. Strategy order is baseline then blueprint when p is even,
blueprint then baseline otherwise. Unit ordinal u=2*p+a+1 for ordered arm a=0,1.
At most 96 pairs / 192 trials. The exact plan is fixed before any trial starts.
Session suffix is eval-SUFFIX-uUUU with three-digit u; its prefix is
pontius-v0a-table-session-v2-correctness- for baseline and
pontius-v0a-table-session-v1-correctness- for blueprint. The existing session derives
the corresponding host/event IDs and -h01 suffix. No identity of an old owner is used.

Each child vector is exactly -B -P tools/v0a_table_session.py --session PAIR_INPUT
--blueprint SNAPSHOT/tests/fixtures/table_host/empty_blueprint.json --session-id ID
--strategy STRATEGY --format json --auto. No child sees request/seed or all-pair plan.

## Admission, resources and source loader

The evaluator requires actual Windows CPython 3.11+ with -B -P and its exact tool
path under the D-local snapshot. Acceptance uses actual 3.11.15 then 3.14.6. Reject
preloaded pontius or fixed helper aliases before loading. Native executables/inputs
and all ancestor directories are regular/non-reparse and have stable read identities.

Admit every tracked src/pontius blob plus tools/v0a_rehearsal_driver.py,
tools/v0a_hand_adapter.py, tools/v0a_event_adapter.py, tools/v0a_table_host.py,
tools/v0a_table_session.py, tools/v0a_seeded_deals.py, and the empty blueprint against
their exact B raw blobs. Reject added/missing src Python/source paths, not just edits.
Both new tools must equal current HEAD raw blobs; their exact two-name population is
part of the manifest. Current commit, raw byte identity and path identity must hold
before helper loading, before/after each child and before final publication. Manifest
rows use sorted whole digest/two-space/POSIX-path/LF bytes. No replace objects or PATH Git.

The wrapper source manifest is distinct from child source_manifest_sha256. Derive
the latter exactly as accepted host.Source does: whole-row hashes over all tracked
src/pontius blobs and the unchanged hand adapter, event adapter and rehearsal driver;
exclude table host, table session, seeded generator and both new tools. Compare child
ready/decision manifests with that derived value, not with the wrapper manifest.
Root/nested/ready/decision provider configuration and blueprint policy digests must
agree under their versioned field names; raw empty-blueprint artifact hash is pinned
independently. The fixed admitted child source establishes their semantic identities.

Raw-load only the three exact verified tool files: contract helper, seeded generator,
and host, into distinct fresh fixed aliases. Host use is limited to Job and its native
ownership operations; generator use is deal_for_hand. These fixed exec/compile routes
must operate exclusively on the admitted captured bytes, never arbitrary input paths.
Do not instantiate Source/Table/Session, call game loaders, or import pontius in the
parent. Child source admission remains untouched in its separate interpreter.

Contract tool import allowlist: __future__, base64, hashlib, json, math, re.
CLI tool allowlist: __future__, argparse, ctypes, hashlib, json, os, pathlib, re,
stat, subprocess, sys, threading, time, types. No external or optional dependencies.
Boundary tooling registers only these two origins/allowlists and named loader edges;
existing graph, SCC, origins, analyzer inference and dynamic-route restrictions remain.
Static loader checks are bounded structural controls, not a general soundness claim.

Child environment keeps SystemRoot, WINDIR, SystemDrive, COMSPEC, USERPROFILE, APPDATA,
LOCALAPPDATA only, then sets task-local TEMP/TMP, native absolute PONTIUS_GIT,
PYTHONPATH=SNAPSHOT/src, PYTHONNOUSERSITE=1, PYTHONIOENCODING=utf-8. Same interpreter
as the wrapper. Never inherit arbitrary GIT_/PYTHON/PONTIUS_ values.

Reuse the accepted host Job: create suspended process, assign before resume, contain
all descendants, and refuse on containment failure. Register Job/process/streams and
capture threads immediately, before later fallible work. Drain raw stdout/stderr in
parallel. Per-trial caps: 4 MiB stdout and 64 KiB stderr; retain at most those bytes,
flag overflow and stop the Job. Capture storage is bounded by the planned 192 trials,
not claimed as an aggregate disk or process-memory guarantee. Child stdout base64
decodes to at most 2 MiB and stderr to 64 KiB; frame bytes at most 16,384 each.

One monotonic total deadline begins before card/plan generation. Whole trial budget
plus 5,000 ms cleanup reserve must fit before each launch; the same deadline covers
all arms/seats/lineups and final publication commit verification. Trial deadline covers
startup, capture
and validation. On expiry/interrupt/failure, stop the Job, wait for inactive status
under a 5,000 ms cleanup grace, close resources, retain any unknown/cleanup failure.
Never launch another trial after such a stop. Grace grants no extra payload work or
late success. OS calls can block; no universal hard wall or calibrated ceiling is claimed.

## Retained files and publication

Use create-only reservation.json, request.json, plan.json and per-pair input files;
per-unit uUUU directories contain intent.json, stdout.bin, stderr.bin and result.json.
Flush intent before process creation. Record exact argv/environment/source/input
identities, launch status, actual exit or null, capture completeness, timing and causes.
Root or file collision refuses and preserves all existing state. No retained-file deletion,
root recovery, concurrent runner or automatic resumption. At first non-success trial,
stop all later units. A prelaunch failure leaves later units explicitly unstarted.

Use canonical JSON for plan and wrapper records with exact typed versions. The plan's
exact fields: version, request_sha256, source_commit, source_manifest_sha256,
blueprint_artifact_sha256, pairs, units. Each pair: pair_index, deal_index, lineup_index,
rotation, controlled_seat, button, input_path, input_sha256. Each unit: ordinal,
pair_index, strategy, session_id, input_path, input_sha256. Paths are root-relative
POSIX strings from the fixed layout only. plan version is pontius-v0a-evaluation-plan-v1.

Result version is pontius-v0a-evaluation-result-v1. Exact top-level fields: version,
evaluation_id, status, comparison_complete, source_commit, source_manifest_sha256,
request_sha256, plan_sha256, planned_pairs, completed_pairs, planned_trials,
completed_trials, trials, pairs, aggregate, failure_reason, secondary_failures,
total_elapsed_ns, deadline_met, evidentiary. Status is completed/failed/interrupted;
evidentiary is false. Internal reservation/intent/result records use separate v1
versions. reservation.json fields are version, evaluation_id, request_sha256,
source_commit, started_ns, deadline_ns; version is pontius-v0a-evaluation-reservation-v1.
Each intent fields are version, ordinal, pair_index, strategy, session_id, argv,
environment, source_commit, source_manifest_sha256, request_sha256, input_sha256,
intent_ns, trial_deadline_ns; version is pontius-v0a-evaluation-intent-v1.
An additional create-new launch.json records version, ordinal, pid, created_suspended,
assigned, resumed; version is pontius-v0a-evaluation-launch-v1. Emit it after successful
resume; a missing launch record after intent is unknown launch, never retry authority.
Trial result.json is the trial-summary field set below plus version, launched,
cleanup_complete, primary_phase, secondary_failures and elapsed_ns; its version is
pontius-v0a-evaluation-trial-v1. launched is true/false/null (null is unknown), and
cleanup_complete is exact bool. Do not turn an unknown launch into unstarted state.
These coordination fields create no alternative launch or success authority.

Before any root final result/completion file, create an exclusive empty directory
.publication-pending. No consumer accepts a root while any object has that name.
Create-new result.json, write/flush/close it, then reread and byte-compare it. Create-new
completion.json with exact fields version, status, result_sha256, result_bytes,
prepared_elapsed_ns, deadline_met; version is pontius-v0a-evaluation-completion-v1,
status is completed, deadline_met is true. Write/flush/close and reread/byte-compare
completion too. Revalidate both files, all identities and source, then check the shared
monotonic deadline. All operations through this final check must succeed within it.
That check is the irreversible publication commit. No serialized timestamp claims to
measure this later check: prepared_elapsed_ns measures marker preparation; result's
total_elapsed_ns measures result preparation. Both are prefix diagnostics only.

Only after commit, remove the empty .publication-pending directory once. This is the
sole permitted removal, an ephemeral publication resource release; every retained file
and consumed root remains. Release is postcommit visibility work, outside the deadline.
Thus verification commits by the deadline; visibility and CLI return may occur later.
This is not a visibility-by-deadline, hard-wall or crash-durability guarantee. No later
error revokes the committed result. If release fails and the guard remains, consumers
refuse; if an ambiguous release removed it, the previously verified commit is consumable.
Do not retry release, recreate the guard, recover a root or overwrite any record.

The public read_completed(root) predicate requires absent guard, regular/non-reparse
stable result/completion files, exact schemas and identities, exact result hash/size
binding, and an all-complete result with deadline_met=true. Recheck guard absence and
file identities after reading. Exit status and file existence alone confer nothing.
This assumes the admitted cooperative sole writer; external deletion/fabrication or
power-loss durability is not certified. No consumer may bypass this predicate.

| Phase | Required operation | Failure/interrupt/late outcome |
| --- | --- | --- |
| Pending | Create guard before either final file | No consumable output |
| Result | Create/write/flush/close/readback/compare | Retain guard and any bytes |
| Completion | Create/write/flush/close/readback/compare | Retain guard and any bytes |
| Verify/commit | Validate both files/source; final clock <= deadline | Retain guard unless all pass |
| Release | Remove empty guard once, only after commit | Present guard refuses; absent guard exposes committed bytes |

Precommit incomplete roots may retain failed diagnostic JSON without consumable success.
Never rewrite a partially published file to say failed. Return CLI 0 after successful
release, 130 on interruption, 1 on other errors. A postcommit release error/interrupt
is a visibility/CLI outcome, not retroactive invalidation; consumer standing is as above.

## Report extraction and honest denominators

Outer/nested session and wire field sets are the exact accepted B v1/v2 schemas,
documented in design.md and the implementation plan. Version dispatch, duplicate-key
rejection, depth/byte limits, exact integer/bool types and finite floating timings
are required. Bound outer JSON nesting to 16 and decoded frame nesting to 8, with
integer tokens at most 640 digits, as in the inherited wire decoder. Do not import
source codecs to bypass clean parent admission. Successful frame captures must have
one opening ready, ordered event/action correspondence, one terminal hand_result and
one closing session_result with no trailing partial/extra frames, and all identities
and counters must match the public report and host-applied actions.

For a complete trial require exact identity/strategy/source/blueprint/input matches,
exit 0, status completed, one requested/completed hand, nested completed status,
child exit 0, no capture truncation, no primary/secondary failures, valid settlement,
session/hand final-stack equality and integer chip conservation at 1,200. Verify the
nested table-input digest by canonical one-hand-to-table conversion, not session hash.
Verify all action ordinals and the origin/controlled-seat relationship. Accepted host
source establishes legality/settlement; this observer does not replace it with a solver.

Each trial summary has exact fields ordinal, pair_index, strategy, state, exit_code,
capture_complete, report_complete, net_chips, applied_actions_by_kind,
baseline_fallback_selections, baseline_fallback_applied, legacy_choices,
unattributed_applied_actions, work_cutoff_actions, action_deadline_actions,
observation_complete, action_failures, failure_reason, hand_failure_codes,
session_failure_codes,
capture_deficiencies, stdout_sha256, stderr_sha256. state is
unstarted/refused/failed/interrupted/completed. Unknown scalar metrics are null;
unstarted capture hashes/exit are null. Observed action counters in incomplete rows
are explicit prefixes; observation_complete=false. Net chips requires complete trial.

Applied bot action counts use host applied_actions where origin=bot. Baseline fallback
selections use valid v2 decision.selection_origin=blueprint_fallback, grouped by
selection_reason; applied fallback matches the nth decision to the nth host bot action
and exact action value. Legacy choices count table_hit/passive_default separately.
Unmatched applied actions increment unattributed_applied_actions; absent/invalid records
never imply zero fallback. Group work_cutoff_crossed and deadline_crossed independently
by (child hand_id, action_index), coalescing decision/failure duplicates. Conflicting
duplicate observations are a report refusal, not arbitrarily resolved.

action_failures is null when no valid wire observation is available; otherwise it is
a list of observed action-failure objects, possibly empty. Exact object fields:
hand_id, event_index, action_index, code, delivery_status, sources, standing.
Use the immutable B failure schema's identity/code/delivery types and domains, including
its permitted null hand_id, event_index and action_index. Null identity remains
unattributed; no concrete action or multiplicity is inferred from it. sources is an
ordered nonempty subset of
[decision, failure], naming the v2 event_result.decision.failure_reason observation
(with that decision's identity/delivery/timing fields) and event_result.failure.
V1 failed events require null decision under the accepted host contract; they use
the failure source only. Do not invent a decision.failure object or v1 delivery fields.
standing is unverified_prefix for any failed/incomplete trial; no assertion that the
host accepted a failed prefix is permitted. Completed validated trials have an empty
list. Derive observations only from schema/identity-valid event rows; a malformed row
adds a capture deficiency and grants no inferred action failure. Null/missing failure
where a failed event requires it adds missing_action_failure and incomplete coverage.

Deduplicate fully identified observations by (hand_id, event_index, action_index, code),
retaining first wire order. Null-identity observations coalesce only matching copies
within the same event_result frame; never merge unknown identities across frames;
merge matching decision/failure copies by sources. Conflicting identity/code/delivery,
delivered_action or timing between present copies refuses the report with a deficiency;
never choose a convenient copy or count them as two incidents. Multiple codes at one
action across conflicting repeated rows are deficiencies, not distinct valid incidents.
Preserve schema-valid observations preceding a later malformed/unknown row as an
unverified prefix. An empty observed list with observation_complete=false means no
failure seen in that prefix, never proof that no action failure occurred. Missing,
invalid or truncated coverage cannot become observation_complete=true or zero metrics.
Hand/session cause arrays retain their own propagated codes independently. Do not put
action codes into those arrays or label a valid observed action cause a capture defect.

| Metric/output | Authoritative source for complete rows | Incomplete/missing meaning |
| --- | --- | --- |
| net_chips, pair delta, aggregate | Validated host settlement, full fixed denominator | Null score; no survivor aggregate |
| applied_actions_by_kind | Host applied_actions with origin=bot | Explicit observed prefix or null |
| baseline fallback selections/applied | V2 decision origin/reason; exact nth bot-action match | Missing attribution retained, never zero by default |
| legacy_choices | V1 table_hit/passive_default decisions | Separate prefix or null |
| work_cutoff_actions, action_deadline_actions | Per-action deduplicated wire timing flags | Prefix only; outer timeout supplies neither |
| action_failures | Valid event decision/failure observation objects | Explicit unverified_prefix; null or incomplete empty list is unknown |
| hand/session_failure_codes | Respective public report scope | Code presence only, no inferred action cause |
| capture_deficiencies | Observer's schema/identity/coverage checks | Missing/invalid coverage, distinct from observed action causes |

Baseline reasons: provider_selected, provider_abstained, provider_error, provider_invalid,
provider_late, provider_skipped_cutoff. Outcomes: not_called/proposed/abstained/error/invalid.
Legacy decisions have no provider fallback origin. Baseline proposal is never an applied
action count. host_limit and wrapper timeout remain transport/resource causes; they are
not invented action-clock deadline events. Hand/session cause arrays count code presence
at that scope; no total incident multiplicity or causal ordering is claimed.

A failed capture's valid-looking frame prefix remains unverified: byte/schema/identity
checks only establish an observed prefix, not that the host consumed/accepted every row.
No paired scoring from failed/refused/stopped/partial/unknown cases. Preserve malformed
tails and repeated/unknown rows as capture_deficiencies; expose no raw cards in summary.

Each pair row: pair_index, complete, baseline_net_chips, blueprint_net_chips, delta_chips.
Incomplete pair scores/delta are null. Aggregate is null unless every planned pair and
trial completed with full required observations and successful cleanup/publication.
Complete aggregate fields: baseline_net_chips, blueprint_net_chips, delta_chips,
mean_delta_numerator, mean_delta_denominator, by_lineup, by_seat. Mean numerator is
summed pair delta; denominator is planned_pairs. Group rows use the same five numeric
fields plus lineup_index or controlled_seat. All sums are exact integers; no rounding,
confidence interval, statistical winner, generalization or strategy-selection claim.

## Finite correctness population and acceptance

controls.json contains at most two manually specified distinct full deals, synthetic
valid/invalid session-report and wire examples, and literal request vectors. No random
sampling or entropy. Pure planner/reducer tests may use those full deals directly.
One named all-zero-seed generator vector may exercise the complete public pipeline
only after adoption; it is a correctness vector, never an evaluation population.
Maximum actual poker session starts across all new suites: 24 per complete suite-set
execution. At most one full 12-trial matrix uses the generator vector; other native
controls use finite non-poker subprocess fixtures or at most 12 additional sessions.
Record exact fixture counts and new test IDs at freeze. No suite discovery/wildcard runs.

Contract controls: strict request/type/size/depth/unknown/duplicate/lineup/cap refusal;
all six seats, all positions, original physical cards, deterministic order and identical
pair hashes; independent integer/rational arithmetic; mismatched/partial/failed pairs;
legacy vs baseline fallback, unmatched applied actions, propagated timing deduplication,
host timeout distinction, schema/capture/identity refusal and no hidden-card summary.
Include delivery_rejected with no timing flags and propagated child_failed at both
hand/session scopes: preserve one unverified action cause, both scoped causes, and no
pair score. Cover decision/failure duplicates, permitted null index, conflicting
copies, missing/invalid failure and truncated prefix. Deliberately dropping, scope-
folding or double-counting the action cause must fail the independent reducer check.

Runner controls: one complete 12-trial real public matrix, exact reset/input/source/
strategy/namespace/argv/env binding, retained intents/captures, and independently
calculated summary arithmetic. Native non-poker fixtures exercise suspended assignment,
overflow of both streams, partial final JSON, timeout, interrupt and descendants.
Use the real Job/process/file/publication path; injected children test wrapper resource
handling and malformed report admission, never certify poker or fabricate a successful
engine oracle. Child descendants must actually be observed stopped on overflow/timeout.

Boundary controls: absent-root reservation collision; raw source, request, plan and
pair-input drift before/after a trial; extra src paths; missing/cached helpers; invalid
Git/interpreter/env/module origins; full trial cannot fit; exact deadline edges using
a deterministic clock seam; final short-write/readback/flush/completion failure;
real completion write/close delayed beyond deadline and close failure after full bytes;
partial/interrupt and normal publication; delayed/failed/ambiguous empty-guard removal.
The public read_completed predicate must reject every precommit failure despite a
parseable complete marker, without overwrite/retry. Postcommit controls separately
verify guard-presence refusal and valid release of already committed bytes, with no
visibility-by-deadline claim. A prepared timestamp cannot certify a later check.
stop-before-later-units and retained unknown launch/cleanup outcomes. A deliberately
wrong matrix/scoring/publication behavior must fail an independent real contract check.

Source acceptance after two fresh Tier C CLEAN reviews runs these exact commands on
actual 3.11.15 first then 3.14.6, each fresh exact-candidate D-local snapshot, -B -P,
scrubbed env, snapshot cwd/src, origin checks and absolute native Git:

```text
-m pontius.status_generation --check
tests/test_status_generation.py
tools/check_stabilization_boundaries.py
tools/generate_test_inventory.py --check
tests/test_inventory_and_profiles.py
tests/test_v0a_evaluation_contract.py
tests/test_v0a_evaluation_runner.py
tests/test_v0a_evaluation_boundary.py
tests/test_seeded_deals.py
tests/test_seeded_deals_boundary.py
tests/test_v0a_table_host.py
tests/test_v0a_table_host_boundary.py
tests/test_v0a_table_session.py
tests/test_v0a_table_session_boundary.py
tests/test_decision_provider_session.py
tests/test_decision_provider_transport.py
```

Existing unchanged CI gates remain. Compare complete B/candidate analyzer output on
both interpreters before census refresh; preserve every old assertion, test ID, payload
order, grant and inference. Account mechanically for all new records and source-line
shifts. Unexplained drift or a needed new capability/analyzer repair stops for a separate
ruling. No weakening a census gate. Production/test/registration budgets and round
ceilings are those in the brief and ADR-0508; source seal is a later exact decision.
