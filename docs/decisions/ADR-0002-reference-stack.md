# ADR-0002: Reference implementation stack

**Status:** Accepted, 2026-08-18.

## Decision

Use dependency-light Python for the exact executable specification and
experiment orchestration. Introduce C++20 for the poker engine and CPU traversal
only after representative reduced-game workloads exist. Introduce CUDA only
after profiling the C++ implementation.

## Evidence

The first checkpoint values transparency, exhaustive enumeration, and rapid
testing. Optimizing before workload capture risks selecting an unsuitable data
layout or execution backend.

## Revisit condition

If Python prevents exact experiments from reaching the smallest planned games,
move only the measured bottleneck behind the same interface.

