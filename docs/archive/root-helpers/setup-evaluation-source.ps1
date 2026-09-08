$ErrorActionPreference='Stop'
$taskRoot='D:\Pontius\tmp\v0a-evaluation-source-r001'
$work=Join-Path $taskRoot 'authoring'
$gitExe='C:\Program Files\Git\cmd\git.exe'
$base='34616938c708b1ca306b9d8a17b9d98e2f9e451f'
if(Test-Path -LiteralPath $taskRoot){throw 'Existing source task; inspect rather than recreate'}
New-Item -ItemType Directory -Path $taskRoot|Out-Null
& $gitExe --no-replace-objects -c safe.directory=D:/Pontius -c safe.directory=D:/Pontius/.git clone --quiet --no-hardlinks D:/Pontius $work
if($LASTEXITCODE -ne 0){throw 'Clone failed'}
& $gitExe --no-replace-objects -C $work -c core.autocrlf=false checkout --quiet -b codex/paired-evaluation-source $base
if($LASTEXITCODE -ne 0){throw 'Checkout failed'}
$plan='docs/superpowers/plans/2026-09-07-paired-local-evaluation.md'
$sdd=Join-Path $work '.superpowers\sdd\2026-09-07-paired-local-evaluation'
New-Item -ItemType Directory -Path $sdd|Out-Null
[IO.File]::WriteAllText((Join-Path $work '.superpowers\sdd\.gitignore'),"*`n",[Text.UTF8Encoding]::new($false))
$ledger=@"
# SDD ledger - plan: $plan

Source task v0a-evaluation-source-r001. Accepted source opening $base.
Pinned semantic B remains e043f81ecec3ac16128720b42c3312bb41a4ed67.
User requested Let's proceed after exact ADR-0508 adoption. No source seal commit or
actual evaluation is authorized. Repository retention, finite controls, fresh snapshots,
two independent Tier C reviews and initial plus three correction rounds govern.

## Preflight task/interface scan

| Task or shared seam | Producer / consumer | Assessment |
| --- | --- | --- |
| Task 1 | request/matrix/observer/reducer; literal finite fixtures/tests | Consistent with accepted contract; no I/O or poker imports in helper |
| Task 2 | CLI/admission/native owner/publication; real runner controls | Consumes Task 1's fixed interfaces; original tools unchanged |
| Task 3 | boundary faults and six registration exceptions | Consumes integrated tools and three finite test suites; census must stay explained |
| Tasks 1/2 | fixed schemas, build_matrix/observe_trial/reduce_trials | Task 1 owns helper and controls.json; Task 2 reads them without changing signatures |
| Tasks 1/3 | reducer fixtures and reported suite inventory | Task 3 may add boundary tests, not silently widen fixture population |
| Tasks 2/3 | real native/file seams and read_completed | Controlled triggers only; real operations and independent outcomes stay intact |

Ruling: Use a fresh D-local implementation clone and native PowerShell equivalents of
SDD workspace/brief packaging - accepted source admission requires D-local paths and
absolute Git; existing C worktree is retained at its prior base. Cost if wrong: extra
retained coordination clone, no change to accepted source or evidence population.
Ruling: Repository rules override generic skill commits, deletion, five-round and
park-required-findings advice - retain all records, no ceremonial commit until exact
approval, maximum initial plus three corrections, no unresolved required findings.
Cost if wrong: bounded additional work/decision escalation, no weakened acceptance.

Task 1: pending - strict contract, paired matrix and observable report reducer.
Task 2: pending - CLI, native lifetime and retained publication.
Task 3: pending - boundary controls, registration and source acceptance.
Baseline/iteration commands go through task-root/run-source-snapshot.ps1 only.
"@
[IO.File]::WriteAllText((Join-Path $sdd 'progress.md'),$ledger.Replace("`r`n","`n")+"`n",[Text.UTF8Encoding]::new($false))
$planText=[IO.File]::ReadAllText((Join-Path $work $plan))
$global=$planText.Substring(0,$planText.IndexOf('## Task 1:'))
foreach($n in 1..3){
 $start=$planText.IndexOf("## Task ${n}:")
 $end=if($n -lt 3){$planText.IndexOf("## Task $($n+1):")}else{$planText.IndexOf('## Accepted-schema')}
 $body=$global+$planText.Substring($start,$end-$start)+"`nRead the accepted source-contract.md in full and applicable CLAUDE/workflow. No source changes outside your assigned files. No commits/push/deletion/subagents. Run only named finite controls in fresh snapshots through task-root/run-source-snapshot.ps1. Record independent expected cases before implementation; actual floor first. Full report goes beside this brief as task-$n-report.md. All evidence is retained.`n"
 [IO.File]::WriteAllText((Join-Path $sdd "task-$n-brief.md"),$body.Replace("`r`n","`n"),[Text.UTF8Encoding]::new($false))
}
[IO.File]::Copy((Join-Path $PSScriptRoot 'run-evaluation-source-snapshot.ps1'),(Join-Path $taskRoot 'run-source-snapshot.ps1'),$false)
[ordered]@{authoring=$work;branch='codex/paired-evaluation-source';base=$base;ledger=(Join-Path $sdd 'progress.md')}|ConvertTo-Json
