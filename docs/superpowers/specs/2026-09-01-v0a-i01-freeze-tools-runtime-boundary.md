# v0a increment 1 freeze tools r002 runtime boundary

Status: ISOLATED R002 DESIGN DRAFT. This document authorizes no build, utility,
candidate, harness, Model, test, Git, credential, network, or repository
execution. It replaces the r001 runtime shape for review. Values marked
`TO-BE-FROZEN` must be supplied by frozen artifacts before any live dispatch.

Stage0b: cap=3 lock=R002_FREEZE no6=true terminal=r005 ordinal=5 locked=true

## Decision

The authority utilities do not start with the installed `python.exe`. A small,
reviewed native bootstrap starts first, establishes the DLL search policy, and
then loads the exact CPython DLL by absolute path. It configures CPython through
isolated `PyPreConfig` and `PyConfig` values instead of allowing executable or
environment discovery.

Each role receives its own complete runtime projection:

```text
builder
publisher
integrator
```

The fourth review role, `runtime-owner`, is the native supervisor, bootstrap,
capsule producer, audit policy, and typed-broker implementation shared by those
three child roles. It has its own complete reviewed source projection, but it
is not a Python child policy and is never loaded into a child interpreter.
The broker engine is linked into and executes inside this same trusted native
supervisor process. There is no second broker process or broker executable.
Every transition authorization and launch dispatch binds the complete
four-role source-projection set. The supervisor holds and validates its
`runtime-owner` member plus the selected execution-role member before process
creation; runtime evidence repeats the same complete set after Job quiescence.
Each authorization binds one exact route-selector identity and the dispatch
carries its complete owner-only bytes. A normal raw-object-v5 selector is
`pontius-round-preregistration-v1`; the utility's preacceptance HTTPS campaign
uses only `pontius-utility-rehearsal-selector-v1`. For a normal launch, task and
round equal the preregistration root. For a rehearsal launch, authorization and
dispatch task, round, and `rehearsal_task_binding_id` equal the selected campaign
binding; the selector root task and round remain the utility-bootstrap identity.
Role-applicable stable coordinates, table, source projection, and selector kind
must agree before the supervisor opens a repository or creates a process.
The rehearsal selector also carries the complete campaign, derived-input
contracts, typed fixtures, acyclic adoption-chain set, reviewed fault-harness/
parser projection, disjoint case refs, and pre-production/pre-rehearsal
capability observations. A rehearsal adoption fetch and its later adopter select
one exact chain-row digest; that row fixes the builder-intent fixture and copied
candidate, packet, blob-OID, and SHA-256 identities. Task-scoped
refs derive from the selected campaign binding; the case-shared `HANDOFF_MAIN`
row has no task binding. The selector contains no accepted utility authority,
normal preregistration, or later result.
Server-event fault reservations bind the rehearsal endpoint, repository, and
reviewed deployment procedure. Process-only faults on a network schedule retain
all five endpoint, repository, component-binding, server-policy, and
deployment-receipt fields and equal the selected deployment receipt. Offline
process faults have all five fields null. Reservation, activation, fault result,
and final revalidation must preserve that branch exactly.

A projection contains one deterministic, uncompressed ZIP archive of all pure
Python source used by that role, one closed native-image population, one closed
runtime-data population, one audit policy, and one exact role broker identity.
There is no shared source file outside those projections. Common pure-Python
code is copied into each archive and is reviewed and hashed as an explicit row
of each role's source set.

The Python process never receives raw Git argv, a process-launch API, a remote
endpoint selector, a credential, or a repository mutation handle. After the
runtime locks, the supervisor attaches one role-specific typed-operation
broker. The broker resolves a closed operation identifier through the one
role table selected before launch. It accepts no executable, script, argv,
path, URL, ref, environment, helper, or shell selector from Python.

This shape closes the r001 pre-execution gap. Stock `python.exe` cannot install
a safe DLL policy before `python311.dll` is mapped, and `_pth` isolation alone
does not freeze import or native-load behavior. File holds and post-load image
inspection remain useful evidence, but neither is the first enforcement point.

## Protected invariants

The implementation must preserve all of these invariants:

1. Every non-System32 executable byte is identified and held before it can be
   selected for execution.
2. No Python source, cache, native image, or runtime-data file outside the
   selected role projection can influence the process.
3. The selected role source set is exhaustive and is bound through design,
   review, authorization, launch, handshake, receipts, and final revalidation.
4. No import, native load, runtime-data open, or module-set change occurs after
   `RUNTIME_LOCKED`.
5. Python can request only operations in its selected role grammar. It cannot
   construct or launch Git or any other process.
6. No authority channel, repository handle, credential, or remote route enters
   the Python process before the supervisor accepts `RUNTIME_LOCKED`.
7. Runtime failure is sticky. Once observed, no later clean sample, retry, or
   process exit can restore authority in that launch.
8. Every failure handled by a live supervisor terminates the contained process,
   proves job quiescence, and preserves repository, ref, remote, and credential
   state except for an exact operation already reconciled by its role protocol.
   A supervisor crash relies on external kill-on-close containment and emits no
   self-attested semantic envelope.

## Existing source closure and r002 projections

The existing source inventory remains an input, not the execution boundary:

```text
path = D:\Pontius\codex-python-runtime-closure-v1.json
sha256 = 3390ab3d041d432f06754ca94aed348774c421de1c14553a25395c2cab112a3a
byte_count = 413522
schema = pontius-python-runtime-closure-v1
source_file_count = 2614
source_total_bytes = 63499244
```

It identifies CPython `3.11.15` on Windows and includes this root row:

```text
path = python311.dll
sha256 = 71ec92fb9efdf0bf9f8cc1780cf8be4ef7ba38bc1ff6d1d32ab13f24f2ded648
byte_count = 5843968
```

R002 does not put the full 2,614-file installation on `sys.path`. A deterministic
projection builder selects the minimum closed source and native populations for
each role. Every selected CPython source row must reproduce one row of the
existing inventory. Every project source row must reproduce one frozen Git blob
named by the later accepted implementation candidate and its manifest. This
design candidate has no executable source. An unselected installed-runtime file
has no runtime authority.

Each projection is canonical ASCII JSON plus one LF with schema
`pontius-freeze-runtime-projection-v2`. Its root contains exactly these keys in
ASCII order:

| Key | Type |
| --- | --- |
| `archive` | runtime-archive object |
| `archive_entry_rows` | archive-entry array |
| `askpass_adapter` | runtime-component object or `null` |
| `audit_policy` | bound-document identity |
| `bootstrap` | runtime-component object |
| `broker` | broker-projection object |
| `dispatch_registry` | bound-document identity |
| `limits` | runtime-limits object |
| `native_rows` | native-row array |
| `platform` | platform-projection object |
| `process_policy` | bound-document identity |
| `pyconfig` | bound-document identity |
| `python_runtime` | Python-runtime object |
| `role` | `builder`, `publisher`, or `integrator` |
| `runtime_data_rows` | runtime-data-row array |
| `schema` | exact `pontius-freeze-runtime-projection-v2` |
| `source_rows` | source-row array |
| `supervisor_exit_code_map` | bound-document identity |
| `supervisor_executable` | bound-document identity |
| `system_image_rows` | system-image-row array |

The projection does not contain its own digest. Its external SHA-256 and byte
count are pinned everywhere the projection is consumed.

`supervisor_executable` names the complete
`pontius-supervisor-executable-projection-v1` document. That document binds
the installed supervisor file, runtime-owner source projection, deterministic
build receipt, link map, and PE audit. Every role projection repeats the same
identity; the public controller session carries the complete object and the
live image must reproduce its file identity.

### Closed nested projection values

A bound-document identity has exactly `byte_count`, `schema`, and `sha256`.
It names canonical ASCII JSON plus one LF whose parsed root has that exact
schema. The static document occurs exactly once as a held source-projection
entry; a digest without the complete held bytes refuses.

A route-selector identity has the same exact three fields but is a distinct
type. Its complete canonical preimage is held by the supervisor and carried in
the launch dispatch and runtime evidence. It is created after the accepted
source projections and is not required or permitted to masquerade as a source-
projection entry. The authorization identity, both complete wrappers, and
final revalidation must reproduce the same schema, count, and SHA-256.

Every final path in this appendix uses the schema appendix's exact
`GetFinalPathNameByHandleW(FILE_NAME_NORMALIZED | VOLUME_NAME_DOS)` transform.
The supervisor accepts only drive-form results, strips only the extended prefix,
uppercases only the drive letter, and retains returned component spelling. An
input path spelling or a separately normalized string is never an identity.

A runtime-component object has exactly `byte_count`, `capsule_relative_path`,
`logical_name`, `sha256`, and `source_entry_sha256`. Relative paths use the ZIP
member grammar below and logical names are frozen ASCII identifiers. The source
entry must exist exactly once in this role's source population.

An owner-component object has exactly `byte_count`, `logical_name`, `sha256`,
and `source_entry_sha256`. It names exactly one `WINDOWS_OWNER` entry in the
held runtime-owner source projection. It has no capsule path and denotes code
already linked into the live supervisor executable; it cannot select or launch
another program.

`askpass_adapter` is `null` for builder. Publisher and integrator each carry
one runtime-component object whose logical name is exact `ASKPASS_ADAPTER`,
capsule-relative path is exact `pontius-askpass.exe`, and unique source entry
has kind `ASKPASS_ADAPTER`. Runtime-owner and builder have no adapter source
entry. A wrong role population or a second adapter refuses projection.

`pontius-runtime-bootstrap-projection-v1` has exactly `binary`,
`build_receipt`, `pe_audit`, `schema`, and `source`. `binary` is the exact
runtime-component object for the native bootstrap; the other three values are
bound-document identities. `source` has exact schema
`pontius-runtime-bootstrap-source-set-v1`; its root has exactly `entries` and
`schema`, and an entry has exactly `byte_count`, `logical_name`, `sha256`, and
`source_entry_sha256`.

`build_receipt` has exact schema
`pontius-runtime-bootstrap-build-receipt-v1`. Its root has exactly `binary`,
`build_recipe`, `compiler`, `link_map`, `linker`, `rebuilds`, `schema`, and
`source_set_sha256`. Binary and link map are byte identities; build recipe is
an artifact identity; compiler and linker are held file identities; and
`rebuilds` contains exactly two byte-identical output observations from clean
build roots.

`pe_audit` has exact schema `pontius-runtime-bootstrap-pe-audit-v1`. Its root
has exactly `binary_sha256`, `clr_header_present`, `delay_imports`,
`entry_point_hex`, `exports`, `imports`, `machine`, `schema`, and
`tls_callbacks_present`. Machine is exact `AMD64`; both presence booleans are
false; delay imports are empty; and the complete import/export arrays are
sorted and unique. Every bootstrap identity occurs exactly once in the
runtime-owner source projection.

The platform-projection object has exactly `architecture`,
`known_dll_policy`, `os_build`, `system32`, and `tcb_read_policy`.
`architecture` is exact `AMD64`; `os_build` is the controller-frozen Windows
build literal; `system32` is a `sealed_path_identity`; and both policy fields
are bound-document identities. `pontius-runtime-tcb-read-policy-v1` has exactly
`classes`, `os_build`, and `schema`; classes are unique frozen ASCII literals in
the order fixed by the accepted plan.

`pontius-runtime-known-dll-policy-v1` has exactly `api_set_rows`,
`known_dll_rows`, `os_build`, and `schema`. A KnownDLL row has exactly
`basename`, `machine`, and `system_image_path`. An API-set row has exactly
`contract` and `host_basenames`. Arrays are case-fold sorted and unique, and
host arrays are closed. The case-folded union of every KnownDLL basename and
API-set host basename equals the system-image basename population. Each
KnownDLL path and machine equal its unique system-image row, and every row's
build equals this policy. An unresolved or extra host refuses.

The dispatch-registry policy schema is
`pontius-consumed-dispatch-registry-policy-v1`. Its root has exactly `acl`,
`directory`, `filename_grammar`, `record_schema`, `retention`, and `schema`.
`directory` is a sealed-path identity held by the supervisor; `acl` is a bound
policy document; filename grammar is exact
`<plan_sha256>-<dispatch_nonce>.json`; record schema is exact
`pontius-consumed-dispatch-record-v1`; and retention is exact `PERMANENT`.

The Python-runtime object has exactly `abi_tag`, `dll`, `home`,
`implementation`, `installed_projection`, and `version`. `implementation` is
exact `CPython`, `version` is exact `3.11.15`, `abi_tag` is exact
`cp311-win_amd64`, `dll` is a runtime-component object, `home` is a
`sealed_path_identity`, and `installed_projection` is a bound-document identity
for `pontius-installed-runtime-projection-v1`.

`pontius-installed-runtime-projection-v1` has exactly `closure`, `files`,
`root`, `schema`, and `version`. `root` is a `sealed_path_identity`; `version`
is exact `3.11.15`; and `closure` is a bound-document identity for the accepted
`pontius-python-runtime-closure-v1` source-closure document. A file row has
exactly `byte_count`, `file_identity`, `relative_path`, and `sha256`.
`relative_path` uses the archive-member path grammar without a leading
separator. Rows sort by unsigned relative-path bytes, are case-fold unique, and
enumerate the complete `inventory.files` population selected by the closure.
Every row reproduces one closure row's `path`, `byte_count`, and `sha256` and
adds the same-query final-path `FileIdInfo` observed below `root`. The root,
version, and complete file population also reproduce the closure's runtime and
inventory values. The projection contains no discovered extra file and does
not contain its own digest.

The runtime-archive object has exactly `byte_count`, `entry_count`,
`entry_rows_sha256`, `relative_path`, and `sha256`. `entry_count` is positive,
`relative_path` is exact `role.zip`, and the row digest hashes the concatenated
canonical entry-row bytes. An archive-entry row has exactly `archive_path`,
`byte_count`, `crc32_hex`, `sha256`, and `source_entry_sha256`.
`crc32_hex` is eight lowercase hexadecimal characters. Rows sort by unsigned
`archive_path` bytes and are nonempty.

A native row has exactly `byte_count`, `capsule_relative_path`,
`delay_imports`, `imports`, `logical_name`, `machine`, `preload_ordinal`,
`sha256`, and `source_entry_sha256`. Machine is exact `AMD64`; import arrays are
case-fold-unique ASCII basename arrays in stored order; preload ordinals are
positive and contiguous. Rows sort by preload ordinal.

A system-image row has exactly `basename`, `byte_count`, `final_path`, `machine`,
`os_build`, and `sha256`. Basenames are case-fold unique; final paths are
absolute System32 paths; machine and build equal the platform projection. Rows
sort by folded basename. A `SYSTEM32` loaded-image row reproduces its unique
system row's basename, final path, byte count, and SHA-256; a `PRIVATE` row
reproduces one native row. No other relation satisfies loaded-image equality.

A runtime-data row has exactly `kind`, `logical_name`, `row_sha256`, and
`source_entry_sha256`. Kind is `ARCHIVE_ENTRY` or `NATIVE_METADATA`.
`row_sha256` names exactly one archive-entry or native row. Rows sort by kind,
then logical name, and the initial three projections contain no post-lock row.

The audit-policy document schema is `pontius-runtime-audit-policy-v1`. Its root
has exactly `post_lock_rules`, `pre_lock_rules`, and `schema`. A rule has exactly
`action`, `argument_predicate`, `event`, and `ordinal`; action is `ALLOW` or
`DENY`, ordinals are positive and contiguous, and event names are closed ASCII
literals. `argument_predicate` is the complete canonical
`pontius-runtime-audit-argument-predicate-v1` object. That object has exactly
`clauses`, `event`, and `schema`. A clause has exactly `argument_ordinal`,
`kind`, and `value`; kind is `ANY`, `EXACT_ASCII`, `EXACT_COUNT`, `EXACT_NULL`,
or `SEALED_PATH_ROLE`, and value has the matching closed string, integer, null,
or frozen path-role type. Clauses have contiguous ordinals. A generic
expression, regex, callback, omitted argument, or unknown kind refuses. Unknown
security-relevant events select the final deny rule.

The PyConfig document schema is `pontius-pyconfig-projection-v1`. Its root has
exactly `config_fields`, `preconfig_fields`, `schema`, and `version`. Version is
exact `3.11.15`. A field row has exactly `name`, `type`, and `value`; type is
`BOOL`, `INT`, `NULL`, `STRING`, or `STRING_ARRAY`, and value has exactly the
selected JSON type. Rows sort by ASCII name, names are unique, and the accepted
plan freezes the complete CPython field population. Omission is not a default.

`pontius-runtime-broker-projection-v1` has exactly
`authorized_literal_deltas`,
`broker_session_template_set`, `engine`, `operation_schedule_set`,
`operation_set`, `role_table_instances`, and `schema`. `engine` is an owner-
component object. The three set fields and every literal-delta row are bound-
document identities for the schema appendix's complete role-operation,
operation-schedule, broker-template, and authorized-delta documents.
`authorized_literal_deltas` is ASCII digest sorted and contains every distinct
delta named by a table row exactly once, including the canonical empty builder
delta. A
table-instance row has exactly `byte_count`, `instance_kind`,
`literal_delta_sha256`, `operation_schedule_set_sha256`,
`operation_set_sha256`, `sha256`, and `source_entry_sha256`. Instance kind is
`OFFLINE`, `PRODUCTION`, or `REHEARSAL`; network-role rows occur in production,
rehearsal order. Builder has only `OFFLINE` with an empty literal delta. The
instance bytes conform to `pontius-role-table-instance-v1` and repeat both set
digests exactly.

`pontius-broker-session-template-set-v1` has exactly `identities`, `role`, and
`schema`. An identity has exactly `byte_count`, `sha256`, and
`source_entry_sha256`. Rows sort by digest and cover every distinct nonnull
template reference in the complete schedule set exactly once. Each source
entry parses as `pontius-broker-session-template-v1` and closes over the same
role table and schedule coordinates.

The process-policy document schema is `pontius-runtime-process-policy-v1`. Its
root has exactly `all_application_packages_policy`,
`appcontainer_capability_set`, `appcontainer_package_sid`,
`appcontainer_profile`, `appcontainer_setup_receipt`, `askpass_pipe_acl`,
`broker_channel_pipe_acl`, `capsule_acl`, `child_process_policy`,
`current_directory_rule`, `environment`, `final_token_predicates`,
`handle_policy`, `mitigation_policy`, `role_job_policy`,
`schedule_job_policy`, `schema`, and `supervisor_exit_code_map`. The setup receipt is an
`artifact_identity`; every
other nested policy except the two frozen strings is a bound-document identity
for `pontius-runtime-process-policy-leaf-v1`.
The exit-code map is instead a bound-document identity for
`pontius-supervisor-exit-code-map-v1` and is byte-identical to the top-level
runtime-projection binding.

The setup-receipt artifact bytes have exact schema
`pontius-appcontainer-setup-receipt-v1`. Its root has exactly
`askpass_pipe_acl_sha256`, `broker_channel_pipe_acl_sha256`, `capability_sids`,
`capsule_acl_sha256`, `owner_sid`, `package_sid`, `primary_group_sid`, `profile_directory`,
`profile_name`, and `schema`.
Capabilities are empty; profile name and package SID equal the two process-
policy strings; the directory is a file identity; and all three ACL digests equal
their exact process-policy leaves. A receipt path or blob with different
content refuses.

That leaf has exactly `descriptor`, `kind`, `rows`, and `schema`. `descriptor`
is null for non-ACL kinds. For ACL kinds it is a complete
`pontius-security-descriptor-policy-v1` object with exactly `acl_revision_hex`,
`dacl_defaulted`, `owner_sid`, `primary_group_sid`, `sacl_present`,
`schema`, `security_descriptor_control_hex`,
`security_descriptor_revision_hex`, `self_relative_byte_count`,
`self_relative_sha256`, and `template_scope`. Values are exact ACL revision
`00000002`, descriptor revision `00000001`, protected/present/self-relative
control `00009004`, false DACL-defaulted and SACL-present, and setup-receipt
owner/group SIDs. The strict builder and independent reader reproduce the
self-relative bytes, count, digest, and ordered ACE population. Its kind and row key set are
closed:

- `APPCONTAINER_CAPABILITY_SET` has an empty row array;
- `ASKPASS_PIPE_ACL`, `BROKER_CHANNEL_PIPE_ACL`, `CAPSULE_ACL`, and
  `DISPATCH_REGISTRY_ACL` rows have exactly
  `access_mask_hex`, `ace_type`, `flags_hex`, `ordinal`, and `sid`;
- `ALL_APPLICATION_PACKAGES` has one row with exactly
  `creation_policy_hex` and `less_privileged_appcontainer`;
- `CHILD_PROCESS` has one row with exactly `creation_policy_hex`,
  `maximum_children`, and `operation_job_required`;
- `CURRENT_DIRECTORY` has one row with exactly `selector`, whose value is
  exact `RUN_DIRECTORY`;
- `ENVIRONMENT` rows have exactly `name`, `source`, and `value`;
- `FINAL_TOKEN` has one row with exactly `capability_sids`, `integrity_level`,
  `less_privileged_appcontainer`, `package_sid`, and `restricted_sid_policy`;
- `HANDLE` rows have exactly `access_mask_hex`, `duplicate_options_hex`,
  `parent_source_inheritable_at_create`, `role`, and
  `worker_handle_inheritable_at_runtime_lock`;
- `ROLE_JOB` has one row with exactly `active_process_limit`,
  `flags_hex`, `limit_source`, and `ui_restrictions_hex`;
- `SCHEDULE_JOB` has one row with exactly `flags_hex`,
  `limit_source`, and `ui_restrictions_hex`; and
- `MITIGATION` rows have exactly `mask_hex`, `ordinal`, and `policy`.

ACL type is `ALLOW` or `DENY`; environment source is `CLOSED_LITERAL` or
`RESERVATION_DERIVED`. Handle roles are exactly `STDIN`, `STDOUT`, `STDERR`,
`BOOTSTRAP_CONTROL`, `RUNTIME_ATTESTATION`, and `BROKER_CHANNEL`.
`BROKER_CHANNEL` is noninheritable and phase-controlled; the other roles have
their exact read, write, or duplex access frozen by the policy. Token
capabilities are empty and the package SID equals the setup receipt. Role-Job limit source is
`STATIC_ROLE_ONE`; schedule-Job limit source is
`DISPATCH_LIMIT_ROW`. The accepted plan freezes every remaining literal,
ordering, mask, SID, and environment row. Unknown kind, key, row, default, or
generic key/value payload refuses. The dispatch-registry policy's ACL uses the
same leaf schema with kind `DISPATCH_REGISTRY_ACL`.

Process-policy fields map to leaf kinds exactly:

| Field | Required kind |
| --- | --- |
| `all_application_packages_policy` | `ALL_APPLICATION_PACKAGES` |
| `appcontainer_capability_set` | `APPCONTAINER_CAPABILITY_SET` |
| `askpass_pipe_acl` | `ASKPASS_PIPE_ACL` |
| `broker_channel_pipe_acl` | `BROKER_CHANNEL_PIPE_ACL` |
| `capsule_acl` | `CAPSULE_ACL` |
| `child_process_policy` | `CHILD_PROCESS` |
| `current_directory_rule` | `CURRENT_DIRECTORY` |
| `environment` | `ENVIRONMENT` |
| `final_token_predicates` | `FINAL_TOKEN` |
| `handle_policy` | `HANDLE` |
| `mitigation_policy` | `MITIGATION` |
| `role_job_policy` | `ROLE_JOB` |
| `schedule_job_policy` | `SCHEDULE_JOB` |

No field may carry another field's leaf kind.
ACL ACE type is exact `ALLOW`; no deny, inherited, All Application Packages,
Everyone, Anonymous, Administrators, or capability ACE is admitted. Exact rows
are:

In the table, `full` is mask `001f01ff` and `read-execute` is `001200a9`.

| ACL kind | Ordered SID and mask/flags rows |
| --- | --- |
| `CAPSULE_ACL` | SYSTEM `full/03`; owner `full/03`; package `read-execute/03` |
| `BROKER_CHANNEL_PIPE_ACL` | `S-1-5-18/001f01ff/00`; controller owner `001f01ff/00` |
| `ASKPASS_PIPE_ACL` | `S-1-5-18/001f01ff/00`; controller owner `001f01ff/00` |
| `DISPATCH_REGISTRY_ACL` | `S-1-5-18/001f01ff/03`; controller owner `001f01ff/03` |

Owner, package, and SYSTEM SIDs are pairwise distinct. Capsule and dispatch-
registry descriptors are root templates; every created child carries its
freshly queried effective descriptor in runtime evidence. A template digest is
never claimed byte-equal to an inherited child descriptor. Neither pipe grants
the package SID a name-open route: the supervisor creates both broker endpoints
under the owner and duplicates a reduced client handle into the already-bound
worker, while the ordinary askpass adapter opens its outbound pipe as the
controller identity.

`ALL_APPLICATION_PACKAGES` is exactly `creation_policy_hex=00000001` and
`less_privileged_appcontainer=true`. `CHILD_PROCESS` is exactly
`creation_policy_hex=00000001`, `maximum_children=0`, and
`operation_job_required=true`. The six `HANDLE` rows are, in order:

| Role | Granted access | Parent inheritable at create | Worker inheritable at lock |
| --- | --- | --- | --- |
| `STDIN` | `00100001` | true | false |
| `STDOUT` | `00100002` | true | false |
| `STDERR` | `00100002` | true | false |
| `BOOTSTRAP_CONTROL` | `00100001` | true | false |
| `RUNTIME_ATTESTATION` | `00100002` | true | false |
| `BROKER_CHANNEL` | `00100003` | false | false |

Every row has `duplicate_options_hex=00000000`; `DUPLICATE_SAME_ACCESS` is
forbidden. Only the first five enter the initial handle list. Before emitting
`RUNTIME_LOCKED`, the native bootstrap clears `HANDLE_FLAG_INHERIT` on all five
worker handles and queries the cleared state. Resetting or closing only the
parent copies is insufficient. The broker handle is reduced and duplicated
post-lock and is never inherited.

Both Job leaves use `flags_hex=0000260c` and
`ui_restrictions_hex=000003ff`. Role Job active-process limit is one; schedule
Job uses the dispatch limit. PROCESS_TIME, PROCESS_MEMORY, preserve-job-time,
breakaway, and silent-breakaway flags are absent. MITIGATION has the following
ordered rows and exact 64-bit masks: DEP `0000000000000001`, heap terminate
`0000000000001000`, bottom-up ASLR `0000000000010000`, high-entropy ASLR
`0000000000100000`, strict handles `0000000001000000`, Win32k disable
`0000000010000000`, extension-point disable `0000000100000000`, prohibit
dynamic code `0000001000000000`, no remote images `0010000000000000`, no
low-label images `0100000000000000`, and prefer System32
`1000000000000000`. Their OR is exact `1110001111111001`; policy word two,
SEHOP, force-relocate, CFG, signature, font, opt-out, and audit forms are absent.
`ROLE_JOB` has active-process limit one and contains only the AppContainer
worker. `SCHEDULE_JOB` contains no static active-process value; each
created schedule Job receives the separately calibrated positive cap from the
dispatch's exact runtime-limit row for that operation, mode, and variant. Both
Job kinds receive that row's exact per-Job CPU and memory caps and retain its
digest. The owner queries the enabled flags and all three configured values
before resume and again at final revalidation. Schedule Job contains no role
worker. The two policies cannot share bytes or substitute for each other.

The runtime-limits object has exactly `rows` and `schema`. A row has exactly
`calibration_receipt`, `calibration_receipt_artifact`,
`calibration_receipt_byte_count`, `calibration_receipt_sha256`,
`cleanup_reserve_ms`, `cpu_time_ms`, `dispatch_mode`, `memory_bytes`,
`operation`, `schedule_active_process_limit`, `schedule_variant`,
`stderr_byte_cap`, `stdout_byte_cap`, and `wall_ms`. The
receipt is the complete typed `pontius-runtime-limit-calibration-receipt-v1`;
its canonical artifact, positive count, and digest are exact. It contains the
complete `pontius-runtime-calibration-workload-v1` population, including each
`SCALED_REHEARSAL` base artifact, rational scale transformation, executable,
argv, input population, host/runtime projection, and deterministic limit
selection, not a free numeric recommendation. Every numeric field is a positive count. Rows
sort by operation, mode, then variant and cover every
operation-schedule identity in this role projection exactly once. Each row's
standalone canonical bytes plus LF have a frozen digest. Every dispatch binds
that `limit_row_sha256` and repeats its seven numeric values. Each value equals
the selected value in the matching typed receipt row for that role, operation,
mode, and variant. The owner-wall-deadline object repeats the same calibration-
receipt digest.
CPU and memory values are calibrated per Job and apply independently to the
role Job and each schedule Job; wall remains one launch-wide timeline with an
active-work deadline and a later calibrated cleanup deadline.

`python_runtime` also pins a separately accepted installed-runtime projection.
Every installed source is opened first and bound by absolute final path,
same-query `FileIdInfo`, byte count, and SHA-256 before a role projection may be
produced. Moving, reinstalling, or changing the identity of any admitted source
invalidates that installed-runtime projection and requires a new projection
round. Project sources instead bind to frozen Git blob OID, mode, path, byte
count, and SHA-256 from the accepted implementation candidate.

Capsule copies intentionally acquire new, run-local `FileIdInfo` values. Their
authority comes from equality of the copied bytes and declared semantic role,
followed by fresh handle identity for the capsule lifetime. A capsule identity
is never compared as though it were the source installation's file identity.

`process_policy` fixes the preregistered AppContainer profile name, package SID,
empty capability list, frozen setup-receipt identity, capsule, broker-channel,
and askpass-pipe ACL digests, all-application-packages opt-out, child-process
policy, both Job Object policies, process mitigations, inherited
handle set, environment, current-directory rule, and final token predicates.

`source_rows` is the complete ASCII-archive-path-sorted population from which
the role archive was built. Each row has exactly `archive_path` and `source`.
`source` is the schema appendix's exact tagged source entry. Installed runtime,
native, schema, and generated-plan bytes use `HELD_FILE_SOURCE` with final path
and same-query `FileIdInfo`. Project code uses `PROJECT_GIT_SOURCE` with the
accepted implementation candidate, manifest, repository path, mode, blob OID,
byte count, and SHA-256. A zero-byte admitted source is valid. No row is inferred
from an import observed during a run. No source may map to two archive paths,
and no two sources may map to one archive path.

`native_rows` is the complete private PE population. Each row fixes its logical
module name, source identity, capsule-relative path, size, digest, PE machine,
ordinary import names, delay-import names, and preload ordinal. Private import
names are case-fold unique across the projection. A private dependency graph
with an unresolved name or an unsupported cycle blocks projection acceptance.

`system_image_rows` is the exact finite set of image basenames and final
System32 paths allowed for the pinned Windows build. System32 bytes remain in
the trusted platform boundary. Allowing the System32 root does not allow an
unlisted image basename.

`runtime_data_rows` covers every non-code byte CPython or a role may read before
the lock. Each row is also an archive-entry row or an exact native metadata row.
There is no post-lock runtime-data path. Tk, Tcl, profiles, locale databases,
certificate stores, package metadata, user configuration, registry-derived
Python paths, and working-directory data are excluded unless a later projection
explicitly lists and rehearses every required byte. The three r002 projections
must initially exclude them.

This closure governs project-controlled bytes. The projection separately names
the exact classes of OS-owned reads accepted as part of the trusted Windows
boundary, such as KnownDLL and API-set resolution, System32 image mapping, and
documented loader or process metadata. Those classes are nonclaims about byte
identity, not wildcard authority to read project, profile, package, repository,
credential, or working-directory data. An unclassified OS read blocks runtime
acceptance until the TCB class is amended and reviewed.

The producer and an independent consumer must reproduce the complete source
set, archive bytes, native dependency graph, and projection bytes. A projection
that depends on a trace from only one successful run is incomplete.

## Public controller-to-supervisor ABI

Every live run begins at `pontius-controller-supervisor-session-v1`. The
controller starts the one held supervisor executable with nonnull
`lpApplicationName`, null `lpCommandLine`, the exact empty launch directory,
fixed Unicode environment, and one explicit inherited-handle list containing
only control-read, result-write, and bounded diagnostic-write pipes. The
complete `STARTUPINFOEXW` base fields and one handle-list attribute equal the
canonical launch object. No argv, stdin convention, parent environment,
ambient file, registry value, or mutable working path supplies authority.

The fixed `SUPERVISOR_V1` environment is the exact six-entry
`pontius-environment-block-v1` used by the worker launch, with the supervisor's
held empty launch directory supplying `TEMP` and `TMP`. The supervisor opens
and retains its parent process, verifies the complete controller origin, and
accepts the closed outer message sequence: `SESSION_OPEN`,
`SOURCE_ADMISSION`, `AUTHORIZATION`, then `DISPATCH`. The first frame carries
the complete post-create session object; the supervisor checks its own process
and every live-queryable launch fact before accepting later frames. Messages are
session-nonce, sequence, and predecessor-digest bound. All repeated source,
authorization, dispatch, role, operation, task, round, and nonce values must
cross-equal before repository open or process creation. The controller receives
one ordered typed output stream on the result pipe: nonterminal session
acceptance, zero or more secret requests, and exactly one terminal result while
the retained controller/result peer remains live. `PARENT_EXITED` produces
exactly zero terminal wrappers.
Free-form diagnostics are bounded, secret-free, and never semantic evidence.

After dispatch consumption, the same authenticated channel permits only an
exact requested one-use `SECRET_GRANT` or one canonical `CANCEL`. A grant is
followed immediately by one bounded opaque frame; the received frame buffer is
zeroed after its one copy into locked broker storage. The resulting
`pontius-secret-ingress-result-v1` enters the matching broker terminal result.
A cancel becomes `CANCELLED` only through
`pontius-authenticated-controller-cancel-fact-v1` for this session and dispatch.
EOF, controller death, malformed input, replay, or cross-session traffic is
channel loss or protocol failure, never cancellation.
With a live retained parent, control EOF or a nonlocal read failure may complete
typed cleanup and return `CONTROLLER_CHANNEL_LOST`. If the retained parent is
signaled, the result peer is gone: the supervisor cancels result/diagnostic I/O,
zeroes secrets, proves Job active-zero as far as the cleanup wall permits,
emits no semantic terminal object, and exits host failure. A successor
controller must classify the durable consumed dispatch through a fresh
observation-only launch.
If the parent remains live but the result pipe is lost, the supervisor freezes
one `pontius-result-peer-loss-fact-v1` containing the exact accepted prefix,
message sequence, frame stage, controller origin, and write error. That cause
is distinct from parent exit and channel loss and emits no further semantic
wrapper. Every process exit is selected by the frozen
`pontius-supervisor-exit-code-map-v1`; the controller's transport receipt binds
the complete `pontius-supervisor-exit-result-v1`, not an untyped scalar code.

## Sealed run capsule

The supervisor creates one nonce-named, ordinary, non-reparse capsule directory
for the selected role. It uses create-new semantics and handle-relative checks
for every child path. The capsule contains exactly the projection, bootstrap
executable, role ZIP, private native population, and, only for publisher or
integrator, the one projected askpass adapter. It contains no other ordinary
object; builder contains no adapter path or bytes.

The supervisor copies only from authorization-pinned source handles. It reopens
each destination with sharing equivalent to `FileShare.Read`, checks final path,
run-local `FileIdInfo`, size, and SHA-256, and retains every handle. It retains
the capsule and native-directory handles without delete sharing. The capsule's
DACL grants the preregistered AppContainer package SID only the read and execute
access it needs and no write, delete, ownership, or ACL-changing access.

The supervisor materializes and retains the complete
`pontius-runtime-capsule-population-v1`. The supervisor performs an exact
population check before creating the process.
The bootstrap independently repeats it before any private load. A new entry
after either check is never a search candidate: Python searches only the held
ZIP and private images load only by exact absolute path. The next population
check still records the addition as a sticky violation. This is the precise
meaning of `sealed` here; the design does not claim that a directory handle
alone prevents a trusted controller identity from adding a file.

The bootstrap executable mapped by `CreateProcessW` is the held capsule copy.
No code executes from the source installation, a Git working tree, or the
working directory.

## Exact bootstrap launch

`pontius-worker-launch-attempt-v1` has exactly
`all_application_packages_policy`, `application_name`,
`attribute_list_size_bytes`, `child_process_policy`, `command_line`,
`creation_flags`, `current_directory`, `environment`, `inherit_handles`,
`inherited_handles`, `mitigation_policy`, `process_security_attributes`,
`schema`, `security_capabilities`, `startup_info`, and
`thread_security_attributes`. Application name is the held capsule bootstrap
final path; command line and both security-attribute pointers are null; creation
flags and aggregate are exact `CREATE_SUSPENDED`,
`CREATE_UNICODE_ENVIRONMENT`, `EXTENDED_STARTUPINFO_PRESENT` / `00080404`;
current directory and environment are the complete dispatch objects; and
inherit handles is true. Inherited handles are exactly the first five reduced
HANDLE-policy rows in that order.

`startup_info` contains every `STARTUPINFOEXW` base field. On AMD64 `cb=112`,
`dwFlags=00000100` (`STARTF_USESTDHANDLES`), standard handles equal the first
three policy rows, every unused scalar is zero, every unused pointer is null,
`cbReserved2=0`, and `lpReserved2=null`. The attribute count is exact five.
`attribute_list_size_bytes` is the nonzero run-local size returned by
`InitializeProcThreadAttributeList(NULL,5,0,&size)` and the owner allocates and
initializes exactly that size. Attribute-list addresses are never canonical.
The five `UpdateProcThreadAttribute` calls occur in this order:

| Ordinal | Key | Value size and semantic value |
| ---: | --- | --- |
| 1 | `00020002` HANDLE_LIST | 40 bytes; exact five worker handles in policy order |
| 2 | `00020007` MITIGATION_POLICY | 8 bytes; one little-endian DWORD64 `1110001111111001` |
| 3 | `00020009` SECURITY_CAPABILITIES | 24-byte AMD64 struct; semantic object below |
| 4 | `0002000e` CHILD_PROCESS_POLICY | 4-byte DWORD `00000001` |
| 5 | `0002000f` ALL_APPLICATION_PACKAGES_POLICY | 4-byte DWORD `00000001` |

The canonical security-capabilities object records semantic package SID, empty
capability array, count zero, reserved zero, and value size 24, never the run-
local pointer bytes. Every pointed-to buffer remains alive through the actual
call. There is no parent-process, Job-list, pseudoconsole, policy-two, SEHOP, or
unknown attribute. The actual `CreateProcessW` call preimage equals this object
field-for-field, after which the list is deleted during cleanup.

`pontius-worker-launch-result-v1` has exactly `attempt`, `launch_state`,
`process_create_called`, `process_lifecycle`, `schema`, and
`win32_error_hex`. State is `NOT_ATTEMPTED`, `CREATE_FAILED`, or
`CREATE_SUCCEEDED`. Not-attempted has false called and null error/lifecycle.
Create-failed has true called, nonzero eight-lowercase-hex-digit error, and null
lifecycle. Create-succeeded has true called, null error, and the complete worker
lifecycle, including assignment-failed and never-resumed branches. Every
failure cleanup, final revalidation, and runtime evidence carries this complete
attempt/result; a digest-only success or omitted failed call is invalid.

The trusted supervisor creates the worker as the preregistered AppContainer in
the initial `CreateProcessW` call. `PROC_THREAD_ATTRIBUTE_SECURITY_CAPABILITIES`
contains the exact package SID, a null capability pointer, and capability count
zero. The worker therefore has the AppContainer token before the first
bootstrap instruction; conversion after entry is forbidden.

`lpApplicationName` is the exact held capsule bootstrap path and
`lpCommandLine` is null. The bootstrap has no CRT argv parser and receives no
path, role, operation, secret, or option through a command line. The current
directory is the exact held `WORKER`-scope
`pontius-launch-directory-projection-v1` from the dispatch. Its sole
`RUN_DIRECTORY` is unique, created new, ordinary, non-reparse, and empty at
seal; it is never P, H, a Git directory, the capsule, or the installed Python
root. Its dispatch nonce equals the launch and both process ordinals are null.

The new Unicode environment contains exactly:

```text
LANG=C
LC_ALL=C
SYSTEMROOT=C:\Windows
TEMP=<exact empty run directory>
TMP=<exact empty run directory>
WINDIR=C:\Windows
```

These six entries, in the displayed order, form the complete
`pontius-environment-block-v1` embedded in the dispatch. Names are their exact
uppercase ASCII spellings and unique under Windows ordinal case-insensitive
comparison. The supervisor reconstructs `name=value` plus one U+0000 per row
and one final U+0000, encodes that exact sequence as UTF-16LE without a BOM,
and passes those bytes to `CreateProcessW`. Byte count and SHA-256 equal the
object. No parent environment entry, hidden drive-current-directory entry,
alternate case, or extra terminator is inherited or synthesized.

Creation flags and the five ordered attributes are the exact launch-attempt
object above. The supervisor assigns the
suspended process to its one-process job, closes child-side handle duplicates,
and then resumes the one primary thread. Every successful creation immediately
opens a `pontius-process-lifecycle-v1` row from the retained process and primary-
thread handles. Failure before successful Job assignment terminates that exact
suspended process directly, waits for its signal, records its exit, and only
then closes the handles; an empty Job is not exit evidence. Failure after
assignment terminates the Job and requires both the direct process signal and
Job quiescence. No failed assignment can resume.

`CreateProcessW` receives exact `bInheritHandles=TRUE`. Every handle named in
`PROC_THREAD_ATTRIBUTE_HANDLE_LIST` is created inheritable for that launch, and
every other source handle is non-inheritable. The explicit list and this boolean
are one invariant; either mismatch refuses before resume.
Before emitting `RUNTIME_LOCKED`, the bootstrap clears `HANDLE_FLAG_INHERIT` on
its five inherited handles and queries each worker-side flag as false. Closing
or clearing only the parent-side duplicate is not evidence.
The bootstrap-control member is the worker-read end of the complete
`pontius-bootstrap-control-channel-binding-v1`. Its handle-list ordinal,
access, assigned-worker binding, dispatch, nonce, and per-frame cap are
immutable pre-send facts. Admission and attach transfer results carry actual
write, parse, EOF, and close evidence.

The supervisor retains the complete accepted `pontius-launch-dispatch-v1`
owner-side. After resume it sends exactly one canonical, length-framed
`pontius-bootstrap-source-admission-v1` over the bootstrap control pipe.
That object embeds the complete `pontius-planner-launch-view-v1`, runtime
projection, and capsule population and binds their source-set, authorization,
dispatch, process, environment, directory, role, and nonce relations. The
bootstrap strictly parses it, zeroes the raw frame buffer, independently opens
and retains every destination handle, and reproduces the complete capsule
population before any private load.

The embedded planner view contains role, operation, task, round, dispatch mode,
schedule variant, schedule identity, planner-row count, and authority/input
digests. It contains no repository projection, route selector, table instance,
endpoint, ref, credential, precondition, phase bundle, or owner-only input row.
No separate planner input or admission-extension message follows it. The sole
later bootstrap-control message is the mandatory post-lock broker attach.
Planner input bytes arrive later only through the typed
`READ_OPERATION_INPUT` owner request.
For the two local authority-ref operations, the retained dispatch additionally
contains the complete owner-only `pontius-local-ref-transaction-v1`; it is
absent from both planner views. The owner writes only its rerendered exact bytes
to the scheduled Git child's private stdin and records the actual accepted-byte
prefix, digest, EOF close, coordinate, and process binding in
`pontius-git-stdin-write-v1`.

## Deterministic role archive

Each role has one archive at an authorization-pinned absolute path. It contains
all role code, all copied pure shared code, all selected standard-library
source, and all admitted runtime data. It contains no `.pyc`, `.pyd`, DLL,
executable, symlink, reparse point, or path outside its own namespace.

The archive has these byte rules:

1. every member uses `ZIP_STORED`; compression and a zlib dependency are
   forbidden;
2. member names are canonical forward-slash ASCII paths in ascending byte
   order, with no absolute path, drive, dot segment, empty segment, backslash,
   NUL, control character, case-fold duplicate, or prefix collision;
3. local and central headers agree exactly, with no encryption, data
   descriptor, archive comment, member comment, or unapproved extra field;
4. timestamps, creator version, flags, permissions, and external attributes
   use one frozen deterministic value set;
5. CRC-32, uncompressed size, byte count, and SHA-256 reproduce the projection
   row for every member; and
6. the end record describes exactly the preregistered member count and central
   directory extent, with no prefix or suffix bytes.

The supervisor and bootstrap open the archive with sharing equivalent to
`FileShare.Read`. This is deliberate: the bootstrap and CPython may open the
same ZIP for reading while the retained handles deny ordinary write, delete,
and rename access. `FileShare.None` is invalid because it prevents CPython from
opening the archive. Allowing delete or write sharing is also invalid.

The bootstrap validates the ZIP independently before CPython initialization.
It retains its archive handle through job quiescence. CPython's only module
search entry is this exact held archive; no directory is a Python search path.
A file planted beside the archive, in the working directory, or under the base
installation cannot be selected.

## Native bootstrap and build provenance

The native bootstrap is a minimal Windows PE executable. Its reviewed source,
deterministic build recipe, compiler/linker identities, link map, PE audit, and
resulting executable digest are frozen before runtime review. Two independent
clean rebuilds must reproduce the exact executable bytes. A binary-only review
or a source review without matching rebuild evidence is insufficient.

The bootstrap PE must have:

- no static import of `python311.dll` or another private image;
- no TLS callback, delay import, CLR header, embedded script, or plug-in path;
- no current-directory, application-directory, `PATH`, registry, or package
  discovery code;
- a fixed, audited pre-entry import set whose names are only preregistered
  KnownDLL or API-set contracts and whose resolved images are trusted
  System32 rows; and
- one custom entry point with no dynamically linked C or C++ runtime startup.

The initial PE audit and clean-room launch must show that every image mapped
before the first bootstrap instruction is the bootstrap itself or the exact
KnownDLL and API-set closure resolved to allowed System32 images. The supervisor
opens and holds the bootstrap executable before process creation. The operating
system's mapping of that already held image and its System32 dependencies is
part of the trusted bootstrap boundary.

The bootstrap's first loader action calls `SetDefaultDllDirectories` with an
exact policy that excludes the application directory, current directory,
`PATH`, and user DLL directories. It also removes the legacy current-directory
route. No private image is loaded before both calls succeed.

Every private dependency is then preloaded by an authorization-pinned absolute
path. The bootstrap opens the exact file with sharing equivalent to
`FileShare.Read`, checks final path, 64-bit volume serial plus 128-bit
`FileIdInfo`, byte count, SHA-256, PE machine, import table, and delay-import
table, and retains the handle. This permits the Windows loader's read while
denying ordinary write, delete, and rename access. It loads the file with
`LoadLibraryExW` under a System32-only dependency policy. It never uses a
basename, relative path, changed working directory, added DLL directory, or
`LOAD_WITH_ALTERED_SEARCH_PATH`.

All private import and delay-import targets must already be loaded by their
exact absolute paths or resolve to the exact System32 allowlist. This includes
the CPython DLL, private VCRUNTIME copies if selected, native Python extensions,
and every private dependency of those extensions. A private name that would
require directory search refuses the projection before launch.

`python311.dll` is loaded only after the policy and its prerequisite closure
are established. Selected native extensions are loaded by exact path after the
CPython DLL and before `RUNTIME_LOCKED`. Their module initialization occurs only
through the preregistered CPython import sequence. No native directory is added
to `sys.path`.

For each admitted `.pyd`, the bootstrap resolves exactly its preregistered
`PyInit_*` export and registers that function with `PyImport_AppendInittab`
before CPython initialization. The native channel implemented by the bootstrap
is registered the same way. CPython therefore sees these extensions as a
closed builtin set and never performs a directory search for them. A missing,
extra, forwarded, ambiguously encoded, or wrong-address initialization export
refuses before `Py_InitializeFromConfig`.

The bootstrap registers a native DLL-notification observer before the first
private load. It also takes a stable, complete loaded-image enumeration after
each preload phase, immediately before `RUNTIME_LOCKED`, before and after every
broker exchange, and at shutdown. Each sample must equal the projection's
private image set plus its exact System32 set. A notification or sample outside
that set sets a sticky runtime violation.

Image observation is secondary evidence. It does not make an unexpected
`DllMain` safe after execution. The primary exclusion is the closed preload
graph, absolute-path loads, System32-only dependency policy, and absence of a
late load route.

## Isolated CPython initialization

The bootstrap resolves the required CPython C API only from the held
`python311.dll`. It installs the native audit hook before interpreter
initialization, then uses `PyPreConfig_InitIsolatedConfig`,
`Py_PreInitialize`, `PyConfig_InitIsolatedConfig`, and
`Py_InitializeFromConfig`. It must check every returned `PyStatus` and preserve
the first failure.

The frozen `PyPreConfig` and `PyConfig` projections include these required exact
rows within the complete field population:

```text
isolated = 1
use_environment = 0
user_site_directory = 0
site_import = 0
safe_path = 1
write_bytecode = 0
parse_argv = 0
install_signal_handlers = 0
optimization_level = 0
dev_mode = 0
tracemalloc = 0
faulthandler = 0
utf8_mode = 1
module_search_paths_set = 1
module_search_paths = [<exact role archive>]
```

Every remaining field whose default could consult the environment, executable
location, registry, user profile, current directory, locale, or clock is set
explicitly or proven inert for CPython `3.11.15`. The projection fixes the
complete initialized values, including program name, executable, home,
prefixes, filesystem encoding and error mode, standard-stream policy, hash
seed policy, warning options, xoptions, and integer-string limit. No value is
derived from `python.exe`, `_pth`, `pyvenv.cfg`, `site`, `PYTHON*`, or a parent
environment variable.

The process environment is newly constructed and contains only the exact
values required by the bootstrap and trusted Windows APIs. `PATH`, `PATHEXT`,
`HOME`, `USERPROFILE`, `APPDATA`, `LOCALAPPDATA`, every `PYTHON*`, every
`GIT_*`, proxy, TLS, askpass, editor, pager, and shell variable is absent.
`TEMP` and `TMP` name one unique, empty, non-reparse run directory. Python has
no module search or data-read route to that directory and writes no bytecode.

Initialization imports only the exact bootstrap modules required by CPython.
The role then imports, in a frozen order, every pure module and native extension
it may use. The bootstrap checks the exact module-name-to-origin relation after
each phase. Builtin and frozen modules use a closed name set. Every other module
maps to one exact archive member or preloaded native row. Namespace packages,
path hooks, editable installs, zip prefixes, and dynamically generated module
origins are forbidden.

The native audit policy allows pre-lock reads only from the held role archive
and exact private images. It denies registry-based path discovery, profiles,
startup files, user configuration, subprocesses, sockets, dynamic-code loading,
and unlisted filesystem data. Unknown or malformed security-relevant audit
events refuse. The exact event and argument predicate table is part of the
role projection and is exercised before acceptance.

## `RUNTIME_LOCKED`

The runtime may enter `RUNTIME_LOCKED` only after all of these facts are true:

1. the supervisor and bootstrap independently validated and retained every
   bootstrap, projection, archive, native, and authorization source handle;
2. the bootstrap's loader policy is installed and cannot be widened by the
   admitted source set;
3. the exact private and System32 image populations are loaded and stable;
4. CPython process facts, `PyConfig`, `sys.flags`, `sys.path`, environment,
   module origins, archive population, native rows, and data rows match the
   selected projection;
5. every allowed module is already in `sys.modules` and initialized;
6. the interpreter has one application thread and no admitted module exposes
   process launch, raw handle duplication, FFI, socket, dynamic loader, package
   discovery, or unrestricted file access; and
7. the role has performed no repository, Git, credential, network, or other
   authority operation.

At the transition, the bootstrap replaces Python import machinery with a guard
that permits access only to the already initialized exact module objects.
Calls that would import, reload, replace, or remove a module refuse. The native
audit hook changes to the post-lock policy: filesystem opens, runtime-data
reads, imports, native loads, executable mappings, subprocesses, sockets,
registry access, dynamic code, and process-handle operations all refuse unless
they are an exact internal action of the native channel described below.

The runtime ZIP and native handles remain open even though further imports and
loads are forbidden. This permits final rehash and makes ordinary write,
delete, or rename attempts fail throughout the operation.

The bootstrap emits one length-framed canonical ASCII JSON attestation with
schema `pontius-runtime-locked-v2`. Its root binds exactly:

| Key | Type |
| --- | --- |
| `appcontainer_capability_set_sha256` | `sha256` |
| `appcontainer_package_sid` | frozen SID string |
| `appcontainer_setup_sha256` | `sha256` |
| `archive_sha256` | `sha256` |
| `audit_policy_sha256` | `sha256` |
| `authorization_sha256` | `sha256` |
| `authority_channel_absent` | exact `true` |
| `bootstrap_sha256` | `sha256` |
| `bootstrap_admission_transfer_sha256` | `sha256` |
| `bootstrap_control_channel_binding_sha256` | `sha256` |
| `broker_projection_sha256` | `sha256` |
| `capsule_population_sha256` | `sha256` |
| `launch_nonce` | `nonce` |
| `loaded_image_set_sha256` | `sha256` |
| `loaded_module_set_sha256` | `sha256` |
| `native_set_sha256` | `sha256` |
| `planner_launch_view_sha256` | `sha256` |
| `process_policy_sha256` | `sha256` |
| `projection_byte_count` | `positive_count` |
| `projection_sha256` | `sha256` |
| `pyconfig_sha256` | `sha256` |
| `role` | selected child role |
| `runtime_handles_held` | exact `true` |
| `schema` | exact `pontius-runtime-locked-v2` |
| `source_admission_sha256` | `sha256` |
| `source_set_sha256` | `sha256` |
| `sticky_violation_clear` | exact `true` |
| `system_image_set_sha256` | `sha256` |

The capsule and source-admission digests equal their complete accepted objects.
The bootstrap-control digest equals the immutable binding nested in the source
admission. The admission-transfer digest equals the complete
`pontius-bootstrap-admission-transfer-result-v1` at `SENT_ACCEPTED` and binds
that same admission and channel. The supervisor validates the frame, exact process
identity, AppContainer token, package SID, empty capability set, job, handles,
projection, and nonce. Malformed, partial, oversized, duplicate-key,
extra-byte, wrong-process, wrong-role, or wrong-digest input terminates the
job. A Python-authored statement is never sufficient without the supervisor's
independent process and handle checks.
The planner-launch-view digest equals the complete safe view received from the
supervisor. The full dispatch, selector, repository, and owner-only input
projection are absent from the process address space and cannot be reconstructed
from that digest.

The bootstrap sends the attestation over its distinct one-frame
`pontius-runtime-attestation-channel-binding-v1`. The complete transfer result
must be `SENT_ACCEPTED` with exact frame bytes and buffer zeroing. Its channel
remains open for the later attach acknowledgement; attestation acceptance alone
does not close either endpoint or establish `BROKER_ATTACHED`. A digest without
that transport result has no lock authority.

Only after accepting this transfer does the supervisor create the private
broker channel and duplicate its client handle into the bootstrap process.
The handle is not inherited at process creation and does not exist in the
Python process before the lock. The supervisor sends exactly one
`pontius-bootstrap-broker-attach-v1` as its second and final message on the
bootstrap control pipe. After binding the duplicated handle, the native
bootstrap sends exactly one `pontius-bootstrap-broker-attach-ack-v1` on the
still-open attestation channel. The ACK repeats the launch, dispatch, handle,
and attach digests. Only the accepted ACK permits terminal control state
`ATTACHED`; the resulting
`pontius-runtime-attestation-channel-terminal-result-v1` then proves exact EOF,
buffer zeroing, and both endpoints closed. Python never receives the raw numeric handle.
The process-policy leaf nevertheless contains exactly one `BROKER_CHANNEL`
row with noninheritable exact access. Live state for that row is absent through
the accepted `RUNTIME_LOCKED` attestation, present exactly once after validated
duplication in phase `BROKER_ATTACHED`, and absent again after channel close
before `FINALIZED`. Missing, early, duplicate, inheritable, wrong-access, or
wrong-target broker-channel state is sticky failure.

## Dispatch mode and bounded child schedule

Before consuming a dispatch, the supervisor canonicalizes and holds the
complete owner-only route selector. Its schema, count, and SHA-256 must equal
the authorization and dispatch. Its role-applicable stable selectors must equal
the held role table; builder does not validate endpoint, main, or review-output
slots absent from its `OFFLINE` table. Packet, cold-input, receipt, or intent equality
is additionally required only when that operation's frozen input population
carries the corresponding object; later operations inherit it through the
exact validated authority chain. A missing, wrong-route, stale, or mismatched
object refuses before registry consumption, repository open, credential
reservation, or process creation.
Stable full refs follow their selector-pinned or route-derived class. An
authorization-derived attempt ref has only a validated table descriptor and,
for rehearsal, an equal selector descriptor at this point. The supervisor
derives its full value from the already complete external authorization digest
and requires that one value through observation, ref-update, argv, refspec, and
mutation evidence. Before any campaign launch, it also proves the selector has
exactly one intent/result descriptor pair for every selected integration case
and task binding and no extra pair. A caller, preregistration, or selector cannot
supply a full ref.

Before any role process is created, the supervisor validates the complete
ACL-sealed consumed-dispatch registry and durably creates the exact record for
this launch with create-new, write-through, flush, close, reopen, reparse, and
held-handle ordering. Successful creation of a canonical anchor name spends
that plan-and-nonce key before the first content byte. An existing canonical
name therefore refuses that key even if a crash left empty, partial, unreadable,
or noncanonical content; it does not block unrelated keys. An out-of-grammar or
case-colliding name, nonregular or reparse entry, directory or ACL mismatch, or
ambiguous enumeration blocks every launch. No process starts until the new
record's complete bytes survive reopen validation. Crash rehearsal covers
create, every write boundary, flush, close, reopen, and process start. Anchors
and complete records are permanent; an in-memory set or terminal receipt cannot
replace them.

One one-use outer dispatch creates the role process and binds its complete
ordered owner-child schedule program. Static steps and bounded-repeat groups
have fixed request and argv grammars; repeat populations derive only from
complete validated inventories or deterministic raw-object walk state. The
AppContainer worker never creates a child.
Each nonowner expanded step represents exactly one root Git process and returns
only facts obtainable from that one process or independently recomputed from
its declared raw bytes. Mutation and fetch steps return lifecycle completion,
then distinct query and raw-read steps establish postconditions. Aggregate
classifiers, stable-main observations, and receipts are owner-internal
no-process steps over the complete prior transcript. No expanded row hides a
child sub-schedule or treats a mutation's output as its own postcondition.
Only the trusted owner may start the scheduled root Git process at a frozen step
ordinal. The pinned remote helper and askpass adapter are admitted Git
descendants in a separate no-breakaway operation Job; their executable and
image graph is frozen and revalidated. Every actual network child has its own
`(dispatch nonce, step ordinal, repeat ordinal)` broker session and cannot reuse
another child's pipe or credential response.
Before starting that step's root Git process, the trusted broker validates the
bound session template, generates the fresh pipe nonce, creates the restricted
listening pipe, and retains a canonical reservation. The owner creates and
holds the coordinate's complete `GIT_CHILD` launch-directory projection, then
builds the exact `pontius-environment-block-v1` from that projection, the
selected grammar, and, only for a network row, the reservation. It reconstructs
the exact UTF-16LE block bytes and starts Git suspended with that block and the
held run directory as current directory. `CreateProcessW` uses exactly
`CREATE_SUSPENDED | CREATE_UNICODE_ENVIRONMENT |
EXTENDED_STARTUPINFO_PRESENT`, the nonnull held executable path, the frozen
`pontius-windows-command-line-v1` mutable buffer, and
`bInheritHandles=TRUE` with the explicit handle list. Argument one and
`lpApplicationName` equal the same held executable final path. The owner keeps a
pristine copy and independently rerenders the exact argument array. The
complete coordinate-keyed rows
form `pontius-git-environment-set-v1`; its dispatch digest equals this launch
and it bijects with every prepared Git-process coordinate. Assigned
`CREATE_SUCCEEDED` rows map expanded schedule rows; an unassigned, create-
failed, or not-attempted terminal boundary remains explicit with its exact
lifecycle nullability and launch-attempt fact. Only after a held
process identity and Job assignment exist does the broker complete the process-
bound session. Reservation, environment block, directory projection, template,
selected table, process, and Job equality are all required before resume. If a
successful reservation terminates before that concrete session exists, the
owner closes the listener, zeroes any credential buffer, and records the exact
tagged pre-session result; process creation or Job-assignment failure cannot
erase the reservation lifecycle.
That process-bound session is pre-resume binding, not redemption evidence. On
terminal close the broker records every actual connection to the retained pipe
instance, including the exact named-pipe client-PID query, held process handle,
creation/image identity, liveness, schedule-Job membership, and immediate
pre-write recheck, exact write/monitored-flush/disconnect/close sequencing,
adapter signal/exit, plus responses and broker-buffer zeroing, and
terminal reason in the schema appendix's
secret-free session result. Schedule execution and cleanup bind the complete
reservation-terminal set, with exactly one tagged session or pre-session result
per successful reservation. Successful runtime evidence permits only session
results and records every concrete child by static step and repeat ordinal. A
missing, extra, skipped, over-cap, unclosed, unzeroed, or non-one-response
success child invalidates the launch. Negative terminal results remain complete
failure evidence and are bound by the refusal when they can be produced.

Here the recorded request count means completed connections to the exact
retained server instance, including a connection whose PID query, process open,
or identity binding fails; it is not a client-authored message. The server pipe
is outbound and the adapter end is read-only. The owner obtains the connected
PID only from `GetNamedPipeClientProcessId` on that held instance and holds the
resulting process handle through response and close. A wrong pipe coordinate
never reaches the held server; a substituted client process or an operation,
table, template, environment, or route mismatch is sticky broker failure. Only
complete bounded push porcelain becomes typed
parsed status. A network process that returns naturally before the active
deadline later receives an immutable transport outcome from lifecycle
completion plus its completed scheduled fresh observation; the schedule selects
the first non-success outcome, or its final outcome when all succeed. A process
terminated by a wall, cancellation, or other terminal cause has no invented
same-dispatch observation or outcome and requires a later fresh
`OBSERVATION_ONLY` dispatch. Any post-terminal reconciliation remains a
separate `pontius-post-terminal-reconciliation-v1` carrying both unequal
dispatch and authorization identities.

An `OBSERVATION_ONLY` dispatch loads a table with no authority-object write,
authority-ref write, or push request. It may always be issued for an exact
frozen state equation, including after coordinator death. If remote graph bytes
are needed, the owner creates a new dispatch-owned no-ref scratch object
database outside the held authority repository; that residue cannot become an
authority input. A `MUTATION_ATTEMPT` dispatch binds a fresh observation and
loads the one exact precondition-derived mutation variant. It permits at most
one declared local recovery-ref transaction and one remote transition, with a
fresh decisive remote observation between them. A terminal exact observation
closes through the observation-only envelope and never starts a mutation
variant. For integration, absent and exact local-attempt states select distinct
closed variants, so no scheduled step is silently skipped.

The stable transition authorization contains expected selectors and immutable
inputs but no observation, operation-precondition, dispatch, or terminal-result
digest. Both dispatch modes may therefore bind the same authorization without a
bootstrap cycle. Only `MUTATION_ATTEMPT` binds the fresh observation tuple in
its operation precondition.

## Role-specific typed-operation broker

The held role projection contains one exact `(module, callable)` entry for each
role operation. After `BROKER_ATTACHED`, trusted native bootstrap selects the
dispatch operation's entry, invokes it once, and passes the complete
`pontius-planner-launch-view-v1` as its sole argument. Python cannot select an
entry point or infer an operation from input presence, including an operation
with zero planner rows.

The bootstrap exposes one built-in channel function to Python. It accepts a
closed owner-request identifier and one canonical payload conforming to that
request's frozen schema. Native code constructs the exact
`pontius-owner-request-v1` envelope and validates the matching
`pontius-owner-reply-v1` envelope using the schema appendix's typed one-byte
kind and eight-byte little-endian framing. Large raw objects use only the
bounded binary-chunk kind under a complete canonical stream descriptor; they
are hashed and parsed incrementally and are never copied into runtime evidence.
The function exposes no read, write, connect, spawn, handle, path,
URL, refspec, environment, or argv primitive. Before sending a request, the
native function checks the sticky runtime flag, loaded images, module set,
thread count, process policy, contiguous sequence, predecessor-reply digest,
payload size, role, transition operation, and exact next schedule coordinate.
It performs the same checks after the single reply.

The broker loads exactly one trusted-dispatch-selected role-table instance
before it accepts the channel. The common broker engine implements framing,
canonical decoding, identity checks, and process ownership. It has no caller-
supplied command API. The selected table, its role-operation set, its
operation-schedule set, and the held runtime projection together map each
transition operation and owner-request identifier to one complete authorization
grammar, precondition grammar, request sequence, executable, argv grammar,
environment, endpoint, repository, ref, result grammar, and reconciliation
rule. The table
repeats both set digests; the set members equal the selected role source
projection's operation IDs, owner-request IDs, and schedule identities. No
omitted field may be supplied or inferred at runtime.
The table may resolve an endpoint, repository, ref, or output slot only after
the held route selector names the same role-applicable selector and derived ref
coordinate. A route label, operation name, or packet path alone has no
selection authority.

The three role-table families have disjoint operation identifier sets. The
builder family contains no URL, remote name, credential mode, fetch,
`QUERY_REMOTE_REFS`, push, main-ref, or output-ref operation. It retains
`QUERY_LOCAL_REFS` solely as the authority-database observation primitive for
tuple classification. It may contain the closed
`BUILD_REVIEW_OUTPUT` object-construction operation defined by the schema; that
operation has no network or ref authority. The publisher family cannot
construct local authority or main commits. The integrator family contains the
closed object-only `FETCH_MAIN_INPUTS` operation but cannot publish the
candidate pair or adopt candidate objects. Cross-role requests, unknown
identifiers, extra fields, and mismatched predecessor facts refuse before
opening a repository, Git, credential, or network path.

Publisher and integrator each have production and rehearsal literal-table
instances. Both instances share identical engine, operation grammar, and
schedule identities. Stable slot IDs pair their endpoint, repository, ref-
derivation prefix, public-account, and credential-audience fields. A table
contains no future round's full ref. The owner derives that value from the
selected table's closed derivation grammar plus the complete held route
selector and requires equality with its exact coordinate. The rehearsal
instance substitutes only the stable coordinates in the authorized literal delta and
structurally lacks every production capability literal. Every unequal table
leaf is named once by that delta, and every other leaf is equal. Trusted
dispatch selects and holds one instance before child attachment; the child
cannot select or switch it. The four-role source-projection set binds every
accepted instance and the enumerated literal delta.
The selector's fresh pre-production and pre-rehearsal server-capability
observations and both paired endpoint rows carry the same complete capability-
class digest. Table similarity or a capability label cannot establish it; every
rehearsal case later performs a fresh post-case observation.

The in-process broker engine and every accepted table instance are separately
reviewed runtime-owner sources.
The role projection binds their complete source population, binary or script
identity, role table, Git identity where applicable, and allowed descendant
image population. Python cannot choose another table or broker. A common table
loader may accept only the already held table handle selected by the supervisor;
it accepts no path or role selector from the child.

The owner validates its live supervisor process image and held executable
identity against the broker engine's `WINDOWS_OWNER` source entry before it
consumes a dispatch. The broker subsystem has no `CreateProcessW` call, process
binding, executable path, Job, token, environment, stdio, inherited handle, or
quiescence row of its own. The only Job kinds remain `ROLE_PROCESS` and
`SCHEDULE_STEP`; every Git root and admitted helper or adapter descendant lives
in its one no-breakaway schedule Job.

Only after selector, table, template, and operation checks does the controller-
authorized parent secret channel place one short-lived token in zeroizable
supervisor memory. The sole intentional secret path is parent secret channel to
that buffer, broker pipe, verified adapter buffer, and the adapter's private
askpass stdout consumed by the scheduled Git process for HTTP authentication.
The rehearsal server accepts that secret only through one mutually
authenticated control session with the exact ordered
`pontius-server-secret-arm-v1`, ACK, optional CONSUMED, and DISARMED objects.
ARM and the complete lifecycle carry one tagged
`pontius-server-secret-coordinate-v1`. A network step with a fault fixture is
`FAULT_BOUND` to its reservation and nonce. A network step without a fixture is
`SESSION_BOUND` to its broker session, dispatch, request nonce, task binding,
and step, with both fault fields null. Offline steps carry no lifecycle.
Every ACK, CONSUMED, and DISARMED payload is bound by a complete
`pontius-authenticated-server-artifact-v1`, whose independent verifier validates
the domain-separated signature under the certificate and TLS binding from the
mutually authenticated control session. The complete
`pontius-server-secret-lifecycle-v1` exists for every rehearsal network step.
An accepted request requires exact `ARM`, `ACK`, `CONSUMED`, `DISARMED` and use
state `CONSUMED_ONCE`; a request never accepted requires authenticated
`ARM`, `ACK`, `DISARMED`, use state `UNCONSUMED`, and zero remaining uses. A
client-only claim or matching response without that lifecycle is failure.
The public askpass prompt is rendered by the frozen
`pontius-askpass-prompt-grammar-v1`: exact UTF-8 `Password for '`, the selected
HTTPS endpoint with its selected public account percent-encoded as userinfo,
then exact `': `. The fixed Git prefix supplies that account only through
`credential.username`. A username prompt, other endpoint/account, extra byte,
or second invocation refuses before secret release.
The broker pipe uses the schema appendix's exact four-byte little-endian length
prefix and bounded byte-pipe read-to-EOF algorithm. Partial or coalesced reads
cannot select a different payload; early EOF, invalid length, trailing bytes,
second frame, or deadline expiry after a prefix returns no response and zeroes
every partial secret buffer.
The server `WriteFile` is an event-backed overlapped operation cancelled with
`CancelIoEx`; `FlushFileBuffers` runs only on its retained blocking thread and
is cancelled with `CancelSynchronousIo`. Both operations produce complete
`pontius-broker-cancellable-io-v1` evidence bound to the exact reservation,
session, retained server-handle identity, operation nonce, owner deadline, and
event or complete `pontius-broker-flush-thread-binding-v1`. A write also carries
complete `pontius-broker-overlapped-write-terminal-v1` evidence for the exact
cancel return/error, event wait, `GetOverlappedResult` outcome, byte count, and
OVERLAPPED retirement. A flush carries the complete
`pontius-broker-flush-thread-terminal-v1`, whose exact wait result, signal
observation, cancellation return/error, flush result/error, thread exit,
completed join, and successful handle close prove the retained thread is gone
before disconnect or close. A
completed write without completed flush is never redemption.
Secret bytes never enter Python, argv, environment, files, inherited handles,
supervisor-captured diagnostics, logs, exceptions, or canonical evidence. The
adapter receives only public nonce and pipe routing before its one possible
response, after exact process-image and schedule-Job membership checks. Adapter
and Git termination, pipe close, and broker-buffer zeroization are required in
the terminal session result; a reservation that ends before a session exists
requires the corresponding secret-free pre-session result.

After the single safe launch view, every additional byte eligible to reach
Python arrives only as a typed reply from a `delivery=PLANNER` held row or a
closed capability-safe owner result. Owner-only bytes never reach Python. All
proposed object bytes and typed operation requests leave through the channel.
This keeps working-directory files, repository paths, Git config, credentials,
and remote transport outside the Python runtime boundary.

The channel is not a sandbox for malicious reviewed role code. Its claim is
that the exact admitted role code has only a closed, independently validated
operation interface. The broker remains responsible for validating every
request as hostile input.

## Process and handle containment

The AppContainer profile is a separately governed setup artifact. One frozen
setup authorization calls `CreateAppContainerProfile` once, records its profile
name, derived package SID, owner, empty capability set, profile-directory
identity, and ACL templates, and then ends. An independent verifier reproduces
the SID using `DeriveAppContainerSidFromAppContainerName`. Creation,
replacement, deletion, ACL repair, or capability mutation is forbidden during
an authority-tool launch. A missing profile, changed package SID, nonempty
capability set, or changed setup receipt blocks launch. The live supervisor may
validate the profile; it may not provision or normalize it.

The controller and the identity that owns this fixed profile remain trusted.
The design makes no claim against either one changing the profile or its ACLs
outside the protocol.

The supervisor creates the bootstrap suspended with an explicit
`PROC_THREAD_ATTRIBUTE_HANDLE_LIST`. Initial inherited handles are limited to
stdin at EOF, bounded stdout, bounded stderr, the bootstrap control pipe, and
the runtime-attestation pipe. No repository, Git, credential, token, authority,
file-source, directory, job, process, thread, or broker handle is inherited.

Every retained repository, capsule, launch, run, scratch, profile, and ancestor
directory carries a complete `pontius-directory-open-fact-v1` from the same
handle as its path identity. Exact access is directory-list, read-attributes,
read-control, and synchronize; share mode allows read and write but not delete;
flags include backup-semantics and open-reparse-point; inheritance is false;
and queried granted access is `00120081`. Created nonce roots use `CREATE_NEW`;
admitted ancestors and repository roots use `OPEN_EXISTING`.
Each repository projection additionally carries one complete
`pontius-repository-directory-ancestor-chain-v1` per retained repository
directory. Its same-handle rows run from the volume root through the target,
prove every reparse tag null, and remain held through Job active-zero and final
revalidation; a root-only directory fact cannot substitute.

Every named pipe uses a nonce-qualified name under the exact
`\\.\pipe\LOCAL\` AppContainer namespace and an explicit security descriptor.
Named broker-channel and askpass pipes grant only SYSTEM and the exact
controller owner; neither grants the package SID, All Application Packages, or
a wildcard principal. The supervisor transfers the reduced broker client only
by handle duplication after worker identity and runtime lock. The capsule and
its projection, archive, native, and data children use the distinct capsule ACL
template whose sole worker principal is the exact package SID with read/execute
rights. A changed SID, descriptor byte, effective-child descriptor, or endpoint
ACL-policy digest blocks process creation or attachment.

The bootstrap is assigned before resume to a job with kill-on-close, no
breakaway, active-process limit one, die-on-unhandled-exception, fixed memory
and CPU limits, and the headless UI restrictions proven compatible in
rehearsal. `PROC_THREAD_ATTRIBUTE_CHILD_PROCESS_POLICY` independently forbids
child creation. The process-creation mitigation policy must include the
accepted DEP, ASLR, strict-handle, heap-termination, extension-point, Win32k,
dynamic-code, remote-image, low-label-image, and System32-preference settings.
The final bitmasks and every exception are frozen from compatibility evidence;
this draft does not invent an unmeasured value.

The AppContainer security-capability list is empty: it receives no network,
private-network, broad-filesystem, device, or other requested capability SID.
That absence, the child-process policy, and the one-process no-breakaway job are
OS-enforced barriers at their documented Windows boundaries. All authorized
network and process work occurs in the trusted supervisor's in-process role
broker and its bounded schedule Jobs.

AppContainer is not claimed as a universal Windows read allowlist. Windows may
permit reads of OS resources, installed components, or objects readable by an
application package. Project-controlled read closure comes from the exact
bootstrap behavior, held capsule, single ZIP namespace, native audit policy,
and absence of a general file API in the reviewed role source. The projection
lists accepted OS/TCB read classes separately. A broader Windows read that
cannot influence the role may be a recorded nonclaim; a project-controlled or
influential unclassified read is a refusal.

The supervisor concurrently drains bounded stdout and stderr as bytes. After
durable consumed-dispatch revalidation it samples one QPC start and derives the
complete `pontius-owner-wall-deadline-v1` from the dispatch's calibrated active
wall and cleanup reserve. Authority work, role/child execution, and broker
activity stop at the active deadline. After any terminal cause, no new authority
process, network route, or mutation may start; termination, retained-fact
reconciliation, Job-zero, storage accounting, final revalidation, and refusal
assembly must finish before the later cleanup deadline. Missing it is host
failure with no semantic envelope. A pipe, child, retry, or phase never resets
either budget. The owner also enforces the CPU-time and memory limits. Every
limit must come from
frozen calibration evidence for that role, operation, mode, and variant.
Timeout, limit or
output overflow, cancellation, broker-subsystem failure, pipe ambiguity, or coordinator
death closes the job, proves active process count zero, and then revalidates
every retained runtime handle before classification.
At the first stdout or stderr count above its selected calibrated cap, the
supervisor records the stream, cap, first over-cap count, dispatch digest, and
limit-row digest in `pontius-output-cap-fact-v1`. That complete fact repeats in
process completion, cleanup termination under `SUPERVISOR_OUTPUT_COUNTER`, and
the outer `OUTPUT_CAP_EXCEEDED` refusal.
An owner-channel, broker-subsystem, session, or cancellation fault first blocks
new redemptions, closes listeners, terminates each affected schedule Job,
completes every producible reservation terminal result, zeroes every credential
buffer, and proves both schedule and role Jobs active-zero. A supervisor crash
cannot attest its own cleanup and emits no semantic envelope; external kill-on-
close containment and a later observation-only launch must classify authority.

## Final revalidation and receipts

The run-local population schemas are closed. `pontius-runtime-loaded-image-set-v1`
has exactly `images` and `schema`; an image row has exactly `basename`,
`file_identity`, `kind`, and `sha256`, with kind `PRIVATE` or `SYSTEM32`.
`pontius-runtime-loaded-module-set-v1` has exactly `modules` and `schema`; a
module row has exactly `archive_path`, `module_name`, `origin_kind`, and
`source_entry_sha256`, with origin `ARCHIVE`, `BUILTIN`, or `NATIVE` and null
fields only where that origin cannot have them. `FROZEN` is also allowed and
requires both archive path and source-entry digest null. Both arrays sort by their
case-folded logical name and are complete and unique.

`pontius-runtime-native-set-v1`, `pontius-runtime-source-set-v1`, and
`pontius-runtime-system-image-set-v1` each have exactly `rows` and `schema`.
Their rows are byte-for-byte the complete corresponding runtime-projection
population in its normative order; no digest-only or observed-prefix variant is
valid.

`pontius-appcontainer-live-observation-v1` has exactly `capability_sids`,
`integrity_level`, `less_privileged_appcontainer`, `package_sid`, `schema`,
`token_flags`, and `token_user_sid`.
Capabilities are the exact empty array; every other value comes from the held
process token and equals the accepted setup receipt and process policy.
`less_privileged_appcontainer` is the exact true result of
`GetTokenInformation(TokenIsLessPrivilegedAppContainer)` and is rechecked
before resume, at `RUNTIME_LOCKED`, and at final revalidation.

`pontius-runtime-handle-set-observation-v1` has exactly `handles` and `schema`.
A row has exactly `access_mask_hex`, `handle_role`, `runtime_phase`, `state`,
`target_identity_sha256`, `type`, and `worker_inheritable`. State is `ABSENT` or `PRESENT`;
target identity is null only when absent. Rows are the complete process-policy
handle-role population in frozen order, including absent phase-controlled
roles. Every present row equals the policy leaf's granted access and required
worker-side inheritance for that phase plus the live handle query; an extra
handle or unclassified handle refuses.

`pontius-runtime-capsule-adapter-observation-v1` has exactly `byte_count`,
`capsule_relative_path`, `file_identity`, `logical_name`, `schema`, `sha256`,
and `source_entry_sha256`. It is produced from the retained destination handle,
uses exact logical name `ASKPASS_ADAPTER` and path `pontius-askpass.exe`, and
reproduces every deterministic field of the runtime projection's adapter
component. Its file identity is the fresh run-local capsule identity, never the
source entry's identity.

`pontius-runtime-final-revalidation-core-v1` has exactly `appcontainer`,
`archive_sha256`, `askpass_adapter`, `audit_policy_sha256`,
`authority_input_projection_sha256`, `authorization_sha256`,
`bootstrap_admission_transfer`,
`bootstrap_control_terminal_result`, `bootstrap_source_admission`,
`broker_projection_sha256`, `capsule_population`,
`consumed_dispatch_record_sha256`, `controller_cancel_fact`,
`controller_channel_loss_fact`, `controller_session`, `dispatch_sha256`,
`git_environment_set`,
`job_binding_set`, `job_configured_limit_set`, `job_quiescence_set`,
`last_live_handle_set`,
`last_live_thread_count`, `last_runtime_phase`, `launch_input_projection_sha256`,
`loaded_image_set`, `loaded_module_set`, `native_set`,
`observation_scratch_projection_sha256`,
`observation_scratch_teardown`, `owner_wall_deadline`,
`planner_launch_view_sha256`, `process_lifecycle_set`, `process_policy_sha256`,
`projection_sha256`, `pyconfig_sha256`, `rehearsal_case_id`, `rehearsal_step_ordinal`,
`rehearsal_task_binding_id`, `repository_projection_sha256`,
`repository_storage_observation`,
`role_table_instance_sha256`, `route_selector`,
`runtime_attestation_transfer`, `runtime_locked_attestation_sha256`,
`schedule_execution_sha256`, `schema`, `source_set`,
`sticky_violation_state`,
`supervisor_preterminal_transcript`, `supervisor_source_admission`,
`system_image_set`, `unavailable_observations`, `worker_environment`,
`worker_launch_directory_projection`, and `worker_launch_result`.
Last runtime phase is `PROCESS_CREATED`, `JOB_ASSIGNED`, `RUNTIME_LOCKED`,
`BROKER_ATTACHED`, or `FINALIZED`. The nine set or live-observation
fields are complete canonical objects of the schemas above except for the
phase-null rules below.

`controller_session`, `supervisor_source_admission`, and `capsule_population`
are the complete public-session, selected-source, and capsule objects for this
launch. `supervisor_preterminal_transcript` is the complete accepted transcript
through the last control or nonterminal output message and excludes the final
terminal wrapper. `bootstrap_admission_transfer`,
`runtime_attestation_transfer`, and `bootstrap_control_terminal_result` are
complete phase-valid transfer results. `bootstrap_source_admission` is null
only when Job assignment failed before a pre-resume process binding existed;
the admission-transfer state is then `NOT_PREPARED`. At later phases it is the
complete prepared object. `RUNTIME_LOCKED` and later require admission
`SENT_ACCEPTED` plus attestation `SENT_ACCEPTED`. `BROKER_ATTACHED` and
`FINALIZED` additionally require control terminal state `ATTACHED`, a complete
accepted attach ACK, and a terminal attestation-channel result. Earlier
failure cleanup uses the exact not-sent, prefix, refused, channel-lost, or
early-close states and never invents a completed transfer. All complete objects
equal runtime evidence when success evidence exists.
`controller_cancel_fact` is null unless the first
terminal cause is authenticated controller cancellation; then it is the
complete fact and equals every cancellation-bearing process, broker, schedule,
and cleanup object.
`controller_channel_loss_fact` is null unless the first terminal cause is
controller-channel loss; then it is the complete fact and equals every
channel-loss-bearing process, broker, schedule, cleanup, and termination object.
It is mutually exclusive with the cancel fact.
`worker_launch_result` combines the dispatch's immutable
`worker_launch_attempt` with the later actual call outcome. Its application,
environment, directory, flags, five attributes, reduced handle list, and setup
policy equal that pre-call dispatch object; its Win32 error and lifecycle exist
only downstream of the consumed dispatch and equal every process/failure
carrier. Final revalidation rebuilds the complete call
preimage; querying only the successful token or process is insufficient.

`askpass_adapter` is `null` for builder and the complete capsule-adapter
observation for publisher and integrator in every phase. It equals the runtime-
evidence field byte-for-byte. A missing, extra, wrong-path, wrong-source,
changed-byte, or changed-destination-identity adapter is sticky failure.

`worker_environment` is the complete `pontius-environment-block-v1` object and
`worker_launch_directory_projection` is the complete
`pontius-launch-directory-projection-v1` object from the dispatch. The latter
has `WORKER` scope and the launch nonce. `git_environment_set` is the complete
`pontius-git-environment-set-v1` object for this dispatch. It has exactly one
coordinate-keyed row for each prepared Git-child environment, including a
create-failed or not-attempted terminal boundary, and no owner-only or worker
row. Its `CREATE_SUCCEEDED` subset bijects with created `GIT_CHILD` lifecycle
rows, including an unassigned terminal boundary. Each row repeats
the held directory projection, selected grammar, optional broker reservation,
and raw environment-block digest; assigned rows also equal schedule execution.
All three objects equal runtime evidence byte-for-byte; every raw
block is independently regenerated and rehashed during final revalidation.
Every Git row also rechecks the exact directory population and both retained
zero-byte `.netrc`/`_netrc` guard handles, including final path, FileIdInfo,
desired access, creation flags, inheritance state, share mode, byte count, and
hash. A guard closed before Job active-zero, a write-capable retained guard, or an
unexpected profile read is a sticky violation.

`owner_wall_deadline` is the complete
`pontius-owner-wall-deadline-v1` created once after durable dispatch
consumption. Its launch digest, selected limit-row digest, calibrated active
wall and cleanup reserve, QPC frequency, start, and two derived deadlines equal
runtime evidence and every broker reservation. The active timer remains the
only authority-work wall source. After a terminal cause, only nonmutating
cleanup may continue, before the later cleanup deadline. No phase, child, retry,
pipe, connect, or read resets either budget.

`schedule_execution_sha256` equals the associated complete execution or cleanup
prefix. For every Git-child process row, the owner retains the complete
`pontius-windows-command-line-v1` and its pristine raw buffer, rerenders the
arguments, and rechecks the UTF-16LE byte count and digest. That buffer is byte-
equal to the mutable copy supplied as `lpCommandLine`; an argv digest without
its preimage or a post-`CreateProcessW` buffer read cannot satisfy revalidation.
The WORKER row instead revalidates the held bootstrap
`lpApplicationName`, exact null `lpCommandLine`, current directory,
environment block, creation flags, inheritance Boolean, and explicit handle and
security-capability attributes. It never invents a command-line object.
For a local authority-ref transaction, the owner also rerenders the complete
`GIT_UPDATE_REF_CREATE_LF_V1` stream from the retained dispatch transaction,
rechecks its raw byte count and SHA-256, and requires byte equality with the
schedule execution's intended transaction. Success requires an actual
`COMPLETE` stdin-write fact with exact transaction, dispatch, coordinate,
process, bytes, and EOF equality. Failure revalidation instead preserves the
ABORTED execution's exact `PREFIX` or `DIVERGENT` fact with those same binding
equalities; `DIVERGENT` sets sticky violation and `PREFIX` remains clear only
absent another violation. Neither can authorize success. An altered transaction
control, delayed EOF, or cross-dispatch write fact prevents any semantic
success even when the intended refs subsequently classify exact.

`job_configured_limit_set` is the complete post-configuration query set for
every retained role or schedule Job and bijects with `job_binding_set`. Each row
repeats the selected limit-row digest, active-process cap, CPU cap in 100-
nanosecond units, memory cap in bytes, and exact enabled flag mask. Final
revalidation queries every Job again. A CPU or memory classification requires
the matching completion-port code plus queried `TotalUserTime` alone or peak
Job memory at or
above that exact configured limit.

`pontius-runtime-unavailable-observation-set-v1` has exactly `items`
and `schema`. An item has exactly `field` and `reason`. Field is
`loaded_image_set`, `loaded_module_set`, or
`runtime_locked_attestation_sha256`; reason is
`RUNTIME_LOCK_NOT_REACHED` or `ATTESTATION_REJECTED`. Rows sort by
field and are unique.

For last phase `PROCESS_CREATED` or `JOB_ASSIGNED`, those three fields are null
and the unavailable set contains exactly all three rows. Rejected lock framing
uses `ATTESTATION_REJECTED`; a seam before a complete frame uses
`RUNTIME_LOCK_NOT_REACHED`. For last phase `RUNTIME_LOCKED`, `BROKER_ATTACHED`, or
`FINALIZED`, all three fields are complete and nonnull and the unavailable set
is empty. The last-live handle set has `BROKER_CHANNEL` absent through
`RUNTIME_LOCKED`, present exactly once only at `BROKER_ATTACHED`, and absent at
`FINALIZED`; all other handle roles follow their frozen phase rules. Every
other source, policy, token, process, handle, Job binding,
Job quiescence, environment, and static-population field remains mandatory in
every phase because the supervisor holds or measures it independently.

`last_live_handle_set` and `last_live_thread_count` are the final complete
snapshot successfully captured while the worker still occupied
`last_runtime_phase`; they are retained evidence, not post-exit live queries.
The thread count in every such snapshot is exact one.
`process_lifecycle_set` is the complete terminal set for the worker and every
created scheduled root. It equals runtime evidence or cleanup, and every row is
directly waited signaled before its thread/process handles close. An unassigned
suspended process uses `TerminateProcess` and cannot rely on an empty Job.
Assigned rows additionally equal the complete Job bindings and quiescence set.
Every quiescence row records active-process count zero for its exact held Job handle.
Revalidation also reproduces the complete configured-limit set: role Job has
active-process cap one, every schedule Job has the dispatch's calibrated cap,
and both kinds reproduce their bound CPU, memory, enabled-flag, and limit-row
values. Sticky state is
`CLEAR`, `SET`, or `UNKNOWN`; only `CLEAR` can satisfy
success. Every nonnull digest equals the still-held complete bytes for this
launch. Authority success requires last phase `FINALIZED`, a complete all-
signaled process-lifecycle set, an empty unavailable set, all fields present,
and sticky `CLEAR`.
Failure cleanup accepts an earlier last phase only under the exact null
equations above and still requires every created root signaled.
The route-selector identity is mandatory in every phase and
equals the complete owner-only selector in the dispatch and runtime evidence.
The three rehearsal coordinate fields equal the authorization, dispatch, and
runtime-evidence root. They are all null for a normal selector. For a rehearsal
selector they are all nonnull, and the task-binding ID selects the campaign row
whose task and round equal this launch. Final revalidation never compares those
task and round values to the utility-selector root. `planner_launch_view_sha256`
equals the lock attestation and complete runtime-evidence view. The scratch
digest is null unless the schedule created the complete owner-held scratch
projection. `observation_scratch_teardown` is null exactly with that digest;
otherwise it contains the complete terminal remove-or-quarantine inventory and
proves the old scratch root absent before semantic success. Its complete
`pontius-parent-directory-observation-v1` uses retained source/destination
parent handles; quarantine also requires the complete same-volume create-new
`pontius-atomic-directory-move-fact-v1`. Exact seed bytes, every fetched-residue
entry, and every terminal destination row are covered.
The repository-projection digest equals the complete owner-only object embedded
in the held launch dispatch and the authorization payload's
`repository_projection_sha256`. The supervisor revalidates every immutable
baseline path, control, carrier, and handle row. It also embeds the complete
`pontius-repository-storage-observation-v1`, whose exact added-row population
accounts for every authorized object or fetch carrier and forbids unclassified
sidecars. A standalone-object carrier embeds the complete object-write plan and
equals the plan retained in schedule execution; built and fetched carriers
embed their complete typed inventory. Expanded write results, semantic objects,
and physical carriers form one closed relation. Baseline equality plus that
complete post-operation delta, rather than literal equality to a pre-write
directory population, is required before terminal evidence.
The core deliberately contains no repository-mutex lifecycle, lifecycle
digest, outer final-revalidation identity, or runtime-evidence identity. Every
local-ref classifier or transaction is covered by one complete
`pontius-repository-mutex-lifecycle-v1`. Its final milestone binds this exact
core digest while the mutex is still held. The acquiring thread then releases
and closes the handle, after which the owner constructs the complete lifecycle
and the outer object below. Timeout, failure, abandonment, early release, an
omitted milestone, or an action outside the held interval has no protected
mutation and cannot enter successful runtime evidence.

`pontius-runtime-final-revalidation-v1` has exactly `core`,
`core_byte_count`, `core_sha256`, `repository_mutex_lifecycle_count`,
`repository_mutex_lifecycles`, `repository_mutex_lifecycles_sha256`, and
`schema`. Core is the complete self-free object above and reproduces the
adjacent positive count and digest. The lifecycle array is execution ordered
and complete; its count is exact, and its digest covers the concatenation of
each strict canonical lifecycle plus LF. Each successful lifecycle has final
milestone output equal to `core_sha256`, then same-thread `RELEASED` and
`HANDLE_CLOSED`. Only after every lifecycle is terminal does the owner
serialize this outer object. It is the final-revalidation object carried by
runtime evidence and contains no identity or digest of that runtime evidence.

Before each typed-operation owner request, after its reply, before each askpass
adapter connection, after its sole response or zero-response terminal close,
after any Git timeout or lost-acknowledgement reconciliation, and before a
success result, the bootstrap and
supervisor independently recheck their held identities, archive hash, native
hashes, exact image set, module set, thread count, token, job, environment,
audit state, and sticky violation flag. A mismatch blocks the next broker
operation. A post-operation mismatch cannot erase an exact mutation already
observed; it converts the launch to a typed preservation failure and requires
the role protocol's fresh-state reconciliation.

On the natural success route, this final pass follows Python `FINALIZED` and
Job quiescence. On a failure before Python initialization or finalization, it
instead follows held-process termination or signal plus Job quiescence; no
Python-finalization fact is invented. The supervisor then rehashes every held
bootstrap, projection, archive, native, broker, table, authorization,
route selector, and operation-input source. For rehearsal adoption fetch and
adopt operations, it rederives the selected adoption-chain row from the held
selector and requires equality through authorization, receipt, and adopter
input; no downstream result enters the selector. It revalidates every local fault-
harness component binding selected by a rehearsal dispatch and retains the
selector-frozen external deployment-binding identity. Authenticated server
events and post-case capability wrappers are downstream campaign evidence; they
cannot enter runtime evidence or final revalidation. The supervisor repeats
exact population and forbidden-path checks before any handle closes. Handles close once in
reverse acquisition order in the outermost cleanup path.

The canonical runtime-evidence document binds external byte identities for:

- the native bootstrap source, binary, build receipt, and PE audit;
- the selected runtime projection and its complete reviewed source set;
- the role-dependent held askpass-adapter observation, null only for builder;
- the complete authority- and launch-input projections and every held file or
  Git source;
- the complete owner-only route selector and its equality through authorization,
  dispatch, applicable packet state, table selection, and final revalidation;
- the sole capability-safe planner launch view, selected callable, and exact
  planner-row count;
- the exact scratch seed, complete owner-held scratch projection when used,
  digest-only planner summary, and terminal removal-or-quarantine evidence;
- the immutable repository baseline plus complete classified post-operation
  storage observation and any complete object-write plan retained by the
  schedule;
- the role archive and archive-entry set;
- the private native set and exact loaded-image set;
- the audit policy and complete `PyConfig` projection;
- the broker engine, selected role table, and role operation schema;
- every successful broker reservation and its terminal secret-free session or
  pre-session result, including exact prompt grammar, cancellable write/flush
  evidence, plus the dispatch, reservation, and broker coordinates used by the
  downstream fault result and rehearsal step result that carry the authenticated
  lifecycle;
- the AppContainer setup, package SID, empty capabilities, ACL, child-process,
  job, mitigation, typed runtime-calibration, wall, and output policies;
- every directory-open fact and repository-mutex lifecycle for the launch; and
- the `RUNTIME_LOCKED` attestation and final revalidation result.

The runtime-evidence document ends before the supervisor's terminal wrapper and
cannot contain a result-peer-loss fact or supervisor exit result. For delivered
terminal output, `pontius-outer-session-transport-receipt-v1` binds the complete
preterminal transcript, terminal wrapper, exact EOFs, and typed supervisor exit
result after the retained supervisor process signals. For peer loss,
`pontius-outer-session-loss-receipt-v1` carries result-peer loss, the accepted
prefix and frame stage, and the typed supervisor exit result; it is never an
authority result. An implementation must not copy either post-exit fact backward
into runtime evidence or put a loss fact in the delivered transport receipt.

The operation's canonical success envelope binds that completed runtime-
evidence document and the operation-specific result. Success requires exactly
one validated redemption, terminal close, and broker-buffer zeroing for
each network child and schedule completion exact `COMPLETE`. A refusal binds the
complete fresh-state observation, canonical reservation-terminal set, and a
schedule execution whose `ABORTED` branch retains the exact contiguous executed
prefix and terminal coordinate or whose `COMPLETE` branch proves a later
failure. Its object-write facts, transport outcomes, and cleanup storage
observation account for every reached effect. The supervisor first
proves Job active-zero and completes final revalidation plus the canonical
failure-cleanup evidence. If cleanup evidence cannot complete, it emits no
semantic authority envelope, returns `PONTIUS_HOST_FAILURE`, and leaves the
controller to classify state with a new observation-only dispatch. No separate
free-form preparation or operation receipt carries semantic authority.

Malformed or noncanonical authorization and dispatch frames rejected before a
dispatch is accepted use only `pontius-protocol-refusal-v1`; they have no
consumed record, cleanup object, or authority-state claim. After the dispatch
anchor is consumed, a classifiable bootstrap, lock-attestation, owner-channel,
limit, cancellation, or operation failure uses
`pontius-authority-refusal-v1` with phase-valid cleanup. A process created
but stopped before `RUNTIME_LOCKED` records the exact earlier runtime
phase, mandatory supervisor-observable facts, and explicit unavailable rows;
it is not forced into host failure merely because no valid lock attestation
exists.

Run-local handle identities belong in runtime evidence and never in
deterministic Git object preimages. Source paths, Git blob identities, SHA-256
values, byte counts, and projection relations are deterministic authority.
Every repeated digest must be byte-for-byte equal; no consumer fills an absent
value from observation.

## Enforcement claims and nonclaims

- Held file bytes cannot be ordinarily replaced. The basis is Windows share and
  handle semantics with read-only sharing. This does not cover a hostile kernel,
  administrator, or in-memory patch.
- Source and cache injection cannot be selected. The basis is one held ZIP
  search entry and no directory search. This depends on the exact bootstrap and
  pinned CPython behavior.
- Private DLL injection cannot be selected. The basis is the absolute preload
  graph and System32-only dependency policy. An unsupported dependency cycle
  blocks acceptance.
- Python cannot create a descendant process. The basis is job active-process
  limit one and no breakaway. The broker executes inside the already trusted
  supervisor process; no second broker process exists.
- Python has only its preregistered package identity and empty capability set.
  The basis is creation-time AppContainer security capabilities and exact ACLs.
  This is not a universal Windows file-read allowlist.
- No authority is available before runtime lock. The broker handle is duplicated
  only after the accepted attestation. The supervisor and bootstrap remain
  trusted code.
- No late import or load is permitted. The basis is the closed source set,
  import guard, native audit policy, and image checks. Image checks are
  detection, so reviewed code must not bypass the guard.
- Only role operations reach authority. The basis is the broker's selected
  closed table and hostile-input validation. This does not prove arbitrary
  Python code safe.
- Termination is bounded. The basis is job kill-on-close, wall and pipe caps,
  and quiescence proof. The kernel and controller remain trusted.

The design makes no claim against a hostile kernel, loader, local
administrator, trusted supervisor, AppContainer-profile owner, accepted
bootstrap binary, debugger, in-memory patch, or System32 installation. It does
not claim System32 byte identity, historical absence of a race, portability to
another CPython or Windows build, or denial of all OS-owned reads.

Post-load enumeration, audit receipts, and final rehash are evidence and
failure detectors. They do not retroactively prevent instructions that already
executed. The accepted pre-execution claim therefore depends on the exact
archive-only Python namespace and absolute native preload graph. If the
rehearsal cannot prove either one, runtime execution remains blocked.

## Falsifying acceptance matrix

Every row uses the public supervisor boundary. A unit test of a parser or
helper is supporting evidence only.

- `RUN-01`: rebuild the bootstrap twice in independent clean roots. The exact
  binary, link map, PE audit, and SHA-256 must agree.
- `RUN-02`: add a static Python or private import, or a TLS callback, to the
  bootstrap. PE acceptance must refuse before launch.
- `RUN-03`: plant private DLL names in the current directory, application
  directory, and `PATH`. No sentinel instruction may run; the exact private
  image must load.
- `RUN-04`: plant a dependency name after the parent check and before private
  load. The bootstrap must refuse or the exact preload must win; the sentinel
  may not run.
- `RUN-05`: change one private import or delay-import edge. Projection
  construction must refuse before launch.
- `RUN-06`: map an extra System32 or private image. A sticky refusal must occur
  before broker attachment or the next request.
- `RUN-07`: change one System32 path, Windows build, or machine value. Platform
  preflight must refuse before private load.
- `RUN-08`: add source, `.pyc`, a package directory, or `_pth` beside the ZIP.
  The entry must be unselectable and the exact population check must refuse.
- `RUN-09`: mutate ZIP bytes at equal size with a restored timestamp. The
  held-byte digest or final rehash must refuse.
- `RUN-10`: open the ZIP with no sharing or delete sharing. Rehearsal must reject
  the launcher configuration.
- `RUN-11`: duplicate, reorder, compress, comment, or case-collide a member. The
  independent ZIP parser must refuse before CPython initialization.
- `RUN-12`: omit one shared-kernel or standard-library source row. The producer
  and consumer projection mismatch must block launch.
- `RUN-13`: map correct source bytes to a wrong archive path. The source-set and
  archive-entry relation must refuse.
- `RUN-14`: poison `PYTHON*`, profile, registry, site, current-directory, or user
  paths. Exact `PyConfig` and the single-entry `sys.path` must be unchanged.
- `RUN-15`: put marker bytes in Tcl, Tk, profile, locale, or temporary data. The
  marker must not be read; attempted access must refuse before influence.
- `RUN-16`: attempt the first import of an unlisted module. No module byte may
  execute; the runtime must refuse before broker use.
- `RUN-17`: attempt any import or reload after `RUNTIME_LOCKED`. The import guard
  and native audit hook must refuse.
- `RUN-18`: attempt a native or delay load after `RUNTIME_LOCKED`. A sticky
  violation must block the next broker operation.
- `RUN-19`: alter `sys.modules`, `sys.path`, an importer, or audit state. The
  exact-set check must refuse before broker operation.
- `RUN-20`: dispatch a publisher or integrator operation from the builder. The
  broker must refuse before a Git, credential, or network open.
- `RUN-21`: supply a raw executable, argv, URL, path, ref, or environment. The
  typed schema must refuse and no process may start.
- `RUN-22`: select another role table or change the table after launch. Held
  table identity or broker state must refuse.
- `RUN-23`: ask Python to spawn or break away a child. The OS job policy must
  deny the request and active process count must remain one.
- `RUN-24`: attempt a direct write to P, H, `.git`, or credential state. The
  AppContainer token and exact ACL boundary must deny it.
- `RUN-25`: inspect inherited handles before runtime lock. Only the exact five
  bootstrap handles may exist.
- `RUN-26`: forge, truncate, duplicate, or replay the lock attestation. No broker
  handle may be duplicated and the job must terminate.
- `RUN-27`: load the exact runtime, then change one handle identity. Sticky
  refusal must occur; no later clean sample may restore authority.
- `RUN-28`: time out with broker or descendant activity. The job and broker
  operation must stop and quiescence must be proven.
- `RUN-29`: mutate runtime during Git lost-ack reconciliation. The next channel
  check must refuse and the role may perform only fresh classification.
- `RUN-30`: inject one final rehash mismatch after a zero result. The overall
  launch must be a typed preservation failure.
- `RUN-31`: give the builder archive a socket, FFI, subprocess, or Git module.
  Projection policy and the static dependency gate must refuse.
- `RUN-32`: give a role a runtime-data read after the lock. The audit policy
  must refuse before the byte influences output.
- `RUN-33`: run the producer and consumer on all three source sets. Paths, rows,
  archive bytes, native graph, and digests must agree.
- `RUN-34`: exercise every accepted broker operation and result equation.
  Exactly the selected table's public grammar may be reachable.
- `RUN-35`: fail each acquisition, preload, initialization, lock, attachment,
  and close seam. There may be no unclassified exception, leaked handle, or
  authority mutation.
- `RUN-36`: measure each role at cold and warm extremes. Frozen wall, output,
  memory, and CPU limits must have headroom.
- `RUN-37`: remove or replace the preregistered AppContainer profile. Live
  preflight must refuse without creating, repairing, deleting, or changing any
  profile state.
- `RUN-38`: inspect the suspended worker before resume and at its first
  instruction. Both observations must show the exact package SID, AppContainer
  status, and empty capability set.
- `RUN-39`: change the package SID or grant a wildcard application-package SID
  in a capsule or pipe ACL. ACL verification must refuse before process resume.
- `RUN-40`: attempt direct Winsock use from the worker. The empty capability set
  must deny it; the separate authorized broker route remains usable.
- `RUN-41`: record all project-controlled and OS-owned reads during startup and
  every role operation. Project reads must equal the projection, while each OS
  read must match one preregistered TCB class.
- `RUN-42`: grant an OS-readable project marker outside the capsule. The marker
  must not be opened or influence output, demonstrating that AppContainer read
  access is not being mistaken for the project read boundary.
- `RUN-43`: make the broker-channel handle early, missing, duplicated,
  inheritable, wrong-access, or bound to the wrong target. The exact phase row
  and sticky gate must refuse before an owner request gains influence.
- `RUN-44`: omit or change the route selector, selector kind, stable coordinate,
  route-selector identity type, or author-set identity; or require the selector
  to occur in a static source projection. Refusal must precede dispatch
  consumption, repository open, credential reservation, and process creation.
- `RUN-45`: enumerate the role cross-product. Builder has no adapter; publisher
  and integrator have exactly one. Missing, extra, wrong-path, wrong-byte,
  wrong-source, or changed destination identity must refuse before network Git
  resumes.
- `RUN-46`: run adapter bytes from another path, `FileIdInfo`, Job, or breakaway
  child. The broker must record the attempt, return zero responses, and retain
  the exact capsule adapter in reservation and final revalidation.
- `RUN-47`: structurally enumerate every broker process-launch, Job, token,
  environment, stdio, executable-selector, and inherited-handle route. All are
  empty; the engine resolves only to the live supervisor/runtime-owner identity.
- `RUN-48`: fault every session, listener, schedule-Job, cancellation, and
  controller-loss seam. Every producible session becomes terminal, all secret
  buffers are zeroed, all Jobs reach active-zero, and an unprovable supervisor-
  crash cleanup emits no semantic envelope.
- `RUN-49`: for every rehearsal fault, bind the reviewed component-deployment
  projection, fresh reservation, and exact harness activation artifact. Process
  faults reproduce typed cleanup/runtime evidence; server faults also reproduce
  the nonce-correlated server event and its deployment receipt's rehearsal
  endpoint, repository, server-policy identity, selected component-binding
  digest, and procedure ID. Substitute the deployment receipt, procedure ID,
  reviewed or deployed byte digest, policy, or event parser independently;
  every substitution refuses. Missing, organic-lookalike, replayed, production-
  bound, or parser-substituted evidence also refuses, and every case finishes
  with a fresh post-case capability observation.
  The matrix enumerates server-event, process-only network, and process-only
  offline shapes; changing any endpoint, repository, or deployment-field
  nullability or equality refuses before the fault result can close.
- `RUN-50`: exercise `FREEZE_PAIR`, `ADOPT_PAIR`, and create-attempt
  `INTEGRATE_PACKET` with a newly stored standalone intent blob. The complete
  object-write plan in schedule execution, runtime evidence, storage provenance,
  stored-object facts, and physical carrier must agree byte-for-byte. Omit,
  substitute, duplicate, or add a plan member or carrier independently; every
  mutation must refuse without classifying the residue as built or fetched.
- `RUN-51`: fail before, during, and after every schedule row, including each
  network, broker, timeout, cancellation, and object-write seam. Cleanup must
  retain the exact contiguous prefix, boundary, terminal process fact when
  available, complete reservation terminal-result set, produced transport outcomes,
  returned write facts, and physical storage delta. Omission, reordering, a
  post-boundary row, or a bare diagnostic must prevent semantic refusal.
- `RUN-52`: independently remove or substitute the attach ACK/terminal closure,
  post-exit supervisor result, signed server lifecycle, scratch parent/move
  fact, broker-I/O binding, mutex retention milestone, scaled calibration
  workload, and each repository ancestor row. Every mutation must fail the
  exact consumer that claims that boundary; a label or neighboring digest must
  not preserve acceptance. Server-lifecycle cases cross accepted, rejected,
  timeout, cancellation, lost-acknowledgement, and no-request branches and
  independently corrupt ACK-before-launch ordering, signature, certificate,
  TLS binding, state order, coordinates, edge digests, consumed nullability,
  `use_state`, and `remaining_use_count`. They cover fault-bound and session-
  bound tags, required broker/session/request coordinates, and exact fault-field
  nullability. I/O cases independently null or cross-bind the always-nonnull
  operation nonce, write OVERLAPPED/event, write-terminal cancel return/error,
  wait result, `GetOverlappedResult` success/error, completed bytes, retirement
  tick, flush-thread object/digest, cancel target/return/error, flush result/
  error, signal, exit, completed join, terminal tick, and handle-close success/
  error. For write and flush they cross natural success, effective cancellation,
  race-completed success, cancellation-requested other failure, and
  noncancellation failure. Mutex cases test both exact prefixes,
  delete or reorder every mandatory suffix milestone, substitute an outer
  revalidation object for the self-free core, and reject outer construction
  before release and close.

Acceptance also requires a requirement-to-public-boundary coverage map. The
map must enumerate the category behind each fault, its complete discovered
members, and the structural test that detects a new member. Listing only the
specific injected examples above is insufficient.

## Implementation order

No implementation is authorized by this draft. Runtime work starts only from a
complete external-coordinator
`pontius-utility-bootstrap-design-authorization-publication-v1` wrapper whose
nested authorization decision is exact
`AUTHORIZE_FREEZE_TOOLS_IMPLEMENTATION`. That wrapper permits the H plan, map,
brief, and start object to freeze. Only the remotely observed
implementation-start publication opens P source work; P keeps its exact P base,
and the descendant H packet binds the independent P candidate. Packet, two
reviews, rehearsal selector, controller authorization, bootstrap evidence, and
utility acceptance repeat the start, design-authorization, and plan identities.
After both reviews and required rehearsal pass, the implementation controller
issues the typed disposition with decision exact
`AUTHORIZE_CEREMONIAL_INTEGRATION`. Only then may the P finalizer build the
distinct `UTILITY_CEREMONIAL_INTEGRATION` raw commit from the reviewed candidate
tree and freshly observed P predecessor, advances P by compare-and-swap, and
proves the result with the separate post-push P observation. Only afterward may
H publish `CEREMONIAL_INTEGRATION_RECORD_PUBLICATION` with raw kind
`UTILITY_CEREMONIAL_INTEGRATION_RECORD` and every self-free P receipt, then the
separate raw kind `UTILITY_BOOTSTRAP_DURABLE_DISPOSITION`. Neither H commit
equals the P result. The acceptance publication is not terminal success until
its post-push observation core has an external controller write-once retention
receipt; no later Git commit carries that receipt.
An unpublished or missing record, implementer-issued record, blocking design
disposition, or another decision starts no source work. Stage 0b becomes
available only after utility
acceptance for a different activated series; it cannot authorize this bootstrap
implementation. With the accepted bootstrap authorization, runtime work
proceeds in this order:

1. freeze the projection schema, role grammars, and trusted/nonclaim boundary;
2. implement the independent projection producer and consumer;
3. build and reproducibly verify the minimal native bootstrap;
4. create the three deterministic archives and native preload graphs;
5. implement isolated initialization, native audit, lock, and final checks;
6. implement the typed broker with one exact table per role;
7. add process containment and fault injection;
8. run the complete matrix on CPython 3.11.15 and the pinned Windows build;
9. calibrate and freeze walls and resource caps; and
10. obtain two cold reviews bound to the complete frozen source projections.

Until every step is complete and every required review is clean, the r001
launcher remains rejected and no authority utility may execute.
