# ADR-0160: The h32 atomic response preflight passes and is cache-construction bound

- Status: accepted result
- Date: 2026-08-21
- Implements: ADR-0159
- Result: `experiments/results/h32-atomic-response-preflight-v1.json`

## Result

All frozen gates passed over four h32 targets and 24 label-independent atoms. The complete resident teacher evaluated 144 seats. Incremental evaluated-prefix utilities, best responses, and deviation gains agreed with that teacher to at most `4.20e-15`; every stop reason, stop seat, and evaluated-seat prefix agreed exactly.

The incremental certificate wall time was 252.21 ms minimum, 468.31 ms median, and 1,006.45 ms maximum. All 24 certificate-only rows fit 15,000 ms with each preregistered reserve through 1,000 ms. This is not an end-to-end street result: search, atom extraction, scheduling, and selection were excluded by design.

The response overlay retained only 413,232 identity-deduplicated numeric bytes per target. Mean evaluated-prefix terminal recontraction was 4.61% of a complete prefix. The acting seat itself required zero terminal recontractions whenever it was reached, as required by target-omitted path semantics. No best-response action changed on this deliberately narrow atom sample.

The expensive state is elsewhere. Resident-static belief and automaton caches retained approximately 2.96 GB for blocker-heavy and 4.33 GB for balanced families (decimal bytes are stored exactly in the artifact). CuPy pool reservation peaked at 7,934,734,336 bytes while reported free device memory never fell below 7,219,445,760 bytes. Source terminal middle rank was 80 for blocker-heavy and 104 for balanced. Cold static-plus-response construction cost 9.46–12.99 seconds per target.

## Diagnostic envelope observations

Twenty atoms completed the fixed envelope and four stopped on the blueprint cap; none stopped on the objective lower bound. All four cap stops came from the seat-1-selected atom, although the binding response seat depended on target shift. These are frozen diagnostic outcomes, not admissions to a strategy pool and not evidence of value capture. The absence of response-action flips also does not establish that selector kinks are unimportant outside this small deterministic sample.

## Decision

The terminal-numerator overlay is exact and cheap enough to retain. Do not spend the next optimization step compressing its 413 KB payload.

Cold per-target construction is incompatible with treating the complete 15-second street as available decision time: it consumes 63–87% of the budget before search or certification. ADR-0128 through ADR-0132 already built and validated scale-canonical affine sharing across bet amounts; this result does not reopen or duplicate that work. The next implementation target for this response path is the distinct remaining duplication boundary: persistent reuse of the same one-size topology/automaton cache across target-belief shifts, followed by a frozen residency test across the two shifts of one family. Do not run a strategy-quality search expansion from these atom labels.

The memory measurement permits that systems experiment but does not pre-authorize simultaneous duplication of two full balanced-family static caches. The shared-topology design must account unique device arrays and measure actual pool headroom before any widened resident warm step.

## Scope

This result establishes exactness, reuse structure, memory location, and certificate-only timing on the frozen h32 panel. It makes no deployment, selection, composition, exploitability-improvement, or strategy-quality claim.
