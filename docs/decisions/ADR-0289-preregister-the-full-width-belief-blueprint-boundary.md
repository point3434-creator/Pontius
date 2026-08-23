# ADR-0289: Preregister the full-width belief/blueprint boundary

- Status: accepted executable correctness preregistration before any full-width complete-hand result
- Date: 2026-08-23
- Follows: ADR-0288
- Front-Door-Kind: controller-v1
- Front-Door-Research: ADR-0280
- Front-Door-Process: ADR-0289
- Front-Door-Contract: ADR-0282
- Front-Door-Revoked: ADR-0281
- Front-Door-Active-Next: Execute the frozen passive four-street hand once with five full opponent combo axes, exact action-likelihood updates, exact legal integer raise support, and the independent collision controls; keep every resolver and strategy label closed
- Front-Door-Blockers: the full-width one-seat adapter, immutable rational policy source, reduced exact collision oracle, charged replay hooks, and maintained full-width trace do not yet exist

## Question

What is the narrowest boundary that can carry exact full-deck opponent ranges
and blueprint action probabilities through ADR-0288's complete one-seat hand
without pretending that full-width value contraction, a trained blueprint, or
resolving already exists?

## Decision

Build one additive rank-one full-width belief adapter over the accepted
`FactorizedCardBelief` from ADR-0061/0062, one immutable digest-bound rational
reference policy, and one independently enumerated collision oracle. Connect
them only to the unchanged passive four-street fixture A from ADR-0287.

This is a correctness and interface gate. It opens no h32 experiment, strategy
quality, action abstraction, convex master, resident resolver, or deployment
label.

### Frozen one-seat belief contract

Condition on the controlled seat's exact private pair outside the factor object.
The factor object therefore has exactly five axes, one for every opponent seat.
On each street every axis is the complete two-card domain compatible with the
controlled hand and currently revealed board: 1,225 hands preflop, 1,081 on the
flop, 1,035 on the turn, and 990 on the river. Opponent axes remain present
after folds because folded private cards still block the deck.

The initial prior is rank one with equal positive unary weights, conditioned on
hard pairwise card disjointness. Thus every labeled compatible five-opponent
deal has equal mass. Its compatible support count is computed exactly as

`product(C(n - 2*i, 2), i=0..4)`,

where `n` is the number of cards remaining after the controlled hand and public
board. The Cartesian count `C(n,2)^5` is reported separately and must never be
called the compatible joint count.

An observed action by opponent `i` multiplies only opponent `i`'s unary factor
by that action's blueprint likelihood for each exact private combo. Board reveal
filters every axis and its weights by the new public cards. These operations are
exactly closed under the ordinary perfect-recall behavioral-policy assumption
already established by ADR-0061. A policy that depends on shared private
information, collusion, or an unrepresented latent variable remains outside
this boundary.

The adapter must retain immutable action-update provenance and a digest over
the controlled visible cards, opponent-seat order, exact hand axes, Float64
factor bytes, and ordered likelihood-source digests. It must reject a wrong
actor, stale hand axis, mutable alias, nonfinite or negative likelihood, zero
compatible support, board regression, or any opponent/future card in a
controlled decision key.

This gate does not compute the normalized five-opponent full-width joint tensor
or exact full-width marginals. The factor representation is exact and compact;
its general contraction cost is a separate checkpoint. Storage is not a latency
or decision-quality result.

### Frozen immutable reference policy

Use a frozen policy algorithm with no deal, opponent cards, future board, model,
or mutable table. Every lookup first constructs the existing exact
`BlueprintDecisionKey` for the acting hypothetical hand and current public
betting state. The source digest binds its identifier, algorithm version, and
the following integer-weight rule.

For private-card ranks `r1,r2` in 2 through 14, let `S=r1+r2`, `P=1` for a pair,
and `U=1` for a suited hand. Assign:

- check or call weight `64 + S + 8*P + 2*U`;
- fold weight `33 - min(S, 28)` when fold is legal; and
- every exact legal raise-to `t` weight
  `1 + S + 8*P + 2*U + ((t - minimum_raise_to) mod 5)`.

Every unavailable action has weight zero. The denominator is the exact integer
sum over all currently legal actions, including every integer raise-to amount
in the legal interval. Its modular raise sum must use closed integer arithmetic;
the likelihood path may not enumerate or cap the raise interval. Action
probabilities are retained as reduced integer numerator/denominator pairs and
converted to Float64 only at the existing factor backend.

The passive check/call action is the unique maximum under these constants. The
source is deliberately weak, but it is total over every exact legal betting
amount and can assign a likelihood to an observed fold, check, call, short
all-in, ordinary raise, or full all-in. It proposes its passive maximum as a
candidate while ADR-0288's immutable deterministic source remains the atomic
fallback. This proves candidate projection and amount provenance, not strategy
quality or a chosen action abstraction.

### Frozen collision controls

Add a pure-Python rational oracle independent of `FactorizedCardBelief`. Given
two through five reduced hand axes and exact rational unary weights, it
enumerates the Cartesian product, removes every overlapping assignment, sums
the exact `Fraction` partition, and returns exact normalized per-seat marginals.
It rejects a caller request above its explicit Cartesian-work bound.

Use deterministic blocker-stress and seeded projections of the maintained full
axes, with two through five hands per opponent and at most 100,000 Cartesian
assignments per case. Compare the production factorized materialization and all
marginals to the rational oracle within `1e-12`, with exact support identity and
exactly zero incompatible mass. Include at least one projection where separately
normalized unary marginals differ positively from the collision-aware marginals;
reporting the independent product as the joint belief is a gate failure.

At full width, independently probe exact hand-axis membership, pairwise joint
compatibility, action-likelihood numerator/denominator identity, board filtering,
and the analytic compatible-support count. Do not enumerate the full joint or
infer normalized full-width marginal accuracy from these probes.

### Frozen complete-hand trace

Reuse ADR-0287 fixture A literally: button 0, equal 200-chip stacks, blinds 1/2,
controlled seat 3, the same six private pairs, board `2c 7d 9h Js Qc`, and the
same 20 opponent call/check events. No action, card, stack, or expected outcome
may change.

The full-width policy must propose `call/check/check/check` for the controlled
seat, while the deterministic passive source remains the fallback. Before each
opponent action is applied, compute its likelihood over that opponent's complete
current axis and update exactly that unary factor. Controlled actions do not
update the controlled observer's opponent belief. Each board reveal filters all
five axes. The hand must retain 20 opponent updates, four belief snapshots with
the exact widths above, four closing street ledgers, one 12-chip pot, and the
same seat-3 K-high-straight payout.

Initial full-width construction, action-likelihood/key work, Bayesian unary
update, controlled policy selection, and board filtering are agent work and
must each own named charged intervals in ADR-0288's cumulative 15-second street
ledger. Source construction is immutable pre-hand preparation. Snapshot/digest
audit work is charged in this reference trace. Post-terminal showdown and
settlement verification remain separately reported harness work.

## Gates

The checkpoint passes only if all of the following hold:

- all five axes have exact street widths and contain every and only compatible
  combo in canonical order;
- analytic compatible counts, reduced rational enumeration, production support,
  partitions, and marginals agree within the frozen boundary;
- public action updates affect only the acting opponent's unary factor, preserve
  exact source/key/likelihood provenance, and reject every malformed mutation;
- the policy denominator covers the entire exact legal integer raise interval
  without enumeration, all probabilities are exact reduced rationals, the
  passive candidate is legal, and arbitrary exact raise amounts receive the
  frozen positive weight;
- the unchanged complete hand reproduces its action order, 20 belief updates,
  four widths/digests, pot, payout, chip conservation, interval-ledger bijection,
  and four sub-15-second closing snapshots;
- missing/stale policy context, wrong actor, wrong hand axis, all-zero action
  mass, future board, duplicate cards, board-regression, mutable aliases,
  numerical booleans, nonfinite Float64 conversion, and oracle overwork fail
  closed; and
- the complete repository suite, changed-file Ruff, Python 3.11 parse,
  generated front door, documentation integrity, whitespace, and preservation
  of the ADR-0288 baseline all pass.

## Kill criterion

Any collision-support, partition, marginal, blocker, update, provenance,
legality, exact-amount, replay, pot, payout, timing, or visibility mismatch
rejects the gate. So does any attempt to rescue it by reducing the full hand
axes, clipping the legal raise interval, moving belief work off-clock, changing
fixture A, opening a strategy label, or calling compact factor storage a solved
full-width value contraction.

On rejection, retain ADR-0288's passive complete-hand loop and do not connect
the convex master, resident resolver, h32 cache, or any trained model.

## Claims boundary

A pass would establish only a full-width symbolic range and immutable policy-
probability interface for one controlled seat under an ordinary behavioral
opponent model. It would not establish exact normalized full-width marginals,
payoff/value contraction, a trained blueprint, strategic credibility, action-
abstraction quality, off-tree translation, solving, safety, exploitability,
NashConv improvement, AIVAT, league strength, optimized latency, live dealing,
or a complete C5 bot. No revoked experiment or external publication is
authorized.
