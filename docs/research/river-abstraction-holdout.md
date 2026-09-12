# Fixed holdout comparison

Status: build and review candidate; holdout outputs have not been opened.
The accepted design is the unchanged four-method, equal-capacity comparison from
river-abstraction-study.md. This amendment admits the two previously reserved boards
and defines the complete reporting/execution boundary. It changes no features,
clustering rules, range weights, hand selection, CFR updates or payoff equations.

## Fixed experiment and interpretation

The board order is `3c 3d 8h Ts Ad`, then `4s 6s 8s Td Qh`. Each uses uniform then
polarized ranges, 96 hands per player, and checkpoints 100, 1,000 and 10,000.
All four methods run on every case. Alternative group counts equal the baseline's
occupied counts for that player/case. All 48 checkpoint profiles must be present.

Primary comparison: equal-weight mean full-game exploitability at 10,000 iterations
versus uniform-equity bins. Secondary comparison: the same metric versus range-equity
grouping. Every per-case result and difference is retained. Negative candidate-minus-
baseline differences favor the candidate; mixed signs are reported as mixed results.
No winning threshold is selected after seeing data and no earlier checkpoint is
selected as a method's headline result. The summary also supplies means at the two
earlier checkpoints, full and restricted bounds/gains, and pot-normalized metrics.

These are exact finite-population evaluations conditional on four declared cases,
with finite-budget strategies. No sampling confidence interval, six-max strength,
generalization to all boards, or asymptotic abstraction-floor claim follows.
Both holdout boards remain unopened during construction and development rehearsals.

## Execution contract

`tools/river_abstraction_campaign.py plan` writes a JSON plan without evaluating
cards or training a policy. Holdout plans require exactly 96 hands and 10,000
iterations. Development plans may use 2-96 hands and 1-10,000 iterations for checks.
All plans declare exactly two boards times two regimes in fixed order, a new absolute
output directory, Python 3.14.6, NumPy 2.5.2 and computational source/document hashes.
Those pins cover the listed study implementation, not every installed dependency.

`run` requires both the plan path and its SHA-256. It checks the digest, strict
schema, environment and source bytes before atomically creating the output directory.
The directory is the one-shot reservation: existing directories are refused, never
cleared or retried. The original plan bytes are copied before launching a child.
No output-directory or population override is accepted by `run`.

The four cases run sequentially, one BLAS thread, with a 60-second timeout per child.
This gives at most 240 seconds of child waiting, excluding parent validation and I/O.
The workload is bounded to 96x96 payoff arrays and 10,000 iterations per method.
No process RSS cap is imposed or claimed; array storage is not process peak memory.
The child has no project subprocess descendants; subprocess.run's timeout terminates
and waits for that single worker. Child stdout, stderr and exit receipts are retained.
An ordinary exception, nonzero child exit or timeout stops the sequence and records
failure. Failed and completed directories are never reused. Hard process kills,
power loss and external filesystem sabotage are outside this recovery contract.

After each child, verification checks its three-member manifest, source pins,
declared inputs, exact case identity, complete method/checkpoint grid, group capacity,
lifted policies, and recomputed full/restricted metrics. This is a consistency check
using the already independently tested kernel; it is not a new independent solver.
The summary is written only after all four cases and a final source check succeed.
The final campaign manifest and successful process exit are also required: a lone
summary file is not proof that publication completed. Partial files remain evidence.

## Authority and review

Preparing a plan does not execute it. Holdout execution follows one focused opposing
review and the controller's approval of the bound plan. No holdout evaluation is
needed for implementation checks: use development end-to-end fixtures, inspect the
holdout constants, and stop mocked holdout dispatch before card evaluation.
Publication, source adoption, future experiments and CFR-BR work are separate actions.
Historical research receipts and milestone files remain byte-unchanged.
