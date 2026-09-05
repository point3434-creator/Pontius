# Proposed source opening: one-hand file adapter

Status: proposal only; no ADR issued or implementation permission activated.
Base: 7a387e995e3b37232d2379332927247a4d49c64e. Follows ADR-0492.
Inputs: this packet's brief.md and design.md. Tier C.

The controller approved preparing and reviewing this narrow design. After its
two independent cold reviews and exact controller adoption, a later decision
would open the following source round. A draft, review ref or generated STATUS
does not activate it. Source implementation, acceptance/seal and any operating
authority remain distinct. No hand run is authorized now.

## Exact proposed additions

- src/pontius/hand_scenario/__init__.py, inert.
- src/pontius/hand_scenario/codec.py, strict scenario admission and fixture adapter.
- tools/v0a_hand_adapter.py, source-bound file/host/reader CLI.
- tests/test_hand_scenario.py, decoder/literal-card controls.
- tests/test_v0a_hand_adapter.py, real CLI/host/output controls.
- tests/test_hand_adapter_boundary.py, exact import/origin controls.
- tests/fixtures/hand_adapter/raise_scenario.json and raise_blueprint.json.
- tests/fixtures/hand_adapter/showdown_scenario.json and showdown_blueprint.json.

Production budget 500 lines total, new tests 400 lines total, four fixtures at
most 16 KiB combined. Corruptions/negative controls are constructed in disposable
test space, not a larger checked-in fixture collection. No dependency, sibling,
module re-export, new trace schema, action selector or source-proof framework.

## Six current-file registration exceptions proposed

Only upon that later adoption, prospectively supersede CLAUDE.md rule 1 for these
exact current versions and these deltas. Historic versions and evidence remain
immutable. Registration exceptions are not permission to repair the analyzer.

1. tools/check_stabilization_boundaries.py: classify exactly the two new package
   origins and one new tool; enforce design.md's exact direct imports and reject
   undeclared siblings. The sole new incoming edges to hand_scenario are from
   tools.v0a_hand_adapter to pontius.hand_scenario.codec. The sole additional
   incoming edge to the existing blueprint_artifact family is from this same
   tool to pontius.blueprint_artifact.codec. Do not permit arbitrary tool/legacy
   origins. Preserve the six-file v0a population, old complete-deal restrictions,
   inherited edges/SCC checks, old driver exception and every unrelated rule.
   The scenario codec is a separate host-side origin allowed to import replay;
   no runtime/policy origin may import the new package or receive its full deal.
2. tools/generate_test_inventory.py: add the three named test paths to the existing
   registration constant only; no scanner, analyzer, inference or grant changes.
3. tests/test_inventory_and_profiles.py: mirror those registrations and only
   mechanically derived census changes independently attributable to the new tests.
   No test behavior, fixture repair, old IDs, assertion weakening or unrelated
   expectation change. Unexplained generated/census drift stops the round.
4. tests/test-inventory.json: regenerate using the unchanged writer, preserving
   every old test ID and historical row; new registrations/derived hashes only.
5. tests/test-profiles.toml: regenerate the corresponding owned payloads and
   derived identities, with capability binding hashes still zero and no grant.
6. .github/workflows/ci.yml: add direct CPU steps for exactly the three suites to
   the existing floor job. Keep all old steps, triggers and dependency behavior.

Aggregate manual added plus removed lines for those exceptions: at most 100,
excluding generated outputs and separate decision metadata. Do not evade a gate
by placing code outside its scan or copying the analyzer into the new package.

These base Git blob IDs bind the existing versions:

```text
ccf41b8e145d4463b6dd13aa224df54440d87c4d  tools/check_stabilization_boundaries.py
7f7f9cf16553bcc36f2e5015c782bb203baebd68  tools/generate_test_inventory.py
75fdc9bf532958bf5d0300488dc828a5d3a1d66a  tests/test_inventory_and_profiles.py
e36ac6213decc0e3dc9cc9f38559fcf9fa5bed6c  tests/test-inventory.json
685a65c9cd8c0a8c7a347c94832cbc0370a6fd1a  tests/test-profiles.toml
1c5278605fdfde8c75a2b31ea4a06251ca88c975  .github/workflows/ci.yml
```

Unexpected base drift must be explicitly dispositioned before source opening;
no permission automatically transfers to changed versions. Extend ADR-0486's
registration-only zero-grant treatment to this precise task, not to another lane.
If the existing generator cannot register it, stop; do not expand this task.

## Acceptance, authority and completion

Implementation is ordinary correctness development with declared expectations,
under the snapshot policy. All design.md controls are mandatory at implementation
acceptance. Run floor 3.11.15 first, then 3.14.6; scoped development/freeze checks
precede two independent Tier C implementation reviews and the post-CLEAN union
of the new suites, unchanged blueprint/v0a suites and existing direct CPU gates.
No broad scientific profile or old owner runs. Scope tests explicitly even when
using the CLI; its correctness label is not a grant for arbitrary data use.

Allow one initial implementation round and one bounded correction, then return
for reassessment. Qualified mechanical corrections follow ADR-0492 without
retrospective verdict rewriting or changing the substantive anchor. All failed
rounds remain retained. Exceeding any stated budget or needing a sealed-core
change requires a new controller decision before work expands.

Keep src/pontius/v0a, blueprint_artifact, immutable_blueprint and the old driver
byte-identical, along with old tests except the narrow registration/census edits.
Do not edit old briefs, ADRs, source bindings, manifests, locks, PROJECT, ROADMAP,
CLAUDE or workflow. The eventual adoption may add its own ADR, unchanged reviewed
proposal copies and generated STATUS as separately reviewed decision metadata.

No experiment owner, authority record, operation, rehearsal, policy search or
strength/timing claim opens. No byte/memory/wall quota is adopted; engineering
size budgets and the derived integer compatibility domain are not capacity gates.
H32, campaign, compiled work, Gate 13 and analyzer repair stay parked. This round
ends with reviewed proposals and an exact source-opening request, not source code.
