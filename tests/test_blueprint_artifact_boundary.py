"""Source-boundary controls for the portable blueprint artifact round."""
from __future__ import annotations
import importlib.util
from pathlib import Path
import unittest
ROOT = Path(__file__).resolve().parents[1]
CHECKER_PATH = ROOT / "tools" / "check_stabilization_boundaries.py"
SPEC = importlib.util.spec_from_file_location("blueprint_boundary_checker", CHECKER_PATH)
assert SPEC is not None and SPEC.loader is not None
CHECKER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CHECKER)
def assert_public_gate_rejects(test: unittest.TestCase, relative: str, suffix: bytes) -> None:
    path = ROOT / relative
    original = path.read_bytes() if path.exists() else None
    try:
        path.write_bytes((original or b"") + suffix)
        test.assertRaises(CHECKER.BoundaryError, CHECKER.check_repository, ROOT)
    finally:
        if original is None:
            path.unlink()
        else:
            path.write_bytes(original)
class DriverBoundaryAmendmentTests(unittest.TestCase):
    def test_existing_driver_is_scanned_and_the_public_gate_accepts_it(self) -> None:
        CHECKER.enforce_origin_classification({}, {"tools/v0a_rehearsal_driver.py": b""})
        CHECKER.check_repository(ROOT)
    def test_undeclared_driver_siblings_remain_rejected(self) -> None:
        assert_public_gate_rejects(
            self, "tools/v0a_rehearsal_driver_extra.py", b"# owned negative fixture\n")
    def test_driver_import_allowance_is_exact_and_origin_specific(self) -> None:
        allowed = ("import pontius.immutable_blueprint\nimport pontius.v0a.replay\n"
                   "import pontius.v0a.trace\n").encode("ascii")
        CHECKER.enforce_orchestration_import_policy({"tools/v0a_rehearsal_driver.py": allowed})
        self.assertRaises(CHECKER.BoundaryError, CHECKER.enforce_orchestration_import_policy,
                          {"tools/run_tests.py": b"import pontius.immutable_blueprint\n"})
        for relative, suffix in (
            ("tools/v0a_rehearsal_driver.py", b"\nimport pontius.status_generation\n"),
            ("tools/run_tests.py", b"\nimport pontius.immutable_blueprint\n"),
        ):
            assert_public_gate_rejects(self, relative, suffix)
class CodecBoundaryTests(unittest.TestCase):
    def test_codec_family_and_imports_are_exact(self) -> None:
        paths = {
            "src/pontius/blueprint_artifact/__init__.py": b"",
            "src/pontius/blueprint_artifact/codec.py":
                b"from __future__ import annotations\nimport json\n"
                b"import pontius.immutable_blueprint\nimport pontius.no_limit_betting\n",
        }
        CHECKER.enforce_origin_classification(paths, {})
        CHECKER.enforce_blueprint_artifact_import_policy(paths)
        for path, suffix in (
            ("src/pontius/blueprint_artifact.py", b"# owned negative fixture\n"),
            ("src/pontius/blueprint_artifact/extra.py", b"# owned negative fixture\n"),
            ("src/pontius/blueprint_artifact/codec.py", b"\nimport pathlib\n"),
            ("src/pontius/immutable_blueprint.py", b"\nimport pontius.blueprint_artifact.codec\n"),
        ):
            assert_public_gate_rejects(self, path, suffix)
if __name__ == "__main__":
    unittest.main()
