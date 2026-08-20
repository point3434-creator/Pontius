# ADR-0120: Resident CFR is the wide two-step engine

## Status

ADR-0119 executed and all frozen successor gates passed.

## Result

The v2 artifact is `h32-resident-cfr-audit-v2.json`, SHA-256
`9b895be6f6abffc35a51cb8e20c95b8b1657d69b63855255a9e8a33bc3a0372c`.
It reran the immutable ADR-0117 workload in `298.672 s`; it did not reuse the v1
timings.

Cross-run numerical identity passed with wide margins:

- transferred versus stored-teacher regret error: `9.853e-16`;
- transferred versus stored-teacher strategy-sum error: `2.220e-16`;
- resident versus transferred regret error: `9.229e-16`;
- resident versus transferred strategy-sum error: `2.220e-16`;
- maximum resident-versus-transferred policy error: `8.275e-16`;
- maximum mean information-set TV: `2.219e-18`.

Zero of eight independently accumulated state digests matched the stored
teacher, repeating ADR-0118's diagnostic.  They remain reported and are not
misrepresented as semantic identities.

## Economics

The v1 systems result repeated:

- pooled two-step marginal speedup: `3.274x`;
- pooled two-step cache-charged speedup: `2.728x`;
- weakest target one-step cache-charged speedup: `2.228x`;
- weakest target two-step cache-charged speedup: `2.675x`;
- per-target marginal two-step speedup: `3.196x` to `3.332x`;
- resident static cache: `3.468 GB` blocker-heavy and `4.232 GB` balanced;
- maximum GPU pool: `7.408 GB`;
- marginal transfer reduction: `101.19x`, from `351.705 GB` equivalent to
  `3.476 GB` actual across the eight resident steps.

The h7 control measured `1.095x` marginal and `1.035x` cache-charged in v2,
after measuring `0.962x` and `0.908x` in v1.  Its exactness was stable while its
small timing sign was not.  No hand-count selector is fitted or authorized.

## Decision

Adopt `ResidentLeafAdjointPublicTreeCFR` as the exact engine for the demonstrated
h32 one/two-step warm-search customer.  Keep `LeafAdjointPublicTreeCFR` as the
teacher, portability path, small-axis control, and fallback when device-resident
memory cannot be reserved.

The selection is made from declared workload capability, not a fitted timing
rule: h32 with a precompiled resident belief and six target-seat automaton
caches uses the resident engine.  Unsupported widths and memory-constrained
concurrency abstain to the existing transferred path until separately measured.

The next strategic systems test should not optimize this kernel further.  It
should use the saved budget in a wider poker game or in a sustained continuation
that produces a strategy label the current one-bet river laboratory cannot
answer.  A native fusion is deferred because the Python/CuPy resident path has
already removed roughly 70% of step time and terminal contraction still owns
more than 99% of the remainder.

## Scope and limitations

This decision covers one river public tree, equal stacks, one bet size, two
generated range families, four fresh-board target beliefs, and two alternating
DCFR steps on h32 axes.  It does not establish long-run accumulator drift,
multi-size or raised pots, earlier streets, neural leaves, exploitability against
coalitions, or a general hand-count crossover.  The 4.23 GB static-cache cost is
material on the 16 GB RTX 5080 and forbids assuming multiple concurrent resident
workspaces.
