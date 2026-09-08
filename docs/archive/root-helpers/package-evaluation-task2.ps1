param([Parameter(Mandatory=$true)][string]$ReceiptName)
$ErrorActionPreference = 'Stop'
$taskRoot = 'D:/Pontius/tmp/v0a-evaluation-source-r001'
$repo = "$taskRoot/authoring"
$sdd = "$repo/.superpowers/sdd/2026-09-07-paired-local-evaluation"
$git = 'C:/Program Files/Git/cmd/git.exe'
$receiptPath = "$taskRoot/run-records/$ReceiptName"
$receipt = Get-Content -Raw -LiteralPath $receiptPath | ConvertFrom-Json
if ($receipt.Count -ne 2 -or $receipt[-1].exit_code -ne 0 -or
    $receipt[-1].interpreter -ne 'D:\Pontius-tools\py311\Scripts\python.exe' -or
    $receipt[-1].argv[2] -ne 'tests/test_v0a_evaluation_runner.py') {
    throw 'Expected successful floor runner receipt'
}
$helper = (Get-FileHash "$repo/tools/v0a_evaluation_contract.py").Hash.ToLowerInvariant()
if ($helper -ne 'b62170553c20acce17bead44391904c53be43cf0cc59c0fd2fb9b47743e988ad') {
    throw 'Reviewed helper changed'
}
& "$taskRoot/freeze-source-v3.ps1" -Round task2-r001 | Out-Null
$packet = "$taskRoot/packets/task2-r001"
$identity = Get-Content -Raw "$packet/candidate.json" | ConvertFrom-Json
& $git --no-replace-objects -c "safe.directory=$repo" -C $repo diff --exit-code `
    $receipt[-1].snapshot_head $identity.commit -- tools/v0a_evaluation.py `
    tools/v0a_evaluation_contract.py tests/test_v0a_evaluation_runner.py `
    tests/test_v0a_evaluation_contract.py tests/fixtures/evaluation/controls.json
if ($LASTEXITCODE -ne 0) { throw 'Focused receipt source differs from frozen candidate' }
$receiptHash = (Get-FileHash $receiptPath).Hash.ToLowerInvariant()
$ruling = "$sdd/controller-budget-ruling-2026-09-07.md"
$rulingHash = (Get-FileHash $ruling).Hash.ToLowerInvariant()
$handoff = @"
# Independent Task 2 NEW-SURFACE review

Finalizer: Codex coordinator. Round task2-r001, NEW-SURFACE.
Task-scoped runner checkpoint; integrated Tier C acceptance remains later.
Repository: $repo.
Ref: $($identity.ref).
Candidate: $($identity.commit).
Base: $($identity.base).
Tree: $($identity.tree).
Whole-row manifest SHA256: $($identity.manifest_sha256).

Review tools/v0a_evaluation.py and tests/test_v0a_evaluation_runner.py against Task 2
and the adopted source contract. The other three new files are reviewed dependency
inputs at Task 1 checkpoint b10363549ce6538574ffe34a6db691733ae2c20b, not new Task 2
surface. They remain available to evaluate concrete caller/contract risks. Task 3's
boundary fault suite and registration changes are not yet in this checkpoint.
Do not treat their absence as final acceptance or a Task 2 omission; distinguish
production defects from explicitly pending Task 3 evidence.

Read repository CLAUDE.md and docs/workflow.md, adopted source-contract.md and
Task 2 brief. The controller explicitly approved production ceiling 1250, replacing
1200. Ruling record $ruling, SHA256 $rulingHash.
Scope, correctness populations, old source protection and other caps stay unchanged.

Recompute ref/parent/tree and the manifest from raw candidate blobs. Review immutable
packet files and diff, not mutable authoring files. Do not read implementer reports,
transcripts, coordinator design notes or other reviewers' reports. Permitted focused
receipt: $receiptPath, SHA256 $receiptHash.
Its exact snapshot $($receipt[-1].snapshot_head) matches all five candidate new files.
Inspect commands, full outputs and actual interpreter; do not merely trust a summary.

Assess exact source/native admission, fixed loader origins, capture ownership and
containment, deadline/stop semantics, create-only retention, public reader schemas,
publication transition and real negative-control oracles. State concrete required
failure scenarios with candidate lines. Independently inspect related paths for each
risk; maintain honest coverage limits. No payload execution, source edits, subagents,
commits or remote operations. Stage 3 review is read-only source inspection plus
existing finite receipts; coordinator retains execution ownership.

Write create-new reviews/task-review.md and your attributed one-line progress.md
only in this packet. Bind verdict to commit and manifest. State CLEAN only with no
required finding unresolved; give spec and engineering verdicts and one explicit
design verdict SOUND / STRAINED / WRONG SHAPE. Advisory choices remain distinct from
required corrections. Independent whole-source reviews follow after Task 3.
"@
[IO.File]::WriteAllText("$packet/handoff.md", $handoff.Replace("`r`n", "`n")+"`n",
    [Text.UTF8Encoding]::new($false))
$identity | ConvertTo-Json
