$ErrorActionPreference='Stop'
$taskRoot='D:\Pontius\tmp\v0a-evaluation-opening-r001'
$packet=Join-Path $taskRoot 'packets\r002'
foreach($name in @('run-final-gates','record-acceptance')){
 $raw=[IO.File]::ReadAllText((Join-Path $taskRoot "$name.ps1"))
 $raw=$raw.Replace("@('a',`$ReviewedASha256),@('b',`$ReviewedBSha256)","@('c',`$ReviewedASha256),@('d',`$ReviewedBSha256)")
 $raw=$raw.Replace('review_a_sha256=','review_c_sha256=').Replace('review_b_sha256=','review_d_sha256=')
 $raw=$raw.Replace('demo_launch_authorized=','evaluation_launch_authorized=')
 $target=Join-Path $taskRoot "$name-r002.ps1"
 if(Test-Path -LiteralPath $target){throw 'Preserve helper'}
 [IO.File]::WriteAllText($target,$raw.Replace("`r`n","`n"),[Text.UTF8Encoding]::new($false))
}
$checks=Join-Path $packet 'checks'
if(-not(Test-Path -LiteralPath $checks)){New-Item -ItemType Directory -Path $checks|Out-Null}
$records=@()
foreach($name in @('run-final-gates-r002.ps1','record-acceptance-r002.ps1','check-candidate.ps1','run-snapshot.ps1','freeze-local.ps1')){
 $path=Join-Path $taskRoot $name
 $records+=[ordered]@{path=$path;sha256=(Get-FileHash -LiteralPath $path).Hash.ToLowerInvariant()}
}
$out=Join-Path $checks 'coordination-inputs.json'
if(Test-Path -LiteralPath $out){throw 'Preserve inputs record'}
[IO.File]::WriteAllText($out,($records|ConvertTo-Json).Replace("`r`n","`n")+"`n",[Text.UTF8Encoding]::new($false))
'Prepared helpers only; acceptance commands remain behind both original CLEAN reviews.'
