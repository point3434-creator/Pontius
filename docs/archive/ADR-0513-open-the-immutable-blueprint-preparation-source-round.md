# ADR-0513: Open the immutable blueprint preparation source round

- Status: accepted source-opening decision upon its separately authorized commit
- Date: 2026-09-07
- Follows: ADR-0512
- Base-Commit: 363c9fb669e19a30375537ee5e92ea338a840a2d
- Invocation-Authority: finite named engineering controls after adoption; no operating owner
- Front-Door-Kind: controller-v1
- Front-Door-Research: ADR-0280
- Front-Door-Process: ADR-0513
- Front-Door-Contract: ADR-0307
- Front-Door-Revoked: ADR-0281, ADR-0468, ADR-0472, ADR-0475
- Front-Door-Active-Next: Implement accounted immutable blueprint preparation
- Front-Door-Blockers: prepared source acceptance pending; strength and worst-case latency unknown

## Decision

Upon this decision's separately authorized commit, open the immutable blueprint
preparation source round defined by the brief, design and source contract under
`docs/architecture/v0a-blueprint-preparation-r001/`, with the implementation plan
at `docs/superpowers/plans/2026-09-07-blueprint-preparation.md`.

The controller requested commit/push of ADR-0512 and continuation to the next
step. ADR-0512 is committed as `363c9fb669e19a30375537ee5e92ea338a840a2d`.
This proposal completes its named design checkpoint; it requires its own exact
decision authorization before source implementation. It claims no new speedup.

Prepare an owned exact-key blueprint and unchanged canonical digest once per
runtime hand, inside the existing hand-start accounting interval. Reuse it for
real blueprint actions and baseline fallback. A direct Python provider exposes
equivalent values for future engineering use. Preserve the legacy host lookup
as an independent check of the child, and keep all artifact, provider, legal-action
and action-clock semantics unchanged.

## Prospective source scope

Prospectively supersede CLAUDE.md rule 1 only for the fifteen exact base file
versions and permitted changes in source-contract.md. This is a finite exception
for this source round, not standing permission for later versions. Recheck every
base pin before editing. Add only the two preparation package files, v3 evaluator,
fixed historical launcher and five suites named in that contract.

Whole-package source admission makes the old v1/v2 evaluators incompatible with
the new runtime population. Preserve those evaluators and their tests unchanged;
run the 55 source-dependent old tests at the exact ADR-0512 commit. Register their
historical target truthfully and retain the existing baseline locks and capability
grants. Current v3 tests must cover current admission, child execution and the
current boundary checker; historical results never replace current acceptance.
Approve only the source contract's exact three-row historical manifest extension
and its pinned new seed digest. Preserve all 167 old rows and retained evidence.

The new evaluator retains v2's bounded reader and the old artifact/schema/ID
meanings. Its exact source commit and manifest identify this successor. Preserve
all source/file/handle/ancestor identity rechecks and raw captured execution. No
cache of filesystem source checks, new strategy label or relaxed acceptance gate.

## Qualification and authority

The brief specifies scope estimates, dependencies and one initial candidate plus
at most two bounded corrections, with the workflow's earlier residual/design stop.
The source contract specifies exact finite correctness and cost observations.
No unmeasured speed or memory threshold becomes an acceptance gate. Include owned
copy, index and cached bytes in setup/memory costs; retain the host reference cost
in end-to-end results. No new preparation credit or time outside accounting.

This documentation-only opening candidate contains exactly this ADR, the three
architecture documents, the implementation plan and generated STATUS.md. Freeze
all six raw blobs and the sorted SHA-256/path manifest, then obtain two fresh
independent Tier C CLEAN reviews. After review closure, run unchanged status
generation --check and all twelve status tests in fresh exact-candidate D-local
snapshots on actual 3.11.15 first, then 3.14.6. Recheck exception base pins, LF/no
BOM and the exact six-file scope. No poker, inventory or performance payload runs
in this design task.

After opening adoption, implementation must pass the named current and historical
gates on both interpreters after independent source review closure. Source sealing
and adoption of measured implementation are a later separately authorized decision.
No training, tuned or learned blueprint, live demonstration, native migration,
research owner, consumed-run retry or operating budget follows from this opening.
