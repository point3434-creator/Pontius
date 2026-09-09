# Evaluation-loop design: export bridge and fresh-deal panel

Companion to the [brief](brief.md). The brief says what must be true; this says
how, before any implementation. It exists mostly because the interfaces turned
out to disagree with three of the brief's acceptance criteria as first written,
in ways that needed a controller ruling rather than an implementer's quiet
resolution. Those rulings were made on 2026-09-08 and are recorded below; the
brief now carries the amended criteria.

## Goals and observation

The brief's eight criteria, and where each is observed:

1–2 (no third outcome; agreement over a declared enumeration) — observed in the
provider's own records. The host records every controlled decision as
`table_hit` or `passive_default` and every provider outcome as `blueprint_hit`
or `blueprint_default`. The agreement test drives the actual host on a sample of
deals and reads those labels; it does not compare against a re-implementation
of the lookup.

3 (fits or the overflow point is recorded) — observed on the encoded artifact's
**wire bytes**, because that is what the host's 1,048,576-byte input cap
measures. The retained 883-entry corpus is the warning: 71,939 canonical bytes,
1,047,220 wire bytes. A capacity check on canonical bytes would pass a file the
host refuses.

4–7 (seeds, pairing, clustering, loss budget) — observed in a frozen
preregistration and in the panel's run record, which carries every seed, every
filter decision, and every excluded observation with its reason.

8 (one journal line; family summary) — observed in `execution_journal.jsonl`
and `experiments/bot-validation.md`.

Criteria 4, 5 and 6 could not be satisfied as originally written. Section
"Rulings" records why, and the amendments accepted.

## The game, and why it fits the key space

The codec stores one deterministic action per **exact full-hand key**: seat,
two private cards, board, blinds, all six stacks and contributions, and the
complete public history as eight-field records. The exact solvers produce
policies over abstract information-set strings. Neither Kuhn nor the
float-chip `RiverHoldem` microgame has any image in that key space.

`legal_river_continuation.LegalHeadsUpRiverContinuation` does. It is an exact
two-player river game whose states carry a real `NoLimitBettingState` and a
`RiverDeal`, so at every hero decision node the blueprint key can be built by
the same `BlueprintDecisionKey.from_state` call the runtime uses. Its entry
condition is narrow — checked-to river, exactly two live seats, the other four
folded with **zero** committed chips, one prior river check by the other seat,
a check-or-bet root — and that narrowness is the point: the host's scripted
opponents reach exactly that state deterministically.

The prefix, already the fixture in `tests/test_legal_river_continuation.py`:
button 0; seats 3, 4, 5, 0 fold to the big blind for zero chips; seat 1 (small
blind) completes; seat 2 (big blind) checks; flop and turn check through; seat 1
checks the river; seat 2 acts. Logical player 0 is seat 2, player 1 is seat 1.
The host produces this with opponents `fold_to_bet` in seats 0, 3, 4, 5 and
`passive` in seat 1, controlled seat 2, for **every deal**, because neither
script consults cards. The bot's own pre-river decisions are passive defaults by
construction (no pre-river keys are exported), which is declared, identical
across compared policies, and cancels in pairing.

Two knobs, both `TableInput` parameters:

- **Stack depth `s`** (all six seats, ≥ 2). Pot at the root is 4; remaining
  stacks are `s − 2`; the kernel enumerates every integer raise-to from 2 to
  `s − 2`. The fixture's `s = 6` gives root actions (check, 2, 3, 4) and roughly
  four hero decision nodes per hand. `s = 4` should give exactly one bet size,
  an all-in, and exactly **one** hero decision node per hand — to be confirmed
  against the kernel, not assumed.
- **Hero pool `H`** ⊆ the 1,081 hands compatible with the board. Villain is
  uniform over the 990 hands compatible with board and hero hand, which is also
  the panel's marginal villain distribution given the hero's cards regardless of
  what the four folders hold.

Capacity arithmetic: entries ≈ |H| × (hero nodes per hand). At roughly one
kilobyte per wire row — eleven history records plus the six-vectors — 1,081
entries at `s = 4` land within a few percent of the cap on either side. That is
a measurement, made first, and it decides |H|. At `s = 6`, |H| is bounded near
250, about 23% coverage. The design recommends `s = 4` for both slices: maximal
coverage, one decision per hand, a tree small enough that both teachers below
are exact in seconds, and a panel in which almost every seeded deal is a table
hit. It is the smallest bridge that is not vacuous; richer sizing is a later
variant, not a Slice A ambition.

## Mechanisms, invariants, and covered places

1. **The prefix is replayed through the kernel, never constructed.** Export,
   agreement enumeration, and the panel all obtain the root `NoLimitBettingState`
   by applying the same scripted action sequence to `new_hand`. Invariant: the
   exported key at a hero node equals `BlueprintDecisionKey.from_state` at the
   state the host actually reaches. It must hold in three places — export,
   agreement, panel — and it is observed end to end by driving the host and
   reading `table_hit`, not by comparing two objects built in one process.
   Board equality and starting-stack equality are part of the key and therefore
   part of the invariant.

2. **Two teachers, one primary.** T1 is `evaluation.best_response` for player 0
   against the declared villain — the `passive` script is "call every bet" at
   the villain's only decision nodes. T1 is pure by construction (it returns one
   action per information set), so export loses nothing and agreement must be
   exact. T2 is `TabularCFR`'s average strategy: mixed, and therefore requiring a
   determinization rule that is a ruling, not a default. Invariant: the exported
   table is a function of the frozen teacher policy and nothing else; the policy
   object's digest is recorded in the artifact `source_id`. Neither teacher is
   an equilibrium claim; T1 is explicitly exploitative of the declared opponent.

3. **Tree-walk export over the teacher's own reachable set.** The export
   traverses the game from every deal in the joint range and emits an entry at
   each hero decision node reachable when hero follows the teacher and villain
   plays anything. Nodes hero would never reach under its own policy are not
   exported. Invariant: the unsupported set is exactly the complement of `H` at
   the root — set equality, checked, not a count. Where it must hold: export and
   agreement share the reachability definition, and the panel's `passive_default`
   count at the river must equal its off-pool deal count.

4. **Capacity is measured on wire bytes before solving.** A synthetic artifact
   with |H| placeholder entries at the declared prefix is encoded and its length
   compared to the cap; |H| is the largest pool that fits. If |H| < 1,081 the
   pool is chosen by a **strength-blind** declared rule — a seeded uniform
   subset — so the panel's hero distribution is not biased by hand quality. The
   smallest failing |H| is recorded whichever way it goes (criterion 3).

5. **Agreement is observed through the host.** For every hand in `H` and a
   seeded villain hand, one host session is played and the river decision's
   provider record must show `blueprint_hit` with the teacher's action; every
   pre-river decision must show `blueprint_default`. For hands outside `H` the
   river decision must show `blueprint_default`. Any other label anywhere in the
   hand fails the run. Invariant: the labels are the oracle for criteria 1–2;
   the enumeration is over `H` ∪ a declared off-pool sample, and the counts are
   reported separately (hits, teacher disagreements, unsupported).

6. **Sessions are composed, not generated.** `v0a_seeded_deals.deal_for_hand`
   supplies the twelve private cards under a recorded seed; the board is the
   declared teacher board; a deal whose private cards collide with the board is
   rejected by that rule alone, before play, and counted. Button 0, controlled
   seat 2, stacks `(s,)*6`, blinds 1/2, opponents as above. **One hand per
   session**, because `play_hand` derives each subsequent hand from carried
   stacks and a rotated button, and the bot must be the big blind for the root
   to exist. Sessions run in one worker that admits the host once — the
   repeated-verification bottleneck is already measured in this project; do not
   reintroduce it — with source verification at run boundaries only.

7. **Pairing and labels.** The pairing unit is the identical `(hero hand,
   villain hand, board)` triple played by each compared policy; with
   deterministic scripts and a deterministic table, each cell is a pure function
   of the triple and the policy, so all variance is sampling over private-card
   draws. The duplicate is the **hand swap**: the triple `(v, h, B)` is also
   played, both hands being in `H`. Two labels exclude an observation from the
   comparison and appear in the run record with counts: **prefix-diverged** (a
   policy acted pre-river so the root was never reached — `baseline-rules-v1`
   will do this) and **cutoff-fallback** (any `provider_late` or
   `provider_skipped_cutoff` selection; a clock-induced passive action is not a
   decision and is never pooled as one).

8. **Two controls with known answers.** First, calibration: hero's exact
   expected chips under T1 against the passive villain are computable with
   `expected_utilities` over the same joint range, per hand and pooled; the
   panel's empirical mean over in-pool deals must be consistent with that
   expectation. This tests pairing, settlement extraction, and chip arithmetic
   end to end where the truth is known, so the estimator can be trusted where
   it is not. Second, direction: T1 against the empty (passive) blueprint has a
   predicted sign, and so does T1 against T2 facing a passive villain. A panel
   that cannot recover either has failed regardless of its confidence interval.

9. **Uncertainty is over private-card draws, conditional on the board; boards
   are the clusters.** With one board, every observation shares the same public
   root and the result is a statement about that board only. Slice B therefore
   runs `k` declared boards, each with its own teacher and artifact, reports
   per-board and pooled, and treats boards as sampling clusters — with the
   honest caveat that small `k` gives weak cluster-robust inference. The loss
   budget is declared in chips per paired hand; because every outcome is
   bounded by `s`, the required number of deals for that budget follows
   directly and is written into the preregistration before the holdout run.

10. **One run, one record.** The panel tool calls `begin_run` once and
    `finish_run` once, writes `result.json` under `experiments/results/runs/`,
    and appends exactly one journal line; sessions are cells within the run, as
    in the blueprint workload harness. Development seeds and holdout seeds are
    disjoint and both recorded before the first run; the analysis plan is frozen
    in the shape of `v0a-paired-prereg-r001/preregistration.md`. At the end the
    `bot-validation` summary gains question, population, scope, limitations and
    review date. No per-hand or per-decision verification write exists.

The exported artifact plays through the existing `blueprint-v1` label. The
`PROVIDERS` tuple is closed and stays closed; no provider, codec version, or
key version changes.

## Controlled schedules and coverage limits

The coverage category is: every path from a frozen teacher policy to a
recorded chip outcome, plus every declared exclusion. Members are enumerated
from four frozen surfaces — `legal_river_continuation`, the codec, the
provider/runtime label sets, and the host's `select_opponent` — and mapped in a
compact coverage record before implementation.

Slice A tests: key identity through the host for a sample of `H` and off-pool
hands; set equality of the unsupported set; wire-byte capacity at the chosen
|H| and the recorded first failure; T1 purity and export determinism (two
exports of one frozen policy are byte-identical); a deliberately perturbed
prefix (one different stack) must produce zero hits — the discriminating
control that shows the identity check has teeth.

Slice B tests: seed disjointness; collision rejection counts; one-hand-session
composition; hand-swap bookkeeping; prefix-divergence and cutoff-fallback
labeling against constructed records; settlement-to-net-chips arithmetic
against the kernel's `net_returns`; and the exact-expectation reconciliation on
a small pool where `expected_utilities` and the host agree to the chip.

Limits: these are deterministic correctness schedules on a tiny-stack river
game against scripted opponents. They establish that the instrument reads
true where the truth is known. They do not establish poker strength, transfer
to deeper stacks or earlier streets, or behavior against adaptive opponents.

## Alternatives rejected

**Kuhn or `RiverHoldem` as the teacher game.** Neither has an image in
`BlueprintDecisionKey` space; `RiverHoldem` uses float chips and its own tree,
and embedding it would reinvent the kernel-backed continuation that exists.

**Extending the codec to distributions.** Forbidden by the brief, and it would
force a new provider label into a deliberately closed tuple. Determinization at
export is the cost of not doing this, and it is why T1 is primary.

**A Monte-Carlo teacher against five passive opponents.** Not exact; the exact
version is infeasible. The two-live-seat continuation is what makes exactness
cheap.

**A full-deck, multi-street policy.** At the retained 661-byte preflop row
size, 1,326 combinations at a single decision node already consume about
876 KB; a second decision node per hand exceeds the cap. The format cannot hold
one street of a full-deck policy with any betting history, which is itself a
finding for the roadmap's distillation row.

**Random boards.** The key includes the board, so no artifact can cover
randomly dealt boards; the probability of a hit is effectively zero. The board
must be declared, which is why criterion 4 needs amending.

**Modifying `v0a_seeded_deals.py`.** Forbidden; composing session documents
from its `deal_for_hand` output is sufficient and leaves it sealed.

**Seat rotation.** The continuation root exists only when the hero acts last on
the river, so the hero is always the big blind; criterion 5's "each seat
position" cannot be met in this game.

## What each element makes easy to get wrong

Constructing the base state by hand instead of replaying the scripted actions;
a hand-built state with the right pot and the wrong `uncalled_return` fields
produces zero hits with no error. Measuring capacity on canonical bytes.
Counting unreachable teacher nodes as disagreements, or counting pre-river
passive defaults as failures. Treating a `blueprint_default` on an off-pool
hand as a defect rather than the declared unsupported outcome. Argmax ties in a
float-valued T2. Pooling a `baseline-rules-v1` hand that raised preflop as if
it reached the river root. Pooling a clock-induced fallback as a passive
decision. Choosing `H` by strength. Adjusting `H`, `s`, or `k` after seeing a
holdout result. Reading the T1 calibration match as evidence that T1 is good
poker. One journal line per session instead of per run.

## Rulings — 2026-09-08

All six were put to the controller after the design pass and accepted as
proposed. The reasoning is kept so a later reader sees why each was necessary.

1. **Criterion 4 amended.** Hero and villain private cards are drawn from
   `v0a_seeded_deals.py` output under a recorded seed; the board is the declared
   teacher board; a deal whose private cards collide with the board is rejected
   by that rule alone, before play, and counted. Without this the panel would
   measure the passive default on every deal, since the key includes the board.

2. **Criterion 5 amended.** Every compared policy plays the identical
   `(hero hand, villain hand, board)` triple; the hand-swap triple is also
   played; the matched pair is the unit of analysis. Seat rotation is
   unavailable because the root exists only with the hero in the big blind.

3. **Criterion 6 amended; `k = 4`.** Boards are the sampling clusters; a
   single-board result is conditional on that board; Slice B runs four declared
   boards and reports per-board and pooled, stating the weakness of
   few-cluster inference rather than papering over it.

4. **T1 is the primary teacher.** Exact best response to the declared opponent,
   pure by construction, exports losslessly, and agreement must be exact. T2
   (CFR average strategy) is secondary. T2's determinization rule — argmax with
   a declared canonical-order tie-break, or seeded realization — is **still
   open** by the ruling's own terms and must be declared in the preregistration
   before any T2 export; the recommendation is argmax with tie-break, because
   seeded realization makes per-key agreement ill-defined. T1 is explicitly
   exploitative of the declared opponent and is not an equilibrium claim.

5. **Stack depth `s = 4`** for both slices; `s = 6` is a declared later
   variant, not part of this lane's acceptance.

6. **Placement.** Deal composition and pairing arithmetic live in the library
   with a test; the worker and orchestration are a `tools/` entry. The helper
   may import `deal_for_hand` from the sealed dealer tool; the dealer itself is
   unchanged.

## Ties, barriers, and blast radius

This lane is the outcome variable for roadmap items 3, 5, 6 and 7 and the
dependency edge that keeps item 2 behind item 3. It moves
`legal_river_continuation` from a "small-game semantic control" to a capability
with a caller, which is what the working rules require of retained library
code. It produces the first artifact in the repository that is a solved policy
rather than a fixture — and, unavoidably, the first hard number on what the
artifact format can hold, which the roadmap's distillation row currently lacks.

It assumes the sealed codec, provider contract, host, and seeded dealer, and
forecloses nothing: a codec v2, a distribution-valued provider, or a deeper
game all remain open and are informed by what this measures.

Barriers: the capacity measurement may force |H| below full coverage;
per-session host cost bounds panel size (measure it; the 12-trial wrapper ran
in 49 seconds after bounded reads); T2 at full `H` traverses about a million
deals per iteration in pure Python and may need a smaller `H` or be deferred;
native trace-handle checks have previously failed under the restricted Windows
sandbox and passed outside it. Cheap to revise: preregistration parameters,
`H`, `s`, `k`, disposable diagnostics. Permanent once journaled: the exported
artifact bytes, the panel results, and the family-summary claims built on them.

Adoption follows the brief's stop rule: two review rounds per slice, then the
controller. Kill criteria stand as written there; the capacity measurement in
mechanism 4 is the first place the format-fit kill can fire, and it fires
before any solving.

## Not designed here

Multi-street or pre-river policies; any provider label, codec version, or key
version change; opponent modeling or adaptive opponents; training loops; GPU
work; live-clock measurement beyond recording what the host already records;
bunching or folded-range inference; any claim about stacks deeper than the
declared `s`.

## Base blobs

| Path | Git blob at `b378104c` |
| --- | --- |
| `tests/cases.json` | `53497f56ab0ac4b05c4dba7ca21e022f5bf62813` |
| `src/pontius/legal_river_continuation.py` | `dc82aa748a195391143a09958e4e0dade827c45b` |
| `src/pontius/blueprint_artifact/codec.py` | `c8a21b91cc4d285ff6e82b1f1b187c4e178bb5ce` |
| `tools/v0a_seeded_deals.py` | `2963004e38c6e66f76ae9ce3bd474063eee870fe` |

`tests/cases.json` is the one registration surface this lane changes. The other
three must be byte-identical to these blobs at every freeze.
