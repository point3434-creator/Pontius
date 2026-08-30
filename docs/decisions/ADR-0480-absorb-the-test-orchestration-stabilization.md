# ADR-0480: Absorb the test-orchestration stabilization

- Status: accepted process absorption; the 2026-08-27 through 2026-08-29 stabilization era — orchestration contracts (Task 1), Windows reparse/OneDrive architecture fixes (Task 11a), and the test inventory and profile generator (Task 2) — is integrated onto the mainline at merge `156f0b3` after two independent whole-candidate adversarial CLEAN reviews on the frozen 11-file manifest, a bound holistic architecture audit, and a controller substitution ruling for the unreachable CodeRabbit gate; the generator's `--check` and the stabilization boundary check both pass from the integrated primary checkout, checked-in capability state remains intentionally absent with every capability outcome deny-all pending the Task 10 approval gate, no broad scientific/GPU suite ran, and no ADR-0476 research blocker is cleared
- Date: 2026-08-29
- Follows: ADR-0479
- Frozen candidate manifest (sorted rows, SHA-256): `79600d1112e52a37f22b649b5d4d5a2f382cb8daf247082466700729b99e82ef`
- Candidate commit: `8c1bed3` on `codex/orch-task2` (11 files, 65,449 insertions, base `a265976`)
- Integration merge: `156f0b3` on `master` (34 files, 97,127 insertions, zero path overlap with the governance commits, every reviewed SHA preserved)
- Acceptance gates at the frozen candidate: inventory/profile suite 87/87; configuration/model suite 53/53; H32 fixture 9 run, 8 passed, exactly one approved unconditional skip; pre-write `--check`, authorized `--write`, and post-write `--check` all exit 0
- Generated inventory SHA-256: `0dd70ea42bcbde0c2abfc156c20c0214060a504b80bfb1cbbad495d48336543d`
- Generated profiles SHA-256: `2773545eb34b8e643c55c87e1e6ba6ee0a3ac5a930038d4266f514e54ae497ea`
- Holistic architecture audit SHA-256: `24dcbf30c023ab785a09f9232e5e0c230df027c7737322f6da1d13f7474ab02d`
- External review: two fresh independent whole-candidate adversarial reviews, both CLEAN, manifest unchanged before and after each; CodeRabbit gate substituted by controller ruling after four identical authenticated `WebSocket closed` connection failures at the pre-analysis connecting phase (CLI 0.7.5 latest, valid seat, service-side), with the exact ruling and evidence recorded in the Task 2 report and progress ledger
- Post-merge mainline validation: `tools/generate_test_inventory.py --check` exit 0 and `tools/check_stabilization_boundaries.py` exit 0 from the integrated primary checkout
- Capability state: checked-in subprocess definitions / call definitions / bindings are `0 / 0 / 0`; every capability outcome is deny-all pending the Task 10 hard user approval gate
- Front-Door-Kind: controller-v1
- Front-Door-Research: ADR-0280
- Front-Door-Process: ADR-0480
- Front-Door-Contract: ADR-0307
- Front-Door-Revoked: ADR-0281, ADR-0468, ADR-0472, ADR-0475
- Front-Door-Active-Next: Hold the compiled synthetic topology-calibration lane and conduct the architecture checkpoint before any successor owner: bind a real production source-local base producer, its exact algebra, epoch identity, refresh cadence, exponent admission, and cold-versus-hit frequency in the one-seat river bridge, or park this lane and return to v0a integration; any later compiled experiment requires a fresh preregistration and lifecycle, must charge cold structural cover once per genuine production epoch and provenance hits at their actual consumers, and may not reuse v7's partial rows, relax the rejected wall, thin the frozen population, or select an arm from this artifact. Separately, continue the stabilization plan's remaining orchestration tasks under the installed collaboration protocol, rule explicitly on the proposed protocol amendments during the architecture review, and complete the open operations items — the restore drill, push automation, and a retained-evidence inventory test — before broad-suite reliance
- Front-Door-Blockers: v7 is permanently consumed and the compiled calibration is incomplete; no production source-local base producer, refresh cadence, exponent admission, or width bound exists; no selected topology, complete reduced compiled-calibration result, population-25 result, actual-45 numerical result, global resolver-certificate integration, complete resolver iteration, known certificate count per action, or 15-second action result exists; no repeated-actor multiway existence result, off-tree opponent-action result, cross-street belief and certificate handoff, certified full-width river strategy bridge, trained blueprint, integrated bot, production action width, or poker-strength result exists; the stabilization adds test-governance capability but clears none of these, and broad-suite execution, capability approvals, the holistic-audit backlog, the protocol-amendment rulings, and the restore drill remain open

## Question

Between 2026-08-27 and 2026-08-29, the evidence-integrity and test-profile
orchestration plans executed outside the decision record. What is now
accepted onto the mainline, on what evidence, and what does the record still
not claim?

## Decision

Absorb the stabilization era into the record and make the mainline the single
canonical line. The merge `156f0b3` integrates three bodies of reviewed work
onto `master` with zero path overlap against the governance commits and every
reviewed commit hash preserved: the Task 1 orchestration contracts, the Task
11a Windows reparse and OneDrive architecture corrections (integrated at
`a265976` with `FileAttributeTagInfo` bound from opened handles before and
after every read), and the Task 2 test inventory and profile generator.

Task 2 is the era's center of mass. Its 25,356-line generator and 30,366-line
test suite implement exact baseline and working discovery, four ownership
partitions, an exact AST capability and source-order analyzer with typed
fail-closed blockers, secure same-directory governance publication with
ownership-owning transaction and retry machinery, and raw authenticated Git
object access. The candidate survived an initial frozen review rejection and
five bound fix rounds that widened into roughly eighteen correction
iterations, each with deterministic RED reproductions before production edits
and integrated GREEN evidence after. The frozen 11-file candidate at manifest
`79600d1112e52a37f22b649b5d4d5a2f382cb8daf247082466700729b99e82ef` passed
87/87 inventory, 53/53 configuration, and the exact H32 gate with one
approved unconditional skip, regenerated its governance outputs byte-stably,
and was accepted by two independent whole-candidate adversarial reviews, both
CLEAN with the manifest recomputed unchanged before and after inspection.

The external CodeRabbit gate did not run: four authenticated invocations of
the exact command failed with the identical recoverable `WebSocket closed`
transport error before analysis, with the client current, the seat valid, and
the service's status page showing degraded markers. The controller ruled the
gate substituted, the adversarial CLEAN verdicts standing as external review,
with a courtesy rerun permitted if the service recovers; the ruling, its
evidence, and its cost-if-wrong are recorded in the Task 2 report. The
correction loop is deliberately wound down: the bound holistic audit found no
remaining correctness defect, named architectural concentration as the
principal residual risk, recorded a read-only diagnostic that the retained v7
journal's structural cover ran serially on device, and left a prioritized
post-acceptance backlog. Those are recommendations, not authorizations.

Two v7 maintenance modules received reviewed corrections closing the
authorization re-read defects; the sealed retained v7 artifacts are
byte-unchanged and now hash-bound by the ADR-0479 manifests. Checked-in
capability state is intentionally absent — zero subprocess definitions, zero
call definitions, zero bindings — so every capability outcome remains
deny-all until the Task 10 hard approval gate. No broad scientific or GPU
suite ran during the era, and this absorption makes no payload claim beyond
the focused gates named above. From the integrated mainline, the generator's
`--check` and the stabilization boundary check both exit 0.

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
accidental v5 attempt and closes v5, ADR-0471 source-seals only fresh v6,
ADR-0472 authorizes only its exact one-generation identity without firing it,
ADR-0473 rejects that gate and closes v6 uninvoked, ADR-0474 source-seals only
fresh v7, ADR-0475 authorizes only its exact one-generation invocation identity
without firing it, and ADR-0476 retains its laboratory-wall rejection and
closes v7 permanently. ADR-0477 through ADR-0480 record the stabilization
era — archive replication, the agent charter and collaboration protocol, the
evidence layer and sealed-boundary manifests, and this orchestration
absorption — without invoking any consumed owner or altering any retained
byte.

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

### Result boundary

The absorbed era proves reviewed, integrated, deny-all test-governance
infrastructure and the focused gates named above. It proves no broad-suite
execution, no capability approval, no scientific or GPU payload result, no
compiled-calibration progress, and no change to any retained evidence byte.
The serial-structural-cover observation is a read-only diagnostic of the
retained v7 journal, not a speed claim, an arm comparison, or authorization
for device work.

### Kill criteria

Kill any use of this absorption as payload evidence: generator acceptance is
not test-suite passage, and deny-all rows are not approvals. Kill any
capability execution before the Task 10 hard approval gate. Kill any reopening
of the wound-down Task 2 correction loop absent a fresh finding under the
workflow protocol. The CodeRabbit substitution is specific to this candidate
and its recorded failure evidence; future gates rule on their own substitutions
explicitly or run their tools.

### Claims boundary

ADR-0480 proves only the reviewed acceptance, integration, and validations
stated above. It supplies no research result, clears no ADR-0476 blocker,
adopts no proposed protocol amendment, authorizes no item of the holistic
audit's backlog, and makes no poker-strength, resolver, action-clock, or
blueprint claim.
