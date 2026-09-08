param([Parameter(Mandatory=$true)][ValidatePattern('^[a-z0-9]{1,8}$')][string]$Stage,
      [ValidateSet('test','production')][string]$Population,
      [ValidateSet('diagnose','explain')][string]$Mode='diagnose')
$ErrorActionPreference = 'Stop'
$taskRoot = 'D:/Pontius/tmp/v0a-evaluation-source-r001'
$scripts = 'C:/Users/point/.codex/worktrees/fa55/Pontius'
$python = 'D:/Pontius-tools/py311/Scripts/python.exe'
$code = if ($Population -eq 'test') { 't' } else { 'p' }
$capture = "$taskRoot/process-temp/c-$Stage-$code-311/census-$Population.json"
$directory = "$taskRoot/census-$Stage-$Population"
if ($Mode -eq 'diagnose') {
    & $python -B -P "$scripts/prepare-evaluation-census-map.py" $capture $directory
    if ($LASTEXITCODE) { throw 'Line-map preparation failed' }
    $notes = "$directory/empty-explanations.json"
    $output = "$directory/unexplained-comparison.json"
} else {
    & $python -B -P "$scripts/explain-evaluation-census-additions.py" `
        "$directory/unexplained-comparison.json" $capture "$directory/source-explanations.json"
    if ($LASTEXITCODE) { throw 'Source explanations failed' }
    $notes = "$directory/source-explanations.json"
    $output = "$directory/explained-comparison.json"
}
& $python -B -P "$taskRoot/compare-census-v2.py" `
    --baseline311 "$taskRoot/process-temp/baseline-census-$Population-311/census-$Population.json" `
    --baseline314 "$taskRoot/process-temp/baseline-census-$Population-314/census-$Population.json" `
    --candidate311 $capture `
    --candidate314 "$taskRoot/process-temp/c-$Stage-$code-314/census-$Population.json" `
    --repository "$taskRoot/authoring" --git 'C:/Program Files/Git/cmd/git.exe' `
    --line-map "$directory/line-map.json" --explanations $notes --output $output
$resultCode = $LASTEXITCODE
if (-not (Test-Path -LiteralPath $output)) { throw 'Comparator did not produce its retained report' }
$report = Get-Content -LiteralPath $output -Raw | ConvertFrom-Json
if ($Mode -eq 'explain' -and ($resultCode -ne 0 -or -not $report.mechanical_checks_pass)) {
    throw 'Explained comparison is not clean; inspect retained report'
}
if ($Mode -eq 'diagnose' -and $resultCode -notin @(0,1)) { throw 'Comparison crashed' }
[ordered]@{mode=$Mode;population=$Population;stage=$Stage;exit=$resultCode;
    issues=$report.issues.Count;output=$output;sha256=(Get-FileHash $output).Hash.ToLowerInvariant()} |
    ConvertTo-Json -Compress
