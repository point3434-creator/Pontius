# Independent opposing review 01

No Critical or Important finding was established for the declared first development-candidate gate. One Minor reporting nonconformance remains. This is one independent review, with no subagents, source changes, retained comparison, or campaign execution.

## Verdicts

- **Specification: PASS for the material first-gate requirements, with the Minor reporting omission below.** The specialized payoff/BR kernel, alternating vanilla CFR, four representations, matched occupied capacity, deterministic input preparation, and bounded single-case driver are supported by fresh executable evidence. This is not a claim of literal completeness of the later fixed comparison reporting specification.
- **Engineering: PASS for the declared bounded development use.** The 14 focused tests passed on CPython 3.14.6; independent mathematical checks passed after correctly separating exact-indifference trajectory sensitivity from equation correctness. There is no authorization or readiness verdict for a formal campaign, holdout, deployment, commit, or push.

Confidence in absence of a material issue in this bounded scope is moderate-to-high; finite tests and inspection do not prove every possible numerical input. No general playing-strength or abstraction-improvement conclusion follows.

## Findings

### Critical

None.

### Important

None.

### Minor M1: normalized bounds and individual deviation gains are not emitted

- **Location:** `D:/Pontius-worktrees/eval-runner-consolidation/tools/river_abstraction_study.py:104-105`.
- **Requirement:** `docs/research/river-abstraction-study.md:82-83` asks for raw bounds and both individual deviation gains in chips and fractions of pot; inventory items 6 and 12.
- **Reachable example/falsifier:** every ordinary successful driver run, including the existing two-hand/10-iteration focused success test, stores `full_game` and `restricted_game` with chip-valued `value`, `lower`, `upper`, `deviation0`, `deviation1`, and `exploitability`. Only `full_exploitability_fraction_of_pot` is emitted. Inspecting the record proves that lower/upper and either player's gain have no normalized counterpart. Emitting those counterparts, equal to each existing chip value divided by the persisted pot, would falsify the finding.
- **Consequence/materiality:** consumers must normalize these fields themselves. The raw values and pot are retained, so nothing needed to recover or audit them is lost. This is a narrow output completeness issue, not a payoff, evaluation, capacity-fairness, or run-safety defect. It does not block the first engineering smoke gate.
- **Smallest correction direction:** emit consistent normalized versions of the full/restricted measurements or expressly defer that report format in the first-gate contract. No correction was made in this review.
- **Confidence:** high, directly supported by the record-building code and successful focused driver test.

## Scope and independence

Identity read before assessment: `D:/Pontius/tmp/river-study-review-01/identity.json`. Checkout root is `D:/Pontius-worktrees/eval-runner-consolidation`; HEAD is `ce73bf3e9cc996990e5fa5dbece8e16e14c8e0b7`; branch is `codex/river-abstraction-study`. All five identity members matched SHA-256 before source assessment and again at completion; the final evidence is `identity-final.json` in this review directory. The candidate consists of the design, kernel, development driver, focused test file, and one tests/cases.json insertion. The insertion adds only `test_river_abstraction_study`.

The inventory was independently derived from design/source and relevant unchanged dependencies, written to `inventory.md`, and hashed **before opening test contents or executing checks**. Its SHA-256 is `16f8dfcf6cbcc44090c704b55b67c83577b385a41941865b16c95f5476d36e50`.

Automatically injected context included a memory summary with historical Pontius training/evaluator information and user preferences. It was not used as evidence. No memory file/index, ledger, STATUS/progress/INDEX file, forbidden review/check directory, author observations, other reviewer output, or prohibited scratch document contents were opened. Git status exposed the pathname of the implementation plan, but its contents were not opened. Parent messages supplied identity/scope, confirmation that files remained unchanged, and an environment hint to use execution escalation; no substantive author findings were consumed. The using-superpowers skill explicitly exempts dispatched subagents; code-verification and its verification matrix were used. No prohibited-source content exposure occurred.

## Requirement-to-evidence assessment

| Invariant | Evidence and result |
| --- | --- |
| Legal joint population, exact ties, payoff economics | Kernel builds from positive RiverHoldem marginal support and weighted legal deals. Generic evaluator agreement, all-tie fixture, independent scalar outcome enumeration, and 16-hand polarized product-weight reconstruction passed. Incompatible pairs contribute zero, including in tie features. |
| Information-constrained full best responses | Existing generic BR comparison and normal-form value bracketing passed. Independently enumerated all pure own-hand policies on 40 tiny matrix cases; maximum absolute value/bound discrepancy was 1.7763568394002505e-15 chips. BR optimization remains per own hand, not per hidden deal. |
| Aggregation changes policy class only | Block-sum aggregation preserves lifted values. Both focused tests and 40 independent cases confirmed full upper >= restricted upper, full lower <= restricted lower, and equal fixed-policy value within 1e-12. Exact grouping retains each hand. |
| CFR update and averaging | Generic full-tree and grouped-information-set trajectory checks passed. Independent scalar signed-regret bookkeeping agreed for 800 steps across 40 nondegenerate small cases, with 1e-11 absolute/relative comparison tolerances. Player 1 updates against newly updated player 0. Own prior action reach is one for both players, so arithmetic average per hand/group is appropriate even after an opponent's zero-probability bet. Negative regrets are retained. |
| Uniform baseline reproduction | The declared baseline abstraction.py SHA-256 matched `91ae39e94d8f1e2f908bcc3be2690d6e7a9114e4c1143330c290fe7c463a5518`. Every one of 1,081 first-development-board equities matched baseline river_equity bit-for-bit, using its distinct pure-Python rank evaluator and inclusion-exclusion counting. All corresponding 200-bin labels matched. The multiplication-before-int operation is preserved. |
| Input selection and polarized weights | Independent SHA-256 payload/order construction reproduced the first board's 16 selected hands for each player. All weight assignments matched 4/1 cutoff rules. The prepared polarized case had 225 legal joint deals, each matching independently reconstructed normalized products within 1e-15. No policies were trained for this preparation check. |
| Range features and perspective | Generic conditional-range tests and independent direct half-open-band comparisons passed for both players. Feature masses sum to one, win/tie masses respect band mass, and equity equals win mass plus half tie mass. Own-hand conditioning correctly reverses showdown perspective for player 1. |
| Fair occupied capacity and anchored clustering | The prepared polarized case had exact capacity [16,16], and [12,13] for baseline, range-equity and range-response methods. Duplicate-vector checks with K=1,4,8 remained occupied; deterministic seed/anchor and 20 weighted Lloyd source logic matches the declared rule. |
| Bounded driver, artifacts and failure handling | Source inspection verifies CLI ranges and development-board-only input. Existing focused success test executed 2 hands/10 iterations, reconstructed every saved full-game result, checked manifests, and confirmed overwrite refusal. Failure injection/tracing-refusal test passed. Tiny tests directly exercise the driver; no campaign runner or external wrapper was launched. |
| Timing and storage labels | Source inspection confirms separate compilation/grouping/aggregation/training/evaluation windows and cumulative training checkpoints. Array bytes are explicitly qualified and tracing is refused. No timing, process peak, convergence-rate, or playing-strength claim was inferred. |
| Tests registry and unchanged target | cases.json diff contains the single intended registration; final five hashes plus HEAD/branch match the supplied identity. |

## Fresh execution and diagnostic classification

All executable checks used `D:/Pontius-worktrees/eval-runner-consolidation/.venv/Scripts/python.exe`, CPython **3.14.6**, NumPy **2.5.2**, with `PYTHONDONTWRITEBYTECODE=1` and `-B`. TEMP/TMP for pytest were set to this review directory. No dependency was installed. Initial sandboxed `--version` attempts at candidate and workspace venv launchers failed with Access is denied; execution escalation resolved the environment restriction. No automatic approval review rejected an action.

1. From the candidate root: `.venv/Scripts/python.exe -B -m pytest tests/test_river_abstraction_study.py -p no:cacheprovider --basetemp D:/Pontius/tmp/river-study-review-01/pytest-temp -q` -> **exit 0, 14 passed in 0.85s**. Direct file selection avoided the tracked journal harness. This includes the only successful driver execution performed in the review: the existing tiny focused test.
2. `.venv/Scripts/python.exe -B D:/Pontius/tmp/river-study-review-01/diagnostics.py` -> **exit 0**. Details are retained in `diagnostics.json`. This performs baseline reproduction, exhaustive pure-response tests, scalar CFR checks, grouped value/BR checks, 16-hand polarized input preparation, conditional features and capacity checks. It is a bounded mathematical diagnostic, not a retained method-comparison run.
3. The original integer-weight random diagnostic failed its overstrong scalar-vs-vector trajectory equality assertion at trial 2, second step. The original case is preserved in `tie_sensitive_diagnostic.py`; its failure context was obtained with one rerun. A separate exact-fraction calculation, `tie-diagnostic.py`, exited 0 and saved `tie-diagnostic.json`, proving the cause: player 1's last-hand fold and call values both equal **-10/13** exactly. Scalar summation produces regrets [0,0]; the matrix sum produces [1.1102230246251565e-16,0]. Vanilla regret matching therefore chooses uniform versus fold at the exact-indifference boundary. Subsequent trajectories can diverge despite locally equivalent payoffs. Nondegenerate real-weight cases were then used for the trajectory comparison and all 800 steps passed.

The tie diagnostic is a synthetic matrix stress case, not a claimed reachable poker-card counterexample or a material finding against the declared driver. Its useful lesson is that mathematical CFR equivalence does not imply bit-identical trajectories across summation orders at zero regret. The preserved evidence rules out treating the initial failed assertion as an unexplained green-retry or concealing it. No payoff/BR disagreement of material magnitude was found.

## Limits and intentionally deferred work

- No 96-hand comparison, holdout, default 16-hand/100-iteration smoke, training campaign, benchmark wrapper, commit, push, candidate mutation, or index/HEAD/worktree mutation was executed. The 16-hand polarized check only prepared inputs/features/groups; the diagnostic CFR instances were tiny synthetic games.
- The formal multi-case plan consumer, equal-weight campaign reports, retention of failed campaign attempts, and frozen holdout decision rules are explicitly later gates. Their absence is not a first-gate finding.
- The cited saved baseline-000 meta.json hash was not independently located or verified. Baseline algorithm reproduction was verified against the exact source hash and all first-board equity values. No saved blueprint strength or provenance claim rests on the unverified metadata citation.
- Baseline equity identity was exhaustively checked on the first development board only. No global all-board evaluator proof, interval-certified numerical bound, campaign performance test, or large convergence study was attempted.
- The focused driver test validates its supported small namespace invocation; unsupported arbitrary hand-built PayoffGame arrays, imported run(args) outside the CLI contract, and hypothetical hostile output-directory races were not escalated into findings.

All review-created files are confined to `D:/Pontius/tmp/river-study-review-01`. The report and inventory hashes are delivered separately to avoid self-referential report hashing.
