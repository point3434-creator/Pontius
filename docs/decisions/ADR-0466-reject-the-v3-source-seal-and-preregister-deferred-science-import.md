# ADR-0466: Reject the v3 source seal and preregister deferred science import

- Status: accepted prefire source-seal rejection and fresh lifecycle preregistration; three independent CPU-only audits prove that ADR-0465's v3 campaign child would resolve the immutable parent science instead of the repaired overlay and that the eagerly loaded overlay would make any successful journal fail the inherited bootstrap reader, so v3 is closed permanently uninvoked with both result and compiler/device evidence absent, while a fresh v4 owner must emit bootstrap before an explicit sealed-science import, bind the executed module and complete signature manifest, durably consume pre-writer attempts, and later require a one-commit invocation authorization
- Date: 2026-08-26
- Follows: ADR-0465
- Rejected source-seal commit: `77feb7c78990ca53e70b1302a6866fe5d781411f`
- Config: `experiments/configs/legal-river-quotient-compiled-global-separation-calibration-v5-deferred-science-import.json`
- Config canonical-LF SHA-256: `f61d236530e8add3e5eb063f9f3afa641e205defd9cdefaa56fd9a2de53c8d1f`
- V3 public invocations / result rows: `0 / 0`
- V3 result exists: `false`
- Compiler calls / CuPy scientific imports / device queries / allocations / module loads / kernel launches / timing values: `0/0/0/0/0/0/0`
- Independent audits confirming both blockers: `3/3`
- CUDA declarations / host launch sites / count mismatches / semantic argument mismatches: `28 / 46 / 0 / 0`
- Candidate / topology / arithmetic schedule selected: `null / null / null`
- Front-Door-Kind: controller-v1
- Front-Door-Research: ADR-0280
- Front-Door-Process: ADR-0466
- Front-Door-Contract: ADR-0307
- Front-Door-Revoked: ADR-0281
- Front-Door-Active-Next: Implement and source-seal only a fresh v4 lifecycle around ADR-0465's immutable scientific overlay: keep v3 permanently uninvoked and absent; import neither science module at v4 module scope; emit and acknowledge bootstrap with science and CuPy absent; explicitly import the exact v3 module afterward without aliasing; bind its effective-source, CUDA, complete recomputed signature-manifest, and executed-module identities; install a durable attempt marker and exact Git-status states; retain fresh protocol/campaign/result identities and an independent reader; stop before compiler, device, timing, or v4 result work, then create a separate one-commit invocation authorization naming that source-seal commit
- Front-Door-Blockers: no correct deferred-import v4 source seal, invocation authorization, or v4 result exists; ADR-0465's v3 owner is permanently closed uninvoked and ADR-0461's v2 owner is permanently consumed; no production source-local base producer, refresh cadence, exponent admission, or width bound exists; no selected topology, population-25 result, actual-45 numerical result, global resolver-certificate integration, complete resolver iteration, known certificate count per action, or 15-second action result exists; no repeated-actor multiway existence result, off-tree opponent-action result, cross-street belief and certificate handoff, certified full-width river strategy bridge, trained blueprint, integrated bot, production action width, or poker-strength result exists

## Question

May the clean ADR-0465 source identity be invoked after a final prefire audit of
the exact campaign-child import and reader paths?

## Decision

No. Permanently close the v3 owner uninvoked and preserve its absent result.
Three independent read-only audits and a separate local reproduction found the
same two critical lifecycle defects without importing CuPy, querying a device,
or invoking the public owner.

First, `_fresh_scientific_module_alias` changes only the parent's fully
qualified `sys.modules` entry. The v3 runner has already imported the immutable
parent science, leaving that object on the `pontius` package attribute. The
inherited campaign child later executes:

```text
from . import legal_river_quotient_compiled_global_separation_calibration as science
```

Python resolves the existing package attribute, not the replacement stored
only in `sys.modules`. A safe exact-import probe observed the parent at the
package attribute, the v3 overlay in `sys.modules`, and the production import
returning the parent. Firing v3 would therefore bypass both call-site repairs
and the central guard and would likely repeat ADR-0462's 8-versus-9 driver
rejection.

Second, importing v3 runner eagerly imports the v3 science overlay. After
`configured_parent` binds `SCIENTIFIC_MODULE` to that v3 name, the inherited
child's pre-import bootstrap necessarily records
`scientific_source_loaded=true`. The independent reader requires false. A dual
package-plus-`sys.modules` alias would fix only the first defect; any successful
result would remain unreadable under the frozen bootstrap contract.

The controls were green because they exercised different semantics. The alias
test used full-name `__import__`, which consults the changed `sys.modules`
entry rather than the production relative-import path. The synthetic journal
injected a rejecting campaign directly and never executed the production child;
the inherited reader returns early for a rejection before validating bootstrap.
Those are now named members of the recurring scope-substitution family: one
import mechanism stood in for another, and rejection readability stood in for
success readability.

The audit also found three lower-severity integrity gaps. The reader accepted a
mutated signature row while trusting an unchanged stored manifest digest; the
header therefore did not bind the complete signature contents or the module
actually executed. Failures before the parent writer left no durable attempt
marker. Finally, the clean-Git check accepted any clean 40-hex HEAD rather than
one bounded authorization descendant of the source seal. The fresh successor
must close all three before invocation.

Freeze a fresh v4 lifecycle, not a mutation of sealed v3. The new runner must
not import either science module at module scope and must not use module
aliasing. Its own additive campaign child reuses the inherited child-runtime
validator, emitter, schemas, walls, claims, and terminal shaping. It emits and
acknowledges bootstrap while the exact v3 science name and CuPy are absent,
then imports that exact v3 module explicitly and calls its
`execute_calibration`. Every terminal carries the executed module name,
effective-source hash, CUDA hash, and recomputed complete signature-manifest
hash. The independent reader recomputes the manifest from all 28 ordered rows
and rejects any detachment.

Before mutable public preconditions, v4 must create one exclusive durable
attempt marker. Its strict Git wrapper admits exactly marker-before-result and
marker-plus-result-after-create. A later source-seal commit is not itself
invocation authority: one subsequent authorization commit must name that exact
parent source-seal commit, contain only the frozen authorization surface, and
be the current HEAD. An unchanged owner on any later clean descendant rejects.

The remaining scientific audit is clean at spot-check scope. All 46 host sites
match all 28 CUDA declarations in count, order, scalar width, pointer meaning,
and status layout. The effective source remains exactly one deletion and one
insertion with SHA-256 `7c63e2706f5aa28c37f25bfa58d09f03d2f5fe26f3a3312fe2baf7b849cec3fc`;
the CUDA literal remains `4f626802bd792788dff74c58adb90e7e30876e0c8f22d7fcb79de0c90334f8f7`.
This does not certify equal-arity semantics generally.

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
ADR-0463 opens the fresh arity source lane, ADR-0464 corrects that lane before
source seal, ADR-0465 records the rejected v3 source seal, and ADR-0466 closes
v3 uninvoked while opening only the deferred-import lifecycle successor.

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

### Kill criteria

Kill any successor that imports science before bootstrap, uses an alias to
redirect the inherited relative import, delegates to the inherited campaign
child, trusts a stored manifest without recomputation, omits executed-science
identity, leaves a pre-writer attempt retryable, accepts an arbitrary later
clean HEAD, mutates v3 science, or opens compiler/device evidence before its
fresh source seal and authorization.

### Claims boundary

ADR-0466 is a prefire lifecycle rejection and prospective repair only. It
provides no compiled calibration, numerical, resource, speed, topology, target,
resolver, action-clock, decision-quality, truncation, blueprint, or strength
result. The clean static ABI audit is spot-checking, not certification.

## Consequences

- ADR-0465 remains historically exact but carries no invocation authority.
- The fresh successor removes import aliasing rather than strengthening it.
- Readability of success and durability of pre-owner failure become explicit
  lifecycle obligations before the next one-shot command exists.
