# GPU solving and card representation

[Results index](RESULTS.md) · Updated 2026-09-08 · Local research and engineering evidence

**Current conclusion:** exact structure and device residency made reduced river
solving substantially cheaper. A different occupied-card representation also
made one literal full-width contraction fit the workstation. Neither result
establishes a complete full-width poker resolver. The later legal-context and
exact-integer work retains useful arithmetic controls, but its capacity
projections fail and its final compiled calibration is incomplete.

This guide consolidates the representation question separately from
[solver foundations](solver-foundations.md), [safe search](safe-search.md), and
[action abstraction](action-abstraction.md). It exists because a successful
kernel, a successful numerical comparison, and a useful poker decision answer
different questions. Archived decisions below are historical evidence, not
current operating instructions.

**Terms:** `h32` means 32 retained private hands per seat, not full poker ranges.
A tensor train (TT) represents a large value array as contracted smaller arrays;
its rank controls their connecting dimension. FactorTT combines this with card
belief factors and exact conflict exclusion. An **open mode** leaves a player's
hand axis available for action values. **Leaf adjoints** propagate terminal
contributions back through the public tree without repeatedly recompressing
policy-conditioned TTs. **Resident** means reusable arrays stay on the GPU.
An **occupied-card quotient** groups labeled assignments by their used-card set,
after including seat-specific features; its transpose returns contributions to
the required labeled records. RRNS is a redundant residue number system, an
integer arithmetic alternative to positional representation.

## Which capabilities survived their controls?

Times below retain their original measurement boundaries. A validation campaign
contains reference work and repetitions; it is not a resolver iteration.

| Question | Evidence and interpretation | Scope and source identity |
|---|---|---|
| Can exact expectations avoid joint-deal enumeration? | [Direct FactorTT](../docs/archive/ADR-0066-direct-factor-tt-contraction-passes.md) measured a pooled **6.300 ms** hot operator versus **1,556.741 ms** enumeration at ten hands. | Topology and belief compilation excluded. Rank eight ceased to be exact on the seven-hand extension, despite passing the earlier four/five-hand screen. Source `2001743a64132768ff4f7cc454c08cfebaf8127e`; recorded raw path `experiments/results/factor-tt-direct-contraction-audit-v1.json`. |
| Does accelerating a value reader produce a solver? | [Sparse incidence](../docs/archive/ADR-0084-sparse-incidence-transfers-but-raw-action-gate-rejects-exact-ties.md) improved the held-out h32 reader **8.627×**, but failed 13 raw action identities at mathematical ties. [Leaf-adjoint DCFR](../docs/archive/ADR-0086-leaf-adjoint-dense-free-h32-dcfr-passes.md) subsequently passed complete update comparisons and emitted h32 policies. | The latter removed 1,152 public-node SVDs; its h7 comparison improved **18.149×** over rounded public caches, while the small dense teacher remained faster. Source `842499bcfb184fb709a44a3185378b0b5a232c91`; recorded raw path `experiments/results/leaf-adjoint-cfr-gpu-audit-v1.json`. |
| Does residency preserve solver semantics? | [Resident v2](../docs/archive/ADR-0120-resident-cfr-is-the-wide-two-step-engine.md) measured **3.274×** marginal and **2.728×** cache-charged two-step speedup. [Restart correction](../docs/archive/ADR-0124-resident-cfr-restores-exactly-and-continues-equivalently.md) established exact immediate restoration and numerically equivalent future execution. | Static cache **3.468–4.232 GB**; demonstrated restart horizon eight iterations. Earlier byte-identity failures remain failures. Recorded raw files: `experiments/results/h32-resident-cfr-audit-v2.json` and `h32-resident-cfr-restart-semantics-audit-v1.json` in that directory; archived decisions retain their hashes. |
| What should h32 optimization target? | [Corrected profile](../docs/archive/ADR-0198-device-pipeline-dominates-h32-step-host-fold-is-second.md): device work **67.87%**, host record-to-hand folding **30.56%**, transfers **0.63%**. Median complete step **9,433.52 ms**. | Two previously exposed timing extremes, three restarts each; no latency distribution. Device total combines pipeline and product-generation buckets. Recorded source `9f62521`; raw path `experiments/results/h32-resident-step-bottleneck-profile-v2.json`. |
| Can the h32 layout simply grow to full ranges? | [Full-width capacity rejection](../docs/archive/ADR-0366-retain-the-full-width-factor-tt-representation-rejection.md) derived **733,055,400** three-opponent half records and an optimistic scalar topology lower bound of **202.627 GB**. | Zero target allocations or contractions. This rejects the explicit-half-assignment layout, not exact full-width computation generally. Source `6fb001d58272856c35a437d49a7407c13ba77d48`; [raw result](results/full-width-river-capacity-preflight-v2.json). |
| Did quotienting overcome that representation barrier? | [Literal-45 primitive](../docs/archive/ADR-0384-retain-the-passing-literal-45-quotient-target.md) passed all **27 gates**, with **11.621 GB** maximum pool allocation and complete release. It followed the passing staged ladder through 40 cards. | Full 45-card geometry, 990 hands per large axis, structured affine fixture; not a calibrated poker-context resolver. Source `102307bb565892fb07fc9ec8467e91c17cc09b83`; [raw journal](../artifacts/literal_45_quotient_target_v1.jsonl). |
| Did legal-context CUDA inherit that success? | [Shared-direct v3](../docs/archive/ADR-0429-retain-the-passing-shared-sample-plan-v3-validation.md) passed complete populations **10 and 22**; population 22 took **49.419 s**. Its [capacity assessment](../docs/archive/ADR-0432-retain-the-shared-direct-artifact-capacity-rejection.md) subsequently projected **4,999.487 s** against a 180-second validation allowance. | Correct bounded numerics, failed conservative capacity estimate; no complete population-25 value. V3 source `00d29e048d88ff4ece325b2a00866ddbd084617c`; [raw journal](../artifacts/work_preflight/legal_river_quotient_cuda_shared_direct_device_v3.jsonl). Assessment source `e0662641f0ff1d59e2576425ceab27d678ce3e6a`. |
| Can fixed-width integer arithmetic work on the device? | [Split-runtime preflight](../docs/archive/ADR-0448-retain-the-passing-split-runtime-fixed-width-device-preflight.md) passed all **42 candidate observations** on complete-10 and signed-12. Positional and batched RRNS passed symbolic memory eligibility; resident-nine RRNS failed that memory condition. | No selected arm, no actual-45 numerical call. Source `f271e6deeefe11f228d582c9734a166c0ba32b45`; [raw journal](../artifacts/work_preflight/legal_river_quotient_fixed_width_device_preflight_v3.jsonl). |
| Did memory eligibility imply usable full-width work? | [Fit projection](../docs/archive/ADR-0452-retain-the-literal-45-fit-projection-rejection.md) rejected both eligible arms: **3,186.555 s** positional and **9,908.353 s** batched RRNS versus a 14-second component allowance. Global adjoint scans supplied over **90%** of each projection. | Conservative extrapolation, not measured literal-45 latency or impossibility proof. Source `d6f85ac9d95bf87149e9c411b2ec81bae86977ba`; [raw journal](../artifacts/work_preflight/legal_river_quotient_fixed_width_actual45_fit_projection_v1.jsonl). |
| Did compiled global separation select a replacement? | [V7 calibration](../docs/archive/ADR-0476-retain-the-v7-laboratory-wall-rejection.md) reached **1,510.054 s** against a 1,500-second laboratory limit: **480 warmup cells**, **89 partial measured-labelled cells**, no completed measured pass or arm choice. | Complete journal, incomplete experiment. Source `aaca2dda40e29be8ebd091d58e7853bce1c62fd8`; [raw journal](../artifacts/work_preflight/legal_river_quotient_compiled_global_separation_calibration_v7.jsonl). |

## What the negative results teach

Two earlier infrastructure outcomes remain distinct from later capacity results.
The first full-width capacity attempt failed in Windows memory telemetry before
either reduced control or target accounting; it established no capacity bound.
Its invocation source was `c7d96241e8642aa85964865a0c90e591a6788f9c`.
[Telemetry failure](../docs/archive/ADR-0364-retain-the-full-width-capacity-telemetry-failure.md)
The artifact-only exact-cubin selector inspected five retained candidate records,
rejected the only semantically eligible resource candidate on its nonzero return
code, and returned no qualified inspector. No resource gate, calibration, or
projection followed from that selection. Its source-only parent was
`9ef1c2787432ccfb30db0c42d7e41d10b7fab919`.
[Empty selection](../docs/archive/ADR-0409-retain-the-empty-exact-cubin-inspector-selection.md)
Their archived reports and result JSONs remain after retiring the tests that
only reasserted these saved outcomes.

Compression correctness and economics must be tested separately. The
[policy-delta TT cache](../docs/archive/ADR-0070-policy-delta-tt-correct-four-reuse-rejected.md)
was correct but missed its four-reuse speed gate: expensive upper-tree
recompression dominated despite skipping many nodes. Likewise, small rank
errors can change responses; the early rank-eight result never established a
universal rank bound.

Floating-point comparisons need explicit semantics. The
[bounded legal CUDA consumer](../docs/archive/ADR-0390-retain-the-bounded-cuda-consumer-numerical-rejection.md)
missed an absolute transpose ceiling by one ULP at a large numerator, despite
passing its relative comparison. That is a numerical-contract rejection.
Compiler/bootstrap failures elsewhere answer no arithmetic question. Resident
restart failures instead distinguished stored-object identity from future
parallel reductions; the corrected experiment tested both separately.

The fixed-width device sequence makes that distinction concrete: v1 failed
because NVCC could not find `cl.exe`; v2 failed before any scientific event
because the child runtime changed PATH after compiler activation. V3 then
completed the reduced numerical campaign with separate environment bindings.
Similarly, shared-direct v2 mixed seven-row and sixteen-row sample plans before
v3 shared a single plan. Their separate findings and invocation commits are in
[the root-launcher harvest](RESULTS.md#final-root-research-launcher-harvest--2026-09-08).

V7's retained partial schedule diagnoses excessive cold base construction:
`base_structural_cover` occupied **96.41% of recorded primitive wall**. It cannot
rank topologies because the measured population is incomplete. More critically,
the experiment recorded `producer_absent`: no production source-local base and
refresh cadence existed to justify amortizing that construction.

## What evidence would make these capabilities useful next?

- **Preserve the exact teachers.** Dense small-game and transferred leaf-adjoint
  paths distinguish representation errors from solver-update errors. Reduced-game
  NashConv improvement was separately measured in
  [ADR-0088](../docs/archive/ADR-0088-dense-free-nashconv-passes-two-step-policy-improves.md);
  kernel speed alone supplies no poker-strength claim.
- **Measure complete resident work.** Test device-side record-to-hand folding
  against numerical and timing controls. The profile's hardware multipliers are
  serial counterfactuals, not evidence that a particular GPU upgrade delivers them.
- **Bind a real full-width consumer.** Establish its exact base algebra, exponent
  bounds, invalidation and cold/hit frequency before another topology calibration.
  Retain global coverage of omitted rows; certifying only an active subset does
  not establish a global resolver certificate.
- **Separate fit from quality.** Complete actual-context numerical and resource
  measurements, then charge a complete iteration and action. Neither the passing
  primitive nor a rejected conservative projection decides that final result.

## Evidence availability

This synthesis checked archived originals and raw hashes for the six locally
present linked capacity/device journals or results. Early FactorTT, leaf-adjoint,
resident and profile JSONs named above are absent from this checkout; their
numbers and identities come from the archived reports, not fresh raw validation.

The [shared-direct capacity result](../artifacts/work_preflight/legal_river_quotient_shared_direct_artifact_capacity_v1.json)
has a documented checkout newline difference: the local file is 9,183 bytes;
its verified HEAD Git blob is the recorded 9,182 bytes with SHA-256
`9e6e3d45797eb9aeea8e91994f67e7ff641747a80a8d240799adfab1325961af`.
Use that blob for historical byte verification. No experiment was rerun for this
page. Historical readers may require their original source checkout; their
failure on a later checkout is not by itself evidence corruption.

## Retired experiment drivers — 2026-09-08

The leaf-adjoint CFR/GPU audit driver and its frozen-config test were retired
after preserving their question, comparison, result, and source above: does the
leaf-adjoint update match the dense control and reduce solver cost? The reported
update agreement and 18.149× h7 comparison remain historical measurements from
source `842499bcfb184fb709a44a3185378b0b5a232c91`. The reusable leaf-adjoint CFR,
evaluation, and contraction implementations and their behavioral tests remain.

The one-off actual-45 fit-projection launcher and runner were also retired.
Their result remains the 3,186.555 s / 9,908.353 s conservative projection
rejection from source `d6f85ac9d95bf87149e9c411b2ec81bae86977ba`; it is not a
measured actual-45 latency. Projection arithmetic, the reader, and the outcome
module remain. Eight synthetic behavioral checks now run in the normal pytest
manifest, covering counts, timing boundaries, independent reconstruction,
outcome interpretation, and malformed inputs. Tests requiring an uninvoked
owner, missing result, or archived source seal were retired.

No result/configuration file was deleted or experiment rerun. Retired code is
recoverable from `91f031e91c957a9b273c2ccc345421f7b286b416`. Historical readers
that resolve source files through Git still use the original commit; this
cleanup does not claim to modernize all remaining evidence-reader interfaces.

The next isolated-driver batch also retired the fixed-policy root TT and
incremental TT audit drivers, leaf-adjoint best-response audit, resident CFR v2
rerun, sustained/restart audits, and the failed original step profiler. Their
question/method/result/source paragraphs were preserved before deletion in
[the results harvest](RESULTS.md#harvests-before-retiring-isolated-audit-drivers--2026-09-08).
Reusable TT algebra, cache updates, resident solvers, evaluation, and checkpoint
code remain with behavioral tests. Public-policy and incremental-cache tests
now run in the maintained manifest; optional GPU coverage remains separate.

The direct factor–TT audit has now been retired as well, after its question,
method, result, and source were [harvested](RESULTS.md#mixed-helper-and-root-staging-cleanup--2026-09-08).
Its only live helper consumer was a sparse-contraction test. That deterministic
fixture now lives in the existing test module, with identical generated arrays;
`factor_tt_contraction.py` and the sparse/dense contraction implementations
remain. This separates test data generation from the old experiment driver.

The final six root launchers and the unused selective-separation runner have
also been retired after the linked harvest. The five completed device journals
remain unchanged and their hashes match the archived reports. Selective
separation still has no completed one-shot artifact: its retained value is the
exact CPU pricing/bound/search capability and its independent reader, not a
measured pruning or latency result. Seven existing behavioral controls now
join the maintained test manifest. Their synthetic codec fixture isolates the
old source-admission guard while exercising real pricing, search, serialization,
and independent reconstruction. Original campaigns belong in their historical
checkout, not the current working tree.

The follow-on caller review retired four more runners: shared-direct v2/v3 and
fixed-width device preflight v2/v3. Their only live consumers were historical
wrapper tests. The shared sample-plan implementation remains, and nine v2 reader
controls plus eleven v3 sample-plan/reader controls now join the normal manifest.
Their common synthetic fixture extracts the same hash-checked cubin from the
retained journal; it no longer calls historical source admission. Payload
classification and semantic/mutation checks remain real and passed in the
focused run. No CUDA code executes in these tests.

The original fixed-width runner was initially retained for its numerical-reader
fixture and has now been retired after that fixture moved into the existing
test file. Its in-memory success and failure journals matched the old writer
byte for byte. Fifteen fixed-width tests now join the maintained manifest; one
population/representation test requires `math.fma` and runs on Python 3.14,
with an explicit skip on Python 3.11. Numerical population setup isolates the
historical capacity source-admission check while retaining the actual algebra.
The synthetic reader verifies the fixture file's actual dependency hash rather
than the old source manifest. See [the fixture extraction](RESULTS.md#fixed-width-synthetic-fixture-extraction--2026-09-08).

The fixed-width outcome suites also
retain a known limitation: a pre-deletion run passed six of ten cases, while
four failed or errored because readers expected archived ADRs at their former
paths. This does not change the recorded device results or imply damaged raw
artifacts. Those legacy read paths are not validated by the maintained CPU suite.
See [the wrapper-retirement record](RESULTS.md#historical-device-wrapper-retirement--2026-09-08)
for scope, source recovery, and verification.
