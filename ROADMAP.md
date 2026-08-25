# Roadmap and Checkpoint Gates

This file is the compact forward map. The generated [STATUS.md](STATUS.md)
names the latest accepted decision; the immutable records under
[`docs/decisions`](docs/decisions) retain the complete experimental history.

The authoritative live target is maximum marginal chip-valued decision quality
per millisecond of attributable online compute under one continuous 15,000 ms
response wall for each controlled action, including the frozen emission
reserve. Prior-street and opponent-turn preparation is measured separately and
may be credited only through an exact matching artifact; it never extends the
live response wall. Older cumulative-street and 5-250 ms targets are historical
only
([ADR-0307](docs/decisions/ADR-0307-make-action-clock-and-preparation-bank-authoritative.md)).

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
- a historical prepared 15-second street ledger: one resident warm step plus two exact
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
first executable historical cumulative 15-second street ledger. No h32 cache, candidate or
strategy label was opened.

[ADR-0286](docs/decisions/ADR-0286-install-the-exact-six-seat-legal-decision-spine.md)
connects that ledger to an immutable six-seat integer-chip betting reference.
The kernel covers exact action order, fold/check/call/raise-to bounds, the full-
bet and cumulative short-all-in reopening rules, unmatched returns, independently
eligible side pots, integer odd chips, settlement, and all street transitions.
The historical one-seat controller charges observed-action processing and all
foreground or background agent work, pauses opponent/transport idle, retains
one ledger across repeated actions, and fails closed to a caller-supplied legal
blueprint action. A maintained exhaustive three-chip oracle covers 45,456
semantic states and 60,732 transitions for all button positions. ADR-0307 keeps
this implementation for reproduction but supersedes its timing contract.

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
module. [ADR-0299](docs/decisions/ADR-0299-width-four-passes-replicated-sizing-power.md)
passes the owned replications at 12 qualifiers after 23, 24, and 32 openings,
with all numerical, diversity, teacher, and pivot gates clean. The next active
gate is to preregister exactly one v3 mechanism before deriving fresh,
disjoint representative and qualified panels. Do not fit or confirm against
any opened panel or open ADR-0295 batch 2.

[ADR-0300](docs/decisions/ADR-0300-preregister-collision-repair-v3-and-fresh-dual-panels.md)
freezes that mechanism and its dual-panel gates before source implementation.
The successor
[ADR-0301](docs/decisions/ADR-0301-freeze-collision-repair-v3-source-and-fresh-seeds.md)
passes exhaustive exact-legality and v2-superset validation and freezes the
source digest plus two exact fresh seeds.
[ADR-0302](docs/decisions/ADR-0302-seal-fresh-v3-structures-before-qualification-values.md)
now commits the resulting value-free 48-context representative structure and
96-context qualified pool, with zero counterpart in 604 maintained prior
contexts.
[ADR-0303](docs/decisions/ADR-0303-seal-fresh-qualified-panel-before-v3-values.md)
passes the separate candidate-blind full/narrow screen at 24 qualifiers after
60 contexts and seals the final panel plus teacher controls.
[ADR-0304](docs/decisions/ADR-0304-reject-collision-repair-v3-on-qualified-recovery.md)
rejects the resulting v3 campaign before integration. Representative and
qualified maximum/mean normalized losses pass, but qualified raw-chip recovery
is `0.800547544995807` versus the frozen `0.90` floor. The next boundary is a
separate prospective preregistration for one materially different bounded-
width mechanism and wholly fresh panels; no v3 retuning or panel reuse is
authorized.
[ADR-0305](docs/decisions/ADR-0305-preregister-capacity-filling-pot-odds-v4.md)
now freezes capacity-filling pot-odds v4 before source code. It preserves every
v3 action and the seven-raise ceiling, then fills deduplicated capacity by an
exact-rational farthest-point rule. Its 48-context representative stream and
two separate 96-context qualification streams were seed-bound there before any
structure or value.
[ADR-0306](docs/decisions/ADR-0306-freeze-capacity-filling-v4-source.md)
now passes and freezes the value-free source after exhaustive legality,
v3-superset, full-slot, provenance, projection, and bounded-work validation.
[ADR-0309](docs/decisions/ADR-0309-seal-capacity-filling-v4-structures-before-qualification.md)
now seals the three frozen value-free streams at 48/96/96 contexts after
239/570/451 raw card candidates. All are mutually unique and have zero
counterparts in the finite 748-context maintained inventory.
[ADR-0310](docs/decisions/ADR-0310-reject-capacity-filling-v4-on-qualified-b-numerical-failure.md)
rejects the ordered candidate-blind qualification. A reaches 24 qualifiers
after 73 contexts and passes all teacher controls, but B stops on the
full-integer arm of context 21 when the native simplex solution fails primal
verification. No final A/B panel exists, the representative and every
candidate value remain unopened, and v4 is parked. The next eligible boundary
is a separately preregistered candidate-independent native-simplex robustness
audit; it cannot repair and retry this v4 panel.
[ADR-0311](docs/decisions/ADR-0311-preregister-native-simplex-robustness-audit.md)
now freezes that audit before source or values. It prospectively binds one
known regression, 48 exactly enumerable micro LPs, 128 fresh candidate-free
sizing LPs, five exact metamorphic representations, and native/HiGHS-DS/
HiGHS-IPM arms with unit-specific reconstruction and certificate gates.
[ADR-0312](docs/decisions/ADR-0312-seal-native-simplex-audit-compiler-and-corpora.md)
now seals the value-free compiler, both prospective structures, the known
  regression snapshot, all 177 bases, and all 885 exact representations. The
  fresh 64-context structure is disjoint from the finite 988-context inventory
  through ADR-0310.
  No optimum or backend result existed at that ADR-0312 boundary.
  [ADR-0313](docs/decisions/ADR-0313-seal-native-simplex-audit-runner-before-results.md)
  now seals the runner and typed result schemas before results. It owns exact
  micro enumeration, all three fixed adapters, original-coordinate semantic
  reconstruction and outward bounds, complete failure capture, and the exact
  2,655-invocation schedule under CPython 3.14.6, NumPy 2.5.2, SciPy 1.18.0,
  and embedded HiGHS 1.12.0. Only unsealed toys had run at that source boundary.
  [ADR-0314](docs/decisions/ADR-0314-retain-native-simplex-audit-and-reject-frozen-gate.md)
  now retains the one-shot 2,655-observation result. Both HiGHS methods pass all
  885 arms; native records 849 verified returns and 36 failures. The literal
  frozen gate rejects on its sole `known-native-regression-mismatch` because
  it required maximum row 215 to be the entire above-allowance row set. HiGHS
  remained ineligible at ADR-0314. ADR-0315 source-seals the separately
  disclosed artifact-only correction and synthetic controls before
  authoritative access. ADR-0316's one exact-digest reanalysis passes with no
  corrected-gate failure and makes HiGHS dual simplex eligible only for a
  later prospective adapter evaluation. No backend or exact/certificate work
  is rerun. ADR-0317 now separates that adapter question from behavioral-master
  optimization. The active boundary is a source-sealed canonical HiGHS adapter
  for the compact reduced-sizing LP, with independent original-unit
  reconstruction and an outward certificate. Behavioral masters already use
  HiGHS and consume only 0.063%-0.151% of the two retained complete ledgers;
  persistence and specialization are parked until a fresh certified-v2 ledger
  crosses a 5% perfect-solver materiality trigger. If that trigger opens,
  persistent warm HiGHS remains the null hypothesis before any untrusted
  product-of-simplexes proposer. ADR-0318 now source-seals the separate
  canonical reduced-sizing HiGHS adapter and its exact behavioral/outward-bound
  acceptance path after toy-only controls. ADR-0319 now source-seals the
  failure-complete runner, one-call counters, exact ordered 177-base schedule,
  and immutable result schema. ADR-0320 retains the single sealed invocation:
  all 177 observations pass with no clips or failures and a maximum
  `8.50e-11`-chip sizing interval. A separately preregistered additive
  certified-v2 reduced-sizing consumer is now eligible. ADR-0321 freezes its
  exact research-only contract before source: two live seats at a river
  opening, fold/call-only responses, caller-supplied kernel-legal raise-to
  subsets, distinct raise-to-to-increment conversion, one certified public
  proposal, and typed no-action rejection to a caller-owned fallback. ADR-0322
  now source-seals that implementation after eleven unsealed semantic and
  corruption controls. ADR-0323 now preregisters a fresh finite-block
  action-width research owner before source, structures, or values. Its local
  authority is certified full/subset interval arithmetic over complete
  kernel-legal integer universes, with exhaustive anchored best-subset teachers
  at raise widths two through six. A direct block price is admitted only after
  the proposed size's complete fold/call rows are installed and their exact row
  identities retained. Development selects; one commit-derived fresh transfer
  population confirms or rejects. It opens no fresh action-width value.
  ADR-0324 now source-seals the first value-free layer: one 96-context fresh
  development population after 440 attempts, exact 7/9/11-raise kernel
  universes, and a 12,556-subset prospective work ledger. The source contains
  no solver or action path and cannot construct transfer. A separate ordered
  full-versus-width-two qualification runner must be source-sealed next.
  ADR-0325 now seals that owner and its exact 192-task schedule, conservative
  chip-interval classifier, complete stop/failure schema, and target-only panel
  rebinding. ADR-0326 retains its one authorized invocation: 51 contexts, 102
  one-call arms, 16 qualifiers, 35 nonqualifiers, zero ambiguity, and an exact
  16-context panel. Every retained endpoint and semantic request/legal/LP
  identity rebinds from the canonical artifact without solving. The next gate
  is source-only again: seal the panel's 2,495-task exhaustive teacher before
  any width-three-through-six value.
  ADR-0327 now passes that source gate. It freezes the exact 16-full/2,479-
  subset order, one-call/no-retry ownership, conservative chip and normalized
  regret, interval teacher envelopes, strict dominance, sole-survivor
  uniqueness, potentially empty reporting equivalence, and no-clobber result
  retention. The active gate is one retained invocation through the sealed
  artifact wrapper. It may measure plateau cardinality and the regret curve but
  cannot choose a greedy mechanism, construct transfer, or make a production
  action-width claim.
  ADR-0328 now retains that sole invocation: all 2,495 calls complete, the
  canonical artifact and solver-free rebinder reproduce every semantic and
  numerical identity, and width three is the first exhaustive-teacher width to
  pass the full-regret-only maximum/mean limits. It is not a selected width
  because greedy recovery and width-matched teacher excess remain unopened.
  The active boundary is source-only direct closed finite-block greedy
  ownership before any price, candidate value, transfer construction, or
  action path. ADR-0329 now passes that source gate: 2,479 exact arms, 7,848
  possible response-closed transitions, the exact 400-call realized-path rule,
  lower-endpoint/smaller-raise choice, all five frozen development conjuncts,
  failure-complete evidence, and no-clobber retention are sealed without
  opening a greedy value. ADR-0330 records the one invocation as a terminal
  artifact-boundary failure: 400 calls reached a completed-result path, but a
  self-referential width-gate digest prevented publication. No result or width
  survives, replay is permanently closed, and transfer remains unopened. The
  active boundary is source-only: seal a genuinely new untouched-population
  successor with synthetic success serialization and write-ahead evidence
  survival before any new value. ADR-0331 now prospectively freezes that
  successor's commit-derived seed, all-96 semantic non-overlap gate, self-free
  hash chain, fsynced append receipts, exact-prefix/torn-tail semantics, and
  402-record synthetic success requirement. The active gate is its additive
  value-free source and exact population/journal seal. ADR-0332 passes that
  gate: 96 new contexts are unique and fully disjoint after 551 attempts, the
  journal has no nonexclusive production constructor, and the 610,098-byte
  synthetic fixture survives all 402 complete-prefix cuts plus representative
  torn lines. No value was opened. The active boundary is source-only
  candidate-blind qualification on the sealed new pool before its first
  consumer call. ADR-0333 now seals that qualification owner and its exact
  policy/dual witness rebinder, receipt-gated 192-task schedule, semantic stop
  categories, and phase-typed failure-complete journal reduction without
  opening a value. ADR-0334 now records the one no-clobber retained invocation:
  the
  exact 100-record journal has 98 accepted arms, 49 complete contexts, 16
  qualifiers, 33 nonqualifiers, zero ambiguity, and a target terminal. The
  solver-free result owner reproduces every witness, classification, terminal,
  and exact target-only panel. The active boundary is source-only again: seal
  the new panel's 2,113-task exhaustive teacher before any teacher value;
  direct mechanism, transfer, latency, and action paths remain closed.
  ADR-0335 now passes that source boundary. It freezes 16 full and 2,097
  anchored-subset tasks, policy/dual endpoint reconstruction, conservative
  interval-max and survivor reductions, exact payoff-span normalization,
  receipt-gated write-ahead evidence, and distinct semantic versus
  infrastructure failures. Its 2,115-record completed fixture is synthetic and
  opens no value. The active boundary is one retained no-clobber invocation
  from a clean source commit; no direct mechanism, transfer, latency, or action
  path is eligible first. ADR-0336 now retains the completed real journal and
  solver-free curve. The frozen maximum-plus-mean gate and descriptive median
  knee first pass at width three, while two positive-lower tail contexts persist
  until width four. The active boundary is source-only implementation of the
  preregistered 376-call non-replay direct mechanism; its price and selection,
  transfer, latency, and action paths remain unopened.
  ADR-0337 now passes that source-only boundary. The complete 2,097-arm,
  6,543-transition graph, exact adaptive 376-call slots, response closure,
  behavioral-lower/smaller-raise choice, five gates, durable evidence, and
  378-record synthetic terminal are sealed before price. The active boundary
  is one retained no-clobber invocation from this clean source commit. No
  transfer, capacity, latency, action, or production-width path is eligible
  first.
  ADR-0338 now retains that sole invocation: all 376 calls are accepted, the
  exact 1,437,835-byte journal rebinds solver-free, and all five gates first
  pass at development raise width three. The context-local menus are not a
  fixed ladder, and no elapsed field or production claim exists. The active
  boundary is value-free construction and source sealing of the commit-seeded
  96-context untouched transfer population plus semantic non-overlap against
  both complete development pools and the maintained prior inventory. No
  transfer qualifier or value is eligible first.
  ADR-0339 now passes that source-only boundary. The first 96 admissible
  contexts occur after 478 candidates, expose 13,587 unopened anchored
  subsets, and have zero counterparts in the exact 1,244-context enumerated
  exclusion inventory. The active boundary is a separate source-sealed
  candidate-blind qualifier over this exact order. It must freeze the
  complete-universe-then-width-two schedule, unchanged classifier, first-16
  stop, durable receipts, and solver-free panel rebinding before any transfer
  value.
  ADR-0340 now passes that source boundary. The exact transfer-bound 192-task
  schedule, six semantic stops, post-`fsync` continuation, phase-typed raw-
  prefix failures, policy/dual evidence reuse, cross-campaign rejection, and
  target-only panel schema are sealed. The prospective artifact is absent.
  The active research boundary is its sole no-clobber retained invocation from
  a clean commit; no transfer teacher or direct-mechanism value is eligible in
  the same checkpoint.
  ADR-0341 now retains that sole invocation. The exact 378,108-byte journal
  reaches the first-16 target after 47 contexts and 94 accepted one-call arms;
  31 contexts are nonqualifying, no semantic or infrastructure failure occurs,
  and the remaining 49 transfer contexts stay unopened. The solver-free result
  owner seals the exact target-only panel and payoff-span-normalized threshold
  separation. Qualification is not width-three confirmation. The active
  boundary is a source-only transfer-confirmation owner that applies the frozen
  ADR-0338 context-local width-three mechanism without width reselection and
  preserves every unchanged development conjunct.
  ADR-0342 now passes that source boundary. It binds the 32 retained prior arms,
  126 prospective width-three candidate calls, complete response-closed
  transitions, the frozen direct selection, the same-call exhaustive teacher,
  and all five unchanged gates. Completed confirmation and completed rejection
  are separate scientific terminals; consumer, numerical, unexpected, and
  infrastructure failures retain distinct evidence. The prospective path is
  absent. The active research boundary is the sole no-clobber confirmation
  invocation from this committed source, followed by a solver-free result seal.
  ADR-0343 now retains that exact invocation and result seal. All 126 candidate
  arms are accepted; the 16 contexts complete; every direct selection equals
  the unique exhaustive-teacher winner; and all five unchanged transfer
  conjuncts pass. Width three is therefore confirmed on the untouched reduced
  panel without width reselection or abstention. The C5 path now opens the
  separately preregistered responder-raise and full-width-capacity lanes in
  parallel, while value-free blueprint and v0a engineering may continue.

[ADR-0307](docs/decisions/ADR-0307-make-action-clock-and-preparation-bank-authoritative.md)
now amends the governing resource contract before more v4 work. Each controlled
action receives one continuous 15-second response wall. Earlier-street and
opponent-turn compute can contribute only through an exactly matching prepared
artifact and is reported as attributable online work, not free latency or
literal deadline carryover.
[ADR-0308](docs/decisions/ADR-0308-install-the-action-clock-and-preparation-bank.md)
now passes the additive action-clock ledger, preparation bank, and exact-spine
v2 checkpoint with deterministic boundary, provenance, archive, and fallback
tests. It establishes accounting mechanics only: complete-hand/live-host
integration and useful preparation hit/quality evidence remain absent. Its
successor gate returned to ADR-0309's sealed v4 boundary; ADR-0310 has since
rejected that qualification while preserving every representative and
candidate value as unopened.

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

The first four exact-legality candidates were killed before integration: v1
on reduced sizing recovery, v2 on confirmation power, and v3 on qualified
aggregate recovery, then v4 on qualified-B numerical robustness. The next
checkpoint remains narrower than blueprint training or resolver integration.
ADR-0297
preregisters a four-by-four private-type game while holding the one-bet tree
fixed. The three-by-three pool failed its second yield replication and remains
parked. The width-four game now passes its frozen replicated yield and exact-
work boundary. Collision-repair v3 is implemented but rejected and parked.
Capacity-filling v4 is implemented as a frozen value-free source but rejected
by ADR-0310 when qualified B hits the native solver's numerical kill criterion.
Its A selection is provisional, no final evaluation panels exist, and every
representative and candidate value remains unopened. All four exact-legality
  action candidates are parked. Before another sizing campaign can be trusted,
  ADR-0311's candidate-independent native-simplex robustness audit had to pass
  its one-shot result boundary. ADR-0314 now records that complete campaign but
  rejects the literal gate on an over-specified known-regression row-set
  predicate. All 1,770 HiGHS arms pass, but no backend is replacement-eligible
  under ADR-0314. ADR-0316's source-separated correction now passes on the
  exact retained digest, making dual simplex eligible only to enter a later
  prospective adapter gate. ADR-0317 freezes that next gate for the compact
  reduced-sizing LP, whose legacy consumer still invokes rejected native
  simplex. It does not authorize v4 or any candidate value. The separate
  product-of-simplexes behavioral master already uses HiGHS; its perfect-solver
  ceiling is below 0.2% on both retained six-target ledgers, so persistent
  HiGHS and any untrusted specialized proposer remain parked under a 5%
  complete-ledger trigger. The passive reference source remains the emitted
  fallback. ADR-0318 seals the canonical reduced-sizing adapter source, and
  ADR-0319 seals its canonical 177-base validation runner, and ADR-0320 records
  its complete finite pass. ADR-0321 now preregisters the additive v2 consumer
  with exact legal-action/context binding and typed rejection before source.
  Because its reduced responder cannot raise, the consumer is explicitly not a
  six-player action chooser. Any wholly fresh action-width mechanism remains
  downstream of ADR-0322's now-passing source seal. The next owner must measure
  exact full-minus-subset chip regret and bounded best-subset teachers
  separately from fresh population transfer, and close both own-column and
  opponent-row violations before production action selection. ADR-0323 now
  freezes that owner's temporal and mathematical protocol. The immediate gate
  is value-free: implement and seal the independent 96-context development
  structure owner, exact kernel universes, and anchored subset schedules while
  leaving every sizing value and the commit-derived transfer population
  unopened. ADR-0324 passes that structural gate. The active boundary remains
  value-unopened: source-seal the owned candidate-blind qualifier, conservative
  chip-interval classifier, exact call schedule, stop state, and panel rebinding
  before its first ADR-0322 invocation. ADR-0325 passes that source gate. The
  single retained invocation now passes under ADR-0326 and freezes the exact
  16-context development panel after a 51-context prefix. The active boundary
  passes under ADR-0327: the complete 2,495-task exhaustive full/subset teacher,
  set-valued dominance/equivalence reductions, failure-complete result owner,
  and canonical no-clobber retention path are source-sealed without opening an
  intermediate-width value. The active boundary is exactly one retained
  teacher invocation. ADR-0328 completes that invocation and seals its exact
  artifact plus solver-free rebinder. Width three passes only the exhaustive
  full-regret conjuncts; the active gate is to source-seal the complete direct
  closed finite-block greedy schedule and result owner before values. ADR-0329
  passes that gate with a complete adaptive graph and exact realized-path call
  ledger. ADR-0330 closes its single invocation without a result after terminal
  width-gate serialization recurses. The partial witness survives, replay and
  transfer are forbidden, and no selected width exists. The next gate is a
  source-sealed non-replay protocol on a new commit-derived population whose
  synthetic success path and write-ahead journal prove evidence survival before
  any solver call. ADR-0331 passes that prospective protocol boundary without
  constructing the population or journal. Implement and source-seal only those
  value-free owners next; qualification and every new sizing value remain
  closed. ADR-0332 now passes that implementation boundary with exact all-96
  exclusion, durable append receipts, byte-preserving recovery, and a complete
  synthetic success rebinder. Source-seal only the replacement qualification
  owner next; its first value-bearing invocation remains a later checkpoint.
  ADR-0333 passes that source-only boundary with the exact 192-task order,
  conservative classifier, distinct reversal/rejection/unexpected stops,
  solver-free policy/dual endpoint reconstruction, post-`fsync` next-call
  authorization, and raw-prefix failure reduction. ADR-0334 completes the one
  retained public qualification invocation and seals the exact target-only
  panel from 98 accepted arms without replay. The next checkpoint is a
  source-sealed replacement exhaustive teacher with 2,113 frozen tasks; no
  width-three-through-six value or later mechanism is open. ADR-0335 now seals
  that exact owner and schedule, including a full success-shaped durable
  control and solver-free semantic reader. The next checkpoint is its sole
  retained invocation; all replacement teacher values and later mechanisms
  remain unopened until that call. ADR-0336 now seals the completed invocation
  and exact gate/median/tail distinctions. The next checkpoint is a source-only
  additive direct mechanism with 376 prospective calls and a complete durable
  synthetic terminal before its first value.
  ADR-0337 now seals that exact owner and full graph without opening any of its
  376 values. The next checkpoint is its sole retained invocation from a clean
  commit and absent no-clobber artifact; every later mechanism remains closed
  until the exact journal independently rebinds.
  ADR-0338 now closes that invocation with an exact accepted journal and a
  solver-free width-three development selection. Next construct and source-
  seal only the untouched transfer pool from the ADR-0337 source commit; prove
  all-prior semantic non-overlap and open no transfer value.
  ADR-0339 now seals that exact 96-context pool after 478 candidates, its
  13,587 prospective subset ledger, and zero intersections with the finite
  1,244-context exclusion inventory. Next source-seal only the candidate-blind
  transfer qualifier. Before any transfer value, freeze the interpretation:
  width three confirms only by passing every unchanged conjunct; a mean-only,
  14-of-16, or other partial pass is diagnostic and rejects unrestricted
  transfer. Any abstention policy is a new hypothesis requiring a new
  preregistration and untouched evidence.
  ADR-0340 now seals that exact transfer qualifier without opening value. The
  next checkpoint is one retained public invocation from a clean committed
  source and an absent path. Whatever terminal or infrastructure state occurs
  is final without retry; only an exact first-16 target may later authorize a
  separately source-sealed real panel result.
  ADR-0341 now seals that exact result and identity-only panel after the target
  is reached in 47 contexts. Next source-seal the transfer-confirmation owner
  before value. Raise width three is fixed, menu content remains context-local,
  and every unchanged conjunct must pass; mean-only, 14-of-16, or any other
  partial passage rejects unrestricted transfer.
  ADR-0342 now seals that exact owner without a real confirmation value. The 32
  retained full/width-two calls are prior evidence, while the only prospective
  ledger is 126 context-ordered width-three candidates. The same values supply
  the frozen greedy mechanism and exhaustive width-three teacher, and all five
  conjuncts remain literal. Next invoke the no-clobber owner once from a clean
  commit and preserve any terminal without retry; no width reselection or
  post-outcome abstention rule is authorized.
  ADR-0343 retains `completed_confirmed` from that sole invocation. The exact
  journal contains 126 accepted observations and all five conjuncts pass on all
  16 contexts. This closes untouched reduced-panel transfer in favor of the
  frozen context-local width-three mechanism. It does not close response-side
  width, responder raises, full-range capacity, or production integration.

The post-transfer C5 route has three coordinated lanes rather than one serial
queue:

- **Response semantics:** add responder raises first at small private width.
  Repeated action by a seat invalidates the path-single-visit behavioral
  shortcut, so the existing repeated-actor sequence-form keystone becomes the
  starting formulation. Treat response-row growth, selector stability in a
  deeper tree, multiway closure, and legal off-tree observed raises as
  separate preregistered gates. Repeated-actor multiway closure has no
  existence proof in the current stack and remains a research risk.
  ADR-0344 source-sealed the first finite gate before opening its result.
  Its checked-to river bridge obtains every integer action and terminal chip
  settlement from the authoritative six-seat kernel. The frozen tree contains
  both a full raise from two to four and the legal short all-in from three to
  four that the deliberately simplified legacy sizing game omits. Logical
  player zero repeats, so sequence form must match a separately enumerated
  16-by-18 pure-plan teacher. The one-hand gate does not independently test
  reopening and cannot establish h4 coefficients, row capacity, selector
  stability, multiway closure, latency, or quality.
  ADR-0345 now retains the sole clean invocation. All 24 gates pass: the six-
  node/eleven-terminal kernel schema, full and short-all-in branches, exact
  chip oracle, repeated-actor shortcut rejection, and the 16-by-18 complete-
  teacher agreement all hold. This crosses the one-hand gate and authorizes
  only a separately preregistered h4 legal responder-raise open-axis
  coefficient differential on the same public semantics. Response-row growth,
  selector stability, multiway closure, and off-tree observation remain
  separate gates. The 0.791-second tiny-game campaign is not an action-clock
  or capacity result.
  ADR-0346 source-sealed that exact next coefficient gate before opening a
  result. The same public tree is widened to four-by-four legal private hands
  with 32 exactly dyadic joint weights. The open actor has 12 information sets
  and 32 sequence variables, including 16 final-response variables. A separate
  Fraction enumerator must match all coefficients in four payoff and two gain
  rows and all six frozen endpoint values; its coverage tape reaches both full
  and short-all-in raise histories. The call graph forbids endpoint selector
  recomputation and any optimizer.
  ADR-0347 retains the sole clean invocation. All 34 gates pass: all 192
  Float64 coefficients equal their reduced Fraction counterparts, all 36
  affine/direct endpoint identities hold, the exact profile rows are zero-sum,
  both gain-row identities rederive, and both final-response histories carry
  nonzero coverage. A solver-free owner rejects byte drift and fully rehashed
  gain algebra corruption. This crosses h4 coefficient identity, not row
  capacity, selector stability, or latency. Next preregister responder-row
  growth on the unchanged h4 tree, keeping its response signatures,
  conditioning, oracle work, retained bytes, and infrastructure wall separate
  from selector and action-clock questions.
  ADR-0348 now source-seals that exact growth audit with no h4 trajectory
  opened. One read-only observer calls the unchanged production generator
  once; every complete signature and gain row is retained and independently
  checked with Fraction coefficients and fixed-tape terminal values. Exact
  feasibility/convergence classification, final incumbent feasibility,
  restricted-master diagnostics, oracle-call algebra, independently rebound
  conditioning, and canonical retained-row bytes are frozen. The 60-second
  subject and 120-second complete walls are infrastructure-only. Next invoke
  once from the committed source boundary and retain its first terminal; only
  a literal pass may preregister selector stability.
  ADR-0349 retains the sole clean invocation. All 25 gates pass: the two
  inherited exact rows close in one 18-pivot master, no row is generated, the
  exact finite-fixture incumbent is `27/64`, and the final gap is `2^-53`.
  Float64/Fraction rows and candidate evaluations have zero retained error;
  conditioning and oracle ledgers rebind exactly. The responder selector does
  change at the candidate, but its exact gain is zero and no cut is violated.
  This crosses finite h4 row-growth infrastructure, not selector stability or
  action latency. Next preregister a selector-window gate with a prospectively
  frozen policy family, complete tapes, tie rules, fixed-tape exact values, and
  conservative activation/envelope classifications.
  ADR-0350 now source-seals that exact selector normal-fan gate while every h4
  target value remains unopened. Its selector-free family contains three
  public-block one-step DCFR regret vertices and the retained-master proposal,
  each changing exactly one public history. A Fraction mapper uses sequence-
  form realization interpolation and reports `fixed`, `tie_unresolved`, and
  `switched` measures plus exact tie points. Total-function tape identity is
  the certificate authority; reachable-support identity is a separate
  behavioral column and never gates. Engineered crossing and full-measure tie
  controls make both unresolved paths real. All four one-public-history rays
  must reproduce the old exact margin/closing-slope breakpoint, and retained
  gain rows must form the correctly directed maximum envelope. The 17-point
  dyadic schedule fixes 136 production selector calls under bounded
  infrastructure walls. Next invoke once from the clean source commit and
  retain the first terminal; only a literal pass may preregister h4 selector-
  stable affine integration.
  ADR-0351 retains that sole invocation and overturns its nominal all-pass
  successor decision. The exact map survives: player zero is reachable tie-
  unresolved over the full interval on all four directions; responder
  breakpoints are exactly `15/19`, `139/163`, `1`, and `1`; the first two
  sections switch beyond their facet and the last two expose total-only
  endpoint ties with four and eleven phantom entry changes. All 136 production
  values, legacy differentials, affine rows, and maximum envelopes rebind.
  The v1 certificate does not: it returned scale one for four exact source
  ties because a nonclosing slope bypassed source separation. The solver-free
  owner therefore records four violations, rejects certificate passage, and
  authorizes nothing. `selector_window_v2` now makes margin-above-reserve a
  prerequisite before slope. Next preregister a tie-aware active-row-envelope
  integration recovery; never replay the closed mapper and never manufacture
  a unique tape from an unresolved set.
  ADR-0352 now source-seals that recovery while leaving every public h4
  integration value unopened. The exact oracle retains the bounded Cartesian
  closure of local maximizing total tapes, including distinct tapes with an
  identical affine row. The adapter uses v2 only for exact singleton sources;
  ties must fail closed in v2 and enter through the complete maximum envelope.
  Every identity pair carries both source and current pruned tapes, with total
  identity authoritative and reachable identity descriptive. The one-shot
  runner has zero production best-response calls and checks the exact envelope
  plus master direction `z >= row`. Pre-seal alternate-tape reconnaissance is
  disclosed and is not a gate, so a later same-fixture pass is development
  integration only and may authorize only a separately sealed fresh
  confirmation. Invoke once from the clean source commit and retain the first
  terminal.
  ADR-0353 retains that terminal as a clean rejection. The 961-byte artifact
  records only that at least one sampled exact local-maximizer product exceeded
  the frozen 256-tape bound after 64.651 seconds of complete infrastructure
  work. It contains no completed direction, section, active-set count, row,
  envelope, or adapter result. Never replay the owner or raise the observed
  bound. Next source-seal a factorized total active-set identity and compact
  exact affine-row quotient, prove both against exhaustive and overflow
  controls, and open no h4 target value until a separate diagnostic is
  preregistered. This representation arc remains independent of literal full-
  width capacity and supplies no action-clock or quality prior.
  ADR-0354 now source-seals that successor without opening a legal h4 target.
  One point instrument runs two independent exact lexicographic backward
  passes to minimize and maximize slope over the factorized active face; the
  existing exact normal fan remains the ray instrument that sees inactive
  rows crossing later. Total-function and reachable-support cardinalities are
  separate arbitrary-precision columns. A measurable work ledger reports
  zero materialized tapes, linear logical operations in the explicit tree,
  and exact-integer bit lengths; the billion-tape control passes over 61 tree
  nodes. The composed future-crossing seam, repeated-actor quotient, zero-
  support, positive-measure tie, and shared consumer-conformance controls pass.
  Next preregister one new exclusive legal h4 directional-face diagnostic over
  the four inherited directions and schedule. Do not invoke ADR-0352 again,
  and do not treat this source-only mechanism seal as h4, full-width, action-
  clock, quality, or strength evidence.
  ADR-0355 now preregisters that diagnostic and leaves its result path absent.
  The target is the exact four inherited directions by two players: eight
  composed fan/face sections and 136 separate calls on the unchanged dyadic
  schedule. Complete factor identities, total and reachable cardinalities,
  both slope extrema, fan cells/facets, seam checks, logical operations and
  integer bit lengths are retained. No cardinality, tie, crossing, slope, or
  cell-count outcome is gated. The 100,000 explicit-node and 256 fan-piece
  guards are not face bounds. Invoke once only after the source boundary is
  committed clean; preserve pass, rejection, or typed failure and never call
  ADR-0352. A pass can open only a later integration preregistration.
- **Capacity preflight:** in parallel with response semantics, price one
  label-free full-width river contraction and warm step on the exact
  1,225/1,081/1,035/990 belief axes. This is a representation, wall-time, and
  memory diagnostic only; it supplies no strategy-quality prior. A failure
  triggers representation work before more h32 optimization.
- **Blueprint and integration:** value-free blueprint kernel, abstraction,
  and isomorphism engineering may proceed independently now; training starts
  only after untouched transfer confirms the frozen width. Assemble **v0a**
  now as the exact legal spine plus immutable blueprint lookup through complete
  hands, including a deliberately uncertified river strategy, with certified
  legality, state transition, clocking, provenance, and fallback. It retires
  interface risk, not strategic risk. **v0b** later swaps in the certified
  full-width river strategy bridge after that bridge earns its own seal.
  Neither is a strength claim.

Before turn resolving, preregister cross-street range handoff, certificate
expiry, and anchor-epoch rules; this handoff has no current existence proof.
Before real play or league evaluation, run one preregistered off-tree bake-off
over pseudo-harmonic translation, a continuous-size interpolated action-
likelihood model, and an exact re-solve trigger. An adversarial bettor chooses
legal off-menu integers to maximize posterior error relative to exact ground
truth; compare belief total variation, downstream certified chip-value damage,
and charged wall time. No incumbent is adopted silently. Before claiming
preparation value, freeze what the preparation bank
builds, its exact keys, invalidation and eviction rules, and a cheap baseline
that warms the highest-blueprint-probability opponent continuations. Before
strength evaluation, freeze the opponent pool: passive source, blueprint-only,
prior versions, and simple exploiters at minimum.

## C6: Neural blueprint and leaves

Begin value-free compiled MCCFR, card-abstraction, isomorphism, checkpoint, and
data-contract engineering while C5 transfer work proceeds. Start the first
long training run only after untouched transfer confirms the frozen action
width and five prerequisites are sealed: trainer semantics, checkpoint/resume
identity, abstraction identity, the transfer-confirmed action lattice, and an
operational slice-certification audit pipeline capable of aborting a
pathological run early. No compute rental precedes that gate. Add river-to-flop
teachers and policy/value/action/uncertainty models behind the exact runtime
contract. Pass on root-strategy harm at equal latency, not value-function mean-
squared error alone.

## C7: Adaptive public-belief search

Add dynamic width/depth, continuous action proposals, residual solving, and
street/player specialization. Adaptive search must Pareto-dominate fixed search
at multiple budgets with no material rare-branch vulnerability.

## C8: Cache and speculation

Add range-aware caches, topology/embedding reuse, pondering, and preemptible
future-state work. Future decisions must improve without degrading current-
decision p95 latency or reusing a strategy across incompatible beliefs.
Preregister the preparation-bank filling policy separately: candidate events,
exact provenance keys, resource caps, invalidation, eviction, miss accounting,
and preemption. The transparent baseline prewarms the legal opponent
continuations with highest immutable-blueprint probability; a learned policy
must beat that baseline rather than an empty bank.

## C9: Learned value-of-computation scheduler

Train only after a richer workload demonstrates enough attainable value to pay
for inference and training. A learned scheduler must beat the best transparent
heuristic on hidden games and full traces; otherwise retain the heuristic.

## C10: Full evaluation

Require exact reduced-game results, adversarial responders, complete cross-play
matrices, paired-deal confidence intervals, latency and memory profiles, and all
major ablations before a defensible final report.
Freeze the league cast before evaluating the candidate: passive source,
blueprint-only control, prior Pontius checkpoints, and simple targeted
exploiters, with AIVAT-compatible hand histories and seat-balanced paired deals.
