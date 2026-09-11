# River abstraction study: development-001

Status: completed local development trial; no holdout or formal campaign claim.
The user said "Let's try it" after the candidate and next gate were described.
The coordinator completed one opposing review, announced the bounded development
trial, then executed four cases sequentially with a 60-second timeout per case.
No source code was changed after review. No commit, push or adoption occurred.

## Result

At 10,000 iterations, range-response grouping had lower full-game exploitability
than the existing uniform-equity bins in all four fixed development cases.
The equal-weight mean was 49.19% lower. Range-equity-only grouping was 41.31%
lower than baseline. The richer features beat that control in three of four
cases; the first board's polarized range favored the simpler control.
These are finite-budget observations in four declared heads-up river microgames.
They do not establish six-max strength, unseen-board generalization, or an
asymptotic abstraction floor. No grouping rule changed after the author smoke.

Exploitability in chips; lower is better. Pot is 10 chips in every case.

| Case | Exact hands | Baseline bins | Range equity | Range response |
| --- | --- | --- | --- | --- |
| d0-uniform | 0.00016726 | 0.01127407 | 0.00985794 | 0.00750577 |
| d0-polarized | 0.00016989 | 0.01513708 | 0.01075320 | 0.01149043 |
| d1-uniform | 0.00016392 | 0.00905367 | 0.00585252 | 0.00445092 |
| d1-polarized | 0.00017675 | 0.01990466 | 0.00603409 | 0.00468616 |

| Method | Equal-weight mean, chips | Reduction versus baseline |
| --- | --- | --- |
| exact | 0.00016946 | 98.78% |
| range_equity | 0.00812444 | 41.31% |
| range_response | 0.00703332 | 49.19% |
| uniform_equity_200 | 0.01384237 | 0.00% |

The exact-hand reference has 96 groups per player. Each of the three compressed
methods has 37/36 occupied groups on board 0 and 45/51 on board 1. Thus the two
alternatives have exactly the baseline's occupied capacity per player and case.
Board 0 has 8,432 compatible deals; board 1 has 8,440. Uniform and polarized
regimes keep those same populations but assign different declared weights.

Within their restricted games, the compressed profiles' exploitability was about
0.00016-0.00025 chips at the final checkpoint, compared with full-game values of
0.00445-0.01990 chips. This is consistent with information lost through grouping
being important here. It does not prove the limiting error of continued training.
The exact-hand reference mean was about 0.00016946 chips, not zero.

## Evidence and preservation

All four child processes exited zero, about 6.6 seconds combined wall time.
Each ran all four methods to 10,000 iterations and saved checkpoint policies at
100, 1,000 and 10,000. All 48 method/checkpoint records are present.
Every case manifest and source hash verified. Independent reconstruction used the
unchanged RiverState terminal returns and scalar math.fsum accumulation, instead
of the new compiled payoff matrices. The largest discrepancy across full values,
bounds and individual gains was 8.881784197001252e-16 chips.

The derived analysis contains full and restricted metrics divided by the saved
pot, addressing review M1 for this report. The original driver and its historical
records remain unchanged; the driver schema omission remains a follow-up item.

Durable local milestone:
`D:/Pontius-training/river-abstraction-study/development-001/`.
It contains the bound development plan, four raw result directories, stdout,
stderr, exit receipts, analysis, both orchestration/verification scripts and a
whole-file digest manifest. Creation refused an existing milestone directory.
All checkpoints and non-improvements are preserved. No rolling save was replaced.
There was no measured RSS cap or process-peak claim: population, matrix dimensions,
iteration counts and timeouts were bounded. This is not the formal campaign runner.

## Review disposition

One independent Codex review: specification PASS on material first-gate obligations,
engineering PASS for supported development use, zero Critical, zero Important,
one Minor. Exact report bytes and inventory are preserved under
`river-abstraction-study-reviews/review-01/`. The reviewer disclosed automatically
injected historical memory context. This is an independent review, not a claim of
perfect context isolation. Its inventory preceded tests and it opened no author results.

M1 is accepted: raw bounds/gains were present, but not all pot-normalized fields.
Normalization is explicitly supplied in analysis.json for this development report;
emit those fields consistently in the next report/driver revision. No new review
round is required for that reporting omission alone.

The preserved exact-indifference diagnostic is also accepted as a numerical
limitation: different summation orders can select different CFR trajectories at
zero regret. Evaluation remains the comparison criterion; bit-identical policy
trajectories across platforms are not promised.

## Next decision

Keep the current grouping rules fixed. Before a formal retained or holdout campaign,
freeze a complete multi-case plan consumer and acceptance criteria and bind the
resource envelope. The two declared holdout boards remain unexecuted. A further
development experiment can also test whether narrower groups close the remaining
gap, but changing capacity is a separate comparison and must be labeled as such.
