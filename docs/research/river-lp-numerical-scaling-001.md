# LP numerical scaling 001

The fixed rescaling closed both strict numerical misses from full-combo-direct-002.
All four cases pass the unchanged exact gap limit of 1e-8 on the original binary64
payoff matrices. This is a numerical diagnostic on four observed restricted river
games, not a fresh-board test or a larger betting tree. No production solver changed.

## Cause and falsifier

The installed HiGHS small_matrix_value default is 1e-9. Each original LP contains
49,989-514,102 nonzero coefficients at or below that cutoff. Replaying the retained
vectors against the complete constraints exposes residuals up to 3.79e-7. Removing
only those tiny coefficients reduces the maximum violation in every LP to at most
7.18e-16. Solver success therefore did not certify the complete supplied game.

A one-variable control, minimize -x subject to 1e-10*x <= 0 and 0 <= x <= 1,
returned x=1 through the original solver path. Its mathematically necessary x=0
assertion failed. The same control passed after rescaling. The RED remains retained.
This explains the coefficient-discard mechanism; individual policy-quality effects
are established by the exact original-matrix certificates, not by LP statuses.

## One fixed correction

Use value units S=2^20. For policy variables p and free value variables v, substitute
v'=S*v, multiply inequality rows and objective by S, and keep the policy simplex
equalities unchanged. The transformed objective is S*c_p*p + c_v*v'; transformed
inequalities are S*A_p*p + A_v*v' <= S*b. Divide returned free variables by S.
Policies retain their original units. Every scaling operation is an exact binary
power-of-two change for the finite coefficients in this panel; reverse scaling of
all reconstructed matrices, right-hand sides and objectives reproduced their bytes.
No nonzero transformed matrix coefficient falls below the cutoff; the smallest is
2.0455e-8. The adapter refuses if the fixed scale leaves any such coefficient.

The game, ranges, actions, solver method, 1e-9 feasibility tolerances, 10-second LP
limit, 20,000-iteration cap, and exact acceptance threshold are unchanged. The scale
was fixed from coefficient magnitudes before any full-case correction solve. There
was no search over scales, retraining, policy repair, retry, or threshold relaxation.

## Results

Error is half the unrestricted-response gap, normalized by 10/actual pot. Strict
acceptance means error <=5e-9. Times include transformation, LP assembly/solves and
the original-matrix exact certificate; shared game/kernel setup is separate.

| Situation | Previous error | Corrected error | Strict pass | Solve/certificate s | Worker peak commit MiB |
|---|---:|---:|---|---:|---:|
| 1 | 4.955590245e-09 | 2.989815184e-15 | Yes | 1.489 | 1238.4 |
| 2 | 1.370876885e-07 | 4.303660265e-16 | Yes | 4.583 | 2492.6 |
| 3 | 4.464393644e-09 | 1.371139777e-15 | Yes | 1.635 | 1218.8 |
| 4 | 2.164931289e-08 | 4.779184013e-16 | Yes | 1.558 | 1222.8 |

The prior experiment remains two passes and two misses. These are four new passing
solutions. Times have one observation per case; this is not a speed benchmark.
Each worker has a 120-second timeout and a sampled 3072 MiB private-memory stop
at 50 ms intervals. OS peak commit measures the full correction worker, including
game construction and certificate setup; it is not directly comparable with the
previous worker containing both learner and LP arms plus grouping-floor diagnostics.
Observed and executing process IDs matched for all eight worker/verifier processes.
The complete bounded campaign, including separate verifiers, took 29.004 s.

## Verification and retention

- Four GREEN tests passed: the analytic regression, exact algebra including a free
  value variable, refusal for insufficient scaling, and literal certificates for
  one- and two-size small games. The last test contains both game shapes.
- The retained campaign made exactly eight full-case LP calls, two per case.
  Small preflight controls made six other calls in total, including the RED.
- Four separate verifiers reconstructed games, checked 16,359,854
  binary64 coefficients against exact integers, and passed 12 literal subgame checks.
- The subsequent scaling audit reconstructed all eight LPs, reversed every coefficient
  transformation, bound raw scaled/unscaled vectors to the saved profiles, and made
  zero solver calls. The diagnostic replays also made zero solver calls.
- All 35 preceding milestones were hash-checked and preserved; the new record retains
  raw results, scripts, initial and cutoff diagnostics, tests, and the frozen plan.

Plan SHA-256: fcf7eb72aea54cc8507faf8ce02eea0a00b594d485fa2605246e01a2bacc9729

## Interpretation and next boundary

Probability weighting can make individual LP coefficients tiny without making their
aggregate strategic effect negligible. Keep an independent original-game certificate
and check the solver's numerical cutoffs whenever changing population or formulation.
The fixed scaling is validated here, not a universal conditioning policy for larger LPs.
Earlier certified bounds remain valid statements about their returned strategies;
this discovery does not retroactively turn prior numerical success into a certificate.

Direct full-hand LP remains the useful reference for this restricted river family.
The next useful test is a larger actual-stack river tree, including play after a check
and a raise response, to locate the time/memory boundary before returning to compression.
All 1,081 holdings are represented, but this still omits much of the betting tree,
joint folded-card marginalization, and multiway strategic interaction. No six-max
strength, policy adoption, or universal live-clock claim follows. No commit or push.
