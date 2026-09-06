# Watch-first table session: source-opening proposal r002

Status: unadopted proposal. Task: v0a-table-session-design/r002.
Base: fa28d191143586dee682b2726fb8cac253ab49f5. No implementation authority yet.

## Proposed decision and scope

After accepted design review and exact decision authorization, open the bounded
source-only implementation in brief.md and design.md. Compose the sealed host for
a finite watch-first session with stack carryover, button rotation, visible updates
and between-hand next/quit. Preserve every existing game, wire, timing and ownership
contract. New session/hand summary versions do not change the sealed CLI receipt.

Exact additions:

- tools/v0a_table_session.py
- tests/test_v0a_table_session.py
- tests/test_v0a_table_session_boundary.py
- tests/fixtures/table_session/two_hands.json
- tests/fixtures/table_session/below_blind.json

Reuse tests/fixtures/table_host/empty_blueprint.json unchanged. No new src/pontius
file, dependency, shared launcher, policy interface or persistent result store.
The new tool admits only the fixed sealed host source through design.md's verified
compile/exec route and public names. No direct Pontius imports, other sibling tool
loads, private host/CPython access or replacement native ownership implementation.
The host's raw sealed blob is 0faa101f9be9940f9ae935df51f8c79e2eeb2b15.
Adopt the corrected cancellation boundary: interrupted means a KeyboardInterrupt
observable by the caller and primary in its failure order. Internally classified
constructor/cleanup failures retain their public host reasons and exit 1. No signal
observer, cause introspection or stronger provenance claim is opened. The paired
real finish-time interruption/non-interrupt cleanup controls in design.md bind.
Allow standard library __future__, argparse, base64, dataclasses, hashlib, json,
os, pathlib, re, stat, subprocess, sys and types. Any further import needs a bounded
proposal correction before freeze. Existing host imports remain its own boundary.

## Six exact current-file registration exceptions

Check these raw base blobs before implementation. Supersede current-file sealing
only for the following prospectively admitted changes:

- tools/check_stabilization_boundaries.py, blob
  af0f37e417fec673f10b8e08fba99e3edc7ae50d: classify the new session and precisely
  allow its fixed host dependency/imports; preserve all prior rules and allowlists.
- tools/generate_test_inventory.py, blob
  2314838261c8835e723d58857bca241b0a233aaf: register the two new suites in the
  existing CPU treatment; no inference, capability, profile or analyzer repair.
- tests/test-inventory.json, blob
  bb11a09319434af5d9dd040d91121192045339dd: unchanged generator's new test rows
  and required derived identities only; preserve every old row and test ID.
- tests/test-profiles.toml, blob
  583436970e0e058ac7fd10d261827a015b9ddea3: mechanical regeneration for the two
  suites, retaining old membership/order semantics and zero capability grants.
- tests/test_inventory_and_profiles.py, blob
  f6e63652de9f8b12985e828c582a136842f05805: add new suite names to registration
  expectations and prospectively refresh only derived current-source census
  expectations in CheckedInInventoryTests.
  test_working_discovery_binds_every_entry_and_introduced_id.
- .github/workflows/ci.yml, blob
  64debe40cd25509ef7a52ed30a9686b30bcefdba: add the two direct CPU suite steps
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

Adopt brief.md's 700 production / 1200 new-test LF line / 8192 fixture byte /
200 manual registration add-remove line limits. Exactly one initial source
candidate plus at most one bounded correction; two independent Tier C reviews
for substantive bytes. Qualified mechanics require ADR-0492's independent proof.
Stop before a third candidate, scope/budget expansion or sealed-core change.

Initial focused controls: the two new suites and actual boundary gate, plus the
full affected inventory expectation before source freeze. Require design.md's
independent stack/action/control arithmetic, private projection and real cleanup
falsifiers. After CLEAN review, run both new suites with these unchanged suites:

- tests/test_v0a_table_host.py
- tests/test_v0a_table_host_boundary.py
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
Run the new session's integer decoder controls at int_max_str_digits=640 on each
slot. Use fresh D-local snapshots and actual interpreter/module-origin preflights,
floor 3.11.15 first then development 3.14.6, -B -P, snapshot-root cwd, snapshot/src
PYTHONPATH, scrubbed environments and absolute PONTIUS_GIT. Native tests require
real Windows permission; retain any blocked attempt and obtain permission for a
fresh snapshot rather than substituting mocked containment. No wildcard/discovery,
research profile, performance/strength run, operating session or arbitrary deal.

## Adoption and execution boundaries

The prospective decision incorporates exactly the reviewed brief, design and this
proposal plus ADR-0499 and generated STATUS. Metadata needs independent review and
the unchanged generator check/full twelve status tests on both actual interpreter
snapshots. Exact commit authorization remains separate. This proposal itself opens
no source work, seals no implementation and authorizes no operation or publication.
No cleanup/ref retirement, historical edit or consumed/rejected owner reopening.

Only finite named correctness schedules and failure controls are admitted to the
future source round. Interactive operating play needs its separate entry decision;
a source-correctness identifier is not a substitute for that authority. Human action
input is deferred by the controller's watch-first choice. Neural self-play/league
reuse remains a compatibility aim; no training machinery or strength claim here.
