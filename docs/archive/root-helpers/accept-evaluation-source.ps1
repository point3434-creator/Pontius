param(
    [Parameter(Mandatory=$true)][ValidatePattern('^[0-9a-f]{40}$')][string]$Candidate,
    [Parameter(Mandatory=$true)][ValidatePattern('^r[0-9]{3}$')][string]$Round
)
$ErrorActionPreference = 'Stop'
$taskRoot = 'D:\Pontius\tmp\v0a-evaluation-source-r001'
$harness = Join-Path $taskRoot 'run-source-snapshot-v2.ps1'
$packet = Join-Path $taskRoot "packets\$Round"
$identity = Get-Content -Raw -LiteralPath (Join-Path $packet 'candidate.json') | ConvertFrom-Json
if ($identity.commit -cne $Candidate) { throw 'Candidate identity mismatch' }
# The coordinator verifies the two independent CLEAN review documents before invoking.
# These fixed command vectors are transcribed from the adopted source contract.
$commands = @(
    @{name='status'; argv=@('-m','pontius.status_generation','--check')},
    @{name='status-tests'; argv=@('tests/test_status_generation.py')},
    @{name='boundaries'; argv=@('tools/check_stabilization_boundaries.py')},
    @{name='inventory-check'; argv=@('tools/generate_test_inventory.py','--check')},
    @{name='inventory-tests'; argv=@('tests/test_inventory_and_profiles.py')},
    @{name='evaluation-contract'; argv=@('tests/test_v0a_evaluation_contract.py')},
    @{name='evaluation-runner'; argv=@('tests/test_v0a_evaluation_runner.py')},
    @{name='evaluation-boundary'; argv=@('tests/test_v0a_evaluation_boundary.py')},
    @{name='seeded'; argv=@('tests/test_seeded_deals.py')},
    @{name='seeded-boundary'; argv=@('tests/test_seeded_deals_boundary.py')},
    @{name='host'; argv=@('tests/test_v0a_table_host.py')},
    @{name='host-boundary'; argv=@('tests/test_v0a_table_host_boundary.py')},
    @{name='session'; argv=@('tests/test_v0a_table_session.py')},
    @{name='session-boundary'; argv=@('tests/test_v0a_table_session_boundary.py')},
    @{name='provider-session'; argv=@('tests/test_decision_provider_session.py')},
    @{name='provider-transport'; argv=@('tests/test_decision_provider_transport.py')}
)
if ($commands.Count -ne 16) { throw 'Command population mismatch' }
foreach ($slot in @('311','314')) {
    $commandIndex = 0
    foreach ($command in $commands) {
        $commandIndex += 1
        $runName = 'a-{0}-{1:d2}' -f $Round, $commandIndex
        & $harness -RunName $runName -Slot $slot -PythonArgs $command.argv -ExactCandidate -Candidate $Candidate | Out-Null
        $receiptPath = Join-Path $taskRoot "run-records\$runName-$slot.json"
        $receipt = Get-Content -Raw -LiteralPath $receiptPath | ConvertFrom-Json
        if ($receipt.Count -ne 2 -or $receipt[-1].exit_code -ne 0 -or $receipt[-1].snapshot_head -cne $Candidate) {
            throw "Acceptance failed: $receiptPath"
        }
        [ordered]@{
            slot=$slot; name=$command.name; exit_code=$receipt[-1].exit_code;
            receipt=$receiptPath; sha256=(Get-FileHash -LiteralPath $receiptPath -Algorithm SHA256).Hash.ToLowerInvariant()
        } | ConvertTo-Json -Compress
    }
}
