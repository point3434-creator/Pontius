# Status

Generated from execution_journal.jsonl.

Recorded runs: 69. Most recent 12 below.

| Recorded (UTC) | Command | Outcome | Seconds | Finding |
|---|---|---|---:|---|
| 2026-09-12T20:25:24.912382+00:00 | pytest -p no:cacheprovider -q | passed | 92.680 | 585 unittest cases exercised; 10 skipped; pytest exit 0 |
| 2026-09-12T20:04:35.746164+00:00 | pytest -p no:cacheprovider -q -k sampled_cfr or early_holdem or training_checkpoint or test_cfr or test_kuhn or test_updates or test_evaluation or test_holdem_cards or test_no_limit_betting | passed | 15.537 | 95 unittest cases exercised; 0 skipped; pytest exit 0 |
| 2026-09-12T20:01:07.463762+00:00 | experiments/2026-09-12-early-blueprint.py --iterations 2 --evaluation-deals 2 --max-nodes 1 --seconds-per-cell 10 | passed | 0.889 | Four bounded early-street training cells; checkpoint round trips and serial resumes matched; sparse-coverage paired evaluation, no poker-strength claim. |
| 2026-09-12T19:59:29.924878+00:00 | experiments/2026-09-12-early-blueprint.py --iterations 100 --evaluation-deals 32 --max-rows 20000 --max-nodes 100000 --seconds-per-cell 60 | passed | 20.132 | Four bounded early-street training cells; checkpoint round trips and serial resumes matched; sparse-coverage paired evaluation, no poker-strength claim. |
| 2026-09-12T19:57:10.052407+00:00 | pytest -p no:cacheprovider -q -k sampled_cfr or early_holdem or training_checkpoint or test_cfr or test_kuhn or test_updates or test_evaluation or test_holdem_cards or test_no_limit_betting | passed | 18.783 | 94 unittest cases exercised; 0 skipped; pytest exit 0 |
| 2026-09-12T03:14:50.823614+00:00 | PYTHONPATH=$PWD uv run --no-sync pytest -p no:cacheprovider -q (Ubuntu host) | failed | 143.930 | First non-Windows run of the library: 40 passed, 2 skipped (optional SciPy screen), 2 failed; pytest exit 1. Both failures are Windows-only filesystem tests - NTFS junction replacement and open-handle parent pinning - not library defects. All 44 manifest cases collected. |
| 2026-09-08T23:20:21.584370+00:00 | pytest -p no:cacheprovider -q -o pythonpath=. src tests | passed | 69.247 | 552 unittest cases exercised; 11 skipped; pytest exit 0 |
| 2026-09-08T23:18:15.245570+00:00 | pytest -p no:cacheprovider -q | passed | 73.678 | 552 unittest cases exercised; 11 skipped; pytest exit 0 |
| 2026-09-08T23:16:47.520790+00:00 | pytest -p no:cacheprovider -q tests/test_pontius.py::test_behavior[test_legal_river_quotient_cuda_shared_direct_device_v2] | failed | 0.432 | 0 unittest cases exercised; 0 skipped; pytest exit 1 |
| 2026-09-08T23:16:34.732709+00:00 | pytest -p no:cacheprovider -q | failed | 70.726 | 521 unittest cases exercised; 1 skipped; pytest exit 1 |
| 2026-09-08T18:08:38.690579+00:00 | work-folder archive creation and recovery verification | passed | 4.239 | 7,402 files recoverable: 7,309 archived and 93 exact Git duplicates; eight work folders and two handoff files removed; 228 maintained local links resolve; no production changes or experiments |
| 2026-09-08T17:55:56.378222+00:00 | pytest -q -p no:cacheprovider | passed | 86.173 | 552 unittest cases exercised; 10 skipped; pytest exit 0 |
