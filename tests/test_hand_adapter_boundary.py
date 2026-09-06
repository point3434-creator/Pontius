"""Real repository boundary gate, including forbidden new incoming edges."""
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    'adapter_boundary', ROOT / 'tools/check_stabilization_boundaries.py')
CHECKER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CHECKER)


class BoundaryTests(unittest.TestCase):
    def test_exact_opening_and_forbidden_origins_edges(self):
        CHECKER.check_repository(ROOT)
        for path, suffix in (
                ('src/pontius/hand_scenario/extra.py', b'# extra\n'),
                ('tools/v0a_hand_adapter_extra.py', b'# extra\n'),
                ('src/pontius/hand_scenario/codec.py', b'\nimport pathlib\n'),
                ('src/pontius/v0a/runtime.py', b'\nimport pontius.hand_scenario.codec\n'),
                ('src/pontius/immutable_blueprint.py', b'\nimport pontius.hand_scenario.codec\n'),
                ('tools/run_tests.py', b'\nimport pontius.blueprint_artifact.codec\n'),
                ('tools/v0a_hand_adapter.py', b'\nimport pontius.immutable_blueprint\n')):
            target = ROOT / path
            original = target.read_bytes() if target.exists() else None
            try:
                target.write_bytes((original or b'') + suffix)
                with self.subTest(path=path):
                    self.assertRaises(CHECKER.BoundaryError, CHECKER.check_repository, ROOT)
            finally:
                target.unlink() if original is None else target.write_bytes(original)


if __name__ == '__main__':
    unittest.main()
