# ADR-0325: Source-seal candidate-blind action-width qualification

- Status: accepted source-only candidate-blind qualification owner; all 96 development sizing contexts remain value unopened
- Date: 2026-08-23
- Follows: ADR-0324
- Qualification source canonical-LF SHA-256: `95974fee5a3fe056828bdb899986235f7b482d9e3d36ec066c0d85e822cb4ca7`
- Qualification seal canonical-LF SHA-256: `7ebd5e9b234b9c28339f2a49214889c3acfdb879c8cb529dd4c7b57c56d5aa76`
- Focused-test canonical-LF SHA-256: `afd9a9e05d4414bbc17cff02f7803bccc9149efab04e64e028c4b410db01da21`
- Qualification protocol SHA-256: `154e7dad5a95165b064deda4a550bd61483e4ffe572f1203c8792d3c45baa70a`
- Qualification schedule SHA-256: `de4b5c39cb973673d51dd9b80be5e47193d6b0ace77c77cd56471dca7eeeb6cc`
- Front-Door-Kind: controller-v1
- Front-Door-Research: ADR-0280
- Front-Door-Process: ADR-0325
- Front-Door-Contract: ADR-0307
- Front-Door-Revoked: ADR-0281
- Front-Door-Active-Next: Invoke `run_adr0323_development_qualification` exactly once against the committed ADR-0325 source and ADR-0324 pool; process contexts and full-then-width-two tasks only in sealed order; stop at the first 16 qualifiers, pool exhaustion, ambiguity, consumer rejection, or runner rejection; retain every opened certified endpoint, conservative chip-regret interval, classification, public-call count, stop state, result digest, and any complete exception chain; if and only if target-reached, derive and commit the exact 16-context development-panel identity before implementing or opening any exhaustive width-three-through-six teacher, finite-block mechanism, or transfer structure
- Front-Door-Blockers: the sealed development qualification has not been invoked and no qualified panel exists; every development sizing value remains unopened; no certified regret curve, exhaustive best-subset teacher, closed finite-block price, frozen greedy mechanism, fresh transfer panel, preparation ledger, six-player response model, live strategy bridge, h32/full-range result, earlier street, complete 15-second decision, or poker-strength result exists

## Question

Does the new owner completely freeze the first fresh value schedule, certified
interval semantics, stop behavior, and panel rebinding before it sees any
development sizing value?

## Decision

Yes. Accept and source-seal
`pontius.fresh_action_width_qualification` and its adjacent manifest. The
module verifies the ADR-0324 source closure, deterministic pool, pool digest,
candidate-attempt count, and complete combinatorial work ledger before it can
build the schedule. Its public value runner additionally verifies its own
source/protocol seal before the first ADR-0322 call.

The source constructs exactly 192 prospective tasks: for each of 96 contexts
in pool order, complete integer universe first and anchored raise-width two
second. Schedule SHA-256
`de4b5c39cb973673d51dd9b80be5e47193d6b0ace77c77cd56471dca7eeeb6cc`
binds every context semantic digest, arm, exact raise totals, scope, label, and
ordering. Building and testing this schedule invokes no sizing consumer.

The inherited trust chain remains explicit. ADR-0318 binds HiGHS 1.12.0, and
ADR-0319 requires one public HiGHS-DS call per canonical task. All 177 ordered
observations pass under ADR-0320 and keep the separate consumer eligible.
ADR-0321 leaves every legal fallback with the caller-owned legal fallback
boundary, while ADR-0322 returns research evidence or rejection with no
action. ADR-0323 governs the value-unopened finite-block research line, and
ADR-0324 supplies its sealed structures.

## Source and protocol seal

The qualification source canonical-LF SHA-256 is
`95974fee5a3fe056828bdb899986235f7b482d9e3d36ec066c0d85e822cb4ca7`.
The adjacent manifest binds:

| Source | Canonical-LF SHA-256 |
|---|---|
| `fresh_action_width_qualification.py` | `95974fee5a3fe056828bdb899986235f7b482d9e3d36ec066c0d85e822cb4ca7` |
| `fresh_action_width_structures.py` | `429f72fff02de515536db36a4754708e71cf93653ad6574026c1fe3c4de82acf` |
| `fresh_action_width_structures_seal.py` | `7c810d4bdd1eae509c50ae8ddd44fc221837241eeb186e5a67a86d79bb61ed29` |
| `certified_reduced_sizing_consumer_v2.py` | `931d6aa2d919efc3fc39e3d404dfa4bf0f6ced756acc2a918dc6c0cde8b4210a` |
| `certified_reduced_sizing_consumer_v2_seal.py` | `c4257cc79f15de3192eea8920fecf18dbb77f2e3a06eb6ad237489717b1e701a` |

The qualification seal hash is
`7ebd5e9b234b9c28339f2a49214889c3acfdb879c8cb529dd4c7b57c56d5aa76`,
the focused-test hash is
`afd9a9e05d4414bbc17cff02f7803bccc9149efab04e64e028c4b410db01da21`,
and protocol SHA-256 is
`154e7dad5a95165b064deda4a550bd61483e4ffe572f1203c8792d3c45baa70a`.

Static controls find no v1-v4 action owner, old qualification module,
legacy/native sizing oracle, direct LP, action construction/application, or
result artifact import. The only two consumer call sites are the prospectively
ordered full and width-two arms inside the public runner.

## Certified interval semantics

The runner has separate nominal records for:

- dimensionless normalized opportunity floor `1e-4`;
- chip-valued nested-value reversal allowance `1e-8`;
- chip-valued qualification ambiguity guard `1e-8`;
- certified chip-value intervals; and
- signed plus nonnegative certified chip-regret intervals.

For full `[L_f, U_f]` and width-two `[L_s, U_s]`, source code fixes the signed
interval to `[L_f - U_s, U_f - L_s]`. It rejects when the upper endpoint is
below `-1e-8` chips, then separately clips each endpoint at zero for the
nonnegative view. It never subtracts lower from lower, upper from upper, or a
point estimate from a point estimate.

Classification derives `payoff_span_chips` from the frozen context. Qualifying
requires the regret lower endpoint strictly above
`1e-4 * payoff_span + 1e-8 chips`; nonqualifying requires its upper endpoint
strictly below `1e-4 * payoff_span - 1e-8 chips`; every equality or overlap is
ambiguous. Stack cannot substitute for payoff span, and the two numerically
equal chip controls cannot substitute for each other.

## Failure-complete result boundary

Each complete observation retains both immutable ADR-0322 accepted records,
the context semantic digest, conservative regret endpoints, classification,
and two one-public-call counts. It can rederive its exact requests and
classification against the sealed context.

The campaign admits exactly four stop reasons:

1. target reached at the 16th qualifier;
2. all 96 contexts exhausted below target;
3. first ambiguous classification; or
4. first typed consumer rejection.

Observations must be a contiguous prefix, qualifying indices are derived rather
than trusted, and no state can continue after ambiguity or rejection. A
consumer rejection retains its arm, exact rejected record, exception chain,
call count, and any already accepted full arm. There is no retry, alternate
backend, native fallback, changed subset, or skipped task.

Source/schedule preflight exceptions return a typed zero-call rejection.
Unexpected execution exceptions retain the exact completed observation prefix,
qualified indices, pool/schedule/source identities, current context and arm,
known public-call count, an explicit flag that the count is incomplete, and the
complete unsuppressed exception chain. Result digests bind certified endpoint
hex encodings, request/legal/public/LP/source identities, regret values,
classification, failure evidence, and stop state rather than only labels.

A panel can be derived only from a target-reached result. Extraction first
rebuilds the exact schedule, rebinds every observation/failure to the sealed
pool, and then retains the 16 ordered pool indices, semantic context digests,
pool digest, and complete qualification-result digest.

## Unsealed controls

Ten focused tests pass. They cover:

- canonical source/dependency/protocol seals and CRLF/LF equivalence;
- forbidden import/action paths and exactly two prospective call sites;
- the 192-task value-free schedule, exact arm order, scopes, anchors, and
  schedule digest without consumer invocation;
- conservative endpoint subtraction, tolerated interval overlap, and material
  nested reversal rejection;
- distinct floor/reversal/ambiguity types, strict three-way classification,
  and a payoff-span-not-stack control;
- target, ambiguity, and typed consumer-rejection schemas;
- result digests changing when chip-regret evidence changes;
- zero-call source-preflight rejection;
- unexpected synthetic execution failure with retained prefix/current state
  and explicitly incomplete call accounting;
- ADR-0324 source drift before pool use; and
- panel/schedule ordering corruption.

Two already-bounded h2 analytic schema arms make one public HiGHS-DS proposal
each. One deliberately invalid analytic request rejects before the backend.
Synthetic preflight and execution controls make no public proposal. No test
calls the public runner with a development context, and no fresh development
sizing value is opened.

Ruff remains unavailable in the pinned environment, so no Ruff claim is made.
Generated STATUS, documentation, adjacent consumer/structure regressions, and
source seals pass. The complete repository suite passes 1,306 tests in
339.879 seconds with two intentional environment-dependent skips.

## Consequences and next boundary

Exactly one sealed qualification invocation is now eligible. It must call only
`run_adr0323_development_qualification`, retain the returned object even on a
negative stop, and perform no post-outcome retry or source change.

If it reaches 16 qualifiers, the successor may serialize and commit the exact
result and panel identities. It may not yet implement or invoke the exhaustive
teacher. If it exhausts, becomes ambiguous, receives a consumer rejection, or
returns a runner rejection, retain that negative result and stop this panel.

## Evidence classification and dissent

- **Known:** source, protocol, schedule, pool, arm order, interval math, and
  failure schema are sealed before values.
- **Reproduced:** 192 value-free task identities and the unsealed analytic/
  corruption controls.
- **Observed:** no development sizing value or qualification outcome.
- **Hypothesis:** the sealed pool reaches 16 material unambiguous contexts
  before a negative stop.
- **Rejected:** any source-only pass as evaluation-power, action-width,
  latency, or poker-strength evidence.

Supporting acceptance: request construction is exact-kernel-derived, endpoint
directions are explicit, every terminal state is typed, and panel extraction
rebinds the complete evidence.

Opposing evidence: the first real invocation can still fail on numerical or
opportunity grounds, and h4 fold/call qualification does not model production
responses.

Largest unknown: the unopened qualification yield and stop state.

Cheapest falsifier: the one now-authorized sealed invocation.

Confidence: high in the source and temporal boundary; no confidence claim is
made about the unopened result.

## Claims boundary

This result establishes only a source-sealed candidate-blind qualification
owner and a value-free schedule. It does not open a development value, qualify
a context, freeze a panel, report regret, select an action width, construct an
exhaustive teacher or greedy mechanism, price a block, close responder raises,
construct transfer, measure preparation or a 15-second action, integrate a
strategy, cover h32/full ranges or earlier streets, train a blueprint, or
establish NashConv, AIVAT, league, coalition, or poker strength. No revoked
experiment, external publication, or thesis change is authorized.
