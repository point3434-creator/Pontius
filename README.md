# Pontius

Pontius is a poker bot and a reusable poker research library. The bot supplies a
playable target; game models, solvers, evaluation, abstractions, and codecs let
experiments improve it. Current small-game and reduced-population results do
not establish multiway poker strength.

## Development

Python 3.11 or newer is required. Create a fresh environment with:

```powershell
uv sync --group dev
uv run pytest
```

Do not sync over a GPU environment containing undeclared packages; use a separate
virtual environment for CPU development. The default test manifest is
`tests/cases.json`. One parameterized pytest entry point runs its existing
behavioral unittest suites, preserving their assertions and fixtures.
To focus a suite, use `uv run pytest -k blueprint_preparation`.
Other retained research suites can be run explicitly with, for example:

```powershell
$env:PYTHONPATH = "src"
python -m unittest discover -s tests -p test_occupied_card_quotient.py
```

The CPU suites exercise game rules, CFR, evaluation, resolving, blueprint codecs,
providers, runtime clocks, and replay/trace behavior. GPU checks require their
own CUDA environment and are not silently counted as passing CPU coverage.

## Where work belongs

- `src/pontius/`: reusable game, solver, runtime, and codec code. New experiment
  orchestration does not belong in the library. Existing one-off code is being
  removed after its findings are harvested.
- `tools/`: user-facing bot, evaluation, and benchmark entry points.
- `experiments/`: one dated script per research question, importing the library
  and never imported by it. Code needed by two experiments graduates into the
  library with a test.
- [Experiment results](experiments/RESULTS.md): the short research index links
  seven maintained categories, their conclusions, limitations, and evidence.
  [Brainstorming](experiments/brainstorming.md) preserves external ideas and
  corrections; the [research roadmap](experiments/research-roadmap.md) connects
  them to evidence and ranks the next useful experiments.
  The long historical ledger is archived. Git history preserves deleted code;
  raw measurements need separate retention.
- `execution_journal.jsonl`: one outcome line per run or benchmark.
- `STATUS.md`: generated from the journal, using
  `python -m pontius.status_generation` with `PYTHONPATH=src`.
- `docs/archive/`: historical ADRs and root documentation. These are references,
  not current instructions or prerequisites for development.

The maintained bot entry points are `tools/v0a_table_host.py` and
`tools/v0a_table_session.py`. They verify the source once and share that identity
with hand processes. Use `--reviewed-commit SHA` for reviewed execution; the
current HEAD is the default. `--development` permits a dirty checkout and records
it as unreviewed. Source comparison accounts for Git text newline conversion;
the journal also records the hash of the actual source bytes. The recorded
scope includes source, tools, tests and fixtures, CI, dependency files, and Git
text attributes; archived documents and retained run outputs are excluded.

The blueprint benchmark reuses an existing `population.json`, `plan.json`, and
their referenced artifacts. For a focused check:

```powershell
python -B -P tools/v0a_blueprint_workload.py run --development `
  --population-root D:/bww515/as-is-run-001 `
  --kinds construction --sizes 883 --cells 3 --seconds 60
```

Adjust the population directory to your retained corpus. One worker runs all
selected cells for the invoking Python runtime. The controller checks HEAD and
the selected inputs before each nonce-bound grant, without per-cell files.
Memory is limited for the whole worker job from suspended launch. Job memory
peaks accumulate across cells; traced allocation measurements remain scoped to
the measured operation. Each run writes `runtimes.json` and a final `result.json`
under `experiments/results/runs/`, then one journal line. Historical benchmark
artifacts remain readable with `read --result LEGACY_RUN_DIRECTORY`.

Historical experiment orchestration still embedded in the library and
paired-evaluation wrappers needs further cleanup. The root research launchers
have been retired; use the maintained commands in `tools/`. The CPU suites
exercise the reusable evaluation library. Passing model tests is not a new
full-matrix or GPU benchmark result.
Historical evaluation preparation and run-coordination scripts are preserved
in [the helper archive](docs/archive/root-helpers/); they are reference material,
not maintained commands. Their relocation and recovery limits are recorded in
the results index.

## Working rules

The goal is a working poker bot supported by reusable research capabilities.
Everything in this repository is judged by whether it serves that.

1. Verify once, at boundaries: hash source against the reviewed commit at run
   start and outputs at run end. No cell, iteration, or call gets a separate
   seal, admission, or verification write. Lightweight per-cell HEAD/input
   reads and nonce/grant messages are permitted; they create no verification files.
2. Delete unused versioned, seal, and result companions rather than combining
   them into a new pattern. Preserve each one-off finding first; Git history
   and its commit SHA are the code archive. Keep live bot dependencies and
   reusable research capabilities with a test and a caller or a one-line
   capability entry.
3. Explain the reason before adding any file, abstraction, config schema, or
   process document. Ask when the need is uncertain.
4. Use one parameterized pytest harness and a small data manifest. Do not
   regenerate test inventories or enforce ADR freshness.
5. Record each run or benchmark once in `execution_journal.jsonl`. Before
   finishing work that changes evidence or interpretation, update the relevant
   family summary: conclusion, population, measurement scope, limitations,
   source/run references, and review date. Keep failures and later corrections
   distinct. A confirming run can add a brief evidence note without repeating
   the narrative. Update the results index only when the category conclusion,
   priority, or coverage changes. Source changes that invalidate an old claim
   must mark it historical or pending remeasurement. Update brainstorming and
   roadmap entries when findings resolve an idea or change priorities; keep
   external proposals distinct from measured results. STATUS stays generated
   from the journal. ADRs are for structural changes only, at most one per week
   without asking; archived ADRs are not required reading.
6. Keep one README under three pages and one journal-generated STATUS at the
   root. Archive other root documents.
7. Measure before optimizing: no performance-driven format, library, or
   code-path change without a number showing it matters.
8. Prefer readable code: plain names, no one-letter variables outside loops,
   and no long chained `require` conditions.
