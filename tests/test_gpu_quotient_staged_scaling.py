from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest

import numpy as np

from pontius import gpu_occupied_card_quotient as bounded
from pontius.durable_evidence_journal import (
    DurableEvidenceJournalWriter,
    JournalRecordKind,
)
from pontius.gpu_quotient_staged_scaling import (
    FEATURE_WIDTH,
    GPU_QUOTIENT_STAGED_SCALING_PROTOCOL_SHA256,
    QUERY_SAMPLE_FEATURES,
    SOURCE_RANK,
    STAGE_CARDS,
    build_allocation_rejection_stage_payload,
    build_synthetic_stage_payload,
    compile_stage_fixture,
    query_only_fixture,
    query_sample_ranks,
    source_refresh_fixture,
    source_sample_ranks,
    stage_allocation,
    stage_geometry,
    stage_semantic_identity,
    stage_work,
    validate_runtime_identity,
    validate_stage_payload,
)
from pontius import gpu_quotient_staged_scaling_runner as runner
from pontius.gpu_quotient_staged_scaling_result import (
    rebind_staged_scaling_journal,
)


_ROOT = Path(__file__).parents[1]
_CONFIG = _ROOT / "experiments/configs/gpu-quotient-staged-scaling-v1.json"
_RESULT = _ROOT / "artifacts/gpu_occupied_card_quotient_staged_scaling_v1.jsonl"
_PARTIAL = Path(f"{_RESULT}.partial")


class GpuQuotientStagedScalingTests(unittest.TestCase):
    def test_source_seal_config_rebinds_and_contains_no_target_outcome(self) -> None:
        payload = json.loads(_CONFIG.read_text(encoding="utf-8"))
        self.assertEqual(runner.parse_config(payload), payload)
        self.assertNotIn(45, payload["stage_cards"])
        self.assertNotIn("target_result", payload)
        mutation = deepcopy(payload)
        mutation["stage_cards"][-1] = 45
        with self.assertRaisesRegex(ValueError, "stage_cards"):
            runner.parse_config(mutation)

    def test_stage_geometry_and_work_are_the_frozen_complete_axes(self) -> None:
        expected = {
            10: (210, 18_900, 1_260, 488_960, 2_158_592),
            16: (8_008, 720_720, 10_920, 10_125_312, 26_432_512),
            22: (74_613, 6_715_170, 43_890, 78_555_136, 157_640_704),
            28: (376_740, 33_906_600, 122_850, 364_077_056, 636_956_672),
            34: (1_344_904, 121_041_360, 278_256, 1_237_160_448, 2_001_276_928),
            40: (3_838_380, 345_454_200, 548_340, 3_419_791_360, 5_270_342_656),
        }
        self.assertEqual(STAGE_CARDS, tuple(expected))
        for cards, row in expected.items():
            geometry = stage_geometry(cards)
            self.assertEqual(
                (
                    geometry.source_occupancies,
                    geometry.labeled_source_visits,
                    geometry.labeled_query_records,
                    geometry.recurrence_scalar_additions,
                    geometry.table_plus_query_bytes,
                ),
                row,
            )
            work = stage_work(cards)
            self.assertEqual(work["cold_source_pairing_visits"], row[1])
            self.assertEqual(work["source_refresh_pairing_visits"], row[1])
            self.assertEqual(work["query_only_source_pairing_visits"], 0)
            self.assertEqual(work["adjoint_allocated_label_writes"], 0)
            self.assertGreater(work["adjoint_modeled_label_writes"], 0)

    def test_literal_target_rejects_before_cupy_import(self) -> None:
        before = bounded.cupy_import_call_count()
        with self.assertRaisesRegex(ValueError, "literal 45-card target"):
            stage_geometry(45)
        with self.assertRaisesRegex(ValueError, "literal 45-card target"):
            compile_stage_fixture(45)
        self.assertEqual(bounded.cupy_import_call_count(), before)

    def test_all_host_fixtures_are_complete_rank_127_and_readonly(self) -> None:
        for cards in STAGE_CARDS:
            fixture = compile_stage_fixture(cards)
            geometry = stage_geometry(cards)
            self.assertEqual(fixture.source_rank, SOURCE_RANK)
            self.assertEqual(fixture.feature_width, FEATURE_WIDTH)
            self.assertEqual(len(fixture.hands), geometry.hand_width)
            self.assertEqual(len(fixture.query_masks), geometry.labeled_query_records)
            self.assertEqual(fixture.source_pair_positions.shape, (90, 6))
            self.assertEqual(
                len(set(int(mask) for mask in fixture.query_masks)),
                geometry.query_occupancies,
            )
            for values in (
                fixture.unary_weights,
                fixture.mode_factors,
                fixture.mixture_weights,
                fixture.pair_to_hand,
                fixture.source_pair_positions,
                fixture.query_masks,
                fixture.query_hand_indices,
                fixture.unary_offsets,
            ):
                self.assertFalse(values.flags.writeable)

    def test_refreshes_change_only_the_frozen_unary_side(self) -> None:
        fixture = compile_stage_fixture(16)
        source = source_refresh_fixture(fixture)
        query = query_only_fixture(source)
        self.assertIs(source.automaton, fixture.automaton)
        self.assertIs(query.automaton, fixture.automaton)
        self.assertTrue(np.array_equal(source.query_masks, fixture.query_masks))
        self.assertTrue(np.array_equal(query.query_masks, fixture.query_masks))
        self.assertFalse(np.array_equal(source.unary_weights, fixture.unary_weights))
        self.assertFalse(np.array_equal(query.unary_weights, source.unary_weights))
        source_start = int(fixture.unary_offsets[1])
        query_start = int(fixture.unary_offsets[4])
        hand_width = len(fixture.hands)
        changed_source = np.flatnonzero(
            source.unary_weights[0] != fixture.unary_weights[0]
        )
        changed_query = np.flatnonzero(query.unary_weights[0] != source.unary_weights[0])
        self.assertTrue(
            all(source_start <= index < source_start + hand_width for index in changed_source)
        )
        self.assertTrue(
            all(query_start <= index < query_start + hand_width for index in changed_query)
        )

    def test_preallocation_prices_every_phase_and_passes_without_live_authority(self) -> None:
        expected_peaks = {
            10: 71_499_680,
            16: 117_915_320,
            22: 364_705_168,
            28: 1_265_911_592,
            34: 3_842_056_832,
            40: 10_046_423_704,
        }
        for cards, expected in expected_peaks.items():
            allocation = stage_allocation(compile_stage_fixture(cards))
            self.assertEqual(allocation.requested_device_peak_bytes, expected)
            self.assertTrue(allocation.fixed_cap_pass)
            self.assertTrue(allocation.physical_reserve_pass)
            self.assertIsNone(allocation.live_reserve_pass)
            self.assertEqual(
                allocation.requested_device_peak_bytes,
                max(
                    allocation.warm_forward_peak_bytes,
                    allocation.query_only_peak_bytes,
                    allocation.adjoint_peak_bytes,
                    allocation.dot_product_peak_bytes,
                ),
            )
            self.assertIn("adjoint_current_and_reference", allocation.arrays)
            self.assertIn("cuda_library_scratch_allowance", allocation.arrays)

    def test_samples_and_semantic_identities_are_prospectively_stable(self) -> None:
        self.assertEqual(
            GPU_QUOTIENT_STAGED_SCALING_PROTOCOL_SHA256,
            "3f7e3e8ffcfa62a2c5d165c11438606e4fe4916c8fbdc4a318ddabea4138452e",
        )
        expected = {
            10: (
                (
                    0, 209, 3, 97, 113, 91, 25, 136,
                    191, 30, 103, 179, 73, 107, 123, 92,
                ),
                (0, 209, 191, 94, 185, 122, 135, 26),
                "c422879503654e9cc41eda5b0850efd55e19ad2f8bc3e2a2395493f804fdb469",
            ),
            16: (
                (
                    0, 8007, 4313, 3999, 7392, 1400, 4792, 4746,
                    5629, 6748, 3171, 2537, 3357, 5909, 1230, 139,
                ),
                (0, 1819, 1416, 419, 821, 1201, 726, 950),
                "18fe28efba9619fea67ad85472363167d6fc483a6d5f62b77670cf16fd907523",
            ),
            22: (
                (
                    0, 74612, 50819, 18248, 68662, 53618, 45114, 15601,
                    40494, 1959, 45313, 25795, 3485, 35116, 9544, 1157,
                ),
                (0, 7314, 4394, 906, 6621, 3115, 2237, 6093),
                "fdc7ccf584d4537ca037dedfbdaf1562e555cd74ba2fe11983a623779856f045",
            ),
            28: (
                (
                    0, 376739, 359357, 337323, 1593, 207121, 296578, 26531,
                    29105, 80048, 322976, 266620, 329320, 29366, 283501, 174848,
                ),
                (0, 20474, 17253, 7889, 17784, 5074, 15140, 17481),
                "5f7e769d27b4db8a5b0ee3ab0078d97b2dbf242a169f574a00df03f03eca150c",
            ),
            34: (
                (
                    0, 1344903, 126750, 262766, 1123131, 679254, 414096,
                    201432, 167039, 297900, 678799, 1303548, 153406, 558244,
                    939000, 1322495,
                ),
                (0, 46375, 29508, 36225, 9724, 4507, 37264, 6897),
                "28dd05e26e722895411911b16a2815344312695cd56b31a89574436ea991580b",
            ),
            40: (
                (
                    0, 3838379, 362822, 981696, 26932, 545394, 1163876,
                    3470630, 315222, 508423, 2276267, 2755068, 2653194,
                    1829155, 3191596, 3660495,
                ),
                (0, 91389, 85174, 27270, 89881, 39714, 58351, 6692),
                "338f8fd031e2a616b42cd9eb15d2381bc6529947237d2730b5d4ec67787d27a8",
            ),
        }
        self.assertEqual(QUERY_SAMPLE_FEATURES, (0, 1, 2, 31, 63, 95, 126, 127))
        for cards, (source, query, identity) in expected.items():
            self.assertEqual(source_sample_ranks(cards), source)
            self.assertEqual(query_sample_ranks(cards), query)
            self.assertEqual(stage_semantic_identity(cards), identity)

    def test_runtime_identity_is_exact_except_for_driver_floor(self) -> None:
        runtime = {
            "device_name": "NVIDIA GeForce RTX 5080",
            "compute_capability": "120",
            "cupy_version": "14.2.0",
            "cuda_runtime_version": 13_020,
            "cuda_driver_version": 13_030,
            "device_total_bytes": 17_094_475_776,
        }
        validate_runtime_identity(runtime)
        for field in (
            "device_name",
            "compute_capability",
            "cupy_version",
            "cuda_runtime_version",
        ):
            changed = dict(runtime)
            changed[field] = "wrong" if isinstance(changed[field], str) else 1
            with self.assertRaisesRegex(RuntimeError, field):
                validate_runtime_identity(changed)
        changed = dict(runtime)
        changed["cuda_driver_version"] = 13_029
        with self.assertRaisesRegex(RuntimeError, "driver"):
            validate_runtime_identity(changed)

    def test_synthetic_stage_payload_rebinds_and_mutations_fail(self) -> None:
        payload = build_synthetic_stage_payload(22)
        self.assertTrue(validate_stage_payload(payload, expected_cards=22)["passed"])
        mutation = dict(payload)
        mutation["work"] = {**payload["work"], "cold_source_pairing_visits": 1}
        with self.assertRaisesRegex(ValueError, "work ledger"):
            validate_stage_payload(mutation, expected_cards=22)
        mutation = dict(payload)
        mutation["semantic_identity_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "semantic identity"):
            validate_stage_payload(mutation, expected_cards=22)
        mutation = dict(payload)
        timings = {**payload["timings"]}
        warm = {**timings["warm"]}
        phases = {**warm["phases"]}
        device = {**phases["device_sum"]}
        device["median_hex"] = float(999.0).hex()
        phases["device_sum"] = device
        warm["phases"] = phases
        timings["warm"] = warm
        mutation["timings"] = timings
        with self.assertRaisesRegex(ValueError, "median"):
            validate_stage_payload(mutation, expected_cards=22)

        mutation = deepcopy(payload)
        mutation["allocation"]["requested_device_peak_bytes"] += 8
        with self.assertRaisesRegex(ValueError, "allocation model"):
            validate_stage_payload(mutation, expected_cards=22)

        mutation = deepcopy(payload)
        mutation["samples"]["identity_observations"]["warm"][2] = False
        with self.assertRaisesRegex(ValueError, "gates were not"):
            validate_stage_payload(mutation, expected_cards=22)

        mutation = deepcopy(payload)
        mutation["gates"]["direct_queries"] = False
        mutation["passed"] = False
        mutation["rejection_reason"] = "forged gate"
        with self.assertRaisesRegex(ValueError, "gates were not"):
            validate_stage_payload(mutation, expected_cards=22)

    def test_live_allocation_rejection_is_reconstructed_and_stops(self) -> None:
        runtime = {
            "device_name": "NVIDIA GeForce RTX 5080",
            "compute_capability": "120",
            "cupy_version": "14.2.0",
            "cuda_runtime_version": 13_020,
            "cuda_driver_version": 13_030,
            "device_total_bytes": 17_094_475_776,
        }

        def synthetic(cards: int):
            if cards != 22:
                return build_synthetic_stage_payload(cards)
            fixture = compile_stage_fixture(cards)
            allocation = stage_allocation(fixture, live_free_bytes=0)
            return build_allocation_rejection_stage_payload(
                cards,
                allocation=allocation,
                topology_ms=1.0,
                stage_total_ms=2.0,
                reason="live_preallocation_rejected",
                runtime=runtime,
            )

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "allocation-rejected.jsonl"
            terminal = runner.execute_campaign_to_path(
                output_path=path,
                config_sha256="7" * 64,
                source_commit="8" * 40,
                stage_executor=synthetic,
            )
            self.assertEqual(terminal["terminal"], "completed_stage_rejection")
            result = rebind_staged_scaling_journal(path.read_bytes())
            self.assertEqual(result.completed_stage_cards, (10, 16, 22))
            self.assertEqual(result.failed_stage_cards, 22)

    def test_stage_and_campaign_wall_rejections_stop_without_replay(self) -> None:
        calls = []

        def stage_wall(cards: int):
            calls.append(cards)
            payload = build_synthetic_stage_payload(cards)
            if cards == 16:
                payload["timings"]["host_hex"]["stage_total"] = float(
                    120_001.0
                ).hex()
                payload["gates"]["stage_wall"] = False
                payload["passed"] = False
                payload["rejection_reason"] = "synthetic_stage_wall_rejection"
            return payload

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "stage-wall.jsonl"
            terminal = runner.execute_campaign_to_path(
                output_path=path,
                config_sha256="9" * 64,
                source_commit="a" * 40,
                stage_executor=stage_wall,
            )
            self.assertEqual(terminal["terminal"], "completed_stage_rejection")
            self.assertEqual(calls, [10, 16])
            result = rebind_staged_scaling_journal(path.read_bytes())
            self.assertEqual(result.failed_stage_cards, 16)

            campaign_path = Path(directory) / "campaign-wall.jsonl"
            clock = iter((0.0, 601.0))
            terminal = runner.execute_campaign_to_path(
                output_path=campaign_path,
                config_sha256="b" * 64,
                source_commit="c" * 40,
                stage_executor=lambda cards: self.fail("stage must not run"),
                monotonic=lambda: next(clock),
            )
            self.assertEqual(terminal["terminal"], "completed_stage_rejection")
            result = rebind_staged_scaling_journal(campaign_path.read_bytes())
            self.assertEqual(result.completed_stage_cards, ())
            self.assertEqual(result.failed_stage_cards, 10)

    def test_synthetic_complete_journal_rebinds_without_device(self) -> None:
        calls = []

        def synthetic(cards: int):
            calls.append(cards)
            return build_synthetic_stage_payload(cards)

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "complete.jsonl"
            terminal = runner.execute_campaign_to_path(
                output_path=path,
                config_sha256="a" * 64,
                source_commit="b" * 40,
                stage_executor=synthetic,
            )
            self.assertEqual(terminal["terminal"], "completed_pass")
            result = rebind_staged_scaling_journal(
                path.read_bytes(),
                expected_config_sha256="a" * 64,
                expected_source_commit="b" * 40,
            )
            self.assertTrue(result.passed)
            self.assertEqual(result.completed_stage_cards, STAGE_CARDS)
            self.assertEqual(len(result.stage_payloads), 6)
            self.assertEqual(calls, list(STAGE_CARDS))
            with self.assertRaises(FileExistsError):
                runner.execute_campaign_to_path(
                    output_path=path,
                    config_sha256="a" * 64,
                    source_commit="b" * 40,
                    stage_executor=synthetic,
                )

    def test_synthetic_rejection_stops_before_later_stages(self) -> None:
        calls = []

        def synthetic(cards: int):
            calls.append(cards)
            return build_synthetic_stage_payload(cards, passed=cards != 28)

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "rejected.jsonl"
            terminal = runner.execute_campaign_to_path(
                output_path=path,
                config_sha256="c" * 64,
                source_commit="d" * 40,
                stage_executor=synthetic,
            )
            self.assertEqual(terminal["terminal"], "completed_stage_rejection")
            result = rebind_staged_scaling_journal(path.read_bytes())
            self.assertFalse(result.passed)
            self.assertEqual(result.failed_stage_cards, 28)
            self.assertEqual(calls, [10, 16, 22, 28])

    def test_synthetic_exception_becomes_one_durable_infrastructure_terminal(self) -> None:
        calls = []

        def synthetic(cards: int):
            calls.append(cards)
            if cards == 22:
                raise RuntimeError("injected stage failure")
            return build_synthetic_stage_payload(cards)

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "failed.jsonl"
            terminal = runner.execute_campaign_to_path(
                output_path=path,
                config_sha256="e" * 64,
                source_commit="f" * 40,
                stage_executor=synthetic,
            )
            self.assertEqual(terminal["terminal"], "infrastructure_failure")
            result = rebind_staged_scaling_journal(path.read_bytes())
            self.assertEqual(result.completed_stage_cards, (10, 16))
            self.assertEqual(result.failed_stage_cards, 22)
            self.assertEqual(calls, [10, 16, 22])

    def test_torn_suffix_and_semantically_rehashed_mutation_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "complete.jsonl"
            runner.execute_campaign_to_path(
                output_path=path,
                config_sha256="1" * 64,
                source_commit="2" * 40,
                stage_executor=build_synthetic_stage_payload,
            )
            raw = path.read_bytes()
            with self.assertRaisesRegex(ValueError, "incomplete"):
                rebind_staged_scaling_journal(raw[:-11])

            mutated_path = Path(directory) / "mutated.jsonl"
            campaign = runner.campaign_identity(
                config_sha256="3" * 64,
                source_commit="4" * 40,
            )
            header = runner._header_payload(
                config_sha256="3" * 64,
                source_commit="4" * 40,
                campaign_sha256=campaign,
            )
            mutated = build_synthetic_stage_payload(10)
            mutated["work"] = {
                **mutated["work"],
                "cold_source_pairing_visits": 7,
            }
            terminal = runner._terminal_payload(
                terminal="infrastructure_failure",
                completed_stage_cards=[10],
                failed_stage_cards=16,
                reason="synthetic mutation",
                campaign_wall_ms=1.0,
            )
            with DurableEvidenceJournalWriter.create(
                path=mutated_path,
                protocol_sha256=GPU_QUOTIENT_STAGED_SCALING_PROTOCOL_SHA256,
                campaign_sha256=campaign,
            ) as writer:
                writer.append(
                    kind=JournalRecordKind.HEADER,
                    semantic_identity_sha256=runner._semantic_digest(header),
                    payload=header,
                )
                writer.append(
                    kind=JournalRecordKind.OBSERVATION,
                    semantic_identity_sha256=stage_semantic_identity(10),
                    payload=mutated,
                )
                writer.append(
                    kind=JournalRecordKind.TERMINAL,
                    semantic_identity_sha256=runner._semantic_digest(terminal),
                    payload=terminal,
                )
            with self.assertRaisesRegex(ValueError, "work ledger"):
                rebind_staged_scaling_journal(mutated_path.read_bytes())

    def test_real_result_and_partial_paths_remain_absent(self) -> None:
        self.assertFalse(_RESULT.exists())
        self.assertFalse(_PARTIAL.exists())


if __name__ == "__main__":
    unittest.main()
