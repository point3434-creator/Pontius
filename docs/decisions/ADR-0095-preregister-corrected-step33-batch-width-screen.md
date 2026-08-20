# ADR-0095: Preregister corrected step-33 batch-width screen

**Status:** Accepted after ADR-0093's post-balanced cleanup rejection, before
any row value, blocker-heavy arm, summary, selector, or gate result

**Date:** 2026-08-20

## Decision

Rerun the ADR-0093 screen with one additive orchestration correction. Preserve
every scientific field, source, width, order, repetition, selector, threshold,
and resource ceiling.

The corrected frozen config is
`experiments/configs/leaf-adjoint-batch-width-audit-v2.json`, SHA-256
`f9b8a23221ce008d89013bcfad140567120ce841b6bf5a99cdb2bb608cbcc432`.
The additive runner is
`src/pontius/leaf_adjoint_batch_width_audit_v2.py`, SHA-256
`478143cb1d0b2a6144c9dcc76faf3e8d922e74825363fcb7698047b66ca35967`.
The result target is
`experiments/results/leaf-adjoint-batch-width-audit-v2.json`.

The rejected ADR-0093 implementation remains immutable at SHA-256
`d41fab3383dd4f9d0fb65bc8acf3b7cbdbf7a06e06004e8e734b26036c74696f`
and is pinned by the successor config.

## Frozen scientific identity

ADR-0093 remains the complete scientific protocol. In particular, retain:

- ADR-0092 checkpoint source SHA-256
  `242de5f0a42693248f98cc8f127f4fc892606df58e94d28c107d542b1276736b`;
- both h32 range families and the exact iteration-32 states;
- one width-384 warmup per family;
- measured order `384, 768, 1536, 1536, 768, 384`;
- two repetitions per width/family;
- pooled selector `minimum_sum_family_median_step_ms_ties_smaller_width`;
- full regret, strategy-sum, current-policy, and average-policy comparisons;
- `1e-9` accumulator/probability and `1e-10` mean-TV gates;
- at least 1.10x selected pooled step speedup and 2.0x batch reduction;
- exact trace/batch and source-state identities; and
- the 8 GB host, 12 GB CuPy-pool, 60-second step, and 900-second audit
  ceilings.

No NashConv or other strategy-quality label enters selection.

## Sole implementation correction

Move complete family scheduling into `_measure_family_schedule`. It owns:

1. warmup execution and compaction;
2. release of the warmup's private tables;
3. all six measured arms;
4. width repetition accounting;
5. first-baseline reference retention;
6. full numerical comparisons; and
7. compact row return.

The caller receives only compact warmup/measured rows. Family-local solver,
workspace, GPU, automata, and reference objects then expire by ordinary scope
and a cleanup that does not name the already-released warmup.

The numerical and tracing primitives are imported unchanged from the rejected
v1 implementation. The corrected runner adds no new width, metric, branch, or
threshold.

## Evidence boundary

Known at freeze:

- v1 validated/restored balanced iteration 32 and executed its warmup plus six
  measured balanced arms before failing in cleanup;
- no row value was serialized or printed;
- no aggregate, selector, or gate ran;
- blocker-heavy did not start; and
- the only observed scientific fact is the failure position.

Still held out:

- every balanced and blocker row timing/error/phase/memory value;
- batch counts at width 768 or 1536;
- selected width and pooled speedup;
- all exactness/economic/resource gates; and
- every output policy or accumulator digest.

The successor is therefore less pristine than ADR-0093 because it knows the
balanced schedule did not raise before cleanup, but its actual measurements
and decision remain sealed.

## Complete-path test added

A mocked family test invokes the same scoped helper used in production. It
crosses:

- one warmup;
- all six widths in exact order;
- repetition indices `[1, 1, 1, 2, 2, 2]`;
- baseline retention and all numerical comparison fields;
- private-table removal from every returned row; and
- successful return after the point where v1 failed.

The corrected parser, scientific-field immutability, rejected/new
implementation hashes, and gate immutability also pass targeted tests. This
test would have failed the v1 orchestration contract.

## Interpretation

Use ADR-0093's frozen branches unchanged. A corrected execution failure is
recorded as another rejection; do not make a third silent correction. A clean
result selects a width only if exactness, batch reduction, speed, and resource
gates all pass.

## Limitations

All ADR-0093 limitations carry forward. This correction does not restore the
pristine pre-balanced evidence boundary and does not turn the screen into a
strategy experiment.

## Dissent protocol

**Confidence:** very high that the duplicate-cleanup defect is removed and the
complete-path test covers its class; unchanged confidence in the unknown width
economics.

**Opposing evidence:** mocked scope cannot reproduce GPU allocation lifetime.
The production run still exercises actual workspaces and CuPy pools under the
same 12 GB gate.

**Largest risk:** another top-level orchestration defect after spending the
balanced bill again. The helper test now crosses the prior failure boundary,
and the remaining aggregation code is already unit-tested in v1.

**Cheapest falsification:** complete corrected execution; no smaller h32 probe
can recover the two-family pooled selector.
