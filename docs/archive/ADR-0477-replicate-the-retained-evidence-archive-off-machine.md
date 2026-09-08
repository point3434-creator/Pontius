# ADR-0477: Replicate the retained evidence archive off-machine

- Status: accepted operations decision; the repository gained its first off-machine replication after the OneDrive exit left exactly one copy of protocol-unreproducible evidence, and the archive now exists in a private GitHub remote (all branches), point-in-time snapshot refs for then-uncommitted evidence, a release asset carrying every retained result JSON including the gitignored and over-100 MB files, and a second-volume local mirror; the restore drill, push-on-commit automation, and a retained-evidence inventory test remain explicitly open, and replication is not evidence that restoration works
- Date: 2026-08-29
- Follows: ADR-0476
- Remote: private `origin` at `https://github.com/point3434-creator/Pontius` (created 2026-08-29; five branches pushed: `master`, `codex/evidence-test-stabilization`, `codex/orch-task1`, `codex/orch-task11a`, `codex/orch-task2`)
- Snapshot refs (temporary-index construction; no HEAD, index, or worktree change): `backup/2026-08-29-main` = `5f9556e76752cc208eea6b5d06fc806bef69b6c2`; `backup/2026-08-29-evidence-stab` = `cefb8456d22465bdaf66a2629be7af6b68643427`; `backup/2026-08-29-orch-task2` = `701b31de13da1d5142c105a8cfeed105e74c450a`, later retired after its tree proved byte-identical to committed `8c1bed3`
- Release: tag `evidence-backup-2026-08-29`; asset `experiments-results-2026-08-29.tar.gz`, `96133441` bytes, SHA-256 `c3a83c618a21f7864b25228b45498182e4140106a36a82108d5dfcf97d1cd61b`, plus a 204-byte `.sha256` companion
- Release coverage: all 191 `experiments/results` JSON files, including 110 gitignored files and four files above GitHub's 100 MB blob limit (133.8, 105.0, 157.2, and 197.5 MB)
- Local mirror: `C:\PontiusBackup\` — `Pontius` (2,187 files, 1.248 GB) and `Pontius-worktrees` (3,825 files, ~807 MB), robocopy with zero failed copies, excluding only `.venv` and cache directories
- Cloud sync: Google Drive syncs `D:\Pontius` on demand only (user-confirmed intentional); syncs must not run while a sealed reader or one-shot owner executes against the primary checkout, because `.tmp.driveupload/` entries violate exact untracked-path gates

## Question

After the OneDrive exit, the evidence archive existed as a single copy on one
disk with no Git remote, while the protocol forbids ever regenerating consumed
one-shot evidence. What replication now exists, and what does it not prove?

## Decision

Replicate the archive four ways and record exactly what each layer covers. The
private GitHub remote carries every branch of committed history. Snapshot refs
built through a temporary index captured the then-uncommitted evidence — the
frozen Task 2 candidate, the `.superpowers` review record, and the untracked
plan documents — without touching HEAD, the real index, or any worktree. The
release asset carries the complete `experiments/results` population, which a
branch push alone cannot: 110 of its 191 files are gitignored and four exceed
GitHub's per-blob limit. The local mirror covers raw bytes independent of Git
entirely. Google Drive remains a user-triggered fourth copy.

The `backup/2026-08-29-orch-task2` snapshot was retired only after `git diff`
proved its tree byte-identical to the later real commit `8c1bed3`. The other
two snapshots remain live until the bytes they guard reach committed history.

### Result boundary

This decision proves replication, not recoverability. No restore drill has
executed the documented reproduction procedure from a fresh clone. Pushes are
manual; a future commit that is never pushed is protected only by the mirror
and any later Drive sync. No test yet enforces that every ADR-named retained
path is tracked or captured by the backup set.

### Kill criteria

Kill any claim that the archive is "backed up" in the tested sense before one
restore drill has recreated a detached authorization checkout from the remote
and run a sealed reader there. Kill any procedure that triggers a Drive sync
during a sealed execution. Never delete a live snapshot ref before proving its
tree is contained in committed history.

### Claims boundary

ADR-0477 makes no research claim. It changes no sealed byte, runs no owner,
and leaves every ADR-0476 blocker in force.
