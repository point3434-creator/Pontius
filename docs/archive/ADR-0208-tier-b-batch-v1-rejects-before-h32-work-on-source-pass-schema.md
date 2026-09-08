# ADR-0208: Tier-B batch v1 rejects before h32 work on the source pass schema

- Status: rejected execution before any h32 coefficient or timing measurement
- Date: 2026-08-21
- Implements: ADR-0207
- Clean preregistration commit: `4ff0faa`
- Result artifact: none

## Failure

The single ADR-0207 invocation parsed and hash-validated its frozen config,
validated the runtime, and read the retained source-blueprint artifact. It then
failed before entering the target loop at:

```text
KeyError: 'gates'
```

The runner asked for `source_parent["gates"]["passed"]`. The pinned source
artifact exposes a top-level `passed` field and a separate `gate_results`
object; it has no `gates` object.

No target was reconstructed. No warm step, candidate construction, scalar
opponent call, batched opponent call, coefficient, timing sample, memory
headroom decision, label load, or result serialization occurred. The output
path does not exist.

## Decision

Reject v1 as evidence. Preserve ADR-0207's batch primitive, workload, timing
schedule, numerical ceilings, memory gates, charge boundary, and decision
branches unchanged.

Authorize one reviewed successor that changes only both source-pass reads from
`source_parent["gates"]["passed"]` to `source_parent["passed"]`, pins the real
top-level schema with a mutation control, writes to a versioned v2 result path,
and starts from a clean commit. It may not reuse any failed process state.
