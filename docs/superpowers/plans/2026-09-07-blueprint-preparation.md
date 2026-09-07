# Immutable Blueprint Preparation Implementation Plan

> For agentic workers: use superpowers:executing-plans task by task. Repository
> source-opening, snapshot, review and per-decision commit rules take precedence.

**Goal:** Remove repeated whole-table digest and linear lookup work from the real
runtime while preserving blueprint behavior and accounting.

**Architecture:** Own and prepare an exact-key table once during hand start; reuse
it for runtime fallback and expose an equivalent direct Python provider. Keep the
legacy host as an independent oracle, version the current evaluator, and retain
old evaluator gates on their exact historical source.

**Tech Stack:** Standard-library Python, actual CPython 3.11.15 then 3.14.6, native
Windows Git, unittest, the existing betting/runtime/codec contracts.

**Spec:** `docs/architecture/v0a-blueprint-preparation-r001/brief.md`, `design.md`
and `source-contract.md`. Read all three before editing source.

## Global constraints

- Base: `363c9fb669e19a30375537ee5e92ea338a840a2d`.
- No source edit precedes separately authorized ADR-0513 adoption.
- New dependencies: none. Exact types, LF, no BOM, 100 columns.
- No old-file edit outside the source contract's exact prospective exceptions.
- Keep 14,000 ms work cutoff, 15,000 ms action wall and preparation-bank semantics.
- Test payloads run with `-B -P`, snapshot cwd/src, scrubbed environment and
  absolute native Git in fresh disposable D-local snapshots; 3.11 runs first.
- No decision commit between tasks. Freeze/review/gate the complete source before
  a later separately authorized source-seal decision commit and push.

## Task 1: Owned table and direct provider

Create the two preparation package files and `tests/test_blueprint_preparation.py`.
The initializer contains only its package docstring. `lookup.py` exposes:

```python
class PreparedBlueprint:
    def __init__(self, source: ImmutableBlueprintActionSource): ...
    def canonical_bytes(self) -> bytes: ...
    @property
    def digest(self) -> str: ...
    def action_for(self, *, cards, betting, decision) -> BlueprintSelection: ...

class PreparedBlueprintProvider:
    def __init__(self, blueprint: ImmutableBlueprintActionSource): ...
    @property
    def identity(self) -> ProviderIdentity: ...
    def propose(self, observation: DecisionObservation) -> DecisionProposal: ...
```

- [ ] Pin base blobs and author the finite parity/ownership tests before source.
  Use the real betting constructors; a minimal literal CALL control is:

```python
cards = OneSeatCardState.preflop(controlled_seat=3, private_hand=make_hole("Ks", "Td"))
state = NoLimitBettingState.six_max_100bb(button=0)
decision = state.legal_decision()
key = BlueprintDecisionKey.from_state(cards=cards, betting=state, decision=decision)
source = ImmutableBlueprintActionSource("prepared-control", (BlueprintActionEntry(key, CALL),))
prepared = PreparedBlueprint(source)
result = prepared.action_for(cards=cards, betting=state, decision=decision)
self.assertEqual(result.action, CALL)
self.assertTrue(result.table_hit)
self.assertEqual(prepared.canonical_bytes(), source.canonical_bytes())
self.assertEqual(result.source_digest, source.digest)
```

- [ ] Run the new suite in a development snapshot on 3.11 and retain RED for the
  absent preparation class. Include source/action/key/result alias mutation,
  full-key collision, legal/illegal hit, passive miss, all streets and provider
  identity/proposal checks from the source contract.
- [ ] Implement exact ownership first, then canonical bytes/digest and a private
  `MappingProxyType` over complete keys. Return fresh action/identity values and
  preserve legal checks. Do not implement artifact serialization again.
- [ ] Add a real-method call counter around old table canonicalization: one call
  during construction, unchanged count after repeated selections. Verify the old
  provider exceeds that count. Run GREEN, then the old immutable blueprint,
  blueprint artifact and decision-provider suites. Keep the observed RED/GREEN.

## Task 2: Accounted real runtime and child path

Modify only runtime and the four source-admission/pin tool paths specified in the
contract. Create `test_blueprint_preparation_runtime.py` and
`test_blueprint_preparation_transport.py`.

- [ ] Write failing real-runtime controls proving hand-start preparation, one
  preparation per runtime, its charged elapsed interval and both fallback routes.
  Use the existing HandRuntime fixtures and deterministic clock; derive expected
  interval cost from clock inputs, never by reading the prepared implementation.
- [ ] Add the absent prepared slot, construct inside `_process_hand_started`, and
  publish it with the successful source digest. Preserve the pre-start property.
  Use the existing `_HandFailure` closure route for preparation errors, preserving
  clock-first classification and no partial cache on failed initialization.
- [ ] Add an internal optional prepared argument to the admitted selector. Keep
  exact context/legality reconstruction and classification. Runtime passes its
  own cache; the old public selector retains its existing default path.
- [ ] Update hand/event/host admission from B with the exact two additions and
  scoped changed-blob sets. Freeze host bytes and derive its raw Git blob for the
  session pin, checker expectation and existing session test's two literals.
- [ ] Exercise a preparation exception followed by a closure clock fault and
  check both genuine causes in order. Exercise existing cutoff/deadline edges
  through real application/delivery. Do not replace successful ledger or host code.
- [ ] Run both modes through non-empty hit/miss real sessions using existing
  explicit deals. Assert expected actions, settlement/carried stacks and complete
  cleanup, with unchanged host fallback as an independent reference. Preserve
  default versus explicit blueprint-mode equivalence and old runtime tests.

## Task 3: Versioned evaluation and truthful historical gates

Create `tools/v0a_evaluation_v3.py`, `tools/run_evaluation_history.py`,
`tests/test_v0a_evaluation_v3.py` and `tests/test_evaluation_history.py`. Modify the
exact checker, generator, historical manifest, inventory/profile, registration
test and CI paths named in the source contract.

- [ ] Start with RED: current v2 admission refuses the added package; the current
  checker refuses the new origins. Retain those correct refusals as motivation,
  not defects to remove from v2.
- [ ] Copy v2 to v3 and change only source identity/admission as specified. Keep
  the original loader tuple positions, bounded reader, lifecycle and wire schemas.
  Validate v3 self/helper/dealer/host raw loading and unexcepted-blob refusals.
- [ ] Implement the fixed history CLI and run-root ownership contract. Its only
  suite map is:

```python
SUITES = {
    "runner": ("tests/test_v0a_evaluation_runner.py", 28),
    "boundary": ("tests/test_v0a_evaluation_boundary.py", 19),
    "v2": ("tests/test_v0a_evaluation_v2.py", 8),
}
```

- [ ] Test real historical cloning and selected suite execution, recorded exact
  commit/tree/test bytes, three result receipts, and whole-run failure on a failed
  gate. Negative controls cover existing root, non-native Git, wrong pinned tree
  and missing selected tests. Preserve outputs; do not fake successful subprocess
  results. A controlled failure seam may force a selected test's nonzero exit.
- [ ] Add exact preparation/launcher/v3 origin rules and new suite registrations.
  Reclassify only the 55 named old evaluator IDs to their pinned historical case.
  Apply the exact exception to both inventory branches. Extend the evidence
  manifest generator with the pinned three selected-test rows and snapshot;
  reproduce the approved digest before updating manifest/test expectations.
  Regenerate manifests/profiles and compare complete census rows on 3.11/3.14;
  preserve old baseline locks, capability grants and every unrelated test entry.
- [ ] Route existing CI evaluator gates through the fixed launcher and add the
  current suites using the established native D-local snapshot procedure. Retain
  independent exits and all other existing CI steps.
- [ ] Test the current checker against forbidden imports/loaders for v1/v2/v3,
  then run a real v3 child and artifact read. Exercise bounded read mutation
  controls against actual v3 handles, not only the historical v2 reader.

## Task 4: Whole-source review, gates and cost report

- [ ] Audit scope and complete literal/oracle coverage. Freeze the complete source
  candidate and manifest; publish its permanent handoff packet. Obtain two fresh
  independent Tier C reviews. Resolve findings within the brief's round budget.
- [ ] After review closure, run the following acceptance population on the exact
  final candidate, first actual 3.11.15 then 3.14.6. Each slot uses a fresh D-local
  snapshot; sequential commands may share that slot's immutable source snapshot.

```text
-m pontius.status_generation --check
tests/test_status_generation.py
tools/check_stabilization_boundaries.py
tools/generate_test_inventory.py --check
tests/test_inventory_and_profiles.py
tests/test_stabilization_boundaries.py
tests/test_test_orchestration_configuration.py
tests/test_evidence_manifest_generation.py
tools/generate_evidence_manifests.py --check
tests/test_blueprint_preparation.py
tests/test_blueprint_preparation_runtime.py
tests/test_blueprint_preparation_transport.py
tests/test_v0a_evaluation_v3.py
tests/test_evaluation_history.py
tests/test_immutable_blueprint.py
tests/test_blueprint_artifact.py
tests/test_blueprint_artifact_boundary.py
tests/test_decision_provider.py
tests/test_decision_provider_runtime.py
tests/test_decision_provider_transport.py
tests/test_decision_provider_session.py
tests/test_v0a_replay.py
tests/test_v0a_trace.py
tests/test_v0a_contract_faults.py
tests/test_v0a_hand_replay.py
tests/test_hand_scenario.py
tests/test_v0a_hand_adapter.py
tests/test_hand_adapter_boundary.py
tests/test_v0a_event_adapter.py
tests/test_v0a_event_adapter_boundary.py
tests/test_v0a_table_host.py
tests/test_v0a_table_host_boundary.py
tests/test_v0a_table_session.py
tests/test_v0a_table_session_boundary.py
tests/test_seeded_deals.py
tests/test_seeded_deals_boundary.py
tests/test_v0a_evaluation_contract.py
```

- [ ] Also invoke the fixed historical launcher with `--suite all` and new absolute
  D-local source/run roots per interpreter. Retain all 55 historical results and
  distinguish them from current acceptance. Rehearse exact CI blocks locally;
  record hosted status separately if available.
- [ ] For manifest derivation/checks, supply only the already retained inputs
  named and pinned by the existing current-file manifest to the disposable
  snapshot. Verify each original and copied raw hash; never rerun an owner to
  reconstruct retained bytes. Preserve those manifests unchanged except for the
  exact historical extension already approved in the source contract.
- [ ] Freeze the diagnostic inputs/launcher before timing. Run the finite table,
  cold construction, memory, non-empty session and v3 matrix observations in the
  source contract with fresh identities and no concurrent scans or test payloads.
  Compare every action/settlement/cleanup before interpreting elapsed time.
- [ ] Write the measured report and later source-seal ADR as new files. Freeze
  any resulting adoption candidate, close its required reviews, rerun applicable
  final gates and make the exact commit reviewable for controller authorization.
  Commit/push only that authorized decision; retain failed candidates and costs.
