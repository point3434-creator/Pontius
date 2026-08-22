# ADR-0248: Auto-bootstrap the pinned Windows CUDA DLL bundle

- Status: accepted process correction
- Date: 2026-08-22
- Follows: ADR-0247
- Bootstrap SHA-256: `66d6bcfaadbaf47f110854380c227163cf052414f494a510dd53a4ea2ef91bef`
- Control SHA-256: `342f49b08b2fbe6b7942e2ab77f7d4dc3e50f72d601eaa96cdf5571612dc9fc6`

## Problem

The pinned Windows CUDA bundle was already installed under the repository
`.venv`, but every new shell still had to set
`PONTIUS_CUDA_DLL_DIRECTORY`, `CUDA_PATH`, and `PATH` manually. Three accepted
result lines—ADR-0212, ADR-0235, and ADR-0245—record a first invocation that
stopped before GPU work solely because this shell initialization was omitted.
The failures did not corrupt evidence, but repeated operator memory is not a
sound runtime contract.

Several legacy runners also check the environment variable before calling the
shared CuPy loader. Fixing only the newest runner or only the loader would not
retire the defect family.

## Decision

On Windows, importing the `pontius` package now performs a filesystem-only
bootstrap before any runner module executes. If the environment variable is
absent, it searches only deterministic Python-environment locations for
`nvidia/cu13/bin/x86_64`. A candidate is accepted only when all five DLLs used
by the established loader are present. The bootstrap then:

1. sets `PONTIUS_CUDA_DLL_DIRECTORY` for the current process;
2. records whether resolution came from the active interpreter, its site-
   packages, or the repository-local `.venv`;
3. sets `CUDA_PATH` without overwriting an operator-supplied value; and
4. prepends the DLL directory to the current process `PATH` exactly once.

An explicit `PONTIUS_CUDA_DLL_DIRECTORY` always wins and is never silently
replaced. The existing GPU loader validates the directory, and frozen runtime
gates still validate the effective CuPy, CUDA-runtime, driver, and compute-
capability versions. Automatic discovery never scans or chooses an arbitrary
system CUDA installation. If no complete repository-controlled bundle exists,
the variable remains absent and existing GPU gates still reject the run.

The bootstrap imports no CUDA or CuPy code. CPU-only Pontius use remains
CUDA-optional, and non-Windows environments are left byte-for-byte unchanged.

## Compatibility and verification

The accepted `cupy_sparse_incidence.py` loader remains byte-identical at
SHA-256 `ef1671d1e4091b00a9051f5f9ba753546f783bebca41b17953fa36efa40ff098`,
preserving the source hashes embedded in historical experiment
configurations. Package bootstrap occurs early enough to satisfy both the
legacy pre-import environment checks and the shared loader.

Controls cover non-Windows no-op behavior, explicit-override precedence,
rejection of incomplete automatic candidates, complete-bundle discovery,
source recording, `CUDA_PATH`, and idempotent process `PATH` setup. A clean-
shell smoke test with all three CUDA variables removed automatically resolved
the active `.venv` bundle and loaded CuPy `14.2.0`, CUDA runtime `13020`, driver
`13030`, and compute capability `120`.

This is startup plumbing only. It runs no strategy, optimizer, certificate, or
quality experiment and changes no numerical methodology.

## Decision consequence

Future repository commands need only the pinned `.venv` interpreter and
`PYTHONPATH=src`; no CUDA environment preamble is required. `RUNBOOK.md`
retains the explicit variable solely as a controlled override for nonstandard
reproduction environments.
