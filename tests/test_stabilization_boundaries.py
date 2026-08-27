from __future__ import annotations

from hashlib import sha256
import importlib.util
import os
from pathlib import Path
import tempfile
import tomllib
import unittest


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


class DependencyBaselineTests(unittest.TestCase):
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


class StabilizationPolicyTests(unittest.TestCase):
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
