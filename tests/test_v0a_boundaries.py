"""Slice-C boundary tests: v0a origin classification and import policy.

These exercise the real checker functions with real source bytes; the whole
repository check runs too, so a policy that only passes on synthetic input
cannot pass here.
"""

from __future__ import annotations

import importlib.util
import os
import shutil
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
CHECKER_PATH = REPOSITORY_ROOT / "tools" / "check_stabilization_boundaries.py"
BASELINE_PATH = REPOSITORY_ROOT / "docs" / "architecture" / "dependency-baseline.toml"

# ADR-0485 pins the legacy dependency baseline by blob id. Slice C classifies
# the new package; it never regenerates the lock to absorb it.
PINNED_BASELINE_BLOB = "5fe6ee47f3380b65887b528efef05b72c8e6ac0a"


def _load_exact(name: str, path: Path) -> object:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not load {path.name} by exact path")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


CHECKER = _load_exact("pontius_boundary_checker_v0a_tests", CHECKER_PATH)


def _source(text: str) -> bytes:
    return text.encode("utf-8")


class LegacyBaselineIsPinnedTests(unittest.TestCase):
    """The lock is preserved byte-for-byte, never regenerated."""

    def test_the_baseline_blob_matches_the_adr_pin(self) -> None:
        git = os.environ.get("PONTIUS_GIT")
        self.assertTrue(git, "PONTIUS_GIT must name the absolute Git executable")
        blob = subprocess.run(
            [git, "-C", str(REPOSITORY_ROOT), "rev-parse", "HEAD:docs/architecture/dependency-baseline.toml"],
            capture_output=True, text=True, check=True,
        ).stdout.strip()
        self.assertEqual(
            blob,
            PINNED_BASELINE_BLOB,
            "the legacy dependency baseline was regenerated; ADR-0485 forbids it",
        )

    def test_the_baseline_file_is_unmodified_in_the_working_tree(self) -> None:
        git = os.environ.get("PONTIUS_GIT")
        changed = subprocess.run(
            [git, "-C", str(REPOSITORY_ROOT), "status", "--porcelain",
             "docs/architecture/dependency-baseline.toml"],
            capture_output=True, text=True, check=True,
        ).stdout.strip()
        self.assertEqual(changed, "", "the pinned baseline has working-tree edits")


class V0aOriginClassificationTests(unittest.TestCase):
    """Every v0a source file is declared by name; no wildcard."""

    def test_the_declared_set_matches_the_package_on_disk(self) -> None:
        on_disk = {
            f"src/pontius/v0a/{path.name}"
            for path in (REPOSITORY_ROOT / "src" / "pontius" / "v0a").glob("*.py")
        }
        self.assertEqual(set(CHECKER.V0A_ORIGIN_PATHS), on_disk)

    def test_an_undeclared_v0a_file_is_rejected(self) -> None:
        sources = {path: b"" for path in CHECKER.V0A_ORIGIN_PATHS}
        sources["src/pontius/v0a/smuggled.py"] = _source("x = 1\n")
        with self.assertRaises(CHECKER.BoundaryError) as caught:
            CHECKER.enforce_origin_classification(sources, {})
        self.assertIn("smuggled.py", str(caught.exception))

    def test_the_declared_files_are_accepted(self) -> None:
        sources = {path: b"" for path in CHECKER.V0A_ORIGIN_PATHS}
        CHECKER.enforce_origin_classification(sources, {})


class V0aImportPolicyTests(unittest.TestCase):
    """ADR-0485's allowlist, including the host-only river exception."""

    def policy(self, sources: dict[str, bytes]) -> None:
        CHECKER.enforce_v0a_import_policy(sources)

    def test_the_permitted_kernels_are_allowed(self) -> None:
        for permitted in sorted(CHECKER.V0A_PERMITTED_INTERNAL):
            with self.subTest(permitted):
                self.policy(
                    {"src/pontius/v0a/runtime.py": _source(f"import {permitted}\n")}
                )

    def test_a_foreign_internal_import_is_rejected(self) -> None:
        for forbidden in ("pontius.river", "pontius.status_generation", "pontius.river_oracle"):
            with self.subTest(forbidden):
                with self.assertRaises(CHECKER.BoundaryError):
                    self.policy(
                        {"src/pontius/v0a/runtime.py": _source(f"import {forbidden}\n")}
                    )

    def test_only_the_explicit_deal_host_may_use_the_river_evaluator(self) -> None:
        # permitted for the host
        self.policy({"src/pontius/v0a/replay.py": _source("import pontius.river\n")})
        # refused for every policy module
        for module in ("runtime", "model", "clock", "trace"):
            with self.subTest(module):
                with self.assertRaises(CHECKER.BoundaryError):
                    self.policy(
                        {f"src/pontius/v0a/{module}.py": _source("import pontius.river\n")}
                    )

    def test_a_policy_module_may_not_import_the_host(self) -> None:
        """This isolation is what keeps the complete deal out of selection."""

        for module in ("runtime", "model", "clock", "trace"):
            with self.subTest(module):
                with self.assertRaises(CHECKER.BoundaryError) as caught:
                    self.policy(
                        {
                            f"src/pontius/v0a/{module}.py": _source(
                                "import pontius.v0a.replay\n"
                            )
                        }
                    )
                self.assertIn("explicit-deal host", str(caught.exception))

    def test_siblings_and_stdlib_are_allowed(self) -> None:
        self.policy(
            {
                "src/pontius/v0a/trace.py": _source(
                    "import json\nimport pontius.v0a.model\n"
                )
            }
        )

    def test_the_real_package_satisfies_its_own_policy(self) -> None:
        sources = {
            f"src/pontius/v0a/{path.name}": path.read_bytes()
            for path in (REPOSITORY_ROOT / "src" / "pontius" / "v0a").glob("*.py")
        }
        self.assertTrue(sources)
        self.policy(sources)


NON_HOST_ORIGINS = (
    "src/pontius/v0a/__init__.py",
    "src/pontius/v0a/model.py",
    "src/pontius/v0a/clock.py",
    "src/pontius/v0a/runtime.py",
    "src/pontius/v0a/trace.py",
)
COMPLETE_DEAL_IMPORTS = (
    "from pontius.holdem_cards import SixSeatHoldemDeal\n",
    "from pontius.holdem_cards import SixSeatHoldemDeal as Deal\n",
    "from ..holdem_cards import SixSeatHoldemDeal\n",
    "from ..holdem_cards import SixSeatHoldemDeal as Deal\n",
    "import pontius.holdem_cards\nvalue = pontius.holdem_cards.SixSeatHoldemDeal\n",
    "import pontius.holdem_cards as cards\nvalue = cards.SixSeatHoldemDeal\n",
    "from pontius import holdem_cards as cards\nvalue = cards.SixSeatHoldemDeal\n",
    "from .. import holdem_cards as cards\nvalue = cards.SixSeatHoldemDeal\n",
    "from pontius.holdem_cards import *\n",
    "from ..holdem_cards import *\n",
    "value = SixSeatHoldemDeal\n",
    "value = cards.SixSeatHoldemDeal\n",
)


def _import_contexts(fragment: str) -> tuple[str, ...]:
    nested = "if True:\n" + textwrap.indent(fragment, "    ")
    typed = "from typing import TYPE_CHECKING\nif TYPE_CHECKING:\n"
    contexts = (fragment, nested, typed + textwrap.indent(fragment, "    "))
    if "import *" not in fragment:
        contexts += ("def deferred():\n" + textwrap.indent(fragment, "    "),)
    return contexts


class V0aCompleteDealBoundaryTests(unittest.TestCase):
    """Static trusted-component separation, using a complete real source map."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.sources = {
            path.relative_to(REPOSITORY_ROOT).as_posix(): path.read_bytes()
            for path in (REPOSITORY_ROOT / "src" / "pontius").rglob("*.py")
        }

    def policy_with(self, origin: str, fragment: str) -> None:
        sources = dict(self.sources)
        sources[origin] = _source(fragment)
        CHECKER.enforce_v0a_import_policy(sources)

    def test_complete_deal_is_refused_from_every_non_host_origin(self) -> None:
        for origin in NON_HOST_ORIGINS:
            for fragment in COMPLETE_DEAL_IMPORTS:
                for source in _import_contexts(fragment):
                    with self.subTest(origin=origin, source=source):
                        with self.assertRaises(CHECKER.BoundaryError) as caught:
                            self.policy_with(origin, source)
                        self.assertIn("complete-deal", str(caught.exception))

    def test_replay_retains_complete_deal_access_in_every_import_form(self) -> None:
        for fragment in COMPLETE_DEAL_IMPORTS:
            for source in _import_contexts(fragment):
                with self.subTest(source=source):
                    self.policy_with("src/pontius/v0a/replay.py", source)

    def test_visible_state_comments_and_strings_remain_allowed(self) -> None:
        permitted = (
            "from pontius.holdem_cards import OneSeatCardState\n",
            "from ..holdem_cards import OneSeatCardState as Visible\n",
            "import pontius.holdem_cards as cards\nvalue = cards.OneSeatCardState\n",
            "from .. import holdem_cards as cards\nvalue = cards.OneSeatCardState\n",
            "# from pontius.holdem_cards import SixSeatHoldemDeal\nvalue = 1\n",
            'value = "SixSeatHoldemDeal and cards.SixSeatHoldemDeal"\n',
            'value = "from ..holdem_cards import *"\n',
        )
        for origin in NON_HOST_ORIGINS:
            for fragment in permitted:
                for source in _import_contexts(fragment):
                    with self.subTest(origin=origin, source=source):
                        self.policy_with(origin, source)

    def test_host_import_remains_refused_with_complete_module_resolution(self) -> None:
        forbidden = (
            "import pontius.v0a.replay\n",
            "import pontius.v0a.replay as host\n",
            "from pontius.v0a import replay\n",
            "from pontius.v0a import replay as host\n",
            "from . import replay as host\n",
            "from .replay import run_hand\n",
            "from .replay import *\n",
        )
        for origin in NON_HOST_ORIGINS:
            for source in forbidden:
                with self.subTest(origin=origin, source=source):
                    with self.assertRaises(CHECKER.BoundaryError) as caught:
                        self.policy_with(origin, source)
                    self.assertIn("explicit-deal host", str(caught.exception))

    def test_invalid_source_has_a_normalized_boundary_refusal(self) -> None:
        for origin in NON_HOST_ORIGINS:
            for raw in (b"def broken(:\n", b"value = '\xff'\n", b"value = 1\x00\n"):
                with self.subTest(origin=origin, raw=raw):
                    sources = dict(self.sources)
                    sources[origin] = raw
                    with self.assertRaises(CHECKER.BoundaryError):
                        CHECKER.enforce_v0a_import_policy(sources)

class WholeRepositoryGateTests(unittest.TestCase):
    """The real gate, end to end, with the v0a package present."""

    def test_the_repository_check_passes(self) -> None:
        CHECKER.check_repository(REPOSITORY_ROOT)


    def test_complete_deal_import_is_refused_by_the_real_repository_gate(self) -> None:
        with tempfile.TemporaryDirectory(prefix="pontius-v0a-boundary-") as directory:
            root = Path(directory)
            for relative in ("src", "tools"):
                shutil.copytree(REPOSITORY_ROOT / relative, root / relative)
            baseline = root / "docs" / "architecture" / "dependency-baseline.toml"
            baseline.parent.mkdir(parents=True)
            baseline.write_bytes(BASELINE_PATH.read_bytes())
            for relative, source in (
                ("src/pontius/v0a/runtime.py", COMPLETE_DEAL_IMPORTS[1]),
                ("src/pontius/v0a/__init__.py", COMPLETE_DEAL_IMPORTS[9]),
            ):
                with self.subTest(origin=relative):
                    path = root / relative
                    original = path.read_bytes()
                    try:
                        path.write_bytes(_source(source))
                        with self.assertRaises(CHECKER.BoundaryError) as caught:
                            CHECKER.check_repository(root)
                        self.assertIn("complete-deal", str(caught.exception))
                    finally:
                        path.write_bytes(original)

def main() -> int:
    result = unittest.main(module=__name__, exit=False, verbosity=1).result
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(main())
