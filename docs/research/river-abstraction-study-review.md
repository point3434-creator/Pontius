# River abstraction study: candidate review entry

Status: author verified, opposing review pending. No CLEAN verdict is asserted.
Branch: `codex/river-abstraction-study` (uncommitted candidate).
Base: `ce73bf3e9cc996990e5fa5dbece8e16e14c8e0b7`.
Checkout: `D:/Pontius-worktrees/eval-runner-consolidation`.

## Scope and review order

This is a new small research experiment, not another Slice A wrapper repair.
The candidate implements a one-bet river payoff/CFR kernel, four representations,
and a bounded development driver. Existing runtime and solver sources are unchanged.
One opposing review is the next gate. No further implementation should be bundled
into that review; the retained campaign runner is explicitly a subsequent task.

For independent inventory first, read the design, the three new Python files and
the base commit's river, CFR, evaluation and river-oracle dependencies. Derive the
invariants before opening the checks directory or the author observations below.
This entry is not an automated cold-context isolation mechanism. A reviewer should
disclose any exposure to author observations before forming their inventory.

Key questions:

1. Does compilation preserve the entire collision-conditioned joint population,
   terminal payoffs and exact ties? Is the no-raise domain explicit?
2. Do exact-hand best responses evaluate the lifted grouped policies, with complete
   information-set coverage? Do finite-budget bounds avoid an equilibrium claim?
3. Do alternating regret and averaging updates implement the existing vanilla CFR
   semantics, including when multiple hands share one information set?
4. Is baseline equity identical to the 200-bin saved baseline? Do both alternative
   methods use the same occupied group counts and only declared public range data?
5. Are the range-equity control and richer-feature candidate distinct, deterministic
   and fairly measured? Does anchoring keep capacity without claiming optimal clustering?
6. Can the development driver overwrite prior evidence, consume a holdout board,
   silently omit a failure, or time work with tracemalloc active?

Use Python 3.14.6 only. Small tests are permitted; do not start a retained campaign,
change sources, commit or push as part of the review. Reviewer findings should state
the violated requirement, a reachable example, and a falsifying observation. Review
this scope proportionately; documentation advisories alone do not demand another round.

## Author verification

`river-abstraction-study-checks/author-evidence.json` binds candidate and check files.
The retained JUnit receipt has 55 tests, zero failures, errors or skips: 14 new cases
and 41 existing river/CFR/evaluator cases. ResourceWarning was promoted to error.
Ruff passes for all three new Python files. This is focused validation, not a full
repository suite. The initial missing-module RED was observed in tool history;
no independently retained RED receipt is claimed.

Independent comparisons within the tests include full-tree versus matrix values
and individual best responses; generic versus specialized CFR at multiple iteration
counts; generic grouped information sets; a tiny normal-form oracle; ties;
direct conditional-range features; duplicate-vector clustering; and driver output
reconstruction, failure recording, tracer refusal and overwrite refusal.

The baseline check pins the old abstraction and evaluator source digests, extracts
only the equity-table code, and loads no bucket/policy cache. All 1,081 hands on the
first development board match in hexadecimal float equity and final 200-bin label.
The old evaluator ran its Python fallback under 3.14.6. This checks one board, not
all boards. The script and raw result are retained in the checks directory.

## Development smoke observations

First development board, uniform ranges, 16 hands/player, 100 iterations, 225 legal
joint deals. All four results and full policies are retained under
`river-abstraction-study-checks/development-smoke/`. The manifest and source hashes
were rechecked when copied from the original scratch output.

| Representation | Occupied groups P0/P1 | Full exploitability, chips | Restricted gap, chips |
| --- | --- | --- | --- |
| Exact hands | 16 / 16 | 0.02137006 | 0.02137006 |
| Uniform equity, 200 bins | 12 / 13 | 0.03788204 | 0.02664443 |
| Range equity | 12 / 13 | 0.03962348 | 0.02031162 |
| Range-response features | 12 / 13 | 0.04790757 | 0.02559443 |

Both gap columns use (upper-lower)/2. Lower is better. These are observed values
for one deliberately small development check. The proposed richer features did
not win this check; no better-strategy claim is made and no clustering rule or
board was changed in response. The reduced gaps show incomplete convergence.
The 96-hand comparison, second development board, polarized regime, and all holdout
experiments have not been run. Timing and array storage are diagnostics only;
online latency and process peak are not measured.

## Following this candidate

After the opposing review and any material fixes, prepare one explicit multi-case
campaign plan with a resource preflight and retained failure handling. Freeze the
decision criteria before opening holdout results. Successful execution and superior
strategy quality remain separate questions; save non-improvements as well as wins.
