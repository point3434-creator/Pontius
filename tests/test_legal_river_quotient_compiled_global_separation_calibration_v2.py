from __future__ import annotations

from hashlib import sha256
import json
import os
from pathlib import Path
import tempfile
import unittest

from pontius import legal_river_quotient_compiled_global_separation_calibration as science
from pontius import legal_river_quotient_compiled_global_separation_calibration_runner as parent
from pontius import legal_river_quotient_compiled_global_separation_calibration_result as parent_reader
from pontius import legal_river_quotient_compiled_global_separation_calibration_v2_runner as successor
from pontius import legal_river_quotient_compiled_global_separation_calibration_v2_result as successor_reader


ROOT = Path(__file__).parents[1]
CONFIG = ROOT / successor.RECOVERY_CONFIG_RELATIVE_PATH
PARENT_RESULT = ROOT / successor.CONSUMED_RESULT_RELATIVE_PATH
RESULT = ROOT / successor.RESULT_RELATIVE_PATH
PARENT_SOURCE = ROOT / "src/pontius/legal_river_quotient_compiled_global_separation_calibration.py"
PARENT_RUNNER = ROOT / "src/pontius/legal_river_quotient_compiled_global_separation_calibration_runner.py"
PARENT_READER = ROOT / "src/pontius/legal_river_quotient_compiled_global_separation_calibration_result.py"
PARENT_LAUNCHER = ROOT / "run_legal_river_quotient_compiled_global_separation_calibration.py"
LAUNCHER = ROOT / "run_legal_river_quotient_compiled_global_separation_calibration_v2.py"


def _canonical_lf(path: Path) -> bytes:
    return path.read_bytes().replace(bytes((13, 10)), bytes((10,)))


class AbsoluteGitCalibrationSuccessorTests(unittest.TestCase):
    def test_config_parent_failure_and_frozen_science_rebind(self) -> None:
        self.assertEqual(
            sha256(_canonical_lf(CONFIG)).hexdigest(), successor.RECOVERY_CONFIG_SHA256
        )
        config = json.loads(CONFIG.read_text(encoding="utf-8"))
        self.assertEqual(config["parent"]["invocation_count"], 1)
        self.assertEqual(config["parent"]["process_exit_code"], 1)
        self.assertFalse(config["parent"]["result_exists"])
        self.assertEqual(
            config["parent"]["failure_classification"],
            "unjournaled_preowner_infrastructure_rejection",
        )
        self.assertEqual(
            sha256(_canonical_lf(PARENT_SOURCE)).hexdigest(),
            config["frozen_science"]["scientific_source_canonical_lf_sha256"],
        )
        self.assertEqual(science.CUDA_SOURCE_SHA256, config["frozen_science"]["literal_cuda_source_sha256"])
        self.assertFalse(PARENT_RESULT.exists())
        self.assertFalse(RESULT.exists())

    def test_absolute_git_identity_and_real_post_scrub_probe(self) -> None:
        before = dict(os.environ)
        evidence = successor.verify_absolute_git()
        self.assertEqual(evidence["path"], str(successor.GIT_PATH))
        probe = successor.source_seal_probe(sha256(b"adr0460-source-seal").hexdigest())
        self.assertIsNone(probe["relative_git_resolution"])
        self.assertTrue(probe["environment_replaced"])
        self.assertTrue(probe["git_version"].startswith("git version "))
        self.assertFalse(probe["compiler_executed"])
        self.assertFalse(probe["cupy_scientific_imported"])
        self.assertFalse(probe["device_queried"])
        self.assertTrue(probe["result_absent"])
        self.assertEqual(dict(os.environ), before)

    def test_parent_bindings_are_fresh_absolute_and_restored(self) -> None:
        original = {name: getattr(parent, name) for name in successor._PARENT_BINDINGS}
        with successor.configured_parent() as engine:
            self.assertEqual(engine.RESULT_PATH, RESULT)
            self.assertEqual(engine.PROTOCOL_SHA256, successor.PROTOCOL_SHA256)
            self.assertEqual(engine.CAMPAIGN_SHA256, successor.CAMPAIGN_SHA256)
            self.assertEqual(engine.PREREGISTRATION_COMMIT, successor.PREREGISTRATION_COMMIT)
            self.assertIs(engine._git, successor._absolute_git)
            self.assertNotEqual(engine.LITERAL_WORKER_MODULE, original["LITERAL_WORKER_MODULE"])
        for name, value in original.items():
            self.assertIs(getattr(parent, name), value) if callable(value) else self.assertEqual(getattr(parent, name), value)

    def test_source_has_no_relative_git_fallback_and_parent_is_immutable(self) -> None:
        text = Path(successor.__file__).read_text(encoding="utf-8")
        self.assertNotIn('["git", *arguments]', text)
        self.assertIn('[str(GIT_PATH), *arguments]', text)
        self.assertIn('"_git": _absolute_git', text)
        self.assertEqual(
            sha256(_canonical_lf(PARENT_RUNNER)).hexdigest(),
            "8f0ad58392ecd533b3166b5340a939d2ff5e01fd047ca9c7a3aadaaf47bea576",
        )
        self.assertEqual(
            sha256(_canonical_lf(PARENT_READER)).hexdigest(),
            "585d4022b1e0279813b1de486710597552c7b153b827105efbff571f79f1d7a4",
        )
        self.assertEqual(
            sha256(_canonical_lf(PARENT_LAUNCHER)).hexdigest(),
            "a0c8bfa3278258e6f272762672018b8c475bc8d2e7d645ca7f36f087cd6556ab",
        )

    def test_fresh_dependency_identity_and_launcher(self) -> None:
        self.assertIn(
            "docs/decisions/ADR-0461-source-seal-the-absolute-git-compiled-calibration-successor.md",
            successor.DEPENDENCY_RELATIVE_PATHS,
        )
        self.assertNotEqual(successor.PROTOCOL_SHA256, parent.PROTOCOL_SHA256)
        self.assertNotEqual(successor.CAMPAIGN_SHA256, parent.CAMPAIGN_SHA256)
        self.assertNotEqual(successor.RESULT_RELATIVE_PATH, parent.RESULT_RELATIVE_PATH)
        launcher = LAUNCHER.read_text(encoding="utf-8")
        self.assertIn("main", launcher)
        self.assertIn("SystemExit", launcher)

    def test_synthetic_terminal_is_exclusive_and_independently_readable(self) -> None:
        adr = ROOT / "docs/decisions/ADR-0461-source-seal-the-absolute-git-compiled-calibration-successor.md"
        if not adr.exists():
            self.skipTest("ADR-0461 is written after successor controls settle")

        def campaign(emit):
            emit(
                "terminal_evidence",
                {
                    "schema_version": "pontius-adr0457-compiled-calibration-terminal-evidence-v1",
                    "terminal": "compiler_rejected",
                    "passed": False,
                    "laboratory_elapsed_ns": 1,
                },
            )
            return {"terminal": "compiler_rejected", "passed": False, "laboratory_elapsed_ns": 1}

        ticks = iter((100, 110, 120, 130, 140))
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "synthetic-v2.jsonl"
            with successor.configured_parent() as engine:
                execution = engine.execute_owner_to_path(
                    output_path=path,
                    campaign_executor=campaign,
                    monotonic_ns=lambda: next(ticks),
                )
            self.assertFalse(execution.terminal["passed"])
            assessed = successor_reader.assess_calibration_bytes(path.read_bytes())
            self.assertFalse(assessed.passed)
            self.assertEqual(assessed.terminal, "compiler_rejected")
            with self.assertRaises(FileExistsError):
                with successor.configured_parent() as engine:
                    engine.execute_owner_to_path(
                        output_path=path,
                        campaign_executor=campaign,
                        monotonic_ns=lambda: 1,
                    )
            mutated = path.read_bytes().replace(b"ADR-0443", b"ADR-0444", 1)
            self.assertNotEqual(mutated, path.read_bytes())
            with self.assertRaises(ValueError):
                successor_reader.assess_calibration_bytes(mutated)

    def test_reader_binding_restores_parent_even_on_failure(self) -> None:
        reader_text = Path(successor_reader.__file__).read_text(encoding="utf-8")
        self.assertNotIn(
            "from .legal_river_quotient_compiled_global_separation_calibration_v2_runner import",
            reader_text,
        )
        self.assertEqual(
            successor_reader.DEPENDENCY_RELATIVE_PATHS,
            successor.DEPENDENCY_RELATIVE_PATHS,
        )
        original = {
            name: getattr(parent_reader, name)
            for name in successor_reader._PARENT_BINDINGS
        }
        with self.assertRaises(ValueError):
            successor_reader.assess_calibration_bytes(b"not a journal\n")
        for name, value in original.items():
            self.assertEqual(getattr(parent_reader, name), value)

    def test_source_seal_remains_result_compiler_and_device_free(self) -> None:
        self.assertFalse(PARENT_RESULT.exists())
        self.assertFalse(RESULT.exists())
        config = json.loads(CONFIG.read_text(encoding="utf-8"))
        self.assertEqual(config["parent"]["compiler_calls"], 0)
        self.assertEqual(config["parent"]["device_queries"], 0)
        self.assertEqual(config["parent"]["kernel_launches"], 0)
        self.assertEqual(config["parent"]["result_rows"], 0)


if __name__ == "__main__":
    unittest.main()
