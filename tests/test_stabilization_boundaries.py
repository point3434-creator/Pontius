from __future__ import annotations

from hashlib import sha256
import importlib.util
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import tomllib
from types import SimpleNamespace
import unittest
from unittest import mock


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
GENERATOR_PATH = REPOSITORY_ROOT / "tools" / "generate_dependency_baseline.py"
CHECKER_PATH = REPOSITORY_ROOT / "tools" / "check_stabilization_boundaries.py"
BASELINE_COMMIT = "a842c4b6a73a2991a63a481f4107580b72750582"
EDGE_DIGEST = "c178ed92158da1c544abaf39ab14842721658a31f3f9246cbeb3e05e3e3da6ee"
SCC_DIGEST = "9987fddd06742fc2af87de7b8ebf79bc8b2dda7231260f7cc9efdcca18dff345"


def _load_exact(name: str, path: Path) -> object:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not load {path.name} by exact path")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


GENERATOR = _load_exact("pontius_dependency_baseline_generator_tests", GENERATOR_PATH)
CHECKER = _load_exact("pontius_stabilization_boundary_checker_tests", CHECKER_PATH)


def _source(text: str) -> bytes:
    return text.encode("utf-8")


def _git_executable() -> Path:
    configured = os.environ.get("PONTIUS_GIT")
    if configured is None or not Path(configured).is_absolute():
        raise RuntimeError("PONTIUS_GIT must name an absolute test Git executable")
    return Path(configured)


def _run_fixture_git(repository: Path, *arguments: str) -> None:
    environment = os.environ.copy()
    environment["GIT_CONFIG_NOSYSTEM"] = "1"
    environment["GIT_CONFIG_GLOBAL"] = "NUL" if os.name == "nt" else "/dev/null"
    completed = subprocess.run(
        [str(_git_executable()), *arguments],
        cwd=repository,
        env=environment,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        timeout=30,
        shell=False,
    )
    if completed.returncode != 0:
        raise AssertionError(completed.stderr.decode("utf-8", errors="replace"))


def _create_directory_link(link: Path, target: Path) -> None:
    try:
        link.symlink_to(target, target_is_directory=True)
        return
    except OSError:
        if os.name != "nt":
            raise
    command_processor = os.environ.get("ComSpec", "C:/Windows/System32/cmd.exe")
    completed = subprocess.run(
        [command_processor, "/d", "/c", "mklink", "/J", str(link), str(target)],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        timeout=10,
        shell=False,
    )
    if completed.returncode != 0:
        raise AssertionError(completed.stderr.decode("utf-8", errors="replace"))


def _copy_checker_fixture(root: Path) -> Path:
    shutil.copytree(REPOSITORY_ROOT / "src" / "pontius", root / "src" / "pontius")
    shutil.copytree(REPOSITORY_ROOT / "tools", root / "tools")
    baseline = root / "docs" / "architecture" / "dependency-baseline.toml"
    baseline.parent.mkdir(parents=True)
    shutil.copyfile(
        REPOSITORY_ROOT / "docs" / "architecture" / baseline.name,
        baseline,
    )
    return baseline


class DependencyBaselineTests(unittest.TestCase):
    def _assert_failure_temporary_policy(self, directory: Path) -> None:
        temporaries = [path for path in directory.iterdir() if path.name.endswith(".tmp")]
        if os.name == "nt":
            self.assertEqual(temporaries, [])
        else:
            self.assertEqual(len(temporaries), 1)

    def test_exact_baseline_graph_matches_the_approved_mechanical_lock(self) -> None:
        graph = GENERATOR.derive_baseline_graph(
            REPOSITORY_ROOT,
            baseline_commit=BASELINE_COMMIT,
            git_executable=_git_executable(),
        )

        self.assertEqual(len(graph.modules), 470)
        self.assertEqual(len(graph.edges), 2577)
        self.assertEqual(GENERATOR.edges_sha256(graph.edges), EDGE_DIGEST)
        self.assertEqual(len(graph.sccs), 469)
        self.assertEqual(GENERATOR.sccs_sha256(graph.sccs), SCC_DIGEST)
        self.assertEqual(
            tuple(component for component in graph.sccs if len(component) > 1),
            (("pontius.action_clock", "pontius.preparation_bank"),),
        )

    def test_import_scanner_resolves_absolute_relative_and_type_checking_edges(self) -> None:
        sources = {
            "src/pontius/pkg/d.py": _source("VALUE = 1\n"),
            "src/pontius/a.py": _source(
                "from typing import TYPE_CHECKING\n"
                "from . import b\n"
                "from .pkg import c\n"
                "import pontius.pkg.d\n"
                "if TYPE_CHECKING:\n"
                "    from pontius import e\n"
            ),
            "src/pontius/pkg/__init__.py": b"",
            "src/pontius/e.py": b"",
            "src/pontius/__init__.py": b"",
            "src/pontius/pkg/c.py": b"",
            "src/pontius/b.py": b"",
        }

        graph = GENERATOR.scan_sources(sources)

        self.assertEqual(
            graph.modules,
            (
                ("pontius.__init__", "src/pontius/__init__.py"),
                ("pontius.a", "src/pontius/a.py"),
                ("pontius.b", "src/pontius/b.py"),
                ("pontius.e", "src/pontius/e.py"),
                ("pontius.pkg.__init__", "src/pontius/pkg/__init__.py"),
                ("pontius.pkg.c", "src/pontius/pkg/c.py"),
                ("pontius.pkg.d", "src/pontius/pkg/d.py"),
            ),
        )
        self.assertEqual(
            graph.edges,
            (
                ("pontius.a", "pontius.b"),
                ("pontius.a", "pontius.e"),
                ("pontius.a", "pontius.pkg.c"),
                ("pontius.a", "pontius.pkg.d"),
            ),
        )
        self.assertEqual(
            tuple(sorted(member for component in graph.sccs for member in component)),
            tuple(module_name for module_name, _ in graph.modules),
        )

    def test_render_and_parse_are_sorted_strict_and_recompute_graph_digests(self) -> None:
        graph = GENERATOR.scan_sources(
            {
                "src/pontius/z.py": _source("from . import a\n"),
                "src/pontius/__init__.py": b"",
                "src/pontius/a.py": b"",
            }
        )

        raw = GENERATOR.render_baseline(graph, baseline_commit=BASELINE_COMMIT)
        parsed = GENERATOR.parse_baseline_bytes(raw)
        decoded = raw.decode("utf-8")

        self.assertEqual(parsed.graph.modules, graph.modules)
        self.assertEqual(parsed.graph.edges, graph.edges)
        self.assertEqual(parsed.graph.sccs, graph.sccs)
        self.assertEqual(parsed.baseline_commit, BASELINE_COMMIT)
        self.assertLess(
            decoded.index('module_name = "pontius.__init__"'),
            decoded.index('module_name = "pontius.a"'),
        )
        self.assertLess(
            decoded.index('module_name = "pontius.a"'),
            decoded.index('module_name = "pontius.z"'),
        )
        self.assertEqual(raw[-1:], b"\n")

        document = tomllib.loads(decoded)
        wrong_digest = decoded.replace(document["edges_sha256"], "0" * 64, 1).encode()
        wrong_count = decoded.replace("module_count = 3", "module_count = true", 1).encode()
        extra_key = raw + b"unexpected = true\n"
        unsorted = decoded.replace(
            'module_name = "pontius.__init__"\nrelative_path = "src/pontius/__init__.py"',
            'module_name = "pontius.zzz"\nrelative_path = "src/pontius/zzz.py"',
            1,
        ).encode()
        for label, candidate in (
            ("digest", wrong_digest),
            ("boolean count", wrong_count),
            ("extra key", extra_key),
            ("unsorted row", unsorted),
        ):
            with self.subTest(label=label), self.assertRaises(GENERATOR.BaselineError):
                GENERATOR.parse_baseline_bytes(candidate)

    def test_digest_encoding_is_literal_and_order_independent(self) -> None:
        edges = (("pontius.b", "pontius.c"), ("pontius.a", "pontius.b"))
        sccs = (("pontius.c",), ("pontius.a", "pontius.b"))
        expected_edges = sha256(
            b"pontius.a\tpontius.b\npontius.b\tpontius.c\n"
        ).hexdigest()
        expected_sccs = sha256(
            b"pontius.a\tpontius.b\npontius.c\n"
        ).hexdigest()

        self.assertEqual(GENERATOR.edges_sha256(edges), expected_edges)
        self.assertEqual(GENERATOR.sccs_sha256(sccs), expected_sccs)

    def test_generator_defaults_to_check_and_write_is_limited_to_exact_baseline(self) -> None:
        arguments = GENERATOR.parse_arguments([])
        self.assertIsNone(arguments.write)
        self.assertTrue(arguments.check)

        with tempfile.TemporaryDirectory(prefix="pontius-dependency-write-policy-") as directory:
            root = Path(directory).resolve()
            architecture = root / "docs" / "architecture"
            architecture.mkdir(parents=True)
            expected = architecture / "dependency-baseline.toml"
            self.assertEqual(
                GENERATOR.validate_write_destination(root, expected), expected
            )
            for candidate in (
                Path("docs/architecture/dependency-baseline.toml"),
                root / "dependency-baseline.toml",
                architecture / "other.toml",
            ):
                with self.subTest(candidate=candidate), self.assertRaises(
                    GENERATOR.BaselineError
                ):
                    GENERATOR.validate_write_destination(root, candidate)

    def test_generator_requires_an_explicit_absolute_git_executable(self) -> None:
        prior = os.environ.pop("PONTIUS_GIT", None)
        known_git = prior or (
            "C:/Program Files/Git/cmd/git.exe" if os.name == "nt" else "/usr/bin/git"
        )
        try:
            with self.assertRaises(GENERATOR.BaselineError):
                GENERATOR.configured_git_executable()
            os.environ["PONTIUS_GIT"] = "git"
            with self.assertRaises(GENERATOR.BaselineError):
                GENERATOR.configured_git_executable()
            os.environ["PONTIUS_GIT"] = known_git
            self.assertTrue(GENERATOR.configured_git_executable().is_absolute())
        finally:
            if prior is None:
                os.environ.pop("PONTIUS_GIT", None)
            else:
                os.environ["PONTIUS_GIT"] = prior

    def test_git_executable_rejects_even_a_supported_cloud_reparse_tag(self) -> None:
        with tempfile.TemporaryDirectory(prefix="pontius-cloud-git-") as directory:
            executable = (Path(directory).resolve() / "git.exe")
            executable.write_bytes(b"synthetic executable")
            actual = os.lstat(executable)
            cloud_info = SimpleNamespace(
                st_mode=actual.st_mode,
                st_file_attributes=0x400,
                st_reparse_tag=0x9000E01A,
            )

            with mock.patch.object(GENERATOR.os, "lstat", return_value=cloud_info):
                with self.assertRaises(GENERATOR.BaselineError):
                    GENERATOR._validated_git_executable(executable)

    def test_reparse_policy_allows_only_identity_stable_cloud_tags(self) -> None:
        reparse = 0x400
        cloud_tags = (0x9000001A, 0x9000601A, 0x9000E01A, 0x9000F01A)
        rejected_tags = (0, 0xA0000003, 0xA000000C, 0x8000001B, 0x9000001B)

        for tag in cloud_tags:
            with self.subTest(tag=hex(tag)):
                self.assertFalse(
                    GENERATOR._is_disallowed_reparse_values(reparse, tag)
                )
        for tag in rejected_tags:
            with self.subTest(tag=hex(tag)):
                self.assertTrue(
                    GENERATOR._is_disallowed_reparse_values(reparse, tag)
                )
        self.assertFalse(GENERATOR._is_disallowed_reparse_values(0, 0))

    @unittest.skipUnless(os.name == "nt", "Windows cloud-tag handle test")
    def test_windows_directory_identity_accepts_cloud_but_rejects_name_surrogate(
        self,
    ) -> None:
        attributes = 0x10 | 0x400
        active_tag = 0x9000E01A

        def information(_handle: object, pointer: object) -> bool:
            pointer._obj.dwFileAttributes = attributes
            return True

        def extended(
            _handle: object, information_class: int, pointer: object, _size: int
        ) -> bool:
            if information_class == 9:
                pointer._obj.FileAttributes = attributes
                pointer._obj.ReparseTag = active_tag
            elif information_class == 18:
                pointer._obj.VolumeSerialNumber = 42
                for index in range(16):
                    pointer._obj.FileId.ByteIdentifier[index] = index
            else:  # pragma: no cover - fail loudly if the production contract drifts
                raise AssertionError(information_class)
            return True

        with mock.patch.object(
            GENERATOR,
            "_windows_directory_api",
            return_value=(None, information, extended, None),
        ):
            self.assertEqual(
                GENERATOR._windows_directory_handle_identity(123, Path("C:/cloud")),
                (42, bytes(range(16))),
            )
            active_tag = 0xA000000C
            with self.assertRaises(GENERATOR.BaselineError):
                GENERATOR._windows_directory_handle_identity(
                    123, Path("C:/name-surrogate")
                )

    @unittest.skipUnless(os.name == "nt", "Windows hydration retry test")
    def test_identity_bound_read_retries_one_metadata_only_cloud_transition(self) -> None:
        with tempfile.TemporaryDirectory(prefix="pontius-baseline-cloud-transition-") as directory:
            root = Path(directory).resolve()
            target = root / "source.py"
            target.write_bytes(b"VALUE = 1\n")

            with mock.patch.object(
                GENERATOR,
                "_file_identity",
                side_effect=((1,), (2,), (3,), (3,), (4,)),
            ) as identity:
                snapshot = GENERATOR.read_regular_snapshot(
                    target,
                    maximum_bytes=64,
                    root=root,
                )

            self.assertEqual(snapshot.raw, b"VALUE = 1\n")
            self.assertEqual(snapshot.identity, (4,))
            self.assertEqual(identity.call_count, 5)

    @unittest.skipUnless(os.name == "nt", "Windows hydration retry test")
    def test_identity_bound_read_rejects_a_second_metadata_transition(self) -> None:
        with tempfile.TemporaryDirectory(prefix="pontius-baseline-cloud-repeat-") as directory:
            root = Path(directory).resolve()
            target = root / "source.py"
            target.write_bytes(b"VALUE = 1\n")

            with mock.patch.object(
                GENERATOR,
                "_file_identity",
                side_effect=((1,), (2,), (3,), (4,)),
            ) as identity:
                with self.assertRaises(GENERATOR.BaselineError) as caught:
                    GENERATOR.read_regular_snapshot(
                        target,
                        maximum_bytes=64,
                        root=root,
                    )

            self.assertIn("changed while reading", str(caught.exception))
            self.assertEqual(identity.call_count, 4)

    @unittest.skipUnless(os.name == "nt", "Windows regular-file cloud-tag test")
    def test_regular_file_snapshot_binds_handle_cloud_metadata(self) -> None:
        with tempfile.TemporaryDirectory(prefix="pontius-cloud-file-") as directory:
            root = Path(directory).resolve()
            target = root / "source.py"
            target.write_bytes(b"VALUE = 1\n")
            cloud = (0x20 | 0x400, 0x9000E01A)

            real_lstat = GENERATOR.os.lstat

            def cloud_lstat(path: object) -> object:
                info = real_lstat(path)
                if Path(path) != target:
                    return info
                return SimpleNamespace(
                    st_dev=info.st_dev,
                    st_ino=info.st_ino,
                    st_size=info.st_size,
                    st_mtime_ns=info.st_mtime_ns,
                    st_ctime_ns=info.st_ctime_ns,
                    st_mode=info.st_mode,
                    st_file_attributes=cloud[0],
                    st_reparse_tag=cloud[1],
                )

            with mock.patch.object(
                GENERATOR.os, "lstat", side_effect=cloud_lstat
            ), mock.patch.object(
                GENERATOR,
                "_windows_regular_handle_metadata",
                side_effect=(cloud, cloud),
            ):
                snapshot = GENERATOR.read_regular_snapshot(
                    target,
                    maximum_bytes=64,
                    root=root,
                )
            self.assertEqual(snapshot.raw, b"VALUE = 1\n")

            for label, metadata in (
                ("name surrogate", (0x20 | 0x400, 0xA000000C)),
                ("unknown", (0x20 | 0x400, 0x8000001B)),
            ):
                with self.subTest(label=label), mock.patch.object(
                    GENERATOR,
                    "_windows_regular_handle_metadata",
                    return_value=metadata,
                ):
                    with self.assertRaises(GENERATOR.BaselineError):
                        GENERATOR.read_regular_snapshot(
                            target,
                            maximum_bytes=64,
                            root=root,
                        )

            mismatched_cloud = (cloud[0], 0x9000601A)
            with mock.patch.object(
                GENERATOR.os,
                "lstat",
                side_effect=cloud_lstat,
            ), mock.patch.object(
                GENERATOR,
                "_windows_regular_handle_metadata",
                side_effect=(cloud, mismatched_cloud),
            ):
                with self.assertRaises(GENERATOR.BaselineError) as caught:
                    GENERATOR.read_regular_snapshot(
                        target,
                        maximum_bytes=64,
                        root=root,
                    )
            self.assertIn("changed while reading", str(caught.exception))

            with mock.patch.object(
                GENERATOR.os,
                "lstat",
                side_effect=cloud_lstat,
            ), mock.patch.object(
                GENERATOR,
                "_windows_regular_handle_metadata",
                return_value=mismatched_cloud,
            ):
                with self.assertRaises(GENERATOR.BaselineError) as caught:
                    GENERATOR.read_regular_snapshot(
                        target,
                        maximum_bytes=64,
                        root=root,
                    )
            self.assertIn("changed while opening", str(caught.exception))

    def test_identity_bound_read_rejects_same_size_replacement_before_open(self) -> None:
        with tempfile.TemporaryDirectory(prefix="pontius-baseline-read-race-") as directory:
            root = Path(directory).resolve()
            target = root / "baseline.toml"
            replacement = root / "replacement.toml"
            target.write_bytes(b"first\n")
            replacement.write_bytes(b"other\n")
            real_open = getattr(GENERATOR, "_open_regular_no_follow", None)

            def replace_then_open(path: Path) -> int:
                os.replace(replacement, target)
                if real_open is None:
                    return os.open(path, os.O_RDONLY | getattr(os, "O_BINARY", 0))
                return real_open(path)

            with mock.patch.object(
                GENERATOR,
                "_open_regular_no_follow",
                create=True,
                side_effect=replace_then_open,
            ):
                with self.assertRaises(GENERATOR.BaselineError) as caught:
                    GENERATOR._validated_regular_file(target, maximum_bytes=64)

            self.assertIn("changed while opening", str(caught.exception))

    def test_identity_bound_read_rejects_same_size_mutation_during_read(self) -> None:
        with tempfile.TemporaryDirectory(prefix="pontius-baseline-handle-race-") as directory:
            root = Path(directory).resolve()
            target = root / "baseline.toml"
            target.write_bytes(b"first\n")
            real_read = GENERATOR.os.read
            mutated = False
            mtime_before_ns = 0
            mtime_after_ns = 0

            def mutate_then_read(descriptor: int, count: int) -> bytes:
                nonlocal mutated, mtime_before_ns, mtime_after_ns
                if not mutated:
                    mtime_before_ns = os.stat(target).st_mtime_ns
                    target.write_bytes(b"other\n")
                    # A same-size rewrite can land inside the filesystem's
                    # timestamp tick and leave the identity tuple unchanged
                    # (observed on CI hardware). Advance mtime explicitly so
                    # the test exercises the identity contract the reader
                    # actually promises, independent of tick timing.
                    advanced_ns = mtime_before_ns + 10_000_000
                    os.utime(target, ns=(advanced_ns, advanced_ns))
                    mtime_after_ns = os.stat(target).st_mtime_ns
                    mutated = True
                return real_read(descriptor, count)

            with mock.patch.object(GENERATOR.os, "read", side_effect=mutate_then_read):
                with self.assertRaises(GENERATOR.BaselineError) as caught:
                    GENERATOR._validated_regular_file(target, maximum_bytes=64)

            self.assertTrue(mutated, str(caught.exception))
            self.assertNotEqual(mtime_after_ns, mtime_before_ns)
            self.assertIn("changed while reading", str(caught.exception))

    def test_snapshot_revalidation_rechecks_content_when_metadata_is_concealed(self) -> None:
        with tempfile.TemporaryDirectory(prefix="pontius-baseline-content-pass-") as directory:
            root = Path(directory).resolve()
            target = root / "baseline.toml"
            target.write_bytes(b"first\n")
            snapshot = GENERATOR.read_regular_snapshot(
                target,
                maximum_bytes=64,
                root=root,
            )
            target.write_bytes(b"other\n")

            with mock.patch.object(
                GENERATOR,
                "_file_identity",
                return_value=snapshot.identity,
            ):
                with self.assertRaises(GENERATOR.BaselineError) as caught:
                    snapshot.revalidate()

            self.assertIn("content changed", str(caught.exception))

    def test_check_accepts_only_the_exact_all_crlf_checkout_transformation(self) -> None:
        graph = GENERATOR.scan_sources(
            {
                "src/pontius/__init__.py": b"",
                "src/pontius/a.py": b"from . import b\n",
                "src/pontius/b.py": b"",
            }
        )
        expected = GENERATOR.render_baseline(graph, baseline_commit=BASELINE_COMMIT)
        with tempfile.TemporaryDirectory(prefix="pontius-baseline-autocrlf-") as directory:
            root = Path(directory).resolve()
            source = root / "source"
            checkout = root / "checkout"
            source.mkdir()
            _run_fixture_git(source, "init", "--quiet")
            baseline = source / "docs" / "architecture" / "dependency-baseline.toml"
            baseline.parent.mkdir(parents=True)
            baseline.write_bytes(expected)
            _run_fixture_git(source, "-c", "core.autocrlf=false", "add", ".")
            _run_fixture_git(
                source,
                "-c",
                "user.name=Pontius Test",
                "-c",
                "user.email=pontius@example.invalid",
                "commit",
                "--quiet",
                "-m",
                "fixture",
            )
            _run_fixture_git(
                root,
                "-c",
                "core.autocrlf=true",
                "clone",
                "--quiet",
                str(source),
                str(checkout),
            )
            checked_out = checkout / "docs" / "architecture" / baseline.name
            actual = checked_out.read_bytes()

            self.assertEqual(actual, expected.replace(b"\n", b"\r\n"))
            GENERATOR.check_baseline(checked_out, expected)

            mixed = actual.replace(b"\r\n", b"\n", 1)
            checked_out.write_bytes(mixed)
            with self.assertRaises(GENERATOR.BaselineError):
                GENERATOR.check_baseline(checked_out, expected)

    def test_generated_governance_files_are_pinned_to_lf(self) -> None:
        attributes = (REPOSITORY_ROOT / ".gitattributes").read_text(encoding="utf-8")
        expected = (
            "/docs/architecture/dependency-baseline.toml text eol=lf",
            "/tests/test-inventory.json text eol=lf",
            "/tests/test-profiles.toml text eol=lf",
        )

        for rule in expected:
            with self.subTest(rule=rule):
                self.assertEqual(attributes.splitlines().count(rule), 1)

    def test_write_rejects_an_architecture_symlink_escape(self) -> None:
        with tempfile.TemporaryDirectory(prefix="pontius-baseline-link-") as directory:
            root = Path(directory).resolve()
            docs = root / "docs"
            docs.mkdir()
            outside = root / "outside"
            outside.mkdir()
            architecture = docs / "architecture"
            _create_directory_link(architecture, outside)
            destination = architecture / "dependency-baseline.toml"

            try:
                with self.assertRaises(GENERATOR.BaselineError):
                    GENERATOR.validate_write_destination(root, destination)
                self.assertEqual(list(outside.iterdir()), [])
            finally:
                if architecture.is_symlink():
                    architecture.unlink()
                else:
                    architecture.rmdir()

    def test_bound_write_detects_a_post_validation_directory_swap(self) -> None:
        with tempfile.TemporaryDirectory(prefix="pontius-baseline-write-swap-") as directory:
            root = Path(directory).resolve()
            architecture = root / "docs" / "architecture"
            architecture.mkdir(parents=True)
            destination = architecture / "dependency-baseline.toml"
            destination.write_bytes(b"old\n")
            displaced = root / "docs" / "architecture-displaced"
            expected = GENERATOR.validate_write_destination(root, destination)
            real_uuid4 = GENERATOR.uuid.uuid4
            attempted = False
            swapped = False

            def swap_then_name() -> object:
                nonlocal attempted, swapped
                attempted = True
                try:
                    os.replace(architecture, displaced)
                    architecture.mkdir()
                except OSError:
                    pass
                else:
                    swapped = True
                return real_uuid4()

            failure = None
            with mock.patch.object(GENERATOR.uuid, "uuid4", side_effect=swap_then_name):
                try:
                    GENERATOR.write_baseline(expected, b"new\n")
                except GENERATOR.BaselineError as error:
                    failure = error

            self.assertTrue(attempted)
            if swapped:
                self.assertIsNotNone(failure)
                self.assertEqual(list(architecture.iterdir()), [])
                self.assertEqual((displaced / destination.name).read_bytes(), b"old\n")
                self._assert_failure_temporary_policy(displaced)
            else:
                self.assertIsNone(failure)
                self.assertEqual(destination.read_bytes(), b"new\n")

    def test_bound_write_retains_validated_identity_while_binding_parent(self) -> None:
        with tempfile.TemporaryDirectory(prefix="pontius-baseline-bind-swap-") as directory:
            root = Path(directory).resolve()
            architecture = root / "docs" / "architecture"
            architecture.mkdir(parents=True)
            destination = architecture / "dependency-baseline.toml"
            destination.write_bytes(b"old\n")
            displaced = root / "docs" / "architecture-displaced"
            expected = GENERATOR.validate_write_destination(root, destination)
            method_name = "_bind_windows" if os.name == "nt" else "_bind_posix"
            real_bind = getattr(GENERATOR._BoundBaselineDirectory, method_name)
            swapped = False

            def swap_then_bind(transaction: object) -> None:
                nonlocal swapped
                os.replace(architecture, displaced)
                architecture.mkdir()
                swapped = True
                real_bind(transaction)

            failure = None
            with mock.patch.object(
                GENERATOR._BoundBaselineDirectory,
                method_name,
                autospec=True,
                side_effect=swap_then_bind,
            ):
                try:
                    GENERATOR.write_baseline(expected, b"new\n")
                except GENERATOR.BaselineError as error:
                    failure = error

            self.assertTrue(swapped)
            self.assertIsNotNone(failure)
            self.assertEqual(list(architecture.iterdir()), [])
            self.assertEqual((displaced / destination.name).read_bytes(), b"old\n")

    def test_bound_write_detects_a_directory_swap_at_atomic_replace(self) -> None:
        with tempfile.TemporaryDirectory(prefix="pontius-baseline-replace-swap-") as directory:
            root = Path(directory).resolve()
            architecture = root / "docs" / "architecture"
            architecture.mkdir(parents=True)
            destination = architecture / "dependency-baseline.toml"
            destination.write_bytes(b"old\n")
            displaced = root / "docs" / "architecture-displaced"
            expected = GENERATOR.validate_write_destination(root, destination)
            real_replace = getattr(GENERATOR, "_replace_staged_file", None)
            attempted = False
            swapped = False

            def swap_then_replace(*arguments: object, **keywords: object) -> None:
                nonlocal attempted, swapped
                attempted = True
                try:
                    os.replace(architecture, displaced)
                    architecture.mkdir()
                except OSError:
                    pass
                else:
                    swapped = True
                if real_replace is None:
                    raise AssertionError("bound replacement seam is absent")
                real_replace(*arguments, **keywords)

            failure = None
            with mock.patch.object(
                GENERATOR,
                "_replace_staged_file",
                create=True,
                side_effect=swap_then_replace,
            ):
                try:
                    GENERATOR.write_baseline(expected, b"new\n")
                except GENERATOR.BaselineError as error:
                    failure = error

            self.assertTrue(attempted)
            if swapped:
                self.assertIsNotNone(failure)
                self.assertEqual(list(architecture.iterdir()), [])
                self.assertEqual((displaced / destination.name).read_bytes(), b"new\n")
                self.assertFalse(any(path.name.endswith(".tmp") for path in displaced.iterdir()))
            else:
                self.assertIsNone(failure)
                self.assertEqual(destination.read_bytes(), b"new\n")

    def test_bound_write_contains_a_staging_fault_without_replacing_destination(self) -> None:
        with tempfile.TemporaryDirectory(prefix="pontius-baseline-write-fault-") as directory:
            root = Path(directory).resolve()
            architecture = root / "docs" / "architecture"
            architecture.mkdir(parents=True)
            destination = architecture / "dependency-baseline.toml"
            destination.write_bytes(b"old\n")
            expected = GENERATOR.validate_write_destination(root, destination)

            with mock.patch.object(
                GENERATOR,
                "_write_staged_bytes",
                create=True,
                side_effect=OSError("injected staging failure"),
            ):
                with self.assertRaises(GENERATOR.BaselineError):
                    GENERATOR.write_baseline(expected, b"new\n")

            self.assertEqual(destination.read_bytes(), b"old\n")
            self._assert_failure_temporary_policy(architecture)

    def test_posix_cleanup_does_not_unlink_a_substituted_temporary_entry(self) -> None:
        transaction = GENERATOR._BoundBaselineDirectory(
            Path("/synthetic"),
            Path("/synthetic/docs/architecture/dependency-baseline.toml"),
        )
        transaction._architecture_descriptor = 456
        temporary = GENERATOR._StagedBaseline("temporary.tmp", 123)
        transaction._temporaries.append(temporary)
        handle_info = SimpleNamespace(
            st_dev=1,
            st_ino=10,
            st_mode=GENERATOR.stat.S_IFREG | 0o600,
            st_mtime_ns=1,
            st_size=4,
        )
        substitute_info = SimpleNamespace(
            st_dev=1,
            st_ino=11,
            st_mode=GENERATOR.stat.S_IFREG | 0o600,
            st_mtime_ns=1,
            st_size=5,
        )

        with mock.patch.object(GENERATOR.os, "name", "posix"), mock.patch.object(
            GENERATOR.os,
            "fstat",
            return_value=handle_info,
        ), mock.patch.object(
            GENERATOR.os,
            "stat",
            return_value=substitute_info,
        ), mock.patch.object(GENERATOR.os, "unlink") as unlink, mock.patch.object(
            GENERATOR.os,
            "close",
        ) as close:
            transaction._cleanup_temporary(temporary)

        unlink.assert_not_called()
        close.assert_called_once_with(123)
        self.assertEqual(transaction._temporaries, [])
        self.assertEqual(temporary.state, "closed")

    def test_posix_failure_cleanup_is_close_only_for_an_owned_entry(self) -> None:
        transaction = GENERATOR._BoundBaselineDirectory(
            Path("/synthetic"),
            Path("/synthetic/docs/architecture/dependency-baseline.toml"),
        )
        transaction._architecture_descriptor = 456
        temporary = GENERATOR._StagedBaseline("temporary.tmp", 123)
        transaction._temporaries.append(temporary)
        owned_info = SimpleNamespace(
            st_dev=1,
            st_ino=10,
            st_mode=GENERATOR.stat.S_IFREG | 0o600,
            st_mtime_ns=1,
            st_size=4,
        )

        with mock.patch.object(GENERATOR.os, "name", "posix"), mock.patch.object(
            GENERATOR.os,
            "fstat",
            return_value=owned_info,
        ), mock.patch.object(
            GENERATOR.os,
            "stat",
            return_value=owned_info,
        ), mock.patch.object(GENERATOR.os, "unlink") as unlink, mock.patch.object(
            GENERATOR.os,
            "close",
        ) as close:
            transaction._cleanup_temporary(temporary)

        unlink.assert_not_called()
        close.assert_called_once_with(123)
        self.assertEqual(transaction._temporaries, [])
        self.assertEqual(temporary.state, "closed")

    def test_bound_write_contains_a_replace_fault_without_replacing_destination(self) -> None:
        with tempfile.TemporaryDirectory(prefix="pontius-baseline-replace-fault-") as directory:
            root = Path(directory).resolve()
            architecture = root / "docs" / "architecture"
            architecture.mkdir(parents=True)
            destination = architecture / "dependency-baseline.toml"
            destination.write_bytes(b"old\n")
            expected = GENERATOR.validate_write_destination(root, destination)

            with mock.patch.object(
                GENERATOR,
                "_replace_staged_file",
                create=True,
                side_effect=OSError("injected replacement failure"),
            ):
                with self.assertRaises(GENERATOR.BaselineError):
                    GENERATOR.write_baseline(expected, b"new\n")

            self.assertEqual(destination.read_bytes(), b"old\n")
            self._assert_failure_temporary_policy(architecture)

    @unittest.skipIf(os.name == "nt", "POSIX directory-descriptor mutation test")
    def test_posix_write_rejects_staged_entry_substitution_before_replace(self) -> None:
        with tempfile.TemporaryDirectory(prefix="pontius-baseline-posix-entry-") as directory:
            root = Path(directory).resolve()
            architecture = root / "docs" / "architecture"
            architecture.mkdir(parents=True)
            destination = architecture / "dependency-baseline.toml"
            destination.write_bytes(b"old\n")
            expected = GENERATOR.validate_write_destination(root, destination)
            real_replace = GENERATOR._replace_staged_file

            def substitute_then_replace(
                transaction: object,
                temporary: object,
                destination_name: str,
            ) -> None:
                attacker = architecture / "attacker.tmp"
                attacker.write_bytes(b"evil\n")
                os.replace(attacker, architecture / temporary.name)
                real_replace(transaction, temporary, destination_name)

            with mock.patch.object(
                GENERATOR,
                "_replace_staged_file",
                side_effect=substitute_then_replace,
            ):
                with self.assertRaises(GENERATOR.BaselineError):
                    GENERATOR.write_baseline(expected, b"new\n")

            self.assertEqual(destination.read_bytes(), b"old\n")
            substitutes = [
                path for path in architecture.iterdir() if path.name.endswith(".tmp")
            ]
            self.assertEqual(len(substitutes), 1)
            self.assertEqual(substitutes[0].read_bytes(), b"evil\n")

    @unittest.skipUnless(os.name == "nt", "Windows handle lifecycle test")
    def test_windows_cleanup_retries_disposition_but_closes_only_once(self) -> None:
        transaction = GENERATOR._BoundBaselineDirectory(
            Path("C:/synthetic"),
            Path("C:/synthetic/docs/architecture/dependency-baseline.toml"),
        )
        temporary = GENERATOR._StagedBaseline("temporary.tmp", 123)
        transaction._temporaries.append(temporary)
        disposition_error = GENERATOR.BaselineError("injected disposition failure")

        with mock.patch.object(
            GENERATOR,
            "_windows_dispose_relative_file",
            side_effect=(disposition_error, None),
        ) as dispose, mock.patch.object(
            GENERATOR,
            "_windows_close_file",
            return_value=None,
        ) as close:
            transaction._cleanup_temporary(temporary)

        self.assertEqual(dispose.call_count, 2)
        self.assertEqual(close.call_count, 1)
        self.assertEqual(transaction._temporaries, [])
        self.assertIsNone(temporary.handle)

    @unittest.skipUnless(os.name == "nt", "Windows handle lifecycle test")
    def test_windows_cleanup_never_retries_an_ambiguous_close_failure(self) -> None:
        transaction = GENERATOR._BoundBaselineDirectory(
            Path("C:/synthetic"),
            Path("C:/synthetic/docs/architecture/dependency-baseline.toml"),
        )
        temporary = GENERATOR._StagedBaseline("temporary.tmp", 123)
        temporary.renamed = True
        transaction._temporaries.append(temporary)

        with mock.patch.object(
            GENERATOR,
            "_windows_close_file",
            side_effect=GENERATOR.BaselineError("injected close failure"),
        ) as close:
            with self.assertRaises(GENERATOR.BaselineError) as caught:
                transaction._cleanup_temporary(temporary)

        self.assertEqual(close.call_count, 1)
        self.assertEqual(temporary.state, "close_attempted")
        self.assertIsNone(temporary.handle)
        self.assertIn(temporary, transaction._temporaries)
        self.assertIn(temporary, caught.exception.retained_owners)

    @unittest.skipUnless(os.name == "nt", "Windows handle lifecycle test")
    def test_windows_directory_close_never_retries_an_ambiguous_failure(self) -> None:
        close_error = OSError("injected directory close failure")
        close = mock.Mock(side_effect=(close_error, None))

        with mock.patch.object(
            GENERATOR,
            "_windows_directory_api",
            return_value=(None, None, None, close),
        ):
            with self.assertRaises(GENERATOR.BaselineError) as caught:
                GENERATOR._windows_close_directory(123)

        self.assertEqual(close.call_count, 1)
        self.assertIn(123, caught.exception.retained_owners)

    @unittest.skipUnless(os.name == "nt", "Windows directory lifecycle test")
    def test_windows_directory_api_failure_retains_acquired_handle_ownership(self) -> None:
        api_error = GENERATOR.BaselineError("injected API resolution failure")

        with mock.patch.object(
            GENERATOR,
            "_windows_directory_api",
            side_effect=api_error,
        ):
            with self.assertRaises(GENERATOR.BaselineError) as caught:
                GENERATOR._windows_close_directory(123)

        self.assertIn(123, caught.exception.retained_owners)

    @unittest.skipUnless(os.name == "nt", "Windows directory lifecycle test")
    def test_windows_transaction_never_retries_an_ambiguous_directory_close(self) -> None:
        transaction = GENERATOR._BoundBaselineDirectory(
            Path("C:/synthetic"),
            Path("C:/synthetic/docs/architecture/dependency-baseline.toml"),
        )
        transaction._windows_handles.append(
            (Path("C:/synthetic"), 123, (42, b"i" * 16))
        )
        close_error = GENERATOR.BaselineError("injected directory close failure")

        with mock.patch.object(
            GENERATOR,
            "_windows_close_directory",
            side_effect=close_error,
        ) as close:
            with self.assertRaises(GENERATOR.BaselineError):
                transaction.close()
            with self.assertRaises(GENERATOR.BaselineError):
                transaction.close()

        self.assertEqual(close.call_count, 1)

    def test_posix_transaction_never_retries_an_ambiguous_directory_close(self) -> None:
        transaction = GENERATOR._BoundBaselineDirectory(
            Path("/synthetic"),
            Path("/synthetic/docs/architecture/dependency-baseline.toml"),
        )
        transaction._posix_descriptors.append((Path("/synthetic"), 123, (1, 2)))
        close_error = OSError("injected directory close failure")

        with mock.patch.object(
            GENERATOR.os,
            "close",
            side_effect=close_error,
        ) as close:
            with self.assertRaises(GENERATOR.BaselineError):
                transaction.close()
            with self.assertRaises(GENERATOR.BaselineError):
                transaction.close()

        self.assertEqual(close.call_count, 1)

    @unittest.skipUnless(os.name == "nt", "Windows directory access test")
    def test_windows_directory_open_requests_traverse_without_list_access(self) -> None:
        create = mock.Mock(return_value=123)
        expected_identity = (42, b"i" * 16)

        with mock.patch.object(
            GENERATOR,
            "_windows_directory_api",
            return_value=(create, None, None, None),
        ), mock.patch.object(
            GENERATOR,
            "_windows_directory_handle_identity",
            return_value=expected_identity,
        ):
            handle, identity = GENERATOR._windows_open_directory(Path("C:/synthetic"))

        desired_access = create.call_args.args[1]
        self.assertEqual(handle, 123)
        self.assertEqual(identity, expected_identity)
        self.assertEqual(desired_access & 0x00000001, 0)
        self.assertEqual(desired_access & 0x00000020, 0x00000020)

    @unittest.skipUnless(os.name == "nt", "Windows handle ownership test")
    def test_windows_file_binding_reports_an_ambiguous_handle_close(self) -> None:
        create = mock.Mock(return_value=123)
        close = mock.Mock(return_value=False)
        binding_error = OSError("injected descriptor binding failure")

        with mock.patch.object(
            GENERATOR,
            "_windows_path_api",
            return_value=(create, None, close),
        ), mock.patch.object(
            GENERATOR.msvcrt,
            "open_osfhandle",
            side_effect=binding_error,
        ), mock.patch.object(GENERATOR.ctypes, "get_last_error", return_value=6):
            with self.assertRaises(GENERATOR.BaselineError) as caught:
                GENERATOR._open_regular_no_follow(Path("C:/synthetic.py"))

        self.assertEqual(close.call_count, 1)
        self.assertIn(123, caught.exception.retained_owners)
        self.assertEqual(len(caught.exception.failures), 2)

    def test_posix_directory_binding_retains_a_descriptor_before_fstat(self) -> None:
        transaction = GENERATOR._BoundBaselineDirectory(
            Path("/synthetic"),
            Path("/synthetic/docs/architecture/dependency-baseline.toml"),
        )
        open_directory = mock.Mock(return_value=123)
        supported_dir_fd = {
            open_directory,
            GENERATOR.os.replace,
            GENERATOR.os.stat,
            GENERATOR.os.unlink,
        }

        with mock.patch.object(
            GENERATOR.os,
            "O_DIRECTORY",
            0x10000,
            create=True,
        ), mock.patch.object(
            GENERATOR.os,
            "O_NOFOLLOW",
            0x20000,
            create=True,
        ), mock.patch.object(
            GENERATOR.os,
            "open",
            open_directory,
        ), mock.patch.object(
            GENERATOR.os,
            "supports_dir_fd",
            supported_dir_fd,
        ), mock.patch.object(
            GENERATOR.os,
            "supports_follow_symlinks",
            {GENERATOR.os.stat},
        ), mock.patch.object(
            GENERATOR.os,
            "fstat",
            side_effect=OSError("injected identity failure"),
        ), mock.patch.object(GENERATOR.os, "close") as close:
            with self.assertRaises(GENERATOR.BaselineError):
                transaction._bind_posix()
            transaction.close()

        close.assert_called_once_with(123)

    def test_posix_cleanup_never_retries_an_ambiguous_close_failure(self) -> None:
        transaction = GENERATOR._BoundBaselineDirectory(
            Path("/synthetic"),
            Path("/synthetic/docs/architecture/dependency-baseline.toml"),
        )
        transaction._architecture_descriptor = 456
        temporary = GENERATOR._StagedBaseline("temporary.tmp", 123)
        temporary.renamed = True
        transaction._temporaries.append(temporary)

        close_error = OSError("injected descriptor close failure")
        with mock.patch.object(GENERATOR.os, "name", "posix"), mock.patch.object(
            GENERATOR.os,
            "close",
            side_effect=close_error,
        ) as close:
            with self.assertRaises(GENERATOR.BaselineError):
                transaction._cleanup_temporary(temporary)
            with self.assertRaises(GENERATOR.BaselineError) as caught:
                transaction._cleanup_temporary(temporary)

        self.assertEqual(close.call_count, 1)
        self.assertEqual(temporary.state, "close_attempted")
        self.assertIsNone(temporary.handle)
        self.assertIn(temporary, transaction._temporaries)
        self.assertIn(temporary, caught.exception.retained_owners)

    @unittest.skipUnless(os.name == "nt", "Windows handle lifecycle test")
    def test_windows_cleanup_retains_owner_after_persistent_disposition_fault(self) -> None:
        transaction = GENERATOR._BoundBaselineDirectory(
            Path("C:/synthetic"),
            Path("C:/synthetic/docs/architecture/dependency-baseline.toml"),
        )
        temporary = GENERATOR._StagedBaseline("temporary.tmp", 123)
        transaction._temporaries.append(temporary)

        with mock.patch.object(
            GENERATOR,
            "_windows_dispose_relative_file",
            side_effect=GENERATOR.BaselineError("injected disposition failure"),
        ):
            with self.assertRaises(GENERATOR.BaselineError) as caught:
                transaction._cleanup_temporary(temporary)

        self.assertIn(temporary, transaction._temporaries)
        self.assertEqual(temporary.handle, 123)
        self.assertIn(temporary, caught.exception.retained_owners)


class StabilizationPolicyTests(unittest.TestCase):
    def test_checker_commit_pin_is_independent_from_the_generator_constant(self) -> None:
        baseline = REPOSITORY_ROOT / "docs" / "architecture" / "dependency-baseline.toml"
        drifted_commit = "b" * 40
        forged = baseline.read_bytes().replace(
            BASELINE_COMMIT.encode("ascii"),
            drifted_commit.encode("ascii"),
            1,
        )
        parsed = GENERATOR.parse_baseline_bytes(forged)

        with mock.patch.object(CHECKER._BASELINE, "BASELINE_COMMIT", drifted_commit):
            with self.assertRaises(CHECKER.BoundaryError) as caught:
                CHECKER.authenticate_approved_baseline(parsed)

        self.assertIn("approved mechanical lock", str(caught.exception))

    def test_checker_rejects_a_valid_self_consistent_forged_baseline(self) -> None:
        graph = GENERATOR.scan_sources(
            {
                "src/pontius/__init__.py": b"",
                "src/pontius/a.py": b"from . import b\n",
                "src/pontius/b.py": b"",
            }
        )
        forged = GENERATOR.render_baseline(graph, baseline_commit=BASELINE_COMMIT)
        with tempfile.TemporaryDirectory(prefix="pontius-forged-baseline-") as directory:
            root = Path(directory).resolve()
            source = root / "src" / "pontius"
            source.mkdir(parents=True)
            (source / "__init__.py").write_bytes(b"")
            (source / "a.py").write_bytes(b"from . import b\n")
            (source / "b.py").write_bytes(b"")
            baseline = root / "docs" / "architecture" / "dependency-baseline.toml"
            baseline.parent.mkdir(parents=True)
            baseline.write_bytes(forged)

            with self.assertRaises(CHECKER.BoundaryError) as caught:
                CHECKER.check_repository(root)

        self.assertIn("approved mechanical lock", str(caught.exception))

    def test_source_collection_revalidates_cross_file_identity_changes(self) -> None:
        with tempfile.TemporaryDirectory(prefix="pontius-source-cross-race-") as directory:
            root = Path(directory).resolve()
            source = root / "src" / "pontius"
            source.mkdir(parents=True)
            (source / "__init__.py").write_bytes(b"")
            first = source / "a.py"
            first.write_bytes(b"VALUE = 1\n")
            (source / "b.py").write_bytes(b"VALUE = 2\n")
            replacement = root / "replacement.py"
            replacement.write_bytes(b"VALUE = 1\n")
            real_read = CHECKER._read_regular_source

            def mutate_first_while_reading_second(path: Path, *, root: Path) -> object:
                snapshot = real_read(path, root=root)
                if path.name == "b.py":
                    os.replace(replacement, first)
                return snapshot

            with mock.patch.object(
                CHECKER,
                "_read_regular_source",
                side_effect=mutate_first_while_reading_second,
            ):
                with self.assertRaises(CHECKER.BoundaryError) as caught:
                    CHECKER._collect_sources(root, "src/pontius")

            self.assertIn("identity changed", str(caught.exception))

    def test_source_collection_revalidates_the_complete_python_inventory(self) -> None:
        with tempfile.TemporaryDirectory(prefix="pontius-source-inventory-race-") as directory:
            root = Path(directory).resolve()
            source = root / "src" / "pontius"
            source.mkdir(parents=True)
            (source / "__init__.py").write_bytes(b"")
            (source / "a.py").write_bytes(b"VALUE = 1\n")
            (source / "b.py").write_bytes(b"VALUE = 2\n")
            added = source / "c.py"
            real_read = CHECKER._read_regular_source

            def add_path_while_reading_last(path: Path, *, root: Path) -> object:
                snapshot = real_read(path, root=root)
                if path.name == "b.py":
                    added.write_bytes(b"VALUE = 3\n")
                return snapshot

            with mock.patch.object(
                CHECKER,
                "_read_regular_source",
                side_effect=add_path_while_reading_last,
            ):
                with self.assertRaises(CHECKER.BoundaryError) as caught:
                    CHECKER._collect_sources(root, "src/pontius")

            self.assertIn("source inventory changed", str(caught.exception))

    def test_source_inventory_rejects_noncanonical_python_suffix_case(self) -> None:
        with tempfile.TemporaryDirectory(prefix="pontius-source-suffix-") as directory:
            root = Path(directory).resolve()
            source = root / "src" / "pontius"
            source.mkdir(parents=True)
            (source / "__init__.py").write_bytes(b"")
            (source / "unreviewed.PY").write_bytes(b"import cupy\n")

            with self.assertRaises(CHECKER.BoundaryError) as caught:
                CHECKER._collect_sources(root, "src/pontius")

            self.assertIn("noncanonical Python suffix", str(caught.exception))

    def test_repository_check_revalidates_baseline_identity_after_policy_work(self) -> None:
        with tempfile.TemporaryDirectory(prefix="pontius-final-identity-") as directory:
            root = Path(directory).resolve()
            baseline = _copy_checker_fixture(root)
            real_policy = CHECKER.enforce_orchestration_import_policy

            def mutate_after_policy(sources: object) -> None:
                real_policy(sources)
                replacement = root / "baseline-replacement.toml"
                replacement.write_bytes(baseline.read_bytes())
                os.replace(replacement, baseline)

            with mock.patch.object(
                CHECKER,
                "enforce_orchestration_import_policy",
                side_effect=mutate_after_policy,
            ):
                with self.assertRaises(CHECKER.BoundaryError) as caught:
                    CHECKER.check_repository(root)

            self.assertIn("dependency baseline identity changed", str(caught.exception))

    def test_repository_check_revalidates_source_identity_after_policy_work(self) -> None:
        with tempfile.TemporaryDirectory(prefix="pontius-final-source-identity-") as directory:
            root = Path(directory).resolve()
            _copy_checker_fixture(root)
            source = root / "src" / "pontius" / "__init__.py"
            real_policy = CHECKER.enforce_orchestration_import_policy

            def mutate_after_policy(sources: object) -> None:
                real_policy(sources)
                replacement = root / "source-replacement.py"
                replacement.write_bytes(source.read_bytes())
                os.replace(replacement, source)

            with mock.patch.object(
                CHECKER,
                "enforce_orchestration_import_policy",
                side_effect=mutate_after_policy,
            ):
                with self.assertRaises(CHECKER.BoundaryError) as caught:
                    CHECKER.check_repository(root)

            self.assertIn("Python source identity changed", str(caught.exception))

    def test_only_plan_declared_stabilization_origins_are_classified(self) -> None:
        CHECKER.enforce_origin_classification(
            {
                "src/pontius/evidence/__init__.py": b"",
                "src/pontius/evidence/authorization.py": b"",
            },
            {
                "tools/run_tests.py": b"",
                "tools/test_orchestration/model.py": b"",
            },
        )

        with self.assertRaises(CHECKER.BoundaryError) as caught:
            CHECKER.enforce_origin_classification(
                {"src/pontius/evidence/unplanned.py": b""},
                {"tools/unplanned_runner.py": b""},
            )

        self.assertIn(
            "unclassified stabilization origin: src/pontius/evidence/unplanned.py",
            str(caught.exception),
        )
        self.assertIn(
            "unclassified stabilization origin: tools/unplanned_runner.py",
            str(caught.exception),
        )

    def test_v0a_origin_classification_is_the_exact_six_file_package(self) -> None:
        expected = {
            "src/pontius/v0a/__init__.py",
            "src/pontius/v0a/clock.py",
            "src/pontius/v0a/model.py",
            "src/pontius/v0a/replay.py",
            "src/pontius/v0a/runtime.py",
            "src/pontius/v0a/trace.py",
        }
        actual = {
            path.relative_to(REPOSITORY_ROOT).as_posix()
            for path in (REPOSITORY_ROOT / "src" / "pontius" / "v0a").glob("*.py")
        }
        self.assertEqual(actual, expected)
        CHECKER.enforce_origin_classification(
            {path: b"" for path in expected},
            {},
        )

        for undeclared in (
            "src/pontius/v0a/unplanned.py",
            "src/pontius/v0a.py",
        ):
            with self.subTest(undeclared=undeclared):
                with self.assertRaises(CHECKER.BoundaryError) as caught:
                    CHECKER.enforce_origin_classification(
                        {**{path: b"" for path in expected}, undeclared: b""},
                        {},
                    )
                self.assertIn(
                    f"unclassified stabilization origin: {undeclared}",
                    str(caught.exception),
                )

    def test_v0a_import_policy_allows_only_the_preregistered_dependencies(self) -> None:
        policy = getattr(CHECKER, "enforce_v0a_import_policy", None)
        self.assertTrue(callable(policy), "the v0a import policy is absent")
        permitted = (
            "pontius.action_clock",
            "pontius.preparation_bank",
            "pontius.legal_decision_spine_v2",
            "pontius.no_limit_betting",
            "pontius.holdem_cards",
            "pontius.immutable_blueprint",
        )
        for target in permitted:
            with self.subTest(permitted=target):
                policy({"src/pontius/v0a/runtime.py": _source(f"import {target}\n")})
        policy(
            {
                "src/pontius/v0a/trace.py": _source(
                    "import json\nfrom . import model\n"
                )
            }
        )

        for target in ("pontius.status_generation", "cupy", "tests.fixture"):
            with self.subTest(forbidden=target):
                with self.assertRaises(CHECKER.BoundaryError) as caught:
                    policy(
                        {"src/pontius/v0a/runtime.py": _source(f"import {target}\n")}
                    )
                self.assertIn(
                    f"forbidden v0a import: pontius.v0a.runtime -> {target}",
                    str(caught.exception),
                )

    def test_only_replay_may_import_the_river_or_complete_deal(self) -> None:
        policy = getattr(CHECKER, "enforce_v0a_import_policy", None)
        self.assertTrue(callable(policy), "the v0a import policy is absent")
        policy(
            {
                "src/pontius/v0a/replay.py": _source(
                    "from ..holdem_cards import SixSeatHoldemDeal\n"
                    "from .. import river\n"
                )
            }
        )

        forbidden_sources = (
            "from pontius.holdem_cards import SixSeatHoldemDeal as Deal\n",
            "import pontius.holdem_cards as cards\nvalue = cards.SixSeatHoldemDeal\n",
            "from .. import holdem_cards as cards\n"
            "def deferred():\n"
            "    return cards.SixSeatHoldemDeal\n",
            "from ..holdem_cards import *\n",
        )
        for source in forbidden_sources:
            with self.subTest(source=source):
                with self.assertRaises(CHECKER.BoundaryError) as caught:
                    policy({"src/pontius/v0a/runtime.py": _source(source)})
                self.assertIn("complete-deal", str(caught.exception))

        with self.assertRaises(CHECKER.BoundaryError) as caught:
            policy(
                {
                    "src/pontius/v0a.py": _source(
                        "from pontius.holdem_cards import SixSeatHoldemDeal\n"
                    )
                }
            )
        self.assertIn("complete-deal", str(caught.exception))

        for source in (
            "from pontius.v0a import replay\n",
            "from .replay import ReplayHost\n",
            "import pontius.v0a.replay as host\n",
        ):
            with self.subTest(host_import=source):
                with self.assertRaises(CHECKER.BoundaryError) as caught:
                    policy({"src/pontius/v0a/runtime.py": _source(source)})
                self.assertIn("explicit-deal host", str(caught.exception))

        with self.assertRaises(CHECKER.BoundaryError) as caught:
            policy({"src/pontius/v0a/runtime.py": _source("import pontius.river\n")})
        self.assertIn("pontius.river", str(caught.exception))

    def test_the_real_v0a_package_passes_the_public_boundary_gate(self) -> None:
        CHECKER.check_repository(REPOSITORY_ROOT)

    def test_untouched_legacy_outgoing_edge_change_is_rejected(self) -> None:
        baseline = GENERATOR.scan_sources(
            {
                "src/pontius/__init__.py": b"",
                "src/pontius/a.py": _source("from . import b\n"),
                "src/pontius/b.py": b"",
                "src/pontius/c.py": b"",
            }
        )
        current = GENERATOR.scan_sources(
            {
                "src/pontius/__init__.py": b"",
                "src/pontius/a.py": _source("from . import c\n"),
                "src/pontius/b.py": b"",
                "src/pontius/c.py": b"",
            }
        )

        with self.assertRaises(CHECKER.BoundaryError) as caught:
            CHECKER.enforce_legacy_edges(baseline, current)

        self.assertIn("pontius.a", str(caught.exception))
        self.assertIn("pontius.a -> pontius.b", str(caught.exception))
        self.assertIn("pontius.a -> pontius.c", str(caught.exception))

    def test_evidence_origins_allow_only_siblings_and_durable_journal(self) -> None:
        allowed = {
            "src/pontius/__init__.py": b"",
            "src/pontius/durable_evidence_journal.py": b"",
            "src/pontius/evidence/__init__.py": b"",
            "src/pontius/evidence/errors.py": _source("import pathlib\n"),
            "src/pontius/evidence/good.py": _source(
                "from . import errors\n"
                "from pontius import durable_evidence_journal\n"
            ),
        }
        CHECKER.enforce_evidence_import_policy(allowed)

        denied = dict(allowed)
        denied[
            "src/pontius/"
            "legal_river_quotient_compiled_global_separation_calibration_v7_result.py"
        ] = b""
        denied["src/pontius/evidence/bad.py"] = _source(
            "from pontius import "
            "legal_river_quotient_compiled_global_separation_calibration_v7_result\n"
            "import cupy\n"
            "import tests.fixture\n"
        )
        with self.assertRaises(CHECKER.BoundaryError) as caught:
            CHECKER.enforce_evidence_import_policy(denied)

        message = str(caught.exception)
        self.assertIn(
            "pontius.evidence.bad -> "
            "pontius.legal_river_quotient_compiled_global_separation_calibration_v7_result",
            message,
        )
        self.assertIn("pontius.evidence.bad -> cupy", message)
        self.assertIn("pontius.evidence.bad -> tests.fixture", message)

    def test_new_or_expanded_internal_cycle_is_rejected(self) -> None:
        baseline = GENERATOR.scan_sources(
            {
                "src/pontius/__init__.py": b"",
                "src/pontius/a.py": _source("from . import b\n"),
                "src/pontius/b.py": _source("from . import a\n"),
            }
        )
        current = GENERATOR.scan_sources(
            {
                "src/pontius/__init__.py": b"",
                "src/pontius/a.py": _source("from . import b\nfrom . import c\n"),
                "src/pontius/b.py": _source("from . import a\n"),
                "src/pontius/c.py": _source("from . import a\n"),
            }
        )

        with self.assertRaises(CHECKER.BoundaryError) as caught:
            CHECKER.enforce_no_new_or_expanded_scc(baseline, current)

        self.assertIn("pontius.a, pontius.b, pontius.c", str(caught.exception))


if __name__ == "__main__":
    unittest.main(verbosity=2)
