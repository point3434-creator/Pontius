$ErrorActionPreference='Stop'
$taskRoot='D:\Pontius\tmp\v0a-evaluation-opening-r001'
$packet=Join-Path $taskRoot 'packets\r002'
$coverage=Join-Path $packet 'coverage.md'
if(Test-Path -LiteralPath $coverage){throw 'Preserve coverage'}
[IO.File]::Copy((Join-Path $PSScriptRoot 'evaluation-coverage-r002.md'),$coverage,$false)
$hash=(Get-FileHash -LiteralPath $coverage -Algorithm SHA256).Hash.ToLowerInvariant()
$handoff=@"
# Fresh blind Tier C FIX review: paired evaluation source opening r002

FIX. Finalizer: Codex coordinator. Whole six-path candidate is reviewed.
Authoring repo D:/Pontius/tmp/v0a-evaluation-opening-r001/authoring.
Ref refs/heads/review/v0a-evaluation-opening/r002.
Candidate cb47f22c3bf140351564316344d6596a1a81d433.
Base e043f81ecec3ac16128720b42c3312bb41a4ed67.
Tree 09d9a3bce37071bab9e8679e9924221aba075dbf.
Manifest SHA-256 bf109d6dee99f76f860c5e0eeefa0c18c3bdcf82844cd6279dc4b04ca6789025.
Deferred input coverage.md SHA-256 $hash.
Do not open coverage.md until your independent invariant/related-path inventory is
recorded in your own create-new initial-inventory file. Then compare and assess closure.

Read CLAUDE.md fully, docs/workflow.md/checklist, relevant PROJECT rules, then all six
raw frozen files from this packet/Git: brief/design/source-contract/plan/ADR/STATUS.
Read accepted B source/schema/Job/admission/registration contracts as necessary.
Independently verify candidate/parent/tree/scope, raw whole-row-sorted manifest, all
nine base pins, and the referenced prior disposition hash. Initial input is these
requirements and frozen source only, not author reasoning or earlier reviewer reports.

Controller approved preparing this bounded proposal. No exact commit/adoption, source
implementation or actual evaluation is approved. No population/seed is created. Source
correctness is finite and conditional on later adoption; no poker payload runs now.

Review the whole design: pair/reset/population/order/denominator semantics, native
ownership, closed raw source loading, deadlines/publication/unknown states, versioned
metric/failure extraction, exact permissions and finite controls. Require separate
specification/engineering and CLEAN/NOT CLEAN verdicts and SOUND/STRAINED/WRONG SHAPE.
Advisory design concerns stay separate from required material findings, each of which
needs a concrete failure scenario, violated contract and correction/verification.

No tests, CLI help, generator/poker imports, inventory/census, benchmarks, cards,
source edits or evaluation runs. Read-only Git/source/hash analysis only. Do not read
other current reviewers' files or author transcripts. After recording initial inventory,
open only the deferred coverage and prior required-finding report explicitly linked there.
Write attributed create-new review-c.md or review-d.md and own ledger in reviews/ as
dispatched. Include candidate/manifest and exact hashes of your original report records.
No current authoring file outside frozen input can replace a frozen review source.
This substantive correction requires a fresh session; no exposed reviewer is reused.
"@
$target=Join-Path $packet 'handoff.md'
if(Test-Path -LiteralPath $target){throw 'Preserve handoff'}
[IO.File]::WriteAllText($target,$handoff.Replace("`r`n","`n")+"`n",[Text.UTF8Encoding]::new($false))
New-Item -ItemType Directory -Path (Join-Path $packet 'reviews')|Out-Null
[ordered]@{coverage_sha256=$hash;handoff_sha256=(Get-FileHash -LiteralPath $target).Hash.ToLowerInvariant()}|ConvertTo-Json
