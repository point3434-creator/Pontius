# CLAUDE.md

Guidance for AI agents (Claude Code, Codex workers, reviewers) working in this
repository. Read this file completely before touching anything.

## What this is

Pontius is a research agent for six-player no-limit Texas hold'em, run like a
registered trial: every experiment is preregistered, source-sealed, authorized
for exactly one invocation, and retained forever — pass or fail — as one of the
numbered decisions in `docs/decisions/` (ADR-0001…). The optimization target is
chip-valued decision quality per millisecond under a hard 15,000 ms action wall
(ADR-0307). The evidence protocol outranks convenience, speed, and cleverness.

## Iron rules — violating any of these destroys evidence

1. **Sealed history is untouchable.** Never modify, move, rename, normalize,
   re-encode, or delete a file governed by an accepted ADR — source, test,
   config, attempt marker, journal, or result. Fixes ship as new files/versions,
   never edits to sealed bytes.
2. **Consumed owners never run again.** A one-shot experiment owner that has
   fired (e.g. the v7 calibration) is permanently closed. Never invoke it,
   re-create its lifecycle identities, or build a successor that reuses its
   protocol/campaign/result identity.
3. **No tuning against opened evidence.** Rejected candidates stay parked. Never
   adjust a mechanism, wall, population, or gate to make a previously failed
   result pass. Successors require a fresh preregistration.
4. **Commits are ceremonial.** One commit per decision, short imperative title
   matching the ADR (e.g. "Retain v7 laboratory-wall rejection"). Never commit,
   merge, cherry-pick, or push without the user's explicit authorization for
   that specific commit. Push to `origin` after every authorized commit.
5. **Test payloads never run from this checkout.** Execute tests only from a
   fresh disposable D:-local snapshot (clone/detach, overlay working bytes) with
   `python -B -P`, `cwd` at the snapshot root, `PYTHONPATH=<snapshot>/src`, a
   scrubbed environment, and Git resolved only via an absolute `PONTIUS_GIT`
   executable — never `PATH` lookup. Quick single-file dev runs from a worktree
   are tolerated for iteration, but acceptance evidence requires the snapshot.
6. **Fail closed, never guess.** When analysis cannot prove something, record an
   explicit typed refusal (a "blocker") with a reason. No silent passes, no
   heuristic approvals, no `print()`-and-continue in evidence paths.
7. **Exact types in evidence code.** `type(value) is int`, `type(value) is
   bool`. A `bool` never satisfies an integer field. Byte-exact digests, LF-only
   governance files.
8. **Real paths, not doubles.** A helper double or state-shape test never
   satisfies an ownership/transaction contract — only the real production path
   under a real failure schedule does.
9. **Cloud sync discipline.** Google Drive syncs this folder on demand only.
   Never trigger (or run during) a sync while a sealed reader or one-shot owner
   executes against this checkout — stray `.tmp.driveupload/` entries break
   gates that assert exact untracked-path sets.

## Read before working

1. `STATUS.md` — generated; the latest decision, blockers, and "Active next".
2. `PROJECT.md` — charter and evidence/dissent protocol.
3. `ROADMAP.md` — checkpoint ladder C0–C10.
4. The latest few ADRs in `docs/decisions/` plus anything STATUS names.
5. `ARCHITECTURE.md` — the 12 system boundaries. These files are huge
   (60–220 KB); grep headers (`^## `) and read sections, don't read them whole.

Live stabilization/orchestration state (in progress, outside the ADR record
until integrated) lives in
`D:/Pontius-worktrees/evidence-test-stabilization/.superpowers/sdd/2026-08-27-test-profile-orchestration/`
— `progress.md` is the ledger; task reports are the detail. The consolidated
review is `task-2-holistic-architecture-audit.md`.

## Repository geography

- `src/pontius/` — ~470 flat modules. Treat the flat root as read-only
  sediment: place new work in subpackages (`pontius/evidence/` is the
  precedent), never as new top-level modules.
- `docs/decisions/` — the ADR chain. `STATUS.md` is generated from it by
  `python -m pontius.status_generation`; never hand-edit STATUS.md
  (`test_status_generation` enforces freshness).
- `experiments/`, `artifacts/` — retained evidence. `experiments/results/*.json`
  is gitignored but IS retained evidence — never delete; it is backed up via
  GitHub release assets.
- `tests/` — ~392 files, unittest-style, invoked directly per file (not pytest).
- `tools/` — orchestration tooling (test inventory/profile generator).
- `D:/Pontius-worktrees/` — linked worktrees for in-flight branch work.
- Remote: private `origin` = github.com/point3434-creator/Pontius. Local mirror
  at `C:\PontiusBackup\`.

## Environment and commands

- Windows 11, PowerShell primary. Dev interpreter: `.venv` (CPython 3.14.6,
  uv-managed). Release acceptance additionally requires a separate CPython 3.11
  slot — its absence is an explicit gate, never a reason to substitute 3.14.
- Git for evidence paths: absolute `PONTIUS_GIT` (e.g.
  `C:/Program Files/Git/cmd/git.exe`), validated regular/non-reparse.
- Typical dev run (iteration only, not acceptance):
  `$env:PONTIUS_GIT=(Get-Command git).Source; $env:PYTHONPATH="D:\Pontius\src"; .venv\Scripts\python.exe -B -P tests\test_<name>.py`
- Regenerate status after ADR changes:
  `.venv\Scripts\python.exe -m pontius.status_generation`
- Importing `pontius` eagerly configures CUDA DLLs; GPU modules need CuPy and
  the RTX 5080. Never let GPU/optional deps become required for correctness
  tests.
- Style: Ruff config in `pyproject.toml`, line length 100, LF-only for
  governance outputs, no BOM, no trailing whitespace.

## When in doubt

Prefer refusing with an explanation over acting on inference. Surface the exact
ADR, ruling, or file that constrains you. Uncertainty about whether something is
sealed means treat it as sealed and ask.
