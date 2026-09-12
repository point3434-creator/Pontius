# Witness-groups-development-001: action incentives at fixed capacity

The single approved invocation completed successfully. All four development cases
and eight asymmetric LP solutions are retained. Worker and parent exited 0; the
worker took 10.181 seconds and the full invocation, including parent verification,
took 15.490 seconds. There was no retry or additional optimization during analysis.

At matched occupied group counts, witness_advantage lowered the equal-weight mean
grouping floor by 33.90% versus the primary range-equity control and 28.87% versus
the secondary range-response control. Both case-level comparisons are mixed:
three lower floors and one higher floor. Every result is retained.

## Certified grouping floors

Exploitability is in chips, with a 10-chip pot. Lower is better. These are minima
over policies obeying each method's fixed group assignments, evaluated against
unrestricted individual-hand responses. They are not ordinary CFR checkpoint
scores. Exact rational interval endpoints remain in the retained JSON; displayed
decimals are rounded. The mean is equal-weight over all four declared cases.

| Method | Mean grouping floor | New method's reduction relative to control |
| --- | ---: | ---: |
| Uniform-equity | 0.0087157175 | 58.07% |
| Range-equity (primary) | 0.0055293141 | 33.90% |
| Range-response (secondary) | 0.0051380898 | 28.87% |
| Witness-advantage candidate | 0.0036547801 | -- |

The exact-hand control's mean interval contains zero with an upper endpoint below
6.35e-17 chips. The candidate has a strictly higher floor than this uncompressed
control in every case. Compression still has a cost.

| Development case | Groups, seats 0/1 | Uniform-equity | Range-equity | Range-response | New candidate |
| --- | --- | ---: | ---: | ---: | ---: |
| 0, uniform | 37/36 | 0.00770873 | 0.00496895 | 0.00607804 | 0.00626811 |
| 0, polarized | 37/36 | 0.01146635 | 0.00750960 | 0.00722990 | 0.00649415 |
| 1, uniform | 45/51 | 0.00672817 | 0.00384131 | 0.00276461 | 0.00176902 |
| 1, polarized | 45/51 | 0.00895963 | 0.00579741 | 0.00447981 | 0.00008784 |

Board 0 is 2c 7d 9h Js Qc; board 1 is 2h 7h Jh Qc Ks. Each retained case uses
96 hands per seat and the original range and collision population. All compressed
methods have the same occupied capacity per seat/case. No groups were added.

The first board's uniform case is worse than both range-based controls: the new
floor increases by 0.00129916 chips versus range-equity and 0.00019007 versus
range-response. The second board's polarized case supplies the largest gain.
The new method is better than uniform-equity in all four cases. No case or
control was dropped, and no headline was chosen after looking at the outcomes.

The exact primary mean difference interval is approximately
[-0.001874533911785429, -0.001874533911785118] chips. The secondary interval is
approximately [-0.001483309630173745, -0.001483309630173542] chips. These are
numerical certificate intervals on fixed cases, not statistical confidence
intervals or a random-board population claim.

## What this establishes

The chosen action-incentive features can produce a substantially lower grouping
floor on average in these development games, without using additional groups.
The improvement is therefore in the policy class represented by the assignments,
not a difference in the number of ordinary CFR training iterations. There was
no new CFR training in this invocation. The paired constrained-seat policies are
retained and certify the achievable upper endpoint for each candidate floor.

This is an oracle-assisted screen. Each hand's four features use opponent
witnesses from previously solved controls, including the full-hand control.
Their construction cost is excluded from the measured screen runtime. Equal
group counts do not imply equal feature-generation compute or information.
The result does not establish a cheap online feature generator or improvement
in the deployed bot, six-max playing strength, BB/100, or unseen-board play.

The next recommended experiment is to freeze this rule and declare a fresh board
panel before opening its results. That can test whether the favorable direction
survives outside development. The old holdout cases were already observed and
should not be relabeled fresh confirmation. If the direction survives, a later
ablation can ask whether cheaper witness banks retain the gain. Neither next
experiment is authorized or invoked by this report.

## Verification, authority and retention

The reviewed parent reconstructed all four games, reverified the retained bank
certificates, regenerated the features and group assignments, certified each new
solution, and recomputed every comparison before writing the summary/manifest.
Every source, input and witness pin was checked before launch and before completion.

Post-run verification used no additional LP call. It independently recomputed
all 3,072 feature entries with scalar math.fsum calculations, checked all eight
asymmetric saddle bounds and four paired policies with scalar accumulation,
and rechecked sixteen per-case differences and all four means with Fraction
arithmetic. Maximum feature discrepancy was 8.882e-15 chips; maximum value
discrepancy was 1.111e-16 chips. All eight rational certificates satisfied the
1e-8-chip requirement; the widest was 3.829e-16 chips. This audit reused the
reconstructed payoff matrices and did not independently implement card ranking.

All ten result-manifest members verified. The original output directory was
read-only during analysis. All 63 pre-invocation packet members, seven identity
members, ten source/document pins, sixteen input files, four witness-case files
and the witness manifest/plan bindings remain intact. The previous three
milestones were also verified unchanged during retention.

The approved plan SHA-256 is:
9581a2a8e8d74d9d66e31abed59a61cff7625b769be4521a303b0c343f0ed855.
The user's exact approval words, I approve, are recorded with that plan identity.
Runtime was Python 3.14.6, NumPy 2.5.2 and SciPy 1.18.0 in the pinned environment.
The worker remained within its 120-second timeout; each LP retained its five-second
and 10,000-iteration limits. Parent verification and I/O were outside the worker
timeout. No RSS cap was imposed or peak-memory measurement claimed.

Original output:
D:/Pontius-training/river-abstraction-study/witness-groups-development-001.
The named milestone contains a byte-exact output copy, invocation authority and
captures, post-run verification and the evidence helper scripts. Those scripts
are retained evidence, not authority to execute again. Its milestone manifest
covers every other file in the archive.

- [Summary and all case certificates](../../experiments/river-abstraction-study/witness-groups-development-001/summary.json)
- [Compact analysis](../../experiments/river-abstraction-study/witness-groups-development-001/invocation/analysis.json)
- [Verification receipt](../../experiments/river-abstraction-study/witness-groups-development-001/invocation/verification.json)
- [Reviewed disposition](river-witness-groups-r001/disposition.md)
- [Recorded authorization](river-witness-groups-r001/invocation-001/authorization.json)

Earlier packet readiness statements are retained as historical records; this
report records the completed invocation. No source or milestone was committed
or pushed. Publication and any later experiment require separate authorization.
