# Orchestration Preflight B — Tasks 7–12

Verdict: **BLOCKERS**. The approved ordering has a two-sided Task 7 integration cycle: Task 6 requires the child to install guards before imports, but Task 7 is the first task that produces the guard implementation; Task 7 in turn requires an authenticated primary-root identity whose concrete producer (`PrimaryCapture`) is Task 8, scheduled later. The remaining reviewed task interfaces are internally consistent once that cycle is resolved.

## Task internal consistency

| Task | Internal contract check | Status | Concrete contradiction (if any) |
| --- | --- | --- | --- |
| 7 — Child capability guards | Requires guards before test imports and an authenticated primary-root identity. | BLOCKER | Task 6 says `test_child.py` must “Install guards” before test import, while Task 7 is the first producer of `install_child_guards`; Task 7 is after Task 6. Separately, Task 7 consumes an *authenticated* `PrimaryRootIdentity`, but the plan's authentication/capture producer is Task 8 `capture_primary_state` / `PrimaryCapture`, scheduled after Task 7. |
| 8 — Current-state harness | Captures primary state and materializes H without primary writes. | PASS | — |
| 9 — Core/current/full/GPU engine | Consumes the immutable execution, guard, workspace, and manifest contracts with one preparation pass. | PASS, conditional on resolving Task 7 | — |
| 10 — Historical clones and probe | Uses prepared historical rows and worker-plan closures; keeps proposal review separate from approved execution. | PASS | — |
| 11 — Dependency baseline/boundaries | The stated 11a early contract and 11b post-Task-10 integration split aligns with the global order. | PASS | — |
| 12 — Canonical matrix/review | Final inventory, design approval, verification workspace, profile matrix, and review fixed point are ordered after Tasks 3–11. | PASS | — |

## Shared Task 7–12 files and interfaces

| Task pair | Shared file/interface | Status | Consistency check |
| --- | --- | --- | --- |
| 7 ↔ 8 | `PrimaryRootIdentity`; primary-root write guard / `PrimaryCapture` | BLOCKER | Task 7 needs an authenticated identity, but Task 8 is its stated concrete producer and runs later. |
| 7 ↔ 9 | `tools/test_child.py`; guard events/counters; capability bindings | PASS after Task 7 is reordered/split | Task 9 correctly consumes the child guard and retains its counters in profile summaries. |
| 7 ↔ 10 | `tools/test_child.py`; `tests/test-profiles.toml`; historical guard policy | PASS after Task 7 is reordered/split | Task 10's historical probe and exact capability rows extend the same child guard boundary. |
| 7 ↔ 11 | `tools/test_child.py`; stabilization import/owner-launch policy | PASS | Task 11b's AST boundary scan explicitly permits only the declared child probe/capability dispatcher. |
| 7 ↔ 12 | `tests/test-profiles.toml`; final design-scope capability approval | PASS | Task 12 deliberately replaces Task 7's preapproval state only after final inventory regeneration and user approval. |
| 8 ↔ 9 | `workspace.py`; `PrimaryCapture`; H materialization; `model.py` | PASS | Task 9 consumes Task 8's capture/materialization and primary-unchanged checks as immutable inputs. |
| 8 ↔ 10 | `workspace.py`; `HardenedGit`; temporary clone/root rules | PASS | Task 10 extends the same hardened Git and verified-temp-root contract for historical T clones. |
| 8 ↔ 12 | hardened Git / verified temporary-workspace rules | PASS | Task 12 explicitly reuses Task 8 hardened-Git rules for review scope; its verification workspace is a separate safe-root protocol. |
| 9 ↔ 10 | `engine.py`; `test_child.py`; `model.py`; `tests/test-profiles.toml`; `ExecutionBundle` / `ResolvedWorkerPlan` | PASS | Task 10 supplies historical-clone/probe behavior through the immutable plan closure Task 9 requires, without reparse. |
| 9 ↔ 11 | `tools/run_tests.py`; `tools/test_child.py`; stabilization boundary checker | PASS | Task 11b validates the real parent/child boundary after the Task 9 integration surface exists. |
| 9 ↔ 12 | `tools/run_tests.py`; `compare_run_summaries.py`; JSON summaries; profiles | PASS | Task 12 runs the canonical profiles and comparator after final design approval. |
| 10 ↔ 11 | `test_child.py` declared probe/capability dispatcher; historical import boundary | PASS | Task 11b's scanner accommodates the Task 10 sealed-reader probe only inside its declared dispatcher. |
| 10 ↔ 12 | inventory/profile/capability rows; historical summaries | PASS | Task 12 preserves and revalidates the approved historical scope while approving design scope and executes the historical profile. |
| 11 ↔ 12 | dependency-baseline/checker commands; stabilization-boundary tests | PASS | Task 12 invokes both Task 11 generator/checker gates before profiles and reviews. |

## Relevant predecessor boundary

| Producer → consumer | Interface | Status | Concrete contradiction |
| --- | --- | --- | --- |
| Orchestration Task 6 → Task 7 | Task 6 `test_child.py` must install guards before repository-test import; Task 7 produces `install_child_guards`. | BLOCKER | The consumer behavior is mandatory in Task 6, but its only specified producer is Task 7, which follows it. This is a direct order inversion. |

## Material cross-plan producer/consumer boundaries

| Producer → consumer | Contract | Status | Consistency check |
| --- | --- | --- | --- |
| Evidence Tasks 1–3 → Orchestration Tasks 1–2 and 11a | Four exact evidence TOML schemas/identities; baseline and boundary constants. | PASS | Both plans prescribe the same schema literals, standard-library orchestration parsing, and early data-contract order. |
| Orchestration Tasks 1–2 and 11a → Evidence Tasks 4–9 | Tool-local configuration/inventory/boundary contracts before the active evidence slice finishes. | PASS | This is the declared early coordinated slice; later orchestration runtime work remains gated. |
| Evidence Task 3 → Orchestration Tasks 9–10 | Sealed present/absence, historical blob, and retained-v7 manifests; commit/root/blob/overlay identities. | PASS | Task 9 reads all four schemas once without importing `pontius`; Task 10 uses prepared historical rows and matching v7 overlay identities. |
| Evidence Tasks 6–7 → Orchestration Tasks 9–10 | Negative retained-v7 facts: terminal, completeness separation, scientific/authoritative counts, historical commit, frozen manifest. | PASS | Current assessment is a current-profile test; the historical sealed-reader probe independently requires the same negative facts without importing the active assessor into T. |
| Evidence Task 8 → Orchestration Tasks 9–12 | Evidence import/protected-diff boundary and generator `--check`. | PASS | Orchestration's evidence guard and final verification invoke equivalent manifest/protected-state checks while retaining their no-`pontius` boundary. |
| Evidence Task 9 completion gate → Orchestration Tasks 3–10, 11b, 12 | Evidence-slice approval/review gate. | PASS | Both global orders explicitly prohibit these runtime/final tasks until the evidence gate has fresh passing evidence. |

## Required correction

Split or move the guard bootstrap so that Task 6 has a produced, testable pre-import guard contract, and ensure the authenticated primary-root identity is produced before the full Task 7 integration tests. A minimal ordering repair is: introduce the guard API and primary-root authentication primitive before or within Task 6, keep Task 7 for policy expansion/conformance tests, then retain Task 8 as the concrete current-snapshot implementation.
