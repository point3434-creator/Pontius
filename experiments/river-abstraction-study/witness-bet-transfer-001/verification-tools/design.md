# Frozen bet-size transfer: witness-bet-transfer-001

User instruction: "Let's design and run that test". Authorized scope is the proposed
quarter-pot, half-pot and pot-sized frozen-model transfer experiment. No model fit,
production modification, commit, push or adoption. Keep fourteen prior milestones.

## Population and intervention

Every case from witness-preference-confirmation-001: 16 observed boards, three
fixed hand pools, uniform and synthetic polarized ranges, 96 holdings per seat.
All bets share identical boards, ranges, collision-conditioned deal probabilities,
pot 10 and stacks 20/20. Construct actual RiverHoldem objects with bets 2.5, 5 and
10; no raises or multiway play. Only called-showdown stakes change with bet size.
Derive the new matrices through the existing public game builder. Independently
check unchanged joint/check/fold arrays and call = sign(check)*joint*(5+bet).

The eleven raw features, four classifier outputs and both group assignments must
match the frozen half-pot predecessor exactly at every size. This invariant is
expected because these features contain no bet-size input. It is not an assertion
that the optimal action probabilities are unchanged. Keep ordinary-preference,
range-response and range-equity at matched occupied capacity. No new training,
feature changes, capacity search, alternate seed or panel extension.

## Computation and controls

For bets 2.5 and 10, use two asymmetric LPs per method to certify the least
full-hand exploitability representable by the grouping. Use the unchanged
alternating vanilla CFR from zero regrets through 10000 iterations, saving the
unweighted average policy at 100, 1000 and 10000 iterations. Re-solve each bet
independently. Rotate method order by case index and bet index. This is a matched
iteration comparison; stage times are diagnostics, not matched-wall-time claims.

For bet 5, copy the exact existing certificates and iteration checkpoint policies
from confirmation-001 and solver-budget-001; verify them again. This retained
anchor is not a newly independent replication. All 288 case/bet cells remain.
Exactly 1152 new LP calls, 576 new CFR trajectories, 1728 new policy checkpoints,
864 reused checkpoints and 576 reused asymmetric certificates. There are 1728
asymmetric certificates total and 2592 resolved checkpoint policies to verify.
No full-hand LP is necessary: each grouping floor has its own saddle certificates.

For every method and bet, separately score the unchanged half-pot 10000-iteration
policy under that bet's payoffs. These 864 fixed-policy controls require no new
solving. Report resolved-minus-fixed-policy exploitability and the marginal-weighted
absolute action-probability change for each seat. They are secondary diagnostics.

## Endpoints and rules

Primary actual-policy metric: full-hand exploitability at 10000 iterations.
Primary reference: range-response; range-equity is secondary. Within each bet,
average six cases per board equally, then sixteen boards equally. Never pool bets
for the primary claim. Quarter-pot and pot-sized bets must each have mean
candidate-minus-response below -1e-10 chips for actual-policy transfer to pass.
The separate representation-transfer flag requires a negative upper endpoint of
the mean candidate-minus-response certified floor interval at each new bet size.
The retained half-pot anchor cannot rescue a failed transfer endpoint.

Separate robustness flag: actual-policy and floor differences favor the candidate
within every texture, range regime and leave-one-board-out panel at both new sizes.
Report board means, case counts and largest losses even if mean flags pass. Report
each new bet's change in relative advantage versus the half-pot anchor; numerical
differences across different games are descriptive interactions, not win rates.
Earlier iteration checkpoints and fixed-policy controls cannot replace primaries.
No statistical-confidence, BB/100, realistic range-reach or six-max strength claim.

## Verification and bounds

Preflight: public game/tree payoff agreement at every size, exact called-showdown
stake identities including ties, unchanged feature/group inputs, invalid bet
refusals, existing CFR parity and asymmetric certificate tests. No scored-panel
rehearsal. Freeze scripts, design, predecessor manifests and transitive source pins
before launch. Refuse any existing output directory. Python 3.14.6, NumPy 2.5.2,
SciPy 1.18.0, one BLAS thread, no allocation tracing. Worker limit 1200 seconds,
parent verifier 1200 seconds; no RSS cap or peak-memory claim. Each LP retains the
existing five-second / 10000-iteration limit and rational certificate gate.

Parent independently rebuilds every game and grouping, rechecks every certificate
with LP disabled and replays all checkpoint policies from CFR, including the
retained half-pot anchor. Scalar fsum evaluation checks every resolved policy and
every fixed-policy control. Separate stdlib rational arithmetic recomputes summary
means, counts, floor interval differences, interactions and decision flags. Retain
all original output, receipts, policies, certificates, scripts and report. Preserve
any failed invocation; do not overwrite or silently rerun it.
