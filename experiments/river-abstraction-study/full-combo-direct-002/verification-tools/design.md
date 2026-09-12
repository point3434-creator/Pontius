# Full-combo direct 002

Measurement repair: the first attempt completed all mathematical checks but the Windows
venv launcher hid its child from the process-memory observer. Its memory figures and stop
claims are invalid. Preserve the attempt verbatim; repeat unchanged solver settings after
starting the base CPython 3.14 executable directly with isolated paths to the same scientific
packages. Assert observed PID equals executing PID, and prove a 128 MiB allocation is seen.
This repeats the measurement after a harness defect, not after an unfavorable solver result.

Approved question: where does direct solving with a strategy for every holding stand
against our compressed river approach in quality, time and memory?

Reuse all four public range records from blueprint-range-transfer-001, with the actual
pots, stacks and odd-chip settlement validated in river-stack-transfer-001. Deduplicate
bet sizes: cases 0,2,3 have check/all-in and case 1 has check/bet14/bet29. The caller
can fold or call after a bet; check ends in showdown. No future streets, caller lead
after check, reraises, additional sizes or multiway opponents. Full hand detail means
all 1081 board-legal two-card holdings independently represented, not a full betting tree.

Ranges and floor remain fixed; collision-only joint inclusion, all 1070190 ordered
compatible deals, exact ties with seat-ordered odd chips. Folded-player cards remain
unmodeled. Preserve the frozen preference model's sixteen groups for the compressed
arm. Both arms use identical full payoff matrices, normalized by 10/actual pot.

Per case:
- Compressed: unchanged plain-regret best-response learner, both roles 50000 updates,
  exact unrestricted-response exploitability evaluated after the final update.
- Grouping floor: two asymmetric primal/dual LP pairs, unchanged certification.
- Full hand detail: one primal/dual LP pair with both group maps equal to identity.
  No card abstraction. Solve with the existing HiGHS dual-simplex code, unchanged
  time limit 10s per LP, 20000 iterations and 1e-9 feasibility settings. Retain exact
  rational bounds on the original binary64 matrix; require gap <=1e-8, corresponding
  to exploitability <=5e-9. Do not treat solver success alone as a certificate.

Observe and retain solver statuses, iterations, options, raw solutions and wall time.
An LP failure or certificate refusal remains not_certified; no automatic retries,
changed tolerances or substituted algorithms. Unexpected execution failures remain
visible per-case failures. No mean over survivors presented as a complete panel.

Order alternates: full first on even cases, compressed first on odd cases. Shared
game and integer-evaluator construction are timed separately. Full solve time includes
LP setup and exact bounds; report exact-bound time separately. Compressed time includes
setup, 50000 updates and average; exact scoring is separate. Grouping certificates are
diagnostics. This is an operating-point comparison, not a matched-time experiment or
an algorithm-independent lower bound on compute. One timing observation per case.

Largest dense primal inequality matrix has 4324 rows x 5405 columns, 186969760 bytes.
The dual has 3243 rows x 3243 columns, 84136392 bytes, plus 46742440 bytes of primal
equalities. This static inventory is not an RSS prediction: solver conversions, copies,
factorization and exact-integer arrays add memory. A parent samples private bytes every
50ms and stops above 3072 MiB; it is a sampled stop rule, not a hard memory cap.
Each case worker and verifier has a 120s wall stop. One case subprocess at a time;
one BLAS thread, Python 3.14.6, existing evaluator, no tracing or dependency installation.
Record worker/verification process peaks separately. Peaks cover the whole case process,
not isolated solver arms. Run receipts distinguish stops, exits and uncertified LPs.

Before freeze: tests against literal Fraction bounds for one/two bets and grouped/full
response constraints; small full-hand LP parity; four actual-game dimension/group checks;
byte-identical two-size payoffs to the last milestone. Exercise success, time-stop and
memory-stop observer paths. Verify all 34 preceding milestones and frozen dependencies.

Fresh verifier: replay compressed updates, rebuild games and input identities, recheck
full and grouping certificates without new LP solves, inspect all integer coefficients
against their float integer ratios, literal subgame bounds for full solutions, and
repeat 60 engine settlement observations. Retain policies and every outcome as a named
milestone. Preserve previous evidence and unrelated dirty files; no production edits,
checkpoint training, commit or push.

Interpretation: exact enumeration removes Monte Carlo evaluation noise conditional on
these four cases. It does not establish broad board generalization, mature blueprint
range quality or six-max playing strength. Direct solving of this small restricted tree
does not demonstrate feasibility for a full river tree, earlier streets or six players.
