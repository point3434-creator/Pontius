# ADR-0144: Preregister six fresh-panel source blueprints

## Status

Frozen after ADR-0143 established safe resident-cache headroom and before any
fresh-panel h32 source policy step or strategy-quality measurement.

## Workload

Construct exactly six independent source beliefs: balanced and blocker-heavy
h32 axes on each of the three deterministic fresh boards from ADR-0142.  Use
only the one-size `3`-chip game.  Each source receives one cold, uninterrupted
64-step resident DCFR trajectory.  The source order is fixed and alternates the
family order on the middle board to reduce a simple order confound.

Record state, current-policy, and average-policy identities at iterations 1,
2, 4, 8, 16, 32, and 64.  Retain the full canonical state only at iteration 64.
The immutable source blueprint is `64:average`; no measured diagnostic may
choose a different iteration or policy kind.

## Restart boundary

Round-trip every final checkpoint through canonical JSON, restore it into a
pristine compatible resident solver, and require immediate state/current/
average digest identity.  Do not continue the restored solver.  Prior evidence
shows that an immediate restore is exact while a resumed GPU path can acquire
small reduction-order differences; the scientific trajectory therefore stays
uninterrupted.

## Frozen-gate methodology

Require the ADR-0143 cache authorization, a clean Git state, exact six-source
belief identities, 384 total source steps, finite checkpoint states and
policies, exact JSON and restore identities, and the frozen resource ceilings.
All six training trajectories must finish before the first diagnostic quality
call.

After training, evaluate exactly the six source `average64` policies on their
own construction beliefs.  These diagnostics gate only finiteness, zero sum,
vector accounting, and resource ceilings.  NashConv is reported but has no
acceptance threshold, does not select a policy, and cannot affect any later
source trajectory.

## Prohibited work and decision rule

Construct zero target beliefs, zero two-size trees, and zero target quality
profiles.  Make no strategy-quality or action-width claim.

A complete pass freezes six exact source-blueprint artifacts for a separately
preregistered transfer experiment.  Any identity, numerical, ordering, or
resource failure rejects this construction run; it does not authorize tuning,
partial reruns, or selection from the observed source diagnostics.

## Dissent

Three boards and two range families are a deliberately small deterministic
panel.  Exact construction does not show that `average64` is strong, transfers
well, benefits from action widening, or represents the river-board population.
The cheapest next falsification is a frozen target-transfer panel whose target
identities and acceptance rule are registered without inspecting these source
diagnostics.
