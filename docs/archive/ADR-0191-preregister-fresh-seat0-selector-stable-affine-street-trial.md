# ADR-0191: Preregister a fresh seat-0 selector-stable affine street trial

- Status: accepted preregistration
- Date: 2026-08-21
- Depends on: ADR-0166, ADR-0179, ADR-0186, ADR-0190
- Config: `experiments/configs/h32-fresh-selector-stable-affine-street-v1.json`

## Question

On fresh beliefs, can a fixed seat-0 regret-vertex rule finish one exact
selector-stable affine proof inside the prepared 15-second street and emit a
certified candidate when that proof finds value?

This is the first prospective trial allowed to let the affine certificate
choose a simulated emitted candidate. It tests one transparent acquisition
rule, not a learned selector or a strategy population.

## Fresh target panel

Use the four remaining source-panel contexts whose seat-0 blocker shift has
never appeared in the repository's sealed history:

| Target | Selected seat-0 hand | Frozen target SHA-256 |
|---|---|---|
| panel 1 balanced | `Kh Ad` | `a1a69f7cb3cf89265895edea3eff6af218c8e455f01535a32092a1de758f18c7` |
| panel 1 blocker-heavy | `3c Kh` | `a9976c59745a4765640dcf8baa2f4631b18ffdef81a4d4f4a95aa35cc93ae754` |
| panel 2 blocker-heavy | `3d 5c` | `e67c92d3137bd69cb2ecdbc46ddc89a9975c71b93324a6d57d4114d000a76790` |
| panel 3 balanced | `6s Qh` | `da203c79eb38f89fa4cdb38081b01b3b1a696c034b5590acc52358dfa022d086` |

The label-free construction doubles the likelihood of the seat-0 hand chosen
by maximum opponent-axis card overlap, then strength, then smallest canonical
hand. Target and descriptor digests must be absent from commit
`76bcc4b80d976376220deaeb2601e721d54eeb92`, which predates their construction.
Their identities are frozen before any target warm step or policy-quality
label. Panel 2 balanced and panel 3 blocker-heavy are excluded because
ADR-0175 already labeled their seat-0 shifts.

## Prepared state and immutable anchor

Before the decision clock, construct the target belief, resident response
context, immutable source average-64 blueprint, its exact target-belief quality,
and a numerically identical regret-mass warm start. This is the established
prepared-street boundary: belief/topology preparation and anchor certification
are cached inputs, not decision work.

The clock starts immediately before one resident DCFR step. The blueprint is
preloaded as the fallback before that step starts. Cross-run warm identity uses
ADR-0179's `1e-12` maximum probability and `1e-13` mean information-set TV
ceilings. Policy digests are diagnostics only.

## Fixed causal rule

After the warm step, recover its instantaneous regret delta, construct the same
deterministic public-node blocks, and select only acting seat 0's block. Move
that block to its instantaneous-regret vertex. There is no feature ranking,
probe, adaptive direction choice, or inspection of another block's value.

Run exactly one six-seat selector-stable affine endpoint sweep. Use ADR-0190's
unchanged source-selector tape, `2e-11` selector and envelope allowances,
half-radius safety factor, and 34-point downward geometric-halving grid. If the
envelope selects and the interpolated candidate is ready before the emission
cutoff, the simulated emitted policy is that candidate. Otherwise emit the
preloaded immutable blueprint.

## Hard street ledger

The street budget is `15,000 ms`, including a fixed `1,000 ms` synchronization
and emission reserve. The candidate-ready cutoff is therefore `14,000 ms`.

Two frozen start guards avoid beginning work that retained evidence says is
unlikely to finish:

1. after the warm step, require at least `1,000 ms` for all-block construction,
   endpoint construction, affine proof, and candidate formation, in addition
   to the emission reserve;
2. after construction, require at least `500 ms` for the affine proof and
   candidate formation, again in addition to the reserve.

The first guard is above ADR-0190's largest observed seat-0 post-step workload
of about `835 ms`; the second is above its largest observed seat-0 affine sweep
of about `335 ms`. They are fixed before fresh timing. If either guard denies a
start, close the live ledger and emit the blueprint. If an attempted proof
unexpectedly overruns, its candidate is ineligible and the hard-deadline gate
fails; do not tune either guard from this panel.

## Off-clock exact teachers

Close the live ledger and freeze its emitted policy before any old-verifier
teacher runs. Then, for every target:

- finish the frozen seat-0 construction and affine sweep off clock if a guard
  skipped them;
- directly evaluate one fixed witness strictly inside the selector interval;
- if the affine envelope selects, independently run the accepted old exact
  verifier at that scale; and
- compare utility, best-response value, and deviation gain at `1e-9` maximum
  absolute error and require zero response-action flips.

These teachers may invalidate the trial but may never change the recorded live
selection or emission. Their value, timing, and any skipped-live opportunity
are descriptive labels.

## Outcome-neutral gates

Require four targets, four warm steps, four fixed seat-0 blocks, 24 affine seat
rows, four fixed witnesses, clean committed execution, accepted parents, exact
source/target/descriptor/checkpoint/blueprint identities, absence of every
fresh target and descriptor digest at the frozen base commit, numerical warm
identity, one-node acting-seat-0 affine scope, source intercept error at most
`2e-11`, teacher errors at most `1e-9`, fixed witnesses inside the selector
interval with zero flips, every selected-scale teacher complete with zero
flips, causal teacher ordering, fixed-rule and fail-closed emission identity,
all live ledgers at most `15,000 ms`, candidate-ready work at most `14,000 ms`,
finite accounting, 60-second step/construction/sweep/teacher ceilings, the
12 GB pool ceiling, a 1 GB physical-free floor, and a broad 1,800-second audit
ceiling.

Do not gate on whether live construction or proof starts, whether the affine
envelope selects, non-blueprint emission count, selected scale, certified value,
lost off-clock opportunity, latency margin, or any target's strategy outcome.

## Frozen artifacts

- config SHA-256:
  `90704c11d8cc3a778fbfdb9d25586b7580fbbe7a7d4fa4f790e6c8ce0d59cb0c`;
- additive audit SHA-256:
  `2e435e835d7c2bc536deb06433a3f2e67bc5dd5e3b406d1ad81ea217a4391a5e`;
- mutation-control SHA-256:
  `cde1d4ade13d8b6c65d159a843f7b66caca0cf3318e3ab6e9ad27da1ebcdb48a`;
- result target:
  `experiments/results/h32-fresh-selector-stable-affine-street-v1.json`.

The 14 focused affine, deadline, numerical-identity, and historical-hash
controls pass. The complete repository suite passes 673 tests. No fresh target
policy step, affine proof, or policy-quality teacher has run.

## Decision rule

Commit the additive runner, config, controls, and this ADR before the first
fresh target policy step. Execute the four targets exactly once from that clean
commit.

If exactness or causal ordering fails, reject the live use of the primitive. If
the hard deadline fails, retain blueprint fallback and optimize cancellation or
the warm step before spending another fresh panel. If every gate passes, accept
the trial only as four-context prospective evidence; candidate count and value
remain descriptive, and no deployment, composition, or population claim
follows.
