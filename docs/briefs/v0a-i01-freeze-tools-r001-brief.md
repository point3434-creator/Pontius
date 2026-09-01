# v0a-i01-freeze-tools r001 brief

Tier: C

Round kind: NEW-SURFACE

Base: `d1ed3cbda6107d61ea8e77133871720af04970cd` on
`codex/v0a-i01-freeze-tools`, worktree
`D:\Pontius-worktrees\codex-v0a-i01-freeze-tools-v1`.

Finalizer: `codex/finalizer` for this authority-tool checkpoint. This does not
change the finalizer of the C implementation checkpoint.

## Scope

Build one reusable, reviewed authority-tool bundle:

- a PowerShell runtime launcher that verifies and holds the declared direct
  CPython runtime while a child utility runs;
- three standalone Python entry points for offline raw-object construction,
  atomic remote-pair publication, and remote-main integration;
- one shared Python library loaded only from a pinned absolute path; and
- focused disposable-repository and runtime-boundary tests.

No candidate, Model, sensitive case, analyzer, transition harness, controller,
or evidence payload may be imported or executed. The bundle may read candidate
bytes only after its own round is accepted and a separate exact dispatch is
authorized.

## Acceptance criteria

1. The launcher starts the direct CPython 3.11.15 base executable under the
   exact isolated argv and environment. Before launch it independently
   reproduces the full runtime inventory, opens every governed file without
   write/delete sharing, and holds the population through child exit.
2. The builder has no network route and never uses a checkout, the real index,
   attributes, filters, or `git add`. It constructs and reparses exact blobs,
   trees, commits, manifests, packet sources, inventories, and local intent refs.
3. The publisher can change only the exact candidate and packet ref pair. It
   classifies one fresh strict observation, uses one atomic create-only push,
   and treats partial, different, malformed, unavailable, and ambiguous state
   as preserved refusal.
4. The integrator can add only the exact remote receipt and advance only the
   pinned main ref under an exact lease. It preserves the complete current-task
   subtree and accepts unrelated single-parent main descendants only under the
   preregistered rule.
5. Every Git child uses direct pinned Git-for-Windows routes, held executable
   identities, a newly constructed environment, a literal URL, explicit refs,
   a kill-on-close no-breakaway Job, bounded output, and bounded wall time.
6. Lost acknowledgements reconcile from fresh local or remote state. No failure
   path deletes an object, ref, packet, report, or other authority.
7. The utility-review handoff uses the adopted temporary-index Stage 2 and
   packet rule 6 only. Two independent Tier-C reviews bind the frozen utility
   commit and manifest and each state defect and design verdicts.
8. Disposable tests and rehearsals prove success, refusal, timeout, crash,
   rerouting, runtime drift, same-size mutation, partial state, and recovery
   through the real process and Git boundaries.

## Seam inventory

- controller and PowerShell/.NET launcher;
- launcher and direct CPython runtime;
- Python and Win32 file/process/Job APIs;
- Python and pinned Git-for-Windows plumbing;
- Git object database and transactional local refs;
- Git HTTPS transport, shell, GCM, and the remote ref pair;
- utility review provenance and the later candidate cold-input packet.

## Size budget

Target at most 3,500 nonblank source lines across the launcher, shared library,
and three entry points, plus at most 2,500 focused test lines. If the shared
library exceeds 1,800 nonblank lines or a role entry point exceeds 500, stop for
a design checkpoint before adding code.

## Forbidden claims

This round does not prove the C candidate, execute any C artifact, publish its
candidate or packet refs, dispatch its reviewers, run its RED authority, mutate
the evidence repository, or accept production code. It prevents configuration,
path, interpreter, and file-identity drift under a trusted local controller and
Windows platform. It does not defend against a hostile controller, kernel,
loader, local administrator, already patched process image, DNS/TLS platform,
or Windows Credential Manager.

## Test plan

Each public behavior starts with a failing test. Tests use disposable SHA-1
repositories and bare remotes, literal hand-derived object identities, real Git
plumbing, and fault schedules at the process boundary. Network publication is
rehearsed against a local transport mode that cannot be selected by a live
dispatch. The final rehearsal uses the exact installed Git/GCM route for a
read-only remote observation before any separately authorized live mutation.
