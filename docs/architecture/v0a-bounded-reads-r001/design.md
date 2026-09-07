# Bounded read successor design

## Goals and observation

Satisfy the companion brief's resource ceiling without changing stable-read
acceptance, source integrity, or evaluation semantics. A real-file ceiling test
fails before the change; native mutation controls and existing contract suites
establish the preserved behavior. Fresh source-bound executions establish actual
v2 admission and publication. Versioned source is necessary because ADR-0509
sealed v1; this is a successor to that implementation.

## Mechanisms, invariants, and covered places

1. The runner observes a regular file's identity and size before opening it,
   admits that size against the caller's existing cap, and requests one byte
   beyond the observed size. Before/after handle identity, final named identity,
   byte length and ancestor identities remain authoritative. This applies to
   every `read_stable` call: captured source, request/deal/lineup inputs, child
   artifacts, completed results and revalidation. Enumerate the callers from the
   frozen runner; all current caps are fixed non-negative integers. The extra
   byte is essential: growth that is restored before final metadata observation
   must still be refused when that extra byte was observed.
2. A standalone v2 copy changes its admitted self-origin, while the helper and
   inherited child/source population remain byte-identical. The raw loader still
   loads exactly the captured helper, dealer and host. The guard registers v2
   and applies the same closed imports and exact loader to each runner with its
   own fixed self-origin. This must hold in both source admission and repository
   boundary validation; adding a filename alone would miss the second boundary.
3. Source commit and sorted path/hash manifest identify the implementation.
   Existing v1 request/result schemas, ordering, subprocess arguments, clocks,
   cleanup, publication and independent completed-reader rules are unchanged.
   Fresh output roots and evaluation suffixes distinguish every diagnostic run.
   Cross-version reading covers the compatibility claim independently of copying
   source. The unchanged helper's bytes are checked against the base commit.
4. The new CPU suite is explicitly registered in the origin guard, inventory
   generator, generated inventory/profiles, current census assertions and CI.
   Historical inventory locks and old test identities are preserved. Diff each
   changed registration against the six base blobs recorded below.

## Controlled schedules and coverage limits

Tests operate on real temporary files and real handles. At `Path.open`/stream
read/close seams, a wrapper may impose a resource ceiling or schedule real growth,
shrinkage or named replacement; it forwards the production read and observes
actual bytes. Ancestor replacement occurs between captured identity and final
revalidation. No fake returns a selected contract result. A restored-growth
control changes real bytes then restores size and mtime before the final handle
observation. A deliberately incorrect size-only read must accept the otherwise
identical schedule, proving the extra-byte check's discriminating power.
These are deterministic correctness schedules, not claims about race prevalence
or proof that every possible Windows filesystem race is detected.

The category is all stable-read invariant checks plus every modified guard edge.
Enumerate checks from the frozen `read_stable`, `admit_source`, `SourceBinding.check`
and import-policy implementations, and map them in a compact coverage record.
Reuse unchanged evaluation suites for execution and publication paths; add public
source admission and cross-version artifact reading in fresh D-local diagnostics.

## Alternatives and easy mistakes

Editing sealed v1 violates immutable history. A monkeypatch launcher cannot by
itself identify executed replacement bytes in the source manifest. A generalized
loader or read cache adds trust state unrelated to this measured bottleneck.
Reading exactly the observed size loses extra-byte growth detection. Removing
source checks trades away the contract; neither is selected. A native engine
replacement does not address the measured parent read overhead.

Do not weaken the v1 guard while accepting v2, change schema prefixes incidentally,
reuse a consumed output identity, mix profile overhead with ordinary wall time,
sum overlapping parent/child cumulative times, or use chip outcomes for tuning.

## Rulings, project ties, and barriers

The controller's instruction to follow the proposed versioned correction and
diagnostics authorizes this implementation. No unresolved mechanism ruling is
needed. Final decision adoption follows CLAUDE.md rule 4 after the concrete
candidate is qualified. A successor ADR records only the six prospective
registration supersessions; no general sealed-source exception is inferred.

This reduces evaluation cost and provides the profile for the next optimization.
It assumes the accepted v1 game/evaluation contract and forecloses no training
architecture. Non-empty blueprint measurements are separate synthetic cost
observations, not learned-policy or playing-strength evidence. Toolchain absence,
source drift, failed invariant tests or disagreement on the mechanism block
adoption. Documentation and disposable diagnostics are cheap to revise; the
adopted runner, tests and decision become permanently sealed. Apply the brief's
one initial candidate and at most two correction rounds.

Not designed here: policy learning, indexed blueprint lookup, caching source
checks, changed clocks, game rules, deadline changes, or native engine migration.

## Base registration blobs

| Path | Git blob at base |
| --- | --- |
| `.github/workflows/ci.yml` | `d5e7bf8b31326c5ebd2a2416d1439d3449e0fde9` |
| `tests/test-inventory.json` | `eb6e02d47d2caa79688a494dc3c75bcfc9fd4eb6` |
| `tests/test-profiles.toml` | `b9b6f62b5dbf57567454fa271d3924c2e01b5387` |
| `tests/test_inventory_and_profiles.py` | `8ef0c1f4de568f3f5e35471a44acc8d7b06e0b74` |
| `tools/check_stabilization_boundaries.py` | `63cb7adea11f71e17eaa4e98dcd42a028a1ff08d` |
| `tools/generate_test_inventory.py` | `599d0def700131a07f403b9c4076457511da7333` |
