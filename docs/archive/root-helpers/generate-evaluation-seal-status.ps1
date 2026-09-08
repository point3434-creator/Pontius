$ErrorActionPreference = 'Stop'
$taskRoot = 'D:/Pontius/tmp/v0a-evaluation-seal-r001'
$harness = Join-Path $taskRoot 'run-seal-snapshot.ps1'
& $harness -RunName 'mgen1' -Slot 311 -PythonArgs @('-m','pontius.status_generation') | Out-Null
$receiptPath = Join-Path $taskRoot 'run-records/mgen1-311.json'
$records = Get-Content -Raw -LiteralPath $receiptPath | ConvertFrom-Json
if ($records.Count -ne 2 -or $records[-1].exit_code -ne 0) { throw 'Generation failed' }
$from = Join-Path $records[-1].snapshot 'STATUS.md'
$to = 'D:/Pontius/tmp/v0a-evaluation-source-r001/authoring/STATUS.md'
$raw = [IO.File]::ReadAllBytes($from)
$text = [Text.Encoding]::UTF8.GetString($raw).Replace("`r`n","`n")
if ($text.Contains("`r") -or $text.StartsWith([string][char]0xfeff)) { throw 'Generated status encoding' }
$before = (Get-FileHash -LiteralPath $to -Algorithm SHA256).Hash.ToLowerInvariant()
$normalized = [Text.Encoding]::UTF8.GetBytes($text)
[IO.File]::WriteAllBytes($to,$normalized)
$record = [ordered]@{
    receipt=$receiptPath; receipt_sha256=(Get-FileHash -LiteralPath $receiptPath -Algorithm SHA256).Hash.ToLowerInvariant();
    snapshot=$records[-1].snapshot; snapshot_head=$records[-1].snapshot_head;
    source=$from; generated_raw_sha256=(Get-FileHash -LiteralPath $from -Algorithm SHA256).Hash.ToLowerInvariant();
    destination=$to; previous_sha256=$before;
    copied_sha256=(Get-FileHash -LiteralPath $to -Algorithm SHA256).Hash.ToLowerInvariant();
    transformation='Only generated Windows CRLF to governance LF; no content edit';
    standing='Generated metadata only; exact-candidate final checks remain pending'
}
$recordPath = Join-Path $taskRoot 'status-generation-copy.json'
if (Test-Path -LiteralPath $recordPath) { throw 'Retain original copy record' }
[IO.File]::WriteAllText($recordPath,($record|ConvertTo-Json).Replace("`r`n","`n")+"`n",[Text.UTF8Encoding]::new($false))
$record | ConvertTo-Json
