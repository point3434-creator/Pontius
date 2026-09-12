# Witness order diagnostic 001

Question: do inconsistent ordinal probabilities damage caller grouping?
Prior ordinal-001 had a half-pot representation regression concentrated in the
caller. Crossings are a hypothesis, not an established cause. This is an observed
panel diagnostic. No unseen-board claim, model selection, or adoption follows.

Freeze before scoring: all 64 evaluation cells of ordinal-001, without selection
by loss or crossing. Eight boards, two pools, two regimes, bets 5 and 10; 96 hands
per seat, pot 10, stacks 20/20, heads-up one-bet game. Half-pot is primary; pot is
secondary. Equal weights within each bet panel; eight boards are the board units.

One new method, caller_projected: freeze ordinal-001's coefficients and bettor
groups. For each caller hand and each witness, Euclidean-project its three sigmoid
outputs onto the nonincreasing cone using equal-weight PAVA. Thresholds remain
-0.25, 0, +0.25 chips. This changes inference features, potentially including the
zero head; no fit is performed. Ordered triplets remain identical. Use all nine
projected features in unchanged weighted anchored clustering, with the original
occupied caller group count. Both seats' group counts must remain unchanged.

References are the retained ordinal, sign_conditioned, ordinary_preference and
range_response. Reuse their exact retained groups, certificates and trajectories.
Do not refit, regenerate opponents or use oracle labels to select a repair.

For each new cell solve the two asymmetric constrained LPs and run the unchanged
RegretBR for 50,000 iterations, retaining 1,000/10,000/50,000 checkpoints. Exactly
128 new LP calls and 64 trajectories. Existing baseline certificates are rechecked
and all baseline checkpoint scores re-evaluated. Every new trajectory is replayed
from zero in a separate verifier with LP and fitting disabled. Scalar evaluation
must agree within 1e-10 chips; certified floor must bound actual within 1e-8.

Primary mechanism support requires half-pot mean floor upper difference < 0 and
50k actual difference < -1e-10 against unmodified ordinal. Stronger practical
recovery additionally requires both criteria against sign_conditioned and the
old ordinary_preference incumbent. Secondary pot non-regression requires actual
delta <= 1e-10 and floor upper delta <= 1e-10 against ordinal. These are diagnostic
flags, not population significance tests or promotion gates. Report all flags.

Report means, paired intervals for floors, cell directions, every board, texture,
regime and leave-one-board-out panel. Retain per-cell caller crossing mass before
and after (threshold tolerance 1e-12), changed-hand marginal mass, zero-head mean
absolute shift, weighted squared feature distance, and marginal-product mass of
hand pairs whose caller co-membership changes. A corrected order need not improve
strategy quality. Do not reinterpret a negative result as success.

Projection checked independently by exhaustive contiguous partitions on 1,125
triplets and all actual caller triplets, plus idempotence, bounds, ties and witness
boundaries. Parent verifies fresh inference from frozen coefficients and retained
raw features, reconstructs games and verifies input provenance. Bettor trajectory
must remain bit-identical to the retained ordinal trajectory.

Python 3.14.6, NumPy 2.5.2, SciPy 1.18.0; single BLAS thread, no tracing. Worker
and verifier each have a 900-second timeout; sequential, no RSS cap or memory
claim. No scored rehearsal. Unique output, preserve failure, verify source pins
before/after, retain non-improvements and every prior milestone unchanged. No
production code changes, publication, commit, push or cold-review claim.
