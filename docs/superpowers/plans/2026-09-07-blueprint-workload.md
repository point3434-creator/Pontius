# Representative Blueprint Workload Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans
> to implement this plan task-by-task. Steps use checkbox syntax for tracking.

**Goal:** Build and qualify the r002 workload tools so the next finite invocation
can choose an optimization target from capacity, reuse, phase and history evidence.

**Architecture:** Four additive tools outside src: bounded launcher/session
observer, reachable population builder, direct cost workers and pure result reader.
Use accepted kernel/provider/codec/session/Job implementations. Preserve their bytes.

**Tech Stack:** CPython 3.11.15 floor, confirming 3.14.6, standard library, unittest,
existing native Windows process containment and absolute Git. No new dependency.

**Spec:** `docs/superpowers/specs/2026-09-07-representative-blueprint-workload-design-r002.md`.
Exact source/controls: `docs/architecture/v0a-blueprint-workload-r001/source-contract.md`.
Invocation details: that directory's `execution-protocol.md`.

## Global constraints

- ADR-0515 must be adopted before source work. Exact commit approval remains a
  separate checkpoint. Opening approval does not authorize full population/timing.
- All src, host/session/dealer/adapter/provider/codec/evaluator and old fixture bytes
  remain B-exact. Only the six prospective registration exceptions may change.
- Use the existing isolated C worktree. Run acceptance from fresh raw-blob D-local
  snapshots with -B -P, snapshot cwd/src, scrubbed environment and absolute Git.
- Work on 3.11 first. Preserve all old stable IDs/assignments, baseline locks,
  historical rows and failures. Never invoke an old owner or consumed cost command.
- Every control has an independent expected value/outcome and a named boundary.
  Test doubles may trigger a fault but cannot certify a native resource contract.
- Freeze before independent review; final acceptance follows review closure.
  No measured performance population during source development/qualification.
- Keep implementation progress and mutable receipts outside frozen plan bytes.
  One initial candidate and at most two corrections; honor earlier design stops.

## Checkpoint 0: qualify and adopt this exact opening

- [ ] Freeze the eight documentation paths listed in source-contract.md through a
  temporary Git index and create-only review ref, leaving HEAD/user index untouched.
- [ ] Recompute raw blob hashes and whole-row-sorted manifest from that commit.
  Verify six B exception pins and r001/r002/review-response preservation hashes.
- [ ] Obtain two independent cold Tier C reviews of the frozen package and B seams.
  Retain all findings and design verdicts. Correct/refreeze only within the budget.
- [ ] After closure run status_generation --check and all 12 status tests on 3.11,
  then 3.14, each command in a fresh exact-candidate D-local snapshot. Verify no
  tracked source change and raw candidate byte identity before/after payloads.
- [ ] Present the exact candidate/tree/manifest and requested ADR title. After its
  specific authorization, make the one decision commit and immediately push origin.

## Task 1: public contracts and literal controls

Files: create all four named tool files as needed for their interfaces, and
`tests/test_blueprint_workload_population.py`, `tests/test_blueprint_workload_report.py`
plus `tests/fixtures/blueprint_workload/control.json`.

- [ ] Define the strict versioned plan, context, cell-intent, cell-result and terminal
  records. A plan has ordered unique cell IDs, source/runtime/protocol bindings and
  fixed parameters; a result references one plan cell and never creates a new one.
- [ ] Fix public CLI parsing exactly as execution-protocol.md and bind the later
  invocation-authority document before any worker. `read` cannot execute children.
- [ ] Write literal controls for recipe factor mapping, row-byte accounting,
  disjoint seeds, all fixed matrix/subset counts and duplicate/unknown/missing cells.
  Use the explicitly permitted control seed, not future r002 population seeds.
- [ ] Run new focused 3.11 files and retain expected RED evidence for absent contract
  behavior. Implement the minimum strict parsing/census/byte calculations; verify
  malformed exact types, duplicate keys, NaN, oversized data and wrong identities fail.
- [ ] Fix test method names and allowed source imports early. Registration occurs in
  Task 5; focused local iteration does not claim complete inventory acceptance.

Public interfaces: population `build_population(recipe, sink)` and
`freeze_plan(population_manifest, runtimes)`; measurement `measure_cell(cell, inputs)`;
report `read_run(root)` and `summarize(records, plan)`; launcher `main(argv)`.
Exact immutable values cross these seams; bounded writer/clock/resource handles are
explicit arguments for controls. Avoid a plugin registry or arbitrary callables in
serialized plans. The CLI exposes only the fixed reviewed modes/cell population.

## Task 2: reachable population and capacity

Files: `tools/v0a_blueprint_workload_population.py` and its population suite/fixture.

- [ ] Drive accepted legal transitions, dealer index zero, accepted opponent rules
  and baseline provider with only actor-visible cards/state. Keep full deals in the
  reference driver. Verify literal early actions and settlement against fixtures.
- [ ] Record pre-action contexts, canonical key bytes, passive action and first
  witness; test deduplication and street interleaving using small literal streams.
- [ ] Implement independent query factor ordering, preserved within-hand sequence
  and exact history-bin qualification. Missing coverage or 256 actions refuses.
- [ ] Compute largest member-prefix capacity using exact codec row lengths, then
  verify full N_fit/N_fit+1 encodings. Codec sorting must not change prefix membership.
- [ ] Freeze natural hit labels, diagnostic memberships, fresh equal-valued query
  keys, reusable 32-hand selection, unique size union and full case invocation order.
- [ ] Run the focused 3.11 suite under the finite twelve-trajectory control allowance;
  assert the full qualification recipe has not been executed. Confirm on 3.14.

## Task 3: direct measurements and retained preparation

Files: `tools/v0a_blueprint_workload_measure.py` and
`tests/test_blueprint_workload_measure.py`.

- [ ] Write controls for exact key/hash/mapping/identity/provider outputs using
  accepted legacy results and fixture expectations, with tiny declared observations.
- [ ] Implement five-block ABBA subblocks with no doubled sample counts, retained
  outputs validated after each measured phase, GC enabled, no tracing in timings.
- [ ] Record clock/bracket/loop controls and independent construction boundaries;
  distinguish source preparation from synthetic construction and from file reading.
- [ ] Implement fresh/retained H groups, charging initial preparation in both and
  per-hand cached-byte verification in retained. Use frozen query sequences only.
- [ ] Test ordinary parity, caller/result isolation and byte mismatch refusal.
  A controlled clock verifies inner and outer accounting without performance claims.
- [ ] Add separate traced/untraced memory workers with explicit object lifetimes and
  real Windows process counter sampling from the controller. Keep peaks distinct.
- [ ] Run focused small 3.11 controls, then 3.14; no full history/reuse/scaling matrix.

## Task 4: session observer and native lifecycle

Files: `tools/v0a_blueprint_workload.py` and
`tests/test_blueprint_workload_session.py`.

- [ ] Write literal nested-span controls, admission-precedence and unclosed-span
  refusals. Match exact B filename/co_qualname; record raw call/return timestamps.
- [ ] Implement the standard-library diagnostic bootstrap before any poker import.
  Load the unchanged session with accepted argv; its Admission owns host imports.
  Use the B CLI spellings fixed in execution-protocol.md, including --format json.
- [ ] Run finite real empty/one-entry sessions at seats 0/3 in both strategies,
  and the diagnostic counterpart of each (eight plus eight per interpreter max).
  Compare actions/settlements and preserve natural membership versus fallback use.
- [ ] Extract original ledger records by action/event ID and demonstrate seat-3
  first response includes preparation while off-turn aggregate work is not added.
- [ ] Use the real host Job for suspended/no-window worker admission. Test real
  non-poker child/descendant timeout, interrupt and output-overflow cleanup. Inject
  only resource-stop triggers; independently observe exit and job closure.
- [ ] Verify wrong source/input/authorization, existing root, wrong cell, late drift,
  capture overflow, worker failure and cleanup failure preserve distinct terminals.
- [ ] Run floor focused controls then current; retain all failed executions. No
  profiled timings from these correctness fixtures become r002 performance data.

## Task 5: report reductions and exact registrations

Files: `tools/v0a_blueprint_workload_report.py`, its suite, the six declared existing
exception files. Preserve every other old file. No analyzer or capability repair.

- [ ] Cover all seven thresholds and adjacent boundaries with independently calculated
  literal observations. Test nearest-rank minimum counts, profiler inflation, timer
  sensitivity, nonpositive/noisy scaling and failed/unattempted denominator retention.
- [ ] Implement raw manifest verification and pure reduction. Naturally weighted
  traffic, diagnostic strata, versions, parent wall and child ledger stay separate.
  Every published number references its raw case set and eligibility conditions.
- [ ] Recheck six B blob pins, add the four exact origins/import sets and four suite
  registrations. New boundary tests reject an extra sibling/forbidden incoming edge.
- [ ] Generate inventory/profiles; compare complete B/candidate test and production
  censuses on floor/current, preserving 3,180 old stable IDs and assignments. Refresh
  only explained registration/census expectations in the existing inventory suite.
- [ ] Add four current CI suite steps in the existing snapshot pattern. Preserve all
  old steps, absolute Git resolution, environment and exit propagation.
- [ ] Reassess size/proportionality against the brief before adding a support layer.

## Task 6: source freeze, independent review and acceptance

- [ ] Freeze the exact four tools/four suites/fixture and six registration changes
  as a 15-path source candidate. Retain raw source, manifest, finite control receipts,
  acceptance map and self-report. Any extra changed path requires new prospective scope.
- [ ] Obtain two fresh independent Tier C cold reviews. Bind findings to the commit
  and manifest; keep implementer narrative out of initial reviewer inputs. Use the
  workflow's deferred coverage claim only for FIX rounds. No live review during timing.
- [ ] After closure run the source gates below on 3.11 then 3.14 from fresh exact
  D-local snapshots. All gates run even if another independent gate fails; overall
  acceptance requires every required gate and honest existing platform-skip reporting.
- [ ] Verify complete raw B preservation outside scope and all added paths. Rehearse
  the four added CI blocks locally; distinguish that from hosted CI evidence.
- [ ] Prepare the later source-seal decision with exact incorporation/review/gate
  identities. Obtain its specific commit/push authorization; no measurement yet.

Source gates (each Python command uses the snapshot wrapper, -B -P and absolute Git):

```text
tools/check_stabilization_boundaries.py
tools/generate_test_inventory.py --check
tests/test_blueprint_workload_population.py
tests/test_blueprint_workload_measure.py
tests/test_blueprint_workload_session.py
tests/test_blueprint_workload_report.py
tests/test_stabilization_boundaries.py
tests/test_inventory_and_profiles.py
tests/test_blueprint_artifact.py
tests/test_blueprint_preparation.py
tests/test_blueprint_preparation_runtime.py
tests/test_blueprint_preparation_transport.py
tests/test_seeded_deals.py
tests/test_v0a_table_session.py
tests/test_v0a_table_session_boundary.py
tests/test_decision_provider_session.py
tests/test_v0a_evaluation_v3.py
tests/test_evidence_manifest_generation.py
```

These are current source gates. The sealed old evaluator suites keep their existing
historical registrations/CI bridge; this round changes none of their source inputs.
If an unchanged gate fails because a named implementation needs wider scope, retain
the failure and seek a prospective correction; do not remove the gate or edit sealed
bytes. Do not execute a prior measured matrix as a compatibility check.

## Next invocation boundary, after source seal

- [ ] Prepare exact staged finite authority for qualify then run, binding source,
  interpreter identities, recipe/protocol and one absent root. Its derived corpus
  and all cell/argv manifests freeze before timing. Qualification refusal closes run.
- [ ] Execute only after that exact authorization, using r002's complete floor pass
  followed by the fixed current subset within one measured 60-minute envelope.
- [ ] Preserve partials and unattempted cells; produce the pure report and next
  source-target proposal. Commit results only under their own exact authorization.
