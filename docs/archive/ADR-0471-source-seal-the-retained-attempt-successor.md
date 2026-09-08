# ADR-0471: Source-seal the retained-attempt successor

- Status: accepted CPU-only retained-attempt successor source seal; the fresh v6 launcher, runner, complete independent reader, exact retained-v5-attempt recovery header, durable attempt and one-use launch lifecycle, injected authorization and Git proof, and source-only controls pass 17/17 with zero skips; combined v4/v5/v6 regression passes 74/74 and the 35-test calibration-base regression passes; the retained 606-byte v5 attempt remains byte-exact, every v3/v4/v5 closed-state predicate and every v6 lifecycle path remains unchanged, and no public v6 owner, compiler call, CuPy import, device work, timing value, or result exists
- Date: 2026-08-27
- Follows: ADR-0470
- Recovery config: `experiments/configs/legal-river-quotient-compiled-global-separation-calibration-v8-v5-attempt-recovery.json`
- Recovery config canonical-LF SHA-256: `5fab5270880625e8f909fd7f1a334f6fa38471ca34bd453de47d93fbfd2413ff`
- Launcher: `run_legal_river_quotient_compiled_global_separation_calibration_v6.py`
- Launcher bytes / canonical-LF SHA-256: `2337 / ff1630f2264a17b3d3825ef5b7b0650b5d11c95cc7e22991cd16190ded2c1a44`
- Runner: `src/pontius/legal_river_quotient_compiled_global_separation_calibration_v6_runner.py`
- Runner bytes / canonical-LF SHA-256: `28465 / b3aa4436e574b575537a39301a68857bfe32562bd55460ab182c4931b98cb35f`
- Independent reader: `src/pontius/legal_river_quotient_compiled_global_separation_calibration_v6_result.py`
- Reader bytes / canonical-LF SHA-256: `43564 / ad3f3f22ca30d8598c8b9a337b14a5c870e0b2e5a236bebd052797a1afef4f47`
- Controls: `tests/test_legal_river_quotient_compiled_global_separation_calibration_v6.py`
- Controls bytes / canonical-LF SHA-256: `62293 / 31b6d5eaa6b17ed3aaa657561dd1da04a035daa9f954d659e81a1411b5c55978`
- Focused source-only controls / skipped: `17/17` passed / `0`
- Combined v4/v5/v6 regression: `74/74` passed
- Calibration-base, v2-outcome, and v3 regression: `35/35` passed
- Actual header mapping domains / missing-key mutations / extra-key mutations: `21 / 355 / 21`
- Rejection aliases / started-science aliases / success-site aliases rejected: `46 / 47 / 56`
- Retained v5 attempt bytes / raw SHA-256: `606 / 104820d0c67391365d18fb76ca72c704e40e467e2993a96c618d4bf91155600d`
- V4 public invocations / v4 result rows / v5 public invocations / v5 result rows: `0 / 0 / 1 / 0`
- V6 public invocations / v6 result rows / v6 attempt markers / v6 launch markers: `0 / 0 / 0 / 0`
- Compiler calls / CuPy imports / device queries / allocations / module loads / kernel launches / timing values: `0/0/0/0/0/0/0`
- Candidate / topology / arithmetic schedule selected: `null / null / null`
- Front-Door-Kind: controller-v1
- Front-Door-Research: ADR-0280
- Front-Door-Process: ADR-0471
- Front-Door-Contract: ADR-0307
- Front-Door-Revoked: ADR-0281, ADR-0468
- Front-Door-Active-Next: Create exactly one separate authorization commit whose sole parent is this source seal and whose diff is limited to the frozen six-file v6 authorization surface; then rerun all 17 focused v6 controls from that exact clean commit, require the live one-generation ancestry branch to pass with zero skips, recheck every retained and unopened lifecycle path, and stop before the public owner unless every prefire gate passes
- Front-Door-Blockers: no separate one-generation v6 invocation authorization or v6 result exists and the public v6 owner remains uninvoked; v5 is permanently closed after its retained accidental attempt and v4 is permanently closed uninvoked; no production source-local base producer, refresh cadence, exponent admission, or width bound exists; no selected topology, population-25 result, actual-45 numerical result, global resolver-certificate integration, complete resolver iteration, known certificate count per action, or 15-second action result exists; no repeated-actor multiway existence result, off-tree opponent-action result, cross-street belief and certificate handoff, certified full-width river strategy bridge, trained blueprint, integrated bot, production action width, or poker-strength result exists

## Question

Does the fresh v6 retained-attempt successor satisfy ADR-0470 at source-seal
scope strongly enough to create a separate one-generation authorization?

## Decision

Yes, at source-seal scope only. Do not invoke the public owner from this ADR.
The v6 launcher, runner, independent reader, and controls are accepted as the
sole prospective successor to the permanently closed v4 and v5 lifecycles.
The exact v5 attempt marker remains a regular, non-symlink, non-reparse
606-byte file with raw SHA-256
`104820d0c67391365d18fb76ca72c704e40e467e2993a96c618d4bf91155600d`.
The rejected-v3 result, every v4 lifecycle path, the v5 result, authorization
and launch paths, and every v6 result, attempt, authorization and launch path
remain absent by `lexists`.

The launcher now tests effective `-B` and safe-path state immediately after
the builtin `sys` import and before `pathlib` or any repository import. Its
unsafe control scrubs both `PYTHONPATH` and `PYTHONSAFEPATH`, executes only an
isolated copied launcher with a poisoned non-builtin import, and requires the
exact pre-import failure. The real launcher is source-imported safely but no
test calls its private or public owner. All public, child, reader, Git,
dependency, attempt and launch wrappers recheck the retained predecessor state
in `finally`; v4's binding lock is always acquired before v6's, and no v5 lock
or v5 public assessor is used.

A final independent audit found that the runner module's own `main` entry could
bypass the launcher's safe-path guard before source seal. The runner now checks
exact argv, `sys.dont_write_bytecode`, and `sys.flags.safe_path` as the first
statement in `main`, before predecessor checks or inherited delegation. A
non-invoking AST control fixes that order and synthetic calls reject each
missing property independently. This was corrected before any v6 public entry
or lifecycle artifact existed; it is not a result or consumed attempt.

The production header round-trips through the independent reader with all 16
top-level fields, including the separately typed retained-v5-attempt recovery
layer. Recursive controls cover all 21 mapping domains with 355 missing-key and
21 extra-key mutations after rebuilding the semantic and journal chains.
Forty-six rejection aliases, 47 imported/started-science aliases, and 56
success-comparison aliases prove that Boolean/integer equality cannot stand in
for exact JSON type identity. The reader validates imported-but-unstarted
science truthfully, and executed-module identity becomes authoritative only
when science actually starts.

Authorization parsing and Git validation execute against injected exact
responses in both writer and reader. Both reject a working authorization file
whose bytes differ from its committed Git blob. Real temporary paths exercise
cold attempt creation, pending-to-consumed, pending-to-aborted and implicit
abort transitions without touching a production lifecycle path. The one live
ancestry branch is present and source-tested in its authorization-absent state;
it must run against the real authorization in the next clean commit before an
owner can become eligible.

The fresh-process source probe imports only the hash-bound deferred science
source needed by the inherited provenance check. It observes science absent
before that import, CuPy absent throughout, no repository bytecode, no compiler
execution and no device query. It never starts calibration science. The probe
leaves the retained attempt byte-identical and every v6 lifecycle path absent.
This distinction is deliberate: a source import is not a scientific execution,
and neither is evidence of device or numerical behavior.

Three independent read-only audits found no concrete source, runner, reader or
test blocker after the final controls were added. The final focused suite passes
17/17 with zero skips; the combined v4/v5/v6 regression passes 74/74; and the
calibration-base, v2-outcome and v3 regression passes 35/35. These are scoped
checks, not certification. A latent implementation, driver, compiler or device
defect can still make the one-shot run reject. The lifecycle converts such a
failure into retained evidence rather than permission to retry.

Authorization remains external to this seal. The future authorization must use
the frozen v9 path and `pontius-adr0472-one-commit-v6-authorization-v1` schema.
Its commit must be the sole child of this source-seal commit and change exactly
`ARCHITECTURE.md`, `RISK_REGISTER.md`, `ROADMAP.md`, `STATUS.md`, the exact
ADR-0472 file, and the exact v9 authorization config. It may not change any
sealed implementation, test, recovery config, retained marker or lifecycle
byte. The complete 17-test suite must then pass from that exact clean HEAD with
the live Git-ancestry branch exercised before the public owner is fired.

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
pre-owner failure, ADR-0460 freezes the absolute-Git recovery, ADR-0461 source-
seals that recovery, ADR-0462 retains its launch-arity rejection, ADR-0463
opens the fresh arity source lane, ADR-0464 corrects that lane before source
seal, ADR-0465 records the rejected v3 source seal, ADR-0466 closes v3
uninvoked, ADR-0467 source-seals the deferred-import v4 lifecycle, ADR-0468
authorizes only its exact one-generation invocation identity without firing it,
ADR-0469 rejects that authorization gate and closes v4, ADR-0470 retains the
accidental v5 attempt and closes v5, and ADR-0471 source-seals only fresh v6.

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
literal-45 config. ADR-0386 records the source-sealed actual-context quotient
bridge. ADR-0405 remains an accepted source seal.

### Source-seal boundary

Only the fresh v6 lifecycle, retained-attempt recovery layer, effective
launcher guard, exact source bindings, independent reader, temporary lifecycle
transitions, and CPU-only controls are sealed. The source probe's provenance
import starts no science. Compiler and device work remain unopened. A later
public v6 owner consumes the identity at attempt creation even if authorization,
launch, compiler, device or scientific gates reject afterward.

### Kill criteria

Kill before invocation if the retained v5 marker differs by one byte; any
v3/v4/v5 closed or v6 unopened path exists even as a dangling link; the source
seal and authorization are not exact parent and child; the authorization diff
is not exactly the frozen six paths; any sealed dependency differs from its
source-seal Git blob; the complete 17-test suite does not pass from clean HEAD;
the live ancestry branch does not execute; a repository bytecode or extension
shadow is present; any legacy environment variable survives; or the owner would
run from a checkout that is not the exact authorization commit.

### Claims boundary

ADR-0471 proves only the scoped source, reader, lifecycle and adversarial
controls described above. It supplies no compiled calibration, numerical,
resource, speed, topology, population-25, target-45, resolver, action-clock,
decision-quality, truncation, blueprint or strength result. The independent
audits and tests are spot-checking, not certification. A clean negative first
invocation remains a valid and permanently retained result.

## Consequences

- The retained v5 attempt remains immutable evidence; v4 and v5 stay closed.
- V6 is source-sealed but not yet authorized or invoked.
- Exactly one separate ADR-0472 authorization generation may make v6 eligible.
- The full live-authorization suite and clean-state audit must pass before firing.
