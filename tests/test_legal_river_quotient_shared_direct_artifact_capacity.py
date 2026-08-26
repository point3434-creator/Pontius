from __future__ import annotations

import ast
from copy import deepcopy
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import pontius.legal_river_quotient_shared_direct_artifact_capacity as source
import pontius.legal_river_quotient_shared_direct_artifact_capacity_result as reader
import pontius.legal_river_quotient_shared_direct_artifact_capacity_runner as runner


ROOT = Path(__file__).parents[1]
CONFIG = ROOT / source.CONFIG_RELATIVE_PATH
INPUT = ROOT / source.INPUT_RELATIVE_PATH
RESULT = ROOT / source.RESULT_RELATIVE_PATH
RETAINED_RESULT_SHA256 = (
    "9e6e3d45797eb9aeea8e91994f67e7ff641747a80a8d240799adfab1325961af"
)
SOURCE = ROOT / "src/pontius/legal_river_quotient_shared_direct_artifact_capacity.py"
RUNNER = ROOT / "src/pontius/legal_river_quotient_shared_direct_artifact_capacity_runner.py"
READER = ROOT / "src/pontius/legal_river_quotient_shared_direct_artifact_capacity_result.py"


def _source_endpoints(
    *, phase_ns: int = 1, gap_10: int = 0, gap_22: int = 0
) -> tuple[source.EndpointObservation, source.EndpointObservation]:
    phases = {phase: phase_ns for phase in source.PHASE_ORDER}
    campaign = phase_ns * len(source.PHASE_ORDER)
    return (
        source.endpoint_observation(
            10,
            phases,
            population_elapsed_host_ns=campaign + gap_10,
        ),
        source.endpoint_observation(
            22,
            phases,
            population_elapsed_host_ns=campaign + gap_22,
        ),
    )


def _reader_endpoints(
    endpoints: tuple[source.EndpointObservation, source.EndpointObservation],
) -> tuple[reader.Endpoint, reader.Endpoint]:
    return tuple(
        reader.Endpoint(
            endpoint.population,
            endpoint.phase_host_ns,
            endpoint.campaign_host_ns,
            endpoint.population_elapsed_host_ns,
            endpoint.outside_phase_host_ns,
        )
        for endpoint in endpoints
    )  # type: ignore[return-value]


def _synthetic_reader_document(
    endpoints: tuple[reader.Endpoint, reader.Endpoint],
    config: dict[str, object],
) -> dict[str, object]:
    projection = reader._expected_projection(endpoints, config)
    passed = bool(projection["passed"])
    return {
        "schema_version": (
            "legal-river-quotient-shared-direct-artifact-capacity-result-v1"
        ),
        "config_sha256": source.CONFIG_SHA256,
        "source_git_commit": "a" * 40,
        "dependency_hashes": {
            relative: "b" * 64 for relative in reader.DEPENDENCY_RELATIVE_PATHS
        },
        "input": {
            "relative_path": source.INPUT_RELATIVE_PATH,
            "raw_sha256": source.INPUT_SHA256,
            "bytes": source.INPUT_BYTES,
            "source_commit": source.INPUT_SOURCE_COMMIT,
            "terminal": "completed_validation_pass",
            "populations": [10, 22],
            "phase_rows": source.INPUT_PHASE_ROWS,
        },
        "projection": projection,
        "terminal": (
            "completed_capacity_pass" if passed else "completed_capacity_rejection"
        ),
        "claims": reader._expected_claims(projection),
    }


class SharedDirectArtifactCapacityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.config = source.load_preregistered_config()

    def test_preregistered_config_and_lifecycle_are_exact(self) -> None:
        self.assertEqual(
            sha256(CONFIG.read_bytes().replace(b"\r\n", b"\n")).hexdigest(),
            source.CONFIG_SHA256,
        )
        source.verify_preregistered_contract(self.config)
        if RESULT.exists():
            self.assertEqual(sha256(RESULT.read_bytes()).hexdigest(), RETAINED_RESULT_SHA256)
        self.assertFalse((ROOT / source.RESERVED_ACTUAL_RESULT_RELATIVE_PATH).exists())
        self.assertEqual(source.COMPONENT_ORDER, reader.COMPONENT_ORDER)
        self.assertEqual(runner.DEPENDENCY_RELATIVE_PATHS, reader.DEPENDENCY_RELATIVE_PATHS)

    def test_import_boundary_is_device_result_and_process_free(self) -> None:
        source_tree = ast.parse(SOURCE.read_text(encoding="utf-8"))
        imports = {
            alias.name.split(".")[0]
            for node in ast.walk(source_tree)
            if isinstance(node, ast.Import)
            for alias in node.names
        }
        imports.update(
            (node.module or "").split(".")[0]
            for node in ast.walk(source_tree)
            if isinstance(node, ast.ImportFrom)
        )
        self.assertTrue({"cupy", "numpy", "subprocess"}.isdisjoint(imports))
        with tempfile.TemporaryDirectory() as directory:
            retained = RESULT.read_bytes() if RESULT.exists() else None
            script = (
                "import pathlib,sys; "
                "import pontius.legal_river_quotient_shared_direct_artifact_capacity as m; "
                "print(int('cupy' in sys.modules))"
            )
            environment = dict(os.environ)
            environment["PYTHONPATH"] = str(ROOT / "src")
            completed = subprocess.run(
                [sys.executable, "-B", "-c", script],
                cwd=directory,
                env=environment,
                check=True,
                capture_output=True,
                text=True,
            )
        self.assertEqual(completed.stdout.strip(), "0")
        self.assertEqual(RESULT.read_bytes() if RESULT.exists() else None, retained)

    def test_repository_root_public_owner_module_resolves_without_package_environment(self) -> None:
        environment = dict(os.environ)
        environment.pop("PYTHONPATH", None)
        environment.pop("PYTHONHOME", None)
        retained = RESULT.read_bytes() if RESULT.exists() else None
        script = (
            "import importlib, pathlib, sys; "
            "m=importlib.import_module('src.pontius.legal_river_quotient_shared_direct_artifact_capacity_runner'); "
            "print(int('cupy' in sys.modules))"
        )
        completed = subprocess.run(
            [sys.executable, "-B", "-c", script],
            cwd=ROOT,
            env=environment,
            check=True,
            capture_output=True,
            text=True,
        )
        self.assertEqual(completed.stdout.strip(), "0")
        self.assertEqual(RESULT.read_bytes() if RESULT.exists() else None, retained)

    def test_all_ratios_rederive_and_unchanged_phases_match_parent(self) -> None:
        import pontius.legal_river_quotient_cuda_compensated_work_preflight as parent

        for component in source.COMPONENT_ORDER:
            stored = self.config["component_projection_ratios"][component]
            for population in source.CALIBRATION_POPULATIONS:
                derived = source.component_projection_ratio(component, population)
                self.assertEqual(stored[f"25_over_{population}"], list(derived))
                self.assertEqual(derived, reader._ratio(component, population))
                if component not in {
                    "shared_direct_fold_and_query",
                    source.OUTSIDE_COMPONENT,
                }:
                    self.assertEqual(
                        derived,
                        parent.phase_projection_ratio(component, population),
                    )

    def test_shared_ratio_is_exact_constituent_maximum(self) -> None:
        for population, expected in ((10, (54_264, 1)), (22, (54_264, 18_564))):
            rows = source.shared_component_constituents(population)
            self.assertEqual(
                {name for name, _, _ in rows},
                {
                    "compatible_sources_per_query_occupancy",
                    "shared_direct_source_unranks",
                    "shared_direct_compatible_coefficient_pair_adds",
                    "shared_direct_final_feature_pair_products",
                    "shared_direct_boundary_pair_copies",
                },
            )
            copies = next(row for row in rows if row[0].endswith("boundary_pair_copies"))
            self.assertEqual(copies[1:], (512, 512))
            self.assertEqual(source.component_projection_ratio("shared_direct_fold_and_query", population), expected)
            for _, numerator, denominator in rows:
                self.assertGreaterEqual(
                    expected[0] * denominator,
                    numerator * expected[1],
                )

    def test_ratio_below_constituent_mutation_rejects(self) -> None:
        mutated = deepcopy(self.config)
        mutated["component_projection_ratios"]["shared_direct_fold_and_query"][
            "25_over_10"
        ] = [54_263, 1]
        with self.assertRaisesRegex(ValueError, "projection ratio differs"):
            source.verify_preregistered_contract(mutated, verify_parent_files=False)
        endpoints = _reader_endpoints(_source_endpoints())
        with self.assertRaisesRegex(ValueError, "config ratio differs"):
            reader._expected_projection(endpoints, mutated)

    def test_integer_ceiling_and_inclusive_wall_boundaries(self) -> None:
        self.assertEqual(source.ceil_ratio(0, 54_264, 18_564), 0)
        self.assertEqual(source.ceil_ratio(1, 1, 2), 1)
        self.assertEqual(source.ceil_ratio(2, 1, 2), 1)
        self.assertTrue(source.capacity_passes(179_999_999_999))
        self.assertTrue(source.capacity_passes(180_000_000_000))
        self.assertFalse(source.capacity_passes(180_000_000_001))
        with self.assertRaises(ValueError):
            source.capacity_passes(-1)
        for path in (SOURCE, READER):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            self.assertFalse(
                any(
                    isinstance(node, ast.Constant) and isinstance(node.value, float)
                    for node in ast.walk(tree)
                )
            )

    def test_synthetic_projection_passes_and_reader_matches(self) -> None:
        endpoints = _source_endpoints(phase_ns=1)
        projection = source.project_capacity(endpoints, self.config)
        independent = reader._expected_projection(
            _reader_endpoints(endpoints), self.config
        )
        self.assertEqual(projection, independent)
        self.assertTrue(projection["passed"])
        self.assertEqual(len(projection["component_rows"]), 16)
        self.assertEqual(
            projection["projected_host_ns"],
            sum(row["upper_ns"] for row in projection["component_rows"]),
        )
        self.assertFalse(
            projection["endpoint_22_only_counterfactual"]["authoritative"]
        )

    def test_outside_envelope_alone_can_kill(self) -> None:
        endpoints = _source_endpoints(phase_ns=0, gap_10=144_000_000_000, gap_22=0)
        projection = source.project_capacity(endpoints, self.config)
        rows = {row["component"]: row for row in projection["component_rows"]}
        for phase in source.PHASE_ORDER:
            self.assertEqual(rows[phase]["upper_ns"], 1_000_000)
        outside = rows[source.OUTSIDE_COMPONENT]
        self.assertGreater(outside["upper_ns"], source.WALL_LIMIT_NS)
        self.assertEqual(outside["deciding_endpoint"], "10")
        self.assertFalse(projection["passed"])

    def test_endpoint_swap_drop_duplicate_and_negative_gap_reject(self) -> None:
        endpoints = _source_endpoints()
        for malformed in (
            endpoints[::-1],
            endpoints[:1],
            (endpoints[0], endpoints[0]),
        ):
            with self.assertRaisesRegex(ValueError, "ordered 10 and 22"):
                source.project_capacity(malformed, self.config)
        with self.assertRaisesRegex(ValueError, "phase envelope"):
            source.endpoint_observation(
                10,
                {phase: 1 for phase in source.PHASE_ORDER},
                population_elapsed_host_ns=14,
            )

    def test_synthetic_result_document_and_claim_mutations(self) -> None:
        endpoints = _reader_endpoints(_source_endpoints())
        document = _synthetic_reader_document(endpoints, self.config)
        rebound = reader.validate_capacity_result_document(
            document, endpoints=endpoints, config=self.config
        )
        self.assertTrue(rebound.passed)
        mutations = []
        changed_claim = deepcopy(document)
        changed_claim["claims"]["action_result"] = True
        mutations.append(changed_claim)
        changed_pass = deepcopy(document)
        changed_pass["projection"]["passed"] = False
        mutations.append(changed_pass)
        dropped = deepcopy(document)
        dropped["projection"]["component_rows"].pop()
        mutations.append(dropped)
        duplicated = deepcopy(document)
        duplicated["projection"]["component_rows"].append(
            deepcopy(duplicated["projection"]["component_rows"][0])
        )
        mutations.append(duplicated)
        changed_terminal = deepcopy(document)
        changed_terminal["terminal"] = "completed_capacity_rejection"
        mutations.append(changed_terminal)
        for mutation in mutations:
            with self.assertRaises(ValueError):
                reader.validate_capacity_result_document(
                    mutation, endpoints=endpoints, config=self.config
                )
        with self.assertRaisesRegex(ValueError, "projection endpoints differ"):
            reader.validate_capacity_result_document(
                document, endpoints=endpoints[:1], config=self.config
            )

    def test_reader_is_independent_of_assessor_and_runner(self) -> None:
        tree = ast.parse(READER.read_text(encoding="utf-8"))
        imported = {
            node.module or ""
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom)
        }
        self.assertFalse(
            any(
                name.endswith("legal_river_quotient_shared_direct_artifact_capacity")
                or name.endswith("legal_river_quotient_shared_direct_artifact_capacity_runner")
                for name in imported
            )
        )
        self.assertNotIn("cupy", READER.read_text(encoding="utf-8").lower())

    def test_exclusive_writer_never_replaces(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "result.json"
            runner.write_exclusive(path, b"{}\n")
            self.assertEqual(path.read_bytes(), b"{}\n")
            with self.assertRaises(FileExistsError):
                runner.write_exclusive(path, b"changed\n")
            self.assertEqual(path.read_bytes(), b"{}\n")

    def test_real_v3_control_rebinds_without_projecting(self) -> None:
        raw = INPUT.read_bytes()
        self.assertEqual(len(raw), source.INPUT_BYTES)
        self.assertEqual(sha256(raw).hexdigest(), source.INPUT_SHA256)
        endpoints = source.extract_bound_endpoints(raw, rebind_current_sources=True)
        self.assertEqual(tuple(endpoint.population for endpoint in endpoints), (10, 22))
        self.assertEqual(tuple(len(endpoint.phase_host_ns) for endpoint in endpoints), (15, 15))
        self.assertEqual(
            tuple(endpoint.outside_phase_host_ns for endpoint in endpoints),
            (2_786_065_800, 1_190_895_700),
        )
        with self.assertRaisesRegex(ValueError, "artifact identity differs"):
            source.extract_bound_endpoints(raw[:-1], rebind_current_sources=False)

    def test_retained_result_rebinds_after_the_one_shot_boundary(self) -> None:
        if not RESULT.exists():
            self.skipTest("authoritative artifact-only result remains unopened")
        raw = RESULT.read_bytes()
        self.assertEqual(len(raw), 9_182)
        self.assertEqual(sha256(raw).hexdigest(), RETAINED_RESULT_SHA256)
        rebound = reader.rebind_capacity_result_bytes(
            raw, rebind_current_sources=False
        )
        self.assertEqual(rebound.terminal, "completed_capacity_rejection")
        self.assertFalse(rebound.passed)
        self.assertEqual(rebound.projected_host_ns, 4_999_486_743_986)
        self.assertEqual(rebound.deciding_endpoints, ("10",) * 16)


if __name__ == "__main__":
    unittest.main()
