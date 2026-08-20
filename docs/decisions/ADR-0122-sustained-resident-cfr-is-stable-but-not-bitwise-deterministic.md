# ADR-0122: Sustained resident CFR is stable but not bitwise deterministic

## Status

ADR-0121 executed.  The frozen audit failed five restart-identity gates and is
not relabeled as a pass.

## Result

The artifact is `h32-resident-cfr-sustained-audit-v1.json`, SHA-256
`9f60a3d5da5a49c089f3af125d8de854317fb97e898498826a2d6eaf1a0a9c85`.
It completed in `307.198 s` and executed 32 primary resident steps plus four
restart-continuation steps.

Every teacher, economics, stability, memory, and resource gate passed.  Across
16 stored-teacher comparisons through iteration eight:

- maximum regret error: `2.735e-15`;
- maximum strategy-sum error: `4.663e-15`;
- maximum policy-probability error: `4.552e-15`;
- maximum mean information-set TV: `6.390e-18`.

The errors grew gradually from iterations one to eight but remained more than
four orders below the frozen numerical ceilings.  No stored-teacher state digest
matched, consistent with ADR-0118 and ADR-0120's cross-run result.

Sustained economics also passed on every target:

- pooled marginal speedup: `3.201x`;
- pooled cache-charged speedup: `3.052x`;
- weakest target marginal speedup: `3.162x`;
- weakest target cache-charged speedup: `3.016x`;
- maximum late/early median-step ratio: `0.985`;
- maximum step: `8.818 s`;
- maximum GPU pool: `9.417 GB`.

The failed restart compared an uninterrupted iteration-eight state with a
continuation restored from its literal iteration-four checkpoint.  Differences
were small but nonzero:

- regret error: `1.277e-15`;
- strategy-sum error: `1.846e-15`;
- current-policy maximum error: `1.915e-15` and mean TV `4.111e-18`;
- average-policy maximum error: `7.286e-16` and mean TV `2.936e-18`.

Consequently the current policy, average policy, and final state digest were not
byte-identical.  The zero-error gates correctly failed.

## Interpretation

The checkpoint serializer restores the literal accumulator object; the failed
claim is stronger: independently executing the next four GPU sparse reductions
does not reproduce identical final bits.  The resident path uses CuPy CSR sparse
matrix products whose parallel reduction order is not specified by this
laboratory.  The artifact is consistent with reduction-order variation, though
it does not by itself isolate a particular CUDA primitive.

This is not evidence of strategic drift through iteration eight.  It is evidence
that exact checkpoint restoration and bitwise deterministic future execution are
different contracts.  ADR-0121 deliberately conflated them as a strict test, and
the test rejected that conflation.

## Decision

Preserve the formal failure.  ADR-0121 does not yet authorize resident CFR for
longer blueprint training under its frozen contract.

Authorize one contained successor on the single restart-control target.  It must
separate and test three properties:

1. immediate restore/re-export of the stored checkpoint is bit-identical;
2. two independent continuations from that same checkpoint remain within the
   pre-existing numerical CFR and policy tolerances;
3. exact current- and average-policy quality vectors remain within `1e-10` after
   continuation.

The successor will run two independent restored continuations so the source of
variation is not inferred only from uninterrupted-versus-restored execution.
No speed threshold changes, new strategy target, or second correction is
authorized.

## Scope

This result still covers only eight warm-search iterations.  Numerical stability
at eight does not prove average-policy equivalence at 64 or eliminate the need
for a deterministic native reduction if byte-reproducible training becomes a
product requirement.
