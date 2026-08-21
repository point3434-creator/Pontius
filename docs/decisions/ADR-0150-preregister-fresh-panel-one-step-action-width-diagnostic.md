# ADR-0150: Preregister fresh-panel one-step action-width diagnostic

## Status

Frozen after ADR-0149 and before any fresh-panel h32 two-size policy step or
two-size strategy-quality measurement.

## Context

ADR-0143 found all 24 fresh-panel one-size and two-size resident caches safe.
ADR-0145 then froze six source-only average-64 one-size blueprints. ADR-0149
measured two one-size target-transfer steps on all 12 label-free targets. It
accepted one non-blueprint candidate and abstained on 11 targets, but made no
action-width claim.

That result is now disclosed evidence. It is not a target filter, order rule,
gate, expected winner, or reason to widen only the accepted local target. All
12 identities were fixed before their one-size labels existed, and all 12
remain scheduled here.

The next bounded question is whether one complete warm resident step behaves
differently when the public tree retains one bet size or admits the already
preflighted second size. This is a diagnostic of this panel and horizon, not a
strategy-quality or population action-width conclusion.

## Frozen identities

The machine-readable contract is
`experiments/configs/h32-fresh-panel-action-width-warm-step-v1.json`, SHA-256
`f677e75be8fc2fc3680667799031ad455bf6c81d7a0253ecb3cd9b2e42c14372`.
The additive runner is
`src/pontius/h32_fresh_panel_action_width_warm_step_audit.py`, SHA-256
`77ee4b7c72e45ff2abfb3c59b75347d8b9ca5cd280cff8e79acf875cdacd557d`.
Its direct control is
`tests/test_h32_fresh_panel_action_width_warm_step_audit.py`, SHA-256
`88f6606ac5094abd10ebefc45b2c0a362719f520d13df06bc453e85ef0b2a576`.
The result target is
`experiments/results/h32-fresh-panel-action-width-warm-step-v1.json`.

The contract pins ADR-0143's cache result and config, ADR-0145's source result
and config, ADR-0149's accepted result and corrected config, the original
target-identity config, and the action-width bridge, solver, evaluator, and
runner implementations. Every referenced config is reparsed by its strict
validator.

ADR-0149 is pinned so the disclosed outcome cannot silently change. The new
runner reads it only for identity, pass status, and its null action-width
claim. It does not read target selections while scheduling or measuring this
workload.

## Frozen workload

For each of the 12 targets, in the original frozen order:

1. reconstruct the matching immutable source average-64 blueprint;
2. reproduce the source belief, target belief, target descriptor, and hand
   axes;
3. build a one-size arm with bet `3` and a two-size arm with bets `(3, 6)`;
4. warm each arm from its corresponding blueprint with pseudo-regret mass
   `0.1 *` that arm's layout-derived payoff span;
5. execute exactly one complete resident DCFR step in each arm; and
6. only after both steps finish, evaluate the embedded source blueprint and
   both current-1 candidates completely in a fresh two-size verifier.

Arm order alternates one/two and two/one across the 12 targets. There is no
deadline stream, interpolation, average-policy candidate, second step, or
outcome-dependent early stop. The one-size current-1 policy is embedded with
zero opening mass on bet `6`; below that off-tree action it uses the frozen
retained-bet continuation. The two-size current-1 policy is represented in the
same compact schema and is required to round-trip exactly.

The common verifier has layout-derived payoff span `48` and fixed seat order
`0,1,2,3,4,5`. Both candidates receive complete six-seat quality vectors.
Each is then considered separately against the same immutable embedded
blueprint cap vector, using raw guard `1e-10 * 48`. A candidate may be reported
as feasible or selected for this one-shot certificate, but it never becomes a
new anchor.

## Frozen measurements

For each planning arm, record target-workspace construction, resident-cache
construction, belief and automaton persistent bytes, GPU-pool totals,
physical-device free bytes, maximum and total middle rank, accumulator bytes,
warm-start numerical distance, complete-step wall time and work telemetry,
compact-policy identity, total variation from the incumbent, and added-bet
use.

For the common verifier, record cold construction, all profile utilities,
best-response values, deviation gains, NashConv, normalized NashConv,
zero-sum residual, quality-vector sum error, full wall time, cap diagnostics,
and separate fixed-envelope selections. Report the paired two-minus-one
candidate normalized reduction as an ungated diagnostic.

## Frozen gates

The run passes only if:

1. the repository is clean and every pinned source reproduces;
2. ADR-0143 passes, authorizes all 24 caches, records zero h32 strategy work,
   and keeps its strategy claim null;
3. ADR-0145 and ADR-0149 pass, and ADR-0149 keeps its action-width claim null;
4. the h2 common-game utility, exact-quality, zero-sum, compact round-trip,
   378-shared-basis, and payoff-span controls reproduce;
5. all 12 targets, 24 arms, 24 complete steps, and 36 complete widened quality
   profiles execute in frozen order;
6. every source and target identity reproduces and both payoff spans are
   layout-derived as `30` and `48`;
7. warm-start mean total variation is at most `1e-12`, every step is at most
   `60 s`, every cache construction is at most `120 s`, and every complete
   profile is at most `120 s`;
8. all policies, telemetry, and quality values are finite, every compact
   policy round-trips, and both arms finish planning before target quality;
9. quality-vector sum error is at most `1e-10`, zero-sum residual is at most
   `1e-9`, and any selected candidate satisfies every immutable blueprint cap;
10. the GPU pool remains below `12 GB`, total wall time remains below `5,400 s`,
    and the top-level strategy-quality claim is null.

There is no gate on NashConv direction, reduction, candidate feasibility,
selection, abstention, arm winner, added-bet probability, cost ratio, or any
panel aggregate.

## Decision branches

- **Mechanism failure:** preserve the artifact, make no strategic
  interpretation, and repair only under a new preregistration.
- **Clean diagnostic outcome:** report all paired values, cap decisions, costs,
  and added-bet use while retaining a null strategy-quality claim.
- **Apparent width advantage:** treat it as panel-specific, one-step diagnostic
  evidence only. Do not change the action abstraction or make a strategy claim.

## Pre-freeze controls

Three direct controls pass. They reproduce all 12 inherited target identities,
pin one step per arm and 36 complete profiles, reject prior-outcome, target
order, step-count, gate, and source-hash mutations, and require the explicit
independence rule. No fresh-panel h32 two-size step or quality profile was
constructed during these controls.

## Dissent

**Confidence:** extremely high in identity and memory authorization; high in
the common-game bridge and complete-quality measurement; low that one warm
step identifies the long-run value of a second bet size.

**Opposing evidence:** two revealed boards previously produced universal
fixed-cap abstention under wider wall-clock streams. ADR-0149 produced one
safe one-size transfer on this fresh panel. Both facts are relevant context,
but neither predicts this frozen paired result.

**Largest risk:** readers mistake complete candidate quality outside the fixed
caps, or a 12-target paired average, for a deployable width ranking. The
policies are deliberately shallow and share only three boards and two range
families.

**Cheapest falsification:** run this artifact once. Any identity, memory,
bridge, exactness, phase-order, step, or cap-selection failure rejects the
mechanism. A clean directional result remains claim-null until independently
replicated at a separately preregistered horizon or panel.
