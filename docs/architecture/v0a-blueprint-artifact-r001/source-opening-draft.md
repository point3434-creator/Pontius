# Proposed decision: Open the portable blueprint artifact source round

Status: draft only; no ADR number issued, no source opening activated.
Base: `7ee314b443e10896e87a2e194f24eddda31ff77d`.
Follows: ADR-0489. Design: this packet's `design.md`.

## Controller approval received

The controller answered yes to including a narrow registration amendment in the
proposed source-opening decision alongside the codec design. That authorizes
preparing these documents. It does not authorize editing the six listed existing
files, writing feature/test code, running a payload, adopting an ADR or committing.

## Proposed source opening and activation

After the frozen design receives its applicable Tier C independent reviews and
the controller separately adopts this decision, open one additive, CPU-only
implementation round for the two byte-level codec operations in `design.md`.
This draft has no effect; the eventual decision takes effect only at its
separately authorized adoption commit. A separate source-seal decision is needed
after implementation review and acceptance. No operating or rehearsal authority
is bundled with either decision.

The original brief's no-sealed-byte instruction and CLAUDE.md rule 1 would be
superseded only for the exact six current-checkout registration files below, only
for this round's stated deltas. Historic commits, source seals, review snapshots,
issued records and their hashes remain unchanged and authoritative for their own
versions. This is not a general permission to edit sealed source or test behavior.

## New paths proposed

- `src/pontius/blueprint_artifact/__init__.py`: inert package initializer.
- `src/pontius/blueprint_artifact/codec.py`: the two operations and typed refusal.
- `tests/test_blueprint_artifact.py`: schema, identity and actual-runtime controls.
- `tests/test_blueprint_artifact_boundary.py`: narrow registration/import controls.
- `tests/fixtures/blueprint_artifact/raise_control.json`: independent literal data.
- `tests/fixtures/blueprint_artifact/history_control.json`: independent literal data.

No extra module, tool, launcher, parent re-export, fixture tree or dependency is
opened implicitly. Design bounds: 300 codec lines including the initializer,
300 new test lines combined, two data fixtures of at most 8 KiB combined.

## Six exact registration exceptions proposed

1. `tools/check_stabilization_boundaries.py`: classify exactly the new package
   initializer and codec as an additive family, enforce their direct import
   limits from the design, and call that check from the existing public gate.
   Reject other origins in that family. Preserve baseline outgoing edges, SCC
   rules, the six-file v0a population, host-only access rules and unrelated checks.
   Do not widen a family to arbitrary descendants or treat registration as an
   exemption from scanning. The codec may not import the host or runtime.
2. `tools/generate_test_inventory.py`: add exactly the two new test paths to
   `STABILIZATION_TEST_FILES`. No analyzer, inference or authorization logic edit.
3. `tests/test_inventory_and_profiles.py`: add those two paths to the mirrored
   registration expectation. Adjust only discovery-derived census expectations
   whose exact delta is independently attributable to this addition. Retain all
   test methods, assertions, baseline/historical locks and capability semantics.
   An unexplained or unrelated expectation change stops the round.
4. `tests/test-inventory.json`: regenerate with the existing authorized writer,
   with only additions and derived identities/counters justified by the new tests.
   Do not remove/reassign existing test IDs, rewrite historical rows or add grants.
5. `tests/test-profiles.toml`: mechanically regenerate the corresponding current-
   owned payload registrations and derived identities. Existing capability binding
   hashes stay zero; no new probe, process, network or GPU capability is granted.
6. `.github/workflows/ci.yml`: add direct CPU steps for the two new suites under
   the existing release-slot job. Keep every existing hard gate and trigger; no
   new launcher, dependency installation, execution mode or test-runner framework.

The aggregate manual delta for these existing files is at most 100 added plus
removed lines, excluding mechanically generated outputs. The exception for the
inventory test is for registration/census data only, not a behavioral waiver.
Keep generation and tests on the floor first; examine the generated delta itself.
If the unchanged generator cannot register the tests, stop rather than fix it.

Base Git blob identities bind which existing versions the exception concerns:

```text
c3f739f001fd70d5326bc7ec4609f483e1ba5525  tools/check_stabilization_boundaries.py
da0fb1efd0f38747ad90f91aea572789ace7e0aa  tools/generate_test_inventory.py
45c65de9cde1506db8ad900d624ec69fce5b9893  tests/test_inventory_and_profiles.py
d655d205053c13da2634e8a22b36c58b72ee340b  tests/test-inventory.json
ada2c73eb0834fe9822b84e5d31b2ffdfb78b4a6  tests/test-profiles.toml
0585dcd6191dbe97b4f00f3866cc5da9798b4c51  .github/workflows/ci.yml
```

Any base drift is compared and dispositioned explicitly before source opening;
these permissions do not silently transfer to a different registration design.

## Limits, evidence and review

Extend ADR-0486's registration-only, zero-grant treatment to this exact task on
the same limited rationale: no owner, process, GPU or network capability is
admitted. The capability analyzer stays known unsound and parked; the codec does
not depend on it proving safety. This extension does not apply to another lane.

Implementation/source-seal acceptance requires the real controlled-action and
complete-hand checks, not merely hashes or self-round-trip. The exact population
and controls are in `design.md`; run them only after source opening and applicable
review/iteration authority, in fresh D-local snapshots on 3.11.15 first, then
3.14.6. Design/source-opening approval is a prior, read-only review of the contract
and permissions, not a claim those runtime tests have already passed. This
decision would authorize ordinary correctness development, not a scientific profile.

Require the normal two independent Tier C reviews for the design and subsequent
implementation. The existing-reviewer light exception for the ADR-0489 docs
decision is not reused. No clean verdict or completed verification is asserted.
Budget one initial implementation round and one bounded correction, then return
to the controller if still not acceptable. All failed candidates remain retained.

The prospective format ceiling of 1,048,576 bytes is an admission-format choice
subject to design adoption, not measured operational data. It neither adopts the
deferred 120000 ms/32768-byte proposals nor authorizes any owner or rehearsal.

All other runtime, kernel, configuration, behavioral test and evidence bytes stay
sealed. Do not edit the original brief, CLAUDE.md, workflow, dependency baseline,
legacy manifests, locks, prior ADRs or prior results. The eventual decision may
add its own ADR and generated STATUS metadata; the source round does not grant
arbitrary documentation rewrites. Parked lanes and consumed identities stay closed.

## Present disposition

Prepared for review only. No implementation, existing-file exception, source seal,
test result, policy-strength claim, commit or push exists from this draft.
