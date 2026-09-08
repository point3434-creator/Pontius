param([Parameter(Mandatory=$true)][string]$ReceiptName,
      [Parameter(Mandatory=$true)][string]$CoverageName)
$ErrorActionPreference = 'Stop'
$taskRoot = 'D:/Pontius/tmp/v0a-evaluation-source-r001'
$repo = "$taskRoot/authoring"
$sdd = "$repo/.superpowers/sdd/2026-09-07-paired-local-evaluation"
$git = 'C:/Program Files/Git/cmd/git.exe'
$anchor = '674f82da9e044705fdaa6df46ad0a3d43b681ca9'
$anchorManifest = '036e0830134303e5240911216062ea588dba99893d4d5e1913a420530badcf0b'
$reviewHash = 'a3788610d9cedcc4cca16ea4db9f62124084ce1df59c5b9a4220b82169be431c'
$receiptPath = "$taskRoot/run-records/$ReceiptName"
$receipt = Get-Content -Raw $receiptPath | ConvertFrom-Json
if ($receipt.Count -ne 2 -or $receipt[-1].exit_code -ne 0 -or
    $receipt[-1].interpreter -ne 'D:\Pontius-tools\py311\Scripts\python.exe' -or
    $receipt[-1].argv[2] -ne 'tests/test_v0a_evaluation_runner.py') {
    throw 'Expected successful floor runner receipt'
}
if ((Get-FileHash "$taskRoot/packets/task2-r001/reviews/task-review.md").Hash.ToLowerInvariant() `
    -cne $reviewHash) { throw 'Issued review changed' }
$coverageBytes = [IO.File]::ReadAllBytes("$sdd/$CoverageName")
$coverageHash = (Get-FileHash "$sdd/$CoverageName").Hash.ToLowerInvariant()
& "$taskRoot/freeze-source-v3.ps1" -Round task2-r002 | Out-Null
$packet = "$taskRoot/packets/task2-r002"
$identity = Get-Content -Raw "$packet/candidate.json" | ConvertFrom-Json
& $git --no-replace-objects -c "safe.directory=$repo" -C $repo diff --exit-code `
    $receipt[-1].snapshot_head $identity.commit -- tools/v0a_evaluation.py `
    tools/v0a_evaluation_contract.py tests/test_v0a_evaluation_runner.py `
    tests/test_v0a_evaluation_contract.py tests/fixtures/evaluation/controls.json
if ($LASTEXITCODE -ne 0) { throw 'Focused receipt source differs from frozen candidate' }
$changed = & $git --no-replace-objects -c "safe.directory=$repo" -C $repo diff `
    --name-only $anchor $identity.commit
if ($LASTEXITCODE -ne 0 -or @($changed).Count -ne 2 -or
    @($changed | Where-Object { $_ -notin @('tools/v0a_evaluation.py',
        'tests/test_v0a_evaluation_runner.py') }).Count) { throw 'FIX scope changed' }
[IO.File]::WriteAllBytes("$packet/coverage.md", $coverageBytes)
$start = [Diagnostics.ProcessStartInfo]::new()
$start.FileName = $git
$start.UseShellExecute = $false
$start.CreateNoWindow = $true
$start.RedirectStandardOutput = $true
$start.RedirectStandardError = $true
foreach ($arg in @('--no-replace-objects','-c',"safe.directory=$repo",'-C',$repo,
    'diff','--no-ext-diff','--no-renames','-U10',$anchor,$identity.commit)) {
    $start.ArgumentList.Add($arg)
}
$proc = [Diagnostics.Process]::Start($start)
$buffer = [IO.MemoryStream]::new()
$errors = $proc.StandardError.ReadToEndAsync()
$proc.StandardOutput.BaseStream.CopyTo($buffer)
$proc.WaitForExit()
if ($proc.ExitCode) { throw $errors.Result }
[IO.File]::WriteAllBytes("$packet/fix.diff", $buffer.ToArray())
$receiptHash = (Get-FileHash $receiptPath).Hash.ToLowerInvariant()
$handoff = @"
# Independent Task 2 FIX review

Finalizer: Codex coordinator. Round FIX, task2-r002, T2-01 and T2-02.
Repository: $repo.
Ref: $($identity.ref).
Candidate: $($identity.commit).
Base: $($identity.base).
Tree: $($identity.tree).
Manifest SHA256: $($identity.manifest_sha256).
Rejected anchor: $anchor; manifest $anchorManifest.
Issued findings: ../task2-r001/reviews/task-review.md, SHA256 $reviewHash.

Read CLAUDE/workflow, adopted source contract and Task2 brief. The user-approved
production ceiling is1250; all other scope and population constraints remain.
Read immutable packet source and exact fix.diff. Independently record the native
execution-admission and completed-row downgrade invariants and related sites BEFORE
opening coverage.md (SHA256 $coverageHash). Then challenge that deferred coverage
inventory, actual cases/oracles and stated limits. No implementer reports/transcripts,
coordinator rationale or other current reviewers' findings are permitted inputs.

Recompute candidate/ref/parent/tree, raw whole-row manifest, changed scope, dependency
preservation and exact focused snapshot binding. GREEN receipt $receiptPath,
SHA256 $receiptHash; snapshot $($receipt[-1].snapshot_head).
Deferred coverage names the retained RED evidence against unchanged rejected tools.
Only wrapper and runner tests change from the rejected anchor. No Task3 new surface
belongs in this FIX; publication fault suite/registrations and integrated reviews are later.

Assess closure of both findings, related category coverage and changed-path regressions.
Give concrete required scenarios, explicit spec/engineering and design verdict
SOUND/STRAINED/WRONG SHAPE. CLEAN requires no unresolved required correction.
Preserve your independent initial site inventory before comparing coverage.
No source edits, payloads, poker/generator/census execution, subagents, commits or pushes.
Write create-new reviews/task-review.md and attributed progress.md in this packet only.
Native Git is absolute with --no-replace-objects and exact command-local safe.directory.
This is scoped Task2 FIX review; full integrated TierC acceptance remains pending.
"@
[IO.File]::WriteAllText("$packet/handoff.md", $handoff.Replace("`r`n", "`n")+"`n",
    [Text.UTF8Encoding]::new($false))
$identity | ConvertTo-Json
