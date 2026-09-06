# ADR-0501: Permit one watch-first demonstration

- Status: accepted demonstration-only exception upon its separately authorized decision commit
- Date: 2026-09-06
- Follows: ADR-0500
- Base-Commit: ef5268448862f3ab77870db42b383dfcbcbc66e7
- Invocation-Authority: none until separate exact demonstration launch authorization
- Front-Door-Kind: controller-v1
- Front-Door-Research: ADR-0280
- Front-Door-Process: ADR-0501
- Front-Door-Contract: ADR-0307
- Front-Door-Revoked: ADR-0281, ADR-0468, ADR-0472, ADR-0475
- Front-Door-Active-Next: Authorize one supervised demo; formal operation/research closed
- Front-Door-Blockers: demo launch approval pending; formal operating prerequisites open

## Decision

Prospectively permit one separately authorized, supervised terminal demonstration
of the exact source-sealed watch-first session. Its purpose is to let the controller
see cards, public actions, carried stacks and the between-hand controls. It yields
no correctness acceptance, cost calibration, policy selection or research result.
This proposal has no effect before its exact decision commit is authorized and made.
The decision commit alone does not launch the demonstration.

This is an explicit narrow exception to the blanket execution closures in
ADR-0489 and ADR-0500, and to ADR-0485's operational prerequisites only for this
named non-evidentiary display. It is not an inference that a run becomes permitted
when called a demo. All formal operating, rehearsal, experimental and research
invocations still require their existing prerequisites and separate authorization.
The source acceptance and two original source reviews under ADR-0500 stand unchanged.

The demo uses the unchanged executable correctness namespaces listed below because
the sealed session, host and event adapter require those literal identities. For
this one display only, this decision permits their use under external demonstration
authority. Their names and event fields are not evidence of a test execution or an
authorized research mode. Preserve them verbatim, including evidentiary=false in
the event result. Do not patch a prefix, change a trace mode, promote an old run,
or claim that the sealed parser now supports an authorized trace. This exception
does not define a reusable authorization interface or change any semantic schema.

## Exact demonstration

Source snapshot: ef5268448862f3ab77870db42b383dfcbcbc66e7, from ADR-0500.
Use a fresh detached D-local clone with core.autocrlf=false and no working overlay.
Its entire tracked tree must equal that commit and its working files must match
the raw Git blobs before launch. Keep the snapshot and original outputs afterward.

Reserve only D:/Pontius/tmp/v0a-watch-demo-run-r001 as the disjoint demo root.
It and its source subdirectory remain absent until separate exact launch approval.
The snapshot root and process cwd will be that root's source subdirectory.
No historical experiment, rehearsal, correctness run or retained root is reused.

Bind these existing snapshot-relative files without modification:

- tools/v0a_table_session.py, SHA-256
  13b98563a92f1d2d78116d4efa2e6d4b15f491d623397166b3b1618e5276ef09.
- tests/fixtures/table_session/two_hands.json, SHA-256
  d346935d0a6ff660cea77e3e3703999bb976ec0274a12d389eaba150d8a56e78.
- tests/fixtures/table_host/empty_blueprint.json, SHA-256
  f10540623dcb1a725d60831ca367e0e3f1e519b14ebf68da8f36afa840e45258.

Interpreter: D:/Pontius-tools/py311/Scripts/python.exe, actual CPython 3.11.15;
verify the actual implementation/version before the poker payload. Interpreter
selection is compatibility, not a performance choice. Use -B -P and absolute
PONTIUS_GIT=C:/Program Files/Git/cmd/git.exe. Scrub the parent environment to the
Windows process essentials used by accepted snapshot checks, set PYTHONPATH to
the snapshot's src, PYTHONNOUSERSITE=1 and PYTHONIOENCODING=utf-8, and put TEMP/TMP
in the disjoint demo root. No GPU, optional packages, network play or import overlay.

The exact payload vector uses absolute input paths and the pinned source cwd:

```text
-B -P tools/v0a_table_session.py
--session
D:/Pontius/tmp/v0a-watch-demo-run-r001/source/tests/fixtures/table_session/two_hands.json
--blueprint
D:/Pontius/tmp/v0a-watch-demo-run-r001/source/tests/fixtures/table_host/empty_blueprint.json
--session-id pontius-v0a-table-session-v1-correctness-watch-demo-001
--format text
```

Line breaks above separate arguments for readability, not multiple invocations.
There is no --auto. Use an interactive terminal; Enter/n advances and q/EOF stops
between hands. Ctrl+C requests interruption under the existing caller-observable
contract. Do not inject poker actions, change the schedule, add a hand or retry.
The fixed source derives child IDs ending in correctness-table-watch-demo-001-h01
and correctness-table-watch-demo-001-h02 under its existing event protocol.

Population is exactly the existing two-hand synthetic schedule: six seats, 200
chips each, blinds 1/2, initial button 0, Pontius in seat 3, five passive opponents.
Both deals repeat the same fixed cards; this is deliberately visible behavior,
not randomness or strategic variety. The empty blueprint exercises legal passive
fallback; it is not a trained policy. Existing test expectations are final stacks
[210,198,198,198,198,198] after hand one and [220,196,196,196,196,196] after hand two,
with buttons 0/1. Those facts describe the adopted fixture, not a future result
or a new acceptance gate. Pontius does not win these fixed hands.

## Supervision, limits and honest failure

One launch attempt is permitted after exact approval; zero retries or successor
attempts. This is a count chosen for the requested demonstration, not a calibrated
research lifecycle budget. Reserve the root with create-new semantics after approval.
Record the approval, source/input identities, expanded argv and environment before
the payload; record a create-new launch intent before starting it. An existing root,
preflight failure, ambiguous launch or interrupted attempt stops this plan. Retain
the state and return to the controller; never delete the root to obtain another try.
These operator records are not a new evidence owner or machine-enforced scientific
authorization certificate. No concurrent launch or automatic resumption is allowed.

The existing normative 15000 ms action wall and 1000 ms emission reserve remain
binding. Preserve source limits: 256 actions/events per hand, 60-second exchange
wait within the 300-second hand deadline, 2 MiB child stdout and 64 KiB child stderr
capture per hand, and 4096-byte text lines within 4 MiB total terminal publication.
Existing failure codes, partial captures and native cleanup retain their meanings.
These are inherited source bounds, not measured operating ceilings or proof of a
whole-session deadline. In particular, a blocked terminal write and between-hand
human waiting are not covered by a newly claimed hard wall. The operator must stay
present and stop an unresponsive session; do not leave it running unattended.

No calibrated process-tree memory limit, aggregate temporary-storage limit or
whole-session watchdog is claimed or introduced. This named display uses trusted
unchanged local source, fixed tiny inputs, existing bounded captures and human
supervision; it is not admitted as an unattended or resource-certified operation.
If those conditions cannot be met, stop before launch. Formal operating limits
still require their own resource/provenance/enforcement/failure mapping and closure.
Do not substitute old launcher-only memory samples for payload-tree measurements.

Retain the terminal output available from this single display, actual exit status,
and an operator disposition. A truncated/unavailable capture remains so labeled;
it cannot establish a complete session. Observed completion, deliberate quit,
interruption, failure and unknown launch outcome stay distinct. No new run is made
to recover missing output. No measured duration, memory, throughput, strength,
quality ranking or tuning data may be inferred or reused from the demonstration.
If it reveals a defect, report it; any fix needs its own bounded source task and
fresh correctness evidence, not a relabeled demonstration receipt.

## Acceptance and scope

This decision changes exactly this new ADR and generated STATUS. It changes no
source, tests, fixtures, registration, workflows or previous decision bytes.
The authority exception requires two independent fresh Tier C reviews of an
immutable candidate. After both are CLEAN, run unchanged status generator --check
and all twelve status-generation tests in fresh exact-candidate D-local snapshots
on actual CPython 3.11.15 first, then 3.14.6, following the accepted scrubbed -B -P
procedure. Recheck referenced raw blobs and absence of the reserved demo root.
These metadata gates execute no poker hand and are not demonstration permission.

After review and gates, ask the controller to authorize the exact decision commit
and push. Ask separately for the exact launch, or clearly name both actions in one
approval request. A generic historical commit approval grants no new launch.
Keep every original review and failed attempt. No cleanup or ref retirement.

The exception ends after this one attempt. Additional demonstrations, altered deals,
opponents or policies, human poker input, operating use, calibration, training,
self-play, league evaluation, H32, campaign, compiled work and analyzer repair are
not opened. The next choice after the display is ordinary product development or
an explicitly scoped formal operating entry; this decision does not choose either.
