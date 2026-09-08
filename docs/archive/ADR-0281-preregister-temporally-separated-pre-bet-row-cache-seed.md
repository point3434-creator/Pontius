# ADR-0281: Preregister temporally separated pre-bet row-cache seed

- Status: accepted label-free seed-only preregistration before any h32 cache population or capacity replay
- Date: 2026-08-22
- Follows: ADR-0280
- Config: `experiments/configs/h32-pre-bet-initial-row-cache-seed-v1.json`
- Config SHA-256: `ec2972bceb416e28f83917f75362aabf9912bda4d0f66350a5c663872dcd66ce`
- Seed runner SHA-256: `caeff3e3225378039ee48b3ba676fa2e6af9363f914faf895a95709ff52f99aa`
- GPU row primitive SHA-256: `9bf203622a75bdebd931d5124ae0f97d9f81cf01c854b948552941713b7ae26f`
- Control SHA-256: `a9650185ab4dab9a9c7a74c1eaba7d2c75bc780303fd02906acf0e6fa81a4da3`

## Question

How can exact h32 pre-bet initial rows be populated off the live clock without
allowing the invocation that creates their hashes to treat those same hashes
as external byte-truth authority or to open a capacity or strategy label?

This is a seed-only preregistration. It authorizes no capacity replay, cache
admission into a current-node master, master solve, candidate endpoint,
separation round, retreat, certificate, quality row, or policy emission.

## Temporal trust dependency

ADR-0280 requires an externally trusted SHA-256 of each literal cache file
before any coefficient is parsed. A hash first computed by the invocation that
also consumes the file is not external preregistration. Content addressing or
a self-hash does not repair that order: a substituted affine row can retain the
same provenance fields and source intercept while differing away from the one
source point. Recomputing the row independently during lookup would restore
trust but also restore the work this cache is meant to remove.

Therefore seed and replay are separate evidence stages:

1. this stage may construct, validate, persist, and hash exact cache bytes;
2. its result labels every cache hash `observed_untrusted_until_external_seal`
   and cannot consume one for capacity;
3. a later clean result decision must pin the literal complete seed-result
   hash, which transitively fixes the listed file paths, byte lengths, hashes,
   identities, order, and telemetry; and
4. only another prospective replay preregistration may consume that externally
   pinned manifest and charge identity, lookup, validation, and gain assembly
   on the 15-second decision clock.

The config freezes `trusted_seed_manifest_sha256 = null` and
`capacity_replay_authorized = false`. The executable contains no replay
operation. Its barrier can move only from `cache_seed` to
`cache_bytes_observed_untrusted` after all twelve files complete in order.

## Label-free target selection

Use the sealed ADR-0278 timing matrix read-only. Under ADR-0279's deliberately
optimistic warm-free, zero-cost-cache counterfactual, acting seat 5 is the only
complete position below 15 seconds on all six retained sources. Its worst
two-size proxy is `12,966.496699966956 ms`, leaving conditional headroom
`2,033.503300033044 ms`. Every other acting position has at least one source
above the wall even before lookup cost.

Freeze exactly those six seat-5 source/current-prefix identities in retained
source order. Seed both one-size and two-size bundles for each identity, twelve
files total. This is lawful timing-based work selection from a result that
opened zero candidates or strategy labels. It supports only a paired mechanism
and lookup differential; it does not establish capacity, hit rate, or strategy
quality for seat 5 or any other position.

## Exact GPU primitive and bundle contracts

The one-size and two-size row primitives have distinct manifest digests:

- one size: `0ad913f86f5e2d68d2cd94ed0e18258c6ee40029c1fe57e4805000e3f20cc0c0`;
- two size: `7611ef14efba20bbfbfcabb39e115dd3b9b01890c27fb0e3cebc5b3f2bf3cf44`.

Each manifest binds its arm-specific source oracle, row contraction, backend,
Float64 contract, player and hand counts, feature-batch width, NumPy/CuPy/CUDA
versions, driver floor, and compute capability. It also hashes the canonical-LF
literal local-source import closure of the GPU primitive, the sealed ADR-0277
context builder, and the exact cache implementation. The current closure has
106 source modules. Line-ending canonicalization is explicit for source
provenance; cache, config, checkpoint, and result artifacts retain literal
file-specific `-text` Git attributes.

Each file stores the complete all-or-nothing `2N - 1 = 11` bundle from
ADR-0280: six immutable-blueprint profile rows followed by five nonacting
fixed-response rows. Cache identity binds the complete exact policy and tape,
belief, hands, game provenance, topology, fixed continuation, action schema,
roles, primitive manifest, and numerical contract. After writing, the seed
stage performs a mechanical same-run lookup and requires every flattened row
byte to round-trip exactly, every source and reconstructed gain intercept to
remain within `2e-11`, and the persisted bytes to reproduce their observed
hash. This mechanical control does not convert that hash into replay trust.

The seed primitive has no warm solver, restricted master, candidate,
certificate, or emission dependency. Focused AST controls freeze that absence.
A small six-player GPU composition control executes both distinct arms,
constructs all eleven rows and six gains, and round-trips both files with zero
optimizer or label counters.

## Active campaign deadline and resource bounds

One `MonotonicCampaignDeadline` starts before config and provenance parsing at
the unchanged `3,600 s` campaign ceiling. Before every GPU-bearing unit the
runner atomically checkpoints its complete byte-truth state:

- six source/target context units, each bounded at `120 s`; and
- twelve complete cache-seed units, each bounded at `120 s`, including device
  cache construction, source oracle, eleven row passes, gain assembly,
  serialization, hashing, parsing, numerical validation, and byte comparison.

The sum of all frozen complete unit bounds is `2,160 s`, leaving `1,440 s` for
prerequisite validation, checkpoints, cleanup, and finalization without
relaxing the campaign ceiling. Admission fails before a unit whose complete
bound no longer fits. A unit or campaign overrun stops all later work and
cannot cross the prelabel barrier.

Retain the original per-entry component ceilings of `120 s` each for cold
cache construction, source oracle, and eleven rows. Retain the 12-GB GPU-pool
cap, 1-GB physical-free floor, and stricter 5,184,456,164-byte noncache reserve
used by the cache safety check. Mechanical lookup must stay below `2,000 ms`,
which is only a seed-stage falsifier against the conditional worst-seat-5
headroom, not passing live evidence.

## Unchanged live and safety contracts

Off-clock population moves work; it does not reduce total computation. A
future replay must still charge exact current identity construction, cache-file
hashing, parsing, full provenance validation, all eleven source intercepts, and
six gain rows on-clock. A miss is a completed immutable one-size-blueprint
fallback with no admitted row, master, candidate, label, or emission.

The 15,000-ms street wall, 1,000-ms emission reserve, 500-ms second-master
floor, 1,250-ms exact-proof reserve, 50-ms retreat/envelope reserve, Float64
ceilings, cap allowances, memory limits, and exact independent final
certificate remain unchanged. No cached row can certify a candidate or become
an external policy.

## Failure and decision rule

Reject the seed invocation on any provenance or manifest mismatch, dirty Git,
target-order drift, active-deadline stop, unit or component overrun, unsafe
memory snapshot, incomplete bundle, source/gain error above `2e-11`, cache-byte
or round-trip mismatch, missing checkpoint byte truth, nonfinite telemetry,
barrier failure, nonzero optimizer/label/emission counter, or non-null
population claim. Preserve every produced file as untrusted diagnostic bytes;
do not replay it or adapt another target from a partial result.

If every frozen gate passes, seal the observed cache files and complete seed
result in a separate clean result decision. That decision may authorize only a
new prospective capacity-replay preregistration which pins the literal seed
result hash. It may not infer a live hit, relax a bound, or open quality.

## Decision

Commit the seed runner, GPU primitive, config, controls, file-specific byte
attributes, this ADR, roadmap, project contract, and generated status from one
clean tree. After that clean preregistration commit, invoke this seed-only h32
campaign at most once. Do not invoke ADR-0277, consume a generated cache in a
master, or open any endpoint, certificate, strategy-quality row, or widened
policy before a later externally sealed replay preregistration.

## Claims boundary

This preregistration establishes a temporal trust protocol, target and file
inventory, exact row-construction contract, active campaign bounds, and
fail-closed barrier. It makes no h32 cache-correctness result, lookup-latency,
hit-rate, capacity, optimizer-convergence, certification, action-width quality,
deployment, population, multi-seat, composition, cross-street, chip-EV, AIVAT,
exploitation, or poker-strength claim. The immutable one-size blueprint
remains the only external policy.
