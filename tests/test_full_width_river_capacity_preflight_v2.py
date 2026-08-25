from __future__ import annotations

import hashlib
import importlib.util
import inspect
import json
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path

from pontius.full_width_river_capacity_preflight_v2 import (
    _parse_config,
    _runtime_snapshot,
    _typed_failure_result,
    _write_exclusive,
)

_ROOT = Path(__file__).parents[1]
_CONFIG = _ROOT / "experiments/configs/full-width-river-capacity-preflight-v2.json"
_V1_RESULT = (
    _ROOT / "experiments/results/full-width-river-capacity-preflight-v1.json"
)
_V2_RESULT = (
    _ROOT / "experiments/results/full-width-river-capacity-preflight-v2.json"
)


class FullWidthRiverCapacityPreflightV2Tests(unittest.TestCase):
    def parsed(self) -> dict[str, object]:
        return _parse_config(json.loads(_CONFIG.read_text(encoding="utf-8")))

    def test_overlay_binds_v1_and_contains_no_target_outcome(self) -> None:
        config = json.loads(_CONFIG.read_text(encoding="utf-8"))
        parsed = _parse_config(config)

        self.assertEqual(
            parsed["target_semantics"],
            "exact_adr0363_target_unchanged_only_windows_process_memory_abi_replaced",
        )
        self.assertEqual(parsed["required_process_counter_struct_bytes"], 80)
        self.assertEqual(
            parsed["v1"]["street_widths"],
            (1225, 1081, 1035, 990),
        )
        serialized = json.dumps(config, sort_keys=True).lower()
        for forbidden in (
            "expected_capacity_admitted",
            "expected_terminal",
            "expected_topology_numeric_bytes",
            "expected_warm_contraction_ms",
            "representation_rejected_before_target_allocation",
            "literal_full_width_warm_contraction_completed",
        ):
            self.assertNotIn(forbidden, serialized)

    def test_parent_failure_is_exact_and_v2_result_is_absent(self) -> None:
        parsed = self.parsed()
        raw = _V1_RESULT.read_bytes()

        self.assertEqual(
            hashlib.sha256(raw).hexdigest(),
            parsed["expected_v1_result_sha256"],
        )
        self.assertFalse(_V2_RESULT.exists())

    def test_provenance_semantic_and_telemetry_mutations_fail_closed(self) -> None:
        config = json.loads(_CONFIG.read_text(encoding="utf-8"))
        mutations = []
        source = deepcopy(config)
        source["expected_v1_result_sha256"] = "0" * 64
        mutations.append(source)
        semantics = deepcopy(config)
        semantics["target_semantics"] = "changed_target"
        mutations.append(semantics)
        structure = deepcopy(config)
        structure["required_process_counter_struct_bytes"] = 79
        mutations.append(structure)
        allowance = deepcopy(config)
        allowance["maximum_process_memory_cross_source_delta_bytes"] += 1
        mutations.append(allowance)
        for mutation in mutations:
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                _parse_config(mutation)

    def test_v2_does_not_patch_or_call_the_closed_v1_telemetry_and_writer(self) -> None:
        from pontius import full_width_river_capacity_preflight_v2 as subject

        source = inspect.getsource(subject)
        self.assertNotIn("v1._host_memory_snapshot", source)
        self.assertNotIn("v1._runtime_snapshot", source)
        self.assertNotIn("v1._write_exclusive", source)
        self.assertNotIn("setattr(v1", source)
        self.assertIn("v1._small_control", source)
        self.assertIn("v1._run_target", source)

    @unittest.skipUnless(importlib.util.find_spec("cupy"), "optional CuPy control")
    def test_outcome_free_runtime_seam_reaches_the_pinned_gpu(self) -> None:
        _, runtime, telemetry = _runtime_snapshot(self.parsed())

        self.assertTrue(telemetry["passed"])
        self.assertEqual(runtime["device_name"], "NVIDIA GeForce RTX 5080")
        self.assertEqual(runtime["compute_capability"], "120")
        self.assertGreater(runtime["host_available_physical_bytes"], 0)
        self.assertGreater(runtime["device_free_bytes"], 0)

    def test_result_writer_is_exclusive_and_bounded(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "result.json"
            _write_exclusive(path, b"first\n", maximum_bytes=16)
            self.assertEqual(path.read_bytes(), b"first\n")
            with self.assertRaises(FileExistsError):
                _write_exclusive(path, b"second\n", maximum_bytes=16)
            with self.assertRaises(ValueError):
                _write_exclusive(
                    Path(directory) / "large.json",
                    b"x" * 17,
                    maximum_bytes=16,
                )

    def test_typed_failure_retains_zero_emissions(self) -> None:
        result = _typed_failure_result(
            RuntimeError("synthetic typed failure"),
            git={"commit": "a" * 40, "dirty": False},
            evidence_stage="source_sealed",
        )

        self.assertIs(result["passed"], False)
        self.assertEqual(result["terminal"], "typed_failure")
        self.assertEqual(
            result["emissions"],
            {
                "actions": 0,
                "strategy_labels": 0,
                "strategy_quality_rows": 0,
                "quality_claim": None,
            },
        )


if __name__ == "__main__":
    unittest.main()
