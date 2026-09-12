# River abstraction research

The latest completed checkpoint is holdout-001: the unchanged four methods were
tested on the two previously reserved boards, each under uniform/polarized ranges.
All 48 profiles were retained and verified. At 10,000 iterations, range-response
grouping reduced equal-weight mean exploitability by 15.39% versus uniform-equity
bins and 2.17% versus range-equity grouping. Both comparisons are mixed across
cases (three wins, one loss). These are conditional heads-up river-game results.

- [Holdout results and interpretation](river-abstraction-holdout-001.md)
- [Holdout milestone](../../experiments/river-abstraction-study/holdout-001/)
- [Fixed holdout design](river-abstraction-holdout.md)
- [Reviewed r002 disposition](river-abstraction-holdout-r002/disposition.md)
- [Passing focused recheck](river-abstraction-holdout-r002/reviews/recheck-02.md)
- [Original study design](river-abstraction-study.md)
- [Development results and disposition](river-abstraction-study-development-001.md)
- [Development milestone](../../experiments/river-abstraction-study/development-001/)
- [Original independent review](river-abstraction-study-reviews/review-01/report.md)

The original development archive remains unchanged. Development's 49.19% mean
reduction did not carry over in magnitude; the holdout result is positive on
average but case-dependent. No six-max playing-strength claim follows.

Use Python 3.14.6. Absolute paths in retained scripts/receipts identify the original
execution machine. Historical pending-review/uninvoked statements preserve their
original evidence context. The r001 holdout plan is superseded; r002 was invoked
once and its output directory cannot be reused. Archival scripts and approval
records do not authorize another run. Publication remains a separate action.

## Prepared fixed-group diagnostic

The next diagnostic is built and independently reviewed, but has not executed.
It measures the best strategy each frozen grouping can represent against full-hand
responses, then compares that bound with all 96 saved development/holdout profiles.

- [Mathematical and execution contract](river-group-optimality.md)
- [Passing disposition](river-group-optimality-r001/disposition.md)
- [Independent review](river-group-optimality-r001/reviews/review-01/report.md)
- [Bound execution request](river-group-optimality-r001/execution-request.md)

This adds an optional SciPy research test suite. Run it explicitly using the pinned
Python 3.14.6 / NumPy 2.5.2 / SciPy 1.18.0 environment described in the specification.
The default registry skips this optional suite when Python 3.14.6 or SciPy is absent;
the retained explicit author run exercised all 75 selected tests with zero skips.

## Fixed-group diagnostic completed

[Group-optimality-001](river-group-optimality-001.md) records the single approved
run: eight observed cases, 32 certified grouping floors and 96 saved profiles.
It separates grouping restrictions from the remaining policy gap.

## Witness-action-value grouping candidate

[Design](river-witness-groups.md) and
[reviewed packet](river-witness-groups-r001/disposition.md) define one
fixed-capacity, oracle-assisted development screen. Execution awaits approval.

## Witness-action-value development result

[Witness-groups-development-001](river-witness-groups-development-001.md) records
the completed four-case, fixed-capacity screen and its certified comparisons.
The mean floor improved against both range-based controls, with one worse case.

## Fresh-board witness grouping pilot

[Design](river-witness-pilot.md) and
[reviewed packet](river-witness-pilot-r001/disposition.md) fix eight fresh
boards, three hand pools and two range regimes before scoring. The 48-case
pilot reports board and pool sensitivity; execution awaits separate approval.

## Fresh-board witness grouping pilot result

[Witness-pilot-001](river-witness-pilot-001.md) records
the completed 48-case pilot and its certified board/pool comparisons.
All eight boards, three pools and both range regimes are retained.
