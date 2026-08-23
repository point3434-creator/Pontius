# ADR-0296: Reject candidate-blind power pools and own stop state

- Status: accepted negative diagnostic and corrective process control; ADR-0295 rejected before v3
- Date: 2026-08-23
- Follows: ADR-0295
- Front-Door-Kind: controller-v1
- Front-Door-Research: ADR-0280
- Front-Door-Process: ADR-0296
- Front-Door-Contract: ADR-0282
- Front-Door-Revoked: ADR-0281
- Front-Door-Active-Next: Preregister a richer reduced sizing-power game before choosing v3; use the owned fail-closed qualification runner, keep batch 2 values unopened, and keep both rejected lattices and all replay, blueprint, convex-master, resolver, and strategy labels closed
- Front-Door-Blockers: the second candidate-blind replication yields only 11 of 12 material contexts within 96, the one-bet three-by-three game remains low-power, and no richer reduced game is frozen

## Verdict

Reject ADR-0295's candidate-blind power-pool protocol before any v3 mechanism
is chosen. Batch 0 reaches its target, but batch 1 yields only 11 material
contexts within the frozen 96-context cap. Batch 2 full/narrow values remain
unopened. No action-abstraction source or candidate value entered this
diagnostic.

Also record a protocol violation in the first follow-up diagnosis: the initial
test failure did not report its batch identity, and a mistaken attribution to
batch 0 caused values 40 through 95 of that already-target-complete batch to be
opened after the frozen stop point. This independently fails ADR-0295's
no-value-after-target gate. Those extra batch-0 values are tainted process
diagnostics and have no authority in this or any future selection.

## Decision

Park the three structural pools, batch-0 qualified panel, batch-0/batch-1
observations, and expected-rejection controls. Do not lower the opportunity
floor, increase the 96-context cap, use the tainted post-stop values, open batch
2, or choose v3 from this result.

Install a structural successor for evidence opening:
`run_candidate_blind_sizing_power_qualification` now owns both LP calls,
classification, sequential context order, and termination. It returns an
immutable result with explicit batch id, pool digest, contiguous observations,
qualified indices, stop reason, and result digest. Panel extraction rebinds the
complete opened observation prefix to the supplied pool. A target-reached
result is valid only when its twelfth qualifier is its final opened
observation; a pool-exhausted result is valid only after all 96 contexts and
fewer than 12 qualifiers; and ambiguity must be the first terminal ambiguity
before the target. The maintained test uses this runner rather than a caller-
managed loop.

This corrects the plumbing defect but cannot rescue the failed research gate.
The next checkpoint must preregister a richer reduced sizing-power game before
another pool or candidate is opened.

## Sealed pools

The three structurally generated pools remain byte-stable:

| Batch | Raw card candidates | Pool SHA-256 | Value status |
|---:|---:|---|---|
| 0 | 180 | `37d6e5ee5ce23b5473b1a3cf7cf521a9e40673a0b514ff2368dc02c5e325eda2` | original prefix through index 39 valid; later diagnostic values tainted |
| 1 | 181 | `7590e8490266315bc3bfcf5757fb6e1cdea232151cb0dd0000b90dbe66aedde6` | all 96 opened by frozen failure path |
| 2 | 175 | `6ac85b6314e4d8bd1124775e2d65899fcc1dd059a6bc649dce42bc3d860ebac8` | **full/narrow values unopened** |

ADR-0293's earlier panel still reconstructs to
`c3d1f5ca6dea3291e202d73e542caccb05cf61bca775b327fad90c3e62bc5438`.
No sealed generator primitive changed.

## Frozen diagnostic result

Batch 0 reaches 12 qualifiers after exactly 40 opened contexts, at indices
`(8, 11, 13, 15, 16, 21, 22, 23, 26, 28, 33, 39)`. Its owned result digest is
`7f4d9e6df70e489bbc5325f1fbf87a4d6ba071c14389be961d68fd96524ddd17`;
the 12-context panel digest is
`e40102cfaeff0a682be78b6628bd415d2c43daacf9a37e65434a1fba9fa8b4ce`.
Those 12 span six pot values, five stack values, and ten showdown-sign
matrices. Their leading two-by-two compact/normal-form comparisons differ by at
most `9.238e-14` chips with maximum duality gap `1.759e-13` chips.

Batch 1 exhausts all 96 contexts with only 11 qualifiers, at indices
`(5, 13, 39, 44, 46, 47, 63, 69, 71, 74, 92)`. Its result digest is
`7574ba9fc1adaf4c3d8546514179630499633bbc07289d1af505917d4b4c05f5`.
The next-largest normalized full-over-narrow gap is
`7.3326432e-5`, materially below the frozen `1e-4` floor; no context lies in
the `1e-8`-chip ambiguity band. This is a yield failure, not a boundary tie.

Across the valid opened paths, maximum probability-simplex residual is
`4.685e-13` and maximum chip-objective reconstruction error is `1.397e-12`,
both below `1e-9`. Static AST inventory confirms that the pool, runner, and
diagnostic test import no legal-action abstraction or candidate source.

## Protocol incident

The initial assertion reported only `11 != 12`, not the batch. The follow-up
incorrectly assumed batch 0 had failed and scanned its complete pool, opening
56 values after its target at index 39. Once the mistaken attribution was
noticed, replay of the original stop path identified batch 1 as the actual
failure and did not open batch 2.

The structural cause was caller-owned termination plus batch-free failure
telemetry. A disciplined `break` was part of the test but not an owned evidence
boundary, so an ad hoc diagnostic could bypass it. The new runner makes stop
state and batch identity part of the semantic result. Future evidence must use
that runner or a successor with equivalent ownership; scratch loops may not
open values.

## Evidence classification

- **Known:** all three structural pool bytes/digests and batch 2's value-
  unopened status.
- **Reproduced:** batch 0 target at 40, batch 1 exhaustion at 11/96, numerical
  controls, and candidate-blind imports.
- **Observed but tainted:** batch-0 values after context 39; they may not
  support any claim or threshold choice.
- **Rejected:** ADR-0295 as a replicated power-construction protocol, a larger
  post-outcome cap, lower floor, batch-2 opening, and any v3 choice now.
- **Hypothesis:** a richer private-type or response-action reduced game can
  produce sizing opportunity at a stable rate without candidate conditioning.

## Dissent

Supporting rejection: the second frozen replication misses its target, the
miss is not numerically ambiguous, and the follow-up violated an independent
stop gate.

Opposing evidence: batch 0 builds a diverse 12-context panel in 40 openings;
batch 1 misses by only one; all numerical controls pass; and the qualifier is
strictly candidate-blind.

Largest unknown: whether low yield is caused primarily by only three private
types, the one-bet/no-raise tree, or the chosen random joint distributions.

Cheapest falsifying next experiment: preregister a small richer-game ladder—
for example increased private-type width versus a responder-raise branch—then
compare full-over-narrow opportunity yield and exact-oracle cost without any
candidate action lattice.

## Claims boundary

This result establishes a failed candidate-blind power diagnostic and an owned
stop-state correction. It does not validate any action abstraction, authorize
v3, make the opened pools representative, establish strategically exact
translation, connect replay hooks, train a blueprint, open action width through
the convex master, resolve a street, establish multiplayer safety, report
NashConv, AIVAT, league strength, optimized latency, or complete C5. No revoked
experiment, external publication, or thesis change is authorized.
