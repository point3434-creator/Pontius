from __future__ import annotations

import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from pontius.runner_harness import (
    artifact_passed,
    assemble_environment,
    finalize_gates,
    load_artifact,
    require_path,
    serialize_result,
)


class RunnerHarnessTests(unittest.TestCase):
    def test_pass_accessor_accepts_each_schema_and_rejects_disagreement(self) -> None:
        self.assertTrue(artifact_passed({"passed": True}))
        self.assertFalse(artifact_passed({"gates": {"passed": False}}))
        self.assertTrue(artifact_passed({"passed": True, "gates": {"passed": True}}))
        for artifact in (
            {},
            {"passed": 1},
            {"passed": None, "gates": {"passed": True}},
            {"passed": True, "gates": {"passed": False}},
        ):
            with self.subTest(artifact=artifact), self.assertRaises(ValueError):
                artifact_passed(artifact)

    def test_load_hashes_before_decode_and_can_require_parent_pass(self) -> None:
        payload = b'{"gates":{"passed":true},"value":3}\n'
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "artifact.json"
            path.write_bytes(payload)
            loaded = load_artifact(
                path,
                expected_sha256=hashlib.sha256(payload).hexdigest(),
                require_passed=True,
            )
            self.assertEqual(loaded.payload["value"], 3)
            with self.assertRaises(ValueError):
                load_artifact(path, expected_sha256="0" * 64)

    def test_required_path_environment_gates_and_serialization_are_canonical(self) -> None:
        self.assertEqual(require_path({"a": {"b": 4}}, ("a", "b"), artifact_name="x"), 4)
        with self.assertRaisesRegex(ValueError, "x lacks required field a.c"):
            require_path({"a": {}}, ("a", "c"), artifact_name="x")
        environment = assemble_environment(
            base={"python": "test", "git": {"dirty": True}},
            runtime={"cuda": "13"}, git={"commit": "abc"}
        )
        self.assertEqual(
            environment,
            {"python": "test", "runtime": {"cuda": "13"}, "git": {"commit": "abc"}},
        )
        finalized = finalize_gates({"schema": True, "finite": False})
        self.assertFalse(finalized["passed"])
        self.assertEqual(finalized["passed"], finalized["gates"]["passed"])
        self.assertEqual(json.loads(serialize_result(finalized)), finalized)


if __name__ == "__main__":
    unittest.main()
