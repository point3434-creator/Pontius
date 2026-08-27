from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
CHECKER_PATH = REPOSITORY_ROOT / "tools" / "check_stabilization_boundaries.py"


def _load_checker() -> object:
    spec = importlib.util.spec_from_file_location(
        "pontius_orchestration_import_checker_tests", CHECKER_PATH
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("boundary checker could not be loaded by exact path")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


CHECKER = _load_checker()


class OrchestrationImportPolicyTests(unittest.TestCase):
    def test_orchestration_origins_allow_standard_library_and_siblings(self) -> None:
        sources = {
            "tools/run_tests.py": (
                b"import argparse\n"
                b"from tools.test_orchestration import configuration\n"
            ),
            "tools/test_orchestration/__init__.py": b"",
            "tools/test_orchestration/configuration.py": b"import tomllib\n",
            "tools/generate_dependency_baseline.py": b"import ast\n",
            "tools/check_stabilization_boundaries.py": b"import pathlib\n",
        }

        CHECKER.enforce_orchestration_import_policy(sources)

    def test_parent_forbidden_imports_report_every_exact_edge(self) -> None:
        sources = {
            "tools/run_tests.py": (
                b"import pontius\n"
                b"import tests.helper\n"
                b"import experiments.owner\n"
                b"import cupy\n"
                b"from pontius import "
                b"legal_river_quotient_compiled_global_separation_calibration_v7_runner\n"
            ),
        }

        with self.assertRaises(CHECKER.BoundaryError) as caught:
            CHECKER.enforce_orchestration_import_policy(sources)

        message = str(caught.exception)
        for target in (
            "pontius",
            "tests.helper",
            "experiments.owner",
            "cupy",
            "pontius.legal_river_quotient_compiled_global_separation_calibration_v7_runner",
        ):
            with self.subTest(target=target):
                self.assertIn(f"tools.run_tests -> {target}", message)

    def test_non_orchestration_tools_do_not_gain_a_sibling_exemption(self) -> None:
        sources = {
            "tools/generate_dependency_baseline.py": b"import tools.unreviewed_helper\n",
            "tools/unreviewed_helper.py": b"",
        }

        with self.assertRaises(CHECKER.BoundaryError) as caught:
            CHECKER.enforce_orchestration_import_policy(sources)

        self.assertIn(
            "tools.generate_dependency_baseline -> tools.unreviewed_helper",
            str(caught.exception),
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
