# Roadmap and Checkpoint Gates

This file is the compact forward map. The generated [STATUS.md](STATUS.md)
names the latest accepted decision; the immutable records under
[`docs/decisions`](docs/decisions) retain the complete experimental history.

The authoritative live target is one shared 15,000 ms wall-clock budget per
street of cumulative charged agent work, including the frozen emission reserve.
Opponent/transport idle pauses the ledger; useful background work consumes it;
and it does not reset at each action on the same street. Older 5-250 ms targets
are historical only
([ADR-0282](docs/decisions/ADR-0282-make-fifteen-second-street-wall-authoritative.md)).

## C0-C2: Research contract and exact solver laboratory

**Status:** Passed as foundations.

The repository has reproducible extensive-form controls, exact utilities and
best responses, NashConv, CFR-family solvers, frozen configurations, causal
holdout discipline, and explicit fallbacks. These checkpoints remain the
reference layer; they are not evidence that full hold'em is solved.

## C3: Reduced multiplayer hold'em

**Status:** Active at the six-player h32 river boundary.

Completed subgates include:

- exact two-to-six-player river controls with per-seat unilateral deviation
  gains and separate coalition-stress diagnostics;
- public-tree quotienting, factorized compatible-card beliefs, low-rank
  showdown structure, clean-fringe deltas, and shared-topology GPU residency;
- exact incremental response certification against an immutable blueprint;
- allocator lifecycle control for two resident h32 belief contexts; and
- a prepared 15-second street ledger: one resident warm step plus two exact
  atomic certificates and a one-second emission reserve on two frozen trials
  ([ADR-0166](docs/decisions/ADR-0166-prepared-street-fits-two-atomic-certificates-after-one-warm-step.md)).

The active strategy result identifies generator direction as the weak link.
Regret vertices expose about 20.54 times the value of one-step soft DCFR, while
the regret-mass proxy fails to rank that opportunity
([ADR-0178](docs/decisions/ADR-0178-regret-vertices-expose-soft-generator-weakness-but-not-a-live-selector.md)).
The subsequent 8/32/64 ladder rejects ordinary depth as the next architecture:
the best deep endpoint rises only 1.256x over step 8 and captures 2.97% of the
retained two-direction oracle. Purification adds 4.99x over raw average-64 but
is concentrated in one target and still trails the regret vertex
([ADR-0184](docs/decisions/ADR-0184-ordinary-deep-dcfr-plateaus-while-purification-remains-direction-sensitive.md)).

The fresh causal direction/opportunity screen replicates the generator
diagnosis: soft DCFR captures only 5.47% of its bounded three-family oracle,
while the regret vertex captures 99.20%. An immutable-blueprint best-response
vertex is directionally redundant and adds no material value. Regret mass and
minimum action gap both fail as free opportunity selectors. A charged
cap-radius probe captures 95.41% of the target-best denominator but is unstable
across targets and unavailable before certificate work
([ADR-0186](docs/decisions/ADR-0186-fresh-vertices-replicate-generator-weakness-but-no-free-selector-transfers.md)).

The first online-feasibility engineering subgate now passes. The additive
selector-stable affine certificate matches the old exact verifier to at most
`1.36e-15` across 36 retained regret-vertex blocks, and all six conservative
seat-0 ledgers fit the 15-second boundary. It captures 48.80% of the frozen
three-family bounded oracle under its preregistered half-radius rule
([ADR-0190](docs/decisions/ADR-0190-selector-stable-affine-certificate-is-exact-and-fits-retained-street-ledgers.md)).
The slowest retained ledger has only 338.90 ms of boundary headroom after the
one-second reserve, so the result validates the primitive but not a latency
distribution.

The first fresh live-rule trial passes on all four precommitted contexts. Fixed
acting seat 0 produces four deadline-eligible affine-certified candidates with
at least 3.80 seconds of boundary headroom, and post-emission exact teachers
agree to `1.67e-16`. Certified value is highly heterogeneous: one target carries
86.45% of the total and the target spread is 565x
([ADR-0192](docs/decisions/ADR-0192-fixed-seat0-affine-rule-emits-four-fresh-certified-candidates-before-deadline.md)).

The unchanged other-extreme replication also passes. Acting seat 5 emits four
fresh, exact, deadline-eligible candidates with at least 2.57 seconds of
headroom. Yet one target supplies 91.50% of seat-5 value and the target spread
is 11,004x. Across both extreme-seat trials, two of eight targets supply 88.78%
of all certified value
([ADR-0194](docs/decisions/ADR-0194-affine-street-mechanism-transfers-to-seat5-but-value-remains-concentrated.md)).

**Open gates:** broaden transfer rather than repeat the exposed blocker family,
and reduce compute time without changing the accepted live semantics. Before
new labels, freeze new board or belief regimes, explicit position coverage,
and a causal materiality/no-op rule. A one-raw-guard threshold is only a
retrospective development candidate even though it retains 99.902% of the
eight observed values. Modern DCFR variants remain deferred: the certificate
and deadline mechanism now work, while opportunity magnitude remains the
strategy weak link.

The retained-label selector replay is now closed by ADR-0206. Across the
primary six regret-vertex blocks per context, the exact Tier-B
slope-times-cap-radius composite selects all six winners and has mean
within-target Spearman `1.0`. It remains nearly perfect after every soft row is
removed, so the result is not merely family discrimination. The exact free
Tier-A own-gain slope is nevertheless a poor ranker and its prefilter discards
winners; the proposed A-to-B-to-C cascade is rejected. Current clock-derived K
is only 1--5 of six blocks and the literal cascade captures 78.17% pooled with
zero or partial capture on three contexts
([ADR-0206](docs/decisions/ADR-0206-opponent-sensitivity-composite-locates-retained-value-but-tier-a-cascade-fails.md)).

ADR-0210 now closes that selector engineering gate. Packing 30 scalar opponent
reads into six responding-seat calls is exact but yields only `1.0059x` median
speedup; terminal-contraction time remains `99.48%` of the scalar bill and the
full six-block B-to-C ledger fits only three of six contexts. The accepted
ADR-0158 overlay was already active and reused `94.47%` of possible terminal
rows, so repeating it cannot supply the missing multiplier. K remains bound.
A later fresh panel should prefer action-conditioned in-tree posterior shifts
with a genuinely widened single-family block library, but it remains sealed
until the engineering ledger can price its candidate set honestly.

The subsequent systems and strategy line changes that assessment materially.
The resident device fold speeds both the warm-step and Tier-B customers
([ADR-0212](docs/decisions/ADR-0212-device-record-fold-materially-speeds-both-resident-customers.md)),
while the isolated profile identifies sparse FP64 compute pressure rather than
a hidden transfer or host barrier
([ADR-0218](docs/decisions/ADR-0218-resident-sparse-profile-identifies-compute-pressure.md)).
Action-conditioned posteriors contain exact value but the widened live selector
still misses the wall boundary
([ADR-0222](docs/decisions/ADR-0222-widened-range-transfer-finds-value-but-live-selection-is-infeasible.md)).

Continuation rooting is the first strategy-positive correction to that
failure. It is exact, cuts five sixths of strategic nodes, prices all 31 legal
blocks, and delivers exact certified value on all 12 opened targets before the
deadline ([ADR-0224](docs/decisions/ADR-0224-continuation-root-is-exact-and-removes-five-sixths-of-strategic-nodes.md),
[ADR-0226](docs/decisions/ADR-0226-continuation-root-unbinds-the-complete-31-block-library.md),
[ADR-0228](docs/decisions/ADR-0228-continuation-root-delivers-exact-safe-value-on-all-twelve-targets.md)).
Two independent steps fit every conservative ledger
([ADR-0230](docs/decisions/ADR-0230-two-continuation-steps-fit-the-conservative-street-ledger.md)),
and the disjoint 12-target Latin-C/D posterior panel is sealed
([ADR-0232](docs/decisions/ADR-0232-heldout-continuation-posterior-panel-is-fresh-and-nondegenerate.md)).

The held-out depth gate is now closed. Two steps consume 14.00% more charged
time, deliver 1.10% less pooled exact value, and reduce value rate by 13.24%.
Eleven of twelve targets reproduce the exact same winner; the sole material
switch is harmful
([ADR-0235](docs/decisions/ADR-0235-one-step-retained-after-heldout-depth-value-trial.md)).

The first direction-diversity capacity gate is closed. A complete second
soft/regret bisector family is structurally distinct but exceeds the street
boundary on 4 of 12 targets, reaching 19.42 seconds
([ADR-0237](docs/decisions/ADR-0237-full-bisector-library-does-not-fit-every-street.md)).
No direction labels were opened.

ADR-0239 rejects the first label-free cross-payoff implementation before any
coefficient matrix completed: its fixed-response splice used embedded layout
hand keys instead of the continuation's external posterior axes. The algebra
remains open, but a mechanical rerun is deferred in favor of the stronger
one-seat convex-program question.

ADR-0241 closes the finite keystone. The sequence-form row solver matches both
complete 64-by-64 normal-form teachers to at most `3.47e-17`, preserves the
safe-incumbent and `U - L` timeout contract, rejects the behavioral shortcut on
a repeated-actor path, and passes realization-retreat identities below
`1.1e-16`. It uses five opponent rows for acting seat 0 and three for seat 1;
those sparse control counts are not an h32 prediction.

ADR-0243 closes the h4 open-axis identity gate. The repeated-actor sequence-
form row and post-bet behavioral row match independent dense teachers below
`8.0e-15`; the corrected explicit-axis response splice is exact while the old
embedded-key splice fails all 256 mutation entries. The measured CPU h4 costs
are controls, not h32 predictions.

ADR-0244 freezes the narrow h32 successor on the tight Latin-D target and its
widest acting seat. Eleven initial resident passes build all six epigraph rows;
16 frozen regret vertices are projection teachers only. The self-priced ledger
charges a measured full response oracle and all five possible new response
rows per cut round, plus a separate measured-or-floor final proof reserve.

ADR-0245 closes that preflight. All 96 projections agree below `4.2e-15`; six
gain rows occupy 49.2 KB, the pool peaks at 5.66 GB, and physical free memory
stays above 9.62 GB. The measured conservative ledger fits exactly one complete
cut round at 13.47 seconds. A second does not fit.

ADR-0246 freezes the label-free one-round h32 master prototype on the identical
target and acting seat. It corrects the conservative ledger by charging the
previously omitted initial master reserve: the complete one-round path is now
`13,967.616 ms`, not `13,467.616 ms`. The runner solves the source restricted
master, runs one exact all-seat multi-cut oracle, resolves at most once, and
stops. It reports verified `L`, independent `U`, `U - L`, response signatures,
rows, active caps, retreat, timings, memory, and both complete ledgers while
emitting only the immutable blueprint.

ADR-0247 closes the optimizer gate. The initial master needs two new opponent
facets; one all-opponent multi-cut round then closes exact `U - L` to
`3.84e-15`. The final exact cap violation is only `1.03e-15`, the measured live
ledger is 8.72 seconds, and the corrected conservative ledger is 13.97
seconds. A result audit caught that the frozen runner reused the looser
epigraph tolerance for its cap-feasible Boolean; independently applying the
preregistered `2e-11` cap allowance leaves the branch unchanged by nearly four
orders of magnitude. The endpoint and diagnostic retreat remain un-emitted,
and no strategy-quality claim is open.

ADR-0250 records that ADR-0249's first invocation stopped at its pre-label
barrier: source, cuts, row counts, and both LP bounds reproduced, but three
GPU-derived policy byte digests did not. No retreat or fallback label opened
and no artifact was written. This is the ADR-0179 reassociation class, not a
changed optimizer branch.

ADR-0252 closes the corrected quality gate. The independently certified half-
retreat delivers exact value `0.00795681`, `3.14x` the accepted fallback's
value, and retains `1.50e-9` minimum cap slack. Its conservative value rate is
`2.37x` the fallback rate while the full `13,967.616 ms` ledger still fits.
All numerical/discrete reconstruction gates pass while the three policy byte
digests remain non-gating reassociation diagnostics.

ADR-0254 accepts the final label-free panel. All 12 target IDs and digests are
fresh, every source/bettor/acting seat appears twice, and the three panels now
cover all 36 source-bettor combinations exactly once. Acting-player marginal
TV is nonzero on every target (`0.044–0.194`); no quality label was opened.

ADR-0255 freezes that strategy replication before any Latin-E warm step or
final label. All six Latin-E targets run in manifest order with no opportunity
selection or cross-target adaptation. Each target pays one warm step, one
source master, one exact multi-cut construction oracle, at most one resolve,
and one independent exact factor-`0.5` retreat certificate. The cap and
epigraph allowances remain separate, the effective ledger is at least
`13,967.616 ms`, all external policies remain the blueprint, and the bounded
one-round master makes no global-optimality claim.

ADR-0256 rejects the partial v1 invocation without a strategy result. Target 1
completed in memory but its label was never printed, persisted, or inspected;
target 2 stopped before its final label. Its first oracle found three apparent
epigraph violations whose response signatures were already resident and whose
rows matched exact gains within `4.98e-16`. The largest `3.073e-9` discrepancy
matched the master's recorded inequality residual, identifying a response-
classification defect rather than a missing facet. No artifact was written and
Latin-F remains untouched.

ADR-0257 freezes the label-blind correction. Already-resident response rows are
accepted only when they reproduce the exact oracle within `2e-11` and remain
inside the unchanged `1e-8` master primal ceiling; genuinely new opponent
signatures are still cut. It also requires all six candidates to freeze before
any v2 final retreat label. Certificate contexts are then reconstructed one at
a time, with identities and reconstruction time recorded separately from the
unchanged resident live ledger.

ADR-0258 closes the corrected campaign. All six candidates freeze before the
first v2 label; all six exact half-retreats are cap-safe, material, and on time.
Pooled delivered value is `0.0649285`, with target values from `0.0017020` to
`0.0323617`; all three balanced and all three blocker-heavy targets pass. The
four verified resident residual rows match exact gains within `4.72e-16`, ten
new facets are cut, measured live time stays below 8.98 seconds, and the full
13.97-second conservative ledger fits every target. Target 1 remains explicitly
label-blind reconstructed under ADR-0256; no candidate was emitted.

**Immediate gate:** preregister the unchanged algorithm and thresholds on the
six untouched Latin-F targets. Preserve the campaign-wide barrier, factor
`0.5`, exact final proof, resident-row classification, full conservative
ledger, immutable blueprint emission, and null global/population claims. Treat
Latin-F as confirmation of the breadth branch, not as a license to retune or
introduce a fresh fallback comparison.

ADR-0259 freezes that confirmation before any Latin-F GPU work. All six targets
run in manifest order as first final-label evaluations. The algorithm,
tolerances, factor, campaign barrier, exact proof, `0.001` materiality floor,
four-of-six breadth rule, family requirement, and complete ledgers are inherited
unchanged from ADR-0257/0258. No Latin-E value enters a Latin-F threshold.

**Immediate gate:** execute ADR-0259 once and seal the fixed confirmation
branch. A pass authorizes only a separately preregistered prospective live-
shadow integration test with immutable blueprint fallback; a clean failure
retains Latin-E evidence but rejects that integration step. Neither branch
licenses deployment or a population claim.

ADR-0260 accepts the untouched confirmation at the exact frozen floor. Four of
six Latin-F targets materially pass, with both families represented and every
schedule inside the full ledger. All six raw half-retreats are positive and
exact-cap-feasible; two abstain solely because minimum slack (`1.374e-9` and
`1.246e-9`) misses the stronger `1.48e-9` interior requirement. Latin-E/F now
deliver accepted pooled value `0.1104383` across ten contract-passing targets,
while every actual policy remains the blueprint.

ADR-0261 freezes the first deployment-aligned identity panel without opening a
strategy label. Each retained source observes checks, a bet, and exactly the
first responder's call; the second responder is then the player actually on
the clock, with three opponents still acting downstream. Source, bettor,
observed responder, and acting player are each balanced exactly once. The
manifest must prove the legal prefix, current-player identity, one-node h32
axis, path-single-visit topology, fresh posterior identity, and nondegenerate
belief shifts before GPU work.

ADR-0262 accepts the label-blind manifest. All six posterior identities are
fresh and nondegenerate; every declared actor is the current fold/call player,
with three downstream responders, one acting public node, 32 h32 information
sets, and 64 behavioral variables. Current-actor marginal TV is
`0.062778–0.152469`. The manifest generated zero strategy labels.

ADR-0263 freezes that strategy trial before any decision-aligned label. A scoped
adapter changes only posterior/continuation setup and must restore the sealed
Latin setup after the bounded campaign. The one-round core, factor `0.5`, exact
certificate, `1.48e-9` interior floor, full measured and conservative ledgers,
global prelabel barrier, and immutable-blueprint external emission remain
unchanged. Process validity is separate from the inherited four-of-six material
value-transfer threshold.

ADR-0264 accepts the prospective current-decision result. All six half-retreats
are exact-cap-safe, interior, positive, and shadow-accepted; four exceed
`0.001`, both range families are present, and measured live time tops out at
5.081 seconds while the 13.968-second conservative floor remains binding. The
scoped setup adapter restores correctly and every actual emission is still the
blueprint.

ADR-0265 freezes the label-blind post-fold differential. It reuses the six
sources and positional schedule, changes only the first observed response from
call to fold, and requires fresh disjoint identities, legal current-player
roots, three downstream responders, one-node h32 axes, and zero strategy
labels. A pass seals identities but deliberately does not authorize their GPU
strategy evaluation.

ADR-0266 accepts and seals the post-fold manifest. All 36 gates pass, the six
identities are fresh and disjoint from the post-call panel, every actor is
current with one h32 public node and three downstream opponents, and actor TV
is nonzero at `0.037662–0.130666`. The CPU-only run generates zero strategy
labels; those identities remain closed.

ADR-0267 corrects the retained inventory from 24 to 42 eligible opened
contexts: Latin-A/B, C/D, E/F, and the post-call panel. The roster contains 36
wide last-responder axes and six current-decision axes; every source, bettor,
and acting seat appears seven times. It freezes exact multi-cut generation to
verified cap and `U - L` closure, with 32-round, 240-second target, and
10,800-second campaign caps. The census is explicitly retrospective, keeps the
post-fold six label-blind, preserves one warm step and all-seat oracles, and
uses ADR-0247 as a numerical/discrete replay control.

ADR-0268 rejects the first census invocation without an artifact. Four printed
targets close in 3, 2, 0, and 1 rounds; a fifth reaches the frozen no-new-facet
numerical-stall branch; target 6 then raises the master's primal/dual
verification guard. Universal one-round closure is already falsified, but the
five printed rows are not a complete census and target 6's intermediate state
is conservatively treated as opened. The failure is orchestration-local: one
target exception erased prior in-memory rows and prevented the fixed remainder
from running.

ADR-0269 freezes the target-isolated correction. It imports ADR-0267's pinned
config and target implementation without changing any scientific field,
discloses recomputation of targets 1–6, atomically checkpoints every outcome,
and continues only after the known master-verification error has been marked
censored and GPU state released. Any other target error fails the process;
neither kind can count as closure. The original 42/42 one-round and full-
closure branches remain unchanged even though the printed 3- and 2-round rows
have already falsified the first.

ADR-0270 seals the 42-target census. Thirty-five programs close globally:
seven at round 0, eleven at round 1, ten at round 2, and seven at round 3. Six
facet-closed candidates fail the tighter exact cap and retain material `U - L`
gaps; one wide-axis target has the isolated KKT failure. The broad one-round
claim is false and the direction path remains live. All six actual current-
decision targets, however, close in zero or one round (four/two) with no stall
or error. Every difficult row belongs to the wider future-axis scope.

ADR-0271 freezes that read-only paired ledger join. The four zero-cut paths owe
no additional oracle because their first endpoint is already exact and closed;
the two one-cut paths owe exactly one post-cut endpoint oracle. The inherited
safe retreat must remain exact-certified, cap-feasible, interior, accepted,
and positive. Measured accounting adds the recorded incremental time, while
conservative accounting adds a fixed 1,000 ms to the unchanged 13.968-second
floor, leaving only 32.384 ms on the one-cut shape. The replay is CPU-only and
opens no post-fold label.

ADR-0272 accepts the replay. All pair identities agree within `1.08e-14`. Four
zero-cut paths retain two exact oracles; the two one-cut paths add one exact
post-cut endpoint oracle at 760.975 and 844.294 ms. The worst measured combined
ledger is 5.885 seconds. The worst conservative ledger is 14.968 seconds,
leaving 32.384 ms. Every inherited retreat remains exact-safe and positive,
and the post-fold labels remain unopened.

ADR-0273 freezes that fresh confirmation. It uses all six post-fold identities
in manifest order, a separately pinned fold adapter, and a restoration-tested
capture of the sealed core's exact endpoint and final epigraph outputs. All six
candidates freeze before any post-cut endpoint or final retreat label. Zero-cut
paths reuse the first oracle; one-cut paths add exactly one endpoint oracle and
never continue to round two. Global closure requires exact cap and epigraph
closure plus `U - L <= 1e-8`.

ADR-0274 accepts the process-valid fresh mixed result. All six post-fold
half-retreats are exact-safe, positive, and material, with pooled value
`0.04710747`; measured complete ledgers top out at 5.337 seconds. Universal
one-round closure nevertheless fails: four of six endpoints close, while two
fresh one-cut endpoints expose new response facets and retain exact gaps
`0.00077635` and `0.00034964`. Direction demotion is rejected.

ADR-0275 freezes that off-clock diagnostic. ADR-0276 accepts its process-valid
result: both failures close, but at depths three and two rather than a common
second round. The blocker-heavy target exposes two successive pairs of new
seat-0/seat-5 response tapes. Later-round measured work is `555.105–764.960 ms`,
but the unchanged conservative ledger has only `32.384 ms` left and the
diagnostic omits a new retreat proof. Exact global closure therefore remains
off-clock; the one-round master remains the bounded safe generator and the
direction fallback remains live. ADR-0276 also discloses a Windows newline
checkpoint-hash telemetry defect and installs a byte-truth helper for future
runners without rewriting the sealed artifact.

ADR-0277 freezes the action-width capacity successor and corrects its root
scope before GPU work. A post-bet root would compare fold/call against
fold/call and therefore contain no current action-width choice. The accepted
pre-bet scope instead crosses all six retained sources with all six current
positions after prior checks, opening only the current public node. This keeps
the exact affine master valid even though a checking actor may act again later;
all future own-policy rows remain at blueprint and are solved afresh if reached.

ADR-0278 rejects the sole invocation because its `3,844.795 s` total exceeds
the frozen `3,600 s` campaign ceiling; every other leaf gate passes and no
widened strategy label opens. The complete diagnostic matrix shows that the
canonical affine/shared cache has already solved the memory problem: all 72
caches are safe, two-size median persistent bytes are slightly below one-size,
and peak pool use is 5.169 GB. Runtime is the wall. No two-size arm fits the
15-second conservative proxy; only the last acting position fits one size on
all six sources. Retain one size and keep widened quality closed.

[ADR-0279](docs/decisions/ADR-0279-install-active-campaign-deadlines-and-prioritize-exact-pre-bet-row-speculation.md)
installs and tests the shared active campaign deadline without running h32. One
`monotonic_ns` wall now checkpoints before each frozen unit, denies a unit whose
complete preregistered bound does not fit, and stops after either a unit or
campaign overrun. The campaign wall remains distinct from the live street
ledger.

Its read-only ADR-0278 repricing also localizes the next action-width lever. The
warm DCFR state is not consumed by the pre-bet restricted master; removing that
step saves a two-size median 9.331 seconds but leaves no complete position. The
eleven exact initial rows cost a larger median 17.292 seconds. Conditional on a
zero-cost exact row-cache hit, removing both blocks would place all six seat-5
sources below 15 seconds, with a worst proxy of 12.966 seconds. That is a
counterfactual bound, not capacity evidence: lookup, validation, hit rate, and
fresh execution remain unmeasured.

**Immediate gate:** build a CPU/h2 exact round-trip control for a byte-truth,
full-provenance source/current-prefix row cache and remove the nonfeeding warm
step only in the pre-bet restricted-master successor. Charge lookup and
validation on-clock and preserve the immutable blueprint on every miss. The
one-size/added-column overlay remains unproved: even optimistic paired-delta
arithmetic for initial and future cut rows leaves the worst seat-5 source at
15.856 seconds unless endpoint contractions also shrink. The sealed artifact
contains zero endpoints or cuts, so it cannot price an anytime separation rule.
Do not run h32 or open action-width quality until a fresh label-free capacity
preregistration freezes these mechanics, per-unit bounds, numerical identity,
independent certification, and every unchanged safety cap.

[ADR-0280](docs/decisions/ADR-0280-exact-pre-bet-row-cache-passes-cpu-h2-fail-closed-control.md)
closes that CPU/h2 falsifier. The complete `2N - 1` initial-row bundle binds
the full policy and exact probability tape, belief, hands, game provenance,
compiled topology, fixed continuation, action schema, acting/payoff roles,
every fixed-response tape, row primitive, numerical contract, and literal
persisted bytes. Lookup revalidates every source intercept within `2e-11` and
admits no partial row set.

On the two-player, two-hand literal control, all three cached rows round-trip
byte-exactly, reconstruct both gain rows byte-exactly, and feed the same
restricted master. Independent endpoint evaluation agrees within
`1.34e-15`. All eleven provenance-digest mutations and the byte, response,
schema, numerical, size, and fallback adversaries miss or reject. The
successor path performs zero warm steps and keeps the defensive blueprint as
its only external policy. These are cache-correctness controls, not h32 timing
or capacity evidence.

[ADR-0281](docs/decisions/ADR-0281-preregister-temporally-separated-pre-bet-row-cache-seed.md)
historically froze the first executable GPU stage without authorizing replay. The sealed
label-free matrix lawfully narrows the scope to all six acting-seat-5 sources,
the only complete position below 15 seconds under the warm-free, zero-cost-hit
ceiling. Both one-size and two-size bundles remain in the differential. Their
distinct primitive manifests bind 106 local source modules plus the arm,
backend, batching, Float64, and runtime contracts.

The seed executable is structurally unable to trust or consume its own hashes:
`trusted_seed_manifest_sha256` is null, replay is false, and its all-cache
barrier ends at observed-untrusted bytes. Six 120-second context units and
twelve complete 120-second seed units total 2,160 seconds under the unchanged
3,600-second active monotonic wall, with a byte-truth checkpoint before every
unit. Each seed unit includes cache construction, source oracle, eleven exact
rows, six gains, serialization, hashing, parsing, numerical validation, and
byte comparison. No warm step, master, candidate, certificate, label, or
policy-emission path exists.

[ADR-0283](docs/decisions/ADR-0283-withdraw-v1-seed-authority-and-install-v2-trust-controls.md)
revokes ADR-0281 before invocation. Independent review found that v1 left the
acting best-response scalar outside the hash-bound cache and accepted it from
the successor caller; a different finite scalar could therefore shift the
acting gain after an exact cache hit. The seed runner also left result
assembly, rehashing, serialization, write, and readback outside any separately
admitted finalization unit. Nominal campaign slack does not repair either
semantic boundary.

The additive CPU v2 derives all identity, source-tape, payoff and acting-response
inputs in a factory-only live context; population generates rows only from
provenance-bound affine contexts. It binds scalar and rows in one persisted-byte
hash, returns both or neither, rejects v1 bytes, and removes caller identities,
rows and scalars from the successor API. The writer returns no replay authority:
only a separately persisted seal loaded under an already expected seal hash can
authorize lookup. A reusable deadline-owned publisher uses separately bounded
data and completion-seal phases while an exclusive lock marks partial or late
state unconsumable. These are adversarial CPU/fake-clock controls, not an h32
cache or capacity result. Historical v1 files remain unchanged and are not
authorized for population or replay.

The generated front door now treats ADR-0282 as an explicit runtime-contract
head, requires every latest ADR to publish a complete snapshot, and makes
revocations cumulative and permanently visible rather than recent-ledger
heuristics.

**Immediate gate:** first preregister a reduced scalability diagnostic for an
independent row oracle and the complete data/seal finalization envelope. Review
a replacement v2 h32 seed only after its arm-specific GPU primitive, complete
import manifests, external-seal plan and measured bounds are frozen. Until
then, do not run the v1 seed, invoke ADR-0277, solve a cached master, open a
candidate endpoint, or make an action-width quality claim.

[ADR-0284](docs/decisions/ADR-0284-install-certified-bound-and-semantic-type-successors.md)
installs the remaining independent-review controls without rewriting sealed
artifacts. Historical convex masters used feasible primal objectives as lower
bounds; 18 of 41 retained-census target rows consequently record `U - L < 0`,
with worst reversal `-6.676663499849411e-09`. The additive master v2 instead
uses an outward-rounded bounded-variable Lagrangian certificate and keeps raw
primal/dual quantities separate. Historical JSON cannot be recertified because
it did not retain the needed dual vectors and matrices.

The same correction makes public-node rows root-only until upstream own reach
is represented, binds complete source context plus acting/payoff roles,
separates seven tolerance semantics, and makes host topology the sole index
authority in the non-consuming device-fold v2. The transitive v2 contraction,
resident CFR, cross-payoff and selector-affine paths pass reduced GPU/host
differentials; this is correctness evidence, not an h32 timing result. These
controls change no sealed strategy label and authorize no rerun. Any future
optimizer successor must consume the certified master/sequence adapter and
explicit tolerance schema before making a lower-bound or closure claim.

[ADR-0285](docs/decisions/ADR-0285-close-second-and-third-round-review-defects.md)
closes the remaining review defects in strict evidence loading, affine/cache
provenance, deadline admission arithmetic, behavioral-master unit separation,
negative-reach folding and transitive successor routing. It also installs the
first executable shared 15-second street ledger. No h32 cache, candidate or
strategy label was opened.

[ADR-0286](docs/decisions/ADR-0286-install-the-exact-six-seat-legal-decision-spine.md)
connects that ledger to an immutable six-seat integer-chip betting reference.
The kernel covers exact action order, fold/check/call/raise-to bounds, the full-
bet and cumulative short-all-in reopening rules, unmatched returns, independently
eligible side pots, integer odd chips, settlement, and all street transitions.
The one-seat controller charges observed-action processing and all foreground
or background agent work, pauses opponent/transport idle, retains one ledger
across repeated actions, and fails closed to a caller-supplied legal blueprint
action. A maintained exhaustive three-chip oracle covers 45,456 semantic states
and 60,732 transitions for all button positions.

[ADR-0287](docs/decisions/ADR-0287-preregister-the-complete-reference-hand-replay.md)
froze the complete reference hand replay before results. The successor
[ADR-0288](docs/decisions/ADR-0288-complete-reference-hands-pass-the-exact-one-seat-loop.md)
passes that gate. An explicit six-seat deal stays in the replay oracle while
the controlled decision sees only its two private cards and the revealed board.
Exact single-opponent domains have widths 1,225/1,081/1,035/990. A digest-bound
future-blind table can represent every semantic legal action and defaults only
to the deliberately weak passive rule.

Both frozen hands reproduce their full action order, public-card transitions,
four immutable street ledgers, showdown, actual pots, payouts, and chip
conservation. The multiway all-in fixture agrees with a separate test-only
chip-depth pot/payout oracle. Every charged interval is named and accounts for
exactly one interval in its closing street snapshot.

[ADR-0289](docs/decisions/ADR-0289-preregister-the-full-width-belief-blueprint-boundary.md)
froze the next interface before results. The successor
[ADR-0290](docs/decisions/ADR-0290-full-width-belief-and-rational-policy-cross-the-reference-hand.md)
passes it. All five opponent axes retain exact 1,225/1,081/1,035/990 street
widths, hard card disjointness, actor-only rational action updates, board
filtering, and immutable provenance through the unchanged 20-event hand. A
separate rational oracle matches reduced production supports, partitions, and
marginals while proving that independent unary normalization is not the joint
belief. The full Cartesian tensor and normalized full-width marginals remain
uncomputed.

This is still C5 foundation, not a C5 pass. The policy is deliberately weak and
untrained; scalable value contraction, a fixed action abstraction, a trained
full-game blueprint, and a strategy-producing resolver remain outside the loop.

[ADR-0291](docs/decisions/ADR-0291-preregister-the-exact-legality-action-abstraction-boundary.md)
froze the first exact-legality action lattice before results. Its successor
[ADR-0292](docs/decisions/ADR-0292-reject-action-abstraction-v1-before-complete-hand-integration.md)
rejects v1 before replay integration. The exact lattice and barycentric
projector pass all 45,456 three-chip states and 60,732 transitions, and the
compact sizing LP matches bounded complete normal forms. But only one frozen
quality context is nondegenerate, and v1 recovers effectively none of that
context's full-over-minimum/all-in gain. Small normalized loss does not override
the failed conjunctive gates.

[ADR-0293](docs/decisions/ADR-0293-preregister-the-dyadic-pot-odds-confirmation-successor.md)
freezes a dyadic successor and a deterministic untouched panel. Its outcome
[ADR-0294](docs/decisions/ADR-0294-reject-dyadic-v2-on-confirmation-power.md)
rejects v2 before replay integration. Conditional diagnostics are promising:
94.51% aggregate recovery, maximum normalized loss 0.0282%, and lower aggregate
loss than v1. But only five of 24 contexts have measurable full-over-narrow
opportunity versus the frozen minimum of eight. Structural showdown diversity
did not guarantee sizing informativeness.

[ADR-0295](docs/decisions/ADR-0295-preregister-candidate-blind-sizing-power-diagnostic.md)
freezes three full-versus-minimum/all-in-only power replications. Its outcome
[ADR-0296](docs/decisions/ADR-0296-reject-candidate-blind-power-pools-and-own-stop-state.md)
rejects the protocol before v3. Batch 0 reaches 12 material contexts after 40
openings; batch 1 exhausts 96 with only 11; batch 2 values remain unopened. A
follow-up also opened batch-0 values after its stop point due to unattributed
failure telemetry. Those values are quarantined, and a new owned runner now
binds batch, contiguous prefix, and stop reason.

[ADR-0297](docs/decisions/ADR-0297-preregister-width-four-sizing-power-replications.md)
freezes the smallest richer sizing-power game before any new pool or value:
four private types per seat with the same one-bet tree, opportunity floor, and
candidate-blind controls. It adds exact LP-dimension and pivot ceilings.
[ADR-0298](docs/decisions/ADR-0298-seal-width-four-structural-pools-before-values.md)
now seals all three 96-context pools and analytic dimensions in a value-free
module. The next active gate is to implement and execute the owned replications
unchanged. Do not tune the floor, enlarge the pools, open ADR-0295 batch 2, or
choose v3.

ADR-0198 closes the first compute-attribution subgate. The resident GPU
pipeline consumes 67.87% of pooled step time, host record-to-hand folding
30.56%, and transfer only 0.63%. This retained C4 line should next distinguish
FP64 arithmetic from memory/sparse-pipeline pressure on the exact workload; a
resident hand-fold differential remains its concrete software lever after
ADR-0210 rejected opponent-call packing. It remains parked while the C5 action-
abstraction boundary is active. When resumed, the differential must charge host
milliseconds removed and device milliseconds added separately, cover both the
warm step and Tier B, and reprice the complete ledger. If the sparse pipeline
still controls K afterward, separate arithmetic from memory pressure before a
kernel rewrite. Neither screen is a license to change the frozen live rule.

**C3 exit gate:** on fresh reduced multiplayer regimes, a precommitted online
rule must improve certified value under the complete wall-clock and memory
contract without weakening any per-seat cap. Exact offline opportunity alone
does not pass.

## C4: Optimized runtime

**Status:** Partly explored inside C3; not passed as a checkpoint.

Build the production-oriented flat/native runtime, cancellation and emission
path, latency distributions, and memory accounting. Optimized results must
match the reference numerically under the frozen protocol and improve real
decision traces without strategy regression.

## C5: Pluribus-style control agent

**Status:** Complete explicit-deal one-seat loop with symbolic five-opponent
ranges passed; complete agent not passed.

Build a complete legal six-max control agent with a fixed abstraction,
blueprint, ranges, fixed-depth resolving, off-tree handling, and fail-closed
fallbacks. The resolver must improve the blueprint in reduced exact games and
against a frozen evaluation league.

The first two exact-legality candidates were killed before integration: v1 on
reduced sizing recovery and v2 on confirmation power. The next checkpoint
remains narrower than blueprint training or resolver integration. ADR-0297
preregisters a four-by-four private-type game while holding the one-bet tree
fixed. The three-by-three pool failed its second yield replication and remains
parked. Only after the width-four game passes its frozen replicated yield and
exact-work boundary may a v3 mechanism be frozen. The passive reference source
remains the emitted fallback.

## C6: Neural blueprint and leaves

Add river-to-flop teachers and policy/value/action/uncertainty models only after
the exact runtime and decision contract are stable. Pass on root-strategy harm
at equal latency, not value-function mean-squared error alone.

## C7: Adaptive public-belief search

Add dynamic width/depth, continuous action proposals, residual solving, and
street/player specialization. Adaptive search must Pareto-dominate fixed search
at multiple budgets with no material rare-branch vulnerability.

## C8: Cache and speculation

Add range-aware caches, topology/embedding reuse, pondering, and preemptible
future-state work. Future decisions must improve without degrading current-
decision p95 latency or reusing a strategy across incompatible beliefs.

## C9: Learned value-of-computation scheduler

Train only after a richer workload demonstrates enough attainable value to pay
for inference and training. A learned scheduler must beat the best transparent
heuristic on hidden games and full traces; otherwise retain the heuristic.

## C10: Full evaluation

Require exact reduced-game results, adversarial responders, complete cross-play
matrices, paired-deal confidence intervals, latency and memory profiles, and all
major ablations before a defensible final report.
