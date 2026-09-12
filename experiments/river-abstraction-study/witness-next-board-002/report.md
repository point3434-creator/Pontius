# Next board 002

One fresh board through the frozen two-repair procedure. Four cases cover both
existing range regimes and bets. Every case is retained, including non-improvements.
This is one additional board, not a population confidence or six-max strength claim.

Board integer IDs: [25, 36, 38, 40, 51]. Texture: one-pair.
First unused board in the original SHA-256 sequence: attempt 8. Suit-equivalent prior boards excluded.

| Bet | Regime | Original | First repair | Second repair | Matched | Generous |
|---|---|---:|---:|---:|---:|---:|
| 5 | uniform | 0.007855472 | 0.006049318 | 0.004842177 | 0.005882739 | 0.005873782 |
| 10 | uniform | 0.014326130 | 0.008705893 | 0.007854991 | 0.008186277 | 0.008163452 |
| 5 | polarized | 0.008148198 | 0.007917464 | 0.007917464 | 0.007567405 | 0.007554085 |
| 10 | polarized | 0.018046572 | 0.016020353 | 0.016020353 | 0.015573359 | 0.015559235 |

Exact-hand exploitability in chips; lower is better.

The matched control stops before crossing the second repair pre-gate work time.
The generous control spends the entire second-repair budget on continuation,
then adds the acceptance check. Gate times vary; see actual ratios below.
These are component budgets, excluding reconstruction, scoring and verification.

## Per-case audit and mean outcomes

```json
{
  "passed": true,
  "selection": {
    "attempt": 8,
    "board": [
      25,
      36,
      38,
      40,
      51
    ],
    "texture": "one-pair"
  },
  "cases": [
    {
      "bet": 5,
      "regime": "uniform",
      "values_exact": {
        "original": "668269662878191095621075046410028971/85070591730234615865843651857942052864",
        "first": "8233904974565129605835219798566797511/1361129467683753853853498429727072845824",
        "second": "6590829165212348610833193812741211453/1361129467683753853853498429727072845824",
        "matched": "2001792429316125581413442402828290031/340282366920938463463374607431768211456",
        "generous": "15989954328283497143287740147016796749/2722258935367507707706996859454145691648"
      },
      "values": {
        "original": 0.007855472135392281,
        "first": 0.006049317989255526,
        "second": 0.004842176531838681,
        "matched": 0.005882739230449822,
        "generous": 0.005873781557126136
      },
      "first_group_floor": 0.00575257714740404,
      "second_below_floor": true,
      "second_beats_generous": true,
      "raw_repair_regression": [
        false,
        false
      ],
      "accepted_roles": [
        [
          true,
          true
        ],
        [
          true,
          true
        ]
      ],
      "reference_seconds": 1.0634255000040866,
      "total_ratios": {
        "matched": 0.9964996138330955,
        "generous": 1.1509645953015484
      },
      "total_iterations": {
        "matched": 41800,
        "generous": 48000
      }
    },
    {
      "bet": 10,
      "regime": "uniform",
      "values_exact": {
        "original": "4874929324087226246545294665648248575/340282366920938463463374607431768211456",
        "first": "1481231015038764567146708257248143817/170141183460469231731687303715884105728",
        "second": "5345829572936498372719119902719821213/680564733841876926926749214863536422912",
        "matched": "5571291645121663299967839270685027213/680564733841876926926749214863536422912",
        "generous": "11111514636573398983112269830560550285/1361129467683753853853498429727072845824"
      },
      "values": {
        "original": 0.014326129702806117,
        "first": 0.008705893452204152,
        "second": 0.00785499057930697,
        "matched": 0.008186277319529905,
        "generous": 0.008163451677731996
      },
      "first_group_floor": 0.007886500531474832,
      "second_below_floor": true,
      "second_beats_generous": true,
      "raw_repair_regression": [
        false,
        false
      ],
      "accepted_roles": [
        [
          true,
          true
        ],
        [
          true,
          false
        ]
      ],
      "reference_seconds": 1.109843100013677,
      "total_ratios": {
        "matched": 1.0026299211521896,
        "generous": 1.1775346440946899
      },
      "total_iterations": {
        "matched": 44800,
        "generous": 50700
      }
    },
    {
      "bet": 5,
      "regime": "polarized",
      "values_exact": {
        "original": "11090752146495441980735024061149241051/1361129467683753853853498429727072845824",
        "first": "10776693778669212715699269699653137517/1361129467683753853853498429727072845824",
        "second": "10776693778669212715699269699653137517/1361129467683753853853498429727072845824",
        "matched": "82401741066647780157661022952560090303/10889035741470030830827987437816582766592",
        "generous": "164513408703061330587478006536338038375/21778071482940061661655974875633165533184"
      },
      "values": {
        "original": 0.00814819780910972,
        "first": 0.007917464160854594,
        "second": 0.007917464160854594,
        "matched": 0.007567404775137919,
        "generous": 0.007554085256444013
      },
      "first_group_floor": 0.007463307914382758,
      "second_below_floor": false,
      "second_beats_generous": false,
      "raw_repair_regression": [
        true,
        true
      ],
      "accepted_roles": [
        [
          false,
          true
        ],
        [
          false,
          false
        ]
      ],
      "reference_seconds": 1.0790850999765098,
      "total_ratios": {
        "matched": 1.0004014514442,
        "generous": 1.1545173779182787
      },
      "total_iterations": {
        "matched": 43300,
        "generous": 49500
      }
    },
    {
      "bet": 10,
      "regime": "polarized",
      "values_exact": {
        "original": "98254883975478592471750874612193411981/5444517870735015415413993718908291383296",
        "first": "87223096793999241304513749293805984501/5444517870735015415413993718908291383296",
        "second": "87223096793999241304513749293805984501/5444517870735015415413993718908291383296",
        "matched": "339157721864325653670023006297332200855/21778071482940061661655974875633165533184",
        "generous": "84712535288797694202580308989303753629/5444517870735015415413993718908291383296"
      },
      "values": {
        "original": 0.018046572039667873,
        "first": 0.016020352741026825,
        "second": 0.016020352741026825,
        "matched": 0.015573358831612165,
        "generous": 0.01555923541809615
      },
      "first_group_floor": 0.015308204154382303,
      "second_below_floor": false,
      "second_beats_generous": false,
      "raw_repair_regression": [
        true,
        true
      ],
      "accepted_roles": [
        [
          false,
          true
        ],
        [
          false,
          false
        ]
      ],
      "reference_seconds": 1.0582225999969523,
      "total_ratios": {
        "matched": 1.0009008498977505,
        "generous": 1.1720321411303358
      },
      "total_iterations": {
        "matched": 43300,
        "generous": 49100
      }
    }
  ],
  "means": {
    "5": {
      "values": {
        "original": 0.008001834972251001,
        "first": 0.00698339107505506,
        "second": 0.006379820346346638,
        "matched": 0.0067250720027938705,
        "generous": 0.006713933406785074
      },
      "values_exact": {
        "original": "21783066752546499510672224803709704587/2722258935367507707706996859454145691648",
        "first": "4752649688308585580383622374554983757/680564733841876926926749214863536422912",
        "second": "8683761471940780663266231756197174485/1361129467683753853853498429727072845824",
        "matched": "146459098804763798762891179843065371295/21778071482940061661655974875633165533184",
        "generous": "292433043329329307733779927712472412367/43556142965880123323311949751266331066368"
      },
      "second_improves_first": true,
      "second_beats_matched": true,
      "second_beats_generous": true,
      "second_gain_percent": 8.642946130632726,
      "versus_generous_percent": 4.976413082989237
    },
    "10": {
      "values": {
        "original": 0.016186350871236994,
        "first": 0.01236312309661549,
        "second": 0.011937671660166897,
        "matched": 0.011879818075571036,
        "generous": 0.011861343547914073
      },
      "values_exact": {
        "original": "176253753160874212416475589262565389181/10889035741470030830827987437816582766592",
        "first": "134622489275239707453208413525746586645/10889035741470030830827987437816582766592",
        "second": "129989733377491228286266708515564554205/10889035741470030830827987437816582766592",
        "matched": "517439054508218879268993862959253071671/43556142965880123323311949751266331066368",
        "generous": "129158593835091290135029388311545954769/10889035741470030830827987437816582766592"
      },
      "second_improves_first": true,
      "second_beats_matched": false,
      "second_beats_generous": false,
      "second_gain_percent": 3.441294186944256,
      "versus_generous_percent": -0.643503090054643
    }
  },
  "novelty_historical_plans": 27,
  "novelty_literal_boards_checked": 1617,
  "prior_milestones": 27
}
```

## Verification

17 preflight checks, direct suit-permutation novelty audit against 27 historical plans.
317,300 updates replayed, 16 asymmetric certificates verified,
11,760 independently enumerated proposal exchanges,
16 independent exact security-gate audits; no LP solves in the verifier.
Worker and verification completed in 53.337 seconds, exit 0.
Python 3.14.6; one BLAS thread; no allocation tracing; 900-second limit per phase.
Continuation capped at 200,000 total updates; no hard RSS cap.
K=16, 96 holdings per role, pot 10, stacks 20; all compatible deals included.
Preference model and repair rules unchanged; no fitting, adoption, commit or push.
All 27 earlier milestones verified unchanged.

Plan SHA-256: 349338e22fa92fd02aaeb5820f81c0ed55013dfd105ee12223b16cfa1615e48c

Results manifest SHA-256: 5f77f78830bea001831322f3ca9a100f9368f05ec60ef912640862ba5967fdc3
