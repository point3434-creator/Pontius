from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import unittest

from pontius.sparse_incidence_audit import parse_sparse_incidence_audit_config


_ROOT = Path(__file__).parents[1]
_CONFIG = (
    _ROOT
    / "experiments"
    / "configs"
    / "sparse-incidence-open-mode-audit-v1.json"
)


class SparseIncidenceAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.config = json.loads(_CONFIG.read_text(encoding="utf-8"))

    def test_frozen_config_parses_with_validation_family_and_memory_bill(self) -> None:
        parsed = parse_sparse_incidence_audit_config(self.config)
        self.assertEqual(parsed["hands_per_player"], (7, 16, 32))
        self.assertEqual(parsed["range_families"], ("balanced", "blocker_heavy"))
        self.assertEqual(parsed["validation_speed_family"], "blocker_heavy")
        self.assertEqual(parsed["maximum_feature_width_per_batch"], 96)
        self.assertEqual(
            parsed["gates"]["maximum_h32_sparse_peak_numeric_bytes"],
            600_000_000,
        )
        self.assertEqual(
            parsed["gates"]["minimum_validation_h32_speedup"],
            5.0,
        )

    def test_stage_hash_workload_backend_and_gate_mutations_fail(self) -> None:
        mutations = []

        stage = deepcopy(self.config)
        stage["evidence_stage"] = "validation_revealed"
        mutations.append(stage)

        source = deepcopy(self.config)
        source["expected_sparse_backend_sha256"] = "0" * 64
        mutations.append(source)

        validation = deepcopy(self.config)
        validation["validation_speed_family"] = "balanced"
        mutations.append(validation)

        workload = deepcopy(self.config)
        workload["hands_per_player"] = [7, 32]
        mutations.append(workload)

        cap = deepcopy(self.config)
        cap["maximum_feature_width_per_batch"] = 384
        mutations.append(cap)

        version = deepcopy(self.config)
        version["required_scipy_version"] = "latest"
        mutations.append(version)

        speed = deepcopy(self.config)
        speed["gates"]["minimum_validation_h32_speedup"] = 1.0
        mutations.append(speed)

        memory = deepcopy(self.config)
        memory["gates"]["maximum_h32_sparse_peak_numeric_bytes"] = 1_000_000_000
        mutations.append(memory)

        extra = deepcopy(self.config)
        extra["best_observed_backend"] = "csr"
        mutations.append(extra)

        for mutation in mutations:
            with self.subTest(mutation=mutation):
                with self.assertRaises(ValueError):
                    parse_sparse_incidence_audit_config(mutation)


if __name__ == "__main__":
    unittest.main()
