# Safe resolving, candidate generation, and compute allocation

[Results index](RESULTS.md) · Updated 2026-09-08 · Evidence through ADR-0280

**Current conclusion:** exact certification plus blueprint fallback can retain
useful local improvements in the tested games. Direct constrained generation
finds better candidates than several fixed CFR search rules, and a small river
scheduler survives reserved board/range tests. Neither result establishes a
general online policy. In reduced h32, convex search produces certified shadow
candidates, but fresh post-fold cases disprove universal one-round optimality.
Full convergence remains an offline teacher; actual external policies in these
h32 campaigns remained the immutable blueprint.

**Reading the evidence:** NashConv sums unilateral deviation gains; lower is
better. “Value” below means its exact reduction in the stated game and belief,
not chip winnings. A certificate checks the relevant frontier or per-seat gain
caps; those are different guarantees. A restricted convex master gives a lower
bound `L` on the minimum objective; an independently certified feasible policy
gives upper bound `U`. Endpoint closure requires verified feasibility and a
small `U − L`. The interior half-retreat toward the blueprint is a different
policy and requires its own certificate. h32 denotes the reduced six-player
river workload, not full hold'em.

## Why local improvement did not authorize search

| Question | Evidence | Conclusion and limit |
|---|---|---|
| Can low leaf error authorize replacement? | EXP-0008 searched 788/1,440 Kuhn2 holdouts; 434 were harmful or tied. Even near-exact leaves retained failures. | Risk-only selection lost to no-op. Resolver structure matters independently of leaf accuracy. |
| Do probes or continual Bayesian updates repair composition? | EXP-0009 local gain was positive for 38 harmful Kuhn2 and 40 harmful Kuhn3 candidates. EXP-0010 continual replacement harmed all six terminal-depth Kuhn2 controls. | Exact fixed-policy continuation values and correct posteriors do not preserve opponents' counterfactual best responses. High ranking AUC does not validate a zero threshold. |
| Does the safe gadget suffice? | EXP-0011 raw finite-residual deployment averaged negative improvement; strict certification had worst improvement zero and deployed only 18/128 roots. Neither arm violated its residual bound. | A correct bound may permit harm. Strict frontier gating is the tiny-game no-harm control; the raw finite solve is not. |
| Which safe objective helps? | EXP-0012 sum-margin improved all eight cases, delivering 42.94× max-min's aggregate improvement and 96.99% of the hidden greedy control's improvement. | An unchangeable frontier component can pin max-min. Sum-margin is a useful target-free teacher here; exponential normal-form enumeration is not runtime machinery. |

These findings and methods are in the [historical EXP-0008–0012 records](../docs/archive/experiment-results-through-2026-09-08.md#exp-0008-frozen-counterfactual-risk-selector-v1).
The two-player gadget result is not a theorem for arbitrary multiplayer
replacement or chained h32 updates.

## What transfers in generation and scheduling

| Experiment | Result that survives later review | What failed or remains narrow |
|---|---|---|
| EXP-0013 warm-start incumbent | Certified retention safely falls back to the blueprint. | Frozen mass-10, three-iteration DCFR captured only 2.51% of holdout sum-margin headroom; rate fell 130.72×. |
| EXP-0014 direct generation | Generated rows/columns reproduce the exact teacher without resolver-plan enumeration; holdout capture was 63.02%. | Five updates achieved only 82.70% of paired CFR's quality/ms and failed the gate. |
| EXP-0015 phase-aware generation | Holdout capture reached 81.26%; executable fixed-loop rate beat CFR 5.06×. | Absolute rate retained less than half of development, so the frozen rule still failed. Candidate-ready timing had omitted pricing already paid by executable runs. |
| EXP-0016 opportunity ceiling | Within-blueprint perfect allocation captured 83.21% at 5 ms versus 67.64% for the oracle fixed checkpoint. | Future knowledge was free. Early candidate rewards were zero even though 37/40 boundaries improved later; scalar features were weak. |
| EXP-0017–0018 river transfer | Exact sequential raises broke the shallow regret/NashConv identity; current-tree regret retained moderate efficiency correlation. | Reusing one-bet difficulty rankings failed: correlations with sequential efficiency ranged from −0.191 to 0.009. Probe-charged oracle uplift was only 4.15–6.00%. |
| EXP-0019–0020 frozen allocator | Active raw regret after two DCFR iterations sends the lowest/highest 12.5% toward checkpoints two/six and the middle toward four. Reserved validation/test charged-rate uplifts were 2.630%/2.499%; test final exploitability fell 12.522%. | Shadow regret added cost without better allocation. The accepted result concerns pooled exact sequential-river jobs, not live asynchronous scheduling or wider trees. |

The [generation records](../docs/archive/experiment-results-through-2026-09-08.md#exp-0013-screening-cfr-to-safe-objective-regret)
preserve failed frozen rules. [ADR-0019](../docs/archive/ADR-0019-phase-v2-wins-paired-but-fails-transfer-gate.md)
separates executable cost from phase-stop diagnostics and lower holdout headroom
from worse capture. [ADR-0028](../docs/archive/ADR-0028-river-scheduler-passes-sealed-test.md)
records the sealed test; its small timing edge is not a general scheduler win.

## How h32 changed the opportunity and proof boundary

| Question | Measured answer | Limitation |
|---|---|---|
| Can affine proof buy value? | Corrected [ADR-0190](../docs/archive/ADR-0190-selector-stable-affine-certificate-is-exact-and-fits-retained-street-ledgers.md) verified 35 selected scales; [ADR-0192](../docs/archive/ADR-0192-fixed-seat0-affine-rule-emits-four-fresh-certified-candidates-before-deadline.md) produced four fresh deadline-eligible shadow candidates. | The certificate covers one seat/node, one interpolation scale, and unchanged response selectors. Total fresh value was only `1.1263e-6`, 86.45% from one target. |
| Why root at the observed continuation? | [ADR-0222](../docs/archive/ADR-0222-widened-range-transfer-finds-value-but-live-selection-is-infeasible.md)'s complete-tree live slice captured just 0.000178% of its oracle pool. [ADR-0224](../docs/archive/ADR-0224-continuation-root-is-exact-and-removes-five-sixths-of-strategic-nodes.md) reduced strategic nodes from 192 to 31; [ADR-0228](../docs/archive/ADR-0228-continuation-root-delivers-exact-safe-value-on-all-twelve-targets.md) certified winners on all 12 targets, reducing local NashConv 2.14–9.91%. | Earlier complete-tree values included actions already unavailable. Continuation ledgers of 5.674–10.564 s are constructed-context observations. |
| Does more work help? | [ADR-0235](../docs/archive/ADR-0235-one-step-retained-after-heldout-depth-value-trial.md)'s second warm step cost 14.00% more and reduced pooled value 1.095%; eleven winners were identical. | Extra depth was rejected. [ADR-0237](../docs/archive/ADR-0237-full-bisector-library-does-not-fit-every-street.md)'s 62-row direction library fit only 8/12 ledgers; its quality was never measured. |
| Can convex directions cross response switches? | [ADR-0241](../docs/archive/ADR-0241-one-seat-convex-generation-matches-complete-teacher.md) matched complete small-game teachers; [ADR-0247](../docs/archive/ADR-0247-one-round-h32-convex-master-closes-the-exact-gap.md) closed one h32 endpoint after adding two response facets. [ADR-0252](../docs/archive/ADR-0252-convex-retreat-beats-the-live-fallback-on-the-frozen-target.md)'s certified half-retreat delivered 3.14× the known-target fallback value. | One-target dominance is not fresh transfer. Sequence form handles repeated actors; behavioral coordinates require the topology predicate. |
| Does breadth survive? | Latin-E accepted 6/6 retreats; Latin-F accepted 4/6. [ADR-0264](../docs/archive/ADR-0264-current-decision-convex-shadow-delivers-six-safe-candidates-in-five-seconds.md) current-decision post-call shadows accepted 6/6, with four materially positive. | Latin-F's two positive, cap-feasible policies failed interior slack and count as abstentions. Structured panels are not IID samples; fresh fallback dominance was unmeasured. |
| Is one round universally optimal? | [ADR-0270](../docs/archive/ADR-0270-current-decision-programs-close-wide-axis-census-does-not.md) closed 35/42 retained programs; six stalled and one was censored by a master verification failure. [ADR-0274](../docs/archive/ADR-0274-post-fold-confirms-safe-value-but-not-universal-one-round-closure.md) post-fold retreats were all safe/material, but only 4/6 endpoints closed. | [ADR-0276](../docs/archive/ADR-0276-post-fold-failures-close-in-two-and-three-rounds.md) closed the two failures in two and three rounds offline. Safe candidate value does not imply endpoint optimality, and endpoint optimality does not transfer to the retreat. |

The [combined ledger](../docs/archive/ADR-0272-current-decision-closure-and-safe-retreat-fit-one-street.md)
paired retained post-call measurements; it was not a same-invocation execution.
Its conservative one-cut path left just **32.384 ms** under 15 seconds, including
emission reserve. Cheap later rounds in an outcome-selected diagnostic do not
establish deadline admission.

## Remaining questions

Can exact master refinement remove cap-boundary stalls without weakening the
independent certificate? Can bounded search allocate work causally under real
deadline accounting? Do gains survive new boards, action widths, earlier
streets, and composition? These are open, not consequences of the local results.

Action widening remains especially incomplete. [ADR-0278](../docs/archive/ADR-0278-reject-pre-bet-action-width-capacity-invocation-on-campaign-duration.md)
rejected its campaign for exceeding one hour; diagnostic two-size proxies all
exceeded 15 seconds and no widened quality labels opened.
[ADR-0280](../docs/archive/ADR-0280-exact-pre-bet-row-cache-passes-cpu-h2-fail-closed-control.md)
passed CPU/h2 exact row-cache mechanics, not h32 hit rate, lookup cost, capacity,
or strategy quality. Removing an unused warm step and assuming free exact row
hits remained optimistic accounting, not measured live feasibility.

## Evidence and provenance

The linked reports preserve configuration identities, full hashes, methods,
and raw result paths under `experiments/results/`. These are supporting
research records; archived procedural instructions are historical.

| Evidence family | Recorded source identity | Detailed record / raw location |
|---|---|---|
| Early safe search | Frozen rules: `3776496`, `58f2e66`, `c7d096b`; not asserted as invocation commits | Historical EXP-0013–0015; configs under `experiments/configs/`; generated early JSON was ignored. |
| River scheduler | Development invocations `9e81d05`, `09acdfb`; evaluator freeze `68eecc8`, teacher repair `662c46a`, validation record `c38fa4b` | EXP-0017–0020 and ADR-0028 contain trace/result SHA-256 identities. |
| Affine/continuation | Preregistrations `119c0efc`, `951cda2d`, `9109058`, `47513af` | ADR-0190/0192/0228/0235; `h32-heldout-continuation-depth-value-v1.json`. |
| Convex breadth | Preregistrations `a5b1e98d`, `a7960be3`, `2c353a93`, `9f623e65`, `0fbba5c4` | ADR-0247/0252/0258/0260/0264; `h32-latin-f-convex-retreat-confirmation-v1.json`. |
| Closure and limits | Preregistrations `23e9fae8`, `57dacfcc`, `abc88c5d`, `db1b933b` | ADR-0270/0274/0276/0278; `h32-post-fold-failure-closure-diagnostic-v1.json` and checkpoint. |

No invocation SHA is supplied for ADR-0280 because that report supplies file
digests instead. The commit containing this summary identifies documentation,
not historical experimental execution. [ADR-0276](../docs/archive/ADR-0276-post-fold-failures-close-in-two-and-three-rounds.md)'s checkpoint hash field used
LF bytes while Windows persisted CRLF; its report preserves the actual digest.
ADR-0233's payoff-span correction, [ADR-0247](../docs/archive/ADR-0247-one-round-h32-convex-master-closes-the-exact-gap.md)'s distinct cap tolerance, and
[ADR-0258](../docs/archive/ADR-0258-convex-half-retreat-delivers-material-value-on-all-six-latin-e-targets.md)'s resident-row classification correction preserve their stated earlier
numerical outcomes; rejected predecessor invocations remain rejected.

The September 8 follow-on cleanup retired the original closure-census driver,
its v2 driver, the post-fold failure diagnostic, and their three dedicated
experiment tests. Their question was whether the retained and fresh post-fold
programs closed, and how many offline rounds the failures needed. The preserved
census found 35/42 closures, six stalls, and one censored master error; the two
post-fold failures needed two and three rounds. The result JSONs, checkpoints,
and configs remain, including the census JSON consumed by combined-ledger replay.
Reusable masters, exact oracles, and resident solver code remain. The retired
source and tests can be recovered from
`91f031e91c957a9b273c2ccc345421f7b286b416` (recovery commit, not invocation identity).
