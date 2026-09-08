$ErrorActionPreference='Stop'
$taskRoot='D:\Pontius\tmp\v0a-evaluation-opening-r001'
$packet=Join-Path $taskRoot 'packets\r002'
$gitExe='C:\Program Files\Git\cmd\git.exe'
function Git([string[]]$Arguments){
 $value=& $gitExe --no-replace-objects -c safe.directory=D:/Pontius -C D:/Pontius @Arguments
 if($LASTEXITCODE -ne 0){throw 'Git failed; inspect retained state before continuation'}
 return $value
}
function Hash([string]$Path){(Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()}
function Save([string]$Name,$Value){
 $bytes=[Text.UTF8Encoding]::new($false).GetBytes(($Value|ConvertTo-Json -Depth 8).Replace("`r`n","`n")+"`n")
 $file=[IO.File]::Open((Join-Path $packet $Name),[IO.FileMode]::CreateNew,[IO.FileAccess]::Write)
 try{$file.Write($bytes,0,$bytes.Length);$file.Flush($true)}finally{$file.Dispose()}
}
foreach($name in @('authorization.json','commit-result.json')){
 if(Test-Path -LiteralPath (Join-Path $packet $name)){throw "Preserve existing adoption state: $name"}
}
$id=Get-Content -Raw -LiteralPath (Join-Path $packet 'candidate.json')|ConvertFrom-Json
if($id.commit -ne 'cb47f22c3bf140351564316344d6596a1a81d433' -or
 $id.manifest_sha256 -ne 'bf109d6dee99f76f860c5e0eeefa0c18c3bdcf82844cd6279dc4b04ca6789025' -or
 $id.tree -ne '09d9a3bce37071bab9e8679e9924221aba075dbf' -or
 $id.base -ne 'e043f81ecec3ac16128720b42c3312bb41a4ed67'){throw 'Approval identity mismatch'}
& (Join-Path $taskRoot 'check-candidate.ps1') -Round r002
foreach($pair in @(
 @('checks\final-acceptance-summary.json','580c1f2b06546114baae147c153e405b472790f1d622c5c531be55ee31bead4e'),
 @('reviews\review-c.md','52be9cd7964ce3d7b3beba711e732de50bc8ae25333e6eee61339cd48d018d6f'),
 @('reviews\review-d.md','ea9a4cabed2133b4647ba1800f43aa2f7f775659079a048574b954916e985d52'))){
 if((Hash (Join-Path $packet $pair[0])) -ne $pair[1]){throw 'Reviewed acceptance record changed'}
}
$acceptance=Get-Content -Raw -LiteralPath (Join-Path $packet 'checks\final-acceptance-summary.json')|ConvertFrom-Json
foreach($command in $acceptance.commands){
 if((Hash $command.receipt) -ne $command.receipt_sha256){throw 'Original command receipt changed'}
}
$paths=@('docs/decisions/ADR-0508-open-the-paired-local-evaluation-source-round.md',
 'docs/architecture/v0a-evaluation-r001/brief.md',
 'docs/architecture/v0a-evaluation-r001/design.md',
 'docs/architecture/v0a-evaluation-r001/source-contract.md',
 'docs/superpowers/plans/2026-09-07-paired-local-evaluation.md','STATUS.md')
foreach($relative in $paths){
 if($relative -ne 'STATUS.md' -and (Test-Path -LiteralPath (Join-Path D:/Pontius $relative))){throw "Adoption path collision: $relative"}
}
if((Git @('branch','--show-current')) -ne 'master'){throw 'Primary branch changed'}
if((Git @('remote','get-url','--push','origin')) -ne 'https://github.com/point3434-creator/Pontius.git'){throw 'Remote destination changed'}
$remote=Git @('ls-remote','--exit-code','origin','refs/heads/master')
if(($remote -split '\s+')[0] -ne $id.base){throw 'Remote advanced'}
Save 'authorization.json' ([ordered]@{user_message='Commit and push';decision='ADR-0508';
 title='Open the paired local evaluation source round';approved_candidate=$id.commit;
 manifest_sha256=$id.manifest_sha256;expected_parent=$id.base;expected_tree=$id.tree;
 actions=@('incorporate exact six reviewed documentation blobs','commit exact decision','push to origin/master');
 actual_evaluation_authorized=$false;timestamp_utc=[DateTime]::UtcNow.ToString('o')})
foreach($relative in $paths){
 $from=Join-Path $packet "files\$relative"
 $to=Join-Path D:/Pontius $relative
 New-Item -ItemType Directory -Force -Path (Split-Path -Parent $to)|Out-Null
 [IO.File]::Copy($from,$to,($relative -eq 'STATUS.md'))
 if((Hash $from) -ne (Hash $to)){throw 'Adopted raw bytes differ'}
}
Git (@('-c','core.autocrlf=false','add','--')+$paths)|Out-Null
if((Git @('write-tree')) -ne $id.tree){throw 'Staged tree differs from reviewed tree'}
Git @('diff','--cached','--check')|Out-Null
Git @('commit','-m','Open the paired local evaluation source round')
$commit=Git @('rev-parse','HEAD')
if((Git @('rev-parse','HEAD^{tree}')) -ne $id.tree -or
 (Git @('rev-parse','HEAD^')) -ne $id.base){throw 'Decision identity mismatch'}
$remote=Git @('ls-remote','--exit-code','origin','refs/heads/master')
$hookPushed=(($remote -split '\s+')[0] -eq $commit)
if(-not $hookPushed){
 if(($remote -split '\s+')[0] -ne $id.base){throw 'Remote changed unexpectedly'}
 Git @('push','origin','HEAD:refs/heads/master')
 $remote=Git @('ls-remote','--exit-code','origin','refs/heads/master')
}
if(($remote -split '\s+')[0] -ne $commit -or
 (Git @('status','--porcelain','--untracked-files=no'))){throw 'Final remote or tracked-state mismatch'}
Save 'commit-result.json' ([ordered]@{status='COMMITTED_AND_PUSHED';commit=$commit;tree=$id.tree;
 parent=$id.base;approved_candidate=$id.commit;manifest_sha256=$id.manifest_sha256;
 post_commit_hook_push_verified=$hookPushed;remote_master_verified=$true;
 tracked_and_index_clean=$true;source_opening_adopted=$true;
 source_implementation_performed=$false;actual_evaluation_executed=$false})
"COMMITTED_AND_PUSHED $commit"
