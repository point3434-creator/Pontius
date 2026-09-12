# Bettor size repair 001

One bounded pilot on all eight retained combined-menu diagnostic cases. Known boards,
same K=16 partitions, hands, ranges, check/half-pot/pot actions and observed-size caller.
Caller policy stays fixed at the retained 50k checkpoint in every comparison.

Use the retained asymmetric bettor witness. For each hand compute all three weighted
action payoffs. Split a group by pot value > half-pot value versus <= (ties go right).
For every split and pair of other groups to merge, evaluate exact three-action group
objective gain minus merge cost. Choose largest strictly positive net gain; exact
ties choose lexicographically earliest (split,a,b). No gain means unchanged groups.
One binary split and one merge only; no parameter tuning or second repair.

Train the proposed bettor partition from uniform at 10k and 50k updates. Reconstruct
the original bettor at 50k and continue to 100k. Require the original coefficients
match retained bytes. Compare candidate 50k and continued 100k to incumbent 50k, all
with the identical retained caller policy. Both arms perform 50k additional bettor
updates; they are not equal-compute arms. Reused witness cost is excluded and stated.

For each candidate compute unrestricted worst-case bettor value across both observed
sizes. Accept only if >= incumbent; ties allowed. Caller value is unchanged. Retain
raw and selected exploitability. Independently enumerate terminal fold/call payoffs
to audit acceptance. Rejecting a proposal protects quality but spends computation.

After decisions, solve and certify the proposed bettor grouping; reuse the unchanged
caller certificate for a diagnostic grouping floor. This LP does not select a repair.
Verify the proposal by independent exhaustive partition enumeration and replay all
saved checkpoints. Verifier LP calls forbidden.

Descriptive criteria: exact nonregression for accepted repair and continuation; mean
accepted repair improvement >1e-6 chips versus incumbent and separately versus
accepted continuation. Report every case and raw regression; passing is not needed
for run completion. No fresh-board or generalization claim. Pilot ends with whether
this specific split earns further investigation, not automatic additional repairs.

Four new analytic checks and five inherited multi-action checks. Python 3.14.6,
one BLAS thread, no tracemalloc, 900-second worker/verifier limits; inherited LP
limit 10 seconds/20k iterations. No hard RSS cap. Immutable retention including
negative results; no automatic retry, fitting, production adoption, commit or push.
