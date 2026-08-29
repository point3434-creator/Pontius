# Task 2 holistic architecture and performance audit

Date: 2026-08-29

## Status and evidence binding

This audit is bound to the frozen 11-file Task 2 candidate in
`D:/Pontius-worktrees/orch-task2`. The canonical manifest is the SHA-256 of
lexicographically sorted rows in the form `<lowercase file sha256><two
spaces><relative POSIX path><LF>`. Its SHA-256 is:

`79600d1112e52a37f22b649b5d4d5a2f382cb8daf247082466700729b99e82ef`

The candidate passed the following fresh gates:

- inventory/profile suite: 87/87 in 123.812 seconds;
- configuration/model suite: 53/53 in 0.295 seconds;
- H32 fixture: 9 run, 8 passed, exactly one approved unconditional skip;
- inventory generation: pre-write `--check`, authorized `--write`, and
  post-write `--check` all exited zero;
- generated inventory SHA-256:
  `0dd70ea42bcbde0c2abfc156c20c0214060a504b80bfb1cbbad495d48336543d`;
- generated profiles SHA-256:
  `2773545eb34b8e643c55c87e1e6ba6ee0a3ac5a930038d4266f514e54ae497ea`;
- dependency-baseline authentication and stabilization-boundary check: clean;
- all nine Python files, the JSON document, and the TOML document parsed;
- `git diff --check`: exit zero; no trailing-whitespace or final-newline issue;
- cache census: zero `__pycache__`, `.pyc`, or `.pyo` artifacts; and
- two fresh independent whole-candidate reviews: CLEAN, with the manifest
  unchanged before and after each review.

CodeRabbit did not produce a verdict. Three authenticated invocations of
`coderabbit review --agent -t uncommitted --include-untracked` failed before
analysis with the same recoverable connection error, `WebSocket closed`.
Authentication, the Pro+ seat, branch, repository, and review context were
valid. This is the sole external acceptance gate still pending; it is not a
CodeRabbit finding and no candidate bytes changed.

The direct V7 live harness is intentionally inapplicable to this dirty,
live-artifact checkout because its setup requires the retained live artifact
to be absent. Focused production-path tests, source inspection, and both final
reviews covered the two original V7 authorization findings. This environment
boundary is not treated as a passing harness run.

## Executive assessment

The candidate's correctness posture is strong. It uses immutable contracts,
deterministic hashes, explicit ownership, fail-closed analysis, durable
receipts, and adversarial production-path failure schedules. The review has
converged: additional speculative edge-family searches are no longer
proportionate. Stop correctness exploration here, retain the exact candidate,
and rerun only the pending CodeRabbit command when its service is reachable.

The codebase's principal remaining risk is architectural concentration rather
than an identified correctness defect. The generator and its tests have become
new monoliths, the production package is almost entirely flat, private-symbol
coupling is widespread, and repository layout is embedded in many modules.
Those items belong to a separately planned post-acceptance refactor with the
current byte contracts and regression harness held fixed.

## Phase 1: Architectural integrity and design patterns

### Structural health

The source tree contains 474 Python modules and 309,599 lines. Of those, 470
modules are directly under `src/pontius`, so domain, evidence, runtime, GPU,
audit, result, and runner concerns are represented mainly by naming rather than
package boundaries.

`tools/generate_test_inventory.py` is 25,356 lines with 569 function nodes and
66 class nodes. It contains four separable engines:

1. source discovery and inventory/profile derivation;
2. exact AST capability and source-order analysis;
3. secure transaction/publication and retry ownership; and
4. raw Git object and repository snapshot access.

`tests/test_inventory_and_profiles.py` is 30,366 lines with 498 function nodes
and 54 classes. Its size made scoped review necessary and is now a material
barrier to navigation, selective execution, and independent ownership.

Recommended post-acceptance structure, preserving the current public façade:

```text
tools/test_inventory/
  facade.py                 existing CLI and canonical byte contract
  discovery.py              source snapshot and inventory/profile derivation
  analysis/                 flow values, census, resolver, protocol semantics
  publication/              transaction, ownership, rollback, retry manager
  git_objects.py            authenticated Git executable and raw object access
```

Extract transaction/publication and Git access first because they have the
clearest contracts and highest correctness cost. Extract discovery and the AST
analyzer only after characterization tests bind the façade's exact bytes,
errors, ordering, and receipts.

### Coupling and dependencies

The current implementation graph has 2,558 implementation-layer edges (2,580
total unique internal edges) and a longest condensed path of 41 modules. One
cyclic component remains: `action_clock` and `preparation_bank`. A neutral
preparation-use protocol/value module can remove the deferred-import cycle and
the private `_attach_preparation` dependency.

There are 546 relative-import statements importing 973 underscore-prefixed
names across 181 modules. In addition, 214 source modules derive the repository
root with `Path(__file__).parents[2]`. These patterns make file moves and local
refactors behave like cross-system changes. Public domain contracts should
replace private cross-module imports, while artifact/configuration location
should be supplied at runner or composition boundaries.

The package façade is also coupled to runtime setup. `src/pontius/__init__.py`
eagerly imports 20 modules, reaches 24 transitively in the measured graph, and
invokes CUDA DLL environment configuration during package import. Leaf-module
imports should not require unrelated numerical dependencies or mutate process
state.

### Consistency

- Twenty-seven production modules plus one tool implement `_require_digest`
  variants with different signatures and exception behavior.
- `src/pontius/evidence/errors.py` and
  `tools/test_orchestration/errors.py` contain near-parallel typed error
  hierarchies rather than one shared stable error contract.
- The tree contains 31 version-suffixed modules, 42 result modules, 27 runners,
  and 44 audit modules without package-level grouping.
- There are 184 `main()` functions but no `[project.scripts]` entry points in
  `pyproject.toml`.
- The strongest transaction and evidence paths use explicit typed failures and
  durable receipts, while much ordinary code still relies on direct printing
  and local exception conventions.

Create one small shared validation/error library, add explicit CLI entry
points, and define retirement/compatibility policy for versioned modules.
Avoid a mass move: migrate one bounded domain at a time behind compatibility
imports and dependency-boundary tests.

## Phase 2: Performance and compute bottlenecks

**Issue Name:** Serial Single-Thread CUDA Structural Cover

**Impact Level:** High

**The Bottleneck:** The structural kernels in
`src/pontius/legal_river_quotient_compiled_global_separation_calibration.py`
around lines 1966 and 2008 reject every CUDA thread except block zero/thread
zero, then serially traverse sources, levels, ranks, and RRNS channels. The
retained V7 journal has 569 phase records totaling 1,293.6428099 primitive
seconds; `base_structural_cover` consumes 1,247.2065142 seconds, or 96.4104%.

**Optimized Refactor:** Preserve level ordering but make each thread own one
`(rank, channel)` result, using a kernel boundary between dependent levels:

```diff
- _launch(context, "build_base_rrns_batch", 1, ...)
+ _launch(context, "fill_base_rrns", source_rows * channel_count, ...)
+ for level in range(1, SOURCE_WIDTH + 1):
+     _launch(
+         context,
+         "build_structural_level_rrns",
+         comb(cards, level) * channel_count,
+         (..., level),
+     )
```

Cache admitted structural artifacts by their exact provenance identity for
ordinary consumers, while retaining an isolated cold-refresh benchmark arm
where cold timing is scientifically required.

**Issue Name:** Eager Package Import and CUDA Environment Bootstrap

**Impact Level:** Medium

**The Bottleneck:** `src/pontius/__init__.py` eagerly imports 20 modules and
then configures the CUDA DLL environment. Importing a leaf therefore pays the
façade's dependency and initialization cost and can fail on an unrelated
optional dependency.

**Optimized Refactor:** Make the package initializer side-effect-free, retain
compatibility exports through `__getattr__`, and invoke GPU initialization only
from GPU runners or an explicit `pontius.gpu.initialize()` boundary:

```diff
- from .full_width_belief import FullWidthOneSeatBelief
- configure_cuda_dll_directory()
+ _EXPORTS = {
+     "FullWidthOneSeatBelief":
+         ("pontius.full_width_belief", "FullWidthOneSeatBelief"),
+ }
+ def __getattr__(name):
+     module_name, symbol = _EXPORTS[name]
+     return getattr(import_module(module_name), symbol)
```

**Issue Name:** Repeated Whole-Corpus AST Parsing

**Impact Level:** Medium

**The Bottleneck:** A normal inventory-generator pass parses each of 399
working test modules at least four times for discovery, profile derivation,
capability review, and string-decoy census, then separately parses 392 baseline
files. The entry points around generator lines 1290, 23964, 24331, and 25278
produce at least 1,988 full test-module AST constructions per check.

**Optimized Refactor:** Build one immutable `ParsedCorpus` containing canonical
bytes, hashes, ASTs, parent maps, aliases, and discovery indexes. Pass the same
snapshot to every consumer, then revalidate its original byte identities before
publication. This improves speed without weakening concurrent-snapshot safety.

**Issue Name:** Generator Recompiled 71 Times Per Test Suite

**Impact Level:** Medium

**The Bottleneck:** `_load_generator()` in
`tests/test_inventory_and_profiles.py` reloads and recompiles the 25,356-line
generator for individual tests. Static suite analysis found 71 loads. Fresh
measurement produced a 0.2976-second median load and a projected 21.13 seconds
per suite; compilation was 0.2712 seconds while executing a cached code object
was 0.0315 seconds.

**Optimized Refactor:** Cache only the compiled code by exact generator digest,
but execute it into a new module namespace for every test so global state does
not leak:

```python
_GENERATOR_RAW = GENERATOR_PATH.read_bytes()
_GENERATOR_CODE = compile(_GENERATOR_RAW, str(GENERATOR_PATH), "exec")

def _load_generator() -> ModuleType:
    module = ModuleType("pontius_test_inventory_generator")
    module.__file__ = str(GENERATOR_PATH)
    sys.modules[module.__name__] = module
    exec(_GENERATOR_CODE, module.__dict__)
    return module
```

**Issue Name:** Whole-State Descriptor Rewrite Amplification

**Impact Level:** Medium

**The Bottleneck:** Each implicit-class protocol change around generator line
14821 recursively rewrites live flow values, helper returns, captured local
bindings, and deferred-generator defaults. Nested values are reconstructed by
the logic around line 12905. Repeated changes approach
`O(updates × reachable state)` and allocate many short-lived immutable values.

**Optimized Refactor:** Give descriptors stable IDs and store their immutable
versions in a branch-local descriptor table. Flow values retain IDs rather than
embedded descriptor copies. Resolve the current version lazily, or use a
reverse-reference index for bounded eager replacement, so work is proportional
to changed descriptors rather than the whole analyzer state.

## Phase 3: Maintainability, readability, and testability

### Cognitive load

The largest routines are beyond safe local-reasoning scale:

- `_SourceOrderedResolver._evaluate`: 2,114 lines at generator line 16872;
- `_write_windows_governance`: 525 lines at generator line 6303;
- `_run_calibration_cell`: 1,008 lines at calibration line 3677;
- `assess_device_preflight_bytes`: 534 lines at device-preflight-result line
  834; and
- `_fix18_final_reviewer_runtime_contracts_fail_closed`: a 2,392-line test
  helper at inventory/profile test line 17020.

Split these by explicit state transition rather than arbitrary line count.
For the analyzer, use table-driven protocol dispatch and small handlers that
return typed successor states. For publication, keep one explicit ownership
state machine and extract platform primitives behind it. Replace repeated
embedded CUDA constants such as 176, 6, channel widths, and structural levels
with generated admitted configuration shared by Python and kernel contracts.

### Observability

Scientific evidence observability is unusually strong. The durable journal
provides exclusive creation, append/flush/fsync receipts, hash chaining,
poisoning after failed writes, and exact torn-tail recovery.

Operational observability is weak. No source or tool module imports the
standard logging framework; 178 source modules contain 277 direct `print()`
calls, while only 21 modules use the durable journal. Add a structured event
sink with run, cell, phase, artifact identity, duration, and typed error code.
Adapt the sink to both the durable journal and an operator-facing logger so the
scientific record remains canonical while live debugging becomes searchable.

### Testability coverage

The inventory/profile test monolith has 382 patch API calls, 60 mock
constructors, and 69 temporary-directory uses. It accounts for 44.1% of all
866 patch calls in the test suite. This reflects direct dependence on module
globals and concrete OS, Git, subprocess, clock, and CUDA APIs.

Introduce narrow injected ports for filesystem ownership, Git object access,
clocks, subprocess launch, and CUDA launch. Keep the existing real
production-path fault-schedule tests: the review repeatedly demonstrated that
helper-only or state-shape tests do not satisfy ownership contracts. Use fakes
only behind the same production ports, and split tests along the four extracted
engines.

## Winding-down decision and prioritized backlog

The correction loop should stop at this candidate. The only remaining
acceptance action is to rerun the exact CodeRabbit command without changing any
bytes when WebSocket connectivity returns. Do not commit, merge, push, or
integrate without separate user authorization.

Post-acceptance work should be separate, planned changes in this order:

1. parallelize the base structural-cover CUDA work and measure the retained
   cold arm against the same evidence contract;
2. extract transaction/publication and authenticated Git access behind the
   existing generator façade;
3. cache the parsed corpus and compiled generator code without sharing mutable
   analyzer/test state;
4. extract the analyzer and discovery engines with characterization tests;
5. make package import lazy and side-effect-free; and
6. migrate flat domains and private imports incrementally behind explicit
   public contracts.

These are maintainability and performance projects, not reasons to continue
the current edge-case hunt.
