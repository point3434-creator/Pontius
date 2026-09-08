$ErrorActionPreference = 'Stop'
$packet = 'D:/Pontius-handoffs/v0a-paired-closure/r001'
$candidate = 'e80b794050a466a3f8115b640b53dca3b51816a7'
$manifest = '927d94949ce4e751afef29bc2beccb47ccf88424748f23273573e29d8143a20b'
foreach ($name in @('review-a.md', 'review-b.md')) {
    $report = Get-Content -LiteralPath "$packet/reviews/$name" -Raw
    if (-not $report.Contains($candidate) -or -not $report.Contains($manifest)) {
        throw "Review identity missing: $name"
    }
}
if (Test-Path -LiteralPath 'D:/Pontius/tmp/v0a-paired-evaluation-run-001') {
    throw 'Reserved rehearsal root must remain absent'
}
$runner = 'D:/Pontius/tmp/v0a-paired-closure-r001/run-closure-snapshot.ps1'
& $runner -RunName status-check -Slot 311 -PythonArgs @('-m', 'pontius.status_generation', '--check') -ExactCandidate -Candidate $candidate
& $runner -RunName status-tests -Slot 311 -PythonArgs @('tests/test_status_generation.py') -ExactCandidate -Candidate $candidate
& $runner -RunName status-check -Slot 314 -PythonArgs @('-m', 'pontius.status_generation', '--check') -ExactCandidate -Candidate $candidate
& $runner -RunName status-tests -Slot 314 -PythonArgs @('tests/test_status_generation.py') -ExactCandidate -Candidate $candidate
