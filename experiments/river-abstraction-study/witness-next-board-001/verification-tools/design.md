# Next board: frozen two-repair confirmation

Run one unseen board, two existing range regimes and both bet sizes: four cases.
Select the first unused board in the existing SHA-256 sequence, starting at attempt
zero, with the original confirmation seed. Exclude all 26 retained plan inventories,
development and holdout boards, including suit-equivalent boards. Do not select by
texture or observed strategy results. Freeze the board and executable pins first.

Use the unchanged preference model, K=16, 96 holdings per role, pot 10, stacks 20,
bet sizes 5 and 10, uniform and polarized ranges. Train initial groups for 10,000
updates. Twice: solve the current-group witness, propose one split/merge per role,
train proposed groups from uniform through 1,000 and 10,000 updates, then apply the
existing exact per-role acceptance gate. Preserve every rejected role's incumbent.

From the accepted first repair, reconstruct its solver at 10,000 and run the frozen
timing comparison against the second repair's measured work and total budgets.
Matched stops before crossing pre-gate work; generous reaches total budget then
adds its own gate. Save raw and selected policies, costs and all timing boundaries.
Scoring, reconstruction and verification remain excluded from incremental costs.

Report all four cases without replacement or selective stopping. Exact nonregression
is mandatory. A mean second-step improvement >1e-6 chips for each bet and comparisons
against both continuations are descriptive outcomes, not run-validity gates.
Verify all certificates, solver endpoints, proposal exchanges, exact gate decisions,
and unchanged-group floor claims. Separate verifier performs no new LP solving.

15 inherited timing/gate/runner tests; direct suit-permutation novelty check;
900 seconds per worker and verifier, 200,000-iteration continuation cap, Python 3.14.6,
one BLAS thread, no allocation tracing or hard memory cap. Keep failures, no retries.
This is one additional board, not a population estimate. No fitting, adoption or publish.
