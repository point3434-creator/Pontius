# One-hand reactive table host: source-opening proposal r001

Status: unadopted proposal. Task: v0a-table-host-design/r001.
Base: 1329c2c201bbf2f396946f2ebf460ee944ae4ece. No implementation authority yet.

## Proposed decision and scope

After accepted design review and exact decision authorization, open the bounded
source-only implementation in brief.md and design.md. The external table applies
the bot's returned action semantically while preserving the event adapter's
distinct local-byte delivery receipt. It adds no acknowledgement to the bot wire,
extends no action wall and changes no existing receipt or accounting meaning.

Exact additions:

- tools/v0a_table_host.py
- tests/test_v0a_table_host.py
- tests/test_v0a_table_host_boundary.py
- tests/fixtures/table_host/fold_table.json
- tests/fixtures/table_host/showdown_table.json
- tests/fixtures/table_host/sidepot_table.json
- tests/fixtures/table_host/empty_blueprint.json

No new src/pontius package/module, external dependency, shared launcher library,
policy interface, trace format, authority file or generic transport framework.
Use the existing event-adapter fold blueprint unchanged for the fold control.

Direct internal imports are restricted to pontius.blueprint_artifact.codec,
pontius.no_limit_betting, pontius.holdem_cards, pontius.legal_decision_spine_v2,
pontius.v0a.model and pontius.v0a.trace, public names only. Never import a bot
runtime/old tool or invoke selection to predict the child action. The explicit
complete-deal allowance belongs only to this host, never to the controlled policy.
Allow standard library __future__, argparse, base64, ctypes, dataclasses, hashlib,
io, json, math, os, pathlib, queue, re, stat, subprocess, sys, threading and time.
The fixed bootstrap additionally imports runpy after its release gate. Only
Popen._handle is admitted as a private CPython dependency, for job assignment;
no new private Pontius dependency is permitted.

## Six exact current-file registration exceptions

Check these raw base blobs before implementation. Supersede current-file sealing
only for the following prospectively admitted changes:

- tools/check_stabilization_boundaries.py, blob
  3cee624d2a8266535df90027eabcd944e598dde4: classify the new host and precisely
  allow its imports/codec incoming edge; preserve all prior rules and allowlists.
- tools/generate_test_inventory.py, blob
  aa7ee446bec91a86be4dc3c3a8c339a872db8e63: register the two new suites in the
  existing CPU treatment; no inference, capability, profile or analyzer repair.
- tests/test-inventory.json, blob
  674bcebad9794de56f615131ca3f60e67c5a1680: unchanged generator's new test rows
  and required derived identities only; preserve every old row and test ID.
- tests/test-profiles.toml, blob
  7d0b4e644b62d1e3a6e098353d68d5e52edb0a00: mechanical regeneration for the two
  suites, retaining old membership/order semantics and zero capability grants.
- tests/test_inventory_and_profiles.py, blob
  596afff4e3d5fe618eab638b525f5f48c778e21d: add new suite names to registration
  expectations and prospectively refresh only derived current-source census
  expectations in CheckedInInventoryTests.
  test_working_discovery_binds_every_entry_and_introduced_id.
- .github/workflows/ci.yml, blob
  7f395c0afe6fe4ecf1ee6771ab4521d65ac2f997: add the two direct CPU suite steps
  following current invocation conventions; preserve every old gate.

The census exception includes complete counts, digests, reason counts and source
locations affected by the newly admitted suites and registration insertions. It
does not permit altered predicates, discarded old observations, new analyzer
behavior, weakened assertions or changed existing test IDs. Before refreshing,
compare the unchanged real analyzer output against the accepted base on both
actual interpreters; account for every old record and every introduced record,
including downstream source-line shifts from the expectation edits themselves.
The full original assertion chain and full inventory suite must pass afterward.
This prospectively avoids the incomplete four-literal diagnosis of ADR-0496.
If the output cannot be explained entirely by this scope, stop before editing.

No historical decision, core file, older tool, baseline edge/SCC or existing
source rule changes. Analyzer inference remains parked and known unsound under
ADR-0486. Registration grants no capability or analyzer-soundness claim.

## Review, tests and limits

Adopt brief.md's 1200 production / 1600 new-test LF line / 16384 fixture byte /
200 manual registration add-remove line limits. Exactly one initial source
candidate plus at most one bounded correction; two independent Tier C reviews
for substantive bytes. Qualified mechanics require ADR-0492's independent proof.
Stop before a third candidate, scope/budget expansion or sealed-core change.

Initial focused controls: the two new suites and the actual boundary gate,
plus the full affected inventory expectation before any source freeze. After
CLEAN review, run the two new suites with these unchanged named suites:

- tests/test_v0a_event_adapter.py
- tests/test_v0a_event_adapter_boundary.py
- tests/test_v0a_hand_adapter.py
- tests/test_hand_adapter_boundary.py
- tests/test_hand_scenario.py
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

Also run tools/generate_test_inventory.py --check and the real boundary gate.
Run the new host's integer decoder boundary controls at int_max_str_digits=640
on each slot. Use fresh D-local snapshots and actual interpreter/module-origin
preflights, floor 3.11.15 first then development 3.14.6, -B -P, snapshot-root cwd,
snapshot/src PYTHONPATH, scrubbed environments and absolute PONTIUS_GIT. Native
job/process tests require real Windows permission; retain any blocked attempt,
and obtain it for a fresh snapshot instead of substituting mocked containment.
No wildcard/discovery, research profile, performance/strength run or arbitrary deal.

## Adoption and execution boundaries

The prospective decision incorporates exactly the reviewed brief, design and
this source-opening proposal plus a new ADR and generated STATUS. Metadata must
receive its independent review and unchanged generator check/full twelve status
tests on actual floor/development snapshots. Exact commit authorization remains
separate. This proposal itself cannot open source work, seal an implementation,
authorize operation or publish a packet. No cleanup/ref retirement is included.

Terminal/human interaction and multi-hand operation remain subsequent tasks.
Neural self-play/league reuse is a compatibility goal only; it creates no training
machinery or result claim here. No previously consumed or rejected owner reopens.
