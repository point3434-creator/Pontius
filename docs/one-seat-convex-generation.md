# One-seat convex generation

## Scope

Fix a finite perfect-recall game, an exact belief/payoff model, a blueprint
profile, and one acting seat `i`. Only seat `i`'s continuation strategy may
change. All other seats remain at the blueprint except when an exact best-
response oracle evaluates one of them. This document proves the optimization
claim in sequence-form coordinates. It does not import a two-player safety
theorem and it does not cover joint edits by multiple seats.

## Sequence-form domain

Let `x_i` be seat `i`'s realization plan. Its feasible domain `X_i` is the
polytope defined by nonnegativity, unit mass at each root information set, and
the usual flow equality

```text
sum_a x_i(I, a) = x_i(parent_sequence(I)).
```

The empty parent sequence has mass one. Perfect recall makes every information
set's parent sequence well-defined. A mixed normal-form strategy and its
behavioral projection induce the same realization plan.

With all other strategies fixed, every terminal probability contains at most
one realization variable from `x_i`: the variable for seat `i`'s last sequence
on that terminal history. Consequently every fixed-response payoff is affine
in `x_i`, including topologies in which seat `i` acts more than once.

## Gain geometry

For target seat `j != i` and a fixed pure response plan `b`, define

```text
ell[j,b](x_i)
  = u_j(x_i, b, blueprint_-(i,j))
  - u_j(x_i, blueprint_j, blueprint_-(i,j)).
```

Both terms are affine in `x_i`, so `ell[j,b]` is affine. An exact best response
may be chosen pure in a finite perfect-recall game. Therefore

```text
G_j(x_i) = max_b ell[j,b](x_i)
```

is a finite maximum of affine functions and is convex. For `j = i`, the best-
response value depends only on the fixed opponents, not on seat `i`'s current
strategy. Thus `G_i` is affine on `X_i` (and is nonnegative because the current
strategy is itself an available response).

The blueprint-relative envelope

```text
G_j(x_i) <= G_j(x_blueprint) + guard
```

is an intersection of convex sublevel sets. NashConv restricted to this
one-seat domain, `F(x_i) = sum_j G_j(x_i)`, is convex.

## Finite epigraph LP

Introduce one epigraph variable `t_j` per seat. The global one-seat problem is
the finite LP

```text
minimize    sum_j t_j
subject to  x_i in X_i
            0 <= t_j <= G_j(x_blueprint) + guard
            t_j >= ell[j,b](x_i)  for every pure response b and every j != i
            t_i >= G_i(x_i).
```

The implementation need not materialize all response rows. A restricted master
with only a subset of the epigraph rows is a relaxation, so its objective `L`
is a valid lower bound on the complete one-seat optimum. An independently
evaluated cap-feasible policy is an incumbent with objective `U`, a valid upper
bound. The first-class timeout statement is

```text
optimality_gap = U - L.
```

The reverse subtraction is invalid for this minimization problem.

At each master solution, exact best responses separate every opponent's
epigraph, even when the candidate already satisfies all caps. All violated
opponent rows are added in the same iteration. If no exact gain exceeds its
epigraph variable beyond the frozen tolerance, the master solution is feasible
for the complete LP and is globally one-seat optimal to that tolerance. Because
the pure response set is finite, exact row generation terminates after finitely
many distinct rows absent a numerical or implementation failure.

## Row identity, conditioning, and reuse

The immutable response-tape signature is the only row-deduplication key. A
numerically near-parallel row is still an exact constraint and may not be
dropped merely because its distance is below the LP tolerance. Approximate row
removal would require a separate conservative dominance proof. Numerical rank,
condition number, and normalized row separation are diagnostics only.

A generated row is reusable only inside the exact epoch

```text
(belief, blueprint opponents, payoff/layout semantics, acting seat coordinates).
```

Rows accumulate monotonically across iterations and restarts within that epoch.
Any change to an epoch component invalidates the library unless a separate
transformation theorem applies.

## Behavioral-coordinate shortcut

The same fixed-response payoff is affine in the acting seat's full behavioral
probability vector only under the sufficient topology predicate that no
root-to-terminal path visits the same strategic seat twice. The new geometry
gate consumes the compiled public layout, and any behavioral-coordinate
shortcut must call it immediately after layout construction. This leaves the
frozen evaluator lineage byte-identical. Full one-bet trees can fail the
predicate when a checker later responds to a bet; post-bet continuation trees
can pass it. Sequence form remains valid in both cases.

## Interior retreat and emission authority

For an exactly cap-feasible endpoint `x_star`, emit an interior realization
plan only after choosing a frozen `eta` in `[0, 1]`:

```text
x_emit = (1 - eta) x_blueprint + eta x_star.
```

Convexity gives, for every seat,

```text
G_j(x_emit)
  <= (1 - eta) G_j(x_blueprint) + eta G_j(x_star)
  <= G_j(x_blueprint) + eta guard.
```

The retreat therefore restores at least `(1 - eta) guard` of cap slack. Jensen
also gives

```text
F(x_emit) <= (1 - eta) F(x_blueprint) + eta F(x_star),
```

so it retains at least an `eta` fraction of any endpoint improvement in the
one-seat objective. These inequalities do not authorize emission. The existing
independent exact certificate remains the sole authority for both the endpoint
and the retreated policy.

## Anticipated scope

Blocks remain useful for early cut-extraction and wall-clock ladders, but they
are not a mathematical limit of the sequence-form program. Once the open-axis
coefficient machinery and exact final certificate are priced, the same master
can optimize the acting seat's entire continuation plan jointly. That future
scope change still remains one-seat-only; multi-seat joint edits reintroduce
multilinear reach interactions and require a different theorem.
