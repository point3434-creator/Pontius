# ADR-0204: The final selector wrapper rejects on an environment API mismatch

- Status: rejected final corrected replay
- Date: 2026-08-21
- Implements: ADR-0203
- Clean preregistration commit: `f071b81`
- Intended result: `experiments/results/h32-retained-affine-selector-cascade-replay-v3.json`
- Result artifact: absent

## Failure

The ADR-0203 invocation passed its literal four-field memory guard and printed
all six target feature-extraction progress lines. It then raised during result
assembly:

```text
TypeError: environment_metadata() got an unexpected keyword argument 'extra'
```

No result file, gate table, selector metric, coefficient, K, or aggregate was
printed or persisted.

## Cause

The unchanged ADR-0199 runner calls:

```text
environment_metadata(seed, extra=...)
```

The pinned repository helper accepts no arguments and returns the Python,
platform, and Git fields. Every current h32 audit extends it by dictionary
merge. This mismatch is independent of the memory-schema corrections and lies
in v1's direct result assembler.

## Evidence boundary

Reject v3. Although execution reached result construction after in-memory
scoring, no serialized artifact or validity gates exist. Do not infer an
outcome from progress or from the failing line's position.

ADR-0203's stop rule now applies: do not add a fourth wrapper or another
monkeypatch. Close the wrapper line and review the direct runner's complete
orchestration and result assembly before any successor is proposed.

## Decision

The only admissible continuation is a separately preregistered direct
orchestration runner that:

- calls the frozen ADR-0199 feature/scoring helpers without monkeypatching;
- consumes the helper's real `gpu_free_bytes` field directly;
- calls `environment_metadata()` with its actual zero-argument signature and
  merges runtime/Git metadata explicitly;
- pins both helper implementations;
- unit-tests raw memory extrema, environment assembly, and JSON serialization;
  and
- reruns all targets, features, and the semantic label join from scratch.

If that direct review exposes any further ambiguous scientific or result-schema
dependency, stop this replay rather than guessing.
