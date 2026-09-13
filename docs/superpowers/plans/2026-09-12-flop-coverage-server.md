# Flop coverage server experiment implementation plan

> **For agentic workers:** Use superpowers:subagent-driven-development for the independent trainer component and independent review. Keep one implementation subagent active at a time; the coordinator owns experiment integration and deployment.

**Goal:** Implement, verify and launch the agreed four-arm coverage experiment on the user's Ubuntu server.

**Architecture:** Extend the serial reference with independent averaging streams and a versioned structural flop encoder. A dated experiment controller runs bounded child processes, creates fixed panels before training, retains immutable checkpoints, and reports paired coverage and play measurements. A Linux service supplies a cgroup and a hard outer deadline.

**Tech stack:** CPython 3.14, existing standard-library simulator/checkpoint tools, pytest behavioral harness, Ubuntu systemd and cgroup v2.

**Spec:** `docs/flop-coverage-design.md` (approved through the user's request to run this test; original user-facing copy retained in the task's outputs directory).

## Global constraints

- Six dealt players, equal 100bb stacks, no rake, one aggression per early street including the opening bet.
- Ordinary frozen-policy external-sampling CFR; check/call training continuation; no turn/river tables.
- A/B exact flop keys, C/D diagnostic structural groups; A/C use R=1, B/D use R=8.
- Independent deterministic regret and per-player averaging RNG streams, all persisted. Contributions have weight 1/R. Average sampling cannot alter regret trajectories before capacity differences.
- Keep 169 preflop class, full betting history, actor and public ledger. Never expose hidden or future cards in keys.
- Main seeds 1101,1102,1103; calibration 1001; coverage 2101; play 3101. All fresh identities/runs.
- Target 5,000 iterations; milestones 0,100,1000,5000 plus stopping point; 500,000 rows; 100,000 nodes per whole iteration.
- Per-cell 20 minutes including saves, then at most 30 seconds graceful shutdown; 12 GiB soft memory, 16 GiB hard cgroup; 50 GiB run disk; 100 GiB free before launch; 6 hours total including evaluation, with 45 minutes reserved for final play evaluation.
- Panels use 2000 deal blocks per declared profile; all six seat rotations remain in their paired blocks. Partial evaluation yields no strength verdict.
- Preserve existing pilot, user edits to STATUS.md and execution_journal.jsonl, and all significant milestones. Do not add training artifacts to Git.

## Task 1: Independent averaging and structural grouping

Files: `src/pontius/sampled_cfr.py`, `src/pontius/early_holdem.py`, and their existing behavioral test files.

Interfaces:

```python
ExternalSamplingCFR(..., averaging_trajectories: int = 1)
EarlyHoldemGame(..., flop_representation: str = "exact")  # or "structural"
structural_flop(hole, board) -> tuple[int, int, int]
# RegretRow retains average_visits as distinct completed averaging iterations.
# Add average_samples, average_regret_samples, regret_visits integer counters.
# Trainer exposes total_regret_nodes and total_average_nodes.
```

- [ ] Add a failing same-seed comparison proving the absent R argument. Verify A/B and C/D regrets, regret visits and regret RNG match through common iterations; average-only rows are excluded.
- [ ] Add a literal one-decision averaging fixture: eight trajectories contribute total weight 1, sample count 8, distinct iteration count 1. Add rollback, resume and malformed counter/RNG cases.
- [ ] Implement validated R, stable SHA-256 seed domains, per-player average RNGs, aggregated contributions, atomic counter/RNG rollback and a v2 identity/state format. Reject v1 trainer resumes explicitly; keep generic checkpoint reading unchanged.
- [ ] Add key tests: all suit permutations agree; same starting class/top-pair and bottom-pair examples merge when their declared structural tuple matches; different preflop classes/history do not merge; opponent/future-card mutations do not affect the key.
- [ ] Implement structural tuple (nine made categories, four maximum-suit-multiplicity states, four straight-completion states with wheel support), preserving exact mode by default and versioning the game identity.
- [ ] Run `python -m pytest -p no:cacheprovider -q -k 'sampled_cfr or early_holdem or training_checkpoint'`; record failure-before-change and fresh passing results. Review this component before integration is declared complete.

## Task 2: Bounded experiment and evidence

Files: new `experiments/2026-09-12-flop-coverage.py`, new `tests/test_flop_coverage_experiment.py`, and `tests/cases.json`.

Interfaces: the dated script supports `run --run-directory PATH`, `cell`, `calibrate`, `resume-check`, and `evaluate` child modes. Test mode has separately recorded reduced limits; production defaults remain the spec.

- [ ] First write behavioral tests exercising a tiny real four-cell subprocess run and a resumed completed run. Assert four unique configuration identities, immutable checkpoint bytes, fixed panel identity and incomplete/failure classification. Add bootstrap block and resource-cap cases with literal results.
- [ ] Create immutable hashed panel files before training. Coverage observations retain deal and public history, actor, profile and deal-block ID; query all arms identically and stratify live-player count.
- [ ] Add independent cell processes with persisted start/deadline and progress records. Monitor process-group memory on Linux; enforce disk and wall limits, record reasons, retain valid checkpoints after interruption, and forbid new writes to old milestones.
- [ ] Collect coverage per milestone and row ownership/sample diagnostics, policy movement, CPU/wall/RSS and checkpoint save/load timing. Persist policy exports without building all historical policies in memory.
- [ ] Run calibration regret equivalence and exact small-game oracles. Exercise actual interrupted writers at staging and after synchronized publication in disposable roots. Compare original live trainer with a separately restored process for 100 continuation steps for each first-seed arm.
- [ ] Evaluate B/C/D minus A at the latest common checkpoint with paired deal blocks across six seats, both opponent profiles and both continuation policies; bootstrap whole block means. Store every raw paired return and fallback count, and all partial outcomes.
- [ ] Apply the fixed 5-point/2-of-3-seeds engineering gate, preserve all third-seed and live-count outcomes, and issue no automatic production promotion or broad strength claim.
- [ ] Verify the tiny end-to-end command and targeted behavioral suites; review the integrated diff against every spec section.

## Task 3: Linux launch and handoff

Files: `tools/run_flop_coverage_server.py`, `docs/early-blueprint-linux.md`, relevant experiment-family summary.

- [ ] Add a Linux launcher which checks Python version, source identity, free disk and cgroup-v2/systemd support, creates a unique run/service, and refuses duplicate or incompatible resumes.
- [ ] Keep the job independent of SSH disconnects. Install a narrowly scoped named systemd unit with MemoryMax=16G, MemorySwapMax=0, bounded restart policy, and the fixed persisted experiment deadline; enable restart after reboot only for this authorized job and stop rerunning once it is terminal.
- [ ] Test launcher argument validation and generated invocation through real subprocess validation; record Linux-only checks separately from Windows checks.
- [ ] Run the full behavioral harness and relevant formatting checks. Review exact changes; commit/push the verified source using existing shared-Git authorization and the requested server-run scope. Wait for CI and verify the remote commit.
- [ ] Fast-forward the server checkout while preserving its generated journal/status edits, run focused Linux checks, run a tiny rehearsal, then start the requested main job. Verify service state, run identity, settings and first progress output.
- [ ] Return service/run paths and simple status/result commands, with implemented/tested/launched facts separated.
