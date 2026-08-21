# ADR-0141: Second sized board passes mechanism and repeats cap abstention

## Status

ADR-0140 executed once from clean commit `a198298`.  All 24 frozen mechanism
gates passed.  Both arms retained the immutable blueprint on all four targets,
and the top-level strategy-quality claim remains null.

## Evidence identity

The 28,703,546-byte artifact is
`experiments/results/h32-second-board-action-width-v1.json`, SHA-256
`9d32c13622e0f3be4785eaeca1878ae84952c6c128f74c41d23ab35280a86c88`.
Its configuration SHA-256 is
`15e99de5d5bc45a62de4d6e24a06bb1a6a9d29d863464756e6b95a2f8e4cc011`;
its implementation SHA-256 is
`74b47ab4160746646f6c7788bfe1a8a15e27bfb72716b6b7f26ce6ebca85f559`.

Strict Git metadata records clean full commit
`a1982985b68887090954a7eceedf28b367263961`.  Total wall time was
`886.6825 s`, below the 3,600-second ceiling.  Both exact average-64 source
policies, all four label-free target digests, the cache-safety parent, topology,
policy widths, payoff spans, arm order, and planning-before-quality phase order
reproduced.

The h2 control again produced exact embedded profile utility, quality error
`3.553e-15`, zero-sum residual `1.645e-15`, 378 canonical bases, exact
385/763-node and 127-terminal-group geometry, and an exact compact-policy
round trip.

## Frozen selection result

| Target | Embedded blueprint normalized NashConv | One-size arm | Two-size arm |
|---|---:|---|---|
| balanced / local blocker seat 3 | `0.0171952601` | blueprint abstention | blueprint abstention |
| balanced / all-seat strength | `0.0261037918` | blueprint abstention | blueprint abstention |
| blocker-heavy / local blocker seat 3 | `0.0170603342` | blueprint abstention | blueprint abstention |
| blocker-heavy / all-seat strength | `0.0281698520` | blueprint abstention | blueprint abstention |

Each of the eight arms produced four unique candidates, for 32 unique
schema-bound policy artifacts overall.  No candidate completed all six
verification seats.  Every stream stopped on an immutable blueprint-cap test:

- 29 candidates stopped at seat 0;
- the balanced/local one-size deadline average stopped at seat 2; and
- the balanced/local one-size current-1 and alpha-0.50 candidates stopped at
  seat 5.

Thus zero non-blueprint candidates entered the final fixed-envelope selector
as complete feasible policies.  Both arm totals, and therefore the frozen
two-minus-one selected normalized reduction, are exactly zero.  The artifact
marks this outcome explicitly as not a gate.

This is stronger diagnostic detail than merely saying the arms tied.  The
generator produced changed policies, but the fixed unilateral certificate
could not admit any of them under the common widened game.

## The widened branch was exercised

One-size embeddings assign zero opening mass to bet `6`, as frozen.  Every
two-size candidate assigned positive opening mass to that branch.  At each
target's deadline-current policy:

| Target | Mean bet-6 probability | Maximum | Positive opening information sets |
|---|---:|---:|---:|
| balanced / local blocker seat 3 | `0.2432%` | `3.7992%` | 25 / 192 |
| balanced / all-seat strength | `0.2937%` | `5.5166%` | 24 / 192 |
| blocker-heavy / local blocker seat 3 | `0.4404%` | `12.7974%` | 23 / 192 |
| blocker-heavy / all-seat strength | `0.5439%` | `18.2276%` | 19 / 192 |

Universal abstention therefore cannot be explained by the two-size solver
leaving the added branch identically unused.  It says only that these shallow,
wall-clock-frozen widened policies breached at least one immutable blueprint
cap before complete certification.

## Work and cost result

| Target | Arm | Complete steps | Planning | Candidate verification | Full one-shot bill |
|---|---|---:|---:|---:|---:|
| balanced / local | one size | 5 | `65.663 s` | `60.523 s` | `176.285 s` |
| balanced / local | two size | 2 | `72.132 s` | `17.452 s` | `139.684 s` |
| balanced / strength | one size | 5 | `61.053 s` | `16.946 s` | `127.301 s` |
| balanced / strength | two size | 2 | `71.518 s` | `18.118 s` | `138.938 s` |
| blocker-heavy / local | one size | 7 | `64.763 s` | `13.677 s` | `114.136 s` |
| blocker-heavy / local | two size | 3 | `71.111 s` | `13.694 s` | `120.500 s` |
| blocker-heavy / strength | one size | 7 | `60.027 s` | `12.094 s` | `107.279 s` |
| blocker-heavy / strength | two size | 3 | `68.753 s` | `12.297 s` | `116.208 s` |

The raw one-size arm completed more than twice as many steps under the same
clock.  The two-size arm paid its known canonical-cache construction bill and
completed only two or three steps.  Balanced/local one-size verification was
unusually expensive because three candidates survived beyond seat 0; this
made its full one-shot bill larger than the matching two-size bill even though
its planning was faster.  That is verifier-path accounting, not evidence that
the two-size strategy was better or cheaper in general.

The largest complete step took `22.824 s`, the largest cache construction
took `27.094 s`, and the largest exact seat read took `4.735 s`.  Maximum pool
totals were `7,934,734,336` bytes during planning and `7,099,907,072` bytes
during quality, both below the 12 GB ceiling.  Complete quality-vector sum
error was exactly zero and the largest incumbent zero-sum residual was
`5.149e-15`.

## Relationship to earlier evidence

At the deployed-selection level, this repeats ADR-0137's first sized board:
both arms abstain on all four targets.  It does not establish that one and two
sizes have equal latent quality, because the rejected candidates did not
receive complete six-seat quality vectors.

It also does not contradict ADR-0106's useful original-board one-size local
policies.  ADR-0106 replayed a larger 13-policy corpus in the one-size game.
This audit used a four-candidate wall-clock stream and certified its embeddings
inside the two-size game, where the added off-tree branch and payoff span alter
the unilateral cap geometry.

## Decision

Accept the second-board action-width mechanism and record universal cap
abstention as a diagnostic replication.  Preserve:

- the exact result artifact;
- the fixed-envelope acceptance contract;
- the common-game comparison;
- the raw one-size and scale-canonical two-size implementations; and
- a null top-level strategy-quality claim.

Do not rank action widths, retune the shot clock, relax unilateral caps, or
mine rejected partial vectors for a winner.  The result now points away from
another acceptance-semantics revision and toward a genuinely fresh multi-board
corpus frozen before one-size or two-size labels exist.  That successor should
separate two questions: whether the generator can produce any completely
certifiable candidate, and whether accepted quality differs by action width.

## Dissent

**Confidence:** extremely high in the mechanism, identity, cap-stop, and
resource results; high that the added branch was genuinely exercised; very low
that two universal-abstention boards identify an action-width ranking.

**Opposing evidence:** two boards now show the same deployed outcome, which is
real replication evidence about this fixed short-horizon generator plus fixed
envelope.  It would be wrong to dismiss that repetition merely because it is
negative.

**Largest unknown:** whether complete candidate quality would favor either arm
outside the immutable caps.  This audit deliberately stops before learning
that label, so it cannot distinguish a nearly safe improvement from a broadly
bad candidate once the first cap is crossed.

**Cheapest falsification:** preregister several genuinely fresh boards with
label-free target construction and the unchanged envelope.  A single complete,
feasible non-blueprint candidate would falsify universal generator abstention;
continued cap stops would strengthen the case that candidate generation, not
action-width choice, is the current bottleneck.
