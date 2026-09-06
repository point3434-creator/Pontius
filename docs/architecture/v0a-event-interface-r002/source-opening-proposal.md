# One-hand event interface: source-opening proposal r002

Status: unadopted proposal. Base: 5f90279ab3d7d78fe790b115a697c52262280c0d.
Task: v0a-event-interface-design/r002. No implementation or invocation authority.

## Proposed decision

After design review and exact authorization, open the source-only implementation
of brief.md and design.md. Adopt their explicit raw-frame receipt and local pipe
delivery and accounting/reporting boundaries for this new tool only. The two
public preparation totals end before hand_result publication; its publication
is measured separately and session_result is the declared external host receipt.
Bootstrap before begin_host_accounting and transport of that closing receipt
are outside these totals, with no full-process cost or operating claim.
For this tool's host reporting, the existing trace_write_failed code denotes
frame serialization/write failure, without implying a persisted trace exists.
ADR-0485's existing in-memory host
and every historical measurement retain their exact meaning. The new boundary
does not alter ADR-0307's 15-second wall, 1-second reserve or preparation rules.
It grants neither an operating run nor an arbitrary-peer liveness claim.

Prospectively permit this tool's named dispatch-shell private dependencies as
listed in design.md, pinned to runtime blob
1c855b3b5e8f2d057105128733f43279b9f73990. No runtime/ledger/witness mutation,
substituted sample, second authority ledger or other private access is opened.

## Exact proposed additions

- tools/v0a_event_adapter.py
- tests/test_v0a_event_adapter.py
- tests/test_v0a_event_adapter_boundary.py
- tests/fixtures/event_adapter/fold_blueprint.json
- tests/fixtures/event_adapter/showdown_blueprint.json

Those are the only fixture additions; the repeated-action case uses the fold
policy and separately declared test events. There is no new src/pontius module,
dependency, owner,
launcher, general JSON protocol package, trace format or proof framework.

Permit direct internal imports only from pontius.blueprint_artifact.codec,
pontius.v0a.model, pontius.v0a.runtime, pontius.v0a.clock and pontius.v0a.trace.
The exact standard-library allowance is __future__, argparse, hashlib, io, json,
msvcrt, os, pathlib, re, stat, subprocess and sys. No other module, networking,
GPU, dynamic policy execution or policy search is admitted.

## Six proposed current-file registration exceptions

Each raw Git blob below must still match at opening. Prospectively supersede
sealed-current-file immutability only for these exact registration deltas:

- tools/check_stabilization_boundaries.py, blob
  4d8261db59e56dfad21cd746e1ae8861f9a704c4: classify the one tool; admit only its
  specified imports, including the codec incoming edge; retain old predicates.
- tools/generate_test_inventory.py, blob
  f08097686d7b747d082c0fec99db45015a35458d: register the two exact new test files
  in the existing CPU-only treatment; no inference change.
- tests/test-inventory.json, blob
  41435dc113d3e40c8916117f1cd6cb5920c6dc53: mechanically generated new test rows
  and required derived identities only.
- tests/test-profiles.toml, blob
  4b2e5ecb1750819e524bfbcf9581e999522fa270: mechanical regeneration for the two
  suites; no capability grant or broadened profile.
- tests/test_inventory_and_profiles.py, blob
  e6ec7b00abe415433d25bd13b031755efb3423ff: add the two suite names to existing
  registration expectations in generated order; preserve old assertions/rows.
- .github/workflows/ci.yml, blob
  c17c0561dfb7fe5c8fd06a06b606d8edb4baf2d2: add two direct CPU suite steps with
  existing invocation conventions; preserve all old gates.

Carry ADR-0486's registration-only, zero-grant treatment into this exact source
task; analyzer inference remains parked and known unsound. No old row, historical
ID, legacy edge, SCC restriction, core/policy boundary or CI gate is removed.
If unchanged generation cannot register this surface, stop and return.

## Future acceptance and stop

One initial implementation candidate and at most one bounded correction, two
independent Tier C passes on each substantive candidate. ADR-0492's mechanical
route requires independent qualification; it never silently transfers verdicts.
Apply the brief's size limits and every acceptance behavior in the design.

Initial focused checks: the two new suites and the real boundary gate. After
CLEAN review, run their union with these unchanged named CPU suites:

- tests/test_hand_scenario.py
- tests/test_v0a_hand_adapter.py
- tests/test_hand_adapter_boundary.py
- tests/test_blueprint_artifact.py
- tests/test_blueprint_artifact_boundary.py
- tests/test_v0a_hand_replay.py
- tests/test_v0a_trace.py
- tests/test_v0a_replay.py
- tests/test_v0a_contract_faults.py
- tests/test_immutable_blueprint.py
- tests/test_no_limit_betting.py
- tests/test_holdem_cards.py
- tests/test_action_clock.py
- tests/test_legal_decision_spine_v2.py
- tests/test_inventory_and_profiles.py

Also run tools/generate_test_inventory.py --check and the repository boundary
check. Run event integer/JSON controls at int_max_str_digits=640 on each slot.
Use fresh D-local snapshots, actual interpreter/origin preflight, 3.11.15 first
then 3.14.6, -B -P, snapshot-root cwd/src, scrubbed environment and absolute Git.
Record blocked attempts; no substituted floor, wildcard or research profile.

Stop before a third implementation candidate, scope/budget expansion, sealed
core change, generalized private access, new evidence/transport framework,
analyzer repair or any claimed operating/scientific use. No source acceptance
is established until the future implementation actually passes these checks.

## Adoption boundary

This document is a proposed source opening, not an accepted ADR. After design
acceptance, a separately authorized decision may incorporate the exact reviewed
brief, design and this proposal plus its new ADR and generated STATUS only.
Faithful incorporation needs the applicable independent metadata review and
status generation checks on both interpreters. Never hand-edit STATUS.
The original design packet/reviews remain immutable. There is no standing
authorization for that commit, source implementation, publication or operation.
