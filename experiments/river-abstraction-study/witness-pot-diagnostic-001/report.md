# Pot-sized failure diagnostic: witness-pot-diagnostic-001

## Results under the frozen rules

| Separate decision | Result |
|---|---|
| solver_gap_reduced | PASS |
| solver_ranking_repaired | PASS |
| oracle_representation_repaired | PASS |
| oracle_context_gain | PASS |

The solver rules use the 48 polarized-range cases at 50000 iterations. Gap
reduction means learned BR is less exploitable than learned ordinary CFR.
Ranking repair separately means learned BR is less exploitable than response BR.
Both require a mean difference below -1e-10 chips.
The oracle rules use the 24 multiple-pairs-or-trips cases. Representation repair
requires the pot-witness floor to beat both frozen learned and response floors.
Context gain separately requires it to beat the half-witness floor. Each floor
difference must have a negative upper numerical endpoint.
These are separate predeclared diagnostics, not a combined adoption gate.

This is a post-finding diagnostic on previously observed failing panels.
It is not a fresh confirmation or a population confidence statement.
The 60-case union contains 48 polarized cases and 24 paired/trips cases, with
12 in their intersection. Every case from each declared panel was kept.
Panels receive equal board weights and are reported separately; there is no
primary average over the union that could hide one panel behind the other.

## Interpretation

On polarized ranges, changing the solver reduces learned-policy exploitability by
30.68% at matched 50000 updates,
removing 94.21% of its residual
above the fixed grouping floor. The learned-vs-response ranking under BR is
favorable on this panel.
That small aggregate ranking is board-sensitive: learned BR wins on nine of
sixteen board means, and omitting any of boards 2, 10 or 13 reverses the mean
ranking. Passing the ranking flag is not a robust across-board advantage.
This separates a solver-objective limitation from a lack of representation
capacity. It does not prove ordinary CFR has converged; the finite checkpoint
comparison and the independently attained LP targets are the evidence.

The paired/trips panel must still be considered separately. Its learned floor
remains worse than the response floor, and its learned BR policy is also worse
than response BR at the final checkpoint. The solver improvement does not
repair that representation ranking. Oracle pot-witness grouping reduces the
floor by 83.89% versus
learned and 83.41% versus response.
That demonstrates substantial room at the same group count when exact target-
game information is supplied. The half-witness control performs worse than
both frozen groupings here, so exact signals from the old context are not
enough. Payoffs and opponent witnesses change together; the test does not
identify which of those two changes explains the context gain.

A practical follow-up is to use the unrestricted-response objective when
judging groupings and test whether a bet-conditioned predictor can recover
the oracle advantage on untouched boards. The current result establishes
neither that learned recovery nor a deployable policy improvement.

## Solver comparison at all checkpoints

Lower unrestricted full-hand exploitability is better. Units are conditional
river-game chips, with pot 10 and bet 10. These are deterministic enumerated
best-response values, not sampled match returns or BB/100.

| Panel | Iterations | Learned CFR | Learned BR | Response CFR | Response BR |
|---|---:|---:|---:|---:|---:|
| intersection | 1000 | 0.0161040624 | 0.0123000217 | 0.0143843463 | 0.0115355859 |
| intersection | 10000 | 0.0148917879 | 0.0104149635 | 0.0138097162 | 0.0096002844 |
| intersection | 50000 | 0.0147103264 | 0.0101387177 | 0.0141184409 | 0.0093205707 |
| paired_trips | 1000 | 0.0172523746 | 0.0135237844 | 0.0164302961 | 0.0132472115 |
| paired_trips | 10000 | 0.0162677870 | 0.0118297067 | 0.0162908545 | 0.0115426609 |
| paired_trips | 50000 | 0.0162560453 | 0.0116078026 | 0.0165966697 | 0.0113090533 |
| polarized | 1000 | 0.0087581313 | 0.0068663515 | 0.0084951808 | 0.0069627517 |
| polarized | 10000 | 0.0070060177 | 0.0049902292 | 0.0067731463 | 0.0050745611 |
| polarized | 50000 | 0.0068333004 | 0.0047368938 | 0.0067471717 | 0.0048069251 |

## Representation targets and remaining solver gaps

The grouping floor is the least full-hand profile exploitability representable
by a pair of groups, certified by two asymmetric saddle problems. A compressed
game equilibrium need not minimize that full-hand quantity.
Floor values below are interval midpoints; exact rational endpoints are retained.

| Panel | Method | Floor | CFR residual, 50k | BR residual, 50k |
|---|---|---:|---:|---:|
| intersection | ordinary_preference | 0.0099922513 | 0.0047180751 | 0.0001464664 |
| intersection | range_response | 0.0091467957 | 0.0049716452 | 0.0001737749 |
| paired_trips | ordinary_preference | 0.0114833340 | 0.0047727112 | 0.0001244686 |
| paired_trips | range_response | 0.0111475712 | 0.0054490985 | 0.0001614821 |
| polarized | ordinary_preference | 0.0046081543 | 0.0022251461 | 0.0001287395 |
| polarized | range_response | 0.0046567914 | 0.0020903803 | 0.0001501337 |

The saved LP target combines each grouping's constrained-seat saddle policies.
All 120 resulting full-hand profiles attain the corresponding certified floor
upper endpoint within 1e-10 chips. These are oracle targets, not additional
iterative solver trajectories. They independently establish the attainable
representation target against which finite solver residuals are measured.

## Solver sensitivity at 50000 iterations

Counts are lower / higher / numerically overlapping. Differences are in chips.

| Panel | Comparison | Mean delta | Case counts | Board counts | Omit-board counts |
|---|---|---:|---:|---:|---:|
| intersection | learned_br_minus_cfr | -0.0045716088 | 12/0/0 | 4/0/0 | 4/0/0 |
| intersection | learned_minus_response_br | 0.0008181470 | 6/6/0 | 1/3/0 | 0/4/0 |
| intersection | learned_minus_response_cfr | 0.0005918855 | 7/5/0 | 2/2/0 | 1/3/0 |
| intersection | response_br_minus_cfr | -0.0047978703 | 12/0/0 | 4/0/0 | 4/0/0 |
| paired_trips | learned_br_minus_cfr | -0.0046482427 | 24/0/0 | 4/0/0 | 4/0/0 |
| paired_trips | learned_minus_response_br | 0.0002987493 | 14/10/0 | 1/3/0 | 1/3/0 |
| paired_trips | learned_minus_response_cfr | -0.0003406244 | 14/10/0 | 3/1/0 | 3/1/0 |
| paired_trips | response_br_minus_cfr | -0.0052876164 | 24/0/0 | 4/0/0 | 4/0/0 |
| polarized | learned_br_minus_cfr | -0.0020964066 | 42/6/0 | 15/1/0 | 16/0/0 |
| polarized | learned_minus_response_br | -0.0000700313 | 23/25/0 | 9/7/0 | 13/3/0 |
| polarized | learned_minus_response_cfr | 0.0000861287 | 28/20/0 | 9/7/0 | 3/13/0 |
| polarized | response_br_minus_cfr | -0.0019402467 | 43/5/0 | 15/1/0 | 16/0/0 |

### solver_boards

| Panel | Board | Learned BR minus CFR | Response BR minus CFR | Learned minus response BR |
|---|---|---:|---:|---:|
| intersection | 12 | -0.0052075744 | -0.0072655354 | 0.0022073651 |
| intersection | 13 | -0.0010775679 | -0.0025592445 | -0.0021964700 |
| intersection | 14 | -0.0079360616 | -0.0026395904 | 0.0024290046 |
| intersection | 15 | -0.0040652310 | -0.0067271109 | 0.0008326884 |
| paired_trips | 12 | -0.0054865488 | -0.0074592070 | 0.0009428601 |
| paired_trips | 13 | -0.0033042016 | -0.0037338195 | -0.0020659065 |
| paired_trips | 14 | -0.0054792007 | -0.0030546405 | 0.0008820680 |
| paired_trips | 15 | -0.0043230196 | -0.0069027986 | 0.0014359755 |
| polarized | 0 | -0.0011113977 | -0.0012585016 | 0.0010000005 |
| polarized | 1 | -0.0032467616 | -0.0012844612 | -0.0004676156 |
| polarized | 10 | -0.0021605268 | -0.0017579514 | -0.0019434617 |
| polarized | 11 | -0.0044315069 | -0.0017813935 | 0.0015259399 |
| polarized | 12 | -0.0052075744 | -0.0072655354 | 0.0022073651 |
| polarized | 13 | -0.0010775679 | -0.0025592445 | -0.0021964700 |
| polarized | 14 | -0.0079360616 | -0.0026395904 | 0.0024290046 |
| polarized | 15 | -0.0040652310 | -0.0067271109 | 0.0008326884 |
| polarized | 2 | -0.0001063030 | -0.0006768211 | -0.0014423252 |
| polarized | 3 | 0.0000250584 | 0.0000264568 | -0.0003528222 |
| polarized | 4 | -0.0002770358 | -0.0012590192 | -0.0010598796 |
| polarized | 5 | -0.0010521174 | -0.0007562817 | -0.0005597267 |
| polarized | 6 | -0.0006789129 | -0.0002524309 | -0.0005288744 |
| polarized | 7 | -0.0002686152 | -0.0003180025 | 0.0001667817 |
| polarized | 8 | -0.0012682128 | -0.0019514229 | -0.0007885239 |
| polarized | 9 | -0.0006797389 | -0.0005826363 | 0.0000574194 |

### solver_leave_one_board_out

| Panel | Board | Learned BR minus CFR | Response BR minus CFR | Learned minus response BR |
|---|---|---:|---:|---:|
| intersection | 12 | -0.0043596202 | -0.0039753153 | 0.0003550743 |
| intersection | 13 | -0.0057362890 | -0.0055440789 | 0.0018230193 |
| intersection | 14 | -0.0034501245 | -0.0055172969 | 0.0002811945 |
| intersection | 15 | -0.0047404013 | -0.0041547901 | 0.0008132999 |
| paired_trips | 12 | -0.0043688073 | -0.0045637529 | 0.0000840457 |
| paired_trips | 13 | -0.0050962564 | -0.0058055487 | 0.0010869679 |
| paired_trips | 14 | -0.0043712566 | -0.0060319417 | 0.0001043097 |
| paired_trips | 15 | -0.0047566504 | -0.0047492223 | -0.0000803261 |
| polarized | 0 | -0.0021620739 | -0.0019856963 | -0.0001413667 |
| polarized | 1 | -0.0020197163 | -0.0019839657 | -0.0000435256 |
| polarized | 10 | -0.0020921319 | -0.0019523997 | 0.0000548641 |
| polarized | 11 | -0.0019407332 | -0.0019508369 | -0.0001764293 |
| polarized | 12 | -0.0018889954 | -0.0015852274 | -0.0002218577 |
| polarized | 13 | -0.0021643292 | -0.0018989801 | 0.0000717313 |
| polarized | 14 | -0.0017070963 | -0.0018936237 | -0.0002366336 |
| polarized | 15 | -0.0019651516 | -0.0016211224 | -0.0001302126 |
| polarized | 2 | -0.0022290802 | -0.0020244750 | 0.0000214550 |
| polarized | 3 | -0.0022378376 | -0.0020713602 | -0.0000511785 |
| polarized | 4 | -0.0022176980 | -0.0019856618 | -0.0000040414 |
| polarized | 5 | -0.0021660259 | -0.0020191777 | -0.0000373849 |
| polarized | 6 | -0.0021909062 | -0.0020527677 | -0.0000394417 |
| polarized | 7 | -0.0022182594 | -0.0020483963 | -0.0000858188 |
| polarized | 8 | -0.0021516195 | -0.0019395016 | -0.0000221317 |
| polarized | 9 | -0.0021908511 | -0.0020307540 | -0.0000785280 |

## Oracle grouping comparison on paired/trips cases

Both oracle groupings keep each case's occupied group count. Three action-
advantage columns come from the learned, response and equity opponent witnesses
in that fixed order, clipped to [-0.5, 0.5], with unchanged weighted anchored
clustering. Half-witness uses half-pot payoffs and witnesses; pot-witness uses
pot-sized payoffs and witnesses. Both floors are evaluated in the pot-sized game.
Thus the intervention changes both payoff context and opponent witnesses.
It is not a one-scalar bet-input ablation. Target-case oracle information is
used, so neither is a deployable learned candidate or evidence of generalization.

| Panel | Learned floor | Response floor | Half-witness floor | Pot-witness floor |
|---|---:|---:|---:|---:|
| overall | 0.0114833340 | 0.0111475712 | 0.0168708699 | 0.0018497303 |
| boards:12 | 0.0158870511 | 0.0148633340 | 0.0095019280 | 0.0020096754 |
| boards:13 | 0.0078694447 | 0.0098867198 | 0.0411159860 | 0.0028586199 |
| boards:14 | 0.0101229825 | 0.0092322848 | 0.0108613887 | 0.0009055309 |
| boards:15 | 0.0120538578 | 0.0106079462 | 0.0060041771 | 0.0016250951 |
| regimes:polarized | 0.0099922513 | 0.0091467957 | 0.0192843204 | 0.0005731312 |
| regimes:uniform | 0.0129744168 | 0.0131483467 | 0.0144574195 | 0.0031263294 |
| leave_one_board_out:12 | 0.0100154283 | 0.0099089836 | 0.0193271839 | 0.0017964153 |
| leave_one_board_out:13 | 0.0126879638 | 0.0115678550 | 0.0087891646 | 0.0015134338 |
| leave_one_board_out:14 | 0.0119367846 | 0.0117860000 | 0.0188740304 | 0.0021644635 |
| leave_one_board_out:15 | 0.0112931595 | 0.0113274462 | 0.0204931009 | 0.0019246087 |

| Panel | Pot-witness minus | Lower endpoint | Upper endpoint | Case counts |
|---|---|---:|---:|---:|
| overall | pot_minus_half_witness | -0.0150211396 | -0.0150211396 | 23/1/0 |
| overall | pot_minus_ordinary_preference | -0.0096336037 | -0.0096336037 | 24/0/0 |
| overall | pot_minus_range_response | -0.0092978409 | -0.0092978409 | 24/0/0 |
| boards:12 | pot_minus_half_witness | -0.0074922527 | -0.0074922527 | 6/0/0 |
| boards:12 | pot_minus_ordinary_preference | -0.0138773758 | -0.0138773758 | 6/0/0 |
| boards:12 | pot_minus_range_response | -0.0128536586 | -0.0128536586 | 6/0/0 |
| boards:13 | pot_minus_half_witness | -0.0382573660 | -0.0382573660 | 6/0/0 |
| boards:13 | pot_minus_ordinary_preference | -0.0050108248 | -0.0050108248 | 6/0/0 |
| boards:13 | pot_minus_range_response | -0.0070280999 | -0.0070280999 | 6/0/0 |
| boards:14 | pot_minus_half_witness | -0.0099558578 | -0.0099558578 | 6/0/0 |
| boards:14 | pot_minus_ordinary_preference | -0.0092174517 | -0.0092174517 | 6/0/0 |
| boards:14 | pot_minus_range_response | -0.0083267540 | -0.0083267540 | 6/0/0 |
| boards:15 | pot_minus_half_witness | -0.0043790820 | -0.0043790820 | 5/1/0 |
| boards:15 | pot_minus_ordinary_preference | -0.0104287627 | -0.0104287627 | 6/0/0 |
| boards:15 | pot_minus_range_response | -0.0089828510 | -0.0089828510 | 6/0/0 |
| regimes:polarized | pot_minus_half_witness | -0.0187111891 | -0.0187111891 | 11/1/0 |
| regimes:polarized | pot_minus_ordinary_preference | -0.0094191201 | -0.0094191201 | 12/0/0 |
| regimes:polarized | pot_minus_range_response | -0.0085736645 | -0.0085736645 | 12/0/0 |
| regimes:uniform | pot_minus_half_witness | -0.0113310901 | -0.0113310901 | 12/0/0 |
| regimes:uniform | pot_minus_ordinary_preference | -0.0098480874 | -0.0098480874 | 12/0/0 |
| regimes:uniform | pot_minus_range_response | -0.0100220173 | -0.0100220173 | 12/0/0 |
| leave_one_board_out:12 | pot_minus_half_witness | -0.0175307686 | -0.0175307686 | 17/1/0 |
| leave_one_board_out:12 | pot_minus_ordinary_preference | -0.0082190130 | -0.0082190130 | 18/0/0 |
| leave_one_board_out:12 | pot_minus_range_response | -0.0081125683 | -0.0081125683 | 18/0/0 |
| leave_one_board_out:13 | pot_minus_half_witness | -0.0072757308 | -0.0072757308 | 17/1/0 |
| leave_one_board_out:13 | pot_minus_ordinary_preference | -0.0111745300 | -0.0111745300 | 18/0/0 |
| leave_one_board_out:13 | pot_minus_range_response | -0.0100544212 | -0.0100544212 | 18/0/0 |
| leave_one_board_out:14 | pot_minus_half_witness | -0.0167095669 | -0.0167095669 | 17/1/0 |
| leave_one_board_out:14 | pot_minus_ordinary_preference | -0.0097723211 | -0.0097723211 | 18/0/0 |
| leave_one_board_out:14 | pot_minus_range_response | -0.0096215365 | -0.0096215365 | 18/0/0 |
| leave_one_board_out:15 | pot_minus_half_witness | -0.0185684922 | -0.0185684922 | 18/0/0 |
| leave_one_board_out:15 | pot_minus_ordinary_preference | -0.0093685507 | -0.0093685507 | 18/0/0 |
| leave_one_board_out:15 | pot_minus_range_response | -0.0094028375 | -0.0094028375 | 18/0/0 |

## Solver definition and cost

Ordinary CFR is the existing alternating compressed-game solver. The new BR
solver is two independent regret learners, each facing an unrestricted exact
best response on every iteration. The averaged constrained-seat policies are
paired only for profile evaluation. Both solvers start with zero regrets and
uniform policies and use unweighted average strategies; exact best-response
ties use probability 0.5. Every checkpoint is retained. No algorithm samples.
The two methods receive matched paired update counts, not matched wall time or
arithmetic work. Method/algorithm order rotates by case. No timing threshold
is used to select a winner. Reported active times exclude checkpoint scoring.

This full-enumeration one-bet specialization follows the objective of
[Johanson et al., Finding Optimal Abstract Strategies in Extensive-Form Games
(2012)](https://johanson.ca/publications/poker/2012-aaai-cfr-br/2012-aaai-cfr-br.pdf).
Its two-player zero-sum interpretation does not establish a six-player guarantee.

| Panel | Learned CFR seconds | Learned BR seconds | Response CFR seconds | Response BR seconds |
|---|---:|---:|---:|---:|
| intersection | 1.193393 | 1.398457 | 1.186182 | 1.398293 |
| paired_trips | 1.192125 | 1.404044 | 1.189532 | 1.404626 |
| polarized | 1.321057 | 1.550787 | 1.299032 | 1.541607 |

## Verification and retention

All games use the retained public RiverHoldem path, 96 holdings per seat,
pot 10, bet 10, stacks 20/20, heads-up and one bet without raises. These are
synthetic conditional ranges, not ranges reached by a full-game betting policy.
The learned classifier, frozen groups and source code were not modified.
Exactly 240 solver trajectories produced 720 checkpoint policies. Forty-eight
oracle group pairs required 96 new LP calls. LP time/iteration limits and
rational certificate acceptance were unchanged. There were no model fits.

The analytic update test first failed against a non-updating RED scaffold.
After implementation, six preflight tests passed: direct scalar regret updates,
exhaustive toy best responses, a known grouping floor, zero-payoff ties,
invalid-input refusals and witness feature arithmetic.
Thirteen existing payoff and optimality tests passed. No scored-panel rehearsal.
The independent parent pass disabled LP and learning, reconstructed games and
oracle features/groups, checked 600 certificates and replayed all 720 checkpoint
policies from zero for 12000000 paired iterations. Ordinary CFR at 1000 and
10000 iterations reproduced the retained pot-sized policy and score bytes.
Separate scalar arithmetic checked all policy values and 120 LP targets.
A separate standard-library rational audit rebuilt panels, means, intervals
and the four frozen decision flags. This is computational verification;
no independent cold review or population confidence interval is claimed.
Maximum scalar discrepancy: 8.881784e-16 chips.
Summary scalar checks: 2,093.
Pinned files checked before and after execution: 1139.
Worker: 372.524209 s; verifier: 413.082989 s.
Combined invocation: 785.809632 s, exit 0.
Each subprocess was bounded to 1200 seconds. No RSS cap or peak-memory claim.
Python 3.14.6, NumPy 2.5.2, SciPy 1.18.0; one BLAS thread; no tracemalloc.
All fifteen predecessor milestones were verified and preserved. Every result,
including failures of decision flags, is retained. No production change,
adoption, commit or push was performed.

Plan SHA-256:
d36f7afc29177f1ebee9c6b73a821ae7ee8b70b0db4fbca618a8f1cff0aa94c0

Frozen learned candidate SHA-256:
ee50b041d7a096fc223082df5b02845a551171bfca062ae8cae22a1e791ad8ce

Original result manifest SHA-256:
8ed4acf9cbbbadb16cd4679e1d68a7097da3e5ed2de26d8709cab70b0b8f98e7
