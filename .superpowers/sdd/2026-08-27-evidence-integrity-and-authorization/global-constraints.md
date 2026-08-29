# Binding global constraints — Evidence Integrity and Authorization

- Execute the coordinated plans in this order: evidence Tasks 1–3; orchestration Tasks 1–2 plus Task 11a; evidence Tasks 4–9; orchestration Tasks 3–10; Task 11b; then Task 12.
- Baseline is `a842c4b6a73a2991a63a481f4107580b72750582`; re-read HEAD/status before the task.
- Do not modify, normalize, delete, move, or rewrite any existing v2–v7 source, reader, runner, test, configuration, decision, attempt, marker, result, retained artifact, or protected absence.
- Do not modify `src/pontius/__init__.py`.
- New evidence modules import only the standard library, sibling `pontius.evidence` modules, and (when the task requires it) `pontius.durable_evidence_journal`; never import historical owners/readers/runners, tests, experiments, CuPy/CUDA, or GPU modules.
- Active library code raises typed exceptions; it does not print, exit, raise `SystemExit`, invoke a one-shot owner, or write lifecycle state.
- Evidence reads are bounded, no-follow/nonreparse, one read from one handle, and identity-verified before/after whenever this task touches I/O.
- Exact parser/model types are mandatory: booleans never satisfy integer fields.
- Until the canonical runner exists, execute every test payload only in a disposable snapshot outside OneDrive. Never execute a repository test from the development worktree or the primary checkout.
- Resolve Git only as absolute `C:/Program Files/Git/cmd/git.exe`; invoke it by argument vector with a scrubbed minimal Git environment and no ambient `GIT_*` routing/object/config controls. Mutating snapshot Git calls target only the disposable H clone.
- The development interpreter is the regular nonreparse copied venv executable at `C:/Users/point/AppData/Local/Temp/pontius-evidence-test-stabilization/.venv/Scripts/python.exe`; invoke tests with `-B -P` and `PYTHONPATH` exactly `H/src`.
- Test support under `-P` is loaded by exact file path with `importlib.util`, never by adding H, H/tests, the primary checkout, or an empty path to `sys.path`.
- Cleanup validates the exact run root as a strict child of the resolved OS temporary directory with the expected `pontius-` prefix before recursive removal.
- Local commits on branch `codex/evidence-test-stabilization` are explicitly authorized. Do not push, merge, publish, or mutate the primary checkout.
- Follow strict RED → GREEN → REFACTOR. Record the exact failing and passing commands/output in the task report.
