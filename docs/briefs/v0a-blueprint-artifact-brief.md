# Portable v0a blueprint artifact: proposed brief

Scope now: brief/design only under ADR-0489; no feature implementation or run.
Prospective implementation tier: C for a policy-admission data boundary.
Existing consumer: `HandRuntime(blueprint=...)` and `ReplayHost(..., blueprint=...)`.

## Product outcome

Supply a non-empty immutable policy as plain data instead of editing Python code.
The runtime already supports table hits, non-passive actions, passive misses and
typed illegal-hit refusal. This task does not reimplement those behaviors or
claim to invent a stronger strategy. Its consumer is that existing runtime API.

## Proposed bounded shape

A small additive codec exports and loads a versioned UTF-8 JSON artifact containing
the source ID, complete visible-state decision keys, and exact action values.
The existing canonical policy representation contains key hashes and is not a
lossless storage format; the new artifact must not pretend otherwise.
Loading returns the existing `ImmutableBlueprintActionSource`, never executable
behavior, pickle, a callback or a modified runtime. Missing-key passive behavior
and illegal matching-entry failure remain the sealed runtime's responsibility.

Design must name the exact schema, canonical encoding, raw-artifact identity and
existing policy-digest relationship. Preserve all public-history and own-card
information needed to reconstruct each key; admit no host, future schedule or
opponent-private data. Reject duplicate keys/entries, unknown fields, wrong exact
types, unsupported versions and malformed values without partial policy admission.

## Acceptance and bounds for the subsequent design

1. Round-trip non-empty keys/actions without changing the existing policy digest.
2. Loaded policy drives a real controlled action and complete-hand replay through
   the existing consumer; an independently stated expected action differs from
   passive default. No accepted/rehearsal output becomes the expected oracle.
3. An unmatched key retains passive fallback; an illegal matching action remains
   a typed failure with no emission. Malformed artifact refusal occurs before use.
4. Both reader/exporter and actual runtime use are exercised on the supported
   floor first. Tests are ordinary correctness cases with fresh disjoint IDs.
5. Propose at most 300 codec lines and 300 new test lines, plus tiny explicit data
   fixtures. No new launcher, generalized schema/proof engine, external dependency,
   training, benchmarking, GPU integration or owner lifecycle.

Ground truth: the sealed blueprint/key public contract, declared control actions,
independent legal replay and chip settlement. Self-round-trip alone is insufficient.
Existing neighboring tests already cover policy hits and fold-terminal replay;
reuse those contracts, not another review of the whole core.

The design must select new package paths and narrow import/CI treatment without
editing any sealed byte or inflating this into analyzer work. No path or capability
grant is made by this draft. If immutable-source or registration constraints make
this small codec require broad copying or tooling, return that precise conflict
to the controller before implementation. Do not build a workaround silently.

Only this design depends on the present engineering disposition. It has no
dependency on an authoritative A/B run or the deferred operational budget.
One bounded design pass, then return for the explicit source-opening decision;
no implementation-plan machinery is commissioned by this brief alone.
