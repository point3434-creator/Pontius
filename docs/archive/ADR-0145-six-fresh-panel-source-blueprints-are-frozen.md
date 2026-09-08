# ADR-0145: Six fresh-panel source blueprints are frozen

## Status

ADR-0144 executed from its clean preregistration commit and all 25 frozen gates
passed.

## Evidence identity

The 21,121,245-byte result artifact is
`experiments/results/h32-fresh-panel-source-blueprints-v1.json`, SHA-256
`c2a6691d214eec7e35c9f4d18e489f60de1ebf47cb35bba9785796e0582cbced`.
Its configuration SHA-256 is
`6b806a01073e0e07026b8d6beae80630d619225555387f1894c321b9fbb225df`.
The implementation SHA-256 is
`e53225cf8cdbc7d3a7012f59fb11f8169e41a41c4bc8b6bad5349be73f70dc0b`.
The artifact records strict clean Git state at
`1364a1c3c26756a2c9db46e2053b1bc7e7fbb863` and completed in
`4137.2824 s`.

An initial invocation stopped before source construction because the packaged
CUDA DLL environment variable was absent.  It wrote no artifact and executed
no source step.  The recorded invocation supplied the same packaged CUDA
directory used by the resident lineage and began from the unchanged clean
preregistration commit.

## Construction result

Exactly six cold one-size resident DCFR trajectories ran uninterrupted through
iteration 64: balanced and blocker-heavy sources on each of the three fresh
boards.  The run executed 384 source steps and retained one full canonical
iteration-64 checkpoint per source.  Digest summaries at iterations 1, 2, 4,
8, 16, 32, and 64 are included in the artifact.

Every final checkpoint survived canonical JSON round-trip and immediate restore
into a pristine compatible resident solver with exact state, current-policy,
and average-policy digest identity.  No restored solver was continued.  The six
immutable blueprints are the following `64:average` identities:

| Source | Final state SHA-256 | Average-policy SHA-256 |
|---|---|---|
| panel 1 / balanced | `fab601421d7dc8a482dc3bcdafdcc9cdc16efa811845f565a7d210f51c693394` | `3e8ea26a335b94c920eb85b6cddbc46d1c5a6801f5e1e280218d7b7d23fa376e` |
| panel 1 / blocker-heavy | `bc5374c87a0e3f1460c78d3b30abb3d19c56a34847a0d0922543414d011bfe90` | `ac0714d6d0371bcc33831029762d6a6ffb7ec82fdddde1108c317bca9bbe9f32` |
| panel 2 / blocker-heavy | `f043c754fb3ec9479fefa78f84cef999db113c8ddd01b5fdd6f7195774863518` | `ff1fd9de19ed158f4c1d001b459bd1475e129a3bf38a80daa6b04827a6e0be34` |
| panel 2 / balanced | `28e52c81f41be351fb8f7cdebc1cc108c67339e18ef9498abfd5acb213fe501a` | `3bbd6f2d612de578aaac8a658814dd37367519f9e312546e8788a594f828ff0c` |
| panel 3 / balanced | `6d8f674336a26010400b1f9c4e7764498c32fcbafa68f573c08f83d171518c83` | `7e6f3b4c47a426aad124d8fc15e20547db96fbb16327c9b04c167e51b8d8efdd` |
| panel 3 / blocker-heavy | `a619bc658788a4f2bed0ab9df1775b4ae3a07b59380ce14e0fbd90bf87bb9f87` | `0652da12f493d9251d9cffa4064cd47dc5e602dd61ef40d106f7c165145ac081` |

## Frozen-gate and resource result

All six training trajectories finished before the first source diagnostic.
All checkpoint states and diagnostic vectors were finite.  Maximum diagnostic
zero-sum residual was `5.163e-15`, and deviation-vector accounting was exact at
the frozen tolerance.

- Maximum source step: `13,127.0843 ms` against the `60,000 ms` ceiling.
- Maximum source diagnostic: `12,268.4343 ms` against the `120,000 ms` ceiling.
- Maximum cache compilation: `4,186.2271 ms` against the `120,000 ms` ceiling.
- Maximum GPU-pool total: `7,706,509,312` bytes against the `12 GB` ceiling.

Training time ranged from `516.290 s` for panel 3 blocker-heavy to `808.109 s`
for panel 2 balanced.  These are laboratory construction bills, not production
latency measurements.

## Quality accounting boundary

The six fixed post-training source diagnostics reported normalized NashConv
from approximately `0.001705` to `0.002882`.  These values had no threshold,
did not rank or select a source, and occurred only after every source trajectory
was complete.  They are retained as finite/zero-sum accounting, not evidence
that one board or family has a better strategy.

The artifact constructed zero target beliefs, zero sized trees, and zero target
quality profiles.  Its strategy-quality claim is null.

## Decision

Freeze the six exact `average64` checkpoints as source artifacts for a
separately preregistered transfer experiment.  The next experiment may define
fresh-panel targets and an outcome-neutral acceptance rule, but it must pin
those identities and rules before reading target labels.

Do not infer action-width value, source superiority, board-population
generality, or production readiness from this construction result.

## Scope

This result covers three deterministic river boards, two generated h32 range
families, one `3`-chip action size, six equal stacks, one cold DCFR schedule,
and one resident GPU environment.  It does not cover a full 1,081-combo range,
earlier streets, raises, side pots, target transfer, or two-size strategy.
