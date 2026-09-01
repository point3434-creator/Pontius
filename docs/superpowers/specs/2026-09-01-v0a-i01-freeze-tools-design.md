# v0a-i01-freeze-tools r001 design

Status: DRAFT FOR DESIGN REVIEW. It authorizes no implementation or execution.

This design supplies the nonrecursive authority-tool layer needed to freeze the
R2-E1 transition candidate. The adopted temporary-index workflow freezes and
reviews this bundle first. Only accepted tool bytes may later receive a
candidate-specific dispatch.

## Frozen design inputs

This design is completed by three exact appendices:

- runtime boundary: SHA-256
  `126cadb5f8be5ae6f8fe6346d560deb323684df7cf240c8f5970a2b01d723ee0`,
  31,013 bytes;
- Git/GCM boundary: SHA-256
  `434f0cb6138e808dccdb597f780151a645689802bd402ac915e8669257cb4dee`,
  18,040 bytes; and
- direct CPython runtime closure: SHA-256
  `3390ab3d041d432f06754ca94aed348774c421de1c14553a25395c2cab112a3a`,
  413,522 bytes, 2,614 files, and 63,499,244 governed bytes.

The proposed workflow amendment v4 has SHA-256
`8c96bf04d983ec5fa77a24b6dfbfc9a5d495eac86512d1100a1e32385af678ca`.
It remains proposed during this design review and grants no execution by itself.

## Goals and observations

The bundle must make four facts independently observable:

1. the intended CPython and Git programs, configuration, and paths were the
   ones used;
2. candidate and packet objects equal the declared bytes without checkout or
   index normalization;
3. every local and remote authority transition is atomic or preserved as an
   explicit refusal state; and
4. a crash, timeout, or lost acknowledgement can be classified from durable
   state without rollback or deletion.

Each fact is observed through canonical receipts plus fresh object/ref
revalidation. A receipt never substitutes for the state it describes.

## Alternatives considered

The selected shape is one shared library, three narrow Python entry points, and
one PowerShell runtime launcher. The library owns validation, canonical
encoding, Git process control, identity handles, object parsing, and state
classification. Each entry point exposes one authority transition only.

A single Python program with `build`, `publish`, and `integrate` modes would be
shorter. It also recreates the v2 failure shape: one role gate separates an
offline builder from network and main-ref authority. A routing defect would
cross the largest boundary in the system.

Three fully standalone programs would make role separation obvious. It would
duplicate the most delicate code: canonical Git invocation, timeout cleanup,
identity comparison, ref classification, and object verification. Reviewers
would have to prove that three copies stay equivalent.

The selected middle shape keeps the policy entry points small while giving the
mechanical invariants one implementation. The launcher supplies the runtime
hold that Python cannot establish before its own startup.

## Component boundaries

### Runtime launcher

`tools/handoff_freeze_runtime_launcher.ps1` is the only supported way to start
an accepted Python role. It accepts exact absolute paths and SHA-256 values for
the runtime closure, role entry point, shared library, and one-use dispatch.

The launcher parses the externally frozen runtime inventory, independently
enumerates the direct CPython base population, opens every governed file with
read sharing only, hashes and identifies each open file, and retains every
handle through child exit. It creates a unique empty temporary and pycache root,
constructs the complete child environment from an allowlist, and starts the
direct base `python.exe` with the fixed isolated argv. It bounds stdout, stderr,
wall time, and descendant lifetime. It forwards bytes only after the child and
its process tree have terminated.

PowerShell, .NET, the controller, Windows kernel/loader/NTFS semantics, and
allowlisted System32 paths form the bootstrap trust boundary. This design does
not recursively attempt to prove that platform with the Python it launches.

### Shared library

`tools/handoff_freeze_common.py` contains mechanism, never role selection. It
provides:

- canonical JSON and digest validation;
- exact path, file, directory, and Git-object identity readers;
- retained Windows handles and FileIdInfo comparisons;
- direct `CreateProcessW` plus Job ownership for Git children;
- exact Git environment, argument, output, timeout, and reconciliation rules;
- repository/config/object/ref validation; and
- typed refusal values with stable machine-readable codes.

The launcher pins and holds the library. An entry point loads it from that
absolute path and verifies the expected digest before calling a public API.
The library cannot infer a missing dispatch value from environment, repository
configuration, HEAD, a tracking ref, a checkout, or a working file.

### Offline builder

`tools/handoff_freeze_builder.py` accepts only a canonical build dispatch. It
has no network verb or credential route. It validates the complete source
population, creates raw blobs, rebuilds trees, creates deterministic commits,
and reparses every object. It creates the local intent, candidate, and packet
anchor refs together from absence with one `update-ref --stdin` transaction.

Its terminal states are exact success, exact idempotent recovery, or preserved
refusal. Unreachable objects are permitted residue. No path deletes them.

### Remote-pair publisher

`tools/handoff_freeze_publisher.py` cannot build objects or update main. It
validates the accepted local graph, observes the exact remote candidate/packet
pair, and either accepts exact `EE`, attempts one atomic create-only push from
`AA`, or refuses. It reobserves after every push return, including timeout and
nonzero exit.

### Main integrator

`tools/handoff_freeze_integrator.py` cannot construct or publish a candidate
pair. It validates exact remote-pair authority, constructs the one permitted
receipt child, and advances only the pinned main ref under an exact lease. A
permitted unrelated main descendant must be a single-parent chain preserving
the entire current-task subtree. Any current-task mutation refuses.

## Authority and data flow

```text
adopted temporary-index Stage 2
  -> frozen utility candidate + manifest
  -> two independent Tier-C reviews
  -> ordinary rule-6 review packet commits
  -> controller-authorized utility-review projection

runtime closure + accepted tools + exact candidate dispatch
  -> runtime launcher
  -> offline builder
  -> atomic pair publisher
  -> main integrator
  -> COLD_INPUT_READY
```

The utility-review round never runs the new tools to establish their own
authority. The later candidate packet contains only structured CLEAN review
provenance, not utility findings or narratives.

The C candidate's `handoff.md` is generated from a controller-authorized
canonical cold-input spec after candidate identity exists. Opaque handoff prose
is never accepted as semantic authority.

## Process and Git boundary

Every Git command starts the pinned inner Git executable with a non-null
`lpApplicationName`, fixed Windows quoting, fixed current directory, explicit
repository `-C`, and an exact newly constructed environment. The positive HTTPS
route is the pinned `git-remote-https.exe`. The only credential route is the
pinned Git shell executing an absolute GCM path. Held handles deny write/delete
replacement through final reconciliation.

The root Git process is created suspended, assigned to a kill-on-close,
no-breakaway Job, then resumed. Pre-assignment failure terminates the root;
post-assignment failure or timeout terminates the Job and waits for active zero.
Job notifications are diagnostic and cannot prove a complete descendant census.
The trusted pinned Git/GCM bytes may launch only their documented route; this is
an environmental-rerouting boundary, not malicious-child containment.

## State and failure model

Every durable tuple uses the same classifications:

- `ABSENT`: every governed member is absent;
- `EXACT`: every member and complete graph is exact;
- `PARTIAL`: only a proper subset exists;
- `DIFFERENT`: a syntactically valid member has another identity;
- `UNKNOWN`: state cannot be read or classified exactly.

Only `ABSENT` may attempt a create operation. `EXACT` may close a lost
acknowledgement after complete revalidation. Every other state preserves and
refuses. `UNKNOWN` takes precedence over conclusions derived from incomplete
members.

The tools have no rollback transition. Cleanup owns only ephemeral processes,
pipes, temporary directories, and handles created by that invocation. Durable
objects and refs are monotonic residue or authority.

## Testing strategy

Tests are written before each public behavior and run under CPython 3.11 first.
They invoke real entry points against disposable SHA-1 repositories and bare
remotes. Hand-derived bytes and OIDs form expectations; production encoders do
not compute the expected side of their own assertions.

The test matrix covers:

- canonical and malformed dispatches, manifests, objects, and outputs;
- runtime drift, same-size mutation, reparse paths, path replacement, and
  launcher-held sharing denial;
- exact Windows argument/environment transmission and inherited-handle limits;
- hook, filter, attribute, index, worktree, config, URL, helper, proxy, askpass,
  extension, and PATH rerouting attempts;
- atomic local ref creation and every partial/different/unknown tuple;
- atomic remote pair creation, lease conflict, unsupported atomic push,
  timeout, nonzero exit, retry, and lost acknowledgement;
- main descendants, protected-subtree mutation, main lease conflict, and
  integration lost acknowledgement; and
- root/descendant process failure, timeout, Job termination, and active-zero.

The local transport rehearsal is available only under a separately keyed
rehearsal dispatch and refuses all live task/ref namespaces. The live dispatch
accepts only the literal private HTTPS endpoint.

## Barriers and deliberate exclusions

The accepted bundle cannot run until this design, implementation, tests, and
two cold reviews complete under the existing workflow. Any role expansion,
runtime/Git servicing, new import, new child image, new transport, deletion, or
review-output publication route requires a new round.

This design does not materialize candidate files for review, publish reviewer
outputs, edit task ledgers, execute the C candidate, run its RED authority,
mutate retained evidence, dispose refs, or make a production acceptance claim.
