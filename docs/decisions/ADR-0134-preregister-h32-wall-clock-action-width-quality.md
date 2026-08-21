# ADR-0134: Preregister wall-clock-matched h32 action-width quality

## Status

Frozen before any h32 two-size policy construction, sized-game best response,
or common-game action-width quality measurement.

## Question

From one immutable one-size incumbent and under one fixed construction-plus-
planning shot clock, does a second opening size produce more fixed-envelope-
accepted strategy quality than spending the same opportunity on the faster
one-size resident solver?

This is the strategy question ADR-0132 deliberately left open.  The accepted
cache geometry and the failed diagnostic step supply systems priors only; they
do not set a quality threshold or outcome gate.

## Fixed incumbent and target corpus

Use the clean ADR-0113 fresh-board artifact exactly.  For balanced and
blocker-heavy ranges, reconstruct the immutable average-64 source blueprint
from its stored checkpoint.  Reconstruct the same two support-preserving target
beliefs per family:

- local blocker seat 5 likelihood doubled; and
- all-seat showdown-strength likelihood from 1 to 2.

This gives four frozen targets on board `4h 6s Td Qh As`.  The corpus is enough
for the first sized comparison, not for population transfer.  No source
retraining, new board, alternate range family, or target filtering is allowed.

ADR-0133 supplies the common deployment universe.  Both arms are scored in the
same two-size game with pot `12`, equal stacks `30`, bets `3` and `6`, and
game-derived payoff span `48`.  The one-size incumbent and every one-size
candidate map unsized bet mass to `3`, put zero opening mass on `6`, and copy
their small-bet fold/call continuation below both sized bets.

## Wall-clock arms

Each arm independently receives `90,000 ms`.  The charged interval starts
before target `FactorTT` workspace construction and includes:

1. target-workspace construction;
2. cold belief and six-seat terminal-cache construction;
3. solver construction and normalized warm initialization;
4. every complete alternating DCFR step;
5. current/average candidate capture; and
6. compact schema-bound policy serialization and diagnostics.

The one-size arm uses the accepted raw one-size resident cache and a `3`-chip
game.  The two-size arm uses the accepted scale-canonical affine cache and the
`3/6`-chip game.  Warm pseudo-regret mass is `0.1 *` each solver game's own
payoff span: `3.0` one-size and `4.8` two-size.

Steps are indivisible six-traverser updates.  An arm may start a step only if at
least `35,000 ms` remains.  A step above that reserve is a mechanism failure.
Both arms cap at eight complete steps.  Unused sub-reserve time is reported and
is not converted into partial-seat work.  This is an actual deadline rule, not
an iteration match or interpolation between quality labels.

Arm order alternates by target as `one/two`, `two/one`, `two/one`, `one/two`.
The h2 control warms common kernels before h32; order remains recorded because
thermal and allocation effects may persist.

## Frozen candidate stream

Search sees no exact quality label.  Each arm emits, in order:

1. warm current iteration one;
2. the behavioral `0.50` interpolation of current iterations one and two, if
   two completes;
3. current policy at the deadline; and
4. average policy at the deadline.

The iteration-one and `0.50` interpolation forms are inherited from the two-
board one-size evidence rather than fitted here.  Deadline policies allow the
faster arm's additional completed work to matter.  Exact policy-digest
duplicates are merged causally and retain aliases.  Every unique sized policy
is stored as ordered probability rows bound to the complete external
information-schema digest and must round-trip exactly.

No candidate is selected during planning.  For each target, both arms finish
before that target's first sized quality call.  Later execution cannot branch
on an earlier target's strategic result; the workload, order, deadline, and
candidate rule are fixed in code and config.

## Fixed-envelope verification

After both arms finish, construct a fresh canonical sized verifier cache and
evaluate the embedded incumbent completely for all six seats.  This fixes the
immutable sized-game cap vector.  It is never reanchored to a selected
candidate.

For each arm independently, verify its deduplicated stream in seat order
`0,1,2,3,4,5`.  Stop a candidate when either:

- one deviation gain exceeds the incumbent seat's gain plus raw guard
  `1e-10 * 48`; or
- the nonnegative partial NashConv already exceeds the best complete feasible
  candidate plus that guard.

Run the canonical fixed-blueprint-envelope selector over complete candidates.
The incumbent wins every guard tie.  Thus the primary deployed outcome for an
arm is exact sized-game normalized NashConv reduction from the same incumbent
after immutable six-seat acceptance, including abstention.

Report three bills separately:

- construction and planning under the 90-second shot clock;
- marginal arm bill, adding its candidate verification; and
- full one-shot bill, also adding fresh verifier construction and incumbent
  certification.

No exact evaluator time or label is hidden inside the planning budget.

## Implementation identity

The machine-readable contract is
`experiments/configs/h32-action-width-quality-v1.json`.  It binds the ADR-0113
strategy artifact, ADR-0132 cache artifact, environment requirements, common-
game policy bridge, sized evaluator, both resident solvers, canonical cache,
fixed-envelope selector, and their direct controls by SHA-256.

Before freeze, the complete repository passed 554 tests.  The new h2 controls
additionally execute both planning arms through two steps, compact candidate
round trips, a fresh canonical verifier cache, and the sized fixed envelope.
No h32 function in the new audit was called.

## Frozen gates

The result passes only if:

1. all source hashes, clean Git state, environment versions, parent outcomes,
   target descriptors, belief digests, hand axes, and target order reproduce;
2. the h2 embedding/evaluator control remains within its frozen Float64 bounds;
3. one-size and two-size topology, information-set, action-entry, payoff-span,
   and 378-basis counts reproduce;
4. all eight arms complete at least one whole step, no step exceeds 35 seconds,
   no charged arm exceeds 90 seconds, and no cache exceeds 120 seconds;
5. every compact candidate artifact round-trips exactly and all policies are
   finite and normalized;
6. both planning arms precede every target's quality phase;
7. every complete quality vector sums exactly within tolerance, every profile
   is zero-sum within `1e-9`, and every seat read is at most 60 seconds;
8. every selected policy remains inside all immutable incumbent caps;
9. the GPU pool remains below 12 GB; and
10. the complete audit finishes within 3,600 seconds.

There is no gate on candidate feasibility, selected action width, added-bet
mass, NashConv reduction, arm winner, quality rate, abstention count, step
count above one, or strategy direction.  A clean two-size loss is a passing and
useful result.

## Decision branches

- If a mechanism gate fails, preserve the artifact and repair only through a
  new preregistration before interpreting strategy.
- If two-size wins across the frozen aggregate, record a conditional one-board
  action-width result and replicate on new boards before changing the action
  abstraction.
- If one-size wins, retain one size under this shot clock and do not rescue the
  second size by changing the budget, completion, warm mass, or candidate rule
  after inspection.
- If both abstain broadly, treat the experiment as evidence that this fixed
  generator cannot safely expose the action-width opportunity, not that the
  wider game has no strategic value.

## Dissent

**Confidence:** very high in the common-game exactness and frozen accounting;
high in the fixed-envelope semantics; low-to-moderate that four targets can
rank action width beyond this board.

**Opposing evidence:** the two-size cache spends roughly 20–25 seconds cold and
the only diagnostic step was 2.245x the one-size bill.  Conversely, the
one-size completion exposes a zero-probability `6`-chip branch with copied
responses, which may create real widened-game vulnerability that only two-size
planning can repair.

**Largest risk:** exact verification still takes seconds, so even a strategic
win would not close the project's 5–250 ms online thesis.

**Cheapest falsification:** execute this frozen four-target audit once.  Do not
inspect an h32 sized policy before the preregistration commit is clean.
