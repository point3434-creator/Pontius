# Selectable Decision Provider Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to
> implement this plan task-by-task. Steps use checkbox syntax for tracking.

**Goal:** Complete a real multi-hand session using a selectable fixed baseline,
with engine-enforced legality/time and truthful provider/fallback records.

**Architecture:** Add owned provider values, a fixed registry and versioned codec.
Integrate selection into the existing runtime and current adapters, preserving
legacy blueprint behavior and all unchanged historical source.

**Tech Stack:** Python standard library, existing exact poker kernel, Windows
child-process transport, unittest, PowerShell and absolute Git.

**Spec:** docs/architecture/v0a-decision-provider-r001/brief.md, design.md and
source-contract.md, adopted together by ADR-0505. The source contract controls
exact interfaces and scoped exceptions; read all three before execution.

## Global constraints

- Do not execute until the exact ADR-0505 source-opening commit is authorized
  and adopted. This plan is documentation, not implementation or launch authority.
- Actual CPython 3.11.15 first, then 3.14.6; fresh D-local snapshots, -B -P,
  scrubbed environments, snapshot cwd/src and absolute PONTIUS_GIT.
- Five new provider files, four suites and two fixtures; twelve exact current-file
  exceptions only. Recheck each base blob before editing. No other source/test edit.
- 1,200 added/removed production lines, 1,800 added test lines, 160 manual
  registration added/removed lines, 32 KiB fixtures; one initial source round and
  at most one correction. Source acceptance covers all slices together.
- No GPU/optional dependency, arbitrary plugin, training, operating or demo run.
- Preserve the continuous 15,000 ms wall, 1,000 ms reserve and all source/transport
  limits. A fallback action does not turn a cutoff/deadline failure into success.
- Keep all old assertions, test IDs, capability grants and CI gates. Never tune to
  the observed demonstration or silently broaden tests beyond finite controls.
- Local freeze refs are review objects. No per-task decision commits or pushes:
  repository per-decision authorization overrides the skill's frequent-commit
  template. Source sealing follows final reviews/checks and exact user approval.

## Task 1: Owned contract and fixed providers

**Create:** src/pontius/decision_provider/{__init__,model,providers,selection}.py,
tests/test_decision_provider.py, tests/fixtures/decision_provider/rules.json.
**Interfaces:** model's DecisionObservation/DecisionProposal/ProviderIdentity;
providers.make_provider(kind, blueprint); each built-in's propose(observation);
selection.resolve_proposal(observation, proposal, fallback_action, fallback_reason)
and its owned Selection value. All fields and enums are fixed by source-contract.md.

- [ ] Save independent rule cases before executing a new policy. Use at most 48
  cases from the contract's partitions. The following initial preflop test has
  independent literal actions; add the remaining enumerated boundaries to this
  same suite, using existing state transitions to construct legal contexts.

```python
from pontius.decision_provider.model import DecisionObservation
from pontius.decision_provider.providers import make_provider
from pontius.holdem_cards import OneSeatCardState
from pontius.immutable_blueprint import ImmutableBlueprintActionSource
from pontius.no_limit_betting import NoLimitBettingState
from pontius.river import parse_cards

def opening_observation(text):
    state = NoLimitBettingState.six_max_100bb(button=0)
    cards = OneSeatCardState.preflop(
        controlled_seat=3, private_hand=tuple(sorted(parse_cards(*text.split()))))
    return DecisionObservation(
        version='pontius-decision-observation-v1',
        hand_id='pontius-v0a-event-interface-v2-correctness-rules',
        action_index=1, cards=cards, betting=state,
        decision=state.legal_decision(), remaining_work_ns=13_000_000_000)

# In a unittest.TestCase method:
policy = make_provider('baseline-rules-v1',
                      ImmutableBlueprintActionSource(source_id='provider-test'))
for cards, kind, amount in [('As Ah', 'raise', 4),
                             ('9c 9d', 'call', None),
                             ('7c 2d', 'fold', None)]:
    proposal = policy.propose(opening_observation(cards))
    self.assertEqual((proposal.action.kind.value, proposal.action.raise_to),
                     (kind, amount))
```

- [ ] Run the new suite in a fresh 3.11 snapshot and retain RED, then implement
  only the exact owned types, registry, rules and resolver required for GREEN.
  Use exact type checks, copied immutable records and canonical JSON digests.
  Exercise stale proposal binding and foreign/mutable values through resolver
  admission, not only dataclass constructors.
- [ ] For turn ranking, implement the bounded adapter below in providers.py;
  add independently ranked six-card cases, including a case whose best five omit
  a private card. Do not call evaluate_seven with six cards or change the evaluator.

```python
from itertools import combinations
from pontius.river import evaluate_five, evaluate_seven

def visible_rank(cards):
    if len(cards) == 5:
        return evaluate_five(cards)
    if len(cards) == 6:
        return max(evaluate_five(group) for group in combinations(cards, 5))
    if len(cards) == 7:
        return evaluate_seven(cards)
    raise ValueError('expected five to seven already-visible cards')
```

- [ ] Verify exact threshold edges, explicit abstention, illegal/stale proposals,
  identity digests assembled independently from contract JSON, one raise per
  street and hidden-value absence. Run focused GREEN on actual 3.11 then 3.14.
  This slice is testable but does not complete the user-facing deliverable.

## Task 2: Runtime selection and new records

**Modify:** only src/pontius/v0a/runtime.py within its exception.
**Create:** src/pontius/decision_provider/codec.py and
tests/test_decision_provider_runtime.py. Extend new model/selection as needed.
**Consumes:** owned observation, fixed provider and Selection from Task 1.
**Produces:** HandRuntime(..., strategy='blueprint-v1', source_manifest_sha256=None)
with legacy default compatibility; baseline requires a validated manifest string.
ProviderDecisionRecord; codec.decision_payload(record) and
codec.validate_decision(payload), with exact contract fields and cross-invariants.

- [ ] Add a real dispatch RED control: premium preflop must apply/deliver raise-to
  4 and return a provider record. A collecting mailbox returns the existing
  DeliveryReceipt; its independent envelope list is the delivery observation.

```python
from pontius.immutable_blueprint import ImmutableBlueprintActionSource
from pontius.river import parse_cards
from pontius.v0a.model import DeliveryReceipt, HandStartedEvent
from pontius.v0a.runtime import HandRuntime

class Mailbox:
    def __init__(self):
        self.envelopes = []
    def deliver(self, envelope):
        self.envelopes.append(envelope)
        return DeliveryReceipt(envelope.hand_id, envelope.action_index)

mailbox = Mailbox()
runtime = HandRuntime(
    blueprint=ImmutableBlueprintActionSource(source_id='provider-test'),
    mailbox=mailbox, strategy='baseline-rules-v1',
    source_manifest_sha256='1' * 64)  # Unit-context label, not source admission.
event = HandStartedEvent(
    hand_id='pontius-v0a-event-interface-v2-correctness-runtime', event_index=0,
    button=0, controlled_seat=3, starting_stacks=(200,) * 6,
    small_blind=1, big_blind=2,
    private_cards=tuple(sorted(parse_cards('As', 'Ah'))))
outcome = runtime.dispatch(event)
self.assertEqual(outcome.status, 'decided')
self.assertEqual(len(mailbox.envelopes), 1)
self.assertEqual(mailbox.envelopes[0].action.kind, 'raise')
self.assertEqual(mailbox.envelopes[0].action.raise_to, 4)
self.assertEqual(outcome.decision.selection_origin, 'provider')
```

- [ ] Insert provider choice after valid context and fallback resolution, before
  final emission. Keep existing wall ownership and deadline classification. Use
  a new-record branch; do not change the old model/trace or disguise a provider
  action as an exact blueprint hit. Reuse application/publication bookkeeping.
- [ ] Add controlled provider exceptions/abstention/invalid responses plus clock
  edge controls through runtime.dispatch. For each assert provider outcome,
  selection reason, actual mailbox count/action, final state and timing failure.
  Patch only propose at the named seam or the deterministic clock; never patch
  the engine's acceptance predicate or the observed mailbox outcome.
- [ ] Exercise late+error and late+invalid compound outcomes, skipped invocation,
  unknown/rejected delivery and failure after confirmed delivery. Verify that
  cutoff fallback records failure and only ordinary timely fallback may pass.
- [ ] Add paired hidden-deal observations captured at the actual propose seam;
  equal visible inputs must give equal digest/action, while one specified visible
  change changes the baseline action. Do not supply full deals to the provider.
- [ ] Run new runtime controls and old replay/trace/contract-fault suites on fresh
  floor-first snapshots. Keep every old assertion; any old default behavior
  difference is a defect, not permission to refresh expected actions.

## Task 3: Source-admitted transport and complete session

**Modify:** tools/v0a_hand_adapter.py (admission only), v0a_event_adapter.py,
v0a_table_host.py, v0a_table_session.py. Do not edit v0a_rehearsal_driver.py.
**Create:** tests/test_decision_provider_transport.py,
tests/test_decision_provider_session.py and the declared session.json fixture.
**Consumes:** Task 2 records/codec and Task 1 fixed registry/configuration.
**Produces:** explicit --strategy baseline-rules-v1 through the complete v2 path;
omitted/explicit blueprint-v1 remains the old v1 behavior and field sets.

- [ ] Build source-admission RED controls for the exact new population, together
  with changed unrelated blob, added/cached file, foreign import and late drift
  refusals. Implement only the finite source exceptions in the contract. Rebind
  parent/child manifests to the same actual frozen source; source identity does
  not assert approval. Keep the historical driver and its seal untouched.
- [ ] Add a real child-process baseline readiness/action control and v1 default
  equivalence. Use the contract's literal versions and exact field sets. Assert
  provider/source/config identity before any supplied event. Unknown strategy,
  wrong protocol/identity, stale record and extra field must refuse the exchange.
- [ ] Integrate host-side observation hashing and applied-action agreement. Test
  failure before action and after received action independently. Preserve raw
  prefixes, real native ownership, duplicate refusal and original exit outcomes.
- [ ] Author the following finite session fixture using existing-format card
  integers (rank order 23456789TJQKA, suit order cdhs). Each private pair is sorted.
  Start with six 200 stacks, button 0, blinds 1/2, bot seat 3; all five opponents
  use the existing fold_to_bet controller. No shuffle or generator invocation.

| Hand | Seat 0 | Seat 1 | Seat 2 | Bot seat 3 | Seat 4 | Seat 5 | Board runout |
|---|---|---|---|---|---|---|---|
| 1 | 2c 3d | 4c 5d | 6c 7d | As Ah | 8c 9d | Tc Jd | Qc Kd 2h 3s 4h |
| 2 | 3c 4d | 5c 6d | 8c 9d | 7c 2d | Th Jd | Qc Kd | As Kh 2h 3s 4h |
| 3 | 2c 3d | 4c 5d | 6c 7d | Ac Kc | 8c 9d | Tc Jd | Qc Kh 2h 3s 4h |

  Independent accounting: hand 1 bot raises to 4 and wins the three blind chips;
  hand 2 everyone folds to the bot's big blind, net one chip; hand 3 the bot's
  small-blind raise wins the big blind, net two chips. Returned unmatched wagers
  do not create profit. After-hand stacks are respectively
  [200,199,198,203,200,200], [200,199,197,204,200,200],
  [200,199,197,206,198,200]. Buttons are 0,1,2. No hand requires the saved board.
  These simple fold controls isolate session bookkeeping; the other runtime
  controls cover postflop decisions and showdown/side-pot regression remains.
- [ ] Verify the real session with a fresh correctness ID and retained capture:

```python
process = subprocess.run([
    sys.executable, '-B', '-P', str(REPO / 'tools/v0a_table_session.py'),
    '--session', str(REPO / 'tests/fixtures/decision_provider/session.json'),
    '--blueprint', str(REPO / 'tests/fixtures/table_host/empty_blueprint.json'),
    '--strategy', 'baseline-rules-v1', '--session-id',
    'pontius-v0a-table-session-v2-correctness-provider-fixture',
    '--auto', '--format', 'json'], cwd=REPO, env=os.environ.copy(),
    capture_output=True, timeout=150)
self.assertEqual(process.returncode, 0, (process.stdout, process.stderr))
report = json.loads(process.stdout)
self.assertEqual(report['version'], 'pontius-v0a-table-session-result-v2')
self.assertEqual(report['completed_hands'], 3)
self.assertEqual(report['carried_stacks'], [200, 199, 197, 206, 198, 200])
self.assertEqual([hand['button'] for hand in report['hands']], [0, 1, 2])
```

  Here REPO is the fresh snapshot root, not D:/Pontius; import os, sys, json,
  subprocess and pathlib.Path in the new test. Each test owns a fresh temporary
  directory/output capture. The literal correctness suffix is local to disposable
  test snapshots and is never an operational owner or either retained demo ID.
- [ ] Add text rendering, early stop and same-policy-through-hands checks. Run the
  four new suites and current hand/event/host/session suites floor first. Complete
  the exact host blob derivation before the final integrated freeze.

## Task 4: Registration, cold review and acceptance

**Modify:** only the six registration paths and existing session test's binding
target listed by the source contract. No new framework or test discovery mode.
**Produces:** classified origins/imports, registered four suites, unchanged legacy
membership/assertions, and one immutable source candidate with complete evidence.

- [ ] Add exact provider origin/import rules and negative controls to the new
  provider suite. Retain complete-deal bans and old direct runtime import bans.
  Bind session and checker HOST_BLOB to the frozen host; replace the old test
  mutation target with that same literal and assert its occurrence count is one.
- [ ] Compare complete unchanged analyzer output before/after on both actual
  interpreters. Account for every record and line shift before updating census
  expectations. Preserve every old assertion, test ID, capability and payload order.
- [ ] Register only four suites, regenerate inventory/profiles and add four CI
  steps. Run explicit changed checks, inspect the full diff and count budgets.
- [ ] Freeze one candidate/ref with raw manifest and RED/GREEN receipts under
  docs/workflow.md. Obtain two independent fresh Tier C reviews. Fix only within
  the one permitted correction round; all changed bytes get a new frozen round.
- [ ] After both CLEAN verdicts, run every named final command in source-contract.md
  on actual 3.11.15 first and 3.14.6 second, each in a fresh exact snapshot. Recheck
  source/fixture hashes, old untouched blobs, module origins and complete receipts.
- [ ] Prepare the source-seal decision with the actual candidate/manifest, review
  hashes and check receipts. Request that exact decision's commit/push approval
  only when reviewable and ready. No watch session or training follows implicitly.

## Plan self-review and completion boundary

The four tasks cover all six brief criteria and the source contract's full public
path. Interfaces are defined above or in the normative exact contract. No helper
establishes its own ground truth. The primitive examples are starters, not a waiver
of the complete finite boundary categories or regression list. Follow the contract
when examples omit unrelated setup. The work is incomplete until the baseline
actually passes through a real complete session and all required gates pass.
