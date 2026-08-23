from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from pontius.runner_harness_v2 import (
    load_artifact,
    load_config,
    require_passing_artifact_schema,
)


def _config_schema(payload: dict[str, object]) -> None:
    if set(payload) != {"schema", "nested"} or payload["schema"] != "test-v1":
        raise ValueError("config schema differs")
    nested = payload["nested"]
    if not isinstance(nested, dict) or set(nested) != {"values"}:
        raise ValueError("config nested schema differs")


class RunnerHarnessV2Tests(unittest.TestCase):
    def test_config_is_one_exact_immutable_byte_snapshot(self) -> None:
        raw = b'{"schema":"test-v1","nested":{"values":[1,2]}}\n'
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "config.json"
            path.write_bytes(raw)
            loaded = load_config(
                path,
                expected_sha256=hashlib.sha256(raw).hexdigest(),
                schema_validator=_config_schema,
            )
            path.write_bytes(b'{"schema":"changed"}\n')

        self.assertEqual(loaded.raw_bytes, raw)
        self.assertEqual(loaded.sha256, hashlib.sha256(raw).hexdigest())
        self.assertEqual(loaded.payload["nested"]["values"], (1, 2))
        with self.assertRaises(TypeError):
            loaded.payload["schema"] = "mutated"  # type: ignore[index]
        with self.assertRaises(TypeError):
            loaded.payload["nested"]["values"] = ()  # type: ignore[index]

    def test_duplicate_keys_nonfinite_constants_and_oversize_fail_closed(self) -> None:
        cases = (
            b'{"schema":"test-v1","schema":"test-v1","nested":{"values":[]}}',
            b'{"schema":"test-v1","nested":{"values":[NaN]}}',
            b'{"schema":"test-v1","nested":{"values":[Infinity]}}',
        )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "input.json"
            for raw in cases:
                with self.subTest(raw=raw):
                    path.write_bytes(raw)
                    with self.assertRaises(ValueError):
                        load_config(path, schema_validator=_config_schema)
            path.write_bytes(b"{}" * 100)
            with self.assertRaisesRegex(ValueError, "byte limit"):
                load_config(
                    path,
                    schema_validator=_config_schema,
                    maximum_bytes=10,
                )

    def test_passing_artifact_requires_explicit_complete_schema(self) -> None:
        payload = {
            "schema": "evidence-v1",
            "passed": True,
            "gates": {"quality": True, "passed": True},
            "measurement": {"value": 3.0},
        }
        raw = (json.dumps(payload, allow_nan=False) + "\n").encode()

        def validator(candidate: dict[str, object]) -> None:
            if candidate.get("schema") != "evidence-v1":
                raise ValueError("artifact schema differs")
            require_passing_artifact_schema(
                candidate,
                required_paths=(("gates", "quality"), ("measurement", "value")),
            )

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "artifact.json"
            path.write_bytes(raw)
            loaded = load_artifact(path, schema_validator=validator)
            self.assertTrue(loaded.payload["passed"])

            path.write_text('{"passed":true}\n', encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "schema differs"):
                load_artifact(path, schema_validator=validator)

        with self.assertRaisesRegex(ValueError, "required fields"):
            require_passing_artifact_schema(
                {"passed": True},
                required_paths=(),
            )

    def test_schema_validator_is_mandatory(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "input.json"
            path.write_text("{}\n", encoding="utf-8")
            with self.assertRaisesRegex(TypeError, "schema validator"):
                load_config(path, schema_validator=None)  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main()
