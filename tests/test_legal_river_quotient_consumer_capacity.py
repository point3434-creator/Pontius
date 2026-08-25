from __future__ import annotations

import ast
from copy import deepcopy
from dataclasses import replace
from fractions import Fraction
from hashlib import sha256
import inspect
import os
from pathlib import Path
import subprocess
import sys
import unittest

import numpy as np

from pontius.legal_river_quotient_bridge import (
    build_preregistered_legal_river_context,
    compile_legal_river_quotient_bridge,
)
from pontius.legal_river_quotient_consumer_capacity import (
    AdjointOccupancyChunk,
    BoundedConsumerDifferentialReport,
    CLAIMS,
    DEVICE_NUMERIC_CAP_BYTES,
    DEVICE_RESERVE_BYTES,
    EXCLUDED_MEMORY_CLASSES,
    FeatureSlice,
    ForwardRecordChunk,
    HOST_NUMERIC_CAP_BYTES,
    HOST_RESERVE_BYTES,
    MAXIMUM_WORKSPACE_WIDTH,
    MINIMUM_DEVICE_PHYSICAL_BYTES,
    MINIMUM_HOST_PHYSICAL_BYTES,
    PHASES,
    PREREGISTERED_CONFIG_SHA256,
    REACH_GLOBAL_FEATURE,
    SourceOccupancyChunk,
    StreamingContract,
    TOTAL_FEATURE_WIDTH,
    build_legal_river_consumer_capacity_report,
    chunk_spans,
    feature_slices_from_config,
    frozen_feature_slices,
    legal_river_consumer_lifetime_rows,
    load_preregistered_consumer_capacity_config,
    normalize_after_recombination,
    require_fixed_allocation_admission,
    run_bounded_consumer_differential,
    streaming_contract_from_config,
    validate_feature_slices,
    validate_lifetime_proposal,
    validate_lifetime_schedule,
    validate_parent_and_geometry,
    verify_preregistered_dependencies,
)


_ROOT = Path(__file__).parents[1]
_SOURCE = _ROOT / "src/pontius/legal_river_quotient_consumer_capacity.py"


def _canonical_sha256(path: Path) -> str:
    return sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


class LegalRiverQuotientConsumerCapacityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.config = load_preregistered_consumer_capacity_config()
        cls.bridge = compile_legal_river_quotient_bridge(
            build_preregistered_legal_river_context()
        )
        cls.report = build_legal_river_consumer_capacity_report(
            bridge=cls.bridge
        )
        cls.differential: BoundedConsumerDifferentialReport = (
            run_bounded_consumer_differential()
        )

    def test_config_dependencies_parent_and_geometry_are_rebound(self) -> None:
        self.assertEqual(
            _canonical_sha256(
                _ROOT
                / "experiments/configs/legal-river-quotient-consumer-capacity-v1.json"
            ),
            PREREGISTERED_CONFIG_SHA256,
        )
        verify_preregistered_dependencies(self.config)
        validate_parent_and_geometry(
            self.config,
            self.bridge,
            reference_bridge=self.bridge,
        )
        report = self.report
        self.assertEqual(
            report.bridge_sha256,
            "bfe0f1e768bf323fa7d8036ef05176d5e0373f712e4875dcf76eabb96532a702",
        )
        self.assertEqual(
            report.topology_sha256,
            "b499a4e92a739ea2bdf1d64b1653d5c652b707e5b88d8959db7f17f82f8761a9",
        )
        self.assertEqual(
            dict(report.geometry),
            {
                "available_cards": 45,
                "source_cards": 6,
                "query_cards": 4,
                "source_occupancies": 8_145_060,
                "source_recurrence_rows": 9_531_040,
                "source_pairings_per_occupancy": 90,
                "query_occupancies": 148_995,
                "query_pairings_per_occupancy": 6,
                "labeled_query_records": 893_970,
                "adjoint_recurrence_rows": 164_221,
                "source_rank": 175,
                "source_state_feature_count": 175,
                "reach_global_feature_index": 175,
                "total_feature_width": 176,
                "component_count": 1,
            },
        )

    def test_every_bridge_aggregate_expands_to_physical_shape_dtype_rows(self) -> None:
        rows = self.report.rows
        self.assertEqual(len(rows), 58)
        self.assertEqual(len({row.name for row in rows}), len(rows))
        self.assertTrue(
            all(
                row.numeric_bytes
                == int(np.prod(row.shape, dtype=object))
                * np.dtype(row.dtype).itemsize
                for row in rows
            )
        )
        host_consumer = sum(
            row.numeric_bytes
            for row in rows
            if row.placement == "host"
            and row.semantic_category == "bridge_resident"
        )
        host_validation = sum(
            row.numeric_bytes
            for row in rows
            if row.placement == "host"
            and row.semantic_category == "bridge_validation"
        )
        device_mirror = sum(
            row.numeric_bytes
            for row in rows
            if row.name.startswith("device_bridge_")
        )
        self.assertEqual(host_consumer, 15_888_996)
        self.assertEqual(host_validation, 84_972)
        self.assertEqual(device_mirror, 15_888_996)
        self.assertEqual(
            self.report.warm_mutable_numeric_bytes_nonadditive,
            79_216,
        )
        self.assertFalse(any("warm" in row.name for row in rows))
        self.assertEqual(
            sum(
                row.numeric_bytes
                for row in rows
                if row.name.startswith("host_validation_factorized_")
            ),
            79_224,
        )

    def test_phase_peaks_come_only_from_named_row_lifetimes(self) -> None:
        rows = self.report.rows
        independent_host = {
            phase: sum(
                row.numeric_bytes
                for row in rows
                if row.placement == "host" and row.live_at(phase)
            )
            for phase in PHASES
        }
        independent_device = {
            phase: sum(
                row.numeric_bytes
                for row in rows
                if row.placement == "device" and row.live_at(phase)
            )
            for phase in PHASES
        }
        self.assertEqual(dict(self.report.host_phase_bytes), independent_host)
        self.assertEqual(dict(self.report.device_phase_bytes), independent_device)
        self.assertEqual(
            (self.report.host_peak_phase, self.report.host_peak_bytes),
            ("host_bridge", 15_973_968),
        )
        self.assertEqual(
            (self.report.device_peak_phase, self.report.device_peak_bytes),
            ("forward_slice_0_source", 9_910_940_332),
        )
        self.assertEqual(independent_device["forward_release"], 82_997_932)
        self.assertEqual(independent_device["adjoint_slice_0_query"], 318_265_004)
        self.assertEqual(independent_device["adjoint_slice_0_source"], 351_819_436)

    def test_fixed_caps_pass_while_live_admission_and_every_value_claim_stay_absent(self) -> None:
        report = self.report
        self.assertLessEqual(report.host_peak_bytes, HOST_NUMERIC_CAP_BYTES)
        self.assertLessEqual(report.device_peak_bytes, DEVICE_NUMERIC_CAP_BYTES)
        self.assertLessEqual(
            report.host_peak_bytes + HOST_RESERVE_BYTES,
            MINIMUM_HOST_PHYSICAL_BYTES,
        )
        self.assertLessEqual(
            report.device_peak_bytes + DEVICE_RESERVE_BYTES,
            MINIMUM_DEVICE_PHYSICAL_BYTES,
        )
        self.assertTrue(report.host_numeric_cap_pass)
        self.assertTrue(report.device_numeric_cap_pass)
        self.assertTrue(report.host_physical_reserve_pass)
        self.assertTrue(report.device_physical_reserve_pass)
        self.assertTrue(report.all_source_gates_pass)
        self.assertIsNone(report.live_host_free_bytes)
        self.assertIsNone(report.live_device_free_bytes)
        self.assertIsNone(report.live_admission_pass)
        self.assertEqual(report.claims, CLAIMS)
        self.assertTrue(all(value is None or value is False for value in CLAIMS.values()))
        self.assertEqual(report.excluded_memory_classes, EXCLUDED_MEMORY_CLASSES)
        for forbidden in (
            "latency",
            "strength",
            "action",
            "solve",
            "full_width_quotient_value",
        ):
            if forbidden == "full_width_quotient_value":
                self.assertIsNone(report.claims[forbidden])
            else:
                self.assertFalse(hasattr(report, forbidden))

    def test_global_feature_partition_and_streaming_units_are_not_interchangeable(self) -> None:
        slices = self.report.feature_slices
        self.assertEqual(
            tuple((item.start, item.stop, item.width) for item in slices),
            ((0, 128, 128), (128, 176, 48)),
        )
        self.assertEqual(
            tuple(feature for item in slices for feature in item.global_feature_indices),
            tuple(range(TOTAL_FEATURE_WIDTH)),
        )
        self.assertEqual(sum(item.owns_reach_feature for item in slices), 1)
        self.assertTrue(slices[1].owns(REACH_GLOBAL_FEATURE))
        self.assertEqual(self.report.logical_feature_work, 176)
        self.assertEqual(self.report.physical_workspace_width, MAXIMUM_WORKSPACE_WIDTH)
        self.assertFalse(any(48 in row.shape for row in self.report.rows))

        streaming = self.report.streaming
        self.assertIsInstance(streaming.forward, ForwardRecordChunk)
        self.assertIsInstance(streaming.adjoint_query, AdjointOccupancyChunk)
        self.assertIsInstance(streaming.adjoint_source, SourceOccupancyChunk)
        self.assertEqual(streaming.forward.records, 65_536)
        self.assertEqual(streaming.adjoint_query.occupancies, 10_922)
        self.assertEqual(streaming.adjoint_query_records, 65_532)
        self.assertEqual(streaming.adjoint_source.occupancies, 32_768)

    def test_forward_storage_dies_before_adjoint_birth_and_forbidden_arrays_are_absent(self) -> None:
        rows = {row.name: row for row in self.report.rows}
        forward = rows["device_forward_recurrence_workspace"]
        compatible = rows["device_forward_compatible_chunk"]
        adjoint = rows["device_adjoint_recurrence_workspace"]
        unique = rows["device_unique_source_adjoint_chunk"]
        self.assertTrue(forward.live_at("forward_slice_1_fold"))
        self.assertTrue(compatible.live_at("forward_slice_1_fold"))
        self.assertFalse(forward.live_at("forward_release"))
        self.assertFalse(compatible.live_at("adjoint_slice_0_query"))
        self.assertFalse(adjoint.live_at("forward_release"))
        self.assertTrue(adjoint.live_at("adjoint_slice_0_query"))
        self.assertFalse(unique.live_at("adjoint_slice_0_query"))
        self.assertTrue(unique.live_at("adjoint_slice_0_source"))
        names = " ".join(rows)
        for forbidden in (
            "full_compatible",
            "full_query_covector",
            "full_unique_source",
            "record_expanded_source",
            "source_coefficients_allocation",
            "adjoint_aggregates_allocation",
        ):
            self.assertNotIn(forbidden, names)

    def test_complete_ten_card_rank_175_differential_is_exact(self) -> None:
        result = self.differential
        self.assertEqual(
            (
                result.source_occupancies,
                result.query_occupancies,
                result.labeled_query_records,
                result.source_rank,
                result.feature_width,
            ),
            (210, 210, 1_260, 175, 176),
        )
        self.assertEqual(
            result.forward_sha256,
            "57f8a809041af0f02a371e0f19d3910301d7ba6585eeddc34e969da5bef234f2",
        )
        self.assertEqual(
            result.adjoint_sha256,
            "edc515bc581585c0f3a6feb039b0c6796afdfba306b50d3a082de42b06b2b433",
        )
        self.assertEqual(result.monolithic_numerator, Fraction(-128_107_591, 29_400))
        self.assertEqual(result.monolithic_reach, Fraction(277_249, 100))
        self.assertEqual(result.conditional_value, Fraction(-128_107_591, 81_511_206))
        self.assertEqual(result.transpose_dot, result.monolithic_numerator)
        self.assertTrue(result.exact_forward_pass)
        self.assertTrue(result.exact_reverse_slice_order_pass)
        self.assertTrue(result.exact_fold_pass)
        self.assertTrue(result.exact_adjoint_pass)
        self.assertTrue(result.exact_transpose_pass)
        self.assertTrue(result.forward_chunk_partition_pass)
        self.assertTrue(result.adjoint_group_partition_pass)
        self.assertTrue(result.source_chunk_partition_pass)
        self.assertTrue(result.normalize_after_recombination_pass)
        self.assertTrue(result.boundary_detecting_mass_pass)
        self.assertLessEqual(result.maximum_float64_recombination_absolute_error, 2e-11)
        self.assertTrue(result.all_gates_pass)

    def test_monolithic_oracles_are_direct_and_do_not_call_the_quotient_operator(self) -> None:
        import pontius.legal_river_quotient_consumer_capacity as capacity

        for function in (
            capacity._literal_disjoint_forward,
            capacity._literal_disjoint_adjoint,
        ):
            tree = ast.parse(inspect.getsource(function))
            names = {
                node.attr
                for node in ast.walk(tree)
                if isinstance(node, ast.Attribute)
            }
            self.assertFalse(
                names
                & {
                    "apply_exact",
                    "apply_coefficients_exact",
                    "apply_adjoint_exact",
                }
            )

    def test_feature_normalization_and_chunk_adversaries_reject(self) -> None:
        slices = frozen_feature_slices()
        with self.assertRaisesRegex(ValueError, "missing, overlapping, or reordered"):
            validate_feature_slices((slices[1], slices[0]))
        with self.assertRaisesRegex(ValueError, "reach feature"):
            validate_feature_slices(
                (replace(slices[0], owns_reach_feature=True), slices[1])
            )
        with self.assertRaisesRegex(ValueError, "slice-local"):
            FeatureSlice(0, 0, 128, tuple(range(128, 256)), False)
        with self.assertRaisesRegex(ValueError, "per-slice"):
            normalize_after_recombination(
                (Fraction(1),),
                (Fraction(2),),
                consumed_slice_ordinals=(0,),
            )
        with self.assertRaisesRegex(ValueError, "semantic group"):
            chunk_spans(12, 5, group=6)
        with self.assertRaisesRegex(ValueError, "knobs were reused"):
            StreamingContract(
                forward=ForwardRecordChunk(65_532),
                adjoint_query=AdjointOccupancyChunk(10_922),
                adjoint_source=SourceOccupancyChunk(32_768),
                query_labels_per_occupancy=6,
            )

        mutated = deepcopy(self.config)
        mutated["feature_slices"]["ordered_ranges"] = [[0, 127], [128, 176]]
        with self.assertRaisesRegex(ValueError, "missing, overlapping, or reordered"):
            feature_slices_from_config(mutated)
        mutated = deepcopy(self.config)
        mutated["streaming"]["adjoint_query_record_chunk"] += 1
        with self.assertRaisesRegex(ValueError, "occupancy-derived"):
            streaming_contract_from_config(mutated)

    def test_dependency_parent_and_same_shape_payload_adversaries_reject(self) -> None:
        mutated_config = deepcopy(self.config)
        mutated_config["expected_sources"]["occupied_card_quotient"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "occupied_card_quotient"):
            verify_preregistered_dependencies(mutated_config)
        with self.assertRaisesRegex(ValueError, "parent bridge identity"):
            validate_parent_and_geometry(
                self.config,
                replace(self.bridge, bridge_digest="0" * 64),
                reference_bridge=self.bridge,
            )

        terminal = self.bridge.fixture.automaton.terminal_winner_values.copy()
        terminal[0] = np.nextafter(terminal[0], np.inf)
        terminal.flags.writeable = False
        automaton = replace(
            self.bridge.fixture.automaton,
            terminal_winner_values=terminal,
        )
        fixture = replace(self.bridge.fixture, automaton=automaton)
        forged = replace(self.bridge, fixture=fixture)
        with self.assertRaisesRegex(ValueError, "numeric payload"):
            validate_parent_and_geometry(
                self.config,
                forged,
                reference_bridge=self.bridge,
            )

    def test_lifetime_unit_overlap_forbidden_array_and_cap_adversaries_reject(self) -> None:
        rows = self.report.rows
        proposals = self.config["lifetime_model"]["rows"]
        self.assertIsInstance(proposals, list)

        omitted = deepcopy(self.config)
        omitted["lifetime_model"]["rows"].pop()
        with self.assertRaisesRegex(ValueError, "omitted or added"):
            validate_lifetime_proposal(omitted, rows)

        duplicated = deepcopy(self.config)
        duplicated["lifetime_model"]["rows"].append(
            deepcopy(duplicated["lifetime_model"]["rows"][-1])
        )
        with self.assertRaisesRegex(ValueError, "duplicated"):
            validate_lifetime_proposal(duplicated, rows)

        wrong_unit = deepcopy(self.config)
        wrong_unit["lifetime_model"]["rows"][3]["unit"] = "numeric_bytes"
        with self.assertRaisesRegex(ValueError, "device_cardinality_offsets"):
            validate_lifetime_proposal(wrong_unit, rows)

        wrong_lifetime = deepcopy(self.config)
        wrong_lifetime["lifetime_model"]["rows"][6]["last_live"] = (
            "adjoint_slice_0_query"
        )
        with self.assertRaisesRegex(ValueError, "forward_recurrence"):
            validate_lifetime_proposal(wrong_lifetime, rows)

        by_name = {row.name: row for row in rows}
        overlapping = tuple(
            replace(row, last_live="adjoint_slice_0_query")
            if row.name == "device_forward_recurrence_workspace"
            else row
            for row in rows
        )
        with self.assertRaisesRegex(ValueError, "co-resident"):
            validate_lifetime_schedule(overlapping)

        forbidden = (
            *rows,
            replace(
                by_name["device_forward_compatible_chunk"],
                name="device_full_compatible_query_matrix",
            ),
        )
        with self.assertRaisesRegex(ValueError, "forbidden"):
            validate_lifetime_schedule(forbidden)

        oversized = tuple(
            replace(row, shape=(12_000_000, 128))
            if row.name == "device_forward_recurrence_workspace"
            else row
            for row in rows
        )
        with self.assertRaisesRegex(MemoryError, "device numeric cap"):
            require_fixed_allocation_admission(oversized)

    def test_source_is_cupy_free_and_cannot_call_literal_target_or_device_entry(self) -> None:
        source = _SOURCE.read_text(encoding="utf-8")
        tree = ast.parse(source)
        imported_modules = []
        called_names = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported_modules.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imported_modules.append(node.module)
            elif isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    called_names.add(node.func.id)
                elif isinstance(node.func, ast.Attribute):
                    called_names.add(node.func.attr)
        self.assertTrue(all("cupy" not in name.lower() for name in imported_modules))
        self.assertTrue(
            all("literal_45_quotient" not in name for name in imported_modules)
        )
        self.assertFalse(
            called_names
            & {
                "execute_gpu_stage",
                "run_literal_45_quotient_target",
                "import_module",
                "getDeviceCount",
                "memGetInfo",
            }
        )
        self.assertNotIn("device_output", source)

    def test_fresh_process_import_and_capacity_rejection_leave_cupy_and_owner_absent(self) -> None:
        script = """
import sys
from dataclasses import replace
assert 'cupy' not in sys.modules
assert 'pontius.literal_45_quotient_target' not in sys.modules
from pontius.legal_river_quotient_consumer_capacity import (
    build_legal_river_consumer_capacity_report,
    require_fixed_allocation_admission,
)
assert 'cupy' not in sys.modules
assert 'pontius.literal_45_quotient_target' not in sys.modules
report = build_legal_river_consumer_capacity_report()
rows = tuple(
    replace(row, shape=(12_000_000, 128))
    if row.name == 'device_forward_recurrence_workspace'
    else row
    for row in report.rows
)
try:
    require_fixed_allocation_admission(rows)
except MemoryError as error:
    assert 'device numeric cap' in str(error)
else:
    raise AssertionError('oversized schedule passed')
assert 'cupy' not in sys.modules
assert 'pontius.literal_45_quotient_target' not in sys.modules
print(report.device_peak_bytes)
"""
        environment = os.environ.copy()
        environment["PYTHONPATH"] = os.pathsep.join(
            (str(_ROOT / "src"), str(_ROOT))
        )
        completed = subprocess.run(
            [sys.executable, "-B", "-c", script],
            cwd=_ROOT,
            env=environment,
            check=False,
            capture_output=True,
            text=True,
            timeout=60,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(completed.stdout.strip(), "9910940332")


if __name__ == "__main__":
    unittest.main()
