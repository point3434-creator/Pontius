# ADR-0130: The h32 affine preflight fails scale-canonical identity

## Status

ADR-0129 executed from clean commit `b89ed7d`.  Sixteen of seventeen frozen
gates passed, but the affine-basis count gate failed.  The run is not accepted
as a successful h32 affine-cache result.

## Evidence identity

The 38,651-byte artifact is
`experiments/results/h32-affine-resident-cache-preflight-v1.json`, SHA-256
`b09612a2bb7afe46053bffbf3bf19bdae7bf03c0dc40b3283c720ccdc9200e5f`.
Its configuration SHA-256 is
`903b904b285f10e9ecf7134873c23e4eff368f54e387265dab18e5580fc0f825`.
The run recorded strict clean Git state at
`b89ed7dd9c29a414bc9d919d70624be3f61ee024` and completed in
`105.2500 s`.

An initial invocation stopped before runtime measurement because
`PONTIUS_CUDA_DLL_DIRECTORY` was absent.  The recorded invocation supplied the
packaged CUDA directory, passed the frozen runtime identity, and wrote the only
result artifact.

## Passing evidence

The parent, strict-cleanliness, h2 affine correctness, target identity, public
topology, payoff-span, logical-rank, raw-equivalent-byte, storage-reduction,
cold-construction, pool-ceiling, conditional-branch, step-resource,
no-quality, and wall-time gates all passed.

- The constructed two-size game derived a 48-chip payoff span from
  `layout.game.payoff_span`; the stack was not used as a span.
- All four targets reproduced their frozen descriptors and belief digests.
- Raw-equivalent automaton bytes matched ADR-0128 exactly.
- Logical total middle rank remained 20,648 for balanced and 19,432 for
  blocker-heavy beliefs; maximum ranks remained 105 and 99.
- Affine persistent bytes were 4,232,286,556 balanced and 3,468,533,492
  blocker-heavy, approximately 51.30% of raw two-size residency.
- Post-cache pool totals were 4,298,886,656 and 3,527,368,704 bytes, leaving
  7,701,113,344 and 8,472,631,296 bytes below the 12 GB ceiling.  Physical
  free memory was also above the unchanged 5,184,456,164-byte reserve.
- Production compilation reconstruction-checked every grouped member and did
  not raise an identity or payoff error.

These measurements are retained as diagnostics.  The failed aggregate gate
prevents promoting them as an accepted successor result.

## Failed basis-count gate

ADR-0129 required 378 affine basis identities, matching the amount-independent
transition topology count.  The hardened cache observed 384: 64 per target
seat rather than 63.

The cause is not a missing semantic field or an incompatible winner basis.
The hardened digest divides the stored terminal payoff by `final_pot` and
hashes the resulting Float64 bytes.  A five-way winner share demonstrates the
problem:

- `(12 * (1/5)) / 12` has hexadecimal Float64 value
  `0x1.999999999999bp-3`;
- `(30 * (1/5)) / 30` has value `0x1.999999999999ap-3`; and
- `(48 * (1/5)) / 48` returns `0x1.999999999999bp-3`.

Thus the all-check full-contender basis and one amount-specific full-contender
basis fail to share on h32 axes containing a five-way tie, even though their
winner-share algebra is identical and their reconstructed vectors agree within
the frozen tolerance.  The h2 preregistration control lacked that tie pattern
and therefore observed the expected 378.

This is a safe false negative for sharing, not silent payoff corruption.  It
still falsifies the frozen representation claim and gate.

## Conditional step disposition

All four measured caches and the selected cache rebuild passed the frozen
headroom rule, so the runner executed the authorized single alternating affine
resident step before evaluating the aggregate basis-count gate.  This complied
with ADR-0129's conditional branch; the later gate failure makes the step
diagnostic only.

The step used game-derived payoff span 48 and regret mass 4.8.  It completed in
`19,616.316 ms`, or `2.24529x` the matching `8,736.643 ms` one-size incumbent.
Terminal contraction consumed `19,530.645 ms`; 824 sparse batches covered all
2,310 terminal contractions.  CuPy pool high-water was 9,737,651,712 bytes,
below the frozen 12 GB ceiling.  No policy was serialized or evaluated.

The one-step allowance is spent.  It must not be repeated merely to repair the
failed cache-identity gate.

## Decision

Reject ADR-0129 as an accepted h32 affine-cache result because one frozen gate
failed.  Preserve the artifact and the one step as diagnostic evidence only.

Build an additive scale-canonical cache identity that encodes each normalized
winner share by its exact semantic class: zero or tie multiplicity `1..N`.
Retain the production per-member reconstruction check.  Small controls must
cover five-way ties and equal transition tables with genuinely different
final-mode winner bases.

After those controls pass, preregister one cache-only h32 successor replay over
the same four targets.  It may measure corrected basis count, bytes, ranks,
construction, and headroom, but it must execute zero widened steps regardless
of memory outcome.  No strategy-quality claim is authorized.

## Dissent

**Confidence:** very high in the failure diagnosis because the extra basis is
reproduced by exact Float64 encodings and no member reconstruction failed;
high that semantic tie-multiplicity codes restore 378; moderate that removing
the six duplicate bases materially changes bytes.

**Opposing evidence:** hashing rounded normalized floats would be a smaller
patch.  It would introduce an arbitrary tolerance into an identity key and
could merge values that are merely close rather than algebraically equal.

**Largest unknown:** the byte contribution of the six full-contender duplicate
bases at h32 and whether removing them changes cold construction enough to
matter after production reconstruction checks.

**Cheapest falsification:** an h2/h7 cache containing explicit five-way ties.
It must produce equal canonical identities across pots 12, 30, and 48 while
still separating a changed final-seat strength library.
