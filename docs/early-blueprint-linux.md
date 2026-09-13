# Run the early-street blueprint reference on Ubuntu

GitHub shares code between the Windows and Linux computers. Pushing uploads a
version of the code; cloning downloads a separate copy; running starts the
program on the computer whose terminal you are using. A push does not start
training automatically.

The branch is `codex/early-street-blueprint` in
`https://github.com/point3434-creator/Pontius.git`.

Use these commands in a terminal **on the Ubuntu machine**, either directly or
inside an SSH connection to it. Run one step at a time. If a command reports an
error, stop there and keep the error text so it can be diagnosed.

## 1. Check the tools

```bash
git --version
uv --version
```

If both print a version, continue to step 2. If Git or curl is missing:

```bash
sudo apt update
sudo apt install git curl
```

If uv is missing, use its official installer and make it available in this terminal:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH="$HOME/.local/bin:$PATH"
uv --version
```

This is the [official uv installation method](https://docs.astral.sh/uv/getting-started/installation/).
The next steps install Python and the project's packages in a separate environment.

## 2. Download a separate blueprint copy

In the directory where you keep projects:

```bash
git clone --branch codex/early-street-blueprint https://github.com/point3434-creator/Pontius.git Pontius-blueprint
```

Once cloning finishes successfully:

```bash
cd Pontius-blueprint
git branch --show-current
```

The last command should print `codex/early-street-blueprint`. This creates a
separate folder from an existing `Pontius` checkout. If `Pontius-blueprint`
already exists, inspect it before repeating the clone; do not delete its results.
If GitHub reports an authentication error, use the access already set up on this
machine or ask for help with that error. Do not paste tokens into chat.

## 3. Install the matching Python environment

From inside `Pontius-blueprint`:

```bash
uv sync --locked --group dev --python 3.14.6
uv run --no-sync python --version
```

The version should be `3.14.6`. uv uses `uv.lock` to install matching packages
in this copy's `.venv` folder, separate from the operating system's Python and
other project copies. [uv project documentation](https://docs.astral.sh/uv/guides/projects/)

## 4. Run the blueprint tests

```bash
uv run --no-sync pytest -p no:cacheprovider -q -k 'sampled_cfr or early_holdem or training_checkpoint'
```

This selects four suites covering sampled updates, the poker adapter,
checkpoints and interrupted-writer recovery. Successful output ends in `4 passed`
plus the number of unselected suites. Resolve any failure before training.

For the complete repository's CPU manifest:

```bash
uv run --no-sync pytest -p no:cacheprovider -q
```

Optional tests may be skipped when their extra dependency is absent; `FAILED`
or `ERROR` is different from a declared skip.

## 5. Run the small training experiment

After the tests pass:

```bash
PYTHONPATH=src uv run --no-sync python experiments/2026-09-12-early-blueprint.py --iterations 100 --evaluation-deals 32 --max-rows 20000 --max-nodes 100000 --seconds-per-cell 60
```

Keep the terminal open while this runs. It finishes by itself. Four small cells
at 100bb compare ordinary and linearly weighted sampled CFR with two simple
later-street continuation policies. It retains checkpoints at iterations 0, 50
and 100, checks restart equivalence, and records a small paired evaluation. The
60-second limit is checked between training iterations in each cell; evaluation
and saving take additional time.

The last output line starts `Result:` and gives the path to `result.json`.
New data is under `experiments/results/runs/<new-run-name>/`. Each cell contains
`generations/milestone-.../checkpoint.json` and a `policy.json` export. Keep the
full run directory. One outcome is also recorded in `execution_journal.jsonl`,
and `STATUS.md` is refreshed.

This is a bounded reference experiment with a small action menu and simple
continuations. It trains no turn/river strategy tables. The Windows pilot did
not establish poker strength or useful general flop coverage. Larger runs need
an abstraction/continuation decision and measured memory limits first. This
command does not install an automatic restart service or start a weeks-long job.

## Next test: supervised four-arm flop coverage

The [next experiment design](flop-coverage-design.md) crosses exact versus
diagnostic structural flop keys with one versus eight averaging trajectories per
player. All arms use ordinary sampled CFR, equal 100bb stacks and a frozen
check/call continuation. Three independent training seeds give 12 sequential
cells. These coarse groups are diagnostic controls, not production buckets.

This uses a new trainer/game identity and independent RNG streams. The older
v1 pilot remains historical evidence. Its checkpoints require the original
trainer at commit `de513a4bd10a1553e023d9ceb492bd213c7ca837` for continuation;
the new experiment starts fresh and explicitly rejects incompatible resumes.

After the reviewed source is installed and its CI is green, verify the affected
suites with the existing environment (no environment rebuild is needed):

```bash
.venv/bin/python -m pytest -p no:cacheprovider -q -k 'sampled_cfr or early_holdem or training_checkpoint or flop_coverage'
```

The short rehearsal uses the same controller with reduced counts. Give every
new run a different directory:

```bash
PYTHONPATH=src .venv/bin/python experiments/2026-09-12-flop-coverage.py run --profile smoke --run-directory experiments/results/runs/coverage-smoke-001
```

The full run needs root, Linux cgroup v2, systemd, at least 100 GiB free disk,
and the intended CPython 3.14 virtual environment. From the verified checkout,
the launcher below creates a new persistent service. Choose a unique run name.
The SHA supplied is the exact reviewed checkout, which the launcher verifies:

```bash
.venv/bin/python tools/run_flop_coverage_server.py --run-name coverage-001 --reviewed-commit "$(git rev-parse HEAD)"
```

Add `--print-unit` to inspect the unit without installing or starting it. The
actual install validates the unit with systemd before enabling it. It refuses
existing run/service names, unreviewed source edits and a competing active job.

For the example name above, these commands show progress and the retained result:

```bash
systemctl status pontius-flop-coverage-coverage-001.service --no-pager
journalctl -u pontius-flop-coverage-coverage-001.service -n 30 --no-pager
cat experiments/results/runs/coverage-001/progress.json
cat experiments/results/runs/coverage-001/result.json
```

`result.json` appears when the controller finishes; `progress.json` appears
after completed cells. Earlier work is visible in the service log and in
`jobs/calibrate.log` or `cells/<arm>-<seed>/progress.json` inside the run directory.
An SSH disconnect does not stop the service. Its installed unit starts again
after reboot; the controller retains the original deadline and resumes its
checkpoints. A terminal run exits without retraining. Bounded restart attempts
can leave the service failed after repeated abnormal exits; inspect its logs.

The limits are 5,000 iterations and 500,000 rows per cell, 20 minutes per cell
including checkpoint work, a 12 GiB graceful memory stop and 16 GiB hard memory
ceiling for the service, no swap, a 50 GiB experiment file budget, and six hours
overall with time reserved for evaluation. Shutdown has a 30-second grace
period. Timing after an unexpected process restart is marked incomplete where
lost CPU measurements cannot be reconstructed; wall time still includes downtime.

Milestones at 0, 100, 1,000, 5,000 and a capacity stopping point are immutable.
The run also retains fixed panel hashes, policy exports, resource logs, paired
deal-block returns and software interruption checks. Status `capped` is a
resource or incomplete-evaluation result. Status `failed` requires inspection.
Even status `passed` means the declared experiment completed; it does not
establish general poker strength, a six-player equilibrium or physical SSD
power-cut durability. Keep the entire run directory; Git does not copy it.

To stop this job deliberately:

```bash
systemctl stop pontius-flop-coverage-coverage-001.service
```

The controller attempts to close its current worker and retain a result. This
is a terminal stop, rather than a pause intended to obtain a fresh time budget.
To prevent this service from being invoked on subsequent boots, disable it:

```bash
systemctl disable pontius-flop-coverage-coverage-001.service
```

## Code updates and training data

Large checkpoints and policy tables remain in each machine's run directory;
pushing or pulling code does not copy those ignored files. Transfer milestones
separately when needed, preserving the entire generation and its identity. Small
result summaries are included on this branch; large Windows checkpoints are not.

Before a later code update, stop the trainer and inspect the checkout:

```bash
git status --short
```

Tests and experiments deliberately change the local journal and `STATUS.md`.
Preserve those records before updating. Once the working tree is clean:

```bash
git pull --ff-only
uv sync --locked --group dev --python 3.14.6
```

If Git reports local changes or a conflict, keep the files and ask for help with
that output. Avoid reset/clean commands that could lose work or milestones.
