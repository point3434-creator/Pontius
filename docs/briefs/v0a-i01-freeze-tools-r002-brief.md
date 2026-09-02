# v0a-i01-freeze-tools r002 brief

Tier: C

Round kind: FIX

Stage0b: cap=3 lock=R002_FREEZE no6=true terminal=r005 ordinal=5 locked=true

Base: `d1ed3cbda6107d61ea8e77133871720af04970cd` on
`codex/v0a-i01-freeze-tools`, worktree
`D:\Pontius-worktrees\codex-v0a-i01-freeze-tools-v1`.

Rejected predecessor: candidate
`ad8fbcc1ae5a9e3c3b61ae93d5ae5c0b3e4d289e`, manifest SHA-256
`862d245f838f4b7459b6ce2aae19eede3b77a4861575722817db12d63af7b689`.

Finalizer: `codex/finalizer` for this authority-tool design checkpoint. This
does not change the finalizer of the C implementation checkpoint.

## Scope

Replace r001's observation-based runtime and generic Git layer with one closed
authority-tool architecture:

- a reviewed Windows owner that loads one exact role policy and accepts only
  typed operation requests;
- a minimal native bootstrap that establishes DLL policy before loading an
  exact CPython 3.11 runtime projection and starts a role-specific Python
  planner with no network or child-process capability;
- separate builder, pair-publisher, and main-integrator source populations,
  each with a complete frozen grammar and no load path to another role;
- deterministic raw Git-object serialization and monotonic local and remote ref
  transitions;
- a one-shot broker-bound askpass route with no Git Credential Manager or
  durable credential mutation;
- exact review-provenance, recovery, adoption, and first-parent state schemas;
  and
- public-boundary tests and disposable HTTPS mutation rehearsals.

This r002 candidate contains design authority only. It adds no executable tool,
test, runtime projection, credential, repository mutation, or candidate
dispatch. Implementation starts only after this design round is accepted.

## Acceptance criteria

1. Every role's source population, input grammar, predecessor schema, typed
   operations, result equations, and refusal states are complete. Builder
   executable code, role policy, and actionable request grammar contain no URL,
   remote-ref, credential, pair-publication, or main-transition selector.
   Artifact and evidence bytes may be parsed and may be authoritative for
   deterministic content, but they are non-authoritative for capability
   selection. No derived value can populate an owner endpoint, ref, refspec,
   credential, argv, role, operation, executable, or table selector.
2. The native bootstrap applies the frozen loader policy before
   `python311.dll` is mapped, initializes Python with isolated `PyConfig`, and
   admits only held role archives and a closed native/runtime-data projection.
   The planner runs in the preregistered AppContainer with no network, no child
   process, and no access to repository or profile paths. Its dispatch carries
   the complete six-entry UTF-16LE environment preimage and exact held run-
   directory projection; neither can be inherited or supplied by the planner.
3. The Windows owner receives only typed, canonical planner frames and resolves
   them through the single loaded role policy. No raw argv, executable, path,
   URL, refspec, config pair, credential selector, or environment override
   crosses the planner boundary.
4. Every candidate, packet, integration, review-output, finalizer, and
   disposition commit is derived from canonical raw commit bytes with fixed
   identity, time, parent order, tree, message, separator, and final LF. No Git
   config or wall clock supplies an omitted field.
5. Local intent, candidate, and packet-anchor refs form one create-only atomic
   tuple. Publisher adoption cannot create authority. A later offline
   builder-adopt transition validates exact fetched objects and creates the
   tuple transactionally. The dispatch binds the exact `update-ref --stdin`
   preimage and execution retains the actual accepted-byte/EOF fact; a later
   exact tuple cannot conceal an extra or different command.
6. Candidate and packet refs use one atomic create-only HTTPS push to the same
   preregistered handoff endpoint and remain permanent spent evidence for the
   raw-object route. No accepted role can update or delete them. A push that
   returns naturally before the active deadline is followed by its already scheduled
   fresh exact ref observation, including nonzero and lost-output returns. If
   the active deadline or another terminal cause terminates the push, cleanup
   starts no new child or network operation, preserves state as unknown, and
   requires a later fresh `OBSERVATION_ONLY` dispatch before any retry or state
   claim.
   Raw Git output is noncanonical. Only a complete bounded locale-fixed parsed
   push status may enter immutable transport-cause evidence; fresh typed ref
   observation still decides repository state.
7. Main integration commit `I(H0,P)` has first parent `H0` and designated
   packet parent `P`, and advances main by ordinary fast-forward under exact
   predecessor observation. State uses two independent bounded walks. Phase
   history starts at `H0`, consumes every historical bundle once, and reaches an
   explicit `NO_TASK` baseline; lineage walks from observed tip only to the first
   result or predecessor anchor. History uncertainty preserves classified
   lineage and `result_seen` while forcing task state unknown.
8. GCM is absent. The credential broker binds one short-lived,
   repository-scoped token to the selected Git PID/job, typed operation,
   literal URL, exact refspec, nonce, and one response. Git helpers are reset;
   netrc, GSS, redirects, proxies, headers, cookies, hooks, URL rewrites, and
   config injection cannot supply another route.
   The broker runs only inside the trusted native supervisor. Builder has no
   askpass adapter; publisher and integrator each hold one exact capsule copy.
   Its one-instance pipe is outbound at the supervisor and read-only at the
   adapter, with no client request frame. Reservation and pipe creation precede
   environment construction, suspended Git creation, Job binding, completed
   session binding, and resume. The broker admits PID/image/Job; prompt sanity is
   adapter-local but byte-exact: the frozen grammar renders one password prompt
   from the selected public account and HTTPS endpoint. The pipe's overlapped
   write and blocking flush have distinct cancellable-I/O evidence. The
   supervisor records a typed output-cap fact at the first
   stdout or stderr count above the selected calibrated cap.
   Every Git process has one coordinate-keyed complete environment and launch-
   directory projection equal to its schedule row. All effective home selectors
   resolve to one held profile root whose create-new zero-byte `.netrc` and
   `_netrc` guards deny write/delete sharing through Job active-zero. Worker and
   Git-child populations cannot substitute for one another.
9. This documentation round uses adopted temporary-index Stage 2 and handoff
   packet rule 6 and issues no source receipt. The later frozen implementation
   uses the same bootstrap; its two independent reviewers each issue one
   report, one exact ledger line, and one receipt document containing a package
   header plus four role receipt objects. Those two complete receipt documents,
   not the role rows alone, are the machine semantic source. Utility acceptance
   binds the exact downstream HTTPS rehearsal result between plan tests and
   controller authorization, then requires the implementation-controller
   disposition to decide exact `AUTHORIZE_CEREMONIAL_INTEGRATION`. The complete
   historical bootstrap chain
   through a distinct finalizer-authored P ceremonial commit, compare-and-swap
   P push, separate pre/post-push query types, H publication of every self-free
   receipt, durable disposition carrying the complete controller triple, and
   externally retained acceptance observation.
   The upstream pinned authority verifies every H observation receipt; future
   Stage 0b round-freeze, review-result, disposition, and build-authority
   publications use the same self-free core plus retained wrapper.
   P construction has a three-event transcript: predecessor query, acceptance
   of the complete authorizing controller disposition, then ceremonial-input
   authorization. The build receipt and result carry that same transcript.
   Authorship
   evidence exactly covers every source path; the four ordered required tests
   and controller-disposition artifact/count/digest propagate through
   acceptance. Each later raw-object-v5 round has one
   upstream canonical preregistration and excludes reviewers from the complete
   canonical `pontius-round-review-author-set-v1`: utility authors and
   implementers plus candidate authors and implementers.
10. The same pinned Git, broker, askpass, loader, Job, and timeout route performs
    real mutations against a separately authorized private HTTPS rehearsal
    target structurally unable to address production refs. Local transport and
    read-only observation do not satisfy this gate.
    The owner-only preacceptance selector binds the complete campaign, pure
    derived-input contracts, typed fixtures, an upstream adoption-chain set,
    reviewed fault-harness/parser component bindings, disjoint case/task refs,
    and fresh pre-production and pre-rehearsal capability observations without
    accepted utility authority or a normal preregistration. Each rehearsal fetch
    preselects its later adopter, builder-intent fixture, and exact identities in
    that acyclic chain set. Each step selects one case-local task/round binding;
    that binding follows through authorization, dispatch, evidence, and task-
    scoped ref resolution. Only the case-shared `HANDOFF_MAIN` row has no task
    binding. Every fault binds a fresh reservation and activation artifact;
    server faults add a correlated event that repeats the reviewed component-
    binding digest, procedure, deployment policy, and current reservation. Every
    successful askpass mutation also binds the authenticated server ARM, ACK,
    CONSUMED, and DISARMED lifecycle proving one use and zero remaining uses.
    Every network lifecycle has a tagged coordinate: fault-bound repeats the
    reservation and nonce; reservation-free binds broker session, dispatch,
    request nonce, task binding, and step with null fault fields.
    Each case finishes with a fresh post-case capability observation. A process-only
    network fault retains all five endpoint, repository, component-binding,
    server-policy, and deployment-receipt fields; an offline process fault has
    all five null.
11. Every authority-database object-writing schedule retains its complete
    object-write plan in schedule and runtime evidence. The post-Job storage
    observation maps each new physical carrier to that plan or to a complete
    built or fetched inventory. Standalone builder and integration intent blobs
    therefore have typed provenance without inventing a downstream receipt.
    Missing plan members, extra semantic objects, changed baseline carriers, and
    forbidden sidecars block authority.
12. Schedule execution has explicit `COMPLETE` and `ABORTED` branches. An in-
    launch authority refusal after dispatch consumption retains the exact
    contiguous executed prefix, terminal coordinate,
    created broker sessions and results, assembled transport outcomes, reached
    object-write facts, and cleanup storage observation. Missing lifecycle facts
    produce host failure, never a weaker authority refusal.
13. Runtime evidence includes the bootstrap broker-attach ACK, the frozen
    supervisor exit and result-peer-loss policy, measured runtime-limit calibration, exact
    scratch seed and terminal remove-or-quarantine inventory, complete
    repository-mutex lifecycles, and same-handle canonical directory-open
    access/share/flags/granted-access facts.
    Launch dispatch carries only the immutable worker-launch attempt. Post-exit
    evidence uses the transport receipt for delivery and loss receipt for peer loss;
    neither result enters runtime evidence. Calibration retains
    typed scaled-rehearsal workloads. Scratch teardown has typed parent/move
    facts, repositories have ancestor chains, and mutex rows retain milestones
    through the self-free final-revalidation core. Release and close occur
    before the outer revalidation object carries the completed lifecycle array.
14. Every rehearsal network step carries an independently verified signed
    server-secret lifecycle. Accepted requests prove consumed-once; unaccepted
    requests prove authenticated terminal disarm and zero remaining uses.
    Cancellable write/flush evidence binds the exact reservation, session,
    server handle, operation, deadline, and event or flush thread. Write proves
    exact cancellation, event wait, `GetOverlappedResult`, completed bytes, and
    OVERLAPPED retirement. Flush also records exact cancellation, flush result,
    signal, wait, thread exit, completed join, and successful handle close.

## Seam inventory

- adopted controller to role owner and exact authorization;
- controller to the fixed native supervisor ABI, typed control/result channels,
  and retained-origin liveness;
- role owner to native Python bootstrap and AppContainer worker;
- bootstrap to CPython DLL, stored ZIP archives, native images, and runtime data;
- planner frames to one loaded role policy and Windows process owner;
- process owner to pinned Git and the one-shot askpass adapter;
- Git object database and complete local ref transaction;
- Git HTTPS transport, remote permanent pair, and first-parent main history;
- publisher fetch residue to offline builder-adopt authority;
- reviewer report, one four-role receipt document, issuer ledger line, and
  self-excluding manifest; and
- rejected r001 bootstrap to the adopted temporary-index and rule-6 root.

## Size and complexity breaker

### Stage 0b design-convergence breaker

The current `v0a-i01-freeze-tools-design` series is the bootstrap exclusion for
the Stage 0b mechanism designed here. Its r002 through terminal r005 rounds are
administered by the external coordinator through the already adopted
temporary-index Stage 2, direct-Git, and packet-rule-6 workflow. No Stage 0b
JSON object, future executable, or post-acceptance activation authorizes or
retrospectively upgrades this series.

The exact terminal rule was decided on 2026-09-01 while r002 remained mutable
and before any frozen r002 review evidence existed. The preregistration and A/B
histories took five and six rounds, so the ruling permits at most three
corrective successors, r003 through r005. It preserves immediate exit on an
accepted clean review set and the independent same-contract residual/design
breaker. Draft edits before r002 freeze remain r002. After that freeze, a
changed P byte or permitted H review input advances the adopted-workflow round.
Alias, rebase, rename, split, reviewer replacement, or a new label never resets
the sequence.

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

This calibration is amendable only before r002 freezes. The r002 freeze makes
terminal r005 immutable for this series; changing it after review evidence is
opened is tuning against evidence and selects `PARKED` with gate-defect
classification. No r006 exists. The prospective Stage 0b schemas mechanize the
same interface-counting and terminal semantics only after accepted utilities
publish `pontius-stage0b-activation-publication-v1` for a different series.
Every future Stage 0b object from calibration through build authority repeats
that activation's exact task and uses it for every packet and ledger path.

Before implementation, freeze a file-by-file source budget. Stop for a new
design checkpoint if the combined native bootstrap and askpass adapter exceed
1,800 nonblank lines, the shared pure kernel exceeds 1,200, any role policy plus
planner exceeds 900, or focused tests exceed 4,500. Generated schemas, fixed
tables, and fixture data are counted separately but must have generators and
independent readers.

The implementation round must first prove a minimal startup, sandbox, and
one-shot credential spike. If AppContainer launch, CPython bootstrap, or exact
HTTPS mutation cannot be made deterministic within two focused lifecycles,
stop and choose a smaller accepted route; do not emulate the boundary with a
post-load audit or local transport.

## Forbidden claims

This round does not prove or execute the C candidate, freeze or publish its
refs, dispatch its reviewers, run RED authority, mutate retained evidence,
accept source, or advance the evidence repository. It does not prove a hostile
controller, kernel, administrator, debugger, AppContainer implementation,
System32 population, DNS/TLS platform, Git server, or already patched process.
It does not claim global one-use history after a server-side reset. It defines
which exact later evidence is required before any live authority exists.

## Review and verification plan

Two blind Tier-C reviews bind the same frozen r002 commit and manifest under
the adopted packet-rule-6 workflow. Before opening `coverage.md`, each reviewer inventories
every declared schema, entry-point contract, and lifecycle state set, plus role
capability and startup
source/image/data closure, commit bytes, credential paths, local and remote ref
state, first-parent history, fresh-clone adoption, and provenance cardinality.
Each review returns an attributed typed bootstrap-design-review receipt, report,
issuer ledger line, defect verdict, and design verdict. Peer blindness is an
explicit reviewer attestation in this pre-utility bootstrap; it is not presented
as mechanically observed. The external controller joins both publications and
issues the typed bootstrap design disposition.

The frozen P candidate contains exactly these six normative design-source paths
in ASCII path order:

1. `docs/briefs/v0a-i01-freeze-tools-r002-brief.md`
2. `docs/superpowers/specs/2026-09-01-raw-object-workflow-amendment-v5.md`
3. `docs/superpowers/specs/2026-09-01-v0a-i01-freeze-tools-design.md`
4. `docs/superpowers/specs/2026-09-01-v0a-i01-freeze-tools-git-boundary.md`
5. `docs/superpowers/specs/2026-09-01-v0a-i01-freeze-tools-runtime-boundary.md`
6. `docs/superpowers/specs/2026-09-01-v0a-i01-freeze-tools-schemas.md`

This list is the frozen path oracle. `coverage.md` is separate coordinator
evidence, not a seventh P path. `coverage-plan.md` does not define or amend the
population. Candidate authority remains the source ref, commit, and
manifest SHA-256. The adopted handoff packet freezes the two reviewer slots,
design-author set, seven canonical terminal-r005 declarations, convergence policy, and all review
inputs. Each review publication preserves packet history and carries its issuer
ledger line, typed receipt, and report.

Only a complete
`pontius-utility-bootstrap-design-authorization-publication-v1`, published by
the external controller after both reviews and carrying decision exact
`AUTHORIZE_FREEZE_TOOLS_IMPLEMENTATION`, permits the H implementation plan,
path-budget map, Markdown brief, and self-free start object to be frozen and
published. Authorization and start bind the pinned external-retention service,
producer, verifier, Ed25519 key, genesis head, namespace, and write-once policy.
The start freezes candidate and product refs, ceremonial message and
metadata, Tier C, two reviewer slots, and finalizer; its Markdown rendering is
the exact adopted brief repeated downstream. Only the remotely observed
`pontius-utility-bootstrap-implementation-start-publication-v1` opens P source
work. The P candidate has the plan's exact P base and carries no H start field
or H ancestry; adopted nine-key `candidate.json` stays unchanged. The H
implementation packet descends from H start and adds
a separate typed start link that binds the independent P candidate tuple; only
then is that candidate admissible. Every
review, selector, controller authorization, bootstrap evidence, and acceptance
object repeats the start, design-authorization, and plan identities.
The prospective Stage 0b counter, round-freeze anchor, disposition, and build-
authority schemas are implementation targets for a different activated series;
they are not current r002 handoff artifacts.
`coverage-plan.md` is working input and enters neither object.

Static candidate checks map every r001 finding to a normative section and
falsifying public-boundary case, reject stale r001/GCM/`commit-tree`/main-force
push/ref-deletion/generic-state language, enforce cross-document schema and
role vocabulary, and verify UTF-8, LF, line length, path population, and exact
hashes. No executable rehearsal occurs in this design round.
