# R002 Git and remote-transition boundary

Status: COORDINATOR DRAFT. This file authorizes no execution, credential access,
object write, ref mutation, or network operation. It does not amend
`docs/workflow.md` by itself.

Stage0b: cap=3 lock=R002_FREEZE no6=true terminal=r005 ordinal=5 locked=true

This design replaces the r001 Git/GCM appendix. The accepted positive route has
no Git Credential Manager, shell, browser, terminal prompt, ambient netrc,
generic command suffix, remote-name selection, or caller-supplied ref selector.

## Scope and claims

This boundary defines five things:

1. the exact executable and configuration population for direct Git operations;
2. a one-shot credential adapter backed by a controller-authorized broker;
3. closed, role-specific Git operation grammars;
4. canonical raw commit serialization and ref-transition preconditions; and
5. remote observation, reconciliation, and disposable HTTPS mutation evidence.

The surrounding runtime design must establish the process, file, loader, and
data namespace before any operation in this file can run. This file does not
claim that a post-start process census can prevent an unknown child from
executing. It requires an unknown observed image to fail closed, while the
runtime and role-policy boundaries prevent undeclared routes from being
selected.

No network operation is eligible until implementation has frozen and reviewed
the complete executable closure, the role policy, the broker, the adapter, and
the operation schema. A missing identity is a refusal, never a discovery step.

## Role capability boundary

The offline builder can select only offline object and local-ref operations.
Its executable code, loaded policy, and actionable request grammar contain no
URL, endpoint, remote-ref, main-ref, credential, fetch, query, push, or remote-
publication selector. Artifact and evidence bytes may be parsed and may be
authoritative for deterministic content, but they are non-authoritative for
capability selection. No value derived from them may populate an owner
endpoint, ref, refspec, credential, argv, role, operation, executable, or table
selector. Those selectors derive only from held role policy and controller
authorization.

The publisher can select only these typed operations:

- observe the exact candidate and packet pair;
- create that pair atomically from absence;
- fetch that exact pair as nonauthority object residue for adoption;
- observe one frozen review-output ref; and
- create one frozen review-output ref from absence.

The integrator can select only the five operation IDs in the closed grammar
below. Across those operations it may fetch one closed main-input inventory,
construct one authorized main overlay, validate the permanent inputs, observe
main, and publish the exact packet-integration, review-finalizer, or disposition
result under an exact lease. It has no candidate-pair creation,
review-output publication, arbitrary fetch, arbitrary object, or other ref
route.

The credential adapter cannot select a repository, URL, ref, operation, or
credential source. It answers one broker session already bound to those values.

A worker sends a schema-validated operation identifier and closed arguments to
the native process owner. It never supplies raw Git argv, a path to Git, a URL,
a remote name, a refspec, a config pair, a credential selector, or an executable
selector. The owner resolves the identifier through the one role policy loaded
before `RUNTIME_LOCKED`. Cross-role and unknown identifiers refuse before Git,
repository, broker, or network access.

## Frozen executable population

The adopted direct Git identity is:

```text
path = C:\Program Files\Git\mingw64\bin\git.exe
byte_count = 4383048
sha256 = 1a0043555d254618f2d56c936c3d9a1fbfb878bc878416a133c346bc7835eda9
```

The adopted HTTPS remote-helper identity is:

```text
path = C:\Program Files\Git\mingw64\libexec\git-core\git-remote-https.exe
byte_count = 2529112
sha256 = 45e7df11f1b5ee4348a6380e0c66e8d41193d94d43478845f98db9e9942ed151
```

The Git MSYS runtime identity already observed in r001 is:

```text
path = C:\Program Files\Git\usr\bin\msys-2.0.dll
byte_count = 3368543
sha256 = 2ea49553e4c03055dcf1c4a2bef54668081a07663fba283f4b34cf70f2157191
```

Those three rows are inputs, not a claim that the complete closure has only
three files. The implementation-stage executable projection must enumerate and
bind every native image, sidecar, policy, and data file admitted by the real
route. It binds the reviewed askpass adapter by its held capsule final path,
byte count, SHA-256, `FileIdInfo`, source-set identity, and role policy. Broker
code is the in-process subsystem of the held live supervisor executable and
runtime-owner source projection; no broker executable path may be invented.

The following programs are absent from the positive route:

```text
C:\Program Files\Git\mingw64\bin\git-credential-manager.exe
C:\Program Files\Git\usr\bin\sh.exe
C:\Program Files\Git\usr\bin\bash.exe
C:\Windows\System32\cmd.exe
powershell.exe
pwsh.exe
```

Same bytes at another path do not satisfy an identity. Every admitted regular
executable, dependency, sidecar, and regular-file ancestor is opened with exact
`FILE_SHARE_READ`, denying write, delete, rename, and replacement, checked
through the handle, and retained from before the first reachable process until
operation reconciliation and Job active-zero. Directory ancestors use only
their separately frozen directory share semantics. A reparse component, wrong final path,
wrong file identity, changed bytes, inaccessible file, or unlisted dependency
refuses before the root process starts.

## Exact child environment and Git configuration

For every prepared Git-process coordinate, the owner constructs one complete
`pontius-environment-block-v1` and one complete `GIT_CHILD`-scope
`pontius-launch-directory-projection-v1`. Their coordinate-keyed rows form the
complete `pontius-git-environment-set-v1` for the dispatch. The set has the
dispatch digest and exactly one row per prepared Git child; owner-only schedule
rows have none. `CREATE_SUCCEEDED` rows biject with process lifecycle, while a
sole `CREATE_FAILED` or `NOT_ATTEMPTED` boundary row has null lifecycle digest
and remains bound to the ABORTED completion. A row's nonce and step/repeat
ordinals equal the launch and schedule coordinate. Its grammar ID and raw block
SHA-256 equal the expanded row when one exists, or the exact attempted/prepared
buffer on the terminal boundary. A network row also repeats the complete
reservation digest; an offline row has null.

The environment inherits no caller entry. Names use their frozen uppercase
ASCII spelling, are unique under Windows ordinal case-insensitive comparison,
and the complete merged population is globally sorted by
`CompareStringOrdinal(..., bIgnoreCase=TRUE)`. Fixed, dynamic, and network-only
entries are not concatenated as separate groups. Positive contiguous ordinals
record that one strict order. The raw block is exact
`name=value` plus U+0000 for each row, followed by one additional U+0000, all
encoded UTF-16LE without a BOM. Its exact even byte count and SHA-256 are
recorded and the same bytes are passed to `CreateProcessW`. Alternate case,
reordering, omission, addition, a hidden drive-current-directory entry, or a
different terminator count refuses.

Each child gets unique ordinary run, scratch, and profile directories. The
owner opens without traversal and holds every complete ancestor chain. `HOME`
and `USERPROFILE` are the same held `PROFILE_ROOT`; `HOMEDRIVE` and `HOMEPATH`
are its exact decomposition. `APPDATA`, `LOCALAPPDATA`, and `XDG_CONFIG_HOME`
resolve to its three declared empty descendants. No real user profile is
reachable. `TEMP` and `TMP` resolve only to the held scratch directory, while
the held run directory is the child's exact current directory.

Before any child exists, the owner creates exact zero-byte ordinary `.netrc`
and `_netrc` guard files in `PROFILE_ROOT` with one `CREATE_NEW` open each,
`FILE_SHARE_READ`, exact read/attribute/control/synchronize desired access, no
write/append/delete/security-write access, a noninheritable handle, and ordinary
open-reparse-point creation flags. It retains those original handles through
child Job active-zero and final revalidation. Exact access, flags, final paths,
FileIdInfo, zero length, and the empty-content SHA-256 are part of the
projection. A preexisting file or
writable/delete handle, case variant, mutation, rename, deletion, replacement,
hard-link write, or early close refuses. This occupies both Windows libcurl
fallback names without a close/reopen race. Any other observed profile-file
read is an undeclared source and refuses.

Both exact grammars contain these fixed entries:

```text
GIT_ATTR_NOSYSTEM=1
GIT_CONFIG_GLOBAL=NUL
GIT_CONFIG_NOSYSTEM=1
GIT_CONFIG_SYSTEM=NUL
GIT_LITERAL_PATHSPECS=1
GIT_NO_REPLACE_OBJECTS=1
GIT_OPTIONAL_LOCKS=0
GIT_TERMINAL_PROMPT=0
LANG=C
LC_ALL=C
PATH=C:\Windows\System32
PATHEXT=.EXE
```

Each grammar also contains exactly the dynamic keys `APPDATA`, `HOME`,
`HOMEDRIVE`, `HOMEPATH`, `LOCALAPPDATA`, `TEMP`, `TMP`,
`USERPROFILE`, and `XDG_CONFIG_HOME`. Their held absolute values obey
the launch-directory rules above.

`GIT_OFFLINE_V1` ends there. It contains no `GIT_ASKPASS`,
`GIT_EXEC_PATH`, `PONTIUS_ASKPASS_NONCE`,
`PONTIUS_ASKPASS_PIPE`, credential, HTTP, HTTPS-helper, proxy, cookie,
header, TLS-override, remote-helper, or broker-routing entry.

`GIT_NETWORK_V1` contains the same common population plus exactly:

```text
GIT_ASKPASS=<held shell-inert forward-slash capsule adapter path>
GIT_EXEC_PATH=C:\Program Files\Git\mingw64\libexec\git-core
PONTIUS_ASKPASS_NONCE=<canonical public nonce>
PONTIUS_ASKPASS_PIPE=<canonical public nonce-qualified pipe name>
```

The two `PONTIUS_ASKPASS_*` values are public routing data bound by the
launch dispatch, broker-session reservation, and completed broker session;
neither contains a credential. The trusted broker reserves a fresh step nonce,
derives and opens the pipe, and supplies those exact values to the network
environment builder before `CreateProcessW`. The adapter accepts no other
routing input.
The environment contains no `CURL_HOME`, `NETRC`, proxy, cookie, header, TLS override,
alternate askpass, SSH, GCM, browser, trace, caller namespace, alternate-object,
replace-ref, graft, shallow, config-count, author, committer, or clock-routing
entry. The sealed profile projection and its retained `.netrc` and `_netrc`
guards are required because Git's libcurl route may otherwise consult those
home files even when no explicit netrc variable exists.

The network grammar's `GIT_ASKPASS` value is the forward-slash rendering of
`broker_session.reservation.askpass_adapter.file_identity.final_path`. The
retained handle must still resolve to that preregistered capsule path. It
matches only this ASCII
grammar:

```text
[A-Za-z]:/[A-Za-z0-9._/-]+/pontius-askpass.exe
```

It contains no whitespace, backslash, quote, percent, exclamation, wildcard,
or Git shell metacharacter. The implementation test proves Git starts the exact
adapter directly with no `sh.exe`, `cmd.exe`, or other command interpreter.

The controller binds the complete repository projection from the schema
appendix: worktree root when present, `.git` entry, worktree Git directory,
common Git directory, objects and refs directories, exact control rows, and
same-query handle identities. A linked worktree's `.git` gitfile and
`commondir` file are parsed independently and must resolve exactly to the held
directories. A bare repository has no worktree or `.git` entry.

For an authority worktree repository, every direct Git invocation begins with
the exact held executable and explicit directory arguments below. A bare
authority repository uses only the `--git-dir` argument. Neither form uses
`-C` or Git discovery. Both config-prefix grammars share this exact
common prefix:

```text
C:\Program Files\Git\mingw64\bin\git.exe
--git-dir=<held absolute worktree Git directory>
--work-tree=<held absolute worktree root>
-c
core.hooksPath=NUL
-c
core.fsmonitor=false
-c
core.commitGraph=false
-c
core.multiPackIndex=false
-c
maintenance.auto=false
-c
gc.auto=0
-c
fetch.writeCommitGraph=false
-c
pack.useBitmaps=false
-c
pack.useBitmapBoundaryTraversal=false
-c
push.useBitmaps=false
-c
pack.readReverseIndex=false
-c
pack.writeReverseIndex=false
-c
commit.gpgSign=false
-c
tag.gpgSign=false
-c
protocol.allow=never
```

`GIT_OFFLINE_V1` ends at that line. It contains no `credential.*`,
`http.*`, `protocol.https.*`, remote-helper, public account, proxy,
cookie, header, or TLS entry. Its argv grammar contains no URL, remote, or
refspec that can invoke a transport.

`GIT_NETWORK_V1` appends exactly:

```text
-c
credential.helper=
-c
credential.interactive=true
-c
credential.useHttpPath=true
-c
credential.sanitizePrompt=true
-c
credential.username=<controller-bound public account name>
-c
protocol.https.allow=always
-c
protocol.version=2
-c
http.proxy=
-c
http.followRedirects=false
-c
http.emptyAuth=false
-c
http.proactiveAuth=basic
-c
http.allowNTLMAuth=false
-c
http.delegation=none
-c
http.sslVerify=true
-c
http.sslBackend=schannel
-c
http.sslAutoClientCert=false
-c
http.schannelUseSSLCAInfo=false
-c
http.extraHeader=
-c
http.saveCookies=false
```

The empty network `credential.helper` value resets the helper list. There
is no later helper value. Therefore Git's credential approve and reject actions
have no external helper to receive `store` or `erase`.

The pinned Git for Windows `v2.55.0.windows.3` source is authority for these
HTTP controls. Its `http.c:628-659,1131-1143` maps proactive Basic to the
credential/askpass path and `CURLAUTH_BASIC`; `http.c:124-125,413-419` removes
NTLM when `http.allowNTLMAuth=false`; and `http.c:1125-1139` gates Schannel
automatic client-certificate use. `http.delegation=none` forbids GSS
delegation. No `http.cookieFile` argument exists: pinned `http.c:1564-1574`
passes a null cookie-file pointer when unset, while an empty configured value
would enable libcurl's in-memory cookie engine. `http.saveCookies=false` remains
defense in depth, not the disabling mechanism.

System and global configuration are disabled. Before launch, the owner parses
the descriptor-derived common and worktree configuration through an independent
strict reader and requires the exact authorized multimap. It rejects an
include, URL rewrite, helper, askpass, proxy, cookie, extra header, credential
selector, HTTP auth override, delegation, SSL certificate selector, alternate,
graft, shallow file, namespace, unknown extension, remote mirror, or undeclared
refmap route. Generic and URL-scoped `http.cookieFile`,
`http.sslAutoClientCert`, `http.sslCert*`, `http.delegation`, proactive-auth,
and NTLM-auth keys are forbidden in repository configuration. Corresponding
`GIT_SSL_*` environment entries are absent. Command-line configuration is
fixed by the selected schedule's exact config-prefix ID and cannot be extended
by a worker.
A broker-required step uses the network environment and config prefix; every
other child uses the offline pair. Mixing IDs or placing a network-only key in
an offline child refuses.

The owner separately verifies every exact control row derived from the held
common and worktree Git directories, including configs, alternates, grafts,
shallow state, packed refs, replacement refs, `HEAD`, index, and `commondir`.
Object quarantine, namespaces, replacement refs, alternate object databases,
shallow boundaries, grafts, and configured fetch destinations are outside the
positive route.
Every held repository, launch, run, scratch, profile, and ancestor directory
also carries the same-handle `pontius-directory-open-fact-v1`: exact list/read-
attributes/read-control/synchronize access, read/write but no delete share,
backup-semantics plus open-reparse-point flags, noninheritability, and queried
granted access `00120081`. Created nonce roots use `CREATE_NEW`; admitted
repository and ancestor directories use `OPEN_EXISTING`.
Every repository projection also carries one complete
`pontius-repository-directory-ancestor-chain-v1` for each retained repository
directory. Same-handle rows run from volume root through target, prove every
reparse tag null, and remain held through Job active-zero and final
revalidation.

The repository projection also enumerates and holds every loose object, pack,
and pack index Git may consult. Existing commit graphs, multi-pack indexes,
bitmaps, reverse indexes, and other sidecars are recorded as forbidden-read
rows. Fixed configuration disables their supported read paths. Windows process
I/O evidence in characterization and rehearsal must prove they remain unread;
a poisoned forbidden cache influencing any result blocks acceptance. Raw object
parsing and the independent first-parent verifier remain the semantic authority.
The prelaunch projection is an immutable baseline, not an assertion that an
authorized write leaves the objects directory byte-identical. After Job
quiescence the owner re-enumerates storage and produces the complete
`pontius-repository-storage-observation-v1`: every baseline row remains exact,
and every added loose or pack-family carrier maps to one complete typed
provenance object. `FREEZE_PAIR`, `ADOPT_PAIR`, and create-attempt
`INTEGRATE_PACKET` carriers embed the complete object-write plan retained in
schedule/runtime evidence. Build and fetch carriers embed their complete typed
inventory. An unclassified addition, missing plan member, forbidden sidecar,
changed baseline carrier, or extra semantic object blocks success.

Network operations always use one canonical credential-free literal HTTPS URL
from the selected role table. The owner rejects userinfo, password, query,
fragment, percent encoding, alternate scheme, redirect, or noncanonical
host/port/path before process creation. Git receives those exact bytes as its
remote argv element. It never uses a remote name or a URL from repository
configuration.

## One-shot credential broker

The outer launch dispatch binds one complete ordered Git-child schedule
program. Each static network template binds the role, operation ID, step
ordinal, endpoint, audience, and ref slot IDs, expected prompt class, and exact
`OUTER_DISPATCH_ONLY` deadline policy; it contains no numeric wall, capability
literal, or launch nonce. For every actual network
child, the selected table resolves those slots to the literal URL, repository,
account, audience, and ref-derivation prefixes. The owner validates each ref's
closed derivation and resolution class. Selector-pinned stable refs equal the
normal preregistration or rehearsal-selector row. Route-derived stable refs use
the selected task and round and, in rehearsal, equal the selector row.
Authorization-derived attempt refs have descriptors only upstream; their full
values are derived once after the complete external authorization digest exists.
On a rehearsal route every task-scoped coordinate uses the authorization's
exact case and task binding, while only `HANDOFF_MAIN` uses that case's null-
binding row. Observation, the canonical ref-update set, argv, refspec, and
mutation evidence must consume the one class-valid result.
Its reservation and session bind the dispatch
nonce, repeat ordinal, pipe, held process, and Job. The broker receives a
repository-scoped token whose server permission
cannot address the production repository when the operation is a rehearsal.
The token is never placed in argv, environment, working files, receipts, logs,
exceptions, or captured child output.

Before creating the scheduled root Git process, the trusted broker validates
that template, generates a fresh one-use step nonce, derives the nonce-qualified
pipe name, creates the ACL-restricted listening pipe, and retains a canonical
session reservation. The environment receives exactly that reserved nonce and
pipe name. Git then starts suspended. After the owner binds the held Git process
identity and assigns its Job, the broker completes the process-bound session
document and rechecks the reservation, environment, template, table instance,
process, and Job. Any mismatch terminates the suspended process; only equality
permits resume. The pipe name and nonce are public routing values; neither is
the credential. This session document is a pre-resume binding and its
one-response field is a cap, not evidence of redemption.
If a successful reservation becomes terminal before that session document can
be completed, including `CreateProcessW`, Job-assignment, or pre-resume
validation failure, the broker retains a tagged pre-session result. It closes
the reservation's listener and zeroes any credential buffer before completing
that result. Every successful reservation therefore has exactly one terminal
session or pre-session result; neither process failure nor listener close can
silently discard it.
Only the held askpass adapter in the authorized Job may redeem the session. The
broker completes the connection on the exact retained server handle, obtains
the actual client PID with `GetNamedPipeClientProcessId`, opens and holds that
process, and measures its creation/image identity, liveness, and membership in
the exact scheduled Job. Immediately before the sole write it repeats the pipe-
PID, held-handle PID, liveness, Job, and image checks. Any failed query, open,
mismatch, dead process, or substituted pipe/client returns no credential and is
retained in the terminal attempt record. Only after equality does the broker
write the one exact frame, wait for monitored `FlushFileBuffers` to prove the
client read every pipe byte, call `DisconnectNamedPipe`, close the server
handle, and wait the same held adapter process to signal. Only adapter exit zero
after that sequence counts one redemption; completed `WriteFile` or flush alone
does not. The broker then zeroes its buffer and retains typed refusal evidence
for a wrong adapter identity, Job, transfer, or adapter exit. The
outbound length-prefixed byte pipe carries no client request frame: a wrong pipe name, nonce,
or ordinal never reaches the retained server handle, and the handle closes after
the sole response. An operation, table, template, environment, or route mismatch
is sticky broker failure before resume. A later schedule step cannot reuse an
earlier pipe or credential session.
`WriteFile` is issued with one manual-reset event and a nonnull `OVERLAPPED`;
the active deadline cancels it with `CancelIoEx`. `FlushFileBuffers` runs only
on a retained blocking thread cancelled with `CancelSynchronousIo`. Both are
joined before disconnect or close and retain complete
`pontius-broker-cancellable-io-v1` results bound to the exact reservation,
session, retained server handle, operation nonce, deadline, and event or flush-
thread identity. The write terminal records the exact cancel return/error,
event wait, `GetOverlappedResult` outcome, completed bytes, and OVERLAPPED
retirement. The flush binding is complete and its typed terminal object records
the exact cancel return/error, flush result/error, signal, wait result, exit,
join completion, and successful later handle close. A prefix, cancelled flush,
failed wait, early close, or
unjoined I/O operation can never become redemption.
After terminal close, the broker completes the secret-free session result with
the complete request-ordered client-attempt bindings, measured scheduled-Job
membership, request and response counts, close state, buffer-zero state, and
terminal reason. A nonmember attempt is retained as typed refusal evidence and
never represented as an admitted process binding. Success requires the complete
result set and exactly one validated member-adapter redemption for every network
child; missing or ambiguous lifecycle evidence refuses.

Git receives the selected public account through the fixed command-line
`credential.username` assignment, so the accepted path has one password prompt.
`pontius-askpass-prompt-grammar-v1` renders exact UTF-8 `Password for '`, the
selected credential-free endpoint with that account RFC3986-percent-encoded as
userinfo after `https://`, and exact `': `. Git starts the held absolute adapter selected by
`GIT_ASKPASS`. The adapter checks those complete bytes as a mandatory
condition, opens only its authorized pipe session, accumulates the exact four-
byte little-endian length and bounded payload across partial overlapped reads,
requires exact EOF after that payload, then writes the credential plus one LF
to Git's private askpass stdout through a bounded full-write loop. It exits zero
only after all payload bytes plus LF are accepted; a failed write or zero-length
progress exits nonzero. It then zeroes its private buffers. It treats early EOF, zero/over-cap
length, NUL/CR/LF payload, trailing bytes, a second frame, or deadline expiry
after a prefix as failure and exits nonzero. Forced process teardown is retained
as such and makes no physical adapter-memory-zeroization claim. Its stderr is
empty.

The prompt string is not authority. It does not prove the operation, URL, ref,
TLS peer, or credential audience. Those facts come only from the controller
authorization, loaded role policy, broker session, exact Git grammar, and
server-scoped token.

In the disposable HTTPS rehearsal, the server secret is armed only through one
mutually authenticated control session. Every ACK, CONSUMED, and DISARMED
payload is bound by a complete `pontius-authenticated-server-artifact-v1` whose
independent verifier validates the signed envelope under that session's exact
certificate and TLS binding. Every rehearsal network step carries a complete
`pontius-server-secret-lifecycle-v1` with one complete tagged coordinate.
Fault-bound coordinates repeat the reservation and nonce; reservation-free
coordinates bind broker session, dispatch, request nonce, task binding, and
step while both fault fields are null. Server acceptance requires exact ARM,
ACK, CONSUMED, DISARMED and one use; no acceptance requires authenticated ARM,
ACK, DISARMED and zero remaining uses. Evidence kind cannot omit this lifecycle.
A client-only success or matching remote result does not satisfy the gate.

An adapter nonzero exit, second invocation, username prompt, unknown prompt,
pipe failure, timeout, or broker refusal terminates the operation. With
`GIT_TERMINAL_PROMPT=0`, Git cannot fall back to a terminal. `GIT_ASKPASS` takes
precedence over repository `core.askPass`; the repository config verifier also
requires that key to be absent.

No accepted source, executable, configuration, environment, argv grammar, or
audit-policy route can invoke credential `store` or `erase`, GCM, a browser, a
shell, credential-bearing netrc, a generic helper, or another askpass program.
The only admitted netrc file opens are reads of the two exact retained zero-byte
guard identities. Observation of any other such image, process, file, registry,
or network route, or changed guard bytes, terminates the Job and refuses. This
is an enforceable closed-route claim; the design does not inspect or attest
unrelated user credential-store contents.

## Closed operation grammar

Each role policy maps a typed operation ID to one complete argv suffix. Schema
validation rejects unknown fields, omitted fields, duplicate keys, uppercase or
noncanonical OIDs, relative paths, symbolic refs, remote names, and values not
equal to the controller authorization. No string concatenation creates an
option or refspec.

The complete role operation sets are:

```text
builder:    FREEZE_PAIR
builder:    ADOPT_PAIR
builder:    BUILD_REVIEW_OUTPUT
publisher:  PUBLISH_PAIR
publisher:  FETCH_FOR_ADOPTION
publisher:  PUBLISH_REVIEW_OUTPUT
integrator: FETCH_MAIN_INPUTS
integrator: BUILD_MAIN_OVERLAY
integrator: INTEGRATE_PACKET
integrator: FINALIZE_REVIEWS
integrator: PUBLISH_DISPOSITION
```

Each identifier has one closed predecessor, input, object, ref, process,
observation, and terminal-result schema. `BUILD_REVIEW_OUTPUT` and
`BUILD_MAIN_OVERLAY` construct objects offline; they never publish a ref.
Adding or renaming an identifier requires a new reviewed design round.

Every identifier also requires one complete owner-only route selector in the
launch dispatch. It is never a planner input. Later raw-object-v5 launches use
`pontius-round-preregistration-v1`; the bundle's preacceptance HTTPS campaign
uses only `pontius-utility-rehearsal-selector-v1`. Its route-selector identity
equals the authorization; this post-projection identity is distinct from every
static source-bound document. The complete selector is carried and held through
dispatch and runtime evidence rather than inserted into the accepted source
projection. A normal launch's task and round equal the
preregistration root. A rehearsal launch's authorization and dispatch task,
round, and `rehearsal_task_binding_id` equal the selected campaign binding; the
selector root task and round remain the utility-bootstrap identity. Task-scoped
refs derive from that binding, while the case-shared `HANDOFF_MAIN` row has no
binding. Role-applicable endpoint, table, and derived ref coordinates must
agree. Builder validates only its local slots and receives none of the selector
bytes. Missing, cross-kind, production-capable rehearsal, or unequal selection
refuses before a repository, credential route, or process is opened. The bundle
cannot create or consume a normal round preregistration for its own design or
implementation bootstrap.

Each identifier has one frozen `OBSERVE` schedule and a closed set of mutation
schedule variants where meaningful. An `OBSERVATION_ONLY` schedule contains
only local reads, literal remote queries, and an optional object-only fetch into
a new no-ref scratch database. It has no authority-database object write,
`update-ref`, or `push` step and may be issued without a prior eligibility
result. A `MUTATION_ATTEMPT` schedule binds the fresh precondition observation
and its mechanically derived variant, permits at most one declared local
recovery-ref transaction and one remote transition with a decisive
reobservation between them, then reconciles. A terminal exact observation
closes without a mutation dispatch. Integration uses different variants for
absent and exact local-attempt state; no fixed step is omitted at runtime. One
outer dispatch starts the role process and the complete schedule program. Every
Git child has a fixed `(step ordinal, repeat ordinal)` coordinate in the
validated concrete expansion, and every network child receives a distinct
one-use broker session.

The scratch database starts from the exact
`pontius-observation-scratch-seed-v1` population: only `git`, `git/objects`,
`git/refs`, and `git/HEAD`, whose bytes name the fixed unborn branch. Before any
semantic result, `pontius-observation-scratch-teardown-v1` inventories every
seed and fetched-residue entry and proves either deepest-first removal or one
atomic move to a never-reused quarantine root. Its typed parent-directory
observation proves the old name absent; quarantine additionally binds the same-
volume create-new `pontius-atomic-directory-move-fact-v1` and retained
destination identity. Partial deletion, omitted residue, changed quarantine
bytes, or an old root still present refuses.

Each nonowner schedule row starts at most one root Git process and returns only
bounded lifecycle completion plus that process's declared primitive result.
`QUERY_LOCAL_REFS` and `QUERY_REMOTE_REFS` parse exact NUL- or LF-framed rows
for only their authorization-bound selectors. One parsed query is evidence,
not a terminal state claim. Stable observations require the schedule's repeated
queries, raw object reads, identity checks, and equality rules.

Fetch and mutation rows return process-completion facts only. Later query and
raw-read rows establish their postconditions. `FETCH_REVIEW_OUTPUT_OBJECTS` is
scratch-object support for review finalization and grants no destination ref.
For every network fetch or mutation, only a natural root-process return before
the active deadline may continue into the same dispatch's already scheduled
read-only observation suffix. If the active deadline, cancellation, broker
failure, Job limit, output cap, channel loss, or another terminal cause
terminates the child, the schedule aborts at that coordinate: cleanup starts no
new process or network operation, preserves authority state as unknown, and a
later fresh `OBSERVATION_ONLY` dispatch is required before any retry or state
claim. The cleanup reserve never funds a Git query. This rule applies to pair,
review-output, main-integration, finalizer, disposition, and object-fetch routes.
After all required primitives finish, an `OWNER_ASSEMBLE` step with no process
constructs the adoption receipt, object-build receipt, stable observation, or
complete observation set from the bound transcript and still-held sources. A
single child exit or stdout stream can never serve as its own postcondition.

The stable transition authorization contains only expected selectors and
immutable inputs. It never names an observation, mutation precondition,
dispatch, or terminal result. Observation-only dispatch can therefore precede
eligibility. The later mutation dispatch binds the exact returned observations
through its operation precondition.

An observation scratch invocation instead uses the held executable, the same
frozen configuration list, and only
`--git-dir=<held dispatch-owned scratch Git directory>`. The scratch projection
is bare, has no worktree, alternates, refs, or authority-shared object directory,
and never receives an authority write. `FETCH_FOR_ADOPTION` and the future
integrator main-input fetch are mutation schedules that intentionally place
object-only residue in the authority object database; they are not scratch
observations and do not create refs.

All repository object IDs are lowercase 40-hex SHA-1. The owner first verifies
that the repository's object format is `sha1`. Another object format requires a
new schema and design round.

The offline grammar contains only the exact forms required for:

- hashing a retained blob without filters;
- reading one exact object by OID and expected type;
- listing one exact tree with NUL framing;
- hashing one canonical binary tree body as a tree object;
- hashing canonical commit bytes as a commit object;
- checking one exact ancestry relation;
- reading and transactionally updating enumerated local refs; and
- computing a declared diff without rename inference.

The local-ref form is exact `update-ref --stdin`. The owner derives the complete
null-endpoint ref-update set after authorization, renders ASCII `start`, one
ordered `create <ref> <oid>` line per row, then `prepare` and `commit`, each
terminated by LF, and closes stdin immediately after the final LF. No CR, NUL,
blank line, quoting, option, update, delete, verify, abort, extra command, or
delayed EOF exists. The dispatch and schedule bind the complete
`pontius-local-ref-transaction-v1`; the expanded row binds the actual
`pontius-git-stdin-write-v1`. A later exact intended-ref observation cannot
conceal a different or additional stdin command.

The network grammar contains only the suffixes defined below. Options appear
in the exact displayed order. No operation admits an upload-pack override,
receive-pack override, tag, submodule, hook, remote helper selector, destination
fetch ref, deletion refspec, wildcard, abbreviated OID, or extra `-c` pair.

## Canonical raw commit grammar

Every commit-producing operation supplies complete canonical commit bytes to:

```text
hash-object -t commit -w --stdin
```

No author, committer, timestamp, offset, message, encoding, or parent value is
read from Git configuration, process environment, repository state, or the
wall clock.

The canonical UTF-8 preimage is:

```text
tree <lowercase 40-hex tree OID><LF>
parent <lowercase 40-hex parent 1 OID><LF>
...
author <exact name> <<exact email>> <decimal epoch seconds> +0000<LF>
committer <exact name> <<exact email>> <decimal epoch seconds> +0000<LF>
<LF>
<exact message bytes ending in one LF>
```

The schema binds the exact name, email, epoch seconds, message bytes, tree, and
ordered parent vector for each object. Names and emails contain no `<`, `>`, LF,
CR, NUL, or ambiguous whitespace. Epoch seconds use canonical unsigned decimal
with no leading zero except zero. The timezone is exactly `+0000`. There is no
`encoding`, signature, merge tag, continuation header, blank header, or unknown
header. The message is valid UTF-8, contains no CR or NUL, and ends in exactly
one LF.

Parent order is semantic:

- candidate: the exact base is the only parent;
- freeze packet: the exact candidate is the only parent;
- packet integration: exact handoff main predecessor first, exact packet second;
- reviewer output: the identical cold-input integration commit is the only
  parent;
- review finalizer: the exact fresh handoff-main predecessor is the only parent;
- disposition: the exact fresh handoff-main predecessor is the only parent; and
- utility ceremonial integration: the exact freshly observed P product
  predecessor is the only parent, while its tree equals the reviewed Stage-2
  candidate tree and its result OID is distinct from that candidate OID;
- utility ceremonial integration record: the exact fresh H-main predecessor is
  the only parent, the raw kind is
  `UTILITY_CEREMONIAL_INTEGRATION_RECORD`, and its artifacts bind the P result;
  and
- utility bootstrap durable disposition: the exact fresh H-main predecessor is
  the only parent, raw kind is `UTILITY_BOOTSTRAP_DURABLE_DISPOSITION`, and its
  preserved history contains the integration record.

The owner independently constructs the Git object framing
`commit <decimal-byte-count><NUL><preimage>`, computes its SHA-1, writes the
preimage through the exact offline Git operation, and requires Git to return the
same OID. It then reads the stored object through two independent paths and
requires byte identity before a ref transaction. Different clocks, identities,
configurations, locales, clean repositories, or retry times must produce the
same bytes and OID.

## Exact remote-pair operations

Let `CREF` and `PREF` be the two full, controller-bound permanent refs. Let `C`
and `P` be their expected commit OIDs. Pair observation uses:

```text
ls-remote
--refs
<literal HTTPS URL>
<CREF>
<PREF>
```

Pair creation uses one atomic request:

```text
push
--atomic
--porcelain
--no-verify
--no-follow-tags
--recurse-submodules=no
--force-with-lease=<CREF>:
--force-with-lease=<PREF>:
<literal HTTPS URL>
<C>:<CREF>
<P>:<PREF>
```

The two empty expected-value leases mean create from absence. Neither refspec
has a leading plus. No sequential fallback exists. A server that does not
support atomic push blocks the route.

After every natural push return before the active deadline, including exit
zero, nonzero, or lost output, the publisher performs the already scheduled
fresh exact query. If the active deadline, cancellation, or another terminal
cause terminates the push, cleanup starts no new child or network operation,
preserves state as unknown, and requires a later fresh `OBSERVATION_ONLY`
dispatch to classify it. It accepts the
complete state only as defined by the v5 amendment. Exact candidate plus absent
packet is `PAIR_PARTIAL_CANDIDATE_ONLY`; absent candidate plus exact packet is
`PAIR_PARTIAL_PACKET_ONLY`. Both are fatal because one atomic request promised
those states were unreachable. The publisher never repairs either side
separately.

The accepted policy contains no update or delete operation for `CREF` or
`PREF`. Exact pair presence is permanent spent evidence, not permission to push
again.

## Object-only fetch and fresh adoption

An authorized publisher may fetch the exact expected pair as nonauthority
object residue with no destination refs:

```text
fetch
--refmap=
--no-write-fetch-head
--no-tags
--no-recurse-submodules
--no-auto-maintenance
--no-write-commit-graph
<literal HTTPS URL>
<CREF>
<PREF>
```

The publisher queries the pair before and after this fetch and requires the
same exact expected OIDs. It verifies that those exact objects now exist, then
issues the canonical adoption receipt defined by the v5 amendment. The fetch
creates no local ref, tracking ref, tag, `FETCH_HEAD`, commit graph, maintenance
run, checkout, index entry, or authority fact.

On a rehearsal route, the held selector's upstream adoption-chain set maps this
fetch case, step, and task binding to exactly one later `ADOPT_PAIR` step and
builder-intent fixture. Fetch authorization and receipt repeat that strict row
digest and its candidate, packet, intent-blob, and SHA-256 identities. The fetch
does not consume the later fixture or choose an identity from runtime output.

The later builder-adopt operation has no network grammar. Under a new one-use
dispatch, it validates the receipt, complete object graph, packet inventory,
candidate manifest, intent, and expected local tuple before one atomic local
ref transaction. In rehearsal it also consumes the exact linked fixture at its
declared adopter coordinate and repeats the same chain-row digest.

## Independent review-output operations

Let `OREF` be one exact permanent output ref and `O` its expected reviewer-output
commit. Observation uses:

```text
ls-remote
--refs
<literal HTTPS URL>
<OREF>
```

Independent create-only publication uses:

```text
push
--porcelain
--no-verify
--no-follow-tags
--recurse-submodules=no
--force-with-lease=<OREF>:
<literal HTTPS URL>
<O>:<OREF>
```

The output refspec has no leading plus. An exact ref is terminal success and
closes lost acknowledgement. An absent ref remains unproduced. A different,
malformed, ambiguous, or unavailable observation refuses without repair.
The publisher schedule uses the dedicated `OBSERVE_REVIEW_OUTPUT` typed request
for every preflight and reconciliation query; the remote-write request cannot
be overloaded as an observer.

For a later selected raw-object-v5 round, the finalizer observes exactly two
output refs.
`EXACT/ABSENT`, `ABSENT/EXACT`, and `ABSENT/ABSENT` are
`WAITING_FOR_REVIEWS`, because the two publishers are independent. They are not
candidate/packet `PARTIAL` states.

After both refs are exact, their observation becomes an input to the closed
`FETCH_MAIN_INPUTS` operation below. The finalizer has no separate fetch route.
No output publisher can select another reviewer's ref, and the finalizer cannot
create or update one.

## Main-input fetch before overlay construction

`FETCH_MAIN_INPUTS` is the integrator's only authority-object-database fetch.
An observation-only dispatch first uses a new scratch bare repository to derive
the complete closed object inventory from stable main plus permanent-input
observations. The mutation dispatch binds that inventory and fetches the exact
full refs with `--refmap=`, `--no-write-fetch-head`, `--no-tags`,
`--no-recurse-submodules`, `--no-auto-maintenance`, and
`--no-write-commit-graph`. It supplies no destination ref.

Packet integration fetches main, candidate, and packet. Review finalization
fetches main and both reviewer outputs. Disposition fetches main and both
permanent reviewer outputs. Every ref is queried before and after fetch and
must remain at its bound OID. The authority object database must reproduce the
scratch-derived complete inventory before the fetch receipt is issued.

The operation may leave only unreachable object residue. It creates no local
or remote ref, tracking ref, tag, `FETCH_HEAD`, index entry, commit graph, MIDX,
bitmap, reverse index, or maintenance run. `BUILD_MAIN_OVERLAY` requires that
receipt and inventory; it has no fetch step of its own.

## Exact main integration and lease preflight

Let `HREF` be the one typed full-ref slot resolved solely from the selected
table and route selector's `HANDOFF_MAIN` row. A normal route resolves it exact
`refs/heads/main`; a rehearsal route resolves it to that case's sole case-
shared, null-task-binding main row. Ref-update set, query, fetch, argv, refspec,
lease, observation, and server-event values all equal this one resolved byte
string. No literal production-main fallback is permitted on a rehearsal route.
Let `H0` be the controller-authorized predecessor observed at `HREF` and `P` the exact
payload commit. For initial packet publication, `P` is the permanent freeze
packet commit. Let `I(H0,P)` be the canonical integration commit whose parent
vector is exactly `[H0, P]` and whose tree is the authorized exact overlay of
`P` onto `H0`.

Before any main push, the integrator independently proves:

1. `H0`, `P`, the overlay schema, protected projection, and expected `I` equal
   the transition authorization;
2. raw parsing of `I` yields exactly tree, parent 1 `H0`, parent 2 `P`, and no
   other parent or header;
3. every `H0` path outside the authorized overlay is byte-, mode-, type-, and
   existence-equal in `I`;
4. every overlay and shared append operation has its exact declared source,
   predecessor, and result bytes;
5. the task-protected projection changes only by the authorized transition;
6. an independent ancestry check proves `H0` is an ancestor of `I`; and
7. a stable fresh remote observation is exactly `H0`.

The push uses an ordinary refspec and an exact compare-and-swap lease:

```text
push
--porcelain
--no-verify
--no-follow-tags
--recurse-submodules=no
--force-with-lease=<HREF>:<H0>
<literal HTTPS URL>
<I>:<HREF>
```

There is no leading plus and no separate force option. The explicit lease is
force-capable, so the offline parent and ancestry preflight is mandatory proof
that the proposed update is a fast-forward. A lease rejection never triggers a
push against a newly observed predecessor. It requires classification and, when
appropriate, fresh controller authorization for a newly computed result.

## Stable main observation

Main observation first performs strict `ls-remote --refs` for the exact full
integration ref. To obtain an observed object without changing a local ref, the
integrator uses:

```text
fetch
--refmap=
--no-write-fetch-head
--no-tags
--no-recurse-submodules
--no-auto-maintenance
--no-write-commit-graph
<literal HTTPS URL>
<HREF>
```

It then repeats the exact query. The two observations must be equal and the
observed commit must exist locally. A changed observation restarts only the
bounded read phase; it never authorizes mutation. An equal-before-and-after
sample cannot exclude an administrator or nonconforming writer performing an
ABA reset. Without an append-only server or external audit source, the route
makes no historical no-reset claim; accepted writers are still constrained to
the exact fast-forward protocol.

Before classification, the owner performs the bounded raw-object all-parent
spent-result DAG observation. If the expected result is reachable only through
a side parent, the transition is spent with
`RESULT_SIDE_ANCESTOR/PROTECTED_CONFLICT`; it can never appear eligible again.
An unavailable or capped DAG observation blocks mutation. The classifier then
walks the complete first-parent chain from the observed main.
At each commit it compares against expected `I` before comparing against `H0`.
It parses the raw commit chain independently from protected-task evaluation and
validates the protected projection at every first-parent edge. Each row carries
one closed task status and reason plus nullable inventory, phase, and phase-
evidence fields. A readable raw chain may therefore establish result lineage
while a protected-inventory or future-bundle failure records `TASK_UNKNOWN`.
Endpoint equality alone is insufficient because a protected change followed by
a revert is still a conflict.
The plan binds count and canonical-byte caps for both the walk and every inline
phase-evidence bundle. The owner reserves one compact failure row and enforces
the caps before allocation. A raw-chain failure before an anchor yields lineage
unknown; task evidence failure after a classifiable result yields task unknown.
No prefix is authoritative.

Lineage classification stops at the first expected result or predecessor
coordinate. Phase verification uses a second bounded raw-object walk starting
at the expected predecessor and continuing through every historical transition
and intervening commit to an explicitly validated `NO_TASK` baseline. It
consumes the complete historical phase-input set once in phase order. A raw,
inventory, permanent-input, phase-input, or cap failure in this older history
forces task state unknown while preserving an already classified lineage and
`result_seen`. Where predecessor lineage overlaps history, the anchor facts are
byte-equal and no bundle is consumed twice.

The lineage axis is:

- `PREDECESSOR_EXACT`: observed main equals `H0`;
- `PREDECESSOR_DESCENDANT`: first-parent walk reaches `H0` without first seeing
  `I`;
- `RESULT_EXACT`: observed main equals `I`;
- `RESULT_DESCENDANT`: first-parent walk sees `I` before `H0`;
- `RESULT_SIDE_ANCESTOR`: the all-parent spent-result observation reaches `I`
  but the first-parent walk does not;
- `UNRELATED_OR_ABSENT`: main is absent or a complete walk sees neither value;
  and
- `UNKNOWN`: observation, fetch, parse, walk, or object availability fails
  before either expected anchor can be classified.

The `task_state` axis is:

- `INTACT`: every relevant edge preserves the exact task semantic projection;
- `PROTECTED_CONFLICT`: a task-owned blob, mode, type, absence, or task-owned
  record in an append-only shared file changes at an unauthorized edge;
- `TASK_UNKNOWN`: an anchor was found but later protected evidence is
  missing, unreadable, ambiguous, or belongs to a same-task phase whose future
  bundle cannot enter this old authorization; and
- `NOT_APPLICABLE`: lineage is unrelated, absent, or unknown before either
  expected anchor is established.

The observation also carries derived boolean `result_seen`. It is true as soon
as the walk encounters `I` and remains true even if a later object or edge is
malformed, missing, or conflicting. Such an observation cannot retry the old
transition.

The decision table is:

| Lineage | Task integrity | Result |
| --- | --- | --- |
| `PREDECESSOR_EXACT` | `INTACT` | one push is eligible |
| `PREDECESSOR_DESCENDANT` | `INTACT` | `MAIN_PREDECESSOR_CHANGED`; no push |
| predecessor lineage | `PROTECTED_CONFLICT` | refuse; no push |
| predecessor lineage | `TASK_UNKNOWN` | preserve and refuse |
| `RESULT_EXACT` | `INTACT` | complete; closes lost acknowledgement |
| `RESULT_DESCENDANT` | `INTACT` | complete; closes lost acknowledgement |
| `RESULT_DESCENDANT` | `TASK_UNKNOWN` | spent; never retry; future evidence unavailable |
| result lineage | `PROTECTED_CONFLICT` | `MAIN_PROTECTED_CONFLICT`; spent |
| result lineage | `TASK_UNKNOWN` | `MAIN_UNKNOWN`; spent |
| unrelated, absent, or unknown | `NOT_APPLICABLE` | refuse; no push |

Any observed ancestry containing `I` spends this exact transition,
even when a later edge changed protected task bytes. Conflict after `I` is a new
correction or disposition problem; replaying the old transition cannot repair
it. A predecessor descendant does not inherit authority: parent 1 and the
result OID would change, so the controller must authorize a fresh exact
`(H0, P, I)` tuple.

After every natural main push return before the active deadline, the same dispatch's
already scheduled stable observation and two-axis classification run under the
same mutex and held identities. If the active deadline, cancellation, or
another terminal cause terminates the push, cleanup starts no new child or
network operation, preserves authority state as unknown, and requires a later
fresh `OBSERVATION_ONLY` dispatch before retry or state claim. Push status and
raw porcelain bytes are nonsemantic. Only a
complete locale-fixed bounded push-status parse becomes typed status facts.
Query and fetch steps have null push status and use their closed typed
observations. A post-process owner step joins the immutable lifecycle fact to a
fresh ref observation only on the pre-deadline route; the operation contract
selects the first non-success outcome, or the last outcome when all succeed.

## Review finalizer operation

The review finalizer is a distinct closed main operation. It does not reuse the
two-parent packet-integration grammar. Let `Hf0` be its exact fresh main
predecessor and `F` the canonical one-parent finalizer commit.

The finalizer authorization binds `Hf0`, `F`, both exact output refs and commit
OIDs, both external package-manifest SHA-256 values, every copied destination
row, both issuer ledger fragments, their ordinal append order, the exact
predecessor and result progress bytes, and the protected review projection.

Before push, the finalizer proves that `F` has only parent `Hf0`, its tree is the
exact authorized byte-for-byte copy and append result, and every other `Hf0`
path is unchanged. An independent ancestry check must prove `Hf0` is an ancestor
of `F`.

The finalizer push is:

```text
push
--porcelain
--no-verify
--no-follow-tags
--recurse-submodules=no
--force-with-lease=refs/heads/main:<Hf0>
<literal HTTPS URL>
<F>:refs/heads/main
```

It uses an ordinary refspec, no leading plus, and no separate force option. The
lease remains force-capable, so the exact parent, ancestry, and tree preflight is
mandatory.

Finalizer reconciliation walks first parents and compares `F` before `Hf0`. A
clean exact `Hf0` is eligible. A clean `Hf0` descendant requires fresh
authorization and a recomputed `F`. Exact `F` or a clean `F` descendant closes
lost acknowledgement. Any `F` lineage with a later protected conflict is
terminal `MAIN_PROTECTED_CONFLICT`; the old finalizer never pushes again.

The finalizer copies package blobs but does not make the two sibling output
commits reachable from main. Their permanent refs remain the reviewer-to-
finalizer authority and cannot be deleted after publication.

## Disposition publication

Disposition is a distinct integrator operation after exact finalized reviews.
The controller completes the disposition report, canonical record, and one
program-ledger fragment first. `BUILD_MAIN_OVERLAY` derives `D` from a fresh
held main predecessor, adds those exact artifacts, and preserves every other
protected byte. It does not append the controller line to task progress or the
program ledger; the adopted Stage 5 retains that authority. `D` has the fresh
predecessor as its sole parent.

`PUBLISH_DISPOSITION` validates the finalizer lineage, exact record and overlay,
raw `D` bytes, protected before/after inventories, and fresh main value. It then
uses the same ordinary refspec, exact lease, fast-forward proof, and two-axis
post-return reconciliation. A seen `D` result is terminal even if later
protected evidence conflicts or becomes unknown. The handoff disposition does
not substitute for the separately authorized product-repository Stage 5 commit.

## Local serialization and attempt identity

Every classifier and writer for one repository acquires the same visible
repository-scoped authority mutex before its first local state read. The mutex
name derives from the held common-Git-directory `FileIdInfo` and one suite-wide
constant, not a role policy, caller string, or worktree path. Linked worktrees
and different roles sharing an object/ref database therefore share one mutex.
It is an ACL-restricted `Global\` object visible across Terminal Services
sessions to builder, publisher, integrator, adoption, and recovery processes.
Cross-session creation, denial, and abandonment are rehearsed. A process that
cannot acquire or verify it refuses.

Each acquisition produces one complete
`pontius-repository-mutex-lifecycle-v1`. Its event order is acquisition,
then either the exact read-only classification prefix or the exact classify,
mutate, observe prefix, followed by object validation, process completion, any
remote reconciliation, receipt durability, Job active-zero, and the self-free
final-revalidation core. Same-thread release and handle close complete the
lifecycle; only then is the outer final-revalidation object assembled.
`WAIT_ABANDONED`, timeout, failure, an omitted milestone, or early
release records no successful protected mutation and refuses; every action
digest equals its actual retained evidence object.

The owner retains the mutex through object validation, local ref transactions,
process completion, remote reconciliation, receipt durability, Job active-zero,
and final identity revalidation. Read-only user Git outside this protocol is not
claimed to honor the mutex; governed state classification therefore also
checks exact refs and held repository control files on every transition.

A main transition authorization is idempotent only for one exact `(H0, P, I)`
tuple. Its local attempt intent and result refs are qualified by the
authorization digest and are created together before a remote push. They are
local reconstructible residue, not global spent evidence and not atomic with
remote main. A fresh clone may recreate the exact pair after validating the
authorization and objects. Partial, different, or malformed attempt state is
preserved and refused.

Every actual launch also requires a fresh one-use dispatch nonce. Replaying a
consumed launch dispatch refuses even when the transition authorization remains
eligible for a newly authorized retry.
Consumption is the exact durable controller-registry record created, flushed,
reopened, and held before `CreateProcessW`, not process output or volatile
memory. Startup validates every permanent record before accepting a dispatch;
unknown registry state blocks launches. A crash after record durability spends
the nonce even when no child started.

## Process and timeout boundary

The root process starts with non-NULL exact `lpApplicationName`, the exact
mutable raw buffer from its complete `pontius-windows-command-line-v1`, the same
raw environment bytes recorded above, a
held current directory, and an explicit inherited-handle list. Its creation-
flag set is exactly `CREATE_SUSPENDED | CREATE_UNICODE_ENVIRONMENT |
EXTENDED_STARTUPINFO_PRESENT` with no other flag. It starts suspended, is
identified through its process handle, enters a kill-on-close no-breakaway Job,
and only then resumes.
Argument one equals the held executable final path. The owner retains a pristine
buffer, independently rerenders the ordered arguments with the frozen quoting
equation, and rechecks the UTF-16LE terminator, byte count, and hash during final
revalidation. `CreateProcessW` may mutate only the separate launch copy.
For a network step, the listening pipe and canonical reservation already exist;
the process-bound broker session must be complete and equal to the exact child
environment before resume.
When process creation or Job assignment fails, the listener remains retained
until its pre-session terminal result proves close and credential-buffer
disposition. The failed coordinate never receives a fabricated session binding.

`CreateProcessW` uses exact `bInheritHandles=TRUE`. Only handles in the
`PROC_THREAD_ATTRIBUTE_HANDLE_LIST` are created inheritable; every other source
handle is non-inheritable. A false flag, unlisted inheritable handle, or listed
non-inheritable handle refuses before resume.

Only declared private stdin, stdout, and stderr handles are inherited. For a
local-ref transaction, the sole parent stdin write handle supplies exactly the
dispatch-bound transaction stream, records every accepted byte, and closes at
EOF before process completion is accepted. A prefix or divergence terminates
the operation and remains cleanup evidence. The
credential pipe is opened by name by the adapter and protected by its ACL,
nonce, broker binding, one-frame state, and exact bounded framing policy.
Identity, authority, mutex, object,
and repository handles are non-inheritable.

Every successful Git root creation obtains a terminal lifecycle row keyed to
its schedule coordinate. If Job assignment fails, the owner directly terminates
and waits the still-suspended held process; the empty schedule Job proves
nothing about that process and the primary thread never resumes. After
assignment, the lifecycle row repeats live Job membership before resume and
later requires both direct process signal and Job active-zero. Handles close
only after those observations.

The launch dispatch binds the unique accepted runtime-limit row for its role,
operation, mode, and schedule variant. Its CPU, memory, active wall, cleanup
reserve, output, and schedule active-process limits must equal that row and its frozen calibration
receipt. That receipt is the complete typed
`pontius-runtime-limit-calibration-receipt-v1`, including measured workloads,
their complete typed `SCALED_REHEARSAL` base artifacts and scale transforms,
deterministic selections, canonical artifact/count/digest, and the same digest
in the owner deadline. Each schedule Job's configured active-process cap equals the dispatch
row and its retained Job binding. Its per-Job CPU and memory caps, enabled
flags, and limit-row digest also equal the binding and complete retained
configured-limit observation; the owner queries them before resume and at final
revalidation. After durable dispatch consumption the owner
samples one QPC start and derives immutable active and cleanup deadlines. Every broker
reservation embeds that timeline, dispatch digest, and limit-row digest.
Overlapped pipe connect/read and every process wait are cancelled only by that
active timer; no child or retry starts a fresh wall. `WALL_EXPIRED` requires the
same complete owner wall-trigger fact in process, broker, cleanup, and terminal
evidence. Afterward, no process or network route starts; retained-fact cleanup
must finish before the later deadline or emit no semantic envelope. Timeout, cancellation,
resume failure, assignment failure, unknown observed image, output overflow, or
process failure terminates the complete Job, proves active-process count zero,
and then performs only the operation-specific reconciliation still permitted by
the applicable deadline branch before releasing authority.
For output overflow, the supervisor's incremental counter records the exact
stream, selected calibrated cap and limit-row digest, first observed count above
the cap, and dispatch digest in `pontius-output-cap-fact-v1`. The same complete
fact appears in process completion and cleanup termination under source
`SUPERVISOR_OUTPUT_COUNTER`; worker output cannot report the condition.
Before either success or a classifiable semantic refusal, final revalidation
binds the immutable baseline plus the complete post-operation storage
observation whenever a repository was opened. If that physical accounting
cannot complete, cleanup cannot claim semantic authority and the host-failure
path applies.

Job notifications are diagnostic and may be incomplete. They never prove that
no unknown descendant executed. Publication authority comes from unavailable
operation routes, exact executable and source identities, closed argv, server
observations, and ref-state equations.

## Required disposable HTTPS mutation rehearsal

Before the first production mutation, a separately authorized private HTTPS
repository or server-side namespace must exercise the same held Git, remote
helper, adapter, broker, process owner, environment, configuration, grammar
engine, schedule engine, and state machine. A local transport, mock server, or
read-only query does not satisfy this gate.

The rehearsal loads a separately frozen policy-table instance. It has the same
engine and operation shapes as production, while authorization substitutes only
the exact stable-slot coordinates for endpoint, repository, ref prefix, public-
account, and credential-audience literals enumerated by the schema. The paired
tables have byte-identical operation sets, schedule sets, and argv-grammar
identities; every other unequal leaf matches one literal-delta row in both
directions. The owner-held selector also binds the exact campaign, disjoint
case-qualified ref namespaces, pure derived-input contract set, typed fixture
set, complete adoption-chain set, reviewed fault-harness/activation-parser and
server-event exporter/parser projection, and fresh pre-production and pre-
rehearsal capability observations. Every adoption fetch has exactly one linked
later adopter and builder-intent fixture; no other coordinate may consume it.
It contains no accepted utility authority, normal round preregistration, or
later result identity. The rehearsal credential and table structurally lack every
production capability literal. Evidence proves those literals are unreachable
and compares engine, schedule, and grammar identities plus the complete
authorized literal delta. The two pre-observations and paired table rows carry
one complete capability class and digest. A fresh controller-only observation
after each case uses new fact artifacts and must reproduce that class; a label
or replayed pre-case observation is insufficient.
If this separation cannot be enforced, production mutation stays blocked.

The rehearsal must cover at least:

1. atomic candidate/packet creation from absence and exact spent recovery;
2. atomic rejection, an unsupported-atomic response, and both fatal partial
   observations without attempting repair;
3. a transport-level lost acknowledgement after accepted pair creation, exact
   success reconciliation, and a following idempotent observation;
4. exact object-only adoption fetch and all crash points before offline tuple
   creation;
5. exact two-parent main fast-forward, exact-lease rejection, concurrent clean
   predecessor advance, and required reauthorization;
6. exact result and clean result-descendant lost-ack recovery;
7. protected-path mutation before and after `I`, including change then revert;
8. two task integrations in both orders, proving both packet ancestries remain;
9. two independent review-output creations and `WAITING_FOR_REVIEWS` for each
   proper subset;
10. wrong ref, remote, option, credential audience, prompt, operation selector,
    URL userinfo, URL password, percent escape, query, fragment, alternate
    scheme, and noncanonical host/port/path refusal before mutation;
11. success, rejection, timeout, cancellation, and lost acknowledgement with no
    credential-persistence executable, file, registry, or helper route;
12. empty-profile netrc poison, repository config poison, URL rewrite, proxy,
    redirect, cookie, header, hook, askpass, GCM, shell, and browser poison;
13. executable replacement, wrong same-byte path, reparse component, sidecar
    replacement, attempted write sharing, and equal-size mutation with restored
    timestamp while exact `FILE_SHARE_READ` holds;
14. quoting round trips for spaces, quotes, and terminal backslashes; and
15. assignment, resume, timeout, output-overflow, and broker-failure cleanup with
    Job active-zero before mutex release.
16. standalone builder and integration intent writes with one complete retained
    object-write plan, exact stored-object results, and matching physical
    carrier provenance; missing, extra, or cross-branch members refuse.
17. stable-ref and authorization-derived-ref substitution: no preregistration or
    selector contains a full attempt ref; changing its descriptor or external
    authorization digest changes the one derived ref and refuses every stale
    observation, ref-update, argv, refspec, or mutation value; every campaign
    integration case/task binding has exactly its intent/result descriptor pair.
18. source-bound identity and route-selector identity substitution, including a
    selector absent from the static projection and carried consistently through
    authorization, dispatch, runtime evidence, and final revalidation.
19. failure at every schedule boundary, proving the refusal's `ABORTED` or
    post-schedule `COMPLETE` transcript retains every started child, accepted
    reply, broker result, decisive transport outcome, reached object write, and
    cleanup storage carrier with no reordered, missing, or later row.

Every case records the typed operation, exact public inputs, process and source
projection identities, server namespace, immutable transport outcomes, ref
observations, authority envelope, and closed primitive results. Derived inputs
bind exact prior typed fields and their pure renderer; fixtures bind complete
selected rows. Each injected fault has a fresh dispatch-bound reservation and
harness activation artifact. Unsupported atomic and lost-acknowledgement server
faults additionally require the authenticated post-step server event to echo
the reservation nonce, rehearsal endpoint, repository, server-policy digest,
selected component-binding digest, procedure ID, and canonical ref-update-set
digest. Those values equal the reviewed deployment receipt and selector.
Process-only faults bind cleanup or runtime evidence.
Every case ends with its fresh capability wrapper. Raw process diagnostics and
their hashes are absent
from canonical receipts. Receipts contain no credential, authorization secret,
or user-profile content.

No rehearsal may import, compile, execute, or inspect a product candidate. The
rehearsal concerns only the reviewed authority utilities and disposable remote.

## Bootstrap and nonrecursive adoption

The authority-tool bundle governed by r002 cannot use this new route to freeze,
review, publish, or accept itself. Its design and later implementation rounds
bootstrap through the already adopted temporary-index Stage 2, direct Git, and
handoff packet rule 6. The adopted workflow identity is:

```text
sha256 = ab5202b170a5fd9c2cf1540aa198d4a82c742cb336134b0f9a8db944fd64f91a
```

The adopted design packet binds the frozen candidate tuple, six P paths, H
coverage, seven canonical terminal-r005 declarations, complete design-author attribution set,
convergence policy, two reviewer slots, and exact review inputs. The two typed
design-review publications and external-controller disposition precede a
self-excluding
`pontius-utility-bootstrap-design-authorization-publication-v1`. Only its
nested decision exact `AUTHORIZE_FREEZE_TOOLS_IMPLEMENTATION` permits the H
implementation plan, path-budget map, brief, and start object to freeze. Only
the remotely observed H implementation-start publication opens P source work.
The P candidate has the plan's exact P base and carries no H start field or H
ancestry; adopted `candidate.json` remains unchanged. The H
implementation packet descends from H start and adds a separate typed start link
binding the independent P tuple, which is inadmissible until that packet exists.
Every later bootstrap carrier repeats the start,
design-authorization, and plan identities. An unpublished, self-issued,
ambiguous, or different decision opens no Git source, process, credential, or
remote operation.

For the bootstrap integration, the P finalizer builds raw commit kind
`UTILITY_CEREMONIAL_INTEGRATION` from the reviewed candidate tree, canonical
ceremonial message and metadata, the freshly observed P predecessor as sole
parent, and the frozen Tier-C two-reviewer/finalizer/product coordinates, but
only after the implementation-controller disposition decides exact
`AUTHORIZE_CEREMONIAL_INTEGRATION`. The
three-event construction transcript binds the fresh predecessor query, then the
complete authorization and retained disposition object/count/digest, then the
ceremonial input. No input serialization or raw rendering precedes disposition
acceptance; build receipt and result carry the same transcript. The
typed build receipt independently renders, stores, reparses, and reproduces a
new result OID distinct from the Stage-2 candidate. The predecessor comes from
the self-free pre-push query and ordering transcript, never the later push-bound
query type. P is advanced to that OID by compare-and-swap and proven by the
separate post-push observation. Only afterward does H publish every self-free
receipt with raw kind `UTILITY_CEREMONIAL_INTEGRATION_RECORD`, then the complete
controller-disposition triple with raw kind
`UTILITY_BOOTSTRAP_DURABLE_DISPOSITION`; neither H commit is equated with the P
result commit. Both complete H raw inputs use the distinct messages and metadata
frozen in the authorizing implementation-controller disposition and reproduce
their independent stored OIDs.

The Stage 0b counter, review, atomic main-plus-anchor publication, disposition,
and build-authority schemas are prospective. They become authoritative only
after utility acceptance and a self-excluding activation publication for a
different series. They cannot authorize the r002-r005 bootstrap that creates
the utility. Every future Stage 0b calibration, registry, inventory, counter,
freeze anchor, review, disposition, and build-authority carrier repeats one
exact task; that task also supplies every `<task>` packet and ledger path.
Its publication observations use the same self-free core and external retained
wrapper as bootstrap H. The upstream authority pins service namespace,
producer, genesis, Ed25519 key, verifier, and create-only hash-chain policy;
receipt-supplied trust material is never authoritative.

Only after independent review, required tests, the exact expected-equals-
observed HTTPS rehearsal result set, controller authorization, the authorizing
implementation-controller disposition, ceremonial integration, durable
disposition, and the externally retained acceptance observation may a later
round use the new
builder, publisher, review-output producer, or integrator. No utility-produced
receipt can establish the review authority of the utility that produced it.
The reusable utility-acceptance object embeds the complete frozen bootstrap
chain: adopted brief, temporary-index candidate publication, rule-6 packet and
two review publications, plan tests, the exact HTTPS rehearsal result set with
every post-case capability wrapper, controller authorization, ceremonial
implementation-controller disposition with decision exact
`AUTHORIZE_CEREMONIAL_INTEGRATION`, ceremonial integration, fresh exact remote
observation, durable
disposition, and the externally retained acceptance observation. All
commits, refs, parents, manifests, artifacts, and repeated identities are
revalidated; no opaque disposition artifact can stand in for a missing gate.

## Design basis

Git credential selection and helper reset behavior are documented in
<https://git-scm.com/docs/gitcredentials>.

Git push lease and atomic semantics are documented in
<https://git-scm.com/docs/git-push>.

Git fetch options and refmap behavior are documented in
<https://git-scm.com/docs/git-fetch>.

Microsoft documents exact `lpApplicationName` behavior in the
[process and thread API reference][process-api].

Microsoft documents Job completion-port behavior in the
[Windows data types reference][winnt-api].

[process-api]: https://learn.microsoft.com/windows/win32/api/processthreadsapi/
[winnt-api]: https://learn.microsoft.com/windows/win32/api/winnt/
