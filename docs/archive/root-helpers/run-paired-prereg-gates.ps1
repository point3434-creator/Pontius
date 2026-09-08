$ErrorActionPreference = 'Stop'
$packet = 'D:/Pontius-handoffs/v0a-paired-prereg/r001'
$candidate = '4c7882752bd93e56a05dba513c035b02ca2f2325'
$manifest = 'dd8e0cde6d91326e4ec1ef45ce73bccd1d8bdf3a1a0f5fe2268039fc91baf324'
foreach ($name in @('review-a.md', 'review-b.md')) {
    $report = Get-Content -LiteralPath "$packet/reviews/$name" -Raw
    if (-not $report.Contains($candidate) -or -not $report.Contains($manifest)) {
        throw "Review identity missing: $name"
    }
}
if (Test-Path -LiteralPath 'D:/Pontius/tmp/v0a-paired-rehearsal-run-001') {
    throw 'Reserved rehearsal root must remain absent'
}
$runner = 'D:/Pontius/tmp/v0a-paired-prereg-r001/run-prereg-snapshot.ps1'
& $runner -RunName status-check -Slot 311 -PythonArgs @('-m', 'pontius.status_generation', '--check') -ExactCandidate -Candidate $candidate
& $runner -RunName status-tests -Slot 311 -PythonArgs @('tests/test_status_generation.py') -ExactCandidate -Candidate $candidate
& $runner -RunName status-check -Slot 314 -PythonArgs @('-m', 'pontius.status_generation', '--check') -ExactCandidate -Candidate $candidate
& $runner -RunName status-tests -Slot 314 -PythonArgs @('tests/test_status_generation.py') -ExactCandidate -Candidate $candidate
