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
do not rely on a missing-policy fallback. Invoke evaluation.best_response for
player 0. Compare its selected action exactly; compare reported values with a
declared floating-accumulation allowance derived for the reference computation,
while retaining the integer totals as the production identity. A numerical
disagreement is investigated and recorded, never converted into an action tie.

The cost preflight separately records production enumeration and reference
construction/evaluation for As Ad, Kh Kd, Td 8d and 3c 4d on the development
board. The royal-spade/2c 3d control must return CHECK at equal zero totals.
Host agreement later must include both action categories when present in H;
their presence is observed, not presumed from this fixed sample.

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
2. Add per-hand enumeration and explicit singleton reference tests, including exact
   tie and caller budget-stop cases. Do not spend a full pool in a unit test.
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
