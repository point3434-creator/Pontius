$ErrorActionPreference = 'Stop'
$taskRoot = 'D:\Pontius\tmp\v0a-evaluation-source-r001'
$coverage = Join-Path $taskRoot 'task1-fix01-coverage-final.md'
if (-not (Test-Path -LiteralPath $coverage)) { throw 'Final correction coverage missing' }
& (Join-Path $taskRoot 'freeze-source-v3.ps1') -Round task1-r002
$packet = Join-Path $taskRoot 'packets\task1-r002'
$identity = Get-Content -Raw -LiteralPath (Join-Path $packet 'candidate.json') | ConvertFrom-Json
$fixDiffPath = Join-Path $packet 'fix.diff'
& 'C:\Program Files\Git\cmd\git.exe' --no-replace-objects -c 'safe.directory=D:/Pontius/tmp/v0a-evaluation-source-r001/authoring' -C (Join-Path $taskRoot 'authoring') diff --no-ext-diff --no-renames -U10 "--output=$fixDiffPath" 55b1f5f75f7bcdf8061a2a02906a86769345715d $identity.commit
if ($LASTEXITCODE -ne 0) { throw 'FIX diff generation failed' }
Copy-Item -LiteralPath $coverage -Destination (Join-Path $packet 'coverage.md') -ErrorAction Stop
$coverageHash = (Get-FileHash -LiteralPath (Join-Path $packet 'coverage.md') -Algorithm SHA256).Hash.ToLowerInvariant()
New-Item -ItemType Directory -Path (Join-Path $packet 'reviews') | Out-Null
$body = @"
# Independent Task 1 FIX review

Finalizer: Codex coordinator. Round FIX, task1-r002, scoped correction of I-01.
This is a pure-contract checkpoint. Full integrated Tier C acceptance remains later.
Repository: D:/Pontius/tmp/v0a-evaluation-source-r001/authoring.
Ref: $($identity.ref).
Candidate: $($identity.commit).
Base: $($identity.base).
Tree: $($identity.tree).
Manifest SHA256: $($identity.manifest_sha256).
Rejected anchor: 55b1f5f75f7bcdf8061a2a02906a86769345715d.
Anchor manifest: c15299d1d6cbf53e0660fcd24e91f488e228735135b97a0ce467882eee089cb6.
Required finding: ../task1-r001/reviews/task-review.md, I-01.
Issued finding SHA256: 31774fe43923e0a9260dff18563e6e8976f81d7a6db391d38db0651e22d4e364.

Read CLAUDE/workflow, adopted source-contract and Task 1 brief. Read immutable raw
source and the exact FIX diff from rejected anchor. Independently record the relevant
invariant and related mutation/check/publication sites BEFORE opening coverage.md.
Deferred coverage input: this packet's coverage.md, SHA256 $coverageHash.
Then compare the two inventories. Do not read author reports, coordinator/implementer
transcripts or fix rationale outside the permitted frozen coverage claim.

Recompute candidate/ref/parent/tree, raw whole-row manifest and changed-file scope.
Verify all raw source files and final test snapshot binding. Corrected GREEN receipt:
task-root/run-records/task1-fix01-green-311.json, snapshot
2fe913fe95096cf9647fb2998ba856385ed0c99b; 24 tests passed actual 3.11.15.
Receipt SHA256 9a35a50a866e7d45fcef66cb3c59ec3825cd34b9d76279393da35a5a543f809b.
RED receipt task-root/run-records/task1-fix01-red-late-row-311.json must bind unchanged
rejected helper/fixture plus only test additions; 24 tests with eight failed assertions.
No poker, generator or new full-deal population. Native wrapper and registration
are outside this checkpoint; do not silently count their absence as acceptance.

Assess I-01 closure and related invariant/coverage within the scoped FIX, including
new breakage in changed paths. Required corrections remain binding. State CLEAN only
with none unresolved, explicit spec/engineering verdict and SOUND/STRAINED/WRONG SHAPE.
Preserve independent initial inventory in your attributed review before comparing
deferred coverage; report concrete required corrections and finite verification.
No source edits, payload tests, poker/generator/census execution, subagents or commits.
Write create-new reviews/task-review.md and progress.md in this packet only.
Use absolute native Git --no-replace-objects and exact command-local safe.directory.
"@
[IO.File]::WriteAllText((Join-Path $packet 'handoff.md'),($body -replace "`r`n","`n")+"`n",[Text.UTF8Encoding]::new($false))
(Get-FileHash -LiteralPath (Join-Path $packet 'handoff.md') -Algorithm SHA256).Hash
