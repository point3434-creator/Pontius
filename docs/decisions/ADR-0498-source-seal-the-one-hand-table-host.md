# ADR-0498: Source-seal the one-hand table host

- Status: accepted source-only seal upon its separately authorized decision commit
- Date: 2026-09-06
- Follows: ADR-0497
- Base-Commit: 7aefc238b2f82edb5866233ca6e91cbd80ef6529
- Invocation-Authority: none; operating, experimental and rehearsal execution remain closed
- Front-Door-Kind: controller-v1
- Front-Door-Research: ADR-0280
- Front-Door-Process: ADR-0498
- Front-Door-Contract: ADR-0307
- Front-Door-Revoked: ADR-0281, ADR-0468, ADR-0472, ADR-0475
- Front-Door-Active-Next: Select bounded terminal/session source task; operating/research closed
- Front-Door-Blockers: operating budgets, authoritative population and invocation remain closed

## Decision

Accept the exact reviewed one-hand reactive table host r001 as a CPU-only source
asset. This closes the source acceptance opened by ADR-0497. A local dealer owns
one finite six-seat deal, runs five declared simple opponents, and applies the
controlled Pontius child's actual returned actions through the existing public
betting kernel. Opponents react to the resulting state. Complete fold, showdown
and unequal-stack all-in hands now have verified end-to-end correctness controls.
Terminal interaction, repeated hands and stronger decision machinery remain next work.

Effect requires the separately authorized decision commit. A working ADR,
generated STATUS, review ref or passing test run does not activate this seal.
Incorporate the exact 13-path payload below, this new ADR and generated STATUS
only. No workflow-rule adjustment or further implementation change belongs here.

## Bound source identity and exact scope

Task: `v0a-table-host-impl/r001`.
Commit: `1750ad90d12101f33764be9416c06045f1f2b9f9`.
Base: `7aefc238b2f82edb5866233ca6e91cbd80ef6529`.
Tree: `a6165c25be05f0f6506fc335c366d1f5f65d3a34`.
Manifest SHA-256:
`3fff50dc86c948d616459723c22b16d6ff1e74b2060faf2e4d5f9a007c58c1f9`.

These paths must have the candidate's raw frozen blob bytes:

- `.github/workflows/ci.yml`
- `tests/fixtures/table_host/empty_blueprint.json`
- `tests/fixtures/table_host/fold_table.json`
- `tests/fixtures/table_host/showdown_table.json`
- `tests/fixtures/table_host/sidepot_table.json`
- `tests/test-inventory.json`
- `tests/test-profiles.toml`
- `tests/test_inventory_and_profiles.py`
- `tests/test_v0a_table_host.py`
- `tests/test_v0a_table_host_boundary.py`
- `tools/check_stabilization_boundaries.py`
- `tools/generate_test_inventory.py`
- `tools/v0a_table_host.py`

Adopt ADR-0497's bounded input, strict wire/diagnostic validation, dealer-only
complete deal, per-seat public observations, actual-action application and
failure-retention contract. An applied action survives a later protocol, exit or
cleanup failure. Settlement publication requires matching independent host and
child settlement plus successful hand/session reports, EOF, clean exit and clean
native cleanup. Source/input identity checks run before launch and before success.

The host's inherited source base remains
`1329c2c201bbf2f396946f2ebf460ee944ae4ece`. All src/pontius bytes and the three
prior adapter/driver tools remain unchanged. The sealed event adapter's source
pins, delivery/accounting semantics, 15-second action wall and reserve are unchanged.
Only public Pontius interfaces are used. Popen._handle remains the sole private
CPython dependency, confined to native job assignment.

Record the reviewed native launch refinement explicitly. CREATE_SUSPENDED holds
the Windows venv redirector until its real process handle has been assigned to
the non-inheritable kill-on-close job. Public native thread APIs resume its unique
initial thread; missing, ambiguous or failed resources cause refusal and cleanup.
The fixed cooperative G gate remains before bot execution. This closes the
observed interval in which an already running redirector could spawn the actual
interpreter outside the job. Both source reviewers found the refinement compatible
with the adopted containment contract. Real tests observe actual bootstrap and
descendant membership and termination on both supported interpreters.

After the byte gate, the bootstrap restores only the validated existing
executable-relative Lib/site-packages directory needed by inherited imports.
The -S flag remains set; site and .pth startup hooks are not executed.
This adds no older tool edit or further private interface.

The six registration exceptions remain within the exact source opening. All
2892 old inventory rows and 430 old payloads remain exact and in order; 50 new
test methods and two new payloads are registered. The unchanged analyzer's full
old census observations are preserved with verified source-location mapping.
New-suite additions are 27 analyzed sites, 203 helper edges, 3 decoys and 59
blockers; all 141 expanded capability rows remain exact. The complete downstream
count, digest, reason and location assertions pass on both actual interpreters.
Their predicates and all old IDs remain intact. Capability bindings remain zero.
Generator inference is unchanged and remains known unsound under ADR-0486;
this registration supplies no analyzer-safety claim or standing mutation exception.

Final use: 960/1200 production LF lines, 1156/1600 combined new-test LF lines,
four fixtures totaling 1905/16384 bytes and 80/200 manual registration add/remove lines.

## Review lineage and final acceptance

Both independent fresh Tier C source reviews are CLEAN, Spec PASS, Quality PASS,
C/I/M 0/0/0, Design SOUND, with no required correction. Original reports remain
unchanged under D:/Pontius/tmp/v0a-table-host-impl-r001/packets/r001/:

- `reviews/review-a.md`, SHA-256
  `8dc5e4b833ac279df523fba0f27240466dd1ebc158d5ef813bc6deee3759625e`.
- `reviews/review-b.md`, SHA-256
  `5bc8f5e358aefa551dbbbe06c4caf244b27cf5aa2588cd47ab1c7d0eb76ccdc6`.

r001 is the initial and only issued source candidate. All original development
failures, diagnostics, snapshots and receipts remain retained. These include the
real redirector escape and failing descendant-membership control before the
suspended-start correction, plus the registration-order and census-refresh
iterations before freezing. No earlier failure is relabeled as a pass.
Review A's initial non-package unittest invocation did not load either intended
suite; corrected direct-file invocations passed in fresh snapshots. Initial denied
3.14 preflights remain distinct from later permitted fresh native runs.

After both reviews, all 23 declared acceptance commands passed on CPython
3.11.15 first, then 3.14.6. Per interpreter, 19 named suites reported 421/421 tests
passing with zero failures, errors or skips, including all 91 inventory tests.
The two additional minimum decimal-conversion controls passed at
int_max_str_digits=640. Generator --check and the real boundary gate passed.

All 46 commands ran from fresh exact-r001 D-local snapshots with actual
interpreter/module-origin preflights, -B -P, snapshot-root cwd/src, scrubbed
environments and absolute PONTIUS_GIT. Native permissions were used where needed.
Under the source packet root above, final evidence is retained as:

- `checks/final-acceptance-summary.json`, SHA-256
  `4c6c12d3c09fd16dbd3218212b9d122a6c1f02e95ddd970411d4c5bbb07e0294`.
  This indexes all original final receipts, their hashes and the exact population.
- `disposition.md`, SHA-256
  `2486db8ba59f0533b3fa99dfbd5c66d04828189ab8ccaba7315a7c68099fc01a`.

These are bounded local results, not a hosted CI or Ruff pass. Expected negative
CLI diagnostics remain in the original outputs; terminal unittest summaries and
process exits determine acceptance. Independent literal action/pot/stack and
tie/odd-chip expectations supplement agreement with the shared public kernel.
The 256-action/event exhaustion branches are structurally bounded but were not
dynamically exhausted. No arbitrary failure-schedule or operating-liveness claim follows.

The source receipts predate this ADR and STATUS. Following ADR-0491/0494/0496's
faithful incorporation precedent, integration metadata must separately pass one
fresh independent Tier A light review, the unchanged status generator check and
its complete 12-test suite on 3.11.15 then 3.14.6 in fresh snapshots. Verify all
13 payload blobs against r001 and the complete 15-path integration delta.
A mismatch stops incorporation. This metadata review does not replace either
Tier C source review and creates no review waiver.

## Next boundary and exclusions

Select the bounded terminal/session source task separately. This seal grants no
rehearsal, operating hand, repeated-hand invocation, experiment, arbitrary data
use, random-deal generation, policy selection, timing study or strategic claim.
Correctness fixtures are not an admitted operating population; source watchdogs
are not measured operating budgets. Future neural, self-play and league reuse
remains compatibility context. No training or strength evaluation is introduced.
ADR-0307 and the unadmitted operating boundaries in ADR-0485/0489 remain binding.
Gate 13, capability-analyzer repair, H32/instrumentation, campaign and compiled
work remain parked. No consumed owner or rejected scientific identity is revived.
No cleanup or ref retirement is authorized by this decision.
