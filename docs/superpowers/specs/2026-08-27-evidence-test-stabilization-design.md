# Evidence and Test Stabilization Design

- Status: approved by user on 2026-08-27
- Date: 2026-08-27
- Scope: remediation milestones 1 and 2
- Repository baseline: `master` at `a842c4b6a73a2991a63a481f4107580b72750582`

## Context

Pontius combines active poker-runtime code, reusable numerical libraries, and an
append-only research ledger in one flat Python package. Several calibration
owners, readers, tests, configuration files, and retained artifacts are bound to
exact commits and byte hashes. In particular, ADR-0476 permanently consumes and
closes the v7 compiled-calibration owner. It forbids retrying the owner, weakening
the historical reader, reusing partial measurements, or editing the sealed v7
identity as though it were active application code.

The ordinary repository test command does not respect those constraints. Raw
`unittest discover` imports all test modules into one interpreter, while several
tests require their scientific module to be absent before bootstrap. It also runs
preauthorization and pre-result assertions from a checkout that correctly retains
later authorization and result artifacts. Some launch tests require effective
Python `-B` or `-B -P`, but the documented general test command omits those flags.
The resulting failures combine real defects, invalid test phases, shared-import
contamination, and deliberate historical-state rejection.

Two independently reproduced defects also exist in the consumed v7 reader:

1. a valid preauthorization state can reach direct indexing of the live-only
   `authorization_commit` field and leak `KeyError`; and
2. authorization configuration is read twice, so parsing and hashing can use a
   different byte snapshot from the one compared with Git.

Those defects must inform current and future code, but the consumed v7 source
cannot be repaired in place without invalidating its retained identity.

## Decision

Preserve sealed research history byte-for-byte and add a separate active evidence
and test-orchestration layer. The active layer will classify repository content,
assess retained v7 evidence from current HEAD without invoking or weakening the
consumed owner, model authorization phases with distinct types, and run test
profiles in isolated interpreters or exact historical clones.

The compiled-calibration lane is parked. This design creates no v8 owner and
authorizes no scientific replay, retry, continuation, topology selection, or use
of v7 partial measurements.

## Goals

1. Make the canonical current-development test command deterministic and
   meaningful.
2. Preserve every sealed v2-v7 implementation, test, configuration, marker, and
   result byte.
3. Separate current-HEAD behavior tests from historical phase certification.
4. Provide a current-HEAD-safe, read-only assessment of the retained v7 artifact.
5. Prevent missing live-authorization fields through the type model.
6. Parse, hash, and compare authorization configuration from one byte snapshot.
7. Produce stable error codes and actionable diagnostics without leaking internal
   exceptions such as `KeyError`.
8. Establish an exact machine-enforced history boundary and an import-graph
   baseline that later performance and architecture work can rely on.

## Non-goals

- Editing, moving, renaming, or reformatting sealed historical files.
- Making the consumed v7 owner runnable from current HEAD.
- Replaying any one-shot experiment or deleting retained lifecycle artifacts.
- Certifying the incomplete v7 campaign as successful or scientifically complete.
- Creating a new calibration owner before the production-base architecture
  contract exists.
- Reorganizing all 470 source modules in this milestone.
- Assigning final `live`, `library`, or `parked` ownership to every existing
  module; that semantic inventory belongs to the holistic architecture review.
- Implementing package-import or GPU-performance refactors; those are later
  milestones built on this foundation.
- Treating the current assessor as a retroactive replacement for the historical
  sealed reader.

## Immutable invariants

The implementation must preserve all of the following:

1. The primary checkout remains at its user-selected branch and commit unless the
   user changes it.
2. No command invokes a v2-v7 public owner against the primary checkout,
   retained lifecycle state, or real scientific executor. A historical profile
   may exercise an explicitly declared synthetic owner-contract test only in its
   disposable clone, with lifecycle paths redirected below that clone and the
   scientific-execution seam replaced by a non-scientific test double.
3. No test or tool deletes, moves, rewrites, or normalizes a retained artifact.
4. Historical execution occurs only in a temporary local clone at an explicitly
   declared commit.
5. Temporary cleanup resolves and verifies its exact path beneath the operating
   system temporary directory before deletion.
6. V7 result, attempt, and consumed-launch bytes retain their recorded sizes and
   SHA-256 digests.
7. A maintenance assessment reports historical evidence; it does not grant retry
   authority or change the meaning of the retained terminal.
8. Current and historical test profiles never share an interpreter or mutable
   imported-module state.
9. No test payload executes from or writes to the primary checkout. Current-state
   profiles run from a byte-identified disposable snapshot captured once at run
   start; historical profiles run from exact-commit disposable clones.

## Architecture

```text
sealed historical capsule (unchanged)
  v2-v7 owners, readers, controls, configs, markers, results
                         |
                         | read only through declared identities
                         v
src/pontius/evidence/
  model.py          immutable manifests, states, and assessments
  authorization.py single-snapshot authorization-state reader
  retained_v7.py   current-HEAD-safe retained-evidence assessor
  errors.py        typed active-layer failures
                         |
                         v
tools/run_tests.py ---- tests/test-profiles.toml
  isolated profile orchestration
  pre/post evidence verification
           |---------- tests/test-inventory.json
           |             exact test-ID ownership/exclusions
           |
           `---------- tools/test_child.py
                         guarded unittest loading and result protocol
                         |
                         v
docs/architecture/sealed-current-files.toml
  exact paths and current-byte identities that cannot change

docs/architecture/sealed-current-absences.toml
  exact lifecycle paths that must remain absent

docs/architecture/historical-blobs.toml
  exact commit/path/blob identities; current descendants may evolve

docs/architecture/dependency-baseline.toml
  mechanical legacy import-edge and SCC snapshot
```

### Historical boundary manifests

The capsule is a logical classification, not a filesystem move. Existing files
stay at their exact paths. It is represented by three exact manifests; broad glob
patterns cannot confer immutable status:

1. `sealed-current-files.toml` records each current-working-tree file whose bytes
   are retained evidence and must not change, including path, role, byte length,
   raw SHA-256, governing decision, and owner.
2. `sealed-current-absences.toml` records each lifecycle path whose nonexistence is
   part of retained state, with role, governing decision, and owner.
3. `historical-blobs.toml` records exact historical snapshots by commit and root
   tree OID, plus governed source, test, configuration, decision, and dependency
   entries keyed by `(commit, path)`. Each entry contains Git blob OID, raw
   SHA-256, role, phase, and governing decision.

The current-present and current-absent sets are disjoint. A path may also have one
or more historical blob identities because current-state retention and historical
commit binding are different dimensions. The same path may repeat in the
historical manifest at multiple commits when its sealed blob changed between
phases. Active primitives such as `action_clock.py`,
`legal_decision_spine_v2.py`, `durable_evidence_journal.py`, and `__init__.py` are
historical-blob dependencies, not permanently frozen current files.

#### Initial current-byte and absence sets

The current-byte manifest contains exactly these six proven retained identities:

| Path | Bytes | Raw SHA-256 | Decision |
| --- | ---: | --- | --- |
| `artifacts/work_preflight/legal_river_quotient_compiled_global_separation_calibration_v2.jsonl` | 3299268 | `67ac14d408fe8c4299ee603ec1d8c454975094507d4ac28cda73001a42feb90d` | ADR-0462 |
| `artifacts/work_preflight/legal_river_quotient_compiled_global_separation_calibration_v5.attempt.json` | 606 | `104820d0c67391365d18fb76ca72c704e40e467e2993a96c618d4bf91155600d` | ADR-0470 |
| `experiments/configs/legal-river-quotient-compiled-global-separation-calibration-v9-corrected-invocation-authorization.json` | 482 | `57c869df38c23e4c0520730986a65825f51814915f68cc3e4d32a2f39303a535` | ADR-0473 |
| `artifacts/work_preflight/legal_river_quotient_compiled_global_separation_calibration_v7.jsonl` | 7858857 | `78b2f8351ca49785756ec336d4f967bcc83a86f9ef96506a6144726cf3b312b3` | ADR-0476 |
| `artifacts/work_preflight/legal_river_quotient_compiled_global_separation_calibration_v7.attempt.json` | 1825 | `ada1896f0bf63111e0c1e5e707315fbca6c13f6e2b63222805cb5ef4cb9dc413` | ADR-0476 |
| `artifacts/work_preflight/legal_river_quotient_compiled_global_separation_calibration_v7.launch-consumed.json` | 349 | `c3c0a34cba6a677157034d8f8109cf47edea496a33c64992293176d879a2d629` | ADR-0476 |

The absence manifest contains exactly these 18 paths; it does not import the
sealed runner to derive them at runtime:

- `artifacts/work_preflight/legal_river_quotient_compiled_global_separation_calibration_v3.jsonl`;
- the v4 result, attempt, launch-pending, launch-consumed, and launch-aborted paths
  under `artifacts/work_preflight`;
- the v5 result, launch-pending, launch-consumed, and launch-aborted paths under
  `artifacts/work_preflight`;
- `experiments/configs/legal-river-quotient-compiled-global-separation-calibration-v8-corrected-invocation-authorization.json`;
- the v6 result, attempt, launch-pending, launch-consumed, and launch-aborted paths
  under `artifacts/work_preflight`; and
- the v7 launch-pending and launch-aborted paths under
  `artifacts/work_preflight`.

In this list, each versioned lifecycle filename uses the full stem
`legal_river_quotient_compiled_global_separation_calibration_vN` followed by
`.jsonl`, `.attempt.json`, `.launch-pending.json`, `.launch-consumed.json`, or
`.launch-aborted.json` as named above. The checked-in manifest expands every path;
it contains no pattern.

#### Initial historical snapshots and blob keys

The historical manifest records these exact phase snapshots:

| Commit | Root tree OID |
| --- | --- |
| `88148da07324c13b79c72ea494b14167a975c001` | `bc5d1952f690da5d49275344919de36224af26cb` |
| `08bb6857f47f9669b8f531c65079d4decd52a573` | `0d01a4133a4e6ab10467ad0bd298630149702a73` |
| `3de8e0c9eebf67f2cc2573041242a869468de6e9` | `ea80b86ac60cb324e3c18ddad83d8bbba0ade933` |
| `77feb7c78990ca53e70b1302a6866fe5d781411f` | `d26ba99c033875342a652ae352067beee1ca44ee` |
| `ba6a3418b7c991238cc1a65898fd61fa03b4a3cb` | `73b53cb04c91459e8b7028ccd292b972d2dfdf69` |
| `815d23c115289347e3d4028a4866eb9f87d4669a` | `894c026603156df4bba1134ba9861e98bd3a6663` |
| `5c0c9a401e5f2ebf59296832d954d0075c4d4624` | `f3418410c442a4d06c62aba9777def72633ca5c5` |
| `d633f3fb469a27dee688587293c6efb1d2cb2757` | `9c9ff658c2836bde5d1df71f5596d1d6aa1a5bd2` |
| `cbfa3598f22c7aba7d824f71356ca156f8b01b0c` | `9873ff13131c91b058307643dc838a8452268fbb` |
| `56127da2970f5a8a8056a97a247ebe1fdf4b983b` | `ee2437ba1b2efbf2dc4ab3c21bbacdbf26c58648` |
| `aaca2dda40e29be8ebd091d58e7853bce1c62fd8` | `e7bd077f40b1970e9b40a83c891996ab02cd5ffd` |

Within those snapshots, governed identities are enumerated by `(commit, path)`.
The v7 source-seal group contains the exact 96 entries from the first retained-v7
journal record at `body.payload.dependency_hashes`; its six-path authorization
surface is separately keyed at `aaca2dda40e29be8ebd091d58e7853bce1c62fd8`.
Selected source/test/configuration paths for every earlier matrix phase are keyed
at that phase's own commit even when the same path also appears in the v7 group.
There is deliberately no unique-path count because it would collapse distinct
sealed blobs and is prohibited by the schema. The manifest's entry count and
digest are generated from its normalized
`(commit, path)` records and locked by tests.

The dependency baseline separately records the complete legacy internal import
edge set and strongly connected components at repository baseline
`a842c4b6a73a2991a63a481f4107580b72750582` without assigning semantic owners or
rationales. Exact allow/deny policy applies only to imports originating in new or
changed stabilization modules. The new evidence layer may import only the standard
library, sibling evidence modules, and the explicitly declared
`pontius.durable_evidence_journal` seam. The orchestration parent remains
standard-library-only and imports neither `pontius` nor tests. New stabilization
modules may not import compiled-calibration owners/runners/readers, `cupy`/`cupyx`,
GPU/CUDA modules, tests, or experiment owners.

Every untouched legacy edge and the existing `action_clock.py` ↔
`preparation_bank.py` cycle are mechanically grandfathered without semantic
approval. The checker fails any new forbidden edge originating in changed
stabilization code and any new or expanded SCC, but stabilization does not require
classifying or remediating all 470 existing modules.

### Evidence manifest

The retained-v7 manifest is data, not executable authority. It includes:

- schema version;
- source-seal and authorization commits;
- retained-result, attempt, and launch-marker paths;
- expected byte lengths and raw SHA-256 digests;
- journal protocol and campaign identities;
- expected record counts and terminal classification;
- the fact that the scientific campaign is incomplete and authoritative measured
  calls equal zero; and
- the exact historical checkout required for sealed-reader reproduction.

Manifest parsing rejects missing, extra, duplicate, wrongly typed, or malformed
fields. Relative paths must remain below the repository root after resolution.
Digests are lowercase 64-character hexadecimal strings and commit identities are
lowercase 40-character hexadecimal strings.

### Active evidence model

The active layer uses frozen data classes or equivalent immutable values:

```text
EvidenceFileIdentity
  relative_path, byte_length, raw_sha256, role

PreauthorizationState
  head_commit, config_path, present=false, in_head=false, in_index=false

LiveAuthorizationState
  head_commit, authorization_commit, source_seal_commit,
  config_path, config_raw_sha256, config_canonical_lf_sha256,
  authorization_commit_paths

RetainedV7Assessment
  manifest_identity, terminal, journal_complete,
  scientific_campaign_complete, scientific_call_count,
  authoritative_measured_call_count, passed, historical_commit
```

Code requiring live-only fields accepts `LiveAuthorizationState`, not a generic
mapping. A preauthorization value therefore cannot reach live-only field access.

### Single-snapshot authorization reader

The authorization reader receives explicit filesystem and Git adapters. It does
not derive dependencies from mutable module globals. Its sequence is:

1. obtain and validate HEAD, tree entry, and index entry;
2. classify exact absence as `PreauthorizationState`;
3. open a present authorization without following links or reparse points, then
   validate regular-file type and platform file identity from the opened handle;
4. read the opened handle exactly once and revalidate its identity and size;
5. parse and validate configuration from those bytes;
6. compute all raw and canonical-LF digests from the same bytes;
7. compare the same raw bytes with the committed Git blob;
8. validate sole-child ancestry and the exact authorized path set;
9. re-read HEAD, tree, and index identities and confirm that the path still names
   the opened file; and
10. return `LiveAuthorizationState` only after all checks pass.

Mixed filesystem, tree, or index states raise `AuthorizationPhaseError`. No
public path returns a partially populated dictionary. Any concurrent path, file,
HEAD, tree, or index mutation fails closed rather than returning a state assembled
from different repository moments.

### Retained v7 assessor

The maintenance assessor performs no authorization of a new invocation. It:

1. loads and validates the immutable manifest;
2. reads each retained artifact once and verifies its length and raw digest;
3. recovers and validates the durable journal chain through the generic journal
   library;
4. validates only the retained semantics authorized by ADR-0476:
   - exactly 592 LF-only records: one header, 590 observations, and one terminal;
   - protocol, campaign, sequence, payload, semantic, record, and previous-record
     hash-chain identity;
   - exact authorization commit on every observation;
   - 569 structurally and type-valid calibration-cell wrappers, comprising 480
     warmup cells and 89 measured-labelled partial-pass cells;
   - `laboratory_wall_rejected`, `passed=false`, laboratory elapsed
     `1510053980800` ns against `1500000000000` ns, outside-laboratory elapsed
     `48722365700` ns against `300000000000` ns, public elapsed
     `1558776346500` ns against `1800000000000` ns, and exact partition sum;
   - zero authoritative measured calls, no fit projection, no selected candidate,
     topology, or arithmetic schedule, every governed downstream claim null, and
     truncation unauthorized; and
   - exact attempt and consumed-launch identities with pending and aborted launch
     paths absent;
5. reads historical source blobs with explicit `git show <commit>:<path>` calls;
6. never requires current HEAD to equal the historical authorization commit;
7. never imports or invokes the consumed v7 runner; and
8. returns a frozen `RetainedV7Assessment` whose negative terminal and incomplete
   campaign remain explicit.

The assessor is independent maintenance tooling. The exact sealed reader remains
the authority for what was accepted at the historical authorization checkout.
The assessor deliberately does not numerically validate, rank, aggregate, fit, or
admit the 569 partial cell payloads. Stored per-cell pass bits remain
nonauthoritative diagnostics.

## Test profile design

`tools/run_tests.py` is the canonical orchestration entry point. It is launched
with Python `-B -P`, accepts one named profile, captures one disposable execution
snapshot, and spawns every profile payload in a fresh child interpreter with an
explicit environment. It never imports test modules in the orchestration process
and never runs a test payload from the primary checkout.

Each profile names an interpreter slot rather than relying on `PATH`. The initial
slots are the resolved repository virtual-environment CPython and a separately
configured lowest-supported CPython 3.11 environment. The request records the
absolute executable, resolved executable identity, implementation, version,
prefix, and installed-distribution fingerprint (plus a dependency-lock digest if
the repository later adds one). Release `full` requires both supported
slots; a local developer profile may report an undeclared optional slot as
unavailable but cannot silently substitute another interpreter.

### Profiles

| Profile | Scope | Isolation |
| --- | --- | --- |
| `core` | active CPU domain and numerical-library behavior | fresh children in one captured current-state snapshot; no historical lifecycle suites |
| `current` | current integrations, import contract, stabilization boundaries, and retained-v7 assessment | fresh children in one captured current-state snapshot; lifecycle suites serialized |
| `historical` | sealed source-phase, authorization-phase, and retained-state controls | temporary local clones at manifest-declared commits, serialized |
| `gpu` | existing explicit CUDA integration and environment/capability checks | dedicated child in the captured snapshot with explicit GPU bootstrap; never implicit in `core` |
| `full` | orchestration of all applicable profiles | profiles run as separate processes; no shared imports |

`full` is not an alias for raw `unittest discover`. It aggregates profile results
and reports unavailable optional environments, such as a missing supported GPU,
as explicit skipped profiles rather than silently skipped tests. Required
profiles must pass; optional profile status remains visible. An unavailable GPU
does not fail `full` when `gpu` is declared optional, but it does fail an explicit
`gpu` request with the optional-environment-unavailable exit category.

Profile ownership is exclusive and applied in this order: the exact historical
matrix below, tests that require an actual GPU capability, an explicitly reviewed
fast hermetic CPU set for `core`, then every remaining applicable test in
`current`. Core tests may not use repository lifecycle state, Git mutation,
subprocess owners, environment mutation, CUDA/GPU imports, or retained experiment
fixtures. No prior aggregate count, including the earlier informal 72-test core
run, is treated as authoritative. The initial inventory must reconcile the 2367
statically observed direct methods with the earlier 2357-test discovery result;
the reviewed stable-ID lock, not either legacy count, becomes the contract.

### Test inventory and child protocol

`tests/test-inventory.json` is a normalized lock mapping every discovered stable
test ID to exactly one profile payload or to an explicit exclusion with reason,
owner, and review milestone. Stable IDs use repository paths and class/method
names rather than relying on `tests` as an importable package. The runner resolves
the entire inventory before execution and rejects a missing, duplicate,
multiply-owned, excluded-without-reason, or zero-test selector as configuration
failure. A changed discovery set requires an intentional inventory update.

The child command is structurally:

```text
<absolute-python> -B -P <harness-root>/tools/test_child.py
  --request <temporary-request.json>
  --result <temporary-result.json>
```

The harness root `H` is always the captured current-state snapshot containing the
new stdlib-only `test_child.py`. The target root `T` is `H` for core, current, and
GPU payloads, and the exact historical clone for historical payloads. The harness
is never copied into or imported through a historical target.

The child's working directory is `T`. Its constructed `PYTHONPATH` contains only
`T/src`; it does not contain `H`, `T` itself, `T/tests`, the primary checkout, or
an empty path element. `test_child.py` imports no `pontius` module from `H` and
loads its guard/bootstrap support by file-local stdlib code, so historical imports
resolve exclusively from `T`. Ambient Python path, home, startup, user-site, and
inspect variables are scrubbed case-insensitively. The runner sets
`PYTHONDONTWRITEBYTECODE=1`, `PYTHONSAFEPATH=1`, and `PYTHONNOUSERSITE=1` for
descendants, plus `PYTHONHASHSEED=0` and `PYTHONUTF8=1`, while retaining `-B -P`
where argv is itself contractual. The Windows environment is a documented minimal
allowlist containing the resolved interpreter and Git locations plus required
`SystemRoot`/`WINDIR`, `ComSpec`, `PATHEXT`, `TEMP`/`TMP`, and profile-declared
variables. No primary-checkout source, test, tool, configuration, or artifact path
may appear in child `sys.path`; the declared interpreter prefix and its
site-packages are the only permitted primary-tree exception. Child `TEMP` and
`TMP` point to a dedicated directory inside the disposable execution root, not to
the primary checkout.

Before importing tests, the child synthesizes a `tests` package whose only search
location is `T/tests`. It resolves each inventory ID directly to its
path, class, and method and instantiates exactly that `TestCase`; it does not use
`unittest discover`, `loadTestsFromModule`, or `loadTestsFromNames`. A fixed legacy
compatibility rule aliases `tests.test_reduced_river_sizing_oracle` to the same
module object under bare name `test_reduced_river_sizing_oracle` for the two
currently proven consumers and rejects any new bare `test_*` import.

The child writes one schema-versioned JSON result containing run ID, profile and
inventory digests, interpreter identity, sorted stable test IDs, per-test outcome
and duration, aggregate counts, capability-guard counters, captured-output
identities, and child status. Requested, prepared, and executed ID sets must match
exactly, with one terminal outcome per ID. The parent validates exact fields,
types, run ID, digest, and atomic completion. Raw `unittest` return codes and human
output are never treated as the protocol; in particular, a zero-test condition is
decoded as configuration failure rather than being confused with orchestrator
exit code `5`.

Historical non-test probes use stable `probe:` IDs in the profile definition and
the same result protocol. Probe code lives in the stdlib-only harness, while every
repository import and data path resolves against `T`. This permits exact-reader
reproduction without overlaying a new test or active evidence module onto an old
commit.

### Current-state snapshot

Core, current, and GPU profiles execute in one disposable snapshot outside
OneDrive. At run start the orchestrator captures HEAD, branch, index entries,
every tracked working-tree file, tracked deletions, and every non-ignored untracked
file using normalized repository-relative paths, file type, byte length, and raw
SHA-256. It rechecks those identities after capture and aborts as concurrent
workspace mutation if HEAD, index, or any captured path changed mid-snapshot.

The runner materializes the exact HEAD tree into a local clone created with
`--local --no-hardlinks --no-checkout`, reconstructs every primary index stage and
mode from its recorded blob bytes through Git plumbing, and only then overlays the
captured working-tree bytes and deletions. Ignored fixtures are excluded unless a
profile declares their path and immutable digest. It verifies HEAD, the complete
index, and the materialized file inventory before starting a child. No hard link,
junction, symlink, or reparse point may connect the snapshot back to the primary
checkout.

### Historical execution

Historical profiles use a temporary local clone rather than a linked worktree so
cleanup cannot leave shared `.git/worktrees` metadata in the OneDrive checkout.
The runner creates it with local `git clone --local --no-hardlinks --no-checkout`,
disables system and user Git configuration, sets checkout conversion explicitly,
checks out the declared commit detached, and never fetches from the network.
The profile definition declares:

- exact commit;
- test modules or methods;
- required tracked and untracked fixture state;
- allowed environment variables;
- per-stable-ID subprocess capabilities;
- interpreter flags;
- setup, child, termination-grace, cleanup, and total time budgets;
- required or optional capability status; and
- expected lifecycle phase.

Historical source, tests, policies, and configuration are verified as raw Git blob
bytes, independent of ambient `core.autocrlf`, `core.eol`, attributes, and user
configuration. If checkout conversion changes a governed file, it is
rematerialized from the exact blob and reverified before Python starts. Canonical
LF hashing is used only where the historical authorization protocol explicitly
defines it.

Only manifest-declared lifecycle-artifact roots may receive fixture overlays.
Every overlay entry records source path and immutable digest, destination, file
type, before/after identity, lifecycle phase, and collision policy. An overlay
cannot replace source, test, policy, or configuration bytes. An untracked current
file is never a historical fixture unless its exact digest is pinned in the
profile. The primary checkout is never used to simulate an earlier lifecycle
phase.

### Historical phase matrix

The initial historical profile contains these exact cases. “Recorded” counts are
historical evidence; all cases still require fresh contained verification during
implementation.

| Case | Exact commit/state | Exact selector contract | Expected vector |
| --- | --- | --- | --- |
| base source seal | `88148da07324c13b79c72ea494b14167a975c001` | all 21 methods of `CompiledGlobalSeparationSourceSealTests` in `tests/test_legal_river_quotient_compiled_global_separation_calibration.py` | 21 pass, recorded |
| v2 source seal | `08bb6857f47f9669b8f531c65079d4decd52a573` | all 8 methods of `AbsoluteGitCalibrationSuccessorTests` in `tests/test_legal_river_quotient_compiled_global_separation_calibration_v2.py` | 8 pass, recorded |
| v2 retained rejection | `3de8e0c9eebf67f2cc2573041242a869468de6e9` | all 5 methods of `CompiledGlobalSeparationCalibrationV2OutcomeTests`; do not load the v2 source-phase class | 5 pass required; fresh count/outcome verification |
| v3 source seal | `77feb7c78990ca53e70b1302a6866fe5d781411f` | all 9 methods of `CompiledGlobalSeparationCalibrationV3Tests` | 9 pass, recorded; this does not supersede ADR-0466's later uninvoked closure |
| v4 source seal | `ba6a3418b7c991238cc1a65898fd61fa03b4a3cb` | the 38 v4 methods other than `test_full_reader_journal_and_mutations_after_authorization` | 38 pass, recorded |
| v4 authorization rejection | `815d23c115289347e3d4028a4866eb9f87d4669a` | the same 38 positive methods plus exact method `test_full_reader_journal_and_mutations_after_authorization` as a separate child with `PONTIUS_ADR0467_AUTH_READER_CHILD=1` | 38 pass; negative method directly raises `ValueError` with the recorded header-domain reason; zero owner calls |
| v5 retained accidental attempt | `5c0c9a401e5f2ebf59296832d954d0075c4d4624` | all 18 methods of `CompiledGlobalSeparationCalibrationV5Tests` | 18 pass, recorded |
| v6 source seal | `d633f3fb469a27dee688587293c6efb1d2cb2757` | all 17 methods of `CompiledGlobalSeparationCalibrationV6Tests` | 17 pass, recorded |
| v6 authorization rejection | `cbfa3598f22c7aba7d824f71356ca156f8b01b0c` | the same 17 stable IDs as one expected-negative setup vector; never bypass `setUp` | 17 setup failures with the recorded v9-authorization presence reason, zero bodies entered, and zero owner calls |
| v7 source seal | `56127da2970f5a8a8056a97a247ebe1fdf4b983b` | all 20 methods of `CompiledGlobalSeparationCalibrationV7Tests` | 20 pass, recorded |
| v7 live authorization | `aaca2dda40e29be8ebd091d58e7853bce1c62fd8` | the same 20 methods | 20 pass required; fresh verification |
| v7 retained rejection | detached `aaca2dda40e29be8ebd091d58e7853bce1c62fd8` plus the three overlays below | harness-owned `probe:v7-sealed-reader-retained`; exclude the existing v7 class because its setup requires lifecycle absence. The new active-assessor unit test belongs to `current`, not this old target. | exact sealed-reader negative assessment with one probe outcome |

An expected-negative vector is a first-class historical outcome, not an ordinary
green test or a waived failure. The result records `expected_negative_matched`
only when the exact stable IDs, phase, exception type/reason contract, entered-body
count, and capability counters match. An unexpected pass or any different failure
fails the profile.

The v7 retained case is the only historical overlay. It materializes these bytes
from retention commit `a842c4b6a73a2991a63a481f4107580b72750582` without changing the detached
authorization HEAD or index:

- v7 attempt: 1825 bytes,
  `ada1896f0bf63111e0c1e5e707315fbca6c13f6e2b63222805cb5ef4cb9dc413`;
- v7 result: 7858857 bytes,
  `78b2f8351ca49785756ec336d4f967bcc83a86f9ef96506a6144726cf3b312b3`;
  and
- v7 consumed launch: 349 bytes,
  `c3c0a34cba6a677157034d8f8109cf47edea496a33c64992293176d879a2d629`.

Pending and aborted v7 markers remain absent. Every other phase uses the tracked
state at its exact commit; no profile simulates absence by deleting a later file.
Four synthetic-call exceptions are explicit:

- base method
  `test_synthetic_failure_journal_is_permanent_and_independently_readable`, v2
  method `test_synthetic_terminal_is_exclusive_and_independently_readable`, and
  the v3 method with that same name may call their temporary
  `execute_owner_to_path`; and
- v4 method `test_public_pre_writer_failure_consumes_the_attempt` may call patched
  `successor.main()` only against temporary clone-local lifecycle paths with the
  forced non-scientific pre-writer rejection.

No other historical stable ID may call an owner entrypoint.

### Subprocess capabilities

Historical tests that intentionally spawn Git or Python children receive a
deny-by-default capability per stable test ID. Each capability records:

- resolved executable role and identity (`python` or the declared Git binary);
- exact argv or a tokenized argv template whose only variables are validated
  snapshot/temp paths and fixed test values;
- required cwd class, environment additions/removals, timeout, and expected return
  category;
- permitted read and write roots; and
- whether one fixed descendant shape is allowed.

Dynamic `-c` programs are bound by raw SHA-256 or by a fixed template digest after
substitution. Arbitrary wildcards, shell execution, inherited primary-checkout
paths, undeclared environment keys, and breakaway descendants reject before
process creation. Every allowed child remains in the same Windows Job Object and
inherits no-bytecode/safe-path settings. The v4 authorization-negative payload
sets `PONTIUS_ADR0467_AUTH_READER_CHILD=1` itself, so it does not recursively launch
`unittest`; the expected result is the direct inner `ValueError`, not an outer
`AssertionError` derived from nested test output.

### Evidence guards

Before and after every profile, the orchestrator verifies retained artifact
identity. It fails closed if identity changes, even when all tests pass. The final
summary includes profile, interpreter, duration, test counts, result, and evidence
guard result. Child capability guards deny every write to the primary repository
root and report attempted paths. If the live checkout changes after snapshot
capture, the runner classifies it as concurrent workspace mutation, discards the
affected result, and never tries to restore or overwrite the user's state.

### Timeout and process containment

All stage budgets use a monotonic clock. The total profile budget covers snapshot
or clone preparation, fixture verification, child execution, evidence checks, and
cleanup; it must reserve at least the configured termination and cleanup budgets,
so child execution cannot consume them. Positive setup, child,
graceful-termination, and cleanup sub-budgets make the failure stage explicit. On
Windows, each child is created suspended, assigned with all descendants to a Job
Object that forbids breakaway and is configured for kill-on-close, then resumed.
Timeout handling requests graceful termination, drains output, then terminates
the complete job after the declared grace period and confirms every descendant
exited before post-run evidence checks. Cleanup retries Windows locked-file
failures with a bounded backoff, validates the resolved temporary target on every
attempt, and reports cleanup exhaustion as a runtime failure. A POSIX adapter
provides the equivalent process-group contract.

### Child capability guards

The child bootstrap installs profile-specific guards before importing any test
module and emits explicit event counters in its structured result:

- `core` and `current` deny imports of `cupy` and `cupyx`, calls through declared
  CUDA device/query/allocation adapters, calls to v2-v7 public owner entrypoints,
  and writes to retained lifecycle paths;
- `historical` denies real scientific execution and writes outside its disposable
  clone, while allowing only the exact synthetic owner-contract calls declared by
  commit and stable test ID in the profile. Compiler/device launch, public
  campaign mode, production lifecycle paths, and undeclared subprocesses remain
  denied; and
- `gpu` permits declared GPU adapters but continues to deny historical owner
  entrypoints and retained lifecycle writes.

Denied operations are recorded before raising `RuntimeContractError`. Acceptance
uses the counters, not merely `sys.modules`, final files, or the absence of a
terminal marker, to prove that forbidden operations did not occur. The historical
allowlist is deny-by-default and is resolved in full before any test module is
imported.

## Error and exit semantics

Active libraries raise typed exceptions and never call `print`, `exit`, or
`SystemExit`:

- `EvidenceConfigurationError`: malformed manifests or profile definitions;
- `EvidenceIntegrityError`: byte, digest, journal-chain, or historical-source
  mismatch;
- `AuthorizationPhaseError`: invalid or mixed authorization state;
- `LifecycleStateError`: lifecycle state conflicts with the selected profile;
- `RuntimeContractError`: interpreter, environment, Git, or subprocess contract
  violation.

Exceptions contain a stable code, concise message, and immutable context mapping.
They preserve their original cause while excluding secrets and launch tokens.
Composition roots translate them into one structured stderr diagnostic and a
stable nonzero exit category. Test assertion failures remain distinct from
configuration, integrity, and environment failures.

The command-line exit categories are:

| Code | Meaning |
| --- | --- |
| `0` | all required work passed; optional profiles may be explicitly unavailable |
| `2` | invalid manifest, inventory, profile, or command configuration |
| `3` | evidence, retained-byte, journal, or historical-source integrity failure |
| `4` | authorization or lifecycle phase failure |
| `5` | runtime, Git, interpreter, timeout, or malformed-child-result failure |
| `6` | collected tests ran and failed |
| `7` | an explicitly requested optional environment is unavailable |

Capability absence means a successful, schema-valid probe proved that a declared
optional dependency is not present. A crashing, timing-out, or malformed probe is
a runtime failure, not optional unavailability. `full` returns `0` when all
required profiles pass and an optional GPU is validly unavailable; directly
requesting that same `gpu` profile returns `7`.

When more than one condition occurs, evidence-integrity failure takes precedence,
followed by configuration, authorization/lifecycle, runtime, test failure, and
optional-environment unavailability. The structured summary records every
observed condition even when only one category can be returned. Configuration is
validated before creating a child. An integrity, authorization/lifecycle, or
runtime-safety failure cancels later payloads after contained process termination
and evidence checks; their status is `not_run_safety_stop`. Ordinary test failures
do not hide results from already independent payloads, so the default aggregate
continues them and returns `6` after cleanup. User cancellation records
`cancelled`, terminates the active job, verifies evidence, and returns runtime
category `5`. Cleanup exhaustion is category `5` unless retained evidence changed,
which takes category `3` precedence.

## Security and safety

- Repository-relative paths are parsed as data and resolved below an explicit
  root before use.
- Git commands use argument vectors, an explicit repository directory, and no
  shell interpolation.
- Every snapshot or clone cleanup validates the exact absolute target beneath the
  OS temporary directory.
- The profile runner removes lifecycle variables unless the profile explicitly
  declares them.
- Launch tokens are never printed, persisted in summaries, or included in
  exception context.
- No tool accepts a flag that invokes a historical public owner.
- Network access is unnecessary for test execution; local clones use the existing
  repository as their source.

## Verification strategy

Implementation follows test-driven slices. Each behavior is first demonstrated
by a focused failing test, then implemented minimally, then verified broadly.

### Authorization regression checks

1. A preauthorization state supplied where live authorization is required raises
   `AuthorizationPhaseError`, never `KeyError`.
2. A deterministic changing-file double returns two different valid snapshots if
   called twice. The reader must call it once and must return a digest matching
   the exact bytes compared with Git.
3. Mixed filesystem/tree/index states reject.
4. Canonical-LF-equivalent but raw-byte-different working and Git blobs reject.
5. Tests that replace the path, mutate the opened file, advance HEAD, or change
   the index between initial and final validation all fail closed.

### Retained-assessor checks

1. The exact retained v7 files produce the recorded negative assessment from
   current HEAD.
2. One-byte mutations of every retained file reject without modifying the real
   artifact.
3. Missing, extra, duplicate, or wrongly typed manifest fields reject; mapping key
   order has no semantic meaning.
4. Journal-complete and scientific-campaign-complete remain distinct.
5. Stored partial-pass measured-labelled rows never become authoritative measured
   calls.
6. The assessor imports no v7 owner and creates no lifecycle file.

### Profile-runner checks

1. Children observe effective `-B` and `-P`.
2. Test collection order cannot preload science into a freshness-sensitive child.
3. Current profiles do not assert historical lifecycle absence.
4. Historical profiles execute with the declared target commit/root-tree OID,
   current harness root outside the target, target-only repository imports, and no
   harness or active-layer overlay.
5. A child failure, timeout, malformed result, or retained-hash change produces the
   correct exit category.
6. Running the current profile twice yields the same profile-definition digest,
   sorted test IDs, per-test outcomes, counts, and aggregate outcome.
7. Snapshot hashes equal the captured current-state inventory, no child sees a
   primary-checkout code/data path, no primary-root write event occurs, and
   retained hashes remain unchanged.
8. Capability-guard counters prove zero forbidden imports, adapter calls, owner
   calls, and lifecycle writes for each profile.
9. A synthetic timeout with a Python grandchild terminates the complete Windows
   Job Object, drains output, confirms descendant exit, and performs bounded
   cleanup before returning.
10. Every discovered stable test ID is owned exactly once or explicitly excluded;
    missing, duplicate, and zero-test selectors reject before execution.

### Architecture-boundary checks

1. Every new or changed active module and every exact historical-boundary path has
   one stabilization classification.
2. The complete legacy edge set and SCC membership match their mechanical
   baseline unless an intentional changed stabilization module is the origin.
3. Imports originating in new or changed evidence modules match the exact
   stdlib/sibling/journal-seam allowlist and every declared deny rule.
4. The orchestration parent remains stdlib-only and imports neither `pontius`,
   tests, GPU/CUDA modules, nor historical owners/readers.
5. No new or expanded internal import SCC is introduced; the existing
   `action_clock.py` ↔ `preparation_bank.py` SCC remains visible but is not a
   stabilization remediation gate.

## Acceptance criteria

This milestone is complete only when all of the following have fresh evidence:

1. Git diff contains no modification or deletion of any path in
   `sealed-current-files.toml`, and every recorded current-byte identity still
   matches.
2. Recorded retained-v7 sizes and SHA-256 digests match before and after every
   profile.
3. The new authorization tests reproduce the legacy failure modes and pass through
   the active typed API.
4. The current profile passes twice in independent interpreters with identical
   profile-definition digest, sorted test IDs, per-test outcomes, and counts.
5. The core profile passes without importing CuPy or querying or allocating a CUDA
   device. Any existing package-level DLL-directory bootstrap is measured and
   reported but remains unchanged until the deferred package-import milestone.
6. Historical profiles pass at their exact declared commits without touching the
   primary checkout; governed source, test, policy, and configuration bytes equal
   their recorded Git blobs regardless of ambient Git settings.
7. The retained-v7 assessor returns `laboratory_wall_rejected`, `passed=false`,
   `journal_complete=true`, `scientific_campaign_complete=false`, and
   `authoritative_measured_call_count=0` from current HEAD.
8. Core, current, and GPU profiles report zero consumed-owner calls. Historical
   profiles report only manifest-declared synthetic contract calls, zero real
   scientific-executor calls, zero writes outside the disposable clone, and no new
   primary-checkout lifecycle marker.
9. Every touched module and historical-boundary path is classified, the complete
   legacy edge/SCC graph is mechanically baselined without semantic ownership, and
   new stabilization imports obey their exact policy with no new or expanded SCC.
10. README and RUNBOOK name the profile runner as canonical and explain why raw
    one-process discovery is not authoritative.
11. Ruff/static checks for changed active code pass.
12. A repository-owned independent review of the exact diff contains no unresolved
    valid blocking or major issue; available CodeRabbit findings receive the same
    triage.

## Independent review gate

The deterministic gate is a repository-owned read-only review of only files added
or changed since the recorded baseline, including active source, tests, tools,
manifests, and documentation; unchanged historical blobs and generated artifacts
are excluded. CodeRabbit runs over the same exact scope as an additional requested
review. Its run has a 20-minute wall timeout and records the tool/plugin version,
model when reported, UTC timestamp, exact file scope, raw output location, and
baseline commit.

Every finding receives one disposition: `fixed`, `rejected-with-evidence`, or
`deferred-with-approved-owner-and-milestone`. A valid blocking or major finding
cannot be deferred from this stabilization milestone. CodeRabbit unavailability
or timeout is reported explicitly and never represented as a successful
CodeRabbit run, but it does not erase fresh repository-owned review evidence.

## Delivery slices

1. Add the three exact history-boundary manifests, dependency baseline, test
   inventory, and retained-v7 manifest plus tests.
2. Add typed errors, evidence models, and single-snapshot authorization reader.
3. Add retained-v7 assessor through the generic journal seam.
4. Add profile definitions and the process-only orchestration runner.
5. Add exact-commit historical execution and evidence guards.
6. Add stabilization-boundary and no-new-dependency-regression enforcement.
7. Update current test documentation and run the complete stabilization matrix.

Each slice must preserve sealed current bytes, pass its focused tests, and execute
test payloads only inside disposable snapshots or clones.

## Risks and mitigations

### Historical clone cost

Local clones add disk and wall time. Historical profiles therefore remain outside
the fast core profile, use `--no-hardlinks` to avoid mutable object-file sharing,
and clean only verified temporary paths.

### Maintenance assessor misunderstood as scientific authority

Naming, types, documentation, and output explicitly identify it as a retained
maintenance assessment. It cannot produce a passing calibration result or owner
authorization.

### Incomplete module classification

The history boundary and every new or changed module require exact classification;
untouched modules retain a mechanically captured import-graph baseline without a
premature semantic label. Existing legacy edges and SCCs are visible but are not
granted architectural approval. Removing them and completing repository-wide
semantic ownership are architecture work, while new stabilization code must obey
its narrow exact policy.

### Python implementation and version drift

The project currently declares Python 3.11 or newer while development uses Python
3.14. Stabilization verification covers the lowest supported CPython and the
current development runtime. Support for other Python implementations is not
claimed without a separate compatibility decision.

### OneDrive and Windows reparse behavior

The primary Windows/OneDrive checkout remains part of acceptance. Temporary
historical clones live outside OneDrive, and evidence checks retain explicit
non-symlink and non-reparse validation where required by the historical contract.

## Deferred work

After this milestone is green, separate specifications cover:

1. side-effect-free package imports, packaging metadata, and explicit CUDA
   bootstrap;
2. bounded term-axis GPU contractions and active-path residency;
3. structurally shared policy tapes and candidate overlays;
4. bounded NumPy reductions and legacy GPU-path retirement;
5. GPU allocation ceilings, synchronization-count checks, and performance
   benchmarks;
6. elimination or redesign of baselined dependency exceptions and import cycles;
   and
7. the final holistic architecture review and V0a migration backlog.
