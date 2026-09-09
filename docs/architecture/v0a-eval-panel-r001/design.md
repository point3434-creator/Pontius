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
runtime's own v1 `DecisionRecord`, which is what the `blueprint-v1` host mode
actually emits: `selection_reason` is exactly `table_hit` or `passive_default`,
alongside `selected_action`, `timing`, `failure_reason`, and delivery status.
The host does **not** instantiate `BlueprintProvider` in this mode (`runtime.py`
sets `_provider = None` for `blueprint-v1`), so the provider's `blueprint_hit`
labels are never produced there. The agreement test drives the actual host and
reads the v1 record; a separate direct check exercises the `BlueprintProvider`
public boundary against the frozen teacher. Neither is inferred from the other.

3 (fits or the overflow point is recorded) — observed on the encoded artifact's
**wire bytes**, because that is what the host's 1,048,576-byte input cap
measures. The retained 883-entry corpus is the warning: 71,939 canonical bytes,
1,047,220 wire bytes. A capacity check on canonical bytes would pass a file the
host refuses.

4–7 (seeds, pairing, strata, loss budget) — observed in a frozen
preregistration and in the panel's run record, which carries every seed, every
collision rejection, and every excluded unit with its reason.

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
  `s − 2`. The fixture's `s = 6` gives root actions (check, 2, 3, 4) and three
  hero decision histories per hand (root, response to 2→4, response to 3→4).
  At `s = 4` the derivation is static from `_raise_bounds`: current bet 0, last
  full raise 2, hero maximum `0 + 2 = 2`, so minimum and maximum raise-to are
  both 2 (all-in); a check ends the river, and after a bet the hero has no
  chips and the villain can only fold or call. Exactly **one** hero decision
  node per hand. This is a source derivation, not a test result.
- **Hero pool `H`** ⊆ the 1,081 hands compatible with the board. Villain is
  uniform over the 990 hands compatible with board and hero hand. That is also
  the panel's villain distribution given the hero's cards *after marginalizing*
  the four folders' cards — collision rejection is symmetric and every
  compatible `(h, v)` has the same number of folder completions. Conditional on
  the folders' realized cards it would be 666 hands; nothing here conditions on
  them.

Capacity arithmetic: entries ≈ |H| × (hero nodes per hand). At roughly one
kilobyte per wire row — eleven history records plus the six-vectors — 1,081
entries at `s = 4` land within a few percent of the cap on either side. That is
a measurement, made first, and it decides |H|. The placeholder rows use
`check`/`null` actions, which are three wire bytes longer than `raise`/`2`
under the compact codec, so the probe is conservative; the final artifact is
measured again. At `s = 6`, three histories per hand bound |H| near 350, about
a third of coverage. The design recommends `s = 4` for both slices: maximal
coverage, one decision per hand, a per-hand teacher computation small enough to
preflight honestly (mechanism 2), and a panel in which almost every seeded deal
is a table hit. It is the smallest bridge that is not vacuous; richer sizing is
a later variant, not a Slice A ambition.

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

2. **Two teachers, one primary; the primary is computed per hero hand.** T1 is
   the exact best response for player 0 against the declared villain — the
   `passive` script is "call every bet" at the villain's only decision nodes.
   It is pure (one action per information set; `best_response` breaks exact
   ties by first legal-action order), so export loses nothing and agreement
   must be exact. **How it is computed matters.** The sealed game validates
   deal membership by rebuilding `dict(self.game.deals)` at every chance and
   dealt-state check, so one monolithic game over the full range costs at
   least `2·N²` row insertions with `N = 1,081 × 990 = 1,070,190`. T1 and the
   calibration expectation are therefore computed **per hero hand** in new
   caller code: for each `h`, enumerate the 990 compatible villain hands,
   settle check and bet through the kernel, and take the best action under the
   declared villain law. The partition is exact because the villain's policy is
   fixed, so hero information sets do not interact at `s = 4`; it does **not**
   extend to T2, whose villain strategy couples hero hands. Invariant: for
   every hand in a declared sample, the per-hand action equals
   `evaluation.best_response` on the sealed singleton-hero game `{h} × 990`,
   which remains the ground truth. A cost preflight on a small pool, with a
   stop condition, precedes any full-pool computation. T2 is `TabularCFR`'s
   average strategy: mixed, deferred, and requiring a determinization rule
   declared before export. Invariant for both: the exported table is a
   function of the frozen teacher policy and nothing else; the policy digest is
   recorded in the artifact `source_id`. Neither teacher is an equilibrium
   claim; T1 is explicitly exploitative of the declared opponent.

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

5. **Agreement is observed through the host's v1 record, and separately at
   the provider boundary.** For every hand in `H` and a seeded villain hand,
   one host session is played in `blueprint-v1` mode. The river decision's
   `DecisionRecord` must carry `selection_reason = table_hit` and
   `selected_action` equal to the teacher's action; every pre-river decision
   must carry `passive_default`; for hands outside `H` the river decision must
   carry `passive_default`. Exhaustive mapping: `table_hit` with the teacher's
   action → **hit**; `table_hit` with another action → **disagreement** (fails
   the run); `passive_default` off-pool at the river → **unsupported**;
   `passive_default` in-pool at the river → **disagreement**; any record whose
   `timing.status` is interrupted, whose `failure_reason` is non-null, or whose
   delivery status is not accepted → **excluded**, counted, never pooled. There
   is no other record shape on this path. Separately, the `BlueprintProvider`
   public `propose` boundary is driven directly with constructed observations
   for the same hands, and its `blueprint_hit`/`blueprint_default` proposal
   reasons are checked against the same expectations; the coverage record
   states which case proves runtime behavior and which proves provider
   behavior. Invariant: the v1 record is the oracle for criteria 1–2; counts
   are reported as hits, disagreements, unsupported, excluded.

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

7. **One inclusion law, pairing, and labels.** Acquisition rejects a deal only
   for a private-card/board collision — nothing else, and never on hand
   membership in `H`. Every accepted deal yields one **matched unit**: the
   unordered pair `{h, v}` on board `B`, played in both orientations
   (`(h, v, B)` and the hand-swap `(v, h, B)`) by every compared policy. An
   orientation whose hero is off-pool is a legitimate `passive_default` cell of
   the deployed policy — reported separately, never rejected, never silently
   pooled as a teacher decision. The **deployed policy** is defined as the
   table on `H` plus the passive default off `H`; every comparison and every
   expectation in mechanism 8 is about that policy, not about T1 restricted to
   hits. With deterministic scripts and a deterministic table, each cell is a
   pure function of the triple and the policy, so all variance is sampling over
   private-card draws. Two labels exclude a cell, and an excluded cell excludes
   its **whole unit across all policies and both orientations**, with counts in
   the run record: **prefix-diverged** (a policy acted pre-river so the root
   was never reached — `baseline-rules-v1` will do this) and **cutoff or
   failure** (the v1 record's `timing.status` interrupted, `failure_reason`
   non-null, or delivery not accepted; a clock-induced passive action is not a
   decision). Board order is declared ascending and used identically in export
   and session composition, since the key copies the card view's board order.

8. **Two controls with known answers.** First, calibration: the exact expected
   net chips of the **deployed policy** — T1 on `H`, passive default off `H` —
   against the passive villain, over the full accepted-deal population (hero
   uniform over 1,081, villain uniform over 990), computed per hero hand by the
   same enumeration as mechanism 2 and cross-checked on small pools against
   `expected_utilities` on the sealed game. The panel's empirical mean over all
   accepted cells, hits and defaults alike, must be consistent with that
   expectation within the declared tolerance. This tests acquisition, pairing,
   settlement extraction, and chip arithmetic end to end where the truth is
   known, so the estimator can be trusted where it is not. Second, direction:
   T1 **weakly dominates** the empty (passive) blueprint under this population,
   and the exact expected gap is computed and declared before the run; a gap
   of exactly zero is possible (a board that is itself a royal flush ties every
   deal and is the all-zero control) and is a valid outcome, not a failure.
   The finite-sample decision rule for the direction check is stated in the
   preregistration; a bare observed sign is not an acceptance gate.

9. **Estimand, strata, interval, and sample size.** The estimand is the mean
   paired difference in hero net chips between two deployed policies, averaged
   with **equal weights over the four declared boards** — a finite target,
   conditional on those boards. Boards are fixed strata, not a sample from a
   population of boards; nothing in this lane supports a claim about boards
   outside the four, and additional deals reduce only within-board
   uncertainty. Within a board, the observation is the matched unit
   (mechanism 7): the sum over both orientations of the per-orientation
   difference, so each unit's value lies in `[−4s, 4s]`; units are independent
   draws under the dealer model given the board. Per-board intervals come from
   those units; the pooled interval combines the four as strata with equal
   weights. The loss budget is declared in chips per unit together with the
   confidence level; the pre-registered sample-size floor follows from the
   bounded range by a Hoeffding-type bound, and the preregistration may
   tighten it with a declared variance estimate but may not loosen it after
   any holdout observation. Exclusions (mechanism 7) remove whole units and
   are counted against the floor. The same definitions govern calibration,
   per-board output, pooling, and the direction control.

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
from the frozen surfaces the key identity and the oracle actually depend on —
not four files but the inventory: `legal_river_continuation`, the codec,
`immutable_blueprint` (key constructor and passive default), `no_limit_betting`
(kernel), `holdem_cards` (card view), `blueprint_preparation.lookup`,
`v0a/runtime` and `v0a/model` (the v1 `DecisionRecord`), the
`decision_provider` model/providers/selection/codec, `tools/v0a_event_adapter`,
`tools/v0a_table_host` (`select_opponent`, `TableInput`, settlement),
`tools/v0a_table_session`, `tools/v0a_seeded_deals`, and `evaluation`. Their
base blobs are pinned in the round's coverage record. The freeze's whole-tree
diff against base is the identity guard; the inventory is the semantic one.

Slice A tests: key identity through the host for a sample of `H` and off-pool
hands, read from the v1 record; the direct `BlueprintProvider` boundary check
for the same hands; set equality of the unsupported set; wire-byte capacity at
the chosen |H| with the conservative placeholder and the final-artifact
recheck; T1 purity and export determinism (two exports of one frozen policy
are byte-identical); the per-hand T1 action equal to `best_response` on the
sealed singleton-hero game for a declared sample, including a hand whose check
and bet values tie; the cost preflight's recorded numbers; a deliberately
perturbed prefix (one different stack) must produce zero hits — the
discriminating control that shows the identity check has teeth; and a board
supplied in non-ascending order must be refused or canonicalized identically
in export and composition.

Slice B tests: seed disjointness; collision rejection counts and the absence of
any membership-based rejection; an accepted deal with `h ∈ H`, `v ∉ H` whose
swap is played and lands as a `passive_default` cell; a small unequal-degree
pool whose expected weights are derived independently and matched; one-hand
session composition with ascending board; whole-unit exclusion when one cell is
excluded; prefix-divergence and cutoff/failure labeling against constructed v1
records; settlement-to-net-chips arithmetic against the kernel's
`net_returns`; the exact-expectation reconciliation of the deployed policy on
a small pool where the per-hand enumeration, `expected_utilities` on the sealed
game, and the host agree to the chip; and the equal-weight stratified pooling
arithmetic against a hand-computed example.

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

**Random boards.** The key includes the board, and an artifact under the cap
holds about one board's worth of river entries, so the hit probability on a
randomly dealt board is `≈ 1/C(52,5)` per covered board — small enough that
the panel would measure the passive default. The board must be declared, which
is why criterion 4 needed amending.

**Modifying `v0a_seeded_deals.py`.** Forbidden; composing session documents
from its `deal_for_hand` output is sufficient and leaves it sealed.

**Seat rotation.** The continuation root exists only when the hero acts last on
the river, so the hero is always the big blind; criterion 5's "each seat
position" cannot be met in this game.

## What each element makes easy to get wrong

Constructing the base state by hand instead of replaying the scripted actions;
a hand-built state with the right pot and the wrong `uncalled_return` fields
produces zero hits with no error. Looking for provider labels in `blueprint-v1`
host output, where the provider is never instantiated — r001 did exactly this.
Measuring capacity on canonical bytes. Building one sealed game over the full
range and discovering the quadratic membership check by waiting. Adding a
both-in-`H` filter to make the swap tidy, which reweights hero hands by their
compatible-degree and invalidates the calibration — r001 did this too.
Counting unreachable teacher nodes as disagreements, or counting pre-river
passive defaults as failures. Treating a `passive_default` on an off-pool hand
as a defect rather than the declared unsupported outcome. Argmax ties in a
float-valued T2. Pooling a `baseline-rules-v1` hand that raised preflop as if
it reached the river root. Pooling a clock-induced fallback as a passive
decision. Sorting the board in one place and not the other. Choosing `H` by
strength. Adjusting `H`, `s`, or `k` after seeing a holdout result. Reading
the T1 calibration match as evidence that T1 is good poker. Treating an
observed sign as the direction gate. One journal line per session instead of
per run.

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

**Refinements after the r001 cold review (2026-09-08), flagged in the r001
disposition for the controller.** Ruling 3's "sampling clusters" is stated here
as *fixed strata, conditional on the four declared boards*: with four declared
boards there is no board sampling frame, and "cluster-robust" would imply one.
Substance unchanged. Rulings 1–2's inclusion law is made explicit in
mechanism 7 — collision rejection only, both orientations always played, an
off-pool hero cell is a passive-default observation — which removes a
both-in-`H` filter the r001 text had implied, and adds none.

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
in 49 seconds after bounded reads); the sealed game's per-check
`dict(self.game.deals)` rebuild makes any monolithic full-range game — T1,
calibration, or T2 — quadratic in the deal count, which is why mechanism 2
partitions T1 per hero hand and why T2 stays deferred; the per-hand
enumeration is 1,081 × 990 kernel settlements and its cost is preflighted, not
assumed; native trace-handle checks have previously failed under the
restricted Windows sandbox and passed outside it. Cheap to revise: preregistration parameters,
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
three must be byte-identical to these blobs at every freeze. They are the
files this lane *names*; they are not the full set the key identity and the
oracle depend on. That inventory, with base blobs, lives in the round's
coverage record (see "Controlled schedules"), and the whole-tree diff against
base at each freeze is what guarantees nothing else moved.
