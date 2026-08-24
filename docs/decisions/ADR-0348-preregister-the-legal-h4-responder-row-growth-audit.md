# ADR-0348: Preregister the legal h4 responder-row growth audit

- Status: accepted preregistration and source seal before the first legal h4 responder-row growth invocation; every row-growth value, selector-stability result, action-clock result, strategy label, and production action remains unopened
- Date: 2026-08-24
- Follows: ADR-0347
- Config: `experiments/configs/legal-responder-raise-h4-row-growth-v1.json`
- Config SHA-256: `da6c4067cedd71504eb0c5e0c5034ffdf731839d2df71d33f0a07d12bd25cd99`
- Parent decision SHA-256: `d76a984978ba991e7a797f4aad292f6b80278502f14184658a3f42b34c433c63`
- Parent artifact SHA-256: `6dcbf8e44f1c3b2bd54694e0c1f6898082e71373846933bfaa116bc4f2c27255`
- Parent result owner SHA-256: `4c67ce1e724e6196a1fff6d7d6312c7a117fd9ff5ea47c8e82d7a1f21e8e1547`
- Legal kernel SHA-256: `9e2c45d575d28c759aea97c4f916a18584241cd84a6731e89bc609f32c2c7396`
- Legal continuation SHA-256: `4c8f57f259415ece30b12add42243b65a30d3320924b469209e2d94a68064250`
- Generation primitive SHA-256: `a84126b66aad760dcda28ba4870cd4a5daba18ebe5377fef8b1efa53a04d9231`
- Audit observer SHA-256: `f5c6f80bc46a6b8887f9241998207bbb8828fff136a6f1a389475b1aead349eb`
- Independent Fraction oracle SHA-256: `8d70297ab80055c5c77bdeefb82ff6cde817f6c57876059783046669b3a6945a`
- Prospective runner SHA-256: `89f425d5bf5ddca7a1e2ef0eb343d0f34b1ce39cc9b7ee31a3fc4364905b9e58`
- Audit control SHA-256: `14d6bb929af5167d336f8abc724558e2710748efc8b1fc905bb8c120f3a2ed1e`
- Runner control SHA-256: `14c698b38669aeeb624bf844494468856f37eb80c8278ccde6035415f59ac591`
- Expected h4 game provenance SHA-256: `31eb059bdd32f74fc0f72dd07927b21d32493cc2831cacac22b3fe8615658214`
- Expected source-policy SHA-256: `b69b34a644a6c3cec3094584735e8807aed1b24abdaa39806bce3540bebda55a`
- Front-Door-Kind: controller-v1
- Front-Door-Research: ADR-0280
- Front-Door-Process: ADR-0348
- Front-Door-Contract: ADR-0307
- Front-Door-Revoked: ADR-0281
- Front-Door-Active-Next: From one clean commit containing ADR-0348 and an absent legal h4 row-growth result path, invoke the source-sealed audit exactly once and retain pass, rejection, or typed failure without changing the fixture, source policy, initial rows, guard, iteration bound, tolerance, observer, exact checks, byte definition, walls, or claims; a pass authorizes only a separately preregistered selector-stability successor, while full-width river capacity remains a separate parallel lane
- Front-Door-Blockers: no legal responder-row capacity result, selector-stability result in the deeper tree, repeated-actor multiway existence result, off-tree opponent-action result, cross-street belief/certificate handoff, full-width capacity result, certified full-width river strategy bridge, sealed blueprint trainer/checkpoint/abstraction/slice-audit chain, trained blueprint, v0a/v0b integrated bot, preparation-bank filling result, frozen evaluation opponent pool, complete 15-second decision, production action width, or poker-strength result exists

## Question

On ADR-0347's identical legal h4 checked-to river tree and source policy, how
many exact responder rows does the production one-seat sequence-form generator
need before its existing convergence rule closes? What response signatures are
encountered, how much oracle work and retained row storage do they require, and
what numerical conditioning and bounded infrastructure wall accompany that
finite campaign?

This question is intentionally narrower than selector stability. Response
signatures are retained as exact row identifiers because the generator uses
them for deduplication; their appearance is not evidence that a selector stays
stable under perturbation. It is also narrower than action-clock capacity: the
entire laboratory campaign starts from an already constructed h4 game and is
not a complete decision.

## Decision

Add `one_seat_row_growth_audit`, a read-only observer around exactly one call
to the source-sealed production
`solve_one_seat_with_row_generation`. The production primitive is unchanged.
During one single-threaded laboratory call, the observer records its existing
evaluation, master, response-row, best-response, expected-utility, and
open-axis coefficient boundaries. It calls the original objects at every
boundary and returns the production result itself; it is neither a shadow
solver nor an alternate row generator. A process-local lock prevents two
observed calls from overlapping.

Add one failure-retaining prospective runner,
`legal_responder_raise_h4_row_growth`. The runner invokes the observer exactly
once. It never calls `best_response` outside that observed production call.
Every response tape selected by the subject is retained in full and then held
fixed while the independent Fraction enumerator rechecks the corresponding
gain row. Every candidate tape already returned by the subject is likewise
held fixed while exact terminal enumeration rechecks utilities, response
values, deviation gains, caps, convergence classification, and the retained
incumbent. Config or execution exceptions consume the exclusive result path as
typed failures. A pre-existing result path is never overwritten.

ADR-0347's prospective coefficient runner is permanently closed. Its
solver-free result owner remains the parent authority and must pass before the
new subject call begins. No code in this decision invokes or imports the
closed runner.

The inherited trust chain remains explicit. ADR-0310 made native-simplex
robustness the next systems question. ADR-0311's directive is Preregister the
native-simplex robustness audit. ADR-0312's directive is Seal the
native-simplex audit compiler and corpora. ADR-0313's directive is Seal the
native-simplex audit runner before results. ADR-0314's decision is Retain the
native-simplex audit and reject the frozen gate. ADR-0315's directive is
Source-seal the artifact-only native-simplex gate correction. ADR-0316's
decision is Accept the corrected audit and bound replacement eligibility.
ADR-0317's directive is Separate solver classes and prioritize the certified
sizing adapter. ADR-0318 binds HiGHS 1.12.0, ADR-0319 requires one public
HiGHS-DS call per canonical task, and All 177 ordered observations pass under
ADR-0320, making the separate consumer eligible. ADR-0321 preserves
caller-owned legal fallback, ADR-0322 returns research evidence or rejection with no
action, ADR-0324 remains value-unopened, ADR-0325 was authorized exactly once,
ADR-0326 and ADR-0327 govern the exhaustive bounded development-teacher chain,
and ADR-0333 records that No replacement sizing value was opened at its source
boundary. ADR-0330 remains permanently closed, ADR-0331's append-and-fsync
discipline and ADR-0332's exclusive `xb` open remain authoritative, ADR-0337
remains the response-closed direct mechanism with a dynamic-branch rebinder,
ADR-0338 alone records the selected development raise width, and ADR-0339's
exact non-overlap comparison remains a finite absence claim, not
representativeness evidence. ADR-0340's 192 prospective tasks remain distinct
from ADR-0341's 94 accepted one-call arms and ADR-0343's 126 confirmation arms.
ADR-0342 alone authorized the retained confirmation invocation. ADR-0344 and
ADR-0346 remain source-only authorities, while ADR-0345 and ADR-0347 alone own
their retained finite results. No result here weakens those authorities.

## Frozen subject and initial state

The board, six-chip legal betting state, two table seats, integer raise-to
universe, four root hands, four responder hands, 16 positive dyadically
weighted deals, 176 terminal paths, 12 acting information sets, 32 sequence
variables, and key-rotated dyadic source policy are byte-for-byte descendants
of ADR-0347. The guard remains `0.25`, the tolerance remains `1e-10`, and the
iteration ceiling remains 128.

The initial row inventory is exactly one row for each logical player. Its
complete response-signature SHA-256 values, in player order, are frozen as

- acting player: `83b57620097d496624aabfa49fdba1ab64ccb5cd519a9daf20130ade55f7e908`;
- responder: `778a91ab318ea0c94d1baa8dcfe9481ed6155604cc964a6b014720b0b20877f8`.

Their exact gain-row SHA-256 values are respectively
`7be24d40786a55761142e3bfdf230f5b6ddbac5320703cd44050d4d2f345f4a5`
and
`3c1b73c33f1f5ede4ea8a9ccf415c5337a3c033ae4a5549177a19324b0543d90`.
These are inherited facts from ADR-0347, not newly opened growth values.

## Signature identity, rows, and exact checks

The authoritative row identity is the pair of logical target player and the
complete tuple of `(information-state key, action)` selections sorted exactly
as the production evaluator returns them. Equality and dictionary membership
over that tuple are the only deduplication rules. A digest is reporting and
provenance only; no digest prefix, coefficient tolerance, numerical distance,
or policy-value coincidence may merge rows.

For every initial or generated row, retain:

- ordinal, phase, generation iteration, and logical target player;
- the complete response signature and its full digest;
- the Float64 constant and all 32 Float64 coefficients as hexadecimal strings;
- the independently derived reduced Fraction constant and coefficients;
- exact-row digest, maximum Float64/Fraction error, and exact identity bit; and
- canonical retained bytes.

Canonical retained bytes mean the length of compact, key-sorted UTF-8 JSON for
the semantic row record before the `retained_bytes` field is added. The total
must not exceed 8 MiB. This is a storage diagnostic, not resident GPU memory or
a production cache measurement.

The exact evaluator consumes the subject's already selected response tapes; it
does not reselect them. For each baseline or candidate policy it rederives
profile utility and both fixed-tape response values with `Fraction`, checks
nonnegative gains, and checks the production Float64 values within `1e-9`.
Each row must match the independent exact coefficient oracle within `1e-12`.
The exact cap and epigraph comparisons must give the same feasibility and
convergence classifications as the subject's frozen `100 * tolerance` rule.
The final retained incumbent must be one of the already evaluated policy
digests, remain exactly cap-feasible, and match its exact NashConv within
`1e-9`. These are finite fixed-tape checks, not an independent proof that the
best-response selector chose a globally correct tape.

## Conditioning, certificates, and oracle accounting

Retain production and independently recomputed row conditioning per player:
row count, numerical rank, minimum normalized pair separation, and effective
condition number. Values must be finite when present and the two computations
must agree within `1e-10`. No favorable condition-number threshold is
preregistered; a large finite value is a result to interpret, not a reason to
edit the gate after outcome.

For every restricted master retain pivot count, primal constraint violation,
duality gap, epigraph coordinates, monotone lower/upper ledgers, cap and
epigraph checks, row additions, and the production realization-equivalence
error. The final production gap, each master diagnostic, and realization
equivalence must remain at or below `1e-8`.

Oracle accounting is derived from the sealed call graph and must equal the
observer counts. With `I` iterations and `A0` generated acting-player rows,
best-response calls are `2 * (1 + I) + 1 + A0`. Expected-utility calls are the
`1 + I` evaluation calls plus the number of responder rows resident before
each iteration's extraction. Open-axis coefficient calls are the two profile
rows plus every initial or generated non-acting response row. Evaluation,
master, and response-row call counts must also match their retained
transcripts exactly.

## Walls and decision rule

The production observed call has a 60-second infrastructure wall. The complete
parent verification, fixture construction, observed call, exact audit,
serialization preparation, and gate assembly have a 120-second infrastructure
wall. Both are deliberately separate in the artifact. Neither may be called a
per-iteration time, a solve latency, an action-clock measurement, or evidence
that a complete decision fits ADR-0307's continuous 15-second wall.

A pass requires every frozen identity, exact check, convergence and incumbent
check, master diagnostic, conditioning rebind, oracle count, retained-byte
bound, wall, finite-tree check, and clean-Git predicate to pass literally. A
pass authorizes only preregistration of a separate selector-stability gate on
this deeper legal tree. A rejection or typed infrastructure failure closes
this invocation without retry and supplies no successor authority.

## Claim boundary

No h4 target row-growth value has been opened while writing this decision or
running its controls. Development tests use only the previously opened h1
fixture or structural construction. The result path
`experiments/results/legal-responder-raise-h4-row-growth-v1.json` must be
absent at the source commit.

Even a clean pass would establish only one finite h4 responder-row growth and
infrastructure result on one legal checked-to heads-up river fixture. It would
not establish response-selector stability, repeated-actor multiway closure,
off-tree observed-action handling, preparation-bank recovery, h32 or full
private width, GPU contraction, action-clock feasibility, action emission,
production action width, blueprint quality, or poker strength. Systems
feasibility remains no quality prior.

## Next gate

Commit this complete source and protocol boundary. From that clean commit and
an absent target result path, invoke
`python -B -m pontius.legal_responder_raise_h4_row_growth` exactly once. Retain
the first terminal without retry, overwrite, parameter change, alternate
backend, or scope repair.

In parallel, keep the label-free full-width river capacity preflight separate
on the exact 1,225/1,081/1,035/990 belief axes. Neither lane may borrow the
other lane's result as a strategy-quality prior.
