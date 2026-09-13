# Pontius: playable bot integration

Status: initial implementation direction, grounded in current source inspection.
User decision, 2026-09-13: prioritize building Pontius using existing research;
pause further experiments and neural-network work. GPU use is welcome where it
provides a practical benefit. No commit, publication or new training run is implied.

## Product target

Build a locally playable 100 BB six-max cash bot through the existing Pontius
entry points. Use Python 3.14 only. Prioritize complete hands, consistent state,
correct legal actions and visible policy coverage before claiming playing strength.
Do not rewrite the research library or retire unrelated modules as part of this work.

Timing clarification: the user agrees to relax the 15-second development target,
but requires bounded decisions and reports that Pontius previously took at most
33 seconds. Use 33 seconds as the initial configurable complete-decision ceiling
for this build. This is a new working limit based on that reference, not independent
verification of the historical maximum. A shorter table-provided deadline governs.
Budget solver work below the deadline to leave room for cancellation, validation,
fallback and action delivery. Routine lookup decisions should return promptly.
Use a monotonic deadline propagated through the decision path; nested operations
must not each receive a fresh 33 seconds. Expiry must preserve an available legal
fallback. Retain separate preparation, solving and delivery measurements, and count
cold GPU initialization where it occurs on the decision path. Existing clock and
protocol code has not yet been changed; that change needs focused boundary tests.

## What current inspection establishes

- The maintained host/session are tools/v0a_table_host.py and v0a_table_session.py.
  HandRuntime accepts blueprint-v1 and baseline-rules-v1. Its special v1 path does
  not instantiate a provider; integration must account for that explicit boundary.
- DecisionObservation contains hero-visible cards, public betting state/history,
  legal actions and remaining time. The model currently caps remaining work at
  14 billion ns. This is one of several coupled clock/protocol surfaces.
- The retained six-player baseline-000 checkpoint describes 200-chip stacks,
  blinds 1/2, 76,400 iterations and 1,475,868 rows. This identifies an existing
  starting policy, not a measured strong blueprint.
- Its loader/keying/abstraction implementation is in the separate Pluribus Lite
  tree. Pontius's immutable blueprint format is not automatically interchangeable
  with that table. A translation or read-only adapter requires explicit semantics.
- Retained GPU graph and time-quality experiments establish useful exact-array
  computation in restricted heads-up river trees. They are not an unrestricted
  multiway resolver. Adaptive action-menu evidence also has a restricted domain.
- The inspected research checkout is codex/river-abstraction-holdout at 6518b9d,
  with uncommitted research records. The default D:/Pontius checkout is a different
  branch. Do not mix their changes or overwrite the existing pyproject edit.
- The inspected README still advertises Python 3.11 or newer. The user's 3.14-only
  instruction governs this build; reconcile active docs/configuration in the
  first applicable source change, preserving unrelated edits.

## First implementation milestone: trained-policy complete hands

One reproducible command runs a local six-player table through preflop, flop,
turn and river to settlement, with Pontius choosing the controlled seat's actions.
Use a pinned existing policy checkpoint, retaining its bucket identity and game
configuration. Record lookup hits, unsupported/off-abstraction cases and fallback.

Start by testing the translation boundary: seat/button/blinds, stack and pot units,
action histories, raise-to versus increment conventions, card encoding, legal
action menus, information-set keys and mixed-strategy sampling. Preserve hidden
information boundaries. The policy must receive only the controlled player's
visible information, even when the local host knows the full deal.

Confirm policy probabilities and selected actions against the existing loader on
matched reachable observations before using the new adapter in full-hand play.
No forced fingerprint overrides. Missing rows remain explicitly reported; a legal
fallback is not a trained-policy hit. Mixed policies remain mixed.

Acceptance: reproducible complete-hand traces; settlement/chip conservation;
correct legal behavior including all-ins and side pots; independent reconstruction
of the visible state; verified policy identity; and a coverage summary. These are
functional integration checks. They do not establish poker strength.

## Subsequent implementation milestones

1. Keep policy, hand/range state and expensive preparation alive for their correct
   lifetimes. Define invalidation before adding reuse. Prefer extending the
   existing boundary over another competing bot or orchestration framework.
2. Promote the minimal reusable GPU river solver out of the research scripts into
   a tested component. Bind it to actual runtime ranges, pot/stack and legal tree.
   Initially restrict it to supported heads-up river states. Other streets and
   multiway states retain the baseline policy. Keep resource stops and a usable
   fallback. Charge preparation and transfers; GPU lookup alone is not the target.
3. Integrate adaptive menus or guarded local improvements only where their tested
   assumptions hold. Do not transplant reduced-game success as a universal rule.
4. Add a fixed full-hand comparison: unchanged blueprint versus integrated bot,
   matched deals, balanced seats, retained seeds, uncertainty and fallback/coverage
   reporting. Use this to assess whether integration actually improves play.

This is an integration order, not permission for a new long training campaign.
Preserve the 45 completed research milestones. Fresh-board experiments, neural
training and a broad cleanup are paused behind the playable-bot objective.

## GPU scope

Use the measured graph-replay approach for suitable repeated dense river work.
Retain CPU execution for cheap lookup and control flow unless measurement justifies
moving it. A persistent device context is a candidate for testing, not an assumed
benefit across state changes. Do not create a general CUDA game compiler now.
