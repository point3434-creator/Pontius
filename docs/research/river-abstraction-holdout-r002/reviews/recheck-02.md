# Focused correction recheck 02

**Specification verdict: PASS. Engineering verdict: PASS within the reviewed incremental contract.** Original P2 reporting finding is resolved. No material residual finding arose in this focused recheck. This closes the original blocker using the original review evidence for unchanged code plus fresh evidence for the correction; it is not a new broad review or holdout-execution approval.

## Target and identity

Packet: `D:/Pontius-worktrees/eval-runner-consolidation/docs/research/river-abstraction-holdout-r002/`.
Branch: `codex/river-abstraction-holdout`.
HEAD/base: `1b4d1a0e26cd4da90ff74678de2e48ef53ec5599`.
Bound plan SHA-256: `7377d6a37503f8a11e54b06dafcd783ed29e3b0e523d3569bbcfe17dc2a2533c`.

All eight r002 identity members matched at start and finish, with matching branch/base. Evidence: `identity-recheck-02-start.json` and `identity-recheck-02-final.json`. Exact plan parsing/schema/digest and every computational source pin also passed independently of execution; runtime was Python 3.14.6 and NumPy 2.5.2.

The specifically authorized frozen r001 campaign/test source copies were hashed before comparison. They match the original identity: campaign `dc1fc4427966dda08f1dbb6a8a7ceeb8ed99640f281787fd025d1c79826ff4e9`; test `8d8a71bc106ab3967276cce8dff2c4ce8e8304825596f01b0fd6cdcf4469fc7e`.

## Assessment of the correction

The new `summarize()` at `tools/river_abstraction_campaign.py:162` satisfies the missing reporting contract:

- Each checkpoint retains ordered per-case method-minus-reference differences against both `uniform_equity_200` and `range_equity`. This includes both required `range_response` comparisons. Extra comparisons for the other non-reference methods are deterministic and do not replace the primary/secondary references.
- Equal-weight differences use `fsum` of the four per-case differences divided by four. Existing full-exploitability means and original records/receipts remain retained.
- Per-case pot fractions subtract the already reconciled normalized exploitabilities. Their equal-weight mean uses the same four cases. With the fixed ten-chip pot this is the required normalization, subject only to ordinary floating-point arithmetic.
- Negative/zero/positive differences are counted explicitly. Presence of both negative and positive differences yields `mixed`, irrespective of the mean. One-sided patterns are `lower_or_equal` or `higher_or_equal`; all zeros are `equal`. Strict signs introduce no new fitted threshold.
- Metadata fixes the primary reference, secondary reference, subtraction direction and `headline_iteration=plan['iterations']` at line 197. Therefore the bound holdout headline remains 10000, with 100/1000 comparisons retained; the code does not choose a favorable checkpoint from data.

The new call at line 249 remains after all four reconciliations and the final source check. The exact diff against hash-verified prior source adds only `summarize()` and replaces the old inline summary builder with its call. No launch command, case order, timeout, failure behavior, plan schema or reconciliation rule changed. The library and single-case driver are byte-identical to the original reviewed identity; no feature, grouping, CFR or payoff method changed.

The prior finding's falsifier is now met: the successful summary producer explicitly emits `comparisons`, including both per-case series, mean differences, normalized differences, sign counts and mixed-sign labels.

## Focused executable evidence

Source was assessed independently before corrected test source was opened. A separate `recheck-02-inventory.md` was written and hashed first: `85ff689a8e2b66e0a93d782f3bffec6babb1c6cbe2a26447235c30d76af96e0f`.

Required interpreter: `D:/Pontius-worktrees/eval-runner-consolidation/.venv/Scripts/python.exe`. Python calls used `-B`, `PYTHONDONTWRITEBYTECODE=1`, and the available Windows escalation mechanism. TEMP/TMP pointed to the reviewer scratch for tests.

Executed from the source root:

```text
python.exe -B -m pytest -p no:cacheprovider tests/test_river_abstraction_holdout.py::CampaignTests::test_comparisons_preserve_signs_controls_and_all_checkpoints tests/test_river_abstraction_holdout.py::CampaignTests::test_small_development_campaign_and_tamper_rejection --basetemp D:/Pontius/tmp/river-holdout-review-01/pytest-recheck-02 -q
```

Exit 0: **2 passed in 4.37s**, recorded in `pytest-recheck-02.txt`.

The synthetic regression uses declared artificial metric values, not card-derived holdout observations. It checks all three checkpoints, fixed final headline, 18 comparisons, case order, the exact primary differences `[-1, 0, 1, -2]`, mean `-0.5`, normalized mean `-0.05`, sign counts and `mixed`; it also checks the secondary mean/pattern and an all-equal transformation. These are independently hand-checkable arithmetic expectations. The real development integration test verifies successful four-case execution now returns six comparisons for its single checkpoint, while retaining overwrite and tamper rejection coverage.

A separate `python.exe -B -` inline check loaded the runner and called only plan parsing, validation and source hashing; asserted the exact r002 plan digest, source equality and runtime pins. Exit 0, recorded in `plan-validation-recheck-02.txt`. No execution/reconciliation/card evaluation function was called by that check.

PowerShell SHA-256 checks and read-only Git branch/HEAD plus `diff --no-index` established identity and exact correction scope. Diff exit 1 indicates the expected file differences, not a verification error. Git used the absolute executable and per-command safe.directory where applicable. No Git state was mutated.

## Residual limits and preservation

The original nonblocking line-ending/whitespace observation in `tests/cases.json` remains unchanged. No additional style cleanup is required by this focused correction verdict.

The synthetic test does not execute holdout boards. Its values are constant across checkpoints, so the no-cherry-picking conclusion additionally relies on the direct assignment from bound plan iterations. The real integration uses two development hands and ten iterations; full-size holdout timing/memory/outcomes remain unmeasured. No real 60-second timeout test or broad suite was repeated because those paths are byte-unchanged and the requested recheck is narrow. The original review's boundary limits remain applicable.

Original artifacts remained byte-identical:
- `report.md`: `c153c15cae89b661d991f4af9ae11f8b99c7c8bda30021097dae9423f6ab90a0`.
- `inventory.md`: `a1e83f417c783a2625cf0bb8339f70a6e58149e3eeda393f277e5c1c62e7ae53`.

This recheck intentionally knows the original finding and retains the automatically injected historical context disclosed in the initial review. No memory files, ledgers, historical outcome files, previous author checks or other reviewer reports were opened. The only additional historical files read were the expressly authorized, hash-verified original source copies. No saved-smoke parity test was run. This is not an unqualified cold review.

No holdout equities/features/payoffs/policies were evaluated; neither bound packet plan was executed. No source/test edits, new tests, dependency installation, retained experiment, commit, push, publication or subagents occurred. All new writes were confined to the original private reviewer scratch. Holdout invocation approval remains a separate controller action.
