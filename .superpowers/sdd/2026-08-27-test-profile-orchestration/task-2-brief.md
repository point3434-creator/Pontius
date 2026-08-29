### Task 2: Generate the Exact Inventory and Profile Ownership Lock

**Files:**

- Create: `tools/generate_test_inventory.py`
- Create: `tests/test-inventory.json`
- Create: `tests/test-profiles.toml`
- Create: `tests/test_inventory_and_profiles.py`
- Modify: `tools/test_orchestration/configuration.py`
- Modify: `tools/test_orchestration/model.py`

**Interfaces:**

- Consumes: Task 1 strict configuration/models, baseline Git tree `a842c4b6a73a2991a63a481f4107580b72750582`, and working-tree Python test sources parsed only by AST.
- Produces: `tools/generate_test_inventory.py` with default `--check`, explicit inventory `--write`, `--emit-design-capability-review <absolute-temp-path>`, and `--write-design-capabilities --approved-spec-capabilities-sha256 <digest>`; canonical `tests/test-inventory.json`; independently preapproval-capable design and historical scopes in `tests/test-profiles.toml`; and exact inventory/profile digests consumed by every parent/child request.

- [ ] Write failing synthetic-tree tests for AST discovery, direct-method formation, sorted canonical output, duplicate/missing/multiple ownership, unknown payloads, exclusions missing reason/owner/milestone, zero-test selectors, discovery drift, fully expanded scope-partitioned capability digest semantics, both-zero preapproval, token-gated design approval followed by historical-only preapproval, profile-selection refusal for every unapproved applicable scope, cross-scope sharing, digest/row mismatch, dangling/unused capability definitions, and mutations of referenced argv, environment, root, timeout, callable module/qualname, maximum-call, or return-contract fields.

- [ ] Implement deterministic AST discovery of direct `test_*` methods in explicit `unittest.TestCase` subclasses without importing tests. Discover the recorded baseline from Git commit `a842c4b6a73a2991a63a481f4107580b72750582` separately from the implementation working tree. Lock this baseline partition:

In the same AST pass, record exact `setUpModule`/`tearDownModule` and class-local `setUpClass`/`tearDownClass` definitions and emit the module/class lifecycle fixture rows above without adding synthetic test IDs to the 2,367 count. Reject inherited/ambiguous fixture ownership, a fixture spanning payloads, or differing class-level grants among grouped member IDs.

```text
test files:             392
stable IDs:             2367
all-ID digest:          c8e6465527a9b784f4be41947745f6e86d53f45d16fd0d10955009bbb127b37b
historical IDs:         137
historical digest:      77ccf22ac1f52ebbeff7311bf2c4c1fb4f83671a5cfe10f84dbbde655ecb58a8
GPU IDs:                51
GPU digest:             896fb0675371186476df33b13eb7a5d9286dfeb01f53d37daa0f458e72021005
core IDs:               50
core digest:            38166290ad900c24a08c93f08de3376dac92a2c35544a94c3228726b01a02dfc
current IDs:            2129
current digest:         c32575a47a889e7e324db2abb56ef5c5b37295bb6a5cc3e6006cb04c767c6803
explicit exclusions:    0
```

Every digest is SHA-256 of sorted stable IDs joined with LF plus a final LF. The 2,367 lock intentionally supersedes the earlier 2,357 one-process discovery count. New evidence/orchestration test methods are not part of those baseline counts; they are intentionally appended to the final current inventory and receive their own generated count/digest.

- [ ] Assign ownership in this exact order:

  1. Historical: every direct method in the eight exact compiled-global-separation classes from base through v7. Map each ID once to a version payload; a multi-phase payload may execute the same selector at multiple declared commits.
  2. GPU: every method in a class/method carrying the literal `find_spec("cupy")` optional-capability decorator; every method in a class that directly imports `cupy`; and the three methods of `tests/test_legal_river_quotient_cuda_consumer.py::LegalRiverQuotientCudaConsumerDeviceTests`, whose class setup calls the real bounded CUDA consumer. Materialize the resulting exact 51 IDs in the lock; do not reclassify automatically when source changes. Keep all 18 `SharedDirectDeviceSourceSealTests` in current because they explicitly assert CuPy-free/device-free source-seal behavior.
  3. Core: all direct methods in exactly `tests/test_cfr.py`, `tests/test_coalition.py`, `tests/test_evaluation.py`, `tests/test_holdem_cards.py`, and `tests/test_kuhn.py`. This is the deliberately narrow reviewed 50-ID hermetic CPU set.
  4. Current: every remaining applicable ID, exactly 2,129 at baseline.

Every new test file named in either implementation plan is explicitly classified as stabilization/current. A new test outside that reviewed file list, a changed baseline ID, or a changed baseline assignment makes `--check` fail and requires an intentional reviewed inventory/profile update.

- [ ] Emit `tests/test-inventory.json` in canonical UTF-8 JSON with schema `pontius-test-inventory-v1`, baseline commit, exact `baseline_discovery`, exact working-tree `discovery`, and one sorted entry per working-tree ID. Each entry has exactly one `assignment` object or one full `exclusion` object. Baseline entries also record their locked baseline assignment; added stabilization entries record `introduced_after_baseline=true`. Group current/core payloads by test file and GPU payloads by test class so class setup is isolated.

Each `assignment` has exact keys `profile_name`, `payload_id`, and `expectation`. Expectation is one strict variant: `{kind: "pass"}`; `{kind: "platform_conditioned", applicable_platforms: ["windows"|"posix"], skip_safe_reason_code: <stable string>}`; or `{kind: "case_defined"}` for historical IDs only. `applicable_platforms` is sorted/unique/nonempty. Each full exclusion has exact keys `reason`, `owner`, and `milestone`. Each entry also carries its parsed `relative_path`, `case_name`, and `method_name`; `load_configuration` joins entries by `payload_id` into the sorted `PayloadPlan.inventory_items` tuple and retains every validated entry in `ConfigurationBundle.inventory_entries`. Historical ChildRequest items come from the selected case's item expectations, never from a default pass assumption.

- [ ] Define interpreter slots in `tests/test-profiles.toml`: `development` resolves the repository-relative `.venv/Scripts/python.exe` only on Windows and `.venv/bin/python` only on POSIX; any other platform or missing/nonregular executable rejects. `cpython311` resolves only the absolute path in `PONTIUS_CPYTHON311` and requires CPython version `(3, 11)`. `full` requires both. No slot uses ambient `PATH` fallback.

The profile TOML requires exact schema literal `pontius-test-profiles-v1` and has only these top-level keys/tables: `schema_version`, `baseline_commit`, `sealed_current_files_manifest`, `sealed_current_absences_manifest`, `historical_blobs_manifest`, `retained_v7_manifest`, `inventory_path`, `spec_capabilities_sha256`, `capability_bindings_sha256`, `interpreter_slot[]`, `profile[]`, `payload[]`, `historical_case[]`, `overlay[]`, `subprocess_capability[]`, `call_capability[]`, `capability_binding[]`, and `stabilization_test_files`. Each binding has `approval_scope="design"` or `approval_scope="historical_review"`. `spec_capabilities_sha256` covers canonical sorted fully expanded nonempty design-scope bindings whose `item_id` is a core/current/GPU stable ID, lifecycle fixture, or probe; `capability_bindings_sha256` analogously covers nonempty historical-review bindings. The inventory/profile digests bind the complete item universe, and every item absent from the applicable capability bindings is explicitly deny-all—no synthetic no-op capability row is invented. A subprocess record contains its binding plus every stable `subprocess_capability[]` field, including executable role/slot/constraints, argv/template and dynamic-program digest, cwd class, environment delta, timeout, expected return category, allowed/forbidden roots, and descendant permission. A callable record contains its binding plus every `call_capability[]` field: kind (`owner`, `scientific`, `cuda_query`, or `cuda_allocation`), module/qualified name/action, exact maximum calls, and return contract. DLL-directory telemetry is an unconditional non-authorizing preparation observation rule in the guard, never a capability binding or digest row. Host-specific resolved paths, file IDs, and executable hashes are excluded from both checked-in digests; they are measured into `InterpreterIdentity`/`GitToolIdentity`, bound into each runtime request, and independently verified by the child.

Initially both scope definitions/bindings are absent and both digests are the all-zero 64-hex value. Only Task 2's separately parsed design-review generator may operate then; it cannot select a profile, import/launch target code, or write repository state. After the user approves the complete emitted design table/digest and the token-gated write succeeds, core/current/GPU may run with a nonzero `spec_capabilities_sha256` while historical rows remain absent and `capability_bindings_sha256` remains all-zero. Selecting any profile whose applicable scope is unapproved raises `EvidenceConfigurationError("capability_approval_required", "applicable capabilities are not approved")`. Task 10's separately parsed historical-review generator is the only preapproval exception for that scope; it may read historical case metadata and materialize exact read-only proposal clones but never calls `select_profile`, imports target code, or launches a historical payload. Approved historical mode requires a nonzero user-approved historical digest and complete rows whose expansion hashes to it. A capability definition may belong to exactly one scope; reject cross-scope sharing, mixed modes, dangling references, unused definitions, duplicate expanded semantics, missing applicable bindings, a wrong digest, or any mutation that does not change the applicable digest.

The non-capability nested schemas are exact:

```text
development interpreter_slot:
  name="development", resolution="repository_relative",
  windows_relative_path, posix_relative_path, implementation,
  minimum_version=[exact-int, exact-int], required_for_full=exact-bool
exact interpreter_slot:
  name, resolution="environment_absolute", environment_variable,
  implementation, exact_version=[exact-int, exact-int],
  required_for_full=exact-bool
profile:
  name, interpreter_slots, default_interpreter_slot, payload_ids,
  historical_case_ids, subprofiles, gpu_optional,
  budgets={setup_seconds, child_seconds, termination_seconds,
           cleanup_seconds, total_seconds}
payload:
  payload_id, profile_name, target_kind, allowed_interpreter_slots, probe_ids,
  environment_additions, environment_removals, allowed_write_roots,
  forbidden_relative_paths, serialized, ignored_fixture[], lifecycle_fixture[]
payload ignored_fixture:
  relative_path, path_kind, byte_length, raw_sha256
payload module lifecycle_fixture:
  fixture_id="fixture:<relative-path>", kind="module", relative_path,
  member_ids, allowed_write_roots, forbidden_relative_paths, serialized
payload class lifecycle_fixture:
  fixture_id="fixture:<relative-path>::<ClassName>", kind="class",
  relative_path, class_name, member_ids, allowed_write_roots,
  forbidden_relative_paths, serialized
historical_case:
  case_id, phase, commit, root_tree_oid, payload_ids, overlay_ids,
  expected_vector, item_expectation[]
historical pass item_expectation:
  item_id, outcome="pass"
historical negative item_expectation:
  item_id, outcome="expected_negative", phase, exception_type,
  safe_reason_code, body_entered, capability_counters
historical probe item_expectation:
  item_id="probe:<registered-name>", outcome="pass"
positive expected_vector:
  kind="positive", passed, assertion_failed, setup_failed, body_entered,
  owner_calls, scientific_calls
negative expected_vector:
  kind="negative", passed, assertion_failed, setup_failed, body_entered,
  owner_calls, scientific_calls, phase, exception_type, safe_reason_code
overlay:
  overlay_id, source_commit, source_path, destination_path,
  byte_length, raw_sha256
```

Every named array is sorted and unique; `argv` remains the later explicit ordered-token exception. Environment additions are sorted string mappings. Counts/seconds/lengths are exact nonnegative integers (budgets are positive), booleans including `serialized` are exact, paths are normalized to the declared root class, and every reference resolves exactly once. A direct profile's `default_interpreter_slot` is nonnull and belongs to both its `interpreter_slots` and every selected payload's `allowed_interpreter_slots`; `full` has a null default and projects each subprofile once per scheduled binding. Lifecycle fixture member IDs must belong to the same module/class and payload, and every owned module/class fixture is represented exactly once even when it has no positive capability. Direct profiles have empty `subprofiles`; `full` has only `subprofiles` and no direct payload/case IDs. `load_configuration` resolves each profile's `fixture_specs` as the conflict-free union of its referenced payload fixtures; `full` resolves the union of constituent profiles.

Every `HistoricalCase.payload_ids` row is a sorted nonempty unique tuple. Each case item expectation resolves through inventory to exactly one of those payloads, and every named payload owns at least one case item/probe. The engine launches one fresh child per payload and then validates the aggregate `expected_vector`. In particular, the v4 authorization case names distinct `historical:v4-positive` and `historical:v4-authorization-negative` payloads: the 38 positive IDs belong only to the first, the one negative ID only to the second, and the environment flag is granted only to the negative child's exact item capability.

- [ ] Lock these positive profile budgets in seconds, converting once to nanoseconds during parsing:

| Profile | Setup | Child | Termination | Cleanup | Total |
| --- | ---: | ---: | ---: | ---: | ---: |
| `core` | 180 | 900 | 15 | 120 | 1500 |
| `current` | 300 | 7200 | 15 | 180 | 8100 |
| `historical` | 900 | 5400 | 20 | 300 | 7200 |
| `gpu` | 300 | 3600 | 20 | 180 | 4500 |
| `full` | 900 | 27000 | 20 | 300 | 29000 |

`core` and `current` declare both `development` and `cpython311` as allowed, with `development` as their direct default. `historical` and `gpu` allow/default only `development`. `full` schedules core/current once on each supported binding, historical on development, and GPU on development as optional. The selected binding is authoritative for its projected payload rows; no stale payload-level development literal survives a CPython 3.11 projection.

- [ ] Lock the historical selector digests and case grouping:

```text
base source: 21 / 83a33794ecf850587627ace90a9d3a208b82fcf875400ccb6ed7c5cd72cb6e81
v2 source: 8 / 3645c2e5636e658167aafbcac4da1031ebf784416f4c12f05b56e3f9dd87fc9c
v2 retained: 5 / da4886b2674e687b6c336303cb430b8c4d214a1f274db2df23c4a01137415467
v3 source: 9 / 00a4caad1791a20720d133be06f50a9a422a8b691294db4196a5780ae2100813
v4 positive: 38 / 676f497cdedaa8958e96bfefc63808f9335f897621fb8f1d65a0835bfc4bc6f3
v4 negative ID: fa7790a99fecb14eddd78316b017ab7dc82c699866cc851e1d27b97239b52c52
v5 retained: 18 / f927b8680c80739d04b64c667d757377c05723ec7eab25a224ba31bacdc4843d
v6 phases: 17 / 30d6a566cc57298e593a0fa7ac8d66890ad86cdc03df25aca2e1e9915cd7ec7d
v7 phases: 20 / 6f62dc5b6cd8b61709d9ef148384fa9cf319d54b88281d6ea45245496852112c
```

Every historical case also stores the exact root-tree OID and must match the evidence manifest:

```text
88148da07324c13b79c72ea494b14167a975c001  bc5d1952f690da5d49275344919de36224af26cb
08bb6857f47f9669b8f531c65079d4decd52a573  0d01a4133a4e6ab10467ad0bd298630149702a73
3de8e0c9eebf67f2cc2573041242a869468de6e9  ea80b86ac60cb324e3c18ddad83d8bbba0ade933
77feb7c78990ca53e70b1302a6866fe5d781411f  d26ba99c033875342a652ae352067beee1ca44ee
ba6a3418b7c991238cc1a65898fd61fa03b4a3cb  73b53cb04c91459e8b7028ccd292b972d2dfdf69
815d23c115289347e3d4028a4866eb9f87d4669a  894c026603156df4bba1134ba9861e98bd3a6663
5c0c9a401e5f2ebf59296832d954d0075c4d4624  f3418410c442a4d06c62aba9777def72633ca5c5
d633f3fb469a27dee688587293c6efb1d2cb2757  9c9ff658c2836bde5d1df71f5596d1d6aa1a5bd2
cbfa3598f22c7aba7d824f71356ca156f8b01b0c  9873ff13131c91b058307643dc838a8452268fbb
56127da2970f5a8a8056a97a247ebe1fdf4b983b  ee2437ba1b2efbf2dc4ab3c21bbacdbf26c58648
aaca2dda40e29be8ebd091d58e7853bce1c62fd8  e7bd077f40b1970e9b40a83c891996ab02cd5ffd
```

- [ ] Add exact overlay and capability schemas to the profile TOML. A subprocess capability contains portable executable role/slot/constraints, exact argv or fixed tokenized template, dynamic-program digest for `-c`, cwd class, environment additions/removals, timeout, expected return category, read/write roots, and fixed-descendant permission. A call capability contains exact kind/module/qualified-name/action/maximum-call/return-contract fields. Runtime executable identity is never a checked-in field. Start with both scopes absent and both digests all-zero. The design review generator statically derives the complete core/current/GPU stable-ID, fixture-ID, and probe-ID subprocess/call surface—including current source-seal subprocess tests and exact CUDA query/allocation calls—while DLL bootstrap remains only a hard-coded non-authorizing observation rule. Wildcards and shell commands are invalid. Task 10 alone may later populate historical-review rows through its separate approved write command after exact historical-clone materialization exists.

`SubprocessCapability.executable_slot` is exactly `active_worker`, `development`, `cpython311`, or `git`. A target call to `sys.executable` uses `active_worker`; expansion binds its runtime executable field byte-for-byte to the enclosing child/worker `InterpreterBinding.identity`, so the same approved portable row works when core/current are projected under CPython 3.11. Fixed Python slots are permitted only when the reviewed test intentionally invokes a different configured interpreter. `git` binds only the request's measured `GitToolIdentity`. Any mismatch between role/slot/constraint and the measured runtime identity rejects before spawn.

- [ ] Run inventory `--write`, inspect all 2,367 baseline assignments and every then-present stabilization assignment, and prove `--check` plus focused tests pass in a new snapshot while both capability scopes remain absent/all-zero. Implement and test the two design-review/write commands now, including static AST/literal extraction, fail-closed no-target-spawn behavior, the complete nonempty stable/fixture/probe binding table plus a separately enumerated deny-all item list bound by inventory digest, unresolved-dynamic blockers, host-specific diagnostics outside the digest, fresh rederivation, token mismatch refusal, atomic scope-only write, and preservation of the other scope. Do not emit for approval or write design rows yet: Tasks 3-11 intentionally add current-owned process/guard/workspace tests. Task 12 performs one final emission/approval/write over the complete stabilized ID universe. Ordinary inventory regeneration must preserve/revalidate any approved scope; drift always requires a new emitted review and token, never reset or auto-approval.

- [ ] Review checkpoint: run `git diff --check`. With explicit commit authorization only, create `build(testing): lock stable test ownership`.

---

## Controller-approved corrections — 2026-08-27

The user explicitly approved all corrections below. They preserve the locked
baseline partition (51 GPU IDs and 2,129 current IDs) and do not authorize any
capability table write in Task 2.

1. Refactor
   `tests/test_h32_pre_bet_initial_row_cache_seed.py::H32PreBetInitialRowCacheSeedTests`
   from class-local `setUpClass` state to equivalent per-test `setUp` state.
   This removes the only lifecycle fixture split across payloads without moving
   any stable ID. Add a RED/GREEN AST ownership regression before changing the
   source.

2. Add the exact `declared_unconditional_skip` inventory expectation variant.
   It has an empty `applicable_platforms` model value and one nonempty
   `skip_safe_reason_code`; its serialized inventory object has exactly `kind`
   and `skip_safe_reason_code`. It is valid only when static AST derivation finds
   an outer literal `unittest.skip(<literal string>)`. The literal, code, and
   SHA-256 must match one of these two rows exactly:

   - `tests/test_h32_pre_bet_action_width_capacity.py::H32PreBetActionWidthCapacityTests::test_small_runtime_composition_keeps_candidate_at_current_node`;
     literal `sealed rejected runner is retained byte-for-byte and never rerun`;
     code `sealed_rejected_runner_never_rerun`; literal SHA-256
     `50af0f964e7e6b2fd708e85b3cff20b9c073c3d8cb084b65033f333fefbf6f57`.
   - `tests/test_h32_pre_bet_initial_row_cache_seed.py::H32PreBetInitialRowCacheSeedTests::test_small_gpu_seed_round_trips_both_distinct_arms_without_optimizer_work`;
     literal `ADR-0281 seed authority is revoked; its GPU path is never invoked`;
     code `revoked_adr_0281_gpu_path_never_invoked`; literal SHA-256
     `aa949216ccc291eab69a7eca888eb7e0fa5f43c804099bf6cf51c6fde9429909`.

   Later child execution must map this variant to `expected_skip` with a `never`
   predicate, require `body_entered=false`, zero capability counters, and the
   exact safe reason. It does not authorize dependency- or runtime-conditioned
   skips.

3. Require an absolute `PONTIUS_GIT` executable. Reject missing, relative,
   nonregular, symlink/reparse, or identity-changing executables; never fall back
   to `PATH`. Read baseline sources as Git blobs through this measured tool.

4. Keep `spec_capabilities_sha256` as the canonical expanded nonempty design-row
   digest, but require a second token for the eventual write command:
   `--approved-design-review-receipt-sha256 <digest>`. Hash sorted-key compact
   ASCII JSON with no trailing LF and exact schema
   `pontius-design-capability-review-receipt-v1`. The object binds
   `approval_scope`, baseline commit/root-tree OID, canonical inventory semantic
   digest, canonical inventory-document SHA-256, canonical-LF derivation-source
   rows (`relative_path`, `byte_length`, `canonical_lf_sha256`), the design row
   digest, fully expanded rows in the ruled total order, and explicit deny-all
   rows sorted by `(item_kind,item_id)`. Host diagnostics and the receipt digest
   itself are excluded. Emit and write each use one identity-bound source
   snapshot; either token drift requires renewed approval.

5. `.gitattributes` now pins the baseline, inventory, and profile governance
   files to LF. Task 2 must verify those exact rules and use binary atomic LF
   writes; semantic/review identities always use canonical LF bytes.

6. Controller ruling for the previously underspecified v7 overlay identifiers:
   use the hierarchical convention `overlay:<case-slug>:<artifact-kind>`. The
   exact sorted identifiers are `overlay:v7-retained:attempt`,
   `overlay:v7-retained:consumed-launch`, and
   `overlay:v7-retained:result`. Each row uses retention source commit
   `a842c4b6a73a2991a63a481f4107580b72750582`, identical source/destination
   paths from `retained-v7.toml`, and the already approved byte lengths and raw
   SHA-256 values. Tests and the Task 2 report must lock this convention for
   Task 10 consumption.

7. Historical negative vectors must use the exact plan semantics, not
   placeholders. The v4 negative item uses phase `body`, exception
   `ValueError`, safe reason `deferred-import header domain differs`, and
   `body_entered=true`; its aggregate is 38 passed, zero setup failures, and 39
   bodies entered with zero owner calls. The v6 negative items use phase
   `setup`, exception `AssertionError`, safe reason code
   `v6_authorization_path_present`, and `body_entered=false`; the aggregate is
   17 setup failures, zero bodies entered, and zero owner calls. Failure phases
   are only `setup`, `body`, or `probe`; `authorization` is not a valid phase.
