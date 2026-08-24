# ADR-0346: Preregister the legal h4 coefficient differential

- Status: accepted preregistration and source seal before the first legal responder-raise h4 coefficient invocation; every coefficient result, row-growth result, latency result, strategy label, and production action remains unopened
- Date: 2026-08-24
- Follows: ADR-0345
- Config: `experiments/configs/legal-responder-raise-h4-coefficient-differential-v1.json`
- Config SHA-256: `e511be50649a2c1c401948d31c1245f9df890f31aceb4f53a8ef4c63c62803bc`
- Parent decision SHA-256: `cf6fbd0518d4b14702598b50335a7e068352e9731349e10410000679624efeaf`
- Parent artifact SHA-256: `a7cbb0efca87ad3bf9e2a2105d10aa137daf68a763b68518d68e893bfc74be11`
- Legal kernel SHA-256: `9e2c45d575d28c759aea97c4f916a18584241cd84a6731e89bc609f32c2c7396`
- Legal continuation SHA-256: `4c8f57f259415ece30b12add42243b65a30d3320924b469209e2d94a68064250`
- Float64 coefficient primitive SHA-256: `a84126b66aad760dcda28ba4870cd4a5daba18ebe5377fef8b1efa53a04d9231`
- Independent Fraction oracle SHA-256: `8d70297ab80055c5c77bdeefb82ff6cde817f6c57876059783046669b3a6945a`
- Oracle control SHA-256: `5b0aeba06437386156451a7d66687b0274a14abbb138f96f8b2c1ee2bb84a330`
- Prospective runner SHA-256: `e800aa343803c27744172404e1351e564e2817ce357c59bb602bbd6cb357caee`
- Runner control SHA-256: `cbf1386a05fe53efbe6db4b7a0b9bdb3681a015980f4bb36b60a89979dd02502`
- Expected h4 game provenance SHA-256: `31eb059bdd32f74fc0f72dd07927b21d32493cc2831cacac22b3fe8615658214`
- Expected source-policy SHA-256: `b69b34a644a6c3cec3094584735e8807aed1b24abdaa39806bce3540bebda55a`
- Expected coverage-response SHA-256: `310c6206a7f7cadad277d0a76f12d2d81dd00e7fd14aa2de35ae7f80f19cc34f`
- Front-Door-Kind: controller-v1
- Front-Door-Research: ADR-0280
- Front-Door-Process: ADR-0346
- Front-Door-Contract: ADR-0307
- Front-Door-Revoked: ADR-0281
- Front-Door-Active-Next: From one clean commit containing ADR-0346 and an absent legal h4 coefficient result path, invoke the source-sealed differential exactly once and retain pass, rejection, or typed failure without changing axes, policies, response tapes, endpoints, teacher, tolerances, or claims; a pass authorizes only a separately preregistered legal responder-row growth gate, while full-width river capacity remains a separate parallel lane
- Front-Door-Blockers: no legal h4 coefficient result, responder-row capacity result, selector-stability result in the deeper tree, repeated-actor multiway existence result, off-tree opponent-action result, cross-street belief/certificate handoff, full-width capacity result, certified full-width river strategy bridge, sealed blueprint trainer/checkpoint/abstraction/slice-audit chain, trained blueprint, v0a/v0b integrated bot, preparation-bank filling result, frozen evaluation opponent pool, complete 15-second decision, production action width, or poker-strength result exists

## Question

On ADR-0345's exact kernel-derived public tree, do the current Float64
sequence-form open-axis coefficients match an independent exact enumerator at
h4 private width, coefficient by coefficient? Does the identity continue to
hold for fixed responder tapes that reach both the full-raise and short-all-in
final-response sequences, and for the two gain-row directions consumed by the
one-seat convex master?

This is the finite coefficient successor authorized by ADR-0345. It does not
ask how many responder rows are needed, whether selectors remain stable, how
the representation scales, or whether any policy is strong.

## Decision

Add `exact_sequence_form_coefficient_oracle`, a deliberately small-game
Fraction implementation with its own sequence-axis enumeration, policy
normalization, direct expected-utility traversal, realization construction,
and terminal-to-last-sequence accumulation. It imports neither
`one_seat_convex_generation` nor `evaluation`. Its unit control independently
exercises the repeated-actor legal tree and rejects crossed axes and illegal
policies.

Add one failure-retaining prospective runner,
`legal_responder_raise_h4_coefficient_differential`. Its subject is exactly one
call site to `open_axis_payoff_coefficients`; its teacher is exactly one call
site to the Fraction oracle. The sealed call graph contains no LP, row
generator, candidate search, policy optimizer, action emitter, or endpoint
responder-selector call. Config or execution exceptions still consume the
exclusive result path as typed failures. A pre-existing result path is never
overwritten.

The inherited trust chain remains explicit. ADR-0310 made native-simplex
robustness the next systems question. ADR-0311's directive is Preregister the
native-simplex robustness audit. ADR-0312's directive is Seal the native-simplex audit compiler and corpora.
ADR-0313's directive is Seal the native-simplex audit runner before results.
ADR-0314's decision is Retain the native-simplex audit and reject the frozen gate.
ADR-0315's directive is Source-seal the artifact-only native-simplex gate correction.
ADR-0316's decision is Accept the corrected audit and bound replacement eligibility.
ADR-0317's directive is Separate solver classes and prioritize the certified sizing adapter.
ADR-0318 binds HiGHS 1.12.0, ADR-0319 requires one public HiGHS-DS call per
canonical task, and All 177 ordered observations pass under ADR-0320, making
the separate consumer eligible. ADR-0321 preserves caller-owned legal fallback,
ADR-0322 returns research evidence or rejection with no action, ADR-0324
remains value-unopened, ADR-0325 was authorized exactly once, ADR-0326 and
ADR-0327 govern the exhaustive bounded development-teacher chain, and ADR-0333
records that No replacement sizing value was opened at its source boundary.
ADR-0330 remains permanently closed, ADR-0331's append-and-fsync discipline
and ADR-0332's exclusive `xb` open remain authoritative, ADR-0337 remains the
response-closed direct mechanism with a dynamic-branch rebinder, ADR-0338 alone
records the selected development raise width, and ADR-0339's exact non-overlap
comparison remains a finite absence claim, not representativeness evidence.
ADR-0340's 192 prospective tasks remain distinct from ADR-0341's 94 accepted
one-call arms and ADR-0343's 126 confirmation arms. ADR-0342 alone authorized
the retained confirmation invocation. No result here weakens those authorities.

## Frozen legal h4 fixture

Reuse ADR-0345's board, six-chip checked-to river state, logical/table seat
mapping, public-state digest, public schema, and complete legal integer action
set. Widen only the private axes to four hands per player:

- root axis: `As Ad`, `Kh Kd`, `8s 8d`, `6s 5s`;
- responder axis: `Ts 8h`, `Qs Qd`, `9s 9d`, `Ac Kc`.

All 16 cross products are legal. Their frozen positive weight-numerator matrix
is
`((1,2,1,4),(2,1,3,1),(1,3,1,2),(4,1,2,3))`, whose denominator is 32.
Every stored chance probability is therefore exactly dyadic; the gate checks
both exact mass one and power-of-two denominators. The fixture has 176
chance-expanded terminal paths.

Logical player zero remains the open axis. It has 12 information sets and 32
sequence variables: 16 root variables plus 16 final-response variables across
the full-raise and short-all-in histories. The behavioral path-single-visit
shortcut must reject.

## Frozen policies and tapes

The source policy explicitly covers both players' 24 information sets. It
uses key-rotated dyadic templates by legal action width, with digest
`b69b34a644a6c3cec3094584735e8807aed1b24abdaa39806bce3540bebda55a`.
Freeze six acting policies: source, check/fold, bet-two/call, bet-three/fold,
bet-three/call, and all-in/call. Their six exact digests are committed in the
config before invocation.

Freeze two responder tapes in addition to the source profile:

1. a coverage tape that raises to four at all eight eligible h4 information
   sets and splits its four remaining all-in responses into two folds and two
   calls; and
2. the source-policy responder best response, selected once and then fixed
   across all endpoints.

The responder and acting source best-response action digests and hexadecimal
values are frozen in the config. No responder selector is recomputed at an
endpoint. That boundary is enforced by the source-sealed call graph and its
AST control, not by a runtime Boolean pretending to observe calls it cannot
observe. Selector stability remains a later experiment.

## Frozen differential

Extract four payoff rows, each with all 32 coefficients:

- source profile payoff for player zero;
- source profile payoff for player one;
- coverage-response payoff for player one; and
- source-best-response payoff for player one.

Derive two more 32-coefficient gain rows: acting best-response constant minus
acting profile payoff, and responder fixed-response payoff minus responder
profile payoff. Serialize every Float64 coefficient as hexadecimal beside the
teacher Fraction numerator and denominator. Digests alone do not substitute
for retained coefficient evidence.

For every row, compare the constant and every coefficient directly. Then bind
the row at all six acting endpoints to both the standard Float64 evaluator and
the exact teacher's direct utility. Require exact Fraction affine/direct
identity, exact zero-sum utilities, and identity between Float64 and exact
realization coordinates. Both final-response histories must have nonzero
coverage-row coefficients.

## Gates and terminal discipline

Require exact h4 axes, 16 deals, 176 terminal paths, the 12/32/16 information-
set/sequence/final-response counts, all frozen policy and response identities,
one full and one short-all-in final-response history, repeated-actor shortcut
rejection, four payoff plus two gain rows, and clean Git provenance. Maximum
coefficient, realization, affine-value, gain-value, Float64/exact utility, and
acting-best-response identity errors are each `1e-12`. Exact teacher
affine/direct mismatches must be zero. Total control wall must not exceed 60
seconds.

The prospective result path is
`experiments/results/legal-responder-raise-h4-coefficient-differential-v1.json`.
It must be absent at the clean source commit. Invoke the public runner once.
Retain an all-pass result, scientific rejection, config failure, exception, or
infrastructure failure without deletion, retry, or post-outcome repair.

## Promotion and claim boundary

An all-pass result authorizes only a separate preregistration for legal
responder-row growth on this h4 tree. That successor must measure exact response
signatures, generated-row counts, conditioning, oracle work, and retained bytes
before any preparation-bank or action-clock claim. Selector stability,
multiway closure, off-tree observation, and full-width capacity remain separate
gates.

This line opens no coefficient result yet. Even a later pass would establish
only h4 coefficient identity on one frozen legal tree. Direct traversal timing
is not row-growth capacity, h32 or full-width latency, a 15-second decision, or
a systems prior for quality. No strategy label, quality row, production action,
blueprint claim, or poker-strength claim is authorized.
