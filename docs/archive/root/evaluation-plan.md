# Paired Local Evaluation Implementation Plan

> For agentic workers: use superpowers:subagent-driven-development or
> superpowers:executing-plans after the exact source-opening adoption. Repository
> freeze/review/snapshot/commit rules override any generic frequent-commit guidance.

**Goal:** Deliver the bounded matched-table comparison and honest result report.

**Architecture:** Two new stdlib tools wrap the unchanged public session subprocess.
The pure contract plans identical paired inputs and reduces observable reports. The
outer CLI admits exact source, reuses the accepted native Job and retains one-shot
artifacts. No game/provider/host/session/generator changes.

**Tech stack:** Windows PowerShell, CPython 3.11.15 first and 3.14.6 second, unittest,
absolute native Git, existing Windows Job implementation and exact raw JSON contracts.

**Spec:** docs/architecture/v0a-evaluation-r001/brief.md, design.md, source-contract.md.

## Global constraints

- Base B e043f81ecec3ac16128720b42c3312bb41a4ed67; recheck all six raw exceptions.
- No implementation until ADR-0508's exact authorized adoption; no actual evaluation.
- Source ceilings: 1,200 production, 1,800 test, 160 manual registration changed lines;
  fixtures 32 KiB. No src/pontius or existing poker tool edits.
- Correctness: at most two literal deals, one all-zero-seed end-to-end vector, and
  at most 24 actual poker session starts across the three new suites per execution.
- No helper can confer scientific/operating authority. All old owners stay closed.
- Every test command uses its fresh D-local snapshot, -B -P, scrubbed env, cwd/src,
  native absolute Git and actual-version/origin checks; preserve failure receipts.
- No ceremonial commit/push without its exact controller authorization. Local immutable
  review commit-tree objects are coordination, not decision adoption.

## Task 1: strict contract, matrix and observable report reducer

Create tools/v0a_evaluation_contract.py, tests/test_v0a_evaluation_contract.py and
tests/fixtures/evaluation/controls.json. Do not read or execute poker to pick fixtures.

Interfaces owned by the contract tool:

```python
def decode_request(raw: bytes) -> dict: ...
def encode(value: object) -> bytes: ...
def build_matrix(request: dict, deals: list, suffix: str) -> dict: ...
def observe_trial(binding: dict, stdout: bytes, stderr: bytes,
                  exit_code: int | None, capture_complete: bool) -> dict: ...
def reduce_trials(plan: dict, trials: list) -> dict: ...
```

Here signatures declare the required interface, not placeholder implementation code.
build_matrix returns pairs and units. Internal pair rows include canonical input_bytes
alongside the contract's pair metadata; publication removes input_bytes after saving
the exact file. Paths are pairs/pPPP.json, three-digit zero-based pair ordinal.
Each unit metadata matches the public plan. binding contains its unit metadata plus
source_commit, source_manifest_sha256, blueprint identities, controlled_seat, table
input hash and cleanup outcome. observe_trial has no I/O or authority to launch.
reduce_trials returns the pairs and aggregate fields from the source contract.

- [ ] Before implementation, record independently expected matrix/order/count cases
  and fixture meanings in the task packet. Use this literal synthetic deal for pure
  planning controls; it is not an evaluation or selected strategic scenario:

```python
DEAL = {"private_hands": [[0, 1], [2, 3], [4, 5], [6, 7], [8, 9], [10, 11]],
        "board_runout": [12, 13, 14, 15, 16]}
REQUEST = {"version": "pontius-v0a-evaluation-request-v1", "seed": "0" * 64,
           "deal_count": 1, "lineups": [["passive"] * 5], "seat_start": 2,
           "initial_button": 3, "total_budget_ms": 900000,
           "trial_budget_ms": 60000}
```

- [ ] Write focused REDs before adding the contract. Load the standalone helper in
  snapshot tests using an explicit path under the snapshot, with no pontius import.
  Required independent literal expectations for the matrix above: seats
  [2,3,4,5,0,1], buttons [3,3,3,3,3,3], six pairs, twelve units, strategy order
  [baseline,blueprint,blueprint,baseline] repeated three times; all original private
  pairs/board unchanged; two units per pair have exactly equal input bytes/hash.
- [ ] Add exact request refusal controls for bool integers, duplicate/unknown fields,
  noncanonical encodings, repeated lineups, wrong lengths, fourth nesting level plus
  one, deal-count bounds and budget overflow/insufficient full-trial reserve.
- [ ] Implement parsing/encoding and matrix construction under source-contract.md.
  The algorithm is its exact d/l/r/p/s/b enumeration; do not derive expected tests by
  calling that algorithm or replace all-seat coverage with rotating the whole table.
- [ ] Build finite synthetic report/frame controls before reducer code. Example scoring
  oracle: baseline net [4,-2], blueprint net [1,3], pair deltas [3,-5], total -2,
  mean numerator -2 and denominator 2. If either pair is incomplete, global aggregate
  is null; it must not become 3/1 by silently omitting the failed pair.
- [ ] Implement version-dispatched extraction. Successful host-applied actions own
  execution counts; retain missing attribution and incomplete observed prefixes.
  Coalesce duplicate action timing from decision/failure, distinguish host timeout,
  keep legacy choice and baseline fallback categories separate. Do not double-count
  propagated hand/session failure codes or expose hidden cards in summaries.
- [ ] Exercise delivery_rejected with no timing flags and hand/session child_failed;
  require a separate unverified action_failures observation and no pair score. Cover
  duplicate copies, conflicts, null index, missing/invalid rows and truncated prefix.
  Independently reject dropping, scope-folding and double-counting the action cause.
- [ ] GREEN the focused contract suite in a fresh floor snapshot; retain actual output
  and verify each deliberate wrong matrix/count/denominator behavior fails its oracle.

## Task 2: outer CLI, native lifetime and retained run

Create tools/v0a_evaluation.py and tests/test_v0a_evaluation_runner.py.
Consumes all Task 1 interfaces; produces the CLI/artifact contracts in source-contract.md.
Internal entry points are admit_source(repo), run_trial(binding, paths, deadline_ns)
read_completed(root) and main(argv=None). Source admission returns only verified raw buffers, identities
and fixed helper handles; it does not open a poker state. run_trial returns the exact
trial-summary plus lifecycle fields; it does not independently pick the next unit.

- [ ] Write source/admission and absent-root REDs; no fixture may point at primary or
  an existing consumed root. Bind B old closure and both new committed raw tool blobs.
- [ ] Implement exact source checks and fixed alias loaders. Reuse host.Job only for
  native containment; never instantiate host.Source/Table/Session in the parent.
  Confirm a separately spawned public session has clean module state.
- [ ] Implement exclusive reservation, retained request and complete plan publication.
  Generate only the declared finite deal vector after source/request admission. Save
  every input and plan before the first intent. Never create entropy or accept overlays.
- [ ] Write native REDs using finite non-poker workers: descendant creation, stdout/
  stderr overflow, malformed/partial final JSON, pre-resume assignment failure,
  interrupt, timeout and cleanup refusal. These control the trigger at the subprocess
  seam while exercising the real Job, streams, writer and result observer.
- [ ] Implement suspended creation, Job assignment/resume and bounded concurrent raw
  drains. Register resources before fallible probes. Use shared deadline checks before
  and after admission, terminate the Job on any stop, and record incomplete cleanup.
- [ ] Implement fixed matrix execution with per-unit intent/result and stop-on-first
  non-success. Keep unknown launches and unstarted units distinct; never retry.
- [ ] Implement the publication transition table and one public read_completed predicate.
  Create the empty pending guard before final files; close/readback/verify both files,
  source and deadline before commit. Release only the empty guard once after commit;
  all precommit failures retain it. Keep visibility/CLI timing separate from the
  deadline, and serialize preparation times only. No postcommit error revokes commit.
- [ ] Add the one end-to-end zero-seed 12-trial public matrix correctness control.
  Verify exact inputs, all-seat reset, strategy protocol/namespace, exits/cleanup,
  retained records and independent reduction of actual host-accepted integer stacks.
  This checks pipeline behavior, not strategic profitability or a new poker oracle.
- [ ] GREEN runner/native controls in fresh floor snapshots. Demonstrate that bypassing
  pre-resume containment, completing on partial capture or scoring a missing arm fails.

## Task 3: boundary faults, registration and source acceptance

Create tests/test_v0a_evaluation_boundary.py. Modify only the six registration paths
and exact scopes in source-contract.md. Preserve the complete old source population.

- [ ] Add deterministic raw-source/input/plan drift, root collision, wrong interpreter/
  Git/env, extra source and preloaded helper controls. Verify refusal before forbidden
  downstream work and retained prefixes after a started unit.
- [ ] Add deterministic clock edges for full-unit admission, total deadline during
  reduction, short final write, flush/readback and completion-marker failure. Exercise
  real completion write/close delayed past deadline and close failure after full bytes,
  partial markers/interruption and normal success. The real public read_completed must
  refuse all precommit failures while preserving files/guard without retry or overwrite.
  Separately exercise delayed, failed and ambiguous guard removal: remaining guard
  refuses, absent guard exposes previously verified commit even if visibility is late.
  Inject clocks/fault triggers only; actual files/removal/consumer remain real. Do not
  fabricate cleanup/publication success or infer OS durability or a visibility deadline.
- [ ] Complete the acceptance matrix from every numbered brief criterion to its finite
  real/synthetic cases, limits, expected failures and counterexamples.
- [ ] Register exact tools/edges and three CPU suites; add their CI steps. Use the
  unchanged inventory analyzer to compare all B/candidate records on both interpreters.
  Preserve the old ID/order/grant/assertion chain and account for each mechanical shift.
  Analyzer repair, new grants or unexplained drift stop the task.
- [ ] Freeze all source changes as a new immutable review ref/whole-row raw manifest.
  Obtain two fresh independent Tier C reviews. Corrections use new rounds, finite
  RED/GREEN evidence, deferred coverage claims and normal residual rules.
- [ ] After CLEAN, run all sixteen source-contract acceptance commands on actual
  3.11.15 first then 3.14.6, each a fresh exact-candidate snapshot. Check source limits,
  fixture/session counts, raw base exceptions, old protected bytes and full census.
- [ ] Retain receipts/reviews/dispositions. Prepare a separate source-seal decision
  and its required metadata review/gates for exact controller approval. No source
  acceptance result, design approval or committed opening launches an evaluation.

## Accepted-schema reference for the reducer

The exact v1 session fields are version, session_id, status, stop_reason, failure_reason,
secondary_failures, source_commit, input_sha256, blueprint_artifact_sha256,
blueprint_sha256, requested_hands, completed_hands, next_button, carried_stacks, hands.
V2 adds provider/config_sha256 only. Each hand entry is ordinal/button/starting_stacks/
result. Its nested result has version, session_id, status, failure_reason,
secondary_failures, input_sha256, blueprint_artifact_sha256, blueprint_sha256,
source_commit, applied_actions, settlement, child_exit_code, child_stdout_base64,
child_stderr_base64, capture_truncated; v2 adds provider/config_sha256 only.

Settlement: payouts/final_stacks/pots; each pot amount/seats. Applied action:
index/seat/street/action/origin; action kind/raise_to. Every wire frame has
protocol/session_id/type plus accepted B host.WIRE_FIELDS for that type; only v2
ready adds provider/config_sha256. Child records are LF JSON frames, not a JSON array.
Timing keys: status, interruption_reason, wall_start_ns, last_valid_observation_ns,
emission_observed_ns, elapsed_ns, response_compute_seconds, response_uninstrumented_seconds,
work_cutoff_crossed, deadline_crossed. Exact nested decision/failure/preparation keys
are the immutable B v0a trace/provider-codec/model declarations. Freeze copied field
sets against those raw declarations and enforce the relationships used by metrics;
do not claim revalidation of full hidden state or an independent legality engine.

## Plan self-review

Criteria 1-3 map to Task 1 matrix controls; 4 to Task 2 unchanged public subprocess;
5 and 7 to Tasks 2-3 lifetime/deadline/publication controls; 6 to Task 1 reducer;
8 to Task 3 finite suites and separate authority. Source exceptions, file/API ownership,
fixture limits and execution order are explicit. The architecture introduces one outer
runner, not independent projects. No source/fixture/test payload is run while preparing
this plan; its next executable step depends on exact ADR-0508 adoption.
