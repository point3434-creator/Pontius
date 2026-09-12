# Bet-conditioned preference pilot: witness-bet-conditioned-001

## Frozen decisions

| Decision | Result |
|---|---|
| beats_existing_actual | NOT PASSED |
| beats_existing_floor | NOT PASSED |
| conditioning_actual_gain | PASS |
| conditioning_floor_gain | PASS |
| cross_bet_robustness | NOT PASSED |

The primary actual flag compares conditioned against blind on pot-sized games
at 50000 iterations, requiring mean delta below -1e-10. The separate floor flag
requires a negative upper endpoint of the mean certified floor difference.
Practical candidate flags require the same comparisons against both old learned
and range-response. Cross-bet robustness requires both measures to beat all three
controls in every texture, regime and omitted-board panel at both bet sizes.
Every rule was frozen before training. They are descriptive decisions, not
confidence levels or adoption decisions. Neither bet size can offset the other.

## Interpretation

Bet size helps the matched new predictor, but the new candidate does not replace
the existing learned model. On pot-sized evaluation cells, conditioning reduces
actual exploitability by 9.75%
versus the blind control, and also improves its certified grouping floor.
The half-pot actual reduction versus blind is 7.60%.
The conditioned predictor beats range-response on both aggregate bet panels.
However, it is worse than the old learned model on both, by
1.13% at pot size and
17.04% at half pot.
This does not show that adding bet size harms the old model: the new model also
uses different targets, output count and training examples. The matched blind
comparison is the evidence specifically about exposing bet size.

Exact clipped-advantage groups remain much better than all learned groups on
these fresh boards. Exact hard-sign groups are substantially worse at pot size.
That makes magnitude-aware prediction a useful follow-up: the exact values
provide grouping distinctions that hard action labels omit. It does not prove
a learned magnitude predictor will generalize or that hard signs bound what
soft classifier probabilities can achieve. Current coefficients stay unchanged.

## Actual policies on fresh boards

Lower unrestricted exploitability is better. Units are conditional river-game
chips, with pot 10. All methods below use the same RegretBR solver from zero.
These are full enumerations within the selected hand pools, not sampled match
returns, BB/100, or six-max playing-strength results.

| Bet | Iterations | Conditioned | Blind | Old learned | Range-response |
|---|---:|---:|---:|---:|---:|
| 10 | 1000 | 0.0070329504 | 0.0075679031 | 0.0069881556 | 0.0077609860 |
| 10 | 10000 | 0.0053939281 | 0.0059612189 | 0.0053337656 | 0.0061297588 |
| 10 | 50000 | 0.0051779958 | 0.0057371051 | 0.0051203366 | 0.0059039062 |
| 5 | 1000 | 0.0056211797 | 0.0059721584 | 0.0049523294 | 0.0059198953 |
| 5 | 10000 | 0.0044668325 | 0.0048251759 | 0.0038337457 | 0.0047785314 |
| 5 | 50000 | 0.0043331665 | 0.0046895544 | 0.0037024193 | 0.0046305186 |

| Bet | Reference | Actual reduction percent | Floor reduction percent |
|---|---|---:|---:|
| 10 | blind | 9.75 | 9.79 |
| 10 | ordinary_preference | -1.13 | -1.07 |
| 10 | range_response | 12.30 | 12.42 |
| 5 | blind | 7.60 | 7.73 |
| 5 | ordinary_preference | -17.04 | -17.32 |
| 5 | range_response | 6.42 | 6.37 |

Positive reduction means improvement; a negative reduction means worse.

## Representation floors and oracle controls

Floors are the least full-hand profile exploitabilities representable by each
group pair. Displayed numbers are midpoints of retained rational certificate
intervals. Oracle-sign uses exact target-game action preferences; oracle-clipped
uses exact action advantages clipped to [-0.5,0.5]. Neither is deployable.
The sign oracle isolates the information retained by our classification target,
while the clipped oracle retains magnitude as well as direction. Neither is
a bound over all possible groupings. In particular, hard sign features can tie
many hands, while soft learned probabilities can retain additional distinctions;
the sign oracle is not a lower bound on the learned predictor's exploitability.
Oracle features are computed from the certified numerical witness policies;
a computed zero advantage receives label 0.5, as in the predecessor classifier.

| Bet | Method | Certified floor | Actual minus floor at 50k |
|---|---|---:|---:|
| 10 | conditioned | 0.0050577861 | 0.0001202097 |
| 10 | blind | 0.0056069100 | 0.0001301951 |
| 10 | ordinary_preference | 0.0050043856 | 0.0001159510 |
| 10 | range_response | 0.0057753131 | 0.0001285931 |
| 10 | oracle_sign | 0.0096444062 | Not solved iteratively |
| 10 | oracle_clipped | 0.0003057513 | Not solved iteratively |
| 5 | conditioned | 0.0042652751 | 0.0000678914 |
| 5 | blind | 0.0046224107 | 0.0000671437 |
| 5 | ordinary_preference | 0.0036356148 | 0.0000668044 |
| 5 | range_response | 0.0045555522 | 0.0000749664 |
| 5 | oracle_sign | 0.0031771413 | Not solved iteratively |
| 5 | oracle_clipped | 0.0002817612 | Not solved iteratively |

## Matched comparisons and board sensitivity

All deltas are conditioned minus reference. Counts mean lower / higher /
numerically overlapping. Each bet has 32 cases across eight board units.

| Bet | Reference | Actual delta | Case counts | Board counts | Omit-board counts | Floor delta |
|---|---|---:|---:|---:|---:|---:|
| 10 | blind | -0.0005591093 | 18/14/0 | 5/3/0 | 8/0/0 | -0.0005491239 |
| 10 | ordinary_preference | 0.0000576592 | 13/19/0 | 3/5/0 | 4/4/0 | 0.0000534004 |
| 10 | range_response | -0.0007259104 | 19/13/0 | 4/4/0 | 8/0/0 | -0.0007175271 |
| 5 | blind | -0.0003563879 | 20/12/0 | 6/2/0 | 8/0/0 | -0.0003571357 |
| 5 | ordinary_preference | 0.0006307472 | 6/26/0 | 2/6/0 | 0/8/0 | 0.0006296603 |
| 5 | range_response | -0.0002973521 | 18/14/0 | 5/3/0 | 8/0/0 | -0.0002902771 |

### boards

| Bet | Panel | Reference | Actual delta | Floor lower | Floor upper |
|---|---|---|---:|---:|---:|
| 10 | 0 | blind | 0.0000921026 | 0.0000997955 | 0.0000997955 |
| 10 | 0 | ordinary_preference | 0.0000696289 | 0.0000619534 | 0.0000619534 |
| 10 | 0 | range_response | -0.0007777137 | -0.0007767828 | -0.0007767828 |
| 10 | 1 | blind | -0.0027627398 | -0.0027593846 | -0.0027593846 |
| 10 | 1 | ordinary_preference | -0.0011465340 | -0.0011637280 | -0.0011637280 |
| 10 | 1 | range_response | -0.0016347903 | -0.0016140699 | -0.0016140699 |
| 10 | 2 | blind | 0.0001647590 | 0.0001612088 | 0.0001612088 |
| 10 | 2 | ordinary_preference | 0.0013718158 | 0.0013585798 | 0.0013585798 |
| 10 | 2 | range_response | 0.0005868385 | 0.0005671752 | 0.0005671752 |
| 10 | 3 | blind | -0.0005208144 | -0.0005079401 | -0.0005079401 |
| 10 | 3 | ordinary_preference | 0.0009248310 | 0.0009428525 | 0.0009428525 |
| 10 | 3 | range_response | 0.0008199309 | 0.0008152425 | 0.0008152425 |
| 10 | 4 | blind | -0.0006425605 | -0.0006211987 | -0.0006211987 |
| 10 | 4 | ordinary_preference | 0.0006127384 | 0.0006134166 | 0.0006134166 |
| 10 | 4 | range_response | 0.0005273614 | 0.0005462921 | 0.0005462921 |
| 10 | 5 | blind | -0.0002155734 | -0.0002075812 | -0.0002075812 |
| 10 | 5 | ordinary_preference | -0.0000181840 | 0.0000081150 | 0.0000081150 |
| 10 | 5 | range_response | 0.0000507699 | 0.0000598695 | 0.0000598695 |
| 10 | 6 | blind | 0.0004790145 | 0.0005120566 | 0.0005120566 |
| 10 | 6 | ordinary_preference | 0.0014850308 | 0.0014618737 | 0.0014618737 |
| 10 | 6 | range_response | -0.0018896253 | -0.0019068346 | -0.0019068346 |
| 10 | 7 | blind | -0.0010670622 | -0.0010699478 | -0.0010699478 |
| 10 | 7 | ordinary_preference | -0.0028380532 | -0.0028558595 | -0.0028558595 |
| 10 | 7 | range_response | -0.0034900549 | -0.0034311086 | -0.0034311086 |
| 5 | 0 | blind | -0.0000452090 | -0.0000479064 | -0.0000479064 |
| 5 | 0 | ordinary_preference | 0.0009519026 | 0.0009463475 | 0.0009463475 |
| 5 | 0 | range_response | -0.0002305054 | -0.0002367511 | -0.0002367511 |
| 5 | 1 | blind | -0.0010804177 | -0.0010822115 | -0.0010822115 |
| 5 | 1 | ordinary_preference | -0.0000859558 | -0.0000897171 | -0.0000897171 |
| 5 | 1 | range_response | 0.0002249075 | 0.0002019630 | 0.0002019630 |
| 5 | 2 | blind | 0.0000258200 | 0.0000149774 | 0.0000149774 |
| 5 | 2 | ordinary_preference | 0.0006910560 | 0.0006869508 | 0.0006869508 |
| 5 | 2 | range_response | -0.0002896335 | -0.0002891394 | -0.0002891394 |
| 5 | 3 | blind | -0.0000881606 | -0.0000738799 | -0.0000738799 |
| 5 | 3 | ordinary_preference | 0.0008470906 | 0.0008447660 | 0.0008447660 |
| 5 | 3 | range_response | 0.0006917223 | 0.0007145949 | 0.0007145949 |
| 5 | 4 | blind | -0.0013446249 | -0.0013466258 | -0.0013466258 |
| 5 | 4 | ordinary_preference | -0.0006096345 | -0.0006055760 | -0.0006055760 |
| 5 | 4 | range_response | -0.0000332798 | -0.0000330742 | -0.0000330742 |
| 5 | 5 | blind | -0.0003522269 | -0.0003470226 | -0.0003470226 |
| 5 | 5 | ordinary_preference | 0.0010114045 | 0.0010187133 | 0.0010187133 |
| 5 | 5 | range_response | -0.0015803316 | -0.0015877726 | -0.0015877726 |
| 5 | 6 | blind | -0.0000049771 | -0.0000239025 | -0.0000239025 |
| 5 | 6 | ordinary_preference | 0.0006025902 | 0.0005884120 | 0.0005884120 |
| 5 | 6 | range_response | -0.0021611810 | -0.0021176161 | -0.0021176161 |
| 5 | 7 | blind | 0.0000386928 | 0.0000494860 | 0.0000494860 |
| 5 | 7 | ordinary_preference | 0.0016375245 | 0.0016473854 | 0.0016473854 |
| 5 | 7 | range_response | 0.0009994849 | 0.0010255784 | 0.0010255784 |

### textures

| Bet | Panel | Reference | Actual delta | Floor lower | Floor upper |
|---|---|---|---:|---:|---:|
| 10 | multiple-pairs-or-trips | blind | -0.0002940238 | -0.0002789456 | -0.0002789456 |
| 10 | multiple-pairs-or-trips | ordinary_preference | -0.0006765112 | -0.0006969929 | -0.0006969929 |
| 10 | multiple-pairs-or-trips | range_response | -0.0026898401 | -0.0026689716 | -0.0026689716 |
| 10 | one-pair | blind | -0.0004290669 | -0.0004143899 | -0.0004143899 |
| 10 | one-pair | ordinary_preference | 0.0002972772 | 0.0003107658 | 0.0003107658 |
| 10 | one-pair | range_response | 0.0002890657 | 0.0003030808 | 0.0003030808 |
| 10 | unpaired-flush-possible | blind | -0.0001780277 | -0.0001733657 | -0.0001733657 |
| 10 | unpaired-flush-possible | ordinary_preference | 0.0011483234 | 0.0011507161 | 0.0011507161 |
| 10 | unpaired-flush-possible | range_response | 0.0007033847 | 0.0006912088 | 0.0006912088 |
| 10 | unpaired-no-flush | blind | -0.0013353186 | -0.0013297945 | -0.0013297945 |
| 10 | unpaired-no-flush | ordinary_preference | -0.0005384526 | -0.0005508873 | -0.0005508873 |
| 10 | unpaired-no-flush | range_response | -0.0012062520 | -0.0011954264 | -0.0011954264 |
| 5 | multiple-pairs-or-trips | blind | 0.0000168579 | 0.0000127918 | 0.0000127918 |
| 5 | multiple-pairs-or-trips | ordinary_preference | 0.0011200573 | 0.0011178987 | 0.0011178987 |
| 5 | multiple-pairs-or-trips | range_response | -0.0005808481 | -0.0005460188 | -0.0005460188 |
| 5 | one-pair | blind | -0.0008484259 | -0.0008468242 | -0.0008468242 |
| 5 | one-pair | ordinary_preference | 0.0002008850 | 0.0002065687 | 0.0002065687 |
| 5 | one-pair | range_response | -0.0008068057 | -0.0008104234 | -0.0008104234 |
| 5 | unpaired-flush-possible | blind | -0.0000311703 | -0.0000294513 | -0.0000294513 |
| 5 | unpaired-flush-possible | ordinary_preference | 0.0007690733 | 0.0007658584 | 0.0007658584 |
| 5 | unpaired-flush-possible | range_response | 0.0002010444 | 0.0002127277 | 0.0002127277 |
| 5 | unpaired-no-flush | blind | -0.0005628133 | -0.0005650589 | -0.0005650589 |
| 5 | unpaired-no-flush | ordinary_preference | 0.0004329734 | 0.0004283152 | 0.0004283152 |
| 5 | unpaired-no-flush | range_response | -0.0000027989 | -0.0000173941 | -0.0000173941 |

### regimes

| Bet | Panel | Reference | Actual delta | Floor lower | Floor upper |
|---|---|---|---:|---:|---:|
| 10 | polarized | blind | -0.0002546697 | -0.0002334384 | -0.0002334384 |
| 10 | polarized | ordinary_preference | 0.0006303199 | 0.0006274361 | 0.0006274361 |
| 10 | polarized | range_response | 0.0005076615 | 0.0005376169 | 0.0005376169 |
| 10 | uniform | blind | -0.0008635489 | -0.0008648094 | -0.0008648094 |
| 10 | uniform | ordinary_preference | -0.0005150014 | -0.0005206352 | -0.0005206352 |
| 10 | uniform | range_response | -0.0019594824 | -0.0019726711 | -0.0019726711 |
| 5 | polarized | blind | -0.0002693520 | -0.0002721014 | -0.0002721014 |
| 5 | polarized | ordinary_preference | 0.0006852119 | 0.0006876723 | 0.0006876723 |
| 5 | polarized | range_response | 0.0003485207 | 0.0003548038 | 0.0003548038 |
| 5 | uniform | blind | -0.0004434239 | -0.0004421699 | -0.0004421699 |
| 5 | uniform | ordinary_preference | 0.0005762826 | 0.0005716482 | 0.0005716482 |
| 5 | uniform | range_response | -0.0009432249 | -0.0009353581 | -0.0009353581 |

### leave_one_board_out

| Bet | Panel | Reference | Actual delta | Floor lower | Floor upper |
|---|---|---|---:|---:|---:|
| 10 | 0 | blind | -0.0006521395 | -0.0006418267 | -0.0006418267 |
| 10 | 0 | ordinary_preference | 0.0000559493 | 0.0000521786 | 0.0000521786 |
| 10 | 0 | range_response | -0.0007185100 | -0.0007090620 | -0.0007090620 |
| 10 | 1 | blind | -0.0002443049 | -0.0002333724 | -0.0002333724 |
| 10 | 1 | ordinary_preference | 0.0002296868 | 0.0002272759 | 0.0002272759 |
| 10 | 1 | range_response | -0.0005960704 | -0.0005894495 | -0.0005894495 |
| 10 | 2 | blind | -0.0006625190 | -0.0006506000 | -0.0006506000 |
| 10 | 2 | ordinary_preference | -0.0001300774 | -0.0001330537 | -0.0001330537 |
| 10 | 2 | range_response | -0.0009134460 | -0.0009010560 | -0.0009010560 |
| 10 | 3 | blind | -0.0005645800 | -0.0005550073 | -0.0005550073 |
| 10 | 3 | ordinary_preference | -0.0000662225 | -0.0000736641 | -0.0000736641 |
| 10 | 3 | range_response | -0.0009467449 | -0.0009364942 | -0.0009364942 |
| 10 | 4 | blind | -0.0005471877 | -0.0005388275 | -0.0005388275 |
| 10 | 4 | ordinary_preference | -0.0000216378 | -0.0000266019 | -0.0000266019 |
| 10 | 4 | range_response | -0.0009049493 | -0.0008980727 | -0.0008980727 |
| 10 | 5 | blind | -0.0006081858 | -0.0005979157 | -0.0005979157 |
| 10 | 5 | ordinary_preference | 0.0000684940 | 0.0000598698 | 0.0000598698 |
| 10 | 5 | range_response | -0.0008368648 | -0.0008285837 | -0.0008285837 |
| 10 | 6 | blind | -0.0007074127 | -0.0007007212 | -0.0007007212 |
| 10 | 6 | ordinary_preference | -0.0001462510 | -0.0001478100 | -0.0001478100 |
| 10 | 6 | range_response | -0.0005596654 | -0.0005476260 | -0.0005476260 |
| 10 | 7 | blind | -0.0004865446 | -0.0004747205 | -0.0004747205 |
| 10 | 7 | ordinary_preference | 0.0004713324 | 0.0004690090 | 0.0004690090 |
| 10 | 7 | range_response | -0.0003310326 | -0.0003298726 | -0.0003298726 |
| 5 | 0 | blind | -0.0004008420 | -0.0004013113 | -0.0004013113 |
| 5 | 0 | ordinary_preference | 0.0005848679 | 0.0005844192 | 0.0005844192 |
| 5 | 0 | range_response | -0.0003069016 | -0.0002979237 | -0.0002979237 |
| 5 | 1 | blind | -0.0002529551 | -0.0002535534 | -0.0002535534 |
| 5 | 1 | ordinary_preference | 0.0007331334 | 0.0007324284 | 0.0007324284 |
| 5 | 1 | range_response | -0.0003719606 | -0.0003605972 | -0.0003605972 |
| 5 | 2 | blind | -0.0004109891 | -0.0004102947 | -0.0004102947 |
| 5 | 2 | ordinary_preference | 0.0006221317 | 0.0006214759 | 0.0006214759 |
| 5 | 2 | range_response | -0.0002984547 | -0.0002904397 | -0.0002904397 |
| 5 | 3 | blind | -0.0003947061 | -0.0003976008 | -0.0003976008 |
| 5 | 3 | ordinary_preference | 0.0005998411 | 0.0005989309 | 0.0005989309 |
| 5 | 3 | range_response | -0.0004386484 | -0.0004338303 | -0.0004338303 |
| 5 | 4 | blind | -0.0002152112 | -0.0002157799 | -0.0002157799 |
| 5 | 4 | ordinary_preference | 0.0008079446 | 0.0008061226 | 0.0008061226 |
| 5 | 4 | range_response | -0.0003350767 | -0.0003270204 | -0.0003270204 |
| 5 | 5 | blind | -0.0003569823 | -0.0003585804 | -0.0003585804 |
| 5 | 5 | ordinary_preference | 0.0005763676 | 0.0005740812 | 0.0005740812 |
| 5 | 5 | range_response | -0.0001140693 | -0.0001049206 | -0.0001049206 |
| 5 | 6 | blind | -0.0004065895 | -0.0004047404 | -0.0004047404 |
| 5 | 6 | ordinary_preference | 0.0006347697 | 0.0006355529 | 0.0006355529 |
| 5 | 6 | range_response | -0.0000310908 | -0.0000292287 | -0.0000292287 |
| 5 | 7 | blind | -0.0004128280 | -0.0004152245 | -0.0004152245 |
| 5 | 7 | ordinary_preference | 0.0004869219 | 0.0004842709 | 0.0004842709 |
| 5 | 7 | range_response | -0.0004826145 | -0.0004782565 | -0.0004782565 |

## Design and limits

Eight original training boards, two hand pools and two range regimes at each
of two bet sizes give 64 training cells. Eight new boards were selected before
training by the frozen hash rule, two per texture, excluding all 36 earlier
boards and their suit isomorphisms. The same pools/regimes/sizes give 64
evaluation cells. Each has 96 holdings per seat, stacks 20/20, pot 10, one bet
of 5 or 10, with no raises or extra streets. These are synthetic conditional
ranges. Eight balanced boards are eight evaluation units, not 64 independent
boards. This is a small fresh-board pilot, not a population guarantee.

Training uses three fixed bank witnesses per seat from the old learned, response
and equity groupings. Labels are the signs of conditional action advantages,
with exact ties 0.5. The two predictors see identical training rows and labels.
Both use 91 quadratic columns and the same ridge-logistic fit; conditioned
receives bet/pot and blind masks that coordinate to zero. Each cell has equal
weight, distributed by that seat's collision-conditioned hand marginal.
All six binary outputs per predictor are fitted on training cells only.
The candidate is written and hashed before any evaluation cell is opened.
Model fitting is then disabled. No selection among models by holdout scores.

The old learned model has four outputs and older training targets. Therefore
comparisons with it are whole-candidate comparisons. Only the matched blind
ablation isolates exposing bet size within the new training setup.
Adding bet size also adds effective polynomial terms; no equal-effective-
parameter or equal-wall-time claim is made. All groupings match occupied
capacity and use the unchanged anchored clustering algorithm. Oracle holdout
witnesses supply neither predictor's features, coefficients or labels.

## Verification and retention

The initial bet-input test failed as intended against a blind scaffold.
Eight model/data-boundary preflights, six existing BR tests and thirteen
payoff/optimality tests passed. A temporary older-experiment import collision
was caught by preflight and corrected before freeze; its failed receipt is
retained. There was no scored-panel rehearsal.

The worker made 1280 LP calls and fitted 12 binary tasks. It retained 256
solver trajectories with 768 checkpoints. The parent disabled LP, rebuilt
training targets and verified all 1280 certificates, refitted all models
exactly, then disabled fitting for fresh-board verification. It replayed
12.8 million iterations from zero and independently checked every saved
full-hand policy using scalar arithmetic. Blind features and group labels
were identical across bet sizes. A separate Fraction audit rebuilt every
panel, mean, certificate interval and frozen decision flag.
Maximum scalar discrepancy: 1.332268e-15 chips.
Independent summary scalar checks: 3,548.
Pinned files checked before and after: 1243.
Worker: 695.208719 s; verifier: 571.601671 s.
Combined invocation: 1267.060249 s, exit 0.
Python 3.14.6, NumPy 2.5.2, SciPy 1.18.0; one BLAS thread; no tracemalloc.
Each subprocess had a 1200-second timeout. No RSS cap or peak-memory claim.
All sixteen earlier milestones were verified and preserved. No independent
cold review, production change, adoption, commit or push is claimed.

Plan SHA-256:
f2d982cbada98dbc1b773df6644c1fc85aaa97dde7b3f079febcd8e6545e5430

Frozen trained candidate SHA-256:
ca2dcb57b120794d1e3d5700e446a61fbc6fb9e16ced08efaddbc38cf6ec55f4

Original result manifest SHA-256:
f1f38a117f1fbb3bddc262cb16ccbf8a93ab96b83e7736bb57b3bd9b2d363fd0
