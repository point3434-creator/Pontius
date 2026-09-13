# Blueprint test: flop coverage and averaging

Status: accepted experiment design. The user subsequently requested that this test run on the Ubuntu server. Implementation is in `experiments/2026-09-12-flop-coverage.py`; launch instructions are in `docs/early-blueprint-linux.md`. This design does not approve a production abstraction or establish poker strength.

## Decision to answer

At a fixed resource budget, does a coarse flop representation, more average-strategy sampling, or their combination produce useful repeat coverage on fresh observations?

The first Ubuntu run completed 100 iterations in each of four cells. Only about 3.0–3.5% of stored flop rows received an averaging sample; no flop rows received samples in more than one iteration, and no exported flop averages were nonuniform. This suggests a coverage bottleneck, but 100 iterations do not establish that the averaging estimator is incorrect or that any particular production abstraction is best.

There are three plausible next investigations: a controlled representation/averaging comparison; a much larger exact-state run; or conditional flop jobs with explicitly defined public contexts and ranges. I recommend the first. The exact-state arm supplies the larger-run control. Conditional flop jobs are the next alternative if preserving betting context still leaves the pooled representation too fragmented.

This test has an engineering outcome. It cannot approve a production playing blueprint or certify a six-player equilibrium.

## Fixed game and algorithm

- Six dealt players, equal 100bb stacks, no rake.
- Preserve the current legal action menu and the one-aggression-per-early-street cap, including the opening bet. This excludes re-raises.
- Ordinary, frozen-policy external-sampling CFR in every arm. Linear weighting, DCFR, pruning, native rewrites and shared-table parallel updates are deferred so the update rule is not another experimental variable.
- Train preflop and flop only. Use the existing check/call continuation for all training cells.
- Preserve all six private hands in the exact simulator, including folded players' blockers. Keys see only the acting player's hand and public information.
- Full ordered betting history, acting seat, starting stacks, commitments, pot eligibility, legal actions and the 169-class preflop observation remain in the key.
- All cells start from zero under a new versioned sampler/checkpoint identity. Do not resume or overwrite the first Ubuntu pilot.

Keeping the update rule fixed is an experimental control, not a claim that ordinary CFR is stronger. The original MCCFR work supplies the sampled-update foundation; no multiplayer equilibrium conclusion follows from this experiment. [Lanctot et al., MCCFR](https://mlanctot.info/files/papers/nips09mccfr.pdf)

## Four arms

| Arm | Flop representation | Averaging trajectories per player per iteration |
| --- | --- | ---: |
| A | Current exact suit-canonical private-hand/flop key | 1 |
| B | Same exact key | 8 |
| C | Fixed structural grouping described below | 1 |
| D | Same structural grouping | 8 |

Within each representation, A versus B and C versus D isolate the averaging budget. A versus C and B versus D isolate the representation at the same averaging budget. D versus A is the primary combined comparison.

Each seed is shared across all four arms. Main training seeds are 1101, 1102 and 1103, for 12 main cells. Use a distinct calibration seed, 1001. Report each seed separately as well as the three-seed range.

### Structural grouping is a diagnostic control

For this first comparison, use a cheap, deterministic group, not a fitted production abstraction. Its label is the tuple:

1. The standard made-hand category of the five observed cards: the player's two hole cards and the flop.
2. Flush potential: at most two cards of any suit; exactly three; exactly four; or five. Suit names are irrelevant.
3. Straight potential: an existing straight; otherwise zero, one, or at least two distinct unseen ranks that would complete a straight when added to the observed rank set. Include the ace-low straight.

This has at most 9 × 4 × 4 = 144 structural labels, although many combinations are impossible. It does not mean the whole strategy table has 144 rows: preflop class, player and public betting context still multiply the state space.

Replace the exact private-hand/flop tuple with this label only in arms C and D. Do not accidentally retain the exact tuple elsewhere in their policy key. Keep the group unchanged during the flop and preserve the player's preceding abstract observations and action history.

The grouping deliberately loses information. For example, the same starting hand can make a top pair on one board and a bottom pair on another while landing in the same structural group. It must never be adopted as the production abstraction on the basis of this test.

Its purpose is to measure the benefit and remaining limitations of pooling observations without paying for an expensive abstraction builder first. If pooling is useful, the next abstraction study should preserve more strategically relevant distinctions, including future hand-strength distributions and blocker/range sensitivity. Research on state abstractions shows why a single expected hand-strength number can merge hands with different potential. [Johanson et al., evaluating state-space abstractions](https://webdocs.cs.ualberta.ca/~mbowling/papers/13aamas-abstraction.pdf)

## Averaging rules and isolation

One regret iteration still freezes the same joint policy and performs one external-sampling regret traversal per player. More averaging must not alter that regret-training path.

- Use separate deterministic random-number streams for regret sampling, each player's averaging trajectories, and evaluation. Checkpoint every stream.
- Derive stream seeds from a documented stable hash with explicit domain labels; do not use Python's process-randomized hash.
- Give every player R averaging trajectories for every completed iteration, where R is fixed at 1 or 8 for the entire run.
- On an averaging trajectory, sample the target from its current frozen policy and other players uniformly over legal abstract actions, as in the current estimator.
- Each contribution has weight 1/R in this ordinary-CFR test. Sum repeated row contributions across trajectories; do not apply regret updates until all averaging for the iteration is finished.
- Track trajectory-level sample count, distinct iterations with averaging samples, and whether the row had a previous regret update before the sampled policy was read. Eight observations of one unchanged policy must not be reported as eight different training iterations.
- Preserve transactional rollback of tables, counters and all RNG streams if an iteration encounters a capacity or numerical error.
- Version the changed checkpoint schema and sampler identity. Reject incompatible resumes explicitly.

For a fixed representation and seed, the regret stream, regret-update counts, regrets and current policies must match exactly between R=1 and R=8 at every common completed iteration before a resource cap intervenes. Average-only allocated rows can differ and should be excluded from the regret-state comparison. The extra averaging may change the exported average policy, memory use and elapsed time.

Multiplayer averaging needs its own correctness control. OpenSpiel documents problems with simply accumulating an opponent's policy at sampled regret nodes when there are more than two players; the design retains the project's separate averaging estimator. [OpenSpiel source](https://raw.githubusercontent.com/google-deepmind/open_spiel/master/open_spiel/python/algorithms/external_sampling_mccfr.py)

## Stage 1: controls and calibration

Before running the 12 main cells:

1. Use the existing small three-player exact oracles to check the unnormalized averaging expectation and the 1/R normalization. Test aggregation when several trajectories reach the same information set. Treat normalized finite-sample policies as estimates, not exactly unbiased quantities.
2. Verify the paired regret-path invariant above for A/B and C/D over 500 iterations with calibration seed 1001, subject to the same resource ceilings.
3. Verify suit invariance, legal action agreement, and preservation of the 169 preflop class and full betting history. Alter opponents' or future cards and confirm the acting player's key does not change. Confirm representative exact states merge only according to the declared structural rule.
4. Run checkpoint/resume and interrupted-writer controls in disposable test directories. These controls do not modify the retained Ubuntu pilot.
5. Record process memory, checkpoint peak memory and save/load duration. If calibration cannot fit the limits, stop and report that outcome. Do not silently change the experiment.

## Stage 2: bounded main runs

Proposed limits, not forecasts of runtime or required resources:

| Limit | Value |
| --- | --- |
| Main cells | 4 arms × 3 seeds |
| Target | 5,000 completed regret iterations per cell |
| Full checkpoints | 0, 100, 1,000 and 5,000, plus the exact stopping iteration if different |
| Training-cell wall limit | 20 minutes including its checkpoint work, followed by at most 30 seconds for graceful termination |
| Table limit | 500,000 total rows, including average-only rows |
| Node limit | 100,000 per full iteration; count both regret and averaging work |
| Process memory | Request a graceful stop at 12 GiB; enforce a 16 GiB cgroup ceiling including checkpoint children |
| Disk use | At most 50 GiB for this experiment; require at least 100 GiB available before launch |
| Whole experiment | Six-hour wall ceiling including controls, training, evaluation and saving |
| Concurrent training | One cell at a time for the primary timing comparison |

Reserve up to 45 minutes of the six-hour budget for final evaluation and enough time to close the report. A supervisor must enforce the outer deadline independently of the trainer. A timeout, memory stop or row cap is a retained capacity result, not a successful completion of 5,000 iterations.

The JSON checkpoint implementation currently scans and retains decoded historical generations, so live table memory is not a sufficient capacity estimate. Checkpoint peak memory must be measured before enlarging the test.

Independent main cells could later run on separate CPU cores, but this first timing comparison is sequential. It measures useful work in a serial trainer, not 32-core shared-table scaling. Include both CPU seconds and wall seconds; do not assume an eightfold averaging budget costs eight times as much overall.

If an exact arm hits its cap before a grouped arm, compare common saved milestones first. Separately report progress achievable within the resource envelope. Never compare different iteration counts as if they were an equal-work algorithm comparison.

## Fixed evaluation panels

Create and hash the panels before inspecting main-run results.

### Coverage panel

Using independent seed 2101, generate 2,000 full legal deal blocks under each of two frozen behavior profiles: check/call and uniform legal actions. Retain the flop decision observations reached by those profiles, including their seat, live-player count, public history and original deal-block ID.

Every arm is queried on the same observations, regardless of which states its own policy prefers to visit. Retain repeated observations with their original visit weights. Report heads-up, three-way and four-to-six-way flop subsets separately and mark empty subsets rather than filling them in artificially.

At every saved milestone, report:

- Missing lookup, stored-but-unaveraged lookup, and averaged lookup rates.
- Repeat-averaged lookup coverage: a queried row received averaging samples in at least two distinct regret iterations.
- A stricter coverage diagnostic for at least 20 trajectory samples; also record their spread over iterations.
- Rows whose sampled policies incorporated earlier regret updates.
- Regret-only and average-only rows, and preflop/flop row counts.
- Average-policy entropy and policy movement between milestones. These are diagnostics, not strength measures.
- Useful repeat-covered observations per CPU second, wall second and GiB of peak memory.
- Feature/key construction time, training time, checkpoint time and evaluation time separately.

The denominator is the fixed panel's decision observations, not the ever-changing number of rows allocated by training.

### Paired play panel

Use independent seed 3101 and fresh deals. Evaluate final candidates against arm A at the latest common saved milestone. Use 2,000 independent deal blocks per combination of opponent profile and continuation. Balance the candidate over all six seats and reuse each deal/action-stream block for the paired comparator.

Opponent profiles are check/call and uniform legal actions. Evaluation continuations are check/call and the existing simple betting policy. The second continuation is a sensitivity test; it does not change the training objective.

All arms use the same declared fallback for missing observations. Each policy uses its own representation encoder; do not relabel incompatible policy keys or silently change their game identity.

Save raw paired returns and fallback counts. Calculate bb/100 and paired confidence intervals by resampling whole deal blocks, keeping the six seat rotations together. Report intervals separately for each training seed and opponent/continuation cell. With three training seeds, show seed-to-seed variation rather than treating pooled hands as independent training replicates.

D minus A is the primary combined comparison. Other contrasts are exploratory. Do not choose a winner through repeated significance checks or tune the grouping on this final panel. If evaluation exceeds its reserved time, mark it incomplete and do not issue a strength verdict.

These opponents and continuation policies are limited controls. Even a clear gain on this panel would establish only performance in the declared diagnostic games. The multiplayer and continuation limitations remain material. [Pluribus supplementary material](https://noambrown.com/papers/19-Science-Superhuman_Supp.pdf)

## Restart and interruption checks

For each arm's first main seed, retain a live in-memory reference at an early checkpoint and a separate process restored from disk. Continue both for 100 completed iterations under the same configuration and compare logical state hashes: regrets, averaging accumulators, counters, identities and all RNG streams. Exclude publication timestamps and filesystem paths from the comparison.

In separate disposable recovery runs, terminate a writer at two controlled boundaries:

- During staging, before publication: recovery must select the previous valid generation.
- After rename and parent-directory synchronization, before the advisory latest pointer is updated: recovery must select the newly published valid generation.

Also exercise a truncated newest generation in a disposable copy and require fallback to the preceding valid generation. Never damage the retained main milestones. These are process-failure tests on Ubuntu, not a physical power-cut qualification of the SSD.

## Decision rules

The proposed numerical targets below are engineering choices for this test, not literature-derived strength thresholds.

- **Fail correctness:** any illegal action, information leak, wrong averaging normalization, incompatible resume accepted, regret-path mismatch, corrupted state accepted or restart divergence. Stop the main comparison.
- **Pass the coverage gate:** at a common saved milestone, a treatment raises repeat-averaged fixed-panel flop coverage by at least five percentage points over A in at least two of three seeds, with a positive median gain, while staying inside the declared resource envelope. Report the third seed and all live-player subsets. Also report the stricter 20-sample measure without calling it a confidence guarantee.
- **No practical improvement:** coverage gains disappear when measured per CPU second or memory, or only occur at unmatched work budgets. Keep the measurements and do not extend the same setup automatically.
- **Engineering progress, strength unresolved:** the coverage gate passes but paired-play intervals are inconclusive. This is a valid outcome; proceed to a better abstraction/value study, not production adoption.
- **Diagnostic play improvement:** the preregistered paired comparison supports a gain for the stated panel. Retain the limitations and the cross-continuation results. Structural groups still require replacement or a separate abstraction-quality justification before production use.

Before the main run, the practical decision is made explicit as follows. Keep the
raw `coverage_gate_passed` result separate. A treatment that passes it counts as
useful engineering progress only when all three seeds have complete, comparable
measurements at a common saved milestone, and the median treatment-minus-control
gain is positive for both repeat-covered observations per CPU second and per
peak GiB. A nonpositive median in either metric yields
`no_practical_improvement`; incomplete measurements yield
`insufficient_measurements`; a failed raw gate yields `coverage_gate_not_met`.
CPU measurements lost during a process restart cannot satisfy this decision.
These thresholds classify the engineering experiment and do not establish
playing strength.

If B materially helps without pooling, improve averaging first. If C or D helps substantially, proceed to a richer, frozen flop abstraction study. If even D remains fragmented, investigate conditional flop populations and betting-context decomposition with explicitly specified ranges; do not keep coarsening until lookup rates look good.

## Retained outputs and implementation boundary

Retain a machine-readable manifest, source/experiment hashes, exact feature definition and version, seed domains, game and continuation identities, resource logs, every named milestone, exported policies, panel hashes, raw paired returns and the decision report. Recovery generations and comparison milestones remain separate concepts. No large training data should enter Git.

Likely implementation surfaces are the existing sampled-CFR trainer and checkpoint schema, a small flop-group encoder used by the hold'em adapter, the averaging/key/recovery tests, and a new experiment driver. The existing 100-iteration pilot remains a reference. The implementation must provide one Ubuntu launch command after local and GitHub checks pass; this document does not supply a runnable command for features that do not exist yet.
