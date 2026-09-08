param([Parameter(Mandatory=$true)][ValidatePattern('^[a-zA-Z0-9_-]+$')][string]$RunName,
 [ValidateSet('311','314')][string]$Slot='311',
 [Parameter(Mandatory=$true)][string[]]$PythonArgs,
 [switch]$ExpectFailure,[switch]$ExactCandidate,
 [ValidatePattern('^[0-9a-f]{40}$')][string]$Candidate='34616938c708b1ca306b9d8a17b9d98e2f9e451f')
$ErrorActionPreference='Stop'
$taskRoot='D:\Pontius\tmp\v0a-evaluation-source-r001'
$work=Join-Path $taskRoot 'authoring'
$gitExe='C:\Program Files\Git\cmd\git.exe'
$pythonExe=if($Slot -eq '311'){'D:\Pontius-tools\py311\Scripts\python.exe'}else{'D:\Pontius\.venv\Scripts\python.exe'}
$snapshot=Join-Path $taskRoot "snapshots\$RunName-$Slot"
if(Test-Path -LiteralPath $snapshot){throw 'Snapshot already exists; retain it'}
if('discover' -in $PythonArgs -or ($PythonArgs|Where-Object{$_ -match '[?*]'})){throw 'Explicit named controls only'}
$allowed=@('tools/v0a_evaluation.py','tools/v0a_evaluation_contract.py',
 'tests/test_v0a_evaluation_contract.py','tests/test_v0a_evaluation_runner.py','tests/test_v0a_evaluation_boundary.py',
 'tests/fixtures/evaluation/controls.json','tools/check_stabilization_boundaries.py',
 'tools/generate_test_inventory.py','tests/test-inventory.json','tests/test-profiles.toml',
 'tests/test_inventory_and_profiles.py','.github/workflows/ci.yml')
function Git([string]$Repo,[string[]]$Arguments){
 $value=& $gitExe --no-replace-objects -c "safe.directory=$($Repo.Replace('\','/'))" -C $Repo @Arguments
 if($LASTEXITCODE -ne 0){throw 'Git operation failed'}
 return $value
}
$head=Git $work @('rev-parse','HEAD')
if($head -ne '34616938c708b1ca306b9d8a17b9d98e2f9e451f'){throw 'Authoring base drift'}
if(-not $ExactCandidate){
 $changed=@(Git $work @('diff','--name-only',$head))+@(Git $work @('ls-files','--others','--exclude-standard'))
 foreach($path in $changed){if($path -and $path -notin $allowed){throw "Out-of-scope source: $path"}}
 $savedIndex=[Environment]::GetEnvironmentVariable('GIT_INDEX_FILE')
 $tempIndex=Join-Path $taskRoot ("index-"+[guid]::NewGuid().ToString('N'))
 try{
  $env:GIT_INDEX_FILE=$tempIndex
  Git $work @('read-tree',$head)|Out-Null
  $present=@($allowed|Where-Object{Test-Path -LiteralPath (Join-Path $work $_)})
  Git $work (@('-c','core.autocrlf=false','add','--')+$present)|Out-Null
  $tree=Git $work @('write-tree')
  $Candidate=Git $work @('-c','user.name=Codex','-c','user.email=codex@localhost','commit-tree',$tree,'-p',$head,'-m',"Retained iteration snapshot $RunName-$Slot (not a decision)")
  Git $work @('update-ref',"refs/heads/snapshots/evaluation/$RunName-$Slot",$Candidate,('0'*40))|Out-Null
 }finally{
  if($null -eq $savedIndex){Remove-Item Env:GIT_INDEX_FILE -ErrorAction SilentlyContinue}else{$env:GIT_INDEX_FILE=$savedIndex}
  if(Test-Path -LiteralPath $tempIndex){Remove-Item -LiteralPath $tempIndex}
 }
}
New-Item -ItemType Directory -Force -Path (Split-Path -Parent $snapshot)|Out-Null
& $gitExe --no-replace-objects -c "safe.directory=$($work.Replace('\','/'))" -c "safe.directory=$($work.Replace('\','/'))/.git" clone --quiet --no-hardlinks --no-checkout $work $snapshot
if($LASTEXITCODE -ne 0){throw 'Snapshot clone failed'}
Git $snapshot @('-c','core.autocrlf=false','checkout','--quiet','--detach',$Candidate)|Out-Null
if((Git $snapshot @('rev-parse','HEAD')) -ne $Candidate -or (Git $snapshot @('status','--porcelain'))){throw 'Snapshot identity/cleanliness failed'}
$runTemp=Join-Path $taskRoot "process-temp\$RunName-$Slot"
New-Item -ItemType Directory -Path $runTemp -Force|Out-Null
$version=if($Slot -eq '311'){'(3, 11, 15)'}else{'(3, 14, 6)'}
$probe="import sys,pathlib; assert sys.implementation.name=='cpython'; assert sys.version_info[:3]==$version; assert sys.flags.safe_path and sys.dont_write_bytecode; assert pathlib.Path.cwd()==pathlib.Path(sys.argv[1]); print(sys.version); print(sys.executable); print(pathlib.Path.cwd())"
$vectors=@();$vectors+=,@('-B','-P','-c',$probe,$snapshot);$vectors+=,(@('-B','-P')+$PythonArgs)
$records=@()
foreach($vector in $vectors){
 $info=[Diagnostics.ProcessStartInfo]::new();$info.FileName=$pythonExe;$info.WorkingDirectory=$snapshot
 $info.UseShellExecute=$false;$info.CreateNoWindow=$true;$info.RedirectStandardOutput=$true;$info.RedirectStandardError=$true
 $info.Environment.Clear()
 foreach($key in @('SystemRoot','WINDIR','SystemDrive','COMSPEC','USERPROFILE','APPDATA','LOCALAPPDATA')){
  $value=[Environment]::GetEnvironmentVariable($key);if($value){$info.Environment[$key]=$value}
 }
 $info.Environment['TEMP']=$runTemp;$info.Environment['TMP']=$runTemp
 $info.Environment['PONTIUS_GIT']=$gitExe;$info.Environment['PYTHONPATH']=Join-Path $snapshot 'src'
 $info.Environment['PYTHONNOUSERSITE']='1';$info.Environment['PYTHONIOENCODING']='utf-8'
 foreach($arg in $vector){$info.ArgumentList.Add($arg)}
 $started=[DateTime]::UtcNow.ToString('o');$proc=[Diagnostics.Process]::Start($info)
 $stdout=$proc.StandardOutput.ReadToEndAsync();$stderr=$proc.StandardError.ReadToEndAsync();$proc.WaitForExit()
 $record=[ordered]@{snapshot=$snapshot;snapshot_head=$Candidate;interpreter=$pythonExe;argv=$vector;exit_code=$proc.ExitCode;stdout=$stdout.Result;stderr=$stderr.Result;started_utc=$started;finished_utc=[DateTime]::UtcNow.ToString('o')}
 $records+=$record
 if($proc.ExitCode -ne 0){break}
}
$logDir=Join-Path $taskRoot 'run-records';New-Item -ItemType Directory -Force -Path $logDir|Out-Null
$receipt=Join-Path $logDir "$RunName-$Slot.json"
if(Test-Path -LiteralPath $receipt){throw 'Preserve existing receipt'}
[IO.File]::WriteAllText($receipt,($records|ConvertTo-Json -Depth 8).Replace("`r`n","`n")+"`n",[Text.UTF8Encoding]::new($false))
$records[-1]|ConvertTo-Json -Depth 6
"Receipt: $receipt"
if($records.Count -ne 2 -or $records[0].exit_code -ne 0){throw 'Preflight failed'}
if($ExpectFailure){if($records[-1].exit_code -eq 0){throw 'Expected RED but payload passed'}}elseif($records[-1].exit_code -ne 0){throw 'Payload failed; inspect retained receipt'}
