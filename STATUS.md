# Status

Generated from execution_journal.jsonl.

Recorded runs: 64. Most recent 12 below.

| Recorded (UTC) | Command | Outcome | Seconds | Finding |
|---|---|---|---:|---|
| 2026-09-12T03:14:50.823614+00:00 | PYTHONPATH=$PWD uv run --no-sync pytest -p no:cacheprovider -q (Ubuntu host) | failed | 143.930 | First non-Windows run of the library: 40 passed, 2 skipped (optional SciPy screen), 2 failed; pytest exit 1. Both failures are Windows-only filesystem tests - NTFS junction replacement and open-handle parent pinning - not library defects. All 44 manifest cases collected. |
| 2026-09-08T23:20:21.584370+00:00 | pytest -p no:cacheprovider -q -o pythonpath=. src tests | passed | 69.247 | 552 unittest cases exercised; 11 skipped; pytest exit 0 |
| 2026-09-08T23:18:15.245570+00:00 | pytest -p no:cacheprovider -q | passed | 73.678 | 552 unittest cases exercised; 11 skipped; pytest exit 0 |
| 2026-09-08T23:16:47.520790+00:00 | pytest -p no:cacheprovider -q tests/test_pontius.py::test_behavior[test_legal_river_quotient_cuda_shared_direct_device_v2] | failed | 0.432 | 0 unittest cases exercised; 0 skipped; pytest exit 1 |
| 2026-09-08T23:16:34.732709+00:00 | pytest -p no:cacheprovider -q | failed | 70.726 | 521 unittest cases exercised; 1 skipped; pytest exit 1 |
| 2026-09-08T18:08:38.690579+00:00 | work-folder archive creation and recovery verification | passed | 4.239 | 7,402 files recoverable: 7,309 archived and 93 exact Git duplicates; eight work folders and two handoff files removed; 228 maintained local links resolve; no production changes or experiments |
| 2026-09-08T17:55:56.378222+00:00 | pytest -q -p no:cacheprovider | passed | 86.173 | 552 unittest cases exercised; 10 skipped; pytest exit 0 |
| 2026-09-08T17:53:46.626180+00:00 | pytest -q -p no:cacheprovider | passed | 75.617 | 552 unittest cases exercised; 11 skipped; pytest exit 0 |
| 2026-09-08T17:51:34.300521+00:00 | pytest -p no:cacheprovider -q -k test_legal_river_quotient_shared_direct_artifact_capacity | passed | 0.659 | 10 unittest cases exercised; 0 skipped; pytest exit 0 |
| 2026-09-08T17:50:13.008845+00:00 | pytest -q -p no:cacheprovider -k blueprint_workload_session | passed | 5.984 | 15 unittest cases exercised; 0 skipped; pytest exit 0 |
| 2026-09-08T17:49:45.807071+00:00 | pytest -q -k blueprint_workload_session | failed | 6.237 | 15 unittest cases exercised; 0 skipped; pytest exit 1 |
| 2026-09-08T17:38:19.512083+00:00 | pytest -p no:cacheprovider -q | passed | 81.924 | 541 unittest cases exercised; 10 skipped; pytest exit 0 |
