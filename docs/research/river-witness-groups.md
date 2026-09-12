# Fixed-capacity witness-action-value grouping: development screen

One new representation, witness_advantage, tests whether actual action incentives
give better groups than the existing equity and response proxies. This is an
oracle-assisted, development-only screen using the retained group-optimality-001
witnesses. No claim of an affordable or deployable feature pipeline follows.

## Fixed population, controls and information budget

Use the existing four development cases, in order: board 0 uniform, board 0
polarized, board 1 uniform, board 1 polarized. All have 96 hands per seat and the
same one-bet game. No held-out bank file supplies a feature, grouping or score.
The witness manifest/plan also name previously observed holdout cases; those
metadata do not make this a holdout evaluation. All four development cases are
already observed. New confirmation cases must be reserved in a later design.

For each case and seat, match the baseline's occupied group count exactly.
Keep exact-hand, uniform_equity_200, range_equity and range_response as controls.
Their grouping floors and witness policies come from the retained diagnostic;
reverify those certificates against the reconstructed input game before use.
No CFR training, parameter sweep, iterative regrouping, fallback to a winning
control, or selection after looking at candidate results is part of this screen.

The witness bank has four columns in exactly that control-method order. For the
bettor, use each control's seat0.call vector: the unrestricted caller witness in
the game restricting only the bettor. For the caller, use each control's seat1.bet
vector: the unrestricted bettor witness when only the caller is restricted.
These include full-hand solver information from the exact control. Their prior
construction cost is excluded from the screen runtime and must be disclosed;
equal group counts do not mean equal feature-construction compute or information.

## Feature definition and deterministic grouping

Let J_ij be the retained joint hand probability, and C_ij, F_ij, A_ij the already
joint-mass-weighted check, fold and call payoffs to player 0. Let m0_i=sum_j J_ij
and m1_j=sum_i J_ij. Every marginal must be positive. With opponent witness y or x:

    bettor_delta_i(y) = sum_j ((1-y_j)*F_ij + y_j*A_ij - C_ij) / m0_i
    caller_delta_j(x) = sum_i x_i*(F_ij-A_ij) / m1_j

The first is bet minus check for player 0. The second is call minus fold for
player 1, with opponent betting reach retained. It is conditional on the caller's
own hand, not renormalized conditional on facing a bet. Zero betting reach gives
zero caller incentives without division by zero. This keeps both sign and the
importance of the reached decision. Four columns use the same chip units, with
equal column weighting: no whitening, clipping, equity concatenation or scaling.

Use the existing anchored_clusters unchanged: marginal-probability hand weights,
weighted farthest-first initialization, stable hand-index tie breaking, twenty
Lloyd updates and permanently occupied anchors. This is a reassignment at fixed
capacity, not a nested split or a guarantee that distortion or exploitability
improves. Identical features still preserve the exact number of occupied groups.
The output retains all features, marginals, group labels and bank method order.

## Evaluation and reporting

For the one candidate per case, compute the same certified minimum exploitability
as group-optimality-001 using two asymmetric LPs. Pairing their constrained-seat
policies supplies the achievable upper endpoint. The inherited exact-rational
checker must validate both certificates with width at most 1e-8 chips, on the
binary64 payoff coefficients interpreted exactly. It does not certify ideal
pre-rounding card probabilities. Solver success alone is insufficient.

Primary comparison: the equal-weight mean candidate grouping floor minus
range_equity's floor across all four cases. Secondary: range_response. Also
report uniform_equity_200 and exact-hand, every per-case signed interval, all
four candidate solutions and lower/higher/overlapping case counts. For candidate
interval [Lc,Uc] and control [Lb,Ub], the difference interval is [Lc-Ub,Uc-Lb].
Classify lower only when its upper endpoint is negative; higher only when its
lower endpoint is positive. Otherwise report overlapping, not equality or a win.
No best checkpoint, winning subset or minimum improvement threshold is selected
after results. This is a fixed-case screen, not statistical generalization,
six-max strength, BB/100 or a neural-versus-table efficiency comparison.

## Bounded execution and review

Reuse the existing pure payoff, clustering, LP, certificate, strict JSON, source
and input-verification helpers. The small phase driver only binds the new input
bank, dispatches the fixed work, reconstructs results and writes evidence. No
shell invocation wrapper or generic orchestration framework is added. Historical
computational source and data files remain unchanged.

Python 3.14.6, NumPy 2.5.2, SciPy 1.18.0; the same separately pinned environment.
The plan pins interpreter/output paths, ten computational source/document files,
sixteen case-input files, four witness-case files and the witness manifest/plan.
The latter binds each witness to the exact original case inputs. Plan creation
hashes data and does not construct new groups or run an LP. Rehearsals use only
synthetic games and a two-hand fixture, not the four saved 96-hand cases.

The development invocation makes eight LP calls sequentially (four candidates,
two seats), each limited to five seconds and 10,000 iterations. A single worker
has a 120-second wall timeout; parent reconstruction, certificate checking and
I/O are outside it. No process RSS cap is imposed. Prior witness-generation work
is not included in those bounds. One BLAS thread is selected before NumPy import
by the reused driver helper. The parent recomputes features, labels, certificates
and comparisons without optimizing. Source and input bindings are checked before
launch and again before completion.

A new output directory is reserved atomically and never reused. Retain the plan,
start record, captures, worker receipt, each case, complete summary and manifest.
Successful parent exit and a final manifest are required for completion. Any
worker failure, timeout, malformed/missing result, certificate mismatch or
evidence-write failure prevents completion. Failed directories remain evidence;
there is no automatic retry. Hard kills, power loss and hostile concurrent
filesystem changes are outside the existing recovery contract. The internal
worker entry is not a controller authorization interface.

One focused opposing review follows author checks. Execution of the reviewed
development plan needs the controller's separate approval. Commit, push,
deployment and any subsequent experiment require separate authorization.
