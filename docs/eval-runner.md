# Shared evaluation runner

Implementation scope approved by the controller on 2026-09-10; adoption is pending review.
This document is the
design, execution checklist and maintained usage guide for the consolidation; historical
solve/export/agreement packets and their consumed claims remain immutable.

## Contract

One Python 3.14 standard-library executable owns preflight, claim, child launch, capture,
journal attribution and recursive artifact inventory. It imports no Pontius code. The child
continues to own phase validation, worker Job limits, cleanup and its one journal row.
The runner neither retries nor removes a claim. Operator ownership of the checkout, inputs,
authorization and record directory remains required; this is not an authentication service.

A hash-bound launch document supplies the checkout, interpreter, Git executable, execution
plan, record directory, mode and retained checkout. The execution plan remains the only
place for phase, resources and input/prerequisite digests. Retained authorization explicitly
binds the launch document digest. Rehearsal requires a detached checkout different from the
retained checkout. No environment override selects paths or mode.

State advances through preflight, claimed, launching, exited and verified/failed/incomplete.
"Launching" records intent before process creation; it does not prove a child started.
Every post-claim failure leaves the claim consumed. A nonzero child exit wins over evidence
failure; otherwise incomplete evidence returns 99. Preflight refusal returns 2, claim refusal
97 and failure to establish the start records 98. No successful exit is based on a label
alone: exactly one new journal row must bind the newly produced result and runtime files,
and a structured inventory must hash every regular file in that new run directory.
`failed` means a nonzero child outcome with complete evidence. `incomplete` means evidence
or recorder failure, and can accompany either a zero or nonzero child exit.

Inventory traversal propagates enumeration, open, read, write and close errors. Links,
junctions and nonregular entries are refused instead of silently skipped or followed.
JSON represents paths without newline-delimited filename parsing. Evidence files are
create-only. Interrupted or partial records are retained and never upgraded to success.

## Implementation and acceptance checklist

- [x] Characterize validation, attribution and recursive inventory through failing tests.
- [x] Implement `tools/retained_eval_run.py`; prove claim, launch and finalization with a
  controllable child. Fault cases must assert no launch or no false-complete outcome.
- [x] Cover preflight input/environment refusal, two competing callers, record-write errors,
  launch errors, child failure, missing/extra/mismatching journal rows and inventory errors.
- [x] Remove campaign-specific prerequisite/envelope constants from completion admission;
  keep semantic validation and require the plan's exact bound prerequisite bytes.
- [x] Exercise two distinct small campaigns through the same runner and compare their phase
  artifacts/classifications to the existing deterministic oracle, excluding run IDs/timing.
- [x] Register the suite, run focused and relevant broader checks, and document fresh evidence.
- [x] Prepare one reviewable candidate for Claude; no adoption, commit, push or retained
  experiment invocation is included in this implementation authorization.

Runtime/memory optimization, evidence streaming, poker arithmetic, host protocols, session
API extraction and Slice B population design are outside this checkpoint. The existing
child remains responsible for bounded work; abrupt machine/process termination can leave
an incomplete claim, which requires controller disposition. Parent memory is not a Job peak.

## Preparing a campaign

Use a dedicated checkout at the reviewed source commit and its locked Python 3.14 environment.
The execution plan is the existing `v0a_eval_panel.py` plan, generated and admitted using that
source. Solve, export and agreement still need separate plans and invocations; later plans
bind the actual retained outputs of their predecessors. Never edit a completed packet to use
this launcher. Its first retained use requires review of this implementation and a new plan.

Prepare one UTF-8 JSON binding with exactly the following fields. All paths are absolute;
all digests are lower-case SHA-256 of the raw file bytes. `source_commit` is a full Git SHA-1.

| Field | Value |
| --- | --- |
| `version` | `pontius-eval-launch-v1` |
| `mode` | `retained` or `rehearsal` |
| `root` | Execution checkout; source scope must be clean at `source_commit` |
| `retained_root` | Reserved retained checkout; must equal `root` in retained mode |
| `source_commit` | Reviewed child source commit |
| `python` | Absolute child Python executable; version must match the plan's 3.14 runtime |
| `git` | Absolute Git executable |
| `plan` | Object with `path` inside the checkout and its `sha256` |
| `records` | New record directory outside `experiments/results/runs` |
| `authorization` | Absolute path for the separate controller authorization JSON |
| `baseline` | Object with `journal_sha256` and sorted `run_directories` names |
| `runner_sha256` | SHA-256 of the reviewed `tools/retained_eval_run.py` bytes |

Hash `execution_journal.jsonl` byte-for-byte for `baseline.journal_sha256`. Enumerate all
direct child directory names under `experiments/results/runs` for `baseline.run_directories`.
Unexpected files or links in that container are refused. Store the plan and binding outside
the recorded source scope (`src`, `tools`, `tests`, dependency/CI/text-attribute files).
Hash the finished binding; that digest is the CLI argument and authorization identity.
Changing any path, plan, baseline or mode requires a new binding and retained authorization.

For rehearsal, use a disposable detached checkout different from `retained_root`, with its
own plan paths, baseline and records. It does not need an authorization file. Rehearsal
results demonstrate operation only; they do not replace the separately authorized evidence.

For retained mode, record the controller's actual approval without manufacturing or paraphrasing
it. The authorization JSON has exactly `binding_sha256` and `controller_text`, where the latter
contains those verbatim words. Review must establish their authority; parsing a nonempty string
does not authenticate the controller. The approval binds the full launch document, and therefore
the exact plan, resource envelope, input identities and launcher bytes.

Run from a Windows environment with existing `SystemRoot` (or `SYSTEMROOT`), `TEMP` and `TMP`.
Both temporary directories must permit file creation. These checks precede the claim. The child
gets those variables, `PYTHONDONTWRITEBYTECODE=1`, `PONTIUS_GIT` and a checkout-local Git
safe-directory setting; other caller environment variables are not forwarded.

```powershell
& '<Python 3.14 executable>' -I -B -W error::ResourceWarning `
  '<reviewed launcher path>/retained_eval_run.py' `
  --binding '<absolute binding.json path>' --sha256 '<binding SHA-256>' --check
```

`--check` verifies preconditions and reports the bound phase; it never claims or launches a phase.
It invokes Git and probes the child interpreter version as part of preflight.
Retained mode checks authorization even with `--check`. After review and authorization, the
one-shot command is identical with `--check` removed. No path or mode overrides exist.

## Reading outcomes and handling failures

The record directory contains `claim.d/claim.json`, `start.json`, captures `stdout.json` and
`stderr.txt`, and, when finalization succeeds, `journal-row.jsonl`, `inventory.json` and
`outcome.json`. The journal row is copied verbatim, including its original newline style.
The inventory lists relative JSON paths, byte lengths and file hashes, including nested
`host-inputs` files. The outcome binds those evidence files by digest and records child exit,
resource object, wall time, signals and errors. Capture duration includes final capture flushing;
it is not a replacement for the child's computation or Job measurements.

A complete successful outcome requires child exit zero, exact phase/plan identity, completed
status, verified cleanup and resource state, and `phase_complete` for the three completion
phases. Missing attribution or inventory cannot produce success. Child failures can have
complete evidence and still retain their nonzero exit status. Always inspect both exit status
and outcome, rather than interpreting `evidence_complete` as phase success.

SIGINT/SIGBREAK are deferred in the main recorder while the child handles its own cleanup.
A signal observed before launch prevents launch. Before the final signal snapshot, the handler
switches from deferral to interrupting publication. A publication-time interrupt returns 99, or
preserves an already nonzero child exit, and emits a finalization-interrupted diagnostic. Earlier
deferred signals remain in the incomplete outcome. An interrupted publication can leave no outcome,
partial bytes, or an already-written JSON document; a document alone never overrides the nonzero
launcher exit. The file is not rewritten and the claim remains consumed. Hard kills and machine
failures can also leave partial records. The runner never retries, deletes a claim, or infers
permission from an absent child.
Do not rebind the same spent invocation to a fresh directory to bypass this rule: the controller
must disposition it and explicitly authorize a replacement. Do not run another campaign or
mutate source/inputs/journal concurrently in the owned checkout; no hostile-writer isolation
or global lock across distinct bindings is claimed.

The child retains responsibility for the bounded worker and Windows Job cleanup. The recorder
waits for the child and has no second watchdog. It also parses the retained result in memory;
streaming and parent memory bounds remain separate follow-up work.

## Compatibility evidence

The regression exercises one-hand and two-hand solve/export/agreement campaigns through the
public CLI in a disposable clone of the adopted source. It checks the literal retained teacher
totals for `ThKc` (1962/3924) and `8h9c` (580/1160), exact teacher bytes across export, membership,
real-host primary hits, three controls, missingness accounting and nested inventory. Those totals
come from teacher digest `c3ffab403eb7e939857cc31b0f21b255cefdffd8b0d26d078b703c1fe956b3e3`
in retained export run `cf3bcdda9eed4031938c214959b1e10c`.

The test uses 90 seconds / 3072 MiB per disposable phase, with a 32768-draw finite witness bank.
The initial 1536 MiB test envelope caused an OpenBLAS allocation failure in the host subprocess.
The recorder preserved the nonzero child status and complete failure evidence. The established
3072 MiB agreement limit passed both campaigns; no production limit or retained run was changed.
These small campaigns establish compatibility on their declared hands, not full-pool equivalence
or a new strategy-quality result. Changes to full-plan admission are tested separately against
different bound prerequisite bytes and an altered-file refusal.

Before the r002 repair, the full CPU manifest on Python 3.14.6 returned pytest exit 0:
49 suites passed and two optional
suites skipped, with 665 unittest cases counted and 10 optional SciPy cases skipped. The runner
and evaluation-panel suites had no skips. Ruff and `git diff --check` passed. The first broad
attempt failed five fixture imports because the `-P` command omitted the repository root from
`PYTHONPATH`; explicitly supplying root, `src` and `tests` corrected the invocation. Both
attempts are retained in the review packet. No optional dependency was silently added.

The r002 repair adds a deterministic finalization regression for SIGINT and SIGBREAK, before
opening the outcome and during its fsync, with child exits 0 and 7. All eight subcases fail on the
r001 launcher and pass after the repair. The exact pre-repair launcher and regression bytes are
retained with RED/GREEN receipts. The original cold review remains NOT CLEAN / NOT SOUND; a
passing regression is repair evidence, not a rewritten review verdict or adoption authorization.
Fresh r002 verification ran the launcher, completion and protocol suites: 44 cases, zero skips,
pytest exit 0, including both disposable real-host campaigns. The full 51-suite manifest was not
rerun for this finalization-only delta. Ruff and whitespace checks passed on the repaired files.

## Separate optimization follow-up

Repeated blueprint digest hashing and the host's unprepared provider-mode lookup are confirmed
follow-up targets. The host oracle and throwaway identity providers are baseline-only in this
source; ordinary blueprint-v1 play skips them. Export membership already prepares the library
lookup, but its separate legacy BlueprintProvider check still reaches the repeated digest path.
A candidate should preserve canonical wire bytes, selection reasons, passive defaults,
legality refusals and independent oracle checks, then measure on Python 3.14. Package import
cleanup needs public API and CUDA-bootstrap compatibility checks. Entry-point reachability alone
does not justify deleting research modules. None of these optimizations is bundled here.
