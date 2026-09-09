# Slice A design: capacity, per-hand teacher and independent agreement

Companion to brief.md. The accepted lane design remains authoritative at
../v0a-eval-panel-r001/design.md. This document specifies the implementation
boundaries needed for Slice A, including the r003 disposition's carried advice.
It contains no implementation or executed measurements.

## 1. Inputs, phases and shared identity

One explicit run plan fixes the board, replayed prefix, complete ordered hand
universe, pool-selection seed and resulting permutation, finite development
seed/index bank, reference sample, runtime order, resource limits and requested
phase. Validate those inputs before launching work. Each dealer seed is paired
with an index in 0..15. Development and reserved holdout banks must be disjoint;
this lane never opens Slice B holdout results to choose H, a board or a budget.

The plan is a bounded input to the existing tools entry point, not a service or
new lifecycle framework. Capacity, preflight and agreement are explicit phases
of one Slice A implementation. A preflight invocation always exits after its
report. Export/agreement require a later invocation whose plan binds the measured
preflight and the controller's chosen resource envelope. No phase silently
continues into more expensive work because an earlier step succeeded.

The initial review freezes these mechanisms. Concrete execution plans are frozen
with their code candidate before invocation; measured cost acceptance is a later
recorded decision, not an invented numeric performance gate in this document.
Missing mandatory plan inputs cause refusal, never implicit defaults.

Keep distinct identities for the plan, canonical teacher policy, codec canonical
source and encoded wire artifact. Use the existing codec without adding fields.
The teacher identity covers board, prefix, opponent law, H and ordered action
rows, with a declared deterministic serialization. Export source_id is the
fixed-width ASCII string t1: followed by that policy's 64 lowercase hex digits.
The capacity placeholder uses the same source_id width. Actual wire bytes are
retained; a canonical digest does not stand in for their size or identity.

## 2. Capacity without teacher computation

Replay the prefix using public betting operations, including the actual history,
street advances, contributions and returned-chip state. Build card views through
the existing card model. Obtain each export key from BlueprintDecisionKey.from_state.
Never hand-fill a key or construct the root by assigning dataclass fields.

Enumerate the 1,081 compatible hero hands. Freeze a seeded, strength-blind
permutation before evaluation, keeping its actual ordered contents in the plan.
H is a prefix of this permutation. Every candidate prefix has CHECK/null actions
and the fixed-width placeholder source_id. encode_blueprint is the only byte
counter. No teacher, host or solver is needed for this measurement.

Positive row lengths and fixed metadata make wire length monotone in this nested
prefix family. Search that family and retain the boundary encodings/sizes:
largest fitting k and k+1 when k is below 1,081. If all hands fit, state that
there is no overflow within the domain. If k=0, retain the one-row failure and
stop. A one-row failure is not a universal theorem about other games/codecs.

The bound is conservative for this action alphabet: CHECK/null costs three more
wire bytes per row than raise/2. It is not the maximum solved-policy capacity
across all possible pools. Solving does not reopen the pool-selection rule.
Encode and decode the final teacher artifact, measure it again and refuse a
full agreement launch if it exceeds the cap or changes the expected key set.

Falsifiers: canonical size passes but wire size fails; source_id grows after the
probe; duplicate keys manufacture an overflow row; final H differs from the
frozen prefix; a solved artifact exceeds its declared measured bound.

## 3. Per-hand T1 and bounded cost preflight

At s=4, construct two terminal betting outcomes through the real kernel: hero
CHECK, and hero raise_to(2) followed by the villain's CALL. Enumerate each h's
990 compatible villain hands, rank with river.evaluate_seven, and settle both
outcomes through the existing kernel. Accumulate integer net-chip totals and
the common denominator; maximize totals, with CHECK first on exact equality.
This avoids an arithmetic tie being decided by an arbitrary floating epsilon.
Do not replace kernel settlement with a private win/loss payoff formula.

The production helper handles one h at a time. It never builds the joint
1,081 x 990 sealed game, and never transfers this decomposition to T2. The
invariant is one independent hero root under a fixed villain response, not a
general property of poker information sets. The original continuation and
evaluation modules remain unchanged.

The reference uses LegalHeadsUpRiverContinuation with exactly one hero hand
and all 990 compatible villains, equal input weights, the same replayed root
and board. Enumerate villain information keys and assign CALL probability one;
do not rely on a missing-policy fallback. Supply exactly 990 distinct deals,
each with raw weight 1.0; do not supply already-normalized approximations. Assert
one hero root with actions CHECK and raise_to(2), terminal integer utility of
magnitude at most 4, and no additional chance node. A changed domain refuses
this reference rule rather than inheriting its error allowance.

Evaluate both forced hero actions through evaluation.expected_utilities on that
same singleton game, combining an explicit deterministic hero policy with the
explicit CALL villain policy. Retain player 0 values R_check and R_bet. Also
invoke evaluation.best_response for player 0 and retain its returned value and
selected map. These are separate calls: best_response exposes no per-action
value table. Neither reference path may use production's hand totals or rank
counts as its expected values. The sealed evaluator and kernel stay unchanged.

Use n=990 and the exact rational bound E=2^-40 chips for each returned value.
Here is its domain-specific derivation. Unit input weights, their sums through
990, terminal integers, deterministic policy probabilities and zero branches
are exact binary64 values. Normalization rounds 1/n once. Multiplication by the
nonzero terminal values +/-2 or +/-4 is power-of-two scaling and exact; zero
and probability-one operations are exact. expected_utilities accumulates 990
weighted values with explicit +=. With u=2^-53 and gamma_k=k*u/(1-k*u), its
absolute error is at most 4*(u+(1+u)*gamma_989), less than 4*gamma_1000 and
less than E. The returned best_response value uses expected_utilities too.
No underflow/overflow occurs in this domain. This bound does not assume the
implementation of Python's built-in sum or use it as the tie oracle. At code
verification, check these domain assumptions on both supported interpreters;
an unsupported numeric environment cannot pass by borrowing this bound.

Validate before choosing an action. Treat each finite returned float as its
exact dyadic rational (as_integer_ratio), and perform the following comparisons
using integer/rational arithmetic, without a second rounded tolerance test:

- For each action a, require exactly one integer J_a in [-4*n,4*n] satisfying
  abs(R_a - J_a/n) <= E. Zero or multiple candidates fail the reference check.
  Uniqueness follows from 2*E < 1/n. Require J_a == production_total_a.
- Require production's action to maximize those validated integer totals, with
  CHECK on exact equality. Thus production cannot certify its own false tie.
- Require a finite best_response value within E of max(J_check,J_bet)/n, and a
  selected map containing exactly the one hero key with a legal root action.
- If J_check != J_bet, require exact reference/production action equality.
  The smallest lattice gap 1/n exceeds 2*E; no numerical tie is introduced.
- If J_check == J_bet, require production/export CHECK. Either legal reference
  action is acceptable after the preceding independent value checks. Retain its
  raw selected action and label any difference as reference tie-breaking.
  Equality of reconstructed totals implies abs(R_check-R_bet) <= 2*E.

Every failed predicate is a reference disagreement and stops preflight. NaN,
infinity, invalid map or unmet numeric/domain assumptions are never ties.
Record both production totals, both forced-action values, the raw reference map
and value, the bound and the comparison classification in the existing result.

Retain the all-zero royal-board control. Planned numeric-boundary controls also
cover nonzero cancellation with positive, negative and zero residuals, a false
production tie, a changed total, and both signs of the smallest nonzero lattice
gap. Wrong non-tie actions must fail even when their reference values are close.
Arithmetic fixtures exercise the comparison boundary and are labeled as such;
they do not impersonate a sealed poker game. Real sealed checks use the declared
development sample on both interpreters. During an authorized full-H solve,
record the first exact tie with nonzero per-deal returns and add its singleton
reference check. If none exists, state absence only over the completed census
of H; if that census was not completed, report the tie search as unverified.
The preflight sample's lack of a tie cannot establish absence across H or boards.

The cost preflight separately records production enumeration and reference
construction/evaluation for As Ad, Kh Kd, Td 8d and 3c 4d on the development
board. The royal-spade/2c 3d control must return CHECK at equal zero totals.
Host agreement later must include both action categories when present in H;
their presence is observed, not presumed from this fixed sample.

Attribute reference construction, both forced-action evaluations, best_response
and numerical comparison separately; the added calls are not hidden from cost.
Record elapsed and process CPU time, number of hero/villain/action evaluations,
runtime identity, cache state/order and observed process memory. Distinguish a
platform memory peak from traced allocation and mark unavailable metrics as such.
Cold and warm repetitions are labeled; a reference run must not secretly warm
the production measurement. Estimate full-H work from the measurements, showing
the observed spread, initialization costs and cache assumptions. It is an estimate,
not a feasibility proof or an upper bound on elapsed time.

The worker has finite launch-time resource limits. Interruption/refusal preserves
completed observations and a failure reason but cannot pass preflight. A full-H
invocation is permitted only after the measured report supports the separately
recorded resource decision. No unmeasured seconds/memory target is smuggled into
acceptance, and no resource exhaustion is relabeled a mathematical failure.

Falsifiers: default villain distribution instead of CALL; shared full-range
dictionary construction; disagreement with the singleton reference; wrong tie
action; missing costs; warm-only numbers presented as cold; automatic full solve.

## 4. Export membership and actual host witnesses

At the declared root there is exactly one reachable hero information set per h.
Traverse the fixed s=4 legal shape to establish that fact; do not walk a
monolithic chance tree simply to emit repeated copies of the same key.
Emit one entry per h in H and require full key-set equality after decoding.
Enumerate the complement separately with PreparedBlueprint and the public
BlueprintProvider.propose boundary. Build real DecisionObservation values;
checking internal lookup results alone does not exercise the provider contract.

Full host agreement requires a witness for each h in H. Scan the frozen finite
development seed/index bank using the unchanged deal_for_hand and collision-only
board rejection. Keep all twelve cards intact. Record the first accepted draw
whose controlled hand supplies each required h, including its villain and four
folder hands. Never overwrite a dealt hand to force an in-pool key. Record
unused accepted draws and collisions sufficiently to reproduce witness choice.
If the bank does not cover H, the agreement schedule is incomplete and cannot
pass; do not shrink H or silently add seeds after observing the run.

Before freezing that bank, record its sizing rationale and assumptions, including
dependence between seed/index draws. An IID approximation may use a declared
failure probability and a union bound over missing required hands, but is only
a planning estimate unless the actual draw law justifies it. Expected coverage
is not guaranteed coverage, and a smaller bank is not automatically incomplete.
Acceptance depends on the actual complete witness census, regardless of sizing.

This witness selection answers a finite correctness question, not a chip-mean
question. Its selected draws must never become Slice B's analysis population.
Slice B retains every collision-accepted draw under its separate frozen plan.
Test-scale host subsets identify their subset explicitly. Exhaustive library
enumeration does not establish exhaustive host agreement by itself.

Use one hand per session, fixed seats/opponents and identical ascending board
order in export and composition. Report in-pool and off-pool host coverage
separately. If H is the entire universe, a test-only proper-subset artifact
exercises off-pool defaults; its results are not attributed to the full artifact.
Similarly a test-only in-pool CHECK row discriminates hit/default reasons when
the production H happens to lack such an action. Preserve those identities.

Falsifiers: uncovered h counted as agreement; canonical-key count replacing set
equality; teacher recomputed during export; forced hole cards; witness selection
used to estimate chip means; synthetic control attributed to the production table.

## 5. Two separate classification results

eval_agreement first yields hand outcome eligibility, then agreement eligibility
and classification. They are separate values, so an agreement failure cannot
silently remove a completed policy's chips from a future comparison.

Read the nested hands[*].result, not its ordinal/button wrapper. A failed outer
session, absent scheduled result, non-completed hand, non-null failure cause,
truncated capture or absent settlement is an unsuccessful outcome, with a cause.
Use only actual retained envelopes; v1 DecisionRecord has no delivery_status.
Retain and inspect the child_stdout_base64 stream as complete framed messages.
Malformed base64/frames, missing terminal closure, incomplete hand_result or
failed event_result make the attempted observation unusable. A failure before
any river record is still counted. Preserve nullable decision/failure/timing.

For a successful Slice A blueprint hand, require one controlled river record.
Zero or duplicate records fail agreement with a diagnostic. Independently replay
the real applied history/key and cross-check the lookup's table_hit boolean
against the v1 reason; compare selected_action to the frozen teacher. A table
hit with the wrong action or an in-pool default is disagreement. An off-pool
default is unsupported. Unexpected reasons and non-passive pre-river reasons
are explicit disagreement/protocol observations, never implicit success.

A completed prefix-diverged baseline hand is outside the declared river
agreement root but remains chip-eligible. It must not encounter the blueprint
exactly-one-river predicate as a universal outcome gate. This is an interface
constraint for Slice B, not implementation of its estimator in Slice A.

Counters distinguish scheduled attempts, missing outcomes, completed outcomes,
agreement-eligible records, hits, disagreements, unsupported and excluded.
Pre-river records are checks on each attempt, not extra root observations.
Each scheduled attempt has exactly one final agreement disposition; preserve
secondary diagnostics without double counting. Final Slice A acceptance requires
complete required coverage, no disagreement and no unresolved excluded attempt.
Failures remain in the record even if an authorized later attempt completes.

Fixtures exercise nullable failures, accepted-then-failed timing, incomplete
hand/closure, absent result, truncation, malformed frames, zero/duplicate river
records and nested-wrapper mistakes. They prove classifier behavior only.
Retain real-host successful controls and authorized real-boundary failure
schedules; the latter trigger failure without fabricating successful transport,
settlement or cleanup. A changed stack prefix must produce zero hits, and the
reason cross-check must detect a relabeled CHECK hit/default with the same action.

## 6. Orchestration, ownership and verification sequence

The tools entry owns begin_run/finish_run and configures output_directory under
experiments/results/runs before finishing. One worker retains the source/host
admission across cells. Use the existing Session/Admission path and inherited
execution context; each session still launches its real child. This is reuse of
the admitted source, not reuse of betting state across hands. Do not edit host
or session code to make a convenience integration work.

Concretely, set PONTIUS_RUN_CONTEXT on the worker before Session preparation.
Launch the worker with cwd equal to the inherited run root and require that
same cwd before every Session.prepare, which admits Path.cwd(). A mismatched
root fails preparation; do not redirect it or create a second run context.
Admission caches the host module, and Source calls begin_run with that inherited
context, avoiding another source scan. Each Session still runs its own prepare
to load its schedule/artifact and initialize stacks. Do not bypass prepare by
assigning an Admission object to an otherwise uninitialized Session.

Keep phase data in one structured result with ordered observations and retained
wire/teacher artifacts as needed. One run yields one journal line, including
failure; children and cells create none. Run-boundary identity checks and existing
lightweight ownership/transport controls are not replaced with per-cell seals.
The implementation coverage inventory includes execution.py, status_generation.py
and their actual writer/consumer paths. It calls its list direct semantic
dependencies, not transitive closure, and pins exercised clock/admission surfaces.

Implementation order, all inside the existing Slice A budget:

1. Add root/range and capacity helpers plus discriminating codec tests. Demonstrate
   the missing behavior, implement it, and verify the focused disposable snapshot.
2. Add per-hand enumeration and both forced-action singleton reference tests,
   including the independent lattice checks, cancellation/false-tie/wrong-action
   controls and caller budget-stop cases. Do not spend a full pool in a unit test.
3. Add the preflight tools path and inherited one-run ownership checks. Freeze this
   first source checkpoint with its focused receipts and direct dependency inventory.
   Obtain two cold Tier C reviews, applicable broad suites and controller commit/run
   authorization. Execute capacity and preflight, then return their measured report.
   This is a real checkpoint: no bridge completion code is required to learn the cost.
4. Only after that measured decision, add deterministic export, exact membership and
   separate provider checks; then add outcome/agreement fixtures, real host controls and
   the key-perturbation/reason-discrimination cases through the maintained host.
5. Extend the tools entry with export/agreement orchestration. Register suites as they
   appear in tests/cases.json and inspect the combined Slice A diff and line budget.
6. Freeze bridge completion, its focused receipts, dependency inventory and coverage
   claim. Obtain two independent Tier C cold reviews, then applicable broad
   snapshot suites, controller authorization and the finalizer's commit/push.
7. Freeze and authorize its bounded export/agreement plan, binding the preflight and
   chosen resource envelope. Retain failure/kill outcomes and update bot-validation
   with their limited conclusion. Check the remaining review-round budget before
   each candidate; checkpoints do not reset it or grant reauthorization.

Use Python 3.11.15 before 3.14.6, -B -P, explicit snapshot imports, scrubbed
environment and absolute PONTIUS_GIT. A failed environment check is not a product
failure; do not retry an ambiguous retained invocation as if it never occurred.
All steps above are planned work; this specification supplies no green receipt.

## Alternatives, boundaries and open decisions

Building all of Slice A before measuring was rejected because near-capacity wire
rows and unknown per-hand cost can invalidate the planned campaign. A general
export/solver framework was rejected because it introduces unneeded contracts
under a 600-line budget. The chosen phases reuse the accepted narrow game and
real interfaces while making the two feasibility decisions early and observable.

No new controller ruling is required to draft this mechanism. Resource limits,
the finite execution seed bank and acceptance of measured cost are concrete
execution-plan decisions made before their respective launches. T2 determinization
remains outside Slice A. Existing specification/adoption authority does not grant
those launches or an integration commit.

Cheap to revise before freezing: module-local decomposition and development
diagnostics. Changing H, board, prefix, teacher identity or witness bank after
measurement requires a distinct plan/result; published records remain immutable.
The expected benefit is a usable deterministic export and a trustworthy agreement
instrument. Capacity or cost can stop this bridge without blocking independent
research. No runtime, cost, strength or transfer claim is established by this text.
