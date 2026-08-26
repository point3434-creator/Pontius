# ADR-0395: Correct the work-preflight resource instrument before result

- Status: accepted prospective pre-result instrument correction; the unchanged five caller-supplied NVRTC options, retained ELF cubin identity, independent raw `cuobjdump` reparse, driver/cubin register and backing maxima, and explicit device-reserve arithmetic replace ADR-0394's unavailable compiler-spill wording before source seal, real compilation, calibration, projection, or result, while every ADR-0394 arithmetic, population, phase, ratio, wall, lifecycle, and claims boundary remains binding and every complete 25-card numerical value, actual 45-card value, resolver iteration, solve, action, 15-second result, quality result, truncation choice, blueprint result, and poker-strength claim remains unopened
- Date: 2026-08-25
- Follows: ADR-0394
- Base config: `experiments/configs/legal-river-quotient-cuda-compensated-work-preflight-v1.json`
- Base config canonical-LF SHA-256: `88a16d62cf978ec61b7481c79b841eda6a2844a41f374c122a21be5310550d3c`
- Correction config: `experiments/configs/legal-river-quotient-cuda-compensated-work-preflight-v2.json`
- Correction config canonical-LF SHA-256: `a522858696c8266485f7aac4b9c2dbb5f0d0c35e59d3e1515f4674d802ac890c`
- ADR-0394 canonical-LF SHA-256: `362f21a4f246f8598adc5445f3323088c1e38b389f4f07b3ae600c831c57de44`
- Preregistration commit: `fc1892e15522eed4b9935de0404131646820c451`
- Successor draft: present only as an uncommitted, uninvoked source-seal draft
- Prospective result: `artifacts/work_preflight/legal_river_quotient_cuda_compensated_work_preflight_v1.jsonl` absent
- Reserved actual result: `artifacts/legal_river_quotient_cuda_consumer_v1.jsonl` absent
- Actual execution/allocation/scientific counters: `0/0/0`
- Front-Door-Kind: controller-v1
- Front-Door-Research: ADR-0280
- Front-Door-Process: ADR-0395
- Front-Door-Contract: ADR-0307
- Front-Door-Revoked: ADR-0281
- Front-Door-Active-Next: Implement and source-seal only the composite ADR-0394/ADR-0395 work preflight without invoking its real owner: bind and validate both configs; preserve the parent's arithmetic and the 10/22-only numerical lock; require an ELF retained payload before module load; record both driver and exact-cubin resource instruments plus raw tool identity; independently reparse them in the CuPy-free reader; apply the frozen register, backing, resident-thread, and reserve conjuncts; retain every raw shared-boundary phase row and synthetic failure control; and keep both result paths absent until a later clean committed invocation checkpoint
- Front-Door-Blockers: no source-sealed composite work preflight, no retained 10/22-card calibration, and no conservative complete-25 capacity verdict; ADR-0393 remains rejected on wall and ADR-0390's one-ULP absolute seam remains unrepaired; no complete 25-card numerical result, actual owner, or full-width actual-context quotient value, no general odd-chip or side-pot leaf automaton, repeated-actor multiway existence result, off-tree opponent-action result, cross-street belief and certificate handoff, certified full-width river strategy bridge, sealed blueprint trainer/checkpoint/abstraction/slice-audit chain, trained blueprint, v0a/v0b integrated bot, preparation-bank filling result, frozen evaluation opponent pool, complete 15-second decision, production action width, or poker-strength result exists

## Question

Does ADR-0394 fully freeze the compiler-resource instrument it names, and if
not, can the omission be corrected before any real compilation or result?

## Decision

No, then yes. ADR-0394 requires compiler register, local, and spill attributes
for every new direct kernel, but the frozen NVRTC call and
`cuobjdump --dump-resource-usage` do not expose exact spill-load or spill-store
counts. They expose register allocation and local/stack backing. Treating those
backing bytes as exact spill traffic would repeat the project's recurring
semantic-quantity defect. ADR-0394 also freezes no literal backing ceiling, so
selecting one inside a source-seal result would be a post-preregistration
decision.

Adopt the additive v2 correction as an overlay on the complete canonical v1
config. No v1 arithmetic, numerical gate, population, fixture lock, phase,
ratio, timing wall, retry rule, or claim is removed or relaxed. Replace only
the incomplete resource-instrument wording and freeze the missing bounds.
Future source, owner, and independent reader must load, hash, validate, and
report both configs.

The correction is prospective with respect to evidence. An uncommitted draft
source existed when the omission was found, but it had not been imported by a
real owner, compiled for the device, or used to create a calibration value,
projection, or result. Both result paths remain absent. The source-seal draft
and synthetic controls are not outcomes and may be revised under this
correction before they acquire authority.

## Executed-binary and compiler-option contract

The caller continues to supply exactly the five ADR-0394 options:
`--std=c++14`, `--ftz=false`, `--prec-div=true`, `--prec-sqrt=true`, and
`--fmad=false`. No verbose-ptxas option is added. CuPy owns internal target-
architecture, default-execution-space, and version-dependent PCH handling;
those internal additions are disclosed rather than miscounted as caller
options.

The retained compiler payload must begin with ELF magic before `Module.load`.
This fails closed if `CUPY_COMPILE_WITH_PTX=1` or another environment seam
turns the retained bytes into PTX and leaves driver JIT between the inspected
payload and executed code. Record the retained ELF SHA-256, CuPy version,
`cuobjdump` version output, and raw `--dump-resource-usage` stdout. The
standard-library reader independently parses the raw stdout and may not trust
the stored parsed rows or pass bits.

## Resource and reserve contract

For each of the three new direct kernels, record CUDA driver function
attributes and exact-cubin `REG`, `STACK`, and `LOCAL` fields. The register
conjunct is
`max(driver registers, cuobjdump REG) <= 255` per thread. The backing conjunct
is
`max(driver local-size bytes, cuobjdump STACK + LOCAL) <= 4,096` bytes per
thread. Exact spill-load/store traffic is structurally unavailable and must
remain `null`; stack or local bytes are not renamed as spill counts.

The 4,096-byte limit is priced against the inherited two-billion-byte device
reserve. Freeze a conservative maximum-resident-thread bound of 131,072. At
the ceiling, backing is at most `4,096 * 131,072 = 536,870,912` bytes, leaving
`1,463,129,088` bytes inside that reserve. The real runtime must report a
multiprocessor-count times maximum-threads-per-multiprocessor product no larger
than 131,072. Pool peak and every inherited memory gate remain separate
conjuncts; this arithmetic does not certify that backing is simultaneously
resident or predict allocation behavior.

Any non-ELF payload, missing or malformed tool evidence, independent-reader
disagreement, register/backing limit breach, resident-thread bound breach,
device-reserve breach, or invented exact-spill claim is a typed compiler or
primitive rejection before calibration.

The inherited trust chain remains unchanged. ADR-0317 separates solver
classes and prioritizes the certified sizing adapter. All 177 ordered
observations pass under ADR-0320. ADR-0328 retains the exhaustive bounded
development-teacher and solver-free rebinder. ADR-0334 and ADR-0335 bind the
2,113-task non-replay chain. ADR-0338 alone records the selected development
raise width. ADR-0344/0345 own the finite h4 responder-raise keystone;
ADR-0346/0347 lead only to responder-row growth; ADR-0348/0349 lead only to
selector-window work. ADR-0351 requires the tie-aware legal h4 affine-envelope,
and ADR-0354 through ADR-0359 own the factorized face and affine consumer
chain. ADR-0360 through ADR-0362 own untouched confirmation. ADR-0367 through
ADR-0384 own and close the quotient algebra, capacity, bounded CUDA, staged,
liveness, validation, and literal-target ladder. ADR-0385/0386 own the legal
bridge; ADR-0387/0388 own consumer capacity; ADR-0389/0390 own the rejected
first CUDA consumer; ADR-0391/0392 own the paired arithmetic; ADR-0393 retains
its wall rejection; ADR-0394 freezes the work-preflight question; and ADR-0395
corrects only its compiler-resource instrument before any result. No revoked
experiment or earlier consumed owner is revived.

## Scope and claims

This is a resource-instrument correction, not a source seal or systems result.
It establishes no actual register count, local/stack count, timing,
calibration value, projection, capacity verdict, or complete 25-card numerical
evidence. The reserved actual result remains absent.

No number here is resolver latency, per-iteration latency, per-solve latency,
action-clock usage, chip strength, or NashConv. The 4,096-byte threshold is a
memory-reserve guard, not a numerical tolerance or quality prior. ADR-0307's
cumulative 15-second action contract and the decision-quality-per-millisecond
thesis remain unchanged.
