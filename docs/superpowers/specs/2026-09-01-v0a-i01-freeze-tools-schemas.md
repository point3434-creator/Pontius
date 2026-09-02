# v0a-i01 freeze-tools r002 normative schemas

Status: COORDINATOR DRAFT. This appendix defines bytes and state relations. It
does not authorize implementation, launch a role, create an object or ref, query
a remote, accept a review, or advance handoff main.

The words MUST, MUST NOT, SHOULD, and MAY are normative. Angle-bracket names in
grammar blocks are metavariables and are never serialized literally.

## 1. Canonical byte rules

### 1.1 Canonical JSON

Every JSON document defined here has one representation:

1. The encoding is UTF-8 without a BOM.
2. The root is one object. Leading and trailing whitespace are forbidden.
3. Object keys appear once and in increasing unsigned ASCII byte order.
4. Arrays use the semantic order stated by their schema. They are never sorted
   by a general-purpose JSON writer after construction.
5. A string contains ASCII bytes only. NUL, CR, and other control characters
   are forbidden. LF is allowed only in a field whose type is `message` and is
   encoded as the two bytes `\n`.
6. Quote and backslash use `\"` and `\\`. Solidus is not escaped. No other
   escape spelling is accepted.
7. Numbers are base-ten JSON integers in the inclusive range
   `0..9007199254740991`. A leading zero, sign on zero, exponent, fraction,
   `NaN`, or infinity is forbidden.
8. The only other values are lowercase `true`, `false`, and `null`.
9. Separators are `,` and `:` with no adjacent whitespace.
10. Exactly one LF follows the closing brace.

A consumer MUST bound byte count before parsing, reject duplicate keys during
parsing, validate the exact schema and key population, re-encode the value, and
require byte equality. Parsing a noncanonical spelling and normalizing it is a
refusal.

### 1.2 Scalar domains

| Type | Closed domain |
| --- | --- |
| `sha256` | exactly 64 lowercase hexadecimal characters |
| `oid` | exactly 40 lowercase hexadecimal characters |
| `nonce` | exactly 32 lowercase hexadecimal characters |
| `count` | canonical integer in `0..9007199254740991` |
| `positive_count` | canonical integer in `1..9007199254740991` |
| `task` | `[a-z0-9][a-z0-9-]{0,62}` |
| `round` | `r` plus the zero-padded three-digit rendering of integer `1..999` |
| `ordinal` | integer `1` or `2`; ref text is respectively `01` or `02` |
| `reviewer_id` | `[a-z0-9][a-z0-9._/-]{0,127}` |
| `actor_id` | `[a-z0-9][a-z0-9._/-]{0,127}` |
| `role` | `runtime-owner`, `builder`, `publisher`, or `integrator` |
| `execution_role` | `builder`, `publisher`, or `integrator` |
| `mode` | string `100644` or `100755` |
| `endpoint_id` | `PRODUCTION_HANDOFF` or `HTTPS_REHEARSAL` |
| `case_id` | `[A-Z][A-Z0-9_]{0,63}` frozen by the rehearsal campaign |
| `task_binding_id` | `[A-Z][A-Z0-9_]{0,63}` unique within one case |
| `repository_id` | `[A-Za-z0-9][A-Za-z0-9._-]{0,63}` frozen by the selected role table |
| `procedure_id` | `[A-Z][A-Z0-9_]{0,63}` frozen by the accepted plan |
| `account_name` | public ASCII `[A-Za-z0-9._@+-]{1,128}` |
| `audience_id` | `[A-Z][A-Z0-9_]{0,63}` frozen by the selected role table |
| `ref_kind` | a closed ref-role literal fixed by the selected operation set |
| `literal_https_url` | canonical credential-free HTTPS URL defined below |
| `schedule_variant` | `[A-Z][A-Z0-9_]{0,63}` frozen by the operation set |
| `defect_verdict` | `CLEAN` or `NOT CLEAN` |
| `design_verdict` | `SOUND`, `STRAINED`, or `WRONG SHAPE` |
| `stage0b_series_id` | `[a-z0-9][a-z0-9._-]{0,127}` |
| `stage0b_round_ordinal` | canonical integer `2`, `3`, `4`, or `5` |
| `reviewer_path_slug` | `[a-z0-9][a-z0-9_-]{0,62}` |
| `stage0b_finding_id` | mechanically derived Stage 0b finding ID below |
| `stage0b_report_finding_ordinal` | canonical integer from 1 through 999 |
| `date` | an externally supplied valid Gregorian `YYYY-MM-DD` value |
| `route_id` | exact `raw-object-v5` |

`date` is controller input. A reviewer process MUST NOT read a wall clock to
fill it.
`actor_id` and `reviewer_id` are role-specific aliases over one canonical
identity namespace. Membership and equality compare their exact string bytes;
an implementation cannot treat the aliases as disjoint types.

A `literal_https_url` has exact ASCII form
`https://<dns-host>[:<nondefault-port>]/<repository-path>`. The scheme and DNS
host are lowercase. Each DNS label begins and ends with `[a-z0-9]`, contains
only `[a-z0-9-]`, and has at most 63 bytes; the complete host has at most 253
bytes. A port, when present, is canonical decimal `1..65535`; explicit `443`
and a leading zero are forbidden. The repository path follows the repository-
path segment rules, begins with one `/`, and has no empty segment. Userinfo,
password, `@`, query, fragment, percent encoding, backslash, control byte,
Unicode, alternate scheme, helper syntax, and URL-relative spelling are
forbidden. The complete literal is frozen in the selected table instance and
is passed to Git byte-for-byte; no parser normalization or redirect may change
it.

### 1.3 Paths and refs

A repository path uses `/`, is relative, has no empty, dot, or dot-dot segment,
and contains only `[A-Za-z0-9._/-]`. Backslash, whitespace, colon, NUL, a
case-fold collision, and a file/directory prefix collision are forbidden.

An absolute Windows path starts with one uppercase drive letter and `:\\`, has
no `.` or `..` segment, and is derived only from
`GetFinalPathNameByHandleW(FILE_NAME_NORMALIZED | VOLUME_NAME_DOS)` on the held
handle. The extended prefix is the exact UTF-16 sequence `U+005C U+005C U+003F
U+005C`. The returned text must then have ASCII drive-letter-and-colon form;
UNC, volume-
GUID, device, relative, dot-segment, and other result forms refuse. The
canonical JSON value strips exactly the extended prefix, uppercases the ASCII
drive letter, and retains every returned component code unit and separator
unchanged. No input spelling, short-name expansion, locale case fold, or later
path query may substitute for that same-handle result.

Every component after the drive root is nonempty ASCII and contains no control
byte or `< > : " / \\ | ? *`. A component ends with neither U+0020 nor
U+002E. Its case-insensitive basename before the first dot is not `CON`,
`PRN`, `AUX`, `NUL`, `CLOCK$`, `COM1` through `COM9`, or `LPT1`
through `LPT9`; an extension does not make a reserved basename admissible.
The stripped path contains at most 259 UTF-16 code units including drive,
colon, and separators, so its terminating NUL fits the pinned non-extended
Win32 launch route. Before authority use, the owner reopens that exact stripped
spelling without traversal, requires the same final path and FileIdInfo as the
original held handle, and retains the verification handle. A trailing-dot or
space alias, DOS device basename, alternate data-stream colon, overlength path,
normalizing reopen, or different-object reopen refuses.

The following full refs are derived, never caller-selected:

```text
candidate = refs/heads/review/<task>/<round>
packet = refs/heads/handoff-freeze-packet/<task>/<round>
builder_intent = refs/pontius/freeze/<task>/<round>/intent
candidate_anchor = refs/pontius/freeze/<task>/<round>/candidate
packet_anchor = refs/pontius/freeze/<task>/<round>/packet-base
review_01 = refs/heads/handoff-review-output/<task>/<round>/01
review_02 = refs/heads/handoff-review-output/<task>/<round>/02
handoff_main = refs/heads/main
```

For an integration transition authorization with external digest `<auth>`, the
two local attempt refs are:

```text
intent = refs/pontius/integration-attempt/<task>/<round>/<auth>/intent
result = refs/pontius/integration-attempt/<task>/<round>/<auth>/result
```

Role-table ref rows use these exact semantic kind, derivation-ID, and
resolution-class triples:

```text
CANDIDATE                    CANDIDATE_TASK_ROUND
                             SELECTOR_PINNED_STABLE
PACKET                       PACKET_TASK_ROUND
                             SELECTOR_PINNED_STABLE
BUILDER_INTENT               BUILDER_INTENT_TASK_ROUND
                             ROUTE_DERIVED_STABLE
CANDIDATE_ANCHOR             CANDIDATE_ANCHOR_TASK_ROUND
                             ROUTE_DERIVED_STABLE
PACKET_ANCHOR                PACKET_ANCHOR_TASK_ROUND
                             ROUTE_DERIVED_STABLE
REVIEW_OUTPUT                REVIEW_OUTPUT_TASK_ROUND_ORDINAL
                             SELECTOR_PINNED_STABLE
HANDOFF_MAIN                 HANDOFF_MAIN_ROUTE
                             SELECTOR_PINNED_STABLE
INTEGRATION_ATTEMPT_INTENT   INTEGRATION_ATTEMPT_TASK_ROUND_AUTH_INTENT
                             AUTHORIZATION_DERIVED
INTEGRATION_ATTEMPT_RESULT   INTEGRATION_ATTEMPT_TASK_ROUND_AUTH_RESULT
                             AUTHORIZATION_DERIVED
```

For a production table, `literal_prefix` is exactly the constant portion of
the matching ref printed above. A parameterized derivation appends only the
canonical components named by its ID; `HANDOFF_MAIN_ROUTE` appends nothing.
A rehearsal network table uses the distinct prefix fixed by its accepted
literal-delta document and the same derivation ID. Whenever the held route
selector is a rehearsal selector, every role's ref grammar, including builder's
ordinary `OFFLINE` table, appends the selected `case_id` and task-binding ID
before the ordinary task/round derivation components. `HANDOFF_MAIN_ROUTE`
appends only the case ID and is shared by that case's task bindings. Thus
each campaign case owns a disjoint permanent ref namespace and no success,
partial state, or lost-ack result can become another case's precondition. An
unknown pair, suffix, empty component, cross-case ref, or independently unequal
ref refuses.

`SELECTOR_PINNED_STABLE` full refs equal an explicit normal preregistration
field or rehearsal-selector row. `ROUTE_DERIVED_STABLE` refs do not occur in a
normal preregistration; the owner derives them from its table plus the normal
task and round and requires equality through intent, precondition, observation,
and mutation evidence. Rehearsal selectors carry their full case-qualified
rows. `AUTHORIZATION_DERIVED` rows are descriptors only before authorization.
Their full refs are absent from every selector and preregistration and are
derived once from the complete external authorization digest afterward.

No JSON input may substitute a full ref, URL, refspec, executable, argv suffix,
environment override, or credential selector for one derived by the selected
role policy.

### 1.4 Repository projection

Every repository used by these schemas has storage object format exactly
`sha1`. `git rev-parse --show-object-format=storage` must return the single line
`sha1` under the held repository identity. SHA-256 repositories and a change of
object format refuse before any object or ref mutation.

A `sealed_path_identity` has exactly `byte_count`, `file_identity`, `kind`, and
`sha256`. `kind` is `DIRECTORY` or `REGULAR_FILE`. A directory has
`byte_count` and `sha256` equal to `null`; a regular file has a
`positive_count` in `byte_count` and a `sha256`. Both kinds retain the same
final handle identity throughout use.

`pontius-directory-open-fact-v1` has exactly `creation_disposition`,
`desired_access`, `flags`, `granted_access_hex`, `inheritable`, `schema`, and
`share_mode`. Creation disposition is `OPEN_EXISTING` for an admitted ancestor
or repository directory and `CREATE_NEW` for a nonce-qualified runtime
directory. Desired access is exact `FILE_LIST_DIRECTORY |
FILE_READ_ATTRIBUTES | READ_CONTROL | SYNCHRONIZE`; flags are exact
`FILE_FLAG_BACKUP_SEMANTICS | FILE_FLAG_OPEN_REPARSE_POINT`; share mode is
exact `FILE_SHARE_READ | FILE_SHARE_WRITE`; inheritable is false; and the
queried granted-access mask is exact `00120081`. A broader grant, delete share,
traversal open, omitted reparse-point flag, inherited handle, or caller-reported
mask refuses. `pontius-held-directory-v1` has exactly `identity`,
`logical_name`, `open_fact`, and `schema`; identity is the directory
`sealed_path_identity` measured from that same retained handle and open fact is
the complete object above.

A repository control row has exactly `identity`, `logical_name`, `path`, and
`state`. `state` is `ABSENT` or `PRESENT`. `identity` is
`sealed_path_identity` for `PRESENT` and `null` for `ABSENT`. The row names and
paths are derived by repository kind; a caller cannot supply an extra path.

`pontius-git-config-file-v1` has exactly `control_logical_name`,
`identity`, `parsed_rows`, and `path`. `path` is an `absolute Windows
path` and `identity` is the held regular-file `sealed_path_identity`.
Files are exactly the present common and worktree config control rows in that
precedence order. Each file's logical name, path, and identity equal its one
corresponding control row; an absent control row has no file row.

`pontius-git-config-parsed-row-v1` has exactly `canonical_key`,
`line_ordinal`, `name`, `section`, `subsection`, and `value`.
`line_ordinal` is a positive integer, strictly increases inside one file, and
names the physical LF-delimited source line. Section and name are canonical
lowercase ASCII. Subsection retains exact case-sensitive decoded ASCII bytes
or is null. Value is the exact decoded ASCII value. Canonical key is the
unambiguous section, optional quoted subsection, and name rendering. Parsed
rows retain duplicates and source order.

`pontius-git-config-value-v1` has exactly `control_logical_name`,
`line_ordinal`, and `value`. `pontius-git-config-multimap-row-v1` has
exactly `canonical_key` and `values`. Values are the complete ordered
config-value rows obtained by flattening file parsed rows in file precedence
and line order, then selecting that canonical key without reordering. Multimap
rows have unique canonical keys and sort by unsigned ASCII key bytes.

`pontius-git-config-policy-row-v1` has exactly `allowed_values`,
`canonical_key`, `cardinality`, and `comparison`. Policy rows have unique
canonical keys and sort by unsigned ASCII key bytes. `allowed_values` is an
array of unique ASCII strings sorted by unsigned ASCII bytes, with no
case-fold duplicate when comparison is `ASCII_CASE_INSENSITIVE`.
Cardinality is `ZERO`, `ZERO_OR_ONE`, or `MANY`; comparison is `EXACT`
or `ASCII_CASE_INSENSITIVE`. `ZERO` requires an empty allowed-values array
and no multimap row. The other cardinalities require a nonempty allowed-values
array. `ZERO_OR_ONE` permits zero or one flattened occurrence; `MANY`
permits any count. Every occurrence must equal one allowed value under the
declared comparison.

`pontius-git-config-projection-v1` has exactly `files`, `multimap`,
`policy`, and `schema`. Files, parsed rows, multimap rows, and policy rows use
the exact wire types and orders above. The policy population is complete and
frozen. Every multimap row has exactly one policy row whose cardinality is
non-ZERO. Every non-ZERO policy row has the multimap presence permitted by
its cardinality.
An unlisted parsed key, extra multimap row, wrong provenance, wrong occurrence
order, or independently supplied summary refuses.

The strict reader consumes every raw byte under one frozen subset of pinned Git
config syntax: LF lines, ASCII section and name tokens, quoted subsection and
value escapes, comments, and whitespace. Invalid escape, duplicate section
syntax, trailing garbage, non-ASCII token, `include`, and `includeIf` refuse.
The strict reader derives the multimap and its policy decision solely from the
complete parsed-row population. Reconstructing all file rows, flattening them,
grouping by canonical key, and applying the frozen policy must reproduce the
complete projection byte-for-byte.

All generic and URL-scoped security keys have `ZERO` cardinality unless the
fixed command-line prefix supplies them: `include*`, `url.*`,
`credential.*`, `http.*`, `remote.*`, `core.sshCommand`, alternates,
replacement refs, namespaces, hooks, filters, and signing selectors. URL
subsections never collapse into generic keys. Case variants, duplicate
multivars, escaped subsection names, invalid-prefix suffixes, or an unlisted key
refuse. Final revalidation reparses the held raw bytes and requires the complete
projection byte-identical.

A `repository_projection` has exactly these keys:

| Key | Type or required value |
| --- | --- |
| `alternates_present` | exact `false` |
| `ancestor_chains` | complete repository-directory-ancestor-chain array |
| `common_dir` | directory `sealed_path_identity` |
| `config_projection` | complete `pontius-git-config-projection-v1` object |
| `config_projection_byte_count` | `positive_count` |
| `config_projection_sha256` | `sha256` |
| `control_rows` | repository control-row array |
| `directory_handles` | complete held-directory array |
| `git_entry` | `sealed_path_identity` or `null` |
| `grafts_present` | exact `false` |
| `object_format` | exact `sha1` |
| `object_storage_rows` | object-storage-row array |
| `objects_dir` | directory `sealed_path_identity` |
| `partial_clone_present` | exact `false` |
| `promisor_present` | exact `false` |
| `refs_dir` | directory `sealed_path_identity` |
| `repository_kind` | `BARE`, `DIRECT_WORKTREE`, or `LINKED_WORKTREE` |
| `replace_refs_present` | exact `false` |
| `shallow_present` | exact `false` |
| `worktree_git_dir` | directory `sealed_path_identity` |
| `worktree_root` | directory `sealed_path_identity` or `null` |

For `BARE`, `worktree_root` and `git_entry` are `null`, and
`worktree_git_dir`, `common_dir`, `objects_dir`, and `refs_dir` are explicit
held directories. For `DIRECT_WORKTREE`, `git_entry` is the `.git` directory
and equals both Git directories. For `LINKED_WORKTREE`, `git_entry` is the held
regular `.git` gitfile; its exact bytes name `worktree_git_dir`, whose held
`commondir` control file resolves exactly to `common_dir`. No discovery result
may replace these preregistered relations.

`directory_handles` is the path-sorted, duplicate-free population for every
nonnull directory identity in `worktree_root`, `worktree_git_dir`,
`common_dir`, `objects_dir`, `refs_dir`, and directory-kind `git_entry`.
Logical names are those root-key names. Each row repeats the corresponding
identity byte-for-byte and has `OPEN_EXISTING`. One retained handle cannot be
represented by unequal open facts, and no directory identity may be omitted.

`pontius-repository-directory-ancestor-chain-v1` has exactly `ancestors`,
`logical_name`, `schema`, and `target_identity`. Logical name and target equal
one `directory_handles` row. An ancestor has exactly `identity`, `open_fact`,
`ordinal`, and `reparse_tag`; ordinals are contiguous from the volume root
through the target, the final identity equals the target, and every reparse tag
is null. Each identity and open fact come from the same retained no-traversal
handle and every open fact is `OPEN_EXISTING`. `ancestor_chains` contains one
path-sorted row for every directory handle, including each repository root,
Git directory, common directory, objects directory, refs directory, and
directory-kind git entry. All components remain held through Job active-zero
and final revalidation. A missing parent, reparse tag, alias, traversal open,
changed identity, or chain discontinuity refuses.

The sorted `control_rows` population is complete over `HEAD`, index, commondir,
common config, worktree config, packed refs, refs directory, alternates, grafts,
shallow state, and every other control path named by the selected policy. The
verifier rejects an alternate-object database, environment object directory,
graft file, replace ref, shallow boundary, promisor remote, partial clone,
unexpected common directory, or runtime change to any held control identity.
It clears and forbids `GIT_OBJECT_DIRECTORY`,
`GIT_ALTERNATE_OBJECT_DIRECTORIES`, `GIT_REPLACE_REF_BASE`, and related
configuration before invoking Git. A missing object cannot be supplied through
an ambient repository.
The config projection's retained canonical bytes reproduce its adjacent count
and digest. Each file's logical name, path, and identity equal the corresponding
control row. Dispatch, schedule evidence, and final revalidation repeat the
complete repository-projection digest, so a parsed-config or policy substitution
changes authority.

An object-storage row has exactly `byte_count`, `file_identity`, `kind`,
`read_policy`, `relative_path`, and `sha256`. `kind` is `LOOSE_OBJECT`, `PACK`,
`PACK_INDEX`, `MULTI_PACK_INDEX`, `COMMIT_GRAPH`, `BITMAP`, `REVERSE_INDEX`, or
`OTHER_SIDECAR`. `read_policy` is `ADMITTED_CARRIER` only for required loose
objects, packs, and pack indexes; every semantic cache or sidecar is
`FORBIDDEN_READ`. Rows cover the complete objects-directory population and sort
by relative path. All baseline carriers are held and revalidated. An authorized
object-writing schedule may add only its independently inventoried exact object
residue; it may not create a commit graph, multi-pack index, bitmap, reverse
index, or unclassified sidecar.

`pontius-repository-storage-observation-v1` records the complete physical
post-operation delta without changing the immutable baseline projection. Its
root has exactly `added_rows`, `baseline_repository_projection_sha256`,
`operation`, `schema`, and `state`. State is exact `EXACT`. An added row has
exactly `classification`, `provenance`, and `storage`. `storage` is one complete
object-storage row. Classification is `OBJECT_WRITE_PLAN_CARRIER`,
`BUILT_OBJECT_CARRIER`, or `FETCH_RESIDUE_CARRIER`. `provenance` is one complete
tagged canonical object:

- `OBJECT_WRITE_PLAN` has exactly `kind`, `object_write_plan`, and
  `object_write_plan_sha256`;
- `BUILT_OBJECT_INVENTORY` has exactly `inventory`, `inventory_sha256`, and
  `kind`; and
- `FETCHED_OBJECT_INVENTORY` has exactly `inventory`, `inventory_sha256`, and
  `kind`.

The nested objects respectively use `pontius-object-write-plan-v1`,
`pontius-built-object-inventory-v1`, and `pontius-git-object-inventory-v1`.
Each digest is over its complete nested canonical bytes plus LF. Classification
selects the same-named provenance branch; no digest-only or cross-branch value
is valid.

`OBJECT_WRITE_PLAN_CARRIER` is valid only for objects newly stored by
`FREEZE_PAIR`, `ADOPT_PAIR`, or the create-attempt variant of
`INTEGRATE_PACKET`. Its complete plan equals the one retained in schedule and
runtime evidence. `BUILT_OBJECT_CARRIER` is valid only for
`BUILD_REVIEW_OUTPUT` or `BUILD_MAIN_OVERLAY`. `FETCH_RESIDUE_CARRIER` is valid
only for `FETCH_FOR_ADOPTION` or `FETCH_MAIN_INPUTS`. Every other operation has
an empty added-row population.

The owner re-enumerates the complete objects directory after Job quiescence.
Every baseline row is byte- and identity-equal, and every other row occurs once
in `added_rows`, sorted by relative path. Added rows may be only loose objects,
packs, or pack indexes. Bitmap, reverse-index, commit-graph, multi-pack-index,
and `OTHER_SIDECAR` additions are forbidden. Pack families are complete and
every contained object is covered by the branch's complete plan or inventory.
For a loose object, the path-derived OID names exactly one covered semantic
object. A removed or changed baseline row, forbidden or unclassified addition,
provenance mismatch, uncovered semantic object, or extra object makes the
observation invalid and prevents success.

Every authority-repository Git command uses the held explicit Git directory
and, when applicable, held worktree root. It never uses `-C` or repository
discovery. Every local classifier and writer mutex derives from the
`common_dir.file_identity` plus
the suite-wide mutex constant, so linked worktrees and roles sharing one
object/ref database share one mutex.

`pontius-observation-scratch-seed-v1` has exactly `entries` and `schema`. A seed
entry has exactly `byte_count`, `entry_kind`, `mode`, `relative_path`, and
`sha256`. Entry kind is `DIRECTORY` or `FILE`. Directory rows have mode
`DIRECTORY` and null byte identity; file rows have mode `100644` and a complete
byte identity. The exact path-sorted population is directory `git`, file
`git/HEAD`, directory `git/objects`, and directory `git/refs`. `git/HEAD` bytes
are exact ASCII `ref: refs/heads/pontius-observation-unborn` plus one LF. No
config, alternates, shallow, refs, object entry, hook, log, index, or other path
exists at seal.

`pontius-observation-scratch-projection-v1` has exactly `authority_common_dir`,
`directory_handles`, `dispatch_nonce`, `git_dir`, `head`, `objects_dir`,
`refs_dir`, `schema`, `scratch_root`, `seed`, and `seed_sha256`. Directory and file values are
`sealed_path_identity` objects. Seed is the complete object above and its
canonical bytes reproduce the adjacent digest.
Directory handles are the complete `pontius-held-directory-v1` rows for
scratch root and the seed's `git`, `git/objects`, and `git/refs` directories.
They repeat those identities exactly and use `CREATE_NEW`.
The native owner creates the nonce-qualified root with create-new semantics,
writes the fixed minimal bare-repository files, verifies zero refs, zero
alternates, zero object entries, no config route, and a common-directory
identity different from the authority repository. It then holds every root and
control handle.

Only an observation-only schedule may use this projection. Its Git prefix is
the held executable plus only `--git-dir=<scratch git_dir>` and the frozen
configuration. Remote fetches have no destination ref and may add only object
residue under this root. The scratch repository is never an input to a builder,
authority ref transaction, or push. On success it is exactly inventoried before
bounded teardown; after crash it is quarantined and never reused. A missing,
preexisting, aliased, or authority-sharing path refuses.

`pontius-observation-scratch-terminal-entry-v1` has exactly `action`,
`before_entry`, `destination_identity`, `relative_path`, and
`source_absent_after`. Action is `REMOVED` or `QUARANTINED`; before entry is the
complete final inventory row for that relative path; and source-absent-after is
true. Removed rows have null destination. Quarantined rows have the exact
ordinary non-reparse destination identity under the one quarantine root and
preserve type, bytes, file ID, and relative path.

`pontius-parent-directory-observation-v1` has exactly `parents`,
`quarantine_name`, `schema`, and `scratch_name`. A parent row has exactly
`directory_identity`, `entries`, `open_fact`, and `role`. Role is
`SCRATCH_PARENT` or `QUARANTINE_PARENT`; directory identity and open fact come
from the same retained handle and open fact has no delete share. An entry has
exactly `entry_identity`, `entry_kind`, `name`, and `present`; name is one exact
final path component and the identity is null exactly when present is false.
Parents sort by role and are unique. The scratch-parent row proves the original
scratch name absent. For quarantine it also contains a quarantine-parent row
proving the fresh destination name present with the moved root's held file
identity; for removal the quarantine row and name are absent. Enumeration uses
the held parent handles after teardown and is complete for both selected names.

`pontius-atomic-directory-move-fact-v1` has exactly `api`,
`destination_absent_before`, `destination_identity_after`,
`destination_parent_identity`, `flags`, `same_volume`, `schema`,
`source_absent_after`, `source_identity_before`, `source_parent_identity`, and
`win32_result_hex`. API is exact `MoveFileExW`, flags are exact
`MOVEFILE_WRITE_THROUGH`, same volume and destination-absent-before are true,
and result is exact success. The source root's retained handle identity before
the call equals the destination identity reopened without traversal after the
call. Source and destination parents equal the matching rows in the parent
observation above. A copy/delete sequence, cross-volume move, replacement,
unheld source, identity change, or unobserved result refuses.

`pontius-observation-scratch-teardown-v1` has exactly `action`,
`before_inventory`, `before_inventory_sha256`, `parent_after_observation`,
`quarantine_move`, `rows`, `schema`, and `scratch_projection_sha256`. Before
inventory is the complete post-operation scratch tree, including every seed and
fetched-residue entry, and reproduces its digest. Rows biject that inventory.
`parent_after_observation` is the complete
`pontius-parent-directory-observation-v1` above. `quarantine_move` is null for
removal and the complete `pontius-atomic-directory-move-fact-v1` for quarantine.
For `REMOVED`, quarantine move is null; rows occur in deterministic deepest-
path-first removal order; and the final parent observation proves the scratch
root absent. For `QUARANTINED`, one complete create-new atomic root-move fact
names a never-before-used quarantine destination; rows occur in ASCII relative-
path order and map every unchanged entry; and the final parent observation
proves the old root absent and the new root present. A partial delete, unproved
absence, reused quarantine, changed quarantined byte, omitted residue, or
planner-authored cleanup claim refuses. Quarantined roots are retained and
never reused as scratch.

`pontius-scratch-observation-summary-v1` is the only planner-visible form of
that projection. It has exactly `authority_repository_projection_sha256`,
`schema`, `scratch_projection_sha256`, and `state`. State is `EXACT` or
`UNKNOWN`. The scratch digest covers the complete owner-held projection above;
the summary contains no path, handle, nonce, file identity, or nested projection.

### 1.5 Artifact and handle identities

A `byte_identity` object has exactly `byte_count` and `sha256`. It binds complete
bytes but carries no path, Git mode, or Git object claim.

A `bound_document_identity` object has exactly `byte_count`, `schema`, and
`sha256`. It names complete canonical bytes plus LF held through the operation
and occurring exactly once in the accepted source projection. This type is for
static source-bound documents only.

A `route_selector_identity` object has the same exact three keys. It names the
complete canonical route-selector bytes plus LF held by the trusted owner from
authorization construction through final revalidation. The complete preimage
is carried by the launch dispatch and runtime evidence, and each wrapper's
schema, byte count, and SHA-256 reproduce this identity. A route selector is
created after the accepted source projections and is not a source-projection
entry. Substituting the source-bound type or requiring projection membership is
invalid.

A `canonical_document` object has exactly `byte_count`, `content`, `schema`,
and `sha256`. `content` is the complete parsed canonical root whose schema is
the wrapper's `schema`; re-encoding it plus LF reproduces both identity fields.
It is used for run-local evidence whose bytes cannot be supplied by a frozen
source entry.

`pontius-launch-directory-projection-v1` has exactly `directories`,
`dispatch_nonce`, `guard_files`, `process_scope`, `repeat_ordinal`, `schema`,
and `step_ordinal`. Scope is `WORKER` or `GIT_CHILD`. Worker ordinals are both
null; Git-child ordinals are both positive and name one expanded process row.
A directory row has exactly `ancestor_chain`, `logical_name`, `open_fact`, and
`sealed_identity`. An ancestor row has exactly `identity`, `open_fact`, and `reparse_tag`;
`identity` is a directory `sealed_path_identity` and `reparse_tag` is exact
null. Each open fact uses `pontius-directory-open-fact-v1`; ancestors use
`OPEN_EXISTING` and the declared nonce-qualified directory uses `CREATE_NEW`.
Chains run from volume root through immediate parents to the declared
directory, and their last identity equals `sealed_identity`. Each component is
opened without traversal, proven ordinary and non-reparse, and held through Job
active-zero and final revalidation.

The worker directory population is exactly `RUN_DIRECTORY` and its guard-file
array is empty. The Git-child directory population is exactly `RUN_DIRECTORY`,
`SCRATCH_DIRECTORY`, `PROFILE_ROOT`, `APPDATA`, `LOCALAPPDATA`, and
`XDG_CONFIG_HOME`, in that order. Every root is unique to its process coordinate
and created new. The worker run directory and Git run and scratch directories
are empty at seal. The profile root contains exactly its three declared empty
descendants plus the two guard files below. No profile descendant aliases a run
or scratch directory.

A guard-file row has exactly `creation_flags`, `desired_access`, `identity`,
`inheritable`, `logical_name`, `open_disposition`, `share_mode`, and
`zero_sha256`. Worker has no row. Every Git child has exactly
`DOT_NETRC` then `UNDERSCORE_NETRC`, whose final leaf spellings are exact
`.netrc` and `_netrc` under the held `PROFILE_ROOT`. Each is created and opened
once by `CreateFileW` with exact `CREATE_NEW`, `FILE_SHARE_READ`, noninheritable
handle, desired access `FILE_READ_DATA | FILE_READ_ATTRIBUTES | READ_CONTROL |
SYNCHRONIZE`, and creation flags `FILE_ATTRIBUTE_NORMAL |
FILE_FLAG_OPEN_REPARSE_POINT`. The original handle has no write, append, delete,
write-DACL, or write-owner access and is retained without a close/reopen window
through child Job active-zero and final revalidation. Its byte count is
zero and both identity SHA-256 and `zero_sha256` are exact
`e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`.
The retained handle denies write and delete sharing, so a preexisting file or
writable/delete handle, case variant, replacement, rename, deletion, or hard-
link write refuses. `HOME`, `USERPROFILE`, and the `HOMEDRIVE` plus `HOMEPATH`
decomposition all resolve to this same held profile root. A reused directory,
undeclared child, alias, ancestor discontinuity, changed handle identity,
changed guard bytes, early guard close, or reparse tag refuses. Any other
profile-file read is an undeclared source and refuses rather than expanding the
population at runtime.

`pontius-environment-block-v1` has exactly `block_byte_count`, `block_sha256`,
`entries`, and `schema`. An entry has exactly `name`, `ordinal`, `source`, and
`value`. Names are the frozen uppercase ASCII spelling from the selected
grammar, contain neither NUL nor `=`, and are unique under Windows ordinal case-
insensitive comparison. Values contain no NUL. Source is `CLOSED_LITERAL`,
`DIRECTORY_PROJECTION`, or `RESERVATION_DERIVED`. Entries occur in their frozen
positive contiguous ordinal order. That order is the globally ascending result
of Windows `CompareStringOrdinal` over the complete name population with
`bIgnoreCase=TRUE`; uniqueness makes every comparison strict. Network-only
entries are interleaved at their sorted positions rather than appended.

The raw block is the concatenation, for each row, of `name`, `=`, `value`, and
one U+0000, followed by one additional U+0000. Every character is encoded
UTF-16LE with no BOM. `block_byte_count` is the exact even byte length and
`block_sha256` hashes those raw bytes, not canonical JSON. No hidden drive-
current-directory entry, parent entry, alternate key case, reordering, omitted
terminator, or added terminator is valid.

`pontius-windows-command-line-v1` has exactly `arguments`, `argv_grammar_id`,
`buffer_byte_count`, `buffer_sha256`, `renderer_id`, and `schema`. An argument
row has exactly `ordinal`, `slot_id`, `source`, and `value`. Ordinals are
positive and contiguous; values are Unicode strings without NUL. Source is
`HELD_EXECUTABLE`, `CLOSED_LITERAL`, `TABLE_SLOT`, `AUTHORIZATION_DERIVED`,
`DIRECTORY_PROJECTION`, or `VALIDATED_POPULATION`. Slot ID is null exactly for
the held executable and closed literals; otherwise it is the unique typed slot
in the selected immutable argv grammar. The grammar fixes the exact row count,
source, slot, and scalar domain. Argument one is the exact held executable final
path and equals nonnull `lpApplicationName`; no caller value may supply a row.

Renderer ID is exact `WINDOWS_CRT_QUOTE_V1`. It joins arguments with one U+0020
and has no leading or trailing separator. A nonempty argument containing no
space, tab, or quote is emitted verbatim. Every other argument is surrounded by
quotes; each backslash run before a quote is doubled and followed by the escaped
quote, and each trailing backslash run before the closing quote is doubled.
Other backslashes are unchanged. One terminal U+0000 follows the complete
rendering. The buffer is encoded UTF-16LE without a BOM; byte count includes
that terminator and SHA-256 hashes those exact bytes. The owner retains a
pristine immutable copy, passes a separate mutable byte-identical buffer as
`lpCommandLine`, and independently rerenders and rehashes the retained object at
final revalidation. Characterization against the pinned Git parser must recover
the exact argument array. Missing, extra, reordered, cross-grammar, quote,
backslash, terminator, or actual-buffer divergence refuses.

`pontius-git-launch-attempt-v1` has exactly `application_name`,
`command_line`, `creation_flags`, `current_directory`,
`environment_sha256`, `inherit_handles`, `inherited_handles`, and `schema`.
It also has exactly `process_security_attributes`, `startup_info`, and
`thread_security_attributes`; both security-attribute values are exact null.
Application name is the held `PONTIUS_GIT` final path and equals command-line
argument one. Command line is the complete
`pontius-windows-command-line-v1` object. Creation flags are the exact
ordered set `CREATE_SUSPENDED`, `CREATE_UNICODE_ENVIRONMENT`, and
`EXTENDED_STARTUPINFO_PRESENT`. Current directory equals the held run
directory. `inherit_handles` is exact true. An inherited-handle row has
exactly `handle_value_hex` and `purpose`; handle value is 16 lowercase
hexadecimal digits, purpose is a frozen launch-table literal, and rows occur in
the exact `PROC_THREAD_ATTRIBUTE_HANDLE_LIST` order with no duplicate value.
Every listed handle is inheritable for this launch and every unlisted source
handle is non-inheritable. The environment digest equals the exact raw block.

`startup_info` is a complete `pontius-git-startup-info-v1` object with exactly
`attribute_list_entry_count`, `attribute_list_size_bytes`, `attribute_rows`,
`cb`, `cb_reserved2`, `desktop`, `dw_fill_attribute`, `dw_flags`,
`dw_x`, `dw_x_count_chars`, `dw_x_size`, `dw_y`, `dw_y_count_chars`,
`dw_y_size`, `reserved`, `reserved2`, `show_window`,
`stderr_handle_hex`, `stdin_handle_hex`, `stdout_handle_hex`, and `title`.
The platform is exact AMD64, so `cb` is exact decimal 112,
`sizeof(STARTUPINFOEXW)`. `reserved`, `desktop`, `title`, and
`reserved2` are null. `cb_reserved2`, every position, size, character-count,
fill-attribute, and show-window scalar are zero. `dw_flags` is exact
`STARTF_USESTDHANDLES`.
The three standard handles occur in `inherited_handles` with matching frozen
purposes. `attribute_rows` contains exactly one `HANDLE_LIST` row whose ordered
values equal `inherited_handles`. `attribute_list_entry_count` is exact one;
`attribute_list_size_bytes` is the exact nonzero result returned by the
preparatory `InitializeProcThreadAttributeList(NULL,1,0,...)` size query and
equals the allocated and initialized list passed to `CreateProcessW`. No
parent-process, mitigation, child-policy, security-capability, pseudo-console,
unknown attribute, unrecorded base-field value, or extra allocated-list entry
is present.
This object is the complete semantic preimage of the named
`CreateProcessW` arguments even when no process exists.

`pontius-git-environment-set-v1` has exactly `dispatch_sha256`, `rows`, and
`schema`. A row has
exactly `broker_reservation_sha256`, `coordinate`, `directory_projection`,
`environment`, `environment_grammar_id`, `launch_attempt`, `launch_state`, and
`process_create_called`, `process_create_win32_error_hex`, and
`process_lifecycle_sha256`. `coordinate` is a complete
`pontius-observation-primitive-coordinate-v1`; the two nested objects use the
schemas above. `launch_state` is `NOT_ATTEMPTED`, `CREATE_FAILED`, or
`CREATE_SUCCEEDED`. Rows sort by coordinate and form a bijection with every
Git-child coordinate whose complete directory projection and environment block
were prepared, including the sole ABORTED boundary coordinate; owner-only and
worker rows have none. The `CREATE_SUCCEEDED` subset has nonnull lifecycle
digest and forms a bijection with every `GIT_CHILD` row in the associated
process-lifecycle set, including an unassigned process. `CREATE_SUCCEEDED`
requires `process_create_called=true` and null Win32 error. `CREATE_FAILED`
requires called true and a nonzero eight-lowercase-hex-digit error.
`NOT_ATTEMPTED` requires called false and null error. `CREATE_FAILED` and
`NOT_ATTEMPTED` have null lifecycle digest and are valid only for the exact
ABORTED boundary whose completion coordinate equals this row and whose cleanup
termination caused launch abortion.
For a network row with a successful reservation, the same boundary additionally
names the matching pre-session result; an offline row has null reservation and
terminal-broker digest. They never invent a process binding or completion fact. A
prepared row omitted from the set, or a lifecycle row without its prepared
environment, makes semantic cleanup unavailable. The reservation digest is nonnull
exactly for `GIT_NETWORK_V1` and equals that child's complete reservation. It is
null for `GIT_OFFLINE_V1`.

The root dispatch digest equals the selected launch dispatch. Every directory
projection's dispatch nonce equals that launch's nonce; its step and repeat
ordinals equal the corresponding fields of the outer coordinate. Its run
directory is the child current directory. `TEMP` and `TMP` equal its scratch
directory; `HOME`
and `USERPROFILE` equal its profile root; `APPDATA`, `LOCALAPPDATA`, and
`XDG_CONFIG_HOME` equal their named rows; `HOMEDRIVE` and `HOMEPATH` are the
exact drive and path decomposition of that profile root. A network environment's
public pipe and nonce entries equal the reservation. Neither grammar contains
`CURL_HOME` or `NETRC`. For an assigned child, the raw block SHA-256 equals the
matching expanded schedule row's `environment_sha256`. For the sole unassigned
ABORTED boundary child, it instead equals the exact buffer passed to that
successful `CreateProcessW`, and its coordinate equals both the lifecycle row
and schedule-completion boundary; no expanded reply is invented.
For `CREATE_FAILED`, it equals the exact buffer supplied to the failing
`CreateProcessW`; for `NOT_ATTEMPTED`, it equals the fully prepared buffer that
was never supplied. Both coordinates equal the schedule-completion boundary and
the row's exact launch-state/called/error truth; only the reserved network
branch also equals the pre-session result stage and repeats the identical
process-create error. All prepared directories, environment bytes,
and retained guard handles remain available through cleanup and final
revalidation; cross-coordinate or cross-launch-state substitution refuses.

Every row's launch-attempt directory and environment equal its nested
projection and raw block. On `CREATE_SUCCEEDED`, every launch-attempt field,
every `STARTUPINFOEXW` base field, the initialized attribute-list size and
count, command line, application, flags, inheritance Boolean, and handle list
equal the expanded schedule and actual `CreateProcessW` inputs. On
`CREATE_FAILED` they equal the attempted inputs; on `NOT_ATTEMPTED` they
equal the final prepared inputs. A missing argv preimage, changed mutable
buffer, different current directory, base field, attribute-list value, flag,
inherited handle, or application name refuses in every launch state.

`pontius-runtime-calibration-workload-v1` has exactly `arguments`,
`base_workload_artifact`, `base_workload_byte_count`, `base_workload_sha256`,
`dispatch_mode`, `executable_file_identity`, `host_projection_sha256`,
`inputs`, `operation`, `rehearsal_class`, `runtime_projection_sha256`,
`scale_denominator`, `scale_numerator`, `scaled_input_sha256`,
`schedule_variant`, and `schema`. Rehearsal class is exact `SCALED_REHEARSAL`; both scale
terms are positive counts and encode the frozen rational transformation from
the complete base workload to the complete scaled inputs. Base artifact bytes
reproduce the adjacent count and digest. Inputs are the complete canonical
scaled population, and their digest equals `scaled_input_sha256`. Executable,
arguments, inputs, operation, mode, variant, host, and runtime are exactly the
sample that ran. A label, digest-only workload, undocumented scale, synthetic
sleep, or post-measurement reconstruction refuses.

`pontius-runtime-calibration-measurement-v1` has exactly `metric`,
`observed_value`, `sample_ordinal`, `source_artifact`, `source_byte_count`,
`source_sha256`, `workload`, `workload_artifact`, `workload_byte_count`, and
`workload_sha256`. Metric is `CLEANUP_RESERVE_MS`,
`CPU_TIME_MS`, `MEMORY_BYTES`, `SCHEDULE_ACTIVE_PROCESS_LIMIT`,
`STDERR_BYTE_CAP`, `STDOUT_BYTE_CAP`, or `WALL_MS`. Observed value and ordinal
are positive counts. Source artifact bytes reproduce the adjacent count and
digest and strictly parse under the calibration plan's frozen parser. Ordinals
are contiguous within each metric and workload. Workload is the complete typed
object above; its canonical bytes equal its artifact and reproduce the adjacent
positive count and digest. Each sample therefore retains the exact scaled
rehearsal executable, arguments, inputs, operation, mode, variant, scale, and
host/runtime projection rather than an opaque workload digest.

`pontius-runtime-calibration-selection-v1` has exactly `margin_ppm`, `metric`,
`observed_max`, `selected_value`, and `selection_rule`. Selection rule is exact
`MAX_OBSERVED_PLUS_FROZEN_MARGIN_CEILING_V1`; margin is a frozen nonnegative
integer; observed max is the exact maximum over the matching measurement rows;
and selected value is the overflow-checked ceiling of observed max multiplied
by `(1000000 + margin_ppm) / 1000000`.

`pontius-runtime-limit-calibration-receipt-v1` has exactly
`calibration_environment`, `calibration_plan`, `calibration_plan_sha256`,
`dispatch_mode`, `measurement_artifacts`, `measurements`, `operation`,
`schedule_variant`, `schema`, `selected_limits`, `selections`, `status`, and
`tool_file_identity`. Environment and plan are complete bound documents and the
plan digest reproduces its canonical bytes. Measurement artifacts are the
complete path-sorted unique retained population; every measurement selects one
and every artifact is consumed by at least one measurement. Measurements sort
by metric then workload digest then ordinal. Every workload artifact is also a
member of `measurement_artifacts`, parses under the plan's frozen workload
grammar, and is consumed by at least one measurement. Selections contain
exactly one row per metric in the
order above. `selected_limits` has exactly `cleanup_reserve_ms`, `cpu_time_ms`,
`memory_bytes`, `schedule_active_process_limit`, `stderr_byte_cap`,
`stdout_byte_cap`, and `wall_ms`; each value equals its selection row. Status is
exact `ACCEPTED`. Tool identity is the held regular executable that emitted the
strict measurement artifacts. A label, free numeric scalar, unparsed benchmark
output, mutable host description, omitted sample, or post-plan calibration
cannot establish a runtime limit.

`pontius-owner-wall-deadline-v1` has exactly `active_deadline_tick_hex`,
`active_wall_ms`, `cleanup_deadline_tick_hex`, `cleanup_reserve_ms`, `clock_id`,
`dispatch_sha256`, `frequency_hz`, `limit_row_sha256`,
`runtime_calibration_receipt_sha256`, `schema`, and `start_tick_hex`. Clock ID
is exact `QUERY_PERFORMANCE_COUNTER`; all three tick
values are 16 lowercase hexadecimal digits and frequency is positive. The owner
samples start once, immediately after durable dispatch-record revalidation and
before any process creation. Both budgets and both digests equal the dispatch
and selected calibrated limit row; calibration digest equals that row's
complete typed receipt.

The active deadline is the overflow-checked sum of the start tick and the
ceiling of `active_wall_ms * frequency_hz / 1000`. The cleanup deadline is the
active deadline plus the ceiling of `cleanup_reserve_ms * frequency_hz / 1000`
and is strictly later. Role, child, broker, and ordinary authority work stop at
the active deadline. After any terminal cause, only termination, typed
reconciliation over already retained facts without a new process or network
operation, Job-zero, storage accounting, final
revalidation, and refusal assembly may continue, and only before the cleanup
deadline. No child, retry, pipe, or phase resets either tick. Cleanup-deadline
expiry is host failure and emits no semantic authority envelope.

`pontius-wall-trigger-fact-v1` has exactly `deadline`, `observed_tick_hex`,
`schema`, and `source`. `deadline` is the complete object above, source is exact
`SUPERVISOR_OUTER_DEADLINE`, and the observed tick is 16 lowercase hexadecimal
digits greater than or equal to the active deadline tick. Only the trusted owner's
single outer timer produces this fact.

`pontius-deadline-completion-observation-v1` has exactly `deadline`,
`observed_tick_hex`, `phase`, and `schema`. It is sampled only after every
nested terminal fact for the named phase is complete and immutable. For
`ACTIVE_SUCCESS`, the observed tick is strictly before the active deadline. For
`FAILURE_CLEANUP`, it is strictly before the cleanup deadline and no authority
mutation occurred after the terminal cause. A missing or late observation
prevents semantic success or refusal.

An `artifact_identity` object has exactly these keys:

| Key | Type |
| --- | --- |
| `blob_oid` | `oid` |
| `byte_count` | `count` |
| `mode` | `mode` |
| `path` | repository path |
| `sha256` | `sha256` |

A `file_identity` object has exactly these keys:

| Key | Type |
| --- | --- |
| `file_id_hex` | exactly 32 lowercase hexadecimal characters |
| `final_path` | absolute Windows path |
| `volume_serial_hex` | exactly 16 lowercase hexadecimal characters |

Both handle fields come from the same `FileIdInfo` query. An `os.stat` field is
not interchangeable with either value.

## 2. Dependency order and prohibited cycles

The content dependency graph is:

```text
workflow + interpretation + schema + plan + source bytes + runtime bytes
  -> complete role source-entry populations
source-entry populations + frozen per-source attribution evidence
  -> utility author set
source-entry populations + utility author set + workflow + schema + plan
  -> role source projections -> source-projection set
candidate change spec + frozen per-change authorship evidence
  -> candidate author set
candidate author set + utility author set
  -> round review-author set
adopted workflow + freeze-tools design candidate
  -> rule-6 design packet -> two typed rule-6 design-review publications
design packet + two design reviews + controller design disposition
  + convergence policy
  -> bootstrap design authorization -> rule-6 authorization publication
bootstrap design-authorization publication
  -> freeze-tools implementation plan + path-budget map
plan + design authorization + canonical ceremonial commit inputs
  + Tier-C implementation-review slots + finalizer + P target
  -> bootstrap implementation-start object
  -> adopted-rule-6 H implementation-start publication and Markdown brief
each H publication commit + its fresh post-push observation core
  -> external controller retention receipt -> complete publication wrapper
observed H start publication + exact independent P base
  -> temporary-index P implementation candidate with unchanged nine-key record
P candidate + H start publication
  -> descendant H implementation packet with typed start link
  -> reviews, selector, tests, rehearsal, controller authorization,
     and controller disposition
reviewed candidate tree + fresh P predecessor + bound ceremonial commit inputs
  -> typed ceremonial raw-commit build receipt and distinct P result commit
  -> compare-and-swap P push + fresh P remote observation
P integration result + controller disposition
  -> H integration-record publication -> H durable disposition
  -> bootstrap evidence, utility acceptance, and acceptance publication
utility-acceptance publication + different-series rejected r001 root
  -> self-excluding Stage 0b activation publication
activation publication + frozen r002 calibration + contract registry
  + interface inventory + review scope + terminal-rule projection
  + candidate/ref/manifest + coordinator/implementer identities
  + frozen reviewer ID/path bindings
  -> future-series Stage 0b baseline counter proposal
prior chain + prior published NEXT disposition + current inventory
  + exact successor P edit and review-scope deltas + ambiguity resolutions
  + current candidate/ref/manifest + stable calibration and contract registry
  + activation publication + terminal-rule projection
  -> future-series later Stage 0b counter proposal
counter proposal + all bound coordinator artifacts + coverage + handoff
  + candidate record and manifest + fresh H main predecessor
  + complete packet-path history from the fixed H repository root
  -> create-only Stage 0b round-freeze publication
round-freeze publication -> review-input snapshot
review-input snapshot + independent inventory + reviewer report
  -> typed review receipt + issuer ledger append
  -> append-preserving remote review-result publication
counter proposal + exactly two review results + discrepancy adjudication
  + typed blocker adoption + any required design override
  -> Stage 0b disposition -> remote disposition publication
future-series BUILD_IMMEDIATELY disposition publication
  + counter + inventory + predecessor chain + activation publication
  -> self-excluding Stage 0b build authority and publication wrapper
workflow + amendment + schema + plan + source-projection set
  + task/round/base + stable refs + round review-author set
  + reviewer slots + finalizer + utility authority
  -> round preregistration
round preregistration + candidate/change/author/reviewer/workflow inputs
  -> cold-input specification
cold-input specification + complete retained static packet sources
  -> packet-source manifest
cold-input specification + packet-source manifest + canonical packet rows
  -> packet-build spec
integrated packet + cold-input specification + reviewer-authored bytes
  -> reviewer report and issuer ledger line
  -> review receipt document that binds both completed artifacts
  -> self-excluding review-output manifest
  -> canonical output tree/commit preimages and derived OIDs
  -> BUILD_REVIEW_OUTPUT transition authorization
  -> observation-only dispatch and expected-object observation
  -> build mutation precondition and dispatch
  -> stored review-output objects and object-build receipt
  -> PUBLISH_REVIEW_OUTPUT transition authorization
  -> observation-only dispatch and single-slot observation
  -> publication mutation precondition and dispatch
  -> permanent review-output ref and fresh terminal observation

round preregistration + freeze inputs + cold-input specification
  + packet-source manifest + packet-build spec
  -> FREEZE_PAIR transition authorization
  -> raw candidate and packet commit inputs
  -> canonical candidate/packet object bytes and derived OIDs
  -> canonical builder intent
FREEZE_PAIR authorization + intent
  -> observation-only dispatch and builder-tuple observation
authorization + intent + absent/exact builder-tuple observation
  -> mutation precondition and launch dispatch
  -> stored candidate/packet objects and atomic local builder tuple
builder intent + endpoint
  -> PUBLISH_PAIR transition authorization
  -> observation-only dispatch and fresh local/remote observations
authorization + exact local tuple + absent/exact remote pair
  -> PUBLISH_PAIR mutation precondition and launch dispatch
  -> remote pair publication and fresh terminal observation

expected pair + endpoint
  -> FETCH_FOR_ADOPTION transition authorization
  -> observation-only dispatch and remote-pair observation
  -> fetch mutation precondition and dispatch
  -> fetched-object inventory and adoption receipt
receipt + inventory + expected tuple
  -> ADOPT_PAIR transition authorization
  -> observation-only dispatch and builder-tuple observation
  -> adoption mutation precondition and dispatch
  -> the same canonical builder intent and local tuple

expected main/permanent roots
  -> main-input fetch spec and FETCH_MAIN_INPUTS transition authorization
  -> observation-only dispatch and scratch readiness/inventory
  -> mutation precondition and mutation dispatch
  -> authority-database object residue and main-input fetch receipt

packet fetch receipt + fresh main predecessor + integration material
  -> packet-integration overlay spec, raw preimage, and derived OIDs
  -> BUILD_MAIN_OVERLAY transition authorization
  -> observation-only dispatch and expected-object observation
  -> build mutation precondition and dispatch
  -> stored integration objects and object-build receipt
  -> integration intent
  -> integration transition authorization
  -> observation-only dispatch and pair/main/attempt observations
  -> integration mutation precondition and dispatch
  -> local integration-attempt refs
  -> main push, main observation, and downstream phase evidence

review fetch receipt + fresh main predecessor + finalizer material
  -> review-finalizer overlay spec, raw preimage, and derived OIDs
  -> BUILD_MAIN_OVERLAY transition authorization
  -> observation-only dispatch and expected-object observation
  -> build mutation precondition and dispatch
  -> stored finalizer objects and object-build receipt
  -> finalizer authorization
  -> observation-only dispatch and slot/main observations
  -> finalizer mutation precondition and dispatch
  -> main push, main observation, and downstream phase evidence

exact finalized reviews + controller disposition report and ledger line
  + disposition fetch receipt + fresh main predecessor
  -> disposition record, overlay spec, raw preimage, and derived OIDs
  -> BUILD_MAIN_OVERLAY transition authorization
  -> observation-only dispatch and expected-object observation
  -> build mutation precondition and dispatch
  -> stored disposition objects and object-build receipt
  -> disposition intent
  -> PUBLISH_DISPOSITION transition authorization
  -> observation-only dispatch and main observation
  -> disposition mutation precondition and dispatch
  -> main push, main observation, and downstream phase evidence
```

This graph describes the accepted downstream route. This utility design and its
later implementation MUST use the already adopted temporary-index Stage 2 and
handoff packet rule 6 for their own freeze and reviews. They do not execute
`BUILD_REVIEW_OUTPUT` or any other candidate utility to establish its authority.

The following exclusions are mandatory:

- No document contains its own SHA-256, byte count, blob OID, tree OID, or
  commit OID.
- A raw commit input does not contain the OID derived from its commit bytes.
- Builder intent does not name its own bytes, blob OID, adoption receipt,
  builder-adopt authorization, launch dispatch, endpoint, or fetch residue.
- `FREEZE_PAIR` authorization does not name candidate or packet commit input,
  output OID, packet inventory, builder intent, or expected tuple target. Those
  objects may depend on its externally computed digest.
- A round preregistration does not name its own identity, a cold-input
  identity, a transition authorization, a launch, or any result object.
- Integration intent does not name its own bytes, transition authorization, or
  local attempt refs.
- A review receipt does not name its own identity, its output manifest, or its
  output tree or commit. It may and must name the reviewed candidate commit and
  candidate manifest.
- A review-output manifest excludes itself.
- A transition authorization does not name a launch dispatch. Each launch
  dispatch names one already complete transition authorization.
- Integration, finalizer, and disposition commit bytes do not contain their
  transition-authorization digest. The authorization may therefore bind the
  already derived result OID.

An object that needs the identity of a later object is malformed. A producer
MUST NOT break a cycle with a placeholder, second-pass rewrite, fixed-point
search, or an ignored field.

## 3. Complete role source projection

The schema literal is `pontius-role-source-projection-v1`. Its root has exactly
these keys:

| Key | Type |
| --- | --- |
| `entry_count` | `positive_count` |
| `entry_rows_sha256` | `sha256` of the canonical entry rows |
| `entries` | source-entry array |
| `execution_projection_byte_count` | `positive_count` or `null` |
| `execution_projection_sha256` | `sha256` or `null` |
| `operation_ids` | operation-id array |
| `operation_schedules` | operation-schedule-identity array |
| `owner_request_ids` | owner-request-id array |
| `planner_entrypoints` | planner-entrypoint array or `null` |
| `plan_sha256` | `sha256` |
| `role` | `role` |
| `schema` | exact schema literal |
| `schemas_sha256` | `sha256` of this accepted appendix's bytes |
| `utility_author_set_byte_count` | `positive_count` |
| `utility_author_set_sha256` | `sha256` |

A source entry is one of two exact tagged variants. A `HELD_FILE_SOURCE` has
exactly `absolute_path`, `byte_count`, `file_identity`, `kind`, `logical_path`,
`sha256`, and `source_form`. A `PROJECT_GIT_SOURCE` has exactly `blob_oid`,
`byte_count`, `candidate_manifest_sha256`, `candidate_oid`, `kind`,
`logical_path`, `mode`, `repository_path`, `sha256`, and `source_form`.
`byte_count` is `count`, so an admitted empty source is valid. `source_form` is
the variant literal.

A held-file row binds the same-query final-path `FileIdInfo` and complete bytes.
A project-Git row binds the exact accepted implementation candidate and raw
stored blob; mode, repository path, blob OID, byte count, and SHA-256 all
reproduce from that commit. A working-tree path or checkout byte cannot satisfy
a project-Git row.

The source-entry kind is exactly one of:

```text
NATIVE_BOOTSTRAP
WINDOWS_OWNER
PURE_KERNEL
ROLE_POLICY
PROJECT_SOURCE
STDLIB_SOURCE
PYTHON_ARCHIVE
ASKPASS_ADAPTER
RUNTIME_IMAGE
RUNTIME_DATA
SCHEMA
PLAN
```

Entries sort by ASCII `logical_path`. `entry_count` equals the array length.
`entry_rows_sha256` hashes the concatenation of each entry's canonical JSON
bytes, including its LF. It is a population digest, not a projection self-hash.

`pontius-authorship-coordinate-v1` has exactly
`candidate_change_row_sha256`, `coordinate_kind`, `logical_path`, `role`,
`source_artifact`, and `source_entry_sha256`. Coordinate kind is
`DESIGN_SOURCE`, `UTILITY_SOURCE_ENTRY`, or `CANDIDATE_CHANGE`.
`DESIGN_SOURCE` has a canonical P or H repository path and nonnull
`source_artifact`; its other two discriminant fields are null.
`UTILITY_SOURCE_ENTRY` has a role, role-relative logical path, and nonnull
`source_entry_sha256`; its other two discriminant fields are null.
`CANDIDATE_CHANGE` has a canonical changed repository path and nonnull
`candidate_change_row_sha256`; its other two discriminant fields are null.
Every nonnull digest hashes the complete canonical row selected by the
coordinate, including its final LF.

`pontius-authorship-evidence-v1` has exactly `actor_id`, `attribution_kind`,
`controller_id`, `coordinate`, `schema`, and `session_id`. Attribution kind is
`AUTHORED`, `IMPLEMENTED`, `ASSEMBLED`, `GENERATED`, or `REWROTE`. Session ID is
the nonempty printable-ASCII controller assignment or handoff identifier under
which that actor performed the named work. The external controller freezes one
canonical evidence artifact for every distinct actor, coordinate, attribution-
kind, and session tuple before reviewer selection. The controller attests the
event but is not thereby an author. Duplicate tuples, a coordinate not present
in the frozen source/change population, an actor absent from its controller
assignment, or evidence frozen after reviewer selection refuses.

`pontius-utility-author-set-v1` has exactly `attributions`, `authors`,
`implementers`, and `schema`. An attribution row has exactly
`author_ids`, `authorship_evidence`, `logical_path`, `role`, and
`source_entry_sha256`. Author IDs are a nonempty sorted unique
`actor_id` array. `authorship_evidence` is a nonempty path-sorted unique
`artifact_identity` array. Every artifact parses as the complete typed evidence
above, has coordinate kind `UTILITY_SOURCE_ENTRY`, and exactly matches this
row's role, logical path, and source-entry digest. Author IDs are the exact
sorted union of actor IDs on the row's `AUTHORED` evidence. Rows occur in role
order and then ASCII logical-path order, exactly one for every source entry in
all four role projections.
`source_entry_sha256` is the digest of that complete canonical source-
entry row plus LF. An implementer row has exactly `actor_id` and `evidence`;
evidence is a nonempty path-sorted unique `artifact_identity` array. Every
artifact parses as a complete evidence record with that actor and a non-
`AUTHORED` attribution kind. These rows cover every actor that implemented,
assembled, generated, or rewrote any utility source entry.
`implementers` sorts by actor ID. The global `authors` array is the sorted
unique union of every attribution's author IDs and every implementer actor ID;
no author or implementer may be added or omitted independently.

Across the attribution evidence arrays, every authorship-evidence artifact is
consumed exactly once by its coordinate. Implementer evidence arrays are the
exact secondary index of all non-`AUTHORED` records and repeat an artifact only
at its one matching actor row. The complete evidence population has no unused,
multiply coordinated, unparsed, path-only, digest-only, or prose-only member.

The accepted plan freezes the attribution rule and upstream identity records
used to assign every source row, including generated, binary, vendor, and
carried-forward inputs. An unassigned source, an attribution without a source,
or a union mismatch refuses. The author-set object contains no projection
digest, reviewer slot, candidate OID, review, or acceptance identity. Each role
projection repeats its complete byte count and digest, so the relation is
acyclic: source-entry rows precede author set, which precedes projections and
reviewer selection.

The population is complete over every executable, source, policy, archive,
schema, native image, adapter, and runtime-data file that the role can map,
import, execute, or read. Both execution-projection fields are `null` for
`runtime-owner`; its complete native population is bound directly by these
entries. For an execution role they name the complete child runtime-projection
bytes. Owner
entries are held before any child launch is admitted; child entries are held
before that child reaches `RUNTIME_LOCKED`. Late native
images, Python imports, and runtime-data reads are forbidden under the boundary
applicable to that role; held files remain open for revalidation.

`planner_entrypoints` is `null` for `runtime-owner`. For an execution role it
has exactly one row per `operation_ids` member in the same order. A row has
exactly `callable`, `module`, and `operation`. Module and callable are frozen
ASCII Python identifiers naming an already imported member of the role archive.
The trusted bootstrap, not Python input, selects the row by the accepted
dispatch operation. An omitted, duplicate, aliased, or additional entry point
refuses the projection.

The exact `operation_ids` arrays, in stored order, are:

```text
runtime-owner: <empty>
builder: FREEZE_PAIR, ADOPT_PAIR, BUILD_REVIEW_OUTPUT
publisher: PUBLISH_PAIR, FETCH_FOR_ADOPTION, PUBLISH_REVIEW_OUTPUT
integrator: FETCH_MAIN_INPUTS, BUILD_MAIN_OVERLAY, INTEGRATE_PACKET,
            FINALIZE_REVIEWS, PUBLISH_DISPOSITION
```

The exact owner-request arrays, in stored order, are:

```text
runtime-owner:
  <empty>
builder:
  READ_OPERATION_INPUT
  HASH_HELD_BLOB
  ASSEMBLE_OBJECT_BUILD_RECEIPT
  ASSEMBLE_OBSERVATION_SET
  QUERY_LOCAL_REFS
  HASH_BLOB
  READ_OBJECT
  WRITE_TREE_OBJECT
  WRITE_COMMIT
  CLASSIFY_BUILDER_TUPLE
  CREATE_BUILDER_TUPLE
publisher:
  READ_OPERATION_INPUT
  ASSEMBLE_ADOPTION_RECEIPT
  ASSEMBLE_OBSERVATION_SET
  ASSEMBLE_TRANSPORT_OUTCOME
  QUERY_LOCAL_REFS
  QUERY_REMOTE_REFS
  READ_OBJECT
  CLASSIFY_BUILDER_TUPLE
  OBSERVE_REMOTE_PAIR
  OBSERVE_REVIEW_OUTPUT
  PUSH_REMOTE_PAIR
  FETCH_ADOPTION_OBJECTS
  PUBLISH_REVIEW_OUTPUT_REF
integrator:
  READ_OPERATION_INPUT
  ASSEMBLE_MAIN_INPUT_FETCH_RECEIPT
  ASSEMBLE_OBJECT_BUILD_RECEIPT
  ASSEMBLE_OBSERVATION_SET
  ASSEMBLE_TRANSPORT_OUTCOME
  QUERY_LOCAL_REFS
  QUERY_REMOTE_REFS
  OBSERVE_MAIN_INPUT_READINESS
  FETCH_MAIN_INPUT_OBJECTS
  FETCH_REVIEW_OUTPUT_OBJECTS
  HASH_BLOB
  READ_OBJECT
  WRITE_TREE_OBJECT
  WRITE_COMMIT
  CLASSIFY_INTEGRATION_ATTEMPT
  CREATE_INTEGRATION_ATTEMPT
  OBSERVE_REMOTE_PAIR
  OBSERVE_REVIEW_SLOTS
  OBSERVE_MAIN
  PUSH_MAIN
```

These rows are ordered as printed and are not extensible. The native owner
resolves a typed request through the one loaded role policy. A worker request
has an owner-request ID and canonical payload only. It has no raw Git argv,
path, URL, ref, refspec, executable, environment, or credential field.

The owner channel is a byte stream of typed frames. Each frame begins with one
kind byte and an eight-byte unsigned little-endian payload length. Kind `0x4a`
contains exactly one canonical ASCII JSON value with no byte order mark or line
terminator and has payload length `1..16777216`. Kind `0x42` contains
an opaque binary chunk and has payload length `1..4194304`. Early EOF,
an unknown kind, an over-cap length, a JSON payload byte after its value,
duplicate keys, and noncanonical JSON refuse. The stream parser consumes
exactly one frame at a time; residual bytes begin the next frame and are valid
only while the accepted transcript expects it. Residual bytes after the
terminal reply refuse. A JSON document's digest and byte count use its
canonical bytes plus one LF, as elsewhere in this appendix.

`pontius-owner-request-v1` has exactly `dispatch_sha256`, `operation`,
`owner_request_id`, `payload`, `payload_byte_count`, `payload_schema`,
`payload_sha256`, `predecessor_state_sha256`, `repeat_ordinal`, `role`,
`schedule_variant`, `schema`, `sequence`, and `step_ordinal`. `payload` is the
complete canonical object selected by the matching held owner-request grammar;
its byte count and digest use its canonical bytes plus LF. The remaining
fields equal the launch dispatch, operation schedule, and next concrete
expanded-step coordinate. Sequence starts at one and is contiguous.
`predecessor_state_sha256` equals `dispatch_sha256` for sequence one and the
complete preceding accepted reply digest thereafter.

`pontius-owner-reply-v1` has exactly `dispatch_sha256`, `operation`,
`owner_request_id`, `predecessor_request_sha256`, `repeat_ordinal`, `result`,
`result_byte_count`, `result_schema`, `result_sha256`, `role`, `schema`,
`sequence`, `status`, and `step_ordinal`. `status` is `OK` or `REFUSED`.
Routing and sequence fields equal the request; `predecessor_request_sha256`
equals that complete request digest. For `OK`, `result` is the complete
canonical object selected by the static step's result schema. For `REFUSED`,
it is `pontius-owner-refusal-v1`, which has exactly `code`, `operation`,
`owner_request_id`, `repeat_ordinal`, `schema`, and `step_ordinal`; `code` is
one closed refusal code from section 15. A refused reply has exact result schema
`pontius-owner-refusal-v1`; an OK reply has the static step result schema. The
result byte count and digest use
the complete canonical result bytes plus LF.

Every complete object returned to the planner is recursively capability-safe.
It contains no `sealed_path_identity`, `file_identity`, complete
`repository_projection`, route-selector object, owner-only input-source object,
or field named `absolute_path`, `final_path`, or `repository_path`. The native
owner may retain those complete objects in its transcript and terminal runtime
evidence; a digest-bound planner summary cannot be expanded by the planner.

The owner accepts only the exact next `(step_ordinal, repeat_ordinal)` from the
dispatch-selected schedule execution. For a bounded repeat it independently
derives the complete source population and current ordinal before accepting a
request. It re-encodes each payload, recomputes every digest, executes at most
one step, and emits exactly one reply. A refused request closes the channel.
Duplicate, skipped, reordered, replayed, post-refusal, post-schedule, or
cross-dispatch frames refuse without invoking an authority operation. Caller
coordinates, schemas, and IDs are confirmations of held authority and never
select a capability.

`pontius-owner-data-stream-v1` is the canonical transcript for raw bytes that
remain outside JSON and terminal evidence. Its root has exactly `byte_count`,
`chunk_byte_cap`, `chunks`, `schema`, `sha256`, and `source_item_sha256`.
`chunk_byte_cap` is exact 4,194,304. A chunk row has exactly `byte_count`,
`offset`, `ordinal`, and `sha256`. Rows have contiguous positive ordinals and
cover `[0, byte_count)` with contiguous offsets, no overlap or gap, and each
nonfinal row has the cap size. A zero-byte stream has an empty chunk array.
Every row describes the next raw `0x42` frame; the stream SHA-256 is recomputed
incrementally over their concatenation. No raw chunk is embedded in a
canonical receipt or runtime-evidence object.

`pontius-owner-step-payload-v1` has exactly `data_stream`, `owner_request_id`,
`schema`, and `source_item_sha256`. `data_stream` is a complete canonical
`pontius-owner-data-stream-v1` object or `null`. `source_item_sha256` is a
SHA-256 or `null` and, when present, equals the complete operation-input,
authorization, inventory, object-plan, or deterministic-walk member for the
expanded step.
The nested stream repeats the same source-item digest.

`pontius-git-object-facts-v1` has exactly `byte_count`, `object_type`, `oid`,
`schema`, and `sha256`. Object type is `blob`, `tree`, or `commit`; the owner
independently recomputes every field from the raw bytes and its pinned Git
object-format equation.

`pontius-git-parsed-status-v1` has exactly `parser_id`, `schema`, and
`status_facts`. `parser_id` is the one pinned bounded parser in the accepted
plan. A status-fact row has exactly `kind`, `ref`, and `status`; its domains and
order are the closed locale-fixed Git porcelain grammar for the selected
schedule. Raw output bytes and their hashes are not canonical evidence.

`pontius-output-cap-fact-v1` has exactly `dispatch_sha256`,
`first_observed_count`, `limit_row_sha256`, `schema`, `selected_cap`, and
`stream`. Stream is `STDOUT` or `STDERR`; the selected cap equals the bound
runtime-limit row, and `first_observed_count` is the owner's first exact
incremental byte count greater than that cap. The two digests equal the launch
dispatch and its limit row. Worker output cannot assert this fact.

`pontius-process-completion-facts-v1` has exactly `controller_cancel_fact`,
`controller_channel_loss_fact`, `exit_code`, `job_limit_trigger_fact`,
`output_cap_fact`, `parsed_status`, `schema`, `termination`, and
`wall_trigger_fact`.
Termination is `EXITED`, `CPU_LIMIT_EXCEEDED`,
`MEMORY_LIMIT_EXCEEDED`, `OUTPUT_CAP_EXCEEDED`, `WALL_EXPIRED`, `CANCELLED`,
`KILLED`, or `CHANNEL_LOST`. Exit code is a count exactly for
`EXITED` and null otherwise. A limit or cancellation value equals the
trusted supervisor event later embedded in cleanup evidence. Output byte counts
are enforced while the owner drains each stream. `parsed_status` may be complete
only for a `PUSH_REMOTE_PAIR`, `PUBLISH_REVIEW_OUTPUT_REF`, or `PUSH_MAIN`
schedule row whose entire bounded locale-fixed porcelain status stream was
received and strictly parsed. It is null for query, fetch, owner-only, and
offline rows, and after output overflow, wall/cancellation, kill, channel loss,
malformed/incomplete status, or any other termination before a complete push
parse.
`output_cap_fact` is complete exactly for `OUTPUT_CAP_EXCEEDED` and null for
every other termination.
`wall_trigger_fact` is complete exactly for `WALL_EXPIRED` and null for every
other termination. It is the same outer-owner fact carried by each affected
broker result and cleanup termination; a child cannot originate it.
`controller_cancel_fact` is the complete authenticated controller-cancel fact
exactly for `CANCELLED` and null otherwise. It equals the outer termination,
broker result, final revalidation, and runtime-evidence fact byte-for-byte.
`controller_channel_loss_fact` is the complete
`pontius-controller-channel-loss-fact-v1` object exactly for `CHANNEL_LOST` and
null otherwise. It equals the outer termination, broker result, final
revalidation, cleanup, and runtime-evidence fact byte-for-byte. Cancel and
channel-loss facts are mutually exclusive.
`job_limit_trigger_fact` is a complete
`pontius-job-limit-trigger-fact-v1` object for `CPU_LIMIT_EXCEEDED` or
`MEMORY_LIMIT_EXCEEDED`, with matching kind, and null otherwise. It binds the
same Job and configured-limit observation as cleanup termination.
Only the bounded porcelain grammar becomes a typed process fact. Unparsed
diagnostic bytes are never
persisted in canonical evidence or hashed into these facts. A query
contract emits only its independently parsed closed primitive result; a
mutation or fetch emits only this lifecycle object. Cap overflow refuses.
Credential-bearing operations retain only the secret-free parsed status facts;
all diagnostic forwarding remains disabled. Any direct
credential-byte observation is sticky `BROKER_FAILURE` and produces no
semantic authority envelope. These facts record one child lifecycle only. They
are never a repository, object, ref, remote, or receipt observation and cannot
satisfy terminal authority.

`pontius-git-transport-outcome-v1` is assembled only after the process result
and the same dispatch's scheduled fresh remote observation both exist. It has
exactly `authorization_sha256`, `dispatch_sha256`, `outcome`,
`parsed_status_sha256`, `post_observation_sha256`,
`process_completion_sha256`, `repeat_ordinal`, `schema`, and `step_ordinal`.
Authorization and dispatch equal the schedule execution that owns both facts.
`parsed_status_sha256` is the digest of the completion's complete parsed status
when present and null otherwise. Outcome is `SUCCESS`, `REJECTED`,
`TRANSPORT_FAILURE`, or `UNKNOWN`. Push success requires zero exit, complete
success statuses, and the expected exact fresh state. Query or fetch success
requires zero exit, null parsed status, and its complete typed expected
observation. Rejection is push-only and requires a complete parsed rejection
and unchanged fresh state. Transport failure requires a natural child return
before the active deadline with a non-success transport or lost-acknowledgement
result, followed by the already scheduled intended exact fresh state.
Output-cap, wall, cancellation, kill, channel loss, or result-peer loss aborts
before that observation row and produces no transport-outcome row in the
original schedule. Every other same-dispatch combination is `UNKNOWN`; an
expected campaign label cannot choose an outcome. The object is immutable and
never rewrites the earlier process-completion fact.

`pontius-post-terminal-reconciliation-v1` has exactly
`observation_authorization_sha256`, `observation_dispatch_sha256`,
`observation_result_sha256`, `original_authorization_sha256`,
`original_dispatch_sha256`, `original_process_completion_sha256`, `schema`, and
`terminal_cause_sha256`. It is produced only by a separately authorized
`OBSERVATION_ONLY` launch after an output-cap, wall, cancellation, kill,
channel-loss, or result-peer-loss terminal cause. Both dispatch identities and
authorizations are nonnull and unequal; the later result is never inserted into
the original `pontius-schedule-execution-v1` or relabeled as its transport
outcome. Missing or cross-bound coordinates refuse.

`pontius-ref-update-set-v1` has exactly `endpoint_id`, `rehearsal_case_id`,
`rehearsal_task_binding_id`, `repository_id`, `rows`, and `schema`. A row has
exactly `expected_old_oid`, `new_oid`, `ref`, and
`semantics`. `semantics` is `CREATE_ONLY` or `EXACT_LEASE`;
`expected_old_oid` is respectively null or one `oid`, and `new_oid` is always
one `oid`. `endpoint_id` is null exactly when every row belongs to a local
`AUTHORITY_REF_WRITE` transaction or local classification, and is nonnull and
equals the selected endpoint exactly for a remote refspec, push, query, or
server-event use. Rows are unique and sort by unsigned full-ref bytes. The owner derives
the complete set from the selected authorization, owner-held route selector,
operation schedule, and closed refspec grammar before constructing argv. Both
rehearsal coordinates are null on a normal route and equal the authorization on
a rehearsal route. A `SELECTOR_PINNED_STABLE` row resolves through the exact
normal preregistration field or rehearsal-selector row. A
`ROUTE_DERIVED_STABLE` row resolves from the held table plus the selected task
and round; on a rehearsal route its full value also equals the selector row. An
`AUTHORIZATION_DERIVED` row resolves only after the complete external
authorization digest exists and appends that digest through the one validated
descriptor. A rehearsal task-scoped row uses that exact case and task binding;
`HANDOFF_MAIN` uses the case's sole null-binding selector row. The same resolved
values supply observation, ordered refspec, argv, and mutation validation. No
expected campaign outcome, process diagnostic, caller digest, preregistered
attempt ref, or second ref-resolution path may select a row.

`pontius-local-ref-transaction-v1` has exactly `authorization_sha256`,
`operation`, `owner_request_id`, `ref_update_set`,
`ref_update_set_byte_count`, `ref_update_set_sha256`,
`repository_projection_sha256`, `schema`, `stdin_byte_count`,
`stdin_grammar_id`, `stdin_sha256`, and `step_ordinal`.
`ref_update_set` is the complete null-endpoint branch of
`pontius-ref-update-set-v1`; its byte
count and digest use canonical bytes plus LF. `stdin_grammar_id` is exact
`GIT_UPDATE_REF_CREATE_LF_V1`. `step_ordinal` is the selected schedule's sole
`AUTHORITY_REF_WRITE` step. `FREEZE_PAIR` and `ADOPT_PAIR` require owner request
`CREATE_BUILDER_TUPLE` and exactly the three `INTENT`, `CANDIDATE_ANCHOR`, and
`PACKET_ANCHOR` rows. `INTEGRATE_PACKET` requires
`CREATE_INTEGRATION_ATTEMPT` and exactly the two `INTENT` and `RESULT` rows. No
other operation has this object. Every row has `semantics=CREATE_ONLY`, null
expected old OID, and occurs in the ref-update set's unsigned-full-ref-byte
order.

The exact ASCII stdin bytes are `start LF`, then for each ordered row
`create SP <ref> SP <new_oid> LF`, then `prepare LF commit LF`, followed
immediately by EOF. The argv suffix is exact `update-ref --stdin`; `-z`,
`--batch-updates`, message, option, and every other argument are absent. Refs
are already in the closed ASCII full-ref domain and OIDs are lowercase 40-hex,
so quoting and escaping are absent. CR, NUL, blank lines, omitted, extra, or
reordered commands, any `update`, `delete`, `verify`, `option`, or `abort`
command, bytes after the final LF, delayed EOF, or another stdin grammar
refuses. `stdin_byte_count` and `stdin_sha256` cover those raw bytes, not JSON.
The explicit start/prepare/commit sequence makes the complete create set one
transaction.

`pontius-git-stdin-write-v1` has exactly `coordinate`, `dispatch_sha256`,
`process_binding_sha256`, `schema`, `stdin_closed`, `transaction_sha256`,
`write_state`, `written_byte_count`, and `written_sha256`. `write_state` is
`COMPLETE`, `PREFIX`, or `DIVERGENT`. `stdin_closed` is exact true for every
terminal fact. `COMPLETE` requires the concatenation of bytes accepted by every
successful owner `WriteFile`, in call order, to equal the transaction stream
byte-for-byte and the sole parent write handle to close before process
completion is accepted. `PREFIX` includes the empty strict prefix.
`DIVERGENT` covers any nonprefix or extra sequence and sets the sticky runtime
violation. Count and digest cover the actual accepted bytes. Coordinate and
process digest equal the expanded row. `PREFIX` and `DIVERGENT` are terminal
failure evidence and can never support authority success.

`pontius-observation-primitive-coordinate-v1` has exactly `owner_request_id`,
`repeat_ordinal`, `source_item_sha256`, and `step_ordinal`. It reproduces the
accepted request coordinate; `source_item_sha256` follows that request's exact
nullability.

`pontius-observation-primitive-result-v1` has exactly `availability`,
`coordinate`, `expected_facts_schema`, `facts`, `process_completion`, `reason`,
and `schema`. Availability is `AVAILABLE` or `UNAVAILABLE`.
`expected_facts_schema` is the static contract's local-ref, remote-ref, or Git-
object facts schema. For `AVAILABLE`, `facts` is the complete object of that
schema, process completion is `EXITED` with exit code zero, and `reason` is
null. For `UNAVAILABLE`, `facts` is null and reason is exactly one of:

```text
PROCESS_EXIT_NONZERO
OUTPUT_MALFORMED
SOURCE_UNAVAILABLE
OBJECT_UNAVAILABLE
```

An unavailable result retains the exact `EXITED` process completion and
coordinate. CPU, memory, wall, cancellation, channel-loss, output-cap, and
other supervisor termination causes use authority refusal plus cleanup evidence;
they cannot be recoded as an OK primitive fact. It
is a successful protocol reply carrying negative observation evidence, not a
refusal. Protocol, authority, source-identity, schedule, and credential-policy
violations still use `REFUSED` and close the channel.

`pontius-ref-query-row-v1` has exactly `oid`, `ref`, and
`state`. State is `ABSENT` or `PRESENT`; OID is null or
nonnull respectively. Rows occur in the exact request grammar's frozen ref
order and include absent coordinates.

`pontius-local-ref-query-v1` has exactly
`repository_projection_sha256`, `rows`, and `schema`. It is
the strict complete parse of one single-process local ref query against the
held projection.

`pontius-remote-ref-query-v1` has exactly `endpoint_id`,
`query_ordinal`, `rows`, and `schema`. Query ordinal is the
positive occurrence number for that exact ref population in the selected
schedule. It is the strict complete parse of one `ls-remote --refs`
process. Unknown, duplicate, peeled, symbolic, extra, or malformed output
produces an `UNAVAILABLE/OUTPUT_MALFORMED` primitive result. A primitive query
is evidence for that one
response only; stability and terminal state require later owner assembly.

`pontius-owner-step-result-v1` has exactly `data_stream`, `facts`,
`facts_byte_count`, `facts_schema`, `facts_sha256`, `owner_request_id`, `schema`,
and `source_item_sha256`. `data_stream` is a complete canonical stream object
or `null`. `facts` is the complete canonical object selected by the owner-
request contract; its byte count and digest use canonical bytes plus LF.
Source-item identity equals the request except for the ordinal-driven
`READ_OPERATION_INPUT` rule below. For `READ_OBJECT` or
`READ_OPERATION_INPUT`, the owner sends the declared binary chunks immediately
after the JSON reply while holding respectively the Git-object source or exact
operation-input source; every other result has null `data_stream`.

The owner-request contract population is exact:

| Owner request | Input mode | Output mode | Required facts schema |
| --- | --- | --- | --- |
| `READ_OPERATION_INPUT` | `NONE` | `RAW_BYTES` | `pontius-operation-input-read-result-v1` |
| `HASH_HELD_BLOB` | `NONE` | `NONE` | `pontius-git-object-facts-v1` |
| `ASSEMBLE_ADOPTION_RECEIPT` | `NONE` | `NONE` | `pontius-adoption-receipt-v1` |
| `ASSEMBLE_MAIN_INPUT_FETCH_RECEIPT` | `NONE` | `NONE` | `pontius-main-input-fetch-receipt-v1` |
| `ASSEMBLE_OBJECT_BUILD_RECEIPT` | `NONE` | `NONE` | `pontius-object-build-receipt-v1` |
| `ASSEMBLE_OBSERVATION_SET` | `NONE` | `NONE` | `pontius-operation-observation-set-v1` |
| `ASSEMBLE_TRANSPORT_OUTCOME` | `NONE` | `NONE` | `pontius-git-transport-outcome-v1` |
| `QUERY_LOCAL_REFS` | `NONE` | `NONE` | `pontius-observation-primitive-result-v1` |
| `QUERY_REMOTE_REFS` | `NONE` | `NONE` | `pontius-observation-primitive-result-v1` |
| `HASH_BLOB` | `RAW_BYTES` | `NONE` | `pontius-git-object-facts-v1` |
| `READ_OBJECT` | `NONE` | `RAW_BYTES` | `pontius-observation-primitive-result-v1` |
| `WRITE_TREE_OBJECT` | `RAW_BYTES` | `NONE` | `pontius-git-object-facts-v1` |
| `WRITE_COMMIT` | `RAW_BYTES` | `NONE` | `pontius-git-object-facts-v1` |
| `CLASSIFY_BUILDER_TUPLE` | `NONE` | `NONE` | `pontius-builder-tuple-observation-v1` |
| `CREATE_BUILDER_TUPLE` | `NONE` | `NONE` | `pontius-process-completion-facts-v1` |
| `OBSERVE_REMOTE_PAIR` | `NONE` | `NONE` | `pontius-remote-pair-observation-v1` |
| `OBSERVE_REVIEW_OUTPUT` | `NONE` | `NONE` | `pontius-review-output-observation-v1` |
| `PUSH_REMOTE_PAIR` | `NONE` | `NONE` | `pontius-process-completion-facts-v1` |
| `FETCH_ADOPTION_OBJECTS` | `NONE` | `NONE` | `pontius-process-completion-facts-v1` |
| `PUBLISH_REVIEW_OUTPUT_REF` | `NONE` | `NONE` | `pontius-process-completion-facts-v1` |
| `OBSERVE_MAIN_INPUT_READINESS` | `NONE` | `NONE` | `pontius-operation-observation-set-v1` |
| `FETCH_MAIN_INPUT_OBJECTS` | `NONE` | `NONE` | `pontius-process-completion-facts-v1` |
| `FETCH_REVIEW_OUTPUT_OBJECTS` | `NONE` | `NONE` | `pontius-process-completion-facts-v1` |
| `CLASSIFY_INTEGRATION_ATTEMPT` | `NONE` | `NONE` | `pontius-integration-attempt-observation-v1` |
| `CREATE_INTEGRATION_ATTEMPT` | `NONE` | `NONE` | `pontius-process-completion-facts-v1` |
| `OBSERVE_REVIEW_SLOTS` | `NONE` | `NONE` | `pontius-review-slot-observation-v1` |
| `OBSERVE_MAIN` | `NONE` | `NONE` | `pontius-main-observation-v1` |
| `PUSH_MAIN` | `NONE` | `NONE` | `pontius-process-completion-facts-v1` |

Every contract uses payload schema `pontius-owner-step-payload-v1` and result
schema `pontius-owner-step-result-v1`. Mode `NONE` requires null `data_stream`.
For `CREATE_BUILDER_TUPLE` and `CREATE_INTEGRATION_ATTEMPT`, `NONE` means the
worker supplies no input bytes; it does not mean Git receives an unbound stdin.
The trusted owner alone renders the dispatch's complete
`pontius-local-ref-transaction-v1`, writes that exact stream to the scheduled
Git child's private stdin, and retains `pontius-git-stdin-write-v1`.
For input `RAW_BYTES`, the declared binary chunks immediately follow the JSON
request; for output `RAW_BYTES`, they immediately follow the JSON reply. The
receiver bounds, hashes, and incrementally parses each chunk before accepting
the next. An operation-input read verifies source identity, byte count,
SHA-256, and its declared text or canonical schema. Only Git-object contracts
independently recompute object type, size, and OID against the held source or
write plan. The schedule execution retains only
the complete stream descriptors and result facts; it never duplicates raw
object bytes. The facts schema and owner-request ID are fixed by the loaded
contract, never selected by either envelope.
For an available fallible observation primitive, the nested
`expected_facts_schema` is respectively `pontius-local-ref-query-v1`,
`pontius-remote-ref-query-v1`, or `pontius-git-object-facts-v1`. An unavailable
`READ_OBJECT` result has null `data_stream`; an available one carries and
verifies the complete declared stream.

`HASH_HELD_BLOB` is available only to the builder's `FREEZE_PAIR` schedules.
It is a bounded repeat over the packet-build specification's complete
`STATIC_BLOB` population in destination-path order. For each member the owner
resolves exactly one equal row from the complete owner-only
`pontius-packet-static-source-map-v1` and follows only its held source variant.
The owner independently proves artifact byte count, SHA-256, blob OID, mode,
and destination relation before hashing. No raw byte frame is sent in either
direction. A missing, duplicate, unequal, or planner-supplied source refuses
before an object write.

Every request whose facts schema is
`pontius-process-completion-facts-v1` has exact independent observation requests
frozen later in its schedule. They execute only after a natural child return
before the active deadline. Local-ref mutation is then followed by
classification, remote mutation by fresh remote observation, and fetch by fresh
before/after observation plus complete object verification. A wall expiry,
cancellation, or other terminal cause aborts before those child rows, preserves
unknown state, and requires a later fresh `OBSERVATION_ONLY` dispatch. Neither
child exit zero nor captured Git output supplies observation facts.

An `ASSEMBLE_*` request has effect `OWNER_ASSEMBLE`, starts no
process, reads no new path, and derives its complete object only from prior
accepted transcript facts and still-held sources. Adoption, main-input-fetch,
object-build, and multirow observation documents may enter terminal authority
only through their corresponding assembly request. A missing prerequisite,
wrong order, process-completion substitution, or caller-composed receipt
refuses.

The aggregate requests `CLASSIFY_BUILDER_TUPLE`,
`OBSERVE_REMOTE_PAIR`, `OBSERVE_REVIEW_OUTPUT`,
`OBSERVE_MAIN_INPUT_READINESS`, `CLASSIFY_INTEGRATION_ATTEMPT`,
`OBSERVE_REVIEW_SLOTS`, and `OBSERVE_MAIN` also have effect
`OWNER_ASSEMBLE`. They start no process and consume only the exact prior
query, fetch-completion, raw-object-read, inventory, and held-source facts
required by their static schedule. `QUERY_LOCAL_REFS` is one offline
`LOCAL_READ` child; `QUERY_REMOTE_REFS` is one network
`REMOTE_READ` child.
Typed unavailable primitive facts remain accepted transcript facts. The next
applicable `OWNER_ASSEMBLE` request consumes them and emits the operation's
canonical `*_UNKNOWN` state. A deterministic raw-object repeat stops at its
first unavailable coordinate and advances to that assembly step; no dependent
OID is invented and no omitted dependent read is treated as a missing schedule
row. A `REFUSED` primitive never permits this path.

`OBSERVE_MAIN_INPUT_READINESS` is available only to the integrator's
`FETCH_MAIN_INPUTS` observation schedule. Its prior primitive steps create
the exact scratch projection, query held main and input-kind permanent
coordinates, fetch into scratch, repeat the decisive query, and raw-read the
complete inventory. The owner then returns the complete five-row operation-
observation set. `OBSERVE_MAIN` likewise requires query, fetch, second
equal query, and complete first-parent raw-object walk before assembly.
`OBSERVE_REVIEW_SLOTS` requires the complete ref query, needed scratch
fetch, and package graph/tree/blob reads for both slots. No aggregate row may be
supplied by the planner or inferred from one Git child.

The builder projection MUST NOT contain the publisher or integrator policy,
archive, endpoint, askpass adapter, or operation vocabulary. The publisher
projection MUST NOT contain tree or commit construction policy. The integrator
projection MUST NOT contain candidate-pair construction policy. A new operation
or owner request requires a new reviewed schema round.

### 3.0 Public supervisor ABI and bootstrap admission

`pontius-controller-token-policy-v1` has exactly `authentication_id_hex`,
`controller_id`, `elevation_type`, `integrity_rid`,
`logon_session_luid_hex`, `schema`, `token_type`, and `user_sid`.
Both LUID fields are exactly 16 lowercase hexadecimal digits and are equal.
`elevation_type` is `DEFAULT`, `FULL`, or `LIMITED`; `token_type` is exact
`PRIMARY`; `integrity_rid` is a decimal integer in `0..4294967295` equal to the
last subauthority of the live integrity-level SID; and `user_sid` is the
canonical uppercase SDDL SID returned by the held token. Every value is frozen
by the accepted runtime-owner controller policy.
`pontius-controller-token-observation-v1` has the same semantic fields plus
`process_query_access`, `process_query_api_set`, `token_query_access`,
`token_query_api_set`, and `token_policy_sha256`.
It is produced from the retained parent process and token handles; both access
masks are exact: process `00101000`
(`PROCESS_QUERY_LIMITED_INFORMATION|SYNCHRONIZE`) and token `00000008`
(`TOKEN_QUERY`). Process APIs are exactly `GetProcessId`,
`GetProcessTimes`, `QueryFullProcessImageNameW`, and `WaitForSingleObject`.
Token APIs are exactly `OpenProcessToken` followed by `GetTokenInformation` for
`TokenUser`, `TokenIntegrityLevel`, `TokenElevationType`, `TokenType`, and
`TokenStatistics`; no adjust, duplicate, impersonate, VM, thread, or write
access is opened. Its semantic values equal the complete policy whose canonical
digest it repeats.

`pontius-controller-origin-v1` has exactly `controller_id`,
`creation_time_hex`, `executable`, `process_id`, `schema`,
`token_observation`, and `token_policy`. The controller ID is the accepted controller actor.
Executable is a complete `file_identity`. PID and creation time come from the
same retained process handle. Policy and observation are the complete objects
above and agree with controller ID. The supervisor rechecks both held handles
and reproduces the observation before every accepted controller message. Query
failure or a user, integrity, elevation, token-type, authentication, or logon-
session mismatch closes the session.

`pontius-supervisor-executable-projection-v1` has exactly `binary`,
`build_receipt`, `controller_token_policy`, `link_map`, `pe_audit`,
`runtime_owner_source_projection`, and `schema`. Binary is one held regular-file
`sealed_path_identity`. The other four fields are complete
objects: runtime-owner source projection is a `byte_identity`, while build
receipt, controller-token policy, link map, and PE audit are
`bound_document_identity` values from that
accepted source projection. This executable projection is constructed
downstream of the complete runtime-owner source projection; it does not occur
inside or contribute to that source projection. The deterministic build receipt
and link map biject every
`WINDOWS_OWNER` compilation input to the exact binary;
the PE audit binds AMD64 headers, imports, delay imports, TLS state, and entry
point. `NATIVE_BOOTSTRAP` rows belong only to the distinct bootstrap projection,
build receipt, and capsule binary; a shared source must be explicitly present
and attributed in both closed populations. Source rows, build receipt, link map,
PE audit, installed bytes, and the live process image must all agree.
The session origin's complete `pontius-controller-token-policy-v1` bytes and
digest equal `controller_token_policy`; live observation cannot choose its own
acceptance policy.

`pontius-supervisor-channel-binding-v1` has exactly `access`,
`buffer_byte_count`, `controller_access`, `controller_child_copy_closed`,
`controller_handle_value_hex`, `controller_peer_inheritable`, `direction`,
`frame_byte_cap`, `handle_value_hex`, `inheritable`, `logical_name`,
`peer_handle_owned`, `post_create_inheritable`, `schema`, `session_byte_cap`,
and `transport`. Transport is exact
`ANONYMOUS_BYTE_PIPE`. Rows are, in order, `CONTROL_READ` with
`CONTROLLER_TO_SUPERVISOR` and `GENERIC_READ`, `RESULT_WRITE` with
`SUPERVISOR_TO_CONTROLLER` and `GENERIC_WRITE`, and `DIAGNOSTIC_WRITE` with
`SUPERVISOR_TO_CONTROLLER` and `GENERIC_WRITE`. Handle values are 16 lowercase
hexadecimal digits. The supervisor-end `inheritable` value is true only during
the exact supervisor creation and `post_create_inheritable` is false. The
controller peer is never inheritable and its child-side duplicate is closed
before the supervisor can accept `SESSION_OPEN`. The controller owns that
opposite end. Each row records the exact successful `CreatePipe` buffer size of
65,536 bytes. Control and result frame caps are 16,777,216 bytes and their
session caps are 134,217,728 bytes. Diagnostic frame cap is null and its raw
session cap is 1,048,576 bytes. Access is the supervisor end; controller access
is the exact opposite `GENERIC_WRITE` or `GENERIC_READ`. An extra endpoint,
wrong access, open child duplicate, inherited controller end, cap mismatch, or
post-create inheritable supervisor handle refuses before sequence one.

`pontius-supervisor-io-policy-v1` has exactly `blocking_io_threads`,
`cancel_api`, `control_read_mode`, `controller_drain_mode`,
`deadline_source`, `diagnostic_overflow_action`, `result_write_mode`,
`schema`, and `thread_join_rule`. Blocking I/O threads are exactly one retained
supervisor control-reader thread and one retained supervisor result/diagnostic-
writer thread. Both modes are `DEDICATED_BLOCKING_THREAD`; cancellation API is
`CancelSynchronousIo`; deadline source is the one owner-wall deadline;
controller drain mode is `CONCURRENT_RESULT_AND_DIAGNOSTIC`; diagnostic
overflow action is `TRUNCATE_AND_CLOSE_AT_CAP`; and thread join rule is
`CANCEL_WAIT_SIGNAL_CLOSE_BEFORE_PROCESS_EXIT`. Every post-dispatch blocking
read, semantic write, diagnostic write, and pipe flush runs only on the named
retained thread. The monitor cancels that thread on the active or cleanup
deadline, controller-process signal, or terminal peer loss and waits it
signaled before closing the corresponding pipe. No main supervisor thread may
perform an uncancellable pipe operation.

`pontius-supervisor-launch-directory-v1` has exactly `ancestor_chain`,
`created_new`, `directory_identity`, `directory_open_fact`,
`empty_population_sha256`, `launch_nonce`, `schema`, and
`security_descriptor_sha256`. The nonce-named
ordinary directory is created new outside P, H, Git, capsule, profile, and
credential roots. The complete held no-traversal ancestor chain has no reparse
tag. `directory_open_fact` is a complete
`pontius-directory-open-fact-v1` with `CREATE_NEW`; every ancestor carries the
same schema with `OPEN_EXISTING`. `created_new` is true and the population
digest is the canonical empty
enumeration. The same handle is retained through session termination.

`pontius-supervisor-launch-v1` has exactly `application_name`,
`command_line`, `creation_flags`, `current_directory`, `environment`,
`inherit_handles`, `inherited_channels`, `io_policy`, `process_security_attributes`,
`schema`, `startup_info`, and `thread_security_attributes`. Application name is the held
supervisor binary final path; command line and both security-attribute pointers
are null. Creation flags are exact `CREATE_UNICODE_ENVIRONMENT` and
`EXTENDED_STARTUPINFO_PRESENT`. Current directory is one held empty launch
`pontius-supervisor-launch-directory-v1` object. Its final path is the actual
`lpCurrentDirectory`. Environment is the complete fixed Unicode environment block.
`inherit_handles` is true and inherited channels are exactly the three rows
above. `io_policy` is the complete object above. Before accepting sequence one,
the supervisor queries its parent PID,
opens it read/query-only, constructs `pontius-controller-origin-v1` from that
same retained handle, and requires equality with the session.

Environment is exactly `pontius-environment-block-v1` under grammar
`SUPERVISOR_V1`. It contains only `LANG=C`, `LC_ALL=C`,
`SYSTEMROOT=C:\Windows`, `TEMP=<held launch directory>`,
`TMP=<same held launch directory>`, and `WINDIR=C:\Windows`, in the schema's
global ordinal case-insensitive sort. Its raw UTF-16LE block, terminal-NUL
count, byte count, and digest equal `lpEnvironment`. Parent entries, hidden
drive entries, PATH, proxy, Git, Python, DLL, credential, or alternate temporary
values refuse.

The launch's `startup_info` has every `STARTUPINFOEXW` base field and one
attribute list exactly as defined for Git launch attempts. `cb` is 112 on
AMD64; unused pointers are null; unused scalars and `cbReserved2` are zero;
`dwFlags` is `STARTF_USESTDHANDLES`; stdin is `CONTROL_READ`, stdout is
`RESULT_WRITE`, and stderr is `DIAGNOSTIC_WRITE`. Its sole attribute is the
ordered handle list above. The actual `CreateProcessW` call must equal this
complete object.

`pontius-controller-supervisor-session-v1` has exactly `abi_id`,
`controller_origin`, `launch`, `schema`, `session_nonce`,
`supervisor_executable_projection`, `supervisor_process_creation_time_hex`,
and `supervisor_process_id`. ABI ID is exact
`PONTIUS_SUPERVISOR_ABI_V1`. The controller origin and supervisor process facts
come from retained handles. Session nonce is fresh. One supervisor process
serves exactly one authorization/dispatch pair, accepts no second session, and
closes all inherited channel ends after one terminal result.

The outer channel uses a one-byte kind and eight-byte unsigned little-endian
payload length. JSON kind `0x53` carries one canonical JSON value without its
terminal LF and has length `1..16777216`. Secret kind `0x4b` carries opaque
bytes under the selected broker cap. Early EOF, unknown kind, over-cap length,
extra JSON bytes, duplicate key, or noncanonical JSON is a protocol failure.
Secret bytes, their length, and every secret-derived digest are excluded from
canonical evidence.

`pontius-supervisor-source-admission-v1` has exactly `authorization_sha256`,
`dispatch_sha256`, `runtime_owner_source_projection`, `schema`,
`selected_role_source_projection`,
`selected_role_source_projection_byte_count`,
`selected_role_source_projection_sha256`, `session_sha256`, and
`source_projection_set`. The runtime-owner, selected-role, and source-set values
are complete canonical documents. The selected role's adjacent identity equals
its complete bytes, the source-set member, authorization, and dispatch.
Its complete `HELD_FILE_SOURCE` and `PROJECT_GIT_SOURCE` rows are the sole
source-open population for the selected execution role; sibling projections
remain unopened identities. Runtime-owner source rows, supervisor executable
projection, and session binary/build relation also agree before the supervisor
opens a repository.

`pontius-supervisor-control-message-v1` has exactly `kind`, `payload`,
`payload_byte_count`, `payload_schema`, `payload_sha256`,
`predecessor_sha256`, `schema`, `sequence`, and `session_nonce`.
Payload is one complete canonical object. Sequence is positive and contiguous.
Sequence one has a null predecessor; every later predecessor is the preceding
accepted control-message digest. The initial closed sequence is `SESSION_OPEN`,
`SOURCE_ADMISSION`, `AUTHORIZATION`, then `DISPATCH`.

| Kind | Exact payload schema |
| --- | --- |
| `SESSION_OPEN` | `pontius-controller-supervisor-session-v1` |
| `SOURCE_ADMISSION` | `pontius-supervisor-source-admission-v1` |
| `AUTHORIZATION` | operation-contract-selected authorization schema |
| `DISPATCH` | `pontius-launch-dispatch-v1` |
| `SECRET_GRANT` | `pontius-supervisor-secret-grant-v1` |
| `CANCEL` | `pontius-controller-cancel-v1` |

The supervisor validates the session's self PID/creation time, live image,
parent origin, current directory, environment, and inherited channel set before
accepting sequence two. `AUTHORIZATION` is the closed tagged union selected by
the held operation-contract row; its `payload_schema`, parsed root, role,
operation, task, round, and digest equal that row, source admission, and
following dispatch. No generic transition schema substitutes for another
authorization variant. All session, source, authorization, dispatch, role,
operation, task, round, and nonce values cross-equal.
After dispatch consumption only a requested `SECRET_GRANT` or one `CANCEL`
is legal; its nested sequence equals the wrapper sequence. Controller EOF is
`CONTROLLER_CHANNEL_LOST` and is never cancellation.

`pontius-supervisor-secret-request-v1` has exactly `audience_id`,
`controller_session_sha256`, `dispatch_sha256`, `endpoint_id`,
`repeat_ordinal`, `repository_id`, `request_nonce`, `reservation_sha256`,
`schema`, `step_ordinal`, and
`table_instance_sha256`. The supervisor emits it only after successful
post-connect adapter-origin and scheduled-Job admission. It equals the selected
session, dispatch, table, reservation, audience, endpoint, repository, and
process coordinate.

`pontius-secret-issuance-receipt-v1` has exactly `audience_id`,
`endpoint_id`, `grant_nonce`, `repository_id`, `request_nonce`, and
`schema`. `pontius-supervisor-secret-grant-v1` has exactly
`controller_session_sha256`, `dispatch_sha256`, `grant_nonce`,
`issuance_receipt`, `request_output_message_sha256`, `request_sha256`,
`schema`, and `sequence`.
The grant is accepted only as the next controller message after the exact
request output message. Both request digests equal that wrapper and its complete
payload. The immediately following frame must be one bounded `0x4b` payload.
The supervisor copies it once into its locked broker buffer, closes
the grant state, and zeroes the received frame buffer. An unsolicited, replayed,
cross-session, cross-request, post-cancel, or second grant refuses without
credential response.

After accepting the opaque frame and immediately before any pipe write, the
supervisor repeats `PREWRITE` PID, creation-time, image, live-process, and
scheduled-Job membership queries on the same retained pipe and process handles.
A mismatch zeroes the received secret, writes no byte, and closes with
`GRANT_REFUSED` or `BROKER_FAILURE`. The terminal client attempt and ingress
result bind that recheck to the same request, grant, reservation, and process.

`pontius-secret-ingress-result-v1` has exactly `buffer_zeroed`,
`controller_channel_loss_fact`, `grant_control_message_sha256`, `grant_sha256`,
`last_accepted_stage`,
`request_output_message_sha256`, `request_sha256`, `schema`, and `state`.
Last accepted stage is `NONE`, `REQUEST_EMITTED`,
`GRANT_CONTROL_ACCEPTED`, or `OPAQUE_FRAME_ACCEPTED`. State is
`NOT_REQUESTED`, `GRANT_ACCEPTED`, `GRANT_REFUSED`, `WALL_EXPIRED`,
`CANCELLED`, `CHANNEL_LOST`, or `BROKER_FAILURE`.

At `NONE` all four digests are null and state is `NOT_REQUESTED`. At
`REQUEST_EMITTED` both request digests are nonnull and both grant digests are
null. At either later stage all four digests are nonnull, so an accepted
one-use grant remains spent and evidenced even when its opaque frame is absent,
malformed, partial, over-cap, cancelled, or interrupted by the wall.
`GRANT_ACCEPTED` requires `OPAQUE_FRAME_ACCEPTED` and a successful immediate
prewrite recheck. A failed recheck is `GRANT_REFUSED` at that same stage.
Every wall, cancel, channel-loss, or broker-failure state retains the exact last
accepted stage and its required digests. Every state requires all broker-owned
received bytes zeroed before semantic evidence.
`controller_channel_loss_fact` is complete exactly when state is
`CHANNEL_LOST` and a request or grant was active; otherwise it is null. A loss
before any request leaves this ingress `NOT_REQUESTED` and is carried by the
outer broker/process/cleanup facts. Every nonnull ingress fact equals the
complete outer channel-loss fact byte-for-byte.

`pontius-controller-cancel-v1` has exactly `cancel_nonce`,
`controller_session_sha256`, `dispatch_sha256`, `reason`, `schema`, and
`sequence`. Reason is exact `USER_REQUEST` or `CONTROLLER_SHUTDOWN`.
`pontius-authenticated-controller-cancel-fact-v1` has exactly
`accepted_tick_hex`, `cancel`, `cancel_sha256`,
`controller_origin_sha256`, and `schema`. Only the next canonical message on
the origin-bound session after durable dispatch consumption can create it.
The cancel nonce is one-use; session and dispatch must match; and its QPC tick
must precede the first immutable natural or other terminal fact. Replay,
malformed input, wrong origin, wrong dispatch, EOF, or controller death cannot
produce `CANCELLED`.

`pontius-controller-channel-loss-fact-v1` has exactly
`control_channel_binding_sha256`, `control_frame_stage`,
`control_read_error_hex`, `control_read_result`, `controller_origin_sha256`,
`controller_session_sha256`, `dispatch_sha256`, `last_control_message_sha256`,
`last_control_sequence`, `loss_kind`, `observed_tick_hex`,
`owner_wall_deadline_sha256`, `parent_exit_code_hex`,
`parent_wait_error_hex`, `parent_wait_result`,
`preterminal_transcript_sha256`, and `schema`. It is produced only from the
retained controller-control read handle and retained controller process handle
after durable dispatch consumption. `last_control_sequence` is the positive
sequence of the last accepted controller wrapper and its digest equals
`last_control_message_sha256`; it is exactly the final row of the complete
preterminal transcript's `control_messages` array and its kind is `DISPATCH` or
`SECRET_GRANT`, never `CANCEL`. `preterminal_transcript_sha256` is instead the
digest of the complete canonical transcript bytes. The
channel-binding, origin, session, dispatch, transcript, and owner-wall digests
equal this exact launch. `observed_tick_hex` is on that deadline's QPC clock
and is strictly before its active deadline; at or after that boundary the wall
fact is already due and channel loss cannot win.

`control_frame_stage` is `BETWEEN_FRAMES`, `FRAME_HEADER`, `JSON_PAYLOAD`, or
`OPAQUE_SECRET_PAYLOAD`; it exposes no secret length, byte, or digest.
`loss_kind` is `CONTROL_EOF`, `CONTROL_READ_ERROR`, or `PARENT_EXITED`.
The total branch table is exact. `CONTROL_EOF` records a failed synchronous
`ReadFile`, zero transferred bytes, `control_read_result=FAILED_ZERO_BYTES`,
and `control_read_error_hex=0000006d` (`ERROR_BROKEN_PIPE`); parent wait is
`WAIT_TIMEOUT` and both parent error and exit code are null.
`CONTROL_READ_ERROR` records `control_read_result=FAILED`, a nonzero error other
than `0000006d` and locally induced `000003e3`
(`ERROR_OPERATION_ABORTED`), parent `WAIT_TIMEOUT`, and null parent error and
exit code. `PARENT_EXITED` records `WAIT_OBJECT_0`, null wait error, and an
eight-lowercase-hex-digit parent exit code other than `00000103`
(`STILL_ACTIVE`); the read result is `PENDING`, `NOT_OBSERVED`,
`FAILED_ZERO_BYTES`, or `FAILED` with its corresponding native error. A
read snapshot is taken before any supervisor cancellation and therefore a
failed branch may not carry locally induced `000003e3`. A simultaneous parent
signal wins over EOF, which wins over another read error.
`WAIT_FAILED`, local cancellation/handle close, timeout, malformed/replayed/
cross-session bytes, or a reused PID never instantiate this fact. Lower QPC
tick wins against wall, authenticated cancel, process, and broker terminal
facts. Across cause classes the trusted supervisor uses one atomic first-
terminal latch scoped to the currently active launch and schedule boundary.
Wall wins at or after the active deadline; before it, the first completed typed
native fact wins, and equal ticks are host failure rather than relabeling. Every
carrier of this fact has a null authenticated-cancel fact, and every
`CANCELLED` carrier has a null channel-loss fact.

`pontius-bootstrap-json-frame-policy-v1` has exactly `header_bytes`,
`kind_map`, `length_encoding`, `payload_rule`, `schema`, and
`write_rule`. Header bytes are exact nine: one kind byte then an unsigned
64-bit little-endian payload length. Kind map is exact `0x61=ADMISSION`,
`0x62=BROKER_ATTACH`, `0x63=BROKER_ATTACH_ACK`, and
`0x72=RUNTIME_ATTESTATION`. Payload is one
canonical JSON object without its terminal LF, with length in
`1..frame_byte_cap-9`. Write rule is `FULL_WRITE_LOOP_NO_ZERO_PROGRESS`.
The writer loops until all header and payload bytes are accepted, treating zero
progress or error as a prefix failure. The reader consumes exactly the header,
bounds length before allocation, consumes exactly that payload, parses and
re-encodes it, and retains residual bytes only for the one next kind permitted
by the channel state. Frame count and SHA-256 cover header plus accepted payload.
Each binding cap is a positive count of at least ten bytes, and every complete
or prefix transfer count is no greater than that same cap. A permitted
coalesced next frame may remain as residual input for its later stateful read;
an unpermitted coalesced frame, wrong kind, endian, length, canonical bytes,
trailing byte, early EOF, or unpermitted second frame refuses.

`pontius-bootstrap-control-channel-binding-v1` has exactly
`direction`, `dispatch_sha256`, `frame_byte_cap`, `frame_policy`,
`launch_nonce`, `schema`,
`startup_handle_list_ordinal`, `supervisor_write_access`,
`supervisor_write_handle_hex`, `supervisor_write_inheritable`, `transport`,
`worker_process_binding_sha256`,
`worker_read_access`,
`worker_read_handle_hex`, and `worker_read_inheritable_at_create`.
Transport is `ANONYMOUS_BYTE_PIPE`, direction is
`SUPERVISOR_TO_BOOTSTRAP`, worker read access is exact `00100001`, supervisor
write access is exact `00100002`, and supervisor write inheritability is false. The
worker process-binding digest names the complete
pre-resume retained worker binding after successful Job assignment; the later
terminal lifecycle must reproduce its PID, creation time, executable, and Job.
The worker read handle appears exactly once in its
`PROC_THREAD_ATTRIBUTE_HANDLE_LIST` at the recorded ordinal and is inheritable
only for that creation. The supervisor owns only the write end. Dispatch,
nonce, and process binding identify that exact worker. This is immutable
pre-send authority and contains no prospective write, EOF, parse, or close fact.

`pontius-bootstrap-admission-transfer-result-v1` has exactly
`admission_byte_count`, `admission_sha256`, `binding`, `buffer_zeroed`,
`frame_accepted_byte_count`, `frame_sha256`, `parse_state`, `schema`,
and `state`. State is `NOT_PREPARED`, `PREPARED_NOT_SENT`,
`PREFIX_FAILED`, `SENT_ACCEPTED`, `SENT_REFUSED`, or `CHANNEL_LOST`.
Admission identity is null only for `NOT_PREPARED`. Parse state is
`NOT_REACHED`, `ACCEPTED`, or `REFUSED`. Accepted count and frame digest bind
the exact accepted framed-byte prefix; both are zero/null only when no write
began. `binding` is null exactly for `NOT_PREPARED`, where admission count and
digest are null, accepted count is zero, frame digest is null, parse state is
`NOT_REACHED`, and buffer-zeroed is true. Every later state has the complete
assigned-process channel binding. `SENT_ACCEPTED` requires the complete frame, parse `ACCEPTED`, and
true buffer zeroing. `SENT_REFUSED` requires the complete frame, parse
`REFUSED`, and true buffer zeroing. Every other state records its actual
prefix and makes no EOF or parse claim that was not observed. This result does
not close the control pipe because one later broker-attach message may use it.
A prospective close fact, cross-admission digest, partial write claimed
complete, or second admission frame invalidates the result.

`pontius-runtime-attestation-channel-binding-v1` has exactly
`dispatch_sha256`, `frame_byte_cap`, `frame_policy`, `launch_nonce`, `schema`,
`startup_handle_list_ordinal`, `supervisor_read_access`,
`supervisor_read_handle_hex`, `supervisor_read_inheritable`, `transport`,
`worker_process_binding_sha256`, `worker_write_access`,
`worker_write_handle_hex`, and `worker_write_inheritable_at_create`.
Transport is `ANONYMOUS_BYTE_PIPE`. The supervisor read end is noninheritable
with exact access `00100001`. The worker write end has exact access `00100002` and appears once
at the recorded worker handle-list ordinal. Dispatch, nonce, and process binding
equal the bootstrap-control binding.
Both bindings carry the complete frame policy above. Control permits exactly
`ADMISSION` then, only after accepted attestation, `BROKER_ATTACH`.
Attestation permits exactly `RUNTIME_ATTESTATION` then, only after accepted
attach, `BROKER_ATTACH_ACK`.

`pontius-runtime-attestation-transfer-result-v1` has exactly
`attestation`, `attestation_byte_count`, `attestation_sha256`, `binding`,
`buffer_zeroed`, `frame_accepted_byte_count`, `frame_sha256`,
`parse_state`, `schema`, `state`, `supervisor_eof_observed`,
`supervisor_read_handle_closed`, and `worker_write_handle_closed`. State is
`NOT_PREPARED`, `NOT_SENT`, `PREFIX_FAILED`, `SENT_ACCEPTED`,
`SENT_REFUSED`, or `CHANNEL_LOST`. `NOT_PREPARED` has null binding,
attestation, and frame identities, zero accepted bytes, parse `NOT_REACHED`,
and only actual cleanup close facts. Every later state has the complete
assigned-process binding. Only `SENT_ACCEPTED` has a complete
`pontius-runtime-locked-v2` attestation and requires full-frame equality,
accepted parse, and true buffer zeroing. For that state EOF and both close facts
are false because the same channel remains open for one later attach ACK.
Every other state retains its exact prefix and actual close/EOF facts, closes
both ends during cleanup, and cannot authorize broker attachment.

`pontius-bootstrap-broker-attach-v1` has exactly `broker_channel_acl_sha256`,
`broker_channel_handle_hex`, `broker_projection_sha256`, `dispatch_sha256`,
`duplicate_options_hex`, `launch_nonce`,
`owner_client_source_closed`, `owner_client_source_granted_access_hex`,
`process_policy_sha256`, `runtime_locked_attestation_sha256`, `schema`,
`server_granted_access_hex`,
`worker_duplicate_granted_access_hex`, `worker_process_binding_sha256`. It is
constructed only after an accepted
attestation transfer and successful duplication of the exact broker-channel
client handle into that worker. ACL digest equals the process policy's exact
`BROKER_CHANNEL_PIPE_ACL`. The duplex server and owner-side client access are
`0012019f`; `DuplicateHandle` uses desired access `00100003`, options
`00000000`, and noninheritability, after which the broader owner-side client
source is closed. The native bootstrap receives the numeric
handle; Python never does.

`pontius-bootstrap-broker-attach-ack-v1` has exactly `attach_sha256`,
`broker_channel_handle_hex`, `dispatch_sha256`, `launch_nonce`, `schema`,
`state`, and `worker_process_binding_sha256`. State is exact `ACCEPTED`. The
native bootstrap constructs this object only after it receives the attach,
validates every repeated launch identity, adopts the exact duplicated handle as
its sole broker client, and closes no channel needed by the worker. Handle and
all identities equal the attach object; Python never receives the handle value.

`pontius-runtime-attestation-channel-terminal-result-v1` has exactly
`ack`, `ack_byte_count`, `ack_sha256`, `binding_sha256`,
`frame_accepted_byte_count`, `frame_sha256`, `parse_state`, `schema`, `state`,
`supervisor_eof_observed`, `supervisor_read_handle_closed`,
`worker_write_handle_closed`. State is `NOT_PREPARED`, `EARLY_CLOSE`, `ACKED`,
`ACK_REFUSED`, or `CHANNEL_LOST`. Only `ACKED` has the complete ACK object and
identity, a full accepted frame, parse `ACCEPTED`, exact supervisor EOF after
that frame, and both ends closed. `EARLY_CLOSE` applies when no attach was
accepted. Every other state retains the actual prefix, parse, EOF, and close
facts. A missing, second, pre-attach, cross-worker, or mismatched ACK cannot
become `ACKED`.

`pontius-bootstrap-control-terminal-result-v1` has exactly `attach`,
`attach_ack`, `attach_ack_byte_count`, `attach_ack_sha256`,
`attach_byte_count`, `attach_sha256`,
`attestation_channel_terminal_result`,
`attestation_channel_terminal_result_byte_count`,
`attestation_channel_terminal_result_sha256`, `binding_sha256`,
`frame_accepted_byte_count`, `frame_sha256`, `parse_state`, `schema`,
`state`, `supervisor_write_handle_closed`, `worker_eof_observed`, and
`worker_read_handle_closed`. State is `NOT_PREPARED`, `EARLY_CLOSE`,
`ATTACHED`, `ATTACH_REFUSED`, or `CHANNEL_LOST`. `NOT_PREPARED` has null
binding, attach, ACK, and attestation-channel-terminal identities, zero accepted
bytes, and only actual cleanup close facts. Every later state has a nonnull
binding digest.
`ATTACHED` alone has the complete attach
object and identity, a complete accepted frame, the complete accepted attach
ACK and attestation-channel terminal result, exact EOF on both channels, and
all four channel ends closed. Every ACK object, byte count, and digest
reproduces the canonical bytes above. `EARLY_CLOSE` is required when runtime
lock was never accepted; it has null attach, ACK, and channel-terminal fields,
zero accepted bytes, and records actual EOF and closes. No
second attach, pre-lock attach, cross-worker handle, missing EOF, or unclosed
endpoint is valid.

`pontius-runtime-capsule-row-v1` has exactly `byte_count`,
`capsule_relative_path`, `destination_file_identity`,
`destination_security_descriptor_sha256`, `kind`,
`logical_name`, `mode`, `sha256`, `source`, and `source_entry_sha256`.
`source` is one complete tagged source entry (`HELD_FILE_SOURCE` or
`PROJECT_GIT_SOURCE`) and its canonical digest equals `source_entry_sha256`.
The destination is a complete retained run-local regular-file identity and is
never compared to the source's file identity. Kind is
`RUNTIME_PROJECTION`, `NATIVE_BOOTSTRAP`, `ROLE_ARCHIVE`, `PRIVATE_NATIVE`,
`RUNTIME_DATA`, or `ASKPASS_ADAPTER`; mode is `READ_ONLY_DATA` for projection,
archive, and runtime data and `READ_EXECUTE_IMAGE` for bootstrap, private
native, and adapter.

`pontius-runtime-capsule-population-v1` has exactly
`capsule_directory_identity`, `capsule_directory_security_descriptor_sha256`,
`dispatch_sha256`, `launch_nonce`, `role`,
`rows`, and `schema`. Rows sort by capsule path and biject the selected
bootstrap, runtime projection, ZIP, private-native population, runtime data, and
role-conditional adapter. There is exactly one projection, bootstrap, and role
archive row; private-native and runtime-data rows biject the selected runtime
projection's corresponding populations. Builder has zero adapter rows;
publisher and integrator have exactly one. Every row's source object equals the
matching selected projection/source-set member and its bytes, count, SHA-256,
and semantic mode equal the freshly created destination. A complete no-
traversal directory enumeration
admits no extra, missing, reparse, case-colliding, or normalizing entry.
The directory descriptor equals the accepted capsule template. Every child
descriptor is independently queried and is the exact effective inherited or
explicit descriptor derived from that template; its digest is never replaced
by the root-template digest.

`pontius-bootstrap-source-admission-v1` has exactly `authorization_sha256`,
`bootstrap_control_channel_binding`, `bootstrap_process_binding_sha256`,
`capsule_population`, `capsule_population_byte_count`,
`capsule_population_sha256`, `dispatch_sha256`, `launch_nonce`,
`planner_launch_view`, `role`, `runtime_projection`,
`runtime_projection_byte_count`, `runtime_projection_sha256`, `schema`,
`source_projection_set_sha256`, `worker_environment_sha256`, and
`worker_launch_directory_projection_sha256`. Complete capsule, projection, and
planner-view objects reproduce their adjacent identities and the launch.
Exactly one length-framed canonical admission is sent over the origin-bound
supervisor-to-bootstrap control pipe before any private load. The bootstrap
strictly parses it, independently opens and retains every capsule destination,
re-enumerates the capsule, and zeroes the raw admission buffer. It accepts no
route selector, repository, endpoint, ref, credential, or extra handle.

`pontius-session-accepted-v1` has exactly `controller_session_sha256`,
`schema`, and `state`. State is exact `ACCEPTED`.
`pontius-host-status-v1` has exactly `code` and `schema`. Code is exact
`PONTIUS_HOST_FAILURE` and carries no free-form diagnostic.

`pontius-supervisor-terminal-result-v1` has exactly `kind`, `payload`,
`payload_byte_count`, `payload_schema`, `payload_sha256`, and `schema`.
Kind is `PROTOCOL_REFUSAL`, `AUTHORITY_RESULT`, `AUTHORITY_REFUSAL`, or
`HOST_FAILURE`. Payload is the complete matching canonical object. Protocol
refusal uses `pontius-protocol-refusal-v1`. Authority result uses the
dispatch-mode-selected `pontius-authority-observation-v1` or
`pontius-authority-success-v1`. Authority refusal uses
`pontius-authority-refusal-v1`. Host failure uses `pontius-host-status-v1`.
Payload schema, bytes, count, and digest must reproduce that selected object;
cross-kind or cross-operation substitution refuses.

`pontius-result-peer-loss-fact-v1` has exactly `accepted_prefix_byte_count`,
`accepted_prefix_sha256`, `controller_origin_sha256`,
`controller_process_wait_result`, `controller_session_sha256`,
`dispatch_sha256`, `last_output_message_sha256`, `last_output_sequence`,
`loss_kind`, `observed_tick_hex`, `result_frame_stage`,
`result_write_error_hex`, `result_write_result`, `schema`. It is produced only
while the retained controller process is nonsignaled (`WAIT_TIMEOUT`) and the
supervisor is writing the next canonical output frame. Loss kind is
`RESULT_BROKEN_PIPE` for native error `0000006d` or `000000e8`, or
`RESULT_WRITE_ERROR` for another nonzero error except locally induced
`000003e3`. Frame stage is `FRAME_HEADER` or `JSON_PAYLOAD`; accepted prefix is
the exact written prefix and is zero/null only before the first byte. The last
output sequence/digest equals the complete preterminal transcript, or is
zero/null before `SESSION_ACCEPTED`. A live-parent result-peer loss wins the
first-terminal latch at its measured pre-deadline tick and is distinct from
controller-channel loss, parent exit, authenticated cancel, and wall expiry.

`pontius-supervisor-exit-code-map-v1` has exactly `rows` and `schema`. It has
exactly three rows, in order, with `exit_code_hex` and `exit_semantic`:
`TERMINAL_DELIVERED` has `00000000`; `HOST_FAILURE_NO_TERMINAL` and
`RESULT_PEER_LOST` have distinct nonzero eight-lowercase-hex-digit codes. The
complete map is frozen in the runtime projection and process policy before
launch.

`pontius-supervisor-exit-result-v1` has exactly `exit_code_hex`,
`exit_code_map_sha256`, `exit_semantic`, `result_peer_loss_fact`, `schema`,
`terminal_output_message_sha256`, and `termination_sha256`.
`TERMINAL_DELIVERED` has the zero code, a nonnull terminal-wrapper digest, and
null loss and termination. `HOST_FAILURE_NO_TERMINAL` has its mapped nonzero
code, null terminal and loss, and complete nonnull cleanup-termination digest.
`RESULT_PEER_LOST` has its mapped nonzero code, null terminal, the complete
loss fact, and the cleanup-termination digest. No raw exit code or process
signal alone supplies semantic authority.

`pontius-supervisor-output-message-v1` has exactly `kind`, `payload`,
`payload_byte_count`, `payload_schema`, `payload_sha256`,
`predecessor_sha256`, `schema`, `sequence`, and `session_nonce`. Output
sequence is positive and contiguous and has its own predecessor chain rooted
at the validated SESSION_OPEN control-message digest. Kind is
`SESSION_ACCEPTED`, `SECRET_REQUEST`, or `TERMINAL_RESULT`.
`SESSION_ACCEPTED` occurs once as sequence one and carries the fixed
secret-free `pontius-session-accepted-v1` object. `SECRET_REQUEST` carries
one complete `pontius-supervisor-secret-request-v1` and is legal only while no
earlier request is outstanding. `TERMINAL_RESULT` carries one complete
`pontius-supervisor-terminal-result-v1`, occurs exactly once while the result
peer is live, closes every
outstanding request through its ingress result, and is the last output.
The grant's request-output digest equals the exact `SECRET_REQUEST` wrapper.
Diagnostics use only the separate bounded channel and never enter this stream.
This terminal-output requirement applies only while the retained controller
process is nonsignaled and its result peer remains writable. If the selected
loss kind is `PARENT_EXITED`, the supervisor cancels its writer, performs
secret zeroization and Job-zero cleanup, emits no semantic output wrapper, and
exits `PONTIUS_HOST_FAILURE`; the dead controller cannot manufacture a receipt.
If the retained controller remains nonsignaled but its result peer is lost, the
supervisor freezes the complete result-peer-loss fact, cancels and joins its
retained blocking writer thread, performs secret zeroization and Job-zero cleanup, emits no further
semantic output wrapper, and exits with semantic `RESULT_PEER_LOST`.

Malformed, truncated, unknown-kind, or noncanonical `SESSION_OPEN` bytes have
no validated session nonce and therefore emit no canonical output message.
The process exits `PONTIUS_HOST_FAILURE` after bounded diagnostic close. Every
later protocol refusal has the validated nonce and uses the output sequence.

`pontius-supervisor-preterminal-transcript-v1` has exactly
`control_message_count`, `control_messages`, `output_message_count`,
`output_messages`, `schema`, and `session_sha256`. Control rows are every
accepted inbound wrapper through the last grant or cancel. Output rows are
every accepted outbound wrapper through the last secret request and exclude
`TERMINAL_RESULT`. Counts equal array lengths; both predecessor chains, all
request/grant correlations, and the session digest reproduce exactly. This
preterminal transcript can enter runtime or cleanup evidence without a
self-cycle. The controller records the final terminal wrapper only in the
downstream outer-session transport receipt.

`pontius-outer-session-transport-receipt-v1` has exactly
`controller_control_write_closed`, `controller_session_sha256`,
`diagnostic_byte_count`, `diagnostic_eof_observed`,
`diagnostic_read_handle_closed`, `diagnostic_sha256`,
`preterminal_transcript`, `preterminal_transcript_byte_count`,
`preterminal_transcript_sha256`, `result_eof_observed`,
`result_read_handle_closed`, `schema`, `supervisor_exit_result`,
`supervisor_exit_result_byte_count`, `supervisor_exit_result_sha256`,
`supervisor_process_signaled`, `terminal_output_message`,
`terminal_output_message_byte_count`, and
`terminal_output_message_sha256`. The controller concurrently drains the
result and bounded diagnostic pipes while the supervisor runs. It closes its
control-write end after the terminal wrapper or its own authenticated cancel,
then drains both streams to exact EOF, waits for the retained supervisor
process, records its complete typed exit result, and closes both read handles.

The preterminal object is complete and reproduces its positive canonical byte
count and digest. `terminal_output_message` is the complete final
`pontius-supervisor-output-message-v1` wrapper with kind `TERMINAL_RESULT`; its
canonical bytes plus LF reproduce the adjacent positive count and digest. Its
predecessor equals the last preterminal output digest, or the validated
SESSION_OPEN control-wrapper digest when no nonterminal output precedes it.
The result stream contains exactly the preterminal output wrappers followed by
this terminal wrapper and no trailing semantic byte. Diagnostic count is at
most the session's frozen cap; its digest covers exactly the drained secret-free
diagnostic bytes and supplies no semantic claim. All three EOF/close facts,
process signaling, and control close are true for an accepted receipt. A
complete exit result has semantic `TERMINAL_DELIVERED`; its canonical bytes
reproduce the adjacent count and digest and its terminal-message digest equals
this receipt. A
missing drain, result/diagnostic deadlock, unbounded diagnostic stream, output
after terminal, or process exit before the terminal bytes are accepted prevents
controller acceptance.

`pontius-controller-session-result-v1` has exactly `schema` and
`transport_receipt`. The receipt is the complete object above. It is the sole
controller-accepted public-session result for a live result peer and is constructed strictly
downstream of the supervisor's final terminal wrapper. It is never embedded in
the terminal payload, runtime evidence, final revalidation, or cleanup evidence,
so the evidence graph is acyclic.
No controller-session result or transport receipt exists for `PARENT_EXITED`.

`pontius-outer-session-loss-receipt-v1` has exactly
`controller_control_write_closed`, `controller_session_sha256`,
`diagnostic_byte_count`, `diagnostic_eof_observed`,
`diagnostic_read_handle_closed`, `diagnostic_sha256`,
`preterminal_transcript`, `preterminal_transcript_byte_count`,
`preterminal_transcript_sha256`, `result_peer_loss_fact`,
`result_read_handle_closed`, `schema`, `supervisor_exit_result`,
`supervisor_process_signaled`. It is retained only for semantic
`RESULT_PEER_LOST`, never as an authority result. The complete loss fact equals
the exit result, the result read handle is closed, diagnostic bytes are bounded
and drained to EOF, the supervisor is signaled, and the control-write end is
closed. No terminal output object, result EOF claim, authority envelope, or
controller-session result is constructed from this receipt.

`pontius-planner-launch-view-v1` is the sole native-to-Python invocation object.
Its root has exactly `authorization_sha256`, `dispatch_mode`, `dispatch_sha256`,
`input_projection_sha256`, `operation`, `operation_schedule_sha256`,
`planner_input_row_count`, `role`, `round`, `schedule_variant`, `schema`, and
`task`. Every field is derived by the trusted owner from the already accepted
dispatch. Planner input count is the exact number of `delivery=PLANNER` rows;
zero is valid.

The trusted bootstrap selects the exact `(module, callable)` row from the held
role projection, invokes it once after `RUNTIME_LOCKED`, and passes this view as
its sole argument. The view contains no selector, repository, table instance,
endpoint, ref, path, file identity, precondition, phase bundle, credential,
handle, or owner-only input. Python cannot choose its entry point or infer an
operation from input presence. The view's canonical identity is retained in
the lock attestation, schedule transcript, final revalidation, and runtime
evidence.

### 3.1 Operation schedule

An operation-schedule identity has exactly `byte_count`, `dispatch_mode`,
`operation`, `sha256`, and `variant`. Rows sort by operation, dispatch mode,
then variant. The runtime-owner array is empty. Every execution operation has
one `OBSERVATION_ONLY` row with variant `OBSERVE` and one or more closed
`MUTATION_ATTEMPT` variants selected by the exact operation precondition.

The bound document schema is `pontius-operation-schedule-v1`. Its root has
exactly `dispatch_mode`, `operation`, `role`, `schema`, `steps`, and `variant`.
A step has exactly:

| Key | Type |
| --- | --- |
| `argv_grammar_id` | closed ASCII identifier |
| `broker_session_template_byte_count` | `positive_count` or `null` |
| `broker_session_template_sha256` | `sha256` or `null` |
| `broker_session_required` | boolean |
| `config_prefix_id` | closed ASCII identifier |
| `effect` | schedule effect |
| `environment_grammar_id` | closed ASCII identifier |
| `ordinal` | positive integer, contiguous from one |
| `owner_request_id` | value allowed for the role |
| `repeat_kind` | `SINGLE` or `BOUNDED_REPEAT` |
| `repeat_limit` | `positive_count` |
| `repeat_source_id` | closed source ID or `null` |
| `result_schema` | closed schema literal |
| `stdin_grammar_id` | closed ASCII identifier |

Schedule effect is exactly `OWNER_READ`, `OWNER_ASSEMBLE`,
`LOCAL_READ`, `SCRATCH_WRITE`, `OBJECT_RESIDUE_WRITE`,
`AUTHORITY_REF_WRITE`, `REMOTE_READ`, or `REMOTE_WRITE`. An
observation-only schedule contains only `LOCAL_READ`, `OWNER_READ`,
`OWNER_ASSEMBLE`, `SCRATCH_WRITE`, and `REMOTE_READ`; scratch
writes target a new no-ref database outside the authority repository. A
mutation schedule may write unreachable
object residue, then has at most one `AUTHORITY_REF_WRITE` transaction and at
most one `REMOTE_WRITE`. If both occur, the exact local recovery-ref transaction
precedes the remote write, and a fresh decisive remote observation occurs
between them. Each network step requires a broker session.

A `SINGLE` step has `repeat_limit=1` and `repeat_source_id=null`. A
`BOUNDED_REPEAT` step names one source ID frozen by the role-operation set and a
plan-bound positive cap. Its population comes only from a complete canonical
operation-input projection, authorization/precondition inventory, or from a
deterministic raw-object walk
whose next member is parsed from the prior member. The trusted owner validates
the complete source relation and cap before starting each child. A planner may
propose object bytes, but cannot choose the population: the owner derives and
checks the exact authorization-required object rows. `AUTHORITY_REF_WRITE` and
`REMOTE_WRITE` are always `SINGLE`. A repeated network read receives a distinct
broker session for every actual child. Reaching a repeat cap before a complete
stop condition is a refusal; a prefix cannot satisfy the operation.

`stdin_grammar_id` is fixed by the same held step policy. It is
`OWNER_INTERNAL` for owner-only rows, `NONE` for a Git child with no stdin
payload, one of the exact raw-object stream grammars for a declared blob, tree,
or commit byte stream, or `GIT_UPDATE_REF_CREATE_LF_V1` for the sole local-ref
transaction. Only the latter may accompany `AUTHORITY_REF_WRITE`, and every
such step requires it. No argv, caller field, child request, or process output
may choose or alter the stdin grammar.

The repeat-source IDs are closed. `READ_INPUT_ROWS` expands exactly the complete
`delivery=PLANNER` population of the validated
`pontius-launch-input-projection-v1`.
`WRITE_OBJECT_ROWS` expands exactly the `PLANNER_STREAM` partition of the
validated `pontius-object-write-plan-v1` population. `READ_OBJECT_ROWS` expands
the complete bound `pontius-git-object-inventory-v1` population.
`PACKET_STATIC_ROWS` expands exactly the packet-build specification's complete
`STATIC_BLOB` population and is valid only for `HASH_HELD_BLOB` in
`FREEZE_PAIR`.
`FIRST_PARENT_WALK` starts at the bound tip, derives each next OID only by
strictly parsing the prior raw commit, and stops only at an expected anchor,
root, typed unavailable coordinate, or refusal. The accepted operation set fixes
which IDs each schedule may
use and their caps. No caller-defined iterator, file path, query, or stop
predicate is valid.
`PHASE_HISTORY_WALK` starts independently at the expected predecessor, derives
each next OID only from the prior strictly parsed raw commit, and stops only at
the phase-history object's validated `NO_TASK` baseline, typed unavailable
coordinate, or reserved cap-failure row. It is valid only for main-observation
schedules. The lineage and history walks have distinct plan caps and cannot
substitute for or truncate one another.

Every execution schedule begins with one `READ_OPERATION_INPUT`
`BOUNDED_REPEAT` over `READ_INPUT_ROWS`; an empty planner population expands to
zero children, while a nonempty planner population delivers every row once in sorted
order. That step has effect `OWNER_READ`, grammar ID `OWNER_INTERNAL`, no broker
session, config-prefix ID `OWNER_INTERNAL`, environment-grammar ID
`OWNER_INTERNAL`, and no process. No later step may read a file-backed operation
input through another route.
The planner's `READ_OPERATION_INPUT` request has null `source_item_sha256`;
step and repeat ordinal alone select the next held planner row. The reply, data-stream
descriptor, and expanded-step evidence return and bind that row digest. This is
the only repeated request whose source member is owner-selected after the
request envelope.

Every `OWNER_ASSEMBLE` step is `SINGLE`, has all four grammar IDs
exact `OWNER_INTERNAL`, requires no broker session, and starts no process.
Its result schema is fixed by the corresponding assembly or aggregate-
observation request contract.

`argv_grammar_id` selects an immutable argv template in the same held role
policy. Authorization fields may fill only typed slots already declared by that
template. The owner, never the role process, starts each scheduled child and
requires the exact step result before advancing. A missing schedule identity,
extra step, reordered step, wrong effect, or changed template refuses.

The two process-launch grammar IDs are exact `GIT_OFFLINE_V1` and
`GIT_NETWORK_V1`. A step with `broker_session_required=true` uses the network
environment and config prefix; every other process step uses the offline pair.
The offline pair contains no credential, HTTP, HTTPS-helper, askpass, broker,
or remote-helper route. No schedule may mix an environment grammar with the
other config prefix. The Git-boundary appendix defines both populations
byte-for-byte.

`pontius-schedule-execution-v1` records the concrete expansion. Its root has
exactly `broker_session_result_set_sha256`, `completion`, `dispatch_sha256`,
`expanded_steps`, `local_ref_transaction`, `local_ref_transaction_byte_count`,
`local_ref_transaction_sha256`, `object_write_plan`, `object_write_plan_sha256`,
`operation_schedule_sha256`, `schema`, and `transport_outcomes`. An expanded-
step row has exactly
`broker_session_result_sha256`, `broker_session_sha256`, `command_line`,
`config_prefix_id`, `effect`, `environment_grammar_id`, `environment_sha256`,
`git_stdin_write`, `owner_request_id`,
`process`, `repeat_ordinal`, `reply`, `request`, `result_schema`,
`result_sha256`, `source_item_sha256`, and `step_ordinal`. `process` is a
process binding or `null`; `request` and `reply` are the complete canonical owner-channel
envelopes for this coordinate and their predecessor and result equations must
hold;
`broker_session_sha256` is `sha256` for a network child and otherwise `null`;
`broker_session_result_sha256` follows the same nullability and names that
session's unique terminal result;
`source_item_sha256` is `sha256` for a repeated member and otherwise `null`.
For `OWNER_READ` or `OWNER_ASSEMBLE`, command line, environment, and process
are null. Owner-read consumes only the next already-held operation-input
source; owner-assemble consumes only prior accepted facts and still-held
sources. Every other expanded row has a complete
`pontius-windows-command-line-v1`, nonnull environment, and process binding.
Rows occur in step-ordinal then repeat-ordinal order. Single steps have repeat
ordinal one. Repeat ordinals are contiguous, never exceed the static cap, and
equal the complete validated source population or deterministic walk. Every
row repeats the static grammar, effect, request, and result schema and binds the
exact resolved argument array and raw command-line buffer, environment, held
process, and result.

The three `local_ref_transaction` fields are all nonnull exactly when the
selected mutation schedule contains `CREATE_BUILDER_TUPLE` or
`CREATE_INTEGRATION_ATTEMPT`, and otherwise all null. When present, the object
is the complete `pontius-local-ref-transaction-v1`, its byte count and digest
use canonical bytes plus LF, and all three equal the launch dispatch byte-for-
byte. An expanded row's `git_stdin_write` is nonnull exactly for a resumed local
transaction child whose owner stdin write began, and otherwise null. It is the
complete `pontius-git-stdin-write-v1` fact for that coordinate. `COMPLETE`
schedule execution and authority success require `write_state=COMPLETE`.
`ABORTED` retains `PREFIX` or `DIVERGENT` whenever a write began; a process-
creation, assignment, or pre-resume failure retains the intended transaction
at the execution root but has no invented write fact.

`completion` has exactly `boundary`, `coordinate`, `state`,
`terminal_broker_result_sha256`, `terminal_process_completion`,
`terminal_process_lifecycle_sha256`, and `termination_sha256`. State is `COMPLETE` or
`ABORTED`. For `COMPLETE`, boundary is `AFTER_SCHEDULE` and the other four
nullable fields plus `coordinate` are null; expanded rows are the complete
deterministic expansion. For
`ABORTED`, `termination_sha256` is nonnull and equals the complete cleanup
termination object. Boundary is `BEFORE_COORDINATE`, `AFTER_COORDINATE`, or
`AFTER_SCHEDULE`. `coordinate` is a complete observation-primitive coordinate
for the first unaccepted row and is nonnull exactly for the two coordinate
boundaries. Expanded rows form the exact contiguous prefix strictly before that
coordinate for `BEFORE_COORDINATE`, through that coordinate for
`AFTER_COORDINATE`, or through the complete schedule for `AFTER_SCHEDULE`.
`terminal_process_completion` is the complete process-completion-facts object
exactly when the boundary row obtained an assigned, resumed process binding and
complete terminal facts; it is otherwise null. If required
terminal facts cannot be assembled, neither this object nor semantic cleanup can
complete and the host-failure route applies. When the boundary is after that
row, its process binding and completion equal the expanded result. Missing, extra,
skipped, reordered, duplicate, or post-boundary rows invalidate the object.
`terminal_process_lifecycle_sha256` is nonnull exactly when `CreateProcessW`
succeeded for the boundary coordinate and equals that row in the cleanup's
complete process-lifecycle set. It is required even when Job assignment failed,
the primary thread never resumed, and no process binding or process-completion
fact exists. No other lifecycle row may fall outside the worker plus expanded-
prefix relation.
`terminal_broker_result_sha256` is nonnull exactly when the boundary network
coordinate created a successful broker reservation. It equals the
`result_sha256` of that reservation's unique tagged terminal row in
`broker_session_result_set_sha256`: a pre-session result when no concrete
session completed, or a session result otherwise. It is required even when
`CreateProcessW` failed, Job assignment failed, the primary thread never
resumed, or the coordinate has no expanded-step row. A boundary with no
successful reservation has null. No reservation may exist without exactly one
terminal row.

When `terminal_broker_result_sha256` names a pre-session result, its reason and
the same `ABORTED` completion have this exact relation:

| Pre-session reason | Required stage and process evidence |
| --- | --- |
| `PROCESS_CREATE_FAILED` | Rule 1 below |
| `JOB_ASSIGNMENT_FAILED` | Rule 2 below |
| `PRE_RESUME_VALIDATION_FAILED` | Rule 3 below |
| `WALL_EXPIRED` | Rule 4 below |
| `CANCELLED` | Rule 5 below |
| `CHANNEL_LOST` | Rule 6 below |
| `BROKER_FAILURE` | Rule 7 below |

1. `PROCESS_CREATE_FAILED` uses stage `PROCESS_CREATE`, a nonzero Win32 error,
   and an exact environment boundary row with `launch_state=CREATE_FAILED` and
   null lifecycle digest. Terminal lifecycle digest and process completion are
   null because `CreateProcessW` did not succeed.
2. `JOB_ASSIGNMENT_FAILED` uses stage `JOB_ASSIGNMENT`. Its environment row is
   `CREATE_SUCCEEDED`; lifecycle has assignment `FAILED`, null Job binding and
   membership, primary thread not resumed, preassignment process termination,
   process signal, `WAIT_OBJECT_0`, measured exit, and both handles closed.
   Process completion is null.
3. `PRE_RESUME_VALIDATION_FAILED` uses stage `PRE_RESUME_VALIDATION`. Its
   environment row is `CREATE_SUCCEEDED`; lifecycle has assignment `ASSIGNED`,
   membership true, primary thread not resumed, Job-object termination, process
   signal, Job active-zero, and both handles closed. Process completion is null.
4. `WALL_EXPIRED` repeats the wall fact byte-for-byte in cleanup termination
   and the pre-session result. Lifecycle is null or matches the last stage and
   terminal method.
5. `CANCELLED` has exact cleanup termination
   `CANCELLED/AUTHENTICATED_CONTROLLER_CANCEL`; lifecycle follows rule 4.
6. `CHANNEL_LOST` has exact cleanup termination
   `CONTROLLER_CHANNEL_LOST/RETAINED_CONTROLLER_CHANNEL_AND_PROCESS`. Its
   channel-loss fact is byte-equal in result and termination; lifecycle follows
   rule 4.
7. `BROKER_FAILURE` has exact cleanup termination
   `BROKER_FAILURE/BROKER_SUBSYSTEM`; lifecycle follows rule 4.

A successful process creation with lifecycle `assignment_state=NOT_ATTEMPTED`
cannot be relabeled as any of the three structural failure reasons. Except when
an independently typed wall, cancellation, channel-loss, or broker cause terminated that
exact stage, it is host failure and yields no semantic envelope. Cross-reason,
cross-stage, cross-lifecycle, cross-trigger, or cross-result-digest substitution
invalidates the completion.

`object_write_plan` is a complete `pontius-object-write-plan-v1` object and its
digest is over those canonical bytes plus LF, or both fields are null. They are
nonnull exactly when this schedule variant may store a new semantic object in
the authority database: `CREATE_LOCAL_TUPLE`, `ADOPT_LOCAL_TUPLE`,
`BUILD_OBJECTS`, or `CREATE_ATTEMPT_AND_PUSH`. The plan's authorization,
operation, object population, and source input equal the dispatch and all
expanded object-write rows. Every returned stored-object fact is consumed once
by that complete plan. In a `COMPLETE` execution every plan row has its required
write result. In an `ABORTED` execution only rows reached by the contiguous
prefix require results; every returned result is still planned and no unplanned
object is allowed. `PUSH_EXISTING_ATTEMPT` and every
schedule without an object write have both fields null.

`transport_outcomes` is empty when no network child ran. Otherwise it contains
exactly one complete `pontius-git-transport-outcome-v1` per network process for
which decisive assembly completed,
sorted by step then repeat ordinal. Each is the result of an
`ASSEMBLE_TRANSPORT_OUTCOME` owner-only row that occurs only after the matching
process completion and required fresh post-observation rows. Its three digests
equal those earlier immutable results. Every network mutation or fetch schedule
contains this assembly step before terminal success or refusal; the process-
completion reply is never revised in place. A `COMPLETE` execution has one for
every network process. An `ABORTED` execution has the exact produced population
and may omit only the boundary process whose decisive assembly could not
complete; no later process exists.
Only a network process with lifecycle method `NATURAL_EXIT` and a return before
the active deadline may execute its already scheduled read-only observation
suffix. A wall expiry, cancellation, or other terminal cause aborts at that
coordinate: no later child or network row executes, no cleanup-reserve query is
invented, authority state remains unknown, and a later separately authorized
`OBSERVATION_ONLY` dispatch is required for classification.
`broker_session_result_set_sha256` always names the complete canonical terminal
set for every successful reservation created by this execution prefix or its
boundary coordinate, including the canonical empty set when no reservation was
created. Each reservation has exactly one tagged session or pre-session result.
Failure to close that lifecycle makes cleanup evidence unavailable and cannot
be represented as an authority refusal.

For a network step, `broker_session_required` is true and both template identity
fields are nonnull; for every other step it is false and both are null. The owner
validates the template, creates the session reservation and listening pipe,
and builds the exact child environment before process creation. It completes
the process-bound concrete session only after the scheduled root Git process
exists suspended and has a held process identity. Resume is forbidden until
the reservation, environment, process, Job, template, and table all agree.

`pontius-operation-schedule-set-v1` has exactly `identities`, `role`, and
`schema`. `identities` is the complete sorted operation-schedule-identity array
from the matching role source projection. Its rows and order are byte-for-byte
equal; omission, addition, substitution, or reordering refuses.

`pontius-role-operation-set-v1` has exactly `operations`,
`owner_request_contracts`, `owner_request_ids`, `planner_entrypoints`, `role`,
and `schema`.
`owner_request_contracts` is the role's stored owner-request population. A row
has exactly `facts_schema`, `input_mode`, `output_mode`, `owner_request_id`,
`payload_schema`, and `result_schema` and equals the closed contract above.
An operation row has exactly `authorization_schema`,
`decisive_transport_rules`, `mutation_schedules`, `observation_contracts`,
`observation_schedule_sha256`, `operation`,
`owner_request_ids`, `precondition_schema`, `reconciliation_schema`,
`repeat_source_ids`, `result_schema`, and `route_input_contracts`. An
observation-contract row has
exactly `kind` and `schema` and equals the operation population in section 14.
`mutation_schedules` is the nonempty
ordered array of
`MUTATION_ATTEMPT` schedule identities for that operation. The observation
digest names its sole `OBSERVE` identity. Rows occur in the role source
projection's exact operation-ID order, and every identity names the matching
row in the complete operation-schedule set. Each owner-request array is the
exact ordered subset used by those schedules; the unique union of all rows
equals the source projection's complete owner-request-ID population, and its
comparison order is the source projection's order. Authorization, precondition,
result, and reconciliation schema literals equal the closed operation contracts
in this appendix. `repeat_source_ids` is the sorted unique exact population
referenced by the operation's schedules. A differing operation map requires a
new reviewed source projection.

A decisive-transport-rule row has exactly `operation_schedule_sha256` and
`selection`. There is one row for every observation or mutation schedule that
contains a network child and none for an offline-only schedule; rows sort by
schedule digest. `selection` is exact `FIRST_NON_SUCCESS_ELSE_LAST`. At runtime,
the owner scans that schedule execution's complete transport-outcome population
in step/repeat order and selects the first outcome other than `SUCCESS`, or the
last row when all are `SUCCESS`. An empty population has no decisive outcome.
No role process, authority envelope, or campaign expectation can choose a
different coordinate.

A route-input-contract row has exactly `input_id`, `normal_schema`, and
`rehearsal_schema`. Rows sort by input ID. `ADOPT_PAIR` and `PUBLISH_PAIR` each
have the sole row `BUILDER_INTENT`, mapping normal
`pontius-builder-intent-v1` to rehearsal
`pontius-rehearsal-builder-intent-fixture-v1`. `BUILD_REVIEW_OUTPUT` has rows
for `CANDIDATE_AUTHOR_SET`, `RECEIPT`, and `ROUND_REVIEW_AUTHOR_SET`.
`PUBLISH_REVIEW_OUTPUT` has rows for `CANDIDATE_AUTHOR_SET` and
`ROUND_REVIEW_AUTHOR_SET`. `RECEIPT` maps normal
`pontius-utility-review-receipt-v1` to rehearsal
`pontius-utility-bootstrap-review-receipt-v1`; each author-set row maps its
normal named schema to rehearsal `pontius-utility-author-set-v1`. Every other
operation has an empty route-input-contract array. The selected route kind chooses the
schema; a normal/rehearsal substitution refuses even when bytes or digests
otherwise agree. Paired production and rehearsal tables bind one byte-identical
operation set containing both closed branches.

`planner_entrypoints` equals the source projection's complete same-role array
byte-for-byte. It is not inferred from imported module names.

Every operation's observation schema is exact
`pontius-operation-observation-set-v1`; its `observation_contracts` select that
set's complete inner population. The authorization, precondition, result, and
reconciliation schema tuple is exact for each operation:

- `FREEZE_PAIR`: authorization `pontius-transition-authorization-v1`;
  precondition `pontius-operation-precondition-v1`; result
  `pontius-builder-tuple-observation-v1`; reconciliation
  `pontius-operation-observation-set-v1`.
- `ADOPT_PAIR`: authorization `pontius-transition-authorization-v1`;
  precondition `pontius-operation-precondition-v1`; result
  `pontius-builder-tuple-observation-v1`; reconciliation
  `pontius-operation-observation-set-v1`.
- `BUILD_REVIEW_OUTPUT`: authorization `pontius-transition-authorization-v1`;
  precondition `pontius-operation-precondition-v1`; result
  `pontius-object-build-receipt-v1`; reconciliation
  `pontius-operation-observation-set-v1`.
- `FETCH_MAIN_INPUTS`: authorization `pontius-transition-authorization-v1`;
  precondition `pontius-operation-precondition-v1`; result
  `pontius-main-input-fetch-receipt-v1`; reconciliation
  `pontius-operation-observation-set-v1`.
- `BUILD_MAIN_OVERLAY`: authorization `pontius-transition-authorization-v1`;
  precondition `pontius-operation-precondition-v1`; result
  `pontius-object-build-receipt-v1`; reconciliation
  `pontius-operation-observation-set-v1`.
- `PUBLISH_PAIR`: authorization `pontius-transition-authorization-v1`;
  precondition `pontius-operation-precondition-v1`; result
  `pontius-remote-pair-observation-v1`; reconciliation
  `pontius-operation-observation-set-v1`.
- `FETCH_FOR_ADOPTION`: authorization `pontius-transition-authorization-v1`;
  precondition `pontius-operation-precondition-v1`; result
  `pontius-adoption-receipt-v1`; reconciliation
  `pontius-operation-observation-set-v1`.
- `PUBLISH_REVIEW_OUTPUT`: authorization `pontius-transition-authorization-v1`;
  precondition `pontius-operation-precondition-v1`; result
  `pontius-review-output-observation-v1`; reconciliation
  `pontius-operation-observation-set-v1`.
- `INTEGRATE_PACKET`: authorization `pontius-transition-authorization-v1`;
  precondition `pontius-operation-precondition-v1`; result
  `pontius-main-observation-v1`; reconciliation
  `pontius-operation-observation-set-v1`.
- `FINALIZE_REVIEWS`: authorization `pontius-review-finalizer-authorization-v1`;
  precondition `pontius-operation-precondition-v1`; result
  `pontius-main-observation-v1`; reconciliation
  `pontius-operation-observation-set-v1`.
- `PUBLISH_DISPOSITION`: authorization `pontius-transition-authorization-v1`;
  precondition `pontius-operation-precondition-v1`; result
  `pontius-main-observation-v1`; reconciliation
  `pontius-operation-observation-set-v1`.

These are literal values in the canonical operation rows; “same as another
row” is never serialized or inferred.

The mutation-variant population is exact:

| Operation | Mutation variants in stored order |
| --- | --- |
| `FREEZE_PAIR` | `CREATE_LOCAL_TUPLE` |
| `ADOPT_PAIR` | `ADOPT_LOCAL_TUPLE` |
| `BUILD_REVIEW_OUTPUT` | `BUILD_OBJECTS` |
| `FETCH_MAIN_INPUTS` | `FETCH_INPUT_OBJECTS` |
| `BUILD_MAIN_OVERLAY` | `BUILD_OBJECTS` |
| `PUBLISH_PAIR` | `CREATE_REMOTE_PAIR` |
| `FETCH_FOR_ADOPTION` | `FETCH_ADOPTION_OBJECTS` |
| `PUBLISH_REVIEW_OUTPUT` | `CREATE_REVIEW_OUTPUT` |
| `INTEGRATE_PACKET` | `CREATE_ATTEMPT_AND_PUSH`, `PUSH_EXISTING_ATTEMPT` |
| `FINALIZE_REVIEWS` | `PUSH_MAIN` |
| `PUBLISH_DISPOSITION` | `PUSH_MAIN` |

Every operation also has the sole observation variant `OBSERVE`. A variant is
part of the schedule bytes and identity; it is not a caller-selected branch.

### 3.2 Role-table instance and broker session

`pontius-role-table-instance-v1` has exactly `argv_grammars`,
`credential_audiences`, `endpoints`, `instance_kind`, `literal_delta_sha256`,
`operation_schedule_set_sha256`, `operation_set_sha256`, `refs`, `role`, and
`schema`.
`instance_kind` is `OFFLINE`, `PRODUCTION`, or `REHEARSAL`. An argv-grammar row has exactly
`byte_count`, `grammar_id`, and `sha256`; rows sort by grammar ID and cover every
schedule grammar once.

An endpoint row has exactly `endpoint_id`, `literal_https_url`,
`repository_id`, `server_capability_class_sha256`, and `slot_id`; its URL field
has type `literal_https_url`. An
audience row has exactly `account_name`, `audience_id`, `endpoint_id`,
`repository_id`, and `slot_id`; account name is public. A ref row has exactly
`derivation_id`, `kind`, `literal_prefix`, `resolution_class`, and `slot_id`. A
slot ID is a frozen ASCII identifier matching
`[A-Z][A-Z0-9_]{0,63}` and is stable across paired production and rehearsal
tables. Arrays sort by slot ID and are unique. Values equal the role's closed
operations; no wildcard, remote name, relative ref, URL rewrite, or caller
string is valid.
`kind` is a closed semantic ref role and `derivation_id` is one of the fixed
ref grammars in section 1. `resolution_class` and the other two semantic fields
equal one exact section 1.3 triple. A parameterized grammar appends only its
canonical task, round, reviewer ordinal, authorization digest, selected
rehearsal case, task binding, and fixed leaf components to `literal_prefix`.
The table contains no future round's or campaign case's full ref.

For `SELECTOR_PINNED_STABLE`, a normal route derives the full ref from the
production table and complete round preregistration and requires byte equality
with that ref's exact preregistration field. A rehearsal route derives it from
the rehearsal table, selected campaign case, and binding and requires byte
equality with the unique matching stable selector row. For
`ROUTE_DERIVED_STABLE`, a normal route derives the full ref from the table plus
the preregistration's task and round; no preregistration full-ref field exists.
A rehearsal route derives and matches the same unique stable selector row.
For `AUTHORIZATION_DERIVED`, the owner first validates the table descriptor; a
rehearsal route also matches the selector's unique attempt-ref descriptor. Only
after the complete transition authorization digest exists does the owner append
that digest and derive the intent and result refs. No full attempt ref occurs in
a selector, preregistration, authorization input, or caller value.

For every rehearsal task-scoped ref, the binding is the authorization's
`rehearsal_task_binding_id`; it is null only for the case-shared `HANDOFF_MAIN`
slot. Observation, ref-update set, argv, refspec, and mutation validation all
consume the one class-valid result. No other source can populate a ref.
`operation_schedule_set_sha256` and `operation_set_sha256` equal the complete
bound documents in the selected runtime projection. Their role, operation,
owner-request, schedule, grammar, endpoint, audience, and ref populations must
close over this table exactly; an unreferenced capability or unresolved member
refuses.

`pontius-authorized-literal-delta-v1` has exactly `entries`, `role`, and
`schema`. An entry has exactly `array`, `field`, `production_value`,
`rehearsal_value`, and `slot_id`. `array` is `credential_audiences`,
`endpoints`, or `refs`. The allowed fields are respectively
`account_name|audience_id|endpoint_id|repository_id`,
`endpoint_id|literal_https_url|repository_id`, or `literal_prefix`. Values conform to the
field's scalar domain and differ. Rows sort by array, slot ID, then field; each
coordinate occurs once.

Publisher and integrator each have exactly one `PRODUCTION` and one `REHEARSAL`
table with the same nonempty `literal_delta_sha256`. The two tables have equal
role, schema, operation-set digest, operation-schedule-set digest, argv-grammar
array, array lengths, slot-ID population, and nondelta fields. Apart from
`instance_kind`, every unequal scalar leaf in `credential_audiences`,
`endpoints`, or `refs` must match exactly one delta entry, and every delta entry
must match exactly one unequal leaf. Slot IDs, ref kinds, and derivation IDs
cannot differ. No production URL, endpoint ID, repository ID, ref prefix,
account name, or audience
ID may occur in any rehearsal capability field. The endpoint row's server-
capability-class digest is a nondelta field and is equal in each production and
rehearsal pair. Builder has one `OFFLINE`
table and the canonical empty delta; it has no rehearsal table. The complete
delta-document digest is `literal_delta_sha256`; the document does not contain
either table digest and therefore creates no identity cycle.

`pontius-broker-session-template-v1` has exactly
`credential_audience_slot_id`, `deadline_policy`, `endpoint_slot_id`,
`operation`, `prompt_policy`, `ref_slot_ids`, `role`, `schema`, and
`step_ordinal`. Deadline policy is exact `OUTER_DISPATCH_ONLY`; the template
contains no numeric wall. Ref slot IDs are the closed ordered population for
the operation.
`prompt_policy` is a bound-document identity for
`pontius-askpass-prompt-policy-v1`. That policy has exactly `grammars`, `rules`,
and `schema`; its sole rule has exactly `kind`, `ordinal`,
`prompt_grammar_id`, and
`response_source`. Kind is exact `PASSWORD_FOR_SELECTED_ENDPOINT`, ordinal is
one, response source is exact `ONE_SHOT_SECRET`, and the grammar ID selects the
sole complete `pontius-askpass-prompt-grammar-v1` object in `grammars`.

`pontius-askpass-prompt-grammar-v1` has exactly `account_encoding`, `encoding`,
`grammar_id`,
`password_prefix`, `password_suffix`, `schema`, and
`username_prompt_forbidden`. Encoding is exact `UTF8`; account encoding is
exact `RFC3986_USERINFO_PERCENT_ENCODED`; prefix and suffix are exact ASCII
`Password for '` and `': `; and username-prompt-forbidden is true. The trusted
owner supplies the selected public `account_name` to Git through the sole fixed
command-line `credential.username` assignment. The expected prompt bytes are
prefix, the selected endpoint URL with that percent-encoded account inserted
as userinfo after `https://`, and suffix, with no NUL, CR, or LF. The broker
compares the adapter's complete prompt argument byte-for-byte before issuing a
secret request. Any username prompt, decoding or case normalization, absent or
different account, unselected URL, extra byte, or second invocation refuses.
The policy names no template, schedule, table, endpoint, account, or capability
literal; only the dispatch-selected table supplies those public values.
The slot coordinates exist in both paired table instances. The template is
capability-literal neutral and therefore has the same bytes in production and
rehearsal schedules. It contains no URL, repository, ref, account, audience,
table identity, secret, pipe, process, dispatch, or response value. The trusted
owner resolves its slots only through the dispatch-selected table instance.

`pontius-job-binding-v1` has exactly `active_process_limit`, `cpu_time_ms`,
`dispatch_nonce`, `job_kind`, `job_nonce`, `limit_row_sha256`, `memory_bytes`,
`policy`, `repeat_ordinal`, `schema`, and `step_ordinal`. Job nonce is fresh and
has type `nonce`; `policy` is the bound-document identity of the selected Job
process-policy leaf. Job kind is `ROLE_PROCESS` or `SCHEDULE_STEP`.
`ROLE_PROCESS` requires the exact `ROLE_JOB` leaf and `SCHEDULE_STEP` requires
the exact `SCHEDULE_JOB` leaf; substitution refuses. Both
ordinals are null for the role Job and positive counts for a scheduled Job.
Active-process limit is exact one for the role Job and equals the launch
dispatch's `schedule_active_process_limit` for every scheduled Job. The
CPU time, memory, and limit-row digest equal the selected dispatch for both Job
kinds. These are per-Job caps; the design makes no aggregate CPU or memory
claim across separate schedule Jobs. The supervisor configures and queries all
three limits after Job creation and before process resume; mismatch refuses.
This canonical object is a run-local label for one retained Job handle, not a
claimed queryable Windows object identity.

`pontius-job-binding-set-v1` has exactly `bindings`, `dispatch_sha256`, and
`schema`. It contains the role binding first, then every created scheduled Job
binding in step/repeat order. Each retained Job handle has exactly one binding
and vice versa; unknown, duplicate, or missing handles invalidate the set.

`pontius-job-configured-limit-observation-v1` has exactly
`active_process_limit`, `cpu_time_limit_100ns`, `job_binding`,
`job_memory_limit_bytes`, `limit_flags_hex`, `limit_row_sha256`, and `schema`.
It is produced by querying the exact retained Job handle after configuration.
The active-process value equals the binding. CPU time is the overflow-checked
product of its `cpu_time_ms` and 10,000; memory equals `memory_bytes`; both
enabled flags and the active-process flag occur in the exact frozen mask and no
unknown limit flag is set. The row digest equals the binding and launch.

`pontius-job-configured-limit-set-v1` has exactly `dispatch_sha256`, `rows`,
and `schema`. Rows are complete configured-limit observations in the exact
job-binding-set order and form a bijection with it. Runtime evidence and final
revalidation query every still-held Job again and require the same set.

`pontius-job-limit-trigger-fact-v1` has exactly `configured_limits`,
`event_code`, `kind`, `observed_value`, `schema`, and `source`.
`configured_limits` is the complete observation for the affected Job; source is
exact `JOB_COMPLETION_PORT_AND_QUERY`. For kind `CPU`, event code is exact
`JOB_OBJECT_MSG_END_OF_JOB_TIME` and observed value is queried `TotalUserTime`
alone in 100-nanosecond units, greater than or equal to the configured CPU
limit. Kernel time is not added. For kind `MEMORY`, event code is exact
`JOB_OBJECT_MSG_JOB_MEMORY_LIMIT` and observed value is queried peak Job memory
in bytes, greater than or equal to the configured memory limit. An unknown,
ambiguous, missing, or binding-mismatched event cannot classify a limit.

`pontius-job-quiescence-set-v1` has exactly `dispatch_sha256`, `jobs`, and
`schema`. A job row has exactly `active_process_count` and `job_binding`;
`job_binding` is the complete canonical binding and active process count is
exact zero. Rows equal the complete job-binding set in the same order and are
produced only by querying each specific retained Job handle after termination.

A process binding has exactly `creation_time_hex`, `executable`, `job_binding`,
and `process_id`. `creation_time_hex` is 16 lowercase hexadecimal characters,
`executable` is a `file_identity`, `job_binding` is the complete canonical
object above, and `process_id` is a positive count. The held process handle
reproduces PID, creation time, and image. The supervisor separately requires
`IsProcessInJob(process_handle, held_job_handle)` to return exact true for the
specific retained Job handle associated with `job_binding`; no pseudo-identity
is inferred from the process.

`pontius-process-lifecycle-v1` records every successful root `CreateProcessW`,
including a suspended process that never joins a Job. It has exactly
`assignment_state`, `creation_time_hex`, `dispatch_nonce`, `executable`,
`exit_code_hex`, `job_binding`, `job_membership`,
`primary_thread_handle_closed`, `primary_thread_id`,
`primary_thread_resumed`, `process_handle_closed`, `process_id`,
`process_scope`, `process_signaled`, `repeat_ordinal`, `schema`, `step_ordinal`,
`termination_method`, and `wait_result`. Scope is `WORKER` or `GIT_CHILD`;
worker ordinals are null and Git-child ordinals are positive. PID, creation time,
and executable come from the retained process handle; primary-thread ID comes
from the retained creation handle. Both handles remain owned by the supervisor.

Assignment state is `NOT_ATTEMPTED`, `ASSIGNED`, or `FAILED`. Only `ASSIGNED`
has a complete Job binding and exact `job_membership=true`; those values equal
the existing process binding and a held-handle `IsProcessInJob` query before any
resume. The other states have both fields null. Primary-thread resume is true
only after assignment and every pre-resume check; assignment failure or an
earlier seam can never resume it.

Termination method is `NATURAL_EXIT`, `TERMINATE_PROCESS_PREASSIGNMENT`,
or `TERMINATE_JOB_OBJECT`. `TERMINATE_PROCESS_PREASSIGNMENT` is
mandatory when assignment is not successful; a Job-zero query cannot substitute.
The assignment/resume/method truth table is total:

| Assignment | Resumed | Allowed termination method |
| --- | --- | --- |
| `NOT_ATTEMPTED` | false | `TERMINATE_PROCESS_PREASSIGNMENT` |
| `FAILED` | false | `TERMINATE_PROCESS_PREASSIGNMENT` |
| `ASSIGNED` | false | `TERMINATE_JOB_OBJECT` |
| `ASSIGNED` | true | `NATURAL_EXIT` or `TERMINATE_JOB_OBJECT` |

No other combination is valid. In particular, a suspended assigned process
cannot exit naturally, and a Job-assigned process cannot be represented as a
direct preassignment termination.
Every terminal lifecycle has `process_signaled=true`, `wait_result=WAIT_OBJECT_0`,
an eight-lowercase-hex-digit exit code measured from that held process, and both
handle-closed booleans true. The supervisor waits for the process signal before
closing the primary-thread handle and then the process handle. An unsignaled,
wrong-PID, reused-creation-time, premature-membership, resume-after-failure, or
closure-before-wait row is invalid.

`pontius-process-lifecycle-set-v1` has exactly `dispatch_sha256`, `rows`, and
`schema`. Rows contain the worker first when created, then every successful Git
root creation in step/repeat order, including an unassigned terminal-boundary
process. The root digest equals the selected launch dispatch and every row's
nonce equals that launch's nonce. An unassigned Git row's step and repeat
ordinals equal the ABORTED completion boundary coordinate and its lifecycle
digest equals the boundary field. It is a bijection with actual successful
`CreateProcessW` returns and
contains no descendant helper or adapter. Every assigned row matches exactly one
role or schedule Job binding; every schedule process binding matches exactly one
assigned row. Terminal evidence may complete only when every row is signaled.
For each resumed Git row with process-completion facts, `NATURAL_EXIT` is valid
exactly with completion termination `EXITED`, and the completion's numeric DWORD
equals the lifecycle's zero-padded hexadecimal exit code. A
`TERMINATE_JOB_OBJECT` row instead has a non-`EXITED` completion whose cause and
typed trigger facts equal cleanup termination for that same process and Job.
An assigned-but-not-resumed or preassignment row has no process-completion fact
and is bound only by the terminal lifecycle digest. Cross-cause or cross-exit-
code pairs are invalid.

`pontius-broker-secret-frame-policy-v1` has exactly `eof_rule`,
`header_bytes`, `length_encoding`, `max_frame_bytes`, `payload_rule`, and
`schema`. Values are exact:

```text
eof_rule = SERVER_FLUSH_DISCONNECT_CLOSE_AFTER_EXACT_FRAME
header_bytes = 4
length_encoding = UINT32_LITTLE_ENDIAN_PAYLOAD_BYTE_COUNT
payload_rule = NONEMPTY_BYTES_EXCLUDING_NUL_CR_LF
```

`max_frame_bytes` is the positive plan-bound pipe output cap, is at least five,
and is less than `2^32`. A secret response consists of exactly four header bytes
encoding `L`, followed by exactly `L` opaque credential bytes, where
`1 <= L <= max_frame_bytes - 4`; secret bytes and any secret-derived digest are
never canonical. The server writes that one frame, runs monitored
`FlushFileBuffers` on the same retained server handle until the client has read
every pipe byte, then calls `DisconnectNamedPipe` and closes the handle. A
manual-reset event guards the overlapped write and a dedicated broker flush
thread guards the synchronous flush; both are registered with the active timer.
Timeout, cancellation, or peer loss cancels and joins the exact operation and
can never count as delivery. The server sends no second frame. The adapter
accumulates exactly four bytes
across any number of partial overlapped reads under the active deadline, decodes
and validates `L`, accumulates exactly `L` payload bytes across any number of
partial reads, then performs the bounded EOF check. Exact zero-byte
`ERROR_BROKEN_PIPE` after the payload is the sole accepted EOF. EOF before all
header or payload bytes, zero or over-cap length, NUL/CR/LF payload, any trailing
byte, a second frame, a non-EOF read failure, or active-deadline termination
after a prefix is `BROKER_FAILURE` or `WALL_EXPIRED` with zero responses. Every
broker-owned partial header or payload buffer is zeroed before terminal
evidence. On normal adapter completion its private payload and stdout buffers
are zeroed; on forced termination, process teardown is recorded and no physical
adapter-memory-zeroization claim is made. Read and write fragmentation cannot
change the reconstructed payload.

`pontius-broker-pipe-policy-v1` has exactly `acl_policy_sha256`,
`adapter_granted_access_hex`, `client_access`,
`client_creation_disposition`, `client_flags`, `client_share_mode`,
`input_buffer_bytes`, `max_instances`, `output_buffer_bytes`,
`pipe_mode_flags`, `response_frame_policy`, `schema`, `security_descriptor_sha256`,
`server_flush_mode`, `server_granted_access_hex`, `server_handle_inheritable`,
`server_open_mode_flags`, and `server_write_mode`. Values are exact:

```text
client_access = GENERIC_READ
client_creation_disposition = OPEN_EXISTING
client_flags = [FILE_FLAG_OVERLAPPED]
client_share_mode = 0
input_buffer_bytes = 0
max_instances = 1
pipe_mode_flags = [PIPE_READMODE_BYTE, PIPE_REJECT_REMOTE_CLIENTS,
                   PIPE_TYPE_BYTE, PIPE_WAIT]
server_handle_inheritable = false
server_flush_mode = DEDICATED_BLOCKING_THREAD
server_open_mode_flags = [FILE_FLAG_FIRST_PIPE_INSTANCE,
                          FILE_FLAG_OVERLAPPED, PIPE_ACCESS_OUTBOUND]
server_write_mode = OVERLAPPED
```

`response_frame_policy` is the complete canonical
`pontius-broker-secret-frame-policy-v1` object and its `max_frame_bytes` equals
`output_buffer_bytes`. `output_buffer_bytes` is the positive plan-bound
one-response frame cap; it is not a byte-pipe message boundary.
`acl_policy_sha256` equals the process policy's exact `ASKPASS_PIPE_ACL` leaf;
`security_descriptor_sha256` equals that leaf's self-relative descriptor.
The descriptor has only SYSTEM and controller-owner ACEs and no package SID,
All Application Packages, Everyone, or Anonymous ACE. Server granted access is
exact `00120116`; the adapter `GENERIC_READ` open produces exact mapped granted
access `00120089`. The outbound server end is
write-only; the adapter client is read-only. Both connect and read use bounded
overlapped operations with nonnull `OVERLAPPED` structures and manual-reset
events owned by their caller.

`pontius-broker-io-handle-binding-v1` has exactly
`broker_process_binding_sha256`, `handle_hex`, `operation_nonce`,
`pipe_name_sha256`, `reservation_sha256`, `schema`, `server_instance_nonce`,
and `session_sha256`. Handle is the retained server handle owned by the named
broker process. Pipe name, instance nonce, reservation, and session equal the
exact credential-bearing broker session; operation nonce is fresh within that
session. The binding is captured before I/O begins and the same handle remains
held through join, disconnect, and close.

`pontius-broker-flush-thread-binding-v1` has exactly
`broker_process_binding_sha256`, `deadline_sha256`, `operation_nonce`,
`reservation_sha256`, `runtime_owner_file_identity`, `schema`,
`server_handle_identity`, `session_sha256`, `thread_handle_hex`, and
`thread_id`. The runtime owner creates the retained noninheritable thread for
one `FlushFileBuffers` call on the exact server handle. Reservation, session,
deadline, broker process, server-handle identity, and operation nonce equal the
I/O handle binding and selected broker session. The thread handle remains open
until the thread is signaled and joined. Cancellation targets that exact handle
with `CancelSynchronousIo`; a different thread, handle, operation, or session
refuses.

`pontius-broker-flush-thread-terminal-v1` has exactly `binding_sha256`,
`cancel_api`, `cancel_error_hex`, `cancel_requested`, `cancel_succeeded`,
`exit_code_hex`, `flush_error_hex`, `flush_succeeded`,
`handle_close_error_hex`, `handle_close_succeeded`, `join_completed`,
`join_wait_result`, `schema`, `signal_observed`, `terminal_qpc_tick_hex`, and
`wait_api`. Binding digest names the complete flush-thread binding. Wait API is
exact `WaitForSingleObject`; join result is exact `WAIT_OBJECT_0`; signal, join,
and handle-close-success Booleans are true. Cancel and flush errors are null or
exactly eight lowercase hexadecimal digits; exit code is exactly eight
lowercase hexadecimal digits; terminal tick is exactly 16 lowercase
hexadecimal digits. Natural completion
has cancel-requested false and all three cancel fields null. Flush-succeeded is
true, flush error is null, and exit code is exact `00000000`. Cancellation has
cancel-requested true and cancel API exact `CancelSynchronousIo`; either cancel-
succeeded is true with null error or it is false with exact `00000490`
(`ERROR_NOT_FOUND`) because completion won the race. Effective cancellation has
flush-succeeded false, flush error and exit code exact `000003e3`
(`ERROR_OPERATION_ABORTED`). A race-completed success retains the cancellation-
return fields and obeys only the natural flush-success/error/exit fields. A
cancellation-requested other failure retains the cancellation-return fields,
has flush-succeeded false, and has one exact nonzero flush error other than
`000003e3` equal to exit code. A noncancellation failure obeys natural cancel
nullability and the same other-failure outcome fields. Handle-close error is null on the
successful `CloseHandle` result. Terminal tick is captured after signal and
before handle close. The join completes on the retained thread handle after
natural completion or `CancelSynchronousIo` terminal completion; the handle
closes only afterward. A timeout, failed wait, live thread, early close,
substituted binding, or caller-authored joined Boolean refuses.

`pontius-broker-overlapped-write-terminal-v1` has exactly `binding_sha256`,
`bytes_completed`, `cancel_api`, `cancel_error_hex`, `cancel_requested`,
`cancel_succeeded`, `completion_api`, `completion_error_hex`,
`completion_succeeded`, `event_handle_hex`, `event_signaled`,
`overlapped_operation_nonce`,
`overlapped_retired`, `retirement_qpc_tick_hex`, `schema`, `wait_api`, and
`wait_result`. Binding and OVERLAPPED nonce equal the exact I/O binding.
Event handle equals the retained manual-reset event in the outer I/O object.
Wait API is exact `WaitForSingleObject`, wait result is exact `WAIT_OBJECT_0`,
event signaled is true, and completion API is exact `GetOverlappedResult`.
Cancel and completion errors are null or exactly eight lowercase hexadecimal
digits; completed bytes is a canonical nonnegative integer.
Natural completion has cancel-requested false and all three cancel fields null;
completion-succeeded is true, its error is null, and byte count equals the full
frame.
Cancellation has cancel-requested true and cancel API exact `CancelIoEx`.
Either cancel-succeeded is true with null error or it is false with exact
`00000490` (`ERROR_NOT_FOUND`) because completion won the race. The retained
event is then waited signaled and `GetOverlappedResult` establishes the final
completion: an effective cancellation has completion-succeeded false and exact
`000003e3`
(`ERROR_OPERATION_ABORTED`). A race-completed branch retains the cancellation-
return fields and obeys only the natural completion-success/error/byte fields.
A cancellation-requested other failure retains the cancellation-return fields,
reaches the same signaled-event wait, and retains completion-succeeded false,
an exact nonzero completion error other than `000003e3` and
`ERROR_IO_INCOMPLETE`, and the exact completed-byte count. A noncancellation
failure has cancel-requested false and all three cancel fields null and obeys
the same other-failure outcome fields. `overlapped_retired` is true only after
that terminal observation;
retirement tick is exactly 16 lowercase hexadecimal digits and precedes event/
OVERLAPPED disposal, pipe disconnect, and server-handle close. A pending,
timed-out, wrong-event, cross-operation, or Boolean-only completion refuses.

`pontius-broker-cancellable-io-v1` has exactly `api`, `bytes_completed`,
`cancel_api`, `cancel_completed`, `completion_code_hex`, `deadline_sha256`,
`event_handle_hex`, `event_signaled`, `flush_thread_binding`,
`flush_thread_binding_sha256`, `flush_thread_terminal`,
`flush_thread_terminal_byte_count`, `flush_thread_terminal_sha256`, `mode`,
`operation`, `operation_nonce`,
`overlapped_operation_nonce`, `reservation_sha256`, `schema`,
`server_handle_identity`, `session_sha256`, `state`, `write_terminal`,
`write_terminal_byte_count`, and `write_terminal_sha256`. Server-handle identity
is the complete `pontius-broker-io-handle-binding-v1`; reservation, session,
and the always-nonnull operation nonce equal that binding. Deadline names the
one active owner timer. Operation is `FRAME_WRITE` or
`FRAME_FLUSH`. A frame write uses API `WriteFile`, mode `OVERLAPPED`, a unique
manual-reset event, a nonnull event handle, the exact operation nonce as the
nonnull retained OVERLAPPED identity, null flush-thread binding object/digest
and null flush terminal object/count/digest. Its complete write-terminal object
reproduces the adjacent positive count and digest and proves natural or
cancelled completion plus OVERLAPPED retirement. Outer event handle/signaled,
cancel API, and completed bytes equal it. `cancel_completed` is true exactly
when a requested `CancelIoEx` return and error have been captured, and is false
otherwise. Outer completion code is `00000000` exactly when terminal completion
succeeds and otherwise equals its nonnull completion error. Completed bytes are the exact complete
framed byte count only on natural or race-completed success. A frame flush uses
API `FlushFileBuffers`, mode
`DEDICATED_BLOCKING_THREAD`, null event and OVERLAPPED fields, the complete
`pontius-broker-flush-thread-binding-v1` object and its canonical digest, and
`CancelSynchronousIo(flush_thread_handle)`; completed bytes and all write-
terminal fields are null. Its
binding repeats the always-nonnull operation nonce. The complete terminal
object reproduces its adjacent positive count and digest, names that binding,
and proves cancellation return/error, flush outcome, signal, join, and handle
close before pipe disconnect. Outer cancel API equals the terminal; outer
`cancel_completed` is true exactly when a requested cancellation return/error
has been captured and is false otherwise. Outer completion code equals the
terminal exit code. State is
`COMPLETED`, `CANCELLED`, or `FAILED`. Completed requires success completion
code, no effective cancellation, and the operation's completion predicate, and
those conditions require state `COMPLETED`. Cancelled write or flush requires
the nested success Boolean false, error and outer completion code exact
`000003e3` (`ERROR_OPERATION_ABORTED`), and those conditions require state
`CANCELLED`. Failed requires the nested success Boolean false and an exact
nonzero error other than `000003e3`, equal to the outer completion code; those
conditions require state `FAILED`. The write mapping uses completion-success/
error; the flush mapping uses flush-success/error and the equal thread exit.
The active or
cleanup deadline, authenticated cancel, channel loss, or result-peer loss
issues cancellation through this object and joins the operation before pipe
disconnect or handle close. No unbounded main-thread write or flush exists.

`pontius-broker-session-reservation-v1` has exactly `askpass_adapter`,
`deadline`, `dispatch_nonce`, `dispatch_sha256`, `limit_row_sha256`, `pipe_name`,
`pipe_nonce`, `pipe_policy`, `repeat_ordinal`, `schema`, `step_ordinal`,
`table_instance_sha256`, and `template_sha256`. `deadline` is the complete
`pontius-owner-wall-deadline-v1` object; its dispatch and limit-row digests equal
the two root fields and the selected launch. The template's deadline policy is
exact `OUTER_DISPATCH_ONLY`. The
trusted broker generates a
fresh `pipe_nonce`, derives the pipe name from the dispatch nonce, step ordinal,
repeat ordinal, and pipe nonce, then calls `CreateNamedPipeW` once with the
complete `pontius-broker-pipe-policy-v1` object. `pipe_policy` contains that
complete object. A preexisting same-name instance, `ERROR_ACCESS_DENIED`, or
any unequal flag, instance count, descriptor, or returned handle is sticky
`BROKER_FAILURE`; the owner builds no Git-child environment and resumes no
process. The listening handle remains held until the reservation has exactly
one terminal result: a session result after a concrete session was completed,
or a pre-session result otherwise. Only after successful pipe creation and
reservation validation may the owner build the Git-child environment. The
handle remains held through terminal completion and is never closed without a
retained terminal result. The reservation contains no
process identity or credential. Its complete bytes remain held through session
completion.
Connect and read are overlapped operations registered with the one active-
deadline timer. They have no independent numeric timeout, never start a new
budget, and never run after the active deadline.
`askpass_adapter` is the complete canonical
`pontius-runtime-capsule-adapter-observation-v1` object measured from the
retained capsule handle before reservation. Final runtime revalidation later
repeats the same object. Its held final path supplies the only `GIT_ASKPASS`
value.

The canonical ASCII pipe name is
`\\.\pipe\LOCAL\PontiusFreeze-v1-<dispatch_nonce>-<step_ordinal>-<repeat_ordinal>-<pipe_nonce>`.
Both ordinals are canonical positive decimal with no leading zero. Both nonce
fields use the closed nonce domain. Any alternate prefix, separator, case,
padding, suffix, or caller-supplied pipe name refuses.

`pontius-broker-session-v1` has exactly `dispatch_nonce`, `one_response`,
`pipe_name`, `pipe_nonce`, `process`, `repeat_ordinal`, `reservation`, `schema`,
`step_ordinal`, `table_instance_sha256`, and `template_sha256`. `reservation`
is the complete canonical `pontius-broker-session-reservation-v1` object.
`one_response` is exact true and means the prospective response limit is one,
not that a response has occurred; the two nonce values are distinct; and the pipe name is the exact
derived local AppContainer pipe. The duplicated routing, ordinal, template, and
table fields equal the reservation exactly. The template plus selected table
bind the role, operation, ordinal, literal URL, repository, public account,
prompt policy, refspecs, audience, and outer-dispatch-only deadline policy. The
embedded reservation carries the complete calibrated owner deadline, launch
digest, and limit-row digest. The root Git process is still
suspended when this document is completed. Its held process binding and exact
environment must reproduce the reservation before resume. Credential bytes
travel only through the exact bounded length-prefixed byte-pipe frame and never
enter any canonical document.

`pontius-named-pipe-client-origin-observation-v1` has exactly `executable`,
`phase`, `pipe_process_id`, `process_id`, `process_wait_result`,
`scheduled_job_membership`, and `win32_error_hex`. Phase is `POST_CONNECT` or
`PREWRITE`. The owner calls `GetNamedPipeClientProcessId` on the exact retained
server handle, never on a name or reopened instance. On a successful PID query
it opens that PID once with exact
`[PROCESS_QUERY_LIMITED_INFORMATION,SYNCHRONIZE]` and noninheritable false,
then derives `process_id` with `GetProcessId`, creation time and executable
identity through that same held process handle, liveness with
`WaitForSingleObject(handle,0)`, and Job membership with `IsProcessInJob`
against the exact session Job. A fully measured observation has positive PIDs,
`process_wait_result=WAIT_TIMEOUT`, boolean Job membership, a complete
executable identity, and null error. A failed pipe-PID query has all measured
fields null and a nonzero eight-lowercase-hex-digit error. A failed process open
has positive pipe PID, all later fields null, and a nonzero error. A handle-PID
mismatch has two positive unequal PIDs, null later fields, and null error.

`pontius-named-pipe-client-origin-v1` has exactly `api`, `observations`,
`open_access`, `open_inheritable`, `pipe_name`, `reservation_sha256`, `schema`,
and `state`. `api` is exact `GET_NAMED_PIPE_CLIENT_PROCESS_ID`; `open_access`
is exact `[PROCESS_QUERY_LIMITED_INFORMATION,SYNCHRONIZE]` and
`open_inheritable` is false. Pipe name and reservation digest equal the exact
session reservation whose retained server instance completed
`ConnectNamedPipe`. State is `BOUND`, `PIPE_PID_QUERY_FAILED`,
`PROCESS_OPEN_FAILED`, `HANDLE_PID_MISMATCH`, or
`PREWRITE_RECHECK_FAILED`. `observations` begins with exactly one
`POST_CONNECT` row. The first four states follow the corresponding complete or
partial measurement above; only `BOUND` may proceed to Job and adapter
admission. When a credential write is about to occur, a second `PREWRITE` row
is mandatory. It repeats the pipe-PID query on the same retained connected
server handle and remeasures PID, liveness, Job membership, and executable
through the same held process handle. A successful pre-write row is byte-for-
byte equal in its measured fields to the post-connect row, has membership true,
and names the exact held adapter identity. Any unequal or failed second row sets
`PREWRITE_RECHECK_FAILED` and receives no response. No PID or handle supplied by
the client, Git, Job enumeration, or session document may substitute.

`pontius-broker-client-attempt-v1` has exactly `client_origin`,
`creation_time_hex`, `executable`, `process_id`, `process_wait_result`,
`scheduled_job_binding`, and `scheduled_job_membership`. This row exists for
every completed connection to the retained server instance, including an
origin-query or process-open failure. When the origin's post-connect row is
fully measured, PID, creation time, executable, wait result, and membership are
nonnull and derived through that same held client-process handle; the first two
PIDs and root process ID are equal. Scheduled Job binding is the complete
binding from the broker session's scheduled Git process, and membership is the
exact live `IsProcessInJob` result for that held Job. The process handle remains
held through any response and pipe close. When origin measurement cannot bind a
process handle, all six root process/Job fields are null and the origin retains
the partial failure. This type records an actual connection attempt and does
not claim admission.
Every bound attempt's `executable` must equal
`broker_session.reservation.askpass_adapter.file_identity` exactly before a
credential response. Same bytes at another path or file identity, a process
outside the bound schedule Job, a substituted connected PID, a dead process,
or any nonadapter image receives no response.
The outbound framed byte pipe carries no client-authored request frame. Route and
operation authority come from the pre-resume reservation, exact pipe handle,
child environment, template, table, and Job equality; they are not inferred
from a client assertion.

`pontius-broker-frame-transfer-v1` has exactly `adapter_creation_time_hex`,
`adapter_exit_code_hex`, `adapter_process_id`, `adapter_process_signaled`,
`disconnect_completed`, `flush_completed`, `flush_io`,
`schema`, `server_handle_closed`, `state`, `write_completed`, and `write_io`. State is
`NOT_STARTED`, `UNCONFIRMED`, `ADAPTER_COMPLETED`, or `ADAPTER_FAILED`.
`server_handle_closed` and `adapter_process_signaled` are true in every terminal
fact, and the exit code is the exact eight-lowercase-hex-digit value measured
from the held connected-adapter process after signal. Adapter PID and creation
time equal the same bound client attempt and are measured from its still-held
handle; a cross-attempt or reopened process handle is invalid. `NOT_STARTED` has false
write and flush, true disconnect and close, and nonzero adapter exit; both I/O
objects are null.
`UNCONFIRMED` has no completed flush, may have begun or completed the frame
write, then disconnects/closes and has nonzero adapter exit. Each begun
operation has its complete cancellable-I/O object; a not-begun operation is
null. It makes no claim
about how many secret bytes the client read. `ADAPTER_COMPLETED` has true write,
flush, disconnect, close, and signal plus exit code `00000000`.
`ADAPTER_FAILED` has the same four completed server actions but a nonzero
adapter exit. Both completed states require complete `write_io` and `flush_io`
objects in `COMPLETED` state. `write_completed` means the complete frame entered the pipe;
`flush_completed` alone proves that the client read every pipe byte. Neither
fact alone proves that the adapter accepted EOF or completed askpass output.
The exact sequence is complete frame write, monitored `FlushFileBuffers`,
`DisconnectNamedPipe`, server-handle close, adapter signal, then exit-code
measurement. A reordered, omitted, early-close, flush-failure, or active-deadline
interruption cannot become `ADAPTER_COMPLETED`.

`pontius-broker-session-result-v1` is completed only after the session is
terminal. Its root has exactly `adapter_attempts`,
`broker_credential_buffer_zeroed`, `broker_session`, `broker_session_sha256`, `closed`,
`controller_cancel_fact`, `controller_channel_loss_fact`, `frame_transfer`, `request_count`,
`response_count`, `schema`, `secret_ingress_result`, `terminal_reason`,
and `wall_trigger_fact`.
`broker_session` is the
complete immutable canonical `pontius-broker-session-v1` pre-resume binding;
`broker_session_sha256` equals its canonical-byte digest. The embedded
session's prospective `one_response=true` remains a cap and is never terminal
evidence. `adapter_attempts` is the complete request-ordered array of
`pontius-broker-client-attempt-v1` objects for completed connections to this
retained server instance; request count equals its length and response count is
the actual credential-response count. A connection remains counted when pipe-
PID query, process open, origin binding, identity, or Job admission fails.
`frame_transfer` is null when no connection completed or when the
`POST_CONNECT` observation fails process binding, scheduled-Job membership, or
exact adapter-image admission. Otherwise it is the complete
`pontius-broker-frame-transfer-v1` for the sole admitted connected adapter,
whose PID and creation time equal the same attempt. Every admitted post-connect
attempt has one, including a later `PREWRITE_RECHECK_FAILED` attempt, whose
transfer remains `NOT_STARTED`. The broker never waits for, terminates, or
fabricates exit evidence for an unbound, nonmember, or wrong-image client.
Terminal reason is exactly `REDEEMED_ONCE`,
`UNREDEEMED`, `ADAPTER_IDENTITY_REFUSED`, `JOB_IDENTITY_REFUSED`,
`WALL_EXPIRED`, `CANCELLED`, `CHANNEL_LOST`, or `BROKER_FAILURE`. No credential
byte or credential-derived
digest enters the document.
`wall_trigger_fact` is the complete `pontius-wall-trigger-fact-v1` object
exactly for `WALL_EXPIRED` and null otherwise. Its deadline equals the embedded
reservation byte-for-byte. A broker-local timeout, refreshed child budget, or
wall classification without the outer fact is invalid.
`controller_cancel_fact` is the complete authenticated fact exactly for
`CANCELLED` and null otherwise. `secret_ingress_result` is one complete
`pontius-secret-ingress-result-v1` for this reservation and controller session.
Its request, grant, coordinate, dispatch, and zeroization facts equal the outer
message transcripts and this broker session.
`controller_channel_loss_fact` is the complete channel-loss fact exactly for
`CHANNEL_LOST` and null otherwise. It equals every outer carrier and is
mutually exclusive with the cancel fact.

Every complete result has `closed=true`, request count equal to the attempts
array length, request count in `0..1`, response count in `0..1`, and response
count no greater than request count. Its terminal truth table is exact:

| Terminal reason | Requests | Responses | Required attempt predicate |
| --- | ---: | ---: | --- |
| `REDEEMED_ONCE` | 1 | 1 | bound exact adapter; successful completed transfer |
| `UNREDEEMED` | 0 | 0 | no connection completed |
| `JOB_IDENTITY_REFUSED` | 1 | 0 | origin `BOUND`; scheduled-Job membership false; transfer null |
| `ADAPTER_IDENTITY_REFUSED` | 1 | 0 | member; wrong executable; transfer null |
| `WALL_EXPIRED` | 0 or 1 | 0 | transfer null or not `ADAPTER_COMPLETED`; exact outer wall fact |
| `CANCELLED` | 0 or 1 | 0 | incomplete transfer; exact controller cancellation |
| `CHANNEL_LOST` | 0 or 1 | 0 | incomplete transfer; exact channel-loss fact |
| `BROKER_FAILURE` | 0 or 1 | 0 | incomplete transfer; measured failure-point counts |

The redeemed predicate additionally requires origin `BOUND`, exact scheduled-
Job membership and adapter identity, a successful immediate `PREWRITE` recheck,
transfer `ADAPTER_COMPLETED`, and intact session binding. Every shorthand
`incomplete transfer` means null or not `ADAPTER_COMPLETED`.

Response count one is valid if and only if terminal reason is `REDEEMED_ONCE`
and transfer state is `ADAPTER_COMPLETED`. Completed `WriteFile` or flush alone,
and a full frame read followed by adapter failure, never count as redemption.
`REDEEMED_ONCE` additionally requires ingress `GRANT_ACCEPTED`.
`UNREDEEMED` and both identity-refused reasons require `NOT_REQUESTED`.
A wall, cancellation, channel loss, or broker failure after a request retains
the exact ingress state and every consumed request/grant wrapper; when no
request was emitted it uses `NOT_REQUESTED`. `CANCELLED` always carries the
same controller cancel fact, whether ingress was `CANCELLED` or not requested.
Membership is checked before executable identity, so the first failing
predicate selects the reason. An origin state other than `BOUND` selects
`BROKER_FAILURE`, never a Job or adapter refusal. A response requires exactly
two origin observations and a successful immediate pre-write recheck. A wrong
pipe name, nonce, or ordinal never reaches
this retained server handle and therefore cannot become a broker-client attempt;
the one-instance pipe is closed after its sole response. An operation, table,
template, environment, or route mismatch is sticky `BROKER_FAILURE` before
resume and receives no credential response.
Every result except a broker-zeroization-failure `BROKER_FAILURE` has
`broker_credential_buffer_zeroed=true`; only that one broker-failure subtype may set it
false. `REDEEMED_ONCE` is the only success-capable reason and requires exact
true for both booleans. Every other combination is invalid rather than merely
negative evidence. A missing result is failure, never an implicit clean
lifecycle.

`pontius-broker-presession-result-v1` is completed when a successful
reservation becomes terminal before `pontius-broker-session-v1` can be
completed. Its root has exactly `broker_credential_buffer_zeroed`, `closed`,
`controller_cancel_fact`, `controller_channel_loss_fact`, `reservation`,
`reservation_sha256`, `schema`,
`secret_ingress_result`, `stage`, `terminal_reason`,
`wall_trigger_fact`, and `win32_error_hex`. `reservation` is the complete immutable
`pontius-broker-session-reservation-v1` object and `reservation_sha256` equals
its canonical-byte digest. It has no process, Job, adapter-attempt,
request-count, response-count, or credential field and makes no claim that a
client connected. `closed` is exact true. `terminal_reason` is exactly
`PROCESS_CREATE_FAILED`, `JOB_ASSIGNMENT_FAILED`,
`PRE_RESUME_VALIDATION_FAILED`, `WALL_EXPIRED`, `CANCELLED`, `CHANNEL_LOST`, or
`BROKER_FAILURE`. `stage` is the exact last reached boundary:
`BEFORE_PROCESS_CREATE`, `PROCESS_CREATE`, `JOB_ASSIGNMENT`, or
`PRE_RESUME_VALIDATION`. `PROCESS_CREATE_FAILED` requires stage
`PROCESS_CREATE` and nonzero eight-lowercase-hex-digit `win32_error_hex`;
`JOB_ASSIGNMENT_FAILED` requires stage `JOB_ASSIGNMENT` and the same nonzero
error form; `PRE_RESUME_VALIDATION_FAILED` requires stage
`PRE_RESUME_VALIDATION` and null error. For `WALL_EXPIRED`, `CANCELLED`, `CHANNEL_LOST`, or
`BROKER_FAILURE`, stage records the boundary actually reached; the Win32 error
is nonzero only when that terminal broker failure came directly from a Win32
API failure and otherwise null. `wall_trigger_fact` is the complete
`pontius-wall-trigger-fact-v1` object exactly for `WALL_EXPIRED` and null
otherwise; its deadline equals the embedded reservation byte-for-byte.
`controller_cancel_fact` is the complete authenticated fact exactly for
`CANCELLED` and null otherwise. `secret_ingress_result` is the canonical
`NOT_REQUESTED` object because no secret request may precede a complete broker
session.
`controller_channel_loss_fact` is complete exactly for `CHANNEL_LOST` and null
otherwise. It agrees with every outer carrier and is mutually exclusive with
the cancel fact.
`broker_credential_buffer_zeroed` is true for every reason except the exact
zeroization-failure subtype of `BROKER_FAILURE`, which alone may set it false.
The owner closes the retained listening handle and zeroes every broker-owned credential buffer
before completing this result. A missing result, an unclosed listener, or an
unaccounted buffer is failure and cannot support a semantic envelope.

`pontius-broker-reservation-terminal-v1` is the tagged-union row with exactly
`kind`, `presession_result`, `result_sha256`, and `session_result`. `kind` is
`SESSION_RESULT` or `PRESESSION_RESULT`. For `SESSION_RESULT`,
`session_result` is one complete `pontius-broker-session-result-v1` object,
`presession_result` is null, and `result_sha256` equals the session result's
canonical-byte digest. For `PRESESSION_RESULT`, `presession_result` is one
complete `pontius-broker-presession-result-v1` object, `session_result` is null,
and `result_sha256` equals the pre-session result's canonical-byte digest.
Exactly one branch is nonnull. The row's reservation is the session result's
embedded `broker_session.reservation` or the pre-session result's embedded
`reservation`, respectively.

`pontius-broker-session-result-set-v1` has exactly `dispatch_sha256`, `results`,
and `schema`. `results` contains complete
`pontius-broker-reservation-terminal-v1` rows sorted by their embedded
reservation's `(step_ordinal, repeat_ordinal)` and contains exactly one row for
every successful reservation created under that dispatch. No two rows name the
same coordinate or reservation digest. The empty set is canonical exactly when
no reservation was created. A session-result row's expanded network row has
session digest and terminal-result digest equal respectively to the result's
embedded-session digest and `result_sha256`. A pre-session result is instead
named by the aborted schedule completion's `terminal_broker_result_sha256` and
has no expanded-row session digest. Every successful reservation appears in
exactly one branch; every result branch names one such reservation.

### 3.3 Operation precondition

`pontius-operation-precondition-v1` binds the complete eligibility equation for
one mutation dispatch. Its root has exactly `eligible`, `items`, `operation`,
`role`, `round`, `schedule_variant`, `schema`, and `task`. `eligible` is exact
`true`. `schedule_variant` is derived from the item state and names one allowed
mutation variant in the role operation set. A predicate item has exactly
`byte_count`, `kind`, `name`, `schema`, and `sha256`; `kind` is `INPUT` or
`OBSERVATION`. `name` and `schema` equal the closed entry below. Byte count and
digest reproduce the held complete canonical bytes plus LF. Items occur in
this operation-specific order:

- `FREEZE_PAIR`: `CANDIDATE_CHANGE:pontius-candidate-change-spec-v1`, then
  `OBSERVATION_SET:pontius-operation-observation-set-v1`.
- `ADOPT_PAIR`: `ADOPTION_RECEIPT:pontius-adoption-receipt-v1`,
  `OBJECT_INVENTORY:pontius-git-object-inventory-v1`, then
  `OBSERVATION_SET:pontius-operation-observation-set-v1`.
- `BUILD_REVIEW_OUTPUT`: `REPORT:artifact_identity`, `LEDGER:artifact_identity`,
  `RECEIPT:selector-selected review-receipt schema`, then
  `OBSERVATION_SET:pontius-operation-observation-set-v1`.
- `FETCH_MAIN_INPUTS`: `MAIN_INPUT_SPEC:pontius-main-input-fetch-spec-v1`, then
  `OBSERVATION_SET:pontius-operation-observation-set-v1`.
- `BUILD_MAIN_OVERLAY`: `FETCH_RECEIPT:pontius-main-input-fetch-receipt-v1`,
  `OBJECT_INVENTORY:pontius-git-object-inventory-v1`,
  `OVERLAY:pontius-main-overlay-spec-v1`, then
  `OBSERVATION_SET:pontius-operation-observation-set-v1`.
- `PUBLISH_PAIR`: `OBSERVATION_SET:pontius-operation-observation-set-v1`.
- `FETCH_FOR_ADOPTION`:
  `OBSERVATION_SET:pontius-operation-observation-set-v1`.
- `PUBLISH_REVIEW_OUTPUT`:
  `BUILD_AUTHORIZATION:pontius-transition-authorization-v1`,
  `OBJECT_BUILD_RECEIPT:pontius-object-build-receipt-v1`, then
  `OBSERVATION_SET:pontius-operation-observation-set-v1`.
- `INTEGRATE_PACKET`:
  `PROPOSED_PHASE_INPUT:pontius-phase-evidence-input-bundle-v1`, then
  `OBSERVATION_SET:pontius-operation-observation-set-v1`.
- `FINALIZE_REVIEWS`:
  `PROPOSED_PHASE_INPUT:pontius-phase-evidence-input-bundle-v1`, then
  `OBSERVATION_SET:pontius-operation-observation-set-v1`.
- `PUBLISH_DISPOSITION`:
  `DISPOSITION_INTENT:pontius-disposition-intent-v1`,
  `PROPOSED_PHASE_INPUT:pontius-phase-evidence-input-bundle-v1`, then
  `OBSERVATION_SET:pontius-operation-observation-set-v1`.

Every item is a canonical document defined by this appendix or a complete
artifact identity named by the authorization. The exact state predicates in
the operation sections decide eligibility; a caller cannot set `eligible=true`
for a noneligible tuple. The owner reparses every item and recomputes this
document before accepting its digest.

The mutation-needed eligibility predicates are exact:

| Operation | Eligible aggregate predicate |
| --- | --- |
| `FREEZE_PAIR` | fresh expected-OID tuple at `LOCAL_ABSENT` |
| `ADOPT_PAIR` | exact receipt and inventory; tuple `LOCAL_ABSENT` |
| `BUILD_REVIEW_OUTPUT` | objects absent or buildable |
| `FETCH_MAIN_INPUTS` | exact main and permanent observations; exact scratch inventory |
| `BUILD_MAIN_OVERLAY` | exact fetch receipt/inventory; objects absent or buildable |
| `PUBLISH_PAIR` | tuple `LOCAL_EXACT`; pair `PAIR_ABSENT` |
| `FETCH_FOR_ADOPTION` | pair `PAIR_EXACT` |
| `PUBLISH_REVIEW_OUTPUT` | exact build receipt; slot `ABSENT` |
| `INTEGRATE_PACKET` | attempt absent/exact plus clean exact predecessor |
| `FINALIZE_REVIEWS` | outputs ready plus clean exact predecessor |
| `PUBLISH_DISPOSITION` | exact disposition plus clean exact predecessor |

An exact terminal state is never mutation-eligible. An `OBSERVATION_ONLY`
launch closes it through the terminal-result fields in section 14. For
`INTEGRATE_PACKET`, `ATTEMPT_ABSENT` plus
`PREDECESSOR_EXACT/INTACT` selects `CREATE_ATTEMPT_AND_PUSH`;
`ATTEMPT_EXACT` plus that same main pair selects `PUSH_EXISTING_ATTEMPT`.
Finalization and disposition select `PUSH_MAIN` only for
`PREDECESSOR_EXACT/INTACT`. Exact local tuples, exact built objects, exact
remote outputs, and allowed result-lineage pairs close through observation and
start no mutation schedule. Conflict, task-unknown, unrelated, and lineage-
unknown states are neither terminal success nor mutation-eligible.

`pontius-builder-precondition-v1` remains the upstream all-absent gate for
issuing a new `FREEZE_PAIR` authorization. It is not the mutation precondition.
After authorization exists, the observation-only dispatch derives the complete
expected-OID tuple; only that fresh `LOCAL_ABSENT` observation can enter the
mutation precondition. A fresh `LOCAL_EXACT` tuple closes terminally.

For a clean predecessor, the main-observation row at the exact predecessor must
derive the operation's `phase_before` from complete prior phase evidence. Before
push, the proposed raw result, intent/finalizer authorization, overlay, and
proposed phase-evidence input bundle must derive the exact transition kind and
`phase_after`. Packet integration requires `NO_TASK` to `PACKET_INTEGRATED`;
finalization requires `PACKET_INTEGRATED` to `REVIEWS_FINALIZED`; disposition
requires `REVIEWS_FINALIZED` to `DISPOSITION_PUBLISHED`. A wrong, skipped,
missing, or unreadable phase is never eligible for mutation.

`pontius-operation-input-projection-v1` is the complete pre-authorization input
population for one transition. Its root has exactly `inputs`, `operation`,
`role`, `round`, `schema`, and `task`. An input row has exactly `byte_count`,
`delivery`, `input_id`, `schema`, `sha256`, and `source`. `delivery` is
`OWNER_ONLY` or `PLANNER`. Rows sort by `input_id`, which is
a frozen ASCII identifier unique within the operation. Byte count, schema, and
digest describe the exact input content bytes, content schema, and content
SHA-256; they do not hash the containing row. Only `PLANNER` row content is delivered to
the planner.

`source` is one exact tagged variant. `HELD_FILE_INPUT` has exactly
`byte_count`, `file_identity`, `kind`, and `sha256`. `GIT_BLOB_INPUT` has
exactly `blob_oid`, `byte_count`, `commit_oid`, `kind`, `mode`, `path`,
`repository_projection_sha256`, and `sha256`. `INLINE_CANONICAL_INPUT` has
exactly `content`, `kind`, and `schema`; re-encoding its complete content plus
LF reproduces the row's content identity. Every held file is opened and identity-bound before
launch; every Git blob is raw-read from the exact held repository projection
and recomputed. No working-directory discovery is valid.

The row population is exactly every file-backed, Git-backed, or inline
canonical input available before authorization issuance and named by the
operation contract, including candidate changes, cold/build specifications,
report and ledger bytes, and upstream receipts, inventories, or overlays. The
authorization schema fixes each `input_id` and source relation; every
authorization digest that denotes delivered bytes has exactly one equal row,
and no extra row is allowed. A live selector or owner-request capability must
equal the current authorization and held role table. A parsed historical
evidence coordinate instead validates only under the complete upstream plan,
authority, and publication object that governs its tagged evidence schema.
Historical endpoint, repository, and ref literals are inert: they cannot fill,
compare equal by implication to, or select a current request, route, or table
slot. This remains true when historical and current coordinates deliberately
differ. Result-dependent phase evidence and mutable observations
for the current proposed transition are forbidden. The immutable historical
`pontius-phase-evidence-input-set-v1` at the expected predecessor is
allowed exactly where the closed operation table requires it; it contains input
bundles, never observer-derived phase-evidence objects. The projection contains
no authorization or dispatch digest and is therefore upstream of both.

The authority-input ID populations are exact. Every fixed row below has
delivery `PLANNER` except the explicitly owner-only
`PACKET_STATIC_SOURCE_MAP`; the complete route selector is a separate owner-
only launch-dispatch field and never an input row. The populations are:

```text
FREEZE_PAIR:
  CANDIDATE_AUTHOR_SET, CANDIDATE_CHANGE_SPEC, CANDIDATE_MANIFEST,
  COLD_INPUT_SPEC, PACKET_BUILD_SPEC, PACKET_SOURCE_MANIFEST,
  PACKET_STATIC_SOURCE_MAP,
  ROUND_REVIEW_AUTHOR_SET, UTILITY_AUTHOR_SET, UTILITY_REVIEW_AUTHORITY,
  then CANDIDATE_FILE/<candidate-change path> in path order
ADOPT_PAIR:
  ADOPTION_RECEIPT, BUILDER_INTENT, OBJECT_INVENTORY
BUILD_REVIEW_OUTPUT:
  CANDIDATE_AUTHOR_SET, COMMIT_INPUT, LEDGER_LINE, OUTPUT_MANIFEST, RECEIPT,
  REPORT, ROUND_REVIEW_AUTHOR_SET, UTILITY_AUTHOR_SET
FETCH_MAIN_INPUTS:
  MAIN_INPUT_SPEC
BUILD_MAIN_OVERLAY:
  COMMIT_INPUT, MAIN_INPUT_FETCH_RECEIPT, OBJECT_INVENTORY, OVERLAY_SPEC,
  then OVERLAY_SOURCE/<destination path> for every CONTROLLER_BLOB row
PUBLISH_PAIR:
  BUILDER_INTENT
FETCH_FOR_ADOPTION:
  <empty>
PUBLISH_REVIEW_OUTPUT:
  BUILD_AUTHORIZATION, CANDIDATE_AUTHOR_SET, OBJECT_BUILD_RECEIPT,
  REVIEW_OUTPUT_MANIFEST, ROUND_REVIEW_AUTHOR_SET, UTILITY_AUTHOR_SET
INTEGRATE_PACKET:
  BUILD_AUTHORIZATION, INTEGRATION_COMMIT_INPUT, INTEGRATION_INTENT,
  MAIN_OVERLAY_SPEC, OBJECT_BUILD_RECEIPT, PHASE_EVIDENCE_INPUT_SET,
  PROTECTED_TASK_SPEC
FINALIZE_REVIEWS:
  BUILD_AUTHORIZATION, CANDIDATE_AUTHOR_SET, FINALIZER_COMMIT_INPUT,
  MAIN_OVERLAY_SPEC, OBJECT_BUILD_RECEIPT, PHASE_EVIDENCE_INPUT_SET,
  PROTECTED_TASK_SPEC, ROUND_REVIEW_AUTHOR_SET, UTILITY_AUTHOR_SET,
  REVIEW_01_LEDGER_LINE, REVIEW_01_MANIFEST, REVIEW_01_RECEIPT, REVIEW_01_REPORT,
  REVIEW_02_LEDGER_LINE, REVIEW_02_MANIFEST, REVIEW_02_RECEIPT, REVIEW_02_REPORT
PUBLISH_DISPOSITION:
  BUILD_AUTHORIZATION, DISPOSITION_COMMIT_INPUT, DISPOSITION_INTENT,
  MAIN_OVERLAY_SPEC, OBJECT_BUILD_RECEIPT, PHASE_EVIDENCE_INPUT_SET,
  PROTECTED_TASK_SPEC
```

Each `REVIEW_<NN>_<KIND>` row equals that ordinal's exact finalized slot
artifact of the named kind. No bare or duplicate `LEDGER_LINE`, `MANIFEST`,
`RECEIPT`, or `REPORT` input ID exists for `FINALIZE_REVIEWS`.

Every fixed ID equals its same-named authorization digest or artifact identity.
Every input ID present in the operation row's route-input contract parses under
its selector-selected schema. This includes `BUILDER_INTENT`, `RECEIPT`,
`CANDIDATE_AUTHOR_SET`, and `ROUND_REVIEW_AUTHOR_SET` where listed. A rehearsal
builder-intent fixture, bootstrap review receipt, or rehearsal author-set branch
remains inert data; its embedded historical
coordinates cannot populate a live route, table, endpoint, ref, repository, or
credential request. Every fixed ID absent from that contract retains one schema.
`CANDIDATE_FILE/<path>` rows equal the candidate-change row's path, byte count,
SHA-256, mode, and result blob OID. Canonical JSON inputs may use any source
variant but must parse under the exact schema named by their authorization
field. Report, ledger, manifest, receipt, and candidate-file bytes use only a
held-file or Git-blob source unless their governing schema explicitly defines
canonical JSON content. No other ID, source form, ordering, or inferred digest
is valid.

`PACKET_STATIC_SOURCE_MAP` has delivery `OWNER_ONLY` and parses as
`pontius-packet-static-source-map-v1`. Its root has exactly `rows` and `schema`.
Rows sort by `destination_path` and have exactly `artifact`,
`destination_path`, and `source`. `artifact` equals the matching packet-build
`STATIC_BLOB` source. `source` is one exact tagged variant: `OPERATION_INPUT`
has exactly `input_id`, `input_row_sha256`, and `kind`; `ROUTE_SELECTOR` has
exactly `kind` and `route_selector_sha256`; `HELD_FILE` or `GIT_BLOB` has
exactly `input_source` and `kind`, where `input_source` is the corresponding
operation-input source variant. The route-selector variant is valid only for
the complete normal raw-route-preregistration artifact.

There is exactly one map row for every `STATIC_BLOB` packet row and none for a
derived renderer. An operation-input source is referenced at most once unless
two packet destinations intentionally have one equal artifact identity. Every
source-manifest member, map row, packet-build row, object-plan member, and
stored blob agrees on byte count, SHA-256, mode, and blob OID. Thus the owner
has one total source route for every static artifact without sending the map,
route selector, sealed identity, or owner-only bytes to the planner.

`UTILITY_AUTHOR_SET` is the complete
`pontius-utility-author-set-v1` object. For a normal selector its byte count and
SHA-256 equal the freeze authorization, cold-input spec, all four role source
projections, packet artifact, and accepted utility authority. For a rehearsal
selector they equal its embedded utility-author fields, all four reviewed source
projections, and both bootstrap-review receipts; an accepted utility authority,
normal freeze authorization, cold input, and raw-v5 packet are absent.

On a normal selector, `CANDIDATE_AUTHOR_SET` and `ROUND_REVIEW_AUTHOR_SET` are
the complete canonical objects above. Their counts and SHA-256 values equal the
cold-input spec, preregistration, packet artifacts, and applicable review or
finalizer authority. On a rehearsal review-output operation, both IDs instead
carry the same complete `pontius-utility-author-set-v1` selected by their route-
input contracts. That set's authors include every implementation author and
implementer, and the bootstrap receipt's reviewer is absent from the set. The
three author input IDs carry byte-identical set objects whose count and digest
equal the selector and bootstrap receipt fields;
no later selector, authorization, result, or accepted-utility identity occurs in
the set. The selected branch is revalidated before a reviewer-output object is
built or published; a digest-only author union is insufficient.

An `OVERLAY_SOURCE/<destination path>` row exists exactly once for every
`CONTROLLER_BLOB` overlay row and for no other row. Its bytes, byte count, and
SHA-256 equal that overlay row's artifact identity, and the suffix equals the
destination path exactly. Its source is held-file or inline canonical input;
the owner holds it before authorization and the builder rehashes it before
writing the blob. A Git-derived overlay row receives no controller-source row.

For the three main-publishing operations, `PROTECTED_TASK_SPEC` equals the
complete document named by `protected_task_spec_sha256`.
`PHASE_EVIDENCE_INPUT_SET` equals the complete historical set defined in
section 9.3. The commit-input and overlay rows equal the corresponding digests
inside the accepted integration intent, finalizer authorization, or disposition
intent. Every nested digest must also equal the build authorization and object
receipt; a bare nested digest without its complete input row refuses.

`pontius-launch-input-projection-v1` is downstream of authorization and
upstream of one launch dispatch. Its root has exactly
`authority_input_projection`, `inputs`, `operation`, `role`, `round`, `schema`,
and `task`. `authority_input_projection` is the complete canonical object above.
`inputs` uses the same row schema and contains every authority-input row
byte-for-byte plus these reserved inline canonical rows in ASCII-ID order:

- `AUTHORIZATION`, always, containing the complete accepted transition or
  finalizer authorization;
- `OPERATION_PRECONDITION`, exactly for `MUTATION_ATTEMPT`, containing the
  complete canonical mutation precondition; and
- `PROPOSED_PHASE_EVIDENCE_INPUT_BUNDLE`, exactly for `INTEGRATE_PACKET`,
  `FINALIZE_REVIEWS`, and `PUBLISH_DISPOSITION`, containing the complete bundle
  for that operation's proposed result edge.

Every inherited authority-input row retains its frozen `delivery`. Every
reserved row is `OWNER_ONLY`. The inherited and reserved populations are
disjoint and their union is the complete launch-input population. The owner
parses, binds, and revalidates owner-only rows but never frames or streams their
bytes to Python.

Reserved IDs cannot occur in the authority-input population. The launch
projection's authorization and precondition bytes reproduce the dispatch
digests exactly. The proposed bundle follows section 9.3's transition-kind map,
is assembled after authorization and the raw result preimage exist, and makes no
claim that the result is reachable from main. For a mutation launch it equals
the `PROPOSED_PHASE_INPUT` precondition item. A later reconciliation that
observes the result derives phase evidence from this same bundle; the derived
evidence is terminal output and never enters the prelaunch projection. The
launch projection contains no dispatch digest and creates no identity cycle.

`pontius-operation-input-read-result-v1` has exactly `byte_count`, `input_id`,
`input_projection_sha256`, `schema`, `sha256`, and `source_sha256`. It accompanies
the output data-stream descriptor for the next `PLANNER` projection row and
reproduces that selected row's `input_id` plus content and source identities;
the complete wrapped row retains its separate `input_row_sha256`. The planner
cannot select or skip an input ID.

## 4. Transition authorization and one-use launch dispatch

### 4.1 Transition authorization

`pontius-transition-authorization-v1` is stable, content-addressed authority
for one exact idempotent state transition. Its root has exactly:

| Key | Type |
| --- | --- |
| `execution_projection_byte_count` | `positive_count` |
| `execution_projection_sha256` | `sha256` |
| `input_projection_byte_count` | `positive_count` |
| `input_projection_sha256` | `sha256` |
| `operation` | an operation allowed for `role` |
| `payload` | the closed payload selected below |
| `plan_sha256` | `sha256` |
| `rehearsal_case_id` | frozen case ID or `null` |
| `rehearsal_step_ordinal` | `positive_count` or `null` |
| `rehearsal_task_binding_id` | `task_binding_id` or `null` |
| `role` | `execution_role` |
| `role_projection_byte_count` | `positive_count` |
| `role_projection_sha256` | `sha256` |
| `role_table_instance_byte_count` | `positive_count` |
| `role_table_instance_sha256` | `sha256` |
| `route_selector` | `route_selector_identity` |
| `round` | `round` |
| `schema` | exact schema literal |
| `schemas_sha256` | `sha256` |
| `source_projection_set_byte_count` | `positive_count` |
| `source_projection_set_sha256` | `sha256` |
| `task` | `task` |

Payload key sets are exact. Keys below are listed in ASCII order.
Both execution-projection fields equal the complete runtime-projection bytes
named by the selected role-source projection. Both role-table fields equal one
complete table-instance document selected by that runtime projection. The
launch dispatch repeats all four fields exactly.
Both input-projection fields equal the complete canonical operation-input
projection above. The authorization issuer holds and validates every source;
the launch dispatch repeats both fields exactly and the runtime evidence embeds
the complete projection.
The payload's `repository_projection_sha256` equals the owner-only complete
object carried by the later launch dispatch. The authorization and every
planner-visible projection contain no repository path, handle identity, or
complete repository object.
Both source-projection-set fields equal the complete canonical
`pontius-source-projection-set-v1` document containing the runtime-owner and all
three execution-role projections. The selected `role_projection_sha256` is the
matching member of that set. The owner validates every set-member identity
against the selected route's authority chain, but opens, holds, and revalidates
complete bytes only for `runtime-owner` and the selected execution role before
it starts a child. Sibling projection bytes, paths, tables, archives, and
handles are forbidden from the live launch. For a normal selector, the set byte
count and digest equal the accepted utility authority and integrated packet.
For a rehearsal selector, they equal the complete set embedded in that selector
and its adopted implementation candidate, rule-6 packet, reviews, campaign,
derived-input contracts, fixture set, adoption-chain set, and fault-harness
projection;
an accepted utility authority and raw-v5 integrated packet are explicitly
absent. A caller-supplied replacement set refuses.

`route_selector` names exactly `pontius-round-preregistration-v1` for a later
raw-object-v5 launch or `pontius-utility-rehearsal-selector-v1` for the bundle's
preacceptance HTTPS campaign. It is owner-only and never an authority-input
row. The complete selector is carried by the launch dispatch and revalidated
before an observation, repository open, credential reservation, or process
creation. Cross-kind table, endpoint, source-projection, or operation use
refuses. For a normal selector all three rehearsal fields are null and task and
round equal the preregistration. For a rehearsal selector all three are nonnull,
select one exact campaign case, step, and task binding, and that binding's task
and round equal this authorization. The selected step's role, operation,
dispatch mode, and schedule variant equal this authorization and its launch
dispatch. One campaign coordinate cannot authorize another step or task.

The selector/table matrix is closed. A normal selector uses the exact
`PRODUCTION_HANDOFF` endpoint, an `OFFLINE` builder table, and `PRODUCTION`
publisher or integrator tables. A rehearsal selector uses exact
`HTTPS_REHEARSAL`, an `OFFLINE` builder table, and `REHEARSAL` publisher or
integrator tables. Every other selector, endpoint, role, or instance-kind
cross-product refuses before repository open, credential reservation, or
process creation.

`FREEZE_PAIR` has:

```text
base_oid
candidate_change_spec_sha256
candidate_commit_metadata
candidate_manifest_sha256
cold_input_spec_sha256
packet_commit_metadata
packet_build_spec_sha256
packet_source_manifest_sha256
repository_projection_sha256
utility_author_set_byte_count
utility_author_set_sha256
utility_review_authority_sha256
```

`ADOPT_PAIR` has:

```text
adoption_chain_row_sha256
adoption_receipt_sha256
builder_intent_blob_oid
builder_intent_sha256
expected_candidate_oid
expected_packet_oid
object_inventory_sha256
repository_projection_sha256
```

`BUILD_REVIEW_OUTPUT` has:

```text
commit_input_sha256
commit_metadata
expected_output_commit_oid
expected_output_tree_oid
integrated_packet_oid
ledger_line_sha256
output_manifest_sha256
receipt_sha256
report_sha256
repository_projection_sha256
reviewer_ordinal
```

`BUILD_MAIN_OVERLAY` has:

```text
commit_input_sha256
commit_metadata
expected_commit_oid
expected_tree_oid
main_input_fetch_receipt_sha256
main_predecessor_oid
object_inventory_sha256
overlay_kind
overlay_spec_sha256
repository_projection_sha256
```

`FETCH_MAIN_INPUTS` has:

```text
endpoint_id
input_kind
main_input_spec_sha256
repository_projection_sha256
```

`PUBLISH_PAIR` has:

```text
builder_intent_blob_oid
builder_intent_sha256
endpoint_id
repository_projection_sha256
```

`FETCH_FOR_ADOPTION` has:

```text
adoption_chain_row_sha256
endpoint_id
expected_candidate_oid
expected_packet_oid
repository_projection_sha256
```

`PUBLISH_REVIEW_OUTPUT` has:

```text
build_authorization_sha256
endpoint_id
integrated_packet_oid
object_build_receipt_sha256
review_output_commit_oid
review_output_manifest_sha256
reviewer_ordinal
repository_projection_sha256
```

`INTEGRATE_PACKET` has:

```text
build_authorization_sha256
commit_metadata
endpoint_id
integration_intent_sha256
object_build_receipt_sha256
repository_projection_sha256
```

`PUBLISH_DISPOSITION` has:

```text
build_authorization_sha256
commit_metadata
disposition_intent_sha256
endpoint_id
object_build_receipt_sha256
repository_projection_sha256
```

A `commit_metadata` object has exactly `author` and `committer`, each an actor
object from section 5. Every metadata value equals the corresponding raw commit
input and any repeated intent or overlay value. `overlay_kind` is
`PACKET_INTEGRATION`, `REVIEW_FINALIZER`, or `DISPOSITION`.
`reviewer_ordinal` has type `ordinal`. Every key ending
`_sha256` has type `sha256`; every key ending `_oid` has type `oid`;
`endpoint_id` has type `endpoint_id`; `utility_author_set_byte_count` is a
`positive_count`. `adoption_chain_row_sha256` is `sha256` or `null`; it is null
exactly on a normal route and nonnull exactly on a rehearsal `FETCH_FOR_ADOPTION`
or `ADOPT_PAIR` route. No other payload key is nullable.

No transition-authorization payload contains an observation, operation
precondition, launch dispatch, or terminal-result digest. An observation-only
dispatch can therefore bind the already complete transition authorization.
Only the later mutation dispatch binds fresh canonical observations through
`operation_precondition_sha256`.

Every operation that opens an authority repository binds its
`repository_projection_sha256` in this authorization. Where a build
authorization or receipt is also bound, all three values are equal. A later
observation or precondition may prove freshness but can never select a
repository. All repeated repository-projection digests in observations,
receipts, and downstream authorizations equal that authoritative value.

For a rehearsal `FETCH_FOR_ADOPTION` or `ADOPT_PAIR`, the nonnull adoption-chain
row digest names exactly one row in the held selector's complete chain set. The
fetch authorization's case, task binding, expected candidate, and expected
packet equal that row. The later adopter's case, task binding, step, builder-
intent fixture input, receipt, candidate, and packet equal the same row. Normal
routes have no chain row; their existing preregistration, packet, intent, and
receipt equations remain authoritative. A cross-row or caller-supplied digest
refuses.

`FREEZE_PAIR` output commit inputs, trees, OIDs, inventory, builder intent, and
expected tuple targets are deterministic equations over its bound inputs and
external authorization digest. Their deliberate absence from the authorization
prevents a content cycle; it does not permit the worker to choose them.

For `PUBLISH_REVIEW_OUTPUT`, `build_authorization_sha256` names the exact
`BUILD_REVIEW_OUTPUT` authorization and `object_build_receipt_sha256` names its
validated receipt. Both repeat `integrated_packet_oid`, the output OID, manifest
digest, reviewer, round, and task exactly. The publisher independently parses
the output commit and requires that integrated packet as its sole parent before
an absent output ref is eligible.

`FINALIZE_REVIEWS` uses the more specific finalizer authorization in section
13 and is forbidden in this generic envelope.

The transition authorization has no nonce, attempt ordinal, expiry, path, or
clock. Its external complete-byte SHA-256 is the authorization identifier. A
retry may reuse it only after fresh state observation proves the same exact
predecessor and expected result relation.

### 4.2 One-use launch dispatch

`pontius-launch-dispatch-v1` authorizes one role-process creation and its exact
bounded child schedule, not one durable transition. Its root has exactly:

| Key | Type |
| --- | --- |
| `attempt_ordinal` | `positive_count` |
| `authorization_byte_count` | `positive_count` |
| `authorization_sha256` | `sha256` |
| `cleanup_reserve_ms` | `positive_count` |
| `cpu_time_ms` | `positive_count` |
| `dispatch_mode` | `MUTATION_ATTEMPT` or `OBSERVATION_ONLY` |
| `dispatch_nonce` | `nonce` |
| `execution_projection_byte_count` | `positive_count` |
| `execution_projection_sha256` | `sha256` |
| `fault_reservation` | complete rehearsal-fault-reservation object or `null` |
| `fault_reservation_byte_count` | `positive_count` or `null` |
| `fault_reservation_sha256` | `sha256` or `null` |
| `input_projection_byte_count` | `positive_count` |
| `input_projection_sha256` | `sha256` |
| `launch_input_projection` | complete launch-input-projection object |
| `launch_input_projection_byte_count` | `positive_count` |
| `launch_input_projection_sha256` | `sha256` |
| `limit_row_sha256` | `sha256` |
| `local_ref_transaction` | complete `pontius-local-ref-transaction-v1` object or `null` |
| `local_ref_transaction_byte_count` | `positive_count` or `null` |
| `local_ref_transaction_sha256` | `sha256` or `null` |
| `memory_bytes` | `positive_count` |
| `operation` | equal to the authorization operation |
| `operation_schedule_sha256` | `sha256` |
| `plan_sha256` | `sha256` |
| `operation_precondition_sha256` | `sha256` or `null` |
| `rehearsal_case_id` | exact authorization value |
| `rehearsal_step_ordinal` | exact authorization value |
| `rehearsal_task_binding_id` | exact authorization value |
| `repository_projection` | complete owner-only `repository_projection` object |
| `repository_projection_byte_count` | `positive_count` |
| `repository_projection_sha256` | `sha256` |
| `role` | equal to the authorization role |
| `role_projection_byte_count` | `positive_count` |
| `role_projection_sha256` | `sha256` |
| `role_table_instance_byte_count` | `positive_count` |
| `role_table_instance_sha256` | `sha256` |
| `route_selector` | complete owner-only route-selector canonical document |
| `round` | `round` |
| `runtime_calibration_receipt` | complete runtime-limit-calibration receipt |
| `runtime_calibration_receipt_artifact` | `artifact_identity` |
| `runtime_calibration_receipt_byte_count` | `positive_count` |
| `runtime_calibration_receipt_sha256` | `sha256` |
| `schedule_active_process_limit` | `positive_count` |
| `schedule_variant` | `schedule_variant` |
| `schema` | exact schema literal |
| `schemas_sha256` | `sha256` |
| `source_projection_set_byte_count` | `positive_count` |
| `source_projection_set_sha256` | `sha256` |
| `stderr_byte_cap` | `positive_count` |
| `stdout_byte_cap` | `positive_count` |
| `task` | `task` |
| `wall_ms` | `positive_count` |
| `worker_environment` | complete `pontius-environment-block-v1` object |
| `worker_launch_attempt` | complete `pontius-worker-launch-attempt-v1` object |
| `worker_launch_directory_projection` | complete `pontius-launch-directory-projection-v1` object |

`worker_launch_attempt` is the immutable pre-call input object. It contains the
application, command line, environment, current directory, flags, handle list,
and five process attributes, but no call outcome, Win32 error, PID, lifecycle,
or terminal fact. The complete `pontius-worker-launch-result-v1` is produced
only after this consumed dispatch has authorized the actual call and is carried
only by downstream failure, cleanup, final-revalidation, and runtime evidence.

The bound schedule is a canonical document named by the accepted role source
projection. One dispatch starts one role process and arms the owner for only
the preregistered child steps in that schedule. The role process cannot create
a child. Each expanded network child has a distinct
`(dispatch_nonce, step_ordinal, repeat_ordinal)` one-use credential session. No
child receives an independently reusable dispatch. `limit_row_sha256` equals
the digest of the unique runtime-limits row for this role, operation, dispatch
mode, and schedule variant. CPU time, memory, active wall, cleanup reserve, and
output caps equal that row and its accepted calibration receipt. The complete
receipt object equals its artifact bytes, reproduces the adjacent positive
count and digest, and matches the dispatch role-independent operation/mode/
variant coordinate. Schedule
active-process limit also
equals the row and every `SCHEDULE_STEP` Job binding under this dispatch.
The dispatch repeats the authorization's source-projection-set byte count and
digest exactly; the held runtime-owner projection is therefore part of every
live launch even though it is not loaded into the child.
`worker_launch_directory_projection` has scope `WORKER`, null step and repeat
ordinals, and a dispatch nonce equal to this dispatch. Its sole run-directory
row supplies both the worker current directory and the `TEMP` and `TMP` values.
`worker_environment` is the complete six-entry worker grammar in frozen order:
`LANG`, `LC_ALL`, `SYSTEMROOT`, `TEMP`, `TMP`, and `WINDIR`. Its two dynamic
values equal that run directory; the four literals equal the held policy.
The supervisor passes the object's exact reconstructed UTF-16LE block bytes to
the initial worker `CreateProcessW`; a digest-only, parent-derived, reordered,
or independently reconstructed population is invalid.
The complete repository projection, its byte count, and digest reproduce the
canonical bytes plus LF and equal the authorization payload. The trusted owner
opens and holds its exact path, control, object-storage, and handle population
before any repository read or process creation. This object is owner-only: it
is never streamed to the planner or inferred from a path, digest, observation,
or receipt.
The complete owner-only `route_selector` reproduces the authorization's route-
selector identity. It is excluded from both input projections and every
`READ_OPERATION_INPUT` row. For a normal selector, the owner validates all
role-applicable preregistration fields; builder validation excludes endpoint,
main, and review-output capabilities absent from its table. For a bootstrap
selector, only `OFFLINE` or `REHEARSAL` table bindings are valid. The owner
derives every used ref and requires equality before process creation.

The three local-ref-transaction fields are all nonnull exactly for a
`MUTATION_ATTEMPT` variant containing `CREATE_BUILDER_TUPLE` or
`CREATE_INTEGRATION_ATTEMPT`, and otherwise all null. The owner resolves every
stable or authorization-derived ref, constructs the complete null-endpoint
transaction from the accepted authorization and repository projection, and
only then completes this dispatch. Its byte count and digest use canonical
bytes plus LF. The transaction contains the external authorization digest and
never a dispatch, result, observation, or evidence digest; the dispatch may
therefore bind it without a content-hash cycle. It is owner-only and absent
from planner launch and input projections.

The three fault-reservation fields are all null outside a rehearsal campaign
step with a selected `FAULT` fixture. For such a step they are all present,
reproduce the complete object below, and its dispatch nonce equals this dispatch.
The reservation is controller-only and absent from role input projections.
The dispatch also repeats the authorization's operation-input-projection byte count and
digest exactly. `launch_input_projection` is the complete canonical downstream
projection; its byte count and digest reproduce those bytes and its nested
authority projection equals the authorization. Its reserved authorization,
precondition, and optional phase-bundle rows obey the mode and result-state
rules above. The supervisor holds every named source before process creation,
streams rows only through `READ_OPERATION_INPUT`, and revalidates the complete
population before terminal evidence.

For `OBSERVATION_ONLY`, `schedule_variant` is exact `OBSERVE`. For
`MUTATION_ATTEMPT`, it equals the variant derived by the bound operation
precondition. Operation, mode, variant, schedule digest, and complete schedule
bytes must all agree before process creation.

For `OBSERVATION_ONLY`, `operation_precondition_sha256` is `null`, and the
schedule has no authority-object write, authority-ref write, or push step. A
remote graph fetch may target only a dispatch-owned scratch object database
with no refs. For `MUTATION_ATTEMPT`, the field binds the complete canonical
operation precondition above; the schedule repeats every decisive mutable
observation before entering its declared local or remote mutation.

The controller atomically marks the `(plan_sha256, dispatch_nonce)` pair spent
through the durable registry below before process creation and never launches
it again. A crash may require an
observation-only dispatch and, only if still eligible, a new mutation dispatch
with a larger attempt ordinal and nonce while retaining the same transition
authorization. Dispatch identity, attempt ordinal, nonce, temporary paths, and
runtime handles MUST NOT enter a Git object.

`pontius-consumed-dispatch-record-v1` has exactly `authorization_sha256`,
`dispatch_nonce`, `dispatch_sha256`, `plan_sha256`, `schema`, and `state`.
`state` is exact `CONSUMED`; every other field equals the complete launch
dispatch. Its external identity is its canonical bytes plus LF.

The accepted runtime projection binds a controller-owned consumed-dispatch
registry directory, its final path and same-query file identity, its restrictive
ACL policy, and filename grammar
`<plan_sha256>-<dispatch_nonce>.json`. Before any `CreateProcessW`, the trusted
supervisor opens the final record with `CREATE_NEW` and write-through semantics,
writes the complete record, calls `FlushFileBuffers`, closes, reopens with no
write/delete sharing, reparses and rehashes it, and retains that handle through
the launch. Successful creation of the canonical filename spends that
`(plan_sha256, dispatch_nonce)` key immediately, before the first content
byte. The complete validated record is additionally required before any process
starts.

On startup, every directory entry is first classified by filename and file
kind. A canonical grammar-matching regular-file name spends only its named key,
even when a crash left its content empty, partial, unreadable, noncanonical, or
different. Such a key can never launch and the entry is retained permanently;
unrelated keys remain available. A name outside the grammar, a duplicate
case-fold name, a nonregular or reparse entry, a directory identity or ACL
mismatch, or an enumeration ambiguity blocks every launch. Records and
incomplete spent-key anchors are never deleted, renamed, truncated, repaired,
or reused.

Startup enumerates and classifies the complete registry before accepting a
dispatch. Crash after create-new, during any write, after flush, after close, or
after reopen spends the dispatch without an operation, which is safe; the
controller must use a new nonce after fresh observation. Crash rehearsal proves
anchor survival, same-key replay refusal, and unrelated-key availability at
every boundary. A process-start boundary is reachable only after complete-byte
reopen validation. No in-memory set or terminal receipt can substitute for the
pre-launch durable anchor.

## 5. Canonical raw tree and commit bytes

### 5.1 Raw tree input

`pontius-raw-tree-input-v1` has exactly `entries` and `schema`. `entries` is an
array of zero or more tree-entry objects. A tree-entry object has exactly:

| Key | Type |
| --- | --- |
| `mode` | `100644`, `100755`, or `40000` |
| `name` | one repository-path segment |
| `oid` | `oid` |
| `type` | `blob` or `tree` |

Mode `40000` requires type `tree`; the two other modes require type `blob`.
Symlinks, gitlinks, sparse entries, and unknown modes are forbidden. `name`
contains printable ASCII without `/`, backslash, NUL, or whitespace and is not
`.` or `..`. Duplicate, case-fold-colliding, invalid Windows, and file/tree
prefix-colliding names refuse.

Entries use Git's tree-name order. Compare unsigned name bytes; for ordering
only, append `/` to a tree name and NUL to a blob name. The exact raw tree bytes
are the concatenation, in that order, of:

```text
<mode ASCII> SP <name ASCII> NUL <20 raw OID bytes>
```

Trees are built bottom-up. The producer passes only those bytes to
`git hash-object -t tree -w --stdin`, independently computes the SHA-1 Git OID,
then reparses the stored tree and requires byte equality. `mktree`, checkout,
the index, attributes, and filters are not part of this route.

### 5.2 Raw commit input

The schema literal is `pontius-raw-commit-input-v1`. It has exactly:

| Key | Type |
| --- | --- |
| `author` | actor object |
| `committer` | actor object |
| `kind` | commit kind |
| `message` | `message` |
| `parents` | ordered `oid` array |
| `schema` | exact schema literal |
| `tree_oid` | `oid` |

An actor object has exactly `email`, `name`, `timestamp`, and `utc_offset`.
`name` is nonempty printable ASCII without `<`, `>`, leading space, or trailing
space. `email` is printable ASCII without spaces, `<`, or `>`, and contains one
`@`. `timestamp` is a `count` supplied by the frozen plan. `utc_offset` is the
exact literal `+0000`.

A `message` contains printable ASCII and LF, contains no CR or NUL, and ends in
exactly one LF. Its exact bytes and maximum size are fixed before object
creation. It is not obtained from an editor, config, locale, or wall clock.

Commit kinds and parent order are closed:

| Kind | Exact parent population and order |
| --- | --- |
| `CANDIDATE` | one parent: pinned candidate base `B` |
| `PACKET` | one parent: exact candidate commit |
| `PACKET_INTEGRATION` | first parent fresh H main `H0`; second parent packet `P` |
| `REVIEW_OUTPUT` | one parent: exact integrated packet `I` |
| `REVIEW_FINALIZER` | one parent: fresh H main predecessor |
| `DISPOSITION` | one parent: fresh H main predecessor |
| `UTILITY_CEREMONIAL_INTEGRATION` | one parent: fresh P product predecessor |
| `UTILITY_CEREMONIAL_INTEGRATION_RECORD` | one parent: fresh H main predecessor |
| `UTILITY_BOOTSTRAP_DURABLE_DISPOSITION` | one parent: fresh H main predecessor |

No `encoding`, `gpgsig`, `mergetag`, continuation, or unknown header is allowed.
The exact commit payload is:

```text
tree <tree_oid> LF
parent <parents[0]> LF
[parent <parents[n]> LF, in stored order]
author <name> SP <email-in-angle-brackets> SP <timestamp> SP +0000 LF
committer <name> SP <email-in-angle-brackets> SP <timestamp> SP +0000 LF
LF
<message bytes, including final LF>
```

The producer passes only that payload to
`git hash-object -t commit -w --stdin`. It independently computes the Git OID
over `commit`, one space, the decimal payload length, NUL, and the payload. The
returned OID, independent OID, stored bytes, parsed headers, and raw input MUST
all agree before a ref transaction.

Git identity config, environment identity, current time, locale, editor, hooks,
and porcelain commit construction are outside this grammar.

### 5.3 Main-overlay build spec

`pontius-main-overlay-spec-v1` is the complete offline input to
`BUILD_MAIN_OVERLAY`. It has exactly:

| Key | Type |
| --- | --- |
| `commit_input_sha256` | `sha256` |
| `commit_metadata` | `commit_metadata` |
| `expected_commit_oid` | `oid` |
| `expected_tree_oid` | `oid` |
| `ledger_appends` | ledger-append-input array |
| `main_predecessor_oid` | `oid` |
| `overlay_kind` | overlay kind |
| `overlay_rows` | overlay-row array |
| `plan_sha256` | `sha256` |
| `round` | `round` |
| `schema` | exact schema literal |
| `schemas_sha256` | `sha256` |
| `task` | `task` |

Overlay kind is `PACKET_INTEGRATION`, `REVIEW_FINALIZER`, or `DISPOSITION`.
An overlay row has exactly:

| Key | Type |
| --- | --- |
| `destination_path` | repository path |
| `mode` | `mode` |
| `source_kind` | overlay source kind |
| `source_blob_oid` | `oid` |
| `source_byte_count` | `count` |
| `source_path` | repository path |
| `source_sha256` | `sha256` |

Overlay source kind is exactly one of:

```text
PACKET_BLOB
REVIEW_OUTPUT_BLOB
CONTROLLER_BLOB
DERIVED_LEDGER_APPEND
```

A ledger-append input has exactly `destination_path`, `fragments`,
`predecessor`, and `result`. `predecessor` and `result` are
`artifact_identity` objects with the same destination path and mode.
`fragments` is an ordered array of one or two `artifact_identity` objects. The
result bytes equal the predecessor bytes followed by every complete fragment
in stored order, with no inserted, removed, or normalized byte. Its blob OID,
SHA-256, and byte count are independently recomputed.

Rows sort by ASCII `destination_path`. Destinations are unique and have no
case-fold or prefix collision with the predecessor tree. `PACKET_BLOB` resolves
only through the exact packet parent. `REVIEW_OUTPUT_BLOB` resolves only through
one finalizer-bound permanent output ref. `CONTROLLER_BLOB` resolves only from
retained bytes whose complete artifact identity is in the authorization.
`DERIVED_LEDGER_APPEND` is accepted only when its bytes equal the matching
ledger-append result. Every blob is independently reparsed and hashed. Entries
outside the authorized overlay remain byte-identical to the predecessor tree.

`PACKET_INTEGRATION` has the exact append population preregistered by its packet
integration plan. `REVIEW_FINALIZER` has exactly one append whose destination
is `<task>/progress.md` and whose two fragments are the slot ledger artifacts in
ordinal order. `DISPOSITION` has an empty `ledger_appends` array. Its controller
line is retained in the disposition package and reaches the program ledger only
through the separately authorized adopted Stage 5. Every
`DERIVED_LEDGER_APPEND` overlay row has exactly one matching append input, and
no other row may target that path.

The bound raw commit input's metadata equals `commit_metadata`; its tree equals
`expected_tree_oid`; and its parent shape matches `overlay_kind`. The spec does
not contain its own digest or an authorization identity.

`pontius-object-write-plan-v1` is downstream of an authorization and upstream
of object-writing children. It has exactly `authorization_sha256`,
`object_count`, `objects`, `operation`, `schema`, and `source_input_sha256`.
An object row has exactly `byte_count`, `expected_oid`, `object_type`, `ordinal`,
`payload_sha256`, and `payload_source`. Object type is `blob`, `tree`, or
`commit`; `payload_source` is `PLANNER_STREAM` or `OWNER_HELD_STATIC`; ordinals
are positive and contiguous. A planner-stream row's held length-framed payload
reproduces byte count, SHA-256, independent Git OID, and the operation's
complete deterministic object equations before the first write. An owner-held-
static row instead equals one complete packet-static-source-map row and uses
`HASH_HELD_BLOB`; it has no planner byte frame. Rows occur in dependency order, cover every
required write exactly once, and exclude already exact objects when the selected
build predicate permits omission. The owner derives and validates the complete
population from authorization-bound inputs. `source_input_sha256` equals the
accepted authorization's complete `input_projection_sha256` for every plan-
bearing operation; no independent scalar or selected subset is permitted. A
planner row cannot add an object
or capability. The `PLANNER_STREAM` partition equals `WRITE_OBJECT_ROWS` and is
bounded by that repeat cap. The `OWNER_HELD_STATIC` partition is valid only for
`FREEZE_PAIR`, equals `PACKET_STATIC_ROWS` and the packet-build `STATIC_BLOB`
population, and is bounded by that separate repeat cap. Both repeats must finish
their complete populations; `object_count` is the sum of their disjoint counts.
The plan grants no ref or remote authority.

The operation and selected mutation variant determine the complete plan shape.
`FREEZE_PAIR/CREATE_LOCAL_TUPLE` covers every newly required candidate, packet,
tree, commit, static blob, and builder-intent object.
`ADOPT_PAIR/ADOPT_LOCAL_TUPLE` covers exactly the reconstructed builder-intent
blob; fetched closure objects are already baseline residue.
`BUILD_REVIEW_OUTPUT/BUILD_OBJECTS` and
`BUILD_MAIN_OVERLAY/BUILD_OBJECTS` cover their complete newly required tree and
commit closure. `INTEGRATE_PACKET/CREATE_ATTEMPT_AND_PUSH` covers exactly the
integration-intent blob; its result tree and commit are already bound by the
prior object-build receipt. A selected plan omits an already exact object only
under its operation's closed build predicate. No other operation or mutation
variant has a nonnull plan.

For `BUILD_REVIEW_OUTPUT` and `BUILD_MAIN_OVERLAY`, every stored-object fact is
consumed exactly once by the object-build receipt. For `FREEZE_PAIR`, every fact
is retained in the complete accepted schedule transcript and revalidated before
`CREATE_BUILDER_TUPLE`; terminal authority is the fresh `LOCAL_EXACT` builder-
tuple observation. `FREEZE_PAIR` neither creates nor requires an object-build
receipt. `ADOPT_PAIR` and `INTEGRATE_PACKET` likewise retain their standalone-
intent write facts in the complete plan and schedule transcript; their later
atomic local-ref transaction cannot substitute for that object provenance.

### 5.4 Expected-object observation

`pontius-expected-object-observation-v1` has exactly `commit`,
`repository_projection_sha256`, `schema`, `state`, and `tree`. Each member has
exactly `expected_oid`,
`observed_type`, and `state`; `observed_type` is the expected type or `null`, and
member state is `ABSENT`, `EXACT`, `DIFFERENT`, or `UNKNOWN`. `EXACT` requires
raw-byte, type, OID, and complete declared-closure equality.
`repository_projection_sha256` equals the owner-held complete projection named
by the build authorization and later object-build receipt. The complete
projection remains only in launch and runtime evidence and never enters this
planner-visible observation.

Aggregate precedence is `OBJECTS_UNKNOWN`, then `OBJECTS_DIFFERENT`, then the
exact/absent cases. Any unknown member is `OBJECTS_UNKNOWN`; otherwise any
readable mismatch is `OBJECTS_DIFFERENT`; both absent is `OBJECTS_ABSENT`; both
exact is `OBJECTS_EXACT`; and any other absent/exact mix is
`OBJECTS_BUILDABLE`. A build mutation is eligible only for
`OBJECTS_ABSENT` or `OBJECTS_BUILDABLE`; `OBJECTS_EXACT` is idempotent success
without an object write. Different or unknown preserves and refuses. These
content-addressed object rules do not authorize any ref mutation.

## 6. Freeze inputs, utility authority, and local tuple

### 6.0 Stage 0b proportionality counter and disposition

`pontius-utility-bootstrap-retention-authority-v1` is an upstream self-free
controller policy and has exactly `authorization_id`, `authorized_producer_id`,
`chain_genesis_sha256`, `controller_id`, `entry_id_grammar`,
`public_key_hex`, `public_key_sha256`,
`retention_service_id`, `schema`, `service_namespace`, `signature_algorithm`,
`verifier_file_identity`, `verifier_source_entry_sha256`, and
`write_once_policy`. Authorization, producer, controller, service, and
namespace values are frozen identifiers. Entry IDs use exact `nonce` grammar.
Public-key hex is exactly 64 lowercase hexadecimal characters encoding the
32 raw Ed25519 public-key bytes; its SHA-256 hashes those decoded bytes.
Signature algorithm is
exact `ED25519`; write-once policy is exact
`CREATE_ONLY_HASH_CHAIN_FLUSH_BEFORE_RECEIPT_V1`. The held independent verifier
and reviewed source entry parse and verify that algorithm. The genesis digest
is the controller-frozen head predecessor for the first entry. This authority
exists outside P, H, Git, and the utility process before the first governed
publication; it authorizes only the named producer to append records to the
named service namespace and grants no repository-ref capability.

`pontius-stage0b-activation-v1` has exactly `activated_series_id`,
`excluded_bootstrap_series_id`, `rejected_root`, `retention_authority`,
`retention_authority_byte_count`, `retention_authority_sha256`, `schema`, `task`,
`utility_acceptance_authority`, `utility_acceptance_authority_byte_count`,
`utility_acceptance_authority_sha256`, and
`utility_acceptance_publication`. `utility_acceptance_publication` is a complete
`pontius-utility-acceptance-publication-v1`; its nested authority, count, and
digest equal this activation's authority triple byte-for-byte. Both accepted
objects precede this activation. The retention-authority object, count, and
digest reproduce the complete upstream policy carried by utility acceptance;
the activated series cannot substitute a service, producer, verifier, key,
algorithm, namespace, genesis head, or write-once policy. Excluded series
is exact `v0a-i01-freeze-tools-design`; activation cannot authorize any r002-
r005 design or implementation-bootstrap review that built the utility. The
activated series is a different `stage0b_series_id`. `rejected_root` is the
complete series-specific object below, has that activated series, and records
the immutable rejected r001 from which the first governed r002 descends. Task
equals the rejected root and the accepted utility's implementation task.

`pontius-stage0b-activation-publication-v1` has exactly `activation`,
`activation_artifact`, `activation_byte_count`, `activation_sha256`,
`publication`, `remote_observation`, `schema`, and `task`. Activation is the complete
object above. Its canonical bytes, including the required final LF, equal the
artifact bytes and reproduce the positive count and digest. Publication is a
complete adopted-rule-6 publication with stage exact
`RULE6_STAGE0B_ACTIVATION_PUBLICATION`; its artifact population contains the
activation artifact exactly once. The outer remote observation equals the
publication's complete observation and proves its commit/ref exact. This
self-excluding wrapper, rather than the activation body, owns every commit,
ref, and remote coordinate and precedes the activated series' r002 candidate
and calibration freeze. Every active Stage 0b counter and downstream carrier
binds this complete wrapper, its canonical byte count, and its SHA-256. Without
it the Stage 0b schemas are prospective data/test contracts only and grant no
authority. Task equals the activation, publication coordinates, and its
`<task>` artifact-path component.

The current `v0a-i01-freeze-tools-design` r002 through r005 series is the
excluded bootstrap series. The external coordinator administers its dated r005
breaker ruling and reviews through adopted `docs/workflow.md` and packet rule 6;
no Stage 0b JSON object, publication, executable, or future activation can
authorize or retrospectively upgrade that bootstrap work. The canonical
terminal declaration in these six P documents and H coverage is its retained
human-coordinator receipt. The Stage 0b contracts below become executable only
for a different series named by a post-acceptance activation.

`pontius-stage0b-breaker-calibration-v1` has exactly:

| Key | Type |
| --- | --- |
| `base_rate_observations` | exact two-row array defined below |
| `calibration_id` | exact `THREE_CORRECTIVE_ROUNDS_FROM_BASE_RATES` |
| `corrective_round_cap` | exact integer `3` |
| `decision_date` | exact `2026-09-01` |
| `decision_phase` | exact `PRE_R002_FREEZE` |
| `early_exit_on_build_eligible_clean` | exact `true` |
| `lock_event` | exact `R002_FREEZE` |
| `no_r006` | exact `true` |
| `r002_frozen_at_decision` | exact `false` |
| `residual_finding_breaker_unchanged` | exact `true` |
| `schema` | exact schema literal |
| `series_id` | `stage0b_series_id` |
| `task` | `task` |
| `terminal_rule_locked_after_r002_freeze` | exact `true` |
| `terminal_round` | exact `r005` |
| `terminal_round_ordinal` | exact integer `5` |

A base-rate row has exactly `lifecycle_id` and `rounds_observed`. The two rows,
in order, are `v0a-i01-prereg` with integer `5` and `v0a-i01-ab` with integer
`6`. The calibration records the controller ruling made on 2026-09-01 while
r002 was mutable and before any frozen r002 review evidence existed. It is
amendable only until the r002 freeze. The five-round preregistration and
six-round A/B histories justify three corrective successors, r003 through
r005, as a cap rather than an entitlement. Every later valid packet and
counter repeats the complete r002 calibration, artifact identity,
byte count, and digest byte-for-byte. Missing or different calibration bytes
are malformed and cannot enter review. Any post-freeze P or H declaration
that attempts to change the terminal rule while retaining the exact
calibration is proposed and adjudicated as
`POST_FREEZE_CALIBRATION_CHANGE`, which selects gate-defect parking. No
evidence opened after r002 freeze can change the terminal ordinal or create
r006.

`pontius-stage0b-interface-inventory-v1` has exactly `round`,
`round_ordinal`, `rows`, `schema`, `series_id`, and `task`. The series ID uses
`stage0b_series_id`; the round is the exact `r%03d` rendering of the ordinal.
Rows sort by `(kind, interface_id)` as ASCII bytes and are unique. A row has
exactly `contract`, `contract_id`, `interface_id`, and `kind`.
`contract_id` selects exactly one registered contract.
Kind is exact `SCHEMA`, `ENTRY_POINT_CONTRACT`, or
`LIFECYCLE_STATE_SET`. Interface ID matches
`[A-Z][A-Z0-9_.:/-]{0,127}` and remains stable for the life of the series.

`contract` has exactly `clauses`, `source_paths`, and `stable_name`.
`source_paths` is the sorted nonempty set of normative P paths that declare the
interface. `stable_name` is the exact schema literal, entry-point identifier,
or lifecycle identifier. `clauses` is a nonempty ordered array of unique
objects with exactly `clause_key` and `text`. Text is nonempty LF-free UTF-8.
Clause key is exact `<registered-contract-id>#<stable-local-clause-id>`; local
ID matches `[A-Z0-9_.:/-]{1,127}`. Clause keys are globally unique across the
inventory. Every clause prefix equals the row's `contract_id`. Independently
reviewable contracts sharing one path use separate interface rows. For
`SCHEMA` the clauses completely name root and row
fields, tagged variants, scalar domains, nullability, cardinality, ordering,
and cross-object equalities. For `ENTRY_POINT_CONTRACT` it completely names
caller, callee, input, output, refusal, authority, and first-effect boundary.
For `LIFECYCLE_STATE_SET` it completely names states, transitions, terminal
states, and cause precedence. The inventory is a comparison proxy, not
permission to omit a normative contract from P. Before opening the coordinator
inventory, each cold reviewer independently enumerates the same three kinds.
An omitted, duplicate, unstable, or disputed row makes classification
`AMBIGUOUS`.

`pontius-stage0b-semantic-interface-row-v1` has exactly `kind` and
`semantic_contract`. `semantic_contract` has exactly `clause_texts`,
`source_paths`, and `stable_name`. The tuple `(kind, stable_name)` is unique
within each inventory and is the pairing key. Clause texts are a nonempty
ordered array of unique nonempty LF-free UTF-8 strings. Source paths are sorted,
unique, and nonempty reviewed P paths. Stable name is nonempty LF-free UTF-8;
kind uses the coordinator inventory's closed three-value domain. Canonical
semantic-row bytes are canonical JSON for this object plus one LF.

Each coordinator inventory row derives exactly one semantic-interface row:
`kind` is copied unchanged; `stable_name` and `source_paths` equal its nested
contract; and `clause_texts` is the ordered projection of
`contract.clauses[*].text`. The derived population is a bijection over
coordinator rows, has unique pairing keys, and its row digests hash exactly the
canonical semantic-row bytes above. No producer-supplied semantic projection
can replace this derivation.

`pontius-stage0b-independent-interface-inventory-v1` has exactly
`candidate_manifest_sha256`, `candidate_oid`, `candidate_ref`, `reviewer_id`,
`reviewer_ordinal`, `round`, `round_ordinal`, `rows`, `schema`, and
`series_id`, and `task`. Root identities equal the reviewer's frozen slot and input
snapshot. The two reviewer artifacts are distinct blobs. A row has exactly
`kind`, `reviewer_row_id`, and `semantic_contract`. `semantic_contract` has
exactly `clause_texts`, `source_paths`, and `stable_name`. Those values derive
only from reviewed P bytes, without coordinator interface IDs, contract IDs, or
clause keys and without requiring a coordinator counterpart.
`reviewer_row_id` is
the lowercase SHA-256 of the corresponding complete canonical
`pontius-stage0b-semantic-interface-row-v1` bytes. Rows sort by
reviewer-row ID and are unique. Coordinator inventory rows must also have
unique semantic projections. This inventory is fully derivable from P bytes
before the reviewer opens any coordinator-assigned label.

`pontius-stage0b-contract-registry-v1` has exactly `rows`, `schema`,
`series_id`, and `task`. A row has exactly `contract_id` and `source_paths`. Contract ID
matches `[A-Z][A-Z0-9_.:/-]{0,127}`; source paths are sorted, unique, and
nonempty. Rows sort by contract ID and are unique. The registry is complete for
every independently reviewable P contract. Every inventory row names one
registered contract, and its source paths are a subset of that registry row's
source paths. A later interface ADD joins one existing contract through its
inventory row. The exact r002 registry freezes
before review and every successor repeats it byte-for-byte. Contract rename,
subdivision, merge, or omission requires a new preregistration; it cannot reset
a residual ordinal. The reserved contract
`STAGE0B.WIRE.COUNTER_CLASSIFICATION` covers the counter-classification wire
and may have H source paths.

`pontius-stage0b-interface-change-v1` has exactly `change_kind`,
`current_row_sha256`, `interface_id`, `kind`, and `previous_row_sha256`.
Change kind is `ADD`, `REMOVE`, or `MODIFY`. `ADD` requires null previous and
nonnull current digest. `REMOVE` requires nonnull previous and null current.
`MODIFY` requires two unequal nonnull digests for the same stable ID and kind.
The digests hash complete canonical inventory-row bytes. Renaming an interface
is one REMOVE plus one ADD. Rows sort by `(kind, interface_id, change_kind)`
and are unique.

`pontius-stage0b-review-scope-v1` has exactly `candidate_manifest_sha256`,
`candidate_oid`, `candidate_ref`, `review_inputs`, `round`,
`round_ordinal`, `schema`, `series_id`, and `task`. A review-input row has exactly
`artifact`, `byte_count`, `purpose`, and `sha256`. Purpose is
`COVERAGE`, `HANDOFF_INSTRUCTIONS`, `WORKFLOW_RULES`,
`REVIEW_CHECKLIST`, or `OTHER_DECLARED_INPUT`. Rows sort by artifact path
and are unique. They are the complete set of noncandidate byte sequences that
`handoff.md` permits a reviewer to open after its independent inventory and
before its verdict, excluding generated Stage 0b calibration, registry,
inventory, projection, counter, and scope objects. Candidate fields equal the
current P tuple. Every artifact resolves inside the current H handoff or the
explicit source-workflow coordinate named by `handoff.md` and reproduces its
count and digest.

`pontius-stage0b-review-scope-change-v1` has exactly `change_kind`,
`coordinate`, `current_sha256`, and `previous_sha256`. Change kind is
`ADD`, `REMOVE`, or `MODIFY`, with null fields only on the absent side and
unequal nonnull digests for `MODIFY`. The canonical coordinate is
`P:CANDIDATE` for the complete canonical candidate ref, OID, and manifest
tuple and `H:<artifact-path>` for every review input. A P digest hashes that
complete tuple; an H digest hashes the complete canonical artifact identity,
count, purpose, and SHA-256 row. Rows sort by coordinate and are unique. They
are the complete map difference between predecessor and current review scopes.

`pontius-stage0b-terminal-rule-projection-v1` has exactly `rows`, `schema`,
`series_id`, and `task`. It contains one path-sorted row for each of the six P
candidate files plus H `coverage.md` and `handoff.md`. A row has exactly
`corrective_round_cap`, `declaration_byte_offset`, `lock_event`,
`no_r006`, `source_path`, `source_repository_id`, `source_sha256`,
`terminal_round`, `terminal_round_ordinal`, and
`terminal_rule_locked_after_r002_freeze`. Every semantic value equals the
corresponding parsed value from the source's sole canonical declaration:

The `terminal-declaration-v1` grammar recognizes a whole line with exact token
order `Stage0b: cap=<integer> lock=<token> no6=<Boolean> terminal=<round>
ordinal=<integer> locked=<Boolean>`.

The byte offset is the zero-based start of that exact LF-free UTF-8 line.
The integer, token, Boolean, and round fields retain their parsed values, so a
well-formed contradictory declaration can be represented. Source repository
is `PONTIUS_SOURCE` for P and `PONTIUS_HANDOFFS` for H. The source digest
resolves inside the current candidate or handoff commit. Zero or multiple
declarations, malformed syntax, an offset mismatch, or an omitted source row
refuses. The population excludes the projection itself and generated Stage 0b
carriers, preventing a content cycle.

Stage0b: cap=3 lock=R002_FREEZE no6=true terminal=r005 ordinal=5 locked=true

`pontius-stage0b-rejected-root-v1` has exactly `candidate_manifest_sha256`,
`candidate_oid`, `candidate_ref`, `rejection_artifact`,
`rejection_byte_count`, `rejection_sha256`, `round`, `round_ordinal`,
`schema`, `series_id`, `status`, and `task`. Round is exact `r001`, ordinal is
integer one, status is exact `REJECTED`, and series is a `stage0b_series_id`.
The candidate ref is the full immutable r001 review ref for that series.
Rejection artifact bytes parse under the adopted preactivation workflow,
reproduce the adjacent positive count and digest, and bind the same candidate,
manifest, task, series, round, and rejection decision. The activation embeds
this complete object; all active counters repeat it byte-for-byte. A caller-
supplied root, synthetic rejection, or root for the excluded bootstrap series
refuses activation.

`pontius-stage0b-predecessor-round-v1` has exactly:

| Key | Type |
| --- | --- |
| `candidate_manifest_sha256` | `sha256` |
| `candidate_oid` | `oid` |
| `candidate_ref` | full review ref |
| `contract_registry_sha256` | `sha256` |
| `counter_artifact` | `artifact_identity` |
| `counter_byte_count` | `positive_count` |
| `counter_sha256` | `sha256` |
| `decision` | exact `NEXT_DESIGN_ROUND` |
| `disposition_artifact` | `artifact_identity` |
| `disposition_byte_count` | `positive_count` |
| `disposition_publication` | complete disposition-publication object |
| `disposition_publication_byte_count` | `positive_count` |
| `disposition_publication_sha256` | `sha256` |
| `disposition_sha256` | `sha256` |
| `handoff_commit_oid` | `oid` |
| `handoff_packet_path` | exact `<task>/<round>` repository path |
| `handoff_ref` | exact `refs/heads/main` |
| `handoff_repository_id` | exact `PONTIUS_HANDOFFS` |
| `interface_inventory_artifact` | `artifact_identity` |
| `interface_inventory_byte_count` | `positive_count` |
| `interface_inventory_sha256` | `sha256` |
| `next_round` | `round` |
| `review_scope_artifact` | `artifact_identity` |
| `review_scope_byte_count` | `positive_count` |
| `review_scope_sha256` | `sha256` |
| `round` | `round` |
| `round_freeze_publication` | complete round-freeze-publication object |
| `round_freeze_publication_byte_count` | `positive_count` |
| `round_freeze_publication_sha256` | `sha256` |
| `round_ordinal` | `stage0b_round_ordinal` |
| `terminal_rule_projection_sha256` | `sha256` |
| `terminal_rule_projection_status` | `EXACT` or `DIFFERENT` |
| `task` | `task` |

`pontius-stage0b-predecessor-chain-v1` has exactly `calibration_sha256`,
`rejected_root`, `rounds`, `schema`, `series_id`, and `task`. `rejected_root` is the
complete activation-bound object above. For current ordinal N, `rounds` contains exactly
N minus 2 predecessor rows in ascending ordinal order. It is empty at r002.
Every artifact resolves to the named immutable publication, parses under its
declared schema, and reproduces its count and digest. Each row's counter,
inventory, candidate, review-input handoff, disposition, decision, and next
round agree. Round-freeze-publication bytes reproduce their adjacent count and
digest, output commit, handoff coordinates, packet artifacts, counter, and
reviewer bindings. Its disposition-publication bytes reproduce their adjacent count
and digest, nested disposition artifact, commit, ref, repository, and remote
observation. The next H handoff commit descends from that observed output and
preserves the predecessor task subtree byte-for-byte. Adjacent rows agree that
the earlier `next_round` is the later
`round`. Every counter repeats the r002 calibration digest. The chain series
and rejected root equal the complete activation. The last row's
`next_round` equals the current counter round. A missing row, reset, alias,
rebase, task split, or renamed series refuses.

`pontius-stage0b-successor-edit-v1` has exactly
`affected_interface_ids`, `authorizing_finding_ids`, `change_kind`,
`current_blob_oid`, `path`, and `previous_blob_oid`. Change kind is `ADD`,
`MODIFY`, or `REMOVE`, with null fields only on the absent side. Rows sort by
path and cover the complete prior-candidate-to-current-candidate P tree delta.
At r002 the array is empty. At a later round every row has a nonempty sorted
unique finding-ID array drawn only from the immediately preceding disposition's
blocking findings. `affected_interface_ids` is the sorted unique set of
interface IDs changed by that path and may be empty only for a proved
zero-count prose clarification or severity edit. The union equals every
interface-change row. Each cited finding must cover the edit path or one of its
affected interfaces, and every edit must be covered by at least one cited
finding. An unrelated edit, omitted changed path, unmapped interface,
cross-finding substitution, or invented finding ID refuses.

`pontius-stage0b-ambiguity-resolution-v1` has exactly
`ambiguity_finding_id`, `comparison_inventory_sha256`, `evidence`,
`evidence_byte_count`, `evidence_sha256`, `resolution_kind`,
`resolved_interface_ids`, `resolved_paths`, and
`resolved_previous_inventory_sha256`.
Resolution kind is `ADD_OMITTED_ROW`, `REMOVE_SPURIOUS_ROW`,
`REPLACE_DISPUTED_ROW`, or `PROVE_ZERO_COUNT_EDIT`. The evidence bytes parse
under the frozen resolver for that kind and reproduce the adjacent count and
digest. Comparison inventory is the immediately preceding frozen proposal; the
result is the reconstructed inventory of that same prior candidate after
resolving the dispute. Paths and interfaces equal the prior typed ambiguity
finding. A resolution may cite no successor edit when it corrects inventory
bookkeeping without changing P bytes; any cited edit must be covered by the
finding. At r002 this array is empty. A later counter has exactly one resolution
row for each immediately preceding `COUNTER_AMBIGUITY` blocker. Missing,
extra, or cross-finding resolution refuses.

`pontius-stage0b-blocker-resolution-v1` has exactly
`ambiguity_resolution_sha256`, `blocker_finding`,
`blocker_finding_sha256`, `evidence`, `evidence_byte_count`,
`evidence_sha256`, `resolution_kind`, and `successor_edit_row_sha256s`.
Resolution kind is `CANDIDATE_EDIT`, `EVIDENCE_ONLY`, or
`AMBIGUITY_RESOLUTION`. The blocker digest hashes the complete prior
disposition finding row. Successor-edit digests are sorted, unique, and each
names a complete current edit whose finding IDs cite this blocker. They are
nonempty only for `CANDIDATE_EDIT`. Ambiguity-resolution digest is nonnull only
for `AMBIGUITY_RESOLUTION` and names the matching specialized row above.
Evidence is a retained artifact whose bytes reproduce its count and digest and
demonstrate closure under the prior finding's required verification criteria.

`pontius-stage0b-reviewer-path-binding-v1` has exactly `reviewer_id`,
`reviewer_ordinal`, and `reviewer_path_slug`. Ordinals are one and two in
order; IDs equal the counter's two reviewer IDs in the same order. Slugs match
`reviewer_path_slug`, are distinct, and freeze in the counter before either
review starts. The full reviewer ID remains the attribution authority; the
slug is only its injective repository-path binding.

`pontius-stage0b-round-counter-v1` has exactly:

| Key | Type |
| --- | --- |
| `ambiguity_resolutions` | array of ambiguity-resolution rows |
| `blocker_resolutions` | array of `pontius-stage0b-blocker-resolution-v1` rows |
| `baseline_inventory_artifact` | `artifact_identity` |
| `baseline_inventory_byte_count` | `positive_count` |
| `baseline_inventory_sha256` | `sha256` |
| `breaker_calibration` | complete calibration object |
| `breaker_calibration_artifact` | `artifact_identity` |
| `breaker_calibration_byte_count` | `positive_count` |
| `breaker_calibration_sha256` | `sha256` |
| `candidate_manifest_sha256` | `sha256` |
| `candidate_oid` | `oid` |
| `candidate_ref` | full review ref |
| `contract_registry` | complete contract-registry object |
| `contract_registry_artifact` | `artifact_identity` |
| `contract_registry_byte_count` | `positive_count` |
| `contract_registry_sha256` | `sha256` |
| `coordinator_id` | `actor_id` |
| `cumulative_interface_change_count` | `count` |
| `current_inventory_artifact` | `artifact_identity` |
| `current_inventory_byte_count` | `positive_count` |
| `current_inventory_sha256` | `sha256` |
| `implementer_ids` | nonempty sorted unique `actor_id` array |
| `interface_changes` | array of interface-change rows |
| `predecessor_chain` | complete predecessor-chain object |
| `previous_inventory_artifact` | `artifact_identity` or `null` |
| `previous_inventory_byte_count` | `positive_count` or `null` |
| `previous_inventory_sha256` | `sha256` or `null` |
| `previous_review_scope_artifact` | `artifact_identity` or `null` |
| `previous_review_scope_byte_count` | `positive_count` or `null` |
| `previous_review_scope_sha256` | `sha256` or `null` |
| `proposal_ambiguity_affected_interface_ids` | sorted unique interface-ID array |
| `proposal_ambiguity_affected_paths` | sorted unique repository-path array |
| `proposal_ambiguity_reason` | nonempty LF-free UTF-8 string or `null` |
| `proposed_classification` | classification literal defined below |
| `reviewer_ids` | exactly two distinct `reviewer_id` values |
| `reviewer_path_bindings` | exactly two reviewer-path-binding rows |
| `resolved_previous_inventory_artifact` | `artifact_identity` or `null` |
| `resolved_previous_inventory_byte_count` | `positive_count` or `null` |
| `resolved_previous_inventory_sha256` | `sha256` or `null` |
| `review_scope` | complete review-scope object |
| `review_scope_artifact` | `artifact_identity` |
| `review_scope_byte_count` | `positive_count` |
| `review_scope_changes` | array of review-scope-change rows |
| `review_scope_sha256` | `sha256` |
| `round` | `round` |
| `round_interface_change_count` | `count` |
| `round_ordinal` | `stage0b_round_ordinal` |
| `schema` | exact schema literal |
| `series_id` | `stage0b_series_id` |
| `stage0b_activation_publication` | complete activation-publication wrapper |
| `stage0b_activation_publication_artifact` | `artifact_identity` |
| `stage0b_activation_publication_byte_count` | `positive_count` |
| `stage0b_activation_publication_sha256` | `sha256` |
| `successor_edits` | array of `pontius-stage0b-successor-edit-v1` rows |
| `task` | `task` |
| `terminal_rule_projection` | complete terminal-rule-projection object |
| `terminal_rule_projection_artifact` | `artifact_identity` |
| `terminal_rule_projection_byte_count` | `positive_count` |
| `terminal_rule_projection_sha256` | `sha256` |
| `terminal_rule_projection_status` | `EXACT` or `DIFFERENT` |

The coordinator is absent from `implementer_ids` and `reviewer_ids`; each
reviewer is absent from `implementer_ids`. Only the external coordinator issues
the calibration, registry, inventory, review scope, terminal projection,
counter, later disposition, and build authority. The implementer and reviewers
cannot issue, replace, or reinterpret any of them. The calibration, registry,
inventory, scope, projection, and counter are retained at exact paths
`stage0b-breaker-calibration.json`, `stage0b-contract-registry.json`,
`stage0b-interface-inventory.json`, `stage0b-review-scope.json`,
`stage0b-terminal-rule-projection.json`, and `stage0b-counter.json` in the
immutable H handoff commit before review starts.
The counter names the P candidate but not its containing H commit, avoiding a
content cycle.

Every nested object parses from its artifact and reproduces the adjacent count
and digest. The contract registry is byte-identical to r002 at every round.
Task equals the activation, rejected root, calibration, registry, current and
baseline inventories, review scope, terminal projection, predecessor chain,
every predecessor row, candidate packet path, and counter. Every independent
reviewer inventory repeats that same task. A cross-task object with equal
series, round, candidate, or digest is invalid.
The activation-publication artifact bytes parse as the complete wrapper, whose
canonical bytes reproduce its adjacent count and digest.
`stage0b_activation_publication` equals the complete post-acceptance wrapper,
`series_id` equals its nested activation's `activated_series_id`, and the
predecessor chain's rejected root equals that activation's `rejected_root`. The
excluded bootstrap series can
never satisfy those equations.
The current inventory and review scope round, ordinal, series, and candidate
equal the counter. Baseline inventory resolves to r002. At r002 all previous
and resolved-previous inventory and review-scope fields are null; baseline and
current inventory bytes are identical; both interface-change counts are zero;
and the predecessor chain, ambiguity resolutions, blocker resolutions,
successor edits, and review-scope changes are empty.

At a later round, previous inventory resolves to the final predecessor row's
frozen proposal. Resolved previous inventory is byte-identical to it when that
predecessor was nonambiguous. Otherwise it is the complete result of applying
every required ambiguity resolution to the same prior candidate. Baseline
remains exact r002. `interface_changes` is the complete set difference between
resolved previous and current inventory by stable ID and canonical row bytes.
Round count is its length. Inventory-only corrections therefore do not become P
interface-change events.

At a later round, previous review scope resolves to the final predecessor row's
scope. `review_scope_changes` is the complete canonical map difference.
Any P byte change or any added, removed, changed, or newly permitted review
input therefore advances the round ordinal. An inventory-only ambiguity repair
may advance with unchanged P bytes and an empty scope delta. A mutated H input
under the same ordinal, missing scope row, false zero delta, or scope alias
refuses before review.

`terminal_rule_projection_status` is `EXACT` exactly when all eight
projection rows exist and reproduce the frozen calibration tuple. It is
`DIFFERENT` only in a valid successor packet whose exact calibration remains
unchanged and at least one complete row declares a different semantic value.
`DIFFERENT` forces proposed classification `AMBIGUOUS`, reason exact
`POST_FREEZE_CALIBRATION_CHANGE`, and affected paths equal the differing
source rows. At r002 the status must be `EXACT`. A missing row, unresolved
source digest, or missing/different calibration is malformed and refuses; it
cannot be laundered into semantic parking.

Cumulative count is independently recomputed across the complete chain from
the resolved declaration inventory for every candidate transition; it is not
copied from the prior scalar. An ambiguous prior inventory remains an exact
comparison artifact, not an accepted completeness claim. A BUILD can occur
only after the current post-review adjudication is nonambiguous and every
predecessor ambiguity has a successor resolution.

At every later round, blocker resolutions are in finding-ID order and form an
exact bijection with the immediately preceding disposition's blocking findings.
Every prior blocker therefore has one closure claim, and every current
successor edit citation resolves through one such row. The ambiguity-resolution
subset is byte-bound to the specialized array. Missing, extra, duplicate,
unresolved, or cross-blocker rows refuse before review.

Proposed classification is an exact truth table:

- `BASELINE` occurs exactly at r002 when proposal ambiguity is null, change
  count is zero, and `interface_changes` is empty.
- `NO_INTERFACE_CHANGE` occurs exactly after r002 when proposal ambiguity is
  null, change count is zero, and `interface_changes` is empty.
- `INTERFACE_CHANGE` occurs exactly after r002 when proposal ambiguity is null,
  change count is positive, and it equals the interface-change array length.
- `AMBIGUOUS` occurs exactly when `proposal_ambiguity_reason` is nonnull.
  Known change rows and their mechanical count remain recorded but are not
  claimed complete.

Both proposal-ambiguity arrays are empty exactly when the reason is null. With
a nonnull reason at least one array is nonempty and covers the disputed paths
or interfaces. A changed candidate byte outside the declaration rows counts
zero in the proposal only when the coordinator can prove it is prose
clarification or a severity note.

The counter is an immutable pre-review proposal. A reviewer never mutates or
reissues it. Review discrepancy rows below feed the later disposition's
adjudicated classification. At r002, r003, or r004 an adjudicated ambiguity
becomes a typed blocking finding for the one permitted successor. At r005 it
stops. `POST_FREEZE_CALIBRATION_CHANGE` stops at every later ordinal.

`pontius-stage0b-packet-path-history-row-v1` has exactly `commit_oid`,
`packet_path_entry`, `parent_oids`, and `tree_oid`.
`packet_path_entry` is `null` when the path is absent and otherwise is the
exact raw-tree entry at that path. `parent_oids` is the commit object's complete
ordered parent array and is empty only at the fixed readable root.

`pontius-stage0b-packet-path-history-v1` has exactly `baseline_commit_oid`,
`main_predecessor_oid`, `packet_path`, `repository_id`, `rows`, and
`schema`, and `task`. Repository and packet path are exact `PONTIUS_HANDOFFS` and
`<task>/<round>`. `baseline_commit_oid` is exact
`f515631e2658961d7fb8725be0192e3b68648404`, the fixed root commit of
the H repository. Rows are the complete unique transitive ancestor closure of
`main_predecessor_oid` across every parent edge, sorted by commit OID. The main
predecessor and baseline occur exactly once. Every nonbaseline parent OID names
another row; the baseline alone has an empty parent array; every row is
reachable from the main predecessor; and no other root exists. Every commit and
tree is independently read as a raw Git object, every parent array equals the
raw commit order, and every row has `packet_path_entry=null`. A missing, extra,
unreadable, unrooted, second-parent-only, or path-present row refuses.

`pontius-stage0b-detached-worktree-v1` has exactly `common_directory`,
`head_oid`, `head_symbolic_ref`, `index_file`, `schema`, and
`worktree_directory`. Directories and index are complete retained path/file
identities. Head OID is the fresh base and symbolic ref is null.

`pontius-stage0b-hook-selection-v1` has exactly `core_hooks_path_values`,
`detached_symbolic_ref_exit_code`, `hook_path`, `hook_sha256`, `schema`, and
`selected`. The complete trusted Git configuration projection yields exactly
one effective hooks path; `hook_path` is its retained regular executable
`sealed_path_identity`, digest equals the exact installed post-commit bytes,
`selected` is true, and the hook's own `git symbolic-ref --quiet --short HEAD`
returns one in the detached worktree, so its first command exits without push.

`pontius-stage0b-git-command-result-v1` has exactly `argv`,
`current_directory`, `environment`, `executable`, `exit_code`, `schema`,
`stderr_hex`, and `stdout_hex`. Executable is the complete held PONTIUS_GIT
identity; directory and environment are complete closed objects; argv is the
exact absolute invocation; output is bounded hex; and commit success is exit
zero. No config override, hook bypass, `--no-verify`, alternate index, or
environment hook path is permitted.

`pontius-stage0b-detached-construction-v1` has exactly `base_oid`,
`commit_process_completion`, `detached_head`, `hook_selection`,
`output_commit_oid`, `packet_path`, `pre_publication_observation`, `schema`,
`staged_paths`, `task`, and `worktree_identity`. `commit_process_completion` is the
complete Git-command result, `hook_selection` the complete object above,
`worktree_identity` the complete detached-worktree object, and `staged_paths`
the exact path-sorted raw index/tree-entry array with `blob_oid`, `mode`, and
`path`. It bijects the round-freeze wrapper's packet-artifact set.
The coordinator creates a disposable
detached H worktree at the fresh remote-main predecessor, stages only the exact
packet paths, and uses ordinary `git commit`. `detached_head` is true before and
after commit. The installed post-commit hook is retained and its exact bytes
match the artifact/digest; because `git symbolic-ref --quiet --short HEAD` fails in the
detached worktree, the hook exits without a push. The commit has exactly the
base as its sole parent and the intended packet tree. `pre_publication_observation`
is the complete `PRE_PUBLICATION` freeze-ref observation taken after commit and
shows main still at the base and anchor absent. No hook disable,
rename, environment bypass, positive `commit-tree`, branch checkout, or broad
staging operation is permitted.

`pontius-stage0b-atomic-push-status-v1` has exactly
`atomic_capability_advertised`, `post_publication_observation`,
`pre_publication_observation`, `process`, `rows`, `schema`, and `state`.
`process` is one complete Git-command result whose argv is exact HTTPS
`push --porcelain --atomic` with the two explicit refspecs and exact
per-ref leases. Main renders
`--force-with-lease=refs/heads/main:<predecessor-oid>`; the absent anchor renders
`--force-with-lease=refs/pontius/freeze/<series-id>/<round>:` with an empty
expectation after the final colon. Forty zeroes remain the canonical semantic
absent OID in the update row and are never rendered as Git's absent-ref lease.
Rows are the strict
complete porcelain parse in update-ref byte order; each has exactly
`flag`, `ref`, `requested_update_sha256`, `status`, and `summary`. Porcelain
supplies only flag/ref/summary; old and new OIDs come from the frozen update row
plus complete pre/post remote observations and are never invented from status
text. Each row's requested-update digest selects exactly one update. State
`BOTH_ACCEPTED` requires exit zero, advertised atomic support, two `UPDATED`
rows and never an `UP_TO_DATE` row,
matching the requested updates, the complete pre observation, and the complete
post observation with both refs exact. Every other state is failure and grants
no round-freeze publication.

`pontius-stage0b-atomic-publication-v1` has exactly `atomic_requested`,
`construction`, `endpoint_id`, `post_publication_observation`,
`pre_publication_observation`, `push_status`, `repository_id`, `schema`,
`task`, and `updates`. `atomic_requested` is true. Updates are
exactly two rows in ref-byte order; a row has exactly `delete`,
`expected_old_oid`, `force`, `new_oid`, and `ref`. The main row expects the
fresh predecessor and advances to the output. The anchor row expects forty
zeroes and advances to the same output. Both rows have `delete=false` and
`force=false`; lease syntax supplies server-enforced compare-and-swap and does
not permit a non-direct-child main update. The owner invokes one Git HTTPS push
with exact `--atomic`, both leases, and the two explicit refspecs.
`construction` is the complete detached object above
and equals the update base/output. Both observations are complete typed objects
and equal the construction and freeze-anchor fields. `push_status` is the
complete object above and proves both accepted or neither accepted. A server that
does not advertise and honor atomic push makes this route unavailable.

`pontius-stage0b-freeze-anchor-v1` has exactly `anchor_ref`,
`atomic_publication`, `atomic_publication_byte_count`,
`atomic_publication_sha256`, `output_commit_oid`, `post_push_observation`,
`pre_push_observation`, `repository_id`, `round`, `schema`, `series_id`,
`task`, and `zero_old_oid`. `atomic_publication` is the complete object above and its
canonical bytes plus LF reproduce the adjacent positive count and digest.
Anchor ref is exact
`refs/pontius/freeze/<series_id>/<round>`; repository is `PONTIUS_HANDOFFS`;
and `zero_old_oid` is forty ASCII zeroes. `pre_push_observation` and
`post_push_observation` are complete
`pontius-stage0b-freeze-ref-observation-v1` objects at `PRE_PUBLICATION` and
`POST_PUBLICATION`. They equal the atomic publication and construction.
The pre object proves the anchor ref absent and main exact at the freshly
fetched predecessor; the packet-path history independently proves the path absent. The
atomic publication is one two-update transaction:
main expects that predecessor and advances to `output_commit_oid`; the anchor
expects the zero OID and advances to the same output. The complete post-push
remote observation proves both refs exact at that commit. No accepted writer
contains a delete, force, or retarget operation for this namespace. If a later
observation finds the anchor missing or different, the round is compromised
and parks; it is never recreated. Administrator or hosting-service mutation
outside accepted writers remains the explicit remote-integrity nonclaim.

`pontius-stage0b-round-freeze-publication-v1` has exactly
`candidate_manifest_sha256`, `candidate_oid`, `candidate_ref`,
`freeze_anchor`, `main_predecessor_oid`, `output_commit_oid`, `packet_artifacts`,
`packet_path`, `packet_path_history`, `publication_observation`,
`repository_id`, `reviewer_path_bindings`, `round`, `round_ordinal`,
`schema`, `series_id`, `stage0b_activation_publication`,
`stage0b_activation_publication_byte_count`,
`stage0b_activation_publication_sha256`, `task`, and `task_predecessor_oid`.
Repository and packet
path are exact
`PONTIUS_HANDOFFS` and `<task>/<round>`. Packet artifacts are the complete
path-sorted set at that path: `handoff.md`, `candidate.json`,
`manifest.sha256`, `coverage.md`, and the six coordinator JSON objects named
above. They resolve inside the output commit. Candidate, series, round, and
reviewer bindings equal the counter and candidate record.
The activation object, count, and digest equal the counter's complete triple;
its activated series equals `series_id`.

`packet_path_history` is the complete object above. Its repository, path,
and main predecessor equal this wrapper. The freshly fetched main predecessor
therefore proves that this packet path has never appeared anywhere on its
complete all-parent history. `freeze_anchor` is the complete create-only object
above and equals this series, round, repository, and output. Output is a one-
parent direct child that
preserves every predecessor byte and adds exactly the complete packet-artifact
set. At r002 `task_predecessor_oid` is null. At r003 through r005 it equals
the immediately preceding disposition publication's output commit, is an
ancestor of the main predecessor, and names `NEXT_DESIGN_ROUND` for this
exact successor. The remote observation proves output commit exact at main
and at the permanent freeze anchor before review. A routine merge cannot hide
the earlier path-present output because every parent edge is walked. A later
accepted-writer delete cannot occur. A same-round replacement, second
counter, reviewer swap, changed artifact, or reused packet path therefore
cannot create a second valid wrapper.

`pontius-stage0b-review-input-snapshot-v1` has exactly:

| Key | Type |
| --- | --- |
| `breaker_calibration_artifact` | `artifact_identity` |
| `breaker_calibration_byte_count` | `positive_count` |
| `breaker_calibration_sha256` | `sha256` |
| `candidate_manifest_sha256` | `sha256` |
| `candidate_oid` | `oid` |
| `candidate_ref` | full review ref |
| `contract_registry_artifact` | `artifact_identity` |
| `contract_registry_byte_count` | `positive_count` |
| `contract_registry_sha256` | `sha256` |
| `counter_artifact` | `artifact_identity` |
| `counter_byte_count` | `positive_count` |
| `counter_sha256` | `sha256` |
| `coverage_artifact` | `artifact_identity` |
| `handoff_commit_oid` | `oid` |
| `handoff_packet_path` | exact `<task>/<round>` repository path |
| `handoff_ref` | exact `refs/heads/main` |
| `handoff_repository_id` | exact `PONTIUS_HANDOFFS` |
| `interface_inventory_artifact` | `artifact_identity` |
| `interface_inventory_byte_count` | `positive_count` |
| `interface_inventory_sha256` | `sha256` |
| `review_scope_artifact` | `artifact_identity` |
| `review_scope_byte_count` | `positive_count` |
| `review_scope_sha256` | `sha256` |
| `reviewer_path_bindings` | exactly two reviewer-path-binding rows |
| `round_freeze_publication` | complete round-freeze-publication object |
| `round_freeze_publication_byte_count` | `positive_count` |
| `round_freeze_publication_sha256` | `sha256` |
| `round` | `round` |
| `round_ordinal` | `stage0b_round_ordinal` |
| `schema` | exact schema literal |
| `series_id` | `stage0b_series_id` |
| `stage0b_activation_publication` | complete activation-publication wrapper |
| `stage0b_activation_publication_byte_count` | `positive_count` |
| `stage0b_activation_publication_sha256` | `sha256` |
| `terminal_rule_projection_artifact` | `artifact_identity` |
| `terminal_rule_projection_byte_count` | `positive_count` |
| `terminal_rule_projection_sha256` | `sha256` |
| `terminal_rule_projection_status` | `EXACT` or `DIFFERENT` |
| `task` | `task` |

The coordinator constructs this value only after the H packet commit has
frozen. It is a canonical restatement of the handoff, never a replacement for
the authoritative source-candidate ref, commit, and manifest SHA-256. Every
packet artifact resolves at `handoff_packet_path` in the named
`PONTIUS_HANDOFFS` commit. `refs/heads/main` resolves to that commit when the
review request is issued; later routine packet commits do not change the bound
commit. Its `candidate.json` and `manifest.sha256` bind the same P candidate
tuple and manifest digest; there is no second H-packet manifest authority.
Snapshot artifacts and values equal the counter byte-for-byte. Because the
snapshot is downstream of the H commit, neither the counter nor the H commit
contains it. Each review receipt embeds the same complete value byte-for-byte.
The snapshot's activation object, count, and digest equal the counter and
round-freeze publication byte-for-byte. Each receipt repeats that triple.
The complete round-freeze publication reproduces its adjacent count and digest;
its output commit equals `handoff_commit_oid`, and all snapshot artifacts,
candidate fields, packet path, round, series, and reviewer bindings equal that
single create-only wrapper. This selected Stage 0b route narrows the generic
packet rule to exactly those two frozen panel members. A third review is
non-authoritative and cannot enter a result or disposition.
Task equals the counter, every nested coordinator object, the round-freeze
publication, handoff packet path, and both future review receipts and results.

`pontius-stage0b-interface-discrepancy-v1` has exactly
`affected_interface_ids`, `affected_paths`, `classification_statement`,
`coordinator_semantic_row_sha256`, `discrepancy_kind`,
`independent_row_sha256`, and `reason`. Kind is
`OMITTED_COORDINATOR_ROW`, `EXTRA_COORDINATOR_ROW`, `ROW_MISMATCH`, or
`CLASSIFICATION_DISPUTE`. The path and interface arrays are sorted and at
least one is nonempty.

`OMITTED_COORDINATOR_ROW` has a nonnull independent-row digest and null
coordinator and statement fields. `EXTRA_COORDINATOR_ROW` has a nonnull
coordinator-semantic-row digest and null independent and statement fields.
`ROW_MISMATCH` has two unequal nonnull row digests and a null statement.
Each digest hashes the complete canonical semantic-row bytes above.
`CLASSIFICATION_DISPUTE` has null row digests and one complete statement with
exactly `coordinator_classification`, `coordinator_count`,
`independent_classification`, `independent_count`, and
`semantic_inventory_sha256`. Its values are independently recomputed from the
same semantic row population and at least one paired scalar differs.

Rows pair first by the unique `(kind, stable_name)` key. A one-sided
independent key is exactly `OMITTED_COORDINATOR_ROW`; a one-sided coordinator
key is exactly `EXTRA_COORDINATOR_ROW`; a paired key with unequal clause or
path projections is exactly one `ROW_MISMATCH`. `CLASSIFICATION_DISPUTE` is
permitted only after all row keys and projections pair. Discrepancies sort by
kind, pairing key, independent digest with null first, then coordinator digest
with null first, and are unique. The semantic-inventory digest hashes the
concatenated canonical semantic-row bytes in pairing-key order.

`pontius-stage0b-finding-v1` has exactly `affected_clause_keys`,
`affected_interface_ids`, `affected_paths`, `category`, `contract_id`,
`finding_id`, `origin`, `report_finding_ordinal`, `residual_ordinal`,
`reviewer_ordinal`, `severity`, and `source_evidence_sha256`. Arrays are
sorted and unique; at least one affected-interface or affected-path value is
present. Category is `DEFECT`, `DESIGN`, or `WIRE`. Origin is
`REVIEW` or `COUNTER_AMBIGUITY`. Review origin permits only `DEFECT` or
`DESIGN`. `DEFECT` occurs exactly with severity `CRITICAL` or `IMPORTANT`;
`DESIGN` occurs exactly with severity `DESIGN`. Review origin requires
reviewer ordinal one or two, a sequential positive report-finding ordinal, and
the source digest of the exact length-framed report finding body. Its ID is the
exact ASCII rendering
`R<round-ordinal:03>_REVIEW_<reviewer-ordinal:02>_FINDING_<report-ordinal:03>`.

Counter ambiguity occurs only with category `WIRE`, severity
`WIRE_AMBIGUITY`, contract ID exact
`STAGE0B.WIRE.COUNTER_CLASSIFICATION`, null reviewer and report ordinals, and
ID `R<round-ordinal:03>_COUNTER_AMBIGUITY`. Its source digest hashes the
separate complete ambiguity-evidence object below. These renderings make IDs
globally unique without producer choice.

For every REVIEW finding, `affected_clause_keys` is nonempty, every key occurs
in an affected interface row, and every key has one identical registered
contract-ID prefix. `contract_id` is mechanically that prefix; every affected
interface's current inventory row has that ID, and every affected path is in
that registry row's source paths. A report spanning prefixes is normalized
into one finding per contract. The counter-ambiguity finding has an empty
clause-key array and
selects the reserved registry row. `residual_ordinal` equals one plus the
number of distinct predecessor rounds whose disposition contains a BLOCKING
finding with the same contract ID and whose immediately following counter has
the exact blocker-resolution row proving the attempted closure. A prior
NONBLOCKING design mention does not count. Two reviewers in one round therefore
share one recurrence ordinal; r001 contributes zero. A contract rename,
alternate valid label, cross-contract unsplit finding, duplicate-review count,
omitted predecessor, or supplied ordinal that differs from this equation
refuses.

`pontius-stage0b-counter-ambiguity-evidence-v1` has exactly
`affected_interface_ids`, `affected_paths`, `counter_sha256`,
`discrepancy_row_sha256s`, `input_snapshot`, `proposal_ambiguity_reason`,
`reason`, and `schema`. The affected arrays and reason equal the disposition's
adjudicated ambiguity. Discrepancy digests are the sorted unique complete set
from both review receipts. Proposal reason equals the counter proposal and may
be null. This object contains no digest of itself. Its externally computed
SHA-256 becomes the derived `COUNTER_AMBIGUITY` finding's
`source_evidence_sha256`, so no finding row hashes itself.

`pontius-stage0b-cold-input-order-v1` has exactly
`calibration_opened_after_inventory`, `contract_registry_opened_after_inventory`,
`coordinator_inventory_opened_after_inventory`,
`counter_opened_after_inventory`, `coverage_opened_after_inventory`,
`peer_review_opened_before_report_freeze`,
`review_scope_opened_after_inventory`, and
`terminal_projection_opened_after_inventory`. Every
`*_opened_after_inventory` value is exact true; the peer-review field is exact
false.
The reviewer freezes and hashes its complete independent inventory before
opening any named coordinator object or coverage. The inventory artifact's
creation and identity precede those opens in the retained review transcript.

`pontius-stage0b-review-receipt-v1` has exactly
`cold_input_order_attestation`, `counter_comparison`, `defect_verdict`,
`design_verdict`, `discrepancies`, `findings`, `independent_inventory`,
`independent_inventory_artifact`, `independent_inventory_byte_count`,
`independent_inventory_sha256`, `input_snapshot`, `report`, `reviewer_id`,
`reviewer_ordinal`, `reviewer_path_slug`, `schema`, `stage0b_activation_publication`,
`stage0b_activation_publication_byte_count`,
`stage0b_activation_publication_sha256`, `task`, and `verdict_date`.
Findings are the complete report-order array of normalized
`pontius-stage0b-finding-v1` rows for every Critical, Important, and design
finding. `independent_inventory` is the complete
`pontius-stage0b-independent-interface-inventory-v1` object. It parses from its
artifact and reproduces its count and digest before the cold-input-order
attestation's forbidden opens.
The reviewer and ordinal equal the counter slot and are distinct across the two
receipts. Reviewer ID, ordinal, and slug equal the frozen path binding. The
receipt's activation triple equals its input snapshot, counter, and round-freeze
publication byte-for-byte. The activated series equals every nested series. The
report begins with this exact ordered prefix and one blank line:

```text
Reviewer ID: <reviewer_id>
Candidate commit: <candidate_oid>
Manifest SHA-256: <candidate_manifest_sha256>
Handoff commit: <handoff_commit_oid>
Stage 0b counter SHA-256: <counter_sha256>
Independent inventory SHA-256: <independent_inventory_sha256>
Cold input order: INVENTORY_FROZEN_FIRST
Defect verdict: <defect_verdict>
Design verdict: <design_verdict>

```

The prefix is followed by zero or more finding blocks in ascending, gap-free
report-finding ordinal. Each block is exactly:

`Finding: <report_finding_ordinal>`
`Severity: <severity>`
`Category: <category>`
`Contract: <contract_id>`
`Affected clauses: <canonical compact JSON string array>`
`Affected interfaces: <canonical compact JSON string array>`
`Affected paths: <canonical compact JSON string array>`
`Body byte count: <canonical positive decimal>`
`Body SHA-256: <lowercase sha256>`
`Body:`
`<exact body bytes><LF>End finding<LF><LF>`

The body is positive UTF-8 with LF endings and no NUL. Its declared byte count
length-frames it, and its SHA-256 equals `source_evidence_sha256`. Every other
block scalar reproduces the normalized finding; ID and reviewer fields derive
from context and ordinals. After the last block, optional nonnormative text may
occur only under one exact `Notes:<LF>` delimiter and may not contain a line
beginning `Finding: `, `Severity: `, or `Design verdict: `. The parser
reproduces every normalized finding and no other Critical, Important, or design
finding. Defect verdict CLEAN occurs exactly with zero Critical or Important
rows; NOT CLEAN occurs exactly with at least one. STRAINED or WRONG SHAPE
occurs only with at least one DESIGN finding by that reviewer; SOUND occurs
exactly with zero DESIGN findings. The
report artifact's raw bytes reproduce its identity. A report for another
candidate, manifest, H commit, counter, reviewer, slug, or ordinal refuses.

`counter_comparison` is `MATCH` exactly when `discrepancies` is empty, there
is a unique bijection between independent rows and coordinator semantic
projections, and the reviewer recomputes the proposal classification and counts
exactly. It is `DISPUTED` exactly when the nonempty discrepancy array is the
complete semantic difference or label-to-semantic inconsistency. Coordinator
labels never enter the reviewer's pre-open inventory.
Reviewer disagreement is therefore immutable review output, never an in-place
counter edit.

`pontius-stage0b-review-ledger-append-v1` has exactly `appended_line`,
`appended_line_sha256`, `current_progress`, `previous_progress`,
`reviewer_id`, `reviewer_ordinal`, `schema`, and `task`. Both progress values are
`artifact_identity` objects at exact path `<task>/progress.md`. The appended
line is one nonempty LF-terminated UTF-8 line with no other LF. It contains,
in exact field order, round, reviewer ID, candidate OID, candidate manifest
SHA-256, defect verdict, and design verdict. Its SHA-256 equals the adjacent
digest, and current-progress bytes equal previous-progress bytes followed by
that line with no normalization. Reviewer ID and ordinal equal the receipt.
The issuer is therefore the verdict's reviewer even when the mechanical
publication step occurs later.

`pontius-stage0b-remote-ref-query-v1` has exactly `argv`, `exit_code`,
`remote_url`, `stderr_hex`, `stdout_byte_count`, `stdout_hex`, `stdout_sha256`,
and `transport`. Transport is `HTTPS`;
remote URL is exact
`https://github.com/point3434-creator/Pontius-handoffs.git`; exit is integer
zero or two; and stderr hex is empty. Argv is the exact absolute `PONTIUS_GIT`
`ls-remote --exit-code` query for that URL and one full ref. Stdout is exactly
the hex encoding of `<oid><TAB><ref><LF>` with no other bytes for exit zero,
or empty for exit two. Byte count and SHA-256 cover those exact decoded bytes.
This complete inline object is the
raw observation preimage; it is not an unresolved artifact path.

`pontius-stage0b-publication-observation-core-v1` has exactly `evidence`,
`observed_oid`, `ref`, `repository_id`, `schema`, and `state`. `evidence` is
the complete remote-ref-query object and `observed_oid` is an `oid` or null.
Repository ID is exact `PONTIUS_HANDOFFS`; ref is one full frozen H ref; and
state is `EXACT` or `ABSENT`. Exact requires exit zero, nonnull OID, and the
one-row stdout. Absent requires exit two, null OID, and empty stdout. The strict
reader parses decoded stdout and reproduces repository, ref, observed OID, and
state. Existing main-publication uses require exact `refs/heads/main`.

`pontius-stage0b-publication-observation-v1` has exactly `observation`,
`observation_byte_count`, `observation_sha256`, `retention_authority_sha256`,
`retention_receipt`, and `schema`. Observation is the complete self-free core
above and reproduces the adjacent positive count and digest. Retention receipt
is the complete external-retention receipt defined below and names those exact
core bytes. Its authority digest equals the receipt and the complete Stage 0b
activation authority. This wrapper is retained outside the queried Git commit;
it cannot be its own record and needs no successor publication.

`pontius-stage0b-freeze-ref-observation-v1` has exactly `anchor`, `main`,
`schema`, and `state`. Both members are complete publication observations from
separate exact queries, ordered main then anchor in the canonical object. State
is `PRE_PUBLICATION` exactly when the main core is exact at the predecessor and
the anchor core is absent. It is `POST_PUBLICATION` exactly when both cores are
exact at the same output commit. Core repository IDs equal and the anchor core
ref is the selected permanent round anchor. Each core has its own complete
external-retention receipt. No multi-ref output or absence inferred from an
omitted row is valid.

`pontius-stage0b-review-result-v1` has exactly `ledger_append`,
`main_predecessor_oid`, `output_commit_oid`, `output_ref`, `packet_path`,
`publication_observation`, `receipt`,
`receipt_artifact`, `receipt_byte_count`, `receipt_sha256`, and
`repository_id`, `schema`, `stage0b_activation_publication`,
`stage0b_activation_publication_byte_count`,
`stage0b_activation_publication_sha256`, `task`, and `task_predecessor_oid`.
Repository, ref, and packet path
are exact
`PONTIUS_HANDOFFS`, `refs/heads/main`, and `<task>/<round>`. The receipt
artifact has exact path
`<task>/<round>/checks/review-<NN>-<slug>-receipt.json`; its nested report
artifact has exact path `<task>/<round>/reviews/review-<NN>-<slug>.md`; and
its independent
inventory artifact has exact path
`<task>/<round>/checks/review-<NN>-<slug>-interface-inventory.json`. `NN`
is the two-digit reviewer ordinal and `slug` is its frozen path slug. All
three resolve inside `output_commit_oid`.

The output commit is a one-parent direct child of the freshly fetched
`main_predecessor_oid`. The bound `task_predecessor_oid` is an ancestor of
that main predecessor. For ordinal one the task predecessor equals the input
handoff commit; for ordinal two it equals ordinal one's output commit. The tree
preserves every main-predecessor entry byte-for-byte except
`<task>/progress.md`, replaces that file only with the exact ledger-append
result, and adds exactly the reviewer's three new artifacts. All packet-subtree
bytes from the task predecessor remain identical. Unrelated task commits may
intervene on main; a conflicting same-task change refuses and retries from a
newly fetched main rather than overwriting it. No prior packet, finding, or
review artifact disappears or changes.
Publication-observation core repository and ref equal the result, and its
observed OID equals `output_commit_oid`. The receipt bytes reproduce the adjacent
identity. The publication observation proves the commit remotely reachable
before disposition. Two result rows occur in reviewer-ordinal order and bind
one identical input snapshot. Each report was frozen before its reviewer
opened any peer review. The source candidate's `manifest.sha256` is not
misclassified as a per-review output manifest.
Each result repeats the receipt's complete activation triple byte-for-byte.
Its task equals the receipt, input snapshot, counter, activation, packet path,
and ledger path. Equal candidate bytes from another task cannot join.

`pontius-stage0b-design-override-v1` has exactly `decision`,
`finding_ids`, `justification`, `justification_byte_count`,
`justification_sha256`, `reviewer_ordinals`, and `triggers`. Decision is
`BUILD_IMMEDIATELY` or `NEXT_DESIGN_ROUND`. `justification` is an
`artifact_identity`; its byte count is positive and its SHA-256 equals both the
artifact and retained raw bytes. `finding_ids` is a sorted unique nonempty
finding-ID array. `reviewer_ordinals` is a sorted unique subset of one and two.
It is empty exactly when every trigger is a nonreview WIRE residual. Triggers
are a sorted unique nonempty array of
`WRONG_SHAPE_REVIEW` or `SECOND_RESIDUAL` rows, ordered by trigger, contract,
then reviewer ordinal. A trigger row has exactly `contract_id`,
`reviewer_ordinal`, and `trigger`. Contract ID is null only for
`WRONG_SHAPE_REVIEW`; reviewer ordinal is null only for `SECOND_RESIDUAL`.
Finding IDs are the exact union of the current finding rows that establish the
triggers; reviewer ordinals are the sorted union of their nonnull ordinals.
Every non-SOUND verdict supplies at least one DESIGN row, so a WRONG SHAPE
trigger always has a finding ID. The trigger, finding, and reviewer populations
are the exact derivation from the two receipts and predecessor chain. The
justification names those same rows and explains why continuing is safer than
redesign at this point.

A `NEXT_DESIGN_ROUND` override is valid only at r002, r003, or r004, and
every triggering DESIGN finding it relies on is adjudicated BLOCKING. It
selects the immediate successor and retains a nonempty complete blocker set.
A `BUILD_IMMEDIATELY` override is valid only when all triggering DESIGN
findings are NONBLOCKING and, after accepting the override, the ordinary
build-eligibility equation below is true. A residual DEFECT or WIRE blocker
therefore cannot be overridden into BUILD. `NEXT_DESIGN_ROUND` at r005, BUILD
with any blocker, or an override whose selected decision differs from the
disposition refuses.

`pontius-stage0b-finding-adjudication-v1` has exactly `adoption_rationale`,
`adoption_rationale_byte_count`, `adoption_rationale_sha256`, `finding`,
`finding_sha256`, and `outcome`. Outcome is `BLOCKING` or `NONBLOCKING`.
The finding digest hashes the complete canonical finding row. Every receipt
finding occurs exactly once across the disposition array, as does the one
derived counter-ambiguity finding when present. Rows sort by finding ID.
DEFECT and WIRE findings are always BLOCKING. DESIGN findings are BLOCKING only
when the coordinator adopts them and otherwise are NONBLOCKING. The rationale
fields are a complete artifact identity, positive count, and equal digest only
for a BLOCKING design adoption; all three are null otherwise. No Critical or
Important finding may be dismissed as “non-surviving.”

`pontius-stage0b-disposition-v1` has exactly:

| Key | Type |
| --- | --- |
| `blocking_findings` | sorted unique blocking-finding array |
| `candidate_manifest_sha256` | `sha256` |
| `candidate_oid` | `oid` |
| `candidate_ref` | full review ref |
| `coordinator_id` | `actor_id` |
| `counter_artifact` | `artifact_identity` |
| `counter_byte_count` | `positive_count` |
| `counter_sha256` | `sha256` |
| `adjudicated_ambiguity_affected_interface_ids` | sorted unique interface-ID array |
| `adjudicated_ambiguity_affected_paths` | sorted unique repository-path array |
| `adjudicated_ambiguity_reason` | nonempty LF-free UTF-8 string or `null` |
| `adjudicated_classification` | classification literal defined below |
| `counter_ambiguity_evidence` | complete ambiguity-evidence object or `null` |
| `decision` | `BUILD_IMMEDIATELY`, `NEXT_DESIGN_ROUND`, or `PARKED` |
| `design_override` | complete `pontius-stage0b-design-override-v1` object or `null` |
| `design_breaker_clear` | Boolean |
| `build_eligible` | Boolean |
| `defect_set_clean` | Boolean |
| `fresh_preregistration_required` | Boolean |
| `finding_adjudications` | complete finding-adjudication array |
| `next_round` | `round` or `null` |
| `old_panel_discard_required` | Boolean |
| `parking_category` | exact `parked - gate defect` or `null` |
| `parking_reason` | parking-reason literal or `null` |
| `review_results` | exactly two `pontius-stage0b-review-result-v1` rows |
| `review_set_clean` | Boolean |
| `round` | `round` |
| `schema` | exact schema literal |
| `series_id` | `stage0b_series_id` |
| `stage0b_activation_publication` | complete activation-publication wrapper |
| `stage0b_activation_publication_byte_count` | `positive_count` |
| `stage0b_activation_publication_sha256` | `sha256` |
| `task` | `task` |

Parking reason is `ANALYZER_PATTERN_RECURRENCE`,
`AMBIGUOUS_WIRE_STATE`, `NONCLEAN_TERMINAL_R005`,
`POST_FREEZE_CALIBRATION_CHANGE`, or `REDESIGN_DEFAULT_SELECTED`. The external
coordinator issues the disposition only after both review results freeze.
The counter artifact is exact
`<task>/<round>/stage0b-counter.json` in both input snapshots' bound handoff
commit. Its retained bytes reproduce the named count and digest. Disposition
candidate tuple, round, and series equal that counter and both snapshots.
Task equals the counter, both review results and receipts, activation, and
every `<task>` path component.
Its activation triple equals the counter, both receipts, both results, and both
round-freeze publications byte-for-byte.
The two ordered results' receipts equal the counter's reviewer IDs, ordinals,
and path bindings. Classification, findings, overrides, and decision derive
only from this joined population; cross-counter or cross-round substitution
refuses even for a terminal PARK.
`finding_adjudications` is a bijection over the two receipts' finding arrays
plus the derived ambiguity finding, if any. `blocking_findings` is exactly the
complete finding population whose outcome is BLOCKING: every Critical or
Important row, every adopted design row, and any adjudicated ambiguity.
No finding may be invented, omitted, or represented by an untyped ID.
`defect_set_clean` is true exactly when both defect verdicts are CLEAN.
`review_set_clean` is true exactly when `defect_set_clean` is true and no
DESIGN finding adjudication is BLOCKING.

`adjudicated_classification` is `AMBIGUOUS` exactly when the proposal is
ambiguous or either review comparison is `DISPUTED`. Its reason and affected
arrays are the canonical union of the proposal and discrepancy rows; the reason
is nonnull and at least one affected array is nonempty. Otherwise its reason is
null, both arrays are empty, both comparisons are `MATCH`, and classification
equals the proposal. Any reviewer dispute thus prevents BUILD even when both
defect verdicts are CLEAN.

`counter_ambiguity_evidence` is nonnull exactly for an ambiguous adjudication.
Its canonical bytes derive exactly one `COUNTER_AMBIGUITY` blocker. It is null
otherwise. The derived row's paths, interfaces, contract, recurrence ordinal,
category, and evidence digest are fixed by that object and predecessor chain.

The design-trigger population contains every WRONG SHAPE verdict and every
finding whose `residual_ordinal` is at least two. With no trigger,
`design_override` is null and `design_breaker_clear` is true. With a trigger,
BUILD or NEXT requires one complete valid override whose decision equals the
disposition; then `design_breaker_clear` is true. If the coordinator follows
the redesign default, decision is PARKED, override is null,
`design_breaker_clear` is false, and parking reason is
`REDESIGN_DEFAULT_SELECTED`. Every other PARK has null override. A missing,
extra, mismatched, opaque, or self-issued justification refuses.

`build_eligible` is true exactly when the adjudicated classification is
nonambiguous, `review_set_clean` and `design_breaker_clear` are true, and
`blocking_findings` is empty. This is the effective clean state used by the
early-exit rule; bare CLEAN defect verdicts do not bypass an adopted design
blocker or the independent design/residual breaker.

Decision precedence is total and fail-closed:

1. An adjudicated reason `POST_FREEZE_CALIBRATION_CHANGE` selects `PARKED`
   with that reason at every later ordinal.
2. Otherwise a design trigger without a complete valid override selects
   `PARKED` with reason `REDESIGN_DEFAULT_SELECTED` at every ordinal.
3. Otherwise a valid `NEXT_DESIGN_ROUND` override selects that decision and
   the immediate successor at r002, r003, or r004.
4. Otherwise an ambiguous adjudication at r005 selects `PARKED` with reason
   `AMBIGUOUS_WIRE_STATE`.
5. Otherwise r005 with false `review_set_clean` and positive round interface-
   change count selects `PARKED` with reason
   `ANALYZER_PATTERN_RECURRENCE`.
6. Otherwise r005 with false `review_set_clean` selects `PARKED` with reason
   `NONCLEAN_TERMINAL_R005`.
7. Otherwise `build_eligible` selects `BUILD_IMMEDIATELY` regardless of
   interface-change count.
8. The remaining r002, r003, or r004 case selects `NEXT_DESIGN_ROUND` with
   exactly the next ordinal and a nonempty complete blocker array, including
   any counter ambiguity.

`BUILD_IMMEDIATELY` has null parking fields and next round, both gate Booleans
false, closes Stage 0b, and is the only disposition an implementation brief or
candidate may bind. `NEXT_DESIGN_ROUND` has null parking fields, next round
r003, r004, or r005, both gate Booleans false, and authorizes only successor
edits mapped to its exact blockers. `PARKED` has null next round, category exact
`parked - gate defect`, both gate Booleans true, and authorizes no candidate,
review, partial tool, or r006. ADR-0482 permits at most one fresh
preregistration under a redesigned gate with the old panel discarded. That is
a new lifecycle, never quiet continuation, relabeling, or counter reset.

`pontius-stage0b-program-ledger-append-v1` has exactly `appended_line`,
`appended_line_sha256`, `coordinator_id`, `current_progress`,
`previous_progress`, `round`, `schema`, `stage0b_decision`, and `task`. Progress
values are `artifact_identity` objects at exact root path `progress.md`.
The appended line is one nonempty LF-terminated UTF-8 line with no other LF and
contains, in exact order, round, candidate OID, candidate manifest SHA-256,
coordinator ID, Stage 0b decision, and parking reason or `NONE`. Its SHA-256
equals the adjacent digest. Current bytes equal previous bytes followed by that
line with no normalization. The coordinator and decision equal the disposition.

`pontius-stage0b-disposition-publication-v1` has exactly `disposition`,
`disposition_artifact`, `disposition_byte_count`,
`disposition_report_artifact`, `disposition_report_byte_count`,
`disposition_report_sha256`, `disposition_sha256`,
`main_predecessor_oid`, `output_commit_oid`, `output_ref`, `packet_path`,
`program_ledger_append`, `publication_observation`, `repository_id`, `schema`, and
`stage0b_activation_publication`, `stage0b_activation_publication_byte_count`,
`stage0b_activation_publication_sha256`, `task`, and `task_predecessor_oid`. Repository, ref,
packet path, and disposition-artifact
path are exact `PONTIUS_HANDOFFS`, `refs/heads/main`, `<task>/<round>`,
and `<task>/<round>/stage0b-disposition.json`. The artifact parses as the
complete nested disposition and reproduces its count and digest.
The publication's activation triple equals the nested disposition and every
joined review result byte-for-byte.
Task equals the disposition, program-ledger append, packet path, activation,
and every joined review carrier.

The report artifact path is exact `<task>/<round>/disposition.md`. Its bytes
are the exact header `Stage 0b disposition`, candidate tuple, counter digest,
decision, parking fields, and disposition digest, followed by one canonical
compact JSON finding-adjudication line in disposition order. It reproduces its
count and digest and contains every per-finding accept/reject outcome with no
extra finding.

Task predecessor equals review ordinal two's output commit and is an ancestor
of the freshly fetched main predecessor. The output is a one-parent direct
child of that main predecessor. Its tree preserves every predecessor entry
byte-for-byte except root `progress.md`, replaces that file only with the
exact program-ledger-append result, and adds exactly the previously absent
disposition JSON and Markdown report artifacts.
Unrelated-task commits may intervene; a same-task conflict refuses and retries.
The observation core reproduces repository, ref, and output OID; its complete
retained wrapper proves remote main exact before any build authority is issued.

`pontius-freeze-tools-implementation-convergence-policy-v1` has exactly
`budgets`, `generated_output_rule`, `line_metric`, `schema`, and
`spike_policy`. `line_metric` is exact `UTF8_LF_NONBLANK_V1`: strict UTF-8,
no BOM or CR, exactly one final LF, and split before each LF; a line counts if
it contains at least one byte other than ASCII SP or HT. Comments count.

Budget rows have exactly `budget_class`, `limit_nonblank_lines`, and `scope`.
The exact ordered population is:

| Budget class | Scope | Limit |
| --- | --- | ---: |
| `NATIVE_BOUNDARY` | native bootstrap + WINDOWS_OWNER + askpass adapter | 1800 |
| `PURE_KERNEL` | shared authority-free pure kernel | 1200 |
| `BUILDER_POLICY_PLANNER` | builder policy and planner | 900 |
| `PUBLISHER_POLICY_PLANNER` | publisher policy and planner | 900 |
| `INTEGRATOR_POLICY_PLANNER` | integrator policy and planner | 900 |
| `FOCUSED_TESTS` | freeze-tools focused implementation tests | 4500 |

`pontius-implementation-path-budget-map-v1` has exactly `rows` and `schema`.
A row has exactly `budget_class`, `generated`, and `path`. Paths are canonical
repository paths, ASCII sorted and unique; budget class selects exactly one
policy row. This is the complete planned implementation source, test, and
generated-output population. The implementation brief freezes the map before
candidate work. Moving bytes between files or classes cannot change the
classification. `generated_output_rule` is exact
`SEPARATE_ONLY_WITH_BOUND_GENERATOR_AND_INDEPENDENT_READER`: a generated path is
excluded from manual class totals only when its row binds a reviewed generator
source and a distinct independently reviewed reader source; it remains counted
and reported separately. Generated-looking, fixture, table, or schema bytes
without both bindings count in their ordinary class.

`spike_policy` has exactly `combined_gate`, `max_lifecycles`, `mechanisms`,
`park_category`, `stop_on_first_pass`, and `third_lifecycle_forbidden`.
Combined gate and stop are true, max is two, third forbidden is true, park is
ADR-0482 `parked - gate defect`, and mechanisms are exactly, in order,
`NATIVE_PRE_DLL_APPCONTAINER`, `BUILDER_CAPABILITY_DENIAL`, and
`ONE_SHOT_HTTPS_ASKPASS`. One lifecycle runs all three RED public-boundary
tests. The first lifecycle passes only if all three pass and then stops. A first
failure permits exactly one corrected lifecycle; a second failure parks and
requires a fresh preregistration. This is one combined two-attempt gate, never
two attempts per mechanism.

`pontius-implementation-required-test-spec-v1` has exactly `argv`, `kind`,
`mechanism_id`, `ordinal`, and `selector`. Kind is `SPIKE_MECHANISM` or
`FOCUSED_SUITE`. Ordinals are positive and contiguous. `argv` is a nonempty
array of exact argument strings beginning with the held absolute executable;
it contains no shell, response file, environment expansion, relative executable,
or omitted default. A spike row has one nonnull mechanism ID and selector equal
to that ID. The focused-suite row has null mechanism ID and selector exact
`FREEZE_TOOLS_FOCUSED_SUITE`.

`pontius-freeze-tools-implementation-plan-v1` has exactly
`bootstrap_design_authorization_publication_sha256`, `candidate_base_oid`,
`path_budget_map`, `path_budget_map_artifact`,
`path_budget_map_byte_count`, `path_budget_map_sha256`, `policy_sha256`,
`required_tests`, `required_tests_sha256`, `round`, `schema`, and `task`. The
authorization digest selects the complete
published bootstrap wrapper; policy digest equals its complete convergence
policy. The map artifact is frozen under adopted packet rule 6 before candidate
work. Map canonical bytes reproduce the adjacent positive
count and digest. Required tests are exactly four complete spec rows: the three
spike mechanisms in spike-policy order followed by the focused-suite row. Their
argv arrays are the exact commands later executed. `required_tests_sha256`
hashes the concatenation of the four strict canonical row encodings, each with
its final LF. Every later implementation candidate,
packet, review, convergence receipt, selector, controller authorization,
bootstrap evidence, and acceptance object binds this complete plan, its
artifact, byte count, and digest.

`pontius-pre-dll-load-attempt-v1` has exactly `attempted_path`,
`bootstrap_process_binding_sha256`, `loader_entry_reached`, `result`, `schema`,
and `win32_error_hex`. Result is exact `BLOCKED_BEFORE_LOAD`; loader entry is
false; the attempted path is the frozen first forbidden DLL path; and the
process binding names the actual suspended bootstrap under test.

`pontius-native-pre-dll-appcontainer-boundary-evidence-v1` has exactly
`appcontainer_observation`, `bootstrap_process_completion`,
`pre_dll_load_attempt`, `runtime_lock_reached`, `schema`, and
`source_projection_set_sha256`. The observation is a complete
`pontius-appcontainer-live-observation-v1`; the attempt is the complete object
above; runtime lock is false; and process completion proves the expected typed
refusal after the pre-DLL boundary was exercised. A post-load audit, helper
double, unattempted path, or Boolean denial cannot satisfy this object.

`pontius-builder-capability-denial-boundary-evidence-v1` has exactly
`attempted_operation`, `builder_process_completion`, `capability_table_sha256`,
`denial_fact`, `repository_open_attempted`, `schema`, and
`source_projection_set_sha256`. Attempted operation is one publisher- or
integrator-only operation selected by the required test. `denial_fact` is the
complete `pontius-capability-denial-fact-v1` object at the public operation
entry point;
repository-open-attempted is false and completion proves the expected refusal.
A policy-table unit test, mocked repository, or later access error cannot
satisfy this object.

`pontius-capability-denial-fact-v1` has exactly `attempted_operation`,
`capability_table_sha256`, `denied_role`, `dispatch_sha256`, `reason`, `schema`,
and `source_projection_set_sha256`. Reason is exact
`OPERATION_OUTSIDE_ROLE_CAPABILITY`; every identity equals the actual builder
dispatch and projection. It is constructed before any repository, credential,
Git, network, or mutable-state open.

`pontius-one-shot-https-askpass-boundary-evidence-v1` has exactly
`askpass_attempt`, `broker_session_result`, `credential_consumption`,
`post_remote_observation`, `schema`, `server_secret_lifecycle`, and
`transport_process_completion`. Each noncompletion field is the complete typed
object from the real HTTPS askpass, broker, remote-query, and authenticated
server-secret contracts. They bind one session and show exactly one accepted
password prompt, one complete credential transfer, one consumed server secret,
and the expected remote ref result. A prompt-only match, read-only query, local
transport, helper double, or Boolean success cannot satisfy this object.

`pontius-implementation-convergence-test-result-v1` has exactly `argv`,
`candidate_manifest_sha256`, `candidate_oid`, `environment_sha256`,
`mechanism_id`, `observed_public_boundary`, `platform_projection_sha256`,
`process_completion`, `required_test_row_sha256`,
`runtime_projection_sha256`, `schema`, `selector`,
`source_projection_set_sha256`, `status`, and `tool_file_identity`. Mechanism
is one exact spike-policy value. Required-test digest selects that mechanism's
complete plan row; selector and argv equal it byte-for-byte. Environment,
platform, runtime, tool, candidate, manifest,
and source-projection identities equal the current reviewed implementation.
Process completion is complete, has exit zero exactly for PASS, and preserves
bounded stdout/stderr artifacts. Observed public boundary is the complete typed
object whose schema is, respectively,
`pontius-native-pre-dll-appcontainer-boundary-evidence-v1`,
`pontius-builder-capability-denial-boundary-evidence-v1`, or
`pontius-one-shot-https-askpass-boundary-evidence-v1`. It is never a Boolean or
expected label. Status is PASS exactly when that object proves the selected RED
contract; otherwise it is FAIL.

`pontius-implementation-convergence-test-evidence-v1` has exactly
`evidence_row`, `result`, `result_artifact`, `result_byte_count`,
`result_sha256`, and `schema`. Result is the complete self-free object above;
its canonical bytes equal the artifact bytes and reproduce the adjacent
positive count and digest. Evidence row is a downstream repository/ref/commit
anchor for that result artifact and repeats its complete artifact identity.
Neither result nor its artifact bytes contain this wrapper, evidence row, or
their identities.

`pontius-implementation-focused-suite-result-v1` has exactly `argv`,
`candidate_manifest_sha256`, `candidate_oid`, `environment_sha256`,
`process_completion`, `required_test_row_sha256`, `schema`, `selector`,
`source_projection_set_sha256`, `status`, and `tool_file_identity`. Its plan row
is kind `FOCUSED_SUITE`; argv and selector equal that row; process completion is
complete; and status is PASS exactly for exit zero and a parsed zero-failure,
zero-error focused-suite summary.

`pontius-implementation-focused-suite-evidence-v1` has exactly `evidence_row`,
`result`, `result_artifact`, `result_byte_count`, `result_sha256`, and `schema`.
Result is the complete self-free object above; canonical bytes reproduce the
artifact, count, and digest; and the downstream evidence row anchors that exact
artifact at a repository, ref, and commit.

`pontius-implementation-required-test-evidence-v1` has exactly
`focused_suite_evidence`, `kind`, `mechanism_evidence`, `ordinal`,
`required_test_row_sha256`, `schema`, `selector`, and `status`. A
`SPIKE_MECHANISM` row has complete nonnull convergence-test evidence and null
focused-suite evidence. A `FOCUSED_SUITE` row has complete nonnull focused-suite
evidence and null mechanism evidence. Every scalar equals the selected plan row
and nested result; status is exact PASS.

`pontius-implementation-convergence-class-total-v1` has exactly `budget_class`,
`limit_nonblank_lines`, `observed_nonblank_lines`, and `status`. Rows occur once
per policy budget in policy order. Limit equals policy; observed value is the
exact sum of nongenerated receipt path rows in that class; status is PASS exactly
when observed is at most limit.

`pontius-implementation-convergence-mechanism-v1` has exactly `evidence`,
`mechanism_id`, and `status`. Evidence is the complete typed test-evidence
wrapper above;
mechanism and status equal it. Rows occur in spike-policy order.
`pontius-implementation-convergence-attempt-v1` has exactly
`lifecycle_ordinal` and `mechanisms`; ordinal is one, or one then two, and the
mechanism population is complete.

`pontius-implementation-convergence-receipt-v1` has exactly
`candidate_manifest_sha256`, `candidate_oid`, `class_totals`,
`generated_total_nonblank_lines`,
`implementation_plan`, `implementation_plan_artifact`,
`implementation_plan_byte_count`, `implementation_plan_sha256`,
`path_budget_map`, `path_budget_map_byte_count`, `path_budget_map_sha256`,
`path_rows`,
`policy_sha256`, `required_tests_sha256`, `schema`,
`source_projection_set_sha256`, `spike_result`, and `status`. A path row
has exactly `blob_oid`, `budget_class`, `byte_count`, `generated`,
`generator_source_entry_sha256`, `independent_reader_source_entry_sha256`,
`map_row_sha256`, `mode`, `nonblank_line_count`, `path`, and `sha256`. Rows are
the complete manifest-bound implementation source/test/generated population in
ASCII path order and form a row-for-row bijection with the complete plan-bound
path map. `map_row_sha256` hashes the matching canonical map row. Generator and
reader digests are nonnull
exactly for generated rows and select distinct candidate source entries. Class
totals are the complete typed rows above. `generated_total_nonblank_lines` is
the exact sum across generated path rows. The plan artifact parses byte-for-byte
as the complete plan and reproduces its adjacent count/digest. Map, policy,
authorization, candidate base, selectors, and source projection equal the
reviewed implementation and every downstream carrier. Required-tests digest
equals the complete plan projection; the spike attempts select its first three
rows without reordering or substituting argv.

`spike_result` has exactly `attempts`, `policy_sha256`, `schema`, and `status`.
Attempts are the complete typed attempt rows above and have contiguous lifecycle
ordinal one or one then two. Spike status is `PASS` at
the first all-pass lifecycle or `PARK` after the second non-all-pass lifecycle.
Its policy digest equals the receipt, implementation plan, design authorization,
and design-authorization publication byte-for-byte.
Receipt status is `PASS` exactly when every budget passes and spike status is
`PASS`; otherwise it is `PARK` and cannot enter controller authority.

`pontius-stage0b-build-authority-v1` has exactly:

| Key | Type |
| --- | --- |
| `breaker_calibration` | complete calibration object |
| `breaker_calibration_artifact` | `artifact_identity` |
| `breaker_calibration_byte_count` | `positive_count` |
| `breaker_calibration_sha256` | `sha256` |
| `counter` | complete `pontius-stage0b-round-counter-v1` object |
| `counter_artifact` | `artifact_identity` |
| `counter_byte_count` | `positive_count` |
| `counter_sha256` | `sha256` |
| `disposition` | complete `pontius-stage0b-disposition-v1` object |
| `disposition_artifact` | `artifact_identity` |
| `disposition_byte_count` | `positive_count` |
| `disposition_publication` | complete disposition-publication object |
| `disposition_publication_byte_count` | `positive_count` |
| `disposition_publication_sha256` | `sha256` |
| `disposition_sha256` | `sha256` |
| `interface_inventory` | complete interface-inventory object |
| `interface_inventory_artifact` | `artifact_identity` |
| `interface_inventory_byte_count` | `positive_count` |
| `interface_inventory_sha256` | `sha256` |
| `implementation_convergence_policy` | complete convergence-policy object |
| `implementation_convergence_policy_artifact` | `artifact_identity` |
| `implementation_convergence_policy_byte_count` | `positive_count` |
| `implementation_convergence_policy_sha256` | `sha256` |
| `predecessor_chain` | complete predecessor-chain object |
| `schema` | exact schema literal |
| `stage0b_activation_publication` | complete activation-publication wrapper |
| `stage0b_activation_publication_byte_count` | `positive_count` |
| `stage0b_activation_publication_sha256` | `sha256` |
| `task` | `task` |

Each artifact's retained bytes parse byte-for-byte as its matching object and
reproduce the adjacent count and digest. Counter inventory, calibration, and
chain equal the complete copies. The disposition's counter identity, candidate,
series, round, review results, and coordinator agree. The build authority's
activation triple equals its counter, disposition, disposition publication,
and all joined round/review carriers byte-for-byte. Its decision is exact
`BUILD_IMMEDIATELY` and its adjudicated classification is nonambiguous. The
task equals every nested Stage 0b object, disposition publication, and artifact
path. The
complete disposition publication reproduces that artifact, count, digest, and
remote commit; its own count and digest equal its canonical retained bytes. The
counter remains the immutable proposal. The external coordinator creates this
authority after the disposition publication and publishes it under rule 6 at
`<task>/<round>/stage0b-build-authority.json`. It contains no identity, count,
or digest of itself. No authority exists for `NEXT_DESIGN_ROUND`, `PARKED`, an
ambiguous counter, or a nonexact calibration.
The convergence policy is the exact accepted design artifact and is immutable
before implementation begins. No implementation brief, candidate, packet,
review, selector, controller authorization, rehearsal, bootstrap evidence, or
acceptance may omit or replace it.

`pontius-stage0b-build-authority-publication-v1` has exactly
`build_authority`, `build_authority_artifact`,
`build_authority_byte_count`, `build_authority_sha256`,
`candidate_manifest_sha256`, `main_predecessor_oid`, `packet_path`,
`publication_commit_oid`, `publication_observation`, `publication_ref`,
`repository_id`, `schema`, `stage0b_activation_publication`,
`stage0b_activation_publication_byte_count`,
`stage0b_activation_publication_sha256`, `task`, and `task_predecessor_oid`.
The repository, ref, and packet path are exact `PONTIUS_HANDOFFS`,
`refs/heads/main`, and `<task>/<round>`. The artifact resolves inside the
publication commit, parses as the complete authority above, and reproduces its
count and digest. Candidate manifest equals the nested counter and disposition.
The wrapper's activation triple equals the complete nested build authority and
its activated series equals the nested counter's series.
Task equals the build authority, nested counter and disposition, packet path,
activation, and task-predecessor chain.
Task predecessor equals the nested disposition publication's output commit and
is an ancestor of the freshly fetched main predecessor. Publication commit is
a one-parent direct child of that main predecessor. Its tree preserves every
predecessor entry byte-for-byte and adds exactly the previously absent
`<task>/<round>/stage0b-build-authority.json` artifact. Unrelated-task
commits may intervene; a same-task conflict refuses and retries.
Observation-core repository and ref equal the wrapper, and its observed OID
equals `publication_commit_oid`. It proves that commit remotely reachable before the
implementation brief freezes. This wrapper is downstream of publication and
is never stored inside the publication commit.

For a future activated series, its separately preregistered implementation-start
carrier must carry this complete wrapper plus externally recomputed byte count
and SHA-256. That future branch cannot enter, replace, or be copied into the
freeze-tools bootstrap evidence or utility acceptance that precedes activation.
A working or unpushed JSON copy, opaque disposition artifact, prose claim,
delayed build, or self-issued authority cannot substitute.

### 6.1 Candidate-change specification

`pontius-candidate-change-spec-v1` has exactly `base_oid`, `candidate_manifest_sha256`,
`changes`, `round`, `schema`, and `task`. A change row has exactly:

| Key | Type |
| --- | --- |
| `base_blob_oid` | `oid` or `null` |
| `base_mode` | `mode` or `null` |
| `byte_count` | `count` |
| `change_kind` | `ADD` or `MODIFY` |
| `path` | repository path |
| `result_blob_oid` | `oid` |
| `result_mode` | `mode` |
| `sha256` | `sha256` |
| `source_input_sha256` | `sha256` |

Rows sort by ASCII path and cover the complete base-to-candidate tree delta.
`ADD` requires both base fields `null`; `MODIFY` requires the exact base blob
and mode. Deletion, symlink, gitlink, tree replacement, undeclared path, case
collision, and type change refuse. `source_input_sha256` names the unique
canonical `CANDIDATE_FILE/<path>` operation-input row. That owner-held row
carries the regular-file `sealed_path_identity`; the planner-visible change row
does not. The retained source bytes reproduce byte count, SHA-256, raw blob OID,
and result mode before any object write.

The adopted candidate manifest is derived from these same rows. Each row is
`<sha256> SP SP <path> LF`, sorted by the unsigned bytes of the whole row. Its
complete-byte digest equals `candidate_manifest_sha256`. The change spec binds
mode, change kind, base identity, byte count, and retained source-input digest
even though the adopted manifest row intentionally does not.

### 6.2 Review authors, route preregistration, cold input, and packet

`pontius-server-capability-class-v1` has exactly `capabilities` and `schema`.
`capabilities` contains exactly these rows in the displayed order, each with
exactly `capability_id` and `supported`, and every `supported` value is true:

```text
HTTPS_SMART_GIT
ATOMIC_MULTI_REF_PUSH
CREATE_ONLY_REF_UPDATE
EXACT_LEASE
NONFASTFORWARD_REJECTION
CASE_ISOLATED_NAMESPACE
```

`pontius-server-capability-fact-v1` has exactly `capability_id`, `endpoint_id`,
`predicate`, `repository_id`, `schema`, `source`, and `source_kind`. `predicate`
is exact true. `source` is one retained `artifact_identity`; `source_kind` is
`PROTOCOL_ADVERTISEMENT`, `SERVER_POLICY_EXPORT`, or `MUTATION_OBSERVATION`.
The accepted plan freezes one strict parser and field predicate for each
`(capability_id,source_kind)` pair. Atomic and smart-HTTPS facts require parsed
protocol advertisement bytes; ref-update and lease facts require parsed policy
export plus mutation observation; namespace isolation requires parsed policy
export plus a cross-case rejection observation. Where two sources are required,
two fact rows with distinct source kinds must agree before the capability row is
derived. A label, filename, exit code, or caller-authored boolean is not a fact.

`pontius-server-capability-observation-v1` has exactly `endpoint_id`, `facts`,
`observed_class`, `repository_id`, and `schema`. `facts` is the complete ordered
population above and each row repeats the observation coordinates. The owner
strictly parses every retained source and derives the six true class rows; no
row can be copied from the expected class. Production and rehearsal observations
have different endpoint and repository coordinates but byte-identical observed
classes. Their class digest equals the nondelta
`server_capability_class_sha256` in both paired table endpoint rows. A generic
test label or unparsed connectivity result cannot establish class equality.

`pontius-server-control-session-v1` has exactly `client_certificate_sha256`,
`controller_id`, `controller_origin_sha256`, `endpoint_id`, `repository_id`,
`schema`, `server_certificate_sha256`, `server_policy_sha256`, `session_nonce`,
and `tls_channel_binding_sha256`. It is established over mutually authenticated
TLS to the exact rehearsal server procedure. Both certificate digests are the
held public-certificate bytes, the channel binding is derived from that live
TLS session, and the controller origin equals the retained controller process.
Production coordinates, certificate substitution, a bearer token, or a caller-
supplied channel digest refuses.

`pontius-server-secret-coordinate-v1` has exactly `broker_session_sha256`,
`coordinate_kind`, `dispatch_sha256`, `fault_nonce`,
`fault_reservation_sha256`, `request_nonce`, `schema`, `step_ordinal`, and
`task_binding_id`. Broker session, dispatch, request nonce, step, and task
binding are nonnull and equal the selected network attempt. Coordinate kind is
`FAULT_BOUND` or `SESSION_BOUND`. `FAULT_BOUND` requires nonnull fault nonce and
reservation digest equal to the selected fault reservation. `SESSION_BOUND`
requires both fault fields null and is permitted only for a network step with
no fault fixture. A network step cannot omit this coordinate; an offline step
cannot create one.

`pontius-server-secret-arm-v1` has exactly `control_session_sha256`,
`controller_id`, `coordinate`, `coordinate_sha256`, `request_sequence`,
`schema`, `secret_slot_id`, and `state`. State is exact `ARM`; sequence is one;
slot ID is a fresh public identifier. Coordinate is the complete object above
and reproduces its adjacent digest. Fault-bound values equal the selected fault
reservation; session-bound values equal the reservation-free broker/session/
request attempt. The one-use secret itself is delivered only inside the
authenticated channel and no secret byte, length, or derived digest enters
this object or any evidence artifact.

`pontius-authenticated-server-artifact-v1` has exactly `artifact`,
`artifact_byte_count`, `artifact_sha256`, `payload_byte_count`,
`payload_schema`, `payload_sha256`, `signature_algorithm`,
`signature_input_sha256`, `signing_certificate_sha256`,
`tls_channel_binding_sha256`, `verification_result`,
`verifier_file_identity`, and `verifier_source_entry_sha256`. Artifact bytes
strictly parse as the server policy's signed-envelope grammar and reproduce the
adjacent positive count and digest. The domain-separated signature input binds
the payload schema, payload count and digest, TLS channel binding, control-
session nonce, and signing-certificate digest. Signature algorithm equals the
frozen server policy; verification result is exact `VALID` only when the held
independent verifier validates that input under the public key in the exact
certificate used by the mutually authenticated control session. The verifier
identity and reviewed source entry are fixed by the accepted server procedure.
A TLS success label, server log line, unsigned JSON, caller-supplied digest, or
certificate without a valid envelope signature cannot satisfy this object.

`pontius-server-secret-ack-payload-v1` has exactly `arm_sha256`,
`response_sequence`, `schema`, `secret_delivery_state`, `secret_slot_id`, and
`state`. State is exact `ACK`, sequence is one, and delivery state is exact
`DELIVERED`.

`pontius-server-secret-ack-v1` has exactly `authenticated_artifact`, `payload`,
and `schema`. Payload is the complete object above. Authenticated artifact is
the complete `pontius-authenticated-server-artifact-v1`; its payload schema,
count, and digest equal the payload's canonical bytes, and its TLS binding and
certificate equal the control session named by the ARM object. No client
launch is permitted before this verification succeeds.

`pontius-server-secret-consumed-payload-v1` has exactly
`accepted_request_count`, `ack_sha256`, `coordinate_sha256`,
`request_audience_sha256`, `schema`, `secret_slot_id`, and `state`. State is
exact `CONSUMED` and accepted-request count is one.

`pontius-server-secret-consumed-v1` has exactly `authenticated_artifact`,
`payload`, and `schema`. Payload is the complete object above. Authenticated
artifact is the complete signed object above and binds the payload, control
session, certificate, selected HTTPS request, and slot. It proves that the slot
authenticated exactly one selected request and became unusable at that
boundary. Client exit, prompt match, or an unsigned server record cannot
substitute.

`pontius-server-secret-disarmed-payload-v1` has exactly `ack_sha256`,
`consumed_sha256`, `remaining_use_count`, `schema`, `secret_slot_id`, `state`,
and `use_state`. State is exact `DISARMED`, remaining-use count is zero, and use
state is `CONSUMED_ONCE` or `UNCONSUMED`. Consumed digest is nonnull exactly for
`CONSUMED_ONCE` and is null for `UNCONSUMED`.

`pontius-server-secret-disarmed-v1` has exactly `authenticated_artifact`,
`payload`, and `schema`. Payload is the complete object above. Authenticated
artifact binds its canonical bytes to the same control session, certificate,
ACK, and slot. It is obtained after the terminal remote observation and proves
the slot is absent and cannot authenticate a retry.

`pontius-server-secret-lifecycle-v1` has exactly `ack`, `ack_sha256`, `arm`,
`arm_sha256`, `consumed`, `consumed_sha256`, `control_session`,
`control_session_sha256`, `coordinate`, `coordinate_sha256`, `disarmed`,
`disarmed_sha256`, `schema`, `secret_slot_id`, and `use_state`. Every nested
canonical object reproduces its
adjacent digest. For `CONSUMED_ONCE`, consumed is nonnull, use state equals the
disarmed payload's use state, and the exact state sequence is `ARM`, `ACK`, `CONSUMED`,
`DISARMED`. For `UNCONSUMED`, consumed and its digest are null, the exact state
sequence is `ARM`, `ACK`, `DISARMED`, and the signed disarm payload proves zero
remaining uses. Coordinate and digest equal the ARM object and the selected
step. A nonnull CONSUMED payload repeats its coordinate digest. All slot,
session, controller, endpoint, repository, policy, request, and audience
coordinates agree; fault nonce and reservation agree exactly on the
`FAULT_BOUND` branch and are null exactly on `SESSION_BOUND`. No state is
repeatable, reorderable, or derivable from an expected label. Every accepted
server use requires `CONSUMED_ONCE`; partial lifecycle evidence is retained as
a refusal and cannot enter a PASS result or utility acceptance.

`pontius-utility-rehearsal-fault-harness-projection-v1` is upstream of every
fault reservation and has exactly `component_bindings`, `schema`, and
`source_projection_set_sha256`. Components occur in this exact order:

```text
FAULT_HARNESS
FAULT_ACTIVATION_PARSER
SERVER_EVENT_EXPORTER
SERVER_EVENT_PARSER
```

`build_or_deployment_receipt` is a tagged union of exactly three named schemas.
`pontius-linked-runtime-owner-build-receipt-v1` has exactly `binary_file_identity`,
`build_receipt_artifact`, `component_id`, `native_projection_sha256`,
`reviewed_blob_oid`, `reviewed_byte_count`, `reviewed_sha256`,
`reviewed_source_entry_sha256`, `schema`, and `translation_unit_sha256`. The
strict build receipt and translation-unit map prove that the reviewed blob is an
input to the held supervisor binary and reproduce its byte digest and native
projection.

`pontius-external-held-file-install-receipt-v1` has exactly
`component_id`, `destination_file_identity`, `install_receipt_artifact`,
`installed_byte_count`, `installed_sha256`, `installed_source_entry_sha256`,
`mode`, `reviewed_blob_oid`, `reviewed_byte_count`, `reviewed_sha256`,
`reviewed_source_entry_sha256`, and `schema`. The strict receipt proves a
no-normalization copy/install from the
reviewed blob to the held final path; all byte counts and SHA-256 values agree
with both selected source entries and the destination identity.

`pontius-external-server-deployment-receipt-v1` has exactly
`component_id`, `deployed_byte_count`, `deployed_sha256`,
`deployment_receipt_artifact`, `endpoint_id`, `procedure_id`, `repository_id`,
`reviewed_blob_oid`,
`reviewed_byte_count`, `reviewed_sha256`, `reviewed_source_entry_sha256`,
`schema`, and `server_policy_sha256`. The authenticated server receipt proves
that the reviewed bytes and procedure ID are deployed under that exact endpoint,
repository, and policy. `deployed_byte_count` equals `reviewed_byte_count` and
both equal the selected `PROJECT_GIT_SOURCE` row's byte count;
`deployed_sha256` equals `reviewed_sha256` and both equal that source row's
SHA-256. The deployment artifact's strict parser reproduces those equal fields
plus the exact endpoint, repository, procedure, and server-policy identity.
Every artifact above is one retained
`artifact_identity`; its named strict parser is fixed by this appendix and the
accepted plan may select versions, not a weaker evidence shape.

A component-binding row has exactly `binding_kind`, `build_or_deployment_receipt`,
`component_id`, `endpoint_id`, `file_identity`,
`installed_source_entry_sha256`, `native_projection_sha256`, `repository_id`,
`reviewed_source_entry_sha256`, and `server_policy_sha256`. Binding kind is
`EXTERNAL_HELD_FILE`, `EXTERNAL_SERVER_PROCEDURE`, or
`LINKED_RUNTIME_OWNER`.

The receipt schema is respectively
`pontius-external-held-file-install-receipt-v1`,
`pontius-external-server-deployment-receipt-v1`, or
`pontius-linked-runtime-owner-build-receipt-v1`. Every receipt's component ID
equals its enclosing binding. Every other duplicated field equals its enclosing
binding and selected source rows.

Every reviewed-source digest selects one `PROJECT_GIT_SOURCE` entry in the
reviewed runtime-owner projection. `LINKED_RUNTIME_OWNER` has null installed-
source digest, the complete supervisor file identity, nonnull native-projection
digest, and a complete typed build receipt proving that reviewed entry was
linked into those held supervisor bytes. `EXTERNAL_HELD_FILE` has nonnull
installed `HELD_FILE_SOURCE` digest and file identity, null native projection,
and a complete copy/install receipt binding candidate blob, path, mode, byte
count, SHA-256, final path, and `FileIdInfo`. `EXTERNAL_SERVER_PROCEDURE` has
null local installed digest, file identity, and native projection; its complete
authenticated deployment receipt binds the reviewed source, endpoint,
repository, procedure ID, deployed byte digest, and server policy identity.
Endpoint, repository, and server-policy fields are null for both local binding
kinds. They are nonnull for `EXTERNAL_SERVER_PROCEDURE` and equal its complete
deployment receipt. `SERVER_EVENT_EXPORTER` is the projection's sole external-
server-procedure binding; no production or second repository coordinate is
valid. Its procedure ID equals the accepted plan's exact mapping for
`SERVER_EVENT_EXPORTER`; a caller procedure name is invalid.

Receipt schema and parser versions are selected by the accepted plan from the
exact appendix-frozen set. Every
binding is covered by the bootstrap implementation receipts and source-
projection set. No equal-byte inference, mutable script, caller parser, expected
result, selector identity, dispatch identity, or later evidence may enter the
projection. Local held identities are revalidated at final runtime evidence;
the selector-frozen external deployment-binding identity remains held but is not
revalidated by downstream evidence during runtime finalization. The correlated
server event and fresh post-case capability observation are later campaign-
result and utility-acceptance evidence. They cannot enter runtime evidence or
final revalidation.

`pontius-utility-rehearsal-fault-reservation-v1` is created after selector and
authorization validation but before one rehearsal dispatch. It has exactly
`authorization_sha256`, `case_id`, `controller_id`, `dispatch_nonce`,
`endpoint_id`, `evidence_kind`, `fault_fixture_sha256`,
`fault_harness_projection_sha256`, `fault_nonce`, `input_projection_byte_count`,
`input_projection_sha256`, `operation`,
`repository_id`, `schema`, `server_component_binding_sha256`,
`server_policy_sha256`, `server_procedure_id`, and `step_ordinal`. The endpoint,
repository, server-component-binding, server-policy, and server-procedure fields
follow this exact three-way branch:
`endpoint_id` and `repository_id` have their named scalar type or `null`; both
server digests are `sha256` or `null`; `server_procedure_id` is a frozen
procedure identifier or `null`.

| Fault branch | Endpoint/repository | Three server-deployment fields |
| --- | --- | --- |
| `SERVER_EVENT` | nonnull; equal external binding | nonnull; equal receipt |
| process-only network | nonnull; equal authorization/table | nonnull; equal receipt |
| process-only offline | both null | all null |

The server branch equals the selector's sole external-server-procedure binding
and its complete deployment receipt. Every network branch retains the selected
rehearsal endpoint, repository, authenticated server procedure, and deployment
receipt even when its selected fault evidence is process-only. Evidence kind
selects the fault oracle, never whether a server secret is authenticated and
terminally disarmed. The binding digest is the strict canonical digest of the
complete server binding row plus LF and is null only on the offline branch.
`fault_fixture_sha256` names the complete selected `FAULT` fixture row.
The authorization, evidence kind, operation, and campaign coordinates equal the
validated authorization and fixture exactly.
Both input-projection fields equal that authorization and launch dispatch.
The harness-projection digest equals the selector's complete reviewed object.
`fault_nonce` is a fresh public `nonce`, distinct from the dispatch nonce and
every earlier campaign reservation. The controller installs this exact
reservation in the accepted fault harness before process creation; failure to
install or revalidate it refuses without launching. The reservation contains no
expected outcome, credential, result, or later event identity.

`pontius-utility-rehearsal-server-event-v1` is controller-only evidence derived
after one selected rehearsal step completes. It has exactly `artifact`,
`case_id`, `endpoint_id`, `event_kind`, `fault_fixture_id`,
`fault_harness_projection_sha256`, `fault_nonce`, `fault_reservation_sha256`, `operation`,
`ref_update_set_sha256`,
`repository_id`, `schema`, `server_component_binding_sha256`,
`server_policy_sha256`, `server_procedure_id`, `server_secret_consumed`,
`server_secret_consumed_artifact`, `server_secret_consumed_byte_count`,
`server_secret_consumed_sha256`, and `step_ordinal`.
`artifact` is one retained `artifact_identity` produced by the accepted external-
server evidence procedure. Its bytes are strictly parsed by the one frozen
parser and reproduce every coordinate in this object, including the selected
component-binding digest and procedure ID. `event_kind` is exactly
`ATOMIC_MULTI_REF_UNSUPPORTED` or `CONNECTION_DROPPED_AFTER_ACCEPT`.
The complete consumed object is the authenticated one-use server record above;
its canonical bytes equal `server_secret_consumed_artifact` and reproduce the
adjacent positive count and digest. Its payload binds the same fault nonce and
request update set through the same `FAULT_BOUND` coordinate digest.

The procedure authenticates the configured rehearsal endpoint, exports one
immutable server audit event only after the client process and fresh remote-ref
observation have completed, and correlates it through the case-qualified
repository namespace, step ordinal, operation, exact remote-ref update set, and
selected server fault fixture. Its nonce and reservation digest equal the
current launch dispatch's complete fault reservation. Its endpoint, repository,
server-policy digest, component-binding digest, and procedure ID equal that
reservation and the selector's sole external-server-procedure binding. The
binding digest reaches and fixes the complete deployment receipt, reviewed and
deployed byte identities, and server policy. It is never available to a role
process, never
alters a process-completion fact or authority envelope, and contains no
credential, free-form diagnostic, or caller-authored expected
result. A label, client exit code, or unmatched server log line is not an event.

`pontius-utility-rehearsal-fault-result-v1` is completed only after the selected
fault boundary and typed operation evidence both exist. It has exactly
`activation_artifact`, `case_id`, `dispatch_sha256`, `endpoint_id`, `evidence_kind`,
`evidence_sha256`, `fault_fixture_sha256`, `fault_harness_projection_sha256`,
`fault_id`, `fault_nonce`,
`fault_reservation_sha256`, `operation`, `repository_id`, `schema`,
`server_component_binding_sha256`, `server_policy_sha256`,
`server_procedure_id`, `server_secret_coordinate`,
`server_secret_coordinate_sha256`, `server_secret_lifecycle`,
`server_secret_lifecycle_artifact`, `server_secret_lifecycle_byte_count`,
`server_secret_lifecycle_sha256`, and `step_ordinal`.
The five endpoint/repository/deployment fields use the same nullable scalar
types as the reservation.
`activation_artifact` is the immutable output of the accepted fault harness at
the actual injection boundary. Its frozen parser reproduces the reservation
nonce, fixture row, dispatch, case, step, operation, fault ID, and evidence kind.
The harness-projection digest equals the selector, reservation, and any server
event; the held component identities are revalidated before parsing. All five
endpoint/repository/deployment fields equal the reservation's exact three-way
branch. The three server fields are nonnull for both network branches and equal
the selected component binding and deployment receipt; the complete server
event is additionally required only for `evidence_kind=SERVER_EVENT`. An
offline result has all five endpoint/repository/deployment fields null.
Server-secret lifecycle fields are nonnull for every network branch; canonical
lifecycle bytes equal the artifact and reproduce the adjacent positive count
and digest. A lifecycle with use state `CONSUMED_ONCE` contains the
authenticated CONSUMED object for that exact request; when a server event
exists, those objects are byte-identical. A lifecycle with use state
`UNCONSUMED` proves by its authenticated DISARMED object that no request was
accepted and zero uses remain. DISARMED follows the terminal remote observation
in both cases. The server-secret coordinate and digest are nonnull for every
network branch, equal the lifecycle, and are exact `FAULT_BOUND` for this fault
result. All coordinate and lifecycle fields are null only on the offline
branch.
`evidence_sha256` names respectively the complete server event, cleanup
evidence, or runtime evidence selected by `evidence_kind`; that evidence proves
the plan's exact injected predicate. An organic failure with the same outer
termination code but no matching activation artifact cannot satisfy this
object.

`pontius-utility-https-rehearsal-campaign-v1` has exactly `cases`, `schema`,
`server_capability_class_sha256`, `task_bindings`, and `version`. Version is exact `1`. The class
digest names the complete object above. A case has exactly `case_id`,
`expected_terminal_class`, and `steps`. Case IDs have type `case_id`, are sorted
and unique, and equal the complete real-HTTPS cases in the accepted plan. A
step has exactly `derived_inputs`, `dispatch_mode`, `expected_envelope_schema`,
`expected_refusal_code`, `expected_step_terminal_class`, `fault_fixture_id`,
`fixture_ids`, `operation`, `role`, `schedule_variant`, `step_ordinal`, and
`task_binding_id`. `fixture_ids` is a sorted unique frozen-identifier array and may
be empty. `fault_fixture_id` is one of those IDs or null. Ordinals are
positive and contiguous within a case. Each tuple names one existing reviewed
operation schedule; a generic command, URL, ref, credential, or arbitrary
payload is forbidden.

A task-binding row has exactly `case_id`, `round`, `task`, and
`task_binding_id`. Rows sort by case ID then binding ID and are unique. Each step
selects exactly one binding in its case; its authorization task and round equal
that row. A case may bind multiple distinct tasks and rounds, which is required
for both cross-task integration orders and clean other-task descendant cases.
The selector root's own task and round continue to identify the utility
bootstrap and do not substitute for a selected campaign task binding.

A campaign derived-input row has exactly `derivation_id`, `input_id`, and
`source_step_ordinals`. Rows sort by input ID. Source ordinals are a nonempty
sorted unique array of earlier steps in the same case. `derivation_id` names one
closed schema derivation in the accepted plan, such as a prior authorization,
typed operation result, object manifest, or integration intent derived from a
completed build. It is never executable text or a caller callback. The union of
derived-input IDs and `OPERATION_INPUT` fixture rows is exactly the operation's
complete nonreserved authority-input ID population; the two sets are disjoint.

Campaign steps may use the exact `ADOPT_PAIR`, `BUILD_MAIN_OVERLAY`,
`BUILD_REVIEW_OUTPUT`, `FETCH_FOR_ADOPTION`, `FETCH_MAIN_INPUTS`,
`INTEGRATE_PACKET`, `PUBLISH_PAIR`, and `PUBLISH_REVIEW_OUTPUT` operations under
their ordinary roles. `FREEZE_PAIR` remains covered by frozen offline tests;
`FINALIZE_REVIEWS` and `PUBLISH_DISPOSITION` remain normal-route-only. Builder
setup steps use its ordinary `OFFLINE` table and the same reviewed schedule
engine. Network steps use only a paired `REHEARSAL` table. No bootstrap-only
accepted-utility authority is invented.
Expected terminal class is exactly one of:

```text
SUCCESS
IDEMPOTENT_SUCCESS
EXPECTED_REFUSAL
EXPECTED_PARTIAL_FATAL
EXPECTED_UNSUPPORTED_ATOMIC
EXPECTED_OBSERVATION
EXPECTED_TIMEOUT
EXPECTED_CANCELLATION
EXPECTED_LOST_ACK_RECOVERY
EXPECTED_REAUTHORIZATION
EXPECTED_BROKER_FAILURE
```

Expected envelope schema is one of `pontius-authority-observation-v1`,
`pontius-authority-success-v1`, or `pontius-authority-refusal-v1`.
Expected-refusal code is one exact section-15 code only for the refusal schema
and null otherwise. Step terminal class is derived, not freely selected:
success maps from authority success; idempotent success maps from a terminal
exact authority observation. `EXPECTED_OBSERVATION` maps only from a nonterminal
authority observation produced by an `OBSERVATION_ONLY/FETCH_MAIN_INPUTS` step
whose nested `REVIEW_FINALIZER` slot aggregate is exactly
`WAITING_FOR_REVIEWS`; it never launches a mutation or finalizer operation.
`EXPECTED_PARTIAL_FATAL` maps only from a nonterminal authority observation
produced by an `OBSERVATION_ONLY/PUBLISH_PAIR` step whose nested remote-pair
state is exactly `PAIR_PARTIAL_CANDIDATE_ONLY` or
`PAIR_PARTIAL_PACKET_ONLY`. The two states occupy separate campaign cases, and
the dispatch proves that no repair mutation was attempted.
Atomic-unsupported maps only from the exact post-step server-event equation
below. Timeout, cancellation, broker-failure, partial-fatal, and reauthorization
map respectively from exact codes `WALL_EXPIRED`, `CANCELLED`,
`CREDENTIAL_BROKER_REFUSED`, the observation rule above, and
`MAIN_PREDECESSOR_CHANGED`; every other plan-approved refusal maps to
`EXPECTED_REFUSAL`. `EXPECTED_LOST_ACK_RECOVERY` is case-only and cannot be a
step class. These classes describe completed campaign steps; they do not turn a
nonterminal authority observation into terminal authority.

Case terminal class is the deterministic composition of its expected step
classes. Ordinarily it equals the final step class. Lost-ack recovery requires
exactly one authority `SUCCESS` carrying a `TRANSPORT_FAILURE` outcome and
`CONNECTION_DROPPED_AFTER_ACCEPT` server event, followed immediately by
`IDEMPOTENT_SUCCESS`; every earlier class is also `SUCCESS`. The first step's
fresh exact durable-state observation closes the transition despite the lost
client acknowledgement. No other vector may claim
`EXPECTED_LOST_ACK_RECOVERY`.

`pontius-utility-rehearsal-derived-input-contract-set-v1` is upstream of the
route selector and downstream only of the campaign. It has exactly
`campaign_sha256`, `contracts`, `schema`, and `source_projection_set_sha256`.
A contract row has exactly `consumer_case_id`, `consumer_input_id`,
`consumer_operation`, `consumer_step_ordinal`, `consumer_task_binding_id`,
`derivation_id`, `output_schema`, `renderer_id`, and `sources`. Rows sort by
consumer case, step, input ID, then
derivation ID and are unique. They form a bijection with every campaign derived-
input row and repeat that step's operation.

A source row has exactly `field_selectors`, `source_authority_envelope_schema`,
`source_result_schema`, and `source_step_ordinal`. Rows occur in the renderer's
frozen order and name only earlier steps in the same case. `field_selectors` is
a nonempty ordered population from the accepted closed selector grammar; it
selects complete typed fields, never free-form JSON paths or executable text.
The two source schemas equal the campaign's expected authority envelope and the
operation's closed result schema for that step. `renderer_id` names one reviewed
pure deterministic renderer in the runtime-owner source projection. The
renderer accepts only the selected complete typed values, emits exactly one
strict canonical `output_schema` object plus LF, and has no clock, repository,
network, filesystem, callback, expected-outcome, or caller-input route.

Every derived input uses exact `delivery=PLANNER` and source kind
`INLINE_CANONICAL_INPUT`; no held-file or Git-blob materialization is valid. The
owner wraps the rendered content in one complete operation-input row whose
`input_id` and `schema` equal the contract, whose byte count and SHA-256 equal
the rendered content plus LF, and whose inline source repeats that complete
content and schema. `input_row_sha256` is the separate strict digest of this
complete wrapped row. The ordered unique union of source-row step ordinals
equals the campaign derived-input row and result derived-use
`source_step_ordinals` exactly.

The contract set contains schema names, selectors, ordinals, and renderer
identity only. It contains no later envelope, result, dispatch, input-row, or
object digest and therefore creates no result cycle.

`pontius-utility-rehearsal-fixture-set-v1` is upstream of the route selector and
has exactly `campaign_sha256`, `fixtures`, `round`, `schema`,
`source_projection_set_sha256`, and `task`. A fixture row has exactly
`artifact`, `artifact_schema`, `case_id`, `fixture_id`, `input_id`, `operation`,
`source_evidence`, `step_ordinal`, and `use_kind`. `fixture_id` is a unique
frozen ASCII identifier. Rows sort by case ID, step ordinal, use kind, input ID,
then fixture ID. `source_evidence` is a nonempty path-sorted unique
`artifact_identity` array from the frozen implementation tests.

`use_kind` is `FAULT` or `OPERATION_INPUT`. For `OPERATION_INPUT`,
`input_id` is the exact nonreserved authority-input ID for that operation, and
the artifact bytes parse under `artifact_schema`. For `FAULT`, `input_id`
is null, `artifact_schema` is exact `pontius-utility-rehearsal-fault-v1`, and
the artifact strictly describes one accepted-plan server or process fault. That
fault schema has exactly `campaign_sha256`, `case_id`, `evidence_kind`,
`fault_id`, `fixture_id`, `schema`, and `step_ordinal`; `fault_id` is a closed
identifier in the accepted campaign plan, not executable text or a caller
payload. `evidence_kind` is `CLEANUP_EVIDENCE`, `RUNTIME_EVIDENCE`, or
`SERVER_EVENT` and equals the accepted plan's exact mapping for that fault ID.

For every campaign step, its `fixture_ids` equals exactly the fixture-set rows
at that case and ordinal. Its nonnull `fault_fixture_id` selects the sole
`FAULT` row. Every other selected row is an `OPERATION_INPUT` row and
maps to one exact authority-input row by input ID, schema, byte count, SHA-256,
and source artifact. Inputs produced by an earlier campaign step remain subject
to their ordinary typed result and derivation equations and are not fixtures.
The complete authority-input projection retained in runtime evidence proves the
mapping; the result set below binds its digest and complete fixture-use rows. No
selected fixture can supply a live endpoint, repository, ref, table, credential
audience, or operation selector.

Fixture artifacts bind the campaign digest, case, step, and fixture ID where
their schema provides those fields. Neither a fixture artifact nor this set may
contain the later route-selector digest, an authorization or dispatch digest,
a runtime/result identity, or a downstream object OID. The campaign contains
fixture IDs but no fixture artifact identity; the selector contains both the
complete campaign and complete fixture set. This ordering prevents a selector-
fixture identity cycle.

`pontius-utility-rehearsal-adoption-chain-set-v1` is downstream of the campaign,
complete derived-input contract set, and complete fixture set and upstream of
the route selector. Its root has
exactly `campaign_sha256`, `chains`, `derived_input_contract_set_sha256`,
`fixture_set_sha256`, `schema`, and `source_projection_set_sha256`. A chain row
has exactly
`adopt_step_ordinal`, `builder_intent_blob_oid`, `builder_intent_fixture_id`,
`builder_intent_fixture_row_sha256`, `builder_intent_sha256`, `candidate_oid`,
`case_id`, `fetch_step_ordinal`, `packet_oid`, and `task_binding_id`. Rows sort
by case ID, fetch ordinal, then adopt ordinal and are unique.
The four root digests equal the selector's complete embedded campaign, derived-
input contract set, fixture set, and four-role source-projection set byte-for-
byte.

Each campaign `FETCH_FOR_ADOPTION` step has exactly one row and no other row is
allowed. `fetch_step_ordinal` names that step. `adopt_step_ordinal` names a
strictly later `ADOPT_PAIR` step in the same case, and both steps select the
same task binding. The fixture-set row named by ID and strict row digest is
exactly operation `ADOPT_PAIR`, use kind `OPERATION_INPUT`, input ID
`BUILDER_INTENT`, and artifact schema
`pontius-rehearsal-builder-intent-fixture-v1`, at the adopter coordinate. Its
parsed campaign, case, binding, task, round, candidate, and packet values equal
the campaign and chain row; its artifact blob OID and SHA-256 equal the row.
Several fetch rows may point to one later adopter fixture for retry or fault
cases. Each `ADOPT_PAIR` step has exactly one `ADOPTION_RECEIPT` derived-input
contract whose frozen source ordinal selects one of those fetch rows; that row
alone is the adopter's applicable chain row and its strict digest is repeated by
both authorizations and the receipt. Other fetch rows cannot be selected from
runtime success or receipt presence. An orphan adoption receipt, earlier
adopter, cross-binding fixture, ambiguous derived source, or extra row refuses.
The set carries no selector, authorization, receipt, or result identity, so the
order remains campaign, derived contracts and fixture set, chain set, selector,
then runtime authority and results.

`pontius-utility-rehearsal-selector-v1` has exactly:

| Key | Type |
| --- | --- |
| `adoption_chain_set` | complete rehearsal-adoption-chain-set object |
| `adopted_bootstrap_brief` | `artifact_identity` |
| `amendment` | `artifact_identity` |
| `campaign` | complete rehearsal-campaign object |
| `controller_id` | `actor_id` |
| `derived_input_contract_set` | complete derived-input-contract-set object |
| `endpoint_id` | exact `HTTPS_REHEARSAL` |
| `fault_harness_projection` | complete fault-harness projection object |
| `implementation_candidate_manifest_sha256` | `sha256` |
| `implementation_candidate_oid` | `oid` |
| `implementation_convergence_receipt` | complete convergence-receipt object |
| `implementation_convergence_receipt_byte_count` | `positive_count` |
| `implementation_convergence_receipt_sha256` | `sha256` |
| `implementation_plan` | complete freeze-tools implementation-plan object |
| `implementation_plan_artifact` | `artifact_identity` |
| `implementation_plan_byte_count` | `positive_count` |
| `implementation_plan_sha256` | `sha256` |
| `implementation_start_publication` | complete implementation-start-publication object |
| `implementation_start_publication_byte_count` | `positive_count` |
| `implementation_start_publication_sha256` | `sha256` |
| `implementation_start_link` | complete implementation-start-link object |
| `implementation_start_link_artifact` | `artifact_identity` |
| `implementation_start_link_byte_count` | `positive_count` |
| `implementation_start_link_sha256` | `sha256` |
| `implementation_packet_commit_oid` | `oid` |
| `implementation_packet_manifest_sha256` | `sha256` |
| `implementation_tests` | exactly four required-test-evidence objects |
| `implementation_tests_sha256` | `sha256` |
| `plan_sha256` | `sha256` |
| `pre_production_server_capability` | complete server-capability observation |
| `rehearsal_fixture_set` | complete rehearsal-fixture-set object |
| `rehearsal_attempt_ref_descriptors` | complete attempt-ref descriptor array |
| `rehearsal_refs` | nonempty rehearsal-ref array |
| `rehearsal_role_bindings` | exactly three role-binding objects |
| `pre_rehearsal_server_capability` | complete server-capability observation |
| `review_publications` | exactly two bootstrap-review-evidence objects |
| `round` | `round` |
| `schema` | exact schema literal |
| `schemas_sha256` | `sha256` |
| `server_capability_class_sha256` | `sha256` |
| `bootstrap_design_authorization_publication` | complete bootstrap authorization wrapper |
| `bootstrap_design_authorization_publication_byte_count` | `positive_count` |
| `bootstrap_design_authorization_publication_sha256` | `sha256` |
| `source_projection_set_byte_count` | `positive_count` |
| `source_projection_set_sha256` | `sha256` |
| `task` | `task` |
| `utility_author_set_byte_count` | `positive_count` |
| `utility_author_set_sha256` | `sha256` |
| `workflow` | `artifact_identity` |

A rehearsal-ref row has exactly `case_id`, `ref`, `role`, `slot_id`, and
`task_binding_id`. Rows sort by case ID, task-binding ID with null first, role,
then slot ID and cover every case-applicable `SELECTOR_PINNED_STABLE` and
`ROUTE_DERIVED_STABLE` slot. `task_binding_id` is null only for the case's shared
`HANDOFF_MAIN` row; every task-scoped stable row names one campaign binding.
Each full ref is independently derived from the selected rehearsal table,
selected binding's task and round where applicable, case ID, and closed grammar.
Every case has a disjoint `HANDOFF_MAIN` and permanent output namespace. No
attempt ref, production prefix, cross-case coordinate, reset, deletion, or
caller value is valid.

An attempt-ref descriptor row has exactly `case_id`, `derivation_id`, `kind`,
`literal_prefix`, `resolution_class`, `role`, `slot_id`, and `task_binding_id`.
Rows sort by case ID, task-binding ID, then kind in intent/result order. For
every unique `(case_id,task_binding_id)` selected by any campaign
`INTEGRATE_PACKET` step, the array contains exactly the intent and result rows
and no others. Each pair has resolution class exactly
`AUTHORIZATION_DERIVED`, role exactly integrator, and equals the selected
rehearsal integrator table's two section 1.3 descriptors. The selected binding's
task and round supply that step's route components. Rows contain no full ref,
authorization digest, result OID, or process result. The owner validates the
complete population before authorization and derives full attempt refs only
after that exact authorization's external digest exists.

A rehearsal-role binding has exactly `execution_projection_byte_count`,
`execution_projection_sha256`, `role`, `role_projection_byte_count`,
`role_projection_sha256`, `role_table_instance_byte_count`,
`role_table_instance_sha256`, and `table_instance_kind`. Rows occur in builder,
publisher, integrator order. Builder kind is exact `OFFLINE`; publisher and
integrator kind is exact `REHEARSAL`. Every projection and table is the matching
member of the frozen reviewed four-role source set. The selected table is the
only table parsed and loaded into broker state. A sibling table may retain an
opaque source handle solely for complete-byte identity and final revalidation,
but it is never decoded, selected, mapped into broker policy, or supplied to a
child or planner. It has no live selector or capability authority.

This selector is issued under the adopted bootstrap after the implementation
candidate, rule-6 packet, two bootstrap reviews, source projections, campaign,
derived-input contracts, fixture set, adoption-chain set, fault-harness
projection, capability observations, and pre-
rehearsal tests are frozen. The
fixture set is the complete immutable population selected by campaign steps and
is rederived from those tests and the disposable namespace. The pre-production
and pre-rehearsal capability observations reproduce the same complete class and its
digest equals the campaign, paired table rows, and this selector. The fault-
harness projection's sole external-server-procedure binding has the pre-
rehearsal observation's endpoint and repository, and equals every selected
`REHEARSAL` table endpoint row used by a server-fault step. Its server-policy
digest equals the strict parse of every `SERVER_POLICY_EXPORT` source in that
observation. It cannot equal the production endpoint, repository, or policy.
A server-fault fixture cannot replace the baseline pre- and post-case class
observation.

The selector and fixtures contain no accepted utility authority, normal round
preregistration, production ref or rehearsal-table capability literal,
finalizer, later controller authorization, rehearsal result, ceremonial
integration, durable disposition, per-round reviewer slot, or identity of the
selector itself. Their ordered identities can therefore authorize the real
HTTPS campaign without depending on the acceptance that campaign establishes.
The selector contains stable full refs and attempt-ref descriptors only. It
contains no full authorization-derived attempt ref, so its identity is upstream
of every transition authorization it selects.

`pontius-candidate-author-set-v1` has exactly `attributions`, `authors`,
`candidate_change_spec_sha256`, `implementers`, `round`, `schema`, and `task`.
An attribution row has exactly `author_ids`, `authorship_evidence`, and
`candidate_change_row_sha256`. `author_ids` is a nonempty sorted unique
`actor_id` array. `authorship_evidence` is a nonempty array of distinct
`artifact_identity` objects sorted by path. Each artifact parses as one complete
`pontius-authorship-evidence-v1` object frozen by the adopted controller before
reviewer selection, has coordinate kind `CANDIDATE_CHANGE`, and reproduces this
row's complete change-row digest and changed path. Author IDs are the exact
sorted union of actor IDs on the row's `AUTHORED` evidence.

`implementers` is a nonempty array of exact implementer rows sorted by
`actor_id`. A row has exactly `actor_id` and `evidence`; `evidence` is a
nonempty path-sorted unique `artifact_identity` array. Each artifact parses as
a complete evidence record with that actor, coordinate kind
`CANDIDATE_CHANGE`, and a non-`AUTHORED` attribution kind. It covers every role
or session that implemented, assembled, generated, or rewrote any candidate
change, even when another actor is credited as its content author.

There is exactly one attribution for every canonical candidate-change row, in
the same order. `candidate_change_row_sha256` hashes that complete strict
canonical row plus LF. The root `authors` array is the sorted unique union of
all attribution author IDs and all implementer-row actor IDs. Missing, extra,
duplicated, unsupported, or unassigned change authorship or implementation
identity refuses. Across attribution rows every candidate-change evidence
artifact is consumed exactly once; implementer rows are its exact non-author
secondary index. The set contains no candidate commit,
FREEZE authorization, preregistration, reviewer slot, review output, or identity
of itself.

`pontius-round-review-author-set-v1` has exactly:

| Key | Type |
| --- | --- |
| `authors` | sorted unique `actor_id` array |
| `candidate_author_set_byte_count` | `positive_count` |
| `candidate_author_set_sha256` | `sha256` |
| `round` | `round` |
| `schema` | exact schema literal |
| `spent_result_dag` | complete spent-result-DAG observation |
| `task` | `task` |
| `utility_author_set_byte_count` | `positive_count` |
| `utility_author_set_sha256` | `sha256` |

Both author-set identities name complete canonical upstream objects. `authors`
is exactly the sorted unique union of their complete author arrays. It contains
no reviewer slot, preregistration, authorization, or result identity. Its
externally computed complete-byte count and SHA-256 are the reviewer-exclusion
identity for this round.

`pontius-round-preregistration-v1` has exactly:

| Key | Type |
| --- | --- |
| `amendment` | `artifact_identity` |
| `candidate_base_oid` | `oid` |
| `candidate_ref` | derived candidate ref |
| `endpoint_id` | exact `PRODUCTION_HANDOFF` |
| `finalizer_id` | `actor_id` |
| `main_ref` | exact handoff-main ref |
| `packet_ref` | derived packet ref |
| `plan_sha256` | `sha256` |
| `review_output_refs` | exactly two derived review-output refs |
| `reviewer_slots` | exactly two reviewer-slot-spec objects |
| `round_review_author_set_byte_count` | `positive_count` |
| `round_review_author_set_sha256` | `sha256` |
| `route_id` | `route_id` |
| `round` | `round` |
| `schema` | exact schema literal |
| `schemas_sha256` | `sha256` |
| `source_projection_set_byte_count` | `positive_count` |
| `source_projection_set_sha256` | `sha256` |
| `task` | `task` |
| `utility_review_authority_sha256` | `sha256` |
| `workflow` | `artifact_identity` |

Reviewer-slot objects use the exact grammar below. Their ordinals, reviewer
identities, and output refs are complete. Both reviewers are absent from the
complete bound round-review-author set. `review_output_refs` contains those
same two refs in ordinal order. Candidate, packet, output, and main refs are
the exact stable coordinates derived from task and round. `endpoint_id` is the
stable table selector, never a URL. Workflow and amendment artifact identities,
schemas, plan, source-projection set, and accepted utility authority are all
complete before selection. `candidate_base_oid`, task, and round equal the
selected candidate round. `finalizer_id` is the sole controller identity
allowed to issue that round's finalizer authorization.

The preregistration is frozen through the adopted controller workflow outside
the raw-object-v5 utility it selects. The authority-tool bundle cannot produce
or use one for its own design or implementation bootstrap. The object contains
no identity of itself or of a cold input, result commit, result tree,
authorization, dispatch, observation, receipt, review, finalizer authorization,
or disposition. Its externally computed complete-byte count and SHA-256 are
the route-selection identity.

`pontius-cold-input-spec-v1` has exactly:

| Key | Type |
| --- | --- |
| `candidate_change_spec_sha256` | `sha256` |
| `candidate_manifest_sha256` | `sha256` |
| `round_preregistration_byte_count` | `positive_count` |
| `round_preregistration_sha256` | `sha256` |
| `reviewer_slots` | exactly two reviewer-slot-spec objects |
| `round` | `round` |
| `round_review_author_set_byte_count` | `positive_count` |
| `round_review_author_set_sha256` | `sha256` |
| `schema` | exact schema literal |
| `scope_paths` | sorted unique repository-path array |
| `task` | `task` |
| `utility_author_set_byte_count` | `positive_count` |
| `utility_author_set_sha256` | `sha256` |
| `workflow` | `artifact_identity` |

A reviewer-slot spec has exactly `ordinal`, `output_ref`, and `reviewer_id`.
The two rows occur in ordinal order; identities are distinct and absent from
the complete bound round-review-author set. Both utility-author-set fields
equal every role source projection and the freeze authorization. Both round-
review-author fields equal the preregistration and complete packet artifact.
`scope_paths` is complete over the candidate delta and every normative peer
input. Cold input excludes mutable working files, chat, self-report, progress,
dispositions, and peer output.
Both preregistration fields equal the complete object above. Task, round,
reviewer slots, workflow, and accepted utility/source identities reproduce it
exactly; a prose route name or later receipt cannot select the route.

`pontius-packet-source-manifest-v1` is a self-excluding text-row grammar over
the complete retained source-input population authorized for the packet. Each
row is `<sha256> SP SP <byte_count> SP SP <mode> SP SP <blob_oid> SP SP <path>
LF`. Rows sort by unsigned complete-row bytes. The packet destination of this
manifest is excluded from its rows. Its externally computed complete-byte
digest is `packet_source_manifest_sha256`.

`pontius-packet-build-spec-v1` has exactly `cold_input_spec_sha256`,
`packet_rows`, `packet_source_manifest_sha256`, `round`, `schema`, `task`, and
`workflow_sha256`. Its externally computed complete-byte digest is
`packet_build_spec_sha256`. A packet row has exactly `destination_path`, `mode`,
`renderer`, and `source`. `source` is an `artifact_identity` for `STATIC_BLOB`
and `null` for a derived renderer.
Renderer is exactly:

```text
STATIC_BLOB
DERIVED_CANDIDATE_RECORD
DERIVED_CANDIDATE_MANIFEST
DERIVED_HANDOFF
```

Rows sort by destination path and include one `STATIC_BLOB` row for the already
derived packet-source manifest artifact. Each renderer has one canonical
grammar in the accepted plan. Derived rows may consume only values already
fixed by the freeze authorization and deterministically computed candidate
identity; they never consume the later packet OID, builder-intent identity,
launch identity, receipt, or wall clock. The build spec and source manifest are
different objects and neither contains its own digest.

The packet-build population contains exactly one `STATIC_BLOB` row for the
complete utility-author-set document at
`<task>/<round>/utility-author-set.json`, one for the candidate-author set at
`<task>/<round>/candidate-author-set.json`, one for the round-review-author set
at `<task>/<round>/round-review-author-set.json`, and one for the complete round
preregistration at `<task>/<round>/raw-route-preregistration.json`. Their
artifact byte counts and SHA-256 values equal the cold-input spec, nested set
identities, and freeze authorization. Reviewer slots cannot be selected until
all author objects and the preregistration are complete.

### 6.3 Packet inventory and utility acceptance authority

`pontius-packet-inventory-v1` has exactly `artifacts`, `candidate_oid`,
`packet_commit_input_sha256`, `packet_oid`, `packet_tree_oid`, `round`,
`schema`, and `task`. `artifacts` is the complete destination-path-sorted array
of `artifact_identity` objects produced by the packet-build spec. Every tree
entry, raw commit field, blob identity, and spec relation is independently
recomputed. The inventory is downstream output and does not enter the freeze
authorization.

`pontius-utility-bootstrap-bounded-process-output-v1` has exactly `byte_count`,
`content_hex`, `schema`, and `sha256`. Content hex is lowercase, has exactly
twice the byte-count characters, decodes to the complete bounded stdout or
stderr bytes, and reproduces the digest. It is embedded in its self-free
receipt; it is not an `artifact_identity` and needs no later Git carrier.

`pontius-utility-bootstrap-publication-push-receipt-v1` has exactly `argv`,
`controller_id`, `environment_sha256`, `git_config_projection_sha256`,
`git_executable_file_identity`, `process_completion`, `publication_commit_oid`,
`publication_ref`, `repository_id`, `schema`, `stderr_output`, and
`stdout_output`. Both outputs are complete
`pontius-utility-bootstrap-bounded-process-output-v1` objects. Argv is the
exact credential-free held-Git push of the one
publication commit to the one full publication ref with the adopted compare-
and-swap rule. Process completion is success and bounded outputs are retained.
Controller ID is the actor who authorized and observed this exact push attempt.
This self-free receipt contains no remote query, query nonce, observation,
evidence row, or identity of itself.

`pontius-utility-bootstrap-push-query-ordering-v1` has exactly `controller_id`,
`events`, and `schema`. It is a controller-attested, self-free two-event
transcript rather than an independent append-only journal. The events occur in
this exact order and have exactly `event`, `object_sha256`, `ordinal`, and
`qpc_tick_hex`:

1. `PUSH_RECEIPT_FROZEN`, ordinal one, whose object digest is the canonical
   complete-byte digest of the successful publication-push receipt; and
2. `REMOTE_QUERY_ISSUED`, ordinal two, whose object digest is SHA-256 over the
   strict canonical object containing only the query argv and fresh query nonce.

Both ticks use one controller-held QPC source and the second is strictly later.
The transcript contains no query result, remote observation, publication
wrapper, artifact identity, count, digest, or identity of itself.

`pontius-utility-bootstrap-pre-push-query-receipt-v1` has exactly `argv`,
`completed_qpc_tick_hex`, `controller_id`, `credential_free_url_sha256`,
`endpoint_id`, `environment_sha256`, `git_config_projection_sha256`,
`git_executable_file_identity`, `issued_qpc_tick_hex`, `parsed_oid`,
`parsed_ref`, `process_completion`, `query_nonce`, `repository_id`, `schema`,
`stderr_output`, and `stdout_output`. Both outputs use the complete bounded-
output schema above. It is a self-free fresh precondition
query and contains no push receipt, push/query ordering receipt, publication,
result commit, build receipt, artifact identity, or identity of itself. Both
ticks use the controller-held QPC source; completion is strictly
later than issue. Argv is exact
`git ls-remote --refs <credential-free-url> <full-ref>` under the held Git
executable, closed environment, and reviewed config projection. Process
completion is success; stderr is empty; stdout is exactly
`<oid><HT><ref><LF>`; and the strict parser reproduces the sole full ref and
OID.

`pontius-utility-bootstrap-pre-push-remote-observation-v1` has exactly
`observed_oid`, `query_receipt`, `query_receipt_artifact`,
`query_receipt_byte_count`, `query_receipt_sha256`, `ref`, `repository_id`,
`schema`, and `state`. Query receipt is the complete self-free pre-push receipt
above. Its canonical bytes equal the artifact bytes and reproduce the adjacent
positive count and digest. Observed OID, ref, and repository equal the parsed
receipt; state is exact `EXACT`. The later H integration-record publication
stores this receipt artifact; this self-free observation contains no H commit,
publication, remote observation of H, or identity of itself.

`pontius-utility-bootstrap-pre-push-ordering-v1` has exactly
`ceremonial_commit_input_sha256`, `controller_authorization`,
`controller_authorization_byte_count`, `controller_authorization_sha256`,
`controller_disposition`, `controller_disposition_artifact`,
`controller_disposition_byte_count`, `controller_disposition_sha256`,
`controller_id`, `decision`, `events`, and `schema`. It is a self-free
three-event controller transcript. The complete authorization and disposition
canonical bytes reproduce their adjacent positive counts and digests; the
disposition bytes equal the retained artifact. Decision is exact
`AUTHORIZE_CEREMONIAL_INTEGRATION`. Both objects name the same controller,
candidate, start, plan, tests, rehearsal, finalizer, product coordinate,
ceremonial message, metadata, and pinned retention authority. The
events have exactly `event`, `object_sha256`, `ordinal`, and `qpc_tick_hex` and
are, in order:

1. `PRECONDITION_QUERY_COMPLETED`, ordinal one, naming the complete canonical
   pre-push-query-receipt digest;
2. `IMPLEMENTATION_CONTROLLER_DISPOSITION_ACCEPTED`, ordinal two, naming the
   complete canonical controller-disposition digest; and
3. `CEREMONIAL_CONSTRUCTION_AUTHORIZED`, ordinal three, naming the complete
   canonical ceremonial-commit-input digest.

Ticks strictly increase. Event two occurs only after the complete controller
authorization and disposition artifact have been independently parsed and the
authorizing decision accepted. No ceremonial input serialization, raw-commit
rendering, `hash-object`, object write, ref transition, or push may start before
event two; only the canonical ceremonial input may be assembled between events
two and three. No raw-commit rendering or object write may start before event
three. The transcript contains no result commit, push receipt, publication,
remote observation, or identity of itself.

`pontius-utility-bootstrap-remote-query-receipt-v1` has exactly `argv`,
`credential_free_url_sha256`, `endpoint_id`, `environment_sha256`,
`git_config_projection_sha256`, `git_executable_file_identity`,
`ordering_receipt`, `ordering_receipt_byte_count`, `ordering_receipt_sha256`,
`parsed_oid`, `parsed_ref`,
`process_completion`, `publication_push_receipt`,
`publication_push_receipt_byte_count`,
`publication_push_receipt_sha256`, `query_nonce`, `repository_id`, `schema`,
`stderr_output`, and `stdout_output`. Both outputs use the complete bounded-
output schema above. The complete push and ordering receipts reproduce their
adjacent positive counts and digests without naming a Git artifact. The
ordering receipt's first event binds that
push-receipt digest; its second binds this exact argv and nonce, and its
controller equals the push receipt controller and the controller fixed by the
specialized publication carrier. The push receipt's
repository/ref/commit equal this query target. Argv is exact
`git ls-remote --refs <credential-free-url>
<full-ref>` under the held executable, closed environment, and reviewed config
projection. Process completion is success; stderr is empty and
stdout is exactly `<oid><HT><ref><LF>`. The strict parser reproduces parsed ref
and OID and rejects extra, missing, abbreviated, symbolic, or malformed rows.

`pontius-utility-bootstrap-external-retention-receipt-v1` has exactly
`committed_qpc_tick_hex`, `controller_id`, `entry_id`,
`previous_entry_sha256`, `producer_id`, `record_byte_count`, `record_sha256`,
`retention_authority_sha256`, `retention_service_id`, `schema`,
`service_signature`,
`signature_input_sha256`, `signing_key_sha256`, and `verification_result`. The
verification result is exact `VALID`; the domain-separated signature input
binds authority, controller, authorized producer, service, entry, predecessor,
record count and digest, commit tick, and signing key. Controller, producer,
service, key, algorithm, and namespace equal the complete pinned authority.
Entry ID uses its exact nonce grammar. Commit tick is exactly 16 lowercase
hexadecimal digits. The signature preimage bytes are exactly:

```text
pontius-utility-bootstrap-retention-signature-v1 LF
<retention_authority_sha256> LF
<controller_id> LF
<producer_id> LF
<retention_service_id> LF
<entry_id> LF
<previous_entry_sha256> LF
<record_byte_count canonical unsigned decimal> LF
<record_sha256> LF
<committed_qpc_tick_hex> LF
<signing_key_sha256> LF
```

Every substituted value is strict ASCII under its declared scalar grammar;
there is no JSON, locale, escaping, normalization, or optional field. The
SHA-256 of these exact bytes is `signature_input_sha256`. Service signature is
exactly 128 lowercase hexadecimal characters and verifies as Ed25519 over that
input under the held authority public key. The independent authority verifier produces
`VALID`; a receipt-supplied verifier, key, algorithm, or Boolean cannot do so.
The first predecessor equals the authority genesis digest; every later
predecessor equals the immediately preceding receipt SHA-256 in the same
service namespace. Commit ticks strictly increase. The named service creates
and durably flushes one new hash-chained entry containing the exact record
bytes before signing and returning this receipt. Duplicate entry, replacement,
truncation, unflushed acknowledgement, chain fork, or substituted producer
refuses. The service is outside P, H, Git, and the utility process and cannot
create or mutate a repository ref.

`pontius-utility-bootstrap-remote-observation-core-v1` has exactly
`observed_oid`, `query_receipt`, `query_receipt_byte_count`,
`query_receipt_sha256`, `ref`, `repository_id`, `schema`, and `state`. Query
receipt is the complete self-free object above and reproduces the adjacent
positive count and digest. Observed OID, ref, and repository equal the parsed
receipt; state is exact `EXACT`. The core is downstream of the queried
publication and names no retention receipt or identity of itself.

`pontius-utility-bootstrap-remote-observation-v1` has exactly `observation`,
`observation_byte_count`, `observation_sha256`,
`retention_authority_sha256`, `retention_receipt`, and `schema`. Observation is
the complete core above and reproduces the adjacent positive count and digest.
The complete external retention receipt names those same core bytes and the
same pinned authority digest. This wrapper is the finite per-publication durable authority
outside the recursively self-observed Git chain: it is never stored in the
queried commit and requires no later Git publication or remote query.

`pontius-utility-bootstrap-post-push-remote-observation-v1` has exactly
`observed_oid`, `query_receipt`, `query_receipt_artifact`,
`query_receipt_byte_count`, `query_receipt_sha256`, `ref`, `repository_id`,
`schema`, and `state`. Query receipt is the complete push-bound self-free
remote-query receipt above. Its canonical bytes equal the artifact bytes and
reproduce the adjacent positive count and digest. Observed OID, ref, and
repository equal the parsed receipt; state is exact `EXACT`. The later H
integration-record publication stores the query-receipt artifact and distinct
JSON artifacts whose bytes equal every nested ordering and push receipt. This
self-free observation contains no H
commit, H publication, downstream evidence row, or identity of itself.

`pontius-utility-bootstrap-design-source-path-set-v1` has exactly `paths` and
`schema`. Paths are exactly the following ASCII-sorted array:

1. `docs/briefs/v0a-i01-freeze-tools-r002-brief.md`
2. `docs/superpowers/specs/2026-09-01-raw-object-workflow-amendment-v5.md`
3. `docs/superpowers/specs/2026-09-01-v0a-i01-freeze-tools-design.md`
4. `docs/superpowers/specs/2026-09-01-v0a-i01-freeze-tools-git-boundary.md`
5. `docs/superpowers/specs/2026-09-01-v0a-i01-freeze-tools-runtime-boundary.md`
6. `docs/superpowers/specs/2026-09-01-v0a-i01-freeze-tools-schemas.md`

The complete path set is frozen in the adopted brief and candidate manifest.
`coverage.md`, `handoff.md`, and `coverage-plan.md` are not members; the working
coverage plan cannot define, extend, reorder, or replace this set.

`pontius-utility-bootstrap-terminal-declaration-row-v1` has exactly `artifact`,
`byte_offset`, `corrective_round_cap`, `lock_event`, `no_r006`, `source_role`,
`terminal_round`, `terminal_round_ordinal`, and
`terminal_rule_locked_after_r002_freeze`. The seven rows are exactly the path
set above in its frozen order followed by H `coverage.md`. Byte offset selects
the sole canonical `Stage0b:` declaration in the artifact. Parsed values retain
the actual syntactically valid declaration. Zero, duplicate, or malformed
declarations refuse; semantic disagreement remains representable as the typed
contradiction below.

`pontius-utility-bootstrap-interface-inventory-v1` has exactly `rows` and
`schema`. A row has exactly `kind`, `semantic_contract_sha256`, `source_paths`,
and `stable_name`. Kind is `SCHEMA`, `ENTRY_POINT_CONTRACT`, or
`LIFECYCLE_STATE_SET`; paths are sorted and nonempty. Rows sort by kind then
stable name and completely enumerate the seven reviewed source files. The
semantic digest hashes the canonical field/cardinality/order/equality clauses
for that interface. Added, removed, or unequal rows are one interface-change
event; rename is remove plus add.

`pontius-utility-bootstrap-predecessor-round-v1` has exactly
`attempted_closure_contract_ids`, `closure_evidence`,
`decision_publication`, `decision_publication_byte_count`,
`decision_publication_sha256`, `round`, and `round_ordinal`.
`decision_publication` is the complete prior
`pontius-utility-bootstrap-design-disposition-publication-v1`; its canonical
bytes reproduce the adjacent positive count and digest and its nested decision
is exact `NEXT_DESIGN_ROUND`. Attempted-closure contract IDs are the sorted
unique prior blocking contracts whose closure evidence maps to the immediately
following candidate/scope delta. The retained evidence bytes identify those
prior findings, affected paths, predecessor/current blobs, and verification
criteria. Rows are adopted-rule-6 controller decisions in ascending contiguous
round order.

`pontius-utility-bootstrap-series-state-v1` has exactly
`adjudication_evidence`, `adjudication_state`, `candidate_manifest_sha256`,
`candidate_oid`, `candidate_ref`, `interface_inventory`,
`interface_inventory_artifact`, `interface_inventory_byte_count`,
`interface_inventory_sha256`, `predecessor_interface_inventory_sha256`,
`predecessor_rounds`, `review_scope`, `review_scope_sha256`, `round`,
`round_interface_change_count`, `round_ordinal`, `schema`, `series_id`,
`terminal_declarations`, `terminal_rule_status`, and `workflow_sha256`. Series
is exact `v0a-i01-freeze-tools-design`; ordinal is two
through five and round is its exact three-digit rendering. Review scope is the
complete path-sorted artifact population a reviewer may open: the six P files,
H coverage/instructions, adopted workflow, and declared checklist inputs. Its
digest hashes the complete canonical array. Predecessor count is ordinal minus
two. At r002 it is empty; later rows start at r002, are contiguous, and each
decision publication resolves under adopted packet rule 6. Every later scope or
candidate differs from its immediate predecessor; unchanged bytes cannot be
relabelled. The candidate ref's terminal round component equals this round.
Terminal declarations are the complete seven rows above. Ordinal five permits
no successor and ordinal six is outside the type. Alias, rebase, task rename,
series rename, reviewer replacement, or missing predecessor cannot reset the
chain.
The first predecessor publication is r002. Each later publication commit
descends from and preserves the previous one; the current design-packet
publication descends from the last. Each row's round, candidate, scope,
inventory, reviews, findings, and workflow derive from its complete nested
disposition and series state. No caller scalar can replace those preimages.
Interface inventory artifact bytes parse as the complete inventory and
reproduce the adjacent positive count and digest. At r002 predecessor inventory
is null and change count is zero. Later, predecessor digest selects the
immediate prior inventory and change count is its complete canonical set
difference. Adjudication state is CLEAR or AMBIGUOUS; ambiguity requires a
nonnull retained evidence artifact binding disputed paths and interfaces, while
CLEAR requires null. Terminal status is MATCH exactly when all seven parsed
rows equal cap 3, lock R002_FREEZE, no-r006 true, terminal r005, ordinal 5, and
locked true. Any other fully parsed population is CONTRADICTION. R002 requires
MATCH; a later contradiction remains a typed terminal disposition input.

`pontius-utility-bootstrap-design-finding-v1` has exactly `affected_paths`,
`body_byte_count`, `body_sha256`, `category`, `contract_id`, `finding_ordinal`,
`residual_ordinal`, and `severity`.
Ordinal is a gap-free positive integer in report order. Severity is `CRITICAL`,
`IMPORTANT`, or `DESIGN`; category is `DEFECT` for the first two and `DESIGN`
for the third. Affected paths are sorted, unique, and nonempty. Body bytes are
positive UTF-8 with LF endings and no NUL and reproduce the adjacent count and
digest.
Contract ID is a nonempty ASCII `[A-Z][A-Z0-9_.:/-]{0,127}` category selected
from the frozen design checklist. Residual ordinal is one plus the number of
distinct predecessor decisions whose typed review findings name that contract
and whose immediate successor series state proves an attempted closure. Two
reviewers in one round count once. A renamed or alternate contract label cannot
reset the ordinal.

For one typed design review, `finding_sha256` is SHA-256 of ASCII
`<reviewer-ordinal>:<finding-ordinal>` followed by one LF and the complete
canonical finding-row bytes including their final LF. Reviewer ordinal and row
ordinal therefore enter the preimage even when two reviewers report identical
bodies.

`pontius-utility-bootstrap-design-review-receipt-v1` has exactly
`candidate_manifest_sha256`, `candidate_oid`, `defect_verdict`,
`design_packet_publication_sha256`, `design_verdict`, `findings`, `ledger_line`,
`ordinal`, `peer_review_access_attestation`, `report`, `reviewer_id`,
`schema`, `series_state`, `series_state_artifact`, `series_state_byte_count`,
`series_state_sha256`, `verdict_date`, and `workflow_sha256`. Ordinal is one or two;
peer-review access attestation is exact `NO_PEER_REPORT_BEFORE_REPORT_FREEZE`.
This is an attributed human attestation under the adopted bootstrap workflow,
not a claim that the not-yet-accepted utility mechanically observed file opens.
Findings are the complete ordered array
parsed from the report. Defect verdict is CLEAN exactly when no CRITICAL or
IMPORTANT row exists; otherwise it is NOT CLEAN. Design verdict is SOUND
exactly when no DESIGN row exists, and otherwise is STRAINED or WRONG SHAPE as
rendered in the report.
Series state is the complete packet object above; its canonical artifact bytes
reproduce the adjacent positive count and digest. Candidate, manifest, round,
scope, terminal declarations, predecessor chain, and workflow equal the design
packet and both reviewers byte-for-byte.

The report starts with these exact LF-terminated lines and one blank line:

```text
Reviewer ID: <reviewer_id>
Candidate commit: <candidate_oid>
Manifest SHA-256: <candidate_manifest_sha256>
Design packet publication SHA-256: <design_packet_publication_sha256>
Bootstrap series state SHA-256: <series_state_sha256>
Reviewer ordinal: <ordinal>
Defect verdict: <defect_verdict>
Design verdict: <design_verdict>

```

Each finding then renders `Finding`, `Severity`, `Category`, `Contract`,
`Residual ordinal`, canonical compact JSON `Affected paths`, `Body byte count`,
`Body SHA-256`, `Body:`, the exact
length-framed body bytes, and `End finding`, each on its own LF-terminated line.
The strict parser consumes the complete report and reproduces every row; no
Critical, Important, or design text may occur outside those blocks. Report
artifact bytes reproduce its identity. The issuer-authored ledger line is one
physical LF-terminated line containing, in exact order, reviewer, ordinal,
candidate, manifest, report SHA-256, defect verdict, and design verdict. Its
artifact bytes reproduce that exact rendering. Candidate, packet, workflow,
reviewer, date, verdict, report, ledger, finding, and body substitutions refuse.

`pontius-utility-bootstrap-design-review-publication-v1` has exactly
`publication`, `receipt`, `receipt_artifact`, `receipt_byte_count`,
`receipt_sha256`, and `schema`. Receipt is the complete typed object above; its
canonical bytes equal the artifact and reproduce the positive count and digest.
Publication is a complete adopted-rule-6 publication with stage exact
`RULE6_DESIGN_REVIEW_PUBLICATION`, ordinal equal to the receipt, and artifact
population exactly the receipt, report, and issuer ledger line. Its commit
descends from the same stage-`RULE6_DESIGN_PACKET_PUBLICATION` design packet
named by the receipt, and its remote observation proves the commit/ref exact.
The two review wrappers have distinct reviewers, ordinals one then two, and
identical candidate, manifest, packet-publication digest, and workflow digest.
Both reports freeze before either reviewer opens its peer's report.

`pontius-utility-bootstrap-design-path-attribution-v1` has exactly `authors`,
`authorship_evidence`, `path`, and `source_artifact`. Path is one of the six P
paths or exact H `coverage.md`; rows sort by path and form a seven-row bijection.
Source artifact resolves to the exact frozen candidate or handoff artifact.
Authors are sorted, unique, and nonempty. Authorship evidence is a nonempty
path-sorted unique artifact array retained in the adopted design packet. Each
artifact parses as one complete `pontius-authorship-evidence-v1` object with
coordinate kind `DESIGN_SOURCE` and reproduces this path and source artifact.
Authors are the exact sorted union of all evidence actor IDs, including every
actor who authored, implemented, assembled, generated, or rewrote those bytes.
Across the seven attribution rows, every frozen design authorship-evidence
artifact is consumed exactly once and no unparsed or unassigned evidence exists.

`pontius-utility-bootstrap-design-author-set-v1` has exactly `attributions`,
`authors`, and `schema`. Attributions are the complete seven rows above. Authors
are their exact sorted union; no supplied or inferred actor lies outside that
union. The complete object and every evidence artifact are retained in the design packet.
Both design reviewers and the controller are absent from it. Later
implementation source projections derive their separate utility-author set and
require those design reviewers and controller absent at that later gate; no
preimplementation object claims knowledge of future implementation authors.

`pontius-utility-bootstrap-design-finding-adjudication-v1` has exactly
`finding_sha256`, `outcome`, `rationale`, `rationale_byte_count`, and
`rationale_sha256`. Outcome is `BLOCKING` or `NONBLOCKING`. Rationale fields are
all null for a DEFECT finding, which is always BLOCKING. For a DESIGN finding,
the external controller selects BLOCKING or NONBLOCKING; all three rationale
fields are nonnull, the retained rationale bytes reproduce the adjacent count
and digest, name the exact finding and reviewer, and explain the decision.
A WRONG SHAPE design verdict can be NONBLOCKING only when that rationale states
why the current architecture remains implementable despite the reported shape
risk. Rows are ordered by reviewer ordinal then finding ordinal and form a
bijection over both typed receipts.

`pontius-utility-bootstrap-design-breaker-override-v1` has exactly `decision`,
`finding_sha256s`, `justification`, `justification_byte_count`,
`justification_sha256`, and `schema`. Decision is
`AUTHORIZE_FREEZE_TOOLS_IMPLEMENTATION` or `NEXT_DESIGN_ROUND`. Finding digests
are the sorted unique complete trigger population: every finding with residual
ordinal at least two and every DESIGN finding belonging to a WRONG SHAPE review.
The external controller's justification bytes reproduce the adjacent positive
count and digest and explain why this exact decision is safer than the default
redesign. The override cannot make a DEFECT finding nonblocking or select NEXT
at r005.

`pontius-utility-bootstrap-design-disposition-v1` has exactly
`adjudication_evidence`, `adjudication_state`, `candidate_manifest_sha256`,
`candidate_oid`, `controller_id`, `decision`,
`design_breaker_override`,
`design_packet_publication_sha256`, `design_review_publication_sha256s`,
`finding_adjudications`, `next_round`, `parking_category`, `parking_reason`,
`schema`, `series_state`, `series_state_artifact`, `series_state_byte_count`,
`series_state_sha256`, and `workflow_sha256`. Decision is
`AUTHORIZE_FREEZE_TOOLS_IMPLEMENTATION`, `NEXT_DESIGN_ROUND`, or `PARKED`.
Review-publication digests are exactly
the two complete canonical publication-object digests in ordinal order. Finding
adjudications are exactly the typed rows above. Critical and Important findings
require outcome BLOCKING. SOUND reviews have no design findings. Series state
artifact bytes parse as the complete state and reproduce the adjacent count and
digest. Candidate, packet, reviews, state, round, scope, terminal declarations,
and workflow agree. The controller is distinct from both reviewers
and every member of the complete design-author set. Candidate, workflow, packet, review,
and finding bytes are independently revalidated; a prose statement that the
design was accepted cannot replace this object.
Adjudication state is the exact joined series-state value; its evidence is
nonnull exactly for AMBIGUOUS and equals that retained artifact.

Decision precedence is exact:

1. Terminal-rule status CONTRADICTION selects PARKED with reason
   `POST_FREEZE_CALIBRATION_CHANGE`.
2. Otherwise a WRONG SHAPE review or residual ordinal at least two selects
   PARKED with reason `REDESIGN_DEFAULT_SELECTED` unless one complete valid
   breaker override selects AUTHORIZE or, before r005, NEXT.
3. Otherwise r005 plus AMBIGUOUS selects PARKED with reason
   `AMBIGUOUS_WIRE_STATE`.
4. Otherwise nonclean r005 with positive round interface-change count selects
   PARKED with reason `ANALYZER_PATTERN_RECURRENCE`.
5. Otherwise nonclean r005 selects PARKED with reason
   `NONCLEAN_TERMINAL_R005`.
6. Otherwise CLEAR, both defect verdicts CLEAN, and every DESIGN finding
   NONBLOCKING selects AUTHORIZE with null next-round and parking fields.
7. The remaining r002 through r004 case selects NEXT with the exact immediate
   successor and null parking fields.

Every PARKED result has category exact `parked - gate defect`, null next round,
discarded panel, and fresh ADR-0482 preregistration required. NEXT never renders
r006.

`pontius-utility-bootstrap-design-disposition-publication-v1` has exactly
`disposition`, `disposition_artifact`, `disposition_byte_count`,
`disposition_sha256`, `publication`, `remote_observation`, and `schema`.
Disposition is the complete self-free object above; its canonical bytes equal
the artifact and reproduce the adjacent count and digest. Publication has stage
exact `RULE6_DESIGN_ROUND_DECISION_PUBLICATION`, null ordinal and manifest, and
contains exactly the disposition artifact, controller report, and controller
ledger line. Its commit descends from both review publications and preserves
their packet history. The outer remote observation equals the nested one.

`pontius-utility-bootstrap-design-authorization-v1` has exactly
`candidate_manifest_sha256`, `candidate_oid`, `controller_id`, `decision`,
`design_author_set`, `design_author_set_artifact`,
`design_author_set_byte_count`, `design_author_set_sha256`,
`design_disposition`, `design_disposition_artifact`,
`design_disposition_byte_count`, `design_disposition_publication`,
`design_disposition_publication_byte_count`,
`design_disposition_publication_sha256`, `design_disposition_sha256`,
`design_packet_publication`, `design_review_publications`,
`implementation_convergence_policy`,
`implementation_convergence_policy_artifact`,
`implementation_convergence_policy_byte_count`,
`implementation_convergence_policy_sha256`, `implementation_round`,
`implementation_task`, `retention_authority`,
`retention_authority_byte_count`, `retention_authority_sha256`, `schema`,
`series_state`, `series_state_artifact`, `series_state_byte_count`,
`series_state_sha256`, `workflow`, and `workflow_sha256`. Decision is exact
`AUTHORIZE_FREEZE_TOOLS_IMPLEMENTATION`; packet is one complete adopted-rule-6
design packet publication with stage exact `RULE6_DESIGN_PACKET_PUBLICATION`,
null ordinal, a nonnull packet manifest, and an artifact population exactly
covering the candidate tuple and manifest, six P paths, H `coverage.md`, the
complete bootstrap-series-state artifact, complete design-author set, every
authorship-evidence artifact, the standalone convergence-policy artifact, the
retained adopted workflow artifact, and packet instructions. The seven source
files each contain the sole canonical r005
terminal declaration; no separate Stage 0b counter or calibration JSON enters
this bootstrap packet. The author set and convergence-policy canonical artifact
bytes reproduce their adjacent positive counts and digests. Reviews are exactly the
two complete objects above in ordinal order and both nested receipts are CLEAN.
Each review's packet-publication digest equals the complete packet publication;
packet and review commits form the adopted rule-6 ancestry. The disposition is the complete object
above; its canonical artifact bytes, including the required final LF,
reproduce the adjacent positive count and digest, and its decision equals this
authorization. It is AUTHORIZE, has null next/parking fields, and its complete
publication wrapper reproduces the adjacent count and digest. Series state and
its triple equal the disposition, packet, and both reviews. The complete
convergence policy and its artifact bytes likewise
reproduce the adjacent count and digest; it is frozen in the design packet and
precedes every implementation candidate. Workflow
is the retained adopted `docs/workflow.md` artifact and its complete-byte digest
is exact `ab5202b170a5fd9c2cf1540aa198d4a82c742cb336134b0f9a8db944fd64f91a`.
The complete external-retention authority and its canonical count and digest
are controller-selected before this authorization and reproduce the pinned
service, producer, verifier, key, algorithm, namespace, genesis, and write-once
policy. They are immutable for the entire bootstrap and activated Stage 0b
lineage.
The external controller creates this object only after both reviews and before
the implementation brief. It contains no Stage 0b object, implementation
candidate, source projection, test, rehearsal, or utility-acceptance identity.
Implementation task and round are the external controller's exact future
implementation coordinates and are repeated by the start object and plan.

`pontius-utility-bootstrap-design-authorization-publication-v1` has exactly
`authorization`, `authorization_artifact`, `authorization_byte_count`,
`authorization_sha256`, `implementation_convergence_policy`,
`implementation_convergence_policy_artifact`,
`implementation_convergence_policy_byte_count`,
`implementation_convergence_policy_sha256`, `publication`,
`remote_observation`, and `schema`.
Authorization is the complete object above. Its canonical bytes, including its
required final LF, equal the artifact bytes and reproduce the positive count
and digest. Publication is one adopted-rule-6 publication with stage exact
`RULE6_DESIGN_AUTHORIZATION_PUBLICATION` containing exactly that authorization
artifact and the bound convergence-policy artifact; remote observation proves
its commit/ref exact. The outer remote observation equals the complete nested
publication observation. The publication's policy object, artifact, count, and
digest equal the nested authorization byte-for-byte. The implementation brief, packet, both
implementation review receipts, selector, controller authorization, bootstrap
evidence, and utility acceptance carry this same wrapper/count/digest.

`pontius-utility-bootstrap-implementation-start-v1` has exactly
`bootstrap_design_authorization_publication`,
`bootstrap_design_authorization_publication_byte_count`,
`bootstrap_design_authorization_publication_sha256`, `candidate_ref`,
`ceremonial_commit_message`, `ceremonial_commit_metadata`, `finalizer_id`,
`implementation_plan`, `implementation_plan_artifact`,
`implementation_plan_byte_count`, `implementation_plan_sha256`, `product_ref`,
`product_repository_id`, `retention_authority`,
`retention_authority_byte_count`, `retention_authority_sha256`, `review_tier`,
`reviewer_slots`, `round`, `schema`, `task`, `workflow`, and `workflow_sha256`. Task
and round equal the authorization's
`implementation_task` and `implementation_round` and the plan's task and round.
Finalizer ID is the controller-attested actor selected before start
serialization and repeated by the brief's sole exact `Finalizer:` declaration;
it is not inferred from Git author or committer metadata. Product repository is
exact `PONTIUS_SOURCE` and product ref is exact `refs/heads/master`. Candidate
ref is the full immutable P
implementation-candidate ref that the later temporary-index publication must
create. Review tier is exact `C`. A bootstrap implementation-reviewer-slot
object has exactly `ordinal` and `reviewer_id`; `reviewer_slots` contains
exactly two rows in ordinal-one, ordinal-two order. The reviewers are distinct
from one another, the finalizer, controller, design authors, utility authors,
and implementation authors.

`ceremonial_commit_message` is one nonempty printable-ASCII line followed by
exactly one LF. `ceremonial_commit_metadata` is one complete `commit_metadata`
object whose author and committer are both the finalizer's frozen Git
attribution. These values, rather than Git config, environment, clock, editor,
or porcelain defaults, are the sole message and metadata inputs to the later
ceremonial raw commit.
Plan `candidate_base_oid` is the sole P base. Plan `policy_sha256` equals the
authorization's `implementation_convergence_policy_sha256`. Wrapper, plan,
workflow, and their digests otherwise equal the accepted design authorization
and frozen implementation plan.
The retention-authority triple equals the design authorization byte-for-byte
and precedes start serialization and every publication observation.
Their canonical artifact bytes reproduce the adjacent positive counts and
digests. The start object contains no implementation candidate, packet, test,
review, source-projection, rehearsal, acceptance, publication, or identity of
itself.

`pontius-utility-bootstrap-implementation-start-publication-v1` has exactly
`implementation_brief`, `publication`, `remote_observation`, `schema`, `start`,
`start_artifact`, `start_byte_count`, and `start_sha256`. Start is the complete
object above; its canonical bytes equal the artifact bytes and reproduce the
adjacent positive count and digest. `implementation_brief` is an
`artifact_identity` whose bytes are the exact UTF-8/LF rendering below. Angle-
bracket tokens are replaced by their canonical scalar values; message drops
only its required terminal LF. Actor rows render the exact metadata fields
without JSON, locale, or display-name substitution.

```text
# Freeze-tools implementation start

Implementation start SHA-256: <start_sha256>
Design authorization SHA-256: <bootstrap_design_authorization_publication_sha256>
Implementation plan SHA-256: <implementation_plan_sha256>
Retention authority SHA-256: <retention_authority_sha256>
Task: <task>
Round: <round>
Candidate base OID: <implementation_plan.candidate_base_oid>
Candidate ref: <candidate_ref>
Tier: C
Reviewer 1: <reviewer_slots[0].reviewer_id>
Reviewer 2: <reviewer_slots[1].reviewer_id>
Finalizer: <finalizer_id>
Product repository: PONTIUS_SOURCE
Product ref: refs/heads/master
Ceremonial message: <ceremonial_commit_message without terminal LF>
Ceremonial author name: <ceremonial_commit_metadata.author.name>
Ceremonial author email: <ceremonial_commit_metadata.author.email>
Ceremonial author timestamp: <ceremonial_commit_metadata.author.timestamp>
Ceremonial author UTC offset: +0000
Ceremonial committer name: <ceremonial_commit_metadata.committer.name>
Ceremonial committer email: <ceremonial_commit_metadata.committer.email>
Ceremonial committer timestamp: <ceremonial_commit_metadata.committer.timestamp>
Ceremonial committer UTC offset: +0000
```

The closing code-fence line is followed by one LF and there is no suffix.
Publication has stage
exact `RULE6_IMPLEMENTATION_START_PUBLICATION`, null ordinal and manifest, and
artifact population exactly the start JSON, Markdown brief, implementation-plan
JSON, and path-budget-map JSON. Its commit descends from and preserves the
design-authorization publication. The outer remote observation equals its
nested publication observation. The P implementation candidate has parent
exactly the plan's P `candidate_base_oid`; adopted `candidate.json` remains its
unchanged nine-key object and makes no H ancestry or start-authoring claim.

`pontius-utility-bootstrap-implementation-start-link-v1` has exactly
`candidate_base_oid`, `candidate_manifest_sha256`, `candidate_oid`,
`candidate_ref`, `ceremonial_commit_message`, `ceremonial_commit_metadata`,
`finalizer_id`,
`implementation_start_publication`,
`implementation_start_publication_byte_count`,
`implementation_start_publication_sha256`, `product_ref`,
`product_repository_id`, `review_tier`, `reviewer_slots`, `round`, `schema`,
and `task`. The
complete H start wrapper's canonical bytes reproduce the adjacent count and
digest. Candidate base equals the plan; candidate tuple, task, and round equal
ordinary adopted `candidate.json` and its source manifest. The H implementation
packet descends from the observed H start publication, preserves its start and
brief bytes, and contains this link as a separate artifact beside unchanged
`candidate.json`. The candidate becomes admissible only through that post-start
H packet. This contract does not claim that a human could not author mutable or
unpublished P bytes earlier. Every later bootstrap carrier binds the link and
repeats the complete start wrapper, count, and digest. Finalizer and product
coordinates, candidate ref, Tier-C reviewer slots, and ceremonial message and
metadata equal the start object exactly.

`pontius-utility-bootstrap-publication-v1` has exactly `artifacts`,
`commit_oid`, `manifest_sha256`, `ordinal`, `ref`, `remote_observation`,
`repository_id`, `retention_authority`, `retention_authority_byte_count`,
`retention_authority_sha256`, `schema`, and `stage`. `artifacts` is a nonempty path-sorted
unique `artifact_identity` array. `manifest_sha256` is `sha256` or `null`;
`ordinal` is `ordinal` only for a review publication and is `null` otherwise.
`remote_observation` is the complete retained wrapper above; its nested core
repeats commit, ref, and repository exactly. The authority object reproduces
its adjacent positive count and digest; that digest equals the observation
wrapper and receipt. It equals the earliest complete bootstrap design-
authorization authority and every later start, controller, acceptance, and
activation carrier byte-for-byte. Stage is one of:

```text
TEMP_INDEX_CANDIDATE_PUBLICATION
RULE6_DESIGN_PACKET_PUBLICATION
RULE6_DESIGN_REVIEW_PUBLICATION
RULE6_DESIGN_ROUND_DECISION_PUBLICATION
RULE6_DESIGN_AUTHORIZATION_PUBLICATION
RULE6_IMPLEMENTATION_START_PUBLICATION
RULE6_UTILITY_ACCEPTANCE_PUBLICATION
RULE6_STAGE0B_ACTIVATION_PUBLICATION
RULE6_FREEZE_PACKET_PUBLICATION
RULE6_REVIEW_PUBLICATION
CEREMONIAL_INTEGRATION_RECORD_PUBLICATION
DURABLE_DISPOSITION
```

Stage discriminants close repository, ref, ordinal, and manifest shape:

In this table, `P/candidate` means exact `PONTIUS_SOURCE` and the derived
candidate ref. `H/main` means exact `PONTIUS_HANDOFFS` and
`refs/heads/main`. Manifest `candidate`, `packet`, or `review` means the
corresponding nonnull manifest digest; a dash means null.

| Stage | Repository/ref | Ordinal | Manifest |
| --- | --- | --- | --- |
| `TEMP_INDEX_CANDIDATE_PUBLICATION` | `P/candidate` | null | candidate |
| `RULE6_DESIGN_PACKET_PUBLICATION` | `H/main` | null | packet |
| `RULE6_DESIGN_REVIEW_PUBLICATION` | `H/main` | one or two | review |
| `RULE6_DESIGN_ROUND_DECISION_PUBLICATION` | `H/main` | null | - |
| `RULE6_DESIGN_AUTHORIZATION_PUBLICATION` | `H/main` | null | - |
| `RULE6_IMPLEMENTATION_START_PUBLICATION` | `H/main` | null | - |
| `RULE6_FREEZE_PACKET_PUBLICATION` | `H/main` | null | packet |
| `RULE6_REVIEW_PUBLICATION` | `H/main` | one or two | review |
| `CEREMONIAL_INTEGRATION_RECORD_PUBLICATION` | `H/main` | null | - |
| `DURABLE_DISPOSITION` | `H/main` | null | - |
| `RULE6_UTILITY_ACCEPTANCE_PUBLICATION` | `H/main` | null | - |
| `RULE6_STAGE0B_ACTIVATION_PUBLICATION` | `H/main` | null | - |

Every H publication is a one-parent direct child of its freshly fetched H main
predecessor and preserves all prior bytes except its declared append. Within a
bootstrap series, required task ancestry is design packet, design reviews in
ordinal order, round decision, design authorization, implementation start,
implementation packet, implementation reviews in ordinal order, ceremonial
integration in P, its H record publication, durable disposition, utility
acceptance, then any later Stage 0b
activation. Unrelated-task commits may intervene only as preserved H main
predecessors. Each specialized wrapper fixes its exact artifact population.
The complete remote observation repeats this repository, ref, and commit and
uses the typed post-push query receipt above. A different repository, ref,
ordinal, manifest shape, missing ancestor, rewritten prior artifact, or generic
publication substituted for a specialized wrapper refuses.

`pontius-utility-bootstrap-controller-authorization-v1` has exactly
`artifacts`, `bootstrap_design_authorization_publication`,
`bootstrap_design_authorization_publication_byte_count`,
`bootstrap_design_authorization_publication_sha256`, `candidate_ref`,
`ceremonial_commit_message`, `ceremonial_commit_metadata`, `controller_id`,
`finalizer_id`, `https_rehearsal_evidence`,
`implementation_convergence_receipt`,
`implementation_convergence_receipt_byte_count`,
`implementation_convergence_receipt_sha256`, `implementation_plan`,
`implementation_plan_artifact`, `implementation_plan_byte_count`,
`implementation_plan_sha256`, `implementation_start_link`,
`implementation_start_link_artifact`, `implementation_start_link_byte_count`,
`implementation_start_link_sha256`, `implementation_start_publication`,
`implementation_start_publication_byte_count`,
`implementation_start_publication_sha256`, `implementation_tests`,
`implementation_tests_sha256`,
`product_ref`, `product_repository_id`, `retention_authority`,
`retention_authority_byte_count`, `retention_authority_sha256`, `review_tier`,
`reviewer_slots`, and `schema`.
`controller_id` is a
`reviewer_id`. `artifacts` is a nonempty path-sorted unique
`artifact_identity` array whose complete population is fixed by the accepted
bootstrap plan. `https_rehearsal_evidence` is the complete rehearsal-result
evidence row. The artifacts parse and bind the exact candidate publication,
packet publication, two review publications, complete required-test evidence,
schemas, plan, four source projections, and that exact result artifact. Its
selector, campaign, and source-set identities reproduce the nested result set.
`implementation_tests` is the complete four-row required-test-evidence array in
plan order. Its aggregate digest hashes the concatenation of each strict
canonical row plus LF and equals the rehearsal selector, bootstrap evidence,
controller disposition, and acceptance authority. Every row is PASS and its
required-test-row digest, selector, and argv equal the corresponding plan row.
Candidate ref, ceremonial message and metadata, finalizer, product coordinates,
review tier, and reviewer slots equal the implementation start and link. The
two review publications and their nested receipts use exactly those reviewer
slots and ordinals.
`bootstrap_design_authorization_publication` is the complete wrapper above; its
adjacent count and digest reproduce its canonical bytes and equal the selector,
both review receipts, bootstrap evidence, and utility acceptance byte-for-byte.
The complete retention-authority triple equals the implementation start and
bootstrap design authorization; no construction or publication may select it
from a receipt.
This object is an authorization
record, not a Git publication: it contains no commit, ref, repository, remote
observation, ceremonial result, or durable-disposition coordinate.

`pontius-utility-bootstrap-implementation-review-adjudication-v1` has exactly
`design_justification`, `design_justification_byte_count`,
`design_justification_sha256`, `design_verdict`, `review_receipt_sha256`,
`reviewer_id`, and `reviewer_ordinal`. Rows occur in ordinal order and
bind the two complete implementation review receipts. Justification fields are
all null for SOUND and all nonnull otherwise; retained bytes reproduce the
adjacent count and digest and explain why the exact STRAINED or WRONG SHAPE
finding does or does not block ceremonial integration.

`pontius-utility-bootstrap-implementation-controller-disposition-v1` has exactly
`bootstrap_design_authorization_publication_sha256`,
`candidate_ref`, `ceremonial_commit_message`, `ceremonial_commit_metadata`,
`controller_authorization_sha256`, `controller_id`, `decision`,
`durable_disposition_commit_message`, `durable_disposition_commit_metadata`,
`finalizer_id`,
`https_rehearsal_evidence_sha256`, `implementation_candidate_manifest_sha256`,
`implementation_candidate_oid`, `implementation_convergence_receipt_sha256`,
`implementation_plan_sha256`, `implementation_start_link_sha256`,
`implementation_start_publication_sha256`, `implementation_test_sha256s`,
`implementation_tests_sha256`, `integration_record_commit_message`,
`integration_record_commit_metadata`,
`product_ref`, `product_repository_id`, `review_adjudications`, `review_tier`,
`reviewer_slots`, `schema`, `schemas_sha256`,
`source_projection_set_sha256`, and `verdict_date`. Decision is exact
`AUTHORIZE_CEREMONIAL_INTEGRATION`. Candidate, authorization, start, link, plan,
convergence PASS, tests, source projections, schemas, HTTPS rehearsal, and both
reviews equal the complete controller-authorization and selector gates.
Candidate ref, ceremonial message and metadata, finalizer, product coordinates,
review tier, and reviewer slots equal the start, link, and controller
authorization. Both
defect verdicts are CLEAN. Each design verdict is SOUND or has one complete
adjudication row whose justification explicitly accepts the risk; a rejected or
missing justification makes this disposition impossible. The controller is
absent from implementation authors and reviewers. This self-free object names
no ceremonial target, later remote observation, durable disposition,
acceptance, publication, or identity of itself.
The two H messages are distinct nonempty printable-ASCII lines with one final
LF. Their complete metadata objects use the controller's frozen Git attribution
and are the sole message/metadata inputs for the record and durable-disposition
raw commits; Git config, clock, editor, and porcelain defaults are forbidden.

`implementation_test_sha256s` is the four-element array of complete canonical
required-test-evidence row digests in plan order. `implementation_tests_sha256`
is the aggregate digest of those same four LF-terminated row encodings. Both
projections equal the complete array in controller authorization, rehearsal
selector, bootstrap evidence, and acceptance; a subset, permutation, duplicate,
label-only row, or independently supplied digest refuses.

`pontius-utility-bootstrap-product-ref-transition-v1` has exactly `after_oid`,
`before_oid`, `expected_old_oid`, `new_oid`, `ref`, `repository_id`, `result`,
and `schema`. Repository is exact `PONTIUS_SOURCE`, ref is exact
`refs/heads/master`, result is exact `UPDATED`, before and expected-old are
equal, and after and new are equal. The transition uses compare-and-swap; a
missing, different, multiply updated, or unobserved ref state refuses.

`pontius-utility-bootstrap-ceremonial-commit-build-receipt-v1` has exactly
`candidate_oid`, `candidate_tree_oid`, `ceremonial_commit_input`,
`ceremonial_commit_input_byte_count`, `ceremonial_commit_input_sha256`,
`construction_ordering`, `construction_ordering_byte_count`,
`construction_ordering_sha256`,
`independently_derived_commit_oid`, `previous_product_tip_oid`,
`result_commit_oid`, `schema`, `stored_commit_oid`,
`stored_commit_payload_byte_count`, `stored_commit_payload_sha256`,
`stored_parent_oids`, and `stored_tree_oid`.

`ceremonial_commit_input` is the complete `pontius-raw-commit-input-v1` object.
Its kind is exact `UTILITY_CEREMONIAL_INTEGRATION`; its message and metadata
equal the implementation start, start link, controller authorization, and
controller disposition; its tree is the independently parsed reviewed
candidate tree; and its parents array contains only the freshly observed
`previous_product_tip_oid`. Candidate OID identifies the reviewed Stage-2
commit and is not the result commit.

`construction_ordering` is the complete pre-push ordering object above and
reproduces the adjacent positive count and digest. Its ceremonial input digest
equals this receipt, and its complete authorization and disposition bindings
equal the accepted controller objects. Construction begins only after the
transcript's third event.

The input's canonical bytes reproduce its adjacent positive count and digest.
The raw commit payload rendered from that input reproduces the stored payload
count and digest. The independently computed Git OID, `git hash-object` returned
and stored OID, strictly reparsed stored-commit OID, and `result_commit_oid` are
all equal and are distinct from `candidate_oid`. The strictly parsed stored
tree and complete parent array equal `candidate_tree_oid` and the sole fresh
product predecessor. Any config-derived metadata, different tree, extra parent,
candidate/result OID equality, unstored object, independent-OID mismatch, or
stored-byte mismatch refuses before push.

`pontius-utility-bootstrap-product-integration-result-v1` has exactly
`candidate_manifest_sha256`, `candidate_oid`, `candidate_ref`,
`candidate_tree_oid`, `ceremonial_commit_build_receipt`,
`ceremonial_commit_build_receipt_artifact`,
`ceremonial_commit_build_receipt_byte_count`,
`ceremonial_commit_build_receipt_sha256`, `ceremonial_commit_message`,
`ceremonial_commit_metadata`,
`controller_authorization_sha256`, `controller_disposition_sha256`,
`finalizer_id`,
`post_push_ordering_artifact`, `post_push_ordering_byte_count`,
`post_push_ordering_sha256`,
`pre_push_ordering`, `pre_push_ordering_artifact`,
`pre_push_ordering_byte_count`, `pre_push_ordering_sha256`,
`pre_push_remote_observation`,
`previous_product_tip_oid`, `product_ref`,
`publication_push_receipt`, `publication_push_receipt_artifact`,
`publication_push_receipt_byte_count`, `publication_push_receipt_sha256`,
`ref_transition`, `remote_observation`, `repository_id`, `result_commit_oid`,
`result_parent_oids`, `result_tree_oid`, `schema`, and `topology`. Repository is
exact `PONTIUS_SOURCE`, product ref is exact `refs/heads/master`, and topology
is exact `DISTINCT_CEREMONIAL_FAST_FORWARD`. Candidate ref, ceremonial message,
and ceremonial metadata equal the start, link, authorization, disposition, and
complete build receipt. Previous product tip equals the implementation plan's
candidate base and the fresh pre-push observation of P master. That observation
is the complete `pontius-utility-bootstrap-pre-push-remote-observation-v1`,
targets the result's repository and ref, and proves the exact predecessor.
Pre-push ordering is the complete self-free ordering object above; its
canonical bytes equal its artifact and reproduce the adjacent count and
digest. It binds the observation's query-receipt digest before the build
receipt's complete construction-ordering object. That object proves the query,
then complete authorizing disposition, then ceremonial-input authorization
occurred before any input serialization, raw rendering, object write, or push.
Its authorization, disposition, controller, decision, and ceremonial-input
digest equal this result and build receipt byte-for-byte.
Post-push ordering is the complete ordering object nested in the remote
observation's query receipt. Its canonical bytes equal the declared artifact
and reproduce the adjacent positive count and digest.
Result commit is distinct from candidate OID. The complete build receipt's
canonical bytes equal its artifact and reproduce its adjacent positive count
and digest. It proves that its stored
raw commit has the independently parsed candidate tree, exactly the sole
previous product tip as parent, and result OID equal to the independently
derived and stored ceremonial commit OID. Candidate manifest and tree
reconstruct the reviewed candidate without an added, missing, or changed byte.
Result tree and complete result-parent array equal the receipt's stored tree and
parent array exactly.
Ref transition is complete and moves only the product ref from previous tip to
the distinct result commit.

Controller-authorization and controller-disposition digests equal the complete
typed upstream objects; finalizer ID and product coordinates equal the start,
link, authorization, and disposition. Finalizer is the controller-attested
actor who built the bound raw commit and performed the ref transition and push;
its frozen Git author and committer bytes corroborate but do not establish that
actor identity. The complete push receipt's canonical bytes
equal its artifact and reproduce the adjacent positive count and digest. Its
controller, repository, ref, and target commit equal this result and it proves
one successful compare-and-swap push. The fresh complete remote observation
is the complete `pontius-utility-bootstrap-post-push-remote-observation-v1`;
its nested query receipt uses a post-push typed ordering receipt and proves
that exact product ref at the result commit. This object contains no H record
publication, durable
disposition, utility acceptance, artifact identity of itself, or digest of
itself.

`pontius-utility-bootstrap-integration-record-publication-v1` has exactly
`commit_input`, `commit_input_byte_count`, `commit_input_sha256`,
`controller_disposition`, `controller_disposition_artifact`,
`controller_disposition_byte_count`, `controller_disposition_sha256`,
`integration_result`, `integration_result_artifact`,
`integration_result_byte_count`, `integration_result_sha256`, `publication`,
`remote_observation`, and `schema`. The complete disposition and product
integration result canonical bytes equal their artifacts and reproduce their
adjacent positive counts and digests. Their candidate, controller,
authorization, finalizer, product coordinate, plan, test, convergence, and
rehearsal identities agree exactly. Publication is a complete bootstrap
publication with stage `CEREMONIAL_INTEGRATION_RECORD_PUBLICATION`, null
ordinal and manifest. Its exact path-sorted artifacts are the controller-
disposition JSON, ceremonial-build-receipt JSON, pre-push-query-receipt JSON,
pre-push-ordering JSON, publication-push-receipt JSON, post-push-ordering JSON,
post-push-query-receipt JSON, and product-integration-result JSON. Every nested
artifact identity in the result equals its matching publication artifact; no
receipt or ordering artifact remains unanchored. The three Git receipts embed
their complete bounded stdout and stderr objects, so the exact eight-document
population omits no separate output artifact. All eight documents are self-free
and contain no H commit or publication identity, so the H commit can
be derived without a content cycle. It is a one-parent H-main append after both
implementation review publications. Its commit is only the H record; it is
never equated to the P product-integration commit. The outer remote observation
equals the publication observation and proves the H record exact.
Commit input is complete `pontius-raw-commit-input-v1`, reproduces its adjacent
count and digest, has kind exact `UTILITY_CEREMONIAL_INTEGRATION_RECORD`, uses
the controller-disposition record message and metadata, names the exact artifact
tree, and has the freshly observed H-main predecessor as sole parent. Its
independently derived and stored OID equals the publication commit.

`pontius-utility-bootstrap-durable-disposition-v1` has exactly
`controller_disposition`, `controller_disposition_artifact`,
`controller_disposition_byte_count`, `controller_disposition_sha256`,
`controller_id`, `decision`, `integration_record_sha256`,
`integration_result_sha256`, `schema`, and `verdict_date`. The complete
controller disposition canonical bytes equal its artifact bytes and reproduce
the adjacent positive count and digest. Decision is exact
`UTILITY_IMPLEMENTATION_INTEGRATED`. Controller equals the authorization and
controller disposition. The two integration digests name the complete P result
and H record-publication wrapper above. The object is self-free and contains no
own artifact, publication, observation, acceptance, count, or digest.

`pontius-utility-bootstrap-durable-disposition-publication-v1` has exactly
`commit_input`, `commit_input_byte_count`, `commit_input_sha256`,
`disposition`, `disposition_artifact`, `disposition_byte_count`,
`disposition_report_artifact`, `disposition_sha256`, `publication`,
`remote_observation`, and `schema`. Disposition canonical bytes equal the JSON
artifact and reproduce the adjacent positive count and digest. The Markdown
report is the strict deterministic rendering of that complete object and has
no free-form suffix. Publication has stage exact `DURABLE_DISPOSITION`, null
ordinal and manifest, and artifacts exactly the JSON and Markdown report in
path order. Its H commit is a one-parent descendant of the integration-record
publication, preserves that record, and never substitutes for the P product
integration. The outer remote observation equals the publication observation.
Commit input is complete `pontius-raw-commit-input-v1`, reproduces its adjacent
count and digest, has kind exact `UTILITY_BOOTSTRAP_DURABLE_DISPOSITION`, uses
the controller-disposition durable message and metadata, names the exact
preserving tree, and has the freshly observed H-main predecessor as sole parent.
Its history contains the exact integration-record commit, and its independently
derived and stored OID equals the publication commit.

`pontius-role-review-receipt-v1` has exactly `capability_grammar_read`,
`downstream_candidate_artifacts_read`, `role`, `source_population_read`,
`source_projection_byte_count`, and `source_projection_sha256`. The two read
fields are exact `true`; downstream-candidate-artifacts-read is exact `false`.
Four rows always occur in `runtime-owner`, `builder`, `publisher`, `integrator`
order and reconstruct one complete `pontius-source-projection-set-v1`.

`pontius-utility-bootstrap-review-receipt-v1` has exactly:

| Key | Type |
| --- | --- |
| `adopted_bootstrap_brief` | `artifact_identity` |
| `amendment_sha256` | `sha256` |
| `candidate_manifest_sha256` | `sha256` |
| `candidate_oid` | `oid` |
| `cold_input_commit_oid` | `oid` |
| `cold_input_manifest_sha256` | `sha256` |
| `defect_verdict` | `defect_verdict` |
| `design_justification_sha256` | `sha256` |
| `design_verdict` | `design_verdict` |
| `ledger_line` | `artifact_identity` |
| `implementation_plan` | complete freeze-tools implementation-plan object |
| `implementation_plan_artifact` | `artifact_identity` |
| `implementation_plan_byte_count` | `positive_count` |
| `implementation_plan_sha256` | `sha256` |
| `implementation_start_publication` | complete implementation-start-publication object |
| `implementation_start_publication_byte_count` | `positive_count` |
| `implementation_start_publication_sha256` | `sha256` |
| `implementation_start_link` | complete implementation-start-link object |
| `implementation_start_link_artifact` | `artifact_identity` |
| `implementation_start_link_byte_count` | `positive_count` |
| `implementation_start_link_sha256` | `sha256` |
| `plan_sha256` | `sha256` |
| `report` | `artifact_identity` |
| `reviewer_id` | `reviewer_id` |
| `reviewer_ordinal` | `ordinal` |
| `role_receipts` | exactly four `pontius-role-review-receipt-v1` objects |
| `round` | `round` |
| `schema` | exact schema literal |
| `schemas_sha256` | `sha256` |
| `source_projection_set_byte_count` | `positive_count` |
| `source_projection_set_sha256` | `sha256` |
| `bootstrap_design_authorization_publication` | complete bootstrap authorization wrapper |
| `bootstrap_design_authorization_publication_byte_count` | `positive_count` |
| `bootstrap_design_authorization_publication_sha256` | `sha256` |
| `task` | `task` |
| `utility_author_set_byte_count` | `positive_count` |
| `utility_author_set_sha256` | `sha256` |
| `verdict_date` | `date` |
| `workflow_sha256` | `sha256` |

The receipt is downstream of the published bootstrap design authorization,
frozen implementation candidate, and rule-6 implementation packet but upstream
of utility acceptance.
Its cold-input pair is that packet's
commit and manifest. Its four role rows reconstruct the exact reviewed source-
projection set; every candidate, packet, workflow, amendment, schema, plan,
projection, and utility-author identity equals the adopted bootstrap objects.
Its complete bootstrap-design-authorization publication, count, and digest
equal the implementation brief, packet, other review, rehearsal selector,
controller authorization, bootstrap evidence, and acceptance authority. The
nested authorization decision is exact
`AUTHORIZE_FREEZE_TOOLS_IMPLEMENTATION`.
It contains no raw-object-v5 preregistration, later reviewer-author set,
acceptance authority, ceremonial integration, or disposition identity.
Its report prefix, design-justification digest, and issuer ledger-line rendering
use section 11.2 byte-for-byte with this receipt's fields. Thus a rehearsal
review-output build can verify the already frozen bootstrap package without
inventing a second report or ledger grammar.

`pontius-utility-bootstrap-review-evidence-v1` has exactly `publication` and
`receipt`. Publication is a complete
`pontius-utility-bootstrap-publication-v1` with stage
`RULE6_REVIEW_PUBLICATION`; ordinal equals the receipt ordinal. Its artifacts
are exactly the report, receipt JSON, and issuer-authored ledger line, sorted by
path. The manifest digest is recomputed from the three self-excluding artifact
rows under the accepted bootstrap grammar. The receipt artifact bytes parse
byte-for-byte as the complete nested receipt; report and ledger artifacts equal
the identities in that receipt. Candidate, packet parent, reviewer, ordinal,
manifest, ref, commit, projection set, and author set all agree.

The bootstrap report and ledger obey section 11.2's exact report-prefix,
design-justification, and one-physical-line equations. References there to the
later cold input mean this receipt's rule-6 implementation packet. A report,
receipt, ledger, or manifest byte change creates a new review publication.

`pontius-utility-bootstrap-evidence-v1` has exactly:

| Key | Type |
| --- | --- |
| `adopted_bootstrap_brief` | `artifact_identity` |
| `candidate_publication` | complete bootstrap-publication object |
| `ceremonial_integration` | complete product-integration-result object |
| `ceremonial_integration_artifact` | `artifact_identity` |
| `ceremonial_integration_byte_count` | `positive_count` |
| `ceremonial_integration_record_publication` | complete integration-record-publication object |
| `ceremonial_integration_sha256` | `sha256` |
| `controller_authorization` | complete bootstrap-controller-authorization object |
| `controller_disposition` | complete implementation-controller-disposition object |
| `controller_disposition_artifact` | `artifact_identity` |
| `controller_disposition_byte_count` | `positive_count` |
| `controller_disposition_sha256` | `sha256` |
| `controller_id` | `reviewer_id` |
| `durable_disposition` | complete durable-disposition-publication object |
| `https_rehearsal_evidence` | rehearsal-result evidence row |
| `implementation_convergence_receipt` | complete convergence-receipt object |
| `implementation_convergence_receipt_byte_count` | `positive_count` |
| `implementation_convergence_receipt_sha256` | `sha256` |
| `implementation_plan` | complete freeze-tools implementation-plan object |
| `implementation_plan_artifact` | `artifact_identity` |
| `implementation_plan_byte_count` | `positive_count` |
| `implementation_plan_sha256` | `sha256` |
| `implementation_start_publication` | complete implementation-start-publication object |
| `implementation_start_publication_byte_count` | `positive_count` |
| `implementation_start_publication_sha256` | `sha256` |
| `implementation_start_link` | complete implementation-start-link object |
| `implementation_start_link_artifact` | `artifact_identity` |
| `implementation_start_link_byte_count` | `positive_count` |
| `implementation_start_link_sha256` | `sha256` |
| `implementation_tests` | exactly four required-test-evidence objects |
| `implementation_tests_sha256` | `sha256` |
| `packet_publication` | complete bootstrap-publication object |
| `review_publications` | exactly two bootstrap-review-evidence objects |
| `retention_authority` | complete external-retention-authority object |
| `retention_authority_byte_count` | `positive_count` |
| `retention_authority_sha256` | `sha256` |
| `schema` | exact schema literal |
| `bootstrap_design_authorization_publication` | complete bootstrap authorization wrapper |
| `bootstrap_design_authorization_publication_byte_count` | `positive_count` |
| `bootstrap_design_authorization_publication_sha256` | `sha256` |

The named fields close the publication discriminants exactly:

The controller-disposition artifact bytes parse as the complete nested typed
disposition, including its exact key population, and reproduce the adjacent
positive byte count and SHA-256. The same object and artifact triple are byte-
identical to the integration-record publication, durable disposition,
ceremonial integration's disposition digest, and utility acceptance.
`controller_id` equals the complete controller
authorization, controller disposition, integration-record disposition, durable
disposition, and every nested controller coordinate. A malformed, opaque,
count-only, digest-only, or different-controller disposition refuses.

- `candidate_publication`: stage `TEMP_INDEX_CANDIDATE_PUBLICATION`, ordinal
  null, and the exact candidate-manifest digest. Its artifacts are exactly the
  complete path-sorted artifact rows covered by that manifest, with no generic
  evidence or H packet artifact. Its ordinary adopted
  `candidate.json` has exactly the unchanged nine workflow keys and its P commit
  parent is the implementation plan's P base; it contains no H start field.
- `packet_publication`: stage `RULE6_FREEZE_PACKET_PUBLICATION`, ordinal null,
  and the exact freeze-packet manifest digest. Its H commit descends from the
  observed H implementation-start publication and its exact packet artifact
  population is adopted `candidate.json`, candidate manifest, handoff,
  implementation-start-link JSON, implementation-plan JSON, path-budget-map
  JSON, and declared static review inputs. Link bytes parse as the complete
  nested `implementation_start_link` and reproduce its adjacent artifact, count,
  and digest.
- Each `review_publications[].publication`: stage `RULE6_REVIEW_PUBLICATION`,
  ordinal exactly `1` then `2` in array order, and its exact review-package
  manifest digest.
- `ceremonial_integration`: the complete P product-integration result above.
  Its canonical bytes equal its artifact and reproduce the adjacent positive
  count and digest.
- `ceremonial_integration_record_publication`: the complete specialized H
  record wrapper above. Its nested publication stage is
  `CEREMONIAL_INTEGRATION_RECORD_PUBLICATION`, with null ordinal and manifest.
- `durable_disposition`: the complete specialized H disposition wrapper above;
  its nested publication stage is `DURABLE_DISPOSITION`, with null ordinal and
  manifest.

Every publication's complete remote-observation tuple repeats its own commit,
ref, and repository fields exactly. A swapped stage, missing or invented
manifest digest, wrong review ordinal, or field-to-stage mismatch refuses.

Every selector, implementation review, controller authorization, bootstrap
evidence, and acceptance object reconstructs the complete canonical start link
from its P candidate/base, task/round, and start-publication wrapper. Its nested
link, artifact bytes, count, and digest are byte-identical to the exact packet
artifact. A packet without the link, a link inside P `candidate.json`, or any
cross-repository parent claim refuses.

The retention-authority object, count, and digest are byte-identical across the
design authorization, implementation start, controller authorization,
bootstrap evidence, utility acceptance, and later Stage 0b activation. Every
generic or Stage 0b observation wrapper and receipt repeats that digest; the
verifier resolves the complete pinned object only from these upstream carriers.

Every `adopted_bootstrap_brief` in the rehearsal selector, both implementation
review receipts, bootstrap evidence, and utility acceptance is byte-identical
to the `implementation_brief` artifact in the complete start publication and
reproduces its exact byte count and SHA-256. A separately written summary,
earlier design brief, path-only match, or digest without the complete bytes
refuses.

The logical gate order is bootstrap brief, temporary-index candidate
publication, rule-6 packet publication, two independent rule-6 review
publications, all plan-required tests, the exact real-HTTPS rehearsal,
controller authorization, the implementation-controller disposition with exact
decision `AUTHORIZE_CEREMONIAL_INTEGRATION`, P ceremonial integration and its
fresh P remote observation, H integration-record publication, durable
disposition, utility-acceptance publication, and external terminal-observation
retention for that acceptance observation.
The bootstrap brief and every later gate repeat the exact upstream
bootstrap-design-authorization publication. It precedes the implementation
candidate and cannot depend on any implementation or rehearsal result.
Review publication rows occur in ordinal order and have the packet commit as
their adopted cold parent. Their nested receipts are complete and byte-bound as
specified above. Candidate, packet, and review fields equal their
historical manifests, commits, refs, and artifact trees. Test rows are complete
for the accepted plan.

The controller-authorization artifacts bind the exact candidate, packet,
reviews, tests, HTTPS rehearsal, schemas, plan, and source projections. Its
complete `https_rehearsal_evidence` row equals the bootstrap-evidence and later
utility-acceptance fields byte-for-byte. The ceremonial-
integration result binds the authorization and controller-disposition digests,
the exact reviewed P candidate tree in a distinct finalizer-authored raw commit
whose sole parent is the freshly observed P base, the typed build receipt, the
compare-and-swap push receipt, and the fresh post-push P remote observation.
The H integration-record publication stores that complete result without being
equated to the P commit. The durable-disposition commit and artifacts bind
both. The authorization cannot name that later target or observation. Every
commit/ref/object relation and every artifact byte is
independently revalidated; an opaque label or unparsed artifact is insufficient.
The evidence object contains no later utility-acceptance identity and no
per-round raw-object-v5 preregistration.

`pontius-utility-acceptance-authority-v1` is produced only through the adopted
temporary-index, direct-Git, and packet-rule-6 bootstrap. It has exactly:

| Key | Type |
| --- | --- |
| `bootstrap_evidence` | complete `pontius-utility-bootstrap-evidence-v1` object |
| `bootstrap_evidence_byte_count` | `positive_count` |
| `bootstrap_evidence_sha256` | `sha256` |
| `controller_disposition` | complete implementation-controller-disposition object |
| `controller_disposition_artifact` | `artifact_identity` |
| `controller_disposition_byte_count` | `positive_count` |
| `controller_disposition_sha256` | `sha256` |
| `controller_id` | `reviewer_id` |
| `implementation_candidate_manifest_sha256` | `sha256` |
| `implementation_candidate_oid` | `oid` |
| `implementation_convergence_receipt` | complete convergence-receipt object |
| `implementation_convergence_receipt_byte_count` | `positive_count` |
| `implementation_convergence_receipt_sha256` | `sha256` |
| `implementation_plan` | complete freeze-tools implementation-plan object |
| `implementation_plan_artifact` | `artifact_identity` |
| `implementation_plan_byte_count` | `positive_count` |
| `implementation_plan_sha256` | `sha256` |
| `implementation_start_publication` | complete implementation-start-publication object |
| `implementation_start_publication_byte_count` | `positive_count` |
| `implementation_start_publication_sha256` | `sha256` |
| `implementation_start_link` | complete implementation-start-link object |
| `implementation_start_link_artifact` | `artifact_identity` |
| `implementation_start_link_byte_count` | `positive_count` |
| `implementation_start_link_sha256` | `sha256` |
| `implementation_tests` | exactly four required-test-evidence objects |
| `implementation_tests_sha256` | `sha256` |
| `plan_sha256` | `sha256` |
| `retention_authority` | complete external-retention-authority object |
| `retention_authority_byte_count` | `positive_count` |
| `retention_authority_sha256` | `sha256` |
| `round` | `round` |
| `schema` | exact schema literal |
| `schemas_sha256` | `sha256` |
| `source_projection_set_byte_count` | `positive_count` |
| `source_projection_set_sha256` | `sha256` |
| `bootstrap_design_authorization_publication` | complete bootstrap authorization wrapper |
| `bootstrap_design_authorization_publication_byte_count` | `positive_count` |
| `bootstrap_design_authorization_publication_sha256` | `sha256` |
| `task` | `task` |
| `utility_author_set` | complete `pontius-utility-author-set-v1` object |
| `utility_author_set_byte_count` | `positive_count` |
| `utility_author_set_sha256` | `sha256` |
| `https_rehearsal_evidence` | rehearsal-result evidence row |

The acceptance controller ID equals bootstrap evidence, controller
authorization, controller disposition, ceremonial integration's bound
authorization/disposition, integration-record publication, and durable
disposition. Its complete controller-disposition object and artifact/count/
digest triple are byte-identical to bootstrap evidence and reparsed from the
retained artifact before acceptance. No caller scalar, matching digest without
bytes, or controller substitution can satisfy this equality.

Across the candidate record, implementation packet, selector, both review
receipts, controller authorization, bootstrap evidence, and acceptance
authority, every implementation-start-publication wrapper, count, and digest is
byte-identical and equals the observed H start publication. Every
`implementation_plan` copy is byte-identical; its artifact
bytes parse as that object and reproduce the adjacent count and digest. Every
embedded convergence receipt in the selector, controller authorization,
bootstrap evidence, and acceptance authority repeats the same complete plan,
map, policy,
candidate OID and manifest, and source-projection-set digest. Receipt canonical
bytes reproduce each adjacent count and digest and are byte-identical across all
carriers. Receipt status and spike status are exact PASS, every class-total row
is PASS, and the attempt history stops at its first all-pass lifecycle. The
receipt policy equals the complete policy inside the bootstrap design
authorization publication. A PARK receipt, mismatched plan/map/policy,
post-candidate reclassification, or carrier-only digest cannot enter controller
authorization or utility acceptance.

The two implementation reviews are exactly the complete nested bootstrap-
review-evidence objects in `bootstrap_evidence.review_publications`. Their
reviewers are distinct and absent from `utility_author_set.authors`; each
receipt carries all four role receipts and reconstructs the same exact source-
projection set. Both defect verdicts are `CLEAN`. Each design verdict is
`SOUND`, or its exact non-SOUND justification is explicitly resolved by the
bound controller disposition. There is no second, weaker review-row projection.
An evidence row has exactly:

| Key | Type |
| --- | --- |
| `artifact` | `artifact_identity` |
| `commit_oid` | `oid` |
| `label` | frozen evidence-label literal |
| `ref` | full ref allowed by the accepted plan |
| `repository_id` | frozen repository-id literal |

Evidence labels match `[A-Z][A-Z0-9_]{0,63}` and repository IDs match
`[a-z0-9][a-z0-9._-]{0,63}`; the accepted plan lists every allowed value. The
full ref, commit, path, blob OID, byte count, and SHA-256 bind the retained
evidence without copying it into the handoff packet.

`pontius-utility-post-case-server-capability-v1` is controller-only and has
exactly `after_authority_evidence_sha256`, `campaign_sha256`, `case_id`,
`observation`, `route_selector_sha256`, and `schema`. `observation` is a complete
`pontius-server-capability-observation-v1` produced by a fresh capability probe
after the case's final authority envelope. Its endpoint and repository equal the
selector's pre-rehearsal observation; its complete observed class and class
digest equal both pre observations, the campaign, and paired table rows. Every
fact source is a newly retained post-case artifact and differs from the
selector's pre-case fact sources. The wrapper binds the final step's exact
authority-evidence-row digest: `after_authority_evidence_sha256` is SHA-256 of
the complete final step's canonical `authority_evidence` row bytes plus one LF.
The row is the last ordered step of this exact `case_id`; its artifact digest or
envelope bytes alone cannot substitute. Thus a pre-case observation, nonfinal
step, or another case's probe cannot satisfy it. It enters no selector,
authorization, or dispatch.

`pontius-utility-https-rehearsal-result-set-v1` is downstream of the rehearsal
selector and has exactly `campaign_sha256`, `case_results`,
`derived_input_contract_set_sha256`,
`pre_production_server_capability_sha256`,
`pre_rehearsal_server_capability_sha256`, `rehearsal_fixture_set_sha256`,
`route_selector_sha256`, `schema`,
`server_capability_class_sha256`, and `source_projection_set_sha256`. Both
capability-observation digests name the selector's complete objects; their
derived class digests equal each other, the paired endpoint rows, campaign, and
this root. The derived-input-contract-set digest names the selector's complete
object. Case results occur in the campaign's exact case order. A case result
has exactly `case_id`, `observed_terminal_class`,
`post_rehearsal_server_capability`, and `steps`. Its post-case field is the
complete wrapper above. The wrapper's `after_authority_evidence_sha256` equals the digest
derived from that case result's last ordered step by the equation above.
Its steps have the campaign's exact
count and order. Observed terminal class is derived from the step envelopes by
the closed composition rule above and equals that campaign case's expected
terminal class; there is no caller-authored `passed` field.

A rehearsal step result has exactly `authority_envelope_schema`,
`authority_evidence`, `authorization_sha256`, `cleanup_evidence_sha256`,
`derived_input_uses`, `dispatch_mode`, `dispatch_sha256`,
`fault_reservation_sha256`, `fault_result`, `fixture_uses`,
`observed_refusal_code`, `operation`, `operation_input_projection_sha256`,
`role`, `round`, `runtime_evidence_sha256`, `schedule_execution_sha256`,
`schedule_variant`, `server_event`, `server_secret_coordinate`,
`server_secret_coordinate_sha256`, `server_secret_lifecycle`,
`server_secret_lifecycle_artifact`, `server_secret_lifecycle_byte_count`,
`server_secret_lifecycle_sha256`, `step_ordinal`, `task`, `task_binding_id`,
`terminal_class`, and `transport_outcome`.
Authority evidence is one complete
evidence row whose artifact bytes parse strictly as the allowed authority-
observation, authority-success, or authority-refusal envelope named by the
schema. Every coordinate equals the selected campaign step, task binding, and
authorization.
For observation or success, `observed_refusal_code` and cleanup digest are null.
`runtime_evidence_sha256` equals the nested complete runtime evidence and
`schedule_execution_sha256` equals that evidence's complete schedule execution.
For refusal, cleanup digest equals
the nested complete cleanup object; `schedule_execution_sha256` is nonnull and
equals that cleanup object's complete schedule execution.
`runtime_evidence_sha256` equals the nested complete runtime evidence when
present and is null otherwise. `observed_refusal_code`
equals the exact parsed refusal code and the campaign step's
`expected_refusal_code`; it is never inferred from the expected terminal class.
`transport_outcome` is null for a nonnetwork schedule or when an aborted network
boundary produced no complete decisive outcome. Otherwise it equals the
complete decisive transport-outcome fact selected by the operation contract
from the nested schedule execution under `FIRST_NON_SUCCESS_ELSE_LAST`.
`server_event` is nonnull exactly when the
selected `FAULT` fixture's `evidence_kind` is `SERVER_EVENT`; otherwise it is
null. A nonnull value is the complete
`pontius-utility-rehearsal-server-event-v1` derived after that step. Its case,
step, endpoint, repository, server-policy, component-binding, procedure,
operation, ref-update-set, and fixture coordinates all equal the campaign,
selector, schedule, selected deployment receipt, and fault fixture. Process-only
timeout, cancellation, and broker fault fixtures instead bind their exact typed
cleanup or runtime evidence and cannot manufacture a server event.
The coordinate and four server-secret-lifecycle fields are null exactly for a
nonnetwork step. For every network step, coordinate is complete and reproduces
its digest; lifecycle is complete and reproduces its artifact, positive byte
count, and SHA-256. A step with a fault fixture is exact `FAULT_BOUND` and both
objects equal the matching fault result. A step without a fault fixture is
exact `SESSION_BOUND`, has null fault fields, and binds the selected broker
session, dispatch, request nonce, task binding, and step. It independently
proves the same selected server procedure, terminal remote observation, and
zero remaining uses. Every server-accepted request requires use state
`CONSUMED_ONCE`; a network attempt with no accepted request requires
`UNCONSUMED`. Evidence kind cannot make these fields null.
For a step without a fault fixture, `fault_reservation_sha256` and
`fault_result` are both null. Otherwise the digest equals the dispatch's
complete reservation and `fault_result` is the complete
`pontius-utility-rehearsal-fault-result-v1`; its activation artifact and evidence
bind the selected fixture and current attempt. A server event, when present,
repeats that result's nonce, reservation, server-component-binding, procedure,
and policy fields exactly.

`EXPECTED_UNSUPPORTED_ATOMIC` requires an exact
`ATOMIC_MULTI_REF_UNSUPPORTED` server event, unchanged fresh remote refs, and
either `REJECTED/REMOTE_REJECTED` or
`UNKNOWN/REMOTE_OUTCOME_UNKNOWN` as the paired live transport outcome and
authority-refusal code. The campaign's `expected_refusal_code` chooses exactly
one of those two live pairs before execution. Neither pair alone may claim the
atomic class. `REMOTE_TRANSPORT_FAILURE` requires a `TRANSPORT_FAILURE` outcome
when the fresh durable observation does not prove success; an `UNKNOWN` outcome
can emit only `REMOTE_OUTCOME_UNKNOWN`. A lost-acknowledgement fault step instead
emits authority success when its fresh observation proves the exact result. It
still retains the `TRANSPORT_FAILURE` outcome and
`CONNECTION_DROPPED_AFTER_ACCEPT` server event before the following exact
idempotent observation composes `EXPECTED_LOST_ACK_RECOVERY`.
Terminal class is one
closed campaign step class, is derived from the exact parsed envelope and
refusal code, and equals the campaign step's expected class. The exact ordered
vector then derives the case's observed class. Missing, duplicate, reordered, cross-
case, or artifact-only evidence refuses the result set.

A fixture-use row has exactly `evidence_sha256`, `fixture_id`,
`fixture_row_sha256`, `input_id`, `input_row_sha256`, `schema`, and `use_kind`.
It equals one complete selected fixture-set row at that exact case and step;
`fixture_row_sha256` is that row's strict canonical digest. For
`OPERATION_INPUT`, `evidence_sha256` is null and the two input fields are
nonnull; they bind the complete matching authority-input row in nested runtime
evidence when present, or in the refusal's complete cleanup input projection
otherwise, by schema, content byte count, content SHA-256, source artifact, and
complete row digest. The step's operation-input-projection digest equals that
same complete source; when both runtime and cleanup projections are present,
their complete bytes are equal. For `FAULT`, both input fields are null and
`evidence_sha256` is the digest of the complete
`pontius-utility-rehearsal-fault-result-v1`. Its nested evidence digest selects
the server event, cleanup evidence, or runtime evidence under the fixture's
frozen `evidence_kind`. That object reproduces the fixture's case, step, fault,
reservation, activation, and operation predicates. A caller assertion or
expected campaign class cannot satisfy the row. A derived-use
row has exactly `contract_row_sha256`, `derivation_id`, `input_id`,
`input_row_sha256`, and `source_step_ordinals`; it equals the campaign row and
one complete selector-bound derivation-contract row. The verifier runs that
row's held renderer over the exact named earlier typed fields and reproduces the
complete authority-input row and `input_row_sha256` byte-for-byte. That row is
located in runtime evidence when complete and otherwise in the cleanup input
projection under the same digest equation. Derived-use
rows sort by input ID; fixture-use rows
sort by use kind, input ID with null first, then fixture ID. The input fixture
uses and derived uses form a disjoint union equal to every nonreserved row in
the complete authority-input projection, whose digest is
`operation_input_projection_sha256`. Separately, all fixture-use rows and the
selector fixture set form a bijection: every input or fault fixture is consumed
exactly at its declared coordinate. No undeclared third input or fault source
exists.

A rehearsal-result evidence row is an evidence row with label exact
`HTTPS_REHEARSAL_RESULT`; its artifact bytes parse byte-for-byte as the complete
result set above. Its campaign and selector digests equal the bootstrap
selector, and its source-projection set equals the reviewed implementation.
The result set is absent from that earlier selector and therefore creates no
identity cycle.

`pontius-source-projection-set-v1` has exactly `projections` and `schema`.
`projections` has exactly four objects, in `runtime-owner`, `builder`,
`publisher`, `integrator` order. Each object has exactly `byte_count`, `role`,
and `sha256` and binds the complete `pontius-role-source-projection-v1` bytes.
`source_projection_set_sha256` is the complete-byte digest of this canonical
object; its complete count equals `source_projection_set_byte_count`. Both
implementation receipt documents reproduce all four identities exactly;
disagreement or an unrelated digest refuses acceptance.
All four projections repeat one equal utility-author-set byte count and
SHA-256. The embedded set in utility acceptance covers their complete source-
entry populations exactly; a projection with a different or unaccounted row
refuses.

Both implementation defect verdicts are CLEAN, their complete receipt documents
bind all four accepted source projections, tests and real HTTPS rehearsal satisfy
the frozen plan, and the controller disposition accepts that exact candidate.
The complete bootstrap-design-authorization publication in the acceptance
object is byte-identical to the one in the rehearsal selector, controller
authorization, bootstrap evidence, both review receipts, packet, and adopted
implementation brief. Every copy reproduces its count and digest and its nested
authorization has decision exact `AUTHORIZE_FREEZE_TOOLS_IMPLEMENTATION`.
The embedded bootstrap evidence's canonical bytes reproduce its byte count and
SHA-256. Its candidate, reviews, tests, controller disposition, and exact
`https_rehearsal_evidence` row equal the corresponding acceptance fields byte-
for-byte. No implementation-test label can stand in for that distinct row. Its durable-
disposition artifacts contain `controller_disposition`; its ceremonial remote
observation is the pushed accepted implementation target. Missing or reordered
bootstrap gates refuse acceptance.
The external complete-byte SHA-256 of this authority is
`utility_review_authority_sha256`. A caller-supplied digest without the complete
validated authority object has no meaning.

`pontius-utility-acceptance-publication-v1` has exactly
`acceptance_authority`, `acceptance_authority_artifact`,
`acceptance_authority_byte_count`, `acceptance_authority_sha256`, `publication`,
`remote_observation`, and `schema`. The nested authority is the complete object
above. Its canonical bytes, including the required final LF, equal the artifact
bytes and reproduce the adjacent positive count and digest. Publication is a
complete adopted-rule-6 publication with stage exact
`RULE6_UTILITY_ACCEPTANCE_PUBLICATION`, null ordinal and manifest, and an
artifact population containing the authority artifact exactly once. Its commit
descends from the durable-disposition publication in the nested bootstrap
evidence and preserves that history. The outer remote observation equals the
publication's complete observation and proves its commit/ref exact. The wrapper
is self-excluding: no field in the authority names its publication commit,
wrapper, observation, count, or digest.

### 6.4 Builder intent

`pontius-rehearsal-builder-intent-fixture-v1` has exactly:

| Key | Type |
| --- | --- |
| `base_oid` | `oid` |
| `campaign_sha256` | `sha256` |
| `candidate_anchor_ref` | selected case-qualified candidate-anchor ref |
| `candidate_commit_oid` | `oid` |
| `candidate_manifest_sha256` | `sha256` |
| `candidate_tree_oid` | `oid` |
| `case_id` | `case_id` |
| `fixture_id` | frozen fixture identifier |
| `intent_ref` | selected case-qualified builder-intent ref |
| `packet_anchor_ref` | selected case-qualified packet-anchor ref |
| `packet_commit_oid` | `oid` |
| `packet_inventory_sha256` | `sha256` |
| `packet_tree_oid` | `oid` |
| `plan_sha256` | `sha256` |
| `round` | `round` |
| `schema` | exact schema literal |
| `schemas_sha256` | `sha256` |
| `step_ordinal` | `positive_count` |
| `task` | `task` |
| `task_binding_id` | `task_binding_id` |

Its artifact, campaign, case, step, operation, and input ID equal the sole
fixture-set row that selects it. The consumer operation is exactly
`PUBLISH_PAIR` or `ADOPT_PAIR`. `task_binding_id` equals the selected campaign
step, and `task` and `round` equal that campaign binding rather than the utility
selector root. The three refs equal the selector's task-scoped rehearsal-ref
rows for the same case and binding. All object identities are independently
rederived from its strict canonical object graph and selected case-qualified
rehearsal namespace. The local intent ref targets the fixture's exact blob.
The fixture contains no route selector, accepted utility authority, normal
preregistration, endpoint, repository, table, credential, authorization,
dispatch, or downstream result. Under a rehearsal selector it supplies only
the inert expected local tuple for its declared consumer. A `PUBLISH_PAIR`
branch equals that publisher step and fixture row and is never named by an
adoption-chain row. An `ADOPT_PAIR` branch equals the later adopter coordinate
named by the chain row selected through the adopter's frozen derived receipt
input. A prior rehearsal fetch does not
consume or read the adopter fixture as an undeclared input; its selected chain
row carries only copied builder-intent, candidate, and packet identities. The
adopter's authorization, input, dispatch, and result repeat the fixture's
consumer coordinate. The receipt repeats the producer fetch authorization and
the same chain-row digest. All live capability coordinates still come solely
from the held rehearsal selector and table.

`pontius-builder-intent-v1` has exactly:

| Key | Type |
| --- | --- |
| `base_oid` | `oid` |
| `candidate_change_spec_sha256` | `sha256` |
| `candidate_commit_input_sha256` | `sha256` |
| `candidate_commit_oid` | `oid` |
| `candidate_manifest_sha256` | `sha256` |
| `candidate_anchor_ref` | derived local candidate-anchor ref |
| `candidate_tree_oid` | `oid` |
| `cold_input_spec_sha256` | `sha256` |
| `freeze_authorization_sha256` | `sha256` |
| `intent_ref` | derived builder-intent ref |
| `packet_anchor_ref` | derived packet-anchor ref |
| `packet_build_spec_sha256` | `sha256` |
| `packet_commit_input_sha256` | `sha256` |
| `packet_commit_oid` | `oid` |
| `packet_inventory_sha256` | `sha256` |
| `packet_source_manifest_sha256` | `sha256` |
| `packet_tree_oid` | `oid` |
| `plan_sha256` | `sha256` |
| `route_selector` | `route_selector_identity` |
| `round` | `round` |
| `schema` | exact schema literal |
| `schemas_sha256` | `sha256` |
| `task` | `task` |
| `utility_review_authority_sha256` | `sha256` |

The canonical bytes are stored as one blob. The intent ref targets that blob;
the blob OID and complete-byte SHA-256 are derived externally.

The same intent bytes result from original build and fresh-repository adoption.
The intent therefore excludes adoption receipt, adoption authorization, launch
dispatch, endpoint, fetched-object location, runtime handle identity, and
adoption mode. `freeze_authorization_sha256` names the original frozen build
authority carried by the packet, not the later adoption authority.
`route_selector` has schema exact `pontius-round-preregistration-v1`; its
complete byte count and SHA-256 equal the original freeze authorization and
cold-input spec. Adoption reproduces that identity byte-for-byte and cannot
select a rehearsal or different normal route.

### 6.5 Builder precondition

`pontius-builder-precondition-v1` has exactly `members`, `repository`, `round`,
`schema`, and `task`. `repository` is a `repository_projection`. `members` has
exactly three objects in `INTENT`, `CANDIDATE_ANCHOR`, `PACKET_ANCHOR` order.
Each
object has exactly `kind`, `observed_oid`, `ref`, and `state`.

For a new `FREEZE_PAIR` authorization, each state is `ABSENT` and each
`observed_oid` is `null`. The object binds the complete absent predecessor
without naming an output that depends on the authorization. A non-absent or
unknown member blocks a new authorization. Lost-ack recovery reuses the already
issued authorization and classifies the complete expected tuple below.

### 6.6 Builder tuple observation

`pontius-builder-tuple-observation-v1` has exactly:

| Key | Type |
| --- | --- |
| `members` | exactly three local-ref member objects |
| `repository_projection_sha256` | `sha256` |
| `round` | `round` |
| `schema` | exact schema literal |
| `task` | `task` |
| `tuple_state` | builder tuple state |

A member object has exactly `expected_oid`, `kind`, `observed_oid`, `ref`, and
`state`. `observed_oid` is `oid` or `null`. `state` is `ABSENT`, `EXACT`,
`DIFFERENT`, or `UNKNOWN`.

The members occur in this semantic order:

1. `INTENT`: builder-intent ref to exact intent blob;
2. `CANDIDATE_ANCHOR`: local candidate-anchor ref to exact candidate commit; and
3. `PACKET_ANCHOR`: packet-anchor ref to exact packet commit.

`EXACT` requires the expected target, object type, bytes, and complete bound
graph. A missing unreadable object or unclassifiable ref is `UNKNOWN`, not
`EXACT`.
The repository-projection digest equals the complete owner-held object used for
the query. That complete object is never serialized in this observation.

The tuple state is:

| Members | `tuple_state` |
| --- | --- |
| all `ABSENT` | `LOCAL_ABSENT` |
| all `EXACT` | `LOCAL_EXACT` |
| any `UNKNOWN` | `LOCAL_UNKNOWN` |
| otherwise, any `DIFFERENT` | `LOCAL_DIFFERENT` |
| every remaining proper subset | `LOCAL_PARTIAL` |

Only `LOCAL_ABSENT` permits one create-only `update-ref --stdin` transaction.
Only `LOCAL_EXACT` is idempotent success. `LOCAL_PARTIAL`, `LOCAL_DIFFERENT`,
and `LOCAL_UNKNOWN` preserve all state and refuse; no repair-in-place operation
exists.
The permitted transaction is the dispatch and schedule execution's complete
`pontius-local-ref-transaction-v1`. Its three null-endpoint ref-update rows
equal this tuple exactly, and its retained `pontius-git-stdin-write-v1` must be
`COMPLETE` before the subsequent exact tuple observation can support success.
An extra or wrong stdin command is failure even if these three intended refs
later classify exact.

All local ref classification and mutation, including integration-attempt refs,
holds the same ACL-restricted mutex:

```text
Global\PontiusFreezeRefs-v2-<sha256(mutex identity bytes)>
```

The mutex identity bytes are exact ASCII:

```text
pontius-freeze-suite-mutex-v1 LF
<common-dir volume_serial_hex> COLON <common-dir file_id_hex> LF
```

`pontius-repository-mutex-lifecycle-v1` has exactly `acquisition`,
`common_dir_file_identity`, `dacl_sha256`, `events`, `mutex_name`,
`protected_actions`, `schema`, and `terminal_state`. Acquisition has exactly
`create_disposition`, `create_error_hex`, `handle_inheritable`, `wait_result`,
and `wait_timeout_ms`. Create disposition is `CREATED_NEW` or
`OPENED_EXISTING`; `ERROR_ALREADY_EXISTS` is retained only for the latter;
the handle is noninheritable; and wait timeout equals the remaining outer
deadline rather than an independent budget. Wait result is `WAIT_OBJECT_0`,
`WAIT_ABANDONED`, `WAIT_TIMEOUT`, or `WAIT_FAILED`.

A protected-action row has exactly `input_sha256`, `kind`, `ordinal`, and
`output_sha256`. Kind is `CLASSIFY_LOCAL_REFS`, `MUTATE_LOCAL_REFS`,
`OBSERVE_LOCAL_REFS`, `MUTEX_VALIDATE_OBJECTS`,
`MUTEX_PROCESS_COMPLETION`, `MUTEX_REMOTE_RECONCILIATION`,
`MUTEX_RECEIPT_DURABILITY`, `MUTEX_JOB_ACTIVE_ZERO`, or
`MUTEX_FINAL_REVALIDATION`; rows are contiguous in actual execution order.
The first three kinds bind the exact local-ref objects. The six milestone kinds
bind respectively the validated object inventory, process-completion set,
decisive remote reconciliation, durable receipt set, Job active-zero fact, and
the self-free `pontius-runtime-final-revalidation-core-v1` digest. Remote
reconciliation is absent only
for an offline schedule; every other milestone is mandatory. A mutation kind
is present only when the authorized transaction ran. The protected-action
prefix is exactly `[CLASSIFY_LOCAL_REFS]` for a read-only classifier or exactly
`[CLASSIFY_LOCAL_REFS, MUTATE_LOCAL_REFS, OBSERVE_LOCAL_REFS]` for a mutating
transaction. The mandatory suffix is object validation, process completion,
optional remote reconciliation, receipt durability, Job active-zero, and final
revalidation. Events
are the exact ordered state names: successful lifecycle is `ACQUIRED`, every
protected action in row order, `RELEASED`, `HANDLE_CLOSED`; any other wait
result has no protected actions and records `ACQUIRE_REFUSED`, then
`HANDLE_CLOSED`. `WAIT_ABANDONED` is always refused after capturing complete
repository and ref observations; it never authorizes mutation. Terminal state
is correspondingly `RELEASED` or `ACQUIRE_REFUSED`. `RELEASED` requires a
successful `ReleaseMutex` by the acquiring thread before handle close. Timeout,
failure, abandonment, wrong DACL, an inheritable handle, action outside the
event interval, release by another thread, or early close refuses.

Release before any required milestone, a milestone outside the held interval,
an omitted or reordered milestone, or a digest not equal to the corresponding
runtime/cleanup evidence refuses. Thus `RELEASED` mechanically proves the mutex
was held through the complete governed attempt rather than only through the
local ref transaction.

No worktree path, role, operation, or policy digest enters this name. Every role
therefore maps the same held common Git directory to the same suite-wide mutex.
The mutex uses an explicit controller-only DACL. Cross-session create, open,
ownership, abandonment, and denial behavior must pass the Windows rehearsal;
inability to create or verify the global object refuses live use. The classifier
opens and holds the common directory before deriving the mutex. The mutex is
acquired before observation and held through every required protected action
and retention milestone above.

## 7. Permanent remote pair observation

`pontius-remote-pair-observation-v1` has exactly:

| Key | Type |
| --- | --- |
| `candidate` | remote-ref member object |
| `endpoint_id` | `endpoint_id` |
| `packet` | remote-ref member object |
| `pair_state` | pair-state value |
| `round` | `round` |
| `schema` | exact schema literal |
| `task` | `task` |

A remote-ref member has exactly `expected_oid`, `observed_oid`, `ref`, and
`state`. The candidate and packet refs are the derived permanent refs.
`observed_oid` and `state` use the member domains in section 6.6.

Pair state is computed with `UNKNOWN` precedence:

| Candidate | Packet | `pair_state` |
| --- | --- | --- |
| `ABSENT` | `ABSENT` | `PAIR_ABSENT` |
| `EXACT` | `EXACT` | `PAIR_EXACT` |
| `EXACT` | `ABSENT` | `PAIR_PARTIAL_CANDIDATE_ONLY` |
| `ABSENT` | `EXACT` | `PAIR_PARTIAL_PACKET_ONLY` |
| either `UNKNOWN` | any | `PAIR_UNKNOWN` |
| otherwise either `DIFFERENT` | any | `PAIR_DIFFERENT` |

`PAIR_ABSENT` alone permits one atomic create-only HTTPS push of both refs.
`PAIR_EXACT` is terminal exact success and permanent spent evidence. Both
`PAIR_PARTIAL_*` states are fatal; neither permits any mutation.
`PAIR_DIFFERENT` and `PAIR_UNKNOWN` preserve and refuse.

The publisher performs one fresh literal-endpoint observation before a push and
after every return, including rejection, timeout, cancellation, and lost
acknowledgement. Push status and tracking refs are never substituted.

Candidate and packet refs are permanent for this raw-object route. Accepted
role policies contain only their atomic create operation. A replay after
disposition therefore observes `PAIR_EXACT` and performs no mutation.

## 8. Fresh-repository adoption

### 8.1 Required-object inventory

`pontius-git-object-inventory-v1` has exactly:

| Key | Type |
| --- | --- |
| `object_count` | `positive_count` |
| `object_rows_sha256` | digest of canonical object rows |
| `objects` | object-row array |
| `inventory_kind` | object-inventory kind |
| `roots` | root-row array |
| `round` | `round` |
| `schema` | exact schema literal |
| `task` | `task` |

An object row has exactly `byte_count`, `oid`, `sha256`, and `type`. `type` is
`blob`, `tree`, or `commit`. Rows sort by ASCII `oid`; each OID is unique.
`object_count` equals the array length. `object_rows_sha256` hashes the
concatenated canonical row bytes.

A root row has exactly `label` and `oid`. `inventory_kind` and root order are
exact:

| Inventory kind | Root labels |
| --- | --- |
| `ADOPTION` | `BASE`, `CANDIDATE`, `PACKET` |
| `MAIN_PACKET_INTEGRATION` | `MAIN_PREDECESSOR`, `CANDIDATE`, `PACKET` |
| `MAIN_REVIEW_FINALIZER` | `MAIN_PREDECESSOR`, `REVIEW_01`, `REVIEW_02` |
| `MAIN_DISPOSITION` | `MAIN_PREDECESSOR`, `REVIEW_01`, `REVIEW_02` |

The inventory is closed over every object required to parse and validate its
roots and their declared relations. Unreachable extra objects in the authority
object database are nonauthority residue.

Closure is the complete transitive raw Git closure of every root: each commit,
every commit parent, each root tree, every recursive subtree, and every blob.
Annotated tags refuse. Replacements, grafts, shallow boundaries, promisor or
partial-clone substitution, alternates, and missing objects refuse. The raw
reader recomputes type, size, SHA-1, and SHA-256 for every row. The inventory
has an authorization-bounded object-count and canonical-byte cap; exceeding
either refuses rather than truncating.

Builder intent is deliberately not a fetched root: it depends on the packet
OID and cannot be an ancestor of that packet. The publisher derives its
expected bytes and identities without writing an object. The offline adopter
reconstructs and stores those same canonical bytes after validating the packet.

### 8.2 Adoption receipt

`pontius-adoption-receipt-v1` has exactly:

| Key | Type |
| --- | --- |
| `adoption_chain_row_sha256` | `sha256` or `null` |
| `builder_intent_blob_oid` | `oid` |
| `builder_intent_sha256` | `sha256` |
| `candidate_oid` | `oid` |
| `candidate_ref` | derived candidate ref |
| `endpoint_id` | `endpoint_id` |
| `fetch_authorization_sha256` | `sha256` |
| `object_inventory_byte_count` | `positive_count` |
| `object_inventory_sha256` | `sha256` |
| `packet_oid` | `oid` |
| `packet_ref` | derived packet ref |
| `pair_observation_sha256` | `sha256` |
| `publisher_role_projection_sha256` | `sha256` |
| `route_selector` | `route_selector_identity` |
| `round` | `round` |
| `schema` | exact schema literal |
| `schemas_sha256` | `sha256` |
| `task` | `task` |

The publisher issues this receipt only after an exact `PAIR_EXACT` observation, a fetch
that creates no ref, and independent validation of every required-object row.
The receipt is downstream evidence. It is not part of builder intent and does
not change the intent blob OID.
Its `route_selector` uses the same selector kind and complete bytes as the fetch
authorization. On a normal route it also equals the remote packet artifact and
normal builder intent, and a fresh adopter receives those selector bytes from
the packet, and `adoption_chain_row_sha256` is null. On a rehearsal route it
equals the campaign selector and the nonnull chain-row digest equals the fetch
authorization. The row preselects the later adopter's exact builder-intent
fixture and its blob OID, SHA-256, candidate, packet, case, and task binding;
the fixture contains no selector bytes. In both branches the adopter receives the complete
selector owner-side and never infers it from ref names or substitutes the other
kind.

A later `ADOPT_PAIR` authorization binds the receipt and object inventory. The
rehearsal authorization also repeats the same chain-row digest and consumes the
exact named `BUILDER_INTENT` fixture at its declared adopter coordinate. The
offline builder independently reparses the complete graph and then applies the
same three-ref create-only transaction in section 6. The publisher cannot
create an authority ref; the builder has no network operation.

### 8.3 Main-input fetch

`pontius-main-input-fetch-spec-v1` has exactly:

| Key | Type |
| --- | --- |
| `endpoint_id` | `endpoint_id` |
| `input_kind` | main-input kind |
| `main_predecessor_oid` | `oid` |
| `permanent_inputs` | exactly two permanent-input rows |
| `round` | `round` |
| `schema` | exact schema literal |
| `task` | `task` |

`input_kind` is `PACKET_INTEGRATION`, `REVIEW_FINALIZER`, or `DISPOSITION`.
The permanent-input row schema is in section 9.3. Packet integration binds
`CANDIDATE`, then `PACKET`; review finalization and disposition bind
`REVIEW_01`, then `REVIEW_02`. The spec contains only expected roots and exists
before any observation, inventory, overlay, or result.

`pontius-main-predecessor-observation-v1` has exactly `endpoint_id`,
`expected_oid`, `main_ref`, `observed_oid`, `round`, `schema`, `state`, and
`task`. `observed_oid` is `oid` or `null`; state is `EXACT`, `ABSENT`,
`DIFFERENT`, or `UNKNOWN`. It deliberately has no expected result field.

`pontius-permanent-input-observation-v1` has exactly `input_kind`,
`observation`, `observation_byte_count`, `observation_schema`,
`observation_sha256`, and `schema`. `observation` is the complete canonical
permanent-input observation. Its schema is
`pontius-remote-pair-observation-v1` for `PACKET_INTEGRATION` and
`pontius-review-slot-observation-v1` for `REVIEW_FINALIZER` or `DISPOSITION`.
The byte count and digest reproduce its canonical bytes plus LF.

`pontius-optional-object-inventory-v1` has exactly `inventory`,
`inventory_byte_count`, `inventory_sha256`, and `schema`. The first three
fields are all null when readiness is not `INPUTS_EXACT`. At `INPUTS_EXACT`,
`inventory` is the complete canonical `pontius-git-object-inventory-v1` object
and its positive byte count and digest reproduce its canonical bytes plus LF.

`pontius-main-input-readiness-observation-v1` has exactly:

| Key | Type |
| --- | --- |
| `input_spec_sha256` | `sha256` |
| `main_predecessor_observation_sha256` | `sha256` |
| `object_inventory_sha256` | `sha256` or `null` |
| `permanent_observation_schema` | exact `pontius-permanent-input-observation-v1` |
| `permanent_observation_sha256` | `sha256` |
| `round` | `round` |
| `schema` | exact schema literal |
| `scratch_projection_sha256` | `sha256` |
| `state` | main-input readiness state |
| `task` | `task` |

The permanent-observation digest names the wrapper above. Readiness is
`INPUTS_EXACT`, `INPUTS_NOT_READY`, `INPUTS_CONFLICT`, or
`INPUTS_UNKNOWN`, in unknown, conflict, not-ready, exact precedence. Only
`INPUTS_EXACT` carries an object-inventory digest. It requires exact main and
permanent observations plus the input-kind inventory and complete graph in a
new no-ref scratch repository. Missing expected review outputs are not ready;
different or partial permanent state conflicts; unavailable state is unknown.

`FETCH_MAIN_INPUTS` then repeats both decisive observations, fetches main first
and the two permanent full refs with no destination ref into the authority
object database, repeats both observations again, and reproduces every inventory
row from that database. A changed, missing, different, partial, unknown, or
extra root refuses. Fetch residue grants no ref authority.

`pontius-main-input-fetch-receipt-v1` has exactly:

| Key | Type |
| --- | --- |
| `authorization_sha256` | `sha256` |
| `input_spec_sha256` | `sha256` |
| `main_predecessor_observation_after_sha256` | `sha256` |
| `main_predecessor_observation_before_sha256` | `sha256` |
| `object_inventory_byte_count` | `positive_count` |
| `object_inventory_sha256` | `sha256` |
| `operation_precondition_sha256` | `sha256` |
| `permanent_observation_after_sha256` | `sha256` |
| `permanent_observation_before_sha256` | `sha256` |
| `permanent_observation_schema` | exact allowed schema literal |
| `readiness_observation_sha256` | `sha256` |
| `repository_projection_sha256` | `sha256` |
| `role_projection_sha256` | `sha256` |
| `round` | `round` |
| `schema` | exact schema literal |
| `task` | `task` |

`BUILD_MAIN_OVERLAY` accepts main or permanent-input object bytes only when
they revalidate against this receipt and its complete bound inventory. The
before observations equal the readiness inputs, and both after observations
equal their respective before observations. The operation-precondition digest
binds the spec, readiness observation, and complete inventory. The
receipt is downstream fetch evidence and does not authorize an object, ref, or
push.

## 9. Packet integration intent and local attempt refs

### 9.1 Integration intent

`pontius-integration-intent-v1` has exactly:

| Key | Type |
| --- | --- |
| `build_authorization_sha256` | `sha256` |
| `commit_metadata` | `commit_metadata` |
| `endpoint_id` | `endpoint_id` |
| `integration_commit_input_sha256` | `sha256` |
| `integration_commit_oid` | `oid` |
| `integration_tree_oid` | `oid` |
| `main_predecessor_oid` | `oid` |
| `main_ref` | selector-derived main ref |
| `object_build_receipt_sha256` | `sha256` |
| `overlay_spec_sha256` | `sha256` |
| `packet_oid` | `oid` |
| `phase_after` | exact `PACKET_INTEGRATED` |
| `phase_before` | exact `NO_TASK` for the main protected projection |
| `plan_sha256` | `sha256` |
| `protected_task_spec_sha256` | `sha256` |
| `protected_after_inventory_sha256` | `sha256` |
| `protected_before_inventory_sha256` | `sha256` |
| `route_selector` | `route_selector_identity` |
| `round` | `round` |
| `schema` | exact schema literal |
| `schemas_sha256` | `sha256` |
| `task` | `task` |

The named raw commit input has kind `PACKET_INTEGRATION`, first parent equal to
`main_predecessor_oid`, and second parent equal to `packet_oid`. The result is
therefore a fast-forward child of fresh main while preserving packet ancestry.
Its author and committer fields equal `commit_metadata` exactly.
The bound main-overlay spec has kind `PACKET_INTEGRATION` and repeats the same
commit input, metadata, predecessor, tree, and result identities.
`build_authorization_sha256` names the exact `BUILD_MAIN_OVERLAY`
authorization, and `object_build_receipt_sha256` names its validated receipt.
Both repeat the overlay, commit input, tree, result, task, and round exactly.

The integration intent is stored as a blob. It excludes its blob identity, the
later transition authorization, launch dispatch, local attempt refs, and main
observation.
Its `route_selector` has the same selector kind and complete bytes as the input
fetch, build, and later integration authorizations. On a normal route it also
equals the packet artifact's preregistration. On a rehearsal route it is the
current campaign selector, the packet identity comes from the selected fixture
or prior campaign result, and the intent is derived only after that selector and
build result exist. It is therefore downstream of the selector and absent from
the upstream fixture set. A cross-kind or cross-case chain refuses.

### 9.2 Integration-attempt observation

The transition authorization's external SHA-256 derives the two ref names in
section 1.3. The intent ref targets the integration-intent blob. The result ref
targets the integration commit. The owner uses the one already validated
`AUTHORIZATION_DERIVED` table descriptor for each kind and, on a rehearsal
route, the equal selector descriptor. The authorization's task, round, case,
and task binding plus its complete external digest produce each full ref once.
No selector, preregistration, intent, operation input, or caller contains either
full ref.

`pontius-integration-attempt-observation-v1` has exactly:

| Key | Type |
| --- | --- |
| `authorization_sha256` | `sha256` |
| `members` | exactly two local-ref member objects |
| `repository_projection_sha256` | `sha256` |
| `round` | `round` |
| `schema` | exact schema literal |
| `state` | integration-attempt state |
| `task` | `task` |

Members use section 6.6's object schema and occur as `INTENT`, then `RESULT`.
Each member's `ref` equals the single post-authorization derivation above and
the same value in the ref-update set, refspec, argv validation, and mutation
evidence.
The same member equations produce `ATTEMPT_ABSENT`, `ATTEMPT_EXACT`,
`ATTEMPT_PARTIAL`, `ATTEMPT_DIFFERENT`, or `ATTEMPT_UNKNOWN`. Only
`ATTEMPT_ABSENT` permits the two-ref transaction; only `ATTEMPT_EXACT` is
idempotent success. Both refs are created in one local `update-ref --stdin`
transaction before any main push. They share the repository mutex in section
6.3.
That transaction is the dispatch and schedule execution's complete
`pontius-local-ref-transaction-v1`; its two null-endpoint rows equal `INTENT`
then `RESULT` in unsigned-ref order, and its actual stdin-write fact must be
`COMPLETE`. Exact classification of the intended pair cannot hide an extra,
wrong, reordered, or cross-dispatch command stream.

These refs are local reconstructible residue. They are not atomic with the
remote main update and are not global spend evidence. A fresh clone may recreate
them only from the same authorization, exact intent bytes, and exact result
commit. Main observation alone decides whether a remote transition was spent.
The repository-projection digest equals the authorization and complete owner-
held launch projection; the complete object never enters this observation.

### 9.3 Protected task specification, semantic projection, and phase evidence

`pontius-protected-task-spec-v1` fixes the population a main walk must compare.
Its root has exactly `round`, `rules`, `schema`, and `task`. A rule has exactly
`kind`, `path`, and `record_key`. `kind` is `PATH` or `SHARED_RECORD`.
`record_key` is `null` for `PATH` and a canonical ASCII key for
`SHARED_RECORD`. Rules sort by path, kind, then key and are unique. They cover
every task-owned path, required absence, review/disposition destination, and
task-owned record in a shared append-only file. A walk cannot add or omit a
rule.

`pontius-protected-task-inventory-v1` has exactly:

| Key | Type |
| --- | --- |
| `commit_oid` | `oid` |
| `protected_task_spec_sha256` | `sha256` |
| `rows` | protected-row array |
| `round` | `round` |
| `schema` | exact schema literal |
| `semantic_projection_sha256` | `sha256` |
| `task` | `task` |
| `tree_oid` | `oid` |

A protected row has exactly `blob_oid`, `byte_count`, `kind`, `mode`, `path`,
`record_byte_count`, `record_key`, `record_sha256`, `sha256`, `state`, and
`type`. `state` is `ABSENT` or `PRESENT`. A present `PATH` row binds mode, Git
type, blob OID, complete-byte SHA-256, and byte count; record fields are `null`.
An absent row has every content field `null`. A `SHARED_RECORD` row additionally
binds the whole containing blob as carrier evidence and the exact uniquely
parsed record bytes. Duplicate, missing, reordered, normalized, or ambiguous
records refuse.

`pontius-protected-semantic-projection-v1` has exactly `round`, `rows`, `schema`,
and `task`. Its rows preserve the protected-spec order. A `PATH`
semantic row repeats every protected-row field. A `SHARED_RECORD` semantic row
has exactly `kind`, `mode`, `path`, `record_byte_count`, `record_key`,
`record_sha256`, `state`, and `type`; it deliberately omits the containing
blob's OID, SHA-256, and byte count. The projection digest equals the inventory's
`semantic_projection_sha256`.

This split lets another task append its own record to the same carrier. The
carrier blob is still freshly parsed and recorded at each commit, while this
task remains semantically equal when its own record, path mode, and type are
unchanged. Complete inventory digests are never compared as task equality.

`pontius-phase-evidence-v1` is observer-derived after a result exists. It has
exactly:

| Key | Type |
| --- | --- |
| `after_inventory_sha256` | `sha256` |
| `before_inventory_sha256` | `sha256` |
| `commit_input_sha256` | `sha256` |
| `input_bundle` | phase-evidence-input bundle |
| `parents` | exact ordered OID array |
| `permanent_inputs` | permanent-input array |
| `result_commit_oid` | `oid` |
| `result_tree_oid` | `oid` |
| `round` | `round` |
| `schema` | exact schema literal |
| `task` | `task` |
| `transition_kind` | transition kind |

`pontius-phase-evidence-input-bundle-v1` has exactly `document_byte_cap`,
`document_byte_count`, `document_count`, `documents`, `plan_sha256`, `round`,
`schema`, `task`, and `transition_kind`. A document row has exactly
`byte_count`, `content`, `role`, `schema`, and `sha256`. `content` is the
complete parsed canonical object selected by `schema`; its strict canonical
ASCII JSON plus final LF reproduces `byte_count` and `sha256`. Rows occur in
this exact role order:

```text
PACKET_INTEGRATION:
  TRANSITION_AUTHORIZATION
  INTEGRATION_INTENT
  MAIN_OVERLAY_SPEC
  RAW_COMMIT_INPUT
REVIEW_FINALIZER:
  FINALIZER_AUTHORIZATION
  MAIN_OVERLAY_SPEC
  RAW_COMMIT_INPUT
DISPOSITION:
  TRANSITION_AUTHORIZATION
  DISPOSITION_INTENT
  MAIN_OVERLAY_SPEC
  RAW_COMMIT_INPUT
```

`document_count` is respectively four, three, or four and equals the array
length. `document_byte_count` is the exact sum of row byte counts and is no
greater than `document_byte_cap`. The cap is a positive count frozen by
`plan_sha256`, applies before parsing any row, and must fit the launch's input
and memory limits. Exceeding it yields `TASK_UNKNOWN`, never partial evidence.

The proposed bundle is assembled after the authorization and raw result
preimage exist but before a push. It proves only the proposed material edge and
creates no content cycle. If a later observation finds that exact result on
main, the observer combines the bundle with fresh inventories and permanent-ref
observations to derive complete `pontius-phase-evidence-v1`. Missing,
malformed, or incomplete bytes yield `TASK_UNKNOWN`; a readable
contradiction yields `PROTECTED_CONFLICT`.

`pontius-phase-evidence-input-set-v1` is the complete historical input
population for one task and round at the authorization's expected predecessor.
Its root has exactly `bundle_count`, `bundles`,
`document_byte_cap`, `document_byte_count`, `plan_sha256`,
`round`, `schema`, and `task`. An entry has exactly
`input_bundle`, `result_commit_oid`, and `transition_kind`.
`input_bundle` is the complete canonical object above; the other two
fields equal its transition kind and the result OID in its raw-commit-input
document.

The array contains zero to three entries in exact phase order:
`PACKET_INTEGRATION`, `REVIEW_FINALIZER`, then `DISPOSITION`.
Bundle count equals its length. Document byte count is the sum of each complete
bundle's standalone strict canonical bytes plus LF and is no greater than the
plan-bound positive cap. The set contains exactly every historical material
edge for this task and round on the expected predecessor's first-parent chain;
an unused, duplicate, reordered, side-branch, or missing entry refuses or
produces `TASK_UNKNOWN` when bytes cannot be read. Thus integration binds
an empty set, finalization binds the accepted integration bundle, and
disposition binds the accepted integration and finalizer bundles.

The proposed bundle is separate from this historical set. During same-launch
lost-acknowledgement reconciliation, an observed proposed result joins the
historical population only as derived terminal phase evidence. It never mutates
the launch input, authorization, or historical set. A later transition carries
that immutable bundle as a member of its newly authorized historical set.

A permanent input has exactly `commit_oid`, `manifest_sha256`, `ref`, and
`role`; `manifest_sha256` is `sha256` or `null`; `role` is a closed input label.
Every ref target and external manifest digest is freshly revalidated.
Permanent-input populations and order are exact:

| Transition kind | Permanent-input roles |
| --- | --- |
| `PACKET_INTEGRATION` | `CANDIDATE`, then `PACKET` |
| `REVIEW_FINALIZER` | `REVIEW_01`, then `REVIEW_02` |
| `DISPOSITION` | `REVIEW_01`, then `REVIEW_02` |

Each role selects the one derived permanent ref for that task and round. The
candidate and both review roles require their external manifest SHA-256. The
packet role binds its packet-inventory SHA-256 in that field. No other role,
order, ref, or cardinality is valid.

The observer reconstructs phase evidence from the complete input bundle, parsed
raw result commit, both protected inventories, result-tree artifacts, and fresh
permanent-ref observations. It verifies authorization to intent, overlay, raw
input, and result before accepting the material edge. `PACKET_INTEGRATION`
requires the exact packet as second parent and exact pair artifacts.
`REVIEW_FINALIZER` requires exact package copies and the two issuer lines in
`<task>/progress.md`. `DISPOSITION` requires the exact controller report and
record already present in the result tree and both finalized review inputs. No
bare digest refers to an unavailable local authorization, intent, or overlay
file.

`NO_TASK` is the initial derived phase and requires no phase evidence. Every
later phase derives only from one valid material transition:
`PACKET_INTEGRATED`, `REVIEWS_FINALIZED`, or `DISPOSITION_PUBLISHED`. The
transition's before and after inventories share
one protected-task-spec digest and match its first parent and result commit.
Unrelated intervening commits may change carrier inventory digests but must
preserve the task semantic projection. Every edge remains in the walk, so a
task change followed by restoration remains a conflict.

## 10. Two-axis main observation

`pontius-phase-history-v1` verifies the task phase at the operation's expected
predecessor independently of lineage classification. Its root has exactly
`expected_predecessor_oid`, `historical_input_set_sha256`, `plan_sha256`,
`protected_task_spec_sha256`, `round`, `rows`, `schema`, `status`, `task`,
`walk_byte_cap`, `walk_byte_count`, `walk_count`, and `walk_count_cap`. Status is
`INTACT`, `PROTECTED_CONFLICT`, or `TASK_UNKNOWN`.

A phase-history row has exactly `commit_oid`, `first_parent_oid`, `inventory`,
`phase`, `phase_evidence`, `reason`, and `status`. Row status is exactly:

```text
BASELINE_INTACT
INTACT_SAME_PHASE
INTACT_PHASE_ADVANCE
PROTECTED_CONFLICT
HISTORY_UNKNOWN
DEPENDENT_ON_HISTORY_UNKNOWN
```

The status shapes are exact. `BASELINE_INTACT` has null reason, complete
inventory with the `NO_TASK` semantic projection, phase `NO_TASK`, null phase
evidence, and a strictly parsed first parent that may be null only at a readable
root. `INTACT_SAME_PHASE` has null reason, a nonnull strictly parsed first
parent, complete inventory, nonnull phase, and null phase evidence.
`INTACT_PHASE_ADVANCE` has the same shape with complete phase evidence.
`PROTECTED_CONFLICT` has reason `SEMANTIC_MISMATCH` or
`PHASE_CONTRADICTION`, a parsed first parent that may be null only at the
readable root/baseline coordinate, complete inventory, and null phase and phase
evidence.

`HISTORY_UNKNOWN` uses exactly the reason domain below and always has null phase
and phase evidence. Raw-unavailable, raw-malformed, and either cap reason have
null first parent and inventory. Inventory-unavailable has a nonnull parsed
first parent, except that it may be null at the readable root/baseline
coordinate, and null inventory. Phase-input or permanent-input unavailable has
a nonnull parsed first parent and complete inventory.
`DEPENDENT_ON_HISTORY_UNKNOWN` has reason exact
`DEPENDENT_ON_HISTORY_UNKNOWN`, null phase and phase evidence, and independently
nullable parent and inventory; a nonnull value must still be strictly derived
from the held raw commit and inventory bytes.

Rows occur from expected predecessor toward the validated `NO_TASK` baseline.
The first row's commit is the expected predecessor; each later commit equals the
prior row's strictly parsed first parent. Evaluation occurs in reverse order.
With an empty historical input set, the expected predecessor itself is the
baseline. Otherwise the baseline is the strictly parsed first parent of the
earliest historical transition result. Its complete protected semantic
projection has every task-owned path and record in the spec-required absent
state, its phase is `NO_TASK`, and its row is `BASELINE_INTACT`. This explicit
baseline is the stop proof; the producer cannot stop merely because it has seen
the earliest transition result.

Every commit between baseline and expected predecessor appears exactly once.
Each row whose commit is a historical result consumes the one matching bundle
and is `INTACT_PHASE_ADVANCE`; every intervening equal semantic projection is
`INTACT_SAME_PHASE`. A readable semantic mismatch or phase contradiction is
`PROTECTED_CONFLICT`. The complete historical input set is consumed once in
phase order. Missing, extra, duplicated, reordered, side-branch, or unused
bundles cannot yield `INTACT`.

`HISTORY_UNKNOWN` has null phase and phase evidence and reason exactly
`RAW_COMMIT_UNAVAILABLE`, `RAW_COMMIT_MALFORMED`,
`PROTECTED_INVENTORY_UNAVAILABLE`, `PHASE_INPUT_UNAVAILABLE`,
`PERMANENT_INPUT_UNAVAILABLE`, `WALK_COUNT_EXCEEDED`, or
`WALK_BYTES_EXCEEDED`. Inventory and first parent are present only when those
facts were strictly obtained before the failure. Every newer row whose phase
depends on the first unknown is `DEPENDENT_ON_HISTORY_UNKNOWN`; its phase and
phase evidence are null, and its inventory may be complete or null. The compact
cap-failure row consumes reserved count and byte capacity. Status is
`TASK_UNKNOWN` if any row is unknown or dependent, otherwise
`PROTECTED_CONFLICT` if any row conflicts, and otherwise `INTACT`.

Walk counts and byte counts use the same strict standalone-row-plus-LF equation
as the lineage walk and are bounded independently by positive plan caps. The
history walk may fail after lineage is already exact; that forces top-level task
state `TASK_UNKNOWN` but never erases the classified lineage or `result_seen`.

`pontius-spent-result-dag-observation-v1` has exactly `expected_result_oid`,
`observed_tip_oid`, `rows`, `schema`, `state`, `walk_byte_cap`,
`walk_byte_count`, `walk_count`, and `walk_count_cap`. A row has exactly
`commit_oid`, `parent_oids`, and `tree_oid`; parent OIDs equal the raw commit's
complete ordered parent array. Starting at the observed tip, the owner performs
a deterministic OID-priority all-parent traversal. It stops at the first exact
result row (`REACHABLE`) or exhausts the unique reachable DAG (`ABSENT`). A raw-
object failure, cycle, or preallocated count/byte cap produces `UNKNOWN` with
the exact readable prefix and compact failure row. Tip and rows are null/empty
only when main is absent, which is `ABSENT`. This object reads commit/tree bytes
only and does not reinterpret task artifacts.

`pontius-main-observation-v1` has exactly:

| Key | Type |
| --- | --- |
| `endpoint_id` | `endpoint_id` |
| `expected_predecessor_oid` | `oid` |
| `expected_result_oid` | `oid` |
| `lineage` | lineage value |
| `lineage_failure` | lineage-failure object or `null` |
| `main_ref` | selector-derived main ref |
| `observed_tip_oid` | `oid` or `null` |
| `plan_sha256` | `sha256` |
| `phase_history` | complete phase-history object or `null` |
| `protected_task_spec_sha256` | `sha256` |
| `result_seen` | boolean |
| `round` | `round` |
| `schema` | exact schema literal |
| `task` | `task` |
| `task_state` | task-state value |
| `walk` | first-parent walk-row array |
| `walk_byte_cap` | `positive_count` |
| `walk_byte_count` | `count` |
| `walk_count` | `count` |
| `walk_count_cap` | `positive_count` |

`phase_history` is complete for each first-parent anchored lineage and null for
`RESULT_SIDE_ANCESTOR`, `UNRELATED_OR_ABSENT`, or lineage `UNKNOWN`. A side-
ancestor result is already spent and exact `PROTECTED_CONFLICT`; it cannot be
replayed or treated as intact phase history. Its expected predecessor, plan,
task, round, protected spec, and historical-set digest equal the observation's
held inputs. An exact-tip raw failure does not make it null: history still walks
the independently bound predecessor while the exact anchor row carries typed
task uncertainty.

Lineage is exactly one of:

```text
RESULT_EXACT
RESULT_DESCENDANT
RESULT_SIDE_ANCESTOR
PREDECESSOR_EXACT
PREDECESSOR_DESCENDANT
UNRELATED_OR_ABSENT
UNKNOWN
```

Task state is exactly one of:

```text
INTACT
PROTECTED_CONFLICT
TASK_UNKNOWN
NOT_APPLICABLE
```

A walk row has exactly `commit_oid`, `first_parent_oid`, `inventory`, `phase`,
`phase_evidence`, `task_reason`, and `task_status`. `first_parent_oid` is `oid`
or `null`; `inventory` is a complete
`pontius-protected-task-inventory-v1` object or `null`; `phase` is a derived
phase or `null`; and `phase_evidence` is a complete
`pontius-phase-evidence-v1` object or `null`.

Task status is exactly:

```text
INTACT_SAME_PHASE
INTACT_PHASE_ADVANCE
PROTECTED_CONFLICT
TASK_UNKNOWN
NOT_APPLICABLE
```

`task_reason` is `null` for either intact status. For `PROTECTED_CONFLICT` it
is `SEMANTIC_MISMATCH` or `PHASE_CONTRADICTION`. For `TASK_UNKNOWN` it is one
of:

```text
RAW_COMMIT_UNAVAILABLE
RAW_COMMIT_MALFORMED
PROTECTED_INVENTORY_UNAVAILABLE
PHASE_INPUT_UNAVAILABLE
PERMANENT_INPUT_UNAVAILABLE
FUTURE_PHASE_BUNDLE_UNAVAILABLE
ROW_BUDGET_EXCEEDED
DEPENDENT_ON_TASK_UNKNOWN
```

For `NOT_APPLICABLE`, `task_reason` is `NO_ANCHOR` or
`PRE_ANCHOR_LINEAGE_FAILURE`.

`INTACT_SAME_PHASE` requires a strictly parsed parent, complete inventory,
nonnull derived phase, null phase evidence, and equal parent/current semantic
projections. The sole null-parent intact form is a readable predecessor-exact
root whose row agrees with the phase-history `BASELINE_INTACT` row.
`INTACT_PHASE_ADVANCE` requires a strictly parsed parent, complete
inventory, nonnull derived phase, and complete valid phase evidence.
`PROTECTED_CONFLICT` requires a strictly parsed parent and complete inventory;
the parent may be null only for a readable predecessor-exact root that overlaps
the phase-history baseline;
phase and phase evidence are null, and the reason distinguishes a readable
semantic mismatch from a readable phase contradiction.

For `TASK_UNKNOWN`, phase and phase evidence are null. Inventory is null for
`RAW_COMMIT_UNAVAILABLE`, `RAW_COMMIT_MALFORMED`,
`PROTECTED_INVENTORY_UNAVAILABLE`, or `ROW_BUDGET_EXCEEDED`; a
`DEPENDENT_ON_TASK_UNKNOWN` row may have complete or null inventory. Every other
reason requires complete inventory. `RAW_COMMIT_UNAVAILABLE` and
`RAW_COMMIT_MALFORMED` require a null first parent. Either is valid only at the
matched result or predecessor anchor, whose coordinate is fixed by the observed
tip or by the prior row's strictly parsed first parent; its `commit_oid` is that
requested OID. Every
other primary `TASK_UNKNOWN` reason requires that row's strictly parsed first-
parent OID, except `PROTECTED_INVENTORY_UNAVAILABLE` may have a null parent at
the readable predecessor-exact root/phase-history baseline. A dependent row
retains a parsed parent when available but never
claims one from failed bytes. Once task evaluation becomes unknown, every newer
dependent edge uses `DEPENDENT_ON_TASK_UNKNOWN`.

For `NOT_APPLICABLE`, inventory, phase, and phase evidence are null. A complete
readable no-anchor walk uses `NO_ANCHOR`. A readable prefix stopped by a
lineage failure uses `PRE_ANCHOR_LINEAGE_FAILURE`. Each row retains its parsed
first-parent fact, including a null parent only at a readable root.

Walk order is remote tip through the first matched anchor. Its anchor phase is
derived from the complete phase history and, for an expected result, the
proposed input bundle; it is never read from an inventory or caller assertion.
Each row therefore carries a complete task fact or a closed reason why that fact
is unavailable. The plan fixes maximum count and byte caps and
reserves one row plus enough bytes for the compact `ROW_BUDGET_EXCEEDED` form.
`walk_count` equals the array length. `walk_byte_count` is the sum of each walk
row's standalone strict canonical JSON bytes plus LF. Both counts are at most
their plan-bound caps, enforced before allocation. A prefix without its
required compact failure row is not authoritative.

A lineage-failure object has exactly `at_oid` and `reason`. `at_oid` is `oid`
or `null`; reason is one of:

```text
RAW_COMMIT_UNAVAILABLE
RAW_COMMIT_MALFORMED
FIRST_PARENT_AMBIGUOUS
CHAIN_DISCONTINUITY
CYCLE_DETECTED
WALK_COUNT_EXCEEDED
WALK_BYTES_EXCEEDED
```

It is nonnull exactly when top-level lineage is `UNKNOWN`. It identifies the
next requested coordinate when one exists; a malformed or unavailable tip may
use null. It is null for every other lineage. Failed raw bytes never become a
parsed-parent claim. The sole matched-anchor exception is the requested-
coordinate `TASK_UNKNOWN/RAW_COMMIT_UNAVAILABLE` or
`TASK_UNKNOWN/RAW_COMMIT_MALFORMED` row at a matched anchor defined above. For an
unknown lineage, the readable prefix remains bound in `walk`, and every row
uses `NOT_APPLICABLE/PRE_ANCHOR_LINEAGE_FAILURE`.

The separate phase history consumes every entry from
`PHASE_EVIDENCE_INPUT_SET` before the lineage rows are evaluated. The expected
result edge, when encountered in the lineage walk, uses exactly
`PROPOSED_PHASE_EVIDENCE_INPUT_BUNDLE`. The observer derives each
`pontius-phase-evidence-v1` from that complete bundle, the raw walked
commit, fresh before/after inventories, result-tree artifacts, and permanent
inputs. A missing, extra, side-branch, duplicated, or mismatched historical
entry makes phase history non-intact. A later same-task phase beyond the proposed
result without an available
immutable bundle emits a `TASK_UNKNOWN/FUTURE_PHASE_BUNDLE_UNAVAILABLE` row.
Once result lineage is established, that row preserves `result_seen=true`.

Before the semantic first-parent classifier, `spent_result_dag` searches every
parent edge for the expected result. `UNKNOWN` blocks all mutation and forces
lineage `UNKNOWN` unless the observed tip is the exact result. `REACHABLE` on a
non-first-parent path forces `RESULT_SIDE_ANCESTOR`, `result_seen=true`, and
`task_state=PROTECTED_CONFLICT`; the old transition is spent. `ABSENT` proves no
side-parent reset and permits the ordinary classifier below. A first-parent
`RESULT_*` lineage requires DAG state `REACHABLE`.

The classifier walks a contiguous first-parent chain through the first expected
anchor or, if neither appears, through the readable root. It compares expected
result before predecessor:

1. Tip equal to result is `RESULT_EXACT`.
2. A walk that encounters result first is `RESULT_DESCENDANT`.
3. With no result seen, tip equal to predecessor is `PREDECESSOR_EXACT`.
4. With no result seen, a walk that encounters predecessor is
   `PREDECESSOR_DESCENDANT`.
5. A complete readable walk containing neither, or an absent main ref, is
   `UNRELATED_OR_ABSENT`.
6. A raw-unavailable, malformed, missing, ambiguous, cyclic, discontinuous, or
   capped chain before either anchor is classified is `UNKNOWN`.

Lineage is derived only from the observed ref and contiguous strictly parsed
raw commit/first-parent facts. The first row equals the observed tip; each
later row's commit equals the preceding first parent; duplicates and cycles
produce `UNKNOWN` with their exact lineage-failure reason. Anchor comparison
occurs before task evaluation and compares result before predecessor.
`RESULT_EXACT` needs only the observed tip equal to the expected result.
`RESULT_DESCENDANT` requires a complete raw chain to the result coordinate; the
matched result row itself may carry the typed exact-anchor raw failure above. A
protected-inventory or phase failure does not erase such a chain. A raw-commit
failure before a descendant anchor coordinate forces lineage `UNKNOWN` and
`result_seen=false`; it cannot manufacture `RESULT_*`.

`result_seen` is true exactly for `RESULT_EXACT`, `RESULT_DESCENDANT`, and
`RESULT_SIDE_ANCESTOR`. It remains true if
task-state comparison later finds `PROTECTED_CONFLICT`.

For any of the four anchored lineages, `walk` contains every coordinate from
tip through the matched anchor exactly once. No row is `NOT_APPLICABLE`. Any
`TASK_UNKNOWN` row or `phase_history.status=TASK_UNKNOWN` makes top-level task
state `TASK_UNKNOWN`; otherwise any `PROTECTED_CONFLICT` row or
`phase_history.status=PROTECTED_CONFLICT` makes it `PROTECTED_CONFLICT`;
otherwise every lineage row and phase history is intact and top-level state is
`INTACT`. After the first
unknown in anchor-to-tip evaluation, every newer edge is
`TASK_UNKNOWN/DEPENDENT_ON_TASK_UNKNOWN`.

For a predecessor anchor, the anchor lineage row and first phase-history row
refer to the same commit and have identical parent, inventory, phase, and phase-
evidence values. `BASELINE_INTACT` maps to `INTACT_SAME_PHASE`; every other
history status maps to its same-named lineage status, with either history-
unknown status mapping to `TASK_UNKNOWN`. This overlap consumes no bundle twice.
For a result anchor, the phase-history tip establishes the predecessor phase and
the proposed bundle alone evaluates the result edge. If history is not intact,
the result edge and every newer dependent edge cannot claim an intact phase.
History `TASK_UNKNOWN` maps a readable result and every newer readable edge to
`TASK_UNKNOWN/DEPENDENT_ON_TASK_UNKNOWN`; an independent primary failure on an
edge retains its more specific task-unknown reason. History
`PROTECTED_CONFLICT` maps the readable result and newer edges to
`PROTECTED_CONFLICT/PHASE_CONTRADICTION` unless a primary task-unknown failure
occurs, which takes precedence.

Same-phase semantic equality remains intact even if another task changed a
shared carrier blob. A skipped phase, task-semantic removal, replacement,
normalization, unrecognized phase, or unauthorized task-path addition is
conflict when the necessary bytes are readable. Missing or unreadable task
evidence is unknown. Neither outcome erases classified lineage or
`result_seen`.

For `UNRELATED_OR_ABSENT`, every nonempty walk row is
`NOT_APPLICABLE/NO_ANCHOR`; an absent main has an empty walk. For `UNKNOWN`,
every readable-prefix row is
`NOT_APPLICABLE/PRE_ANCHOR_LINEAGE_FAILURE`. Both lineages require top-level
`NOT_APPLICABLE` and `result_seen=false`.

The decision table is:

| Lineage | Task state | Result |
| --- | --- | --- |
| `PREDECESSOR_EXACT` | `INTACT` | current authorization may attempt one push |
| `PREDECESSOR_DESCENDANT` | `INTACT` | fresh authorization required |
| `RESULT_EXACT` | `INTACT` | spent success; never push again |
| `RESULT_DESCENDANT` | `INTACT` | spent success; never push again |
| `RESULT_SIDE_ANCESTOR` | `PROTECTED_CONFLICT` | side-parent result; spent; never retry |
| either first-parent `RESULT_*` | `PROTECTED_CONFLICT` | result seen plus conflict; never retry |
| either first-parent `RESULT_*` | `TASK_UNKNOWN` | result seen plus unknown; never retry |
| either predecessor state | `PROTECTED_CONFLICT` | preserve and refuse |
| either predecessor state | `TASK_UNKNOWN` | preserve and refuse |
| `UNRELATED_OR_ABSENT` | `NOT_APPLICABLE` | preserve and refuse |
| `UNKNOWN` | `NOT_APPLICABLE` | preserve and refuse |

The result-seen decision is made before protected-path disposition. A conflict
cannot turn a spent result into an apparently unused predecessor.
Any lineage and task-state combination not listed is schema-invalid.

## 11. Review receipt document and report equality

### 11.1 Receipt document

There are exactly two review receipt documents, one per reviewer output
package. Each contains exactly four role receipt objects, for eight role receipt
objects total.

The route-input contract selects the receipt grammar. A normal
`BUILD_REVIEW_OUTPUT` accepts only `pontius-utility-review-receipt-v1`. A
rehearsal build accepts only one complete
`pontius-utility-bootstrap-review-receipt-v1` already bound by the rehearsal
selector. Its report, issuer ledger line, role rows, reviewed implementation
candidate, rule-6 packet, source projections, and author set are revalidated by
that bootstrap schema. It remains historical inert review data and is never
reclassified as an accepted raw-object-v5 receipt.

`pontius-utility-review-receipt-v1` has exactly:

| Key | Type |
| --- | --- |
| `amendment_sha256` | `sha256` |
| `candidate_manifest_sha256` | `sha256` of the reviewed candidate manifest |
| `candidate_oid` | `oid` of the reviewed candidate commit |
| `cold_input_commit_oid` | `oid` |
| `cold_input_manifest_sha256` | `sha256` |
| `cold_input_spec_sha256` | `sha256` |
| `defect_verdict` | `defect_verdict` |
| `design_justification_sha256` | `sha256` |
| `design_verdict` | `design_verdict` |
| `ledger_line` | `artifact_identity` |
| `plan_sha256` | `sha256` |
| `round_preregistration_byte_count` | `positive_count` |
| `round_preregistration_sha256` | `sha256` |
| `round_review_author_set_byte_count` | `positive_count` |
| `round_review_author_set_sha256` | `sha256` |
| `report` | `artifact_identity` |
| `reviewer_id` | `reviewer_id` |
| `reviewer_ordinal` | `ordinal` |
| `role_receipts` | exactly four role receipt objects |
| `round` | `round` |
| `schema` | exact schema literal |
| `schemas_sha256` | `sha256` |
| `source_projection_set_byte_count` | `positive_count` |
| `source_projection_set_sha256` | `sha256` |
| `task` | `task` |
| `utility_author_set_byte_count` | `positive_count` |
| `utility_author_set_sha256` | `sha256` |
| `verdict_date` | `date` |
| `workflow_sha256` | `sha256` |

A role receipt object has exactly:

| Key | Type |
| --- | --- |
| `capability_grammar_read` | exact `true` |
| `downstream_candidate_artifacts_read` | exact `false` |
| `role` | `role` |
| `source_population_read` | exact `true` |
| `source_projection_byte_count` | `positive_count` |
| `source_projection_sha256` | `sha256` |

Role receipts occur in this exact order: `runtime-owner`, `builder`,
`publisher`, `integrator`. A path or ordinal does not imply a role. The role literal and
source-projection identity are data in every object.
Those four rows reconstruct the canonical `pontius-source-projection-set-v1`
object byte-for-byte. Its byte count and SHA-256 equal the two receipt header
fields and the exact accepted set carried by the integrated packet and utility
acceptance authority. A well-formed row from another projection set refuses.

The two reviewer identities are distinct and neither appears in the complete
round-review-author set. Its union binds both the candidate-author set and the
utility-author set. The utility-author fields in each receipt header equal the
cold-input spec, all four role projections, packet artifact, and accepted
utility authority. The round-review-author fields equal the cold input,
preregistration, packet artifact, and complete operation input. This
distinctness rule does not require eight reviewer identities.

Both preregistration fields equal the cold-input spec and complete packet
artifact. The receipt reviewer and ordinal equal its selected reviewer slot.
Task, round, workflow, amendment, schemas, plan, source-projection set, and
finalizer selection reproduce the preregistration exactly.

`workflow_sha256` equals the cold-input workflow bytes and every packet repeat;
it is never filled from a reviewer's working checkout.

The cold-input commit/manifest pair is the immutable rule-6 packet handoff for
the implementation bootstrap and the integrated-packet parent for a later
raw-object-v5 output. The output commit's sole parent and the packet's workflow,
amendment, schema, plan, candidate, and manifest bytes must reproduce these
receipt fields, including the complete source-projection-set identity. Reusing
a report or role row under a different cold input refuses.

The receipt is the sole machine-readable semantic authority. It binds the
already complete report and issuer-authored ledger line. It does not contain a
receipt identity, output-manifest identity, output tree, or output commit.

### 11.2 Exact report and ledger equality

The report begins with exactly this six-line ASCII prefix, populated from the
receipt, followed by one blank line:

```text
Reviewer ID: <reviewer_id>
Candidate commit: <candidate_oid>
Manifest SHA-256: <candidate_manifest_sha256>
Defect verdict: <defect_verdict>
Design verdict: <design_verdict>
Design justification SHA-256: <design_justification_sha256>

```

Each label appears exactly once in the report. The report contains one heading
`## Design verdict` and its justification body ends immediately before the next
level-two heading or EOF. The SHA-256 of those exact body bytes, including their
final LF, equals `design_justification_sha256`. Ambiguous or duplicate headings
refuse. The report artifact identity in the receipt must match the raw report
bytes.

The ledger line is rendered entirely from receipt fields as:

```text
<date> | <task>/<round> | <reviewer_id> | defect=<defect_verdict> |
 design=<design_verdict> | candidate=<candidate_oid> |
 manifest=<candidate_manifest_sha256> | report=<report.path> |
 report_sha256=<report.sha256> LF
```

The displayed wrapping is editorial. Serialized bytes contain one physical
line, one ASCII space on each side of every `|`, and one final LF. The exact
rendered bytes must equal the bound ledger artifact. The finalizer copies those
bytes; it never reconstructs or normalizes them.

## 12. Self-excluding output manifest and review-slot observation

### 12.1 Output package and manifest

For ordinal `<NN>`, a review-output commit has the exact review-output ref from
section 1.3, the integrated packet as its sole parent, and exactly four added
paths:

```text
<task>/<round>/reviews/<NN>/report.md
<task>/<round>/reviews/<NN>/receipt.json
<task>/<round>/reviews/<NN>/ledger-line.txt
<task>/<round>/reviews/<NN>/manifest.sha256
```

All modes are `100644`. The first three paths are manifest members. The
manifest path is excluded from its own rows.

`pontius-review-output-manifest-v1` is a text-row grammar. Each row is:

```text
<sha256> SP SP <byte_count> SP SP <mode> SP SP <blob_oid> SP SP <path> LF
```

There are exactly three rows, sorted by the unsigned bytes of the complete row.
The paths are exactly the report, selector-selected receipt, and ledger paths.
Duplicate or
case-colliding paths, wrong object type, wrong mode, wrong byte count, wrong
blob OID, wrong SHA-256, extra tree change, or a manifest self-row refuses.

The communicated handoff is the permanent review-output ref plus the SHA-256
of the complete manifest bytes. That manifest digest is external and does not
appear in the manifest.

### 12.2 Single review-output observation

A slot object has exactly:

| Key | Type |
| --- | --- |
| `announced_handoff` | handoff object or `null` |
| `observed_oid` | `oid` or `null` |
| `ordinal` | `ordinal` |
| `ref` | derived review-output ref |
| `reviewer_id` | `reviewer_id` |
| `state` | `ABSENT`, `EXACT`, `DIFFERENT`, or `UNKNOWN` |

A handoff object has exactly `commit_oid` and `manifest_sha256`. Slots occur in
ordinal order.

`pontius-review-output-observation-v1` has exactly `round`, `schema`, `slot`,
and `task`. It is the publisher's complete authority for one reviewer output;
it contains no other ordinal, reviewer identity, ref, handoff, or state.

An absent ref is `ABSENT`, whether or not its issuer has announced a handoff.
A present ref without an announced handoff is `DIFFERENT`. With a handoff,
`EXACT` requires the exact ref target, sole-parent graph, four-path tree delta,
self-excluding manifest, selector-selected receipt, report equality, ledger
equality, reviewer, ordinal, and all four role rows. On a normal selector the
reconstructed source-projection set equals the integrated packet and accepted
utility authority. On a rehearsal selector it equals the bootstrap receipt,
review publication, fixture binding, and campaign selector; normal
preregistration and accepted-utility fields are absent. Both branches equal the
publisher authorization. A readable
mismatch is `DIFFERENT`; an unreadable or ambiguous state is `UNKNOWN`.

### 12.3 Independent finalizer slots

`pontius-review-slot-observation-v1` has exactly:

| Key | Type |
| --- | --- |
| `aggregate_state` | review aggregate state |
| `round` | `round` |
| `schema` | exact schema literal |
| `slots` | exactly two slot objects |
| `task` | `task` |

Slots occur in ordinal order and reuse the single-slot equations above. Only
the integrator receives this two-slot observation.

Aggregate precedence is `OUTPUT_UNKNOWN`, then `OUTPUT_CONFLICT`, then
`WAITING_FOR_REVIEWS`, then `OUTPUTS_READY`. Any `UNKNOWN` slot produces
`OUTPUT_UNKNOWN`; otherwise any `DIFFERENT` slot produces `OUTPUT_CONFLICT`;
otherwise any `ABSENT` slot produces `WAITING_FOR_REVIEWS`; exactly two
`EXACT` slots produce `OUTPUTS_READY`. One exact and one absent slot is
therefore `WAITING_FOR_REVIEWS`; it is not either fatal candidate-pair partial state and is
not a fatal partial publication. The slots are independent create-only outputs.

## 13. Finalizer authorization

### 13.1 Review finalizer

`pontius-review-finalizer-authorization-v1` is the only authorization for
`FINALIZE_REVIEWS`. It has exactly:

| Key | Type |
| --- | --- |
| `build_authorization_sha256` | `sha256` |
| `commit_metadata` | `commit_metadata` |
| `endpoint_id` | `endpoint_id` |
| `execution_projection_byte_count` | `positive_count` |
| `execution_projection_sha256` | `sha256` |
| `finalizer_id` | `actor_id` |
| `finalizer_commit_input_sha256` | `sha256` |
| `finalizer_commit_oid` | `oid` |
| `finalizer_tree_oid` | `oid` |
| `integrated_packet_oid` | `oid` |
| `input_projection_byte_count` | `positive_count` |
| `input_projection_sha256` | `sha256` |
| `main_predecessor_oid` | `oid` |
| `main_ref` | exact handoff-main ref |
| `object_build_receipt_sha256` | `sha256` |
| `operation` | exact `FINALIZE_REVIEWS` |
| `overlay_spec_sha256` | `sha256` |
| `phase_after` | exact `REVIEWS_FINALIZED` |
| `phase_before` | exact `PACKET_INTEGRATED` |
| `plan_sha256` | `sha256` |
| `protected_task_spec_sha256` | `sha256` |
| `protected_after_inventory_sha256` | `sha256` |
| `protected_before_inventory_sha256` | `sha256` |
| `rehearsal_case_id` | exact `null` |
| `rehearsal_step_ordinal` | exact `null` |
| `rehearsal_task_binding_id` | exact `null` |
| `repository_projection_sha256` | `sha256` |
| `round_preregistration_byte_count` | `positive_count` |
| `round_preregistration_sha256` | `sha256` |
| `round_review_author_set_byte_count` | `positive_count` |
| `round_review_author_set_sha256` | `sha256` |
| `role` | exact `integrator` |
| `role_projection_byte_count` | `positive_count` |
| `role_projection_sha256` | `sha256` |
| `role_table_instance_byte_count` | `positive_count` |
| `role_table_instance_sha256` | `sha256` |
| `route_selector` | `route_selector_identity` |
| `round` | `round` |
| `schema` | exact schema literal |
| `schemas_sha256` | `sha256` |
| `slots` | exactly two finalizer slot objects |
| `source_projection_set_byte_count` | `positive_count` |
| `source_projection_set_sha256` | `sha256` |
| `task` | `task` |

A finalizer slot object has exactly:

| Key | Type |
| --- | --- |
| `ledger_line` | `artifact_identity` |
| `manifest` | `artifact_identity` |
| `ordinal` | `ordinal` |
| `output_commit_oid` | `oid` |
| `output_ref` | derived review-output ref |
| `receipt` | `artifact_identity` |
| `report` | `artifact_identity` |
| `reviewer_id` | `reviewer_id` |

Slots occur in ordinal order and equal the two exact slot packages. The slot
observation is `OUTPUTS_READY`. Reviewers are distinct, all eight role receipt objects
are present, and every repeated identity is equal. Both receipt headers and all
eight rows reconstruct the one source-projection set named by this finalizer
authorization and the integrated packet. Each `manifest.sha256` equals the
announced handoff digest for that slot.
The authorization's source-projection-set count and digest equal the accepted
utility authority and the set repeated by its bound build authorization and
receipt. Its selected integrator projection is the matching set member.
Its repository-projection digest equals the bound `BUILD_MAIN_OVERLAY`
authorization and object-build receipt. The later launch dispatch carries the
complete owner-only preimage with that exact digest before the finalizer's first
read; it never enters a planner input row.
The complete round-review-author set equals both receipt headers, cold input,
preregistration, packet artifact, and operation input. Each selected reviewer
is absent from its author union.
Its preregistration fields equal every receipt header and the integrated
packet. `finalizer_id` equals the sole selected finalizer in that
preregistration.
`route_selector` has schema exact `pontius-round-preregistration-v1`; its byte
count and SHA-256 equal the two explicit preregistration fields. The launch
dispatch carries that complete owner-only document and repeats both null
rehearsal fields. A utility-rehearsal selector cannot authorize finalization.

The raw finalizer commit input has kind `REVIEW_FINALIZER` and exactly one
parent, `main_predecessor_oid`. The finalizer copies the verified report,
receipt, manifest, and issuer ledger bytes from both permanent output refs into
the fresh-main tree. The output commits are not finalizer parents. Their sibling
histories remain reachable through their permanent refs.
The raw input's author and committer fields equal `commit_metadata` exactly.
The bound main-overlay spec has kind `REVIEW_FINALIZER` and repeats those commit
and tree identities.
`build_authorization_sha256` names the exact `BUILD_MAIN_OVERLAY`
authorization, and `object_build_receipt_sha256` names its validated receipt.
Both repeat the overlay, commit input, tree, result, task, and round exactly.

The finalizer performs an ordinary fast-forward push of only
`refs/heads/main`, under an exact lease on `main_predecessor_oid`. It never
uses a non-fast-forward update. A changed predecessor requires a fresh
authorization and newly derived result commit. After every return, section 10
classifies main.

The authorization excludes its own digest and the later launch dispatch. The
finalizer commit message excludes authorization and dispatch identities, so
`finalizer_commit_oid` can be derived before this authorization is encoded.

### 13.2 Disposition intent

`pontius-disposition-record-v1` has exactly:

| Key | Type |
| --- | --- |
| `candidate_manifest_sha256` | `sha256` |
| `candidate_oid` | `oid` |
| `controller_decision` | disposition decision |
| `controller_id` | `reviewer_id` |
| `decision_date` | `date` |
| `disposition_report` | `artifact_identity` |
| `finalizer_commit_oid` | `oid` |
| `program_ledger_line` | `artifact_identity` |
| `review_verdicts` | exactly two disposition-review rows |
| `round` | `round` |
| `round_preregistration_byte_count` | `positive_count` |
| `round_preregistration_sha256` | `sha256` |
| `schema` | exact schema literal |
| `task` | `task` |

Disposition decision is exactly `READY_FOR_STAGE_5`, `REJECTED`, or `PARKED`.
A disposition-review row has exactly `defect_verdict`, `design_verdict`,
`output_commit_oid`, `output_manifest_sha256`, `reviewer_id`, and
`reviewer_ordinal`; rows occur in ordinal order and equal the two finalized
packages. `READY_FOR_STAGE_5` requires both defect verdicts CLEAN. It records a
controller decision but is not the evidence-repository ceremonial-commit
authorization.
The preregistration identity equals both review receipts and the finalizer
authorization, preserving the route under which this disposition is legal.
`candidate_oid` and `candidate_manifest_sha256` equal the candidate tuple in
both exact review receipts and output packages, the integrated packet's frozen
candidate record, and the cold-input candidate manifest. A receipt or record
for another candidate cannot be summarized into this disposition.

The controller completes the attributed disposition report and one program-
ledger fragment before this record. The report begins with exactly this ordered
five-line ASCII prefix, populated from the record, followed by one blank line:

```text
Controller ID: <controller_id>
Candidate commit: <candidate_oid>
Manifest SHA-256: <candidate_manifest_sha256>
Disposition: <controller_decision>
Review finalizer commit: <finalizer_commit_oid>

```

Each label occurs exactly once. Parsing stops at the mandatory blank line; an
alternate order, delimiter, duplicate label, missing LF, or value outside this
prefix refuses. The record binds the complete report and cannot name itself.
The ledger fragment is the canonical one-line rendering:

```text
<date> | <task>/<round> | <controller_id> | disposition=<decision> |
 candidate=<candidate_oid> | manifest=<candidate_manifest_sha256> |
 report=<report.path> | report_sha256=<report.sha256> LF
```

The displayed wrapping is editorial; serialized bytes are one physical line
with one ASCII space around every `|` and one final LF.

The report header values equal the record's controller, candidate, manifest,
decision, and finalizer fields byte-for-byte. The report and program-ledger-line
artifact identities in the later disposition intent equal the record's
`disposition_report` and `program_ledger_line` identities exactly. The overlay
rows use those same artifact identities; a repeated path, blob, byte count,
SHA-256, or header value that differs refuses.

`pontius-disposition-intent-v1` is the closed input named by a
`PUBLISH_DISPOSITION` transition authorization. It has exactly:

| Key | Type |
| --- | --- |
| `build_authorization_sha256` | `sha256` |
| `commit_metadata` | `commit_metadata` |
| `disposition_commit_input_sha256` | `sha256` |
| `disposition_commit_oid` | `oid` |
| `disposition_ledger_line` | `artifact_identity` |
| `disposition_record` | `artifact_identity` |
| `disposition_report` | `artifact_identity` |
| `disposition_tree_oid` | `oid` |
| `endpoint_id` | `endpoint_id` |
| `main_predecessor_oid` | `oid` |
| `main_ref` | exact handoff-main ref |
| `object_build_receipt_sha256` | `sha256` |
| `overlay_spec_sha256` | `sha256` |
| `phase_after` | exact `DISPOSITION_PUBLISHED` |
| `phase_before` | exact `REVIEWS_FINALIZED` |
| `plan_sha256` | `sha256` |
| `protected_task_spec_sha256` | `sha256` |
| `protected_after_inventory_sha256` | `sha256` |
| `protected_before_inventory_sha256` | `sha256` |
| `review_finalizer_commit_oid` | `oid` |
| `round` | `round` |
| `round_preregistration_byte_count` | `positive_count` |
| `round_preregistration_sha256` | `sha256` |
| `schema` | exact schema literal |
| `schemas_sha256` | `sha256` |
| `task` | `task` |

Before construction, the main observation finds
`review_finalizer_commit_oid` on the first-parent line, phase
`REVIEWS_FINALIZED`, and an intact protected inventory. The three controller
artifacts have exact paths `<task>/<round>/disposition.md`,
`<task>/<round>/disposition.json`, and
`<task>/<round>/disposition-ledger-line.txt`. The overlay adds those three blobs
and preserves every other byte. It retains the controller ledger fragment as a
disposition artifact but does not append it to task progress or the program
ledger.

The disposition record's `finalizer_commit_oid`, this intent's
`review_finalizer_commit_oid`, and the selected review-finalizer
authorization's `finalizer_commit_oid` are identical. That exact commit, not a
different commit with the same phase label, occurs on the intact first-parent
line and supplies the historical finalizer phase evidence.

The raw commit input has kind `DISPOSITION`, one parent equal to
`main_predecessor_oid`, and metadata equal to `commit_metadata`. The overlay
spec has kind `DISPOSITION` and repeats the result identities. Publication is
bound to the exact `BUILD_MAIN_OVERLAY` authorization and its validated object-
build receipt; every overlay, input, tree, result, task, and round identity is
equal. Publication is
an ordinary fast-forward of only handoff main under the exact predecessor
lease. Section 10 supplies reconciliation after every return. Result occurrence
is terminal under the same two-axis decision table.

Both preregistration fields equal the generic publication authorization, the
finalizer authorization, integrated packet, disposition record, and both
review receipts. A disposition cannot reinterpret a temporary-index or
historical round as raw-object-v5.

The intent does not authorize candidate acceptance by itself. Exact CLEAN and
design-verdict handling remains the controller's Stage 5 decision and is bound
in the disposition overlay bytes.

## 14. Runtime evidence and terminal success

`pontius-runtime-evidence-v1` binds final source and execution evidence for one
launch. Its root has exactly:

| Key | Type |
| --- | --- |
| `appcontainer_policy` | `canonical_document` |
| `askpass_adapter` | `canonical_document` or `null` |
| `audit_policy` | `bound_document_identity` |
| `authority_input_projection` | `canonical_document` |
| `authorization_sha256` | `sha256` |
| `bootstrap_admission_transfer` | complete admission-transfer-result object |
| `bootstrap_control_terminal_result` | complete control-terminal-result object |
| `bootstrap_projection` | `bound_document_identity` |
| `bootstrap_source_admission` | complete bootstrap-source-admission object |
| `broker_projection` | `canonical_document` |
| `broker_session_result_set` | complete broker-session-result-set object |
| `broker_sessions` | broker-session object array |
| `consumed_dispatch_record` | complete consumed-dispatch-record object |
| `controller_cancel_fact` | complete authenticated-cancel fact or `null` |
| `controller_channel_loss_fact` | complete controller-channel-loss fact or `null` |
| `controller_session` | complete controller-supervisor-session object |
| `capsule_population` | complete runtime-capsule-population object |
| `deadline_completion_observation` | complete deadline-completion-observation object |
| `dispatch_sha256` | `sha256` |
| `final_revalidation` | `canonical_document` |
| `git_environment_set` | complete `pontius-git-environment-set-v1` object |
| `loaded_image_set` | `canonical_document` |
| `loaded_module_set` | `canonical_document` |
| `job_binding_set` | complete job-binding-set object |
| `job_configured_limit_set` | complete job-configured-limit-set object |
| `job_quiescence_set` | complete job-quiescence-set object |
| `launch_input_projection` | `canonical_document` |
| `native_set` | `canonical_document` |
| `observation_scratch_projection` | `canonical_document` or `null` |
| `observation_scratch_teardown` | complete scratch-teardown object or `null` |
| `operation` | operation allowed for `role` |
| `operation_schedule` | `bound_document_identity` |
| `owner_wall_deadline` | complete `pontius-owner-wall-deadline-v1` object |
| `planner_launch_view` | `canonical_document` |
| `process_policy` | `bound_document_identity` |
| `process_lifecycle_set` | complete `pontius-process-lifecycle-set-v1` object |
| `pyconfig_projection` | `bound_document_identity` |
| `rehearsal_case_id` | frozen case ID or `null` |
| `rehearsal_step_ordinal` | `positive_count` or `null` |
| `rehearsal_task_binding_id` | `task_binding_id` or `null` |
| `repository_projection` | complete owner-only `repository_projection` object |
| `repository_mutex_lifecycles` | complete repository-mutex-lifecycle array |
| `repository_storage_observation` | `canonical_document` |
| `role` | `execution_role` |
| `route_selector` | `canonical_document` |
| `role_table_instance` | `bound_document_identity` |
| `role_source_projection` | `bound_document_identity` |
| `round` | `round` |
| `runtime_locked_attestation` | `canonical_document` |
| `runtime_projection` | `bound_document_identity` |
| `runtime_attestation_transfer` | complete attestation-transfer-result object |
| `schedule_execution` | complete schedule-execution object |
| `schema` | exact schema literal |
| `supervisor_preterminal_transcript` | complete supervisor-preterminal-transcript object |
| `supervisor_source_admission` | complete supervisor-source-admission object |
| `source_projection_set` | `canonical_document` |
| `source_set` | `canonical_document` |
| `system_image_set` | `canonical_document` |
| `task` | `task` |
| `worker_environment` | complete `pontius-environment-block-v1` object |
| `worker_launch_directory_projection` | complete `pontius-launch-directory-projection-v1` object |

Canonical-document schemas are exact: `appcontainer_policy` uses
`pontius-appcontainer-live-observation-v1`; nonnull `askpass_adapter` uses
`pontius-runtime-capsule-adapter-observation-v1`; `broker_projection` uses the broker
projection schema from the runtime appendix; `final_revalidation` uses
`pontius-runtime-final-revalidation-v1`; the five loaded/source population
fields use `pontius-runtime-loaded-image-set-v1`,
`pontius-runtime-loaded-module-set-v1`, `pontius-runtime-native-set-v1`,
`pontius-runtime-source-set-v1`, and `pontius-runtime-system-image-set-v1` as
named; `runtime_locked_attestation` uses `pontius-runtime-locked-v2`; and
`source_projection_set` uses `pontius-source-projection-set-v1`. Bound source
documents carry their exact named schema from the selected projection. A
schema-less byte digest is invalid for every field in this root.
The complete controller session, capsule population, bootstrap source admission,
admission transfer, attestation transfer, and control terminal result equal the
public ABI and lock-attestation bindings for this launch. Success requires
`SENT_ACCEPTED`, `SENT_ACCEPTED`, and `ATTACHED` in causal order.
The supervisor source admission is the complete accepted initial source
population for this public session. The preterminal transcript is the complete
accepted controller/output history through the last grant, cancel, or secret
request before the terminal wrapper; it contains no terminal output and equals
final revalidation byte-for-byte.
The cancel fact is null unless cancellation is the first terminal cause; then
it equals every cancellation-bearing nested fact and final revalidation.
The channel-loss fact is null unless controller-channel loss is the first
terminal cause; then it equals every channel-loss-bearing nested fact and final
revalidation. It is mutually exclusive with the cancel fact.
`planner_launch_view` uses `pontius-planner-launch-view-v1` and equals the sole
object passed to the selected Python callable. `observation_scratch_projection`
is null unless this schedule creates scratch storage; otherwise it uses
`pontius-observation-scratch-projection-v1` and its digest equals every planner-
visible scratch summary. `observation_scratch_teardown` is null exactly when
the scratch projection is null. Otherwise it uses
`pontius-observation-scratch-teardown-v1`, repeats that projection's digest,
and proves terminal removal or quarantine before this runtime-evidence object
and its semantic result may exist. `repository_storage_observation` uses
`pontius-repository-storage-observation-v1` and accounts for the complete
post-operation physical delta. Its operation equals this launch. Every
`OBJECT_WRITE_PLAN` provenance object equals
`schedule_execution.object_write_plan` byte-for-byte and repeats its digest.
Built- and fetched-inventory provenance equals the complete inventory assembled
from this schedule. The storage rows, expanded object-write results, and
semantic object population are a closed three-way relation; none may introduce
or omit a member.
`repository_mutex_lifecycles` is the execution-ordered, complete population for
every local-ref classification, mutation, and post-mutation observation in this
launch. Each action digest equals the corresponding dispatch input, retained
transaction, canonical observation, or milestone evidence. Each lifecycle has
an operation-specific prefix followed by the mandatory retention suffix.
Mutating schedules use prefix classify, mutate, observe; read-only classifiers
use classify. The suffix is object validation, process completion, remote
reconciliation unless the schedule is offline, receipt durability, Job
active-zero, and final-revalidation core. The core is complete before the last
milestone; the outer final-revalidation object does not exist until every
lifecycle is terminal `RELEASED` and `HANDLE_CLOSED`. The array contains no
failed acquisition on success. It is byte-identical to
`final_revalidation.repository_mutex_lifecycles`; the outer count and aggregate
digest reproduce this exact ordered population.
`askpass_adapter` is null exactly for builder and otherwise is the complete
retained capsule-destination observation. It equals
`final_revalidation.core.askpass_adapter` byte-for-byte.
`route_selector` uses exactly `pontius-round-preregistration-v1` or
`pontius-utility-rehearsal-selector-v1`. Its canonical bytes, schema, count, and
SHA-256 equal the authorization binding, owner-only dispatch field, and final
revalidation. It is absent from both input projections and every planner frame.
The three rehearsal fields equal the authorization, dispatch, and final
revalidation. They are all null for a normal selector and all nonnull for a
rehearsal selector. In the latter branch, the task-binding ID selects the
campaign row whose task and round equal the authorization, dispatch, runtime-
evidence root, and step result; the utility-selector root remains the bootstrap
identity.
Packet, cold-input, receipt, or intent equality is checked when the selected
operation carries a corresponding binding and otherwise follows through its
already validated authority chain.
`authority_input_projection` and `launch_input_projection` use exact
`pontius-operation-input-projection-v1` and
`pontius-launch-input-projection-v1`. They equal the authorization and dispatch
identities, their nested relation holds, and all held sources survive final
revalidation.
`repository_projection` equals the launch dispatch's complete owner-only field.
Its canonical byte count and digest equal the authorization payload, every
observation and receipt, and
`final_revalidation.core.repository_projection_sha256`. It is excluded from both
input projections and every `READ_OPERATION_INPUT` row; terminal evidence
cannot replace it with a digest-only or newly observed repository object.

`worker_environment` and `worker_launch_directory_projection` equal the
complete objects embedded in the launch dispatch and final revalidation byte-
for-byte. Their directory nonce equals this launch and the exact raw environment
block is rederived and rehashed from its entries before each terminal result.
`git_environment_set.dispatch_sha256` equals this launch. Its rows form a
bijection with every prepared Git-child launch coordinate. The
`CREATE_SUCCEEDED` subset forms a bijection with `GIT_CHILD` rows in
`process_lifecycle_set`, including the sole unassigned terminal boundary when
present; a `CREATE_FAILED` or `NOT_ATTEMPTED` boundary row instead has null
lifecycle digest and equals the ABORTED completion's typed termination stage;
only its reserved network branch also equals the pre-session stage. Each
assigned coordinate, grammar, directory projection, reservation digest, and raw
environment-block digest also equals its expanded row and held launch facts.
The complete set equals final revalidation byte-for-byte. Every held directory
identity and population rule survives Job active-zero; a missing, extra,
replayed, cross-coordinate, or digest-only environment is invalid.
`owner_wall_deadline` is the sole immutable two-deadline timeline derived after
durable dispatch consumption and equals final revalidation byte-for-byte. Its
launch, limit row, active wall, and cleanup reserve equal this evidence and
dispatch. Every process wall fact and broker reservation/result under this
launch embeds that same object; none may start or extend a child-local budget.
`deadline_completion_observation` has phase `ACTIVE_SUCCESS`, repeats that
timeline, and proves every nested success fact was complete before the active
deadline.
`job_configured_limit_set` bijects with `job_binding_set`, repeats this
dispatch and selected limit row, and equals final revalidation byte-for-byte.
Every active-process, CPU, and memory value is the post-configuration query of
the exact retained Job. A CPU or memory process-completion fact embeds the one
matching configured row and typed completion-port-plus-query trigger.
`process_lifecycle_set` contains the worker and every successful scheduled root
creation, equals final revalidation, and closes one-to-one against this
execution. Its assigned rows equal all process bindings; any unassigned boundary
row is permitted only by the associated ABORTED completion equation. Every row
is signaled before this terminal evidence can complete.

Every repeated identity equals the authorization, dispatch, accepted source
projection, and runtime evidence byte-for-byte. This document is completed only
after Job active-zero and final handle revalidation. `role_table_instance`
equals the exact instance named by the authorization and dispatch.
`consumed_dispatch_record` is the complete held durable record created and
flushed before this launch's first process creation; its dispatch digest and
nonce equal this launch exactly.
`source_projection_set` equals the complete set named by both documents. Its
runtime-owner member equals the held supervisor/bootstrap/broker population,
and its selected execution-role member equals `role_source_projection`.
`schedule_execution` is the complete canonical
`pontius-schedule-execution-v1` object. Its dispatch and static-schedule digests
equal this launch, its completion state is exact `COMPLETE`, and its expanded
rows reproduce every actual owner child before runtime evidence can complete.
Its complete local-ref transaction object, count, and digest equal the launch
dispatch, and every reached local transaction row retains the actual owner-to-
Git stdin-write fact. Success requires exact `COMPLETE` bytes and EOF; intended
ref rows or a later exact observation cannot substitute for the actual stream.
`broker_sessions` is empty when the selected schedule has no network step.
Otherwise it has exactly one row per expanded network child, in ascending
`(step_ordinal, repeat_ordinal)` order;
each row is the complete canonical `pontius-broker-session-v1` document and
equals that step's template digest, selected table-instance digest, dispatch
nonce, process binding, step ordinal, and repeat ordinal. Its digest equals the
expanded row's `broker_session_sha256`. A missing, extra, reused, reordered, or
mismatched session makes runtime evidence invalid.
`broker_session_result_set` is the complete canonical terminal-result set. Its
dispatch equals this launch, its digest equals
`schedule_execution.broker_session_result_set_sha256`, and each network row's
terminal-result digest names its unique matching complete result. Every session
has exactly one `SESSION_RESULT` row and vice versa; no
`PRESESSION_RESULT` row is valid in successful runtime evidence. Each session
result's embedded session is
byte-for-byte equal to the corresponding `broker_sessions` row and its
digest equals both the tagged row's result field and expanded schedule row.
The result-set population is exactly the successful-reservation population and
therefore equals the session population on success. Success additionally
requires each session result to have one request, one response,
`REDEEMED_ONCE`, a closed session, a
zeroed broker credential buffer, one `ADAPTER_COMPLETED` frame transfer, and one
exact held-adapter attempt with true scheduled Job membership. Missing,
extra, reordered, duplicate, mismatched, pre-session, unclosed, or nonzeroed results
invalidate success.

`pontius-built-object-inventory-v1` has exactly `object_count`, `objects`,
`operation`, `root_commit_oid`, `root_tree_oid`, `schema`, and
`source_input_sha256`. Object rows use section 8.1's object-row schema, sort by
OID, and form the complete newly required closure for the named tree and commit.
Its source-input digest equals the schedule's complete object-write plan and the
accepted build authorization's `input_projection_sha256`. Unlisted objects are
nonauthority residue and cannot satisfy the receipt.

`pontius-object-build-receipt-v1` has exactly `authorization_sha256`,
`commit_input_sha256`, `object_inventory_sha256`, `operation`,
`output_commit_oid`, `output_tree_oid`, `repository_projection_sha256`,
`role_projection_sha256`, and `schema`. `operation` is
`BUILD_REVIEW_OUTPUT` or `BUILD_MAIN_OVERLAY`. It proves deterministic object
construction but grants no ref or remote authority.
`role_projection_sha256` equals the selected role projection in the bound
authorization: builder for `BUILD_REVIEW_OUTPUT`, integrator for
`BUILD_MAIN_OVERLAY`. Repository projection, raw commit input, complete object
inventory, result commit, and result tree equal that same authorization and the
owner's complete assembled operation transcript. The inventory's
`source_input_sha256` equals the authorization input projection and the
schedule's object-write plan. An independently well-formed
but unrelated projection or object result cannot satisfy the receipt.

`pontius-operation-observation-set-v1` is the complete decisive observation
tuple for one operation. Its root has exactly `observations`, `operation`,
`role`, `round`, `schema`, and `task`. An observation row has exactly
`byte_count`, `kind`, `observation`, `schema`, and `sha256`. `observation` is
the complete canonical object named by `schema`; byte count and digest use its
canonical bytes plus LF. Rows occur in this exact operation-specific order:

- `FREEZE_PAIR`: `BUILDER_TUPLE:pontius-builder-tuple-observation-v1`.
- `ADOPT_PAIR`: `BUILDER_TUPLE:pontius-builder-tuple-observation-v1`.
- `BUILD_REVIEW_OUTPUT`:
  `EXPECTED_OBJECTS:pontius-expected-object-observation-v1`.
- `FETCH_MAIN_INPUTS`, in order:
  `SCRATCH_PROJECTION:pontius-scratch-observation-summary-v1`,
  `MAIN_PREDECESSOR:pontius-main-predecessor-observation-v1`,
  `PERMANENT_INPUTS:pontius-permanent-input-observation-v1`,
  `OPTIONAL_OBJECT_INVENTORY:pontius-optional-object-inventory-v1`, and
  `MAIN_INPUT_READINESS:pontius-main-input-readiness-observation-v1`.
- `BUILD_MAIN_OVERLAY`:
  `EXPECTED_OBJECTS:pontius-expected-object-observation-v1`.
- `PUBLISH_PAIR`, in order:
  `BUILDER_TUPLE:pontius-builder-tuple-observation-v1` and
  `REMOTE_PAIR:pontius-remote-pair-observation-v1`.
- `FETCH_FOR_ADOPTION`:
  `REMOTE_PAIR:pontius-remote-pair-observation-v1`.
- `PUBLISH_REVIEW_OUTPUT`:
  `REVIEW_OUTPUT:pontius-review-output-observation-v1`.
- `INTEGRATE_PACKET`, in order:
  `INTEGRATION_ATTEMPT:pontius-integration-attempt-observation-v1`,
  `REMOTE_PAIR:pontius-remote-pair-observation-v1`, and
  `MAIN:pontius-main-observation-v1`.
- `FINALIZE_REVIEWS`, in order:
  `REVIEW_SLOTS:pontius-review-slot-observation-v1` and
  `MAIN:pontius-main-observation-v1`.
- `PUBLISH_DISPOSITION`: `MAIN:pontius-main-observation-v1`.

The selected role-operation-set row repeats these `(kind, schema)` pairs as
its exact `observation_contracts`. Missing, extra, duplicate, reordered, wrong-
role, wrong-task, wrong-round, stale, or unreconstructible content invalidates
the whole set. A digest-only list is not an observation set.
For `FETCH_MAIN_INPUTS`, every readiness digest equals its preceding complete
row. The optional-inventory wrapper is null exactly when readiness is not
`INPUTS_EXACT`; at exact readiness its nested inventory digest equals the
readiness inventory digest. The readiness row is therefore summary, not a
substitute for the decisive bytes.

Every successful `OBSERVATION_ONLY` launch emits
`pontius-authority-observation-v1`. It has exactly `authorization_sha256`,
`dispatch_sha256`, `observation_set`, `observation_set_byte_count`,
`observation_set_sha256`, `operation`, `role`, `round`, `runtime_evidence`,
`runtime_evidence_byte_count`, `runtime_evidence_sha256`, `schema`, `task`,
`terminal`, `terminal_result`,
`terminal_result_byte_count`, `terminal_result_schema`, and
`terminal_result_sha256`. `observation_set` is the complete canonical set
above; its byte count and digest use canonical bytes plus LF. `terminal` is
boolean. All four terminal-result fields are `null` when it is false. When it
is true, `terminal_result` is the complete operation-result-map object and its
schema, byte count, and digest reproduce those bytes. The bound observation
set may report any wire state, including an eligible
predecessor, an absent ref, a terminal result, conflict, or unknown. A true
terminal value is valid only when the observation independently proves the
exact idempotent result and the result bytes can be reconstructed without an
authority mutation. It closes the operation and starts no mutation dispatch.
The envelope never grants mutation authority. `runtime_evidence` is the
complete canonical `pontius-runtime-evidence-v1` object; its byte count and
digest reproduce canonical bytes plus LF.

Every successful `MUTATION_ATTEMPT` operation emits
`pontius-authority-success-v1` as its only semantic stdout object. Its root has
exactly:

| Key | Type |
| --- | --- |
| `authorization_sha256` | `sha256` |
| `dispatch_sha256` | `sha256` |
| `operation` | operation allowed for `role` |
| `operation_result` | complete mapped canonical object |
| `operation_result_byte_count` | `positive_count` |
| `operation_result_schema` | exact mapped schema literal |
| `operation_result_sha256` | `sha256` |
| `reconciliation` | complete operation-observation-set object |
| `reconciliation_byte_count` | `positive_count` |
| `reconciliation_sha256` | `sha256` |
| `role` | `execution_role` |
| `round` | `round` |
| `runtime_evidence` | complete runtime-evidence object |
| `runtime_evidence_byte_count` | `positive_count` |
| `runtime_evidence_sha256` | `sha256` |
| `schema` | exact schema literal |
| `task` | `task` |

The operation-result map is exact. The result byte count and digest reproduce
the complete `operation_result` canonical bytes plus LF:

| Operation | Required schema and canonical result |
| --- | --- |
| `FREEZE_PAIR` | `pontius-builder-tuple-observation-v1` at `LOCAL_EXACT` |
| `ADOPT_PAIR` | `pontius-builder-tuple-observation-v1` at `LOCAL_EXACT` |
| `BUILD_REVIEW_OUTPUT` | `pontius-object-build-receipt-v1` |
| `FETCH_MAIN_INPUTS` | `pontius-main-input-fetch-receipt-v1` |
| `BUILD_MAIN_OVERLAY` | `pontius-object-build-receipt-v1` |
| `PUBLISH_PAIR` | `pontius-remote-pair-observation-v1` at `PAIR_EXACT` |
| `FETCH_FOR_ADOPTION` | `pontius-adoption-receipt-v1` |
| `PUBLISH_REVIEW_OUTPUT` | `pontius-review-output-observation-v1` at `EXACT` |
| `INTEGRATE_PACKET` | `pontius-main-observation-v1` with result lineage and `INTACT` |
| `FINALIZE_REVIEWS` | `pontius-main-observation-v1` with result lineage and `INTACT` |
| `PUBLISH_DISPOSITION` | `pontius-main-observation-v1` with result lineage and `INTACT` |

The same map governs a true observation-only terminal result. Exact local
tuples, built objects, remote publication slots, or main-result lineage may
close that way. Operations whose result requires a new fetch receipt cannot
claim terminal success from an input observation alone.

For a state-changing operation, `reconciliation` is the complete final fresh
operation-observation set and cannot be inferred from process exit or Git
output. Its byte count and digest reproduce the set bytes. For a build or fetch
operation it contains the required postcondition observation; the result is
the exact receipt. No success is emitted before final runtime evidence is
complete and every operation-specific state predicate above holds.
An exact durable result may accompany a decisive `TRANSPORT_FAILURE` only for
the typed lost-acknowledgement shape: the fresh reconciliation proves the exact
result and runtime evidence retains the failed transport outcome. Process return
alone never supplies this exception.
The complete runtime-evidence bytes and their byte count and digest obey the
same equality as the observation envelope; terminal authority never carries a
bare runtime-evidence digest.

## 15. Canonical refusal envelopes

Before a launch dispatch is accepted, the supervisor may emit
`pontius-protocol-refusal-v1`. Its root has exactly `code`,
`input_byte_count`, `input_sha256`, `schema`, `session_nonce`, and `stage`.
Stage is `SOURCE_ADMISSION_FRAME`, `AUTHORIZATION_FRAME`,
`DISPATCH_FRAME`, or `CONTROL_SEQUENCE`. Session nonce is the already
validated session. Input byte count
and SHA-256 cover the complete bounded frame bytes as received.

Protocol-refusal code is exactly `MALFORMED_JSON`,
`NONCANONICAL_BYTES`, `SCHEMA_MISMATCH`,
`KEY_SET_MISMATCH`, `TYPE_MISMATCH`, `DOMAIN_MISMATCH`,
`AUTHORIZATION_MISMATCH`, `DISPATCH_REPLAY`, `ROLE_MISMATCH`,
`OPERATION_MISMATCH`, `SEQUENCE_MISMATCH`, or
`PREDECESSOR_MISMATCH`. This object is valid only before the new dispatch
key is consumed and before any process or authority operation starts. It makes
no authority-state, residue, reconciliation, cleanup, or repository claim.
Oversized, truncated, or unreadable framing for which complete bounded input
identity cannot be produced returns `PONTIUS_HOST_FAILURE` and emits no
semantic object.
Malformed SESSION_OPEN has no validated nonce and also uses only host failure.
After dispatch consumption, malformed grant or opaque secret input never enters
this object; it follows typed cleanup without hashing secret bytes or uses host
failure when cleanup cannot complete.

After a valid dispatch has been consumed, malformed bootstrap or owner-channel
frames and every other classifiable launch failure use the authority-refusal
path below. The repeated generic code then describes an in-launch frame and is
backed by the accepted dispatch and phase-valid cleanup evidence. A preaccept
failure can never be upgraded to an authority refusal.

`pontius-failure-cleanup-evidence-v1` is completed by the trusted supervisor
after a consumed-dispatch launch failure and before an in-launch authority
refusal. Its root has exactly
`bootstrap_admission_transfer`, `bootstrap_control_terminal_result`,
`bootstrap_source_admission`, `capsule_population`,
`consumed_dispatch_record`, `controller_cancel_fact`,
`controller_channel_loss_fact`, `controller_session`,
`deadline_completion_observation`, `dispatch_sha256`, `final_revalidation`,
`job_quiescence_set`, `job_quiescence_set_byte_count`,
`job_quiescence_set_sha256`, `operation_input_projection`,
`operation_input_projection_byte_count`, `operation_input_projection_sha256`,
`process_created`, `process_lifecycle_set`, `process_lifecycle_set_byte_count`,
`process_lifecycle_set_sha256`, `repository_storage_observation`,
`repository_storage_observation_byte_count`,
`repository_storage_observation_sha256`, `runtime_attestation_transfer`, `runtime_evidence`,
`runtime_evidence_byte_count`, `runtime_evidence_sha256`, `schedule_execution`,
`schedule_execution_byte_count`, `schedule_execution_sha256`, `schema`,
`sticky_violation_state`, `supervisor_preterminal_transcript`,
`supervisor_source_admission`, `termination`, and `worker_launch_result`.
`consumed_dispatch_record` is the complete held
`pontius-consumed-dispatch-record-v1` durable record for the failed launch.
Its `authorization_sha256`, `dispatch_nonce`, `dispatch_sha256`, and
`plan_sha256` equal the accepted launch dispatch, and its state is exact
`CONSUMED`. It is not byte-equal to the dispatch document.
`controller_session`, `supervisor_source_admission`, and
`supervisor_preterminal_transcript` are complete canonical objects from the
accepted public session. Their source, authorization, dispatch, nonce,
predecessor, and message relations equal the consumed dispatch. The transcript
ends before the terminal wrapper and therefore introduces no cycle.
`capsule_population` and `bootstrap_source_admission` are both null exactly when
capsule construction never reached a complete retained population. Otherwise
both are complete and equal the attempted launch. The three transfer-result
objects are always present: before their bindings exist they use their exact
`NOT_PREPARED` branches; afterward they retain the actual prepared, prefix,
refused, channel-loss, accepted, EOF, and close facts. Cleanup may not invent a
successful transfer.
`controller_cancel_fact` and `controller_channel_loss_fact` are mutually
exclusive. Exactly the one selected by the first terminal cause is complete and
equals every nested process, broker, termination, final-revalidation, and
runtime-evidence carrier; both are null for every other cause.
`deadline_completion_observation` is the complete
`pontius-deadline-completion-observation-v1` object with phase
`FAILURE_CLEANUP`. It repeats this launch's owner timeline and is sampled only
after termination, every process signal, Job-zero, storage accounting, final
revalidation, and all other nested cleanup facts are immutable. A tick at or
after the cleanup deadline makes semantic cleanup unavailable and emits no
authority-refusal envelope.
The complete operation-input projection, positive byte count, and digest are
always present after a valid dispatch is consumed. They equal the launch
dispatch and its nested launch-input authority projection, even when the role
process or schedule cannot complete. Thus typed cleanup retains input provenance
without pretending that partial runtime evidence is complete.
`process_lifecycle_set`, its positive canonical byte count, and digest are
always present. `process_created` is true exactly when the set is nonempty; its
first row is then the worker. The remaining rows are every successful scheduled
root creation, including an assignment-failed boundary process absent from the
expanded prefix. Every row is directly waited signaled. Each assigned row maps
to one Job and each unassigned row uses direct preassignment termination.
Schedule completion's terminal lifecycle digest names the sole permitted
boundary row outside the accepted process-prefix relation.
`schedule_execution` is always a complete canonical
`pontius-schedule-execution-v1` object after dispatch consumption. Its positive
count and digest reproduce those bytes. It is `ABORTED` with an exact contiguous
prefix and cleanup-termination digest when schedule execution stopped, or
`COMPLETE` when failure occurred after the full schedule. Its broker-result-set
digest, transport outcomes, object-write plan, returned stored-object facts,
and terminal coordinate account for every fact reached before cleanup. Thus a
failure does not require a falsely complete success expansion and cannot omit a
started child or accepted prior reply.
`repository_storage_observation`, its byte count, and digest are all nonnull
exactly when the authority repository was opened. The observation uses
`pontius-repository-storage-observation-v1` and accounts for the actual physical
delta at cleanup. Its plan or built/fetched provenance equals the completed
schedule prefix; an unclassified carrier or residue prevents semantic refusal.
`final_revalidation` is a complete canonical
`pontius-runtime-final-revalidation-v1` object or `null`; it is nonnull whenever
a role process was created and obeys that schema's exact last-runtime-phase,
process-lifecycle-set, last-live-snapshot, and unavailable-observation equations.
Its worker environment and directory
projection equal the launch dispatch. Its Git environment set covers the full
prepared-coordinate population. The `CREATE_SUCCEEDED` subset forms the exact
bijection with Git-child lifecycle rows in this cleanup, including an unassigned
boundary creation. The sole `CREATE_FAILED` or `NOT_ATTEMPTED` boundary instead
has null lifecycle digest and exact called/error/cleanup-termination equality;
a reserved network row additionally equals its pre-session result, while an
offline row has null terminal broker digest. Assigned rows also equal nonowner
process rows in the COMPLETE execution or ABORTED prefix. An omitted prepared
row, a lifecycle without its prepared row, or cross-state substitution prevents
semantic refusal. The
complete `job_quiescence_set`, its positive
byte count, and digest are all present exactly when a role Job was created and
all null otherwise. It covers every retained binding and records exact active-
process count zero for each. Final revalidation's configured-limit set bijects
with the same bindings and re-queries each active-process, CPU, memory, and flag
value; a CPU or memory termination fact selects exactly one of those rows.
`runtime_evidence` is the complete canonical object when it
finished; its byte count and digest are all present with it or all null. Sticky
state is `CLEAR`, `SET`, or
`UNKNOWN`; only `CLEAR` can accompany success, while either other value remains
typed failure evidence.

`termination` is a complete `pontius-supervisor-termination-v1`
object. Its root has exactly `cause`, `controller_cancel_fact`,
`controller_channel_loss_fact`, `job_binding`, `job_limit_trigger_fact`,
`output_cap_fact`, `process_created`, `schema`, `source`, and
`wall_trigger_fact`. Cause is
`CPU_LIMIT_EXCEEDED`, `MEMORY_LIMIT_EXCEEDED`, `OUTPUT_CAP_EXCEEDED`,
`WALL_EXPIRED`, `CANCELLED`, `CONTROLLER_CHANNEL_LOST`, `BROKER_FAILURE`, or
`OTHER_FAILURE`. Source is
respectively `JOB_COMPLETION_PORT_AND_QUERY`,
`JOB_COMPLETION_PORT_AND_QUERY`, `SUPERVISOR_OUTPUT_COUNTER`,
`SUPERVISOR_OUTER_DEADLINE`, `AUTHENTICATED_CONTROLLER_CANCEL`,
`RETAINED_CONTROLLER_CHANNEL_AND_PROCESS`, `BROKER_SUBSYSTEM`, or
`INTERNAL_FAILURE`.
`output_cap_fact` is the complete object above exactly for
`OUTPUT_CAP_EXCEEDED` and null otherwise. `job_limit_trigger_fact` is the
complete typed fact above exactly for a CPU or memory cause, with equal kind,
and null otherwise. Its configured-limit row's Job binding equals the root.
`wall_trigger_fact` is the complete outer-deadline fact exactly for a wall cause
and null otherwise; it equals every affected process-completion and broker-
result fact byte-for-byte. Job binding is the complete affected held binding
for a Job-derived limit and otherwise the affected binding or null when no Job
was created. Process-created equals cleanup evidence. The typed outer timer or
completion-port event plus held-Job query, never a worker assertion, selects
cause.
`controller_cancel_fact` is complete exactly for `CANCELLED` and null
otherwise. `controller_channel_loss_fact` is complete exactly for
`CONTROLLER_CHANNEL_LOST` and null otherwise. The two are mutually exclusive
and equal every corresponding nested carrier.

Every classifiable role failure with a live controller/result peer emits
`pontius-authority-refusal-v1` as its only semantic stdout object. A selected
`PARENT_EXITED` loss performs the same bounded zeroization, process termination,
and Job-zero cleanup but emits no semantic object, exits host failure, and
leaves the durable consumed-dispatch record for a later fresh observation-only
dispatch. The root has exactly:

| Key | Type |
| --- | --- |
| `authorization_sha256` | `sha256` |
| `broker_session_result_set` | complete broker-session-result-set object |
| `code` | refusal code |
| `cleanup_evidence` | complete failure-cleanup-evidence object |
| `dispatch_sha256` | `sha256` |
| `authority_state` | authority-state value |
| `mutation_attempted` | boolean |
| `operation` | operation allowed for `role` |
| `reconciliation` | complete operation-observation-set object or `null` |
| `reconciliation_byte_count` | `positive_count` or `null` |
| `reconciliation_schema` | schema literal or `null` |
| `reconciliation_sha256` | `sha256` or `null` |
| `residue_state` | residue-state value |
| `role` | `execution_role` |
| `round` | `round` |
| `schema` | exact schema literal |
| `task` | `task` |
| `transport_outcome` | complete transport-outcome object or `null` |

Cleanup dispatch equals the refusal dispatch. The supervisor emits the outer
refusal only after every process in the exact held Job is gone, the final
revalidation completes when a role process existed, and required reconciliation
has completed or is explicitly unknown. If cleanup evidence itself cannot
complete, the supervisor emits no semantic authority object, returns the exact
host status `PONTIUS_HOST_FAILURE`, and the controller treats authority state as
unknown until a new observation-only dispatch classifies it.

Refusal code is exactly one of:

```text
MALFORMED_JSON
NONCANONICAL_BYTES
SCHEMA_MISMATCH
KEY_SET_MISMATCH
TYPE_MISMATCH
DOMAIN_MISMATCH
AUTHORIZATION_MISMATCH
ROLE_MISMATCH
OPERATION_MISMATCH
SOURCE_PROJECTION_MISMATCH
FILE_IDENTITY_MISMATCH
RUNTIME_NAMESPACE_MISMATCH
LATE_LOAD_BLOCKED
CAPABILITY_ROUTE_BLOCKED
OBJECT_GRAPH_MISMATCH
OBJECTS_DIFFERENT
OBJECTS_UNKNOWN
COMMIT_PREIMAGE_MISMATCH
LOCAL_TUPLE_PARTIAL
LOCAL_TUPLE_DIFFERENT
LOCAL_TUPLE_UNKNOWN
LOCAL_TUPLE_NOT_READY
INTEGRATION_ATTEMPT_PARTIAL
INTEGRATION_ATTEMPT_DIFFERENT
INTEGRATION_ATTEMPT_UNKNOWN
REMOTE_PAIR_PARTIAL
REMOTE_PAIR_DIFFERENT
REMOTE_PAIR_UNKNOWN
REMOTE_PAIR_NOT_READY
REMOTE_REJECTED
REMOTE_TRANSPORT_FAILURE
REMOTE_OUTCOME_UNKNOWN
ADOPTION_GRAPH_MISMATCH
ADOPTION_RECEIPT_MISMATCH
CREDENTIAL_BROKER_REFUSED
MAIN_PREDECESSOR_CHANGED
MAIN_PROTECTED_CONFLICT
MAIN_UNRELATED_OR_ABSENT
MAIN_UNKNOWN
MAIN_INPUTS_NOT_READY
MAIN_INPUTS_CONFLICT
MAIN_INPUTS_UNKNOWN
REVIEW_WAITING_FOR_REVIEWS
REVIEW_OUTPUT_CONFLICT
REVIEW_OUTPUT_UNKNOWN
REVIEW_CARDINALITY_MISMATCH
OUTPUT_CAP_EXCEEDED
CPU_LIMIT_EXCEEDED
MEMORY_LIMIT_EXCEEDED
WALL_EXPIRED
CANCELLED
CONTROLLER_CHANNEL_LOST
INTERNAL_INVARIANT
```

`authority_state` is exactly one of:

```text
UNCHANGED
OBSERVED
UNKNOWN
```

`residue_state` is exactly `NONE`, `SCRATCH_ONLY`, or
`UNREACHABLE_OBJECTS_ONLY`.
It is derived from the cleanup schedule execution, repository-storage
observation, and final-revalidation scratch state. `NONE` requires no added
authority-database carrier and no retained scratch. `SCRATCH_ONLY` permits only
the classified no-ref scratch projection. `UNREACHABLE_OBJECTS_ONLY` requires
every added authority-database carrier to have complete plan or built/fetched
provenance and fresh observation to prove that no authority ref or control file
changed. A caller label cannot select residue state.

For `OBSERVED`, all four reconciliation fields bind the complete canonical
operation-observation set. For `UNCHANGED`, all are null only when the owner
proves no authority mutation step began; a read-only set may instead be bound.
For `UNKNOWN`, they bind a complete set containing the canonical unknown
observation when one completed, or are all null when observation itself could
not begin. The object, byte count, schema, and digest are always all present or
all absent; present schema is exact `pontius-operation-observation-set-v1`.
Neither points to free-form stderr. Diagnostics are bounded, nonsemantic, and
absent from canonical evidence; any optional host rendering occurs outside the
protocol and cannot be retained as a receipt.

`broker_session_result_set` is the complete canonical reservation-terminal set,
including negative session reasons, zero-response outcomes, and pre-session
results. Its digest equals the cleanup schedule execution's exact field and its
population equals every successful reservation in the contiguous prefix plus a
successful boundary-coordinate reservation. When zero reservations were
created it is the canonical empty set. If reservation lifecycle accounting
cannot complete, cleanup evidence cannot complete and no semantic refusal is
emitted. Every completed negative result is self-contained through its embedded
immutable session or reservation. Outer
`CPU_LIMIT_EXCEEDED`, `MEMORY_LIMIT_EXCEEDED`, `WALL_EXPIRED`, `CANCELLED`,
or `CONTROLLER_CHANNEL_LOST` equals `cleanup_evidence.termination.cause`. When a
broker session was affected by cancellation, its terminal result is
`CANCELLED`; a successful reservation cancelled before session completion has
a `PRESESSION_RESULT/CANCELLED` row. Only an offline cancellation or a failure
before successful reservation carries the canonical empty result set.
When a live-parent channel loss affects a successful reservation, its terminal
row is `CHANNEL_LOST` and carries the byte-equal outer fact. Only an offline
loss or loss before successful reservation has the canonical empty result set.

`CREDENTIAL_BROKER_REFUSED` is exact for a `BROKER_FAILURE/BROKER_SUBSYSTEM`
termination or for any completed negative broker-session reason other than
`WALL_EXPIRED`, `CANCELLED`, or `CHANNEL_LOST`. Those reasons retain their matching outer
codes. `REDEEMED_ONCE` never supports broker refusal. A pre-resume route, table,
template, environment, pipe-policy, or reservation failure uses the broker
termination cause and requires the matching pre-session result whenever a
reservation already existed.
`OUTPUT_CAP_EXCEEDED` is exact if and only if cleanup termination has that cause
and carries the matching complete `pontius-output-cap-fact-v1`; its dispatch and
limit-row digests equal the refusal and launch dispatch.

`transport_outcome` is null when no network child began or when no complete
decisive outcome could be assembled before a host-level failure. Otherwise it
equals one complete member of the cleanup schedule execution's
`transport_outcomes`, selected by the matching immutable decisive-transport
rule. A
`REMOTE_REJECTED`, `REMOTE_TRANSPORT_FAILURE`, or `REMOTE_OUTCOME_UNKNOWN` code
requires respectively `REJECTED`, `TRANSPORT_FAILURE`, or `UNKNOWN` in that
object. A negative process or transport outcome uses that matching remote code
only when no more specific supervisor cause applies. CPU, memory, output-cap,
wall, cancellation, and broker causes retain their exact outer codes while the
transport object remains evidence of the affected child. A `SUCCESS` outcome
cannot accompany refusal. The object reports
only client transport and fresh-ref facts; rehearsal-only server events never
enter this envelope.

The state-specific refusal codes must bind matching observations: every
`LOCAL_TUPLE_*`, `REMOTE_PAIR_*`, `OBJECTS_*`, `MAIN_*`, and `REVIEW_*` code
equals the corresponding wire state in that observation. A partial remote pair,
protected conflict, output conflict, or unknown observation can never be paired
with a success predicate. A seen main result is success only under the exact
result-lineage-plus-`INTACT` terminal map; when paired with protected conflict or
task unknown it is refusal evidence and can never authorize another push.

The exact state-code equations are:

| Code | Bound observation predicate |
| --- | --- |
| `LOCAL_TUPLE_NOT_READY` | `tuple_state=LOCAL_ABSENT` when exact is required |
| `LOCAL_TUPLE_PARTIAL` | `tuple_state=LOCAL_PARTIAL` |
| `LOCAL_TUPLE_DIFFERENT` | `tuple_state=LOCAL_DIFFERENT` |
| `LOCAL_TUPLE_UNKNOWN` | `tuple_state=LOCAL_UNKNOWN` |
| `INTEGRATION_ATTEMPT_PARTIAL` | `state=ATTEMPT_PARTIAL` |
| `INTEGRATION_ATTEMPT_DIFFERENT` | `state=ATTEMPT_DIFFERENT` |
| `INTEGRATION_ATTEMPT_UNKNOWN` | `state=ATTEMPT_UNKNOWN` |
| `REMOTE_PAIR_PARTIAL` | either `PAIR_PARTIAL_*` state |
| `REMOTE_PAIR_DIFFERENT` | `pair_state=PAIR_DIFFERENT` |
| `REMOTE_PAIR_UNKNOWN` | `pair_state=PAIR_UNKNOWN` |
| `REMOTE_PAIR_NOT_READY` | `pair_state=PAIR_ABSENT` when exact is required |
| `OBJECTS_DIFFERENT` | expected-object aggregate `OBJECTS_DIFFERENT` |
| `OBJECTS_UNKNOWN` | expected-object aggregate `OBJECTS_UNKNOWN` |
| `MAIN_INPUTS_NOT_READY` | readiness `INPUTS_NOT_READY` |
| `MAIN_INPUTS_CONFLICT` | readiness `INPUTS_CONFLICT` |
| `MAIN_INPUTS_UNKNOWN` | readiness `INPUTS_UNKNOWN` |
| `MAIN_PREDECESSOR_CHANGED` | predecessor descendant with `INTACT` |
| `MAIN_PROTECTED_CONFLICT` | anchored lineage with `PROTECTED_CONFLICT` |
| `MAIN_UNRELATED_OR_ABSENT` | `UNRELATED_OR_ABSENT` |
| `MAIN_UNKNOWN` | lineage `UNKNOWN` or task state `TASK_UNKNOWN` |
| `REVIEW_WAITING_FOR_REVIEWS` | `WAITING_FOR_REVIEWS` |
| `REVIEW_OUTPUT_CONFLICT` | single slot `DIFFERENT` or aggregate `OUTPUT_CONFLICT` |
| `REVIEW_OUTPUT_UNKNOWN` | single slot `UNKNOWN` or aggregate `OUTPUT_UNKNOWN` |

The envelope cannot claim rollback or retry authority. `mutation_attempted`,
`authority_state`, `residue_state`, and the bound fresh observation report what
remains. The controller derives any later action from the operation's normative
decision table and a new observation-only dispatch; timeout or a refusal code
alone never authorizes retry.

## 16. Cross-schema validation gates

An implementation is schema-complete only if independent tests establish all
of these relations at public boundaries:

1. Every JSON fixture re-encodes byte-for-byte and every alternate spelling,
   unknown key, duplicate key, wrong order, and wrong scalar domain refuses.
   Raw-byte fixtures independently cover LF, quote, and backslash escaping.
2. Every role projection enumerates the complete role population and exact
   operation grammar. Cross-role requests refuse before repository, credential,
   Git, or network access.
3. Every raw commit kind is reproduced by an independent byte writer and object
   parser under different clocks and poisoned Git identities.
4. Every proper subset and wrong target of both local ref tuples refuses. All
   local classifiers and transactions demonstrably hold the shared mutex.
5. Both remote pair partial states are fatal. Review-slot exact/absent
   combinations remain `WAITING_FOR_REVIEWS`.
6. Adoption reproduces the original builder-intent bytes and excludes its
   receipt and adoption authorization from those bytes.
7. First-parent interleavings compare result before predecessor and retain
   `result_seen` through a later protected conflict.
8. Two review packages produce two receipt documents and exactly eight role
   receipt objects. Report, ledger, manifest, ref, parent, and four-path tree
   identities all agree.
9. The finalizer result is a one-parent child of fresh H main, copies exact
   output bytes, and leaves both sibling output commits reachable from their
   permanent refs.
10. A static dependency check rejects every prohibited self-reference and
    verifies the DAG in section 2.
11. The role cross-product proves builder has no askpass adapter and publisher
    and integrator have exactly one held capsule adapter. Reservation, client
    process image, schedule-Job membership, final revalidation, and runtime
    evidence all reproduce its same live file identity.
12. A structural broker-boundary check proves the broker maps only to the held
    runtime-owner supervisor identity and has no process launch, Job, token,
    environment, stdio, executable-selector, or inherited-handle route of its
    own. Secret material is absent from every canonical byte population.
13. The Stage 0b H packet binds the complete external interface inventory and
    round counter. Independent reviewer inventories reproduce it. The total
    decision table selects BUILD, one exact successor, or ADR-0482 gate-defect
    parking, and only BUILD reaches implementation or utility acceptance.
14. A missing, malformed, wrong-controller, or non-authorizing implementation-
    controller disposition refuses before raw P construction or push. Tests
    independently substitute every P/H commit identity and parent: candidate,
    P result, H integration record, and H durable disposition are pairwise
    distinct; the record binds the P result; and durable history preserves the
    record.

This appendix supplies closed data and byte contracts. OS namespace isolation,
credential monotonicity, HTTPS server capability, Job containment, and timeout
calibration remain later implementation and rehearsal gates; a canonical
receipt cannot substitute for that evidence.
