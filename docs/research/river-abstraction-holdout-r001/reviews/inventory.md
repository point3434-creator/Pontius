# Independent invariant inventory — review 01

Written before opening tests, test registration, or author checks. Single reviewer; no delegation.

## Identity and allowed scope

Root: D:/Pontius-worktrees/eval-runner-consolidation
Branch: codex/river-abstraction-holdout
HEAD/base: 1b4d1a0e26cd4da90ff74678de2e48ef53ec5599
All eight identity.json member SHA-256 values matched before inventory. The bound plan digest is 579fe72afb5a467f7e25cec83bee2ea6faf42e4d21cb3ae96a499545e846d266. Git status contains exactly the listed tracked modifications and new packet/spec/test/campaign paths. Root AGENTS.md and ancestor AGENTS.md were absent; no nested AGENTS.md found under src/tools/tests.

Opened: handoff.md, identity.json, the holdout and original study specifications, plan.json, the changed production source, and the tracked source/.gitattributes diff against base. Tests were hashed as opaque bytes, not opened. Read code-verification skill and its matrix, plus using-superpowers skill (its subagent exclusion applies).

Automatically injected historical memory summary and user preferences were present in context, including older poker training/review descriptions and throughput claims. No memory files, ledgers, earlier review/check directories, author scratch, or development outcomes were opened. This is an independent fresh pass with disclosed injected history, not an unqualified cold review.

## Requirement -> observable invariant -> planned evidence

1. Explicit holdout admission: only the two declared board tuples are accepted with explicit holdout split; development remains the default and rejects holdout. Static board encoding and dispatch plus tests that stop before holdout evaluation.
2. Preservation: payoff math, CFR updates/averaging, equity enumeration, grouping and deterministic hand/range selection remain identical to base after the admission gate. Exact diff and existing development regression checks.
3. Plan-only preparation: creating/parsing/validating the bound plan performs no card evaluation or policy training. Static imports/call graph; parse exact packet bytes with parse_json/validate_plan only.
4. Fixed population/grid: holdout uses 96 hands, 100/1000/10000 checkpoints, exact ordered two boards x two regimes x four methods; alternative group capacity equals baseline per player/case. Static validation and reconciliation; development executable checks only.
5. Binding: exact plan bytes/digest, strict JSON/schema, absolute one-shot output path, Python 3.14.6/NumPy 2.5.2 and declared computational hashes are checked before reservation; no run overrides. Negative existing checks and fresh plan/source equality.
6. Reconciliation: exact child manifest, input population/weights/joint/groups, case identity, checkpoint grid, policy shape/domain/lifting and full/restricted raw/normalized metrics; incomplete or inconsistent child must stop completion. Static trace and existing mutation checks on development fixtures.
7. Sequential resource/failure contract: four children in order, one BLAS thread, 60 seconds each, no continuation after nonzero/timeout/ordinary failure, original bytes/stdout/stderr/receipts retained, output never reused. Existing development/mocked failure checks and static ordering.
8. Complete report: all 48 holdout profiles and per-case results/differences retained; equal-weight final primary comparison against uniform-equity and secondary against range-equity; mixed signs identified as mixed; earlier checkpoint means and full/restricted bounds/gains/pot fractions retained without post-hoc winner selection. Inspect summary builder and assertion oracles. Initial source observation: summary currently builds raw means/records/receipts, so explicit differences and mixed-sign reporting require particular attention.
9. Publication boundary: summary only after four reconciled cases and final source check; successful exit plus final manifest required; failure receipts preserve partial state. Static trace and focused existing checks.
10. Interpretation: finite-population/fixed-case finite-budget scope; no strength, sampling CI, generalization or asymptotic floor claim. Specification and emitted limits inspection.

## Execution limits

Only root .venv/Scripts/python.exe, confirmed 3.14.6, with -B and PYTHONDONTWRITEBYTECODE=1. Direct pytest files with -p no:cacheprovider and unique temporary directory under this review root. No holdout evaluations/features/equities or execution of packet plan. No source edits, new tests, dependency install, index/HEAD mutations, retained experiment, commit or push. Reverify identity at finish. Evidence will be proportionate and limited to this incremental contract.
