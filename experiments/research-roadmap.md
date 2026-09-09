# Research roadmap: connect ideas to evidence

Reviewed 2026-09-08. [Completed evidence](RESULTS.md) · [Brainstorming and revisions](brainstorming.md)

**My highest-value new scientific question is whether exact folded-card work
can be prepared once and reused cheaply while active strategies change.**
First establish that the proposed terminal operator computes the right poker
quantities. Then measure preparation, reuse, and the strategic cost of simpler
alternatives. The latest brainstorming makes this more informative than another
general GPU speed forecast or committing now to a large neural system.

At the same time, keep the bot-facing objective concrete: build a small trained
policy that can travel through the existing provider and be evaluated on fresh
deals/opponents. That practical track should not wait for a full six-player
exact solver. The ranking below reflects expected decision value and readiness,
not measured return on research time or a claim that later ideas are inferior.

## What has connected into something useful?

“Connection” here means agreement, tension, or a useful new hypothesis across
the two bodies of work. We have not established statistical correlation or that
the brainstorming caused an earlier result.

| Brainstorming idea | Completed Pontius evidence | What the connection actually supports |
|---|---|---|
| Compile stable structure and reuse it | [Exact evaluation](exact-evaluation.md): large hot gains, but three-player one-shot quality/time lost 3.30%; a later four-use comparison barely won by 0.29%. [Blueprint performance](blueprint-performance.md): eight-hand fresh preparation 670.038 ms versus retained 81.151 ms, four observations per arm. | **Strong measured theme, new application.** Test fixed-fold compilation; charge cold setup and invalidation. Those measurements do not establish a folded-card speedup. |
| Replace joint enumeration with terminal contractions | [GPU representation](gpu-representation.md): explicit full-width half-assignment layout rejected at a 202.627 GB optimistic bound; a different literal-45 quotient primitive passed, while complete full-width deadline fit remains unestablished. | **Plausible route around a particular cost.** External terminal constructions may complement the quotient; they do not supply all its signed-feature, transpose, and resolver operations. |
| Regularize search against imperfect leaves | [Solver foundations](solver-foundations.md): selected anchored averages helped, but depth-one replacement harmed a strong blueprint even with exact leaves. [Safe search](safe-search.md): certification plus fallback has useful reduced-game evidence. | **Motivation, not validation.** Compare one declared regularized method against average-policy controls and no-op; do not assume the final iterate is better. |
| Spend model accuracy on important decisions and deviations | [Solver foundations](solver-foundations.md): matched root-error trials improved 0/20 times when localized to low-reach leaves, versus 19/20 or 20/20 in high-reach groups. | **Direct reason to reject a reach-only error objective.** Test downstream policy quality and rare profitable deviations; this does not validate a neural uncertainty score. |
| Adapt a compact action menu | [Action abstraction](action-abstraction.md): context-dependent width three recovered 97.2310% aggregate available gain on 16 fresh qualified h4 heads-up river contexts, with fold/call responders. Earlier variants failed. | **Strongest existing policy-design connection.** Extend narrowly; test equivalent-action invariance before adding a regularizer. No global bet ladder or full-game result follows. |
| Distill a useful policy into a deployable blueprint | [Bot validation](bot-validation.md): weighted export preserves tested policies. The next 768-hand / 96-session comparison rejected a coarse transferable fallback and simple prior pooling despite correct execution. One average improvement concealed a 0.830-chip regression. [Blueprint performance](blueprint-performance.md): history-rich keys also constrain capacity. | **Preserving a policy is solved within the tested domain; improving it still needs better state features and objectives.** Test range composition and conditional acceptance against the retained counterexample, then use fresh final cases. No full-game strength follows. |
| Use coherent opponent regimes and robust continuations | Existing multiplayer evaluation separates unilateral improvement, aggregate NashConv, and stronger opponent assumptions. | **Open modeling question.** No validated latent-opponent model or full-game exploitation floor is established. Start with complete, explicit continuation profiles. |

## Ranked research sequence

| Order | Research question and smallest useful experiment | Decision it would enable |
|---|---|---|
| 1 | **Does the new exact terminal construction match poker semantics?** Compare reduced real-board cases with an independent positive enumeration reference: wins, ties, legal mass, all dealt seats, folds, and explicit pot eligibility. | Whether the external algebra can become a Pontius capability at all; which outputs and precision it supports. |
| 2 | **Can fixed-fold compilation make exact bunching affordable through reuse?** Start with heads-up river and four folded seats; compare cold construction, repeated active-range updates, memory, and invalidation with the direct reference. | Whether exact evaluation merits an online arm, and how many valid reuses it needs. This is the most interesting new performance avenue. |
| 3 | **Does bunching accuracy change worthwhile decisions?** Solve a small reachable-root panel with no bunching, a precisely defined approximation, and exact evaluation; reevaluate every resulting policy under the same exact model. | Whether the bot needs that exactness, a cheaper approximation, or better folded-range inference first. |
| 4 | **Does regularization improve quality under a fixed time budget?** Compare existing DCFR/CFR+ controls with one fixed-reference candidate on exact reduced games; separate exact leaves, structured error, and matched noise. | Whether to adopt a solver change, and whether its temperature rule transfers beyond tuning cases. |
| 5 | **How far does the successful small action menu transfer?** First test duplicate-action/reference-mass invariance; then add one missing responder or street capability on fresh contexts. | Whether better action coverage earns its re-solving cost without an artificial prior change. |
| 6 | **Which continuation approximation helps decisions?** On a modest exactly evaluable teacher panel, compare ordinary value-error training with decision/deviation-focused training and analytic/residual controls. | Whether learned leaves or targeted refresh improve searched policies enough to justify larger training. |
| 7 | **Which opponent uncertainty model is useful?** Compare a small set of complete continuation profiles, then held-out styles and range perturbations; distinguish expected payoff from robust objectives. | Whether latent styles add useful predictive or strategic value beyond simple baselines. |
| 8 | **Which accelerated implementation is worth building?** Port only the operator and batching pattern selected by the preceding measurements; include actual reach updates and refresh cadence. | A measured CPU/GPU choice for a real consumer, not another standalone capacity claim. |

### 1–3: exactness, reuse, and strategic value

For the first differential, a fixed river board and small allowed private-card
pool keep enumeration manageable. Begin with a three-dealt, all-active control, then retain
all six dealt seats with different active/folded masks. Compare legal mass,
payoff numerator, and conditional utility only where mass is positive. Test
zero mass explicitly. Use Pontius ranking/payout semantics and independent
enumeration; agreement between two algebraically related implementations alone
is insufficient. Cover concentrated blockers, sparse support, ties, and side-pot
eligibility before claiming general terminal support. Declare the factorized
reach model; arbitrary correlated beliefs are not obtained by multiplying
conditioned marginals.

Separate precision error using references for the intended weights, the exact
stored FP32 weights, and production arithmetic on those stored weights. Compare
pot-scaled value errors as well as mass errors. Stop on unexplained semantic
mismatches, negative mass, or an uncontrolled fallback; fix or narrow the
contract before timing a larger implementation.

For reuse, hold the board and folded-seat reach factors fixed while active
strategies vary. Folded-only compatibility can then be reused; new boards,
changed folded factors, or folds generated inside the current search can
invalidate that premise. As a storage calculation, one FP64 coefficient for
each four-card union on a 47-card river domain is
`choose(47, 4) * 8 = 1,426,920 bytes`, approximately **1.36 MiB**. This excludes
construction workspace, indexing, and other state. It neither measures build
time nor promises cheap queries. The three-active six-card-union table would
already be approximately **81.92 MiB** per root. These proposals come from the
[Sept 8 external review](<D:/Pontius Research/six_max_poker_fresh_review-1.pdf>),
pp. 6–9, and remain untested here.

Measure cold and complete cost versus reuse count, including fallback and range
refresh. Proceed only if the break-even lifetime occurs in the intended
workload. If it does not, retain the exact method as an offline teacher or oracle
and compare approximations; a slow prototype does not prove every implementation
must be offline.

The strategic audit should use reachable histories from declared policies,
with a separate adversarial population. A current baseline-generated population
is a proxy, not a strong-blueprint population. Hero hands sharing a public root
are correlated observations; use roots as the sampling clusters. Report
action-gap-weighted mistakes, counterfactual errors, per-player deviations where
feasible, and complete time. Restricted best responses give lower bounds on
deviation opportunities, not safety certificates. Perturb plausible folded-range
models too: model error might outweigh the difference between counting methods.
Set a meaningful loss budget before the run; wide uncertainty means inconclusive,
not equivalent.

### 4–6: improve the policy with controlled comparisons

Use existing exact Kuhn and reduced-river controls before building a new training
system. Hold game, action menu, initial policy, output convention, and evaluation
fixed. For solver comparisons report both fixed-work diagnostics and complete
fixed-time quality, including setup; separate initialization, reference policy,
temperature, and reference refresh. Evaluate the searched policy in the original
game, preserving no-op and exact-leaf controls. Freeze a selection rule before
holdout testing. An apparent local improvement that harms the blueprint is a
failure for that objective.

For the action experiment, splitting an equivalent label with proportionally
transferred reference mass should preserve aggregate behavior; adding genuinely
new legal sizes need not. Use the existing width-three mechanism as the control,
then evaluate menus in a shared finer game. Extend responder raises or an earlier
street separately so a failure remains interpretable.

For leaf research, start with an affordable teacher panel and a simple legal
continuation baseline. Compare analytic-only values, direct approximations, and
residual approaches before a large network. A learned deterministic residual
can be biased; a correctly baseline-adjusted sampling estimator has different
requirements. Preserve teacher/range/menu identity and judge resulting policies,
not just value RMSE. Structured measured errors, IID errors, and common-mode
shifts need distinct controls. “Noise helps” requires evaluation with an unchanged
exact reference and comparison to explicit exploration.

## Practical bot track alongside the scientific sequence

The active-action integration prerequisite now has a passing bounded result:
[48 diagnostic sessions](blueprint-performance.md#what-changed-and-what-remains-open)
covered bets, re-raises, folds, all-in calls and deliberate fallback. These are
hand-built actions. The subsequent trained river pilot passed its runtime
bridge but failed its deterministic-export quality gate. The weighted follow-up
preserved quality through serialization and per-hand sampled-table execution.
Native weighted artifacts now also pass 100 direct hands and 36 subprocess
sessions, with sampling charged inside the decision interval.
The six-board panel then passed 576 direct hands and 48 sessions: four trained
roots retained quality, two deliberately uncovered roots used passive fallback,
and three covered roots became substantially more exploitable under reversed
prior weights. Maximum session response remained below one millisecond for the
48,097-byte artifact. Those are finite-panel findings, not a full-game ranking.
Measure supported-state coverage explicitly alongside decision quality; exact
history keys can miss on new trajectories.

1. **Repair the measured policy failures before broader deployment.** The
   follow-up comparison rejected both first candidates. Range-strength-bin
   fallback improved mean worst tested NashConv 37.62% but harmed an already-safe
   root by 0.830 chips; pooled-prior training worsened mean worst performance
   17.39%. Use the low-pair counterexample to test betting-range composition as
   an additional feature, and compare an explicit worst-case objective with
   simple prior averaging. A per-situation acceptance check with fallback is
   a useful control for unconditional replacement. Keep the baseline intact,
   evaluate all candidates under identical priors including their misses, and
   freeze new final cases before selecting a revision. The three failed final
   roots are now development evidence. A better finite table alone still does
   not demonstrate unseen-board generalization or full-game strength.
2. **Establish independent paired playing evaluation.** Separate development
   from held-out deals, use matched randomness where appropriate, and report
   uncertainty that respects shared roots and deals. Compare complete policies
   including their fallbacks. The existing fixed-policy comparison used only
   two deals; it cannot rank general playing strength.
3. **Measure actual live preparation reuse and clock margins.** The direct
   eight-hand reuse measurement excludes transport and decode. A runtime change
   still needs an explicit lifetime/mutation contract and first-decision ledger
   measurements under the actual 14-second work / 15-second action limits.

The **most direct route toward a useful bot** is this deployment/evaluation track
plus the already promising adaptive menu. The **largest new scientific upside**
is terminal exactness plus fixed-fold reuse. The **best controlled solver study**
is regularization under structured leaf error. Keeping those distinctions avoids
mistaking a novel kernel for improved play, or delaying playable experiments
until every ambitious research idea is solved.

## Deferred ideas and updates

Defer large equivariant networks, learned solvers, broad backward-label
generation, continuous bet-size gradients, and a full exploitation layer until
smaller tests identify the target and failure mode. Keep general six-dealt
derivative/GPU work available, but require a real consumer before another long
calibration. Nearby-belief strategy reuse, universal KL validity radii, and
unqualified “single-card marginals suffice” should not be adopted as facts.

Update the relevant [completed family](RESULTS.md) when a run finishes, then
revise the matching row here if its priority or interpretation changes. Mark
ideas tested, narrowed, supported within scope, or rejected, with the result
link. Keep the brainstorming source and any failed predecessor visible. These
are proposed experiments; no new run, performance result, or deployment is
claimed by this roadmap.
