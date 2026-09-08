param([Parameter(Mandatory=$true)][ValidatePattern('^[0-9a-f]{40}$')][string]$Candidate)
$ErrorActionPreference = 'Stop'
$taskRoot = 'D:/Pontius/tmp/v0a-evaluation-seal-r001'
$identity = Get-Content -Raw -LiteralPath (Join-Path $taskRoot 'packets/r001/candidate.json') | ConvertFrom-Json
if ($identity.commit -cne $Candidate) { throw 'Candidate mismatch' }
# Coordinator verifies the independently issued Tier A CLEAN verdict first.
$harness = Join-Path $taskRoot 'run-seal-snapshot.ps1'
foreach ($slot in @('311','314')) {
    & $harness -RunName 'mcheck1' -Slot $slot -PythonArgs @('-m','pontius.status_generation','--check') -ExactCandidate -Candidate $Candidate | Out-Null
    & $harness -RunName 'mtest1' -Slot $slot -PythonArgs @('tests/test_status_generation.py') -ExactCandidate -Candidate $Candidate | Out-Null
    foreach ($name in @('mcheck1','mtest1')) {
        $path = Join-Path $taskRoot "run-records/$name-$slot.json"
        $records = Get-Content -Raw -LiteralPath $path | ConvertFrom-Json
        if ($records.Count -ne 2 -or $records[-1].exit_code -ne 0 -or $records[-1].snapshot_head -cne $Candidate) { throw 'Metadata acceptance failed' }
        [ordered]@{slot=$slot;name=$name;receipt=$path;sha256=(Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant()} | ConvertTo-Json -Compress
    }
}
