# Immutable blueprint preparation design

Read `brief.md` and `source-contract.md` together. Coverage includes every route
that will use prepared lookup: the public prepared table, its direct provider,
runtime blueprint selection and baseline fallback. Enumerate incoming imports and
calls from the frozen tree, then check them against these four routes. The old
public selector, old providers, artifact codec and host validator remain references.

## Owned preparation and lookup

`pontius.blueprint_preparation.lookup.PreparedBlueprint` accepts only an exact
`ImmutableBlueprintActionSource`. It first uses the existing exact graph rebuild
in `decision_provider.model.own_value`; caller subclasses and their methods never
receive authority. Constructor validation still detects malformed and duplicate
entries. Compute the owned source's canonical bytes and SHA-256 exactly once.

Build a private read-only mapping from the entire `BlueprintDecisionKey` to its
owned action. Dictionary hash collisions resolve by complete key equality; key
digests alone are not lookup keys. Retain the cached canonical bytes and digest.
Do not publish the owned entries or mutable mapping. Ordinary attribute assignment
is refused after construction. Direct reflection into private Python state is not
a security boundary; caller input and returned-result aliases are the boundary.

Expose `canonical_bytes() -> bytes`, `digest -> str`, and the legacy keyword-only
`action_for(cards, betting, decision) -> BlueprintSelection` shape. Lookup derives
the key with the unchanged `BlueprintDecisionKey.from_state`. An exact hit selects
its stored action; a miss uses CHECK, otherwise CALL, otherwise FOLD. Run the
unchanged legal-action validator for either case. Return a freshly owned action
and query key so mutating a returned dataclass cannot alter subsequent lookups.

`PreparedBlueprintProvider(blueprint)` constructs this table and exposes `identity`
and `propose(observation)` with the old provider value contract. Its provider label
is `blueprint-v1`; configuration JSON and digest are exactly the old ones. It
accepts exact `DecisionObservation`, uses its decision digest, and returns the
existing `DecisionProposal` with `blueprint_hit` or `blueprint_default`. Return an
owned identity value as well. Do not modify `make_provider` or baseline rules.

The easy failure is caching before ownership or returning an internal action.
Either would let a caller change lookup results without changing the cached
digest. Input/result mutation controls must exercise both table and provider.

## Runtime and accounting

`HandRuntime` keeps its existing admitted legacy source and a private prepared
slot, initially absent. Prepare from that admitted source during
`_process_hand_started`, where the old whole-table digest is currently computed.
This is once per hand/runtime instance, not once per multi-hand session or process.
Construction may perform another owned copy; include that cost in measurements.

Complete preparation before publishing the prepared slot and source digest. Bind
both to the same successful hand initialization. The pre-start `blueprint_sha256`
property keeps its current behavior and must not trigger hidden cache preparation.
For preparation failures, preserve clock exception classification first; classify
other ordinary preparation exceptions as `SOURCE_BINDING_MISMATCH` through the
existing `_HandFailure` closure path. Never publish a partial prepared source or
catch process cancellation as a successful hand. The existing boundary close
charges time and retains later clock/cleanup faults in their original order.

Retain `_select_admitted_blueprint_action`'s exact context rebuild, independently
derived legal decision, legal-entry classification and output validation. Add an
internal optional prepared argument, absent for old public callers. The runtime
supplies its own exact prepared object; use the concrete class method, not caller
dispatch. Both runtime strategy modes use this route for their mandatory fallback.
The existing final source-digest/key/action checks remain authoritative.

All preparation and selection work stays in the existing measured boundaries.
Keep the preparation bank, producer-absent meaning, 14,000 ms work cutoff and
15,000 ms wall unchanged. No setup time receives new preparation credit. Prove
hand-start charging and failure closure with the real ledger and controlled clock;
measure actual setup separately from later calls. Do not claim these synthetic
clock schedules establish an operating latency bound.

The table host deliberately retains legacy fallback computation. Its independently
owned table and observed public state check the optimized child's action. A host
admission declaration may change, but host policy evaluation may not. This means
the host's reference cost remains in end-to-end measurements.

## Source identities and old tests

The hand adapter, event adapter and host currently enumerate all of `src/pontius`.
Use the exact base and new-path sets in the source contract, with only named
changed blobs excepted. Preserve captured raw loading, identity rechecks and all
filesystem refusal behavior. Refresh the session's exact host pin after freezing
the host bytes. Never replace source admission with an import success check.

V1/v2 evaluators also bind the whole package and reject this changed population.
Keep them unchanged and add `v0a_evaluation_v3.py` as a source successor using the
bounded read and the same artifact/schema/ID semantics. Its source commit and
manifest identify the different implementation; no new evaluation owner follows.

Run the three source-dependent old evaluation suites against base commit
`363c9fb669e19a30375537ee5e92ea338a840a2d` in fresh D-local snapshots. Keep their
test bytes, assertions and test IDs. A small fixed launcher owns only that exact
historical gate population; current v3 tests cover the new admission and real child
path. The unchanged shared contract suite continues against current source.
`source-contract.md` specifies the launch and registration boundary. Historical
passing results cannot substitute for current v3 acceptance.

## Alternatives and limits

A digest-only cache leaves linear scanning in repeated lookup. A digest-keyed
index adds an avoidable collision assumption. Mutating the old source class breaks
sealed history. A provider-only change misses the actual blueprint runtime, which
does not call that provider. Changing both child and host lookup would share the
new implementation with its oracle. Moving setup outside accounting hides cost.
None is the selected design.

The new package is a reusable blueprint execution primitive, not a blueprint
trainer, CFR traversal, abstraction builder or search engine. Future learned
tables may use it only after their own artifact, memory and authority design.
Source openings and test routing are the main integration cost; an unresolved
registration/capability mismatch stops this source round before implementation
expands. Adoption of the exact source-opening proposal is the remaining controller
ruling. Strategic policy, runtime limits and artifact schemas need no new ruling
because this proposal preserves them.
