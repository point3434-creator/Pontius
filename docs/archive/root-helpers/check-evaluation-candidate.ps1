param([ValidatePattern('^r[0-9]{3}$')][string]$Round='r001')
$ErrorActionPreference='Stop'
$taskRoot='D:\Pontius\tmp\v0a-evaluation-opening-r001'
$work=Join-Path $taskRoot 'authoring'
$packet=Join-Path $taskRoot "packets\$Round"
$gitExe='C:\Program Files\Git\cmd\git.exe'
function Git([string]$Repo,[string[]]$Arguments){
 $value=& $gitExe --no-replace-objects -c "safe.directory=$($Repo.Replace('\','/'))" -C $Repo @Arguments
 if($LASTEXITCODE -ne 0){throw 'Git audit failed'}
 return $value
}
function Hash([string]$Path){(Get-FileHash -LiteralPath $Path).Hash.ToLowerInvariant()}
$id=Get-Content -Raw -LiteralPath (Join-Path $packet 'candidate.json')|ConvertFrom-Json
$base='e043f81ecec3ac16128720b42c3312bb41a4ed67'
if($id.base -ne $base -or (Git $work @('rev-parse',$id.ref)) -ne $id.commit -or
 (Git $work @('rev-parse',"$($id.commit)^")) -ne $base -or
 (Git $work @('rev-parse',"$($id.commit)^{tree}")) -ne $id.tree){throw 'Candidate identity mismatch'}
$scope=@('docs/decisions/ADR-0508-open-the-paired-local-evaluation-source-round.md',
 'docs/architecture/v0a-evaluation-r001/brief.md','docs/architecture/v0a-evaluation-r001/design.md',
 'docs/architecture/v0a-evaluation-r001/source-contract.md',
 'docs/superpowers/plans/2026-09-07-paired-local-evaluation.md','STATUS.md')
$changed=@(Git $work @('diff-tree','--no-renames','--no-commit-id','--name-only','-r',$base,$id.commit))
if($changed.Count -ne 6 -or @(Compare-Object $changed $scope).Count){throw 'Scope mismatch'}
$rows=[Collections.Generic.List[string]]::new()
foreach($path in $scope){
 $file=Join-Path $packet "files\$path"
 $blob=Git $work @('rev-parse',"$($id.commit):$path")
 if((Git $work @('hash-object','--no-filters',$file)) -ne $blob -or
 (Hash $file) -ne (Hash (Join-Path $work $path))){throw "Raw metadata mismatch: $path"}
 $bytes=[IO.File]::ReadAllBytes($file)
 if($bytes -contains 13 -or ($bytes.Length -ge 3 -and $bytes[0] -eq 239 -and $bytes[1] -eq 187 -and $bytes[2] -eq 191)){throw 'Non-LF/BOM metadata'}
 $rows.Add("$(Hash $file)  $path`n")
}
$rows.Sort([StringComparer]::Ordinal)
$manifest=[Text.Encoding]::UTF8.GetBytes(($rows -join ''))
$actual=[Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($manifest)).ToLowerInvariant()
if($actual -ne $id.manifest_sha256 -or (Hash (Join-Path $packet 'manifest.sha256')) -ne $actual){throw 'Manifest mismatch'}
$pins=@{
 'tools/check_stabilization_boundaries.py'='9cc2ae8d8e82ccc77648ade4eb79ae9c34c88a9f'
 'tools/generate_test_inventory.py'='2ac1413b0f89fa848f1ee5df0814b58dcbfa15b8'
 'tests/test-inventory.json'='c28445aa4b77a98cfd706672d955be4570b98a15'
 'tests/test-profiles.toml'='4469bf813b2e97116667c206784a7bc212f6eef5'
 'tests/test_inventory_and_profiles.py'='e71a24322878361fb2feb44437d9210cff79c89e'
 '.github/workflows/ci.yml'='3d873a2f75ff1b155bf3533583eddf971eb7790a'
 'tools/v0a_seeded_deals.py'='2963004e38c6e66f76ae9ce3bd474063eee870fe'
 'tools/v0a_table_session.py'='a5e058260fa56e29f06e38074d59dc55f420c5ee'
 'tools/v0a_table_host.py'='6ec8a162b053158203663c48e82314b10750f962'
}
foreach($path in $pins.Keys){
 if((Git $work @('rev-parse',"${base}:$path")) -ne $pins[$path] -or
 (Git $work @('hash-object','--no-filters',(Join-Path D:/Pontius $path))) -ne $pins[$path]){throw "Base/raw source pin changed: $path"}
}
if((Git D:/Pontius @('rev-parse','HEAD')) -ne $base -or
 (Git D:/Pontius @('status','--porcelain','--untracked-files=no'))){throw 'Primary drift'}
if(Test-Path -LiteralPath (Join-Path D:/Pontius $scope[0])){throw 'Primary ADR collision'}
foreach($path in @((Join-Path $taskRoot 'request.json'),(Join-Path $taskRoot 'seed-selection.json'),
 'D:/Pontius/tmp/v0a-evaluation-run-r001')){if(Test-Path -LiteralPath $path){throw 'Unexpected evaluation population state'}}
Git $work @('diff','--check',$base,$id.commit)|Out-Null
[ordered]@{status='PASS';candidate=$id.commit;base=$base;tree=$id.tree;manifest_sha256=$actual;
 exact_paths=6;raw_base_pins=9;primary_tracked_clean=$true;evaluation_population_created=$false;
 source_implementation_performed=$false;poker_payload_executed=$false}|ConvertTo-Json
