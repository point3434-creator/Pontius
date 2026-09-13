# River LP presolve comparison 001

Disabling HiGHS presolve did not recover either expanded deep-stack game within the
unchanged sampled memory envelope. Both baseline arms passed exact verification.
The off baseline used less peak memory but took longer in this single fresh pair.
No solver-option change earns adoption from this result.

## Question and frozen design

Does presolve account for enough of the native memory increase that turning it off
makes either stopped game affordable? Reuse the same pot-29, stack-186 case from
river-tree-expansion-001, with 1081 holdings per role and 1070190 compatible ordered
deals. Keep the original baseline, betting after check, and one-all-in-raise trees.

Run six fresh workers, one per tree/setting. Order is baseline on/off, checkback
off/on, raise on/off. This balances ordering direction somewhat; it is not random
assignment or statistical replication. Presolve is the sole solver-option change.
Each LP retains highs-ds, 10 seconds, 20000 iterations, 1e-9 feasibility tolerances,
2^20 value scaling, and the exact original-payoff gap threshold <=1e-8. Each worker
retains 180 seconds and the 3072 MiB private-memory stop sampled every 50 ms.

The adapter records the effective options, executing PID, and hashes of objective,
constraints, bounds and right-hand sides before every LP. Corresponding entered
calls received identical matrices and bounds in each pair. Both expanded workers
stop in call 0, so there is no executed second-call equivalence claim for those cells.
No full Python line trace or allocation tracer runs here. Hashing and compact call
records add the same measurement operations to both arms; compute timing includes them.

## Results

Compute includes game setup, assembly, both LP calls, policy extraction and exact
certification. Whole worker additionally includes startup, binding checks and output.
Peak is OS whole-worker commit, not exclusive LP memory. One observation per cell.

| Tree | Presolve | Compute s | Worker s | Peak MiB | Outcome |
|---|---|---:|---:|---:|---|
| baseline | on | 6.341 | 7.872 | 2082.0 | Exact certificate passed |
| baseline | off | 7.951 | 9.484 | 1904.0 | Exact certificate passed |
| checkback | on | not completed | 4.070 | 3331.6 | Memory stop |
| checkback | off | not completed | 2.455 | 3229.5 | Memory stop |
| raise | on | not completed | 7.124 | 6236.2 | Memory stop |
| raise | off | not completed | 3.500 | 6036.7 | Memory stop |

The baseline off arm used about 178 MiB less peak memory, with compute increasing
from 6.34 to 7.95 seconds. This is a descriptive paired observation, not an established
speed or memory ranking. Its exploitability was 1.0192e-15 versus 8.3749e-16 for on;
both are far below the unchanged acceptance limit of 5e-9 (half the gap limit).
Different numerical solutions are allowed; their certified equilibrium intervals overlap.
The on control also reproduced the earlier baseline policy, realization vectors,
payoff hashes and certificate exactly.

Both expanded off arms still reached the sampled stop. Lower recorded peaks or
shorter time-to-kill in these censored runs are not completed-solve improvements.
Neither has a saved policy, quality score, full-solve time or full-solve memory peak.
The monitor permits large overshoot: raise reached about 6 GiB under either setting.
The 3 GiB threshold is unchanged and is not a hard cap.

This establishes that disabling presolve alone is insufficient for these matrices
under this envelope. It does not establish that presolve is harmless, identify the
remaining native allocation, or rule out a better LP formulation. There is no fresh
board, independent replication panel, six-max strength result or compression result.

## Verification and retention

Preflight solved a tiny public-tree game under both settings, checked forwarded
options and identical LP inputs, required exact certificates and overlapping bounds,
and exercised the memory observer with a 128 MiB allocation. Four tiny LPs completed.

The main campaign completed four LP calls across the two baseline arms. Four expanded
workers were stopped during their first call. Each completed policy was checked in
a separate process with optimization forbidden, rebuilding its original payoff hashes,
behavior and exact certificate. The already-retained zero-payoff verifier correction
was used only for verification; the worker uses the original frozen tree implementation.
Thirty engine terminal checks and six literal rational subgames passed; the baseline
bounds overlap the older independently computed reference. All observed PIDs match.

The post-run assessment checked all six outcomes, option records, entered pairwise
matrix identities, exact control equality, and preservation of all 3130 members in
the 38 prior milestones. The unchanged source dependency pins were checked before
and after the campaign. All four stops remain retained with no score imputation.

Campaign wall time: 39.636 seconds, including separate verification.
Runtime: Python 3.14.6, NumPy 2.5.2, SciPy 1.18.0, one BLAS/OpenMP thread.
Frozen plan SHA-256:
1215eb9a264712154212cf5ba57cbf62d15afe3dd523ba1651d8a309951bb5ea

## Next research decision

Close this presolve toggle as a capacity non-improvement and keep the LP references.
The next useful comparison is a full-hand iterative method that computes payoff
products directly without constructing the large LP. Start on these same nested
river trees; measure memory and original-game exploitability against compute, with
the certified baseline as a control. Preserve private-hand detail and action menus
so representation and solver changes are not confused. Approximate progress must
not be relabeled as passing the strict exact threshold. This is a proposed research
comparison, not an already implemented solver or authorization for another run.

If that comparison also has no useful quality/cost tradeoff, revisit formulation or
compression as an explicit new direction. Do not continue an open-ended sequence
of option toggles. The restricted heads-up model and factorized public ranges remain
limitations; joint folded-card marginalization and multiway strength are untested.

Raw call records, worker/verification receipts and policies are under run/. The
frozen adapter, plan, preflight and assessment are under author/. No production
source changed. All previous milestones remain intact. Saved locally, not committed
or pushed.
