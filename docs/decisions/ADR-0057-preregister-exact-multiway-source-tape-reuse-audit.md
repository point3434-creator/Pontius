# ADR-0057: Preregister exact multiway source-tape reuse audit

**Status:** Accepted before implementation or reuse timing

**Date:** 2026-08-19

## Decision

Run a revealed engineering audit of the exact structural-reuse branch selected
by ADR-0056. Compile one `CompiledPolicyDeltaTape` from each source context and
blueprint, then evaluate all four support-preserving target ranges and every
frozen candidate through simultaneous source-relative range and policy inputs.
Compare that path with ordinary traversal and with the prior one-tape-per-target
control.

The frozen configuration is
`experiments/configs/multiway-source-tape-reuse-audit-v1.json`, SHA-256
`c602cebfa58ac113d4668bc1abc7da1ffdd285e5fecf981949fc49d5537ccd03`.
The result target is
`experiments/results/multiway-source-tape-reuse-audit-v1.json`.

All strategy labels are already revealed. This audit cannot select a solver,
checkpoint, target family, acceptance rule, or scheduler; authorize validation
or test access; or establish a new strategy result. It asks only whether exact
source-relative structural reuse preserves the frozen result and improves its
evaluator economics.

## Frozen inputs

Require byte-identical inputs:

1. ADR-0054 configuration SHA-256
   `807d511a920ee1bcb13d5cf54ca61991c30bb63845dabfb9e04d318c1f8ef0a4`;
2. ADR-0056 result SHA-256
   `27739ba1d66a14a2a9d4a69914ce23ea70f332d6535b82fa7efa99192aba1b74`;
3. search runner SHA-256
   `23a645c24d75cd610ccaa11709c6cdf7258062f93181bc755f9c024f706f45fd`;
4. context generator SHA-256
   `806a0238ea2f0f9148209e1e515b35a17ae2fb5731de0ec103317557f2b253aa`;
5. multiway game SHA-256
   `942e2b4bf2acc0c5937b378a2d7620c5f318060d1068c84430af17e13de414d5`;
6. coalition evaluator SHA-256
   `6aee741a2f90d42c935bb85d6b8ac616bbcbbc3d90ef588112529c27133c86a3`;
   and
7. dependency tape SHA-256
   `da7a89870b59dc151c8a056ab32468ed3206471959ac3b26dffca0d733c06501`.

Regenerate exactly six development groups, 24 contexts, 96 targets, and 1,728
candidate records. Construct no reserved context. Every source must retain the
same outcome support under all four range shifts; otherwise fail rather than
expanding the source tape's universe after compilation.

## Three equal-output paths

For every target and candidate, time these paths separately:

1. `ordinary`: ordinary baseline evaluation once per target plus ordinary
   candidate evaluation;
2. `target_compiled`: compile one target-range tape, take its source result as
   the baseline, then apply each candidate as a policy-only update; and
3. `source_reuse`: compile one source tape per context, apply each target range
   with the blueprint once for its baseline, then apply the same target range
   and candidate policy together from the immutable source epoch.

Use dense execution throughout. Compilation, baseline updates, candidate
updates, solver work, policy output, and coalition evaluation remain separate.
The source tape is never mutated into a new baseline: every call is defined
relative to its original range and blueprint.

Ordinary traversal remains the numerical oracle. Recompute all coalition
labels to prove that regenerated candidate policies still reproduce the
revealed frozen records; coalition work is not credited to source-tape speed.

## Correctness and call-order gates

Require:

1. maximum ordinary/target/source evaluation disagreement at most `1e-10`;
2. maximum regenerated baseline or candidate metric disagreement with the
   frozen artifact at most `1e-12`;
3. zero literal best-response action mismatches;
4. zero aggregate, unilateral-Pareto, or coalition-stress label mismatches;
5. identical source and target policy/action schemas;
6. exact support preservation; and
7. after every other range and policy call in a context, replay its first
   target's primary DCFR-32 candidate with zero numerical or action-map change.

The last gate tests source-relative epoch semantics against range and policy
call-order contamination. An approximate distance, overlap, embedding, or
nearest-range cache key is forbidden.

The initial preregistration transcribed the multiway-game digest with `c` in
place of `b`. The strict configuration parser rejected it before context
generation, solving, evaluation, or timing. The digest and configuration hash
above were corrected at that point; no workload or gate changed.

## Frozen performance accounting

Aggregate these evaluator paths over the complete trajectory:

- `target_compiled = 96 target compilations + 1,728 policy-only updates`;
- `source_reuse = 24 source compilations + 96 baseline range updates + 1,728
  simultaneous range-plus-policy updates`; and
- `source_precompiled = source_reuse - 24 source compilations`.

Require source reuse to be strictly faster than the target-compiled path and
the source-precompiled path to be strictly faster than ordinary baseline plus
candidate evaluation. Persisted source-tape bytes divided by four target-tape
bytes per context must be at most `0.26`; the theoretical structural ratio is
one quarter, but report measured bytes rather than assuming equality.

For the fixed primary DCFR-32 arm, retain ADR-0056's exact accepted reduction
and solver charge. Add one target-baseline range update and one simultaneous
candidate update. The precompiled source rate must strictly beat blind. Also
report rates when source compilation is divided by each integer reuse count
from one through eight, and require the first winning count to be at most eight.
This reuse curve is a break-even analysis, not evidence that the four synthetic
targets occur together online.

Do not use the revealed best diagnostic checkpoint to improve a rate. DCFR-32
remains the only primary accounting row.

## Branching interpretation

- If exactness or call-order replay fails, stop. Approximate factorization must
  not build on a contaminated cache.
- If correctness passes but source reuse does not beat target compilation,
  retain the target-specific tape and attack compilation directly before a
  low-rank belief representation.
- If correctness and reuse pass but primary break-even requires more than eight
  reuses, retain source reuse as an offline evaluator optimization only.
- If every gate passes, use the source-compiled evaluator as the exact oracle
  and begin a separately frozen factorized/low-rank belief contraction. That
  next experiment must preserve every per-player term and action map, not only
  root utility or aggregate NashConv.

## Dissent protocol

**Confidence:** very high in exact reproducibility; moderate that saving 72
compilations outweighs the extra baseline range updates; low that Python timing
ratios predict a native six-player kernel.

**Opposing evidence:** the same root support makes this the easiest legitimate
reuse case. Earlier streets can add public cards and delete private combos,
forcing a new topology epoch. Conversely, within-street Bayesian range changes
often preserve support and can reuse much more than four times.

**Largest risk:** confusing exact source-relative reevaluation with a cache hit
for a merely similar range. This audit authorizes only the former.

**Cheapest falsification:** any mismatch against ordinary evaluation, any
changed best-response action, or any failure to replay the first primary
candidate after all other calls in its context.
