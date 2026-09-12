# F1 execution accounting addendum

The first opposing review's F1 is accepted. Its Partial labels remain unchanged.
The frozen runner's receipt measures its worker phase and omits later parent work.
Whole-command cost must therefore be recorded separately for the approved run.

The mandatory execution entry is accounting/measure_invocation.py, SHA-256:
c675cbfd5a6d57b7e43144b26ca2e14462cc87b91682c56faf2388595cb25e7f

It invokes the exact unchanged frozen run command once. A perf_counter interval
begins immediately before subprocess.run and ends when that command returns,
including its startup, worker, parent refit/verification, output finalization and
exit. Recorder preflight and its final receipt write are outside that interval.
The result is invocation-001/receipt.json.whole_command_seconds, separate from the
experiment output's receipt.json.seconds. Do not subtract the two and call the
difference pure parent cost: their start points and included overhead differ.

The recorder requires controller-authorization.json in the packet root, created
only after the user approves. It must contain their verbatim words plus the exact
plan_sha256 and recorder_sha256. This file currently does not exist. The approval
record is an audit prerequisite, not a cryptographic authentication mechanism.
The recorder checks the bound plan, source/training pins and candidate identity,
requires an absent bound output, and reserves invocation-001 with an exclusive
mkdir. Existing evidence is never reused. Captures and receipt use exclusive opens;
a failed write cannot produce a successful return. Child exit status is preserved.
There is no automatic retry and no change to the worker's 1,200-second limit.

Coordinator completion requires the bound runner's successful exit and valid
output manifest AND this outer receipt and captures. Archive both together. The
original run-command.txt is retained historical inner-command documentation; use
accounting/run-command.txt and accounting/approval-template.txt for this invocation.
The root approval-template.txt is superseded history. No original frozen member
or experiment source changed. Only the cost-recording execution layer was added.

Three author tests use inert processes only: delayed work after a simulated worker
phase, nonzero child/receipt-write failure, and approval-binding refusals. No actual
training fit or reserved score was executed. One focused same-reviewer follow-up
checks this F1 remedy; no repeated broad review, new cold claim or extra reviewer.
