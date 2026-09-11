# River abstraction research

The current checkpoint is development-001, a completed local development trial.
It covers four fixed heads-up one-bet river cases; neither holdout board was run.
One independent review passed the material first-gate specification and engineering
checks, with one Minor reporting omission. No six-max strength claim follows.

- [Design](river-abstraction-study.md)
- [Results and review disposition](river-abstraction-study-development-001.md)
- [Independent review](river-abstraction-study-reviews/review-01/report.md)
- [Saved trial and all checkpoint policies](../../experiments/river-abstraction-study/development-001/)
- [Verified analysis](../../experiments/river-abstraction-study/development-001/analysis.json)
- [Archive digest manifest](../../experiments/river-abstraction-study/development-001/milestone-manifest.json)

At 10,000 iterations, equal-weight mean exploitability was 0.01384237 chips for
the existing bins, 0.00812444 for range-equity grouping, and 0.00703332 for richer
range-response grouping. The richer features reduced this metric by 49.19% versus
baseline across these cases at equal occupied bucket capacity. Range-equity-only
grouping beat the richer features in one of the four cases. Pot size is 10 chips.

All 48 checkpoint profiles were checked against the original game's terminal
returns. The complete local archive is copied here byte-for-byte. Absolute paths
inside historical receipts describe the original execution machine; the relative
links above locate the published copies. Historical uncommitted/pending-review
status statements remain unchanged to preserve their evidence hashes.

Use Python 3.14.6. The reusable source driver is tools/river_abstraction_study.py.
Archived orchestration and verification scripts retain their original absolute
paths as evidence; review and adapt paths before any new invocation. No archival
script should be interpreted as fresh authorization to rerun an experiment.
