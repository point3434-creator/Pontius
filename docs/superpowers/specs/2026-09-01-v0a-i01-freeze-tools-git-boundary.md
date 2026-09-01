# V8 Git/GCM execution-boundary replacement

Status: ISOLATED DRAFT INSERT. This file authorizes no execution and does not
amend a plan, schema, workflow, or candidate.

## Replacement scope

This insert replaces only the Git/GCM process boundary. The surrounding v8
state machine, object equations, ref transitions, timeout reconciliation, and
`COLD_INPUT_READY` boundary remain separately controlled.

The replacement prevents:

- parent-environment or Git-config injection;
- URL, proxy, redirect, protocol, askpass, and helper rerouting;
- `CreateProcessW` executable-name ambiguity;
- command-name, extension, `PATH`, and `PATHEXT` substitution;
- reparse-path substitution; and
- executable or launch-input replacement after validation.

The replacement trusts the pinned Git, HTTPS helper, Git shell, and GCM bytes
as programs. It also trusts Windows, the installed DLL and managed-assembly
closure, DNS, the selected TLS platform, and OS credential services. It does
not claim malicious-child containment, a complete process or DLL census, or
proof that no process outside the positive route executed.

Job notifications are diagnostic. They are not publication authority and are
not evidence of a complete descendant census.

## Exact installed identities

The direct Git executable is:

```text
path = C:\Program Files\Git\mingw64\bin\git.exe
byte_count = 4383048
sha256 = 1a0043555d254618f2d56c936c3d9a1fbfb878bc878416a133c346bc7835eda9
```

The HTTPS remote helper is:

```text
path = C:\Program Files\Git\mingw64\libexec\git-core\git-remote-https.exe
byte_count = 2529112
sha256 = 45e7df11f1b5ee4348a6380e0c66e8d41193d94d43478845f98db9e9942ed151
```

The Git shell is:

```text
path = C:\Program Files\Git\usr\bin\sh.exe
byte_count = 2456832
sha256 = acf4ecb52e601f7b4a37db51b07650b5d0315eafd010590e98079fa026da4b7b
```

Git Credential Manager is:

```text
path = C:\Program Files\Git\mingw64\bin\git-credential-manager.exe
byte_count = 132920
sha256 = 593dfd29885443e70255cdf4038988f831d939218aea950e32f2a356ac3b00f5
```

Two known launch-affecting sidecars are also fixed and held:

```text
path = C:\Program Files\Git\usr\bin\msys-2.0.dll
byte_count = 3368543
sha256 = 2ea49553e4c03055dcf1c4a2bef54668081a07663fba283f4b34cf70f2157191

path = C:\Program Files\Git\mingw64\bin\git-credential-manager.exe.config
byte_count = 2890
sha256 = a64e209b9476be9acb9e4a3b7813e0ba48321ae2da1b675cd584f5319dc0c66f
```

The following same-byte or alternative routes are explicitly not accepted:

```text
C:\Program Files\Git\cmd\git.exe
C:\Program Files\Git\mingw64\libexec\git-core\git.exe
C:\Program Files\Git\mingw64\libexec\git-core\git-remote-http.exe
C:\Program Files\Git\usr\bin\bash.exe
```

`git-remote-http.exe` currently has the same size and SHA-256 as the allowed
HTTPS helper. `bash.exe` currently has the same size and SHA-256 as the allowed
`sh.exe`. Path and file identity therefore remain mandatory even when bytes
match.

`C:\Windows\System32\cmd.exe` is not in the positive route. If a disposable
rehearsal proves that GCM requires `COMSPEC`, v8 must be reissued with this
additional fixed identity before execution:

```text
path = C:\Windows\System32\cmd.exe
byte_count = 344064
sha256 = 8dd1ebb0b969370c70a5ee7f7ee347949aa7046aa5e1a33fcd7b1e9415b21fc3
```

No runtime observation may widen this list in place.

## Exact positive route

Every root Git process starts the inner Git executable directly. The `cmd`
wrapper is never started.

For HTTPS operations, the pinned Git program may select only the exact
`git-remote-https.exe` through the fixed `GIT_EXEC_PATH` directory.

The credential-helper list is cleared and replaced by this exact logical
value:

```text
!exec 'C:/Program Files/Git/mingw64/bin/git-credential-manager.exe'
```

The complete corresponding config pair is:

```text
credential.helper=
credential.helper=!exec 'C:/Program Files/Git/mingw64/bin/git-credential-manager.exe'
```

Git appends the helper operation, which is `get`, `store`, or `erase`. The
leading `!` necessarily sends the fixed snippet through Git's shell. The
`exec` builtin and single-quoted absolute operand remove the former
`git credential-manager` command-name lookup and its extra Git dispatch.

The pinned Git program's installation relocation is trusted to select:

```text
C:\Program Files\Git\usr\bin\sh.exe
```

The first read-only remote query must corroborate that path before a push is
eligible. `GCM_INTERACTIVE=Never` and `GCM_GUI_PROMPT=0` are mandatory. A
selector, browser, askpass program, batch file, PowerShell process, repo-local
executable, or other observed child terminates the Job and refuses the
operation.

This insert does not make Windows Credential Manager immutable. The trusted
GCM program may implement the documented `get`, `store`, and `erase` helper
operations. If credential-store mutation is forbidden, a separately reviewed
credential-preauthorization design must replace this route.

## Exact child environment

The owner constructs a brand-new case-insensitive-key-unique UTF-16 environment
block. It inherits no parent entry. `TEMP` and `TMP` are the only per-run
values; both name the same unique verified ordinary directory under:

```text
D:\Pontius\tmp\handoff-freeze-<32 lowercase hex>
```

The complete public environment is:

```text
APPDATA=C:\Users\point\AppData\Roaming
GCM_CREDENTIAL_STORE=wincredman
GCM_GUI_PROMPT=0
GCM_INTERACTIVE=Never
GIT_ATTR_NOSYSTEM=1
GIT_CONFIG_GLOBAL=NUL
GIT_CONFIG_NOSYSTEM=1
GIT_CONFIG_SYSTEM=NUL
GIT_EXEC_PATH=C:\Program Files\Git\mingw64\libexec\git-core
GIT_LITERAL_PATHSPECS=1
GIT_NO_REPLACE_OBJECTS=1
GIT_OPTIONAL_LOCKS=0
GIT_TERMINAL_PROMPT=0
HOMEDRIVE=C:
HOMEPATH=\Users\point
LANG=C
LC_ALL=C
LOCALAPPDATA=C:\Users\point\AppData\Local
PATH=C:\Program Files\Git\mingw64\bin;C:\Windows\System32
PATHEXT=.EXE
PROGRAMDATA=C:\ProgramData
PROGRAMFILES=C:\Program Files
PROGRAMFILES(X86)=C:\Program Files (x86)
SYSTEMROOT=C:\Windows
USERDOMAIN=JEFFPC
USERNAME=point
USERPROFILE=C:\Users\point
WINDIR=C:\Windows
```

`TEMP` and `TMP` are added to that set with the equal per-run value. Environment
keys sort by ordinal case-insensitive key and are emitted once with a final
double NUL.

In particular, the environment contains no `COMSPEC`, `PONTIUS_GIT`, parent
`HOME`, XDG variable, proxy, TLS override, askpass, SSH route, trace,
`GIT_CONFIG_COUNT`, `GIT_CONFIG_KEY_*`, `GIT_CONFIG_VALUE_*`, namespace,
alternate-object, replacement, shallow, graft, or Python-routing variable.

The Git `cmd` directory and Git `usr\bin` directory are absent from `PATH`.
The shell and GCM are reached only by the fixed routes above.

## Exact common Git argv prefix

Every Git invocation has this logical prefix, in this exact order:

```text
C:\Program Files\Git\mingw64\bin\git.exe
-C
<verified absolute repository path>
-c
core.hooksPath=NUL
-c
core.fsmonitor=false
-c
maintenance.auto=false
-c
gc.auto=0
-c
fetch.writeCommitGraph=false
-c
commit.gpgSign=false
-c
tag.gpgSign=false
-c
credential.helper=
-c
credential.helper=!exec 'C:/Program Files/Git/mingw64/bin/git-credential-manager.exe'
-c
credential.interactive=never
-c
credential.useHttpPath=false
-c
protocol.allow=never
-c
protocol.https.allow=always
-c
protocol.version=2
-c
http.proxy=
-c
http.followRedirects=false
-c
http.sslVerify=true
-c
http.sslBackend=schannel
-c
http.schannelUseSSLCAInfo=false
```

No additional global option or `-c` pair is accepted. Each invocation then
uses exactly one operation suffix authorized by the controlling plan and
schema.

The repository-local config key/value multimap remains exactly:

```text
core.repositoryformatversion=0
core.filemode=false
core.bare=false
core.logallrefupdates=true
core.symlinks=false
core.ignorecase=true
core.autocrlf=false
remote.origin.url=https://github.com/point3434-creator/Pontius-handoffs.git
remote.origin.fetch=+refs/heads/*:refs/remotes/origin/*
```

There is no `config.worktree`, include, URL rewrite, helper, proxy, askpass,
alternate, graft, shallow file, replace ref, namespace, or unknown repository
extension. Network operations use only the literal URL and explicit source and
destination identities.

## Exact network suffixes

The pair query suffix is:

```text
ls-remote
--refs
https://github.com/point3434-creator/Pontius-handoffs.git
refs/heads/review/v0a-i01-c-authority/r001
refs/heads/handoff-freeze-packet/v0a-i01-c-authority/r001
```

The main query suffix is:

```text
ls-remote
--refs
https://github.com/point3434-creator/Pontius-handoffs.git
refs/heads/main
```

The remote-pair adoption fetch suffix is:

```text
fetch
--no-write-fetch-head
--no-tags
--no-recurse-submodules
--no-auto-maintenance
https://github.com/point3434-creator/Pontius-handoffs.git
refs/heads/review/v0a-i01-c-authority/r001
refs/heads/handoff-freeze-packet/v0a-i01-c-authority/r001
```

A main-descendant fetch substitutes the exact freshly queried 40-hex main OID
for the two source refs. It never fetches `main` by name as a substitute for
the observed object. It performs a fresh main query after graph validation.

The atomic pair push suffix remains:

```text
push
--atomic
--porcelain
--no-verify
--no-follow-tags
--recurse-submodules=no
--force-with-lease=refs/heads/review/v0a-i01-c-authority/r001:
--force-with-lease=refs/heads/handoff-freeze-packet/v0a-i01-c-authority/r001:
https://github.com/point3434-creator/Pontius-handoffs.git
<CANDIDATE>:refs/heads/review/v0a-i01-c-authority/r001
<FREEZE_PACKET>:refs/heads/handoff-freeze-packet/v0a-i01-c-authority/r001
```

The main push suffix remains:

```text
push
--porcelain
--no-verify
--no-follow-tags
--recurse-submodules=no
--force-with-lease=refs/heads/main:<BASE>
https://github.com/point3434-creator/Pontius-handoffs.git
<INTEGRATED_PACKET>:refs/heads/main
```

The owner rejects any suffix containing an unenumerated option, endpoint,
remote name, refspec, destination ref, upload-pack override, submodule route,
tag route, `FETCH_HEAD` write, or automatic maintenance route.

## Held file identities

Before the first reachable child starts, the owner opens every positive-route
file and required sidecar using `CreateFileW` with read and attribute access,
`OPEN_EXISTING`, and `FILE_SHARE_READ` only. The file itself and every path
component must be ordinary and non-reparse.

For each retained handle, the owner:

1. obtains the final normalized path with `GetFinalPathNameByHandleW`;
2. obtains volume and 128-bit file identity with `FileIdInfo`;
3. obtains exact byte count;
4. hashes the complete bytes through that same handle;
5. compares path, byte count, and SHA-256 to the fixed values; and
6. keeps the handle open through final reconciliation and Job active-zero.

The first open establishes the per-run `FileIdInfo`, which the preparation
receipt records. Before each child, the owner reopens every route reachable by
that operation and requires the same final path and `FileIdInfo`. The retained
handle prevents a write, delete, rename, or replacement from succeeding during
the operation.

Ancestor directory handles may allow read and write sharing but omit delete
sharing so the verified path chain cannot be renamed. They remain held for the
same interval. Failure to acquire or retain any handle refuses before process
creation.

The offline builder need only hold the direct Git route. A publisher or
integrator holds Git, HTTPS helper, shell, GCM, and the two fixed sidecars from
before its first remote query through the final lost-ack reconciliation.

## Exact `CreateProcessW` boundary

The process owner calls `CreateProcessW` with:

```text
lpApplicationName = C:\Program Files\Git\mingw64\bin\git.exe
lpCommandLine = writable UTF-16 encoding of the exact logical argv
lpCurrentDirectory = verified absolute repository path
bInheritHandles = TRUE
dwCreationFlags = CREATE_SUSPENDED | CREATE_UNICODE_ENVIRONMENT |
                  CREATE_NO_WINDOW | EXTENDED_STARTUPINFO_PRESENT
```

`lpApplicationName` is never `NULL`. `argv[0]` repeats the exact application
path. One frozen Windows quoting routine encodes every logical argument. It
rejects NUL and control characters, and the disposable rehearsal proves
round-trip handling for spaces, quotes, and terminal backslashes.

`STARTUPINFOEXW` uses `PROC_THREAD_ATTRIBUTE_HANDLE_LIST`. Only the exact child
stdin, stdout, and stderr pipe handles are inheritable. Every other parent
handle, including identity, mutex, Job, config, and authority handles, is
non-inheritable.

The owner creates the root suspended, compares its queried image path to the
held Git identity, assigns it to the kill-on-close and no-breakaway Job, and
only then resumes the primary thread.

Failure before successful Job assignment calls `TerminateProcess`, confirms
exit, and closes both returned handles. Failure after assignment, including
resume failure or timeout, calls `TerminateJobObject` and confirms the queried
active-process count is zero before releasing the authority mutex.

Each process operation retains the controlling plan's exact 60000 ms wall.
Reconciliation remains operation-specific and runs under the same mutex and
held route identities.

## Job diagnostic and non-claims

The owner associates the completion port while the Job is empty. For each
delivered `JOB_OBJECT_MSG_NEW_PROCESS`, it immediately attempts to open and
retain the process, obtains its final image path, and compares that path and
file identity to the positive route.

An observed unknown image, inaccessible delivered PID, duplicate live PID, or
identity mismatch terminates the Job and refuses. The owner bounds the total
number of delivered process events and waits for a direct
`QueryInformationJobObject` active-process count of zero.

The diagnostic record has an explicit `complete` boolean. It is false after a
missing, delayed, ambiguous, or PID-reuse condition. It is never promoted to
true merely because active process count reached zero.

Windows does not guarantee complete Job completion-port notification delivery,
and a PID may exit or be reused before it is opened. Therefore:

- the diagnostic is not a complete descendant census;
- silence is not evidence that no child ran;
- publication never depends on a completeness claim; and
- exact routes and held file identities remain the authority control.

`DEBUG_PROCESS` is deliberately absent. It would be required if the threat
model changed to "no unallowlisted descendant may begin executing." That
stronger boundary requires a separately reviewed debugger event loop,
exception-continuation rules, image-handle validation before
`ContinueDebugEvent`, and new timeout and cleanup proofs.

This insert also makes no loaded-DLL, managed-assembly, OS-broker, or service
process census claim.

## Required disposable rehearsal additions

Before any real ref or remote mutation, the existing rehearsal adds all of the
following cases:

1. A `C:\Program.exe` marker and a command line containing `Program Files`
   prove that non-NULL exact `lpApplicationName` starts only inner Git.
2. A poisoned parent `PATH`, `PATHEXT`, `COMSPEC`, `GIT_EXEC_PATH`, askpass,
   proxy, TLS, trace, config-count, include, and URL rewrite is absent or
   refused.
3. Repo-local helpers and `.com`, `.bat`, and `.cmd` siblings cannot replace
   the fixed GCM or HTTPS-helper route.
4. Same-hash wrong-path `bash.exe` and `git-remote-http.exe` are refused by
   path and `FileIdInfo`.
5. A pre-hold executable, GCM-config, or MSYS-sidecar mismatch refuses. A
   post-hold write, rename, delete, or replacement fails with a sharing error.
6. A reparse point in any route component, a hard-link alias at the wrong
   path, and a changed ancestor identity refuse.
7. Logical argv containing spaces, quotes, and terminal backslashes round-trip
   exactly through the writable `CreateProcessW` command buffer.
8. An unexpected inherited handle is absent; only the three declared pipe
   handles reach the child.
9. Assignment failure, resume failure, root exit with a live helper, timeout,
   Job termination, and direct active-process-zero proof all preserve the
   existing cleanup contract.
10. Missing, delayed, duplicate, and reordered Job messages plus PID reuse
    never produce a false complete diagnostic or publication fact.
11. Missing credentials, a selector, browser, prompt, or other observed child
    refuses. No push follows a failed read-only route query.
12. An HTTP redirect refuses under `http.followRedirects=false`; proxy and
    askpass poison never reroute the literal HTTPS endpoint.
13. The offline builder starts no HTTPS helper, shell, or GCM process.
14. Query, fetch, and push use only the positive route, and a read-only exact
    `ls-remote` exercises it before the first push.
15. Held identities remain unchanged through nonzero and timeout lost-ack
    reconciliation.
16. GCM `get`, `store`, and `erase` behavior is recorded without exposing a
    credential. If its side effects exceed the accepted threat model, the
    round stops for a separate credential-preauthorization design.

No rehearsal may import, compile, run, or inspect any candidate artifact.

## Design basis

- Git documents that transformed credential-helper commands execute through
  the shell, including absolute-path and leading-`!` forms:
  <https://git-scm.com/docs/gitcredentials.html>.
- Microsoft recommends non-NULL `lpApplicationName` to prevent spaced-path
  executable ambiguity:
  <https://learn.microsoft.com/windows/win32/api/processthreadsapi/nf-processthreadsapi-createprocessw>.
- Microsoft documents that Job completion-port notifications are not
  guaranteed and that process-ID races require retained handles:
  <https://learn.microsoft.com/windows/win32/api/winnt/ns-winnt-jobobject_associate_completion_port>.
- Microsoft documents that `DEBUG_PROCESS` covers descendants and that create
  debug events provide process, thread, and image-file handles:
  <https://learn.microsoft.com/windows/win32/procthread/process-creation-flags>
  and
  <https://learn.microsoft.com/windows/win32/api/debugapi/nf-debugapi-waitfordebugevent>.
