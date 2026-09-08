# ADR-0185: Preregister a fresh h32 causal direction and opportunity screen

- Status: accepted preregistration
- Date: 2026-08-21
- Depends on: ADR-0166, ADR-0178, ADR-0179, ADR-0184
- Config: `experiments/configs/h32-fresh-causal-direction-screen-v1.json`

## Question

ADR-0178 positively identified ordinary one-step soft DCFR as generator-poor
within a two-direction library, while ADR-0184 found that 32-64 ordinary DCFR
steps add policy motion without a material certified-value lift. Which
pre-certificate observation, if any, locates decisive-direction opportunity on
fresh contexts, and does one deterministic third direction materially expand
the bounded library?

This audit separates three questions that prior work could not identify:

1. **opportunity location:** does regret mass or blueprint action-gap width rank
   the public blocks whose bounded direction library contains exact value;
2. **cap geometry:** does a fixed small vertex probe expose a wide or steep
   local policy-to-gain direction; and
3. **library width:** does an immutable-blueprint best-response vertex add
   value beyond soft DCFR and the instantaneous-regret vertex?

The full direction searches and all-six-block probe rankings are off-clock
labels. No feature is a live selector, and no candidate is a strategy-quality
claim.

## Frozen fresh panel

Use the full three-board by two-family source panel with previously unlabeled
seat-2 blocker shifts:

| Target | Selected seat-2 hand | Frozen target SHA-256 |
|---|---|---|
| panel 1 balanced | `6c Qh` | `c9c80d8bb428c2d701284302ec3332d72d5114f41f74a186c9493561be4f7267` |
| panel 1 blocker-heavy | `5s 8s` | `c9e24a106f970d3732b73c3a3325fd9b7f0fdbb0303d9621a5f1d0473301e718` |
| panel 2 balanced | `7s 9s` | `e359c590a2effaf6350274dd972a09e39a4fef37c57e548fd1fadef970128ed1` |
| panel 2 blocker-heavy | `6d Qh` | `41e485b87d097862e4b6021adcbdab4470bfa2f759c695acab3b6c3edbce6c4f` |
| panel 3 balanced | `5c Ac` | `1014d3b5e6a6aaebce7189788612c94dafe8f2b826da76e2ed568b1abc2bdef5` |
| panel 3 blocker-heavy | `3c 8h` | `bdf83667215c4e951759bfa8116a6889802a5d4b4cbd20ca8c4ae808c2b9187f` |

The label-free rule is unchanged: maximum opponent-axis card overlap, then
hand strength, then smallest canonical hand; double only that hand's positive
unary likelihood. Source, target, descriptor, hand-axis, and checkpoint
identities are frozen before any target policy step, probe, or quality label.

## Frozen blocks, free features, and probe

Run one resident DCFR step from the numerically identical immutable source
average-64 blueprint and construct the same six 32-hand public-node blocks as
ADR-0177. Before any candidate certificate for a block, record:

1. `regret_mass`: normalized positive best-action instantaneous-regret mass;
2. `negative_minimum_action_gap`: the negative normalized minimum action gap
   from that acting seat's immutable-blueprint exact best response.

The second score is negated so higher always means “more opportunity” under
the preregistered indifference hypothesis. It is deliberately the already
available per-seat minimum, not a post-label block statistic.

For every block, execute one exact regret-vertex certificate at scale `2^-16`.
If the adaptive label search later requests the same scale, reuse the exact
row; do not charge or recompute it twice. From the probe record:

- completion and binding seat;
- exact positive certified value;
- every evaluated per-seat gain change divided by scale;
- maximum positive observed gain slope; and
- the cap-radius estimate `min(1, raw_guard / maximum_positive_slope)`.

A stopped probe censors the radius because later seats were not evaluated.
Its objective-improvement slope is unavailable and stored as zero only as a
finite diagnostic value with the censor flag set. Probe value and estimated
radius are compared with labels off clock. Selecting among all six blocks by
either probe-derived feature would require six certificates and is explicitly
not a live rule.

## Three-direction bounded library

For every block compare, in order:

1. `soft_dcfr`;
2. `regret_vertex`; and
3. `best_response_vertex`.

The third family moves each selected information set to the exact action in
the acting seat's immutable-blueprint best-response tape. The tape is already
required to form the envelope and is fixed before candidate labels. First
action order continues to break exact ties. This is a direction generator,
not permission to play a best response in the multiplayer game.

Use ADR-0177's 34-point geometric grid and exact convex-scope adaptive search
for each direction. Every query changes one acting seat at one exact public
history and is independently certified against the immutable blueprint. The
fixed probe adds at most one unique query to the 16-query adaptive bound, for a
maximum of 17 unique certificates per regret-vertex direction and 1,764 total.

The bounded label is the largest exact positive certified value among the
three families, with family order as the tie-break. It remains a lower bound
on global attainable value.

## Identification table frozen before labels

The following observations have distinct meanings:

| Observation | Supported reading | Not established |
|---|---|---|
| Best-response vertex makes the three-family aggregate at least `2x` the paired aggregate and clears one raw guard per block in aggregate | the local value landscape remains direction-rich within this added family | that the third family transfers live or approaches a global oracle |
| Best-response vertex does not make that lift | this third family plateaus within the frozen library | opportunity exhaustion or adequacy of soft DCFR |
| A free feature has pooled Spearman `>= 0.5` and captures `>= 50%` of the sum of each target's best block under its frozen top-one rule | descriptive candidate for a separately controlled transfer | live scheduling, population performance, or useful fixed-scale value |
| Probe radius ranks value but probe value does not | cap geometry is informative but objective direction remains unidentified | a useful candidate |
| Probe value ranks the oracle | a charged certificate is an opportunity observation | feasibility of probing all six blocks inside a street |
| Objective-bound searches dominate | remaining immutable-anchor opportunity is exhausted along the library more often than caps bind | global anchor optimality |
| Cap-bound searches dominate | policy-to-gain sensitivity remains the immediate limiter | absence of value behind another direction |

Report pooled and within-target Spearman correlations for all four feature
scores. Also apply every feature's deterministic high-score rule with lowest
acting seat and then public-history order as tie-breaks. For each selected
block report offline bounded-oracle capture and the observed ledger for one
fixed probe. Only regret mass and action gap exist before that probe; the two
probe-derived selectors are off-clock upper-bound diagnostics.

The feature thresholds and the twofold third-family threshold are descriptive
classifications, not result pass gates.

## Fifteen-second boundary

The adaptive searches are never placed in a street. A hypothetical one-probe
ledger contains exactly:

```text
one resident warm step
+ selected block's fixed-scale construction
+ one exact vertex certificate
+ 1,000 ms synchronization/emission reserve
```

Blueprint and resident-context preparation remain outside the prepared street
and are reported separately under the established contract. A ledger below
15 seconds only establishes that a later precommitted free selector could
afford one attempt on the observed target. It does not authorize the observed
feature, block, scale, or candidate.

## Outcome-neutral gates

Require six targets, six warm steps, 36 coherent blocks, 108 direction rows,
36 fixed probes, six blueprint labels, clean committed execution, accepted
parents, all frozen source and target identities, numerical warm identity,
exact direction and feature order, best-response-vertex identity, fixed probe
identity, convex scope, adaptive-search invariants, no more than 1,764 unique
certificates, immutable anchors, independent certificates, finite recovered
regrets and outputs, blueprint emission, 60-second per-step and per-certificate
ceilings, the 12 GB pool ceiling, a 1 GB physical-free floor, and a broad
3,000-second audit ceiling.

Do not gate on feature correlation, selected seat, probe completion, cap
radius, binding condition, certified value, direction winner, library lift,
captured fraction, or descriptive 15-second fit.

## Frozen artifacts

- config SHA-256:
  `d86e443f42cd60749207f18c7ce784eba56ec950ea91626d7f8fefab82b94582`;
- implementation SHA-256:
  `e6520a3542451d38da498934fab5383e03f86764e56a6cd8095dadc220052bd9`;
- mutation-control SHA-256:
  `e0a903471594014f7066444de715f9a93101ef9bf7339a8477bf8d8afe854f5b`;
- result target:
  `experiments/results/h32-fresh-causal-direction-screen-v1.json`.

The six focused mutation and construction controls pass. No seat-2 target
policy step, target quality label, fixed probe, or direction certificate has
been executed.

## Decision

Commit this ADR, config, additive implementation, and controls before the
first target GPU step. Execute once from the clean preregistration commit.
Preserve the immutable anchor and emit only its blueprint. Do not introduce a
predictive/DCFR-family arm until this screen identifies whether another local
direction or a better opportunity feature is the next missing mechanism.
