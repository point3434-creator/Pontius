### Task 11: Baseline Legacy Dependencies and Enforce New Boundaries

**Files:**

- Create: `tools/generate_dependency_baseline.py`
- Create: `tools/check_stabilization_boundaries.py`
- Create: `docs/architecture/dependency-baseline.toml`
- Create: `tests/test_stabilization_boundaries.py`
- Create: `tests/test_test_orchestration_import_boundary.py`

**Interfaces:**

- Consumes: baseline/current Python ASTs, the baseline commit, and the explicit evidence/orchestration origin sets created by both plans.
- Produces: `tools/generate_dependency_baseline.py` with `--check`/explicit `--write`; canonical `dependency-baseline.toml`; and `tools/check_stabilization_boundaries.py` returning nonzero on baseline edge/SCC drift or any forbidden new boundary edge.

#### Task 11a: Early Baseline Generator and Checker Contract

- [ ] Write failing tests for the exact baseline graph, relative/absolute import resolution, `TYPE_CHECKING` imports, sorted edge/SCC encoding, a forbidden evidence edge, a forbidden parent edge, changed untouched-legacy edge, and new/expanded SCC.

- [ ] Implement a standard-library AST scanner and lock this mechanical baseline at `a842c4b6a73a2991a63a481f4107580b72750582`:

```text
modules:       470
edges:         2577
edge digest:   c178ed92158da1c544abaf39ab14842721658a31f3f9246cbeb3e05e3e3da6ee
SCCs:          469
SCC digest:    9987fddd06742fc2af87de7b8ebf79bc8b2dda7231260f7cc9efdcca18dff345
cyclic SCC:    pontius.action_clock, pontius.preparation_bank
```

The TOML records every module/path, every sorted internal edge, and every SCC membership. The existing two-node cycle remains visible and grandfathered mechanically; this milestone neither approves nor removes it.

The baseline has exact schema literal `pontius-dependency-baseline-v1` and only these keys/tables: `schema_version`, `baseline_commit`, `module_count`, `edge_count`, `edges_sha256`, `scc_count`, `sccs_sha256`, `module[]`, `edge[]`, and `scc[]`. A module row has exact string fields `module_name` and normalized repository-relative `relative_path`; an edge row has exact string fields `origin` and `target`; an SCC row has one sorted nonempty unique string array `members`. Rows sort by module name, `(origin, target)`, and member tuple respectively. Counts are exact nonnegative integers that equal row counts (booleans reject), commit/digest forms are strict lowercase hex, every edge endpoint and SCC member resolves to exactly one module, every module appears in exactly one SCC, and canonical row digests are recomputed rather than trusted.

- [ ] Make the generator default to `--check`; permit `--write` only for an explicitly named baseline file beneath `docs/architecture`. Inspect the complete generated diff before accepting it.

- [ ] Implement changed-origin policy: untouched legacy outgoing edges must match baseline; no SCC may be new/expanded; evidence origins may import only stdlib, siblings, and durable journal; orchestration origins may import only stdlib/siblings. Explicitly deny tests, experiments, compiled-calibration owner/runner/reader, CuPy/CUDA/GPU imports from stabilization code.

- [ ] During the coordinated early slice, run all Task 11 synthetic tests, generate the exact baseline with explicit `--write`, inspect it, then prove generator `--check` and checker mutation fixtures pass. Stop Task 11 here; do not claim the not-yet-created real parent/child/current integration has passed.

#### Task 11b: Post-Task-10 Real Integration

- [ ] AST-scan `tools/run_tests.py` and `tools/test_child.py` separately. Assert the parent imports neither `pontius` nor tests and the child imports no sibling helper. Assert neither file contains discovery/owner-launch code outside the declared child probe/capability dispatcher.

- [ ] In a disposable bootstrap snapshot with synthetic test-local guard policy, run the mutation fixtures and the checker directly against the real baseline/current diff. Prove the checked-in current profile still refuses before spawn while design scope is all-zero. Task 12 performs the first real current-profile execution after final design approval.

- [ ] Review checkpoint: run `git diff --check`. With explicit commit authorization only, create `test(architecture): lock legacy graph and new boundaries`.

---

