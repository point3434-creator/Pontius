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
