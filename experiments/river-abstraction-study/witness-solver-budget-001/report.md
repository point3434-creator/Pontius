# Frozen groups under solver budgets: witness-solver-budget-001

## Result

Predeclared numerical improvement flag: PASS.
Predeclared robustness flag: PASS.
These are deterministic benchmark criteria with a 1e-10-chip comparison tolerance,
not statistical confidence levels, adoption decisions or full-game strength claims.

The primary endpoints are 10000 iterations and 0.5 seconds. The timed endpoint
averages the three repetitions within each case. Cases are equally weighted
within each board, and the sixteen boards receive equal weight.

## Actual full-hand exploitability

Lower is better. Units are conditional one-bet game chips, not BB/100.
Policies are lifted to all 96 holdings per seat; best responses are unrestricted.
This measures computed policies, rather than only the best representable floor.

| Budget | Learned preference | Range-response | Range-equity | Reduction vs response |
|---|---:|---:|---:|---:|
| iterations:100 | 0.0197261546 | 0.0205003960 | 0.0212109492 | 3.78% |
| iterations:1000 | 0.0061556346 | 0.0070756136 | 0.0081003165 | 13.00% |
| iterations:10000 | 0.0050653533 | 0.0060881290 | 0.0071378222 | 16.80% |
| seconds:0.05 | 0.0165919207 | 0.0188967780 | 0.0081559734 | 12.20% |
| seconds:0.2 | 0.0051264237 | 0.0061543013 | 0.0071842715 | 16.70% |
| seconds:0.5 | 0.0050200077 | 0.0060535353 | 0.0071001142 | 17.07% |

Counts below mean lower / higher / numerically overlapping cases.

| Budget | Delta vs response | Counts | Delta vs equity | Counts |
|---|---:|---:|---:|---:|
| iterations:100 | -0.0007742414 | 68/28/0 | -0.0014847946 | 77/19/0 |
| iterations:1000 | -0.0009199790 | 70/26/0 | -0.0019446820 | 78/18/0 |
| iterations:10000 | -0.0010227757 | 69/27/0 | -0.0020724690 | 77/19/0 |
| seconds:0.05 | -0.0023048573 | 75/21/0 | 0.0084359472 | 60/36/0 |
| seconds:0.2 | -0.0010278776 | 68/28/0 | -0.0020578478 | 79/17/0 |
| seconds:0.5 | -0.0010335276 | 67/29/0 | -0.0020801065 | 79/17/0 |

## Representation floor and computed-policy residual

The floor is the retained certificate for the best representable full-hand profile.
Residual equals actual exploitability minus this floor. It can include both finite
optimization error and the difference between solving the compressed equilibrium
and minimizing unrestricted exploitability within the representation. It is not
necessarily removable merely by running this CFR solver longer.

| Budget | Method | Full-hand exploitability | Above floor | Compressed exploitability |
|---|---|---:|---:|---:|
| iterations:10000 | ordinary_preference | 0.0050653533 | 0.0017241744 | 0.0001726568 |
| iterations:10000 | range_response | 0.0060881290 | 0.0017309672 | 0.0001762680 |
| iterations:10000 | range_equity | 0.0071378222 | 0.0021293762 | 0.0001735542 |
| seconds:0.5 | ordinary_preference | 0.0050200077 | 0.0016788288 | 0.0000994569 |
| seconds:0.5 | range_response | 0.0060535353 | 0.0016963736 | 0.0001023127 |
| seconds:0.5 | range_equity | 0.0071001142 | 0.0020916681 | 0.0000992827 |

## Board and range sensitivity

| Board | Delta at 10000 iterations | Delta at 0.5 seconds |
|---|---:|---:|
| 0 | -0.0006485528 | -0.0005860825 |
| 1 | -0.0012019987 | -0.0011917359 |
| 2 | -0.0011490047 | -0.0012455785 |
| 3 | -0.0007981820 | -0.0008284362 |
| 4 | -0.0009242413 | -0.0009392834 |
| 5 | -0.0019739855 | -0.0020425271 |
| 6 | -0.0011585266 | -0.0012001684 |
| 7 | -0.0007227771 | -0.0007226950 |
| 8 | -0.0026134666 | -0.0025801034 |
| 9 | 0.0000034570 | 0.0000162621 |
| 10 | -0.0015940123 | -0.0016294932 |
| 11 | 0.0010017179 | 0.0011370078 |
| 12 | -0.0021188262 | -0.0021365228 |
| 13 | -0.0018932518 | -0.0019490958 |
| 14 | -0.0006594149 | -0.0006786630 |
| 15 | 0.0000866542 | 0.0000406728 |

| Panel | Delta at 10000 iterations | Delta at 0.5 seconds |
|---|---:|---:|
| multiple-pairs-or-trips | -0.0011462097 | -0.0011809022 |
| one-pair | -0.0008005760 | -0.0007640817 |
| unpaired-flush-possible | -0.0011948826 | -0.0012261685 |
| unpaired-no-flush | -0.0009494346 | -0.0009629583 |
| polarized | -0.0004630592 | -0.0004693237 |
| uniform | -0.0015824922 | -0.0015977316 |

| Omitted board | Delta at 10000 iterations | Delta at 0.5 seconds |
|---|---:|---:|
| 0 | -0.0010477239 | -0.0010633573 |
| 1 | -0.0010108275 | -0.0010229804 |
| 2 | -0.0010143604 | -0.0010193909 |
| 3 | -0.0010377486 | -0.0010472004 |
| 4 | -0.0010293447 | -0.0010398106 |
| 5 | -0.0009593617 | -0.0009662610 |
| 6 | -0.0010137256 | -0.0010224183 |
| 7 | -0.0010427756 | -0.0010542498 |
| 8 | -0.0009167296 | -0.0009304226 |
| 9 | -0.0010911912 | -0.0011035136 |
| 10 | -0.0009846933 | -0.0009937966 |
| 11 | -0.0011577419 | -0.0011782300 |
| 12 | -0.0009497057 | -0.0009599946 |
| 13 | -0.0009647440 | -0.0009724898 |
| 14 | -0.0010469998 | -0.0010571853 |
| 15 | -0.0010967377 | -0.0011051410 |

## Timing repetitions and completed work

| Repetition at 0.5 s | Learned | Response | Equity | Delta vs response |
|---|---:|---:|---:|---:|
| 0 | 0.0050203949 | 0.0060510240 | 0.0071004460 | -0.0010306291 |
| 1 | 0.0050202228 | 0.0060566601 | 0.0070994834 | -0.0010364372 |
| 2 | 0.0050194054 | 0.0060529220 | 0.0071004130 | -0.0010335166 |

| Budget | Mean learned iterations | Mean response iterations | Mean equity iterations |
|---|---:|---:|---:|
| iterations:100 | 100.00 | 100.00 | 100.00 |
| iterations:1000 | 1000.00 | 1000.00 | 1000.00 |
| iterations:10000 | 10000.00 | 10000.00 | 10000.00 |
| seconds:0.05 | 872.26 | 805.10 | 1098.27 |
| seconds:0.2 | 6454.38 | 6375.52 | 6680.98 |
| seconds:0.5 | 17644.22 | 17573.58 | 17835.42 |

Three timed repetitions rotate method order within every case. Time is measured
on this machine, with one BLAS thread and no allocation tracing. Reported budgets
start with loaded games, full-board equity tables and loaded model coefficients.
They include each method's features, prediction, grouping, aggregation and CFR setup
and updates. Clock/checkpoint bookkeeping is excluded; pre-step policy copies are
included. Imports, disk I/O, certification and scoring are outside the boundary.
Thus these are warm-input active-wall budgets, not cold end-to-end latency.

The saved timed policy is from the last completed iteration before its deadline.
The crossing iteration is not credited. Every cell records both timestamps.
Setup missed 4 checkpoint budgets; those cells retain the uniform policy.
Common input construction and validation: 16.358735 s total.
That shared stage includes exact equity-cache fills, game creation and predecessor
control construction. It is not charged selectively to any method.

| Method | Total setup over 384 trajectories | Mean setup |
|---|---:|---:|
| ordinary_preference | 10.441424 s | 27.1912 ms |
| range_equity | 8.067975 s | 21.0104 ms |
| range_response | 11.143939 s | 29.0207 ms |

| Setup-miss case | Method | Repetition | Budget | Setup ms |
|---|---|---:|---:|---:|
| b04-p0-polarized | ordinary_preference | 1 | 0.05 s | 53.1774 |
| b05-p2-uniform | range_response | 1 | 0.05 s | 53.6384 |
| b05-p2-polarized | ordinary_preference | 1 | 0.05 s | 54.2742 |
| b07-p2-uniform | range_response | 2 | 0.05 s | 53.9558 |

## Largest losses retained

| Endpoint | Case | Learned | Response | Delta |
|---|---:|---:|---:|
| iterations:10000 | b15-p2-uniform | 0.0229007073 | 0.0146295518 | 0.0082711555 |
| iterations:10000 | b14-p0-polarized | 0.0177790927 | 0.0107282541 | 0.0070508387 |
| iterations:10000 | b11-p0-uniform | 0.0151990989 | 0.0092170998 | 0.0059819992 |
| iterations:10000 | b14-p0-uniform | 0.0102573076 | 0.0065474813 | 0.0037098263 |
| iterations:10000 | b12-p0-polarized | 0.0121575466 | 0.0085248991 | 0.0036326474 |
| seconds:0.5 | b15-p2-uniform | 0.0228858757 | 0.0147117229 | 0.0081741527 |
| seconds:0.5 | b14-p0-polarized | 0.0176808814 | 0.0107091158 | 0.0069717655 |
| seconds:0.5 | b11-p0-uniform | 0.0158319702 | 0.0092257773 | 0.0066061929 |
| seconds:0.5 | b12-p0-polarized | 0.0123168787 | 0.0085345146 | 0.0037823641 |
| seconds:0.5 | b14-p0-uniform | 0.0102063651 | 0.0065176069 | 0.0036887581 |

## Design, execution and verification

All 96 cases from witness-preference-confirmation-001 are retained: sixteen observed
boards, three fixed pools and two synthetic range regimes. No new boards, fitting,
hyperparameter search, alternative seed, adaptive budget or favorable subset.
The model, features and groups reproduce the predecessor exactly. Each method has
the same occupied group capacity per case. Pot 10, bet 5, stacks 20/20, one bet,
two players, 96 hands per seat. These ranges are not reached betting posteriors.
The existing alternating vanilla CFR starts with zero regrets and uniform policy.
Strategies use its unweighted average; updates are deterministic full enumeration.

Preflight: seven existing tests passed, including compact/full-tree and grouped
CFR parity, payoff/BR equivalence and aggregation. Synthetic checks covered budget
crossings, crossing several budgets, exact-boundary equality and setup failure.
No scored benchmark rehearsal was used. The preflight tool receipts are described
in the pinned preflight.json; the original console outputs remain in tool history.

Worker: 534.607193 s, exit 0, maximum 1200 s.
Verifier: 232.840546 s, exit 0, maximum 900 s.
Combined invocation: 767.635753 s, exit 0.
No RSS ceiling or peak-memory measurement. CPython 3.14.6 / NumPy 2.5.2 / SciPy 1.18.0.
All 1152 solver trajectories and 3456 checkpoint policies retained. No new LP solve
or model fit. The verifier rebuilt every input and grouping, checked 576 retained
asymmetric certificates with solving disabled, and replayed every saved policy
exactly from the deterministic CFR trajectory. Scalar fsum arithmetic independently
checked all full-hand payoff and best-response metrics. Restricted-game inequalities
and actual-versus-floor bounds passed for every policy.

Replay iterations: 5,157,759.
Maximum scalar/vector metric discrepancy: 1.776357e-15 chips.
Independent rational summary scalar checks: 1,511.
All 691 pinned files were reverified after execution.
No opposing cold review is claimed. Numerical checks bound implementation agreement
at the declared tolerance; they are not uncertainty intervals over possible boards.
The thirteen older milestones, original source and unrelated edits remain preserved.
No production modification, commit, push or adoption was performed.

Plan SHA-256:
f942bb32b63d130520d9d58978e0c2c2f2e0def7016035f444dbebda6c7732ea

Frozen candidate SHA-256:
ee50b041d7a096fc223082df5b02845a551171bfca062ae8cae22a1e791ad8ce

Original result manifest SHA-256:
4dae19820f6db850573c2acb7c8b728d0611970e9ba6bcc9e6e974e59eed6828
