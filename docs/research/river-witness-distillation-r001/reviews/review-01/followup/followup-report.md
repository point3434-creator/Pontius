# Same-reviewer targeted F1 closure

**F1 is resolved for the composite bound execution: the unchanged distillation runner invoked through the mandatory, separately bound accounting recorder.** The original runner still omits whole-command duration by itself. The original Partial report, inventory and manifest remain unchanged; this follow-up does not rewrite that finding or claim a new cold review.

**Targeted specification verdict: Pass for F1 closure. Targeted engineering verdict: Pass for F1 closure.** The recorder covers the full inner command through process exit, retains command/binding/captures/status with a separate duration, and fails rather than reporting success when the tested evidence write or process launch fails. The current contract requires both inner successful completion/valid output manifest and outer receipt/captures. No new unresolved accounting defect was found.

## Exact reviewed composite

- Original plan: `47b26fc64aa3b2ddb36ebe11a02d16253b240a61672cff162c51af689728e524`.
- Mandatory recorder `accounting/measure_invocation.py`: `c675cbfd5a6d57b7e43144b26ca2e14462cc87b91682c56faf2388595cb25e7f`.
- Accounting manifest: `618ac5e076cdc1b99211076b98f0d1fd0434912d2897554978f7f12ac898b64e`.
- Current entry document `CURRENT.md`: `f4ee4fc303890edb499273268535c835f4cd89a0ccc88425425558b1163c1002`.

The recorder checks the controller record's nonempty verbatim words and exact plan/recorder hashes, reads the original bound plan through its existing source/training/environment verification, checks candidate identity pins, refuses an existing bound output, and reserves its invocation evidence directory exclusively. The approval record is an audit prerequisite, as the contract states, not a cryptographic authentication mechanism. This review did not create one.

## F1 traceability

| Requirement | Evidence | Result |
|---|---|---|
| Measure through complete inner-command exit | `measure_invocation.py:41-43` brackets blocking `subprocess.run`; the exact frozen runner command is built at lines 71-72. The contract includes startup, worker, parent refit/verification, output finalization and exit, and explicitly excludes recorder preflight and outer receipt writing. | Pass. |
| Keep full-command timing distinct from worker receipt | Outer `receipt.json.whole_command_seconds`, command and binding are written at lines 44-48; original inner receipt remains untouched. Contract warns against interpreting subtraction as pure parent cost. | Pass. |
| Preserve timing after a simulated worker phase | Fresh supplied test uses .02-second worker and .06-second parent delays. Independent retained probe prints worker completion, sleeps .08 seconds, then prints parent completion; the recorder reports 0.1478722000028938 seconds and captures both phases. | Pass on inert processes. This is boundary evidence, not a research performance estimate. |
| Retain command identity, binding and captures | Fresh tests inspect command/binding equality and stdout. Independent probe additionally checks stderr; retained files are under `inert-success/`. Approval test rejects blank words and mismatched plan or recorder hashes. | Pass. |
| Refuse absent authorization before launching | Independent probe calls the actual entry with subprocess.run guarded to raise if reached; missing controller-authorization.json raises first. | Pass; no subprocess or research import was reached on this path. |
| Preserve failures and avoid retry/reuse | Supplied tests retain nonzero child exit, reject existing evidence and raise on receipt-write error with failed.json. Independent probe retains exit 7 and stderr, and verifies an absent executable produces failed.json and no success receipt. Source uses exclusive directory/file creation and no retry. | Pass. |
| Require both layers for completion | Contract explicitly requires successful bound-runner exit and valid experiment manifest plus outer receipt/captures, archived together. Recorder preserves child return code; evidence write exceptions prevent successful return. | Pass for the documented composite workflow. The recorder does not independently re-audit the output manifest; that remains the stated coordinator completion obligation. |
| Make current entry and approval clear | CURRENT.md and accounting contract explicitly supersede historical root templates with accounting/run-command.txt and accounting/approval-template.txt. Approval text binds both plan and recorder and retains worker/parent resource boundaries. | Pass for selection of the current entry; pending disposition navigation advisory below. |
| Preserve original bytes and original review | All 105 original identity/freeze/source/training bindings and all 29 original review-manifest members were independently rehashed, plus the original review manifest itself. All 8 accounting manifest members match. | Pass at start and completion. |

## Current-packet navigation advisory

`CURRENT.md` says to read `disposition.md` first, but the file was absent on both live checks in this follow-up. An attempted read returned file-not-found. The coordinator confirmed that this is a pending coordinator artifact to be created after reading this sealed report, before delivery, and explicitly asked the reviewer not to wait for or review it.

This is a remaining handoff-document navigation item, not an unresolved timing defect: both CURRENT.md and the accounting contract independently identify the same current command and approval template. This report does not claim disposition.md exists or has been reviewed. No additional review round is required solely for writing that coordinator disposition.

## Fresh checks and retained receipts

Pinned Python 3.14.6 and pytest 9.1.1. Used `-B -W error::ResourceWarning`, pytest `-p no:cacheprovider`, target-worktree `-c .../pyproject.toml`, `PYTHONDONTWRITEBYTECODE=1`, inherited `PYTHONWARNINGS=error::ResourceWarning`, and scratch-only TEMP/TMP/basetemp. The already established pinned-interpreter sandbox escalation was approved. No installation or source mutation was needed.

1. `D:/Pontius/tmp/group-opt-author/venv/Scripts/python.exe -B -W error::ResourceWarning -m pytest -c D:/Pontius-worktrees/eval-runner-consolidation/pyproject.toml -p no:cacheprovider D:/Pontius-worktrees/eval-runner-consolidation/docs/research/river-witness-distillation-r001/accounting/test_accounting.py --basetemp D:/Pontius/tmp/witness-distill-review-01/followup/pytest-temp --junitxml D:/Pontius/tmp/witness-distill-review-01/followup/accounting-tests.xml` — **3 passed in 0.36 seconds**, exit 0. Log: `accounting-tests.txt`.
2. Same interpreter with `-B -W error::ResourceWarning` running `followup/probe_accounting.py` — exit 0. The probe uses only inert commands and the guarded missing-authorization entry. Observations: `probe-receipt.json` and `probe-output.txt`; retained records in `inert-success/`, `inert-exit7/`, `inert-start-failure/`.
3. `followup/verify_preservation.ps1` — passed at entry and completion. Final snapshot: `preservation-final.json`; entry/absence facts: `entry-state.json`.

At final check, the real packet controller authorization and invocation-001 directory and the bound experiment output directory were all absent. No actual fitting, reserved equity/group/LP, scoring or research invocation occurred. No original test suite or original smoke fit was repeated.

## Original seals preserved

- Original inventory: `427562a8801044e19555408c7c105e0c2fe243b8b2e46f164b6bc117886b6678`.
- Original report: `4dfb29b31c37b737d9cc8db9732a7ba1cb726e46f41f5725f5ef751da8d0a208`.
- Original review-manifest: `ce26b6828ac225fe191a18884b59a5f360e9798445053d031433ad299e5455d8`.

This follow-up's artifacts are separately hashed in `followup-manifest.json`; its report SHA-256 is in `followup-report.sha256`. The original manifest was neither extended nor replaced.

## Context and limits

This is the same reviewer following up on their own F1 finding, with full knowledge of the earlier sealed review and the coordinator's acceptance/remediation request. It is not independent of that earlier context and is not described as a cold review. New substantive inputs were accounting/contract.md, recorder source, tests, current command/approval templates, CURRENT.md and accounting manifest; accounting XML/lint files were only hash-read. The pending disposition read failed, so no disposition contents influenced this verdict. The coordinator's statement that it will be created is disclosed above and is not treated as live filesystem evidence.

No memory files, other reviewer scratch, prohibited historical narratives, broad source audit, fan-out, actual model fitting, reserved-case work, launch approval, source/metadata editing, publication, commit, push or ledger entry occurred. Every follow-up write is under `D:/Pontius/tmp/witness-distill-review-01/followup/`. Tests establish the accounting boundary and failure behavior on inert processes; they do not establish full research runtime, resource feasibility or strategic results. Composite closure applies only when the mandatory recorder and dual-layer retention/completion obligations are used.
