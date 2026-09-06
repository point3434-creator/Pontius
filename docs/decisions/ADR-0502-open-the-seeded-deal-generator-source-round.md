# ADR-0502: Open the seeded-deal generator source round

- Status: accepted source-opening decision upon its separately authorized commit
- Date: 2026-09-06
- Follows: ADR-0501
- Base-Commit: cc22fdb67f572a53257cd092c01d192f1a8db5ab
- Invocation-Authority: none; no new demonstration, rehearsal, operating or research run
- Front-Door-Kind: controller-v1
- Front-Door-Research: ADR-0280
- Front-Door-Process: ADR-0502
- Front-Door-Contract: ADR-0307
- Front-Door-Revoked: ADR-0281, ADR-0468, ADR-0472, ADR-0475
- Front-Door-Active-Next: Implement the bounded seeded-deal generator; poker execution closed
- Front-Door-Blockers: generator source acceptance pending; no new session authority

## Decision

Open the bounded CPU-only seeded-deal generator described in
docs/architecture/v0a-seeded-deals-r001.md. The controller selected reproducible
random dealing after viewing the completed fixed two-hand demonstration. Add a
standalone data generator that saves an existing-format session schedule from an
explicit saved seed request. Preserve every sealed poker runtime and tool byte.

Effect requires this exact decision's separately authorized commit. A draft,
review ref, generated STATUS or passing metadata check opens no implementation.
After adoption, source work and the named finite correctness controls are allowed;
source acceptance and permission to play generated hands remain separate.

## Exact new source and contracts

Adopt the companion design's pure APIs, fixed table setup, exact versioned SHA-256
counter/Fisher-Yates recipe, rejection/word limits, per-hand index and dealing order,
strict request/session/receipt schemas, path/I/O/refusal meanings, independent
oracles, bounded source/test scope and stop rules. No runtime or policy changes.

The pure per-hand function takes only a saved seed and hand index. The CLI reads a
request and exclusively creates one session file; it never launches poker, selects
a seed from outcomes or passes seed/future-deal metadata to a policy. Source tests
may materialize only their declared finite known-answer/boundary schedules.
All generated cards are new correctness data, not an admitted demo or population.
The existing session independently validates the unchanged-format output.

Add exactly the five new tool/test/fixture files named in the design. No src/pontius
addition, dependency or existing poker-tool mutation is opened. Preserve the
current session, host, event adapter, old fixtures and blueprints byte-for-byte.
Future neural/self-play reuse is compatibility context, not a training task.

## Six exact registration exceptions

Prospectively supersede CLAUDE.md rule 1 only for these six current registration
versions, and only for the changes stated here. Check each raw base blob before
the first source edit. No registration byte changes in this opening decision.

- tools/check_stabilization_boundaries.py, blob
  be8cb43b01fa781b8fec9915cc5b08848fbef2d6: register the one new tool origin,
  enforce its exact stdlib-only import allowlist and forbid its dynamic import/exec
  routes; preserve every previous origin, policy, source rule and baseline edge/SCC.
- tools/generate_test_inventory.py, blob
  27b43c7dda0452414271875e41bfc8ac3db20663: register the two new CPU suites only.
- tests/test-inventory.json, blob
  319931f2e400bee9d201ae78caef467f08d6ac7c: regenerate for the new suites and IDs,
  preserving every old inventory record and ID.
- tests/test-profiles.toml, blob
  7e6f920045f5009320def234b9eb2a325910f6d7: regenerate for the two suites,
  preserving old payload membership/order and zero new capability grants.
- tests/test_inventory_and_profiles.py, blob
  e863c3a69c3d071a9fb0fc5b7562ce8f18adf603: add the two registration expectations
  and refresh only complete derived census counts, digests, reasons and source
  locations affected by new tests and the registration/expectation insertions.
- .github/workflows/ci.yml, blob
  2a40e8109c681fd331cd7e7c4ea536ac15573eaa: add two direct CPU suite steps using
  the current invocation conventions, retaining all old hard gates.

Before any census expectation refresh, compare the unchanged real analyzer's full
output against this base on both actual interpreters. Account for every retained
and new record, including source-line shifts caused by the expectation edits.
Preserve the full assertion chain, old predicates/IDs and entire inventory suite.
No discarded records, analyzer inference change, hidden capability grant, weakened
gate, permanent mutation permission or repaired-soundness claim is permitted.
Unexplained drift stops the round. The analyzer remains parked under ADR-0486.

## Acceptance, provenance and exclusions

This decision's delta is exactly this new ADR, the companion design and generated
STATUS. Review all three together in one immutable Tier C candidate, with two fresh
independent reviews, then unchanged status --check and all twelve status-generation
tests on actual CPython 3.11.15 first, then 3.14.6 in fresh D-local snapshots. Use
-B -P, scrubbed environment, exact cwd/src, module-origin preflight and absolute Git.
Recheck six registration base pins. No poker payload or algorithm implementation
runs in this documentation task. One initial proposal plus one bounded correction.

Future source acceptance uses the design's exact budgets, two-review procedure
and named finite dual-interpreter checks. Correctness fixture publication does not
authorize live demonstration, population sampling, rehearsal, cost/strength claims,
training, league evaluation or a repeated owner. No generated schedule is selected
because its cards, actions or payouts look favorable. No randomness-quality result
is asserted by naming a deterministic algorithm or passing fixed vectors.

The one ADR-0501 demonstration completed and its exception is consumed. Original
output and disposition remain under D:/Pontius/tmp/v0a-watch-demo-run-r001/;
these are retained local demonstration records, not promoted acceptance evidence.
No second attempt, retry, output replacement or broader demo authority follows.
Formal operating/research prerequisites, ADR-0307, parked lanes and consumed owners
remain unchanged. No cleanup or ref retirement. This is source opening only.
