# ADR-0244: Preregister h32 one-seat open-axis preflight

- Status: accepted preregistration before any h32 full-axis row pass
- Date: 2026-08-22
- Follows: ADR-0243
- Config: `experiments/configs/h32-one-seat-open-axis-preflight-v1.json`
- Config SHA-256: `17c681eb5e9e4cfa7511389b66306260c4edcadb925640ada35ae8f2588e2a51`
- Behavioral-row primitive SHA-256: `382b3d15542f29fde07ffb43500f29f93c3ec9503736e5093383206b0e0e3f24`
- Behavioral-row control SHA-256: `1edb562c0820e1c2fed641a43dc59c82810594d836ed100d26e91d7e5956f393`
- Implementation SHA-256: `3087b39d95f942c92b75f713cb5ecc2d6a9ff10ba0467477c7459643b3efd227`
- Runner control SHA-256: `01606d529999daa3a36825990dd1b6ba392d4b4bf211929fe34adc4c042085a5`

## Question

On the accepted h32 post-bet continuation, can eleven resident target-omitted
passes construct the six exact gain rows needed to initialize a one-seat
cutting-plane master? Are the full rows accurate, small, conditioned, and fast
enough that at least one complete response-oracle/cut/master round plus a
separate independent final proof still fits the 15-second street boundary?

This is a label-free coefficient and capacity preflight. It does not solve a
master, generate a new direction, certify a candidate, or ask whether any
policy has value.

## Frozen target and scope

Use the tight retained Latin-D target
`panel_2/balanced/checks_then_bet_seat1`, the largest expanded ledger in
ADR-0237. Reconstruct its immutable restricted average-64 blueprint and run
exactly one accepted device-fold continuation DCFR step.

Open acting seat 0, the widest responding seat: 16 public nodes, 512 external
h32 information sets, and 1,024 behavioral action entries per payoff row. The
compiled path-single-visit gate must pass. This sufficient behavioral shortcut
is deliberately confined to the post-bet continuation; a repeated-actor
topology must use sequence form and is outside this preflight.

## Frozen row construction

At the immutable source policy, run exactly:

1. six full resident profile-payoff passes, one per payoff seat; and
2. five full resident fixed-response-payoff passes, one for each opponent of
   acting seat 0.

Every fixed response uses the explicit external posterior hand axes and exact
source response-key coverage. Build the acting seat's gain as its invariant
best-response constant minus its profile row. Build each opponent gain row as
fixed-response row minus profile row. Retain all six epigraph families.

Do not infer a profile row from zero sum, delete a numerically similar row, or
deduplicate at an LP tolerance. Serialize exact row digests, errors,
conditioning, and bytes, but no coefficient values. Exact response signatures
remain the only eventual response-row identity.

## Frozen independent projections

After row construction and the capacity decision have been computed, rebuild
only the 16 already-frozen one-node regret-vertex endpoints owned by acting
seat 0. Project all six full rows onto every endpoint and compare profile,
fixed-response, and gain slopes with the accepted selector-stable affine
teacher. Require 96 teacher rows and maximum error at most `2e-11` in every
family.

The teacher may share accepted payoff contraction semantics, but it may not
call the full behavioral-row assembler. ADR-0243's direct dense h4 teacher is
the lower-level independence control. No opportunity, admission, NashConv, or
certified-value field may be serialized.

## Frozen measurements

Measure and report:

- cold resident setup, belief compile, and six-seat source-response compile;
- one warm-step wall and attributable resident work;
- every profile and response pass wall, contraction, reverse, rank, batch,
  transfer, fold, scratch, and GPU-pool field;
- total initial-row construction and the five-response-row subtotal;
- six-row numerical rank, effective condition number, and minimum normalized
  separation without deleting any row;
- retained row bytes, shared resident bytes, response-cache bytes, solver
  bytes, maximum middle rank, maximum peak numeric bytes, pool total, and
  minimum physical free bytes; and
- teacher time and error maxima after the capacity calculation.

The cold setup and teacher are reported but are not smuggled into the resident
live path. The source-response compile is nevertheless charged as the price
proxy for every future full exact response oracle.

## Frozen cut-round ledger

The former fixed `1,250 ms` one-node proof reserve is not sufficient evidence
for a seat-wide policy. Derive the ledger from this run before opening teacher
projections:

```text
fixed = one warm step
      + eleven initial row passes
      + max(1,250 ms, 1.25 × measured six-seat source-response oracle)
        reserved for the independent final certificate
      + 50 ms retreat/envelope reserve
      + 1,000 ms synchronization/emission reserve

each cut round = max(1,250 ms, 1.25 × measured source-response oracle)
               + 1.25 × measured five fixed-response row passes
               + 500 ms unmeasured master reserve
```

The round reserves all five possible new opponent rows even if some active
responses remain unchanged. The final-certificate oracle is separate from
every cut oracle. Report `floor((15,000 ms - fixed) / each cut round)` without
using teacher labels or timing to alter the workload.

This capacity is deliberately conservative about row/oracle variation but is
not a convergence claim: actual cut count and h32 master latency remain for the
successor prototype.

## Promotion rule

If every identity, topology, provenance, finite-runtime, immutable-emission,
no-label, memory, and process gate passes and at least one complete cut round
fits, authorize one label-free h32 one-seat master prototype. That prototype
must measure actual master bounds, exact response-oracle iterations, added
response rows, cut count, timeout `U - L`, retreat, and an independent final
certificate before any strategy-quality trial.

If coefficients are exact but zero complete rounds fit, retain the primitive
for off-clock work and reject this live master path. If identity, external-axis
coverage, memory, or topology fails, reject the preflight rather than tuning
the teacher or selecting a narrower acting seat from the outcome.

## Claims boundary

A pass establishes only h32 full-axis coefficient identity, residency, and the
capacity for at least one conservative prototype round on one target and one
acting seat. It makes no strategy-quality, optimizer-convergence, multiplayer-
safe, deployment, composition, cross-street, population, or broad poker-
strength claim. The independent exact verifier remains the sole emission
authority.

## Decision

Commit the row primitive, preflight runner, config, controls, this ADR,
roadmap, and generated status from one clean tree before the first h32 full-
axis pass. Invoke the frozen runner once and follow the preregistered capacity
branch without changing acting seat, tolerances, reserves, or row families.
