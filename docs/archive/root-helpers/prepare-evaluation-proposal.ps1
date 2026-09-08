$ErrorActionPreference='Stop'
$taskRoot='D:\Pontius\tmp\v0a-evaluation-opening-r001'
$work=Join-Path $taskRoot 'authoring'
$base='e043f81ecec3ac16128720b42c3312bb41a4ed67'
$mapping=[ordered]@{
 'evaluation-brief.md'='docs/architecture/v0a-evaluation-r001/brief.md'
 'evaluation-design.md'='docs/architecture/v0a-evaluation-r001/design.md'
 'evaluation-source-contract.md'='docs/architecture/v0a-evaluation-r001/source-contract.md'
 'evaluation-plan.md'='docs/superpowers/plans/2026-09-07-paired-local-evaluation.md'
 'evaluation-adr.md'='docs/decisions/ADR-0508-open-the-paired-local-evaluation-source-round.md'
}
foreach($entry in $mapping.GetEnumerator()){
 $to=Join-Path $work $entry.Value
 if(Test-Path -LiteralPath $to){throw "Preserve existing proposal path $to"}
 New-Item -ItemType Directory -Force (Split-Path -Parent $to)|Out-Null
 [IO.File]::Copy((Join-Path $PSScriptRoot $entry.Key),$to,$false)
}
[IO.File]::Copy((Join-Path $PSScriptRoot 'evaluation-brief.md'),(Join-Path $taskRoot 'brief.md'),$false)
$scope=@('docs/decisions/ADR-0508-open-the-paired-local-evaluation-source-round.md',
 'docs/architecture/v0a-evaluation-r001/brief.md','docs/architecture/v0a-evaluation-r001/design.md',
 'docs/architecture/v0a-evaluation-r001/source-contract.md',
 'docs/superpowers/plans/2026-09-07-paired-local-evaluation.md','STATUS.md')
$scopeText="@("+(($scope|ForEach-Object{"'$_'"}) -join ',')+")"
$oldScope="@('docs/decisions/ADR-0507-permit-one-baseline-watch-demonstration.md','STATUS.md')"
$oldRoot='D:\Pontius\tmp\v0a-baseline-watch-opening-r001'
foreach($name in @('freeze-local.ps1','run-snapshot.ps1','prepare-status.ps1','run-final-gates.ps1','record-acceptance.ps1')){
 $text=[IO.File]::ReadAllText((Join-Path $oldRoot $name))
 $text=$text.Replace('v0a-baseline-watch-opening','v0a-evaluation-opening').Replace('0363bd50c1626f13d2e357f7ca527713bbdae059',$base).Replace($oldScope,$scopeText)
 $to=Join-Path $taskRoot $name
 if(Test-Path -LiteralPath $to){throw 'Preserve helper'}
 [IO.File]::WriteAllText($to,$text.Replace("`r`n","`n"),[Text.UTF8Encoding]::new($false))
}
[IO.File]::Copy($PSCommandPath,(Join-Path $taskRoot 'preparation-command.ps1'),$false)
'Copied six-path proposal inputs and adapted metadata-only helpers; no payload executed.'
