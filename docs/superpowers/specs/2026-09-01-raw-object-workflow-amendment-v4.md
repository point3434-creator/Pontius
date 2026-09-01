# Proposed workflow amendment: exact raw-object freeze and packet publication

Status: PROPOSED. This file does not amend `docs/workflow.md` by itself.

This proposal supersedes v3 after static review found two remaining bootstrap
gaps: authority utilities could not use their own unreviewed output-ref route to
establish review provenance, and byte-pinning an opaque `handoff.md` did not
validate its cold-input meaning. It also makes remote `UNKNOWN` classification
symmetric.

## Scope and preserved order

The evidence-repository order remains:

```text
freeze -> review -> tests -> authorize -> ceremonial commit -> push
```

Nothing here advances the evidence repository, accepts candidate code, spends
an experiment authority, or weakens any Stage 3 through Stage 5 gate.

This amendment replaces the complete Stage 2 freeze procedure when a round
explicitly selects the raw-object route below. All surviving Stage 2 references
to the temporary index, `git add -A`, add-time normalization, ordinary ref push,
and its example commands apply only to the temporary-index route. Under either
route, candidate identity is the exact stored blobs in the frozen commit.

## Two complete Stage 2 routes

The temporary-index route remains available unchanged for a candidate derived
from a working-tree population.

The raw-object route is allowed only when the preregistration pins the base
commit and the complete changed-path population as canonical repository-
relative POSIX paths, ordinary blob modes (`100644` or `100755`), and retained
bytes. It supports only additions and ordinary-blob modifications. A deletion,
type change, symlink, gitlink, duplicate, case-fold collision, file/directory
prefix collision, invalid Windows path segment, or undeclared base-relative
difference refuses; use the temporary-index route for a different change class.

The builder feeds each retained byte string directly to:

```text
git hash-object --no-filters -w --stdin
```

It rebuilds affected trees with NUL-framed `git ls-tree -z` and
`git mktree -z`, then creates the candidate with deterministic
`git commit-tree` metadata. It never invokes `git add`, checkout, attributes,
filters, or the real index. Before authority creation it proves:

- the candidate has exactly one parent, the pinned base;
- base to candidate differs by exactly the declared rows and change kinds;
- every affected object has its declared type, mode, blob OID, and SHA-256;
- the manifest contains exactly the complete diff, with whole-row byte sorting;
- both independent blob-reading routes reproduce every manifest row; and
- HEAD, the real index, and the working tree remain unchanged.

The local candidate ref and any local packet anchor are created together from
absence in one `update-ref --stdin` transaction. Exact complete state is an
idempotent lost-ack recovery. Partial, different, malformed, or unknown state
is preserved and refused. No cleanup deletes Git objects or refs.

## Nonrecursive authority-tool bootstrap

A candidate whose complete declared surface consists of tools needed to
implement a new freeze, publication, or review-output route, their direct tests,
and their reviewed design authority may bootstrap only from the temporary-index
Stage 2 procedure already present in the adopted workflow. That existing
procedure, direct Git, and handoff packet rule 6 are the trusted root. No
candidate authority utility may run to freeze, review, publish, accept, or
preserve itself.

The bootstrap preregistration pins the adopted workflow SHA-256, H base commit,
task and round, exact candidate ref, complete allowed path population, tier,
required independent reviewers, and finalizer. The temporary-index route may
create and push only that candidate ref. Reviewers publish their attributed
reports and exact issuer-authored ledger lines through ordinary rule-6 handoff
packet commits. Normal workflow review, design-verdict, test, controller-
authorization, acceptance, preservation, and disposition rules still apply.

Bootstrap review authority is the immutable historical packet commit and blob
identity, not a mutable packet file. Before later authority code may depend on
the reviewed tools, a canonical
`checks/utility-review-authority.json` projection must be authorized by the
controller and bind exactly:

- task, round, utility candidate ref, commit, and manifest SHA-256;
- adopted workflow and interpretation SHA-256 values;
- the exact role-to-utility SHA-256 map and controller-authorized author map;
- for each required review: ordinal, reviewer, historical packet commit, report
  path, report blob OID, report SHA-256 and byte count, ledger-line SHA-256,
  defect verdict, design verdict, design-justification SHA-256, implemented-role
  population, and whether candidate artifacts were read; and
- the projection schema. Its complete-byte SHA-256 is external authority and is
  never a field in the projection itself.

Every historical packet commit must be freshly proven reachable from the pinned
handoff integration ref or an exact pushed archive ref. Required reviewers are
distinct and absent from the union of utility authors; implemented-role
populations are empty; every defect verdict is `CLEAN`; every design verdict and
justification reproduces its immutable report; candidate artifacts were not
read; and all repeated utility and candidate identities are equal. Unknown,
unreachable, conflicting, incomplete, or unequal provenance refuses.

Full utility-review narratives and findings remain in their separate utility
packet. The later candidate packet may contain only the authorized structured
projection. Its packet-source manifest and one-use builder dispatch pin the
projection SHA-256. The bootstrap clause creates no review-output transfer ref
and expires when the utility round disposition is remotely published. Downstream
review-output producers and finalizer publishers remain governed by their own
preregistered, reviewed, and rehearsed authority below.

## Candidate authority and coordination packet

The review authority remains only the candidate full ref, candidate commit and
tree, and manifest SHA-256 recorded by the closed `candidate.json` v1 schema.
The packet commit and packet ref provide coordination and durability; they are
never a second candidate identity and never enlarge the candidate manifest.

For task `<task-id>` and round `r<NNN>`, the preregistration pins these full
refs:

```text
refs/heads/review/<task-id>/r<NNN>
refs/heads/handoff-freeze-packet/<task-id>/r<NNN>
refs/heads/archive/<task-id>/r<NNN>
refs/heads/handoff-freeze-packet-archive/<task-id>/r<NNN>
```

The packet commit has exactly one parent, the candidate commit. Its complete
parent-relative difference is the declared pre-review packet inventory. It may
contain the schema-generated handoff, fixed identities, reviewed utilities,
workflow and interpretation snapshots, preparation receipts, the authorized
utility-review projection, and the controller-authorized cold-input spec. It
contains no utility-review narrative, implementer self-report, prior candidate
finding, candidate-review verdict, disposition, retained evidence, or other
non-cold input.

The immutable packet staging ref never moves. Reviewer outputs first freeze on
their own transfer refs; only their validated exact bytes later enter descendants
of the handoff repository's pinned integration branch.

Packet identity is external to `candidate.json`. The round's exact intent
schema binds the deterministic packet ref, packet commit and tree, packet
subtree, self-excluding inventory blob, and inventory SHA-256. The packet
inventory binds every pre-review path, mode, blob OID, SHA-256, and byte count.

## Schema-generated cold handoff

`handoff.md` is never accepted as an opaque authored packet source. Before the
builder dispatch, the controller authorizes the complete-byte SHA-256 of a
canonical `checks/cold-input-spec.json`. Its exact schema carries task, round,
tier, round kind, base, candidate ref, scope paths, acceptance criteria, seam
inventory, forbidden claims, required-review count, finalizer, workflow and
interpretation identities, allowed cold-input paths, forbidden input classes,
and the required review-output contract. Unknown keys, alternate encodings,
wrong types, duplicate or colliding paths, or an unrecognized domain refuse.

The spec contains no candidate commit, candidate tree, candidate manifest
digest, packet identity, descendant identity, or digest of itself. After the
candidate and manifest exist, the builder generates `handoff.md` from the fixed
schema template, the authorized spec, and the derived candidate identity. The
packet-source manifest binds the spec but excludes the generated handoff; the
packet inventory binds both.

The generated bytes must reproduce the task, round, tier, round kind, base,
candidate ref, derived candidate commit and manifest, exact scope, acceptance
criteria, permitted and forbidden inputs, workflow identities, required review
count, finalizer, output rules, and cold-input-spec SHA-256. The handoff may name
only declared cold inputs. Any free-form suffix, external mutable input, utility
review narrative, prior candidate finding, self-report, ledger, disposition, or
identity mismatch refuses.

The controller's one-use freeze authorization pins the exact workflow,
interpretation, plan, schema, utility-review projection, cold-input spec, and
packet-source-manifest SHA-256 values and limits authority to the declared freeze
endpoint. The authorization record names no digest of itself and no uncreated
packet or descendant. Its complete-byte SHA-256 is bound by the preparation
receipt and builder intent. Changed bytes require a new authorization.

## Atomic remote-pair publication

One `git push --atomic` operation requests create-only publication of the
candidate ref and packet ref with an empty expected-value lease for each.
Sequential fallback is forbidden. Push status is never authority. After every
push return, including nonzero, one strict literal-URL `ls-remote --refs` query
with exit zero and empty stderr classifies the exact full-ref pair:

| Candidate ref | Packet ref | Result |
| --- | --- | --- |
| absent | absent | `AA`: retryable; one atomic creation may be attempted |
| exact | exact | `EE`: authority; also closes a lost acknowledgement |
| exact | absent | `PARTIAL`: preserve and refuse |
| absent | exact | `PARTIAL`: preserve and refuse |
| different | absent, exact, or different | `DIFFERENT`: preserve and refuse |
| absent, exact, or different | different | `DIFFERENT`: preserve and refuse |
| malformed, ambiguous, or unavailable | any | `UNKNOWN`: preserve and refuse |
| any | malformed, ambiguous, or unavailable | `UNKNOWN`: preserve and refuse |

Here `different` means a syntactically valid present record with the wrong
target. `UNKNOWN` takes precedence whenever either side cannot be classified;
the `DIFFERENT` rows apply only when both sides are otherwise valid observations.

The exact `EE` observation proves current ref values only. It does not prove
which actor created them or that a partial remote state never existed. Fresh-
clone adoption is allowed only by reconstructing and validating the complete
candidate, manifest, packet, inventory, and intent before creating the exact
local authority refs transactionally.

## Routine handoff-main publication

Each round pins the handoff repository's integration ref as an exact full ref.
For `D:\Pontius-handoffs` it is `refs/heads/main`; local symbolic HEAD, a remote
default branch, or mutable Git configuration never selects it.

After exact remote-pair publication, a deterministic child of the packet commit
may add only a remote-publication receipt and advance the handoff integration
ref with an explicit lease on its pinned predecessor. This is routine packet
publication under packet rule 6. It makes coordination files durable and
browseable before cold review. It is not the Stage 5 evidence-repository
ceremonial commit, candidate acceptance, test evidence, or production
integration. A fresh literal-URL observation of the integration ref is
authority; local tracking refs, local main, the index, and working files are
not.

The integrated packet remains a coordination snapshot. Reviewers still bind
findings to the candidate commit plus manifest, and receive the same integrated
packet commit only as their cold instruction and receipt population.

## Frozen blind-review outputs

Blindness is content-bound. Every reviewer receives a sanitized no-checkout
repository and raw verified reading copies from the identical integrated packet
commit. Another candidate-review report may exist elsewhere, but it is not
fetched, materialized, or named in that input. No temporal publication barrier
is needed to recover which bytes the reviewer saw.

At verdict time, each reviewer authors an attributed report and the exact
one-line task-ledger record. The reviewer freezes those bytes under a distinct
create-only review-output ref whose commit has the integrated packet as its
only parent. A self-excluding output manifest binds the report and structured
receipt; the communicated output ref plus manifest SHA-256 is the only
reviewer-to-finalizer handoff. Chat and mutable files carry no authority.

Review-output refs never advance main. After all required frozen outputs exist,
the single finalizer validates every ref plus manifest pair and copies their
exact report, receipt, manifest, and issuer-authored verdict-line bytes into one
leased main descendant. This transport does not change authorship and preserves
the ledger's single-writer rule. No reviewer resolves another reviewer's ledger
conflict or receives another reviewer's findings as cold input.

This paragraph normatively replaces the workflow's physical-writer and timing
language for frozen review outputs. The issuer fixes the exact ledger-line bytes
at verdict time. The finalizer may only transport verified identical bytes after
all required outputs are frozen; that mechanical append is not new authorship.
The combined routine H-main publication occurs before round disposition and
satisfies Stage 5 item 6 when that stage is reached. No other actor may create,
edit, normalize, reorder, or reconstruct the issuer's line.

Unrelated handoff tasks may advance main while reviews run. The finalizer starts
from fresh main only if the integrated packet remains an ancestor and every
protected current-task input path is identical. A verifier walks each
single-parent edge. Changes outside the current task may remain; within it, the
review publication may only add the validated frozen outputs and append their
complete issuer-authored ledger lines. Disposition is a separate post-review
finalizer phase.

The amendment defines the required authority shape, not an ad hoc command
permission. Each round must preregister, freeze, statically review, and rehearse
the exact output-ref producer and finalizer publisher before either can run.

## Independent retirement

The current workflow's literal `master` retirement wording is superseded by
the round's pinned integration ref.

- The candidate ref may be retired only after its exact candidate commit is
  reachable from that integration ref or preserved at the exact pushed
  candidate archive ref.
- The packet ref may be retired only after its exact packet commit is reachable
  from that integration ref or preserved at the exact pushed packet archive
  ref.
- Review-output transfer refs are permanent. Their sibling commits preserve the
  issuer-authored handoff and are not made reachable merely by copying their
  blobs into a different main commit.

Each retirement requires its own fresh direct proof. Reachability through the
packet may satisfy candidate reachability, but deleting either ref never
authorizes deleting the other. Unknown, conflicting, or unavailable state is
preserved and refused.

Neither candidate nor packet ref may be retired before the round disposition is
published. This timing floor applies even when the commits became reachable
from the integration branch before cold review.
