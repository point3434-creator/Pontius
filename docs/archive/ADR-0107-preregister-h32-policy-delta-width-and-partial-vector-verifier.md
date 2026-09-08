# ADR-0107: Preregister h32 policy-delta width and partial-vector verifier

**Status:** Preregistered; implementation and workload frozen before any live
h32 partial-verifier timing or h32 policy-delta width result

**Date:** 2026-08-20

## Decision

Run one post-label mechanism audit against the exact 13-policy h32 corpus
accepted by ADR-0106. The audit has two deliberately separate arms:

1. an optimistic structural screen of an exact terminal-leaf policy-delta
   representation; and
2. a live acceptance-aware exact verifier that reads one seat at a time and
   stops as soon as the fixed blueprint envelope can classify the candidate.

The delta arm is not presumed to win. An exact multi-seat policy delta can
multiply terminal work: for target seat `t`, changing `k` opponent seats gives
up to `k` ordered-product telescope terms where a complete candidate read uses
one terminal term. Calling that expansion “incremental” does not make it
cheaper.

The live product is therefore the narrowest mechanism that is already
mathematically useful to ADR-0106. It must return the same selected policy
digest as full exact evaluation while avoiding seats that cannot affect the
fixed-envelope result.

This audit creates no new strategy-quality labels. Every candidate already has
an exact six-seat teacher vector. The new evidence is representation width,
partial-evaluation correctness, stopping behavior, and wall time.

## Frozen artifacts and code

The primary fixed sources are:

| Input | SHA-256 |
|---|---|
| ADR-0105 acceptance replay | `1898c24a6c0232059a19c2151f29537a574ba85d8ec9a3641c117eda9b9087af` |
| ADR-0099 warm-search acceptance | `150362ea770c80190c8124148fa66e0a376d98d1bd01b790f3d11e5ad9b5d8a9` |
| ADR-0101 candidate stream | `b432eda21d1978b1dd576a9f4e7451250f1d53dcf9a88a6efa739d681ecb6f33` |
| ADR-0103 interpolation audit | `ba0fdd6ea8dfd67de3f74c9026588d3555525d362a74ad1f03295f35281cb8c0` |
| h32 checkpoint ladder | `242de5f0a42693248f98cc8f127f4fc892606df58e94d28c107d542b1276736b` |
| h32 checkpoint extension | `cf2e2d85bfc8a5dd49f9490b7ddcac2817eaf9d73d9857535a72ac8e964f5ce9` |

Every transitive evaluator, GPU, factor-belief, sparse-incidence, automaton,
and reconstruction implementation is hash-pinned in the config.

The frozen new files are:

- `src/pontius/fixed_envelope_verifier.py`, SHA-256
  `db8040b0a94cc9ffe95fb4b8854a1924525a63093464cb5523f897763a45a053`;
- `src/pontius/h32_policy_delta_verifier_audit.py`, SHA-256
  `16a5e7cad3146a513715dec18376fd86da080c0e915fd07a1b2f79485d15ccfd`;
  and
- `experiments/configs/h32-policy-delta-verifier-audit-v1.json`, SHA-256
  `ea0cd0840de3a2fc31114963ae45dd8b3d3ca6a4906fdaff585a78001d79bb4b`.

The result target is
`experiments/results/h32-policy-delta-verifier-audit-v1.json`.

The complete repository suite passes 492/492 before freeze.

## Exact policy-delta width screen

For a target response seat, cache the baseline terminal numerator vector at
every public terminal. Its h32 storage is tiny compared with the contraction
workspace: one Float64 value per terminal and open target hand.

For baseline opponent-seat path factors `b_i` and candidate factors `c_i`, the
exact ordered telescope is

`product_i c_i - product_i b_i = sum_k (c_k - b_k) product_{i<k} c_i product_{i>k} b_i`.

The screen counts one signed value feature for every nonzero opponent-seat term
at every terminal. It charges neither a reach/mass feature nor a candidate root
and assumes the baseline terminal vectors are already cached. This is
optimistic for the delta arm. It reports:

- changed public nodes and seats;
- supported signed terminal terms;
- full candidate value width;
- the current evaluator's value-plus-mass width;
- optimistic delta/full width ratios per response seat and profile; and
- baseline terminal-numerator cache bytes.

The screen is not timed as an implemented signed contraction. Its purpose is to
answer whether building that contraction is structurally justified. No gate
requires delta width below full width; a negative result must be allowed to
pass honestly.

## Acceptance-aware exact verifier

The baseline blueprint certificate supplies six exact deviation gains and a
raw guard of `3e-9`. For every candidate, compile its probability tape once and
evaluate response seats in the fixed, label-free order `0,1,2,3,4,5`.

After seat `i`, stop for either of two exact reasons:

1. **Blueprint cap:** candidate gain `g_i` exceeds blueprint gain `b_i` plus
   guard. The candidate is infeasible regardless of every unread seat.
2. **Objective lower bound:** the sum of already observed nonnegative gains
   exceeds the lowest fully verified feasible NashConv plus guard. Unread gains
   cannot be negative, so the candidate cannot enter the optimum's tie band.

Otherwise evaluate all six seats. A completed candidate supplies the ordinary
fixed-policy utilities, best-response values, deviation gains, zero-sum
residual, and NashConv. The canonical ADR-0106 selector runs only over the
blueprint and completed feasible candidates.

Neither teacher values nor future candidates enter a live stop decision. The
teacher is consulted only afterward to measure error and stopping identity.

The proof is simple but load-bearing: a cap breach proves infeasibility, and a
partial sum of nonnegative deviation gains is a lower bound on final NashConv.
Thus no stopped candidate can be the fixed-envelope optimum.

## Frozen workload

Use the exact ADR-0106 geometry:

- six seats and 32 hands per seat;
- balanced and blocker-heavy factor beliefs;
- local-blocker and all-seat-strength target shifts;
- one equal-stack, one-bet river tree on `2c 7d 9h Js Qc`;
- width 384, three mixture components, and the accepted CUDA environment; and
- 6,144 information sets and 12,288 hand-action entries.

Reconstruct all policies from immutable checkpoints and require all 52 digests
to match the teachers. The 13-policy order is the source-union order already
published by ADR-0105:

1. average 32 control;
2. current 48 control;
3. search averages 1, 2, and 4;
4. search currents 1, 2, 4, and 8;
5. search average 8; and
6. current-one/current-two interpolations 0.25, 0.50, and 0.75.

The candidate order affects work but not the permitted final answer. Re-simulate
the verifier under canonical, reverse, policy-digest, and 64 seeded orders. All
67 must return the exact ADR-0106 selected digest on every target.

## Honest timing comparison

The live marginal charges:

- candidate probability-tape compilation;
- every actually evaluated seat contraction;
- reverse response/profile propagation; and
- all GPU transfers and synchronization.

Delta width planning is reported separately and is not charged to the partial
verifier product.

The full incumbent bill is the sum of the 13 already recorded exact
full-profile wall times. To control same-day timing drift without rerunning all
179 omitted seat calls, search average one is necessarily completed on every
target. Scale the historical full bill by

`live complete average-one time / recorded complete average-one time`.

Report raw historical, drift-calibrated, and purely structural seat-call
speedups. Require pooled and both per-family calibrated speedups of at least
`1.5x`. The calibration ratio itself must remain between `0.5` and `2.0`; a
wildly different runtime invalidates the historical comparison.

Compilation of the target belief and the already required blueprint
certificate are common to both candidate-verification arms and are reported
separately rather than asymmetrically charged.

## Frozen gates

The result passes only if:

1. every source and implementation hash reproduces and every source audit is
   accepted;
2. there are exactly four targets, 52 candidates, 133 live seat evaluations,
   and 13 completed candidates;
3. all target descriptors, 13-policy unions, and 52 reconstructed policy
   digests reproduce;
4. live seat utility, best-response, and deviation-gain errors are at most
   `1e-9` against their frozen teachers;
5. every completed NashConv error is at most `1e-9` and every completed
   zero-sum residual is at most `1e-9`;
6. every live stop reason and seat matches the exact-vector simulation and
   every stop inequality is literally satisfied;
7. the live final selection and all 67 simulated arrival-order selections
   match the ADR-0106 digest;
8. every delta width and ratio is finite;
9. structural seat-call speedup is at least `1.5x`;
10. pooled and both family drift-calibrated wall-time speedups are at least
    `1.5x`;
11. each seat read is at most 60 seconds, target workspace compilation is at
    most 30 seconds, host numeric peak is at most 3 GB, and GPU pool peak is at
    most 4 GB; and
12. total audit wall time is at most 1,200 seconds.

There is no strategy-quality, winning-candidate, delta-rank, or delta-speed
gate. This is a post-label systems audit.

## Pre-freeze disclosure

The already revealed exact vectors imply—without any new h32 contraction—the
following fixed-order seat counts:

| Family | Shift | Required seats | Full seats | Structural ratio |
|---|---|---:|---:|---:|
| balanced | local blocker | 49 | 78 | 1.592x |
| balanced | strength | 20 | 78 | 3.900x |
| blocker-heavy | local blocker | 46 | 78 | 1.696x |
| blocker-heavy | strength | 18 | 78 | 4.333x |

Pooled, that is 133 versus 312 seat reads, or `2.346x`. This known arithmetic
is frozen as a mechanism-identity gate, not presented later as held-out
discovery.

The historical 13-candidate full bills are approximately 373.1, 373.2, 277.1,
and 278.2 seconds for those four rows. No live partial bill, timing calibration,
or h32 delta width has been observed.

Development controls additionally establish:

- all 52 policies reconstruct to their exact teacher digests;
- the generic partial verifier reproduces a complete h4 leaf-adjoint vector;
- one h4 public-node edit changes exactly one seat and has optimistic delta/full
  width ratio about `0.014`; and
- synthetic cap and objective stops preserve the same final optimum under
  reversed candidate order.

The h4 local edit shows that policy deltas can be excellent for the right
customer. It does not predict the whole-profile h32 result.

## Decision branches

- If the live verifier fails exactness or selection identity, retain full
  profile evaluation and repair stopping semantics.
- If exactness passes but calibrated speed is below `1.5x`, retain the
  mechanism as an optional rejection shortcut but do not call it an economic
  win.
- If it passes, accept partial-vector verification for fixed-envelope candidate
  portfolios. Do not claim that a selected safe candidate itself becomes
  cheaper; it still needs all six seats.
- If realistic h32 deltas are narrower than full, preregister an actual signed
  contraction with baseline terminal caching.
- If realistic h32 deltas are wider, reject the naive exact delta path for
  multi-seat candidates and direct optimization toward early stopping,
  candidate scheduling, or a resident GPU feature pipeline.

## Dissent protocol

**Confidence:** extremely high in the stopping proof and source reconstruction;
high that live exact values reproduce; moderate that historical calibration
supports a stable `1.5x` wall-time gate; low in the h32 delta-width direction.

**Opposing evidence:** selected local candidates require all six seats, so this
mechanism earns its savings only from rejected portfolio members. A generator
that emits one excellent candidate rather than 13 mixed candidates receives
almost no benefit.

**Largest risk:** optimizing verification around a development corpus whose
bad dense directions are unusually easy to reject at seat zero. Transfer to
new boards and wider trees is unmeasured.

**Cheapest falsification:** the first live target. Any seat-value mismatch,
wrong stop, or calibration outside `[0.5, 2.0]` rejects the claimed mechanism
before pooled timing is interpreted.
