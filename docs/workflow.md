# Collaboration and Review Workflow

Adopted 2026-08-29. This document governs how implementation work is handed
between agents (Codex workers, Claude sessions) and the controller for review,
testing, and commit. It governs collaboration mechanics only: the evidence
lifecycle (preregister → source-seal → authorize once → retain) remains owned
by PROJECT.md, and the CLAUDE.md iron rules bind every participant here.

## Principles

1. **Exchange immutable refs, not conversations.** The handoff object between
   implementer and reviewer is a frozen git snapshot ref plus its manifest
   SHA-256 — never a chat transcript, never mutable working files. Findings
   bind to the manifest SHA; a changed byte is a new round.
2. **The reviewer gets a cold start.** A review session receives only the ref,
   the brief/acceptance map, and the checklist — never the implementer's
   reasoning transcript. An implementer's narrative primes a reviewer to see
   what was intended instead of what is there.
3. **Ceremony scales with blast radius; order never changes.** The sequence
   *freeze → review → tests → authorize → commit → push* is invariant. Tiers
   change review depth, never the order.

## Roles

- **Controller** (the user): issues briefs, rulings, and commit authorization.
- **Implementer**: writes code in a worktree, produces RED/GREEN evidence and
  a self-report. May be Codex or Claude.
- **Reviewer**: a cold-context session (Claude or Codex) that never implemented
  the round it reviews. Implementer ≠ reviewer per round; roles may swap per
  task.
- **CodeRabbit**: final automated sweep only. It is the weakest detector in
  the stack (it has passed candidates that fresh adversarial review then
  rejected), so it runs last and is never the load-bearing gate.

## Change tiers

Declare the tier in the brief. When in doubt, round up.

- **Tier A — mechanical** (docs, config, renames, generated files): one light
  review pass, then the gates. Minutes of ceremony.
- **Tier B — ordinary code** (features, tools, non-evidence tests): the full
  loop below with one reviewer.
- **Tier C — evidence-adjacent** (ownership/transaction code, gates, readers,
  analyzers, anything a sealed path depends on): the full loop plus a second
  independent adversarial pass. The helper-double rule is enforced literally.

## The loop

### Stage 0 — Brief

The controller (with reviewer help) writes a one-page brief from the template
below **before implementation starts**: scope, tier, acceptance criteria, seam
inventory, size budget, forbidden claims. The reviewer reviews the brief.
Direction errors cost a page here and tens of thousands of lines later.

### Stage 1 — Implement

The implementer works in its worktree. Every binding contract gets a
deterministic RED reproduction before the fix and an integrated GREEN after.
The self-report records commands, exits, counts, and hashes — claims without
receipts do not count.

### Stage 2 — Freeze

Create an immutable snapshot ref with a temporary index (no HEAD, index, or
working-tree changes), compute the manifest, push the ref:

```powershell
$W = "D:\Pontius-worktrees\<worktree>"; $R = "review/<task>-r<N>"
$env:GIT_INDEX_FILE = "$env:TEMP\freeze.idx"
git -C $W read-tree HEAD
git -C $W add -A
$tree = git -C $W write-tree
$parent = git -C $W rev-parse HEAD
$commit = git -C $W commit-tree $tree -p $parent -m "Review candidate $R (frozen, not a decision commit)"
Remove-Item Env:\GIT_INDEX_FILE
git -C $W update-ref "refs/heads/$R" $commit
git -C $W push origin "refs/heads/$R"
```

The **manifest** is the SHA-256 of lexicographically sorted rows of the form
`<lowercase file sha256><two spaces><relative POSIX path><LF>` over every
added/modified file (the same convention as the Task 2 audit):

```powershell
$py = @'
import hashlib, pathlib, subprocess, sys
w = sys.argv[1]
status = subprocess.run(["git", "-C", w, "status", "--porcelain"],
                        capture_output=True, text=True, check=True).stdout
rows = []
for line in sorted(p[3:].strip('"') for p in status.splitlines()
                   if p and not p.startswith(" D")):
    digest = hashlib.sha256((pathlib.Path(w) / line).read_bytes()).hexdigest()
    rows.append(f"{digest}  {line}\n")
print(hashlib.sha256("".join(rows).encode()).hexdigest())
'@
.venv\Scripts\python.exe -c $py D:\Pontius-worktrees\<worktree>
```

Record the pair (ref commit SHA, manifest SHA) in the report. That pair is the
candidate's identity; the ref is now immutable.

### Stage 3 — Cold review

Open a **fresh** session and paste the cold-review request template below.
The reviewer walks the checklist and the acceptance criteria against the ref.
Output is a findings document bound to the manifest SHA, severity-ordered,
with a concrete failure scenario for every Critical/Important finding.
Findings documents are binding contracts. Verdict is CLEAN only when nothing
survives verification.

### Stage 4 — Fix rounds

Each finding requires a deterministic RED reproduction against the frozen
rejected candidate before the production edit, and an integrated GREEN after.
Fixes freeze as `review/<task>-r<N+1>`. Two rules learned at full price in
Task 2:

- **Circuit breaker:** three rounds without convergence is a controller
  stand-down — re-scope, slice, or split the task. Never grind.
- **Slice proactively:** any candidate over ~3,000 changed lines is reviewed
  as named slices from round one, not after reviews start failing.

### Stage 5 — Acceptance gates, in fixed order

1. Reviewer verdict CLEAN (both passes, for Tier C).
2. Broad/isolated snapshot suites GREEN (never spent on unreviewed code).
3. CodeRabbit sweep on the exact final bytes.
4. Controller authorization — explicit, per commit.
5. Ceremonial commit (short imperative title), immediate push to `origin`.
6. Retire the task's `review/*` refs (delete local and remote).
7. One-line ledger entry, written by whoever issued the verdict.

## Test-run tiers

- **Focused** — single files from the worktree during development: free.
- **Isolated snapshot** — the disposable-snapshot procedure at freeze time:
  these runs are the report's evidence.
- **Broad suites** — only after review-clean. Isolated runs are expensive;
  unreviewed code has not earned them.

## Ledger discipline

`progress.md` gets exactly one line per verdict, written by the verdict's
issuer at the moment of the verdict. The task report holds the detail. Nobody
else updates the ledger for that round — the single-writer rule is what keeps
ledger and report from diverging.

## Review checklist v1

Grown from the ADR bug ledger and the Task 2 fix rounds. Each new incident
adds a line; lines are never removed.

1. **Helper-double rule.** An ownership/transaction contract is satisfied only
   by the real production path under a real failure schedule — never by a
   helper double or state-shape test.
2. **Subprocess environment.** Every child launch is audited under the real
   scrubbed environment; Git only via absolute `PONTIUS_GIT`; no `PATH`
   lookup anywhere.
3. **Cross-boundary contracts.** Every host↔kernel and writer↔reader pair is
   checked against one authority (derived or schema-validated), with a
   field-exhaustive round-trip test on the real artifact.
4. **Module resolution.** Imports resolve to the intended bytes under
   `-B -P` from the snapshot root — prove it, don't assume it.
5. **Test isolation.** No test touches primary-checkout or lifecycle state;
   negative controls point at disposable snapshots only.
6. **Fixture vs. runtime.** Every branch unreachable in development has an
   injected execution in tests; fixtures never contradict the preconditions
   of the branch they exist to exercise.
7. **Measured budgets.** No unmeasured number is frozen as a hard gate; a
   wall or budget carries its calibration measurement as provenance.
8. **Minimal gate predicates.** Gates assert the minimal identifying fact,
   never an over-specified set that can reject a passing substance.
9. **Ownership timing.** Every descriptor/handle/name is registered with a
   close-once owner before any fallible probe; rollback state transitions are
   monotonic; an ambiguously closed numeric resource is never replayed.
10. **Exactness hygiene.** `type(value) is int` / `is bool` discipline in
    evidence paths; changed files are LF-only, BOM-free, ≤100 columns, no
    trailing whitespace.

## Templates

### Task brief (Stage 0)

```markdown
# Task <id> brief — <title>
Tier: A | B | C
Base: <commit sha> on <branch>, worktree <path>
Scope: <paths that may change; paths that must not>
Acceptance criteria: <numbered, individually testable>
Seam inventory: <contracts crossed: subprocess / ABI / writer-reader /
  fixtures / locks / Git / cloud-sync / none>
Size budget: <expected changed lines; slice plan if over ~3,000>
Forbidden claims: <what this task does NOT prove or authorize>
Test plan: <RED targets, focused suites, snapshot gates>
```

### Cold-review request (Stage 3 — paste into a fresh session)

```markdown
Adversarial review request.
Candidate: refs/heads/review/<task>-r<N> at commit <sha>,
manifest SHA-256 <manifest sha>, base <base sha>.
Scope: <paths or named slices>.
Inputs: docs/workflow.md (checklist v1), <path to task brief / acceptance
map>. Do not read implementer transcripts, chat history, or report sections
other than the evidence tables named here.
Rules: findings bind to the manifest SHA; every Critical/Important finding
states a concrete failure scenario (inputs/state → wrong outcome); the
helper-double rule applies literally; verdict CLEAN only if no finding
survives verification; name the required correction but do not implement it.
Output: <task>-r<N>-findings.md, severity-ordered, one entry per finding.
```
