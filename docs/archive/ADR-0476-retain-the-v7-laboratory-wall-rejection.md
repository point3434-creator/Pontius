# ADR-0476: Retain the v7 laboratory-wall rejection

- Status: accepted complete-journal negative one-shot terminal and permanent v7 closure; the exact authorized public command ran once from commit `aaca2dda40e29be8ebd091d58e7853bce1c62fd8`, durably consumed its attempt and launch identities, retained a hash-valid 592-record journal, and terminated `laboratory_wall_rejected` after `1510053980800` ns against the frozen `1500000000000` ns laboratory wall; the public and outside-laboratory walls remained below their ceilings, but the incomplete campaign emitted no fit projection and selected no candidate, topology, or arithmetic schedule; zero authoritative complete-campaign measured calls and zero complete measured passes exist, while 89 stored partial-pass cells marked measured remain diagnostic only; no retry, continuation, compiled-calibration result, symbolic-45 projection, material-zeta claim, production numerical admission, resolver result, action-clock result, decision-quality result, truncation, blueprint result, or strength result is authorized
- Date: 2026-08-27
- Follows: ADR-0475
- Source and authorization commit: `aaca2dda40e29be8ebd091d58e7853bce1c62fd8`
- Source-seal commit: `56127da2970f5a8a8056a97a247ebe1fdf4b983b`
- Result: `artifacts/work_preflight/legal_river_quotient_compiled_global_separation_calibration_v7.jsonl`
- Result bytes / raw SHA-256: `7858857 / 78b2f8351ca49785756ec336d4f967bcc83a86f9ef96506a6144726cf3b312b3`
- Result records / header / observations / terminal: `592 / 1 / 590 / 1`
- Attempt: `artifacts/work_preflight/legal_river_quotient_compiled_global_separation_calibration_v7.attempt.json`
- Attempt bytes / raw SHA-256: `1825 / ada1896f0bf63111e0c1e5e707315fbca6c13f6e2b63222805cb5ef4cb9dc413`
- Consumed launch: `artifacts/work_preflight/legal_river_quotient_compiled_global_separation_calibration_v7.launch-consumed.json`
- Consumed-launch bytes / raw SHA-256: `349 / c3c0a34cba6a677157034d8f8109cf47edea496a33c64992293176d879a2d629`
- Launch token SHA-256: `14904ff277cdf6396577a416464740e58104598b535a6026d286f768b7ee1086`
- Independent reader terminal / passed / terminal-complete journal: `laboratory_wall_rejected / false / true`
- Sealed-reader execution state: exact authorization HEAD `aaca2dda40e29be8ebd091d58e7853bce1c62fd8` with the three finalized lifecycle artifacts as the only untracked paths; a descendant retention HEAD deliberately fails the authorization-HEAD gate, so future reproduction requires recreating that exact checkout and materializing these exact retained bytes
- Reader scientific-call count / authoritative measured-call count: `569 / 0`
- Complete warmup cells / stored partial-pass measured-labelled cells / planned measured cells: `480 / 89 / 2400`
- Laboratory elapsed / wall / excess ns: `1510053980800 / 1500000000000 / 10053980800`
- Outside-laboratory elapsed / wall ns: `48722365700 / 300000000000`
- Public elapsed / wall ns: `1558776346500 / 1800000000000`
- Diagnostic primitive wall / base-structural-cover wall ns: `1293642809900 / 1247206514200`
- Candidate / topology / arithmetic schedule selected: `null / null / null`
- Production base classification / numerical admission: `producer_absent / null`
- Material-zeta speed claim / symbolic-45 projection / truncation authorized: `null / null / false`
- Front-Door-Kind: controller-v1
- Front-Door-Research: ADR-0280
- Front-Door-Process: ADR-0476
- Front-Door-Contract: ADR-0307
- Front-Door-Revoked: ADR-0281, ADR-0468, ADR-0472, ADR-0475
- Front-Door-Active-Next: Hold the compiled synthetic topology-calibration lane and conduct the architecture checkpoint before any successor owner: bind a real production source-local base producer, its exact algebra, epoch identity, refresh cadence, exponent admission, and cold-versus-hit frequency in the one-seat river bridge, or park this lane and return to v0a integration; any later compiled experiment requires a fresh preregistration and lifecycle, must charge cold structural cover once per genuine production epoch and provenance hits at their actual consumers, and may not reuse v7's partial rows, relax the rejected wall, thin the frozen population, or select an arm from this artifact
- Front-Door-Blockers: v7 is permanently consumed and the compiled calibration is incomplete; no production source-local base producer, refresh cadence, exponent admission, or width bound exists; no selected topology, complete reduced compiled-calibration result, population-25 result, actual-45 numerical result, global resolver-certificate integration, complete resolver iteration, known certificate count per action, or 15-second action result exists; no repeated-actor multiway existence result, off-tree opponent-action result, cross-street belief and certificate handoff, certified full-width river strategy bridge, trained blueprint, integrated bot, production action width, or poker-strength result exists

## Question

Did the sole ADR-0475 invocation complete the frozen compiled calibration, and
if not, what evidence and authority survive?

## Decision

No. Retain the exact negative terminal, close v7 permanently, and authorize no
retry or continuation. The exact root launcher entered once from clean commit
`aaca2dda40e29be8ebd091d58e7853bce1c62fd8`. The 1,825-byte attempt and
349-byte consumed-launch marker bind that invocation and remain exact. Pending
and aborted launch paths are absent. The 7,858,857-byte result contains 592 LF-
only journal records whose protocol, campaign, sequence, payload, semantic,
record, and previous-record hash chain independently rebinds without error.
Every observation names the exact authorization commit.

Before retention, the independent sealed reader accepted the artifact from the
exact authorization HEAD, with the result, attempt, and consumed-launch marker
as the only untracked lifecycle paths. It accepted a complete durable journal
with one terminal, not a complete scientific campaign. Its terminal is
`laboratory_wall_rejected`, its pass bit is false, and its 590 observations
include 569 calibration-cell wrappers. The laboratory elapsed wall is
`1510053980800` ns against `1500000000000` ns, an excess of `10053980800` ns.
The outside-laboratory partition is `48722365700` ns against
`300000000000` ns, the public wall is `1558776346500` ns against
`1800000000000` ns, and laboratory plus outside-laboratory equals public
exactly. The frozen check rejected before dispatching the next cell; the last
completed cell was differentially checked and journaled. The excess includes
the interval through rejection cleanup and is not attributed wholly to that
cell.

The measurement vocabulary is kept explicit. Reader `complete=true` means the
journal has a valid terminal; it does not mean all 2,880 planned calls ran.
Reader `measured_call_count=0` means zero authoritative completed-campaign
measurements are admitted from a rejected campaign. The retained bytes contain
one complete 480-cell warmup pass and 89 cells from the first of five required
measured passes. Those 89 records carry `measured=true` because of their
schedule position, but they are a hash-ordered partial pass, not a complete
measurement population. No fit-projection record exists. They may diagnose the
wall but may never feed a fit, materiality conjunct, topology ranking, schedule
ranking, or candidate selection. Stored pass bits are nonauthoritative.

A separate read-only diagnostic reconstructed every stored 19-phase partition
and work receipt. It found 1,293.6428099 seconds of recorded primitive wall, of
which 1,247.2065142 seconds was `base_structural_cover`: 96.41 percent of
recorded primitive work and 82.59 percent of total laboratory elapsed. Cold
base refresh accounts for effectively all of that phase; exact-provenance-hit
cells total about 0.002 seconds there. RRNS cold structural cover contributes
about 1,107.3 seconds and positional cold cover about 139.9 seconds. These are
diagnostics from an incomplete schedule, not an arm comparison, a production
frequency, a speed result, or evidence that one closure topology lost. The
current repository still classifies the production base as `producer_absent`,
so no production cold/hit cadence exists to amortize.

The independent reader deliberately stops before full cell-value validation on
a rejecting terminal. It therefore validated durable journal completeness,
identity, type boundaries, terminal claims, and rejection closure, but it does
not certify the 569 partial cell values as a calibration. Future result types
must keep terminal-complete journal, complete scientific campaign, stored
measured-labelled rows, and accepted measured population as separate semantic
quantities. ADR-0476 makes that distinction in the record rather than changing
the consumed reader after outcome.

The reader is also deliberately authorization-HEAD-bound. Both public
assessment entry points require actual HEAD to equal the sole-child six-path
authorization commit. The ADR-0476 retention commit necessarily becomes a
descendant with a different diff, so direct assessment from latest HEAD will
reject after retention. That is expected security behavior, not evidence
corruption. Future reproduction must create an exact detached checkout at
`aaca2dda40e29be8ebd091d58e7853bce1c62fd8`, materialize the three retained
bytes at their exact paths without changing HEAD, and run the sealed reader
there. Do not weaken the reader post-outcome to admit the retention commit.

No candidate, topology, or arithmetic schedule is selected. The compiled-
calibration result, material-zeta speed claim, symbolic target projection,
production numerical admission, literal-45 result, resolver iteration,
action-clock fit, decision quality, blueprint, and poker strength remain null;
truncation remains unauthorized. `producer_absent` is the only production-base
classification carried forward. The artifact is clean negative evidence and
not a systems-quality prior.

Do not create a friendlier v8 by increasing 1,500 seconds, reducing repeats,
thinning domains, reordering the observed prefix, or relabeling the same cold
work. Before any future device owner, the architecture must acquire an actual
production base producer and freeze its algebra, epoch, invalidation, refresh
cadence, exponent window, and semantic bound. Only then can a new gate test the
structurally different hypothesis that cold structural cover is paid once per
genuine producer epoch while exact provenance hits serve repeated certificate
consumers. If that producer does not exist on the near-term product path, park
the compiled topology lane and return effort to the playable v0a integration
boundary. This ADR authorizes neither branch's implementation.

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
closes v7 permanently.

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

The exact journal, attempt, and consumed-launch marker are permanent retained
negative evidence. They prove one authorized invocation, a complete durable
journal, exact identity and hash-chain closure, and the laboratory-wall
terminal. They do not prove a complete calibration, any fit or arm comparison,
production frequency, target capacity, action fit, or decision quality. The
sealed-reader verdict was obtained before retention at the exact authorization
HEAD; historical reproduction requires reconstructing that checkout state.

### Kill criteria

V7 is already consumed and may never run again. Kill any proposed successor
that reuses its protocol, campaign, result, attempt, launch, or authorization
identity; changes or omits the retained bytes; treats 89 partial-pass rows as a
complete measured population; raises the rejected wall or thins the campaign
to make the same mechanism pass; infers a topology from the incomplete prefix;
or claims epoch amortization before a production base producer and refresh
cadence are bound.

### Claims boundary

ADR-0476 proves only the retained negative terminal, exact lifecycle and Git
identity, journal integrity, wall arithmetic, and scoped diagnostic attribution
stated above. It supplies no passing compiled calibration, materiality,
topology, arithmetic-schedule, symbolic-target, numerical-target, resolver,
action-clock, decision-quality, truncation, blueprint, or strength result.
Independent checks are spot-checking, not certification.

## Consequences

- V7 is permanently consumed and closed under `laboratory_wall_rejected`.
- The three exact lifecycle artifacts are retained; no replay or continuation exists.
- No topology or arithmetic schedule is selected from the incomplete campaign.
- The compiled topology lane pauses at an architecture checkpoint until a production base producer and cadence exist or the lane is parked.
