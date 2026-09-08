$ErrorActionPreference = 'Stop'
$taskRoot='D:\Pontius\tmp\v0a-baseline-watch-opening-r001'
$packet=Join-Path $taskRoot 'packets\r001'
$gitExe='C:\Program Files\Git\cmd\git.exe'
function Git([string[]]$Arguments) {
    $value=& $gitExe --no-replace-objects -c safe.directory=D:/Pontius -C D:/Pontius @Arguments
    if($LASTEXITCODE -ne 0){throw 'Git command failed; inspect retained state before any continuation'}
    return $value
}
function Save([string]$Name,$Value) {
    $bytes=[Text.UTF8Encoding]::new($false).GetBytes((($Value|ConvertTo-Json -Depth 8).Replace("`r`n","`n")+"`n"))
    $f=[IO.File]::Open((Join-Path $packet $Name),[IO.FileMode]::CreateNew,[IO.FileAccess]::Write)
    try{$f.Write($bytes,0,$bytes.Length);$f.Flush($true)}finally{$f.Dispose()}
}
foreach($name in @('authorization.json','commit-result.json')){
    if(Test-Path -LiteralPath (Join-Path $packet $name)){throw "Existing adoption state: $name"}
}
$id=Get-Content -Raw -LiteralPath (Join-Path $packet 'candidate.json')|ConvertFrom-Json
if($id.commit -ne '21bf52adce0c9afaa88971a12ab4c6b929d62e9f' -or
   $id.manifest_sha256 -ne 'deaa1f8fb274bf198bb450bc4d7952849f3509cecd89d52beed76532ed396581'){
   throw 'Approval identity mismatch'
}
& (Join-Path $taskRoot 'check-candidate.ps1') -Round r001
foreach($pair in @(
    @('checks\final-acceptance-summary.json','30c2a349f74173b1d885a27385e7c4b1b0c4f14826452670b0c4b81d3356f6a8'),
    @('reviews\review-a.md','11abc3709fae7011d42627d005dd36971e978af18d5dab63f51859be20468f10'),
    @('reviews\review-b.md','48f040a329ac127f206d4fa6a59cf8ee49347933bf738cf9804275a803512db3'))){
    if((Get-FileHash -LiteralPath (Join-Path $packet $pair[0])).Hash.ToLowerInvariant() -ne $pair[1]){throw 'Acceptance changed'}
}
if((Git @('branch','--show-current')) -ne 'master'){throw 'Wrong primary branch'}
$remote=Git @('ls-remote','--exit-code','origin','refs/heads/master')
if(($remote -split '\s+')[0] -ne $id.base){throw 'Remote advanced'}
Save 'authorization.json' ([ordered]@{user_message='I agree to all';decision='ADR-0507';
    title='Permit one baseline watch demonstration';approved_candidate=$id.commit;
    manifest_sha256=$id.manifest_sha256;expected_parent=$id.base;expected_tree=$id.tree;
    actions=@('incorporate exact two metadata blobs','commit exact decision','push to origin',
    'one supervised seeded generation, receipt validation and at most one three-hand baseline-rules-v1 automatic text session');
    retries=0;private_packet_export_authorized=$false;timestamp_utc=[DateTime]::UtcNow.ToString('o')})
$paths=@('docs/decisions/ADR-0507-permit-one-baseline-watch-demonstration.md','STATUS.md')
foreach($relative in $paths){
    $from=Join-Path $packet "files\$relative"; $to=Join-Path D:/Pontius $relative
    Copy-Item -LiteralPath $from -Destination $to
    if((Get-FileHash -LiteralPath $from).Hash -ne (Get-FileHash -LiteralPath $to).Hash){throw 'Adopted bytes differ'}
}
Git (@('-c','core.autocrlf=false','add','--')+$paths)|Out-Null
if((Git @('write-tree')) -ne $id.tree){throw 'Staged tree differs from reviewed tree'}
Git @('diff','--cached','--check')|Out-Null
Git @('commit','-m','Permit one baseline watch demonstration')
$commit=Git @('rev-parse','HEAD')
if((Git @('rev-parse','HEAD^{tree}')) -ne $id.tree -or (Git @('rev-parse','HEAD^')) -ne $id.base){throw 'Decision identity mismatch'}
$remote=Git @('ls-remote','--exit-code','origin','refs/heads/master')
$hookPushed=(($remote -split '\s+')[0] -eq $commit)
if(-not $hookPushed){
    if(($remote -split '\s+')[0] -ne $id.base){throw 'Remote changed unexpectedly'}
    Git @('push','origin','HEAD:refs/heads/master')
    $remote=Git @('ls-remote','--exit-code','origin','refs/heads/master')
}
if(($remote -split '\s+')[0] -ne $commit -or (Git @('status','--porcelain','--untracked-files=no'))){throw 'Final remote/tree mismatch'}
Save 'commit-result.json' ([ordered]@{status='COMMITTED_AND_PUSHED';commit=$commit;tree=$id.tree;
    parent=$id.base;approved_candidate=$id.commit;manifest_sha256=$id.manifest_sha256;
    post_commit_hook_push_verified=$hookPushed;remote_master_verified=$true;tracked_and_index_clean=$true;
    exact_generation_and_demo_authorized=$true})
"COMMITTED_AND_PUSHED $commit"
