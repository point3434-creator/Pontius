$ErrorActionPreference = 'Stop'
$taskRoot = 'D:\Pontius\tmp\v0a-baseline-watch-opening-r001'
$oldRoot = 'D:\Pontius\tmp\v0a-seeded-watch-opening-r001'
$work = Join-Path $taskRoot 'authoring'
$demoRoot = 'D:\Pontius\tmp\v0a-baseline-watch-run-r001'
$gitExe = 'C:\Program Files\Git\cmd\git.exe'
$base = '0363bd50c1626f13d2e357f7ca527713bbdae059'
$enc = [Text.UTF8Encoding]::new($false)
function Save-New([string]$Path,[string]$Text) {
    $bytes=$enc.GetBytes($Text.Replace("`r`n","`n"))
    $f=[IO.File]::Open($Path,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write)
    try {$f.Write($bytes,0,$bytes.Length);$f.Flush($true)} finally {$f.Dispose()}
}
foreach ($name in @('authoring','seed-selection.json','request.json','seed-intent.json')) {
    if (Test-Path -LiteralPath (Join-Path $taskRoot $name)) {throw "Retain unexpected state: $name"}
}
if (Test-Path -LiteralPath $demoRoot) {throw 'Run root appeared'}
$head=& $gitExe --no-replace-objects -c safe.directory=D:/Pontius -C D:/Pontius rev-parse HEAD
if ($LASTEXITCODE -ne 0 -or $head -ne $base) {throw 'Primary base drift'}
$dirty=& $gitExe --no-replace-objects -c safe.directory=D:/Pontius -C D:/Pontius status --porcelain --untracked-files=no
if ($LASTEXITCODE -ne 0 -or $dirty) {throw 'Primary tracked drift'}
Save-New (Join-Path $taskRoot 'seed-intent.json') ((@{method='One .NET RandomNumberGenerator.GetBytes(32) call';utc=[DateTime]::UtcNow.ToString('o');reroll_permitted=$false;cards_generated=$false}|ConvertTo-Json)+"`n")
$seed=[Convert]::ToHexString([Security.Cryptography.RandomNumberGenerator]::GetBytes(32)).ToLowerInvariant()
Save-New (Join-Path $taskRoot 'seed-selection.json') (([ordered]@{seed=$seed;hand_count=3;method='One .NET RandomNumberGenerator.GetBytes(32) call';schedule_generated=$false;cards_observed=$false;reroll_permitted=$false}|ConvertTo-Json)+"`n")
$request='{"hand_count":3,"seed":"'+$seed+'","version":"pontius-v0a-seeded-deals-request-v1"}'+"`n"
Save-New (Join-Path $taskRoot 'request.json') $request
if ($enc.GetByteCount($request) -ne 139) {throw 'Request length'}
$requestHash=(Get-FileHash -LiteralPath (Join-Path $taskRoot 'request.json')).Hash.ToLowerInvariant()
& $gitExe --no-replace-objects -c safe.directory=D:/Pontius -c safe.directory=D:/Pontius/.git clone --quiet --no-hardlinks --no-checkout D:/Pontius $work
if ($LASTEXITCODE -ne 0) {throw 'Authoring clone failed; retain seed'}
& $gitExe --no-replace-objects -C $work -c core.autocrlf=false checkout --quiet --detach $base
if ($LASTEXITCODE -ne 0) {throw 'Authoring checkout failed'}
$sessionHash=(Get-FileHash -LiteralPath (Join-Path $work 'tools/v0a_table_session.py')).Hash.ToLowerInvariant()
function Adapt([string]$Text) {
    $Text=$Text.Replace('v0a-seeded-watch','v0a-baseline-watch').Replace('ADR-0504','ADR-0507')
    $Text=$Text.Replace('permit-one-seeded-watch-demonstration','permit-one-baseline-watch-demonstration')
    $Text=$Text.Replace('81187c71c50e83126f7222c053780f8be524d4fa',$base)
    $Text=$Text.Replace('64544b2c06f1056467f7aff5033eead6f7845ba43ca03afbe4508ca741d249de',$seed)
    $Text=$Text.Replace('83f34fd9bdd0cc3cf066cac4cdba6a623b8479faf78425265babf8a3c743bd4c',$requestHash)
    $Text=$Text.Replace('13b98563a92f1d2d78116d4efa2e6d4b15f491d623397166b3b1618e5276ef09',$sessionHash)
    $Text=$Text.Replace('pontius-v0a-table-session-v1-correctness-seeded-watch-001','pontius-v0a-table-session-v2-correctness-baseline-watch-001')
    $Text=$Text.Replace('^r00[12]$','^r[0-9]{3}$')
    return $Text.Replace("`r`n","`n")
}
$adr=Adapt ([IO.File]::ReadAllText('D:\Pontius\docs\decisions\ADR-0504-permit-one-seeded-watch-demonstration.md'))
$adr=$adr.Replace('Permit one seeded watch demonstration','Permit one baseline watch demonstration').Replace('- Date: 2026-09-06','- Date: 2026-09-07').Replace('- Follows: ADR-0503','- Follows: ADR-0506')
$adr=$adr.Replace('Authorize one seeded watch demo; formal operation/research closed','Authorize one baseline watch demo; formal operation/research closed')
$adr=$adr.Replace('the sealed seeded-deal generator to the sealed watch-first session. Save three','the sealed seeded-deal generator to the accepted baseline-rules-v1 session. Save three')
$adr=$adr.Replace('This is visible product behavior, not correctness acceptance or a strength result.','The baseline uses the accepted fixed-rule provider with blueprint fallback. This is' + "`n" + 'visible product behavior, not correctness acceptance or a strength result.')
$adr=$adr.Replace('ADR-0500 and ADR-0503, and to ADR-0485', 'ADR-0500, ADR-0503 and ADR-0506, and to ADR-0485')
$adr=$adr.Replace("ADR-0501's earlier`nf ixed", "ADR-0501's earlier`nf ixed")
$adr=$adr.Replace("ADR-0501's earlier`nfixed demonstration is completed and consumed; this does not repeat its identity.","ADR-0501 and ADR-0504's earlier`ndemonstrations are completed and consumed; neither identity is reused.")
$adr=$adr.Replace("--format text`n--auto","--strategy baseline-rules-v1`n--format text`n--auto")
$adr=$adr.Replace("The inherited child`nsuffixes end in correctness-table-seeded-watch-001-h01, -h02 and -h03.","The inherited v2 event child IDs are`npontius-v0a-event-interface-v2-correctness-table-baseline-watch-001-h01, -h02 and -h03.`nHost result IDs are pontius-v0a-table-host-v2-correctness-baseline-watch-001-h01,`n-h02 and -h03. These follow the accepted source's prefix removal and hand suffixing.")
$adr=$adr.Replace("The empty blueprint uses legal passive fallback;`nthis demonstration introduces no trained policy or improved decision mechanism.","baseline-rules-v1 proposes fixed-rule actions;`nthe empty blueprint remains its admitted legal passive fallback. No trained policy`nor strategic improvement is claimed.")
$adr=$adr.Replace('One initial proposal and at most one bounded correction; stop before a third round.','Within-scope corrections may continue as new immutable reviewed rounds; no inherited' + "`n" + 'one-correction cap applies. Source changes or expanded authority need a separate task.')
Save-New (Join-Path $work 'docs/decisions/ADR-0507-permit-one-baseline-watch-demonstration.md') $adr
foreach ($name in @('freeze-local.ps1','run-snapshot.ps1','prepare-status.ps1','check-candidate.ps1','run-final-gates.ps1','record-acceptance.ps1')) {
    Save-New (Join-Path $taskRoot $name) (Adapt ([IO.File]::ReadAllText((Join-Path $oldRoot $name))))
}
$plan=(Adapt ([IO.File]::ReadAllText((Join-Path $oldRoot 'launch-plan.json')))) | ConvertFrom-Json
$plan.session_argv += @('--strategy','baseline-rules-v1')
Save-New (Join-Path $taskRoot 'launch-plan.json') (($plan | ConvertTo-Json -Depth 6)+"`n")
Save-New (Join-Path $taskRoot 'demo-preflight.py') (Adapt ([IO.File]::ReadAllText((Join-Path $oldRoot 'demo-preflight.py'))))
Save-New (Join-Path $taskRoot 'preparation-state.json') (([ordered]@{base=$base;seed=$seed;request_sha256=$requestHash;request_bytes=139;session_cli_sha256=$sessionHash;run_root_absent=(-not(Test-Path $demoRoot));schedule_generated=$false;decision_authorized=$false;launch_authorized=$false}|ConvertTo-Json)+"`n")
Get-Content -LiteralPath (Join-Path $taskRoot 'preparation-state.json')
