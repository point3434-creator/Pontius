# ADR-0111: Fixed-envelope certificates do not reanchor implicitly

**Status:** Accepted; certificate scope and sequential-deployment semantics
frozen before the first fresh-board h32 transfer audit

**Date:** 2026-08-20

## Decision

An ADR-0106 fixed-blueprint-envelope certificate is a one-decision,
one-belief, one-public-root certificate. Selecting or deploying a candidate
does **not** make that candidate the safety anchor of the next decision.

The six acceptance caps remain derived from the immutable certified blueprint
at the certificate's declared root:

`cap_i = deviation_gain_i(blueprint; root, belief) + raw_guard`.

No implementation may replace `blueprint` in that expression with the latest
selected policy merely because the previous candidate passed. Doing so would
permit repeated spending of the same coordinate slack and could random-walk a
seat's deviation gain while every local comparison appeared safe.

## Required certificate scope

Every certificate that claims blueprint-relative unilateral safety must bind
at least:

- the immutable episode blueprint policy digest;
- the certification public-root digest and payoff model;
- the belief digest at that root;
- the already-deployed policy-prefix digest, including all earlier actions
  that affect reach into the certified root;
- the six exact blueprint deviation gains and resulting cap vector;
- the raw guard and payoff span;
- the complete verified candidate policy digest; and
- the verifier implementation and source-provenance digests.

A mismatch in any bound field invalidates reuse of the certificate. A selected
candidate's digest may appear as the deployed policy, but never silently as a
new blueprint anchor.

## Sequential decisions

The current verifier proves a fixed-policy unilateral vector only at its
declared root and belief. After a public transition, private observation,
belief update, or earlier-policy change, that certificate expires for any
claim about cumulative root safety.

The system may construct a new local certificate at the new state. That new
certificate is useful for the local decision, but independent local
certificates must not be summed, chained, or described as a global
no-worse-than-blueprint guarantee.

A cumulative episode-root safety claim requires one of two future mechanisms:

1. exact recertification of the fully composed deployed root policy against
   the immutable episode-root blueprint; or
2. a proved compositional ledger that transports counterfactual reach and
   signed error budgets across public transitions without double-counting
   slack.

Neither mechanism exists in the current six-player system. In particular, six
unilateral deviation-gain caps are not a coalition certificate and do not
inherit two-player safe-subgame-solving guarantees.

## Consequences for experiments

Every current h32 acceptance audit is explicitly one-shot per frozen target
belief. It may compare many candidates inside one immutable blueprint envelope,
but it may not treat the selected candidate as a new safety baseline for a
subsequent target or public state.

The forthcoming fresh-board audit must serialize this rule as a frozen config
field and report its blueprint, root, belief, and policy digests. Its strategy
outcomes cannot authorize sequential reanchoring.

## Why this is stricter than a prose caveat

ADR-0106 made selection order-independent by choosing the optimum verified
policy inside a fixed box. That result does not make the box time-consistent.
Time consistency depends on how the root policy, reach distribution, and
counterfactual values compose across decisions. Multiplayer poker supplies no
free theorem that turns locally feasible boxes into a globally feasible
trajectory.

The safe default is therefore expiration, not reanchoring. This preserves the
meaning of every existing certificate while leaving a precise target for a
future composed-root verifier or reach-weighted ledger.

## Dissent protocol

**Confidence:** very high that implicit reanchoring is unjustified; high that
the required digest scope prevents accidental cross-state reuse.

**Opposing evidence:** exact composed-root recertification may eventually show
that many deployed candidates can safely serve as new anchors. That is a
measurement result to earn, not a property to assume.

**Largest risk:** users may read a sequence of valid local certificates as one
global guarantee even when the software keeps the records separate. Product
language must state the certified root and expiration boundary alongside every
decision.

**Cheapest falsification:** construct two consecutive locally feasible edits
that spend the same seat's blueprint slack, compose them at the original root,
and measure whether the final deviation gain breaches the original cap. Until
that experiment and a general accounting rule pass, implicit reanchoring stays
forbidden.
