# ADR-0440: Correct the batched device-preflight phase topology before source seal

- Status: accepted prospective pre-source correction; ADR-0439's impossible one-pass twelve-phase ledger is retained for positional and resident-nine RRNS but superseded for batched-five-then-four RRNS by two consecutive fully charged pass ledgers and an explicit drain/reuse boundary, scalar and verification transfers now precede their host consumers by name and order, the captured-pair level-six/fixed-width-levels-zero-through-five hybrid is explicit, and no source seal, compiler execution, CuPy import, device query, module load, kernel launch, result, population-25 value, or actual-45 numerical value exists
- Date: 2026-08-26
- Follows: ADR-0439
- Parent config: `experiments/configs/legal-river-quotient-fixed-width-device-preflight-v1.json`
- Parent config canonical-LF SHA-256: `84da7e82ef07620b0d7869a1e52da6a80f5f3815c0e4dc7007068ce6664ed6af`
- Correction config: `experiments/configs/legal-river-quotient-fixed-width-device-preflight-v2-topology.json`
- Correction config canonical-LF SHA-256: `6ebca361aed6c6cfcd11fd2df0b6041c1f676a7e6b07af9739bcd84e64b38e41`
- ADR-0439 canonical-LF SHA-256: `861e10e5ab9d924554ba588d7f69735b39da343547c53329033837de596c1f71`
- ADR-0439 preregistration commit: `096d4ae0a78fa9de3c3c3838c8a64997b716816d`
- Discovery state: one prospective source draft existed only as an untracked, unsealed worktree file; no successor source or control was committed, no compiler or device stack was invoked, and the result remained absent
- Successor source-seal/compile/CuPy/device-query/module-load/kernel-launch/result counts: `0/0/0/0/0/0/0`
- Population-25 and actual-45 numerical calls: `0/0`
- Front-Door-Kind: controller-v1
- Front-Door-Research: ADR-0280
- Front-Door-Process: ADR-0440
- Front-Door-Contract: ADR-0307
- Front-Door-Revoked: ADR-0281
- Front-Door-Active-Next: Implement and source-seal only the ADR-0439 preflight under ADR-0440's corrected arm-specific topology: preserve one twelve-phase partition for positional and resident-nine RRNS; preserve one twenty-phase partition for batched-five-then-four RRNS with first-batch channels `0,1,2,3,8`, a completed output drain, reuse of the same table/stream workspace, and second-batch channels `4,5,6,7`; retain level six as captured high/low pairs and fixed-width forward levels zero through five; run only the fresh-challenge no-CUDA launcher handshake at source seal; keep compile, device operation, result, population 25, actual-45 numerics, candidate selection, resolver integration, action, quality, truncation, blueprint, and strength absent until the corrected source boundary is cleanly committed
- Front-Door-Blockers: no corrected source seal, compiled cubin, resource result, exact reduced-device result, bounded phase wall, eligible or selected candidate, actual-45 fit owner, 15-second fit result, global resolver-certificate integration, or full-width actual-context quotient value exists; no general odd-chip or side-pot leaf automaton, repeated-actor multiway existence result, off-tree opponent-action result, cross-street belief and certificate handoff, certified full-width river strategy bridge, sealed blueprint trainer/checkpoint/abstraction/slice-audit chain, trained blueprint, v0a/v0b integrated bot, preparation-bank filling result, frozen evaluation opponent pool, complete 15-second decision, production action width, or poker-strength result exists

## Discovery

ADR-0439 froze two requirements that cannot both hold under one contiguous
twelve-phase candidate trace. Batched-five-then-four RRNS must complete a
five-channel pass, drain its outputs, reuse the same table workspace, reread
the same captured pairs, and then pay for a four-channel recurrence and every
downstream operation. A phase partition is a sequence of consecutive boundary
differences. Once its `forward_recurrence` or `adjoint_recurrence` interval has
closed, the second pass cannot return to it. Running both recurrences before
the downstream work would require two simultaneously live table workspaces,
contradicting the frozen reuse contract and changing the memory question.
Charging replay work under unrelated later phase names would make the phase
labels false.

The contradiction was found while tracing the prospective device owner. One
source draft existed as an untracked file, but it had not been source-sealed or
committed. No CUDA compiler, CuPy import, device query, allocation, module
load, kernel launch, or result call occurred. This is therefore a prospective
protocol correction rather than an outcome-conditioned relaxation.

The same trace exposed an avoidable ambiguity in the original phase names:
`reconstruction_divisibility_fault_check_and_rounding` preceded the phase
named `output_transfer_and_exact_differential`. Host reconstruction cannot
honestly precede the scalar transfer it consumes. No result exploited that
wording.

## Correction

Positional and resident-nine RRNS retain one twelve-phase trace. Their scalar
phase is now named
`scalar_output_transfer_reconstruction_divisibility_fault_check_and_rounding`,
and the following phase is
`verification_output_transfer_and_exact_differential`. Transfer therefore
precedes every host consumer explicitly.

Batched-five-then-four RRNS uses the correction config's ordered twenty-phase
trace. After the common validation and allocation prefix, channels
`0,1,2,3,8` traverse admission/encoding, forward recurrence, selective and
global forward work, adjoint recurrence, and selective and global adjoint
work. The next phase drains bounded output residues and digests, destroys no
raw captured input, and closes the first workspace lifetime. Channels
`4,5,6,7` then replay the same complete chain through the same workspace
storage identities. Only after both passes do scalar transfer, exact
reconstruction, divisibility, fault checks, rounding, verification transfer,
the independent differential, and cleanup occur.

Every arm-specific phase interval is the difference of consecutive monotonic
integer host stamps. A CUDA synchronization precedes each boundary that closes
device work. The exact sum of all twelve or all twenty intervals equals that
candidate/population/repeat wall. No phase is reentered, and no disjoint
intervals are merged under one label. ADR-0439's candidate wall, laboratory
wall, ordering, repeat, and evidence rules are unchanged.

## Hybrid level-six boundary

The implementation trace also makes ADR-0438's memory representation explicit
rather than leaving it to a field name. Forward source level six remains the
captured high/low binary64-pair buffer. Fixed-width storage contains forward
levels zero through five only; level-five row owners encode their level-six
children directly from captured pairs. The adjoint side contains fixed-width
levels zero through four after six-label aggregation. Materializing a
five-limb or nine-channel level-six table would replace roughly 8.34 GB of
captured pairs at literal-45 tile width 64 with roughly 20.85 GB positional or
37.53 GB resident RRNS storage and answer a different memory question. The
correction config makes that mutation rejecting.

This is not a new optimization learned from timing. It is the hybrid already
represented by ADR-0438's separate `captured_pair_level_6_bytes` and
`forward_levels_0_through_5_bytes` fields, now stated as an executable
precondition.

## Controls and claim boundary

Source-seal controls must reject a batched trace forced into twelve phases, a
second recurrence before first-pass drain, simultaneous first/second table
workspace lifetimes, a missing drain or replay interval, reconstruction before
scalar transfer, either arm-specific partition whose exact sum changes, and
fixed-width level-six materialization. The independent reader must derive the
applicable phase domain from the arm label, not accept a stored phase-count or
pass bit.

All other ADR-0439 clauses remain binding: one translation unit, one direct
CUDA 13.3 `sm_120` cubin, exact same-byte inspection and execution, raw
resource evidence, conservative resource maxima, zero ptxas spill bytes,
symbolic literal-45 memory only, complete-10 and signed-12 numerical work only,
balanced orders and repeats, integer walls, durable first-terminal evidence,
and no candidate selection. This correction supplies no compiled result,
device fit, population-25 evidence, actual-45 numerical value, resolver
iteration, 15-second action result, decision quality, truncation, blueprint,
or poker strength.

## Decision

Accept the correction before source seal. Preserve ADR-0439 as the parent
protocol, supersede only its candidate-phase topology and ambiguous transfer
wording through the immutable V2 overlay, and continue implementation without
compiler or device operation. A clean corrected source seal must be committed
before the one authorized public invocation.

Freeze one additive preflight before source or operation. Compile all three
schedule arms from one literal CUDA translation unit and one ordered CUDA 13.3
NVCC option list into one direct `sm_120` cubin. The arms are signed positional
limbs, resident-nine RRNS, and batched-five-then-four RRNS. The last is a
schedule of the RRNS candidate, not a third arithmetic theorem, and must pay
for its second recurrence and every replay read, edge, load, store, channel,
and transfer under ADR-0440's corrected twenty-phase topology.

The preflight is a screen, not a selector. An arm can become eligible only if
its exact reduced-population outputs, resource instruments, symbolic memory
liveness, phase accounting, and frozen walls all pass. `candidate_selected`
remains null even if one arm is the only survivor. A later artifact-only
decision may compare survivors, and any actual-45 or 15-second question needs
another prospective gate.

The inherited front-door trust chain remains explicit. ADR-0310 made native-
simplex robustness the next systems question. ADR-0311's directive is
Preregister the native-simplex robustness audit. ADR-0312's directive is Seal
the native-simplex audit compiler and corpora. ADR-0313's directive is Seal the
native-simplex audit runner before results. ADR-0314's decision is Retain the
native-simplex audit and reject the frozen gate. ADR-0315's directive is
Source-seal the artifact-only native-simplex gate correction. ADR-0316's
decision is Accept the corrected audit and bound replacement eligibility.
ADR-0317 separates solver classes; ADR-0318 binds HiGHS 1.12.0; ADR-0319
requires one public HiGHS-DS call per canonical task; and All 177 ordered
observations pass under ADR-0320. ADR-0321 preserves caller-owned legal
fallback, ADR-0322 returns research evidence or rejection with no action,
ADR-0324 remains value-unopened, and ADR-0325 was authorized exactly once.
ADR-0326/0327 govern the exhaustive bounded development-teacher; ADR-0328
retains it and the solver-free rebinder before the direct closed finite-block
greedy line; ADR-0330 remains permanently closed; ADR-0331's append-and-fsync
discipline, ADR-0332's exclusive `xb` open, and ADR-0333's No replacement
sizing value was opened statement remain binding. ADR-0334/0335 bind the
2,113-task non-replay chain; ADR-0336 records width three; ADR-0337 owns the
response-closed direct mechanism; ADR-0338 alone records the selected
development raise width; and ADR-0339 remains a finite absence claim.
ADR-0340's 192 prospective tasks remain distinct from ADR-0341's 94 accepted
one-call arms and ADR-0343's 126 confirmation arms; ADR-0342 alone authorized
the retained confirmation. ADR-0344/0345 own the finite h4 responder-raise
keystone line. ADR-0346/0347 lead only to responder-row growth; ADR-0348/0349
lead only to selector-window work. ADR-0350 opened selector-stable affine
integration; ADR-0351 replaced it with tie-aware legal h4 affine envelopes;
ADR-0352 is closed by ADR-0353; ADR-0354/0355/0356 own the factorized exact face
result; ADR-0357/0358/0359 own and close same-fixture integration; and ADR-0360/
0361/0362 alone own the untouched confirmation and assessment. ADR-0363 and
ADR-0365 remain consumed; ADR-0364 remains exactly `GetProcessMemoryInfo failed`;
ADR-0366 remains exactly `representation_rejected_before_target_allocation`
with zero target calls. ADR-0367 through ADR-0384 own and close the quotient
algebra, capacity, bounded CUDA, staged, liveness, validation, and literal-
target ladder. ADR-0380 freezes the complete ordered populations 10 and 22.
ADR-0381 source-seals the one-shot literal-45 CUDA owner. ADR-0385
preregisters the actual-context quotient bridge; ADR-0386 records the source-
sealed actual-context quotient bridge; ADR-0387 freezes the consumer-capacity
seam; and ADR-0388 records the source-sealed CuPy-free consumer-capacity result.
ADR-0389 remains the accepted prospective actual-context quotient CUDA-consumer
boundary; ADR-0390 rejects its source seal; ADR-0391 remains an accepted
prospective bounded-arithmetic boundary and freezes the first paired-tile
boundary; ADR-0392 remains the accepted prospective preregistration-completeness
correction and corrects its pre-source arithmetic completeness; ADR-0393
remains the accepted bounded-device source-seal rejection and retains the first
implementation as a wall rejection. ADR-0390 and ADR-0393 retain the exact
historical status label accepted bounded-device source-seal rejection.
ADR-0394 through ADR-0416 own and close the paired work-preflight, exact-cubin
qualification, and retained capacity rejection. ADR-0417 through ADR-0432 own
and close the shared-direct successor and artifact-only capacity rejection.
ADR-0433 through ADR-0435 own the captured-pair exact-integer keystone.
ADR-0436 freezes the fixed-width comparison, ADR-0437 corrects its provenance
control before source, ADR-0438 source-seals both CPU candidates, ADR-0439
opens only the separate compiled-device preflight, and ADR-0440 corrects its
phase topology before source seal.

For machine-checked continuity, ADR-0317's directive remains Separate solver
classes and prioritize the certified sizing adapter. All 177 ordered
observations pass under ADR-0320, making the separate consumer eligible.
ADR-0326 and ADR-0327 govern the exhaustive bounded development-teacher chain.
ADR-0328 retains that exhaustive teacher and solver-free rebinder. ADR-0334 and
ADR-0335 bind the 2,113-task non-replay chain. ADR-0344 and ADR-0345 own the
finite h4 legal responder-raise keystone line. ADR-0346 and ADR-0347 lead only
to responder-row growth. ADR-0348 and ADR-0349 lead only to selector-window
work. ADR-0351 requires the tie-aware legal h4 affine-envelope. ADR-0354 through
ADR-0359 own the factorized face and affine consumer chain. ADR-0380 freezes
the complete ordered populations 10 and 22. ADR-0383's owner was invoke exactly
once and remains consumed by ADR-0384. The phrases exclusive untouched legal
h4, selector-window, 2,113-task, exhaustive bounded development-teacher,
response-closed direct mechanism, and caller-owned legal fallback retain their
prior meanings.

The exact historical continuity strings remain explicit. ADR-0352 remains
closed before any fresh untouched tie-aware affine result. ADR-0353 precedes
ADR-0354's factorized exact active-set directional-face diagnostic. ADR-0355's
owner was invoke exactly once; ADR-0356 retains that directional-face
diagnostic before tie-aware affine integration. ADR-0357 requires an exclusive
legal h4 owner, ADR-0358 was invoke exactly once, and ADR-0359 requires a fresh
value-unopened confirmation. ADR-0367 preregisters the occupied-card quotient.
ADR-0368 seals the exact bounded algebra keystone. ADR-0369 freezes the
source-only arithmetic boundary. ADR-0370 seals the numeric-array and logical-work
result. ADR-0378 freezes the source-only literal-target liveness boundary.
ADR-0379 retains the 244,970,204-byte margin. ADR-0382 preregistered the
literal-45 config. ADR-0386 records the source-sealed actual-context quotient bridge.
ADR-0405 remains an accepted source seal.
