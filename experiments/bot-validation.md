# Bot integration, evaluation, and evidence quality

[Results index](RESULTS.md) · Consolidated 2026-09-08 · Engineering and descriptive play

**Conclusion:** Pontius has a functioning bot/runtime and reusable evaluation
plumbing. The retained checks support legal action handling, hidden-information
boundaries, replay, settlement, and finite local execution. They do not yet
establish a strong full-game policy. The current bot's blueprint lookup path
and the research library's reduced-game search successes are separate assets;
connecting them still requires evidence.

The small trained river pilot exposed a deterministic-export quality loss.
A follow-up weighted-policy experiment preserved the teacher's quality. Native
weighted artifacts passed 100 direct hand checks and 36 real subprocess sessions.
A fresh six-board panel then passed 576 direct hands and 48 subprocess sessions.
Quality held on all four trained boards, but uncovered boards used a weaker
passive fallback and changing range priors damaged some covered policies. Coverage
and range assumptions are now the practical bottlenecks demonstrated by this panel.
The first follow-up candidates were rejected: a coarse range-strength fallback
helped on average but harmed an already-safe case, while simple prior pooling
worsened the mean worst tested result. Both executed correctly; neither merits
adoption under the declared quality limits.

Use this page for “what can the bot actually do?” Use [Blueprint cost](blueprint-performance.md)
for timing and artifact limits, and [Safe search](safe-search.md) for research
candidate quality. Source acceptance, completed games, and winning poker are
different claims throughout this summary.

## Capabilities and their demonstrated boundaries

| Area | What is supported | What remains outside the evidence |
|---|---|---|
| Legal complete-hand reference | Explicit-deal six-seat fixtures exercise public/private views, betting order, all-in transitions, independent side-pot arithmetic, and passive fallback. [ADR-0288](../docs/archive/ADR-0288-complete-reference-hands-pass-the-exact-one-seat-loop.md) | The passive reference is untrained. Fixed replay correctness is not opponent adaptation or strategy strength. |
| Belief and policy interface | Full-width card domains and an immutable rational policy crossed the reference-hand interface. [ADR-0290](../docs/archive/ADR-0290-full-width-belief-and-rational-policy-cross-the-reference-hand.md) | This was not validated scalable five-opponent value contraction, full-game training, or a connected strategy-producing resolver. |
| Runnable bot path | The maintained table host and session tool execute blueprint and fixed baseline providers, with action legality checks, clocks, child-process cleanup, and a portable blueprint codec. [Runtime milestone](../docs/archive/ADR-0489-close-the-v0a-engineering-milestone.md), [codec record](../docs/archive/ADR-0491-source-seal-the-portable-blueprint-artifact.md), [README](../README.md) | These are engineering components. A portable artifact format does not supply a trained blueprint. |
| Active diagnostic blueprint | **48 one-hand sessions / 24 matched pairs** passed in 20.674 s on Python 3.14. A 64-entry table exercised bets, re-raises, folds, all-in calls, side pots, refunds and intentional misses; all trajectories and payout checks matched. [Active-action evidence](blueprint-performance.md#what-changed-and-what-remains-open) | Constructed test keys and actions, with shared betting/ranking code and a separate payout calculation. No trained strategy, fresh-state coverage or strength result. |
| Repeated nonempty sessions | The preparation comparison completed eight three-hand sessions across two strategies, two source versions, and Python 3.11/3.14; actions, settlements and carried stacks matched controls. [Preparation report](../docs/architecture/v0a-blueprint-preparation-r001/performance-report.md) | One table entry and few decisions; these integration controls do not measure large-table throughput or worst-case response latency. |
| Fixed-policy paired evaluation | **48 trials / 24 matched pairs** completed, using two deals, six seats, two opponent lineups, and two fixed policies. All unit cleanups completed. [Retained comparison](D:/Pontius/tmp/v0a-paired-evaluation-run-001/comparison-report.md) | Only two deals; seat and lineup repetitions are not 24 independent deal samples. No general policy ranking follows. |
| Current CPU behavioral coverage | After native weighted support, Python 3.14 exercised **559 cases through 44 suites: 549 passed / 10 optional SciPy skips**. The earlier cleanup check exercised 552 cases: 542 passed / 10 skipped on 3.14 and 541 passed / 11 skipped on 3.11. [Journal](../execution_journal.jsonl), [manifest](../tests/cases.json) | Fresh CPU verification of native weighted support; no new 3.11, optional SciPy, GPU or poker-strength claim. |
| Current benchmark lifecycle | A persistent worker completed the focused construction and session checks. The larger reuse check retained 30/32 cells at its time limit and confirmed cleanup. [Blueprint summary](blueprint-performance.md) | Whole-job supervision improves observability; it does not establish large-table memory or live latency bounds. |

## Trained river policy: integration passed, projection rejected

The [dated experiment](2026-09-08-trained-river-blueprint.py) trained existing
DCFR for 2,000 iterations on one exactly enumerable heads-up river game: an
8-chip pot, a fixed 4-chip bet, four private hands per player and 16 compatible
joint deals. The bettor can check or bet; the responder can fold or call. This
restricted game excludes raising and betting after a check.

Training took **1.373 s**; the full pilot took **2.118 s** on Python 3.14.6.
Exact evaluation compares the mixed average policy, its argmax projection into
the current single-action codec, and check/call fallback. NashConv is the sum
of the two players' unilateral best-response gains, in chips; lower is better.
It is not a win rate or an exploitability estimate for full poker.

| Policy | NashConv on training model | Exploitability (NashConv / 2) |
|---|---:|---:|
| Learned mixed average | 0.000685585 | 0.000342793 |
| Exported single-action projection | 2.000000 | 1.000000 |
| Passive check/call profile | 2.000000 | 1.000000 |

The teacher passed its fixed **0.02-chip** convergence limit. Projection added
**1.999314415 chips** of NashConv, exceeding the fixed **0.08-chip** allowed
increase. **Do not adopt this projected artifact as a quality-preserving export.**
The mixed teacher bets the two weak hands about 33.3275% of the time and calls
with each bluff catcher about 66.6554%. Argmax removes those bluffs and turns the
calls into certainty. The projected profile's higher bettor self-play payoff
(+2 chips versus the teacher's approximately +1.33333) does not rescue it: the
opponent has a 2-chip profitable deviation against that exported profile.

Changing only the bettor's prior value-hand mass to 25% or 75%, without
retraining, raises the teacher's NashConv to 0.667394 and 1.333450 respectively.
Projection and passive control remain equal at 1 and 3 chips respectively.
These are exact range-sensitivity probes over the same hand support, not
held-out-hand or full-game generalization tests.

The exported artifact contains **13 entries / 10,944 bytes**: eight learned
river entries and five prescribed preflop setup entries. A reachable six-seat
prefix folds seats 3, 4, 5 and 0, raises the small blind to four, calls the big
blind and checks flop/turn. This produces the modeled heads-up river with an
8-chip pot and 196 chips behind each active player.

**100 direct `HandRuntime` replays passed.** These cover all 16 deal pairs in
both controlled roles against three fixed opponent continuations, plus four
changed-board/changed-private-hand controls. All **72 supported modeled river
decisions** hit and matched the projected teacher; all four unsupported modeled
decisions missed and used fallback. Twenty-four unmodeled check-back decisions
also used fallback. Across all streets there were 400 decisions: 72 learned
river hits, 50 setup hits and 278 fallback decisions. All actions, deliveries,
settlements and accounting checks passed; six aggregated runtime payoffs
matched exact microgame evaluation. Maximum observed response wall time was
0.6789 ms. This direct interface check excludes subprocess/session transport,
and settlement/ranking code is shared with the existing library.

The [complete result](results/runs/ab92e996889a41a08c8c3f4e75d54b1f/result.json)
retains the [mixed teacher](results/runs/ab92e996889a41a08c8c3f4e75d54b1f/teacher.json),
[artifact](results/runs/ab92e996889a41a08c8c3f4e75d54b1f/blueprint.json), design,
projection, mapping, runtime hands and exact driver. Production source verified
against `b378104cd2934f248a9545d7d482b0db25db813c`; driver SHA-256 is
`6b56a0d79e0cff635143d428af98e6be18da8f214e99e14c5205a1371eabdd9f`.
The [first attempt](results/runs/41bacc242cd445e9a38e709bd41aba22/result.json)
completed training/evaluation but stopped on the experiment adapter's incorrect
`applied_action` field. The corrected adapter reads `selected_action`, checks
the actual mailbox receipt and verifies the applied state. Both attempts remain
retained locally and uncommitted. Production code was unchanged.

## Weighted river policy: quality preserved in the research prototype

**Question:** Can serialization and action sampling preserve the same trained
teacher that single-action export damaged? The existing dated experiment's
`--mixed` arm loaded the previous hash-checked teacher without retraining. It
stored integer action weights summing to 1,048,576, using largest-remainder
rounding, and recovered probabilities with the library's exact rational type.
The experimental JSON uses abstract river keys; it is not a new production
artifact version.

The limits were retained before execution: maximum probability error of
1/1,048,576; maximum NashConv increase of 0.08 chips; and at most 1.5 percentage
points of frequency error over 20,000 draws per information set. Exact evaluation
uses all 16 deals and best responses in the restricted game, not sampled win rates.

| Representation | NashConv, chips | Increase from teacher |
|---|---:|---:|
| Frozen mixed teacher | 0.000685585330 | — |
| Recovered weighted policy | 0.000686645508 | 0.000001060177 |
| Previous single-action export | 2.000000000000 | 1.999314414670 |

**Quality passed.** Maximum probability error was 0.000000294916. Extremely small
check probabilities on the value hands rounded to zero; that rounding is included
in the exact quality calculation. The weighted policy also closely retained the
teacher's range-probe results: NashConv 0.667397 with value-light weights and
1.333450 with value-heavy weights. It preserves the original strategy, including
its sensitivity to changed priors; it does not solve that sensitivity.

**Sampling and execution passed on Python 3.14.6 in 12.408 seconds total.**
Across eight information sets, 160,000 sampled choices had a maximum frequency
error of **0.45465 percentage points**, below the fixed 1.5-point limit. All
28 nonempty action-interval boundary checks passed; zero/one probabilities
produced the corresponding impossible/certain actions. Each information key
uses its own seeded hash draw, with separate frequency-test and runtime nonces.

The experiment sampled a complete deterministic table anew for each hand and
passed it through the existing codec and direct `HandRuntime`. This implements
the intended mixture in this microgame, where each player has at most one learned
decision per hand. **772 cases plus 48 additional replay hands passed**:

- 768 supported cases covered all deals, both controlled roles, three opponent
  modes and eight seeded repetitions. Every net payoff matched the abstract
  game's terminal calculation; all 768 regenerated sampled artifacts matched.
- 595 learned river decisions comprised 253 bets (runtime action kind `raise`),
  131 checks, 139 calls and 72 folds. All hit the sampled table. These counts
  reflect the designed population and conditional reach, not global frequencies.
- Four changed-board/private-hand cases exercised explicit fallback. The 48
  repeated hands reproduced actions and final stacks. Action delivery, applied
  state, settlement, chip conservation and accounting assertions all passed.

Maximum observed response wall time was **0.7725 ms** in the 772 retained cases.
Sampling and table export occurred outside the runtime's charged interval;
this is not an end-to-end mixed-provider latency or tail bound. The 1,145-byte
weighted JSON contains eight abstract-key rows; the sampled production artifacts
contain 13 full-key rows and occupy 10,938–10,944 bytes. Those are different
representations and scopes, so their sizes do not establish a compression gain.

**Next at the prototype stage:** Add native probability-preserving artifact/provider support, with
per-decision randomness, reproducible test replay and explicit unsupported-state
fallback. Then repeat quality checks through real subprocess sessions and charge
decode, preparation and sampling to the runtime ledger. The prototype's public
research seed is a reproducibility device, not a live randomness design.

The [complete result](results/runs/0a09e4f83c8646b3b00d1d366abfd895/result.json),
[sampling counts](results/runs/0a09e4f83c8646b3b00d1d366abfd895/sampling.json),
[weighted policy](results/runs/0a09e4f83c8646b3b00d1d366abfd895/weighted-policy.json)
and runtime records are retained with the design and exact driver. Production
source verified against `b378104cd2934f248a9545d7d482b0db25db813c`; driver SHA-256
is `b4784922e88127e252f1ed7731b46067fce25f9c1abdba5b2347338292675f3d`.
The result's `export_adoptable` flag means the research quality gate passed;
it does not approve a native production integration. This run and the experiment
changes remain local and uncommitted. No production source changed.

## Native weighted artifact and subprocess sessions

**Question and change:** Can the same teacher execute through a single weighted
production artifact, with action sampling inside the normal clock? The existing
blueprint model now accepts a `WeightedBlueprintAction`: distinct semantic
actions with positive integer weights totaling less than `2**63`. Artifact v2
encodes these choices; deterministic artifacts retain their v1 bytes and
identities. The prepared lookup validates every supported action before drawing
from system randomness. Unknown keys retain passive fallback. The existing
rule-based baseline rejects weighted fallback tables because its separate
verification path assumes a deterministic fallback.

**Method:** The dated experiment's `--native --development` arm loaded the same
hash-checked teacher, rounded weights to a total of 1,048,576 and exported full
production keys. It recovered the probabilities from the decoded production
artifact and reran exact game evaluation. Limits remained a maximum probability
error of 1/1,048,576, a 0.08-chip NashConv increase and 1.5 percentage points of
frequency error over 20,000 calls per information set. Certain-action rows do
not require a random draw.

| Check | Measured result |
|---|---|
| Native decoded policy quality | NashConv **0.000686645508**, versus teacher **0.000685585330**; increase **0.000001060177 chips** |
| Precision and sampling | Maximum probability error **0.000000294916**; maximum frequency error **0.61965 percentage points** over 160,000 selection calls |
| Artifact | **13 entries / 11,617 bytes**: eight learned river distributions and five deterministic setup entries |
| Direct runtime | **100 hands passed** across both roles, three opponent modes and unsupported-state controls; 96 supported net payoffs matched the abstract game's terminal calculation |
| Real subprocess sessions | **36/36 one-hand sessions passed**: 32 supported bettor cases and four changed-board/private-hand controls; all 144 decisions passed action, timing and accounting checks |
| Runtime behavior | 32 learned river hits: **23 bets and 9 checks**; four unsupported river misses used fallback; all actions were in the relevant positive-probability support |
| Timing | **16.851 s** complete experiment; maximum session response **0.7345 ms**; maximum per-hand charged compute **2.7718 ms**, including preparation and sampling |
| Lifecycle | One persistent controller worker; child/session completion, accounting and worker-job cleanup passed |

The session population uses a passive big blind and four fold-to-bet opponents
to reach the fixed river prefix while controlling the small-blind bettor. Both
player roles are covered directly; the subprocess evidence does not cover a
learned responder against an arbitrary scripted bettor. The response and hand
compute numbers come from runtime accounting. Initial file decoding and process
startup remain outside that hand ledger and are included in complete experiment
wall time. These small samples establish neither tail bounds nor near-cap costs.

**Outcome:** The native bridge preserves the teacher's restricted-game strategy
and executes its mixture through real sessions. This justifies moving to a
fresh, separately evaluated panel of boards, private hands and opponent
continuations. Exact-history coverage, action-menu coverage and changed-prior
quality must be measured; this result does not establish full-game strength.

The full maintained Python 3.14 suite exercised **559 cases: 549 passed and ten
optional SciPy cases skipped**, in 128.060 seconds. Seven new checks cover codec
round trips, malformed weights, deterministic compatibility, seeded repeatability,
owned probabilities, legality of the complete support, misses, baseline refusal,
and sampling/cutoff accounting. The focused red run failed on the absent weighted
type before implementation; the subsequent affected 314-case run passed.
Ruff reports four existing lambda/unused-local findings in the touched files;
the new code introduces no additional findings.

The [successful result](results/runs/ae0c45a6ea4543f38fd5cd5a4cad24ec/result.json)
retains the [native artifact](results/runs/ae0c45a6ea4543f38fd5cd5a4cad24ec/blueprint.json),
session inputs and raw child output, direct hands, teacher, recovered policy,
sampling frequencies, design and exact driver. The
[first attempt](results/runs/df124009cd604856ad3d50a598b7654e/result.json) completed
the direct checks but the session adapter supplied card strings instead of the
required integer IDs. It stopped before completing a session and verified cleanup;
the corrected run remains separate. The
[full test result](results/20260909T000703-fe6044a5.json) records the maintained suite.

Both native runs used unreviewed development source based on
`b378104cd2934f248a9545d7d482b0db25db813c`, with working-source SHA-256
`f2be77cfeab17add27bc0ed89f0bbab7851da9497f29e75aa645a25f77e62820`.
The successful driver SHA-256 is
`24effd01435568a027ded3c657d63dc9d0ed042bfb7a00470bae966a960d0d0b`.
These changes and outputs remain local and uncommitted.

## Six-board panel: export passes, coverage and priors remain limiting

**Question:** Does the native bridge preserve quality across a small, declared
panel, and what happens where its table has no learned entries? The dated
experiment's `--panel --development` arm fixed six new board textures and
four private hands per player before training. Python seed `2026090901` selected
16 distinct private cards per board, giving 16 compatible joint deals per root.
Declared integer prior weights vary across roots. Each root uses the same pot-8,
bet-4, 196-behind river microgame and reachable six-seat prefix as the earlier
pilot. No raises, check-back betting or folded-card belief model are included.

Four boards contribute learned entries. The artifact is then frozen before
training reference policies for the two deliberately uncovered boards. These
references measure the cost of fallback; they do not enter the deployed table.
Preflop setup entries include all six boards' private-hand populations, so each
coverage check reaches its intended river. This is a finite constructed panel,
not a random sample of full poker or a test of a learned generalization model.

**All declared gates passed:** 2,000 DCFR iterations per root, teacher NashConv
at most 0.02 chips, supported export increase at most 0.08 chips, and supported
probability error at most 1/1,048,576. `quality_passed` applies to convergence and
supported export; it does not assert that uncovered fallback retains teacher
quality. Evaluation enumerates the complete restricted game and its best responses.

| Board / population | Learned keys | Teacher NashConv | Deployed NashConv | Passive NashConv |
|---|---:|---:|---:|---:|
| Dry: Ac 9d 6h 4s 2c | 8/8 | 0.000659360 | 0.000659943 | 1.666667 |
| Connected: Jh Th 9h 3c 2d | 8/8 | 0.000685585 | 0.000686646 | 2.000000 |
| Paired: Qc Qd 8s 5h 2s | 8/8 | 0.000230990 | 0.000230372 | 0.500000 |
| Monotone: Ah 8h 5h 3d 2c | 8/8 | 0.000269372 | 0.000268936 | 0.750000 |
| Straight board, uncovered: 9c Td Jh Qs Kc | 0/8 | 0.000000005 | 0.333333333 | 0.333333333 |
| Low board, uncovered: 8d 6c 4h 3s 2d | 0/8 | 0.000055331 | 0.666666667 | 0.666666667 |

The largest supported export increase was **0.00000106018 chips** and maximum
probability error **0.000000458414**. Tiny negative increases on two roots are
rounding effects, not evidence of a superior solver. Argmax controls scored
1.333333, 2, 0.3125 and 1 chips on the four supported roots respectively; preserving
mixtures remains useful across these cases. On the straight-board holdout, the
reference argmax happens to have zero NashConv, so projection is not universally
harmful in every game.

**Range sensitivity is separate from table coverage.** Reversing the declared
bettor prior weights, keeping the policy and keys fixed, changed deployed
NashConv on the connected, paired and monotone roots to **0.889750**, **0.476015**
and **1.111140** chips respectively. The dry root's uniform prior was unchanged,
so its reversal is a no-op control. Weighted export still closely follows its
teacher under the changed priors; this is model sensitivity rather than a codec
loss. Current information keys do not carry an inferred range or policy-selection
context. More exact-key entries alone would not fix a wrong prior at an already
covered state.

Exact evaluations against check/call, bet/call and bet/fold continuations cover
each controlled role for every root. Their full payoff tables are retained in
the result. On covered roots, export preserves these teacher payoffs to within
about 0.0000027 chips. On uncovered roots, passive fallback can outperform a
reference against a particular weak opponent yet have higher NashConv; an
individual fixed-opponent payoff is not a general strategy ranking.

**Execution and cost:** Python 3.14 completed **576 direct hands and 48 real
one-hand subprocess sessions in 37.739 seconds**. Each root had 96 direct hands
(all 16 deals, both roles and three declared opponent modes) and eight subprocess
sessions controlling the bettor against the existing passive big blind. All
576 direct net payoffs matched the abstract terminal calculation. Direct modeled
decisions produced **280 learned hits and 136 fallback decisions**; these counts
depend on which states the fixed continuations reach.

The subprocess sessions produced **32 learned river hits and 16 deliberate
uncovered misses**. The 32 hits selected 16 bets and 16 checks. All actions,
payouts, chip conservation, accounting and cleanup checks passed. The designed
32/48 session coverage is not an estimate of coverage in real play.

| Root | Subprocess sessions | Maximum response, ms | Maximum charged hand compute, ms | Standalone learned rows, bytes |
|---|---:|---:|---:|---:|
| Dry | 8 | 0.6237 | 5.8724 | 8,129 |
| Connected | 8 | 0.7223 | 5.3751 | 8,303 |
| Paired | 8 | 0.8099 | 5.5344 | 8,246 |
| Monotone | 8 | 0.7607 | 5.3609 | 8,179 |
| Straight, uncovered | 8 | 0.6780 | 5.7563 | No learned rows |
| Low, uncovered | 8 | 0.6952 | 6.1544 | No learned rows |

The combined artifact has **55 entries / 48,097 bytes**: 32 learned river
distributions and 23 distinct deterministic setup keys (one private hand is
shared across roots). The standalone row sizes above exclude setup entries and
each include their own small source envelope. Hand compute includes preparation
and sampling; file decoding and process startup remain outside that ledger and
inside the complete wall time. Eight sessions per root do not establish tails,
and this artifact is far below the 1 MiB cap.

**Next decision:** Shift the practical track from export mechanics to coverage
and range robustness. A small controlled comparison should test a broader river
policy or fallback against passive play, while evaluating the same covered
policies under explicitly varied priors. Judge both worst tested deviation gain
and complete-policy behavior including misses. Keep a fresh final panel separate
from these development cases; adding the holdout oracles to this table would
improve its declared coverage but would not establish generalization.

The [complete result](results/runs/a1cb79a0f79c4ea6988107ee59c5fadc/result.json),
[fixed design](results/runs/a1cb79a0f79c4ea6988107ee59c5fadc/design.json),
[artifact](results/runs/a1cb79a0f79c4ea6988107ee59c5fadc/blueprint.json),
teachers, recovered policies, direct hands and full subprocess outputs are
retained. This was unreviewed development source based on
`b378104cd2934f248a9545d7d482b0db25db813c`, with working-source SHA-256
`f2be77cfeab17add27bc0ed89f0bbab7851da9497f29e75aa645a25f77e62820`.
Driver SHA-256 is `718c7007927bfefee8382c689b7601c090dbd24c6f822b62aedbd25f2ac74289`.
Only the experiment and summaries changed for this panel; the production source
is the same one covered by the previous 549-pass / ten-skip CPU run. No new full
CPU test run or production optimization is claimed. Outputs remain local and
uncommitted, with one panel outcome in the journal.

## Coverage and robustness candidates: both rejected

**Question:** Can a transferable fallback improve uncovered situations without
large regressions, and does training on pooled priors improve robustness? All
six previous roots became development data. Before fitting candidates, the
experiment fixed three new boards and four-hand ranges with seed `2026090902`:
Kd Tc 7h 5s 2d, 8c 8h 6s 4d 2h, and As Qd 9s 6h 3c.

The fallback groups information sets by player role and one of five range-equity
bins, then averages development teacher probabilities equally within each bin.
Equity is computed against the supplied uniform four-hand opponent support,
which stays fixed across prior probes; it is not the opponent's dealt hand or
a range inferred from history. Nine feature groups were observed in development.
Three final responder information sets used an unseen group and received the
declared check/call default. No final-root teacher labels entered this fallback.

The pooling candidate trains separately on each final root using the equal
mixture of normalized anchor and reversed bettor priors, leaving the responder
prior unchanged. The fixed-prior control trains on the anchor model. Both use
2,000 DCFR iterations; all six fits passed the 0.02-chip training NashConv limit.
Pooling optimizes that average game; it is not a minimax algorithm. The passive
control has setup entries only and defaults at every river decision.

Each decoded candidate is evaluated exactly under five declared cases: anchor,
reversed bettor prior, early-hand concentration, late-hand concentration, and
reversed responder prior. The three new boards are final transfer cases for the
fallback. The anchor/pooling recipes train on those boards, so their evaluation
concerns prior sensitivity, not unseen-board transfer. No final results were
used to select bins, pooling weights or acceptance thresholds.

**Acceptance required** at least 20% improvement in the mean of each root's
worst tested NashConv, with no individual scenario or anchor case worsening by
more than 0.08 chips against its control. The following values are **worst tested
NashConv across the five cases**, not mathematical worst cases over all priors:

| Fresh root | Passive | Transfer fallback | Fixed-prior policy | Pooled-prior policy |
|---|---:|---:|---:|---:|
| Middle rainbow | 3.111111 | 1.025445 | 0.630889 | 0.740593 |
| Low paired board | 0.000000 | 0.829713 | 0.000000 | 0.000000 |
| High two-tone | 0.642857 | 0.486574 | 0.000000 | 0.000000 |
| Mean of root worst cases | **1.251323** | **0.780577** | **0.210296** | **0.246864** |

**Transfer fallback: reject.** Its mean worst result improved **37.62%** over
passive, passing the average-improvement gate. However, its largest scenario
regression was **0.829713 chips**, well above 0.08. The low-pair root is a concrete
counterexample: passive has zero NashConv under every tested prior, but the
fallback damages it. There the candidate bets Qd Ks about **31.11%**, while the
three other bettor hands bet only about **0.002575%**; two responder hands still
fold about **63.56%**. This suggests that averaging by individual range strength
lost important information about the composition of the betting range. It does
not prove that all range-based abstractions fail.

**Pooled prior: reject.** Its mean worst result worsened **17.39%** against the
fixed-prior control. On the middle-rainbow anchor case, NashConv rose from
0.000525 to **0.266612**, a **0.266087-chip** sacrifice. Pooling helped the reversed
and early-concentrated cases but lost on the anchor and late-concentrated cases.
Only one of the three roots had nonzero fixed-policy stress NashConv, so this
small panel cannot rank robustness methods generally. It does reject this fixed
pooling recipe under the stated objective.

**Execution passed in 65.649 seconds:** 768 direct hands, with independently
checked abstract terminal payoffs, and **96/96 subprocess sessions / 384 decisions**.
Each arm had 24 sessions. The three materialized candidates hit all 24 modeled
river decisions; passive missed all 24 as intended. These are finite generated
tables, not installation of a general live fallback. All actions, payouts,
accounting and four worker-job cleanups passed. Maximum session responses were
0.6686 ms passive, 0.7477 ms fixed-prior, 0.7416 ms pooled, and 0.6913 ms fallback;
maximum charged hand compute across arms was **5.7355 ms**. Feature calculation
and materialization occurred offline and are not included in those hand clocks.

The 60 export comparisons passed: largest NashConv increase **0.000000665723**
and probability error **0.000000339195**. Quality failures therefore belong to
these policy methods rather than serialization. Passive occupies 8,155 bytes /
12 setup entries; the other artifacts have 36 entries and occupy 32,086–32,468
bytes. No tails, near-cap costs or full-game win rates follow.

**Next:** Keep both candidates out of the bot. Use the low-pair counterexample
to test whether adding betting-range composition preserves useful fallback
behavior, and give any robustness candidate an explicit worst-case objective
rather than assuming prior averaging supplies one. A per-situation acceptance
check with fallback is worth comparing with unconditional replacement. These
failed final cases are now development evidence; any revised candidate needs a
new frozen final panel. The existing baseline remains the control.

The [complete result](results/runs/df12e8b5392a47da86bdeb4d21a1e4c1/result.json),
[design](results/runs/df12e8b5392a47da86bdeb4d21a1e4c1/design.json),
[frozen fallback](results/runs/df12e8b5392a47da86bdeb4d21a1e4c1/frozen-fallback.json),
candidate/decoded policies, exact driver, artifacts and all hand/session outputs
are retained. Sixteen retained output hashes and 100 input hashes were verified.
The run used unreviewed development source based on
`b378104cd2934f248a9545d7d482b0db25db813c`, with source SHA-256
`f2be77cfeab17add27bc0ed89f0bbab7851da9497f29e75aa645a25f77e62820`.
Driver SHA-256 is `962a89fc5b51ef49c7934c5f29c4b1c187027276d892a72790b859ccd2268cc5`.
Production code is unchanged from the preceding native verification. This
comparison has one completed journal outcome with both candidate gates false;
the successful execution status is not a policy-adoption approval. Work and
outputs remain local and uncommitted.

## What the actual paired poker results say

The retained comparison reported these exact totals:

| Fixed control policy | Net chips across its 24 trials |
|---|---:|
| Baseline rules | -18 |
| Empty-blueprint passive fallback | +101 |
| Baseline minus blueprint | -119, or -119/24 per matched pair |

The sign is stated explicitly because reversing the subtraction reverses the
story. The empty blueprint generated 64 passive-default decisions: 26 calls and
38 checks. It was not a trained policy. Large opposing seat totals and the two
underlying deals prevent treating the overall total as a win-rate estimate or
evidence to choose the passive policy. The result establishes working paired
arithmetic and a descriptive outcome on those fixed controls.

The old run took 382.532 seconds from parent launch through exit and retained
269 output files totaling 917,500 bytes. Those figures belong to that older
evaluation wrapper; they are not the current persistent-worker benchmark's
runtime or storage cost. Raw game results and complete subgroup arithmetic are
in the [descriptive result](D:/Pontius/tmp/v0a-paired-evaluation-run-001/descriptive-result.json).

## What changed in our interpretation

**Interpreter labels needed correction.** An older validation path labeled
Python 3.14.6 executions as isolated Python 3.11 checks. The
[identity correction](../docs/archive/ADR-0481-record-the-release-interpreter-identity-correction.md)
also addressed a Windows identity-width mismatch and recorded fresh checks on
the intended interpreters. Earlier mislabeled runs remain 3.14 evidence. The
obsolete inventory diagnostic was removed during cleanup; the finding survives.

**Repeated verification was a research bottleneck.** The
[bounded-read experiment](../docs/architecture/v0a-bounded-reads-r001/performance-report.md)
reduced a fixed 12-trial wrapper to 49.224 seconds, compared with earlier
88.931/95.554-second controls. Those controls were collected at different times
and paths. The later blueprint harness measurements isolated a much larger
startup problem and justified moving verification to run boundaries. Neither
engineering improvement says the policy plays better.

**Research value is not automatically connected to emitted actions.** Reduced
h32 experiments produced useful certified candidates, while the maintained
bot emits from its blueprint/baseline provider path. A full-game trained policy,
strategy-producing resolver integration, and broad live evaluation are not
established by the results reviewed here.

## Practical next questions

| Question | Evidence needed |
|---|---|
| Is a candidate policy stronger? | A declared objective and independent deal/opponent population, paired controls, uncertainty that respects shared deals, and separation of tuning from final evaluation. |
| Will it act within its budget? | Runtime-ledger preparation and decision measurements on realistic fitting artifacts, misses, long histories, and enough repetitions to examine tails. |
| Can research search safely drive the bot? | An explicit policy/abstraction/ownership contract, full-hand integration controls, and measured candidate acceptance and fallback under the actual clock. |

## Evidence and recovery

The paired execution source was
`bd71f4b11dcc0177283431a4ec468fdc152e7686`; its operating record was adopted at
`5845f32f010a44d924abc2f50ae142d1c6adec1b`. The comparison reports and raw
descriptive result were present at `D:/Pontius/tmp/v0a-paired-evaluation-run-001/`
when this summary was written. The directory is machine-local; a clone does not
recover it. The Windows identity correction is recorded at
`b5df265cf04739cbd051e9de5423bb1e5a66508a`.

The 59 historical evaluation and paired-run coordination scripts were moved
intact from the root to [the helper archive](../docs/archive/root-helpers/).
These previously uncommitted originals are included in the cleanup checkpoint;
`git log -- docs/archive/root-helpers/` locates their recovery commit. The older
source commits above do not establish recovery of those helper bytes.
They are historical reference material with old path and publication
assumptions, not maintained commands. This relocation changes neither the
paired comparison findings nor the raw-result retention limits above.

The September 8 cleanup runs were explicitly unreviewed development work based
on `91f031e91c957a9b273c2ccc345421f7b286b416`; the journal records their scoped
working-byte identities. Follow the current README for workflow. Historical
source seals and one-shot run restrictions in supporting documents are evidence
history, not instructions to reinstate those processes.

The follow-on removal of historical artifact assertions preserved all 34
maintained suites. Fresh Python 3.11 verification exercised 477 cases: 469 passed,
eight optional SciPy cases skipped. Native Windows trace-handle checks failed
under the restricted sandbox and passed when run outside it, including the full
suite. This is CPU behavioral verification of the cleaned working tree, not a
new GPU, Python 3.14, benchmark, or playing-strength result. The execution journal
retains both the initial failures and the successful verification.

The subsequent cleanup batches brought existing projection, public-tree,
policy/cache, sparse-contraction, selective-separation, shared-direct, and
fixed-width controls into the normal manifest while retiring unused
orchestration. Current coverage is 552 cases: Python 3.11 passed 541 with eleven
skips; Python 3.14 passed 542 with ten skips. Both lack optional SciPy in their
isolated environments; Python 3.11 also lacks `math.fma` for one population
control. All fifteen newly included fixed-width controls passed on Python 3.14.
The earlier separate SciPy-enabled run passed all three sparse-contraction cases.
These checks do not rerun the historical experiments whose drivers were removed.

Shared-direct wrapper retirement adds twenty existing sample-plan and synthetic
reader controls to the maintained manifest. Their cubin fixture reads exact
hash-checked retained bytes without re-admitting the old source tree; the
numerical classifier and reader mutation checks still execute. Separately,
the legacy fixed-width outcome suites exposed four existing failures/errors
among ten cases because their readers expected archived ADRs at old paths.
Those legacy read paths remain outside current maintained-suite coverage.
