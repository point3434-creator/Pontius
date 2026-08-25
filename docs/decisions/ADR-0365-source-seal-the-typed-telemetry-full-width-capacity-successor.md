# ADR-0365: Source-seal the typed-telemetry full-width capacity successor

- Status: accepted source-only typed-Windows-telemetry successor; v1 remains closed and every v2 capacity target value remains unopened
- Date: 2026-08-25
- Follows: ADR-0364
- Config: `experiments/configs/full-width-river-capacity-preflight-v2.json`
- Config canonical-LF SHA-256: `23cb6ea4521dc26c5fc1c3962574443b7a1d1b841f9e54c03355f9af9a58ff58`
- Typed telemetry canonical-LF SHA-256: `bab5c4533b7ecedb52c26d64f88aecfef3ce58996a629afe10df4089fe29c6c6`
- Runner canonical-LF SHA-256: `19f89f5124b703b01986c5478ddfbdd7a13c37e6dfc1550062963e51ba488821`
- Runner controls canonical-LF SHA-256: `3953d6b6f30798715e34d35bdbea3e9bf99903eb95467bfe73309368fe94958f`
- Telemetry controls canonical-LF SHA-256: `47875f007c706c736ce357d558aa9e1c326315bb0c904cac3ab2f42f2f88b509`
- Parent v1 result literal SHA-256: `ff1c757fb1c388c239ca3c7fdacad15bffa6ee62e00b882827ffb5626f40a906`
- Result: `experiments/results/full-width-river-capacity-preflight-v2.json` (absent at this source boundary)
- Artifact Git attributes: `/experiments/configs/full-width-river-capacity-preflight-v2.json -text`; `/experiments/results/full-width-river-capacity-preflight-v2.json -text`
- Front-Door-Kind: controller-v1
- Front-Door-Research: ADR-0280
- Front-Door-Process: ADR-0365
- Front-Door-Contract: ADR-0307
- Front-Door-Revoked: ADR-0281
- Front-Door-Active-Next: From this clean committed ADR-0365 source boundary, verify the v2 result path is absent and invoke `python -B -m pontius.full_width_river_capacity_preflight_v2` exactly once; retain its first exclusive pass, pre-allocation representation rejection, or typed failure without retry; never invoke or edit v1, and interpret any result only within ADR-0363's unchanged representation/warm-leaf scope
- Front-Door-Blockers: no literal full-width capacity result, scalable replacement contraction, certified truncation mechanism, repeated-actor multiway existence result, off-tree opponent-action result, cross-street belief and certificate handoff, certified full-width river strategy bridge, sealed blueprint trainer/checkpoint/abstraction/slice-audit chain, trained blueprint, v0a/v0b integrated bot, preparation-bank filling result, frozen evaluation opponent pool, complete 15-second decision, production action width, or poker-strength result exists

## Question

Can the ADR-0363 capacity question be reopened under a new authority after
retiring only the proven Windows process-memory ABI defect, while preserving
the exact v1 target, resource caps, controls, claims boundary, and closed
artifact?

## Decision

Accept the additive typed telemetry primitive, outcome-neutral v2 overlay,
new exclusive owner, controls, and source seal below. Keep the v2 result path
absent at this commit. Invoke the v2 owner exactly once from the resulting
clean commit and retain its first terminal without repair or retry. Never edit
or invoke the v1 runner.

ADR-0364's retained v1 terminal remains exactly `GetProcessMemoryInfo failed`;
it contains no control or target payload and answers no capacity question.

The inherited front-door trust chain remains explicit. ADR-0310 made native-
simplex robustness the next systems question. ADR-0311's directive is
Preregister the native-simplex robustness audit. ADR-0312's directive is Seal
the native-simplex audit compiler and corpora. ADR-0313's directive is Seal the
native-simplex audit runner before results. ADR-0314's decision is Retain the
native-simplex audit and reject the frozen gate. ADR-0315's directive is
Source-seal the artifact-only native-simplex gate correction. ADR-0316's
decision is Accept the corrected audit and bound replacement eligibility.
ADR-0317's directive is Separate solver classes and prioritize the certified
sizing adapter. ADR-0318 binds HiGHS 1.12.0, ADR-0319 requires one public
HiGHS-DS call per canonical task, and All 177 ordered observations pass under
ADR-0320, making the separate consumer eligible. ADR-0321 preserves
caller-owned legal fallback, ADR-0322 returns research evidence or rejection
with no action, ADR-0324 remains value-unopened, and ADR-0325 was authorized
exactly once. ADR-0326 and ADR-0327 govern the exhaustive bounded development-teacher
chain. ADR-0328 retains that exhaustive teacher and solver-free
rebinder before the direct closed finite-block greedy line. ADR-0330 remains
permanently closed; ADR-0331's append-and-fsync discipline, ADR-0332's exclusive
`xb` open, and ADR-0333's statement that No replacement sizing value was opened
remain authoritative. ADR-0334 and ADR-0335 bind the 2,113-task non-replay
chain; ADR-0336 records width three; ADR-0337 owns the response-closed direct
mechanism; and ADR-0338 alone records the selected development raise width.
ADR-0339's exact comparison remains a finite absence claim. ADR-0340's 192
prospective tasks remain distinct from ADR-0341's 94 accepted one-call arms and
ADR-0343's 126 confirmation arms; ADR-0342 alone authorized that retained
confirmation invocation. ADR-0344 and ADR-0345 own the finite h4 legal
responder-raise keystone line. ADR-0346 and ADR-0347 lead only to responder-row
growth; ADR-0348 and ADR-0349 lead only to selector-window work. ADR-0350
opened selector-stable affine integration as a question; ADR-0351 replaced it
with the tie-aware legal h4 affine-envelope requirement. ADR-0352's owner is
closed by ADR-0353 before any fresh untouched tie-aware affine result. ADR-0354
source-seals the factorized exact active-set directional calculus; ADR-0355's
owner is closed by ADR-0356. ADR-0357 seals the factorized affine consumer and
requires an exclusive legal h4 owner. ADR-0358 owns its one same-fixture
integration invocation, and ADR-0359 permanently closes it while requiring a
fresh value-unopened confirmation. ADR-0360 fixes that population; ADR-0361
owns and consumes the sole invocation; ADR-0362 alone performs the artifact-
only scientific assessment. ADR-0363 owns and consumes the sole v1 full-width
capacity invocation; ADR-0364 retains its pre-capacity typed failure; ADR-0365
alone source-seals the additive v2 successor. No earlier owner is revived.

ADR-0355 and ADR-0358 each said invoke exactly once; both owners stay closed.
ADR-0360 required an exclusive untouched legal h4 owner; ADR-0361 consumed it.
ADR-0363 required one literal capacity owner invocation; it is consumed and
cannot serve as v2 authority.

## Additive ABI repair

`windows_process_memory` declares every Windows function signature explicitly:

- `GetCurrentProcess() -> HANDLE`;
- `GlobalMemoryStatusEx(MEMORYSTATUSEX*) -> BOOL`;
- `GetProcessMemoryInfo(HANDLE, PROCESS_MEMORY_COUNTERS_EX*, DWORD) -> BOOL`;
  and
- `K32GetProcessMemoryInfo(HANDLE, PROCESS_MEMORY_COUNTERS_EX*, DWORD) -> BOOL`.

The process structure is frozen at 80 bytes on Win64, with working set at byte
offset 16 and private usage at byte offset 72. Both native entry points must
return nonnegative counters with peak working set no smaller than current
working set. A no-profile, hidden PowerShell child independently queries the
same Python PID and supplies a third managed process view.

The maximum 536,870,912-byte cross-source delta is a telemetry sampling-skew
allowance only. It cannot change host capacity, device capacity, allocation,
admission, timing, action, or quality. Exact equality would be false precision
because process counters can move between sequential readers. The control
reports every raw value and absolute delta; it fails closed on process-identity,
structure, sign, ordering, or allowance violation.

Unsealed controls establish that both native entry points and PowerShell bind
the same current process, the 80-byte layout holds, and the typed telemetry
seam reaches the pinned NumPy/SciPy/CuPy/CUDA/RTX 5080 runtime. These controls
open process and device telemetry only. They do not call the reduced GPU
contraction control, street inventory, allocation ledger, target admission,
topology compiler, or any target contraction.

## Unchanged target contract

The v2 config is an overlay rather than a copied target specification. It
literal-hashes the exact 798-byte v1 result and canonical-LF hashes ADR-0364,
the v1 config, v1 runner, exact allocation model, telemetry source, v2 owner,
and both control files. It then loads the v1 config through the sealed v1
parser. Consequently all of ADR-0363's target semantics remain identical:

- controlled seat 3 with `Ks Td` on `2c 7d 9h Js Qc`;
- the exact 1,225/1,081/1,035/990 street widths;
- one singleton hero plus five complete 990-combo river opponent axes;
- the current 3/3 FactorTT/open-mode/resident lineage;
- the exact persistent-array lower bound before target allocation;
- fixed 48 GB host and 12 GB device numeric caps plus live reserves;
- a reduced 12-hand-per-opponent complete-path GPU control;
- conditional scalar, resident prime, and one identical warm leaf contraction;
- a 14,000 ms warm ceiling plus 1,000 ms emission reserve; and
- zero actions, strategy labels, quality rows, and quality prior.

The v2 owner imports only v1's unchanged `_small_control` and `_run_target`
scientific functions. It does not call or patch v1's broken host telemetry,
runtime owner, exclusive writer, main function, or result path. It owns a new
Git check, runtime snapshot, protocol envelope, typed-failure serializer, and
`O_EXCL`/`fsync` writer.

## Frozen lifecycle

The overlay contains no expected capacity admission, terminal, topology byte
count, compatible-record count, or warm time. Its target-semantic string says
only that ADR-0363 is unchanged and the Windows process-memory ABI is replaced.
The v2 result path is protected by `-text` and absent at this source boundary.

From the clean commit containing this ADR:

1. verify the path remains absent and Git is clean;
2. invoke `python -B -m pontius.full_width_river_capacity_preflight_v2` once;
3. retain the first exclusive pass, pre-allocation representation rejection,
   or typed failure;
4. do not retry, increase an allowance, change target semantics, use another
   split, reduce an axis, or substitute a backend after the terminal; and
5. permanently close v2 after that invocation.

## Kill criteria

The successor rejects if any parent/source hash drifts, the v1 parent ceases to
be the exact target-absent typed failure, the ABI layout differs, either native
reader or PowerShell fails, process identity/sign/order/delta controls fail,
the pinned scientific runtime changes, Git is dirty, the hardware bounds fail,
the reduced control fails, target gates fail, the campaign exceeds its inherited
wall, the result exceeds 1 MiB, or any action/quality emission appears.

## Claims boundary

ADR-0365 supplies only source and telemetry-mechanism evidence. It does not
supply a v2 capacity terminal, representation result, warm-contraction latency,
CFR iteration, solve, action, decision-quality result, truncation certificate,
or poker-strength claim. The 512 MiB telemetry allowance is not a capacity
reserve or uncertainty band. The v1 result remains a rejected plumbing
terminal and forecasts about capacity remain unscored until v2's retained
target artifact exists.
