# ADR-0100: h32 warm search finds sparse safe value; fixed average four fails

**Status:** Accepted as strategy evidence for an exact anytime vector gate;
fixed iteration-four average deployment rejected; online implementation not yet
authorized

**Date:** 2026-08-20

## Result

The frozen ADR-0099 audit completed from clean commit `7a7d572` with every
mechanism gate passing. The canonical local artifact is
`experiments/results/h32-warm-search-acceptance-v1.json`:

- SHA-256:
  `150362ea770c80190c8124148fa66e0a376d98d1bd01b790f3d11e5ad9b5d8a9`;
- size: 46,018,487 bytes;
- config SHA-256:
  `b5cbc538d51f09aad5aa6dca6c860865afd849196b65560ea3338d83293d7f8d`;
  and
- implementation SHA-256:
  `b0d48b0ca34e5153ea8317133bca96a32fd9ea57fcbe539e958fedddcae5870f`.

Measured wall time was 1,011.350 seconds, or 16.86 minutes. All twelve search
states independently reproduce their state, current-policy, and
average-policy digests. There are four target beliefs, twenty evaluated
candidates, sixteen warm-search steps, and no failed gate.

The strategic result is mixed in exactly the way a measurement-first program
must preserve:

- the fixed primary average-four candidate is harmful when deployed blindly;
- aggregate exact acceptance salvages two of four primary candidates;
- no primary average-four candidate passes all six unilateral constraints;
  but
- the sequential unilateral incumbent safely accepts average two on both
  sparse local-blocker shifts and rejects every later harmful or
  redistributive candidate.

Therefore the primary ADR-0099 product hypothesis fails, while the earlier
anytime checkpoint reveals real safe strategy value.

## Headroom-normalized quality

All NashConv values and reductions below are divided by the 30-chip payoff
span. “Headroom captured” is candidate reduction divided by the target-belief
blueprint NashConv. This keeps the sparse and dense shifts from being pooled
under incomparable starting residuals.

| Family | Target shift | Mean marginal TV | Blueprint NashConv | Candidate | Reduction | Headroom captured | Aggregate | Unilateral |
|---|---|---:|---:|---|---:|---:|---|---|
| Balanced | local blocker | 0.008188 | 0.002230 | average 2 | +0.000126 | **5.646%** | accept | **accept** |
| Balanced | local blocker | 0.008188 | 0.002230 | average 4 | +0.000129 | 5.765% | accept | reject |
| Balanced | all-seat strength | 0.072099 | 0.011344 | average 2 | -0.000566 | -4.987% | reject | reject |
| Balanced | all-seat strength | 0.072099 | 0.011344 | average 4 | -0.002143 | -18.893% | reject | reject |
| Blocker-heavy | local blocker | 0.004234 | 0.001888 | average 2 | +0.000095 | **5.054%** | accept | **accept** |
| Blocker-heavy | local blocker | 0.004234 | 0.001888 | average 4 | +0.000133 | 7.060% | accept | reject |
| Blocker-heavy | all-seat strength | 0.070051 | 0.012979 | average 2 | -0.000681 | -5.247% | reject | reject |
| Blocker-heavy | all-seat strength | 0.070051 | 0.012979 | average 4 | -0.003101 | -23.890% | reject | reject |

The shift response is replicated across both generated range families. Sparse
local blocker changes admit a small safe correction after two iterations.
The much larger all-seat strength shifts do not: warm average quality moves in
the wrong direction and the harm grows through iteration four.

This is the inverse of the pre-result low-confidence prediction that the
all-seat shift would produce the reliable gain and the blocker shift would be
null or harmful. The mechanism, not the prediction, survives.

## The anytime gate—not average four—is the result

Average one equals the supplied blueprint at numerical precision in every
target. Normalized differences range from approximately `7e-18` to `3e-17`,
and all four comparisons abstain inside the `3e-9` raw guard. This naturally
exercises the h32 near-identity boundary and confirms the expected own-reach
averaging semantics.

Average two is safe on both local shifts. Relative to each blueprint, all six
deviation gains decrease:

- balanced deltas range from `-0.001180` to `-0.000174`; and
- blocker-heavy deltas range from `-0.000961` to `-0.000114`.

The two accepted normalized reductions sum to `0.000221360`, capturing 5.374%
of their combined target-belief blueprint residual.

Continuing to average four gains only `0.000002656` more normalized aggregate
quality balanced and `0.000037890` blocker-heavy relative to the accepted
average-two incumbents. It does so by redistributing vulnerability. Relative
to the original blueprint, seat two's deviation gain rises by `0.000881`
balanced and `0.000118` blocker-heavy; relative to the accepted average-two
incumbents, four seats worsen balanced and seat two worsens blocker-heavy.
The vector gate correctly keeps average two.

On the dense strength shifts, average two already increases five of six
deviation gains balanced and all six blocker-heavy. By average four all six
increase in both families. This is not merely a sum metric hiding one injured
seat.

The artifact retains every candidate's six raw deviation-gain deltas, so the
no-headroom and redistribution branches remain distinguishable without
reconstruction.

## Fixed primary hypotheses

ADR-0099 froze average four as the primary candidate. Its hypotheses resolve
as follows:

1. pooled blind normalized reduction positive: **false**, at `-0.004982112`;
2. aggregate precompiled rate exceeds blind: **true but degenerate**, because
   rejecting the two harmful candidates beats a negative blind denominator;
3. unilateral primary acceptance at least one of four: **false**, at zero of
   four; and
4. unilateral primary deployed reduction positive: **false**, at zero.

Aggregate primary acceptance deploys the two local candidates and reduces
normalized NashConv by `0.000261906`. It is not unilateral-safe. Blind
deployment loses roughly nineteen times the aggregate value the exact gate
salvages.

The preregistered primary hypotheses must remain failed. The positive
average-two result is a declared checkpoint and sequential-incumbent result,
not a rewrite of the primary endpoint.

## Provenance controls

Both iteration-32 averages are substantially worse than the iteration-64
blueprints under every target. Current 48 is also worse in three cases. On the
balanced strength shift it reduces aggregate NashConv by `0.000392174`, or
3.457% of headroom, but increases deviation gains for seats two, three, and
five and is rejected by the unilateral gate.

Thus the result is not “old checkpoint provenance beats solving.” The only
safe improvements come from newly trained average-two candidates on the local
shifts.

## Cost and resource result

The audit spent:

- 605.564 seconds, 59.88% of wall time, in exact six-seat evaluation;
- 397.988 seconds, 39.35%, in warm-search training; and
- 7.797 seconds in all other work.

For primary average four across four targets:

- blind search costs 397.988 seconds;
- precompiled exact verification costs 500.249 seconds; and
- one-shot exact verification costs 601.282 seconds.

For the useful average-two sequential candidates, search plus precompiled
candidate evaluation across all four targets costs 300.967 seconds. The exact
unilateral incumbent therefore realizes only about `7.35e-10` normalized
reduction per millisecond. The leaf-adjoint evaluator remains an offline
teacher, not an online gate.

Other mechanism results are clean:

- maximum exact evaluation: 29.951 seconds;
- maximum search step: 28.665 seconds;
- maximum target workspace compilation: 67.526 milliseconds;
- maximum zero-sum residual: `7.83e-15`;
- maximum host numeric estimate: 1.497 GB; and
- maximum CuPy pool: 2.127 GB.

The pinned width-384 path and 435/311 family batch counts reproduce exactly.

## Post-freeze shifted-belief dense control

The preregistered h4 orchestration control proved restart and warm-start
identity, but it did not compare quality with a literal dense oracle under the
new shifted beliefs. That omission was identified after the h32 artifact
existed, so it was repaired as an explicitly post-freeze diagnostic—not a
retroactive ADR-0099 gate.

`experiments/results/h4-shifted-belief-dense-crosscheck-v1.json`, SHA-256
`c276a3cb0c5ba0b1cca64ebf39f475b8f6db54d3b48e94313699142c4db0cbe5`,
compares both h4 range families and both target shifts. It checks the
checkpoint-64 blueprint, one warm DCFR trajectory step, and the resulting
average policy through the leaf-adjoint and literal dense paths.

Across the four shifted cases:

- maximum NashConv error is `3.45e-15`;
- maximum utility, best-response, and deviation-gain errors are `2.67e-15`,
  `1.78e-15`, and `2.45e-15`;
- maximum first-step regret error is `9.86e-16`;
- strategy-sum and average-policy errors are exactly zero; and
- the existing `1e-10` identity standard passes.

The diagnostic rules out a shifted-workspace semantics mismatch on an axis
where an external oracle exists. It is not a dense h32 proof. The standalone
runner is `src/pontius/h4_shifted_belief_dense_crosscheck.py`, SHA-256
`6d594734052fb6538151043d38cba0772e9d7828e048cac69dea78aa512596e5`.

## Decision

1. Reject blind fixed average-four deployment. Its pooled quality is strongly
   negative and additional iterations amplify dense-shift harm.
2. Retain the exact all-six-seat best-so-far incumbent as the strategy teacher.
   It abstains on identity, accepts two genuinely safe average-two policies,
   and blocks both later redistribution and outright regression.
3. Do not call the current exact evaluator an online verifier. Its useful
   gain arrives at a roughly 301-second precompiled bill across four targets.
4. Do not fit a shift-kind selector from four cases. The replicated
   local-versus-strength split is a hypothesis for workload expansion, not a
   runtime dispatch rule.
5. Do not optimize a fixed average-four reader. The actual customer is an
   anytime stream whose best candidate may occur earlier and whose current
   policies have not yet been measured.
6. Run the cheapest strategic successor before native verifier work: evaluate
   the stored current policies at warm iterations one, two, and four, continue
   each exact state through iteration eight, and evaluate current and average
   eight. Replay one declared incumbent order over all candidates.
7. Only if that widened candidate stream produces repeatable unilateral-safe
   value should the h32 fixed-belief policy-delta verifier become the next
   systems gate. Its target bill is the measured useful-candidate verifier,
   not the rejected primary average-four bill.
8. If neither sharp current policies nor average eight rescue the dense shifts,
   widen the poker game or improve the adaptation algorithm before accelerating
   the reader. The bottleneck would then be strategy generation, not
   verification.

## What this establishes—and what it does not

Within this reduced h32 river game, two warm DCFR iterations can safely adapt
a strong real blueprint to sparse blocker-sensitive belief changes. A fixed
four-iteration average is not a reliable product: it becomes unsafe locally
and substantially harmful under dense strength shifts. Exact vector-gated
anytime selection improves on both blind search and a fixed stopping rule.

This does not establish online feasibility, transfer to naturally observed
posterior ranges, coalition safety, or benefit in a wider betting/multi-street
game. The replicated split covers one board, two generated source beliefs,
and two deterministic shift constructions.

## Dissent protocol

**Confidence:** very high in source/target identity and exact measured labels;
high that fixed average four is the wrong interface; moderate that a richer
candidate stream will produce enough safe value to justify a native gate.

**Opposing evidence:** the two safe gains are small and confined to closely
related sparse shifts. Exact verification costs more than the search needed to
generate them. The result may be a laboratory curiosity rather than a useful
online adaptation mechanism.

**Largest risk:** interpreting the replicated shift split as a selector. Both
local targets were generated by the same rule on the same board, and both
dense targets share another rule. Four cases cannot estimate deployment
frequency or transfer.

**Cheapest falsification:** exploit the already serialized states. Evaluate
current one/two/four, extend four to eight, and evaluate current/average eight
under the same four exact teachers. This separates a bad fixed average
checkpoint from a genuinely ineffective warm-search trajectory without first
building a new verifier.
