# Proposed workflow amendment: permanent raw-object publication v5

Status: COORDINATOR DRAFT. This file does not amend `docs/workflow.md` by
itself and authorizes no tool execution, repository mutation, credential use,
or remote operation.

Stage0b: cap=3 lock=R002_FREEZE no6=true terminal=r005 ordinal=5 locked=true

This proposal replaces the rejected v4 proposal. It preserves the adopted
workflow's evidence order:

```text
freeze -> review -> tests -> authorize -> ceremonial commit -> push
```

It adds a selected raw-object Stage 2 route, immutable remote slots, acyclic
review-output packages, and concurrent-safe handoff-main publication. It does
not accept candidate code or spend any product experiment authority.

## Narrow scope and explicit supersession

The adopted temporary-index Stage 2 remains unchanged. Historical rounds keep
their existing identities and retirement rules. A round uses this v5 route only
when one upstream canonical `pontius-round-preregistration-v1` names
`raw-object-v5`, the adopted workflow and amendment artifacts, complete
schemas, plan, four-role projection set, accepted utility authority, task,
round, base, endpoint, stable ref coordinates, complete round-review-author
union, two reviewer slots, and sole finalizer. Its complete-byte count and
SHA-256 are repeated through cold input,
authorization, packet, adoption, reviews, main transitions, dispatch, and
runtime revalidation. A prose label or later receipt is not route selection.

For a round selected into `raw-object-v5`, these refs are permanent and
create-only:

```text
refs/heads/review/<task-id>/r<NNN>
refs/heads/handoff-freeze-packet/<task-id>/r<NNN>
refs/heads/handoff-review-output/<task-id>/r<NNN>/<ordinal>
```

For only those refs and only a round whose exact preregistration bytes validate
through the consuming transition, this proposal supersedes:

- the Stage 2 code block's temporary-index object construction, local ref
  update, and candidate-only push; raw-object-v5 uses the canonical object
  grammar, complete local tuple, and one atomic two-ref publication below;
- Stage 5 item 5, which otherwise retires task `review/*` refs; and
- Stage 5 item 6 and the Ledger discipline sentences that require the verdict
  issuer to write `progress.md` at verdict time and forbid another writer. For
  a selected raw-object-v5 round, the issuer instead freezes and publishes its
  exact one-line bytes with the verdict; the single finalizer later appends the
  two issuer-authored blobs byte-for-byte in ordinal order and cannot edit,
  normalize, or synthesize them. The separate Stage 5 program-ledger
  disposition rule remains unchanged; and
- handoff packet rule 4, which otherwise permits retirement after integration
  or archive preservation.

The Stage 2 manifest identity, frozen-blob derivation, round naming, evidence
order, and every review gate remain unchanged. A selected raw-object-v5 round
publishes both permanent refs to the same preregistered handoff endpoint. It
never performs the adopted candidate-only push to the product repository.

The selected refs are never moved, deleted, archived as a substitute, or
reused. Their permanent exact values are monotonic spent evidence. The
temporary-index route, historical refs, and every other Stage 5 and packet rule
remain governed by the adopted text.

The authority-tool bundle that implements v5 cannot select v5 for its own
design or implementation review. Its bootstrap is defined below.

### Stage 0b freeze-tools design-convergence breaker

The current `v0a-i01-freeze-tools-design` r002 through terminal r005 series is
the explicit bootstrap exclusion from the Stage 0b mechanism designed here.
The external coordinator administers it through adopted temporary-index Stage
2, direct Git, and packet rule 6. No Stage 0b JSON object, executable, or later
activation authorizes or retrospectively upgrades this series.

The r005 terminal ruling was made on 2026-09-01 while r002 was mutable and
before any frozen r002 review evidence existed. Five-round preregistration and
six-round A/B histories support at most three corrective successors, r003
through r005. A clean accepted round exits early, and the independent same-
contract residual/design breaker remains. After r002 freeze, a changed P byte
or permitted H review input advances the adopted-workflow round. Alias, rebase,
rename, split, reviewer replacement, or relabeling never resets it.

Both CLEAN defect verdicts make the defect set clean. Implementation eligibility also
requires a nonambiguous adjudication, no blocking finding, and a clear
design/residual breaker. Any WRONG SHAPE verdict or second residual without the
required written override parks as `REDESIGN_DEFAULT_SELECTED`. A
build-eligible r002, r003, r004, or r005 selects `BUILD_IMMEDIATELY` regardless
of interface-change count. Otherwise r002, r003, or r004 may advance exactly
once to close its complete typed blocker set. Ambiguous r005 parks as
`AMBIGUOUS_WIRE_STATE`. Non-CLEAN r005 parks as
`ANALYZER_PATTERN_RECURRENCE` when its interface-change count is positive and
`NONCLEAN_TERMINAL_R005` otherwise. A valid later packet that contradicts the
locked calibration parks as `POST_FREEZE_CALIBRATION_CHANGE`; missing or
different calibration bytes are malformed and refuse before review.

Parking preserves the adopted temporary-index route and the v0a product lane
and authorizes no partial freeze-tool adoption. Resumption requires the one
fresh preregistration permitted by ADR-0482 under a redesigned gate, with the
old panel discarded; it cannot quietly continue this series. No `r006`, task
split, rename, reviewer reset, or one-more-review exception is valid.

The calibration is amendable only before r002 freezes. Freeze makes terminal
r005 immutable; moving it after evidence opens selects `PARKED` with gate-
defect classification. No r006 exists.

The adopted handoff packet binds the candidate tuple, six P paths, H coverage,
two reviewer slots, design-author set, seven canonical terminal-r005 declarations, convergence
policy, and exact review inputs. Each reviewer publishes a typed bootstrap-
design-review receipt, report, and issuer ledger line. The external controller
then publishes the typed design disposition. Only complete
`pontius-utility-bootstrap-design-authorization-publication-v1` with decision
exact `AUTHORIZE_FREEZE_TOOLS_IMPLEMENTATION` permits the H implementation plan,
path-budget map, brief, and start object to freeze. Only the observed H
implementation-start publication opens P source work. The P candidate uses its
exact P base; adopted `candidate.json` remains unchanged. The H packet descends
from H start and adds a separate typed start link binding the P tuple, which is
inadmissible until that packet exists. Later bootstrap
carriers repeat the start, design-authorization, and plan identities.
The implementation start also freezes the candidate/product refs, canonical
ceremonial message and metadata, Tier C, two reviewer slots, and finalizer. Its
deterministic Markdown brief is the byte-identical adopted brief in every later
carrier. Authorship uses complete typed actor/session/path evidence with exact
coverage. The plan's ordered required-test projection contains the three public-
boundary spike commands plus the focused suite, and its digest is repeated
through controller disposition and acceptance. The controller disposition is
reparsed from its retained artifact with exact count, digest, and controller ID.
Design authorization and implementation start bind one upstream external-
retention authority with pinned service namespace, producer, genesis head,
inline Ed25519 public key, verifier, and create-only hash-chain policy. Every
bootstrap and later Stage 0b observation wrapper binds that same authority.

After utility acceptance, a self-excluding
`pontius-stage0b-activation-publication-v1` may enable the Stage 0b counter,
round-freeze anchor, disposition, and build-authority contracts for a different
series. Those prospective objects do not enter the current bootstrap packet.
Every activated calibration, registry, inventory, counter, review, disposition,
and build-authority carrier repeats the activation's exact task, which also
supplies every `<task>` packet and ledger path; cross-task digest equality does
not join objects.

## Names and object symbols

For one task and round:

- `B` is the pinned candidate base commit;
- `C` is the deterministic candidate commit;
- `P` is the deterministic freeze-packet commit whose only parent is `C`;
- `H0` is the exact handoff-main predecessor authorized for packet integration;
- `I(H0,P)` is the exact packet-integration commit;
- `O1` and `O2` are the two utility-review output commits; and
- `F(Hf0,O1,O2)` is the later one-parent main finalizer commit built on the
  fresh authorized main predecessor `Hf0`; and
- `D(Hd0)` is the ordinary one-parent round-disposition commit built on fresh
  H predecessor `Hd0`;
- `U(Bp)` is the P utility ceremonial commit on fresh product predecessor `Bp`;
- `HR(Hr0,U)` is the H integration-record commit on fresh H predecessor `Hr0`
  whose artifacts bind `U`; and
- `HD(Hbd0,HR)` is the H bootstrap durable-disposition commit on fresh H
  predecessor `Hbd0` whose preserved history contains `HR`.

All object IDs are lowercase 40-hex SHA-1. All refs are complete `refs/...`
names. A symbolic ref, abbreviated OID, remote name, wildcard, case variant,
alternate round spelling, or caller-generated path refuses.

The candidate authority remains exactly:

```text
(candidate full ref, candidate commit, candidate manifest SHA-256)
```

The packet, integration commits, output packages, ledgers, and dispositions
coordinate and preserve the review. They never enlarge or replace candidate
identity.

## Selected raw-object Stage 2

The raw route is allowed only for a preregistered complete population of
canonical repository-relative POSIX paths, retained bytes, and ordinary blob
modes `100644` or `100755`. It supports additions and ordinary-blob
modifications only.

A deletion, type change, symlink, gitlink, duplicate, case-fold collision,
file/directory prefix collision, invalid Windows segment, undeclared base
difference, attribute dependency, or filter dependency refuses. That change
uses the temporary-index route or a separately reviewed successor.

The offline builder:

1. validates each retained byte source through a held handle;
2. stores each blob without filters;
3. parses base trees with NUL framing and rebuilds affected canonical binary
   tree bodies without `mktree` or an index;
4. serializes `C` with the canonical raw commit grammar;
5. builds the sorted manifest only from the stored blobs in `C`;
6. builds `P` from the exact candidate and controller-authorized packet inputs;
7. validates the complete object graph through two independent readers; and
8. creates the complete local authority tuple in one transaction.

The builder never uses the real index, checkout, attributes, filters, a working
tree as candidate authority, a network process, or an ambient identity or
clock.

Before local authority creation, it proves:

- `C` has exactly one parent, `B`;
- the complete `B..C` difference equals the declared change population and
  change kinds;
- every affected object has its declared type, mode, blob OID, SHA-256, and byte
  count;
- `manifest.sha256` has exactly the complete sorted whole-row population;
- `P` has exactly one parent, `C`;
- the packet inventory exactly covers its declared additions relative to `C`;
- candidate and packet commit bytes reproduce their expected OIDs; and
- HEAD, the real index, local branches, and working files are unchanged.

## Complete local authority tuple

The builder uses these exact local refs:

```text
refs/pontius/freeze/<task-id>/r<NNN>/intent
refs/pontius/freeze/<task-id>/r<NNN>/candidate
refs/pontius/freeze/<task-id>/r<NNN>/packet-base
```

They target, respectively, the canonical intent blob, `C`, and `P`. The intent
blob binds the task, round, route, base, candidate and packet identities,
manifests, inventories, workflow and amendment identities, plan, schemas,
source projections, role policy, and authorization digest. It contains no
digest or OID of itself.

One `update-ref --stdin` transaction creates all three from absence. Its
dispatch-bound ASCII preimage is exact `start LF`, the three create-only rows in
unsigned-full-ref-byte order, `prepare LF commit LF`, and immediate EOF. The
execution retains the actual accepted-byte count and digest; an extra, wrong,
partial, reordered, or cross-dispatch command is failure even if the intended
tuple later reads exact. The owner
classifies the entire tuple before and after every transaction under the common
repository mutex:

| Tuple population, in precedence order | Result |
| --- | --- |
| any `UNKNOWN` member | `LOCAL_UNKNOWN`; preserve and refuse |
| otherwise any `DIFFERENT` member | `LOCAL_DIFFERENT`; preserve and refuse |
| all `ABSENT` | `LOCAL_ABSENT`; one transaction is eligible |
| all `EXACT` | `LOCAL_EXACT`; complete or lost-ack recovery |
| every remaining proper exact/absent subset | `LOCAL_PARTIAL`; preserve and refuse |

`LOCAL_PARTIAL`, `LOCAL_DIFFERENT`, and `LOCAL_UNKNOWN` are preserved for
diagnosis. No cleanup deletes or repairs refs or objects. Tuple exactness is a
precondition for ordinary publication, not proof that the remote pair exists.

## Canonical candidate and packet inputs

`candidate.json` remains the closed v1 identity object required by the adopted
workflow. Its values are derived from `C` and the manifest, never copied from a
mutable report.

The pre-review packet inputs are governed by closed schemas. The packet includes
only declared cold material such as:

- generated `handoff.md`;
- `candidate.json` and exact `manifest.sha256` rows;
- a FIX round's deferred `coverage.md` and identity;
- workflow, amendment, interpretation, plan, and schema snapshots;
- executable, source, role-policy, and runtime projections;
- preparation and object-verification receipts;
- the cold-input specification; and
- exact integration-overlay source rows and append fragments.

It contains no implementer transcript, self-report narrative, prior candidate
finding, utility-review narrative, candidate-review verdict, review output,
ledger progress snapshot, disposition, retained product evidence, or external
mutable input.

`handoff.md` is generated from the closed cold-input specification and the
derived candidate identity. It has no authored free-form suffix. The packet
source manifest binds the authorized inputs but self-excludes. The packet
inventory binds every packet path, mode, blob OID, SHA-256, and byte count,
including the generated handoff and source manifest.

## Canonical raw commits

Every candidate, packet, integration, reviewer-output, finalizer, disposition,
and utility ceremonial integration commit uses the raw commit grammar in the
r002 Git boundary. The
schema binds exact tree,
ordered parents, author, committer, epoch seconds, UTC offset, message, header
population, separator, and final LF.

The required parent vectors are:

```text
C:  [B]
P:  [C]
I:  [H0, P]
O1: [I]
O2: [I]
F:  [Hf0]
D:  [Hd0]
U:  [Bp]
HR: [Hr0]
HD: [Hbd0]
```

`O1` and `O2` are siblings from the identical cold input. `F` copies their
verified package blobs into fresh main but does not parent either output commit.
The permanent output refs preserve reviewer authorship and package identity.
`U` is the distinct finalizer-authored P result: `Bp` is the freshly observed
product predecessor, `U` has the reviewed `C` tree, and `U` never equals `C` or
either later H record/disposition commit. `HR` uses raw kind
`UTILITY_CEREMONIAL_INTEGRATION_RECORD`; `HD` uses raw kind
`UTILITY_BOOTSTRAP_DURABLE_DISPOSITION`. Both use their controller-frozen
messages and metadata, and `HD` preserves `HR` even if unrelated H commits
intervene between their fresh predecessors. Ordinary `D` remains a different
raw-object-v5 round disposition.

No commit field comes from Git config, environment, a user profile, or the wall
clock. Two clean repositories at different times must reproduce byte-identical
objects and OIDs.

## Atomic permanent candidate and packet publication

The preregistration binds the exact permanent remote pair:

```text
refs/heads/review/<task-id>/r<NNN>
refs/heads/handoff-freeze-packet/<task-id>/r<NNN>
```

These are stable coordinates only. The preregistration contains neither `C`
nor `P`. The later `FREEZE_PAIR` authorization and canonical builder intent
bind their derived target OIDs; putting either result in the preregistration
would create a content-hash cycle.

One closed publisher operation requests their create-only publication in one
atomic HTTPS push, with an empty expected-value lease for each. Sequential
creation, fallback after unsupported atomic push, update, deletion, force
refspec, and repair are absent from the role policy.

After every natural push return before the active deadline, the same dispatch's already
scheduled fresh exact observation classifies both refs. If the active deadline
or another terminal cause terminates the push, cleanup starts no new child or
network operation and emits typed unknown state; a later fresh
`OBSERVATION_ONLY` dispatch must classify both refs before any retry or state
claim:

| Candidate ref | Packet ref | Result |
| --- | --- | --- |
| absent | absent | `PAIR_ABSENT`; a fresh launch may attempt creation |
| exact | exact | `PAIR_EXACT`; terminal success or lost ack |
| exact | absent | `PAIR_PARTIAL_CANDIDATE_ONLY`; fatal, preserve, refuse |
| absent | exact | `PAIR_PARTIAL_PACKET_ONLY`; fatal, preserve, refuse |
| different | absent, exact, or different | `PAIR_DIFFERENT`; preserve, refuse |
| absent, exact, or different | different | `PAIR_DIFFERENT`; preserve, refuse |
| malformed, ambiguous, or unavailable | any | `PAIR_UNKNOWN`; preserve, refuse |
| any | malformed, ambiguous, or unavailable | `PAIR_UNKNOWN`; preserve, refuse |

`PAIR_UNKNOWN` takes precedence whenever either ref cannot be classified. A
syntactically valid wrong target is `PAIR_DIFFERENT` only when both observations are
otherwise complete.

`PAIR_EXACT` is permanent spent evidence. It never authorizes another
push. Because accepted roles contain no update or delete grammar for the pair,
the same transition authorization cannot return to `PAIR_ABSENT` through this
protocol.

Server create-only and no-delete/no-update protection should be enabled and
rehearsed when available. Protocol permanence is enforced by the accepted role
grammars even without that defense. The route makes no historical no-reset
claim against an administrator, leaked credential, or nonconforming writer
unless a separate append-only server or audit source proves it.

## Two-phase fresh-repository adoption

Fresh adoption uses existing roles without merging their authority.

### Network publisher phase

A publisher adoption authorization binds the literal URL, exact remote pair,
expected OIDs, object and packet identities, runtime projection, operation
schema, and output receipt schema. In a normal round those identities follow
from the preregistration and packet. In a rehearsal they equal one selector-
frozen adoption-chain row that names this fetch and one later adopter before any
fetch result exists. Under the publisher policy it:

1. observes `PAIR_EXACT`;
2. fetches only the two exact refs with `--refmap=`, no destination ref, no
   `FETCH_HEAD`, tags, submodules, maintenance, or commit-graph write;
3. observes the same exact pair again;
4. verifies that exact `C` and `P` objects now exist; and
5. issues a canonical adoption receipt with no credential or authority secret.

Fetched objects and pack files are nonauthority residue. The publisher creates
or stores no authority object or ref and chooses no candidate, packet, or intent
identity. It may deterministically serialize and hash the already authorized
intent bytes in memory to populate and validate receipt identities; on rehearsal
the receipt also repeats the selected chain-row digest. It never writes that
intent object or consumes the later adopter fixture.

### Offline builder-adopt phase

A later controller authorization binds the exact adoption-receipt bytes and
SHA-256, expected object graph, complete local tuple, and builder-adopt schema.
On rehearsal it also binds the same adoption-chain row and consumes exactly the
named builder-intent fixture at that row's later adopter coordinate.
The builder has no URL or network operation in its loaded policy. It:

1. validates receipt issuer, operation, observations, identities, and freshness;
2. revalidates `C`, `P`, their parent graph, every manifest and inventory row,
   the canonical intent, and all expected objects through independent readers;
3. classifies the complete local tuple; and
4. creates all three tuple refs atomically only from `LOCAL_ABSENT`.

A crash before the publisher receipt leaves only nonauthority objects. A crash
after the receipt but before the local transaction permits a newly dispatched
offline replay against the same exact receipt. `LOCAL_EXACT` closes a local lost
acknowledgement. Every proper subset, wrong graph, wrong receipt, changed remote
observation, or unbound object refuses without repair.

## Exact packet integration into handoff main

The packet publisher first freezes `P` and establishes
`PAIR_EXACT`. Packet integration is a separate controller-authorized main
transition.

Before constructing any main overlay, the integrator runs the closed
`FETCH_MAIN_INPUTS` transition. An observation-only leg derives a complete
inventory in a new no-ref scratch repository. The mutation leg reobserves and
fetches the same exact full refs into the authority object database without a
destination ref, then reproduces the inventory and issues a fetch receipt.
Overlay construction has no network step and requires that receipt.
The scratch leg begins with the exact fixed unborn-branch seed and ends only
after a complete final inventory proves deepest-first removal or atomic move to
a never-reused quarantine root. Omitted fetch residue or an old root still
present blocks semantic success.

The integration authorization binds:

- exact predecessor `H0`, exact packet `P`, and expected result `I`;
- the literal handoff URL and exact selected `HREF` integration ref, where a
  normal route resolves `refs/heads/main` and a rehearsal route resolves only
  the selector's case-shared, null-task-binding main row;
- the packet inventory and exact source-to-destination overlay rows;
- every shared-file append target, predecessor bytes, fragment, and result;
- the task-protected projection before and after integration;
- canonical commit metadata and the `[H0, P]` parent vector;
- the workflow, amendment, schemas, role policy, and runtime projection; and
- a calibrated wall plus reconciliation policy.

`I(H0,P)` has first parent `H0`, second parent `P`, and no other parent. Its tree
starts from the exact `H0` tree. It copies only authorized exact packet rows,
performs only authorized exact append transforms, and leaves every other `H0`
path byte-, mode-, type-, and existence-equal.

Task protection covers every task-owned path and the exact task-owned records
inside shared append-only navigation files. Other tasks may append their own
records without changing this task's projection.

Before push, raw parsing and an independent ancestry check prove that `I` is a
fast-forward child of `H0`. The main push uses exact `<I>:<HREF>` plus
`--force-with-lease=<HREF>:<H0>` compare-and-swap. Query, fetch, observation,
refspec, lease, and server event all use the same selected full-ref bytes. It has no leading
plus and no separate force option. The lease is force-capable, so the offline
fast-forward proof is mandatory.

## Two-axis main classification

Every preflight and post-push reconciliation obtains a stable exact main
observation from the bound scratch or authority inventory. A bounded phase-
history walk starts at `H0`, consumes every historical transition bundle once,
and follows every intervening first-parent commit to an explicitly validated
`NO_TASK` baseline. Before semantic lineage classification, a separate bounded
all-parent raw-object DAG observation searches every parent edge for `I`.
Unknown or capped DAG state blocks mutation. Reachability only through a
non-first parent is permanently spent `RESULT_SIDE_ANCESTOR` with
`PROTECTED_CONFLICT`; it cannot become fresh eligibility. A separate lineage
walk runs from observed main to the first
`I` or `H0` coordinate, comparing `I` first. At each edge it
records raw commit/first-parent facts separately from a closed task-evaluation
status and reason. It checks task-protected bytes, modes, types, absences, and
shared-file records only after raw lineage is classified. A readable raw chain
can therefore establish `RESULT_DESCENDANT` while unavailable task evidence is
serialized as `TASK_UNKNOWN` without asserting an intact null-evidence edge.
The selected plan binds independent count and canonical-byte caps for both walks and
each inline phase-evidence bundle and reserves one compact failure row. A raw-
chain cap before an anchor yields lineage unknown; a history or task cap after
an exact anchor yields task unknown without erasing lineage or `result_seen`. A
partial prefix never becomes authority.

The independent lineage result is:

- `PREDECESSOR_EXACT`;
- `PREDECESSOR_DESCENDANT`;
- `RESULT_EXACT`;
- `RESULT_DESCENDANT`;
- `RESULT_SIDE_ANCESTOR`;
- `UNRELATED_OR_ABSENT`; or
- `UNKNOWN`.

The independent `task_state` result is:

- `INTACT`: every relevant first-parent edge preserves the protected
  projection;
- `PROTECTED_CONFLICT`: an unauthorized relevant edge changes the projection;
- `TASK_UNKNOWN`: the lineage anchor was found but later protected evidence is
  missing, unreadable, ambiguous, or belongs to a later same-task phase whose
  future bundle cannot enter this old authorization; or
- `NOT_APPLICABLE`: no expected first-parent anchor was established.

The observation also records derived boolean `result_seen`. It becomes true
when the walk encounters `I` and remains true if a later edge or object is
conflicting, missing, or malformed. Such an observation cannot retry the old
transition.

The exact action map is:

| Lineage | Task result | Action |
| --- | --- | --- |
| predecessor exact | intact | eligible for one exact leased push |
| predecessor descendant | intact | `MAIN_PREDECESSOR_CHANGED`; no push |
| predecessor lineage | protected conflict | refuse; no push |
| predecessor lineage | task unknown | preserve and refuse |
| result exact | intact | complete; close lost acknowledgement |
| result descendant | intact | complete; close lost ack |
| result descendant | task unknown | spent; unavailable future-phase evidence never retries |
| result side ancestor | protected conflict | spent; never retry |
| result lineage | protected conflict | `MAIN_PROTECTED_CONFLICT`; spent |
| result lineage | task unknown | `MAIN_UNKNOWN`; spent |
| unrelated, absent, or unknown | not applicable | refuse; no push |

Any lineage containing exact `I` spends this transition even if a later edge
has changed or reverted protected task bytes. Replaying `I` cannot correct a
post-integration conflict. A clean predecessor descendant also cannot inherit
the old authorization: its fresh main parent and deterministic result OID are
different, so the controller must authorize a new exact tuple.

Server protection against main deletion and non-fast-forward updates is a
defense in depth. Without append-only server evidence, first-parent absence
cannot prove historical nonexecution after an administrator or nonconforming
writer performs an ABA reset. The route records that nonclaim and still requires
every accepted writer to use the exact fast-forward transition.

## Blind review-output packages for later selected rounds

After the authority-tool bundle has itself passed the adopted temporary-index,
direct-Git, and packet-rule-6 bootstrap, a later round explicitly selected into
`raw-object-v5` requires exactly two distinct reviewers absent from the complete
round-review-author union. One upstream utility-author set covers every row in
all four reviewed utility source projections. A separate per-round candidate-
author set covers every canonical candidate-change row through frozen content-
authorship evidence and includes every actor or session that implemented,
assembled, generated, or rewrote any change through controller assignment or
receipt evidence. The utility set likewise includes every utility implementer.
Their canonical union is complete before reviewer selection and is bound by the
preregistration, cold input, packet, receipts, and finalizer. Both reviewers
receive the identical immutable `I` cold-input commit
in sanitized no-checkout repositories. Neither receives, fetches, materializes,
or is told the other reviewer's output or findings.

Each reviewer authors one permanent output package under:

```text
refs/heads/handoff-review-output/<task-id>/r<NNN>/<ordinal>
```

The ordinal is `01` or `02` and is bound to the authorized reviewer. Each output
commit has `I` as its only parent and adds exactly four paths:

1. one attributed Markdown report;
2. one canonical receipt document containing exactly four role receipt objects;
3. one issuer-authored ledger-line fragment; and
4. one self-excluding package manifest.

The four role objects are exactly `runtime-owner`, `builder`, `publisher`, and
`integrator`, once each in that order. Across two packages there are eight role
receipt objects, two receipt documents, two reports, two ledger fragments, and
two manifests. There are two reviewer identities, not eight.

### Acyclic package bindings

The canonical receipt document is the sole machine semantic source. Its package
header carries reviewer identity, ordinal, candidate identity, workflow and
schema pins, overall defect verdict, overall design verdict, and the exact
design-justification digest. Each role object carries the exact source-
projection identity and three attestations: complete source population read,
capability grammar read, and no downstream candidate artifact read. Policy,
plan, and runtime bytes are covered through the complete projection population;
there are no separate implied attestation fields.

The receipt binds the already complete report and issuer-authored ledger line
as artifact identities. It contains no digest of itself, package-manifest
identity, manifest digest, output-ref target OID, output commit OID, output tree
OID, or descendant OID. No role object replaces the package-level verdicts.

The report is completed before the receipt. Its fixed header reproduces the
reviewer, candidate, manifest, and package-verdict fields exactly once but does
not bind a receipt identity. Its named design-justification block reproduces
the exact bytes whose digest is later recorded in the receipt. The report does
not bind the receipt, package manifest, output tree, or output commit.

The issuer ledger fragment is exactly one canonical UTF-8 line ending in LF. It
is the new line to append, not a copy or snapshot of `progress.md`. Its fields
derive mechanically from the receipt and report. It contains no mutable current
progress bytes.

The self-excluding manifest contains sorted rows for exactly the report,
receipt document, and ledger fragment. It does not list itself. Its own
complete-byte SHA-256 is external package authority paired with the permanent
output ref.

The dependency direction is therefore acyclic:

```text
report + issuer ledger fragment -> receipt
report + receipt + ledger fragment -> self-excluding manifest
four package blobs -> output commit -> permanent output ref
```

Changing any package byte requires a new candidate round. Both output ordinals
are already fixed and cannot be superseded or reused. Published package bytes
are never edited.

## Independent output publication and `WAITING_FOR_REVIEWS`

Each reviewer-output producer has a separate one-use dispatch and create-only
lease for only its own permanent ref. There is no atomic pair promise across
reviewers; they work independently and may finish in either order.

The finalizer classifies each expected output ref as `ABSENT`, `EXACT`,
`DIFFERENT`, or `UNKNOWN` against its authorized output commit and manifest
SHA-256. The aggregate state is:

| Per-output population | Aggregate state |
| --- | --- |
| any `UNKNOWN` | `OUTPUT_UNKNOWN` |
| otherwise any `DIFFERENT` | `OUTPUT_CONFLICT` |
| all `EXACT` | `OUTPUTS_READY` |
| otherwise only `EXACT` and `ABSENT` | `WAITING_FOR_REVIEWS` |

Thus `EXACT/ABSENT` and `ABSENT/EXACT` are ordinary
`WAITING_FOR_REVIEWS`, unlike the two fatal candidate-pair partial states. The
finalizer performs no main mutation until both exact packages are fetched
without destination refs and fully validated. It never creates, repairs, or
replaces a reviewer-output ref.

## Review finalizer publication for a later selected round

After `OUTPUTS_READY`, the selected future round's single finalizer validates
both package ref plus manifest pairs and the complete acyclic provenance
relation. It starts
from a stable fresh main predecessor `Hf0`. The finalizer authorization binds
that OID, the exact expected finalizer commit `F`, both package identities, the
destination rows, progress predecessor bytes, ledger fragments, append order,
and protected task projection.

`F` has exactly one parent, `Hf0`. Its tree:

- copies the two reports, receipt documents, ledger fragments, and manifests
  byte-for-byte into the declared task paths;
- appends the two exact issuer ledger fragments in ordinal order to the exact
  fresh task `progress.md` predecessor;
- changes only the authorized navigation or review-publication rows; and
- preserves every other path exactly from `Hf0`.

The ledger append is mechanical transport of issuer-authored bytes. It is not a
new verdict or authorship event. No actor reconstructs, normalizes, edits,
reorders, or resolves a reviewer's line.

The finalizer uses its own closed one-parent commit grammar and state machine.
Before push, it proves raw parent, exact overlay, protected projections, and
fast-forward ancestry from `Hf0`. It pushes by ordinary refspec with an exact
lease on `Hf0` and no leading plus or separate force option.

Fresh main classification compares expected `F` before `Hf0` along the complete
first-parent chain and checks the protected review projection at every edge:

- exact `Hf0` plus clean predecessor is eligible;
- a clean descendant of `Hf0` requires fresh authorization and a recomputed
  finalizer commit;
- exact `F` or a clean descendant of `F` closes lost acknowledgement;
- any `F` lineage with later protected conflict is terminal
  `MAIN_PROTECTED_CONFLICT`;
- a predecessor conflict, unrelated history, absence, or unknown state refuses.

`F` deliberately does not make sibling output commits reachable from main.
Their permanent refs preserve the exact reviewer handoffs and are part of why
this route supersedes retirement.

This handoff-main publication records review outputs whether the verdicts are
CLEAN or NOT CLEAN. It is not the evidence-repository ceremonial commit,
controller acceptance, test authorization, product integration, or round
disposition. Those gates retain their adopted order.

Disposition is a separate authorized later main append. It cannot alter issued
packages or reuse either review-output ref.

## Transition authorization, launch dispatch, and mutex

A transition authorization is an idempotent controller object for one complete
state equation. Candidate/packet publication binds exact refs and OIDs. Packet
integration binds exact `(H0, P, I)`. Finalizer publication binds exact
`(Hf0, O1, O2, F)` plus package manifests and destination bytes. Disposition
publication binds exact `(Hd0, D)` plus the finalized-review and controller
artifacts. A main-input fetch authorization binds expected roots; its mutation
precondition binds the exact readiness observation and closed object inventory.
It grants no ref authority.

The stable authorization binds expected selectors and immutable inputs, not an
observation, operation precondition, dispatch, or terminal result. An
observation-only dispatch may therefore run before eligibility exists. The
later mutation dispatch binds the returned canonical observations through its
operation precondition.

Every role-process launch also requires a fresh one-use dispatch with a nonce,
dispatch mode, exact role, operation ID, state-equation digest, operation-
schedule variant and digest, endpoint, runtime projection, wall, and result
schema. It also binds the calibrated active-process cap for each scheduled Git
Job; the role Job remains exact one. One dispatch binds the complete bounded
Git-child schedule program.
Bounded repeats derive only from validated inventories or deterministic raw-
object walk state; runtime evidence records every concrete child. Each network
child has its own step-and-repeat-ordinal-bound one-use broker session. A
separate secret-free terminal result proves adapter-attempt and response count, close,
and broker-credential-buffer zeroing. Success requires exactly one redemption per
network child. A consumed launch dispatch cannot start another role process or
child schedule.
The credential pipe is outbound at the supervisor and read-only at the adapter;
it carries no client-authored request frame. The pipe reservation precedes Git
environment construction, suspended process creation, Job assignment, complete
session binding, and resume. Route or operation mismatch is broker failure
before resume. The supervisor's incremental stdout/stderr counter produces the
typed output-cap fact at the first count above the selected calibrated cap and
repeats that fact through process completion, cleanup termination, and refusal.
Consumption is a permanent create-new controller-registry record flushed,
reopened, validated, and held before process creation. Creation of its canonical
filename spends that plan-and-nonce key even if a crash leaves incomplete
content; unrelated keys remain usable. Out-of-grammar names, case collisions,
nonregular or reparse entries, directory or ACL mismatch, and enumeration
ambiguity block all launches. Crash rehearsal covers every persistence boundary
and a spent nonce always requires a fresh dispatch.

Malformed or noncanonical authorization and dispatch input rejected before
acceptance produces only the canonical protocol refusal and makes no authority-
state claim. Once a dispatch anchor is consumed, a classifiable launch failure
with a live controller/result peer requires phase-valid cleanup, Job quiescence
when a Job exists, and the authority-refusal envelope. A retained parent that
is already signaled instead triggers secret zeroization and Job-zero cleanup,
emits no semantic object or transport receipt, exits host failure, and leaves
the consumed dispatch for a later fresh observation-only classification. If
cleanup cannot complete, no semantic object is
emitted and the controller must classify state with a new observation-only
dispatch.

An `OBSERVATION_ONLY` dispatch may always be issued for an exact frozen state
equation. It cannot write the authority object database, update a ref, or push.
If remote graph bytes are needed, it may fetch only into a new dispatch-owned
scratch database with no refs. A `MUTATION_ATTEMPT` dispatch may be issued only
after an observation-only result proves the same exact transition eligible; it
repeats the decisive observation immediately before mutation. Its closed
schedule variant is mechanically derived from the fresh precondition. A
terminal exact observation closes idempotently and starts no mutation dispatch;
no bound schedule step is silently skipped. Lost-ack reconciliation therefore
does not depend on prior mutation eligibility.
Every network child keeps immutable process-completion facts. Only complete
bounded push porcelain becomes typed parsed status; query and fetch rows use
their own typed observations. After the required fresh post-observation, the
owner assembles a transport outcome. The frozen operation rule selects the first
non-success outcome, or the last when all succeed. An accepted write with lost
client acknowledgement remains authority success when fresh reconciliation
proves the exact durable result, then a following observation proves idempotent
closure.

All local classifiers and writers for the repository acquire the same visible
repository-scoped authority mutex. The owner holds it from the first state read
through object checks, local transactions, child exit, remote reconciliation,
receipt durability, active-process-zero, and final identity revalidation.
The action prefix is exactly `[CLASSIFY_LOCAL_REFS]` for read-only work or
exactly `[CLASSIFY_LOCAL_REFS, MUTATE_LOCAL_REFS, OBSERVE_LOCAL_REFS]` for a
mutation. The mandatory suffix ends by binding the self-free final-revalidation
core. The owner then records same-thread release and handle close, completes
the lifecycle, and only afterward constructs the outer final-revalidation
object. Timeout, failure, or abandonment records no protected mutation and
cannot satisfy a successful transition.

Packet-integration attempt refs are qualified by authorization digest. The
intent ref and expected-result ref are created together locally before a remote
push. They are reconstructible residue, not remote authority, not global spent
evidence, and not atomic with main. A proper subset or wrong value refuses.
Their one local transaction uses the same exact dispatch-bound
`GIT_UPDATE_REF_CREATE_LF_V1` preimage, with the two ordered create rows and
retained actual stdin-write fact. Intended-pair exactness cannot substitute for
that complete stream and immediate EOF.

## Utility bootstrap without recursion

The v5 authority utilities and their design authority bootstrap only through:

1. the temporary-index Stage 2 procedure in the already adopted workflow;
2. the already adopted direct Git executable; and
3. ordinary handoff packet rule 6 commits and pushes.

The adopted bootstrap brief pins the workflow SHA-256, candidate base, task and
round, exact candidate ref, complete path population, tier, required reviewers,
and finalizer. It is not a `pontius-round-preregistration-v1`. Utility reviewers
publish reports and issuer ledger lines through existing rule 6. No v5 builder,
publisher, output-ref producer, credential broker, or integrator may establish
its own review or acceptance or create a v5 selector for the bundle.

The reusable utility-acceptance authority embeds a canonical bootstrap-evidence
object with the adopted brief, temporary-index candidate publication, rule-6
packet publication, both independent rule-6 review publications, every required
test, the exact downstream HTTPS rehearsal result set, controller authorization,
the authorizing implementation-controller disposition, ceremonial integration,
fresh exact remote push observation, durable disposition, and external terminal-
observation retention. The P construction transcript orders the fresh
predecessor query, acceptance of the complete authorizing controller
disposition, and only then ceremonial-input assembly; its build receipt and
result carry that transcript. Ceremonial integration is a distinct finalizer-authored P commit:
its tree equals the reviewed candidate tree, sole parent is the fresh P
predecessor, and raw commit bytes use the frozen message and metadata. The P
predecessor comes from the distinct self-free pre-push-query receipt and
ordering transcript, never the later push-bound query type. The P result is
pushed by compare-and-swap and proven by the distinct post-push observation
before H publishes every self-free receipt in its separate integration record
and then the full controller-disposition triple in durable disposition.
Each H observation core has an external write-once receipt verified under the
pinned authority. Future Stage 0b round-freeze, review-result, disposition, and
build-authority observations use that same finite retained wrapper.
Validators rederive all commit, ref,
manifest, parent, artifact, and repeated-identity relations. A free disposition
artifact or verdict list cannot substitute for this closed historical chain.

Runtime dispatch authority carries only `worker_launch_attempt`; the actual
call outcome remains downstream. Every rehearsal network step has an
independently verified signed server lifecycle. Scaled calibration workloads,
typed scratch parent/move facts, bound broker I/O identities, repository
ancestor chains, and mutex retention milestones remain exact runtime evidence.
Supervisor exit exists only in the post-exit transport or loss receipt.
Result-peer loss exists only in `pontius-outer-session-loss-receipt-v1`; it
never enters the delivered transport receipt or flows backward into runtime
evidence.

After the utility bundle is independently CLEAN, SOUND or explicitly accepted
by design disposition, tested, proven through the complete expected-equals-
observed HTTPS rehearsal result set, controller-authorized, then issued the
implementation-controller disposition with decision exact
`AUTHORIZE_CEREMONIAL_INTEGRATION`, ceremonially integrated, pushed,
dispositioned, and externally retained, a later round may select v5.
Bootstrap authority is
the immutable historical packet commits and blob identities, never a mutable
packet file or transcript.

That result set binds the selector's complete campaign, pure derived-input
contracts, typed fixtures, adoption-chain set, reviewed fault-harness component
bindings, disjoint case refs, and pre-production/pre-rehearsal capability
observations. Every
fault uses a fresh dispatch-bound reservation and activation artifact; server
faults additionally require the nonce-correlated event and canonical ref-update
set. Every case ends with a fresh capability observation using new fact sources.
Labels or expected values cannot establish these facts.

## Failure, recovery, and nonclaims

Every unknown, malformed, incomplete, conflicting, or unavailable observation
preserves state and refuses mutation. Exit status and raw push output are never
state authority. A complete bounded parsed push status may record transport
cause, but fresh remote observation and object validation decide the result.

Objects fetched without refs may remain as nonauthority residue. Governed refs
and published package bytes are never cleaned up to manufacture an initial
state. No accepted route rewrites main, deletes permanent slots, stores or
erases a credential, or repairs half of an atomic pair.

This proposal does not claim protection from a repository administrator who can
disable server rules, rewrite protected history, or delete permanent refs.
Server permissions are recorded and rehearsed; an append-only historical claim
exists only when a separate server or audit control proves it. The exact HTTPS
mutation path remains a mandatory disposable rehearsal.

This proposal also does not claim that design text proves AppContainer behavior,
native loading closure, askpass secrecy, atomic server support, timeout
calibration, or crash recovery. Those are falsifiable implementation gates. A
local mock, post-load observation, prompt match, read-only query, or green unit
test cannot substitute for the real public-boundary evidence.
