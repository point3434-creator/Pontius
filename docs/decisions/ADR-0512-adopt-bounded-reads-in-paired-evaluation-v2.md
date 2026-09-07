# ADR-0512: Adopt bounded reads in paired evaluation v2

- Status: accepted engineering-only successor upon its separately authorized decision commit
- Date: 2026-09-07
- Follows: ADR-0511
- Base-Commit: 5845f32f010a44d924abc2f50ae142d1c6adec1b
- Invocation-Authority: no new operational or research owner
- Front-Door-Kind: controller-v1
- Front-Door-Research: ADR-0280
- Front-Door-Process: ADR-0512
- Front-Door-Contract: ADR-0307
- Front-Door-Revoked: ADR-0281, ADR-0468, ADR-0472, ADR-0475
- Front-Door-Active-Next: Design immutable blueprint digest and lookup preparation
- Front-Door-Blockers: strength, full-evaluation resources and worst-case action latency unknown

## Decision

Adopt `tools/v0a_evaluation_v2.py` as the bounded-read successor to the sealed v1
paired evaluator. Its two-location change selects its own source origin and reads
one byte beyond the observed file size, after the unchanged cap admission. All
file/handle/ancestor checks, captured source loading, child contracts, cleanup,
clocks and publication semantics remain intact. V1 schemas and evaluation-ID
syntax retain their meaning; source commit and manifest distinguish v2.

Retain the completed performance pass and synthetic non-empty blueprint cost
probe as engineering observations. The controller authorized the focused pass,
then asked to follow the versioned-correction and measurement recommendations.
No learned strategy, tuning, benchmark gate relaxation, or native engine migration
is adopted. Exact decision commit/push authorization is the final adoption step.

## Architecture checkpoint after ADR-0511

The single 48-trial descriptive comparison completed and remains consumed at
`D:/Pontius/tmp/v0a-paired-evaluation-run-001`. Its full parent wall was 382.532 s;
it established a finite engineering comparison, not independent samples or a
playing-strength result. Preserve comparison-report.json SHA256
`74e83b9473d06f1ad20fc932e964710bb2738bec66803eb0f632f058d5faf84a`
and descriptive-result.json SHA256
`26e904e8a8d06deffe781937d70628071422b81d93080caabeb7672d60ce79b0`.
The new consumption check verified both pins without rerunning that owner.

Ruling: continue the engineering source/cost lane only. The earlier focused pass
identified oversized stable-read requests as a dominant parent cost, and its
one-expression prototype reduced elapsed time with matched behavior. That is a
bounded reason for this source successor; it does not reopen the paired owner,
reset failure history, authorize research, or settle absent resource guarantees.

## Exact source and registration scope

The companion brief, design, coverage map, diagnostic definition and performance
report under `docs/architecture/v0a-bounded-reads-r001/` are normative with this
decision. Add only the v2 runner and its eight-test CPU suite. Preserve the sealed
v1 runner, shared evaluation helper, child/game/provider source, fixtures, old
tests other than the named registration expectations, and all historical artifacts.

Prospectively supersede the prior sealed registration bytes only for these six
paths, from the base blobs pinned in design.md:

- `tools/check_stabilization_boundaries.py`: add the v2 origin and apply the same
  closed import/loader guard using each runner's own exact fixed origin.
- `tools/generate_test_inventory.py`: register the one new CPU suite.
- `tests/test-inventory.json`, `tests/test-profiles.toml`: generated membership
  and digest changes for its eight tests; preserve every old entry and grant.
- `tests/test_inventory_and_profiles.py`: new suite membership and three census
  count literals, 693 to 695 total unresolved analyzer rows, 67 to 68 mixed
  receivers and 36 to 37 max/min comparison rows. Complete captured rows confirm
  old blockers, site/decoy digests, capability rows and historical locks unchanged.
- `.github/workflows/ci.yml`: one new suite step, preserving the existing steps.

These exceptions confer no general permission to edit sealed bytes. Generate
STATUS.md from this ADR. Freeze exact Git blobs with a sorted SHA256/path manifest;
two fresh independent Tier C source reviews and fresh floor-first acceptance
must bind that candidate before adoption. Local review freeze commits are not
decision commits and do not constitute adoption.

## Qualification and retained costs

The native resource-ceiling test failed against the original read expression and
passed after correction. Growth, shrinkage, file replacement, same-file-identity
ancestor replacement and restored-size/mtime growth controls exercise real handles
and bytes. The deliberately wrong size-only reader accepts the restored-growth
schedule that v2 refuses. Source admission pins v2 and the unchanged helper;
negative guard controls cover both runner origins and loader edges.

Acceptance requires the new suite, unchanged evaluation contract/runner/boundary
suites, boundary checker and applicable boundary tests, generated inventory check,
checked-in inventory/profile tests, status generation/check/tests, and exact
source/registration diff. Run actual Python 3.11.15 before 3.14.6, each in a fresh
D-local frozen snapshot with scrubbed -B -P, snapshot cwd/src and absolute native
Git. Record full exits, output and any platform-conditioned skips; no new skip or
waiver may be substituted for a required check. Final review and gate records
remain beside the immutable freeze manifests under the retained root below.

At `D:/Pontius/tmp/bounded-reads-v2-20260907-001`, the versioned unprofiled matrix
completed in 49.2236669 s versus earlier ordinary controls of 88.9310463 and
95.5539101 s. All 24 new ordinary/profiled trials completed with matching actions,
settlements and cleanup. Both runner versions read the old and new completed
artifacts. These are finite compatibility and cost observations, not statistical
speed bounds. Diagnostic source commit, manifest, exact timings and limitations
are recorded in performance-report.md and the raw measurement-summary.json.

Non-empty synthetic blueprint measurements show roughly 6-7 ms per provider call
at 1,024 entries, with repeated table digest work dominating the profile. Continue
with a separately designed immutable digest/index preparation successor if the
controller chooses; no caching/index implementation is bundled into this decision.
The first read-size optimization is useful to evaluation throughput. It does not
by itself demonstrate faster on-clock search or better decisions under 15 seconds.

One initial candidate and at most two bounded correction rounds remain the scope
budget. Stop at the reviewed, qualified concrete adoption candidate; unresolved
invariant/design disagreement returns for a ruling. No consumed owner, training,
GPU, H32, full league or real-play authority is created.
