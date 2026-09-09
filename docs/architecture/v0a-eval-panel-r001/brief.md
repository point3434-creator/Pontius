# Trained-policy deployment bridge and fresh-deal evaluation panel

The research roadmap ranks a terminal semantic differential first on scientific
upside, and keeps a practical bot track alongside it. This brief bounds that
practical track. Its purpose is narrow and prior to the ranked sequence: Pontius
cannot presently measure whether any change improves play. The retained paired
comparison ran 48 trials over **two deals** with an untrained control that
emitted 64 passive defaults, and its own summary states that no general policy
ranking follows. Roadmap items 3, 5, 6 and 7 each end in "does this change
worthwhile decisions" and would otherwise each have to invent that measurement
separately.

This lane builds the instrument once. It does not attempt to win at poker.

## Change and invariants

Two slices, reviewed and frozen separately.

**Slice A — export bridge.** Solve an already exactly evaluable abstraction — the
kernel-backed heads-up river continuation in `legal_river_continuation`, at the
declared checked-to prefix and stack depth 4 — with the retained solver, export
the resulting policy through the existing blueprint codec, load it through the
existing blueprint lookup path and, separately, the `BlueprintProvider` boundary,
and compare the emitted decisions against the teacher's own policy over a
declared enumeration of the teacher's reachable information sets. Unsupported
states and fallback are counted and reported, never silently absorbed.

**Slice B — evaluation panel.** Play declared policies against declared opponents
on seeded deals, with development and holdout seeds fixed before any run, and
report a paired result with uncertainty that respects shared deals.

The reusable parts — policy-to-artifact export, the agreement enumeration, the
pairing and clustering arithmetic — belong in the library with a test and a
caller. The panel entry point belongs in `tools/`. The run that answers the
research question belongs in `experiments/` and is never imported by the library.
Do not generalize this into a training framework, a tournament runner, or a
policy-selection service.

Tier C. The protected invariant is that **this lane produces the project's
outcome oracle**: every later claim that a solver change, an action menu, a leaf
model or a bunching method improved play will be expressed in this instrument's
units and will inherit its defects. A test oracle can be Tier C regardless of
size or a "test-only" label. Two independent cold reviews per slice.

## Exact implementation surface

Base: commit `b378104c` on `master`. Branch `codex/v0a-eval-panel`, worktree
`D:/Pontius-worktrees/v0a-eval-panel`.

May change: new library modules for export and panel arithmetic; new
`tools/v0a_eval_panel.py`; new tests; `tests/cases.json`; one dated
`experiments/` script per slice; the `bot-validation` family summary at the end.

Must not change: `src/pontius/blueprint_artifact/codec.py` and the artifact
format; the `decision_provider` contract; `src/pontius/legal_river_continuation.py`,
which is the teacher game; the sealed evaluation runners
`tools/v0a_evaluation{,_v2,_v3}.py`; `tools/v0a_seeded_deals.py`; historical
results, ADRs and retained run outputs. If the abstraction does not fit the
existing format, that is a finding, not a licence to widen the format.

Seams: codec writer/reader; provider preparation and lookup; table host/session
parent-child execution; the 14,000 ms work and 15,000 ms action boundaries;
seeded-deal generation as fixture source; Git source admission at run boundaries;
one journal append per run. Verification stays at run boundaries — no per-deal,
per-hand or per-decision seal, admission or verification write.

Size budget: slice A at most 600 production, 400 test lines; slice B at most 500
production, 350 test lines; generated inventory and profile data excluded. Over
budget returns to the controller rather than being sliced further in flight.

## Acceptance and ground truth

Ground truth is the exact reduced game and its retained independent evaluators:
`evaluation.best_response` against the declared opponent for the primary teacher
(T1, pure by construction), `TabularCFR`'s average strategy for the secondary
teacher (T2), `expected_utilities`/`evaluate_profile` for values, and the
teacher's own policy for decision agreement. T1 is computed per hero hand by
exact enumeration in new caller code and verified against `best_response` on
the sealed singleton-hero game for a declared sample, because a monolithic game
over the full range is quadratic in the sealed implementation. The teacher's
own policy as agreement oracle is stated plainly because it is the weak point:
agreement between an exported artifact and the teacher that produced it tests the
export path only. It does not test whether the teacher is good. **A long-budget
teacher with exact terminal utilities is not thereby an equilibrium teacher**,
and no acceptance criterion below treats it as one.

Numbered, individually testable:

1. Every information set the teacher defines either resolves through the
   blueprint lookup path to the teacher's action, or is reported unsupported.
   The observable, for a completed hand only, is the runtime's v1
   `DecisionRecord` read from the child frame stream the session retains
   (`selection_reason` of `table_hit` or `passive_default`, with
   `selected_action`), cross-checked against an independent `action_for` on the
   replayed key, since `blueprint-v1` host mode neither instantiates the
   provider class nor recomputes the lookup; the `BlueprintProvider` public
   boundary is checked separately and directly. No third outcome exists on
   either path.
2. Decision agreement is reported over a declared enumeration as hits,
   disagreements, unsupported, and excluded, each counted separately. Excluded
   is decided first and at the hand-outcome boundary — a session hand entry or
   host `hand_result` reporting failure or an incomplete hand, or an
   `event_result` with `status = failed` — because such a hand may carry no
   decision record at all; only a completed, settled hand is classified by its
   river decision record.
3. The artifact either fits the codec's stated limit or the exact overflow point
   is recorded. Capacity is representation-specific — the retained corpus fit 883
   entries in 1,047,220 bytes with keys at 95.7%, and 883 is not a universal
   entry limit.
4. Hero and villain private cards are drawn from `tools/v0a_seeded_deals.py`
   output under a recorded seed; the board is the declared teacher board; a
   deal whose private cards collide with the board is rejected by that rule
   alone, before play, and counted. Development and holdout seeds are disjoint
   and both recorded before the first run.
5. Every compared policy plays the identical `(hero hand, villain hand, board)`
   triple, and the hand-swap triple is also played, whatever the pool: an
   orientation whose hero is off-pool is a passive-default observation of the
   deployed policy, reported separately, never a rejection. The matched unit —
   the unordered hand pair on its board, both orientations, all policies — is
   the unit of analysis. A cell lost to cutoff or failure excludes its whole
   unit; a cell whose policy diverged before the river is labeled, not
   excluded, since its settlement is that policy's outcome. Seat rotation is
   unavailable: the teacher game's root exists only with the hero in the big
   blind.
6. Boards are fixed strata, equally weighted. The estimand is the mean paired
   difference over the four declared boards and is conditional on them; a
   single-board result says nothing about other boards, and more deals reduce
   only within-board uncertainty. Slice B reports per-board and pooled.
7. A loss budget is declared before the holdout run. A result inside its interval
   is reported **inconclusive**, never equivalent. Any matched unit lost to
   cutoff or failure withholds the full-population result for its board and any
   pooled result containing it; counts, survivors' statistics, and worst-case
   missing-unit bounds over the planned denominator are reported instead, and
   only re-running the lost units to completion restores the claim.
8. One journal line per run; the `bot-validation` summary updated with question,
   population, measurement scope, limitations and review date.

Criteria 4–6 were amended on 2026-09-08 by controller ruling after the design
pass showed the originals unsatisfiable against the actual key space; criteria
1, 2, 5 and 6 were refined the same day after the r001 cold review, and 1, 2, 5
and 7 again after r002; the [design](design.md) records why and what was
accepted.

Before the first holdout run, the analysis plan is frozen as a preregistration in
the shape of `docs/architecture/v0a-paired-prereg-r001/`: seeds, splits,
clustering, the pairing rule, the loss budget, and the decision the result will
support. Tuning against an opened holdout result voids the run.

Run the new suites and the affected unchanged evaluation, provider, codec and
inventory checks on CPython 3.14.6 only, `-B -P`, scrubbed environments,
absolute native Git. Preserve raw evidence and exact candidate identity.

## Dependencies, stop rule, and what this cannot claim

Waiting on this lane: roadmap items 3, 5, 6 and 7, each of which needs a strength
measurement it does not currently have. **Not waiting:** roadmap item 1, the
terminal semantic differential, which is independent and should proceed in
parallel; item 2 should not start until item 3 can be measured, which is what
this lane enables.

Stop rule. *Adoption* when the numbered criteria hold on the holdout under the
frozen plan. *One bounded correction* for a defect in export or panel mechanics
with the measurement design intact. *Redesign* if decision agreement cannot be
defined without teacher and provider sharing an assumption — an oracle that
inherits the implementation's assumption cannot test it. *Kill* on either of two
conditions, declared here rather than after the second failure: if no exactly
evaluable abstraction fits the existing artifact format, the bridge question is
answered negatively and the lane stops instead of widening the format; and if the
declared loss budget cannot be met at a feasible sample size, report the required
number of deals and stop rather than run an underpowered panel.

Budget: at most two review rounds per slice before returning to the controller.

Forbidden claims. This lane does not establish full-game or multiway poker
strength; does not establish that the teacher is an equilibrium; does not measure
live-clock behavior beyond recording it; does not rank general playing strength,
since a panel of seeded deals against declared opponents is not a population of
opponents anyone will actually face; and does not transfer any reduced-game result
to full hold'em. Passing the new suites is not a benchmark result, a GPU result,
or a strength result. What it produces is an instrument and its stated precision —
which the project currently lacks, and which every ranked experiment downstream
of it will be read through.
