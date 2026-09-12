# Focused opposing review: fresh-board witness pilot r001

No material findings. Specification verdict: PASS for the frozen pre-execution review contract. Engineering verdict: PASS for that same bounded scope. These verdicts do not authorize execution or establish pilot outcomes, runtime feasibility, generalization, or playing strength.

## Identity and seal

Target checkout: D:/Pontius-worktrees/eval-runner-consolidation.
HEAD: 1b4d1a0e26cd4da90ff74678de2e48ef53ec5599.
Branch: codex/river-abstraction-holdout.
Plan SHA-256: 535a3fa5b4d55d8bc6cc29763c63b5ab41f89cf0ea190bca90f9c00a5a8c9d2c.
Identity SHA-256: baa5a07f7a9eb705ed6366bd1ff618e6d68b92908e03c11abde72a7554fee2aa.
Freeze-manifest SHA-256: 524f1c8ad8270dc27e26617d7bc72f650e8686b1b2a42e3badd1d5bbe8d359d8.
Inventory: D:/Pontius/tmp/witness-pilot-review-01/inventory.md.
Inventory SHA-256: b6cb466b6aec3bfe36a47ee05186cf53f01e024d37f130d4cb0fd892c97064a3.

All seven candidate/plan/metadata pins, all 17 freeze-manifest members and all 12 plan source pins matched both at initial inspection and final verification. final-pins.json records the final expected and actual hashes, with zero mismatches. HEAD remained unchanged. The inventory was recorded and hashed before opening checks content; checks were hash-read only during initial freeze verification. The inventory remained unchanged at completion.

## Requirement-to-evidence assessment

| Inventory | Result and evidence |
|---|---|
| R1 frozen identity and environment | PASS. Initial/final hashes and Git identity match. Executed Python is 3.14.6, NumPy 2.5.2, SciPy 1.18.0. README bytes match predecessor; .gitattributes preserves predecessor bytes as a prefix plus exactly three pilot entries. Removing the single added CRLF test_river_witness_pilot registration from tests/cases.json reproduces all predecessor bytes. An initial same-index list comparison was inappropriate because the new registration is inserted at position 16; direct insertion removal resolves it. |
| R2 selection | PASS. Independent implementation of the written hash/texture/suit recipe selects exactly the frozen eight boards; final acceptance is attempt 21. Source dataflow selects using card/rank/suit data only. Existing tests check all 24 suit permutations and exclude all four old suit classes. No equity, grouping or solver result influences selection. |
| R3 hand pools | PASS. Independent hash reconstruction matches all 48 board/pool/seat selections, each 96 distinct holdings drawn from 1081 board-legal holdings. The pool recipe omits regime and includes board/replicate/seat. Existing tests and source checks establish reproducibility, legality, distinct seeded draws, and regime sharing. Pool overlap is allowed by specification. |
| R4 inherited game and representation | PASS. Source trace confirms pot 10, bet 5, stacks 20/20, unchanged exact PayoffGame construction and controls. Polarization uses inclusive <=.2 or >=.8 thresholds with weight four. Joint construction rejects shared cards, and the matrix shape check rejects loss of a selected holding's compatible support. Inherited anchored_clusters retains its weighted farthest-first initialization, tie behavior, twenty updates, and occupied anchors. |
| R5 witness generation/capacity | PASS. solve_record produces four control solutions, then the candidate; each solve_groups performs two asymmetric solves, hence ten LP calls per case / 480 in the bound grid. No retained result archive is read. propose uses the required seat0.call or seat1.bet witness in fixed control order, verifies bank certificates, and matches compressed capacity separately per seat to uniform_equity_200. Synthetic tests cover feature signs, reach weighting, degenerate features, exact occupied counts and capacity rejection. |
| R6 parent reconstruction | PASS. Parent rebuilds ranges, exact game, hand order, joint masses, provenance and controls from the bound case. Canonical comparison rejects altered inputs; inherited propose rechecks all control certificates and regenerates features/groups; verify_candidate reconstructs candidate certificates and all signed comparisons. Existing two-hand test executes parent verification with linprog explicitly forbidden. Synthetic certificate tests compare Fraction bounds to enumerated pure responses and known restriction costs. |
| R7 descriptive aggregation | PASS. Bound-plan admission independently recreates all 48 case descriptors; summarize rejects missing, duplicate or reordered rows. Independent synthetic data varies regime, pool and board effects and verifies overall candidate/control floors, board means, pool SD=.1, board SD=sqrt(6), regime/texture breakdowns, worst-case identity, and all leave-one-board-out means. Rational interval means preserve the balanced board/case identity. Source retains all per-case intervals and lower/higher/overlapping counts. The generic summary helper supports the separately admitted one-case smoke; the bound pilot cannot admit that reduced panel. |
| R8 execution limits | PASS by source/plan inspection and permitted subprocess smoke. One sequential worker; inherited helper sets all three declared BLAS thread variables to one before NumPy import in the driver. Each solve_seat uses five seconds and 10000 iterations. Worker timeout is 1200 seconds, with witness generation included. Cache keys are board tuples in separate worker/parent caches. Parent reconstruction remains explicitly outside timeout. No performance or RSS claim is inferred. |
| R9 evidence/failure completion | PASS. The real old-board two-hand subprocess test produces a summary and manifest; repeat output reservation is rejected. Existing tests exercise worker failure, timeout, missing result, parent rejection, summary-write error and manifest-write error. Success returns only after parent reconstruction, source rebinding, summary and manifest writing; exceptions propagate and attempt failed.json preservation. No retries occur. A write fault can leave partial bytes, which are not a valid completion manifest; successful parent exit remains independently required. |
| R10 claims/authority | PASS. Specification and summary explicitly identify a balanced, oracle-assisted descriptive pilot with eight board units, related pool/regime observations, sample SDs rather than standard errors, no natural-play weights or all-board inference, and no six-max/BB100/equal-compute claim. Separate one-shot controller authorization is required. |

## Fresh execution evidence

Every Python command used D:/Pontius/tmp/group-opt-author/venv/Scripts/python.exe with -B -W error::ResourceWarning. PYTHONDONTWRITEBYTECODE=1 and PYTHONWARNINGS=error::ResourceWarning were set, including for children; TEMP and TMP pointed exclusively to the assigned scratch directory. No dependencies were installed.

1. python -B -W error::ResourceWarning -m pytest -p no:cacheprovider tests/test_river_witness_pilot.py --junitxml=D:/Pontius/tmp/witness-pilot-review-01/pilot-tests.xml -q
   Result: exit 0, eight passed, zero skipped, 6.75 seconds. The initial sandbox attempt could not start the interpreter (Access is denied); the same authorized command ran successfully after tool escalation. This was an environment startup restriction, not a test failure or pilot retry.
2. python -B -W error::ResourceWarning D:/Pontius/tmp/witness-pilot-review-01/independent_checks.py
   Result: exit 0. Independent selection-only reconstruction and synthetic aggregation assertions passed. Python/package versions match the pins. This script never calls fresh-board equity construction, fresh grouping or any LP.
3. python -B -W error::ResourceWarning -m pytest -p no:cacheprovider tests/test_river_witness_groups.py::WitnessGroupsTests tests/test_river_group_optimality.py::OptimalityTests --junitxml=D:/Pontius/tmp/witness-pilot-review-01/dependency-tests.xml -q
   Result: exit 0, 13 passed, zero skipped, .96 seconds. These selected classes operate only on hand-derived synthetic games.
4. python -B -W error::ResourceWarning -m ruff check --no-cache src/pontius/river_witness_pilot.py tools/river_witness_pilot.py tests/test_river_witness_pilot.py
   Result: exit 0, all checks passed.

The author receipt and XML counts were consulted only after inventory sealing. They report five initial missing-module failures, then five green core tests; three missing-driver failures with five passing core tests, then eight green tests; a 95-test green verification run. These are historical author evidence, not substituted for the fresh 21-test reviewer execution above.

## Findings, falsifiers, and limits

There are no actionable findings and no documentation advisory requiring another review round. Therefore there is no finding-specific reachable falsifier to report. Review acceptance remains directly falsifiable by a pin mismatch, different selection under the declared recipe, acceptance of an altered/missing case, acceptance of a corrupt certificate/group/feature, incorrect synthetic board/pool aggregation, or successful return after an evidence-write failure; the relevant permitted checks above passed.

The full 48-case 96-hand workload was intentionally not invoked. No fresh-board equity, feature, grouping, or LP was evaluated. This review does not establish whether all actual pilot cases will certify within the stop bounds, how long parent verification will take, actual memory use, or the sign/size of any result. Those are execution evidence, not grounds to bypass the review's explicit no-scoring boundary. The inherited card evaluator was source-traced where consumed but not independently reimplemented. Historical result archives and their preservation hashes were not independently checked because the handoff prohibited opening them. Hard kills, power loss and hostile concurrent mutation remain the declared exclusions.

## Context and action disclosure

The subagent received the focused dispatch and general injected session/system/developer context, including the provided memory summary about unrelated prior six-max work and governance. No memory file was opened or used as evidence. No earlier review, disposition, progress.md, INDEX.md, conversation transcript, prior result archive, unrelated scratch directory or other reviewer's inventory was opened. Git status exposed only names of other existing modifications/untracked artifacts. The author's receipt necessarily exposed historical archive hash metadata after sealing; the archives themselves were not accessed. A later parent message requested a progress update and reinforced the no-fresh-scoring boundary; it supplied no conclusion or finding.

I used the code-verification skill and its verification-matrix reference. The using-superpowers skill explicitly exempts dispatched subagents. No fan-out occurred. No source/metadata change, ledger write, commit, push, adoption, bound pilot invocation or authorization file was made. All reviewer writes are under D:/Pontius/tmp/witness-pilot-review-01. Report and inventory hashes are retained in seals.json.
