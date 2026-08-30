# ADR-0479: Accept the evidence layer and sealed-boundary manifests

- Status: accepted process decision; the mainline now carries the first structured subpackage `pontius/evidence/` (typed errors, frozen validated models, strict manifest parsing) together with five governed data files that make the sealed boundary machine-checkable — `sealed-current-files.toml`, `sealed-current-absences.toml`, `historical-blobs.toml`, `retained-v7.toml`, and `dependency-baseline.toml` — plus their generators, the stabilization boundary checker, and their test suites; the sealed retained v7 artifacts (journal, attempt, consumed-launch marker) are byte-unchanged and now hash-bound in data rather than prose, and the boundary check passes from the integrated mainline
- Date: 2026-08-29
- Follows: ADR-0478
- Package: `src/pontius/evidence/` — `__init__.py` (22 lines), `errors.py` (64), `model.py` (416), `manifest.py` (343); standard-library-only imports plus `pontius.durable_evidence_journal`
- Governed data: `docs/architecture/dependency-baseline.toml` (13,602 lines), `historical-blobs.toml` (1,575), `sealed-current-absences.toml` (111), `sealed-current-files.toml` (51), `retained-v7.toml` (50)
- Tools: `tools/generate_evidence_manifests.py` (3,218 lines), `tools/generate_dependency_baseline.py` (2,229), `tools/check_stabilization_boundaries.py` (423)
- Tests: `test_evidence_manifest_generation.py` (2,185 lines), `test_stabilization_boundaries.py` (1,443), `test_evidence_manifests.py` (421), `test_evidence_errors_and_model.py` (146), `test_test_orchestration_import_boundary.py` (83), plus shared support modules
- Development lineage: the evidence commit chain on the stabilization line (`ba1e665` through `89303d1` and successors), integrated to the mainline by merge `156f0b3`
- Post-merge validation: `tools/check_stabilization_boundaries.py` exit 0 from the integrated primary checkout with the governance files present
- Sealed retained artifacts: the three ADR-0476 lifecycle files under `artifacts/work_preflight/` remain byte-exact and are the sealed entries of `sealed-current-files.toml`

## Question

The sealed boundary previously lived in prose across hundreds of ADRs, and a
CodeRabbit preflight had exposed authorization-handling defects in the v7
maintenance readers. What machine-checkable boundary now exists?

## Decision

Accept the typed evidence layer and its manifests onto the mainline. The
`pontius.evidence` package supplies stable typed failures, frozen validated
values, and strict TOML parsing with exact-type discipline; it is the
precedent for structured subpackages over new flat-root modules. The five
governed data files bind the sealed boundary in data: which current paths are
sealed and at which hashes, which paths must remain absent, which historical
blobs are retained, the exact retained-v7 identity, and the module dependency
baseline. The boundary checker authenticates that state from the working
tree, and it passes from the integrated mainline with the governance charter
and protocol files present.

The two v7 maintenance modules (`..._v7_result.py`, `..._v7_runner.py`)
received reviewed corrections that close the authorization re-read defects:
authorization configuration is parsed once from a single read instead of
re-read across checks, and deferred-header validation derives authorization
identity coherently from that single source. These are maintenance-reader
corrections shipped through the reviewed stabilization candidate; the sealed
retained artifacts they read are byte-unchanged, and no consumed owner was
invoked.

### Claims boundary

The manifests bind current state; they are not retroactive re-certification of
historical results. The evidence layer runs no experiment, opens no value, and
clears no ADR-0476 blocker. Manifest regeneration after any authorized change
to a governed path is part of that change's own review, never a silent edit.
