$ErrorActionPreference='Stop'
$taskRoot='D:\Pontius\tmp\v0a-evaluation-source-r001'
$target=Join-Path $taskRoot 'capture-census.py'
if(Test-Path -LiteralPath $target){throw 'Preserve census observer'}
[IO.File]::Copy((Join-Path $PSScriptRoot 'capture-evaluation-census.py'),$target,$false)
foreach($slot in @('311','314')){
 foreach($population in @('test','production')){
  & (Join-Path $taskRoot 'run-source-snapshot.ps1') -RunName "baseline-census-$population" -Slot $slot -ExactCandidate -PythonArgs @($target,$population)
 }
}
