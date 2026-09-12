# Witness soft-assignment pilot 001

Status: preparation only. The retained run requires separate approval of its
frozen plan. No incumbent, source branch, or prior milestone is changed.

Question: with frozen ordinary-preference features and the same number of free
strategy parameters, does interpolation between shared strategies reduce the
best-representable exploitability or improve finite-budget learning?

This is an observed-panel mechanism pilot, not an unseen-board confirmation.
Use ordinal-001's eight boards, pool 0 only, both uniform and polarized regimes,
and bets 5 and 10 at pot 10 and stacks 20/20. Pool 0 is selected by its identifier,
not its outcomes. This gives 32 exact 96-by-96 holding games. All compatible
deals and their original joint mass remain in the game and the best responses.

Use the ordinary-preference model from preference-confirmation-001 unchanged.
Reconstruct its eleven inputs and 78-column basis; compare the raw inputs to
the retained ordinal case. No target, witness, test outcome or new model fitting
enters assignment construction. The four prediction coordinates are unscaled.

For each seat and K in {8,16,32}, use the existing deterministic mass-weighted
anchored clustering. Hard assigns a hand to its existing label. Soft assigns it
between that label's weighted centroid and the nearest other centroid. For
Euclidean distances a to its home and b to the other, other weight is a/(a+b).
If both are zero, retain the hard label. Ties for other use the lowest index.
Round the other weight to the nearest multiple of 2^-20 (ties to even); home
is its exact complement. This permits exact row-mass certification. No
temperature sweep, feature refit, outcome-driven selection or winner adoption.

The resulting hand policy is P times a vector of K action probabilities. Both
methods have K free strategy probabilities per seat. Soft additionally stores
two indices and a weight per hand; it is not byte-matched to hard. Retain dense
weights for audit, report actual array storage and assignment nonzero counts.
Neither strategy class contains the other in general. A negative result only
rejects this fixed geometric soft assignment, not learned embeddings as a class.

Primary cell comparison: K=16, bet=5, mean soft-minus-hard certified floor.
Representation support requires its exact upper difference < -1e-8 chips.
Practical support additionally requires mean actual exploitability difference
at 10,000 updates < -1e-6 chips. These are descriptive decision thresholds,
not significance tests or minimum commercially relevant improvements.
Report K=8 and K=32 separately as capacity diagnostics; bet=10 is transfer.
Report every board, texture, regime and leave-one-board-out mean. No pooled
minimum across capacities, and no population confidence interval from seeds.

At each of 192 method-cells solve two asymmetric LPs: constrain only one
player at a time, leave its opponent at exact-hand resolution. The difference
between the two game values, divided by two, bounds the minimum exploitability
of a representable profile. Thus there are 384 LP calls, each using the existing
5-second, 10,000-iteration HiGHS bound. Certify in the original binary64 payoff
game interpreted rationally, including exact dyadic assignment weights.
Rounded reduced matrices only propose witnesses; each original-game saddle
gap must be <= 1e-8 chips. The verifier does not run an LP.

Run independent RegretBR learners against unrestricted hand responses, with
uniform initialization and the existing averaging convention. Retain 1,000 and
10,000 updates. Also run three fresh 0.1-second active-training trials, capped
at 100,000 updates each; record overshoot and actual update count. Timer trials
exclude assignment building, matrix preparation, scoring and I/O, whose time is
reported separately. Alternate hard/soft first across cells and repeat indices.
The primary fixed-work endpoint and secondary matched-time endpoint remain
separate. Total hard/soft trajectories: 192 fixed-work plus 576 timed.

For every saved profile retain component probabilities, hand probabilities,
unrestricted exploitability, and exact exploitability from rational lifting.
An independent scalar terminal enumeration must agree within 1e-10 chips.
All certificates are rechecked and all trajectories replayed from zero in a
separate verifier with LP calls disabled; exact timing is not replayed, recorded
iteration counts are. Record all failures and non-improvements.

Required synthetic checks: one-hot floors match the existing certified solver;
hard RegretBR matches predecessor step-for-step; general soft extrema equal
independent corner enumeration; row mass and feasibility; degenerate centers;
tampered witnesses; and a counterexample where softening worsens the floor.
Rehearse the runner only on synthetic data, never score the observed panel
before freezing. Python 3.14.6, NumPy 2.5.2, SciPy 1.18.0, one BLAS thread,
no tracemalloc. Worker and verifier each have a 1,800-second timeout. No hard
RSS cap is imposed or claimed. Unique output, checked source/input pins before
and after execution, complete captures, failure retention, final manifest.

All original reports and evidence remain untouched. This pilot is a local
research candidate; it does not authorize commit, push, publication or deployment.
