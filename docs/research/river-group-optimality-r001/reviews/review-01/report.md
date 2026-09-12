# Independent opposing review: river group optimality r001

No material actionable findings. Specification verdict: **PASS within the authorized review scope**. Engineering verdict: **PASS within the authorized review scope**. The proposed observed-case invocation remains unexecuted and requires its separate controller approval. These verdicts assess the frozen diagnostic and its bounded smoke behavior; they do not assert successful completion or performance of the eight-case invocation.

## Identity, scope and independence

Candidate: `D:/Pontius-worktrees/eval-runner-consolidation`; branch `codex/river-abstraction-holdout`; base/HEAD `1b4d1a0e26cd4da90ff74678de2e48ef53ec5599`. This is an uncommitted incremental candidate atop prior uncommitted work. Frozen plan SHA256: `de07461ea9364a4fb40d0bce72a506549bc30ac609761bb0bc57ff4600c3b11c`.

I read the handoff, then identity and verified its seven members and branch/base before reading the pinned specification and computational source. I inspected the new kernel/tool and relevant labels, matrix aggregation/evaluation, one-bet reconstruction and evaluator dependency code. The independent inventory was written and hashed before opening test source or executing checks. Its unchanged SHA256 is `2a7e34fcf4d2d40e494b9d3b7fa538a27f66f9afd296e86b71971b27c6b70b1c`.

All seven identity members, seven source pins and 32 data pins match. Final verification repeated all 46 comparisons with zero mismatches and reconfirmed branch/base. Predecessor metadata hashes match identity: attributes preserve the predecessor prefix and add only the three new source/tool/test byte-preservation patterns; the test registry preserves all predecessor content after removing the single new CRLF registration line. An initial reviewer comparison expected LF and returned false for the registry; a direct diff and comparison using its actual CRLF bytes resolved that reviewer-check issue.

Historical-context disclosure: the session automatically supplied a general Pontius project memory summary and parent dispatch context. Near completion the parent also sent an author preflight status claim; I did not open its evidence and did not use that claim for either verdict. No memory files, previous review/disposition/check directories, ledgers, research-result narratives, or unrelated author/reviewer scratch were opened. The 32 pinned input files were used only as allowed data. I do not claim a historically context-free review. The pinned executable and installed packages were used, without opening other author scratch. No additional reviewer or subagent was used.

All writes are confined to `D:/Pontius/tmp/group-optimality-review-01`. No source mutation, dependency installation, commit/push, observed-case optimization, bound-plan invocation, training, clustering, feature calculation or new observed-board selection occurred.

## Independent mathematical assessment

Write `c_i = sum_j C_ij`. The encoded game is

`V(x,y) = sum_i (1-x_i)c_i + sum_ij x_i[(1-y_j)F_ij + y_j A_ij]`.

For a fixed legal x, player 1 chooses one fold/call probability per own hand. Its minimizing payoff is the check base plus `sum_j min(sum_i x_i F_ij, sum_i x_i A_ij)`. The sum over hidden opponent hands must occur before the minimum. For a fixed y, player 0's maximizing payoff is `sum_i max(c_i, sum_j[(1-y_j)F_ij+y_j A_ij])`. Group restrictions replace each own-hand choice with a shared group choice, so all member contributions must be summed before selecting that group's action. `saddle_bounds` implements precisely these legal responses, without revealing the opposing private hand.

Seat 0's LP has grouped x variables and unrestricted-hand t variables. It maximizes `sum c - c.x + sum t` subject to `t <= F^T x` and `t <= A^T x`. Dropping the constant and minimizing produces the implemented objective `[c,-1]` and constraint blocks `[-F^T,I]`, `[-A^T,I]`. Seat 1's LP has grouped y variables and unrestricted-hand u variables, minimizes `sum u`, and imposes `u >= c` and `u >= rowsum(F)+(A-F)y`. These are the implemented `[0,-I]` and `[A-F,-I]` blocks with right sides `-c` and `-rowsum(F)`. All auxiliary variables are free; policy variables have [0,1] bounds. Rectangular shapes and asymmetric grouping are handled correctly.

In the first LP the second inequality block's nonnegative dual weights represent call probabilities; in the second they represent bet probabilities. SciPy's inequality marginals use the opposite sign, matching the implemented negation. Solver clipping and floating aggregation cannot silently certify a wrong answer: full-hand, original binary64 coefficients and returned policies are recomputed as exact Fractions, independently of the LP objective and aggregated coefficients. A failed or overly wide candidate is rejected.

For each asymmetric game, a feasible x yields a lower bound and a feasible y yields an upper bound. Thus `[l0,u0]` contains v0 and `[l1,u1]` contains v1. Exact rational probability checks enforce [0,1] and equality within each required group. The gap limit is checked in exact arithmetic against 1/100000000 chips. Certificates concern the encoded binary64 payoff game, not ideal pre-rounding probabilities or a separately reimplemented card evaluator.

The least representable profile exploitability is `min_(x in X_G,y in Y_G) [U(y)-L(x)]/2 = (v1-v0)/2`, because the two policy variables separate. Therefore the implemented bounds are `[max(0,(l1-u0)/2),(u1-l0)/2]`. Pairing the proposed constrained x from seat 0 with the proposed constrained y from seat 1 realizes the upper endpoint exactly. This does not require those policies to solve the doubly compressed game. For a saved feasible grouped profile with exact exploitability E, subtracting the optimal interval gives `[max(0,E-E*_upper),E-E*_lower]`; the endpoint directions are correct.

Key reviewed locations: `src/pontius/river_group_optimality.py:45` (exact responses), `:72` (LPs), `:108` (verification), `:136` (saved gaps); `tools/river_group_optimality.py:87` (binding), `:116` (reconciliation), `:188` (cohorts), `:229` (execution).

## Requirement-to-evidence matrix

| Requirement or risk | Fresh evidence | Result |
| --- | --- | --- |
| Frozen identity/source/input binding | Independent initial and final hashes; real read_plan environment/binding validation; zero mismatches among final 46 comparisons | Pass |
| Correct asymmetric LPs and legal best responses | Derivation above; known exact synthetic values in focused suite; 36 independent dense/rectangular synthetic group-games with 72 asymmetric certificate checks | Pass |
| Exact saddle/feasibility certification | Independent exact pure-strategy payoff enumeration and separate normal-form simplex LPs with exact rational mixture bounds; malformed/group-inconsistent policy tests | Pass |
| Optimal exploitability and saved-gap direction | Independent enumeration of full-hand responses; proposed pair exactly equals reported upper endpoint in all 36 synthetic group-games; known rational restriction-cost fixtures | Pass |
| Full saved-input reconciliation | Reconstructed all eight 96x96 cases and 96 saved profiles with diagnostic solver patched to fail if called; matched provenance, ordered hands, joint masses, full metrics, groups and grids | Pass |
| Semantic rejection beyond hash checks | Six rehashed/rebound two-hand cases rejected altered lift, metric, joint mass, exact grouping, checkpoint and compressed capacity | Pass |
| Separate development/observed-holdout reporting | Existing synthetic cohort test uses unequal known per-case values and checks independent equal-weight means at all three checkpoints | Pass |
| Bounded execution and one-shot reservation | Source confirms 64 sequential observed LP calls, 5-second/10000-iteration limits, 300-second worker timeout; real two-hand subprocess and output reuse rejection | Pass for implementation and smoke; observed runtime unmeasured |
| Parent verification and failure evidence | Focused nonzero/timeout/missing-result cases; supplemental rejected certificate after nominal worker success; injected summary/manifest write failures prevent final manifest and produce failed record | Pass |
| Existing metadata preservation | Pinned predecessor hashes and direct incremental comparisons | Pass |

The focused tests contain meaningful known answers rather than relying only on the new implementation. Their original synthetic payoff matrix is diagonal and has zero check payoffs, so I supplemented it with 1x1, 2x3, 3x2 and 3x3 dense synthetic coefficient matrices, nonzero positive/negative check values and multiple grouping patterns. The independent normal-form oracle enumerates legal pure policies and optimizes simplex mixtures, then certifies its own bounds using Fractions. It shares SciPy for proposal generation, but does not share the candidate's asymmetric LP formulation or response routine.

## Commands and retained evidence

Environment for Python commands: `PYTHONDONTWRITEBYTECODE=1`, `PYTHONPATH=D:/Pontius-worktrees/eval-runner-consolidation/src`, and both TMP/TEMP set to reviewer scratch. The interpreter was exactly `D:/Pontius/tmp/group-opt-author/venv/Scripts/python.exe`, observed Python 3.14.6, NumPy 2.5.2 and SciPy 1.18.0. No installation occurred.

1. `python.exe -B -m pytest -p no:cacheprovider tests/test_river_group_optimality.py -q`, candidate working directory: **exit 0, 10 passed in 1.95s**. The first sandbox attempt failed to create the Python process (exit 101, access denied); the explicitly authorized escalated retry succeeded. This was an environment restriction, not a test failure.
2. `python.exe -B D:/Pontius/tmp/group-optimality-review-01/independent_checks.py`: **exit 0, all supplemental checks passed**. It retains the exact independent script, synthetic oracle/reconciliation output, rehashed malformed fixtures, persistent smoke artifacts and failure artifacts.
3. Read-only PowerShell SHA256 and Git HEAD/branch/scoped status/diff checks: all identity pins matched; branch/base unchanged; predecessor metadata preserved.

Persistent real smoke plan SHA256: `de2bbef55f36f462bcb13a04eed13fc7290e2f379f2a89c87999a27cdf6efad5`. Its output manifest SHA256: `045f925880b5d98016673826d46801acb937fc60760fb4ce2306b9eba7cc37a0`. Every manifest member was independently rehashed. It contains four method cases and four saved-profile comparisons for a two-hand development-board fixture.

Evidence hashes (SHA256):

- `inventory.md`: `2a7e34fcf4d2d40e494b9d3b7fa538a27f66f9afd296e86b71971b27c6b70b1c`
- `pytest.txt`: `ac9ba12b9658a5071eddd606ee0597aa0c985c97df58b0cd8458836112015dff`
- `independent_checks.py`: `c92fbecbe3cfe0199336ef749a06038a574346edda988db3e2399ba860a1b1ee`
- `independent-checks.txt`: `787143a8f6c7b436a8ae31f88770a13a141255a0aa331d9629ff114bef7c987e`
- `final-identity.json`: `d6ccf64ad943d304fa9cf9da10c07050bf6b6ef279da838eb0d2fb49a1baa6a5`

## Residual limits and disposition

No candidate correction is requested. No material unresolved finding remains in the authorized scope. The 96-hand observed games were not optimized, so their LP termination, actual certificate widths and worker completion within 300 seconds remain facts for the separately approved invocation to establish. Exact certificate rejection is the intended guard if a proposed solver result is unsuitable. Parent reconstruction, verification and I/O are outside the worker timeout, as explicitly specified; no RSS limit is claimed.

Timeout and evidence-write failures were controlled injections, not a real 300-second wait or disk exhaustion. A summary can have been written before a manifest-write failure; under the explicit contract it is incomplete evidence until the parent succeeds and a final manifest exists. The observed write-failure behavior follows that contract. Underlying evaluator reimplementation, hostile concurrent filesystem changes, hard kills/power loss, unrelated architecture, multiway play, unseen-board generalization and playing-strength evidence remain outside this review.
