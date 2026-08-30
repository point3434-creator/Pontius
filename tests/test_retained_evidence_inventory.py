"""Retained-evidence inventory test (ADR-0477/ADR-0481 operations item).

Enforces that every retained-evidence byte is protected by at least one
durable copy path and remains byte-exact on disk:

1. every `sealed-current-files.toml` entry exists, is a regular file, is
   git-tracked (so branch pushes carry it), and matches its sealed byte
   length and raw SHA-256 exactly;
2. every on-disk file under `experiments/results/` is either git-tracked or
   listed in `docs/architecture/retained-backup-manifest.toml`, and every
   manifest entry exists on disk with byte-exact identity (retained evidence
   is never deleted and never silently rewritten);
3. no untracked stray exists under `artifacts/` (everything there rides the
   remote through tracking).

Fail closed with named paths; no heuristic acceptance.
"""

import importlib.util
import os
import subprocess
import sys
import tomllib
import unittest
from hashlib import sha256
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SEALED = REPOSITORY_ROOT / "docs" / "architecture" / "sealed-current-files.toml"
GENERATOR_PATH = (
    REPOSITORY_ROOT / "tools" / "generate_retained_backup_manifest.py"
)
MAXIMUM_BYTES = 1024 * 1024 * 1024


def _load_generator():
    spec = importlib.util.spec_from_file_location(
        "pontius_retained_backup_manifest_tests", GENERATOR_PATH
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


GENERATOR = _load_generator()


def _git(*arguments: str) -> str:
    executable = os.environ.get("PONTIUS_GIT")
    if type(executable) is not str or not Path(executable).is_absolute():
        raise AssertionError("PONTIUS_GIT must name an absolute executable")
    completed = subprocess.run(
        [executable, "-C", str(REPOSITORY_ROOT), *arguments],
        capture_output=True,
        check=True,
    )
    return completed.stdout.decode("utf-8", "surrogateescape")


def _tracked_paths() -> frozenset[str]:
    rows = _git("ls-files", "-z").split("\0")
    return frozenset(row for row in rows if row)


def _read_bounded(path: Path) -> bytes:
    info = os.stat(path, follow_symlinks=False)
    if not os.path.isfile(path) or int(info.st_size) > MAXIMUM_BYTES:
        raise AssertionError(f"retained path is not a bounded regular file: {path}")
    with open(path, "rb") as handle:
        raw = handle.read(MAXIMUM_BYTES + 1)
    if len(raw) != int(info.st_size):
        raise AssertionError(f"retained file changed while reading: {path}")
    return raw


class RetainedEvidenceInventoryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.tracked = _tracked_paths()

    def test_sealed_current_files_are_tracked_and_byte_exact(self) -> None:
        document = tomllib.loads(_read_bounded(SEALED).decode("utf-8"))
        files = document.get("files")
        self.assertIs(type(files), list)
        self.assertGreater(len(files), 0)
        for row in files:
            self.assertIs(type(row), dict)
            path = row.get("relative_path")
            length = row.get("byte_length")
            digest = row.get("raw_sha256")
            self.assertIs(type(path), str)
            self.assertIs(type(length), int)
            self.assertNotIsInstance(length, bool)
            self.assertIs(type(digest), str)
            with self.subTest(path=path):
                self.assertIn(
                    path,
                    self.tracked,
                    f"sealed retained file is not git-tracked: {path}",
                )
                raw = _read_bounded(REPOSITORY_ROOT / path)
                self.assertEqual(
                    len(raw), length, f"sealed byte length differs: {path}"
                )
                self.assertEqual(
                    sha256(raw).hexdigest(),
                    digest,
                    f"sealed raw SHA-256 differs: {path}",
                )

    def test_every_result_file_is_tracked_or_captured_and_captures_hold(
        self,
    ) -> None:
        manifest = GENERATOR.load_manifest()
        results = REPOSITORY_ROOT / "experiments" / "results"
        self.assertTrue(results.is_dir())
        on_disk: set[str] = set()
        for entry in sorted(results.iterdir(), key=lambda item: item.name):
            if not entry.is_file() or entry.name == ".gitkeep":
                continue
            relative = f"experiments/results/{entry.name}"
            on_disk.add(relative)
            with self.subTest(path=relative):
                if relative in self.tracked:
                    continue
                self.assertIn(
                    relative,
                    manifest,
                    "retained result file is neither git-tracked nor "
                    f"captured by any backup set: {relative}",
                )
        # Archive completeness is a property of the machine that hosts the
        # loose retained population. Fresh clones (CI runners, disposable
        # snapshots) legitimately carry only the tracked subset, so absence
        # there is not loss; the primary checkout declares itself with
        # PONTIUS_RETAINED_ARCHIVE=1 and then every captured file must exist.
        archive_host = os.environ.get("PONTIUS_RETAINED_ARCHIVE") == "1"
        for relative, row in sorted(manifest.items()):
            with self.subTest(captured=relative):
                if relative not in on_disk:
                    self.assertFalse(
                        archive_host,
                        "captured retained file is absent from the archive "
                        f"host (retained evidence is never deleted): {relative}",
                    )
                    continue
                raw = _read_bounded(REPOSITORY_ROOT / relative)
                self.assertEqual(
                    len(raw),
                    row["byte_length"],
                    f"captured byte length drifted: {relative}",
                )
                self.assertEqual(
                    sha256(raw).hexdigest(),
                    row["raw_sha256"],
                    f"captured raw SHA-256 drifted: {relative}",
                )

    def test_manifest_is_current_against_the_directory(self) -> None:
        scanned = GENERATOR._scan()
        manifest = GENERATOR.load_manifest()
        scanned_paths = {str(row["relative_path"]) for row in scanned}
        if os.environ.get("PONTIUS_RETAINED_ARCHIVE") == "1":
            self.assertEqual(
                scanned_paths,
                set(manifest),
                "retained-backup manifest is stale; regenerate with --write "
                "and an explicit --capture label",
            )
        else:
            self.assertLessEqual(
                scanned_paths,
                set(manifest) | (self.tracked & scanned_paths),
                "clone carries a result file the manifest never captured",
            )
        for row in scanned:
            path = str(row["relative_path"])
            with self.subTest(path=path):
                self.assertEqual(manifest[path]["byte_length"], row["byte_length"])
                self.assertEqual(manifest[path]["raw_sha256"], row["raw_sha256"])

    def test_artifacts_tree_has_no_untracked_strays(self) -> None:
        artifacts = REPOSITORY_ROOT / "artifacts"
        self.assertTrue(artifacts.is_dir())
        strays: list[str] = []
        for directory, _, names in os.walk(artifacts):
            for name in names:
                full = Path(directory) / name
                relative = full.relative_to(REPOSITORY_ROOT).as_posix()
                if relative not in self.tracked:
                    strays.append(relative)
        self.assertEqual(
            strays,
            [],
            "untracked retained artifacts are protected by nothing: "
            + ", ".join(strays),
        )


if __name__ == "__main__":
    unittest.main(verbosity=1)
