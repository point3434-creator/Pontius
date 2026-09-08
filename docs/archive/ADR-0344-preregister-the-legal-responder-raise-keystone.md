# ADR-0344: Preregister the legal responder-raise sequence-form keystone

- Status: accepted preregistration and source seal before the first legal responder-raise keystone invocation; no result, strategy label, latency result, or production action exists
- Date: 2026-08-24
- Follows: ADR-0343
- Config: `experiments/configs/responder-raise-semantics-keystone-v1.json`
- Config SHA-256: `5a9899ea0ced855cdb6fa30183ccab9b3235470603d7d45f688355eac15dcafd`
- Parent decision SHA-256: `8bc61b35d467f93d0830a7ec9bf4b33e7cb9daf8f634dc1ca09ef6df4db025da`
- Legal kernel SHA-256: `9e2c45d575d28c759aea97c4f916a18584241cd84a6731e89bc609f32c2c7396`
- Legal continuation SHA-256: `4c8f57f259415ece30b12add42243b65a30d3320924b469209e2d94a68064250`
- Sequence-form primitive SHA-256: `a84126b66aad760dcda28ba4870cd4a5daba18ebe5377fef8b1efa53a04d9231`
- Legal-continuation test SHA-256: `0c6a6cb7d63aa7c25ec3570605c8886ceaf780dc9fff3433d52091dc5edc396e`
- Prospective runner SHA-256: `201b937d351d50e072d4f8f00268b3242855abd8f32c468b3d5870fad1682978`
- Runner control SHA-256: `06b5eb1a490694adc6b0a61f7590fdb26bf01e6183943bcc4792b59ced0acba6`
- Expected root public-state SHA-256: `d6976d35018153790f63698d7231d1f920f21c1dfb865a5a0733bd42d1cbcf52`
- Expected public-schema SHA-256: `1b399b2b67b58bd2a8a42d3c0e8ddeb4fbf3d2445f2f059a36c3e5905227d5ff`
- Prediction ledger SHA-256: `5c777da7cd44a76852dcc1e6aeeb5d5e664f865838794ac6ffc69b3c75066461`
- Front-Door-Kind: controller-v1
- Front-Door-Research: ADR-0280
- Front-Door-Process: ADR-0344
- Front-Door-Contract: ADR-0307
- Front-Door-Revoked: ADR-0281
- Front-Door-Active-Next: From one clean commit containing ADR-0344 and an absent responder-raise result path, invoke the source-sealed legal responder-raise keystone exactly once; retain any pass or failure without changing the tree, guard, tolerances, teacher, or claims; a pass authorizes only a separately preregistered h4 legal responder-raise open-axis differential, while the label-free full-width river capacity preflight remains a separate parallel gate
- Front-Door-Blockers: no legal responder-raise keystone result, h4 responder-raise coefficient result, responder-row capacity result, selector-stability result in the deeper tree, repeated-actor multiway existence result, off-tree opponent-action result, cross-street belief/certificate handoff, full-width capacity result, certified full-width river strategy bridge, sealed blueprint trainer/checkpoint/abstraction/slice-audit chain, trained blueprint, v0a/v0b integrated bot, preparation-bank filling result, frozen evaluation opponent pool, complete 15-second decision, production action width, or poker-strength result exists

## Question

Can the authoritative six-seat integer betting kernel supply every action and
chip payoff in one exact checked-to heads-up river responder-raise tree while
the existing one-seat sequence-form row generator reproduces a separately
enumerated complete normal-form teacher? In particular, does the tree preserve
the legal distinction between a full raise and a short all-in that the sealed
simplified sizing games intentionally do not model?

This is the first response-semantics gate after ADR-0343. It asks only about one
finite legal tree and its algebra. It does not ask whether response rows fit the
15-second clock, whether h4 coefficients can be extracted efficiently, or
whether the resulting policy is good poker.

## Decision

Add `LegalHeadsUpRiverContinuation` as a small-game bridge from
`NoLimitBettingState` to the generic extensive-form interface. The bridge does
not reimplement betting rules. At every node it enumerates fold, check, call,
and every integer raise-to amount directly from `legal_decision()`, advances
only through `apply_action()`, and obtains terminal chips only through exact
six-seat settlement. It accepts exactly two live seats after one live river
check and requires every omitted folded seat to have committed zero chips, so
the two exposed utilities remain exactly zero-sum.

The bridge is deliberately not a production tree. Literal enumeration of every
integer raise is appropriate for this finite semantic control and supplies no
scaling claim.

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

## Frozen legal tree

Replay one six-chip hand with button zero, blinds one/two, and all six seats
dealt in. Seats 3, 4, 5, and 0 fold preflop without contributing; seat 1 calls;
seat 2 checks; both live seats check flop and turn; and seat 1 checks the river.
The frozen continuation therefore has pot four, four chips behind for each live
seat, logical-player/table-seat mapping `(0 -> 2, 1 -> 1)`, and public-state
digest
`d6976d35018153790f63698d7231d1f920f21c1dfb865a5a0733bd42d1cbcf52`.

The complete public schema is fixed before the solve:

- root: check or raise-to 2, 3, or 4;
- after raise-to 2: fold, call, or full raise-to 4;
- after raise-to 3: fold, call, or short all-in raise-to 4;
- after raise-to 4: fold or call; and
- after either raise-to 4 response: the opener folds or calls.

This is six strategic nodes and eleven terminal nodes. The raise from two to
four is a full raise. The raise from three to four is a legal short all-in and
its caller has only a final fold/call response. That fixture does not
independently identify reopening—the raiser is all-in and the opener cannot
raise further—so no reopening claim may be drawn from it. Reopening remains
covered by the legal-kernel controls and requires its own strategic-tree gate
if it becomes relevant to responder closure.

The older `MultiSizeRiverHoldem` requires a configured raise-to to be at least
twice the opening bet and therefore omits raise-to four after a bet of three.
That is not a defect inside its explicit one-full-raise simplified scope. It is
the reason it cannot be promoted into the legal responder authority. The
prospective gate must detect that omission rather than silently inheriting it.

## Frozen finite-algebra control

Use board `2c 7d 9h Js Qc`, root hand `As Ad`, responder hand `Kh Kd`, and a
uniform behavioral blueprint. Optimize only logical player zero with raw guard
`0.25`, Float64 tolerance `1e-10`, at most 128 row-generation rounds, and
realization-plan retreat factor `0.8`.

The generated solver must use sequence-form realization coordinates and exact
response-row generation. The independent teacher must enumerate all 16 acting
pure plans and all 18 responder pure plans, build its mixed-normal-form LP from
direct terminal utility evaluation, and never call the open-axis coefficient
primitive. Require generated lower bound, safe incumbent, exact evaluated
NashConv, and complete-teacher objective to agree within `1e-9`, with final
`U - L <= 1e-9`. Bounds must remain monotone, retreat must satisfy the Jensen
inequalities within `1e-9`, and realization-row evaluation must agree within
`1e-9`.

The tree contains a bet/raise/final-response path on which logical player zero
acts twice. The path-single-visit behavioral shortcut must reject it and the
sequence-form solver must remain authoritative. Exact response signatures are
the only row-deduplication key.

An independent chip formula checks all eleven terminal values with a required
error of exactly zero chips. This teacher shares cards and the frozen public
history but not six-seat settlement. It is a spot control, not certification of
all legal betting states.

## Gates and terminal discipline

The one public runner uses an exclusive-create result path. Invoke it only from
one clean commit containing this ADR and only while the result path is absent.
Retain a pass, a semantic rejection, a numerical rejection, an exception, or
an infrastructure failure without retry or parameter change.

Reject the checkpoint on any source/config/provenance drift, dirty tree, public
schema drift, non-kernel action, missing full or short raise class, legacy
omission not detected, terminal chip mismatch, behavioral-shortcut acceptance,
wrong pure-plan count, teacher disagreement, reversed or nonmonotone bound,
failed Jensen control, approximate row deduplication, nonfinite value, runtime
over 60 seconds, or result-path clobber attempt. Do not delete a retained
failure to obtain another first invocation.

## Promotion and claim boundary

A pass authorizes only a new preregistration for an h4 legal responder-raise
open-axis coefficient differential on the same frozen public semantics. That
successor must keep row-growth capacity, selector stability, repeated-actor
multiway closure, and arbitrary observed off-tree raises separate, as ADR-0343
requires. A failure rejects this bridge or formulation before any h4 spend.

No h4 or full-width belief, six-player active tree, arbitrary stack, side-pot
strategy, reopening strategy, selector-stable affine solve, GPU contraction,
15-second ledger, preparation-bank workload, production action, action-width
transfer, blueprint training, league match, or poker-strength result is opened
here. The deterministic one-hand policy is a proof witness only and must not be
reported as a quality result.

The contemporaneous `docs/PREDICTION_LEDGER.md` is reporting-only. Its odds and
resolution rules cannot influence this invocation or any successor gate.
