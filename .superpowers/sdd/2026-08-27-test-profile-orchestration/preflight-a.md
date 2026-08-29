# Orchestration Tasks 1-6 Preflight A

Status: **BLOCKERS** (2). This is a read-only contract review of the approved design and orchestration plan. No repository source, tests, manifests, or configuration were changed.

Reviewed sources:

- `docs/superpowers/specs/2026-08-27-evidence-test-stabilization-design.md`
- `docs/superpowers/plans/2026-08-27-test-profile-orchestration.md`

Global constraints used: stdlib-only parent/child boundaries, no primary-checkout payload execution, fresh `-B -P` children with `PYTHONPATH=T/src`, configuration before child creation, monotonic contained execution, and no real profile before the capability approval gate.

## Per-task consistency

| Task | Own files/tests/interfaces checked | Producer -> consumer | Concrete finding | Result |
| --- | --- | --- | --- | --- |
| 1 | `tools/test_orchestration/{errors,model,configuration}.py`; configuration tests; errors/models/configuration/exit interfaces | Task 1 -> Tasks 2-6 | The immutable core models, strict parser, stable selector grammar, and exit precedence supply the data and safety vocabulary later tasks name. Exact positive-budget and frozen-collection rules support deterministic serialization. | PASS |
| 2 | inventory generator; inventory/profiles data; inventory/profile tests; configuration/model updates | Task 2 -> Tasks 3-6 | AST-only inventory ownership, profile selection, capability scopes, payload/fixture rows, and interpreter slots are coherent with the plan and preserve the all-zero preapproval gate. Capability-array ordering needs a downstream tie-breaker; see Task 2/3. | PASS with paired blocker |
| 3 | protocol module; `tools/run_tests.py`; protocol tests and golden vectors; model/configuration updates | Task 3 -> Tasks 4-6 | The request/result schemas bind Task 1/2 digests and identities; the composition root is stdlib-only and public selectors exclude owner launch. Atomic result exchange and parent-owned stream identities align with the isolation constraints. The capability-row order is underspecified when one item has several rows; see Task 2/3. | PASS with paired blocker |
| 4 | process, Windows Job, POSIX group modules and tests | Task 4 -> Tasks 5-6 | `ProcessSpec`/lease/outcome semantics preserve containment ownership, monotonic budget reserve, EOF drain, and whole-tree termination needed by interpreter probing and child execution. No conflict found. | PASS |
| 5 | environment module/tests and model update | Task 5 -> Task 6 | Absolute measured interpreter/Git identities and a constructed allowlist environment give the child contractual `-B -P`, `PYTHONPATH=T/src`, dedicated temp space, and no ambient Python/Git fallback. The deferred Task 6 integration check is explicitly guarded by a pre-Task-6 tiny probe. | PASS |
| 6 | `tools/test_child.py`; child tests; protocol fixture use; protocol/environment updates | Tasks 3 and 5 -> Task 6; Task 7 should precede/participate | Direct stable-ID loading, target-only import paths, file-local protocol parsing, and exact unittest lifecycle behavior are consistent with the child protocol. However, Task 6 requires guards to be installed before any repository import while the sole guard producer (`install_child_guards`) is assigned to later Task 7. The approved order is Tasks 3-10, so Task 6 cannot meet its own mandatory pre-import guard without implementing Task 7 early or violating Task 7 ownership. | **BLOCKER** |

## Shared file/interface pairs

| Pair | Shared file/interface | Producer -> consumer | Concrete finding | Result |
| --- | --- | --- | --- | --- |
| 1 / 2 | `model.py`, `configuration.py`; `ConfigurationBundle`, `ProfilePlan`, selector/errors/exit models | 1 -> 2 | Task 2 extends exactly the Task 1 configuration/model seam and supplies the profile/inventory data Task 1 parses. No duplicate competing parser or non-stdlib dependency is introduced. | PASS |
| 1 / 3 | `model.py`, `configuration.py`; `ProfilePlan`, identities, typed errors, summaries | 1 -> 3 | Task 3 consumes the declared immutable values and preserves Task 1 exit/error boundaries at the composition root. Its child wire adds data instead of changing Task 1 public configuration contracts. | PASS |
| 1 / 4 | `StageBudgets`, `RuntimeContractError`, captured-output models | 1 -> 4 | Task 4 uses the exact Task 1 budget/error contract and leaves lease ownership to the engine, matching Task 1's parent-owned output identity requirements. | PASS |
| 1 / 5 | `InterpreterIdentity`, `InterpreterSlot`, `GitToolIdentity`, configuration bundle | 1 -> 5 | Task 5 produces the Task 1 exact identity types through contained probing and rejects PATH fallback, as required by the profile model. | PASS |
| 1 / 6 | `ChildExecutionResult`, `CapturedOutputIdentity`, execution statuses | 1 -> 6 | Task 6 emits the Task 3 child report while parent-side reconciliation retains streams; that is compatible with Task 1's no-child-owned-output identity rule. Guard installation remains blocked by the Task 6/7 ordering issue, not this pair. | PASS |
| 2 / 3 | inventory/profile digests, payload plans, expanded capability rows, child request | 2 -> 3 | **Contradiction/ambiguity:** Task 2 allows multiple subprocess/call capability bindings for one stable/probe/fixture item and requires canonical sorted collections; Task 3 orders `expanded subprocess_capabilities` only “by stable/probe ID.” Equal item IDs therefore have no mandated secondary key, so equivalent configurations can serialize different canonical request bytes. Specify a total key, e.g. `(item_id, capability_id)`, and apply it in producer, wire validator, and golden vectors. This conflicts with the spec's deterministic, exact atomic JSON protocol and Task 1 canonical collection rules. | **BLOCKER** |
| 2 / 4 | profile `StageBudgets`; payload capability/environment data | 2 -> 4 | Task 2 validates positive serialized budgets; Task 4 consumes the already-resolved values with monotonic reserve semantics. No mismatched units: Task 2 converts seconds once to nanoseconds. | PASS |
| 2 / 5 | interpreter slots and declared environment additions/removals | 2 -> 5 | Profile slots are absolute/repository-relative only and Task 5 resolves them without PATH. Profile environment declarations are the only additions/removals Task 5 admits. | PASS |
| 2 / 6 | stable IDs, inventory entries, payload fixtures/capabilities | 2 -> 6 | Task 6's direct loader derives each requested class/method from the validated Task 2 stable selector and validates complete payload fixture membership before lifecycle execution. | PASS |
| 3 / 4 | `ProcessOutcome`, `ChildExecutionResult`, parent pipe ownership | 4 -> 3 | Task 4 supplies the structured outcome used by Task 3 reconciliation. Its bounded stream identities are compatible because Task 3 still requires parent EOF/drain and a committed atomic report before accepting protocol completion. | PASS |
| 3 / 5 | full `InterpreterIdentity` wire object; atomic probe/result discipline | 5 -> 3 | Task 5's measured interpreter identity exactly supplies the Task 3 request field; Task 3's duplicate-rejecting atomic conventions are reused for the probe result. | PASS |
| 3 / 6 | golden request/result fixtures; `ChildRequestV1`/`ChildResultV1`; file-local codecs | 3 -> 6 | Task 6 expressly consumes all Task 3 golden/malformed data, implements an independent file-local codec, and requires byte-for-byte conformance while prohibiting sibling imports. This satisfies the self-contained-child constraint. | PASS |
| 4 / 5 | `ProcessAdapter`, contained lease, `StageBudgets` | 4 -> 5 | Interpreter probing is explicitly contained through Task 4 rather than a raw subprocess, and its cleanup ordering respects engine lease ownership. | PASS |
| 4 / 6 | contained child execution, drain/termination behavior | 4 -> 6 | Task 6 runs its child tests through Task 4's contained adapter; Task 4 provides the needed fresh-child/timeout/tree-cleanup seam without adding shared imports. | PASS |
| 5 / 6 | child environment and measured interpreter identity; `-B -P` command | 5 -> 6 | Task 5 creates the exact target-only environment Task 6 requires; Task 6 is invoked as a script from `H/tools/test_child.py`, so `PYTHONPATH=T/src` need not expose `H/tools` as an import root. The staged integration test accounts for ordering. | PASS |

## Required resolution before implementation

1. Move the minimal irreversible `install_child_guards` implementation and its prerequisite tests into Task 6, or split Task 6 so that its guarded execution portion follows Task 7. The chosen change must preserve the rule that guards install before **any** repository test or `pontius` import.
2. Define and test a total canonical ordering for every repeated capability row in `ChildRequestV1` (at least `(item_id, capability_id)`), including configuration expansion, request validation, and both golden fixture encoders.

No other Tasks 1-6 shared file or interface contradicts the listed Global Constraints or the approved specification.
