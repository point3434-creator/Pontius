# ADR-0464: Correct the launch-arity successor before source seal

- Status: accepted prospective pre-source-seal completeness correction; ADR-0463's independent all-site audit found that `evaluate_selected_leaves_rrns_batch` declares ten parameters while its sole host call supplies eleven through an obsolete extra `np.uint64(scan_count)`, so the permitted v3 delta now includes removing exactly that argument in addition to inserting the missing direct `source_count`, while all 46 launch sites must match all 28 unchanged CUDA declarations before source seal and no compiler, device, timing, or fresh result exists
- Date: 2026-08-26
- Follows: ADR-0463
- Config: `experiments/configs/legal-river-quotient-compiled-global-separation-calibration-v4-launch-abi-completeness.json`
- Config canonical-LF SHA-256: `58668f557bcc1f3420454124b8d930d7e59a9d1a870003a8093776f1175d9a92`
- ADR-0463 preregistration commit: `3de8e0c9eebf67f2cc2573041242a869468de6e9`
- Independent CUDA entries / host launch sites / mismatches after first repair: `28 / 46 / 1`
- Additional mismatched kernel: `evaluate_selected_leaves_rrns_batch`
- CUDA declaration / host arguments: `10 / 11`
- Extraneous host expression: `np.uint64(scan_count)` after `cards`
- Device replay / compiler / device / timing / fresh result calls: `0/0/0/0/0`
- Candidate / topology / arithmetic schedule selected: `null / null / null`
- Front-Door-Kind: controller-v1
- Front-Door-Research: ADR-0280
- Front-Door-Process: ADR-0464
- Front-Door-Contract: ADR-0307
- Front-Door-Revoked: ADR-0281
- Front-Door-Active-Next: Complete and source-seal the corrected v3 successor only: preserve the exact v2 artifact, parent source, and CUDA literal; insert `np.uint64(scan_count)` only into the timed direct kernel's `source_count` slot; remove the obsolete `np.uint64(scan_count)` only from the selected-leaf RRNS call; require the independent declaration audit to pass all 46 launch sites and both opposite-sign mutations; retain the central pre-driver arity guard and fresh lifecycle; keep the v3 result absent and stop before compiler, CuPy scientific import, device, timing, or result work
- Front-Door-Blockers: no corrected v3 source seal or result exists; ADR-0461's v2 owner is permanently consumed; no complete compiled calibration, measured pass, material-zeta result, production base producer/admission, selected topology, population-25 result, literal-45 numerical result, resolver integration, certificate count per action, or 15-second action result exists; no repeated-actor multiway existence result, off-tree opponent-action result, cross-street belief and certificate handoff, certified full-width river strategy bridge, trained blueprint, integrated bot, production action width, or poker-strength result exists

## Question

May ADR-0463 be source-sealed after its new all-launch-site control finds a
second, opposite-sign arity mismatch outside the originally permitted delta?

## Decision

No. Correct the prospective boundary before changing that call. ADR-0463
authorized insertion of the missing `source_count` into the timed direct RRNS
launch and a structural arity fence. When the independently written AST audit
applied that conceptual repair across the complete effective source, 45 of 46
launch sites matched their literal CUDA declarations. The remaining site was:

```text
evaluate_selected_leaves_rrns_batch
CUDA parameters: 10
host arguments:  11
extra argument:  np.uint64(scan_count)
```

The CUDA entry already receives `selected_count` and bounds work by
`selected_count * channel_count`; it has no `source_count` parameter. The host
tuple retained an obsolete scan-count argument between `cards` and `moduli`.
If reached, this would pay the same `CUDA_ERROR_INVALID_VALUE` rejected-
invocation tax as ADR-0462. No device replay was needed to establish it.

Expand the permitted effective-source delta by exactly one removal. After both
repairs, the independent audit must report 46 sites, 28 declarations, and zero
mismatches. Restoring the selected-leaf extra must reproduce the 10-versus-11
failure; removing the direct insertion must reproduce the 9-versus-8 failure.
Changing either declaration must reject. The runtime guard remains derived
from the declarations and must stop a malformed tuple before driver dispatch.

Everything else in ADR-0463 remains frozen: parent and retained-result bytes,
literal CUDA bytes, matrix, order, fixtures, arms, arithmetic schedules,
one-arena liveness, phases, work coordinates, projector, thresholds, walls,
fresh lifecycle, and claims. The correction is prospective because no source
seal, compiler, device, timing value, or v3 result exists.

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
opens only the separate compiled-device preflight, ADR-0440 corrects its phase
topology before source seal, ADR-0441 source-seals that corrected owner,
ADR-0442 consumes its compiler rejection, ADR-0443 and ADR-0444 own the first
MSVC recovery, ADR-0445 consumes its zero-event terminal, ADR-0446 freezes the
split-environment successor, ADR-0447 source-seals it without compilation or
device work, ADR-0448 alone retains its passing first device-preflight
terminal without selecting a candidate or opening actual-45 numerics,
ADR-0449 freezes the artifact projection, ADR-0450 corrects its runtime and
artifact accounting, ADR-0451 seals the projector, ADR-0452 retains its
rejection, ADR-0453 freezes the selective-separation mechanism, ADR-0454
source-seals it without opening a result, ADR-0455 freezes the base-first four-
topology successor while closing that result owner uninvoked, ADR-0456 source-
seals the reduced successor without opening its bake-off, ADR-0457 freezes the
compiled calibration, ADR-0458 source-seals it, ADR-0459 consumes its sole
pre-owner failure, ADR-0460 freezes the absolute-Git recovery, ADR-0461
source-seals that recovery, ADR-0462 retains its launch-arity rejection,
ADR-0463 opens the fresh arity source lane, and ADR-0464 corrects that lane
before source seal.

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

### Source-seal boundary

The corrected source seal may contain only the two named call-site repairs,
the declaration-derived arity overlay, fresh lifecycle wrappers/readers, and
their controls. Any other effective-science difference rejects. Source-seal
work remains CPU-only and result-unopened.

### Kill criteria

Kill any path that calls 45/46 sufficient, suppresses the selected-leaf arm,
changes its CUDA declaration to fit the erroneous host tuple, drops the
selected-leaf control, weakens the complete matrix, or invokes the compiler or
device before a clean corrected source seal.

### Claims boundary

ADR-0464 is a prospective source-completeness correction only. It provides no
compiled calibration, numerical, resource, speed, topology, target, resolver,
action-clock, decision-quality, truncation, blueprint, or strength result.

## Consequences

- Both an omitted and an extraneous argument are now named members of R222.
- The complete all-site audit, not the first observed failure, defines repair
  completeness.
- The v3 identity remains unopened and may be source-sealed only at 46/46.
