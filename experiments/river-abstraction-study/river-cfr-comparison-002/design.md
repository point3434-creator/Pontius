# River CFR comparison 002: fixed-parameter confirmation

Authorized by the user: "Ok let's run the next".

Use retained case 000, the lowest-index position not used in comparison 001.
Choose it before inspecting any CFR result for that position. It is a previously
studied game, not an untouched holdout. Preserve its actual board, pot, stack,
range distribution and baseline betting tree, including any collapsed bet sizes.

Reuse the previous solver, tests, six arms, iteration count, update order,
averaging definitions, checkpoint schedule, single-thread float64 environment,
three rotated-order repeats, independent final rational certificates and limits.
Only the experiment identity, authorization and input/reference selection change.
Run 18 serial workers, then six independent certificate workers. Each has a
180-second timeout and a sampled 3,072 MiB stop. No retries or parameter tuning.

Report every arm. Compare paper DCFR+ to matched-averaging CFR+ and matched
PDCFR+ to paper DCFR+. Keep the released-code denominator variant separate.
Success means complete valid measurements; it does not require DCFR+ to win.
The final best-response gap, not the solver's own convergence flag, measures
quality. Retain non-improvements. A complete strict gap <= 1e-8 is a separate
criterion from verification of an approximate result. Do not infer six-max
strength, fresh-board generalization, or expanded-tree capacity from this test.

No GPU work, neural training, policy adoption, commit or push is authorized here.
