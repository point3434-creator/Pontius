$ErrorActionPreference = 'Stop'
$root = 'D:\Pontius-worktrees\eval-runner-consolidation'
$scratch = 'D:\Pontius\tmp\witness-distill-review-01'
$id = Get-Content -Raw "$root\docs\research\river-witness-distillation-r001\identity.json" | ConvertFrom-Json
$plan = Get-Content -Raw "$root\docs\research\river-witness-distillation-r001\plan.json" | ConvertFrom-Json
$freeze = Get-Content -Raw "$root\docs\research\river-witness-distillation-r001\freeze-manifest.json" | ConvertFrom-Json
$checks = @()
foreach ($binding in @(
    @{name='identity';base=$root;map=$id.sha256},
    @{name='freeze';base="$root\docs\research\river-witness-distillation-r001";map=$freeze},
    @{name='sources';base=$root;map=$plan.sources},
    @{name='training';base=$plan.training.directory;map=$plan.training.files}
)) {
    foreach ($entry in $binding.map.PSObject.Properties) {
        $actual = (Get-FileHash -Algorithm SHA256 -LiteralPath (Join-Path $binding.base $entry.Name)).Hash.ToLower()
        $checks += [pscustomobject]@{binding=$binding.name;path=$entry.Name;expected=$entry.Value;actual=$actual;matches=($actual -eq $entry.Value)}
    }
}
$checks | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath "$scratch\identity-final.json"
if (@($checks | Where-Object {-not $_.matches}).Count) { throw 'Identity drift' }
$initial = Get-Content -Raw -LiteralPath "$scratch\identity-initial.json" | ConvertFrom-Json
if (($checks | ConvertTo-Json -Depth 4 -Compress) -ne ($initial | ConvertTo-Json -Depth 4 -Compress)) { throw 'Identity changed during review' }
$checks | Group-Object binding | Select-Object Name,Count
