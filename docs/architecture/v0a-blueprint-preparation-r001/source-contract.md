# Blueprint preparation source contract

Base B is `363c9fb669e19a30375537ee5e92ea338a840a2d`, tree
`10cc82ff78a84ef901242b2f69540f6a74ec498b`. Recheck every base blob before source
editing. This contract takes effect only upon the separately authorized adoption
of ADR-0513. It grants no exception to another version of an old path.

## Exact prospective exceptions

| Old path | Raw base Git blob |
| --- | --- |
| `src/pontius/v0a/runtime.py` | `7f067058188e792b59770f94c974cf7f372b31a6` |
| `tools/v0a_hand_adapter.py` | `192dd469a7b315d3247a899df19700e1aabb02cf` |
| `tools/v0a_event_adapter.py` | `8c9e5ef288d426bb64ce72547ab100505c8f682e` |
| `tools/v0a_table_host.py` | `6ec8a162b053158203663c48e82314b10750f962` |
| `tools/v0a_table_session.py` | `a5e058260fa56e29f06e38074d59dc55f420c5ee` |
| `tools/check_stabilization_boundaries.py` | `b1f36842f71641fc8fbe86c58bc90c8c00f43725` |
| `tools/generate_test_inventory.py` | `b036ee34f4709c5306e18966015f2e797eb0924b` |
| `tests/test-inventory.json` | `e54391e724e507066a7cc4c037cff8717a3d6a6b` |
| `tests/test-profiles.toml` | `194afe9a55ef72ebc84b55f794904d370b697a67` |
| `tests/test_inventory_and_profiles.py` | `84a92441c0d3d77f4b67ca8d6f9b794e181bf278` |
| `tests/test_v0a_table_session.py` | `bd7667885cc5bc0e2914409afc3b333c5c3281ad` |
| `.github/workflows/ci.yml` | `4045887ca578f46c6c61e9d71ec058c6b99a7f4a` |
| `docs/architecture/historical-blobs.toml` | `15bba1a3f0800da12ce339455461c7725b18ca66` |
| `tools/generate_evidence_manifests.py` | `a9abbb6ec8055316b21922600510b20ee8289fbe` |
| `tests/test_evidence_manifest_generation.py` | `7bd0e4b5706586b59da506435aa2bdf88528fede` |

Runtime changes are exactly the owned prepared slot, accounted hand-start
preparation/failure closure, and the validated prepared lookup route in design.md.
Adapter/event/host changes are only source-admission declarations; preserve their
operating code. Session changes only its host blob literal. Its existing test
changes only the two corresponding host-pin literals, preserving the negative
mutation and assertion. No blueprint/provider/codec or host-oracle edit is allowed.

The boundary checker admits the two exact package origins and one new evaluator
origin. It gives v3 the same closed import/loader rules with its own fixed origin,
and updates the session host pin. New preparation imports are limited to standard
library value/hash/mapping support, `immutable_blueprint`, `no_limit_betting` and
`decision_provider.model`; only runtime may add an incoming production edge to it.
The package initializer is inert. No filesystem, host, full-deal, river, dynamic
loader or optional dependency edge is added to the prepared lookup. Give the fixed
historical launcher its own exact standard-library-only origin guard; it has no
production import edge or arbitrary executable/module/ref argument.

Generator/test changes register the named new suites and the exact historical
classification below, with generated inventory/profile output. Preserve every
old test ID, assertion, analyzer blocker, baseline lock and capability grant;
account separately for the explicitly changed historical targets. Compare the
complete old/new census on both interpreters, including shifted sites and decoys.
Refresh only explained registration expectations. No analyzer or model repair.
Evidence-manifest generator/test exceptions add only the new snapshot and three
test rows below, including their exact approval digest and derived expectations.
Preserve every existing historical row, current-file/absence manifest and v7 pin.

CI retains all existing gates and failure propagation. Route only the three old
source-dependent evaluator steps through the historical launcher, and add current
prepared/v3/launcher suites in fresh non-reparse D-local snapshots. Hosted CI is
distinct from a local rehearsal of its exact launch blocks.

## Additions and source admission

Add only these production/tool and test files:

```text
src/pontius/blueprint_preparation/__init__.py
src/pontius/blueprint_preparation/lookup.py
tools/v0a_evaluation_v3.py
tools/run_evaluation_history.py
tests/test_blueprint_preparation.py
tests/test_blueprint_preparation_runtime.py
tests/test_blueprint_preparation_transport.py
tests/test_v0a_evaluation_v3.py
tests/test_evaluation_history.py
```

No new external dependency or fixture file. Use the existing explicit blueprint
and session fixtures, plus finite synthetic values in the new tests. Old tests,
fixtures, v1/v2 evaluators, shared evaluation helper and seeded dealer stay intact
except for the specified registration expectations and two session-test pin literals.

For hand/event/host admission, use B as the base, add exactly the two preparation
package files, and permit changed blobs only for runtime plus the tool's existing
hand/event/host chain. Keep their existing rehearsal-driver input unchanged.
Keep captured raw execution and every subsequent HEAD/file/directory recheck.

V3 is copied from B's v2. Preserve its two-element loader tuple as v3 self and
unchanged contract helper. Inventory B's entire `src/pontius`, the existing six
OLD tools, empty blueprint fixture and contract helper, plus v3. Require exactly
the two package additions and v3; among B's inputs, permit changes only to runtime
and the four hand/event/host/session tools. Every other old blob remains equal.
No loose prefix exception; an extra sibling module must fail admission. Retain
the bounded read expression, native identity checks, subprocess contracts,
artifact publication/reading, cleanup and all schemas/ID semantics unchanged.

## Historical evaluator gate

`run_evaluation_history.py` fixes commit B and its tree above in source. CLI accepts
only `--source-root`, `--run-root`, and `--suite runner|boundary|v2|all`. It never
accepts a ref, test path, code, environment overlay, evaluation request or owner.
The exact suites are `test_v0a_evaluation_runner.py` (28 tests),
`test_v0a_evaluation_boundary.py` (19), and `test_v0a_evaluation_v2.py` (8).

Use an absolute validated native Git and the caller's actual validated CPython.
Create a new non-reparse D-local run root; refuse an existing root. Clone without
hardlinks or overlays, detach exactly B and verify its tree and raw selected test
blobs. Before each suite and after all suites, compare every tracked checkout file
byte-for-byte with B's raw tree blobs, with exact tracked modes/paths. Refuse extra
files in the admitted source population and symlinks/reparse ancestors. Git status
alone is insufficient because filters can hide byte changes. Run each selected
unchanged file with `-B -P`, snapshot cwd/src, a scrubbed
environment and a separate temporary directory. Record full argv, identities,
stdout/stderr, exits, test counts and skips. Run all selected gates even after a
suite failure; overall success requires every selected suite to pass with its
expected count and zero skips. Launch failure is a failure, never an empty pass.
Preserve failed roots and logs; there is no recursive cleanup or owner retry.

Keep the shared evaluation contract suite on current source. Current v3 tests
must independently exercise current source binding, real child completion and
current import-policy refusals for all three evaluator origins. An old snapshot's
boundary checker does not validate the new current checker.

Reclassify exactly the 55 stable IDs found at B in those three unchanged files;
all are post-baseline additions. Use payload IDs
`historical:test_v0a_evaluation_runner`, `historical:test_v0a_evaluation_boundary`
and `historical:test_v0a_evaluation_v2`, with case `case:v0a_evaluation_legacy` and
phase `v0a_evaluation_legacy`. Its fixed commit/tree are B; no overlays or probes.
All 55 item expectations are pass; the positive vector is passed=55,
body_entered=55 and zero assertion/setup failures, owner calls and scientific calls.

Use exact file/ID exceptions in both `_profile_for` and the post-baseline inventory
branch, preserving rejection of every other introduced historical ID. Add the one
snapshot/case to `SNAPSHOTS`/`CASE_PAYLOADS`. Preserve baseline 137 historical IDs
and all baseline assignment locks. Extend existing inventory assertions only for
these 55 transitions, three payload groups and one case; lock their B-derived ID
digests. Keep historical profiles' existing development-only policy; the fixed
launcher explicitly runs this checkpoint on 3.11 first and 3.14 second. This direct
gate does not claim the unfinished general profile executor is operational. Keep
capability definitions/call definitions/bindings empty and both zero digests.

Extend the historical manifest by one B snapshot governed by ADR-0512 and exactly
three `selected_test` records, all with phase `v0a_evaluation_legacy`. Each uses
the corresponding path above and these raw pins:

```text
runner Git blob edd186ccfd6764b93b8b973793d84bdb562e1130
runner SHA-256 9fa3adcd5b350bdcfccfaba251999579e8a37d9d2d63bc7d8789c982ffd3774a
boundary Git blob f2b9534c896fa308e3e777ce3d86c3e5b3034d1d
boundary SHA-256 4a7e323c021c1dace35345782873d8ac2a302eeb6bb7b00df7b9d3445c5f980c
v2 Git blob 477001e2407a9d097359622716b36183d37bb679
v2 SHA-256 76121d42cb8646ea5d47e9f5076cec646a0ea0558c20921ec5b148aac93210cd
```

Append the snapshot after existing generator entries, preserving v7 indices.
Derive the three rows directly from B blobs through the unchanged row/hash helpers.
The existing 167 rows are unchanged; the new totals are 12 snapshots and 170 rows.
The new entries/approved-seed SHA-256 is
`7311fbe67c736ae1d7c72e15aa438db8aee6efc063de3459d95abadbaa0754c8`.
It was computed from the existing parsed rows plus exactly these three records;
the old row digest was first reproduced. Opening adoption approves only this
extension. Extend the manifest tests' snapshot/count/digest/seed-table expectations
without deleting assertions or changing their stable IDs. No parser/schema edit.

## Finite correctness controls

1. Table/provider: empty, first hit, last hit and miss at 16, 128 and 1,024 entries;
   all streets and legal action kinds; exact digest/canonical-byte/config equality;
   source ID, entry-order, key and action changes; complete-key differences and
   controlled hash collision; duplicate/illegal entries; malformed exact graphs
   and subclass hooks; caller and returned-result mutation. Prove one table
   serialization per preparation with a real-method delegating call counter, and
   no table serialization during repeated calls. The reference provider must fail
   that repeated-work assertion, so the performance mechanism is falsifiable.
2. Runtime: actual hand start, dispatch, legal application and delivery in both
   modes; preparation occurs once, inside the charged boundary; preparation
   exception and paired closure clock fault; first-start failure publishes no
   partial cache; unchanged work/deadline exact and adjacent boundaries; prepared
   selection still refuses an illegal matching entry. Existing timing, provider
   outcome, visible-state and mailbox suites retain their original oracles.
3. Transport: real non-empty hit/miss sessions in both modes, actions and carried
   stacks checked against literal controls and the legacy host; current source
   additions/changed unexcepted blobs/wrong host pin/late drift fail closed.
4. Evaluator/history: new v3 real child and artifact round trip; current v3 read
   cap/growth/shrink/replacement/restored-size controls; current import guards;
   fixed history identity and raw selected test bytes; real native historical
   launch and count/skip/exit propagation; wrong ref/tree, existing root and invalid
   executable refusals. No replacement success oracle or mocked successful clone.

Clock schedules may act at the existing clock seam. Preparation failure may be
triggered at the new concrete preparation call, without replacing successful
lookup, ledger closure, host validation or child ownership. Source and pipe fault
schedules operate on disposable files/real resources. Capture all failures.

## Cost observations and final acceptance

After source review closure, compare B and the exact candidate on actual 3.11.15
then 3.14.6. Use fresh D-local snapshots and the accepted scrubbed execution
procedure. Run the five new suites, the fixed 55-test history bridge, and all
unchanged suites/commands listed in the implementation plan. No new skip, waived
gate, unexplained census row or omitted old test is acceptance.

For costs, reuse ADR-0512's deterministic preflop card-pair population and table
sizes 0/16/128/1,024. Retain a diagnostic input/hash definition before timing.
For each version/interpreter, use three warmups then five batches of 20 public
calls per hit/miss case. Also measure five fresh preparation constructions and a
separate tracemalloc pass including owned table, index and cached bytes. Report
median batch means, range, retained/peak Python bytes and exclusions. Do not label
batch means tail latency or compare against a speed threshold chosen afterward.

Run one fixed three-hand non-empty session control per strategy and version with
fresh IDs, plus one fixed 12-trial v3 empty-table compatibility matrix. Publish all
actions, counters, settlements, cleanup and parent elapsed time as engineering
observations; do not rerun ADR-0511's owner. Old readers in B and the new reader
must read the completed matrix artifacts without schema changes. No profiling,
parallel tests, reviewer scans or sync activity during timing. Retain all attempts
with source/runtime/input identities before reporting speed or memory differences.
