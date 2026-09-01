# R2-E1 transition harness v8 runtime-identity insert

Status: ISOLATED DRAFT FOR STATIC REVIEW. This file changes no v8 authority by
itself and authorizes no utility, Git, network, candidate, harness, Model, or
test execution. It is intended to replace the launcher-only CPython identity
in the v8 plan and schemas after review.

## Purpose and proportional boundary

The three Python utilities run under one exact direct CPython installation,
not through the `D:\Pontius-tools\py311` virtual-environment launcher. A fourth
reviewed utility, `runtime-launcher.ps1`, verifies and locks the complete
declared CPython file population before it starts a Python child. It retains
those locks until the child and every descendant have exited.

This design deliberately uses a full 63,499,244-byte runtime inventory instead
of a transitive-import prediction. The extra hashing and approximately 2,614
open file handles are proportionate for short governance utilities and remove
the need to guess which startup, error-path, lazy, extension, or private-DLL
dependency CPython may use.

The protected claim is ordinary runtime drift and file-system replacement
races that obey Windows file-share and handle semantics. The Windows,
PowerShell, and .NET coordinator is the trusted bootstrap boundary supplied by
the adopted workflow Stage 2 and packet rule 6. This insert does not attempt to
make CPython prove itself before that trusted controller has verified and
locked it.

## Fixed runtime authority

The complete runtime manifest is the exact file:

```text
D:\Pontius\codex-python-runtime-closure-v1.json
```

Its immutable identity is:

```text
sha256 = 3390ab3d041d432f06754ca94aed348774c421de1c14553a25395c2cab112a3a
byte_count = 413522
schema = pontius-python-runtime-closure-v1
inventory.file_count = 2614
inventory.total_bytes = 63499244
```

The direct executable is:

```text
C:\Users\point\AppData\Roaming\uv\python\cpython-3.11.15-windows-x86_64-none\python.exe
```

Its inventory row fixes byte count `91648` and SHA-256
`6765c6b1685c86877fabe14d82240f3fab2913a617a85e8d09e61dc40798013b`.
`sys.executable` and `sys._base_executable` must both equal that literal path.
All four prefix values must equal its parent directory.

The manifest's population is closed over:

- every ordinary file directly under the base root;
- every ordinary file recursively under `Lib`;
- every ordinary file recursively under `DLLs`; and
- the exact six ordinary, non-reparse root directories `DLLs`, `Lib`,
  `Scripts`, `include`, `libs`, and `tcl`.

The contents below `Scripts`, `include`, `libs`, and `tcl` are outside the
runtime inventory. They cannot become Python search inputs. Any child path,
module origin, native image, or runtime data access that reaches them refuses.
An extra or missing root file, listed directory, `Lib` file, or `DLLs` file
refuses. A reparse point, nonordinary object, case-fold duplicate, invalid
Windows path, or file/directory prefix collision refuses.

The six `forbidden_startup_paths` in the manifest must remain absent. They
cover `python311.zip`, both `_pth` spellings, `pybuilddir.txt`, the base-root
`pyvenv.cfg`, and the parent-directory `pyvenv.cfg`. Their governing directory
identities are validated and retained by the launcher. A newly present path is
an exact-population conflict, never an input to normalize or ignore.

The runtime manifest does not contain its own digest and does not name the v8
plan, schemas, utilities, receipts, candidate, or packet. Its complete bytes
and SHA-256 are fixed before utility authoring. Utility candidates do not embed
the later plan or schema digests. The content-dependency order is:

```text
runtime manifest -> four utility candidates -> final v8 plan/schemas
-> eight utility reviews -> packet-source manifest -> builder authorization
-> exact local builder graph -> publisher authorization -> exact remote pair
-> integrator authorization -> integrated objects and main observation
```

The final plan and schemas pin the runtime manifest, all four utility candidate
paths, SHA-256 values, byte counts, and the eight required review slots. They do
not pin a review's eventual content identity. Each review binds the final plan,
schemas, and its utility. The later source manifest binds every utility and
review. The builder authorization can then bind those completed inputs.
Publisher authorization is issued only after the exact local builder graph
exists. Integrator authorization is issued only after the exact remote pair and
deterministic publication-receipt inputs exist. Each authorization binds its
complete predecessor state. No earlier object binds a later object's content
identity.

This order is acyclic. Changing any runtime-manifest byte requires a new plan,
new utility bytes, and new static reviews before another live attempt.

## Trusted computing base and nonclaims

The runtime manifest fixes Windows `10.0.26200.0`, UBR `9168`, machine `AMD64`,
and 64-bit pointers. The controller preflight requires PowerShell Core `7.6.4`,
.NET `10.0.10`, a 64-bit process, and the manifest's Windows facts. These are
trusted-controller constraints, not a claim that PowerShell or .NET verified
their own executable bytes.

The trusted computing base is exactly:

- the controller and adopted Stage 2 / packet-rule-6 dispatch;
- the Windows kernel, loader, process, job, pipe, file-share, and NTFS handle
  semantics on the fixed Windows build;
- the PowerShell and .NET process running the reviewed launcher; and
- loaded images whose handle-resolved final path is beneath the literal,
  ordinary `C:\Windows\System32` root.

Every loaded child-process image outside System32 must be an exact runtime-
inventory file, including CPython DLLs, `.pyd` files, VCRUNTIME copies,
OpenSSL, libffi, or any other private dependency. The launcher and child reject
an unlisted non-System32 image.

The design makes no claim against a hostile or compromised controller, kernel,
loader, local administrator, System32 installation, debugger, in-memory patch,
or mechanism that bypasses ordinary Windows sharing semantics. It does not
claim System32 byte identity, actor identity, absence of a historical race, or
portability across Python or Windows servicing. A changed Windows build or
runtime inventory is a new reviewed closure.

## Fourth reviewed utility

The utility bundle gains one PowerShell source:

```text
source: runtime-launcher.ps1
packet path: checks/runtime-launcher.ps1
utility role: runtime-launcher
utility_sha256 key: runtime_launcher
```

The launcher receives the same two independent, utility-only static reviews as
each Python utility. Their packet paths are:

```text
checks/runtime-launcher-static-verification-01.json
checks/runtime-launcher-static-verification-02.json
```

The launcher may read the runtime manifest, the selected utility source, its
fixed launch inputs, and Windows process/runtime state. It never reads a
candidate artifact, constructs a Git object, opens the H repository as Git,
queries a remote, evaluates a verdict, or runs a candidate, harness, Model,
controller, analyzer, or test. Its only mutations are the unique temporary
directory and the child process/job/pipe objects required by this contract.

The trusted Stage 2 controller receives one exact authorization-source path,
SHA-256, and byte count from the nonrecursive workflow authorization. It opens
that source and every source row named within it using `FileShare.Read`, checks
each externally pinned path, byte count, and SHA-256 from the held handle, and
keeps at least the authorization and launcher handles through launcher exit.
This bootstrap prevents ordinary drift while PowerShell reads the reviewed
launcher. The authorization does not contain its own digest.

The launcher accepts one exact role literal: `builder`, `publisher`, or
`integrator`. Each one-use canonical authorization has exactly:

```text
schema, checkpoint, role, plan_sha256, schemas_sha256,
runtime_manifest_source, runtime_manifest_sha256,
runtime_manifest_byte_count, common_source_rows, utility_source_rows,
utility_review_rows, predecessor_state, role_arguments,
role_argument_source_rows, launcher_wall_ms, stdout_byte_cap, stderr_byte_cap
```

`schema` is `pontius-python-runtime-launch-authorization-v1`. `checkpoint` is
exactly `builder-ready`, `publisher-ready`, or `integrator-ready`, matching
`role`. The complete authorization uses compact sorted-key ASCII JSON plus one
LF. Strings contain no NUL, control character, unpaired surrogate, shell
fragment, or environment expansion. Every count and wall is a positive base-
ten JSON integer within the final plan's fixed bound. Digests are lowercase
SHA-256.

`common_source_rows`, `utility_source_rows`, and `utility_review_rows` are
ASCII-path-sorted arrays. Every row has exactly `path`, `sha256`, and
`byte_count`. Common rows cover every plan, schema, workflow, interpretation,
runtime-closure, and packet-source-manifest input required at that checkpoint.
Utility rows cover the launcher and all three Python utilities. Review rows
cover the exact eight required review slots. The Stage 2 controller validates
all eight receipt objects against their paths, roles, distinct-reviewer rules,
plan/schema pins, utility hashes, CLEAN verdicts, and false candidate-read
attestations.

`predecessor_state` is the exact closed role-specific object defined by the
final v8 schemas. Builder authorization binds the initial local authority tuple
and all fixed builder inputs. Publisher authorization is formed only after it
can bind the exact builder intent and local candidate/packet graph. Integrator
authorization is formed only after it can bind that graph, the exact remote
pair, and every deterministic publication-receipt input. Any changed or
unknown predecessor refuses; the launcher never derives a replacement value.

`role_arguments` is an ordered array of exact strings under a closed per-role
schema in the final v8 plan and schemas. `role_argument_source_rows` is sorted
by `argument_index`; each row has exactly `argument_index`, `path`, `sha256`,
and `byte_count`, and covers every file-backed argument source. The final plan
must define each role's exact array length, value domains, and predecessor-
state-to-array equality. An unbound or extra argument refuses.

There is no arbitrary script path, command suffix, shell fragment, environment
override, interpreter override, or pass-through option. Unknown, duplicate,
missing, or extra input refuses before runtime-file opens. The launcher first
opens and retains `FileShare.Read` streams for its own source, the runtime
manifest, the selected role source, and every role-argument source. It checks
their authorization byte counts and SHA-256 values from those same streams and
parses only held bytes. Its self-digest must also equal the source handle
retained by the Stage 2 controller. Neither launcher nor child fills an absent
value from observed bytes.

## Exact child launch

The launcher creates one unique ordinary, non-reparse directory matching:

```text
D:\Pontius\tmp\handoff-freeze-<32 lowercase hex>
```

`TEMP` and `TMP` both equal that directory. Its initially empty `pycache`
child is the exact `pycache_prefix`. The launcher validates the entire path
chain and retains the temporary-root and pycache directory identities. A
preexisting path, wrong owner identity, reparse component, or nonempty pycache
refuses.

The child receives a newly constructed Unicode environment with exactly:

```text
LANG=C
LC_ALL=C
SYSTEMROOT=C:\Windows
TEMP=<the unique verified temporary root>
TMP=<the same unique verified temporary root>
WINDIR=C:\Windows
```

The launcher inherits no parent variable. In particular, `PATH`, `HOME`,
`APPDATA`, `LOCALAPPDATA`, every `PYTHON*`, every `GIT_*`, proxy, TLS, askpass,
trace, module-routing, and shell-routing variable is absent. Environment names
are uppercase and unique under Windows case folding. The launcher serializes
the Unicode environment block by ordinal-ignore-case name order with its
required final double NUL.

The direct executable receives this exact option sequence:

```text
-I
-S
-B
-P
-X
utf8=1
-X
frozen_modules=on
-X
pycache_prefix=<the unique verified pycache directory>
```

The exact role utility path follows those options. After it, the runtime wrapper
arguments are exactly, in this order:

```text
--runtime-lock-write-handle
<unsigned base-ten inherited handle with no leading zero>
--runtime-ack-read-handle
<unsigned base-ten inherited handle with no leading zero>
--launcher-nonce
<32-lowercase-hex nonce>
--authorization-source
<exact held absolute authorization path>
--authorization-sha256
<exact lowercase SHA-256 supplied by Stage 2>
--authorization-byte-count
<positive base-ten count with no leading zero>
--role-arguments-begin
<each role_arguments string in stored array order, with no transformation>
```

The final argv suffix after `--role-arguments-begin` equals `role_arguments`
element-for-element. There is no default, derived, reordered, normalized, or
omitted role argument. The working directory is exactly `D:\Pontius-handoffs`.
Standard input is an immediate-EOF pipe. Standard output and standard error are
separate binary pipes drained concurrently into verified files under the unique
temporary root; neither is decoded until exit.
The two additional pipes carry only the runtime-lock frame and its one-byte
acknowledgement, then close. The executable v8 plan pins exact per-role output
caps; overflow terminates the job and refuses.

The child argument vector starts with the exact direct `python.exe` path, then
the option sequence above, the exact role source, the runtime wrapper arguments,
and the exact stored `role_arguments` tail. The launcher serializes each
argument by this fixed Windows rule:

1. encode an empty argument as `""`;
2. leave a nonempty argument unquoted only when it contains no space, tab, or
   double quote;
3. otherwise surround it with double quotes, preserve every backslash run
   before an ordinary character, emit `2n + 1` backslashes before an embedded
   double quote following a run of `n`, and emit `2n` backslashes before the
   closing quote for a final run of `n`; and
4. join encoded arguments with one U+0020 space and no leading or trailing
   space.

The launcher calls `CreateProcessW` with non-null `lpApplicationName` equal to
the direct executable, a mutable buffer containing that exact command line,
the exact working directory, the constructed environment, `bInheritHandles`
true, and `dwCreationFlags` equal exactly to `CREATE_SUSPENDED` `0x00000004`,
`CREATE_UNICODE_ENVIRONMENT` `0x00000400`, and
`EXTENDED_STARTUPINFO_PRESENT` `0x00080000` ORed together. Process and thread
security-attribute pointers are null. A zero-initialized `STARTUPINFOEXW` has
`cb` equal to its exact native size, `dwFlags` equal only to
`STARTF_USESTDHANDLES` `0x00000100`, and one
`PROC_THREAD_ATTRIBUTE_HANDLE_LIST`. That list has exactly five inheritable
child-side handles: an stdin read handle whose writer is closed before resume,
stdout write, stderr write, runtime-frame write, and acknowledgement read.
Every parent-side pipe handle and every runtime-file, directory, manifest,
utility-source, process, thread, job, mutex, and controller handle is
noninheritable and absent from the attribute list.

The launcher creates a Job Object with kill-on-close and no breakaway, assigns
the suspended child, closes its local duplicates of the five child-side
handles, then resumes the primary thread. No shell or executable search occurs.

Failure after process creation but before assignment or resume terminates the
process and proves exit. Failure after assignment, malformed handshake, child
timeout, or coordinator cancellation terminates the job and proves active
process count zero. The integrated v8 plan must fix a measured per-role launcher
wall before live use; this insert invents no unmeasured wall. Until all three
walls are exact, live execution remains blocked.

## Launcher verification and ownership

The launcher validates the runtime-manifest byte count and SHA-256 before JSON
parsing. It then validates the exact schema, key sets, types, fixed values,
2,614-row population, row ordering, unique paths, root-directory population,
row byte-count sum, and `63,499,244` total. It derives the population from the
literal base root rather than trusting the manifest's file list as an
enumeration result.

For every inventory row, the launcher:

1. opens the exact path using `FileMode.Open`, `FileAccess.Read`, and
   `FileShare.Read`, retaining the resulting `FileStream` strongly;
2. rejects a reparse or non-disk object and validates the handle-resolved final
   path;
3. records one run-local handle identity using one API consistently: 64-bit
   volume serial plus 128-bit `FileIdInfo`;
4. obtains byte count and SHA-256 from that same held stream; and
5. compares them with the exact manifest row.

`FileShare.Read` permits the child loader and import machinery to read the
files while denying ordinary write, delete, and rename opens through any name
for the same file identity. A preexisting conflicting writer makes the
launcher's open fail closed.

The launcher also holds the scoped runtime directories with read/list and
attribute access but no write/delete sharing. It validates each ordinary,
non-reparse ancestor and the directories governing forbidden startup paths.
It performs a final exact population and forbidden-path check after all file
and directory handles are held and immediately before `CreateProcessW`.

Every runtime stream and directory handle remains open through child exit and
job active-process-zero proof. The launcher does not release an unused subset
after the child handshake. This full-duration ownership is the simple rule
that makes late standard-library imports safe without predicting a transitive
module graph.

After job quiescence, the launcher rewinds and rehashes all held runtime files,
rechecks their FileIdInfo, size, and final paths, and repeats the exact
population and forbidden-path checks before releasing any handle. A mismatch
is a typed runtime-integrity failure even when the child exit code is zero.
All acquired handles close once in reverse acquisition order inside the
launcher's outermost `finally` block.

## Child runtime lock and independent checks

Before `RUNTIME_LOCKED`, the Python utility may read only the held role utility,
runtime manifest, canonical authorization, and common bootstrap sources named
by that authorization. It does not read a candidate artifact, packet source, H
repository, Git object, or network path and performs no authority operation.
Its first phase validates the complete manifest bytes and the following exact
process facts:

- every exact field in the manifest's `runtime` object, including CPython
  `3.11.15`, implementation `cpython`, its full version string, integer
  `version_hex` `51056624`, cache tag `cpython-311`, platform `win32`, little
  endian, `filesystem_encoding` `utf-8`, `filesystem_errors` `surrogatepass`,
  and `maxsize` `9223372036854775807`;
- exact `sys.executable`, `sys._base_executable`, `sys.prefix`,
  `sys.base_prefix`, `sys.exec_prefix`, and `sys.base_exec_prefix`;
- exact complete `sys.flags` and `sys._xoptions`, including isolated,
  no-site, no-user-site, ignore-environment, safe-path, no bytecode writes,
  optimization zero, `sys.flags.debug == 0`, `__debug__ is True`, UTF-8 mode,
  frozen modules on, and the exact dynamic pycache prefix;
- exact initial ordered `sys.path`, followed by replacement with only the
  manifest's ordered `DLLs` and `Lib` import paths;
- exact six-entry process environment and exact working directory; and
- absence of every forbidden startup path and an empty pycache directory.

The child imports all modules its role may need before its first authority
operation. It then inventories every file-backed `sys.modules` origin and every
loaded native image. Builtin and frozen modules bind to the held
`python311.dll`. `__main__` binds to the role's exact reviewed utility source.
Every other module origin must map to an exact held runtime-inventory row.
Every loaded image must map to such a row or to an allowed final System32 path.

The child independently opens every used runtime file with read-only sharing,
hashes it from the held handle, validates FileIdInfo, final path, and manifest
row, and retains that handle through its final reconciliation. The used set may
grow monotonically after a later import or native load, but the audit hook
allows only inventory-backed or trusted-System32 origins and the child must
hold and validate the new file before the next authority boundary. The parent
launcher continues to hold the complete inventory throughout, so no unheld
runtime byte can change during that interval.

Immediately before each local `update-ref`, remote push, or success decision,
and after every timeout or lost-acknowledgement reconciliation, the child
rechecks its held used-file identities, hashes, module origins, loaded images,
runtime facts, process environment, and empty pycache directory. A mismatch
preserves state and refuses.

Before any authority operation, the child emits one length-framed ASCII JSON
message on the dedicated control pipe. It has exactly:

```text
schema, phase, launcher_nonce, role, runtime_manifest_sha256,
runtime_manifest_byte_count, runtime_file_count, runtime_total_bytes,
python_executable, python_executable_sha256, used_runtime_file_count,
used_runtime_rows_sha256, loaded_non_system_image_rows_sha256,
pycache_prefix, pycache_empty, child_runtime_handles_held
```

`schema` is `pontius-python-runtime-locked-v1`; `phase` is
`runtime-locked`; `launcher_nonce` is the launcher's one-use 32-lowercase-hex
value; `pycache_empty` and `child_runtime_handles_held` are true. Used-runtime
and non-System32-image digests use complete path-sorted canonical row bytes
defined here. Each selected inventory row is encoded with the schemas' compact,
sorted-key ASCII JSON convention plus one LF. Unique rows sort by ASCII `path`;
the digest hashes their concatenation. The used-runtime set is the union of the
process image, non-System32 images, file-backed modules, and runtime data files.
The non-System32-image set is its image subset.

The complete handshake object uses the same compact ASCII JSON convention plus
one LF. Framing is one unsigned 32-bit little-endian byte length, no greater
than `65536`, followed by exactly that many JSON bytes. The launcher validates
exact types, values, framing, length, nonce, and control-pipe EOF, then writes
the single acknowledgement byte `0x01`. Until it reads that byte, the child
blocks without opening the repository, packet sources, Git, or a network path.
EOF, another byte, or a timeout is a typed refusal. Neither the nonce nor
dynamic pycache path enters a deterministic Git object.

After acknowledgement, the child acquires
`Global\PontiusHandoffsAuthority`. The PowerShell launcher never acquires that
mutex and never performs an authority operation. The child holds the mutex
from its first repository/input validation through every child process, local
or remote mutation, reconciliation, and final classification, exactly as the
v8 utility contract requires. Runtime locking may precede the mutex only
because neither launcher nor unacknowledged child can touch authority state.

## Receipt and object bindings

The v8 fixed literals add:

```text
runtime_manifest_source = D:\Pontius\codex-python-runtime-closure-v1.json
runtime_manifest_packet_path = checks/python-runtime-closure.json
runtime_manifest_sha256 =
  3390ab3d041d432f06754ca94aed348774c421de1c14553a25395c2cab112a3a
runtime_manifest_byte_count = 413522
runtime_file_count = 2614
runtime_total_bytes = 63499244
runtime_controller_tcb = windows-powershell-dotnet-controller-v1
```

The executable v8 plan must pin the runtime-manifest identity, the complete
launcher and three Python utility paths, SHA-256 values and byte counts, the
eight required review slots, and exact per-role maximum bounds for walls and
output caps before final utility review. After all eight reviews, each one-use
live authorization pins the same utility projection, all eight review digests,
the source-manifest digest, and the selected role wall and caps. Absence of any
value blocks live execution; no runtime observation supplies a missing value.
The plan never pins review content that must itself bind the plan.

`utility_sha256` becomes an exact four-key object: `runtime_launcher`,
`builder`, `publisher`, and `integrator`. Every utility static-verification
receipt repeats `runtime_manifest_sha256` and binds the exact v8 plan and
schemas. The launcher's two receipts have `utility_role` equal to
`runtime-launcher`, bind the exact launcher digest, attest that candidate
artifacts were not read, and otherwise follow the reviewed v8 utility-receipt
schema.

The preparation receipt's `runtime` object replaces the launcher-only v7
record. It has exactly:

```text
schema, runtime_manifest_sha256, runtime_manifest_byte_count,
runtime_file_count, runtime_total_bytes, python_executable,
python_executable_sha256, runtime_launcher_sha256, controller_tcb,
child_runtime_locked_when_encoded, launcher_holds_full_runtime_when_encoded,
child_holds_used_runtime_when_encoded, pycache_empty_when_encoded
```

The four booleans are true. They describe the instant of encoding only. The
receipt does not claim future handle retention, persistent FileIdInfo, a
historical absence of a race, or TCB integrity. The launcher state machine is
the requirement that keeps handles held through the later transition.
`schema` is `pontius-python-runtime-attestation-v1`; `controller_tcb` is the
fixed `windows-powershell-dotnet-controller-v1` literal.

The preparation receipt's `operations` object adds exact booleans
`runtime_launcher_executed`, `runtime_manifest_verified`, and
`child_runtime_locked`, all true. Its existing `controller_executed` field
continues to mean execution of the candidate controller artifact; it remains
false and is not an alias for the trusted runtime launcher.

Builder intent, remote-publication receipt, and integration intent repeat
`runtime_manifest_sha256` and `runtime_launcher_sha256`. Every repeated value
is byte-for-byte equal. The packet inventory binds the manifest and launcher
blob OIDs, SHA-256 values, and byte counts. The candidate commit,
`manifest.sha256`, and `candidate.json` do not change.

The packet population changes as follows:

- add `checks/python-runtime-closure.json`;
- add `checks/runtime-launcher.ps1`;
- add the two launcher static-verification receipts;
- expand three utilities to four and six utility receipts to eight; and
- add exactly four non-generated packet-source rows relative to the baseline
  ultimately adopted for v8.

The runtime insertion changes fields in the generated preparation receipt but
does not itself add another generated packet path. Overall source, packet-diff,
and self-excluding-inventory counts must be recomputed from the final v8
receipt and handoff populations. Earlier total-count arithmetic is not
authority for that recomputation.

Fresh-repository recovery requires the exact runtime manifest and reviewed
launcher source as external frozen inputs before any Python utility starts.
After remote packet adoption, their local bytes must equal the packet blobs.
The packet cannot bootstrap a different launcher or runtime because Python has
already started by then.

## Required disposable rehearsal

Before any real H object, ref, or remote mutation, the reviewed launcher and
three children must demonstrate all of the following against a disposable
runtime copy or an equivalent real-file fault schedule:

1. exact success for 2,614 files, 63,499,244 bytes, the manifest digest, direct
   base executable, runtime facts, six-entry environment, argv, and pycache;
2. refusal for one missing, extra, duplicate, reordered, case-colliding,
   reparse, nonordinary, wrong-size, or wrong-digest inventory entry;
3. refusal for same-size content mutation with restored timestamp, proving
   content and handle identity rather than size/time identity;
4. refusal when any forbidden startup path appears, a root directory changes,
   `sys.path` changes, a virtual-environment prefix appears, or site/user path
   injection is attempted;
5. proof that normal runtime `__pycache__` files cannot be selected and that a
   nonempty unique pycache prefix refuses;
6. a preexisting writer conflict that prevents a held open, plus attempted
   write, rename, delete, and hardlink-alias mutation while the launcher holds
   `FileShare.Read` streams;
7. a deliberately relaxed-share swap caught independently by final path,
   FileIdInfo, size, and rehash checks;
8. exact rejection of a wrong executable, option order, environment entry,
   working directory, role, utility digest, script path, extra argument, or
   shell-mediated launch, plus a null or changed `lpApplicationName`, wrong
   `argv[0]` or quoting, wrong creation flag, or extra inherited handle;
9. exact child refusal for wrong version, flags, xoptions, prefixes, encoding,
   startup path, module origin, non-System32 image, used-file digest, or
   runtime-manifest digest;
10. a late standard-library import and private-DLL load admitted only when the
    file is in the locked inventory and added to the child's held used set;
11. malformed, oversized, duplicate-key, wrong-nonce, partial, extra-byte,
    missing, and timeout runtime-lock handshakes, with no authority operation;
12. assignment failure, resume failure, direct-child exit with a live
    descendant, child timeout, coordinator cancellation, and active-process-
    zero proof while every runtime handle remains held;
13. attempted runtime mutation during Git timeout and lost-acknowledgement
    reconciliation, proving launcher and child handles outlive the operation;
14. final full rehash/population success and one injected final mismatch that
    converts an otherwise-zero child exit into a typed refusal; and
15. structural and behavioral proof that the launcher never reads or executes
    a candidate, harness, Model, sensitive case, analyzer, controller, or test;
    and
16. PowerShell Stage 2 preflight refusal before any child is created for a wrong
    Windows version, UBR, architecture, pointer width, PowerShell version, or
    .NET version; for any path, SHA-256, or byte-count mismatch in the runtime-
    closure manifest, launcher, common source, selected role source, role-
    argument source, utility review, or canonical authorization; and for any
    changed plan/schema pin, role/checkpoint pair, predecessor-state binding,
    role-argument array, wall, or output cap.

The rehearsal records the trusted controller facts and the explicit nonclaims.
It does not convert the launcher into evidence, authorize a candidate run, or
widen `COLD_INPUT_READY` beyond the existing v8 boundary.
