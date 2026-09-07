# Selectable decision provider: proposed architecture

Base: e205cd8cd6f46a50db8b2d0cb1f39366da0f2767. Status: design review only.
Companion requirements: brief.md, acceptance criteria 1-6.

## Decision and alternatives

Add an explicit provider boundary inside the existing hand runtime. The engine
continues to own public state, exact legality, time, fallback, action application
and delivery. A provider proposes one action from an immutable observation.
The first providers are the existing immutable blueprint and a fixed CPU baseline.

An expanded exact-state blueprint alone would preserve today's interface but does
not supply a practical general policy for previously unseen random hands. A copied
runtime/host/session would preserve current working files but duplicate the timing
and settlement machinery. The recommended approach is narrow prospective current-
version supersession with explicit source review and legacy compatibility tests.
Historical versions and retained runs remain unchanged.

The current runtime admits an exact ImmutableBlueprintActionSource, records only
table_hit/passive_default, and passes the chosen action through the spine's fallback
slot. Provider integration must change these assumptions explicitly. A provider
result must not be wrapped in a invented one-row blueprint or monkeypatched into
the sealed lookup to avoid changing the records.

## Observation and response contract

One owned DecisionObservation contains a schema version, hand/action identity,
OneSeatCardState, NoLimitBettingState and its engine-derived LegalBettingDecision.
These exact immutable records already contain the bot's cards, public board,
positions, chips, contributions and public action history. Rebuild and validate
the graph at the boundary; do not expose the runtime, mailbox, clock, source loader,
complete deal, schedule or callbacks. Recompute the legal decision from public
state and require agreement before calling a provider.

The observation also carries remaining_work_ns, an exact nonnegative integer
sampled by the engine after observation construction. It is a hint, not a deadline
extension, clock authority or permission to emit. Exclude that varying estimate
from the stable visible-decision digest. Bind that digest to the observation schema,
hand/action identity and all visible semantic state, including legal actions.

The provider's propose(observation) returns a DecisionProposal with the same
decision digest and one exact BettingAction. Its reason is a bounded enum defined
by the selected provider version, not arbitrary text. The engine supplies provider
identity from the admitted configuration; a provider cannot choose its own trusted
identity by returning a hash. Reject foreign types, bools in integer fields,
out-of-range raise-to amounts, extra mutable state and stale decision digests.

This is a logical API boundary for trusted source, not a Python security sandbox.
There is no user-controlled module name, import path, pickle or executable config.
The initial registry accepts exactly blueprint-v1 and baseline-rules-v1. A neural
provider can later implement the same input/action concepts under a separately
versioned adapter; checkpoint loading and inference scheduling are not built here.

## Identity and configuration

The blueprint provider delegates to the existing exact lookup and retains its
blueprint digest. The baseline is stateless and deterministic; all constants are
fixed by baseline-rules-v1, with no tuneable CLI thresholds in this round.
Its canonical configuration digest covers provider kind/version and every rule
constant. The runtime captures configuration plus implementation source manifest
before the hand and checks them at the existing source-validation boundaries.
Configuration identity and source identity are separate fields; neither proves
review approval or strategic quality.

Both modes load an immutable blueprint before the hand as the independently
available fallback. The first demonstration configuration may use the empty
blueprint. No strategy change, configuration mutation or checkpoint swap mid-hand
or mid-session. Each hand gets fresh stateless provider state; no observation or
action history is silently carried outside the visible game state.

## Fixed baseline rules

These rules are chosen to establish situation-dependent behavior, not because of
the three observed demonstration hands. No demonstration result is an acceptance
case, tuning target, expected payout or strategy-selection input.

Preflop, premium means TT or higher pairs, AK, or AQ. Playable means any pair,
any suited ace, or two ranks at least ten. Premium takes a legal minimum raise
when it has not already raised on this street. Otherwise premium calls when legal.
Playable calls only when the incremental call cost is at most two big blinds.
Any remaining case checks if allowed, otherwise folds. A premium or playable
hand with no call available checks; a raise is never synthesized without legal
raise bounds. Count prior bot raises from public street history, not mutable
provider memory. No more than one baseline raise per street.

Postflop, rank the best five-card hand from the two private cards and revealed
board using the existing exact evaluator (5, 6 or 7 visible cards). For a river
board whose best five-card rank equals the combined best rank, treat the hand as
board-only and use the remaining-case rule below. Otherwise two pair or better
takes a legal minimum raise if the bot has not already raised this street; when
not raising, it calls only up to two big blinds. One pair calls only up to one
big blind. Remaining cases check if legal, otherwise fold. When a suggested call
is unavailable, check if legal, otherwise fold. This deliberately simple baseline
does not estimate equity, opponent ranges or draw odds.

Every chip comparison uses exact integer arithmetic and the kernel's incremental
call cost. A minimum raise uses the exact legal minimum raise-to value, including
the kernel's legal short all-in case; never clip an arbitrary illegal action.
Legality validation remains in the engine even for these built-ins.

## Decision flow, fallback and timing

The existing event-entry action wall opens before raw event admission. Observation
construction, fallback lookup, provider work, result validation and publication
all consume that same wall. There is no clock restart or exclusion for strategy
work. Resolve and validate the fallback before invoking the provider.

If the work cutoff has already been reached, skip provider work. Otherwise call
the selected provider once, validate its response, sample time again, and select
the proposal only if it is legal, correctly bound and still before the cutoff.
Ordinary provider exceptions, malformed proposals and explicit abstention select
the already validated fallback, with a distinct retained provider outcome.
KeyboardInterrupt/SystemExit, clock faults, engine state faults, changed source or
configuration, and invalid fallback are not ordinary recoverable provider errors.
They follow the existing failure/stop discipline without inventing a fallback.

At or beyond the inherited 14-second work cutoff, discard the proposal. Preserve
the inherited ability to attempt the fallback emission and report the cutoff
failure; never relabel that action or hand as timely success. More than 15 seconds
through emission is still a deadline violation. A late return cannot restore lost
time, and an already delivered action cannot be retracted or replaced. There is
at most one application and one delivery attempt for the action identity.

Built-ins are bounded synchronous code. No hard interruption of a hung provider
is claimed. Existing host supervision still bounds a stalled child under its
existing limits, which are not a guaranteed 14-second provider cancellation.
Subprocess inference and cancellation must precede support for arbitrary external
or potentially unbounded providers. This round adds neither a timeout thread nor
an unused process manager.

## Versioned records and transport

Provider mode uses a new decision-record and transport version. Keep legacy
blueprint record types, serializers and parsing semantics available for the
default blueprint path. Do not add provider values to the old table-hit enum.

The new decision record binds source manifest, provider configuration digest,
fallback blueprint digest, decision digest and hand/action identity. It records
the proposal when structurally valid, provider outcome, selected/applied action,
selection origin (provider or blueprint fallback), timing and actual delivery
status. Reasons distinguish provider_selected, provider_abstained, provider_error,
provider_invalid and provider_late; retain the blueprint's own fallback selection
reason separately. An invalid arbitrary Python object is never serialized.

The source-checked event adapter advertises the new protocol and policy identity
before accepting an event. The host verifies both, validates returned action
legality against its independently held public state, and matches the applied
action to its decision record. Mismatched mode, protocol, configuration, source,
decision identity, duplicate action or unknown field refuses the exchange.
Receipt emission and later accounting/transport failure remain distinct.

The session gets an explicit strategy selector and retains it through every hand.
Omitting it preserves blueprint behavior. Human-readable output names the
strategy and shows the selected action plus a short reason, such as premium
preflop, pair_small_call, weak_fold or fallback_provider_error. The machine record
remains authoritative; text does not reveal private opponent cards or future boards.
Protocol/version and exact field tables must be frozen in the source-opening
contract before any implementation, with round-trip and refusal controls.

## Source integration and compatibility

Proposed new package: src/pontius/decision_provider/ with __init__.py, model.py,
providers.py and selection.py. Keep contracts, fixed rules and engine-side admission
separate. No new flat pontius module, GPU import or optional dependency.

Likely current integration surfaces are v0a/runtime.py, v0a/model.py, v0a/trace.py,
tools/v0a_event_adapter.py, tools/v0a_table_host.py and tools/v0a_table_session.py.
Legacy rehearsal/hand-adapter source admissions also inventory all src/pontius;
adding a package would otherwise make them reject the new checkout. Their exact
source-admission declarations therefore belong to the same coordinated opening.
Preserve their blueprint-only execution semantics and old wire records.

Source admission must keep an explicit finite source population, raw-blob equality,
module-origin validation, import discipline and late revalidation. Do not replace
an exact population with an accepted directory prefix, allow arbitrary current
files, catch source failures and continue, or loosen every inherited blob pin.
The opening must enumerate each allowed addition/supersession and its raw base
blob, and define the new admitted population consistently across parent and child.
Unrelated source stays byte-identical. Historical snapshots continue to admit
their original source population; no historical seal is reinterpreted.

Registration changes are limited to the boundary tool's explicit origin/import
entries, test inventory/profile registration and CI steps for the new suites.
Mechanical census drift must be accounted for; analyzer repair stays closed.
No existing assertion, test or CI gate is removed to obtain a green result.

## Implementation slices and finite acceptance plan

1. Contract and providers: exact observation/proposal admission, digest binding,
   legacy blueprint adapter and fixed baseline. Independently authored examples
   cover every baseline branch, exact call thresholds, suits/rank edges, board-only
   river, one-raise-per-street and legal short all-ins.
2. Runtime: actual event-to-proposal-to-delivery controls for each action kind,
   legal-bound edges, ordinary provider failure, malformed/stale output, zero work
   remaining, cutoff/deadline edges and clock/source/identity failures. A controlled
   provider response or clock can trigger faults; the real engine must detect them.
3. Transport and session: real child process controls for new/legacy protocol,
   mismatched identity, failed/partial delivery, post-delivery failure and a finite
   three-hand fixture showing button and stack carry. Expected pots and actions
   are independently calculated, not generated by the new policy or session.

For hidden-information isolation, pair complete-deal fixtures with identical bot
cards and public history but different unseen cards. Compare the actual observations
and decisions captured through the runtime path. Vary an allowed visible input
separately to show a specified baseline decision changes. Providers never receive
the paired full deals. No unbounded random sampling or strength tournament.

Run real CPython 3.11.15 first, then 3.14.6, using fresh D-local snapshots, -B -P,
scrubbed environments and absolute Git. Retain old v0a, blueprint, event, host and
session compatibility suites; add explicit bounded provider and integration suites.
The opening must name their exact paths and finite fixture budgets. No source or
poker tests run as part of this design review. A later watched session requires its
own launch instruction after source acceptance.

## Scope, risks and rulings

The largest risk is inconsistent identity or schema changes between runtime,
adapter, host and session. One explicit version/profile and end-to-end rejection
controls address it. The second is disguising an overrun as successful fallback;
retain the old timing failure alongside the delivered action. The third is
mistaking encapsulation for a sandbox; admit only trusted fixed built-ins now.

The controller must approve the prospective current-source supersession approach.
Exact wire schemas, raw source exceptions and test path bindings are intentionally
the next source-opening contract, not discretion to start implementation from this
design. This design grants no source mutation, decision commit or execution.

No neural model, training loop, self-play scheduler, league, evaluation metric,
opponent-policy expansion, learned sizing, resolver, H32 bridge, GUI or live-client
automation. The reusable assets are the visible decision contract, legal-action
validation, policy identity, deterministic baseline and complete session path.
Success means a working selectable policy; winning a demonstration is not a gate.
