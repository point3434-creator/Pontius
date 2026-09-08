# ADR-0407: Preregister the artifact-only exact-cubin inspector selector

- Status: accepted prospective artifact-only selection boundary; one standard-library selector may later classify ADR-0406's immutable corpus under candidate roles, parser grammar, quantity pairing, componentwise maxima, empty-selection semantics, and source/result separation frozen before selector source or authoritative assessment, while every inspector choice, resource gate, calibration population, phase, projection, complete 25-card numerical value, actual 45-card value, action, quality, truncation, blueprint, and strength result remains null
- Date: 2026-08-26
- Follows: ADR-0406
- Config: `experiments/configs/legal-river-exact-cubin-inspector-selection-v1.json`
- Config canonical-LF SHA-256: `70ca948001fc406cd3e4a9e9f8fd4f359184ed622753d92749c542d44a3ed73a`
- Input result: `artifacts/work_preflight/legal_river_exact_cubin_inspector_diagnostic_v1.jsonl`
- Input result bytes: `705101`
- Input result SHA-256: `9e0d160dd36884adb85914f819e11882d5becc42071f7847c1503a42c1d83aed`
- Prospective selector source: absent
- Prospective authoritative assessment: absent
- Reserved actual result: absent
- Front-Door-Kind: controller-v1
- Front-Door-Research: ADR-0280
- Front-Door-Process: ADR-0407
- Front-Door-Contract: ADR-0307
- Front-Door-Revoked: ADR-0281
- Front-Door-Active-Next: Implement only the ADR-0407 standard-library artifact selector, committed source-hash seal, and synthetic controls; source-seal them with the authoritative selection result absent; require the only selectable candidate to pass the exact CUDA 13.3 identity plus zero-return complete `REG`/`STACK`/`LOCAL` parser contract for all three direct kernels; prove `no_qualified_inspector` remains reachable, candidate qualification is independent of the 255/4096 resource ceilings, and no import or execution surface reaches CuPy, CUDA, subprocess, either external tool, a consumed owner, calibration, population construction, the reserved actual owner, or any poker consumer; after a separate clean commit, invoke the sealed no-argument result writer exactly once and retain its deterministic first assessment without retry
- Front-Door-Blockers: no source-sealed or authoritative artifact-only selector, semantically qualified exact-binary inspector, resource-gate verdict, retained 10/22-card calibration, conservative complete-25 capacity verdict, complete 25-card numerical result, actual owner, or full-width actual-context quotient value exists; the three work-preflight owners and exact-cubin diagnostic owner are permanently consumed; no general odd-chip or side-pot leaf automaton, repeated-actor multiway existence result, off-tree opponent-action result, cross-street belief and certificate handoff, certified full-width river strategy bridge, sealed blueprint trainer/checkpoint/abstraction/slice-audit chain, trained blueprint, v0a/v0b integrated bot, preparation-bank filling result, frozen evaluation opponent pool, complete 15-second decision, production action width, or poker-strength result exists

## Question

Under rules fixed before selector source, does any retained ADR-0406 candidate
provide the exact per-function resource quantities ADR-0395 requires?

## Decision

Preregister a source/result-separated, GPU-free selector over the exact
ADR-0406 artifact. This ADR contains no selector source and no authoritative
selection. It freezes which candidate may qualify, the parser it must pass,
the meaning of every paired quantity, and the honest empty terminal before an
assessment exists.

The exact input is 705,101 bytes with SHA-256
`9e0d160dd36884adb85914f819e11882d5becc42071f7847c1503a42c1d83aed`.
The selector must independently recover all 12 journal records through the
hash-bound standard-library ADR-0405 reader, decode and rehash every binary
envelope, verify the retained source commit and 514,039-byte payload identity,
and keep the reserved actual result absent. It may not rewrite or normalize
the input.

### Candidate semantics

NVIDIA's CUDA 13.3 Binary Utilities documentation gives
`cuobjdump --dump-resource-usage` the exact relevant role: per-function
resource output includes `REG`, `STACK`, and `LOCAL`; register is a count and
stack/local are bytes. The same documentation describes default `nvdisasm`
as cubin disassembly and shows per-function `SHI_REGISTERS`, but it does not
define the complete per-function stack/local tuple required here. The
prospective selector therefore freezes these roles:

| Retained candidate | Role | Selectable |
|---|---|---:|
| `cuobjdump_version` | exact tool identity support | no |
| `cuobjdump_resource_usage` | complete resource candidate | yes |
| `cuobjdump_elf` | container-metadata support | no |
| `nvdisasm_version` | exact tool identity support | no |
| `nvdisasm_default` | disassembly/register-metadata support | no |

This is not a popularity choice between tools. It follows the output semantics
needed by ADR-0395. Version success, ELF magic, driver loadability, section
metadata, SASS, and a register count are each insufficient without all three
requested fields for all three kernels.

### Frozen qualification

`cuobjdump_resource_usage` qualifies only when its paired identity command and
payload operation both have status `completed`, return code zero, the exact
CUDA 13.3.73 identity, and admissible raw streams. The resource stdout must be
strict ASCII. Its independently implemented parser uses full function headers
`Function\s+([^:]+):` and resource tokens
`([A-Z]+(?:\[\d+\])?):(\d+)`, rejects duplicate functions or fields, and
requires `REG`, `STACK`, and `LOCAL` for, in order:

1. `direct_selected_queries_tile`;
2. `direct_selected_fold_tile`; and
3. `direct_selected_adjoint_tile`.

Unrelated function rows and fields may exist but cannot substitute for a
required row. LF and CRLF may delimit semantic lines without changing raw byte
identity. Synthetic corpora must prove the new parser differentially
equivalent to the immutable scientific parser for valid and invalid shapes;
the selector may not import that scientific module.

The driver/candidate combination is also frozen semantically:

- candidate `REG` pairs only with driver `registers`;
- candidate `STACK + LOCAL` bytes pair only with driver
  `local_size_bytes`; and
- each reported combined quantity is the componentwise maximum.

Numerical equality is not required. More importantly, instrument qualification
does not depend on whether those maxima pass 255 registers or 4,096 backing
bytes. A valid instrument can report a failing resource result; an invalid
instrument cannot become valid because its nearby numbers are small. The
selector retains the two ceilings but leaves `resource_gate_result=null`.

The terminal is exactly `qualified_inspector` with candidate id, parsed rows,
and combined rows, or `no_qualified_inspector` with all of those fields null.
Input corruption instead yields `artifact_rejection`. There is no generic
`passed` bit whose meaning could drift across those categories.

### Offline and lifecycle boundary

The selector imports only the standard library and the hash-bound
standard-library diagnostic reader. CuPy, CUDA, compilation, module load,
device query, kernel launch, subprocess, `cuobjdump`, `nvdisasm`, temporary
files, and network access are forbidden. All five candidate outcomes are read
from the retained journal. The source seal must use synthetic evidence only
for selection logic and must leave the authoritative result absent.

The later result writer validates its committed canonical-LF source hash
before input read and creates one compact canonical ASCII JSON plus terminal
LF through exclusive no-clobber creation, flush, and fsync. Source and result
must be separate commits. A first result or artifact rejection is permanent;
there is no retry, parser correction, or alternate-candidate negotiation under
the same identity.

Controls must cover a fully qualifying synthetic resource output, all-five-
nonzero and real-shaped empty selections, version-pass/resource-fail, ELF-
magic/driver-only evidence, nvdisasm register-only output, non-ASCII, omitted,
duplicated, reordered, and field/unit mutations, componentwise maxima,
ceiling/qualification independence, input identity mutations, import/effect
closure, exclusive replay, and reserved-result absence.

The inherited front-door trust chain remains explicit. ADR-0310 made native-
simplex robustness the next systems question. ADR-0311's directive is
Preregister the native-simplex robustness audit. ADR-0312's directive is Seal
the native-simplex audit compiler and corpora. ADR-0313's directive is Seal
the native-simplex audit runner before results. ADR-0314's decision is Retain
the native-simplex audit and reject the frozen gate. ADR-0315's directive is
Source-seal the artifact-only native-simplex gate correction. ADR-0316's
decision is Accept the corrected audit and bound replacement eligibility.
ADR-0317 separates solver classes; ADR-0318 binds HiGHS 1.12.0; ADR-0319
requires one public HiGHS-DS call per canonical task; and All 177 ordered
observations pass under ADR-0320. ADR-0321 preserves caller-owned legal
fallback, ADR-0322 returns research evidence or rejection with no action,
ADR-0324 remains value-unopened, and ADR-0325 was authorized exactly once.
ADR-0326/0327 govern the exhaustive bounded development-teacher; ADR-0328
retains it and the solver-free rebinder; ADR-0330 remains permanently closed;
ADR-0331's append-and-fsync discipline, ADR-0332's exclusive `xb` open, and
ADR-0333's No replacement sizing value was opened statement remain binding.
ADR-0334/0335 bind the 2,113-task non-replay chain; ADR-0336 records width
three; ADR-0337 owns the response-closed direct mechanism; ADR-0338 alone
records the selected development raise width; and ADR-0339 remains a finite
absence claim. ADR-0340's 192 prospective tasks remain distinct from
ADR-0341's 94 accepted one-call arms and ADR-0343's 126 confirmation arms;
ADR-0342 alone authorized the retained confirmation. ADR-0344/0345 own the
finite h4 responder-raise keystone. ADR-0346/0347 lead only to responder-row
growth; ADR-0348/0349 lead only to selector-window work. ADR-0350 opened
selector-stable affine integration; ADR-0351 replaced it with tie-aware legal
h4 affine envelopes; ADR-0352 is closed by ADR-0353; ADR-0354/0355/0356 own
the factorized exact face result; ADR-0357/0358/0359 own and close same-fixture
integration; and ADR-0360/0361/0362 alone own the untouched confirmation and
assessment. ADR-0363 and ADR-0365 remain consumed; ADR-0364 remains exactly
`GetProcessMemoryInfo failed`; ADR-0366 remains exactly
`representation_rejected_before_target_allocation` with zero target calls.
ADR-0367 through ADR-0384 own and close the quotient algebra, capacity,
bounded CUDA, staged, liveness, validation, and literal-target ladder.
ADR-0368 seals only the exact bounded algebra keystone for the occupied-card
quotient within that chain. ADR-0369 is the source-only arithmetic boundary.
ADR-0370 seals the numeric-array and logical-work result. ADR-0378 remains the
accepted prospective source-only literal-target liveness and streamed-
validation boundary, and ADR-0379 retains its 244,970,204-byte device-cap
margin without live admission. ADR-0381 source-seals the bounded validation
seam before the one-shot literal-45 CUDA owner. ADR-0385 froze the legal bridge
question; ADR-0386 source-sealed only its host answer; ADR-0387 froze the
consumer-capacity question; ADR-0388 source-sealed only that CuPy-free answer;
ADR-0389 froze the additive CUDA-consumer question; ADR-0390 rejected its
source seal; ADR-0391 froze the first paired-tile boundary; ADR-0392 corrected
its pre-source arithmetic completeness; ADR-0393 retained the first
implementation as a wall rejection; ADR-0394/0395 freeze the work and resource
questions; ADR-0396 through ADR-0403 own and close the three consumed preflight
owners; ADR-0404/0405/0406 own and close the exact-cubin diagnostic; and
ADR-0407 freezes only its artifact selector. No earlier owner is revived.

For machine-checked continuity, ADR-0317's directive remains Separate solver
classes and prioritize the certified sizing adapter. All 177 ordered
observations pass under ADR-0320, making the separate consumer eligible.
ADR-0326 and ADR-0327 govern the exhaustive bounded development-teacher
chain. ADR-0328 retains that exhaustive teacher and solver-free rebinder.
ADR-0334 and ADR-0335 bind the 2,113-task non-replay chain. ADR-0344 and
ADR-0345 own the finite h4 legal responder-raise keystone line. ADR-0346 and
ADR-0347 lead only to responder-row growth. ADR-0348 and ADR-0349 lead only
to selector-window work. ADR-0351 requires the tie-aware legal h4 affine-
envelope. ADR-0354 through ADR-0359 own the factorized face and affine
consumer chain. ADR-0380 freezes the complete ordered populations 10 and 22.
ADR-0383's owner was invoke exactly once and remains consumed by ADR-0384.
ADR-0407 imports neither that owner nor its target. The phrases exclusive
untouched legal h4, selector-window, 2,113-task, exhaustive bounded
development-teacher, response-closed direct mechanism, and caller-owned legal
fallback retain their prior meanings.

The exact historical continuity strings remain explicit. ADR-0328 retains the
exhaustive teacher and solver-free rebinder before the direct closed
finite-block greedy line. ADR-0351 requires the tie-aware legal h4 affine-envelope.
ADR-0352 remains closed before any fresh untouched tie-aware affine result.
ADR-0353 precedes ADR-0354's factorized exact active-set directional-face
diagnostic. ADR-0355's owner was invoke exactly once; ADR-0356 retains that
directional-face diagnostic before tie-aware affine integration. ADR-0357
requires an exclusive legal h4 owner, ADR-0358 was invoke exactly once, and
ADR-0359 requires a fresh value-unopened confirmation. ADR-0382 preregistered
the literal-45 config; ADR-0383 source-sealed it; ADR-0384 closed it.

## Kill criteria

Kill the selector if it reads a different input identity; imports or invokes a
GPU/tool/process path; selects from version, magic, driver, container, SASS, or
register-only evidence; lets a nonzero resource operation select; makes empty
selection unreachable; makes the 255/4096 outcome decide instrument identity;
changes grammar or roles after assessment; overwrites/retries any result; or
promotes selection into resource, capacity, latency, action, quality,
truncation, blueprint, or strength evidence.

## Claims boundary

ADR-0407 freezes an offline question and testable selector contract only. It
contains no selector source, authoritative assessment, selected or qualified
inspector, resource row, resource-gate verdict, exact spill traffic,
calibration, phase timing, projection, complete 25-card value, actual 45-card
value, resolver iteration, solve, action, 15-second result, decision quality,
truncation authority, blueprint value, or poker strength. Systems evidence
remains no quality prior.
