# Next board 001

One fresh board through the frozen two-repair procedure. Four cases cover both
existing range regimes and bets. Every case is retained, including non-improvements.
This is one additional board, not a population confidence or six-max strength claim.

Board integer IDs: [8, 14, 38, 40, 43]. Texture: one-pair.
First unused board in the original SHA-256 sequence: attempt 6. Suit-equivalent prior boards excluded.

| Bet | Regime | Original | First repair | Second repair | Matched | Generous |
|---|---|---:|---:|---:|---:|---:|
| 5 | uniform | 0.010598344 | 0.009127769 | 0.006037655 | 0.009051377 | 0.009048254 |
| 10 | uniform | 0.022926517 | 0.014555783 | 0.012391351 | 0.014372321 | 0.014362538 |
| 5 | polarized | 0.013920241 | 0.008412355 | 0.005509007 | 0.008276293 | 0.008268091 |
| 10 | polarized | 0.025236678 | 0.012188619 | 0.010399107 | 0.012033153 | 0.012024165 |

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
    "attempt": 6,
    "board": [
      8,
      14,
      38,
      40,
      43
    ],
    "texture": "one-pair"
  },
  "cases": [
    {
      "bet": 5,
      "regime": "uniform",
      "values_exact": {
        "original": "7212859204364719864463166224617546443/680564733841876926926749214863536422912",
        "first": "24848151507947016275631333841139172813/2722258935367507707706996859454145691648",
        "second": "8218030549622688845852792617319185449/1361129467683753853853498429727072845824",
        "matched": "49280386057857002618021253311380572363/5444517870735015415413993718908291383296",
        "generous": "98526761142984735675499646052079582011/10889035741470030830827987437816582766592"
      },
      "values": {
        "original": 0.010598344060009084,
        "first": 0.009127769289365007,
        "second": 0.006037655303729031,
        "matched": 0.009051377408961302,
        "generous": 0.009048253994405892
      },
      "first_group_floor": 0.009016832095381252,
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
      "reference_seconds": 1.054805200023111,
      "total_ratios": {
        "matched": 0.9963164761853815,
        "generous": 1.1548411970395656
      },
      "total_iterations": {
        "matched": 43600,
        "generous": 49700
      }
    },
    {
      "bet": 10,
      "regime": "uniform",
      "values_exact": {
        "original": "31205957820120118063899316406143817669/1361129467683753853853498429727072845824",
        "first": "39624610204534796335628074852982902315/2722258935367507707706996859454145691648",
        "second": "16866233630488375990580322351050064289/1361129467683753853853498429727072845824",
        "matched": "156500721986558708210813523267134459583/10889035741470030830827987437816582766592",
        "generous": "156394193680877870688529833313128901243/10889035741470030830827987437816582766592"
      },
      "values": {
        "original": 0.022926516955968614,
        "first": 0.014555782952801818,
        "second": 0.01239135147017998,
        "matched": 0.014372321452719463,
        "generous": 0.014362538372912393
      },
      "first_group_floor": 0.01425855513307916,
      "second_below_floor": true,
      "second_beats_generous": true,
      "raw_repair_regression": [
        false,
        true
      ],
      "accepted_roles": [
        [
          true,
          true
        ],
        [
          false,
          true
        ]
      ],
      "reference_seconds": 1.068170500017004,
      "total_ratios": {
        "matched": 0.9876208898231845,
        "generous": 1.154538905090989
      },
      "total_iterations": {
        "matched": 42800,
        "generous": 49500
      }
    },
    {
      "bet": 5,
      "regime": "polarized",
      "values_exact": {
        "original": "4736812552089228523494825769772197863/340282366920938463463374607431768211456",
        "first": "22900609629771390547191058747372887687/2722258935367507707706996859454145691648",
        "second": "29993888304612987043765841173069170327/5444517870735015415413993718908291383296",
        "matched": "45060422513076156960916708599986043279/5444517870735015415413993718908291383296",
        "generous": "180063082820165833867236362277173593203/21778071482940061661655974875633165533184"
      },
      "values": {
        "original": 0.013920240989712477,
        "first": 0.008412355390682108,
        "second": 0.005509007228323007,
        "matched": 0.008276292517154131,
        "generous": 0.008268091275263697
      },
      "first_group_floor": 0.008179995435056804,
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
      "reference_seconds": 1.0660236999974586,
      "total_ratios": {
        "matched": 0.9763907687501571,
        "generous": 1.1555169926077575
      },
      "total_iterations": {
        "matched": 42200,
        "generous": 49300
      }
    },
    {
      "bet": 10,
      "regime": "polarized",
      "values_exact": {
        "original": "34350385739031032407803229604679691209/1361129467683753853853498429727072845824",
        "first": "132722307528350638254728237555834221499/10889035741470030830827987437816582766592",
        "second": "113236245501052929869916991335693600059/10889035741470030830827987437816582766592",
        "matched": "524117735969953616256502858200031981273/43556142965880123323311949751266331066368",
        "generous": "261863133126598947788414996336696004971/21778071482940061661655974875633165533184"
      },
      "values": {
        "original": 0.025236677740498405,
        "first": 0.012188618963099572,
        "second": 0.010399106788657296,
        "matched": 0.012033153082000932,
        "generous": 0.01202416537808366
      },
      "first_group_floor": 0.011949945990617668,
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
          false,
          true
        ]
      ],
      "reference_seconds": 1.0367540000006557,
      "total_ratios": {
        "matched": 0.9935898964025738,
        "generous": 1.1610976176769727
      },
      "total_iterations": {
        "matched": 42100,
        "generous": 48700
      }
    }
  ],
  "means": {
    "5": {
      "values": {
        "original": 0.012259292524860781,
        "first": 0.008770062340023558,
        "second": 0.0057733312660260185,
        "matched": 0.008663834963057717,
        "generous": 0.008658172634834795
      },
      "values_exact": {
        "original": "16686484308543176911452817764161942169/1361129467683753853853498429727072845824",
        "first": "11937190284429601705705598147128015125/1361129467683753853853498429727072845824",
        "second": "62866010503103742427177011642345912123/10889035741470030830827987437816582766592",
        "matched": "47170404285466579789468980955683307821/5444517870735015415413993718908291383296",
        "generous": "377116605106135305218235654381332757225/43556142965880123323311949751266331066368"
      },
      "second_improves_first": true,
      "second_beats_matched": true,
      "second_beats_generous": true,
      "second_gain_percent": 34.170008807366,
      "versus_generous_percent": 33.31928676499324
    },
    "10": {
      "values": {
        "original": 0.02408159734823351,
        "first": 0.013372200957950695,
        "second": 0.011395229129418637,
        "matched": 0.013202737267360197,
        "generous": 0.013193351875498026
      },
      "values_exact": {
        "original": "32778171779575575235851273005411754439/1361129467683753853853498429727072845824",
        "first": "291220748346489823597240536967765830759/21778071482940061661655974875633165533184",
        "second": "248166114544959937794559570144094114371/21778071482940061661655974875633165533184",
        "matched": "1150120623916188449099756951268569819605/87112285931760246646623899502532662132736",
        "generous": "574651520488354689165474662962953807457/43556142965880123323311949751266331066368"
      },
      "second_improves_first": true,
      "second_beats_matched": true,
      "second_beats_generous": true,
      "second_gain_percent": 14.784191732899526,
      "versus_generous_percent": 13.629006207427578
    }
  },
  "novelty_historical_plans": 26,
  "novelty_literal_boards_checked": 1528,
  "prior_milestones": 26
}
```

## Verification

17 preflight checks, direct suit-permutation novelty audit against 26 historical plans.
317,200 updates replayed, 16 asymmetric certificates verified,
12,075 independently enumerated proposal exchanges,
16 independent exact security-gate audits; no LP solves in the verifier.
Worker and verification completed in 52.013 seconds, exit 0.
Python 3.14.6; one BLAS thread; no allocation tracing; 900-second limit per phase.
Continuation capped at 200,000 total updates; no hard RSS cap.
K=16, 96 holdings per role, pot 10, stacks 20; all compatible deals included.
Preference model and repair rules unchanged; no fitting, adoption, commit or push.
All 26 earlier milestones verified unchanged.

Plan SHA-256: 18fabda7c0ba0acbdec0214b5c8e88288e8019838176ff2cebc542f01e0a18ce

Results manifest SHA-256: 04e03d8d7f5b07eae139fb794d836e167ac8fb942fd88cc8e48780bd813dce2f
