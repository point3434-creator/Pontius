# Collaboration and Review Workflow

Adopted 2026-08-29; freeze guards, the commit-derived manifest, and the
test-tier scope/procedure distinction were corrected the same day after the
protocol's own first cold review. This document governs how implementation work is handed
between agents (Codex workers, Claude sessions) and the controller for review,
testing, and commit. It governs collaboration mechanics only: the evidence
lifecycle (preregister → source-seal → authorize once → retain) remains owned
by PROJECT.md, and the CLAUDE.md iron rules bind every participant here.

## Supported runtime

The controller's 2026-09-09 ruling makes CPython 3.14 the only supported runtime
for development, verification, CI and new experiments. `.python-version` pins
3.14.6. This supersedes older instructions to run 3.11 first or both interpreters.
Frozen packets and historical evidence retain their original bytes and labels;
do not rewrite them or infer new 3.11 execution obligations from them. New packets
must include this ruling among their governing inputs. Snapshot isolation, actual
interpreter identity checks and explicit run authorization still apply.

## Principles

1. **Exchange immutable refs, not conversations.** The handoff object between
   implementer and reviewer is a frozen git snapshot ref plus its manifest
   SHA-256 — never a chat transcript, never mutable working files. Findings
   bind to the manifest SHA; a changed byte is a new round.
2. **The reviewer gets a cold start.** A review session receives only the ref,
   the brief/acceptance map, and the checklist — never the implementer's
   reasoning transcript. An implementer's narrative primes a reviewer to see
   what was intended instead of what is there. Stage 4's narrowly qualified
   mechanical verification is the sole exception to requiring a fresh session;
   it is not a new substantive cold pass.
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

Declare the tier and the protected invariant in the brief before implementation.
Choose the highest material direct or indirect risk of the whole changed scope,
including its consumers. Reviewers challenge the classification; unresolved
uncertainty rounds up. A lower-tier label cannot override a task's stricter contract.

- **Tier A — verified mechanical or non-normative change:** one independent
  light review, then the applicable gates. No behavioral, authority, acceptance
  or evidence-meaning change; examples are non-normative prose and verified reflow.
- **Tier B — ordinary behavior:** the full loop with one reviewer for bounded
  functionality that does not affect the Tier C invariants below.
- **Tier C — protected contract:** the full loop plus a second independent
  adversarial pass when a change can alter evidence validity, authorization,
  identity/ownership/transaction guarantees, or acceptance enforcement. Changes
  to these assurance rules themselves are Tier C.

File type, size, directory and "test-only" labels do not establish a tier. A CI
gate, generated exemption, test oracle or normative rule can be Tier C; mere
proximity to sealed code is not sufficient. Explain the actual changed risk.
Verified mechanical corrections to reviewed Tier B/C work use Stage 4 below;
they do not retrospectively lower that work's substantive review requirement.

### Controlled failure schedules

The brief may authorize deterministic timing, scheduling, allocation-token reuse
or injected faults at a named test boundary. No separate helper-double waiver is
needed when all these conditions hold:

- The real production path whose contract is claimed executes. Native/resource
  operations whose correctness is claimed stay real; simulate only the trigger,
  not successful cleanup, publication, ownership state or contract satisfaction.
- State what was controlled, why the schedule is admissible, and what the test
  cannot establish about the external system. This is not evidence that the OS,
  network or allocator itself produces that schedule in a measured population.
- Observe the outcome independently of the injector's bookkeeping or expected
  result. Retain relevant real-boundary integration controls; a fake cannot
  certify the boundary it replaces.
- A deliberately incorrect behavior must make the independent contract check
  fail through the production path. The injector must not veto or hide that
  behavior before the outcome can be observed. Account for injected events and
  retain deterministic cleanup and explicit failures for unexercised schedules.

This applies to scoped correctness tests in disposable environments only. It
does not open production/experimental execution, weaken an acceptance assertion,
replace the contract with a helper double, or make state-shape checks sufficient.
If a condition cannot be met, the proposed substitution is not authorized here;
return to the controller instead of silently counting it as equivalent evidence.

## The loop

### Stage 0 — Brief

The controller (with reviewer help) writes a one-page brief from the template
below **before implementation starts**: scope, tier, acceptance criteria, seam
inventory, size budget, forbidden claims. The reviewer reviews the brief.
Direction errors cost a page here and tens of thousands of lines later.

Four of those fields decide more than the rest combined. Each has a default;
the point is that the default must be written down rather than assumed.

- **Ground truth.** Where the expected behaviour comes from: a published
  standard, a mature reference implementation, a separately built model, real
  observations, or a fixture whose expected result was not derived by the code
  under test. "The author's own enumeration" is a permitted answer and is often
  the right one — but it must be *stated*, because a check whose oracle came
  from the same assumption as the implementation cannot test that assumption.
- **Dependency statement.** Exactly which other work waits on this. Everything
  not named may proceed in parallel. A local dependency declared as a global
  one stops the project for no reason.
- **Stop rule.** What causes adoption, one bounded correction, redesign, or
  abandonment — written before the first round, not after the second failure.
- **Budget.** The maximum review rounds or sessions before the task returns to
  the controller for reauthorization.

### Stage 0b — Design

The brief says *what* must be true. This says *how*, and it exists before any
implementation. The implementer drafts it; it is reviewed at its tier like any
other candidate, and the design verdict applies.

The case for it is this increment. R2-01 took three failed fixes and R2-03
four, and in both the root cause was a decision nobody ever consciously made —
what establishes policy authority, and how a failure cause reaches the receipt.
The audits that finally settled them were design documents written four rounds
too late. Two further findings, a hashing helper offered as replay verification
and whole-hand deferred writes, were likewise decisions that fell out of the
code rather than being chosen.

A design document carries:

- **Goals.** What this checkpoint must make true — referencing the brief's
  acceptance criteria rather than restating them — and how each is observed.
- **Design elements.** For each: the mechanism, the invariant it maintains,
  and, the part that matters most, *every place that invariant must hold*.
  R2-03 survived four rounds because "retain the cause before cleanup runs" was
  applied where each finding pointed instead of everywhere it was true.
- **What each element makes easy to get wrong.** More useful than generic pros
  and cons, and it hands the reviewer their first place to look.
- **Alternatives rejected, and why.** A rejected design with a stated reason is
  often worth more than the chosen one: it is what stops the same wrong idea
  being tried twice.
- **Decisions needing a ruling.** Anything genuinely ambiguous, left open
  rather than settled by the implementer's preference. r004 shipped one
  interpretation of an ambiguous ADR sentence while asking for a ruling on it,
  and the ruling went the other way.
- **The coverage claim, stated early.** The category this design must cover and
  how its members will be enumerated — declared before building rather than
  defended afterwards.
- **Ties to the whole project.** What this checkpoint makes possible next, what
  it forecloses, and what it assumes from the ones before it.
- **Barriers and blast radius.** What could stop this working, and what is
  cheap to revise later versus what becomes sealed and permanent.
- **What is deliberately not designed here.**

**Granularity.** The test is whether a reviewer can *disagree* with something.
Too vague if there is nothing to argue with; too detailed if checking it would
mean reading the code. Name the mechanism and its invariant, not its
implementation: "one append-only journal, every producer appends at the moment
its cause occurs, the host reads the first entry as primary" is reviewable,
while the method body that does it is only code arriving early — and code in a
design document goes stale the moment it is written. One entry per contract or
invariant, not per module or per function.

**Proportionality.** Tier A needs a paragraph or nothing. Tier B, a page. Tier
C, the full set above, reviewed as carefully as the code will be. The document
lives in the round packet like any other reviewed artifact. This adds a review
to the front of the pipeline and earns its place only if it removes more rounds
than it costs — six rounds on one increment is the evidence that it can, and if
a later checkpoint shows otherwise this stage should be cut rather than kept
out of habit.

### Stage 1 — Implement

The implementer works in its worktree. A demonstrated behavioral defect gets
a deterministic RED reproduction before the fix and an integrated GREEN after.
Coverage-only corrections use the evidence-closure rule in Stage 4.
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
cold-review request template below. For the qualified mechanical route only,
Stage 4 specifies a correction verification instead of another substantive pass.
For a FIX round, the handoff links a frozen `coverage.md` and its SHA-256,
but does not paste the claim itself. The reviewer first records an initial
invariant and related-path inventory from the requirements and frozen source,
then opens the structured coverage claim and compares the two. This is one
review, not another approval stage; implementer transcripts remain excluded.
A session exposed to the fix's design discussion cannot count as a cold pass;
use a fresh reviewer context.
The reviewer walks the checklist and the acceptance criteria against the ref.
Output is a findings document bound to the manifest SHA, severity-ordered,
with a concrete failure scenario for every Critical/Important finding.
Required corrections and their verification criteria are binding; clearly
labeled implementation advice is advisory. Verdict is CLEAN only when no
required correction remains unresolved.

**Engineering guidance (controller ruling, 2026-08-30).** Reviews should help
the implementer remove the cause, not only reproduce the latest symptom.
Where useful, include a concise engineering-guidance section that:

- names the violated invariant and underlying mechanism; distinguish a
  demonstrated cause from a hypothesis and give the cheapest falsifying check;
- recommends a concrete technique, explains which failure class it prevents,
  and states how to verify it through the real public boundary;
- considers related failure paths within scope, so the proposed correction
  closes the contract rather than only the supplied example.

Choose techniques for the observed problem: validated immutable values at a
trust boundary, explicit lifecycle states, ordered typed failure values,
single-owner cleanup, or invariant-based tests and systematic fault
schedules. These are examples, not a mandatory catalogue or a reason to add
dependencies. Mark required behavioral outcomes and verification criteria
separately from advisory implementation choices. The former are binding;
the latter do not become acceptance gates merely by appearing in a review.
Guidance is not permission for the reviewer to implement the fix, and it
does not change the cold-input rules or the frozen review scope.

**Design verdict (required).** The guidance above is advisory and can be
skipped; this cannot. Every review states one design verdict beside its defect
verdict, and states it even when the defect verdict is CLEAN:

- **SOUND** — the shape fits the contract; any findings are ordinary defects.
- **STRAINED** — it works, but the shape invites the defects being found; name
  the change that would stop them recurring.
- **WRONG SHAPE** — recommend redesign before further fixes; say what to build
  instead and roughly what it costs.

A **design finding** carries no reproduction requirement. Demanding
"inputs → wrong outcome" of it is exactly what forces a reviewer to dress a
design problem as a defect, or to drop it — `R2-05` (a hashing helper offered
as replay verification) and `R2-09` (whole-hand deferred writes) both reached
us in defect clothing. A design finding instead states: the failure mode the
current shape invites, evidence it is already happening (rounds, findings, or
repeated residuals), and the alternative with its cost. Design findings are
never Critical and never block a candidate on their own; they are advisory
until the controller adopts one.

**After a second residual on one contract, or any WRONG SHAPE verdict, redesign
is the default.** The disposition may still choose to patch, but must say why
in writing. The burden is inverted deliberately: before that point patching is
the sensible default and redesign needs the argument; after it the evidence
says the shape is the problem, and continuing to patch needs the argument.

### Stage 4 — Fix rounds

**Qualified mechanical correction.** A formatting, newline or non-normative
correction may use one independent light verification instead of repeating the
original Tier B/C substantive reviews, only when all of the following hold:

1. The pinned substantive anchor has completed every review pass required by
   its original tier, and all remaining required findings are mechanical. A
   missing pass, unresolved behavioral/coverage finding or new contract change
   cannot be carried through this route. Keep the original reports unchanged.
2. The correction is within authorized scope. Enumerate the complete cumulative
   delta from that anchor, not just the previous mechanical round. Establish no
   behavior, normative meaning, authority, expected outcome or acceptance change.
   AST equality alone is insufficient: inspect source-position, string/docstring,
   generated-data and other relevant consumers. An independently regenerated
   digest or layout census is permitted only if its meaning and checked population
   remain unchanged; changed goldens or weakened tests are not presumed mechanical.
3. Freeze a new ref and manifest. One reviewer who implemented neither the
   substantive anchor nor the correction verifies eligibility, the exact delta,
   derived artifacts and closure of every remaining finding. An earlier reviewer
   may perform this check;
   familiarity is allowed, authorship is not. Label the result mechanical
   verification, not a fresh cold pass. If eligibility is unproved or a substantive
   issue appears, stop this route and apply the ordinary tier/FIX rules.
4. The new record binds both the anchor and corrected identities, cited prior
   verdicts, eligibility evidence and correction verdict. Earlier non-CLEAN
   reports retain their original status; together these records must establish
   that no required finding remains before Stage 5. Approval never transfers
   silently to changed bytes. Normal round budgets and residual rules still apply.
5. Run focused correction checks and the unchanged applicable final acceptance
   gates against the new candidate. CPython 3.14 verification, snapshot rules,
   failure retention and exact per-commit authorization remain required. This
   route changes review depth, not tests, source-opening permission or history.

The substantive anchor stays fixed through chained mechanical corrections until
the ordinary substantive passes required by the original tier establish another
anchor. This prevents small corrections from concealing an unreviewed cumulative
change. State the eligibility evidence in the existing handoff/coverage record;
no new approval
stage, review tier, special proof framework or automated equivalence claim is needed.

A demonstrated behavioral defect requires a deterministic RED reproduction
against the frozen rejected candidate before the production edit, and an
integrated GREEN after. For a coverage-only finding, establish the missing or
unsound evidence, supply the independent behavioral check, and record its result.
That check may pass on the rejected implementation; no invented product failure
or production edit is required. If it exposes a behavioral defect, use the
ordinary RED/GREEN correction path for that defect.
Fixes freeze as the next round, `review/<task-id>/r<NNN+1>`. The rules below were
learned at full price in Task 2:

- **Rounds declare their kind.** Every frozen packet is a NEW-SURFACE round
  (the first review of code nobody has reviewed) or a FIX round (a response to
  findings), named in its handoff. Findings mean opposite things in the two, so
  they are never counted together.
- **Fix rounds are scope-frozen.** A fix round changes only what its findings
  require; new surface goes in its own candidate however ready it is. Splitting
  and merging scope while *planning* a round is ordinary judgment — it needs no
  trigger and carries no stigma — but a split already made is not collapsed
  partway through fixing it. Learned at `v0a-i01-impl/r002`: slice B rode into
  slice A's fix round, and two residuals arrived indistinguishable from eight
  first-contact findings.
- **State the failure category and coverage before fixing.** Alongside the
  existing brief, name the violated invariant, how related paths were discovered,
  which are affected, and the planned cases and limits. Keep this claim separate
  from the cold reviewer's initial requirements input. Update it explicitly
  as discovery changes. At freeze, put the final claim and evidence references
  in `coverage.md`: discovered members, discovery method, exercised cases,
  exclusions or uncertainty, and an observation that would falsify the claim.
  A short paragraph with links to an inventory is enough; no extra approval
  stage or exhaustive-proof claim is required. The handoff names the file and
  its SHA-256 as deferred review input under Stage 3.
- **Boundary discovery is shared work.** The reviewer independently challenges
  the category and its limits, rather than treating the supplied reproductions
  as exhaustive. Findings identify the invariant, demonstrated mechanism and
  known related paths; unknown coverage stays explicit. Report missed members
  or unsound discovery methods as coverage findings under the existing severity
  rules, not automatic proof of a product defect. A blocking coverage finding
  names an unmet acceptance requirement and a concrete unverified failure
  scenario; advisory design concerns remain advisory.
- **Category tests assert contract behavior.** Derive expected outcomes from
  the contract or an independent reference, not the chosen implementation's
  bookkeeping. Source searches and structural guards help discover paths but
  do not replace checks through real public boundaries. For example, routing
  every closure through a helper does not prove that the final receipt retains
  every actual typed cause once and in occurrence order. Generated compound
  schedules must show which faults actually occurred and in what order;
  distinguish exercised, unreachable and still-uncovered combinations. Pair
  coverage does not establish higher-order coverage.
- **Count residuals, not rounds.** A residual is a finding whose own fix round
  failed to close it. One residual is ordinary — fixes are allowed to be
  incomplete. A second residual on the same contract stops in-place fixing:
  that contract gets its own candidate and a written root-cause note on why the
  two earlier attempts missed, before another fix is attempted. Never grind — a
  repeat fix with no stated reason for the previous miss is a grind. Counting
  rounds instead rewards bundling, because a round that adds surface can always
  explain its findings as new.
- **Slice proactively:** any candidate over ~3,000 changed lines is reviewed
  as named slices from round one, not after reviews start failing.

**Reassess the design when fixes do not converge.** When evidence points to a
shared structural cause, compare a local correction with a bounded refactor
or replacement of the affected slice. The coordinator uses the recorded
residual history; cold reviewers assess only their permitted inputs. Recommend
a rewrite when it would make the required invariants simpler to enforce and
verify, with a concrete explanation of why another patch would retain the
weakness. Name the replacement boundary, behavior to preserve, verification
plan and transition risks. Recurrence prompts this assessment, not an
automatic rewrite or a new gate on unrelated work. The existing second-residual
rule still applies. Any replacement stays within declared fix scope, uses a
new frozen candidate and RED/GREEN evidence, and undergoes the same cold
review and acceptance gates; new surface remains separate. Sealed bytes and
issued reports remain immutable. This guidance authorizes no rewrite by itself.

### Stage 5 — Acceptance gates, in fixed order

1. Reviewer verdict CLEAN (both passes, for Tier C), or the complete qualified
   mechanical record required by Stage 4 closing all remaining findings. This
   is the only substitution for repeating the substantive passes on new bytes.
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
      coverage.md             # FIX only: frozen claim, deferred until independent inventory
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

1. **Real contract and independent oracle.** Apply the controlled-failure-schedule
   conditions above. The production path and claimed resource effects stay real;
   controlling the trigger cannot substitute the contract or its independent check.
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
Protected invariant and direct/indirect changed risk: <why this tier applies>
Base: <commit sha> on <branch>, worktree <path>
Scope: <paths that may change; paths that must not>
Acceptance criteria: <numbered, individually testable>
Seam inventory: <contracts crossed: subprocess / ABI / writer-reader /
  fixtures / locks / Git / cloud-sync / none>
Size budget: <expected changed lines; slice plan if over ~3,000>
Ground truth: <where expected behaviour comes from; say so plainly if it is
  the author's own enumeration>
Dependencies: <what must wait for this; everything unlisted proceeds>
Stop rule: <what triggers adoption / one bounded correction / redesign /
  abandonment>
Budget: <max review rounds or sessions before reauthorization>
Forbidden claims: <what this task does NOT prove or authorize>
Test plan: <RED targets, focused suites, snapshot gates>
FIX coverage planning: <separate draft-claim path; fill before implementation,
  freeze as coverage.md; keep its contents out of initial cold-review inputs>
```

### Cold-review request (Stage 3 — the packet's `handoff.md`)

```markdown
Adversarial review request.
Candidate: refs/heads/review/<task-id>/r<NNN> at commit <sha>,
manifest SHA-256 <manifest sha>, base <base sha>.
Scope: <paths or named slices>.
Round kind: <NEW-SURFACE or FIX>.
FIX deferred input: coverage.md, SHA-256 <digest>; do not open it until your
initial invariant and related-path inventory are recorded. Its claim includes
discovered members/method, exercised cases, limits, and a falsifying observation.
Inputs: docs/workflow.md (checklist v1), <path to task brief / acceptance
map>. Do not read implementer transcripts, chat history, or report sections
other than the evidence tables named here and the deferred structured claim
after the initial inventory.
Rules: findings bind to the manifest SHA; every Critical/Important finding
states a concrete failure scenario (inputs/state → wrong outcome); the
controlled-failure-schedule rule applies; verdict CLEAN only if no finding
survives verification; name the required correction but do not implement it.
Where useful, include concrete engineering guidance: cause or hypothesis,
technique, invariant protected, and verification. Separate required outcomes
from advisory design choices; assess a bounded refactor or slice replacement
when the permitted evidence shows that local fixes retain a structural cause.
Also state one required design verdict — SOUND, STRAINED, or WRONG SHAPE —
with a short justification, even if the defect verdict is CLEAN. A design
finding needs no reproduction: give the failure mode the shape invites,
evidence it is already happening, and the alternative with its cost.
On a fix round, compare your recorded inventory with coverage.md. Challenge
the category, discovery method, actual exercised cases, limits and independent
test expectations. Grade coverage findings under the existing severity rules;
missing coverage is not automatically proof of a product defect. Structural
guards support, but do not replace, observable contract checks.
Output: reviews/review-<NN>-<reviewer>.md in this round's packet,
severity-ordered, one entry per finding, design verdict stated separately.
```
