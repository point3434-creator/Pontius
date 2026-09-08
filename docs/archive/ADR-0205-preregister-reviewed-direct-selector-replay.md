# ADR-0205: Preregister the reviewed direct selector replay

- Status: accepted direct-runner preregistration before replay
- Date: 2026-08-21
- Replaces orchestration only after: ADR-0200, ADR-0202, and ADR-0204
- Scientific protocol: ADR-0199, byte-identical
- Config: `experiments/configs/h32-retained-affine-selector-cascade-direct-v1.json`
- Config SHA-256: `9f3388f4cda960c50501edf58c045848b2bfc6fe3ba911b774e42a331aae8ad4`
- Runner: `src/pontius/h32_retained_affine_selector_cascade_direct_replay.py`
- Runner SHA-256: `6799bf677d1a7fae874bd264505f8b6d42d0a7ebba0390b2949730e8c1703fc1`
- Control test: `tests/test_h32_retained_affine_selector_cascade_direct_replay.py`
- Control-test SHA-256: `f523108d3744cb2d9ec98e103d67cbd661562a58f655e75bef8006e2da2201b4`

## Why a direct runner

The three rejected invocations exposed two result-assembly boundaries that the
scientific unit tests did not exercise:

- the imported memory helper's real four-field schema; and
- the reporting helper's zero-argument API.

The wrapper line is closed by ADR-0204. This successor does not monkeypatch a
module global, add a memory alias, or call a failed wrapper. It directly invokes
ADR-0199's frozen target reconstruction, feature extraction, label join,
scoring, and negative-control helpers, then performs a separately reviewed
orchestration and result assembly.

## Pinned boundary review

Pin the raw memory helper at
`12c7cba9deb1d6307c058120332c56f5a5446a9ca4045d0f34fbb01bb35a7fb4`.
Require every snapshot to contain exactly:

```text
gpu_free_bytes
gpu_total_bytes
gpu_pool_used_bytes
gpu_pool_total_bytes
```

Read pool maximum directly from `gpu_pool_total_bytes` and physical-free
minimum directly from `gpu_free_bytes`. Reject any missing, extra, or aliased
schema.

Pin `reporting.py` at
`9e341347310e256a658bc7e7c13994895faf794f17d48eece82cddbf8828ecb2`.
Call `environment_metadata()` with no arguments, then merge runtime metadata
and the strict Git object by dictionary expansion, matching accepted h32 audit
practice.

Before writing the output path, serialize the complete result in memory with
`json.dumps(indent=2, sort_keys=True, allow_nan=False)`. Unit controls exercise
finite serialization and require NaN rejection.

## Scientific identity

Pin ADR-0199's config, runner, test, and decision at their accepted hashes. The
direct runner reuses without modification:

- all six retained contexts and one exact warm step per context;
- six public-node blocks by three frozen direction families;
- all 108 candidate rows and 648 responding-seat affine rows;
- the complete eight-feature list;
- the exact Tier-A identity and impure-direction negative control;
- exactly five charged opponent-BR rows and the six-charge mutation control;
- the primary six-set, raw 18-set, and soft-excluded 12-set;
- the semantic label barrier and sealed ADR-0186 labels;
- label-independent capacity arithmetic and both K variants;
- recall/value curves, random floors, clairvoyant ceilings, cascade scoring,
  value per charged second, and radius-overshoot localization;
- every numerical, time, memory, provenance, finite, and blueprint-emission
  gate; and
- both report-only predictions and all evidence limitations.

No failed process state, coefficient, timing, K, score, or Python object may be
reused. The direct invocation reconstructs everything from scratch.

## Controls

Five direct-runner controls now precede GPU execution:

1. parse and hash-check the complete ADR-0199 scientific contract;
2. refuse any memory mapping other than the pinned raw four-field schema;
3. assert the reporting helper has zero parameters and test the exact merge;
4. serialize a finite result and reject NaN under the production options; and
5. inspect the runner source to forbid memory-global assignment and the failed
   `gpu_physical_free_bytes` alias.

The full repository regression suite must pass from the clean preregistration
state.

## Evidence boundary and decision

Run once from a clean commit. If the direct runner or any inherited scientific
gate fails, stop this retained replay. Do not add another wrapper or orchestral
correction.

A passing artifact is retained-context development evidence only. Primary-set
K saturation is library limitation, not selector success. The raw 18-set is
weak unless its advantage survives the soft-excluded control. No strategy-
quality, fresh-transfer, deployment, composition, or population claim is
authorized.
