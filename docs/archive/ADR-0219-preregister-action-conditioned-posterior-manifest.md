# ADR-0219: Preregister the action-conditioned posterior manifest

- Status: accepted label-free preregistration before any action-conditioned warm step or label
- Date: 2026-08-21
- Depends on: ADR-0145, ADR-0179, ADR-0206, ADR-0212, and ADR-0218
- Config: `experiments/configs/h32-action-conditioned-posterior-manifest-v1.json`
- Config SHA-256: `c45c38504ced043a586e6466f5b6a333cd24cbef5446fae783a6263cc650a45e`
- Manifest builder: `src/pontius/h32_action_conditioned_posterior_manifest.py`
- Manifest-builder SHA-256: `e30483bb9a72cbd57e3ad1ed8591ba39508a6542888a099996802fd7048c0db1`
- Control: `tests/test_h32_action_conditioned_posterior_manifest.py`
- Control SHA-256: `c5f78c0a03ce087d1948efbb73b8505271ecbafc7fcbeb4496c643ded5d57832`

## Question

Can the retained source blueprints produce a balanced, nondegenerate, exact
factorized-belief panel of posteriors conditioned on in-tree observed betting
sequences, before any strategy opportunity is measured?

This is a target-manifest preflight. It creates no warm candidate, affine row,
certificate, quality evaluation, or strategy label. Its only decision is
whether a later widened-corpus preregistration has valid frozen targets.

## Exact posterior construction

For observed bettor `b`, the public sequence is:

```text
p0:check / ... / p(b-1):check / pb:bet
```

The empty prefix for bettor zero is simply `p0:bet`. For every action in public
order, read the frozen source average-64 blueprint's behavioral probability at
each private hand of the acting seat. Multiply that 32-entry vector into the
actor's unary range with `FactorizedCardBelief.with_likelihood` before applying
the next observed action.

Conditioning only on the final bet would be wrong for bettors one through five:
the preceding checks also carry range information. The reduced control uses a
three-action toy prefix and requires all three unary likelihoods to survive in
the posterior.

Zero probabilities are legitimate Bayes likelihoods, provided the observed
action has positive mass somewhere. Require exact hand-axis preservation and
a nonzero acting-seat marginal shift. Compute exact source and posterior
marginals with the meet-in-the-middle contraction and require its split replay
error at most `1e-12`.

## Balanced panel independent of labels

Use every one of the six frozen sources exactly twice. The first Latin round
assigns observed bettor equal to source index. The second adds three modulo
six. The resulting 12 targets cover:

- all three boards and both range families;
- every source exactly twice;
- every observed bettor exactly twice; and
- 42 observed action rows in total.

This mapping is frozen without inspecting posterior magnitude or any strategy
label. It prevents opportunity, board, family, or position outcomes from
choosing which contexts enter the later experiment.

## Identity and freshness

Reconstruct each canonical h32 source belief and average-64 policy. Require the
source belief and policy digests to match ADR-0145. Every target belief digest
must be unique, differ from its source, and be absent—along with its descriptor
digest—from commit `6d966cb`, the state before this manifest line began.

Record per-action likelihood support and min/max/mean, exact per-seat marginal
TV, the acting-seat marginal TV, partitions, action sequence, belief digest,
and descriptor digest. These are belief descriptors only; they cannot select a
candidate, threshold, target, or strategy.

## Boundary that remains open

The h32 resident engine currently evaluates the complete frozen river public
tree from seat zero. This manifest conditions the private-card belief on an
observed prefix, but it does not yet root the tensor layout and terminal
automata at the continuation state after that prefix. It is therefore a clean
test of action-conditioned range transfer, not yet a complete continual-
resolving deployment replica.

Do not obscure that distinction by calling the later labels full live-subgame
evidence. A continuation-root engine would require a separate structural and
payoff-accounting contract.

## Gates and next branch

Run once from a clean commit. Require all parent, balance, identity,
freshness, nondegeneracy, finiteness, and 600-second gates. New warm steps,
certificates, quality evaluations, and strategy labels must all remain zero.

- If any target is degenerate, stale, duplicated, or structurally invalid,
  reject this panel before GPU science.
- If all gates pass, seal exact target and descriptor digests, then
  preregister the widened single-family regret-vertex corpus against them.

The later corpus must enumerate every coherent changed public-node block,
derive K only from the ADR-0212 wall ledger and observed label-independent
costs, score per target before pooled summaries, preserve immutable-blueprint
fallback, and hold exact strategy labels until every feature and capacity row
is frozen.

No strategy is populated and no strategy-quality, opportunity-distribution,
transfer, deployment, population, composition, or hardware claim is made.
