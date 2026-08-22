# ADR-0269: Preregister target-isolated closure census

- Status: accepted corrective preregistration before any census-label recomputation
- Date: 2026-08-22
- Corrects: ADR-0267 under ADR-0268
- Base config SHA-256: `494b4d93a5e8e17b85e09446e01d291b672b7a3098203513010725d4bd8c0e3c`
- Config: `experiments/configs/h32-retained-convex-closure-census-v2.json`
- Config SHA-256: `0ecaf532922ee77e1824cb5a3e8094b36389e055acaf8f680afe315a264a1f28`
- Runner SHA-256: `8c215185867338f5c1ab90e85691f3b991bada6f5a13f221869165f6497575bc`
- Control SHA-256: `41e2baa89c7c841af42dc07c07ec476698e1831338ab27994156360f1eb7484a`

## Correction scope

Change orchestration only. Load and fully validate the byte-pinned ADR-0267
config, inventory, runner, controls, target order, setup modes, warm step,
master, all-seat oracle, response classifier, cuts, tolerances, bound rule,
32-round cap, 240-second target cap, 10,800-second campaign cap, memory gates,
keystone replay, decision table, post-fold exclusion, and immutable emission.

Do not change any scientific field after the partial outputs from ADR-0268.
The v2 wrapper calls ADR-0267's target implementation directly.

## Partial-label disclosure

The first five target summaries printed during the rejected invocation and
target 6 reached an unpersisted master state. Recompute targets 1–6 in their
unchanged positions. Continue with targets 7–42 without using any recomputed
value, round count, stall, timing, error, or response signature to alter the
roster or method.

Every target already had strategy evidence open before ADR-0267, but these
optimizer labels are still new retrospective labels. Do not call v2
label-blind or fresh.

## Target isolation

Wrap each complete ADR-0267 target invocation. On success, retain its entire
row. On an exception:

- discard every candidate and incomplete numerical row from that target;
- run garbage collection and release the CuPy pool;
- record the target ID, exception type and exact message, elapsed time, and
  post-cleanup GPU memory;
- mark the target `target_error_censored` with no closure round;
- write no candidate and emit only the immutable blueprint; and
- continue to the next predeclared target.

Only
`ArithmeticError: behavioral master primal/dual verification failed` is an
expected target-local error for a process pass. Any other exception is
checkpointed but makes the final process gate fail. The known error remains a
scientific censor even when isolated successfully; it never becomes an
accepted master solve.

No tolerance may loosen. Do not retry with another HiGHS method, perturb the
LP, delete a row, snap a candidate, or accept an unverified KKT result. A later
diagnostic LP replay may explain the component but cannot be authority in this
run.

## Durable checkpoint

After every success or censored target, atomically replace a complete partial
JSON containing all outcomes so far. The next target may start only after that
checkpoint exists and hashes successfully. A later campaign failure therefore
cannot erase already completed rows.

The final artifact records all 42 ordered outcomes, the final partial-artifact
hash, completed-target validity checks, target errors, the keystone replay,
retrospective label counts, and the inherited closure distribution. The
partial artifact is diagnostic; the final sealed artifact remains the
authority when the process finishes.

## Gates and decisions

Require clean Git, exact v1/config/inventory provenance, all 42 targets
attempted in order, one checkpoint per outcome, only the known isolated error,
valid numerical and engineering gates on every completed row, censored status
on every failed row, keystone reproduction when that target completes, zero
post-fold labels, immutable-blueprint emission, explicit partial-label
disclosure, finite output, and null population claim.

Inherit ADR-0267's scientific branches exactly. Any target error, numerical
stall, or resource censor forces the censored/fallback branch. Only 42/42
verified closure by round one can authorize fresh confirmation. Full closure
with any later round keeps the exact solver off-clock and the direction path
live. The already observed 3- and 2-round targets make the first branch
impossible, but its rule remains frozen rather than rewritten post hoc.

## Claims boundary

This correction makes partial work durable; it does not cure the master
failure, prove global closure on a censored target, or strengthen the convex
theorem. The 42 contexts remain retained and non-IID. No deployment,
direction-obsolescence, composition, cross-street, chip-EV, AIVAT, full-width,
exploitation, or poker-strength claim is authorized. The post-fold identities
remain unopened.

## Decision

Commit the v2 wrapper, config, controls, this ADR, roadmap, and generated status
from a clean tree. Invoke v2 once. Do not manually restart at target 6, inspect
the partial checkpoint to adapt later targets, or remove it after a failure.
