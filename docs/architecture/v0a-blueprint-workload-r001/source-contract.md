# Representative blueprint workload source contract

## Brief and acceptance map

Tier C. The protected contracts are source/input identity, truthful measurement
boundaries, complete denominators, real process ownership and action accounting.
This contract is prospective until ADR-0515's exact authorized decision commit.
Base B is `7242891bc8020d33737c3a027ef88d1b65bb2ace`, tree
`92c5f6d5637a342aeb38f5fffd540a27669dd27c`.

The controller-approved r002 design in `docs/superpowers/specs/` is the workload
specification. Its precise filename and raw digest are recorded in ADR-0515.
`execution-protocol.md` fixes invocation details; the implementation plan fixes
the task sequence and source gates. No result exists under this round.

Acceptance criteria:

1. Reproduce the exact seeded, reachable population recipe; refuse missing coverage.
   Reconcile encoded capacity and preserve independent query membership/order.
2. Measure the five direct operations, setup, memory and fresh/retained groups at
   their declared boundaries; validate exact outcomes outside measured intervals.
3. Observe real unchanged sessions; close exclusive parent spans and parse original
   child ledger records without double counting or shifting preparation into credit.
4. Emit a complete frozen case census and retained terminal for every admitted case,
   including interrupted, failed and unattempted cells. Refuse source/input drift.
5. Apply the prospectively fixed interpretation rules, sample eligibility and units.
   Wrong/missing data cannot become zero latency or an unqualified favorable claim.
6. Preserve all sealed runtime/history bytes and existing test assignments; register
   and run the new current controls on both supported interpreters.

Ground truth is the accepted kernel, artifact codec, legacy provider, host validator
and existing literal fixtures. New small literal controls use the author's explicit
enumeration, independently checked against those fixtures and legal transitions.
Agreement among consumers of the same kernel does not prove poker correctness anew.
The changed seams are recipe/artifact, direct ownership/cost, subprocess/native
containment, profiler/span reduction, ledger/report and source/test registration.
Only the next capacity/optimization decision waits on this work. Unrelated training
design remains independent. No playing-strength, production reuse or tail bound claim.

Plan four cohesive tools, roughly 900-1,400 tool lines plus 400-700 focused control
lines. This refines r002's 500-900-line estimate before implementation: a bounded
native supervisor and independent raw-result reader are needed in addition to the
measurement loops. Reuse the existing native Job and poker interfaces; do not build
a general experiment framework. Support larger than this narrow measurement surface
requires a written proportionality reassessment before further growth, not a new
after-the-fact test gate. One initial proposal plus at most two corrections, with
the workflow's earlier repeated-residual/design stop; a failed design is redesigned.

## Exact prospective exceptions

Only these B versions may change after opening adoption:

| Path | Raw B Git blob |
|---|---|
| `tools/check_stabilization_boundaries.py` | `67c3dd8e1e3ec0797b85a6c537fc6710e0646412` |
| `tools/generate_test_inventory.py` | `ff51ebd64521218ecfd3a8e6e898b14ca2794836` |
| `tests/test-inventory.json` | `faabbc9ef72aa11ee3b678730ae4663b04d5e58e` |
| `tests/test-profiles.toml` | `1210c43ef6aa8659cdabd1cb35089c13e0b82814` |
| `tests/test_inventory_and_profiles.py` | `d0aa8143725a0e13f692736fcd520bf8c03145e7` |
| `.github/workflows/ci.yml` | `977f4dfe63850775c60c676d7dba903e536dbed1` |

The boundary checker admits exactly the four new tool origins below. It adds only
their specific outgoing imports, fixed captured-source loader targets and incoming
edges to protected packages; keep all existing origins, constraints and refusals.
The launcher and report reader are standard-library-only. The population tool may
use `pontius.no_limit_betting`, `pontius.holdem_cards`, `pontius.immutable_blueprint`,
`pontius.blueprint_artifact.codec`, `pontius.decision_provider.model` and
`pontius.decision_provider.providers`. The measurement tool may additionally use
`pontius.blueprint_preparation.lookup`. Permit no production import of a new tool.
The only existing tool loader targets are the unchanged host, session and dealer.
New tools may load their exact named siblings. No arbitrary module/path/code loader.
No broad prefix permission or change to the dependency analyzer/baseline/SCC model.

The inventory generator registers exactly the four new suite paths as stabilization
current tests. Regenerate inventory/profiles with existing generators. Preserve all
3,180 old stable IDs, every old assignment, baseline lock, capability grant, existing
historical manifest row and declared skip. Update only the matching registration
list and explained census/count/digest assertions in the inventory suite. Retain
complete before/after test and production census comparisons on 3.11 and 3.14;
explain shifted anchors and all new rows without weakening analyzer refusals.
CI adds the four suites through the existing D-local snapshot pattern and retains
every existing step and failure propagation. No old test body or fixture changes.

## Exact additions and module boundaries

```text
tools/v0a_blueprint_workload.py
tools/v0a_blueprint_workload_population.py
tools/v0a_blueprint_workload_measure.py
tools/v0a_blueprint_workload_report.py
tests/test_blueprint_workload_population.py
tests/test_blueprint_workload_measure.py
tests/test_blueprint_workload_session.py
tests/test_blueprint_workload_report.py
tests/fixtures/blueprint_workload/control.json
```

The launcher authenticates raw B source plus the sealed additive tool/registration
delta, owns one worker at a time, and records intents/exits/captures. Its session
diagnostic mode installs an observational main-thread profiler before loading the
unchanged session entry point. It must not import `pontius`, load the host under
the session's alias, or alter session state before the session's own Admission.

Population construction runs the legal kernel directly with the accepted dealer
and opponent rule function. It exports actor-visible observations, full reference
traces and passive entries. Use complete canonical keys for deduplication and fresh
objects for diagnostic hits. The complete deal is available only to the reference
driver; each provider gets its one-seat visible state. No arbitrary history edits.

The direct measurement module owns timing/memory/reuse workers. The retained arm
hashes owned canonical bytes against the independently frozen source digest before
each hand; it does not revalidate an external file or claim live-index integrity
from a hash of cached bytes. Caller/result aliases remain the accepted boundary.
The actual prepared mapping is inspected read-only for the lookup diagnostic only.

The report module is a standard-library reader of frozen JSON/JSONL records. It
never launches a worker, imports a poker provider, reconstructs missing timings or
changes a denominator. Pure reductions retain case IDs and point back to raw bytes.
Keep source and worker result schemas closed, exact types and finite numeric values.
Use explicit typed refusals for source_invalid, input_invalid, coverage_missing,
parity_failed, profile_invalid, capture_limit, resource_limit, budget_exhausted,
worker_failed and cleanup_failed; preserve primary and secondary causes.

## Finite correctness controls after opening adoption

These engineering controls are disjoint from the future r002 population invocation.
Use existing accepted fixture cards and dealer seed `00` repeated 32 times at index
zero; do not construct the 8,192/1,152-trajectory population during source tests.
At most twelve legal offline trajectories per test invocation cover passive and
min-raise rules, both stack profiles and baseline decisions. Small in-memory table
controls use 0, 1, 16 and 128 entries from their declared witnesses, where available;
capacity boundary arithmetic also uses independent literal row lengths.

The four suites must cover:

- Population: literal seed/deal and recipe ordinal mapping, reachable legal replay,
  one-seat visibility, duplicate-key first witness, interleaved prefix membership,
  exact codec row-byte reconciliation, N_fit/next overflow, missing-bin and action
  cap refusals, query/table separation, fresh equal-valued hit keys and plan counts.
- Direct costs: five operation results versus independent expected keys/actions,
  fresh/retained exact parity, initial setup charged in every group, per-hand hash
  checks, caller/result isolation and deliberate cached-byte mismatch refusal.
  Controlled clock values verify interval boundaries and excluded validation;
  no controlled timing result is reported as performance evidence.
- Session/profile: real empty and one-entry sessions at seats 0 and 3 in both
  strategies, with observational diagnostic counterparts. Each complete invocation
  of the new session suite has at most eight unprofiled plus eight diagnostic
  sessions per interpreter. The plan admits one focused development invocation,
  one post-review acceptance invocation and one added-CI-block rehearsal per source
  candidate: at most 48 new control sessions per interpreter in a clean candidate,
  and 144 across the initial candidate plus both permitted corrections. Failed
  invocations count and are retained; no extra successful repeat is admitted.
  A RED run stopped before any session launch remains recorded and does not spend
  the real-session launch allowance; a run that attempts a session launch spends
  its scheduled invocation even when launch or a later assertion fails. Further
  real-session iteration uses the bounded correction allowance. Unchanged old
  suites retain their own control populations.
  These controls are separate from the 120 later performance sessions.
  Verify source admission, unmodified
  child command, actions/settlements, nested phase closure and original ledger IDs.
  Literal spans verify deepest-category accounting, initialization precedence,
  closure/inflation refusals, and that child compute is not added to parent wall.
- Lifecycle/report: exact subset/cell census, strict percentile denominators, timer
  sensitivity, all seven decision rules and their adjacent thresholds, coincident
  N_fit union, byte-adjusted scaling, missing/corrupt/duplicated result rejection.
  Real contained non-poker sleepers exercise timeout, interruption and descendant
  cleanup; bounded-output children exercise overflow. A controlled sampler may
  request termination without allocating 3 GiB; independent native process state
  must prove termination. No mocked successful cleanup or invented process counters.

Controls may inject clock/sampler/failure triggers at explicit test seams; they
must execute real lookup, ledger parsing, span reduction and native cleanup. A
deliberately incorrect result must fail the independent check, not be hidden by
the injector. Retain any controlled trigger's scope and limits with its receipt.

## Opening contents and later gates

The opening is exactly ADR-0515, STATUS.md, this file, execution-protocol.md,
`docs/superpowers/plans/2026-09-07-blueprint-workload.md`, and these three raw files
under `docs/superpowers/specs/`:

```text
2026-09-07-representative-blueprint-workload-design.md
2026-09-07-representative-blueprint-workload-design-r002.md
2026-09-07-representative-blueprint-workload-review-response-r002.md
```

The opening reviews/gates and source acceptance commands are fixed in the plan.
The current source remains accepted until a later source-seal decision. Source
tests, population qualification, non-evidentiary rehearsal and measured invocation
are separately labeled; passing one does not create authority for the next.
