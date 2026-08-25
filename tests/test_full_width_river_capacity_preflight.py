from __future__ import annotations

import importlib.util
import inspect
import json
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path

from pontius.full_width_factor_tt_capacity import (
    FactorTTHalfAllocation,
    FactorTTPersistentAllocation,
)
from pontius.full_width_river_capacity_preflight import (
    _capacity_admission,
    _parse_config,
    _small_control,
    _street_inventory,
    _typed_failure_result,
    _write_exclusive,
)

_ROOT = Path(__file__).parents[1]
_CONFIG = _ROOT / "experiments/configs/full-width-river-capacity-preflight-v1.json"


class FullWidthRiverCapacityPreflightTests(unittest.TestCase):
    def parsed(self) -> dict[str, object]:
        return _parse_config(json.loads(_CONFIG.read_text(encoding="utf-8")))

    def test_config_freezes_capacity_not_an_outcome(self) -> None:
        config = json.loads(_CONFIG.read_text(encoding="utf-8"))
        parsed = _parse_config(config)

        self.assertEqual(parsed["street_widths"], (1225, 1081, 1035, 990))
        self.assertEqual(parsed["controlled_seat"], 3)
        self.assertEqual(parsed["gates"]["street_action_wall_ms"], 15_000.0)
        self.assertEqual(parsed["gates"]["maximum_warm_contraction_ms"], 14_000.0)
        self.assertNotIn("expected_capacity_admitted", config)
        self.assertNotIn("expected_terminal", config)
        self.assertNotIn("expected_topology_numeric_bytes", config)
        self.assertNotIn("expected_warm_contraction_ms", config)

    def test_street_inventory_uses_every_literal_axis(self) -> None:
        parsed = self.parsed()
        river, rows = _street_inventory(parsed)

        self.assertEqual(
            tuple(row["opponent_hand_counts"][0] for row in rows),
            parsed["street_widths"],
        )
        self.assertTrue(
            all(
                row["opponent_hand_counts"]
                == [parsed["street_widths"][index]] * 5
                for index, row in enumerate(rows)
            )
        )
        self.assertEqual(len(river.hand_axis), 990)
        self.assertEqual(len(river.cards.remaining_deck), 45)

    def test_synthetic_over_cap_model_fails_the_preallocation_guard(self) -> None:
        parsed = self.parsed()
        allocation = FactorTTPersistentAllocation(
            hand_counts=(4, 4, 4, 1, 4, 4),
            split_index=3,
            left=FactorTTHalfAllocation(seats=3, records=10_000),
            right=FactorTTHalfAllocation(seats=3, records=100),
        )
        gates = dict(parsed["gates"])
        gates["maximum_host_persistent_numeric_bytes"] = 1_000
        gates["maximum_device_resident_numeric_bytes"] = 1_000
        checks = _capacity_admission(
            allocation=allocation,
            optimistic_scalar_bytes=allocation.base_topology_numeric_bytes,
            host_available_bytes=10_000,
            device_free_bytes=10_000,
            gates=gates,
        )

        self.assertFalse(all(checks.values()))

    def test_provenance_resource_and_semantic_mutations_fail_closed(self) -> None:
        config = json.loads(_CONFIG.read_text(encoding="utf-8"))
        mutations = []
        source = deepcopy(config)
        source["expected_capacity_model_sha256"] = "0" * 64
        mutations.append(source)
        width = deepcopy(config)
        width["street_widths"][-1] = 989
        mutations.append(width)
        wall = deepcopy(config)
        wall["gates"]["maximum_warm_contraction_ms"] = 13_999.0
        mutations.append(wall)
        claim = deepcopy(config)
        claim["claims_policy"] = "strategy_quality"
        mutations.append(claim)
        for mutation in mutations:
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                _parse_config(mutation)

    def test_target_source_has_no_cartesian_materialization_call(self) -> None:
        from pontius import full_width_river_capacity_preflight as subject

        module_source = inspect.getsource(subject)
        target_source = inspect.getsource(subject._run_target)
        self.assertNotIn(".materialize(", module_source)
        self.assertNotIn(".to_dense(", module_source)
        self.assertIn("if admitted:", target_source)
        self.assertLess(
            target_source.index("if admitted:"),
            target_source.index("_six_axis_belief("),
        )

    def test_result_writer_is_exclusive_and_byte_bounded(self) -> None:
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

    def test_typed_failure_is_terminal_and_emits_nothing(self) -> None:
        result = _typed_failure_result(
            MemoryError("bounded target allocation failed"),
            git={"commit": "a" * 40, "dirty": False},
            evidence_stage="source_sealed",
        )

        self.assertFalse(result["passed"])
        self.assertEqual(result["terminal"], "typed_failure")
        self.assertEqual(result["failure"]["type"], "MemoryError")
        self.assertEqual(
            result["emissions"],
            {
                "actions": 0,
                "strategy_labels": 0,
                "strategy_quality_rows": 0,
                "quality_claim": None,
            },
        )

    @unittest.skipUnless(importlib.util.find_spec("cupy"), "optional CuPy control")
    def test_reduced_complete_path_control_is_exact_and_label_free(self) -> None:
        control = _small_control(self.parsed())
        workload = control["workload"]

        self.assertLessEqual(workload["prime_warm_maximum_repeat_error"], 1e-10)
        self.assertLessEqual(workload["scalar_resident_expectation_error"], 1e-10)
        self.assertTrue(all(workload["allocation_model_matches"].values()))
        self.assertTrue(workload["finite"])
        self.assertEqual(workload["actions_emitted"], 0)
        self.assertEqual(workload["strategy_labels_emitted"], 0)
        self.assertEqual(workload["quality_rows_emitted"], 0)
        self.assertEqual(workload["strategy_quality_evaluations"], 0)


if __name__ == "__main__":
    unittest.main()
