# Fixed-group strategy potential diagnostic

The controller approved building this immediate next experiment: freeze the current
groups and games, optimize each seat against an unrestricted individual-hand opponent,
and compare the best representable policies with the saved policies. This is an
observed-case diagnosis, not new holdout confirmation or an adaptive feature experiment.

## Scope and immutable inputs

Read the eight already observed 96-hand cases from development-001 and holdout-001,
with uniform/polarized regimes on each of the four declared boards. Use the retained
group vectors byte-for-byte for exact, uniform_equity_200, range_equity, range_response.
Reconstruct the original one-bet game from pinned ranges, board, pot=10, bet=5 and
stacks=20/20; verify deal masses, ordered hands, provenance and saved full-game metrics.
No new hand selection, clustering, equity feature calculation, CFR training or board
selection is performed. All 96 saved profiles (three checkpoints x four methods x
eight cases) are compared with 32 fixed-group optima. Exact uses 96/96 groups.
The three compressed methods retain equal occupied capacities in each case.

## Mathematical contract

C, F and A are the full-hand, joint-mass-weighted check/fold/call payoff matrices
to player 0. x is the bet probability per player-0 hand; y is the call probability
per player-1 hand. Values are V(x,y) = sum C(1-x) + x F(1-y) + x A y.
Policies share a probability within each specified group and obey 0 <= p <= 1.
Individual-hand opponents remain information-set legal; no opponent sees hidden cards.

Let X_G and Y_G denote the two fixed group-constrained policy classes, X and Y the
unrestricted individual-hand classes. Two separate LPs find saddle witnesses for:

- v0 = max over X_G, min over Y of V(x,y).
- v1 = min over Y_G, max over X of V(x,y).

The least profile exploitability representable with both group constraints is
E* = (v1-v0)/2. This follows because the best-response upper value depends only on
y, and the lower value only on x. It does not require knowing the full game value.
The paired policies here need not be an equilibrium of the doubly compressed game.

For seat 0, introduce a free variable t_j for each individual opponent hand:
t_j <= sum_i x_g(i) F_ij and t_j <= sum_i x_g(i) A_ij. Maximize sum_i C_i(1-x_g(i))
plus sum_j t_j. For seat 1, introduce free u_i with u_i >= C_i and
u_i >= F_i + sum_j (A_ij-F_ij)y_g(j); minimize sum_i u_i. Probability variables have
box bounds. SciPy HiGHS dual simplex proposes a solution; inequality multipliers
provide the other player's witness. The solver status and objective are insufficient
evidence of correctness. Any clipping to [0,1] is followed by exact certification.

## Independently checkable numerical certificates

Interpret each finite binary64 C/F/A coefficient and each returned binary64
probability as an exact rational number. Fraction arithmetic recomputes min/max
payoffs over every legal group policy by summing before taking groupwise min/max.
It checks feasibility and group equality and certifies intervals [l0,u0], [l1,u1].
Each interval must be at most 1e-8 chips wide. This certifies the encoded payoff
game, not exact real-arithmetic card probabilities before their binary64 conversion.
It also does not independently reimplement the underlying card evaluator.

The minimum exploitability interval is [max(0,(l1-u0)/2), (u1-l0)/2]. Exact numerator/
denominator strings are authoritative; approximate chip floats are display values.
The upper endpoint is achieved by pairing the two proposed constrained policies.
For each saved checkpoint, compute its full-game exploitability E by exact rational
best responses. Its avoidable gap is [max(0,E-E*_upper), E-E*_lower]. This gap includes
finite optimization and compressed-opponent objective effects; it is not proof that
more iterations of the existing training algorithm would remove it.

Retain both seat witnesses, certificates, saved-policy gaps and original cohort/case
identities. Report equal-weight interval means separately for development and the
now-observed holdout, at all three checkpoints, with 10,000 as headline. Do not fit a
winning threshold or infer six-max strength, unseen-board generalization or sampling
confidence intervals. The result decides whether representation refinement or policy
optimization deserves the next experiment; it is not permission for that experiment.

## Bound execution and evidence

Use Python 3.14.6, NumPy 2.5.2 and SciPy 1.18.0. The separate environment is
D:/Pontius/tmp/group-opt-author/venv. Existing project environments stay unchanged.
The plan binds the absolute interpreter/output paths, all computational source and
this specification, and all four retained input files per case by SHA-256.
Plan generation reads/hashes inputs but does not optimize saved cases.

One invocation reserves a new output directory atomically and never reuses it.
The worker performs 64 LP calls sequentially, each with a five-second solver limit
and 10,000-iteration ceiling; the parent imposes a 300-second worker timeout. The
parent then rechecks all certificates and comparisons without invoking the LP solver.
Parent verification/I/O are outside the worker timeout. No process RSS cap is imposed.
Source and input pins are checked before launch and before completion. Failed/partial
outputs remain evidence and cannot be retried in place. Hard kills, power loss and
hostile concurrent filesystem changes are outside this recovery contract.

Internal worker entry is not an authorization interface. Use run with the reviewed
plan and SHA-256. A successful worker alone is not completion: successful parent exit
and the final manifest are required. Timeout, nonzero exit, certificate rejection,
missing result or any evidence write failure prevents a complete invocation claim.

Build checks use hand-derived synthetic games and a two-hand development fixture,
including a real subprocess smoke. One focused opposing review precedes controller
approval of the bound observed-case invocation. Commit and push remain separate.
Original run outputs, computational source and review evidence remain unchanged.

Reference: Johanson, Bard, Burch and Bowling, Finding Optimal Abstract Strategies in
Extensive-Form Games (AAAI 2012), motivates optimizing within an abstraction against
unrestricted responses. This diagnostic uses small LPs, not their CFR-BR algorithm.
https://johanson.ca/publications/poker/2012-aaai-cfr-br/2012-aaai-cfr-br.pdf
