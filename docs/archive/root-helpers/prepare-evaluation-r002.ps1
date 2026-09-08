$ErrorActionPreference='Stop'
$taskRoot='D:\Pontius\tmp\v0a-evaluation-opening-r001'
$work=Join-Path $taskRoot 'authoring'
$planPath=Join-Path $taskRoot 'fix-r002-plan.md'
if(Test-Path -LiteralPath $planPath){throw 'Preserve correction plan'}
[IO.File]::Copy((Join-Path $PSScriptRoot 'evaluation-fix-r002-plan.md'),$planPath,$false)
$mapping=[ordered]@{
 'evaluation-brief.md'='docs/architecture/v0a-evaluation-r001/brief.md'
 'evaluation-design.md'='docs/architecture/v0a-evaluation-r001/design.md'
 'evaluation-source-contract.md'='docs/architecture/v0a-evaluation-r001/source-contract.md'
 'evaluation-plan.md'='docs/superpowers/plans/2026-09-07-paired-local-evaluation.md'
 'evaluation-adr.md'='docs/decisions/ADR-0508-open-the-paired-local-evaluation-source-round.md'
}
foreach($entry in $mapping.GetEnumerator()){
 $text=[IO.File]::ReadAllText((Join-Path $PSScriptRoot $entry.Key)).Replace("`r`n","`n")
 [IO.File]::WriteAllText((Join-Path $work $entry.Value),$text,[Text.UTF8Encoding]::new($false))
}
& (Join-Path $taskRoot 'run-snapshot.ps1') -RunName generate-status-r002 -Slot 311 -PythonArgs @('-m','pontius.status_generation')
$records=@(Get-Content -Raw -LiteralPath (Join-Path $taskRoot 'run-records\generate-status-r002-311.json')|ConvertFrom-Json)
if($records.Count -ne 2 -or $records[-1].exit_code -ne 0){throw 'Generation failed'}
$text=[IO.File]::ReadAllText((Join-Path $records[-1].snapshot 'STATUS.md')).Replace("`r`n","`n")
[IO.File]::WriteAllText((Join-Path $work 'STATUS.md'),$text,[Text.UTF8Encoding]::new($false))
& (Join-Path $taskRoot 'freeze-local.ps1') -Round r002
if($LASTEXITCODE -ne 0){throw 'Freeze failed'}
& (Join-Path $taskRoot 'check-candidate.ps1') -Round r002
