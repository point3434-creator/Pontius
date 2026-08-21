# ADR-0196: Resident-step profile v1 rejects before replay on the parent pass key

- Status: rejected execution before any replay step
- Date: 2026-08-21
- Implements: ADR-0195
- Clean execution commit: `a28b3f2`
- Result artifact: none written

## Failure

The frozen ADR-0195 invocation stopped while validating its retained source
artifact, before target reconstruction, context compilation, or any profiled
GPU step:

```text
KeyError: 'gates'
```

The runner read the source-blueprint pass flag as
`source_parent["gates"]["passed"]`. The immutable
`h32-fresh-panel-source-blueprints-v1.json` schema instead stores the boolean at
top-level `source_parent["passed"]` and names its detailed map
`source_parent["gate_results"]`.

The seat-5 parent uses the expected top-level `passed` field. No source digest,
policy, target, timing, stage bucket, memory row, Amdahl estimate, or
classification was printed or serialized. The configured result path does not
exist.

## Decision

Reject the ADR-0195 v1 execution and preserve its runner at SHA-256
`c77238e017211df9cbd940c386540f3a10a740437afd87dd4f9bdb5696de8033`.
Do not treat the startup failure as performance evidence.

An additive successor may change only the in-memory source pass-field lookup
from the nonexistent nested key to the source artifact's top-level `passed`
boolean. It must pin the v1 config, runner, control test, this rejection, and
ADR-0195; preserve both targets, three restarts, every timing bucket,
counterfactual, numerical tolerance, resource ceiling, and outcome-neutral
gate; and run again only from a new clean preregistration commit.

## Evidence boundary

Because the exception occurred before `_run_target`, all six replay timings and
all classifications remain unobserved. The successor is therefore a pure
schema-compatibility correction, not a rescue based on an unfavorable result.
