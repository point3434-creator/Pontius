# Compute-matched continuation 001

All 64 retained cases: 16 existing boards, two regimes, two bets. Lower exact-hand
exploitability is better. This follow-up controls computation; it adds no fresh boards.

| Bet | Incumbent | Matched continuation | Generous continuation | Second repair |
|---|---:|---:|---:|---:|
| 10 | 0.018963221 | 0.018808061 | 0.018800391 | 0.013375485 |
| 5 | 0.009343606 | 0.009236643 | 0.009231606 | 0.006504161 |

## Representation limit and case directions

| Bet | Current-group mean floor | Repair below floor | Repair vs generous B/E/W |
|---|---:|---:|---|
| 10 | 0.018710135 | 30/32 | 30/0/2 |
| 5 | 0.009176545 | 29/32 | 30/0/2 |

Floor claims use independently verified exact-rational asymmetric certificates
on the retained binary64 payoff matrix. Below-floor counting requires a margin
over 1e-8 chips. More optimization within unchanged groups cannot beat that floor
in these games. This is separate from generalization or six-player strength.

## Measured computation

| Bet | Reference seconds | Matched seconds | Generous seconds |
|---|---:|---:|---:|
| 10 | 1.046931 | 1.045417 | 1.214726 |
| 5 | 1.049155 | 1.049617 | 1.217018 |

The matched checkpoint stops before crossing historical pre-gate work time.
Actual gate time varies; this is a nominal component match, not exact wall-time parity.
Generous training alone reaches the complete historical repair budget, then adds
acceptance time. It therefore favors continuation. Active blocks include snapshots
and updates; input reconstruction, scoring, trace formatting and verification are excluded.
One timing pass. Endpoints replay exactly; hardware timings are observations.

```json
{
  "10": {
    "means": {
      "generous": 0.018800390937692188,
      "incumbent": 0.018963220683849046,
      "matched": 0.018808061245151438,
      "repair": 0.013375485388023441
    },
    "repair_gain_percent": {
      "matched": 28.884294804859113,
      "generous": 28.855280550536644
    },
    "continuation_gain_percent": {
      "matched": 0.8182124823857377,
      "generous": 0.858660819654638
    },
    "mean_group_floor": 0.01871013537296093,
    "repair_below_floor_cases": 30,
    "mean_total_ratios": {
      "generous": 1.1602735076800474,
      "matched": 0.998553990080997
    },
    "ratio_ranges": {
      "matched": [
        0.9712601195944689,
        1.0233571057495972
      ],
      "generous": [
        1.1445986070771417,
        1.2279166350611124
      ]
    },
    "matched_over_budget_cases": 11,
    "mean_extra_iterations": {
      "generous": 38925.0,
      "matched": 32640.625
    },
    "extra_iteration_ranges": {
      "matched": [
        26400,
        35600
      ],
      "generous": [
        32500,
        42400
      ]
    },
    "mean_reference_seconds": 1.046930528129451,
    "mean_actual_seconds": {
      "matched": 1.0454166562012688,
      "generous": 1.2147257561700826
    },
    "versus_generous": {
      "better": 30,
      "worse": 2
    },
    "versus_matched": {
      "better": 30,
      "worse": 2
    },
    "board_directions": {
      "matched": {
        "better": 16
      },
      "generous": {
        "better": 16
      }
    },
    "lobo_beats_generous": true
  },
  "5": {
    "means": {
      "generous": 0.009231606231037444,
      "incumbent": 0.009343606279235476,
      "matched": 0.009236643115369274,
      "repair": 0.00650416136637298
    },
    "repair_gain_percent": {
      "matched": 29.583060803221816,
      "generous": 29.544640406071075
    },
    "continuation_gain_percent": {
      "matched": 1.1447738771261073,
      "generous": 1.1986811606877454
    },
    "mean_group_floor": 0.009176545285251853,
    "repair_below_floor_cases": 29,
    "mean_total_ratios": {
      "generous": 1.1599976073509828,
      "matched": 1.0004400473771473
    },
    "ratio_ranges": {
      "matched": [
        0.9770625802808998,
        1.061512297033771
      ],
      "generous": [
        1.144333066173597,
        1.2135307283309114
      ]
    },
    "matched_over_budget_cases": 10,
    "mean_extra_iterations": {
      "generous": 39306.25,
      "matched": 33125.0
    },
    "extra_iteration_ranges": {
      "matched": [
        29000,
        35800
      ],
      "generous": [
        33300,
        42100
      ]
    },
    "mean_reference_seconds": 1.0491554156305938,
    "mean_actual_seconds": {
      "matched": 1.049617093719462,
      "generous": 1.2170177718708146
    },
    "versus_generous": {
      "better": 30,
      "worse": 2
    },
    "versus_matched": {
      "better": 30,
      "worse": 2
    },
    "board_directions": {
      "matched": {
        "better": 16
      },
      "generous": {
        "better": 16
      }
    },
    "lobo_beats_generous": true
  }
}
```

## Frozen criteria and verification

```json
{
  "beats_generous_half_pot": true,
  "beats_matched_half_pot": true,
  "continuation_nonregression": true
}
```

The half-pot mean advantage threshold is 1e-6 chips for both comparisons.
All profiles must pass the unchanged per-role exact security gate against incumbent.
These are descriptive fixed-panel criteria, not confidence intervals.
15 preflight checks; four incumbent reconstructions before freeze.
Replay verifier: 3,143,400 updates, 64 timing traces,
128 asymmetric certificates, 128 raw and 128 selected profiles,
128 retained reference profiles and 128 independent gate audits. No new LPs or fitting.
Independent retention arithmetic checks: 3041.
Worker 162.913 s; verifier 187.031 s; total 350.053 s, exit 0.
Python 3.14.6, NumPy 2.5.2, SciPy 1.18.0; one BLAS thread; no allocation tracing.
900-second limit per phase; no hard RSS cap. All 25 prior milestones unchanged.
Heads-up one-bet river, 96 holdings per role, K=16; all compatible deals included.
No full-range, six-max, live-latency, population uncertainty or BB/100 claim.
No adoption, commit or push.

Plan SHA-256: b27e14569ef3f97ca7e036c12300894c6095930fb22d91186449d7b7056ed21d

Results manifest SHA-256: 4b7a6f230fea119fdbdf02919b257786e44a51c1d8806315681b44fc927cacbd
