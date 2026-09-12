$ErrorActionPreference = 'Stop'
$root = 'D:\Pontius-worktrees\eval-runner-consolidation'
$packet = "$root\docs\research\river-witness-distillation-r001"
$scratch = 'D:\Pontius\tmp\witness-distill-review-01'
$result = @()
$prior = Get-Content -Raw -LiteralPath "$scratch\identity-final.json" | ConvertFrom-Json
$plan = Get-Content -Raw -LiteralPath "$packet\plan.json" | ConvertFrom-Json
foreach ($entry in $prior) {
    $base = if ($entry.binding -eq 'training') {$plan.training.directory} elseif ($entry.binding -eq 'freeze') {$packet} else {$root}
    $actual = (Get-FileHash -Algorithm SHA256 -LiteralPath (Join-Path $base $entry.path)).Hash.ToLower()
    $result += [pscustomobject]@{binding=$entry.binding;path=$entry.path;expected=$entry.actual;actual=$actual;matches=($entry.actual -eq $actual)}
}
$review = Get-Content -Raw -LiteralPath "$scratch\review-manifest.json" | ConvertFrom-Json
foreach ($entry in $review.PSObject.Properties) {
    $actual = (Get-FileHash -Algorithm SHA256 -LiteralPath (Join-Path $scratch $entry.Name)).Hash.ToLower()
    $result += [pscustomobject]@{binding='original-review';path=$entry.Name;expected=$entry.Value;actual=$actual;matches=($entry.Value -eq $actual)}
}
$originalManifest = (Get-FileHash -Algorithm SHA256 -LiteralPath "$scratch\review-manifest.json").Hash.ToLower()
if ($originalManifest -ne 'ce26b6828ac225fe191a18884b59a5f360e9798445053d031433ad299e5455d8') {throw 'Original review manifest changed'}
$accounting = Get-Content -Raw -LiteralPath "$packet\accounting\manifest.json" | ConvertFrom-Json
foreach ($entry in $accounting.PSObject.Properties) {
    $actual = (Get-FileHash -Algorithm SHA256 -LiteralPath (Join-Path "$packet\accounting" $entry.Name)).Hash.ToLower()
    $result += [pscustomobject]@{binding='accounting';path=$entry.Name;expected=$entry.Value;actual=$actual;matches=($entry.Value -eq $actual)}
}
$result | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath "$scratch\followup\preservation-final.json"
if (@($result | Where-Object {-not $_.matches}).Count) {throw 'Preservation or accounting mismatch'}
$result | Group-Object binding | Select-Object Name,Count
[pscustomobject]@{
    original_review_manifest_sha256=$originalManifest
    accounting_manifest_sha256=(Get-FileHash -Algorithm SHA256 -LiteralPath "$packet\accounting\manifest.json").Hash.ToLower()
    current_sha256=(Get-FileHash -Algorithm SHA256 -LiteralPath "$packet\CURRENT.md").Hash.ToLower()
    controller_authorization_exists=(Test-Path -LiteralPath "$packet\controller-authorization.json")
    invocation_directory_exists=(Test-Path -LiteralPath "$packet\invocation-001")
    bound_output_exists=(Test-Path -LiteralPath $plan.output_directory)
    disposition_exists=(Test-Path -LiteralPath "$packet\disposition.md")
} | ConvertTo-Json | Set-Content -LiteralPath "$scratch\followup\entry-state.json"
