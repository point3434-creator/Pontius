# Selectable provider source contract

Normative upon adoption of ADR-0505. Base B is
e205cd8cd6f46a50db8b2d0cb1f39366da0f2767. This refines the unchanged approved
brief/design; these exact definitions control where the architecture was less
specific. Scope is one complete selectable-baseline session, not training or use.

## Files and prospective exceptions

Create exactly these five production files under src/pontius/decision_provider/:
__init__.py (inert), model.py (owned values and identities), providers.py (fixed
registry and rules), selection.py (admission/outcome resolution), codec.py (new
record payloads and validation). The codec is an additive refinement of the
four-file design sketch, keeping old v0a model and trace bytes unchanged.

Create exactly tests/test_decision_provider.py,
tests/test_decision_provider_runtime.py, tests/test_decision_provider_transport.py,
tests/test_decision_provider_session.py, and fixtures at
tests/fixtures/decision_provider/rules.json and session.json. Total fixture bytes
are at most 32 KiB. Rule cases are at most 48; integration uses at most 12 distinct
explicit deals, including at most three session deals. No sampled decks or random
case generation. All new tests use correctness identities, never old run roots.

The following twelve base blobs are the entire current-file exception list.
Changes must serve the stated permission; unspecified content remains unchanged.

- Path: src/pontius/v0a/runtime.py
  Base Git blob: 1c855b3b5e8f2d057105128733f43279b9f73990
  Permitted change: Add optional fixed provider selection and new record construction at the
  existing controlled decision; preserve default blueprint and inherited event/timing/delivery
  behavior.

- Path: tools/v0a_hand_adapter.py
  Base Git blob: ff77fb8fd0cd6e1091c2704688f00fb8bc01ec23
  Permitted change: New exact source population/exception declarations only; retain
  blueprint-only behavior and old records.

- Path: tools/v0a_event_adapter.py
  Base Git blob: e241eb52ed2a1e79cac4144433b3f211e59f92f4
  Permitted change: Source population, fixed strategy selector, provider readiness/record codec
  and v2 failure reporting.

- Path: tools/v0a_table_host.py
  Base Git blob: 0faa101f9be9940f9ae935df51f8c79e2eeb2b15
  Permitted change: Source population/imports, strategy forwarding, v2 identity/record consumer
  and mode-specific report. Preserve native process ownership, transport limits, game and
  settlement.

- Path: tools/v0a_table_session.py
  Base Git blob: 34a93d36f91df47d460dbca2403534990e8c49d7
  Permitted change: New exact host blob, strategy forwarding, v2 report/identity and bounded
  reason rendering. Preserve schedule, stack/button and interruption behavior.

- Path: tools/check_stabilization_boundaries.py
  Base Git blob: 744b17768ed3048bce80cf31cf32a64ba4961843
  Permitted change: Classify five exact origins, enforce the import/complete-deal restrictions
  below, allow only named new edges, and refresh the exact session host pin. Preserve unrelated
  policies and legacy graph/SCC checks.

- Path: tools/generate_test_inventory.py
  Base Git blob: 40f955ff0ad10e4026874e57dec285055cb60dcd
  Permitted change: Register four new CPU suites only.

- Path: tests/test-inventory.json
  Base Git blob: 0f07d5e38d216c2bba245b15c8bf1feee3b5a9df
  Permitted change: Regenerate with the new suites/IDs, preserving old records and IDs.

- Path: tests/test-profiles.toml
  Base Git blob: bfe60d1e10ab6f0faaa31ec5709b2064386444ea
  Permitted change: Regenerate membership for four suites; retain old payload order and
  capability grants.

- Path: tests/test_inventory_and_profiles.py
  Base Git blob: 4036ba9b44261ff93a24bde7bfbd8fe2a8c40129
  Permitted change: Four registration expectations and full mechanically derived census counts,
  digests, reasons and source locations only; no weakened assertion or inference change.

- Path: .github/workflows/ci.yml
  Base Git blob: 0a9491b6e62a3695c91e878a7579ecec2c421185
  Permitted change: Add four explicit CPU suite steps; preserve every old step/gate.

- Path: tests/test_v0a_table_session.py
  Base Git blob: c49f3a7ecb3026896e1cdae834af24f527e5b897
  Permitted change: Refresh the hard-coded host-blob mutation target in the existing
  import-boundary test to the new frozen host blob; require exactly one occurrence before
  replacing it with zeroes. Retain every case, assertion and test ID.


The approved runtime exception does not permit changes to the old model, trace,
clock, spine, kernel or evaluator. The rehearsal driver, its test and its historical
SEAL/bindings stay byte-identical and closed to new source. It must not claim the
new runtime is its old seal. Its source-admission refusal on an incompatible
checkout is preserved. Current hand-adapter source admission includes the unchanged
driver as a protected dependency; it does not invoke the driver.

## Exact source admission and import boundaries

For hand/event/host Source admissions, take the complete src/pontius population at
B, plus the five new provider files, plus each tool's existing TOOLS tuple. No
source file is removed. Compare every inherited blob to B except the exact changed
paths in that admission's inventory: runtime.py plus its own tool and any modified
current hand/event tool in its TOOLS tuple. All such exception paths still bind
to their raw blob in the current frozen commit and to the complete manifest.
No untracked/cached/extra package file, changed unrelated blob, foreign origin,
HEAD drift or late source drift is admitted. Keep raw-byte checks and no preloaded
Pontius imports. A manifest is source identity, not source-seal or launch authority.

Parent/child manifests use the same actual ordered raw bytes and the existing
host-exclusion rule for child_manifest. Session HOST_BLOB and the boundary checker
pin must equal the final candidate's host blob; refresh the single existing test
target to that same blob. These are mechanical derived bindings, not independent
permission to change the host. Freeze after deriving them; any later host edit
requires a new candidate and refreshed bindings. Old non-exception source pins
remain enforced. Do not update a historical SEAL or old bindings document.

Provider imports are limited by exact origin:

- model: __future__, dataclasses, enum, hashlib, json, math, and
  pontius.holdem_cards, pontius.no_limit_betting, pontius.immutable_blueprint,
  pontius.v0a.model. No runtime or replay import.
- providers: __future__, itertools, and provider.model, pontius.immutable_blueprint,
  pontius.no_limit_betting, pontius.river. The latter is for evaluate_five and
  evaluate_seven on already visible cards only.
- selection: __future__, and provider.model, provider.providers,
  pontius.immutable_blueprint, pontius.no_limit_betting. No clock/transport access.
- codec: __future__, json, math, and provider.model, pontius.v0a.model,
  pontius.v0a.trace. Reuse unchanged timing/action payload helpers.
- __init__: docstring only. In this list provider means pontius.decision_provider.

Only v0a.runtime may newly import provider.model/providers/selection; only the
event adapter and table host may newly import provider.model/providers/codec.
The session remains stdlib-only and obtains checked modules through its host.
No other old origin gains provider access. Preserve the old direct river-import
restriction for runtime; do not extend it to every v0a module. Forbid complete-deal
type access in all five provider files using the existing AST name/attribute/import
checks, and forbid their dynamic import, eval/exec and file/process/network routes.
This is an admission policy for trusted source, not a claim of complete Python
capability analysis or an OS sandbox. No analyzer inference repair or SCC change.

## Public library API and identity

model exposes frozen exact DecisionObservation, DecisionProposal, ProviderIdentity
and ProviderDecisionRecord. providers exposes make_provider(kind, blueprint),
returning one of the two exact built-in types BlueprintProvider or BaselineProvider.
Both implement propose(observation) -> DecisionProposal. Unknown kind/configuration
refuses before the hand. The registry accepts blueprint-v1 and baseline-rules-v1
only; no user callable, module path, pickle, mutable policy or checkpoint input.

DecisionObservation fields: version='pontius-decision-observation-v1', hand_id,
action_index, cards, betting, decision, remaining_work_ns. IDs use the existing
hand ID syntax; index is an exact int >=1. cards is exact OneSeatCardState, betting
exact NoLimitBettingState, decision exact LegalBettingDecision recomputed from
betting; controlled seat/street/card counts agree. remaining_work_ns is exact int
in [0,14000000000]. Rebuild a validated immutable graph; no caller methods or
mutable aliases survive admission. Keep existing finite event/history/chip bounds.

observation.decision_sha256 is SHA-256 over ASCII canonical JSON, sorted keys,
compact separators, no BOM and no final LF, of exactly version, hand_id,
action_index, key and legal. key is the JSON object from the unchanged
BlueprintDecisionKey.canonical_bytes(). legal contains exactly street (enum value),
acting_seat, stack, street_contribution, current_bet, to_call, call_amount,
action_kinds (enum values in kernel order), raise_bounds. Bounds are null or exactly
minimum_raise_to, maximum_raise_to, minimum_full_raise_to,
maximum_contestable_raise_to, all_in_only. All amounts are exact ints, the final
flag exact bool. Do not hash remaining_work_ns, raw clock samples or hidden state.

DecisionProposal fields are decision_sha256, action, reason. Hash is 64 lowerhex;
action is exact BettingAction or null. Null action requires reason=abstain and
is explicit abstention. A non-null action cannot use abstain. Other reason values:
blueprint_hit, blueprint_default, premium_raise, premium_call, playable_call,
made_hand_raise, made_hand_call, pair_call, free_check, weak_fold. Return proposals
using the supplied observation digest. Structurally valid stale/illegal proposals
are provider_invalid, not authority to act. Unknown or malformed objects are not
serialized. Provider-returned digests never establish trusted provider identity.

ProviderIdentity fields are provider and config_sha256. The digest uses the same
canonical encoding over these exact fixed configuration objects:

```json
{
  "blueprint_sha256": "<admitted blueprint digest>",
  "provider": "blueprint-v1",
  "version": "pontius-decision-provider-config-v1"
}
```

Here the digest field is filled only from the admitted immutable blueprint.
The baseline object's exact values are:

```json
{
  "max_raises_per_street": 1,
  "playable_any_pair": true,
  "playable_rank_min": 10,
  "playable_suited_ace": true,
  "postflop_pair_call_cap_bb": 1,
  "postflop_two_pair_call_cap_bb": 2,
  "preflop_call_cap_bb": 2,
  "premium_ace_kickers": [
    12,
    13
  ],
  "premium_call_cap_bb": null,
  "premium_pair_min": 10,
  "provider": "baseline-rules-v1",
  "raise_size": "legal_minimum",
  "river_board_only": "check_or_fold",
  "version": "pontius-decision-provider-config-v1"
}
```

The source manifest separately binds implementation. Capture provider identity,
source manifest and fallback blueprint digest before readiness, keep them fixed
through the session, and revalidate at source/input boundaries. Runtime construction
uses blueprint plus optional strategy='blueprint-v1'; baseline construction also
requires the validated source manifest supplied by its admitted caller. No default
or provider-supplied fabricated source identity. Legacy blueprint-only callers
retain their existing constructor requirements.

## Baseline and engine semantics

Use the exact fixed preflop/postflop rule order in design.md. Prefix reasoning with
the enum above. Premium raise/call precedes playable; raise counts use this seat's
RAISE records on the current street. The kernel's call_amount is the incremental
cost; multiply blind sizes by caps using integers. Check if free, otherwise fold
when no selected legal raise/call applies. Never synthesize or clip a raise.

For flop evaluate_five on five visible cards; for turn take max(evaluate_five(c))
over the six five-card subsets of six visible cards; for river use evaluate_seven.
Compare the river combined rank with evaluate_five(board) to detect board-only.
Use the evaluator's category rank, with two pair category 2 and one pair category
1. No unknown-card rollout, draw/equity estimate, generated opponent ranges or
threshold selection from demonstration results. Preserve source evaluator bytes.

Resolve and legally validate fallback using the old admitted blueprint lookup
before provider work. Construct/validate observation in the same active action
wall. Sample remaining work afterwards, floor nanoseconds and clamp the hint to
[0,14000000000]; the hint cannot cause a clock reset or establish timeliness.
Invoke the built-in once at most, then engine-validate the proposal and sample the
same authoritative clock again. No provider operates the spine, clock or mailbox.

selection.resolve_proposal(observation, proposal, fallback_action,
fallback_reason) returns an owned Selection value. Its fields are proposal (safe
structural projection or null), provider_outcome, selection_reason,
selection_origin and selected_action. It performs proposal binding and legal
checks; runtime owns exception/clock precedence and may replace selection with
the prevalidated fallback. Selection has no delivery or source authority.

Provider outcomes: not_called, proposed, abstained, error, invalid. Selection reasons:
provider_selected, provider_abstained, provider_error, provider_invalid,
provider_late, provider_skipped_cutoff. Origin is provider or blueprint_fallback.
Only valid timely proposed output has provider_selected/provider origin.
Ordinary Exception from the provider gives error/fallback; explicit abstention
gives abstained/fallback; malformed/stale/illegal output gives invalid/fallback.
The existing clock exception classes, KeyboardInterrupt/SystemExit, invalid engine
context/fallback, and changed admitted source/configuration remain fatal. A stale
proposal digest is a provider defect; changed trusted source/configuration is an
engine binding failure. Keep that distinction at every exception boundary.

If the cutoff is known before invocation: not_called, provider_skipped_cutoff,
fallback. If elapsed >=14 seconds after invocation: keep the observed outcome
(including error or invalid) but use provider_late/fallback. Record the inherited
cutoff failure even when fallback was delivered. After emission, >15 seconds is
deadline failure and outranks cutoff exactly as before; neither is timely success.
Clock invalid/reversal retains the inherited primary/secondary failure rules.
Ordinary provider fallback before cutoff may complete successfully, but its
provider outcome cannot be erased. No unbounded code cancellation claim or new
timeout thread/process supervisor; only trusted bounded built-ins are admitted.

Apply the final selected action through the existing spine's legal emission path.
The internal fallback-slot API does not label a provider action as a blueprint or
resolver in the new record. At most one state application and one delivery attempt.
The old blueprint path retains its exact source selection and records.

## Provider record and wire schema

All JSON objects reject missing/extra/duplicate fields, foreign scalar types,
nonfinite numbers, BOM, CR and oversized frames under the existing limits. Output
is canonical sorted compact UTF-8 JSON plus LF. Input events remain the exact
existing v1 event schema: no strategy, source, seed or full-deal field is admitted.

ProviderDecisionRecord has exactly these fields:

```text
schema_version hand_id event_index action_index street_action_index seat street
state_before_sha256 state_after_sha256 visible_cards_sha256 decision_sha256
source_manifest_sha256 provider config_sha256 fallback_blueprint_sha256
fallback_action fallback_reason proposal provider_outcome selection_reason
selection_origin selected_action applied_action delivery_status delivered_action
timing preparation_use failure_reason
```

schema_version='pontius-provider-decision-v1'. IDs/counters/street/hashes follow
old DecisionRecord validation; state_after_sha256 is null only before application.
provider is baseline-rules-v1 in the v2 wire mode. fallback_reason is the existing
table_hit/passive_default value from the real lookup. proposal is null or exactly
decision_sha256, action, reason with structurally valid values defined above.
It may retain a stale digest or legal-shape-but-illegal action as invalid output.
All action objects are exactly kind/raise_to in the existing HandAction encoding;
selected/fallback are mandatory legal actions, applied/delivered may be null.
Invalid arbitrary objects are never included as a proposal.

applied_action describes the runtime's local spine application, not the host's
acknowledgement. It equals selected_action when applied; state_after is then the
actual resulting state digest. delivery_status uses the old not_attempted,
rejected, accepted, unknown meanings. delivered_action is non-null only for a
confirmed accepted delivery and equals selected/applied; unknown must remain
unknown. A host that received an action retains that observed application even
if a subsequent record or final report fails. No failure retracts an action.
timing/preparation_use/failure_reason use old exact payload schemas; preparation
remains producer_absent with no artifacts and zero credited seconds.

New records are created after a valid observation/fallback exists; earlier fatal
admission failures use null decision plus the old typed failure payload. Later
failures retain the new decision when constructed, together with the typed failure.
codec.decision_payload(record) and codec.validate_decision(payload) encode and
validate this new exact schema. They never widen the old trace parser or build a
v1 TraceBuilder stream from provider decisions. No new evidentiary trace reader.

Add optional --strategy to event adapter, table host and table session only,
choices blueprint-v1 (default) and baseline-rules-v1; --blueprint remains required.
Omitted or explicit blueprint-v1 uses the old v1 protocols, IDs, schemas and text.
Baseline uses these exact mode versions and ID prefixes, with the old suffix
length/character constraints and existing per-hand -hNN derivation:

| Surface | Version / prefix |
|---|---|
| Event frames | pontius-v0a-event-interface-v2 |
| Event session/hand ID | pontius-v0a-event-interface-v2-correctness- |
| Standalone host ID | pontius-v0a-table-host-v2-correctness- |
| Host report version | pontius-v0a-table-result-v2 |
| Multi-hand session ID | pontius-v0a-table-session-v2-correctness- |
| Session report version | pontius-v0a-table-session-result-v2 |
| Per-hand nested report version | pontius-v0a-table-session-hand-result-v2 |

Each v2 frame retains protocol/session_id/type and the exact old type fields at
B, except ready adds provider and config_sha256, and event_result.decision is the
new schema or null. Action frames remain hand_id/action_index/seat/street/action;
they identify applied actions, not provider proposals. Other frame field sets and
limits stay exact. v2 failed event_result may carry a constructed provider record;
v1 failed-event rules remain unchanged. Failure reception before an action and
after an action must both preserve the known delivery/application state.

v2 host/session/nested-hand report field sets are the exact v1 sets at B plus
provider and config_sha256 (null until admitted); replace only version/ID family
as above. Existing blueprint fields still identify the actual fallback artifact.
Capture transcripts and failure prefixes unchanged. Text adds one strategy heading
and a bounded enum reason to each baseline bot action after its matching decision
has been verified. The original action may already have applied; no waiting for
the reason authorizes another action. Opponent private cards/future boards are
never rendered. Do not add any fields or change text in legacy mode.

The host independently recomputes decision_sha256 from its pre-action public state
and bot view, verifies readiness and record source/config/fallback identity, checks
selection/outcome consistency, validates the applied action and resulting state,
and matches it to the received action frame. It does not rerun baseline policy to
certify strength or assume a provider outcome is evidence of correctness. Refuse
mode/version/identity/action mismatches and unknown fields at the real exchange.

## Finite correctness and registration acceptance

Four new unittest suites cover the following finite categories, using the two
declared fixtures and in-test deterministic boundary values. Fixture expectations
are authored independently of the implementation; record literal expected actions,
chip commitments and pots before GREEN execution. No expected-value generator
may call the new provider/runtime to make its own oracle.

1. Provider: premium/playable/weak preflop partitions; pair/two-pair/other postflop;
   flop/turn/river and board-only river; cap-1/cap/cap+1 call costs; first/prior
   raise; no-raise and short-all-in legality; exact input types/card conflicts,
   immutable aliases and identity changes; abstention and illegal/stale proposals.
   Configuration and observation hashes get independently assembled JSON oracles.
2. Runtime: real dispatch/application/delivery with each action kind; provider
   error/abstention/invalid result; before-call cutoff and after-call lateness;
   paired outcome+cutoff faults; 14-second exact and adjacent nanosecond edges;
   15-second exact and adjacent edges; invalid/reversed clock; changed trusted
   identity; failed/unknown/accepted delivery and failure after delivery.
   Every positive/negative control independently observes records and mailbox.
3. Transport: real child-process legacy and baseline readiness/action/results;
   protocol/identity/hash/extra-field/duplicate-action refusals; matching and
   mismatching decision/action; failure both before and after action receipt;
   source changed/extra/cached/unrelated-committed/late drift; real partial pipe
   capture remains incomplete. Exercise the current source guards and native
   child ownership, not a helper that claims those guards succeeded.
4. Session: three fixed explicit deals, independent payouts and carried stacks,
   button rotation, fixed provider through hands, reason rendering without hidden
   cards, early stop and legacy default equivalence. Paired hidden-deal controls
   use the real runtime path with identical visible input and compare captured
   observations/actions; a separate visible change must change a specified rule
   action. Hidden pairs never enter a provider observation.

Controlled schedules may replace the fixed provider's propose method at the named
test seam, supply the existing deterministic test clock, trigger existing mailbox
or pipe write failures, and corrupt disposable raw protocol/source bytes. The real
engine/consumer remains responsible for classification, application, delivery and
cleanup. Do not fake their successful outcomes or claim OS timing from injected
schedules. Fixtures may use existing passive/fold_to_bet/min_raise_once/shove_once
opponents only; opponent implementation and policy source remain unchanged.

Before census refresh, compare the unchanged analyzer's entire output for B and
the candidate on both actual interpreters. Account for every old/new record and
source-line shift, preserving old test IDs, assertions, capability grants and
payload order. Only mechanical registration/census changes are permitted. Any
unexplained drift, analyzer limitation requiring a new grant or weakened negative
case stops the source round for a separate ruling.

After both CLEAN source reviews, run this exact suite list on actual 3.11.15 then
3.14.6, each command from a fresh exact-candidate D-local snapshot with the accepted
scrubbed -B -P/cwd/src/absolute-Git procedure:

```text
-m pontius.status_generation --check
tests/test_status_generation.py
tools/check_stabilization_boundaries.py
tools/generate_test_inventory.py --check
tests/test_inventory_and_profiles.py
tests/test_decision_provider.py
tests/test_decision_provider_runtime.py
tests/test_decision_provider_transport.py
tests/test_decision_provider_session.py
tests/test_v0a_replay.py
tests/test_v0a_trace.py
tests/test_v0a_contract_faults.py
tests/test_v0a_hand_replay.py
tests/test_blueprint_artifact.py
tests/test_blueprint_artifact_boundary.py
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
```

These are correctness checks, not demonstration/operating permissions. Keep all
existing CI gates; the historical rehearsal driver suite is not added to the new
source run list or retargeted to a different seal. Before acceptance, verify the
old driver/bindings and all unspecified old files against B. Failure or scope/line
budget breach stops the round; no silent omission, retry of a consumed owner or
unbounded expansion. The line/round budgets in ADR-0505 apply to the complete path.
