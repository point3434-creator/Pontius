# v0a-i01-freeze-tools r002 design

Status: DRAFT FOR DESIGN REVIEW. It authorizes no implementation or execution.

Stage0b: cap=3 lock=R002_FREEZE no6=true terminal=r005 ordinal=5 locked=true

This is a replacement design for rejected r001. It keeps the four logical roles
and raw-object goal, but removes the two shapes that caused the rejection: one
authority-bearing shared Python layer and one post-load runtime audit presented
as confinement.

## Authority and correction inputs

The frozen r001 candidate is commit
`ad8fbcc1ae5a9e3c3b61ae93d5ae5c0b3e4d289e` with manifest SHA-256
`862d245f838f4b7459b6ce2aae19eede3b77a4861575722817db12d63af7b689`.
Its two formal cold reviews both returned `NOT CLEAN`; their design verdicts
were `WRONG SHAPE` and `STRAINED`. The coordinator accepted the stricter
remedy: replace the runtime and capability shape before implementation.

The r002 candidate is completed by these peer documents, all bound externally
by the frozen candidate manifest:

- `2026-09-01-v0a-i01-freeze-tools-runtime-boundary.md`;
- `2026-09-01-v0a-i01-freeze-tools-git-boundary.md`;
- `2026-09-01-v0a-i01-freeze-tools-schemas.md`;
- `2026-09-01-raw-object-workflow-amendment-v5.md`; and
- `v0a-i01-freeze-tools-r002-brief.md`.

No document embeds a mutable sibling path or relies on its own digest. The
candidate manifest and handoff identify the exact frozen bytes.

## Decision

Build one trusted Windows authority owner, one minimal native Python bootstrap,
three mutually unavailable role policies, and three role-specific pure-Python
planner archives. The planner proposes only canonical typed operations. The
owner checks each proposal against the only role policy loaded for that launch
and performs the permitted file or Git operation itself.

The common population contains only canonical encoding, hashing, file identity,
framing, exact process ownership, and typed refusal mechanisms. It contains no
repository endpoint, ref selector, credential path, pair transition, main
transition, or raw command interface. Role policy supplies those values as a
closed table. A builder launch does not load the publisher or integrator table,
archive, adapter, or source.

This is a trusted-code architecture with an OS-enforced planner boundary. The
reviewed owner remains powerful by design; a hostile controller or owner is
outside the claim. The Python planner is denied repository, profile, network,
and process authority so an import or parsing defect cannot silently widen its
role.

### Stage 0b design-convergence breaker

The exact Stage 0b counter and decision schemas are prospective implementation
contracts. This `v0a-i01-freeze-tools-design` r002 through terminal r005 series
is their explicit bootstrap exclusion. Its design freeze, two reviews,
controller disposition, and implementation authorization use the already
adopted temporary-index Stage 2, direct-Git, and handoff packet-rule-6 workflow.
No Stage 0b JSON object or future executable authorizes or retrospectively
upgrades the series that creates it.

The external coordinator set terminal r005 on 2026-09-01 while r002 was mutable
and before any frozen r002 review evidence existed. Five-round preregistration
and six-round A/B histories support three corrective successors, r003 through
r005, as a cap. CLEAN may exit earlier. The same-contract residual/design
breaker remains independent. Draft edits before r002 freeze stay in r002;
afterward a changed P byte or permitted H review input advances the
adopted-workflow round. Alias, rebase, rename, split, reviewer replacement, or
relabeling never resets the sequence.

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
r005 immutable; changing it after review evidence opens is tuning against
evidence and selects `PARKED` with gate-defect classification. No r006 exists.
After utility acceptance, the same machine-readable rule applies only when a
self-excluding `pontius-stage0b-activation-publication-v1` names a different
series. Every activated calibration, registry, inventory, counter, review,
disposition, and build-authority carrier repeats that activation's exact task
and uses it for every packet and ledger path.

## Goals and observations

The checkpoint must make six facts independently observable:

1. one reviewed source and runtime projection, and no sibling role policy, was
   reachable before the planner processed authority input;
2. every Git object equals independently parsed canonical bytes;
3. each local or remote transition either changes the complete authorized tuple
   once or preserves a classifiable refusal state;
4. a credential can reach only one bound Git operation and no durable store;
5. main history preserves both the packet parent and every intervening
   first-parent transition; and
6. every review verdict and ledger line is attributable, byte-bound, acyclic,
   and cold-input independent.

Receipts record these observations but never substitute for fresh runtime,
object, ref, graph, source, credential-route, session-lifecycle, or package
revalidation.

## Alternatives rejected

Patching r001's shared Python layer was rejected because the missing capability
grammar and pre-load boundary are structural. Adding more module, DLL, or data
audits would still observe influence after it became possible.

Launching stock `python.exe` with `_pth` was rejected as the enforcement layer.
It isolates path initialization, but `python311.dll` loads before Python code can
set DLL policy, import machinery remains mutable, ZIP imports reopen archives,
and built-in process facilities remain present.

Writing every utility in native code was rejected because canonical schemas,
Git object parsing, and fault-state logic would become harder to inspect and
would duplicate role mechanics. The selected planner keeps deterministic logic
in small Python archives while Windows denies it authority and the owner keeps
all external effects typed.

Using only the adopted temporary-index route remains a valid fallback and is the
bootstrap for this bundle. It was not selected as the permanent route because
it intentionally passes bytes through an index and add-time normalization and
does not supply the closed automated publication, adoption, output, and
first-parent reconciliation needed for the C lifecycle. If the native boundary
spikes miss their breaker, the raw route parks and this fallback requires a new
controller checkpoint rather than a weakened emulation.

## Review pressure points

The selected design is easiest to get wrong in these places:

- loading or parsing more than one role policy before dispatch validation;
- treating AppContainer or a loaded-image list as a universal Windows sandbox;
- allowing the planner to supply a string later used as argv, config, URL, or
  ref authority;
- treating askpass prompt text as proof of operation, repository, or TLS peer;
- using a lease as proof that a main update is a fast-forward;
- collapsing result occurrence and current protected-byte validity into one
  state;
- including an adoption receipt in the canonical normal-builder intent;
- treating one ready reviewer output as an atomic-pair partial failure; or
- allowing a receipt or manifest to name an object that depends on its bytes.

The cold review and later tests start with these seams rather than the examples
that happened to fail in r001.

## Decisions and project tie

No architecture choice remains for the implementer to settle silently. The
permanent-slot rule, two-parent initial integration, one-parent finalization,
four-role review set, AppContainer planner boundary, and GCM removal are proposed
normative choices in this candidate. A reviewer may reject them; implementation
may not substitute an easier mechanism under the same round.

Acceptance makes only the authority-tool implementation round possible. After
that implementation, tests, reviews, calibration, and HTTPS rehearsal pass, the
controller must first freeze one canonical
`pontius-round-preregistration-v1` outside the utility route. Only then may a
separate dispatch freeze the existing v0a C candidate. This design does not
alter the C candidate, its RED/GREEN evidence, or its ceremonial finalizer.

## Bootstrap root

The utility bundle cannot use a route implemented by the bundle to establish
its own authority. Its design and later implementation freeze through the
already adopted temporary-index Stage 2 procedure. Review reports and exact
issuer-authored ledger lines publish through the already adopted direct-Git and
handoff packet rule 6 path.

The bundle cannot create or use a raw-object-v5 round preregistration for its
own design or implementation. A later controller-created preregistration binds
the exact workflow and amendment artifacts, schemas, plan, complete four-role
projection set, accepted utility authority, task, round, base, endpoint, stable
ref coordinates, complete candidate/utility review-author union, two reviewer
slots, and finalizer. Its external byte count and SHA-256 are the sole route-
selection identity.

This r002 documentation review issues attributed typed bootstrap-design-review
receipts, reports, and exact issuer ledger lines under adopted packet rule 6. It
has no implementation source or runtime projection and therefore cannot issue a
four-role source receipt. Its verdicts are never upgraded after the fact.
Candidate authority remains the source ref, commit, and manifest SHA-256. The
handoff packet freezes the two reviewer slots, complete design-author set,
seven canonical terminal-r005 declarations, convergence policy, and exact review inputs. Each cold
reviewer is absent from the design-author set and attests that its report froze
before it opened the peer report. The external controller is also absent from
the design-author set and publishes the typed design disposition only after both
review publications exist.

Only the self-excluding
`pontius-utility-bootstrap-design-authorization-publication-v1` with nested
decision exact `AUTHORIZE_FREEZE_TOOLS_IMPLEMENTATION` permits freezing the H
implementation plan, path-budget map, Markdown brief, and start object. Only the
authorization and start also bind one upstream self-free external-retention
authority: service namespace, authorized producer, genesis head, Ed25519 public
key bytes, verifier identity, and create-only hash-chain policy. Only the
start freezes the candidate/product refs, canonical ceremonial message and
metadata, Tier C, two reviewer slots, and finalizer. Its deterministic Markdown
rendering is the exact adopted brief repeated by every later bootstrap carrier.
Only the
remotely observed self-excluding implementation-start publication opens P
source work. The P candidate has the plan's exact P base and carries no H start
field or H ancestry; adopted nine-key `candidate.json` is unchanged. The H
packet descends from H start and adds a separate typed start link binding
the independent P tuple, which is inadmissible until that packet exists. Both
implementation reviews, the rehearsal selector,
controller authorization, bootstrap evidence, and utility acceptance repeat the
start, design-authorization, and plan identities. No tool, implementer, or
reviewer can issue or reinterpret the controller decision.

The Stage 0b counter, review, atomic anchor, disposition, and build-authority
schemas in this candidate remain prospective until the accepted utility is
published and a later self-excluding activation names a different series.
The later implementation bootstrap instead freezes one acyclic
`pontius-utility-rehearsal-selector-v1` after its candidate, rule-6 packet, two
complete implementation review receipts, tests, source projections, paired
production/rehearsal tables, campaign, derived-input contracts, typed fixture
set, typed adoption-chain set, reviewed fault-harness projection, case-qualified
refs, and pre-campaign server-capability observations are fixed. Each rehearsal
adoption fetch selects exactly one later adopter and its builder-intent fixture
through a chain row fixed before the selector; fetch receipts and adopter
authorizations repeat that row digest. A case may bind multiple task/round
pairs. Each step selects one case-local binding; the selector root remains the
utility-bootstrap identity. Task-scoped refs use that binding, while the case's
shared `HANDOFF_MAIN` row has none. That owner-only selector authorizes only the
preacceptance HTTPS campaign. Each case obtains a fresh post-case
capability observation; fault reservations use fresh attempt nonces and bind the
current dispatch. Its complete downstream result set and controller
authorization feed the implementation-controller disposition. Only decision
`AUTHORIZE_CEREMONIAL_INTEGRATION`, followed by ceremony, disposition, and the
externally retained acceptance observation, establishes utility acceptance. It can
never substitute for a normal raw-object-v5 preregistration.

The exact four review roles are:

1. `runtime-owner`;
2. `builder`;
3. `publisher`; and
4. `integrator`.

For the later frozen implementation checkpoint, exactly two independent bundle
reviewers each issue one package-level report, one exact ledger-line blob, and
one canonical receipt document through direct Git and packet rule 6. Each
receipt document contains a package header plus exactly four role receipt
objects over the then-frozen source and execution projections. This means eight
role receipt objects in two documents, not eight receipt files or reviewer
identities. Only an accepted implementation may automate the same package shape
for later raw-object-v5 rounds.

Utility acceptance also embeds one canonical bootstrap-evidence object. It
closes the adopted bootstrap brief, temporary-index candidate publication,
rule-6 packet and two review publications, complete plan tests, exact HTTPS
rehearsal result set with every post-case capability recheck, controller
authorization, authorizing implementation-controller disposition, ceremonial integration, fresh
remote push observation, and
durable disposition. Exact commits, refs, manifests, artifact bytes, parent
relations, and repeated identities are revalidated in that order. A disposition
blob or CLEAN labels without this historical chain cannot install the utility.
The ceremonial integration is a distinct finalizer-authored P raw commit whose
tree equals the reviewed candidate, parent is the fresh P predecessor, and OID
is independently rendered, stored, reparsed, compare-and-swap pushed, and
freshly observed. The predecessor uses the distinct self-free pre-push query;
the controller transcript then byte-binds the complete authorization and
authorizing disposition before ceremonial-input assembly and raw rendering.
The build receipt and result carry that same transcript. The later result uses
the push-bound post-push query. H then publishes every
self-free receipt in a separate integration record and the complete controller-
disposition triple in durable disposition; neither H commit equals the P result.
Every H publication's post-push observation core receives a non-Git external
controller write-once retention receipt verified only under the pinned
authority. Future Stage 0b round-freeze, review-result, disposition, and build-
authority publications use the same self-free-core/retained-wrapper contract.
The acceptance wrapper's retained observation terminates receipt recursion and
is required for bootstrap success.
Exact typed authorship
coverage, four ordered required tests, and reparsed controller-disposition
artifact/count/digest/controller identity also close through acceptance.

Before reviewer selection, one canonical utility-author set attributes every
source entry in all four reviewed projections under the frozen attribution
rule. Its `authors` population is mechanically the union of those rows. The
cold-input spec, all projections, freeze authorization, packet artifact, and
acceptance authority bind the same complete bytes; a later free author list is
invalid.

For each later candidate round, a separate candidate-author set attributes
every canonical change row from frozen upstream authorship evidence. A round-
review-author set is the mechanical union of candidate and utility authors.
Reviewer slots are selected only after that union is complete; neither reviewer
may appear in it. These per-round sets do not enter reusable utility acceptance.

## Runtime and source projections

The authority owner receives a canonical one-use launch dispatch from the
trusted controller. It validates and holds every selected source, binary,
archive, policy, schema, authorization, and file-backed input by exact path,
byte count, SHA-256, final handle path, and 64-bit-volume-plus-128-bit
`FileIdInfo`. It retains the complete projection through process-tree
quiescence and final reconciliation.

A minimal native bootstrap has only preregistered static dependencies. It sets
the DLL search policy before loading an absolute held `python311.dll`, then
initializes CPython through isolated `PyConfig`. Each role gets one stored ZIP
archive containing its exact pure-Python standard-library closure, copied pure
shared kernel, and role planner. Native extensions are never imported from ZIP;
every admitted
native image is preloaded from the sealed projection before `RUNTIME_LOCKED`.

The planner runs inside the preregistered AppContainer identity with no network
capability, no child-process capability, a one-process Job limit, and file
access only to the sealed runtime projection and its local framed channel. It
does not open a repository or candidate path. The owner supplies held input
bytes through the channel and receives typed proposals through the same
bounded protocol.

After startup imports and native images are closed, the bootstrap removes the
remaining import routes and emits `RUNTIME_LOCKED`. Later import, native load,
profile read, runtime-data read, process creation, network use, or unlisted file
open is a refusal. Module and image enumeration remains corroborating evidence;
it is not the enforcement mechanism.

The runtime appendix defines the exact loader, AppContainer, ACL, Job, handle,
archive, image, environment, handshake, and cleanup rules. A missing exact
AppContainer provisioning identity or uncalibrated wall blocks live use.
Runtime lock is followed by handle duplication, a bootstrap broker-attach ACK
on the still-open attestation channel, and typed terminal closure; attestation
alone never establishes attachment. Runtime evidence also binds typed
supervisor exit/result-peer-loss semantics, measured limit-calibration
receipts, exact scratch seed and terminal remove-or-quarantine inventory,
repository-mutex lifecycles, and same-handle directory-open access/share/flags/
granted-access facts. A lifecycle's last held milestone binds the self-free
final-revalidation core; release and close precede construction of the outer
revalidation object that carries the completed lifecycle array.
Launch dispatch carries only the immutable `worker_launch_attempt`; the actual
call result, result-peer loss, and supervisor exit remain in later typed
evidence layers. Scratch teardown binds typed parent observations and atomic
move facts. Repository projections carry complete ancestor chains, and mutex
lifecycles retain digest-bound milestones through final revalidation.

## Typed owner boundary

Planner frames use the schema appendix's exact one-byte kind plus eight-byte
little-endian length prefix. Canonical ASCII JSON request/reply envelopes carry
only typed metadata; separately tagged, bounded binary chunks carry large raw
object bytes under a complete hashed stream descriptor. Every request binds
the dispatch, role, transition operation, owner-request ID, next static step
and repeat ordinal, contiguous sequence, predecessor-state digest, and complete
typed payload. Every reply binds the complete request and result. The owner
rejects an unknown key, duplicate key, wrong type, out-of-order or reused
sequence, wrong schedule coordinate, wrong predecessor, oversized frame,
trailing byte, or noncanonical encoding before an operation.
The owner hashes and parses binary streams incrementally. Runtime evidence
retains their descriptors and object facts without copying raw repository
objects into a terminal JSON document.

An operation ID is an enum from the selected role policy. The payload contains
only the closed typed values admitted for that operation. It cannot contain a
program path, arbitrary argv element, command suffix, environment key, Git
configuration pair, URL, ref name, refspec, credential selector, shell text, or
transport selector. The owner derives every such authority value from the held
role policy and current authorization.

The shared owner implements exact process mechanics but has no open command
API. A policy table maps a typed owner request to one fixed executable,
complete argv grammar, complete environment grammar, working directory, input
frame, output parser, timeout, reconciliation rule, and allowed next state.
The dispatch-selected schedule fixes request order and bounded repeats. Values
that vary by task are schema fields already bound by authorization, never
planner-selected strings.

One scheduled process reports only its bounded lifecycle completion. It cannot
also serve as its own ref, remote, fetch, or receipt postcondition. The frozen
schedule follows every mutation or fetch with independent observation steps;
owner-internal no-process assembly then constructs any multi-input receipt or
observation set from the complete accepted transcript and still-held sources.
Successful runtime evidence requires a `COMPLETE` schedule expansion. A failure
cleanup instead carries a complete schedule object whose `ABORTED` branch fixes
the exact contiguous prefix and terminal boundary, or whose `COMPLETE` branch
proves the failure occurred afterward. Broker sessions and results, decisive
transport outcomes, returned object-write facts, and physical residue all close
over that same transcript. An unaccounted started child or prior reply prevents
an in-launch authority refusal. Preaccept protocol refusal carries no authority
or cleanup claim.
Neither exit zero nor Git output can enter terminal authority as state evidence.

## Role capabilities

The role grammars are closed now. Builder operations are `FREEZE_PAIR`,
`ADOPT_PAIR`, and `BUILD_REVIEW_OUTPUT`. Publisher operations are
`PUBLISH_PAIR`, `FETCH_FOR_ADOPTION`, and `PUBLISH_REVIEW_OUTPUT`. Integrator
operations are `FETCH_MAIN_INPUTS`, `BUILD_MAIN_OVERLAY`, `INTEGRATE_PACKET`,
`FINALIZE_REVIEWS`, and `PUBLISH_DISPOSITION`. The schema appendix defines each
operation's exact
predecessor, inputs, generated objects, permitted refs, and terminal
observations. Adding an enum member is a new design round.

Every operation authorization and launch binds one exact route-selector
identity. Normal raw-object-v5 work uses a complete round preregistration; only
the implementation's preacceptance HTTPS campaign uses the utility-rehearsal
selector. Runtime results and durable objects whose schemas carry that selector
repeat the same identity. The two selector kinds cannot substitute for each
other, and a route name, operation ID, ref spelling, or later receipt cannot
create authority.
The route-selector identity is distinct from a static source-bound-document
identity. Source projections are accepted before the selector is created. The
authorization binds its schema, byte count, and SHA-256; the launch dispatch and
runtime evidence carry and hold the complete canonical selector through final
revalidation. Projection membership is neither required nor permitted as a
substitute for that held preimage.
Normal authorization task and round equal the preregistration root. Rehearsal
authorization, dispatch, runtime evidence, and result task and round equal the
selected campaign binding, not the selector root, and repeat its binding ID.

The owner selects the role from the controller's launch dispatch and selects an
operation from the transition authorization. The planner can confirm only that
same pair. No role or operation value received from the planner affects table
selection.
Trusted native bootstrap derives one capability-safe planner launch view and
selects the frozen `(module, callable)` entry for that operation. Python receives
only that view and later `delivery=PLANNER` rows through typed replies; the full
dispatch, selector, repository projection, precondition, and owner-only rows
remain native-owner state.

### Offline builder

The builder planner receives held source bytes, base object bytes, exact path
rows, cold-input specification, and fixed metadata. It independently derives
blob bytes, binary tree bytes, manifest rows, packet bytes, and canonical raw
commit preimages. Its executable code, role policy, and actionable typed inputs
contain no endpoint, credential, remote-ref, or main-transition selector.
Artifact and evidence bytes may be parsed and may be authoritative for
deterministic content, but they are non-authoritative for capability selection.
No value derived from them may populate an owner endpoint, ref, refspec,
credential, argv, role, operation, executable, or table selector; those values
come only from held policy and controller authorization.

Main overlays and their raw commits belong only to the integrator. Moving that
construction out of the builder prevents the builder grammar from acquiring a
main predecessor, main path, or main-phase vocabulary.

The builder policy permits only exact repository validation, object read,
`hash-object -t <type> -w --stdin` for a planner-supplied already validated raw
object, and one complete local `update-ref --stdin` transaction. It forbids
checkout, the real index, attributes, filters, hooks, maintenance, alternates,
replacement objects, shallow state, and any network-capable Git operation.
That transaction is an owner-derived canonical object in the launch dispatch:
ASCII `start`, the complete ordered create-only ref set, `prepare`, `commit`,
and immediate EOF. Schedule evidence retains both the intended stream and the
actual bytes accepted by the child's private stdin. Exact post-state cannot
hide an extra, wrong, partial, or cross-dispatch command stream.

The owner receives a held repository projection, not a directory for Git to
discover. It models direct worktrees, linked-worktree gitfiles and commondir,
or bare repositories explicitly. Git receives exact `--git-dir` and, when
applicable, `--work-tree` arguments. The shared mutex derives from the common
Git directory identity, so sibling linked worktrees cannot race through
different lock names.

The projection is an immutable physical baseline, not a promise that an
authorized object write leaves the objects directory unchanged. Every schedule
that can store a semantic object retains one complete object-write plan in its
execution and runtime evidence. A complete post-Job storage observation maps
each new loose or pack-family carrier to that plan or to one complete built or
fetched inventory. The plan branch accounts for standalone builder and
integration intent blobs without requiring a downstream receipt. A missing
plan member, extra semantic object, changed baseline carrier, or forbidden
sidecar blocks authority.

The round preregistration binds only selector-pinned candidate, packet, review-
output, and main ref coordinates plus the endpoint selector. Builder-intent and
anchor refs are stable route-derived values and have no preregistered full-ref
field. Integration-attempt refs have only closed descriptors upstream; their
full values are derived after the complete external transition-authorization
digest exists. The preregistration contains no candidate, packet, output, or
main result OID. Later authorizations bind the deterministic targets. This order
prevents a content-hash cycle.

The normal builder creates these three refs together from complete absence:

```text
refs/pontius/freeze/<task>/<round>/intent
refs/pontius/freeze/<task>/<round>/candidate
refs/pontius/freeze/<task>/<round>/packet-base
```

They target the canonical intent blob, candidate commit, and packet commit.
Every authoritative classifier and writer holds the same repository authority
mutex. An exact whole tuple is idempotent recovery. Any proper subset,
different value, malformed state, or unknown observation preserves and refuses.

### Pair publisher

The publisher planner receives the exact accepted local tuple and graph. It
cannot synthesize an authority object, create an authority ref, or update main.
An exact fetch may materialize validated unreachable object residue. Its role policy permits a
strict literal-URL pair query, one atomic create-only pair push, the exact
source-only adoption fetch, and the required fresh reconciliations.

Both permanent refs publish to the same preregistered handoff-repository
endpoint. Raw-object-v5 explicitly replaces the adopted Stage 2 candidate-only
product-origin push for a selected round. The product repository remains
unchanged until the separately authorized Stage 5 ceremonial integration.

The candidate and packet refs are permanent write-once slots for this selected
raw route. Both absent permits one atomic push with empty expected-value leases.
Both exact is terminal `PAIR_EXACT`. One exact and one absent is one of the
fatal `PAIR_PARTIAL_*` states because these refs must have been created together. A different,
malformed, ambiguous, or unavailable observation refuses.

Fresh adoption has a network and an offline phase. The publisher fetches only
the exact advertised objects with no destination refs, `FETCH_HEAD`, refmap,
tracking ref, tag, submodule, maintenance, or commit-graph write and emits a
bound adoption receipt after a second exact pair query. A later one-use
builder-adopt dispatch validates the receipt and complete graph offline, then
creates the same canonical intent and three-ref tuple as normal construction.
The adoption receipt is downstream provenance and never changes the intent.

### Main integrator

The integrator cannot publish the pair or reconstruct a candidate. Separate
authorizations govern `FETCH_MAIN_INPUTS` and `BUILD_MAIN_OVERLAY`. After both
succeed, `INTEGRATE_PACKET` receives one publication authorization binding
exact main predecessor `H0`, packet `P`, result `I`, and the validated fetch and
build provenance.

Before any main overlay is built, `FETCH_MAIN_INPUTS` uses a scratch-only
observation to close the required graph, then fetches exact main and permanent
input refs into the authority object database without destination refs. It
issues a receipt only after stable before/after observations and complete
object-inventory equality. The scratch repository begins with the fixed unborn-
branch seed and must be completely inventoried, then removed deepest-first or
atomically quarantined to a never-reused root before semantic success.
`BUILD_MAIN_OVERLAY` requires that receipt and has no
network step. Packet integration fetches main plus candidate and packet;
finalization and disposition fetch main plus both permanent reviewer outputs.

`I(H0,P)` has exactly two parents: first `H0`, second `P`. Its tree is `H0` plus
the authorized packet overlay and no other change. The owner verifies the raw
parent order, tree, overlay, object graph, remote pair, and fresh main value
before creating its authorization-keyed local attempt pair.

The integration route resolves one typed `HREF` from the selected table and
route selector: exact `refs/heads/main` for normal execution and the case-
shared, null-task-binding main row for rehearsal. Query, fetch, observation,
refspec, lease, and server event use that identical value. The only integration
push has ordinary `<I>:<HREF>` and explicit
`--force-with-lease=<HREF>:<H0>`. It has no leading
`+` and no `--force`. Because the lease option can perform a non-fast-forward
update, the owner proves `H0` is the first parent of `I` and that the transition
is a fast-forward before starting Git. The lease is not ancestry evidence.

A stale predecessor never authorizes rebuilding. It requires fresh controller
authorization and a new authorization digest namespace.

## Deterministic Git objects

The planner serializes every derived blob, tree, and commit body. For an already
frozen `STATIC_BLOB`, the owner feeds the held source directly under the same
object plan and exposes only verified object facts to the planner. Git stores
only already determined bytes. Trees use canonical binary Git tree form with
exact path ordering, mode,
name, NUL, and raw child OID. Every commit preimage fixes:

- tree OID;
- complete ordered parent OIDs;
- author name, email, timestamp, and offset;
- committer name, email, timestamp, and offset;
- absence of optional headers unless the schema explicitly requires one;
- one blank-line separator;
- exact UTF-8 message bytes; and
- exactly one final LF.

Candidate, packet, integration, review-output, finalizer, disposition, P utility
ceremonial, H integration-record, and H durable-disposition commits each have
their own closed message and parent grammar. The P ceremonial commit has the freshly observed P
product predecessor as sole parent, the reviewed Stage-2 candidate tree, and a
new result OID distinct from that candidate and both later H commits. The H
record uses raw kind `UTILITY_CEREMONIAL_INTEGRATION_RECORD`; the H disposition
uses `UTILITY_BOOTSTRAP_DURABLE_DISPOSITION` and preserves the record. The wall clock, Git config,
repository identity, locale, editor, signing, cleanup, encoding default, and
environment cannot supply a field. An independent raw parser verifies every
stored object before any ref operation.

## Credential and network boundary

Git Credential Manager, shell-transformed credential helpers, browser login,
terminal prompts, credential-bearing netrc, ambient Windows authentication, cookies, proxies,
redirects, headers, and repository configuration are absent from the positive
route.

For one HTTPS operation, the controller supplies a short-lived token through a
private parent channel. The broker binds it to the exact selected Git process
and Job, typed operation, literal URL, complete refspec, nonce, and one response.
Git receives an absolute pinned askpass adapter and an already fixed username.
The broker is a reviewed in-process subsystem of the trusted native supervisor;
it has no second process, Job, environment, token, or executable selector. The
adapter is an exact held capsule file for publisher and integrator and is absent
from builder.
The adapter connects to the one pre-reserved, ACL-restricted, one-instance local
pipe. The broker validates the connected process PID, image, and scheduled-Job
membership before returning one password response. The nonce-qualified pipe,
operation, table, template, environment, and route are fixed and revalidated by
the owner before process resume; the outbound pipe carries no client-authored
authority frame. The adapter checks the exact frozen password-prompt bytes,
rendered from the selected public account and HTTPS endpoint; a username,
different, or second prompt refuses. The broker's overlapped write uses
`CancelIoEx`, its retained blocking flush uses `CancelSynchronousIo`, and both
have typed terminal evidence. Write evidence records the cancel return/error,
event wait, `GetOverlappedResult` outcome, completed bytes, and OVERLAPPED
retirement. Flush evidence records the exact signal, wait result, thread exit,
cancel return/error, flush result/error, completed join, and successful handle
close. Prompt text is
corroboration; it is never audience authority.

The disposable HTTPS server accepts the rehearsal secret only through one
mutually authenticated ARM, ACK, CONSUMED, and DISARMED lifecycle proving one
accepted use and zero remaining uses. Client success without that server-
authenticated lifecycle cannot pass the public-boundary gate.
Every network lifecycle carries one tagged coordinate. Fault-bound steps repeat
the selected reservation and nonce; reservation-free steps bind the broker
session, dispatch, request nonce, task binding, and step with null fault fields.
Each signed server payload has an independently verified authenticated-artifact
envelope. Every rehearsal network step carries either consumed-once or signed
unconsumed terminal disarm evidence. Broker write/flush facts bind the exact
reservation, session, handle, deadline, and event or flush thread; calibration
retains each typed `SCALED_REHEARSAL` workload and scale transformation.

Network command configuration resets the complete helper list. Its environment
sets terminal prompting off and resolves `HOME`, `USERPROFILE`, and their drive-
path decomposition to one held sealed profile projection. Exact retained zero-
byte `.netrc` and `_netrc` guards are its only admitted netrc reads; `NETRC`,
`CURL_HOME`, credential-bearing netrc, and ambient authentication routes are absent. Offline
children use a disjoint grammar with no askpass, broker, credential, HTTP,
HTTPS-helper, public account, or remote-helper key. The repository, protocol,
hooks, URL, TLS, proxy, redirect, cookie, header, trace, and config-injection
surface is exact. No external helper receives `store` or `erase`; the adapter
has no operation for either.

No production push is eligible until the same route passes an exact HTTPS
mutation rehearsal against a separately authorized private repository or
server-enforced namespace whose credentials cannot write any production task,
output, or main ref.

Campaign inputs are either exact inline canonical fixtures or outputs derived by
selector-bound pure renderers from earlier typed step fields. Fault cases require
the reviewed controller harness to reserve and activate the exact fixture for
the current dispatch. Server-side atomic rejection and lost-ack evidence echo
that reservation nonce and the canonical ref-update-set digest. They also equal
the reviewed component-binding digest, procedure ID, and deployment receipt's
rehearsal endpoint, repository, and server-policy digest. Process-only faults
bind their activation artifact to cleanup or runtime evidence. A process-only
network fault retains all five endpoint, repository, component-binding,
server-policy, and deployment-receipt fields; an offline process fault has all
five null. The live Git path reports only generic rejected, transport-failure,
or unknown outcomes.
An atomic-unsupported campaign verdict additionally requires the authenticated
post-step server event, so an expected label or client diagnostic cannot name
the mechanism.

## Main observation and reconciliation

Main state has two independent axes. `lineage` is one of:

```text
RESULT_EXACT
RESULT_DESCENDANT
RESULT_SIDE_ANCESTOR
PREDECESSOR_EXACT
PREDECESSOR_DESCENDANT
UNRELATED_OR_ABSENT
UNKNOWN
```

`task_state` is one of:

```text
INTACT
PROTECTED_CONFLICT
TASK_UNKNOWN
NOT_APPLICABLE
```

After a strict main query, a bounded all-parent raw-object observation first
tests whether `I` remains reachable anywhere. Side-parent-only reachability is
spent `RESULT_SIDE_ANCESTOR/PROTECTED_CONFLICT`, never fresh eligibility; an
unknown DAG observation blocks mutation. Exact `I` is then tested before exact
`H0`. Otherwise the integrator walks the complete first-parent chain and
compares each commit to `I` before `H0`. Finding `I` establishes
`result_seen=true` permanently for that observation. Finding only `H0`
establishes predecessor-descendant lineage. Reachability through a non-first
parent does not satisfy either first-parent descendant state, but it does spend
the transition through the separate DAG observation.

Every first-parent edge between the anchor and tip is checked. Task equality
uses the complete semantic projection. A shared carrier blob may change when
another task appends its own record, while this task's record, mode, and type
must remain exact. The current transition's proposed bundle can validate its own
result edge. A later same-task phase uses `TASK_UNKNOWN` for this old
authorization because its future immutable bundle cannot enter the frozen
launch inputs. The old result remains seen and spent. Unrelated commits may
interleave only while preserving the task projection. A mutation followed by
restoration is a conflict because the edge walk observes both changes.

Lineage stops at the first expected result or predecessor coordinate, but phase
verification does not. A separate bounded phase-history walk starts at the
expected predecessor, consumes every historical phase-input bundle exactly once,
and continues through every intervening first-parent commit to an explicitly
validated `NO_TASK` baseline. Its typed raw, inventory, evidence, and cap
failures force `TASK_UNKNOWN` without erasing an already classified lineage or
`result_seen`. The lineage anchor and history overlap through exact field
equality and never consume a bundle twice.

Each walk row separates its raw commit/first-parent fact from task evaluation.
Its closed task status is intact same-phase, intact phase-advance, protected
conflict, task unknown, or not applicable. Not-applicable rows use exact no-
anchor or pre-anchor-lineage-failure reasons. Every status has exact reason
codes and nullable inventory/phase fields. Raw lineage can therefore reach a
result through an unreadable
protected inventory and retain `result_seen=true`; the row records why task
state is unknown instead of pretending that null phase evidence means intact.

The accepted plan fixes both row-count and canonical-byte caps for the inline
first-parent walk and each phase-evidence bundle. The owner enforces them before
allocation within the launch memory and output limits and reserves one compact
failure row. A raw-chain cap before an anchor yields lineage `UNKNOWN`; a task
cap on an already classifiable result yields `TASK_UNKNOWN`. A partial row or
bundle is never authority.

Exact result or intact same-phase result descendant closes a lost
acknowledgement without a push. A result descendant with a protected
conflict records that the transition occurred, preserves state, and never
retries or reauthorizes the same transition. An intact predecessor descendant
requires a fresh authorization. Unknown or conflict preserves and refuses.
If a result anchor was found before later protected evidence became missing or
ambiguous, `TASK_UNKNOWN` retains `result_seen=true` and the old transition is
spent; it cannot be retried.

## Launch dispatch and transition authorization

A one-use launch dispatch authorizes one role process and one complete bounded
child-schedule program. It carries a nonce, dispatch mode, fixed role, complete
source/runtime/policy projection, exact state-equation digest, schedule variant
and digest, CPU-time limit, memory limit, wall, output caps, and expected
predecessor. It also binds the calibrated active-process cap for every scheduled
Git Job; the role Job remains exact one. Observation has the sole `OBSERVE`
variant; a mutation variant is
mechanically derived from the fresh precondition. A terminal exact observation
closes idempotently and starts no mutation schedule. It cannot be replayed to
start a second role process. Before process creation, the supervisor durably
creates, flushes, reopens, and retains the schema appendix's consumed-dispatch
record in its ACL-sealed controller registry. Startup validates the complete
permanent registry. A canonical anchor filename spends only its plan-and-nonce
key even if a crash leaves incomplete content; unrelated keys remain usable.
An out-of-grammar, case-colliding, nonregular, reparse, ACL, directory, or
enumeration ambiguity blocks all launches. Process creation requires complete
record bytes revalidated after reopen. A crash at any earlier persistence
boundary spends the nonce and requires fresh observation plus a new dispatch.
Git children are schedule steps inside that launch,
not separately improvised commands or independently reusable dispatches. Each
actual network child receives its own step-and-repeat-ordinal-bound one-use
broker session. Static single steps and bounded-repeat groups admit only fixed
argv grammars. Repeat populations come from complete validated object
inventories or deterministic first-parent walk state, and runtime evidence
records the complete concrete expansion. The pre-resume session binding proves
routing and process attachment; a separate terminal result proves exact frame
write, monitored flush, disconnect, close, adapter exit, actual redemption
count, and broker-buffer zeroing. Every successful
network child requires exactly one of each.

The dispatch carries the worker's complete six-entry environment block and held
run-directory projection. Runtime evidence also carries a coordinate-keyed Git-
child environment set that bijects with every prepared coordinate. Its assigned
`CREATE_SUCCEEDED` subset maps the expanded schedule; an unassigned, create-
failed, or not-attempted ABORTED boundary remains explicit with its nullable
lifecycle and exact launch-attempt fact. Each row freezes
the exact UTF-16LE block bytes, grammar, current/run/scratch/profile directory
identities, and optional broker reservation. Every Git home path resolves to one
held profile root containing exact zero-byte `.netrc` and `_netrc` guards opened
create-new with read sharing only and retained through Job active-zero. No
digest-only, inherited, reordered, cross-child, or alternate-home environment
can reach process creation or terminal evidence.
Every retained directory has a canonical same-handle open fact with exact
desired access, read/write-without-delete sharing, backup/open-reparse flags,
noninheritability, and queried granted-access mask. Every local ref read/write
is enclosed by a typed mutex lifecycle proving acquisition, protected action
order, same-thread release, and close; abandonment never authorizes mutation.
Every dispatch limit derives from a complete typed calibration receipt with
measured workload rows and deterministic selections, not a bare numeric claim.

The supervisor counts stdout and stderr incrementally. At the first observed
count above the selected calibrated cap it records the stream, selected cap,
limit-row and dispatch digests, and first over-cap count in the complete typed
output-cap fact. That same fact appears in process completion, cleanup
termination under `SUPERVISOR_OUTPUT_COUNTER`, and the outer
`OUTPUT_CAP_EXCEEDED` refusal. Child bytes cannot assert overflow.

`OBSERVATION_ONLY` dispatches exist so a trusted controller can classify an
exact frozen state equation after coordinator death, timeout, or lost
acknowledgement. Issuing one does not require a prior eligibility verdict. Its
loaded request table has no authority-repository object write, ref write, push,
or other durable authority mutation. When remote ancestry or tree bytes are
needed, it may fetch only into a new dispatch-owned scratch object database
with no refs; those objects are nonauthority residue and never enter the held
authority repository.

`MUTATION_ATTEMPT` dispatches require a bound fresh observation showing that
the exact transition remains eligible. They may perform one declared local
recovery-ref transaction and one remote transition, with a fresh decisive
remote observation immediately before the latter. A lost-ack path first
uses `OBSERVATION_ONLY`; it does not circularly require proof of eligibility to
obtain the proof.

A transition authorization is an idempotent authorization for one semantic
transition. For integration it binds exactly `(H0,P,I)` and the complete
construction. Its SHA-256 namespaces two permanent local refs targeting the
external intent blob and `I`. The pair is created atomically before a push.
The authorization binds expected selectors and immutable inputs, never an
observation, mutation precondition, dispatch, or result receipt. An
observation-only dispatch can therefore use it before eligibility is known; a
later mutation dispatch binds the returned canonical observations through its
separate operation precondition.
Main-publishing authorizations carry the exact protected-task specification and
historical phase-input set at the expected predecessor. Their launch projection
adds a separate proposed-edge bundle assembled from the accepted authorization
and raw result preimage. Fresh main observation derives phase evidence from
those bytes; observer-derived evidence never flows back into authorization.
Exact state supports a new mutation dispatch only after observation proves the
same transition eligible; observation-only dispatches remain available to
classify it after any prior process disappears.

Local attempt refs are local collision and recovery evidence. They are not a
global spend record and may be reconstructed in a fresh clone. The protocol
makes no claim that they reveal an invocation after local deletion, clone
replacement, or remote-main reset. The local ref transaction and remote main
push are separate operations; no cross-repository atomicity is claimed.
Each attempt-ref kind has one table descriptor. Only after the transition
authorization is complete does its external digest produce the full intent and
result refs. Selectors, preregistrations, intents, and operation inputs contain
no full attempt ref.

## Review outputs and finalization

This section specifies the implemented route for later `raw-object-v5` rounds.
It does not replace the bundle's temporary-index, direct-Git, rule-6 bootstrap.

The upstream round preregistration binds the complete candidate/utility review-
author union and selects exactly two reviewer slots, ordinals, permanent
output-ref coordinates, endpoint, candidate base, four-role set, accepted
utility, and finalizer. The cold-input specification repeats its complete byte
count and SHA-256 and adds the candidate identity and common integrated-packet
parent. Reviewers are distinct and absent from the complete union of utility-
source authors and implementers plus candidate content authors and every actor
or session that implemented, assembled, generated, or rewrote a candidate
change. Frozen controller assignment and receipt evidence supports that complete
union. Each reviewer receives the same integrated packet without the other
output.

Each output commit has the integrated packet as sole parent and adds exactly an
attributed report, canonical receipt document, issuer-authored LF-terminated
ledger-line blob, and self-excluding manifest. The receipt document contains a
package header plus exactly four role receipt objects. Package verdicts govern
cross-role behavior; role objects cannot replace them.

The report and issuer ledger line are fixed first. The receipt binds both as
artifact identities and contains no digest of itself, output manifest, tree, or
commit. The report does not bind the later receipt. The manifest excludes
itself and binds report, receipt, and ledger-line blob by path, mode, Git OID,
SHA-256, and byte count. The external authority is the full output ref, exact
target commit, and complete-byte manifest SHA-256.

Output slots are independent. Both absent, or one exact and one absent, means
`WAITING_FOR_REVIEWS`; it is not the candidate/packet `PARTIAL` state. Only an
absent slot may be created. Both exact permits finalization. A different,
malformed, ambiguous, or unavailable slot preserves and refuses.

The finalizer authorization pins both output tuples, ordinal append order,
common parent, exact main predecessor, and current ledger prefix. The finalizer
copies each frozen artifact byte-for-byte and appends the two complete line
blobs in ordinal order. It does not normalize, edit, synthesize, or become the
issuer. Main publication uses the same two-axis lineage and exact-lease rules.
Output refs remain permanent because copying their blobs does not preserve the
sibling output commits.

## State and failure rules

Durable authority is monotonic. The tools never delete or roll back an object,
intent, attempt, candidate, packet, or output ref. Cleanup owns only processes,
Jobs, pipes, handles, and unique temporary or projection residue created by that
invocation. Unreachable Git objects and source-only fetch residue may remain.

Every external read is strict and fresh. `UNKNOWN` takes precedence over a
conclusion based on incomplete output. Only the closed locale-fixed porcelain
facts from a complete push status stream become typed process evidence; raw
diagnostics remain nonsemantic. Query and fetch outcomes use their own typed
observations. A post-process owner step combines the immutable lifecycle fact
with a fresh ref observation, selecting the first non-success transport outcome
or the final success under the frozen schedule rule. A natural process return
before the active deadline may enter only its already scheduled read-only
observation suffix. A timeout, cancellation, or other terminal cause kills the
complete Job and starts no new process or network operation; cleanup proves
active-process zero, revalidates held identities, preserves authority state as
unknown, and requires a later fresh `OBSERVATION_ONLY` dispatch for durable
classification. Process output and push status bytes are diagnostic and never
replace durable state.

The raw route's remote candidate, packet, and output refs are permanent slots.
The workflow amendment narrowly supersedes retirement deletion for rounds that
carry and validate an exact raw-object-v5 round-preregistration object through
authorization and finalization. Existing rounds and the temporary-index route
keep their adopted rules. Permanence constrains accepted writers; it is not proof
against an administrator or remote reset without a separate append-only source.

## Falsifying implementation strategy

Implementation begins with three spikes, each written RED before production
code:

1. native pre-DLL bootstrap plus AppContainer read/process/network denial;
2. builder launch proving publisher and integrator operations are unavailable;
   and
3. one-shot HTTPS askpass mutation proving zero durable credential change.

Failure of a spike blocks the rest of the implementation. A post-load audit,
prompt comparison, helper double, local transport, or read-only remote query is
not a substitute.

Before implementation, the accepted round freezes a file-by-file source
budget. The combined native bootstrap and askpass adapter may not exceed 1,800
nonblank lines, the shared pure kernel 1,200, any role policy plus planner 900,
or focused tests 4,500. Generated schemas, fixed tables, and fixture data are
counted separately and require generators plus independent readers. Exceeding a
limit stops implementation for a new architecture checkpoint; moving bytes to
another file or generated-looking carrier does not reset a limit.

The minimal startup, sandbox, and one-shot credential spike has two focused
lifecycles to make AppContainer launch, CPython bootstrap, and exact HTTPS
mutation deterministic. Failure parks this architecture. It may not remain
alive through another review cycle or be emulated with a post-load audit or
local transport.

Subsequent tests derive expected object bytes from independent literal fixtures
and exercise public role entry points. Every generated fault schedule binds the
matching fresh reservation and reviewed harness activation artifact. Process
faults bind typed cleanup/runtime evidence; server faults also bind the
correlated controller-only event, and every case ends with a fresh post-case
capability wrapper. A schedule label cannot claim that a fault occurred.
Category inventories cover every operation table member, every
local and remote transition, every first-parent edge class, every receipt
relation, and every runtime source/image/data member. Source scans aid discovery
but do not replace public-boundary behavior.

The Git and runtime appendices contain the complete negative matrices. Before
live use, the exact per-role walls and output caps must be frozen from scaled
rehearsals. An unmeasured fixed wall is absent authority, not a default.

## Barriers and deliberate exclusions

Acceptance of this design authorizes only a later implementation round. That
round must freeze source, generated binaries, projection manifests, schemas,
focused tests, build toolchain identity, measured walls, and exact HTTPS
rehearsal target before any candidate-specific dispatch can exist.
After that implementation is accepted, each later raw-object-v5 round also
requires a separately frozen preregistration whose complete bytes survive
packet construction, adoption, review, finalization, disposition, dispatch,
and runtime revalidation. The utility cannot create this selector for itself.

No r002 design operation imports, compiles, runs, reads semantically, or
publishes the v0a C candidate, harness, Model, controller, analyzer, sensitive
case, or test. No evidence repository ref or retained artifact changes. Any
role expansion, new executable, late import, native image, runtime-data path,
transport, credential source, ref deletion, or main-state shortcut requires a
new reviewed design round.
