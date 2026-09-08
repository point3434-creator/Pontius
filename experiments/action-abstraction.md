# Legal bet sizing and tie-aware response models

[Results index](RESULTS.md) · Consolidated 2026-09-08 · Reduced-game research evidence

**Conclusion:** a context-dependent menu of three legal raises passed a fresh
transfer test in the reduced heads-up river game, recovering at least **97.23%**
of the aggregate gain available beyond minimum/all-in sizing. Separately,
factorized response sets handled exact ties that invalidated a single-response
certificate and overwhelmed explicit enumeration. These are positive results
for bounded action quality and response representation. They do not establish
a production three-size ladder, full-range capacity, or complete decision time.

This page consolidates ADR-0291–0362, chiefly August 23–25, 2026. Archived
decisions supply historical evidence, not current workflow instructions. The
summary was prepared from reports and retained paths without new experiments.

**Reading the terms:** *h4* means four private hands per player in these reduced
games. *Raise width* counts raises, with check separate; amounts are nominal
raise-to totals. *Recovery* divides summed achieved chip gain by summed available
gain over the minimum/all-in baseline. *Normalized loss* divides by the payoff
span, not the stack. A *response tape* specifies choices even at unreachable
information sets; a *face* contains all exactly tied optimal responses. An
*affine envelope* takes the maximum of response-value lines along a policy
direction.

## What passed, failed, or only established a measurement tool?

| Question | Recorded finding | Scope and interpretation |
|---|---|---|
| Could the evaluator find meaningful sizing opportunity? | Three batches each found **12 qualifying contexts**, after opening 23, 24, and 32 contexts. [ADR-0299](../docs/archive/ADR-0299-width-four-passes-replicated-sizing-power.md) | Candidate-blind h4 panels; all passed diversity and numerical controls. This established evaluation power, not a successful sizing mechanism or representative poker frequency. |
| Did collision-repair v3 recover enough value? | **48 representative** cases passed loss limits; **24 qualified** cases recovered **80.0548%**, below the **90%** floor, despite maximum/mean normalized losses of **0.00106468/0.000259461**. [ADR-0304](../docs/archive/ADR-0304-reject-collision-repair-v3-on-qualified-recovery.md) | A substantive quality rejection. Small loss relative to payoff span concealed a material fraction of the available sizing gain. |
| Did capacity-filling v4 fail strategically? | Qualification B stopped at **context 21** on native LP primal verification, before any v4 candidate value. [ADR-0310](../docs/archive/ADR-0310-reject-capacity-filling-v4-on-qualified-b-numerical-failure.md) | Numerical infrastructure failure. Qualification A's 24 targets could not establish the missing result. No strategic ranking of v4 follows. |
| Did the replacement numerical path work? | Canonical HiGHS validation passed **177/177** calls: **48 exact micro LPs** and **129 certified sizing LPs**; maximum sizing certificate interval **8.49312e-11 chips**. [ADR-0320](../docs/archive/ADR-0320-accept-the-canonical-certified-sizing-validation.md) | Finite correctness on canonical compact programs, with independent reconstruction. It did not select a menu or validate arbitrary production masters. |
| Did the adaptive mechanism learn a useful width? | On **16 development contexts**, width three first passed all five limits: recovery lower **97.7775%**, maximum/mean normalized full-regret upper **0.000228613/0.0000237713**. [ADR-0338](../docs/archive/ADR-0338-retain-and-rebind-the-non-replay-direct-mechanism.md) | **376 accepted calls** completed the development schedule. Widths three through six passed; the frozen rule chose the smallest. This was selection, not yet transfer. |
| Did that frozen choice transfer? | On **16 untouched qualified contexts**, all five unchanged limits passed: recovery lower **97.2310%**, maximum/mean normalized full-regret upper **0.000322245/0.0000491925**. [ADR-0343](../docs/archive/ADR-0343-retain-and-seal-the-width-three-transfer-confirmation.md) | **126 fresh calls**, separate from 32 prior full/width-two comparator calls. All 16 direct selections matched the exhaustive teacher. This confirms the reduced-game mechanism on that fresh panel. |
| Could ties be represented without enumerating every response? | The largest exact face had **104,976 total-function members**, but reachable-support cardinality **one**; no response-tape products were materialized. [ADR-0356](../docs/archive/ADR-0356-retain-and-rebind-the-legal-h4-directional-face-diagnostic.md) | One inspected legal h4 fixture, four directions, eight sections, **164** composed/scheduled face observations. The aggregate reachable maximum was two, a different statistic. |
| Did factorized integration survive fresh contexts? | All **32 sections** completed: four contexts × four directions × two players; **28 singleton** and **four tie-aware** source modes. [ADR-0362](../docs/archive/ADR-0362-retain-the-rejected-terminal-and-rebind-its-scientific-payload.md) | Independent artifact assessment accepted every intended scientific conjunct. The original terminal remains rejected because of a separate Boolean-expression defect; it was not rewritten as a passing run. |

## What does the width-three success actually mean?

The frozen mechanism retains minimum and maximum raise anchors and selects one
context-local interior raise. Transfer menus included `(2,3,12)`, `(2,6,10)`,
and `(2,4,8)`. Their variation is part of the success: the result does not
justify one fixed global ladder. The remaining transfer gates bounded maximum
and mean excess regret against the exhaustive teacher at approximately
**1.55e-14** and **1.27e-14**, well inside their **0.001/0.0002** limits.

These were deliberately opportunity-qualified, h4, two-live-seat river-opening
contexts with fold/call-only responder behavior. Freshness excludes reuse of
development contexts; it does not establish representativeness, arbitrary
opponent sizing, responder raises, or earlier-street transfer. The later legal
responder-raise studies address different questions and do not silently extend
the width-three quality claim.

## Why did earlier plausible approaches fail?

V1's legal-action/projection controls passed, but its sizing-quality gate
failed. Preserving the expectation of an off-tree raise through exact rational
interpolation did not prove strategic equivalence.
[ADR-0292](../docs/archive/ADR-0292-reject-action-abstraction-v1-before-complete-hand-integration.md)
Dyadic v2 then recovered **94.5147%** on its five informative confirmation
contexts, but required at least eight of 24. That was an insufficient-power
rejection, not a confirmed success.
[ADR-0294](../docs/archive/ADR-0294-reject-dyadic-v2-on-confirmation-power.md)

Numerical recovery also has two distinct records. The corrected native audit
reassessed **2,655** retained observations: HiGHS dual simplex and IPM each
verified **885/885** arms, while native simplex recorded **36 exceptions**.
ADR-0316 accepted the corrected finite-corpus assessment while preserving
ADR-0314's original gate rejection. The two HiGHS modes were not independent
implementations, and the correction did not rehabilitate native simplex.
[ADR-0316](../docs/archive/ADR-0316-accept-corrected-audit-and-bound-replacement-eligibility.md)

## Why did legal responder raises require a different certificate?

The legal h4 row-growth fixture needed **zero new response rows** after one
restricted-master iteration. That narrowed the immediate bottleneck to selector
semantics on this fixture; it did not prove row growth harmless generally.
[ADR-0349](../docs/archive/ADR-0349-retain-and-seal-the-legal-h4-row-growth-result.md)

The next audit recorded all 25 gates as passing, yet four of eight sections
had reachable source ties. A selected response remaining optimal is weaker
than its being uniquely certified. ADR-0351 rejected the certificate authority
and required a zero single-tape window when source margins fail to clear their
semantic reserve, while retaining the valid exact response map.
[ADR-0351](../docs/archive/ADR-0351-retain-the-legal-h4-fan-map-and-reject-certificate-authority.md)

Enumerating every tied tape then exceeded a **256-member** bound before any
section was serialized. Factorized choices subsequently represented the large
face without the Cartesian product. The earlier rejection did not identify
the offending sample or its exact size; the later 104,976-member observation
must not be retroactively assigned to it.
[ADR-0353](../docs/archive/ADR-0353-retain-the-legal-h4-tie-aware-bound-rejection.md)

Same-fixture integration passed with **12 fan rows but ten interval-owning
envelope pieces**. Three summary-field families remained authenticated to the
writer rather than independently reconstructible; fresh confirmation retained
the missing factors and rows. Its scientific payload passed reassessment,
while a chained comparison of a mapping with `True` explained the original
failed emission gate.
[ADR-0359](../docs/archive/ADR-0359-retain-and-rebind-the-legal-h4-factorized-affine-integration.md),
[ADR-0362](../docs/archive/ADR-0362-retain-the-rejected-terminal-and-rebind-its-scientific-payload.md)

## What remains open, and how can the evidence be recovered?

Numerical validity, action quality, representation, and decision timing remain
separate. The canonical sizing solver's **1.968 ms median call** excludes most
of the decision path. Fresh affine confirmation's **109.808 s campaign wall**
covers a laboratory workload, not poker decisions. Neither establishes the
15-second action boundary. [GPU representation](gpu-representation.md) follows
the full-width capacity question; [Safe search](safe-search.md) covers selection
and certificates, and [Bot validation](bot-validation.md) covers integration.

The following invocation commits were verified to exist locally; artifact
paths were checked for presence, without rerunning or independently validating
their scientific contents. Linked ADRs retain hashes and interpretation limits.

The corrected native-simplex assessment file
`experiments/results/native-simplex-audit-corrected-gate-v1.json` was already
absent during the September 8 follow-on cleanup. Its conclusions above come
from the archived audit report, not a freshly checked local assessment. The
retired saved-result test can be recovered from repository commit
`91f031e91c957a9b273c2ccc345421f7b286b416`; this is a code recovery reference,
not an asserted invocation commit. No result file was deleted by this cleanup.

| Evidence | Invocation source commit | Retained artifact |
|---|---|---|
| Canonical numerical validation | `fada0172713603c905bc236579cb6761ecfb687e` | [Campaign](results/certified-sizing-canonical-validation-v1.json) |
| Width-three development | `b4339f33dec768052208b102ad8a9f510666f40d` | [Development journal](results/fresh-action-width-nonreplay-closed-finite-block-greedy-v1.jsonl) |
| Width-three fresh transfer | `45dc67c5e36fc222620449117eaa33948fcb47ef` | [Transfer journal](results/fresh-action-width-transfer-confirmation-v1.jsonl) |
| Factorized face diagnostic | `5331d0a6e142a97be10678d59e76aa7f1cc9a63e` | [Face artifact](results/legal-responder-raise-h4-directional-face-v1.json) |
| Same-fixture integration | `23c7f023e686b8b84bc1145381c5fe7ba99dc8d4` | [Integration artifact](results/legal-responder-raise-h4-factorized-affine-v1.json) |
| Fresh affine confirmation, original rejected terminal | `8bcf00662f2903686d91311afe1d36a2669b97d6` | [Confirmation artifact](results/legal-h4-factorized-affine-confirmation-v1.json) |
