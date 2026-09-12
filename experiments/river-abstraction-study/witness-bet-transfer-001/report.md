# Frozen bet-size transfer: witness-bet-transfer-001

## Result and decision rules

Actual-policy transfer: PASS.
Representation transfer: PASS.
Texture/range/leave-one-board-out robustness: NOT PASSED.
These are the rules frozen before scoring, not confidence levels or adoption decisions.
The two new bet sizes are judged separately; a win at one cannot offset a loss at
the other. Half-pot data are a verified retained anchor, not a new replication.

Actual-policy transfer requires mean learned-minus-range-response exploitability
below -1e-10 chips at 10000 iterations at both quarter-pot and pot-sized bets.
Representation transfer separately requires a negative upper numerical endpoint
of that difference in certified grouping floors at both new sizes. Robustness
requires both comparisons to hold in every texture, range regime and omitted-board
panel at each new size. Full per-board and case losses remain below.

Failures of the robustness rule are shown explicitly here. Positive delta means
the learned method is worse than range-response in that measure. A negative
floor delta with positive actual delta distinguishes representation potential
from the policy the compressed-game solver actually produced.

| New bet | Panel | Actual delta | Floor delta |
|---|---|---:|---:|
| 10.0 | multiple-pairs-or-trips | -0.0000230675 | 0.0003357628 |
| 10.0 | polarized | 0.0002328715 | -0.0000486371 |

## Actual full-hand exploitability at 10000 iterations

Lower is better. Units are conditional river-game chips; pot is always 10.
These are unrestricted best-response evaluations of computed CFR policies.
They are not sampled match win rates, BB/100 or six-max strength measurements.

| Bet size | Learned groups | Range-response | Range-equity | Reduction vs response |
|---|---:|---:|---:|---:|
| Quarter pot (2.5) | 0.0040547268 | 0.0048924933 | 0.0052437657 | 17.12% |
| Half pot (5), retained anchor | 0.0050653533 | 0.0060881290 | 0.0071378222 | 16.80% |
| Pot sized (10) | 0.0078760367 | 0.0085539289 | 0.0103556700 | 7.92% |

## Certified grouping floors

These are the least full-hand profile exploitabilities representable by each
pair of groupings, shown as rational-certificate interval midpoints. An equilibrium
in the compressed game need not attain this floor.

| Bet size | Learned groups | Range-response | Range-equity | Reduction vs response |
|---|---:|---:|---:|---:|
| Quarter pot (2.5) | 0.0026617772 | 0.0033894616 | 0.0034617204 | 21.47% |
| Half pot (5), retained anchor | 0.0033411789 | 0.0043571618 | 0.0050084461 | 23.32% |
| Pot sized (10) | 0.0053037321 | 0.0059196300 | 0.0069737653 | 10.40% |

Counts mean lower / higher / numerically overlapping cases.

| Bet | Reference | Actual delta | Actual counts | Floor delta | Floor counts |
|---|---|---:|---:|---:|---:|
| 2.5 | range_equity | -0.0011890389 | 76/20/0 | -0.0007999432 | 79/17/0 |
| 2.5 | range_response | -0.0008377665 | 66/30/0 | -0.0007276844 | 74/22/0 |
| 5.0 | range_equity | -0.0020724690 | 77/19/0 | -0.0016672672 | 86/9/1 |
| 5.0 | range_response | -0.0010227757 | 69/27/0 | -0.0010159829 | 70/23/3 |
| 10.0 | range_equity | -0.0024796333 | 73/23/0 | -0.0016700332 | 79/16/1 |
| 10.0 | range_response | -0.0006778923 | 60/36/0 | -0.0006158979 | 61/30/5 |

## Earlier solver checkpoints

| Bet | Iterations | Learned | Range-response | Range-equity |
|---|---:|---:|---:|---:|
| 2.5 | 100 | 0.0165039353 | 0.0171544797 | 0.0173807835 |
| 2.5 | 1000 | 0.0047987042 | 0.0056873931 | 0.0059687405 |
| 5.0 | 100 | 0.0197261546 | 0.0205003960 | 0.0212109492 |
| 5.0 | 1000 | 0.0061556346 | 0.0070756136 | 0.0081003165 |
| 10.0 | 100 | 0.0303736573 | 0.0305206601 | 0.0318957070 |
| 10.0 | 1000 | 0.0093745044 | 0.0099233786 | 0.0115018405 |

## Reusing half-pot actions versus re-solving

The representation is frozen, but CFR chooses actions anew for each bet size.
The separate control applies the unchanged half-pot 10000-iteration policy under
the new payoffs. Negative resolved-minus-fixed means re-solving reduces its
exploitability. This diagnostic was predeclared and does not replace the primary
comparison against other representations.

| Bet | Method | Re-solved | Fixed half-pot policy | Delta | Bettor change | Caller change |
|---|---|---:|---:|---:|---:|---:|
| 2.5 | ordinary_preference | 0.0040547268 | 0.1876512300 | -0.1835965032 | 0.1017080 | 0.1432271 |
| 2.5 | range_response | 0.0048924933 | 0.1860027493 | -0.1811102561 | 0.1026109 | 0.1445522 |
| 2.5 | range_equity | 0.0052437657 | 0.1891059973 | -0.1838622316 | 0.1017237 | 0.1421173 |
| 5.0 | ordinary_preference | 0.0050653533 | 0.0050653533 | 0.0000000000 | 0.0000000 | 0.0000000 |
| 5.0 | range_response | 0.0060881290 | 0.0060881290 | 0.0000000000 | 0.0000000 | 0.0000000 |
| 5.0 | range_equity | 0.0071378222 | 0.0071378222 | 0.0000000000 | 0.0000000 | 0.0000000 |
| 10.0 | ordinary_preference | 0.0078760367 | 0.2483619268 | -0.2404858902 | 0.1069403 | 0.1496866 |
| 10.0 | range_response | 0.0085539289 | 0.2505871897 | -0.2420332607 | 0.1033050 | 0.1512831 |
| 10.0 | range_equity | 0.0103556700 | 0.2518670226 | -0.2415113526 | 0.1044006 | 0.1515420 |

Action change is absolute probability change averaged by that seat's
collision-conditioned hand marginal. The half-pot anchor has exactly zero change.
No action-change threshold was used to select cases or make the transfer ruling.

## Solver residual at 10000 iterations

| Bet | Method | Above grouping floor | Compressed-game exploitability |
|---|---|---:|---:|
| 2.5 | ordinary_preference | 0.0013929496 | 0.0001476784 |
| 2.5 | range_response | 0.0015030317 | 0.0001507671 |
| 2.5 | range_equity | 0.0017820453 | 0.0001509180 |
| 5.0 | ordinary_preference | 0.0017241744 | 0.0001726568 |
| 5.0 | range_response | 0.0017309672 | 0.0001762680 |
| 5.0 | range_equity | 0.0021293762 | 0.0001735542 |
| 10.0 | ordinary_preference | 0.0025723045 | 0.0002740741 |
| 10.0 | range_response | 0.0026342989 | 0.0002795545 |
| 10.0 | range_equity | 0.0033819047 | 0.0002770891 |

The residual includes finite optimization and potentially the mismatch between
a compressed equilibrium and the least exploitable representable profile. It is
not all necessarily removable by more iterations of the same algorithm.

## Board sensitivity

| Board | Quarter-pot actual delta | Half-pot actual delta | Pot-sized actual delta |
|---|---:|---:|---:|
| 0 | -0.0006334873 | -0.0006485528 | -0.0003174544 |
| 1 | -0.0002941783 | -0.0012019987 | -0.0008491000 |
| 2 | -0.0016411755 | -0.0011490047 | -0.0017840015 |
| 3 | -0.0000185866 | -0.0007981820 | -0.0019966216 |
| 4 | -0.0011522791 | -0.0009242413 | -0.0016822297 |
| 5 | -0.0011190663 | -0.0019739855 | -0.0015938271 |
| 6 | -0.0002373499 | -0.0011585266 | -0.0015290985 |
| 7 | -0.0003407067 | -0.0007227771 | -0.0000811812 |
| 8 | -0.0004546187 | -0.0026134666 | 0.0001052591 |
| 9 | -0.0004497634 | 0.0000034570 | -0.0007711755 |
| 10 | -0.0003858464 | -0.0015940123 | -0.0022203111 |
| 11 | 0.0000367251 | 0.0010017179 | 0.0019657353 |
| 12 | -0.0021460842 | -0.0021188262 | -0.0001139859 |
| 13 | 0.0001304259 | -0.0018932518 | -0.0026515928 |
| 14 | -0.0031927150 | -0.0006594149 | 0.0033688811 |
| 15 | -0.0015055573 | 0.0000866542 | -0.0006955723 |

### textures

| Bet | Panel | Actual delta vs response | Floor delta vs response |
|---|---|---:|---:|
| 2.5 | multiple-pairs-or-trips | -0.0016784827 | -0.0016528992 |
| 2.5 | one-pair | -0.0003133759 | -0.0003452346 |
| 2.5 | unpaired-flush-possible | -0.0007123505 | -0.0003714168 |
| 2.5 | unpaired-no-flush | -0.0006468569 | -0.0005411870 |
| 5.0 | multiple-pairs-or-trips | -0.0011462097 | -0.0016112222 |
| 5.0 | one-pair | -0.0008005760 | -0.0008669444 |
| 5.0 | unpaired-flush-possible | -0.0011948826 | -0.0007582220 |
| 5.0 | unpaired-no-flush | -0.0009494346 | -0.0008275429 |
| 10.0 | multiple-pairs-or-trips | -0.0000230675 | 0.0003357628 |
| 10.0 | one-pair | -0.0002301230 | -0.0012072338 |
| 10.0 | unpaired-flush-possible | -0.0012215841 | -0.0007309768 |
| 10.0 | unpaired-no-flush | -0.0012367944 | -0.0008611437 |

### regimes

| Bet | Panel | Actual delta vs response | Floor delta vs response |
|---|---|---:|---:|
| 2.5 | polarized | -0.0006183487 | -0.0004457610 |
| 2.5 | uniform | -0.0010571843 | -0.0010096078 |
| 5.0 | polarized | -0.0004630592 | -0.0005161554 |
| 5.0 | uniform | -0.0015824922 | -0.0015158103 |
| 10.0 | polarized | 0.0002328715 | -0.0000486371 |
| 10.0 | uniform | -0.0015886560 | -0.0011831587 |

### leave_one_board_out

| Bet | Panel | Actual delta vs response | Floor delta vs response |
|---|---|---:|---:|
| 2.5 | 0 | -0.0008513851 | -0.0007614539 |
| 2.5 | 1 | -0.0008740057 | -0.0007567052 |
| 2.5 | 10 | -0.0008678945 | -0.0007274373 |
| 2.5 | 11 | -0.0008960659 | -0.0007811573 |
| 2.5 | 12 | -0.0007505453 | -0.0005521320 |
| 2.5 | 13 | -0.0009023126 | -0.0008066981 |
| 2.5 | 14 | -0.0006807699 | -0.0006373372 |
| 2.5 | 15 | -0.0007932471 | -0.0006678464 |
| 2.5 | 2 | -0.0007842059 | -0.0007020065 |
| 2.5 | 3 | -0.0008923785 | -0.0007403047 |
| 2.5 | 4 | -0.0008167990 | -0.0007513674 |
| 2.5 | 5 | -0.0008190132 | -0.0007324441 |
| 2.5 | 6 | -0.0008777943 | -0.0007582038 |
| 2.5 | 7 | -0.0008709038 | -0.0007637270 |
| 2.5 | 8 | -0.0008633097 | -0.0007603772 |
| 2.5 | 9 | -0.0008636334 | -0.0007437524 |
| 5.0 | 0 | -0.0010477239 | -0.0010582982 |
| 5.0 | 1 | -0.0010108275 | -0.0010277039 |
| 5.0 | 10 | -0.0009846933 | -0.0009637531 |
| 5.0 | 11 | -0.0011577419 | -0.0011018149 |
| 5.0 | 12 | -0.0009497057 | -0.0009035982 |
| 5.0 | 13 | -0.0009647440 | -0.0010056961 |
| 5.0 | 14 | -0.0010469998 | -0.0009631571 |
| 5.0 | 15 | -0.0010967377 | -0.0010327497 |
| 5.0 | 2 | -0.0010143604 | -0.0009958881 |
| 5.0 | 3 | -0.0010377486 | -0.0010322920 |
| 5.0 | 4 | -0.0010293447 | -0.0010232512 |
| 5.0 | 5 | -0.0009593617 | -0.0010186565 |
| 5.0 | 6 | -0.0010137256 | -0.0010366274 |
| 5.0 | 7 | -0.0010427756 | -0.0010541327 |
| 5.0 | 8 | -0.0009167296 | -0.0009866359 |
| 5.0 | 9 | -0.0010911912 | -0.0010514711 |
| 10.0 | 0 | -0.0007019215 | -0.0006538615 |
| 10.0 | 1 | -0.0006664784 | -0.0005778633 |
| 10.0 | 10 | -0.0005750643 | -0.0004653002 |
| 10.0 | 11 | -0.0008541341 | -0.0006555451 |
| 10.0 | 12 | -0.0007154860 | -0.0007252055 |
| 10.0 | 13 | -0.0005463122 | -0.0005224727 |
| 10.0 | 14 | -0.0009476772 | -0.0007163376 |
| 10.0 | 15 | -0.0006767136 | -0.0007533518 |
| 10.0 | 2 | -0.0006041516 | -0.0005837745 |
| 10.0 | 3 | -0.0005899770 | -0.0005826933 |
| 10.0 | 4 | -0.0006109364 | -0.0005998178 |
| 10.0 | 5 | -0.0006168299 | -0.0005897440 |
| 10.0 | 6 | -0.0006211452 | -0.0005812181 |
| 10.0 | 7 | -0.0007176730 | -0.0006621239 |
| 10.0 | 8 | -0.0007301024 | -0.0006016607 |
| 10.0 | 9 | -0.0006716734 | -0.0005833959 |

## Change in relative advantage versus half pot

These are difference-of-differences: (learned minus reference at new bet) minus
(learned minus reference at half pot). A positive value means less absolute
advantage or more disadvantage in chips. Games differ, so this is descriptive;
it is not a causal claim about real betting frequencies or a win-rate estimate.

| Bet | Reference | Actual interaction | Floor interaction |
|---|---|---:|---:|
| 10.0 | range_equity | -0.0004071644 | -0.0000027660 |
| 10.0 | range_response | 0.0003448834 | 0.0004000850 |
| 2.5 | range_equity | 0.0008834300 | 0.0008673240 |
| 2.5 | range_response | 0.0001850092 | 0.0002882985 |

## Largest actual-policy losses

| Bet | Case | Learned | Range-response | Delta |
|---|---|---:|---:|---:|
| 10.0 | b15-p2-uniform | 0.0371219772 | 0.0192029878 | 0.0179189894 |
| 10.0 | b14-p0-polarized | 0.0269062810 | 0.0116211564 | 0.0152851246 |
| 10.0 | b14-p0-uniform | 0.0202931084 | 0.0115117773 | 0.0087813311 |
| 10.0 | b14-p2-polarized | 0.0203304908 | 0.0124037473 | 0.0079267435 |
| 10.0 | b08-p2-uniform | 0.0156877944 | 0.0083947690 | 0.0072930254 |
| 2.5 | b13-p0-uniform | 0.0076933857 | 0.0005584374 | 0.0071349483 |
| 2.5 | b01-p1-uniform | 0.0060239900 | 0.0033185687 | 0.0027054213 |
| 2.5 | b01-p1-polarized | 0.0067479847 | 0.0042929959 | 0.0024549889 |
| 2.5 | b03-p1-uniform | 0.0047091525 | 0.0026784476 | 0.0020307049 |
| 2.5 | b11-p2-uniform | 0.0091219402 | 0.0071557175 | 0.0019662228 |
| 5.0 | b15-p2-uniform | 0.0229007073 | 0.0146295518 | 0.0082711555 |
| 5.0 | b14-p0-polarized | 0.0177790927 | 0.0107282541 | 0.0070508387 |
| 5.0 | b11-p0-uniform | 0.0151990989 | 0.0092170998 | 0.0059819992 |
| 5.0 | b14-p0-uniform | 0.0102573076 | 0.0065474813 | 0.0037098263 |
| 5.0 | b12-p0-polarized | 0.0121575466 | 0.0085248991 | 0.0036326474 |

## Frozen design and verification

All 96 observed-panel cases are reused at each of three bet sizes: 288 cells.
Six cases per board are equally weighted; sixteen boards receive equal weight.
There is no mean pooled across bet sizes for primary claims. These are synthetic
ranges, not reached betting posteriors. All games are heads-up, one bet, 96 holdings
per seat, pot 10, stacks 20/20, with no raises or additional streets.

Quarter-pot and pot-sized games were built through RiverHoldem using identical
input ranges. Joint/check/fold arrays stayed identical; call payoffs equal the
showdown sign times joint probability times (5 + bet). All eleven raw features,
four classifier outputs and group labels stayed identical at every bet size.
The model never received bet size and no coefficient or feature was changed.
Group capacities match the predecessor for every method and case.

There were exactly 1152 new LP calls and 576 new CFR trajectories. The existing
LP iteration/time limits and rational saddle certificates applied unchanged.
CFR uses deterministic alternating updates, zero initial regrets and unweighted
average policies. All three checkpoints were retained. No model fitting, seed
search, adaptive sample extension or scored-panel rehearsal. No new timed-budget
comparison is claimed; source solve times are diagnostic only.

Preflight public-tree checks passed at all sizes, with direct payoff identities,
feature invariance, tied showdowns and invalid bet refusals. Thirteen existing
CFR/certificate tests passed. Console provenance is recorded in preflight.json.
Worker: 439.649230 seconds; verifier: 465.494700 seconds.
Combined invocation: 905.352404 seconds, exit 0.
Each subprocess had a 1200-second limit. No RSS ceiling or peak-memory claim.
Python 3.14.6 / NumPy 2.5.2 / SciPy 1.18.0, one BLAS thread, no tracemalloc.

The parent reconstructed all inputs and groups, checked all 1728 asymmetric
certificates with LP disabled and replayed every resolved policy, including the
retained half-pot anchor: 8,640,000 deterministic iterations. Scalar arithmetic
independently checked full-hand values and best responses for 2592 resolved
policies and 864 fixed-policy controls. The rational summary audit re-derived all
reported panels, intervals, comparisons, interactions and predeclared flags.
Feature values confirmed unchanged: 829,440.
Maximum scalar/vector discrepancy: 1.998401e-15 chips.
Independent summary scalar checks: 6,266.
Pinned files verified before and after: 817.
No independent cold reviewer or population confidence interval is claimed.
All fourteen earlier milestones are preserved. No production change, commit,
push or adoption was performed.

Plan SHA-256:
46bf03c49d70eb121cffe13e77810cfb0edd42866c6833ffd96fe08aa6037320

Frozen candidate SHA-256:
ee50b041d7a096fc223082df5b02845a551171bfca062ae8cae22a1e791ad8ce

Original result manifest SHA-256:
7c6471ab93cdc8a1912a2f26cb2b4022c161b0416534a9b9173c36a9ae99dcfd
