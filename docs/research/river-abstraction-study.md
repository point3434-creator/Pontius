# River abstraction study: design 1

Status: development candidate; no retained comparison or holdout run authorized.

## Question and limits

How much does merging private hands cost in a small strategic river game, and does
range-conditioned information reduce that cost at the same occupied bucket count?
Both players optimize. The game is heads-up, zero-sum, one fixed bet, with check,
bet, fold and call; no raises, earlier streets, side pots or multiplayer guarantees.
This isolates a representation question. It cannot establish six-max playing strength.

The existing baseline uses 200 equal-width bins of exact showdown equity against
the 990 uniformly weighted compatible opponent hands. Its operation is
`min(int(equity * 200), 199)`, including that floating-point evaluation order.
Source: `D:/Projects/pluribus-lite/pluribus_lite/abstraction.py`, SHA-256
`91ae39e94d8f1e2f908bcc3be2690d6e7a9114e4c1143330c290fe7c463a5518`.
Saved baseline-000 `buckets/meta.json` SHA-256:
`6914609fefd483d5e4114596fd19f1aa370c4667b4e8636ded9ec615a83a5943`.

## Fixed comparison

Use Python 3.14.6 and NumPy; no new dependencies. Pot 10 chips, bet 5 chips,
remaining stacks 20 chips each. The public card encoding is rank*4+suit, with
ranks 23456789TJQKA and suits cdhs. Joint weights are the product of declared
positive ranges, rejecting card collisions and normalizing once. Every method
uses exactly that joint distribution, including exact ties.

Development boards, in order: `2c 7d 9h Js Qc`, `2h 7h Jh Qc Ks`.
Holdout boards, in order: `3c 3d 8h Ts Ad`, `4s 6s 8s Td Qh`.
No outcome-based board replacement. Results are conditional on these boards;
there is no claim that these four boards are sampled from all poker situations.

Per player, take the first 96 board-compatible hands ordered by SHA-256 of ASCII
`river-study-v1|<sorted comma-separated board ints>|<player>|<low>,<high>`.
Break digest ties by the hand tuple. Persist the selected hands and weights.
Two range regimes: uniform weights; polarized weights 4 for uniform equity >=0.8
or <=0.2, and 1 otherwise, for both players. This is a declared synthetic range
family, not a model of real preflop or turn play.

Four representations, built independently per player:

1. Exact private hand (reference).
2. Baseline uniform-equity bins (200 nominal bins).
3. Range-equity-only weighted clustering (control).
4. Range-response features, weighted clustering (candidate).

The last two use K equal to the baseline's *occupied* groups for that player on
that game's positive marginal support. Range equity is conditional on the
declared opponent range after removal. Candidate features, for each of three
opponent uniform-equity bands [0,1/3), [1/3,2/3), [2/3,1], are conditional mass,
win mass and tie mass. All nine coordinates stay on [0,1]; no learned scaling.
These features encode removal and payoff relationships to public range strata;
they are a hypothesis, not a claim to preserve every strategically relevant blocker.
They never consume a sampled opponent's private cards or trained policies.

Clustering: weighted farthest-first seeds (first highest marginal weight, ties by
hand order), then 20 weighted Lloyd updates. Squared Euclidean distance; ties by
seed order. Force each distinct seed hand to its own cluster throughout to keep
exactly K occupied groups, including duplicate feature vectors. Declare this
anchor constraint; do not call it unconstrained optimal k-means.

## Solver and acceptance measurements

Alternating vanilla tabular CFR, zero initial regrets, uniform regret matching
when no positive regret, ordinary average policies. Checkpoints 100, 1,000 and
10,000 iterations. Report full and reduced-game best-response gaps separately.
The exact-hand reference is a finite-budget strategy, not an exact equilibrium.
Exact-hand best responses evaluate every lifted policy in the original game.

Let q be normalized joint mass, z be -1/0/1 showdown sign, H=pot/2, B=bet.
Weighted check, fold and call payoffs to player 0 are C=q*z*H, F=q*H,
A=q*z*(H+B). If x is bet probability and y call probability:

```
V = (1-x) dot row_sum(C) + x dot (row_sum(F) + (A-F) @ y)
U = sum(max(row_sum(C), row_sum(F) + (A-F) @ y))
L = (1-x) dot row_sum(C) + sum(min(x @ F, x @ A))
exploitability = (U-L)/2
```

L and U bracket the game's minimax value up to floating-point error. Report the
raw bounds and both individual deviation gains, in chips and fractions of pot.
The abstraction penalty report compares full-game exploitability across methods
at each checkpoint; it must not confuse unresolved CFR regret with an intrinsic
abstraction floor. Report the restricted best-response gap so that limitation is
visible. No improvement is declared from agreement, row count or speed alone.

Report each case separately and equal-weight averages within the fixed board and
range grid. The exact enumeration has no deal-sampling confidence interval.
No statistical claim over unseen boards follows. Retain every checkpoint and
non-improvement. Keep preparation, training and evaluation timing separate; never
run tracemalloc during a timed segment. Report array storage, not process peak,
unless a separate process measurement supplies the latter.

## First gate and subsequent execution

The first candidate supplies the specialized matrix kernel, all four grouping
methods, a bounded single-case development driver, and checks against the existing
generic RiverHoldem evaluator/CFR and small normal-form oracle. The unmodified
generic evaluator is only used on tiny games because its chance transition
rebuilds the deal dictionary. No runtime or existing blueprint artifacts change.

A development smoke uses only the first development board, 16 hands per player,
and 100 iterations. It is engineering evidence, not the 96-hand comparison.
The driver refuses holdout boards in this version. One opposing review comes
before proposing a retained campaign with its own resource bound and authority.
Before that campaign, add a bounded multi-case plan consumer and retention of
failed attempts; the single-case driver is not that campaign runner. Holdout
execution requires freezing grouping rules and decision criteria before results.
The later three-player extension is a separate decision after this study.
