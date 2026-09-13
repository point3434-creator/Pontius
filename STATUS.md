# Status

Generated from execution_journal.jsonl.

Recorded runs: 80. Most recent 12 below.

| Recorded (UTC) | Command | Outcome | Seconds | Finding |
|---|---|---|---:|---|
| 2026-09-13T06:11:42.783946+00:00 | pytest -q -p no:cacheprovider | failed | 204.528 | 725 unittest cases exercised; 40 skipped; pytest exit 1 |
| 2026-09-13T06:11:10.901943+00:00 | pytest -q -p no:cacheprovider | passed | 425.468 | 734 unittest cases exercised; 0 skipped; pytest exit 0 |
| 2026-09-13T06:01:01.932278+00:00 | pytest -q -p no:cacheprovider | failed | 191.640 | 725 unittest cases exercised; 40 skipped; pytest exit 1 |
| 2026-09-13T04:22:03.396513+00:00 | river-time-quality-001 authorized frozen campaign | complete_approximate_quality_gain | — | Six trajectories and 24 exact audits; cost-qualified quality gains with budget misses retained |
| 2026-09-13T04:07:50.551009+00:00 | river-time-quality-001 build and anchor validation | ready_not_campaign_executed | — | Six selector tests; two retained-policy matches; two independent audits |
| 2026-09-13T03:55:11.791705+00:00 | river-gpu-graph-001 frozen three-arm execution and reset comparison | complete_policy_identical | — | 36 solves, six exact audits; see graph report |
| 2026-09-13T03:39:55.647226+00:00 | river-gpu-execution-001 original gate refusal plus frozen exploratory continuation | complete_exploratory_not_original_plan_pass | — | 12 timing runs; 4 exact audits; unchanged quality; modest GPU speed gain; see report |
| 2026-09-13T03:23:29.782957+00:00 | river-cfr-expanded-001 frozen two-tree four-arm CPU comparison | complete_approximate_solutions | — | 24 training workers and eight independent audits completed on both formerly LP-memory-limited trees; see report for residuals |
| 2026-09-13T03:04:45.400007+00:00 | river-cfr-comparison-002 fixed-parameter second-position confirmation | complete_approximate_solutions | — | 18 workers and six rational audits; DCFR+ leads again; prediction mixed; no strict LP gap pass |
| 2026-09-13T02:55:04.267359+00:00 | river-cfr-comparison-001 frozen six-arm alternating CPU comparison | complete_approximate_solutions | — | 18 workers; six independent rational audits; DCFR+ led one retained board; no arm meets strict LP gap threshold |
| 2026-09-13T01:31:46.797791+00:00 | river-lp-presolve-001 frozen six-worker on/off comparison | capacity_non_improvement | 39.636 | Both expanded trees stopped on memory with presolve on and off; two baseline arms certified |
| 2026-09-13T00:33:38.246552+00:00 | river-lp-memory-001 frozen three-cell diagnostic and trace-only correction | diagnostic_complete_capacity_unchanged | 43.701 | Both deep-stack stops inside native HiGHS run; exact control preserved; original trace-filter miss retained |
