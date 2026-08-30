# Collaboration and Review Workflow

Adopted 2026-08-29; freeze guards, the commit-derived manifest, and the
test-tier scope/procedure distinction were corrected the same day after the
protocol's own first cold review. This document governs how implementation work is handed
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
- **Finalizer**: at each checkpoint, whoever wrote the first draft has final
  say and makes the ceremonial commit; the roles alternate at the next
  checkpoint. The round's `handoff.md` names the finalizer. Controller
  authorization remains per commit regardless of finalizer.

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
working-tree changes). Every step is failure-checked, the index file is unique
per freeze and always cleaned up, the caller's original `GIT_INDEX_FILE`
selection is restored on every exit path, and the ref update is create-only —
an existing round ref refuses to be overwritten:

```powershell
$W = "D:\Pontius-worktrees\<worktree>"; $R = "review/<task-id>/r<NNN>"
$savedIndex = $env:GIT_INDEX_FILE
$idx = Join-Path $env:TEMP ("freeze-" + [guid]::NewGuid().ToString("N") + ".idx")
$env:GIT_INDEX_FILE = $idx
try {
  git -C $W read-tree HEAD;             if (-not $?) { throw "read-tree failed" }
  git -C $W add -A;                     if (-not $?) { throw "add failed" }
  $tree = git -C $W write-tree;         if (-not $? -or -not $tree) { throw "write-tree failed" }
  $parent = git -C $W rev-parse HEAD;   if (-not $?) { throw "rev-parse failed" }
  $commit = git -C $W commit-tree $tree -p $parent `
    -m "Review candidate $R (frozen, not a decision commit)"
  if (-not $? -or -not $commit) { throw "commit-tree failed" }
} finally {
  if ($null -ne $savedIndex) { $env:GIT_INDEX_FILE = $savedIndex }
  else { Remove-Item Env:\GIT_INDEX_FILE -ErrorAction SilentlyContinue }
  Remove-Item $idx -Force -ErrorAction SilentlyContinue
}
$zero = "0" * 40
git -C $W update-ref "refs/heads/$R" $commit $zero
if (-not $?) { throw "freeze refused: $R already exists - rounds are immutable, use r<N+1>" }
git -C $W push origin "refs/heads/$R"; if (-not $?) { throw "push failed" }
```

The **manifest** is the SHA-256 of lexicographically sorted rows of the form
`<lowercase file sha256><two spaces><relative POSIX path><LF>` (the same row
convention as the Task 2 audit). Rows sort as whole byte strings — digest
first, exactly as `sorted()` orders the row strings — never by path: a
path-sorted manifest over the same rows is a different digest (the r004
packet incident). It is computed **from the frozen commit's
blobs, never from working files**, so candidate and manifest cannot diverge.
It covers every path where the frozen tree differs from its parent: added,
modified, and typechanged paths hash the blob at `<commit>:<path>`; a deleted
path carries the sentinel digest of 64 zeros. Rename detection is disabled, so
a rename appears as one addition plus one deletion; untracked directories are
a non-issue because the commit stores files only. Candidate identity is over the
**stored blob bytes** — the content after add-time line-ending normalization.
Reviewers recompute and verify identity with the blob-based command below
(`git cat-file blob <commit>:<path>`), never by hashing checked-out or working
files: checkout can re-apply CRLF conversion (this repository has
`core.autocrlf=true`), so both checkout bytes and the implementer's original
working-file bytes may legitimately differ from the blobs. The script runs
from a temporary file because PowerShell 5.1 mangles embedded double quotes in
`-c` arguments.

```powershell
$py = @'
import hashlib, subprocess, sys
w, commit = sys.argv[1], sys.argv[2]
def run(*a):
    return subprocess.run(["git", "-C", w, *a],
                          capture_output=True, check=True).stdout
raw = run("diff-tree", "-r", "-z", "--no-commit-id", "--name-status",
          commit + "^", commit)
fields = raw.decode("utf-8", "surrogateescape").split("\0")
rows, i = [], 0
while i + 1 < len(fields) and fields[i]:
    status, path = fields[i][0], fields[i + 1]
    if status == "D":
        digest = "0" * 64
    else:
        digest = hashlib.sha256(run("cat-file", "blob",
                                    f"{commit}:{path}")).hexdigest()
    rows.append(f"{digest}  {path}\n")
    i += 2
print(hashlib.sha256("".join(sorted(rows)).encode()).hexdigest())
'@
$pyPath = Join-Path $env:TEMP ("manifest-" + [guid]::NewGuid().ToString("N") + ".py")
Set-Content -LiteralPath $pyPath -Value $py -Encoding ascii
.venv\Scripts\python.exe $pyPath $W $commit
```

Record the pair (ref commit SHA, manifest SHA) in `candidate.json` and the
report. That pair is the candidate's identity; the ref is now immutable.

### Stage 3 — Cold review

Open a **fresh** session and paste the round's `handoff.md` — the
cold-review request template below.
The reviewer walks the checklist and the acceptance criteria against the ref.
Output is a findings document bound to the manifest SHA, severity-ordered,
with a concrete failure scenario for every Critical/Important finding.
Findings documents are binding contracts. Verdict is CLEAN only when nothing
survives verification.

### Stage 4 — Fix rounds

Each finding requires a deterministic RED reproduction against the frozen
rejected candidate before the production edit, and an integrated GREEN after.
Fixes freeze as the next round, `review/<task-id>/r<NNN+1>`. Two rules
learned at full price in Task 2:

- **Circuit breaker:** three rounds without convergence is a controller
  stand-down — re-scope, slice, or split the task. Never grind.
- **Slice proactively:** any candidate over ~3,000 changed lines is reviewed
  as named slices from round one, not after reviews start failing.

### Stage 5 — Acceptance gates, in fixed order

1. Reviewer verdict CLEAN (both passes, for Tier C).
2. Broad suites GREEN via the isolated snapshot procedure. Focused snapshot
   runs already happened at each freeze as the self-report's evidence; the
   broad population is spent only on reviewed code.
3. Controller authorization — explicit, per commit, naming the round or
   candidate commit it approves. An authorization that no longer matches the
   current round is void; it never transfers to newer bytes.
4. Ceremonial commit by the checkpoint's finalizer (short imperative title),
   immediate push to `origin`.
5. Retire the task's `review/*` refs under the handoff-packet retirement
   predicate (integrated byte-identically, or archived — rule 4 below).
6. One-line verdict entry in the task ledger by whoever issued the verdict;
   one disposition line in the program ledger.

The CodeRabbit sweep was retired by the controller's 2026-08-30 ruling,
recorded in `docs/workflow-amendment-2026-08-30.md`; no external-service
gate replaces it.

## Test-run tiers

"Isolated snapshot" names the *procedure* (the disposable-snapshot execution
policy); "focused" and "broad" name the *scope*. The two axes are independent:

- **Focused, from the worktree** — single files during development: free,
  iteration only, never evidence.
- **Focused, isolated snapshot** — the task's changed suites under the
  snapshot procedure, at freeze time: these runs are the self-report's GREEN
  evidence for that round.
- **Broad, isolated snapshot** — the full population under the same
  procedure, only after review-clean: broad runs are expensive and unreviewed
  code has not earned them.

## Ledger discipline

Each task's handoff packet carries its own `progress.md` — the task ledger:
exactly one line per verdict, written by the verdict's issuer at the moment
of the verdict. The task report holds the detail. Nobody else updates that
ledger for the round — the single-writer rule is what keeps ledger and
report from diverging. The program ledger records one line per round
disposition, never one per review; verdict lines live only in the task
ledger, so the two ledgers can never disagree about who found what.

## Handoff packets

Every frozen round is published as an immutable packet under one permanent
home outside the repository and every worktree:

```
D:\Pontius-handoffs\
  INDEX.md                    # navigation only: tasks and their current rounds
  <task-id>\
    progress.md               # the task ledger (single-writer, above)
    r<NNN>\
      handoff.md              # cold-review instructions, scope, pinned inputs, finalizer
      candidate.json          # identity: ref, commit, base, tree, manifest digest
      manifest.sha256         # the sorted blob-hash rows themselves
      reviews\
        review-<NN>-<reviewer>.md   # attributed findings, one file per reviewer
      checks\                 # receipts: commands, environment identities, exits
      disposition.md          # per-finding accept/reject and integration outcome
```

Task IDs are short stable kebab-case, `<lane>-<unit>-<phase>` — e.g.
`v0a-i01-prereg`, `v0a-i01-impl` — with no dates and no adjectives. Rounds
are three digits from `r001`. The short reference `<task-id>/r<NNN>`
("cold-review v0a-i01-prereg/r002") locates the packet; the full commit and
manifest SHA-256 in `candidate.json` remain the only authority. Freeze refs
use the matching namespace `review/<task-id>/r<NNN>`, and preserved
candidates `archive/<task-id>/r<NNN>`. Never create a flat ref named exactly
`review/<task-id>`: Git forbids a ref and a ref directory with one name.

`manifest.sha256` contains exactly the manifest rows — lexicographically
sorted `<lowercase file sha256><two spaces><relative POSIX path><LF>` from
the frozen blobs, nothing else — so the SHA-256 of the file's own bytes is
the manifest digest recorded in `candidate.json`. `candidate.json` carries
exactly: `schema_version` (`pontius-handoff-candidate-v1`), `task_id`,
`round`, `ref`, `commit`, `base`, `tree`, `manifest_sha256`, and `date`.

Packet rules:

1. **New bytes or new scope → new round.** Changed candidate bytes or a
   changed review scope get `r<NNN+1>` and a fresh ref. Names like `final2`
   or `latest-fixed` never exist.
2. **Reviewers are parallel and blind.** Any number of reviewers may take
   one round; each writes its own attributed findings file, and no
   reviewer's findings enter another reviewer's cold-review inputs.
3. **Append-only.** Published inputs and issued findings are never edited or
   overwritten; corrections are appended as new records — a new review
   file, a new ledger line, a disposition entry.
4. **Retirement predicate.** A `review/*` ref may be deleted only when the
   packet's `candidate.json` commit is reachable from `master` (integrated
   byte-identically) or preserved under `archive/<task-id>/r<NNN>` pushed to
   `origin`. Accepted and rejected candidates are both preserved.
5. **Short ID locates, identity binds.** Every verdict and disposition
   binds to the commit + manifest pair, never to a folder path.
6. **Own repository, routine push.** `D:\Pontius-handoffs\` is its own Git
   repository with a private `origin`; packet files are committed and
   pushed routinely as they are published. The evidence repository's
   per-commit ceremony does not apply there — packets are already governed
   by rules 1–5.
7. **Coordination only, never evidence.** Packets hold instructions,
   identities, findings, receipts, and dispositions. Retained evidence —
   results, journals, lifecycle artifacts — never leaves the evidence
   repository's retained paths.

Packets predating this section stay where they were published; `INDEX.md`
points at their current locations.

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
11. **Identity recomputation.** Every published identity artifact — manifest
    digest, blob pin, packet row file — is independently recomputed from the
    frozen bytes under the documented convention (whole-row byte sort, LF
    rows) before anything binds to it; a digest that only reproduces under a
    different ordering is a different identity.

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

### Cold-review request (Stage 3 — the packet's `handoff.md`)

```markdown
Adversarial review request.
Candidate: refs/heads/review/<task-id>/r<NNN> at commit <sha>,
manifest SHA-256 <manifest sha>, base <base sha>.
Scope: <paths or named slices>.
Inputs: docs/workflow.md (checklist v1), <path to task brief / acceptance
map>. Do not read implementer transcripts, chat history, or report sections
other than the evidence tables named here.
Rules: findings bind to the manifest SHA; every Critical/Important finding
states a concrete failure scenario (inputs/state → wrong outcome); the
helper-double rule applies literally; verdict CLEAN only if no finding
survives verification; name the required correction but do not implement it.
Output: reviews/review-<NN>-<reviewer>.md in this round's packet,
severity-ordered, one entry per finding.
```
