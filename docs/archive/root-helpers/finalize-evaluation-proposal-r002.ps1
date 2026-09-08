param([Parameter(Mandatory=$true)][string]$ReviewCHash,
      [Parameter(Mandatory=$true)][string]$ReviewDHash)
$ErrorActionPreference='Stop'
$taskRoot='D:\Pontius\tmp\v0a-evaluation-opening-r001'
$packet=Join-Path $taskRoot 'packets\r002'
& (Join-Path $taskRoot 'run-final-gates-r002.ps1') -Round r002 -ReviewedASha256 $ReviewCHash -ReviewedBSha256 $ReviewDHash
& (Join-Path $taskRoot 'record-acceptance-r002.ps1') -Round r002 -ReviewedASha256 $ReviewCHash -ReviewedBSha256 $ReviewDHash
$summaryPath=Join-Path $packet 'checks\final-acceptance-summary.json'
$summary=Get-Content -Raw -LiteralPath $summaryPath|ConvertFrom-Json
if($summary.status -ne 'PASS' -or $summary.commands_passed -ne 4){throw 'Incomplete acceptance'}
$summaryHash=(Get-FileHash -LiteralPath $summaryPath).Hash.ToLowerInvariant()
$text=@"
# Paired evaluation source-opening proposal ready for exact adoption

Candidate: $($summary.candidate).
Base: $($summary.base).
Tree: $($summary.tree).
Manifest SHA-256: $($summary.manifest_sha256).
Ref: refs/heads/review/v0a-evaluation-opening/r002 in task-root/authoring.
Exact proposed decision title: Open the paired local evaluation source round.
Decision: ADR-0508. Exactly six documentation paths; no production code changed.

Two fresh independent Tier C FIX reviews found specification/engineering CLEAN,
0 Critical / 0 Important / 0 Minor required findings, and design SOUND:
- packets/r002/reviews/review-c.md SHA-256 $ReviewCHash.
- packets/r002/reviews/review-d.md SHA-256 $ReviewDHash.
Both recorded independent inventories before deferred coverage and closed A-I1/A-I2
at prospective contract level. Original r001 NOT CLEAN, reviews and bytes are retained.

Metadata acceptance: four commands passed in four fresh exact-candidate D-local
snapshots, actual CPython 3.11.15 first then 3.14.6, scrubbed -B -P procedure.
Each interpreter passed status --check and all twelve status tests, no skips/errors.
Original command receipts and interpreter/source origins are bound by
packets/r002/checks/final-acceptance-summary.json SHA-256 $summaryHash.
Final audit confirms exact six paths, nine raw B pins, primary tracked clean at B,
no source implementation, no poker payload and no new evaluation population.

Deliverable: strict fixed paired matrix with six-seat coverage, fresh stacks and
identical pair inputs; unchanged public sessions and native Job; explicit partial
denominators, action/hand/session cause observations and guarded publication semantics.
The shared deadline covers final verification commit, not later visibility/CLI latency.
Only the empty ephemeral publication guard may be removed after verified commit.

Next authorized action is pending: exact ceremonial adoption commit/push of these
six frozen paths, then its bounded source implementation and named finite correctness
controls. No source seal or actual evaluation run follows automatically. The maximum
new-suite population is 24 actual session starts per complete suite-set execution,
one declared zero-seed matrix and at most two literal deals. Source budgets and the
six exact registration exceptions remain those in the frozen contract.

CLAUDE.md rule 4 requires explicit authorization for this specific decision commit.
The user's earlier agreement was consumed by ADR-0507 and its single demonstration.
The user's Let's Begin authorized preparation of this source-opening proposal.
No decision commit, push, source implementation, seed creation or evaluation occurred.
All rejected/corrected proposal refs, snapshots, commands, coverage and reviews remain.
"@
$out=Join-Path $taskRoot 'readiness-r002.md'
if(Test-Path -LiteralPath $out){throw 'Preserve readiness'}
[IO.File]::WriteAllText($out,$text.Replace("`r`n","`n")+"`n",[Text.UTF8Encoding]::new($false))
"Readiness SHA-256: $((Get-FileHash -LiteralPath $out).Hash.ToLowerInvariant())"
