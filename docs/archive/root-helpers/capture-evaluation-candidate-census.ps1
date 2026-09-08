param([Parameter(Mandatory=$true)][ValidatePattern('^[a-z0-9]{1,8}$')][string]$Stage)
$ErrorActionPreference = 'Stop'
$taskRoot = 'D:/Pontius/tmp/v0a-evaluation-source-r001'
$candidate = $null
foreach ($slot in @('311','314')) {
    foreach ($population in @('test','production')) {
        $code = if ($population -eq 'test') { 't' } else { 'p' }
        $name = "c-$Stage-$code"
        $arguments = @{
            RunName=$name; Slot=$slot;
            PythonArgs=@("$taskRoot/capture-census.py",$population)
        }
        if ($candidate) {
            $arguments['ExactCandidate'] = $true
            $arguments['Candidate'] = $candidate
        }
        & "$taskRoot/run-source-snapshot-v2.ps1" @arguments | Out-Null
        $path = "$taskRoot/run-records/$name-$slot.json"
        $records = Get-Content -LiteralPath $path -Raw | ConvertFrom-Json
        if ($records.Count -ne 2 -or $records[-1].exit_code -ne 0) {
            throw "Census capture failed; preserve $path"
        }
        if (-not $candidate) { $candidate = $records[-1].snapshot_head }
        if ($records[-1].snapshot_head -cne $candidate) { throw 'Candidate drift' }
        [ordered]@{population=$population;slot=$slot;candidate=$candidate;
            receipt=$path;sha256=(Get-FileHash -LiteralPath $path).Hash.ToLowerInvariant();
            capture="$taskRoot/process-temp/$name-$slot/census-$population.json"} |
            ConvertTo-Json -Compress
    }
}
