# ADR-0235: One continuation step is retained after held-out depth value trial

- Status: accepted fresh research result; two-step promotion rejected
- Date: 2026-08-22
- Implements: ADR-0234
- Clean preregistration commit: `47513af`
- Result: `experiments/results/h32-heldout-continuation-depth-value-v1.json`
- Result SHA-256: `b510ca940ab2f2c856fa525e471d8b5eb4062a9db35cde26951696b12d9f5053`

## Formal result

Every provenance, parent, target, arm, step, counterbalance, posterior identity,
source checkpoint, blueprint, warm-start, complete 31-block partition, six-row
charge, affine intercept, feature-label barrier, independent teacher, winner,
deadline fallback, timing, memory, finite, immutable-emission, and no-population
gate passes. The clean recorded run completed in `470.071 s`.

An initial invocation stopped before CUDA initialization because the shell had
not set the runbook's pinned `PONTIUS_CUDA_DLL_DIRECTORY`. It wrote no artifact,
constructed no h32 context, and opened no strategy label. The recorded
invocation used the identical commit and configuration with only that required
process environment initialized, matching the established ADR-0212 precedent.

All 24 independent arms price all 31 blocks. All 24 frozen winners receive one
independent complete exact certificate and are accepted by the shadow rule.
Maximum affine intercept error is zero and maximum affine-to-teacher error is
`1.51e-14`. One-step charged ledgers range from `5,746.122` to `10,537.737 ms`;
two-step ledgers range from `6,472.376` to `12,174.857 ms`. The worst two-step
arm retains `2,825.143 ms` of the hard 15-second boundary.

## Depth does not buy value

One step delivers pooled exact value `0.05632596326410032` in
`91,670.303 ms` of pooled charged ledger. Two steps deliver
`0.05570904250396959` in `104,507.464 ms`. The second step therefore:

- reduces pooled exact value by `0.0006169207601307292` (`1.095%`);
- increases charged time by `14.004%`; and
- reduces value per charged second from `0.000614441` to `0.000533063`
  (`13.244%`).

The raw sign count is six target wins and six losses, but that count is
numerically misleading. Eleven targets select byte-identical endpoint and
interpolated winner policies at both depths; their value differences are only
Float64 reassociation noise. The sole material change is
`panel_2/blocker_heavy/checks_then_bet_seat0`: its two-step direction switches
to a different public block and delivered value falls by
`0.0006169207601308124`.

The preregistered promotion rule fails both of its substantive requirements:
two-step pooled value does not clear the one-raw-guard-per-target materiality
floor, and its value rate is lower.

## Decision

Retain one continuation step. Do not spend street time on a second ordinary
DCFR step for this workload. The extra step is affordable, but affordability is
not value; in 11 of 12 held-out targets it reproduces the same regret-vertex
winner and in the remaining target it selects a worse one.

The next strategy experiment should spend the recovered second on direction or
action diversity, not ordinary depth. Preregister a label-free capacity screen
before opening another strategy panel. Preserve the one-step continuation root,
all 31 blocks, full affine envelope, exact winner proof, hard deadline, shared
payoff semantics, runner harness, and immutable fallback.

This is positive held-out evidence for the one-step reduced-h32 continuation
spine, not a claim about more steps, other generators, other streets,
deployment, composition, population performance, or broad poker strength.
