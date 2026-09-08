param([Parameter(Mandatory=$true)][ValidatePattern('^r[0-9]{3}$')][string]$Round,
      [Parameter(Mandatory=$true)][ValidatePattern('^[a-z0-9]{1,8}$')][string]$CensusStage)
$ErrorActionPreference = 'Stop'
$root = 'D:/Pontius/tmp/v0a-evaluation-source-r001'
$repo = "$root/authoring"
$scripts = 'C:/Users/point/.codex/worktrees/fa55/Pontius'
$git = 'C:/Program Files/Git/cmd/git.exe'
$python = 'D:/Pontius-tools/py311/Scripts/python.exe'
foreach ($population in @('test','production')) {
    $reportPath = "$root/census-$CensusStage-$population/explained-comparison.json"
    $report = Get-Content -LiteralPath $reportPath -Raw | ConvertFrom-Json
    if (-not $report.mechanical_checks_pass -or $report.issues.Count) {
        throw 'Complete explained census comparison required before source freeze'
    }
}
& "$root/freeze-source-v3.ps1" -Round $Round | Out-Null
$packet = "$root/packets/$Round"
$identity = Get-Content -LiteralPath "$packet/candidate.json" -Raw | ConvertFrom-Json
$capture = Get-Content -LiteralPath "$root/process-temp/c-$CensusStage-t-311/census-test.json" -Raw | ConvertFrom-Json
& $git --no-replace-objects -c "safe.directory=$repo" -C $repo diff --exit-code $capture.source_commit $identity.commit
if ($LASTEXITCODE) { throw 'Final full-census candidate differs from frozen source' }
& $python -B -P "$scripts/audit-evaluation-source.py" $identity.commit $Round
if ($LASTEXITCODE) { throw 'Frozen scope/budget/raw registration audit failed' }
$evidence = @{
    runner="$root/run-records/t2-f2-full01-311.json"
    boundary="$root/run-records/bflat1-311.json"
    helper="$root/run-records/task1-fix01-green-311.json"
}
$focused = @()
foreach ($kind in @('helper','runner','boundary')) {
    $receiptPath = $evidence[$kind]
    $receipt = Get-Content -LiteralPath $receiptPath -Raw | ConvertFrom-Json
    if ($receipt.Count -ne 2 -or $receipt[-1].exit_code -ne 0) { throw "Focused $kind did not pass" }
    $paths = switch ($kind) {
        helper { @('tools/v0a_evaluation_contract.py','tests/test_v0a_evaluation_contract.py','tests/fixtures/evaluation/controls.json') }
        runner { @('tools/v0a_evaluation.py','tools/v0a_evaluation_contract.py','tests/test_v0a_evaluation_runner.py','tests/fixtures/evaluation/controls.json') }
        boundary { @('tools/v0a_evaluation.py','tools/v0a_evaluation_contract.py','tests/test_v0a_evaluation_boundary.py','tests/fixtures/evaluation/controls.json','tools/check_stabilization_boundaries.py') }
    }
    & $git --no-replace-objects -c "safe.directory=$repo" -C $repo diff --exit-code $receipt[-1].snapshot_head $identity.commit -- @paths
    if ($LASTEXITCODE) { throw "Focused $kind source differs from frozen bytes" }
    $focused += [ordered]@{kind=$kind;receipt=$receiptPath;
        sha256=(Get-FileHash $receiptPath).Hash.ToLowerInvariant();snapshot=$receipt[-1].snapshot_head;paths=$paths}
}
[IO.File]::WriteAllText("$packet/focused-evidence.json",($focused | ConvertTo-Json -Depth 5).Replace("`r`n","`n")+"`n",[Text.UTF8Encoding]::new($false))
$handoff = @"
# Whole-source independent Tier C review

Finalizer: Codex coordinator. Round kind: NEW-SURFACE, integrated source round $Round.
Repository: $repo
Ref: $($identity.ref)
Candidate: $($identity.commit)
Base: $($identity.base)
Tree: $($identity.tree)
Whole-row manifest SHA256: $($identity.manifest_sha256)

Read D:/Pontius/CLAUDE.md and docs/workflow.md, adopted ADR-0508 and all three
docs/architecture/v0a-evaluation-r001/{brief,design,source-contract}.md documents.
User ruling permits 1250 production lines and similarly small implementation budget
adjustments; all correctness, source scope, retained evidence and population limits hold.
Review the entire frozen12-path source increment independently, including both tools,
all three suites, literal fixture, four manual registrations and two generated artifacts.
Do not rely on earlier checkpoint verdicts. No implementer transcripts, task reports,
coordinator rationale or another current reviewer's findings are permitted inputs.

Only immutable packet files are implementation inputs. Verify ref/parent/tree and raw
sorted whole-row manifest; compare the twelve blobs against their native Git objects.
source.diff excludes only the two generated artifacts; review.diff is the complete diff.
source-audit.json and focused-evidence.json are mechanical evidence to challenge,
not an independent semantic verdict. Focused receipts are real actual3.11 runs bound
to named identical source files; full two-interpreter acceptance is still pending.

Before opening authored census explanations, independently inspect the complete old
and candidate census assertion chain and the exact three suite registrations. Then
read both full explained comparisons in $root/census-$CensusStage-{test,production}/,
their retained raw inputs, source-bound line maps and per-occurrence explanations.
Both test and production populations have actual3.11 then3.14 captures on one source
identity, which is byte-identical to this candidate but a distinct local snapshot commit.
Keep every old ordered row/multiplicity, stable ID and payload/grant; challenge all new
rows and mechanical line shifts. Analyzer behavior may not change. Both installed
capability hashes remain zero. These comparisons do not authorize any evaluation.

Inspect boundary controls as actual operations plus controlled triggers, including
native ownership/retention, exact reserve and final clock edges, precommit file faults,
close-after-full-bytes, delayed completion, irreversible commit and one real guard
release with failure/ambiguity. Synthetic publication records are a permitted isolated
seam, not fabricated engine outcomes. Boundary controls start zero poker sessions;
runner suite has one12-session matrix plus two real retention controls,14total.
Inspect fixed captured raw loaders, per-command native identity, complete/incomplete
metric meaning, observation prefixes, denominator integrity and saved-source drift.
Static loader controls are bounded structural checks, not general dynamic soundness.

Review all eight brief criteria, tests and independent oracles, regression scope and
engineering quality. Record concrete required defects and verification criteria,
separate optional advice, Specification PASS/FAIL, Engineering PASS/FAIL and mandatory
design verdict SOUND/STRAINED/WRONG SHAPE. CLEAN means no required correction remains.
Do not execute payloads, change source, spawn workers, commit or push. Read-only native
Git/blob/AST/hash/receipt operations are allowed. Write your own create-new initial
inventory and attributed final review only under this packet's reviews directory.
Two fresh independent reviews are required; neither sees the other's work.
"@
[IO.File]::WriteAllText("$packet/handoff.md",$handoff.Replace("`r`n","`n")+"`n",[Text.UTF8Encoding]::new($false))
New-Item -ItemType Directory -Path "$packet/reviews" | Out-Null
$identity | ConvertTo-Json
