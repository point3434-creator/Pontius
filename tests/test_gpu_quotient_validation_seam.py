from __future__ import annotations

import importlib.util
import inspect
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest

import numpy as np

import pontius.gpu_quotient_validation_seam as subject


_ROOT = Path(__file__).parents[1]
_ISOLATED_PAYLOAD_PREFIX = "PONTIUS_BOUNDED_SEAM_JSON="


def _isolated_device_payload() -> dict[str, object]:
    report = subject.run_bounded_quotient_validation_seam()
    populations = []
    for population in report.populations:
        populations.append(
            {
                "available_cards": population.available_cards,
                "gates": dict(population.gates),
                "complete_ten_card_errors": (
                    None
                    if population.complete_ten_card_errors is None
                    else dict(population.complete_ten_card_errors)
                ),
                "errors": dict(population.errors),
                "chunk_spans": {
                    name: [list(span) for span in spans]
                    for name, spans in population.chunk_spans.items()
                },
                "telemetry": [
                    {
                        "transition": row.transition,
                        "pool_used_bytes": row.pool_used_bytes,
                        "pool_total_bytes": row.pool_total_bytes,
                    }
                    for row in population.telemetry
                ],
                "active_unary_allocations": population.active_unary_allocations,
                "active_unary_overwrites": population.active_unary_overwrites,
                "observed_invocations": dict(population.observed_invocations),
                "work": dict(population.work),
                "digests": dict(population.digests),
                "wall_ms": population.wall_ms,
                "timings_ms": dict(population.timings_ms),
            }
        )
    return {
        "all_gates_pass": report.all_gates_pass,
        "populations": populations,
        "claims": dict(report.claims),
    }


def _run_isolated_device_payload() -> dict[str, object]:
    environment = os.environ.copy()
    environment["PYTHONPATH"] = os.pathsep.join(
        (str(_ROOT / "src"), str(_ROOT))
    )
    command = (
        "import json; "
        "from tests.test_gpu_quotient_validation_seam import "
        "_ISOLATED_PAYLOAD_PREFIX, _isolated_device_payload; "
        "print(_ISOLATED_PAYLOAD_PREFIX + "
        "json.dumps(_isolated_device_payload(), sort_keys=True))"
    )
    completed = subprocess.run(
        (sys.executable, "-B", "-c", command),
        cwd=_ROOT,
        env=environment,
        capture_output=True,
        text=True,
        timeout=130.0,
        check=False,
    )
    if completed.returncode != 0:
        raise AssertionError(
            "isolated bounded seam failed: "
            f"stdout={completed.stdout!r}, stderr={completed.stderr!r}"
        )
    payload_line = next(
        (
            line
            for line in reversed(completed.stdout.splitlines())
            if line.startswith(_ISOLATED_PAYLOAD_PREFIX)
        ),
        None,
    )
    if payload_line is None:
        raise AssertionError(
            f"isolated bounded seam emitted no payload: {completed.stdout!r}"
        )
    payload = json.loads(payload_line.removeprefix(_ISOLATED_PAYLOAD_PREFIX))
    if not isinstance(payload, dict):
        raise AssertionError("isolated bounded seam payload must be an object")
    return payload


class GpuQuotientValidationSeamSourceTests(unittest.TestCase):
    def test_boundary_models_are_exact_and_cross_two_chunks_only_at_22(self) -> None:
        ten = subject.bounded_validation_allocation(10)
        twenty_two = subject.bounded_validation_allocation(22)
        self.assertEqual(ten.source_reference_bytes, 215_040)
        self.assertEqual(ten.source_reference_chunks, 1)
        self.assertEqual(ten.modeled_device_peak_bytes, 70_670_496)
        self.assertEqual(twenty_two.source_reference_bytes, 76_403_712)
        self.assertEqual(twenty_two.source_reference_chunks, 2)
        self.assertEqual(twenty_two.modeled_device_peak_bytes, 271_464_560)
        self.assertTrue(twenty_two.fixed_cap_pass)
        self.assertTrue(twenty_two.physical_reserve_pass)
        self.assertEqual(
            twenty_two.named_bytes["forward_static_and_one_active_unary"],
            1_069_336,
        )
        self.assertEqual(twenty_two.named_bytes["cardinality_offsets"], 56)
        self.assertEqual(
            tuple(twenty_two.phase_numeric_bytes), subject.TELEMETRY_TRANSITIONS
        )

    def test_every_other_width_rejects_before_cupy_import(self) -> None:
        before = subject.cupy_import_call_count()
        for cards in subject.FORBIDDEN_CARDS:
            with self.subTest(cards=cards):
                with self.assertRaisesRegex(ValueError, "complete 10/22"):
                    subject.bounded_validation_allocation(cards)
                with self.assertRaisesRegex(ValueError, "complete 10/22"):
                    subject._fixture(cards)
        self.assertEqual(subject.cupy_import_call_count(), before)

    def test_public_owner_is_no_argument_and_consumed_owners_are_not_called(self) -> None:
        self.assertEqual(
            tuple(inspect.signature(subject.run_bounded_quotient_validation_seam).parameters),
            (),
        )
        source = Path(inspect.getsourcefile(subject) or "").read_text(encoding="utf-8")
        self.assertNotIn("execute_gpu_stage(", source)
        self.assertNotIn("run_staged", source)
        self.assertNotIn("RESULT_RELATIVE_PATH", source)
        self.assertNotIn("artifacts/", source)

    def test_literal_bytes_not_digest_decide_later_chunk_mutation(self) -> None:
        left = np.arange(40, dtype=np.float64)
        right = left.copy()
        self.assertTrue(subject.literal_byte_equal(left, right, chunk_bytes=128))
        right.view(np.uint8)[-1] ^= np.uint8(1)
        self.assertFalse(subject.literal_byte_equal(left, right, chunk_bytes=128))
        self.assertNotEqual(subject.diagnostic_sha256(left), subject.diagnostic_sha256(right))

        original_digest = subject.diagnostic_sha256
        try:
            subject.diagnostic_sha256 = lambda values: "0" * 64
            self.assertEqual(subject.diagnostic_sha256(left), subject.diagnostic_sha256(right))
            self.assertFalse(subject.literal_byte_equal(left, right, chunk_bytes=128))
        finally:
            subject.diagnostic_sha256 = original_digest

    def test_chunk_cover_rejects_missing_overlap_and_gap(self) -> None:
        good = ((0, 16), (16, 29))
        self.assertTrue(subject.validate_chunk_cover(good, 29))
        self.assertFalse(subject.validate_chunk_cover(good[:-1], 29))
        self.assertFalse(subject.validate_chunk_cover(((0, 16), (15, 29)), 29))
        self.assertFalse(subject.validate_chunk_cover(((0, 16), (17, 29)), 29))

    def test_work_ledger_is_independent_and_invocation_shaped(self) -> None:
        work = subject.bounded_validation_work(22)
        self.assertEqual(work["source_pairing_visits_per_build"], 6_715_170)
        self.assertEqual(work["recurrence_scalar_additions_per_build"], 78_555_136)
        self.assertEqual(work["signed_scalar_additions_per_query"], 89_886_720)
        self.assertEqual(work["adjoint_label_additions_per_pass"], 4_681_600)
        self.assertEqual(work["source_build_invocations"], 4)
        self.assertEqual(work["signed_query_invocations"], 6)
        self.assertEqual(work["adjoint_invocations"], 2)
        self.assertEqual(work["active_unary_allocations"], 1)
        self.assertEqual(work["active_unary_overwrites"], 2)

    def test_source_forbids_full_device_references_products_and_three_unaries(self) -> None:
        source = Path(inspect.getsourcefile(subject) or "").read_text(encoding="utf-8")
        self.assertNotIn("cp.copy(", source)
        self.assertNotIn("compatible * query_covectors", source)
        self.assertNotIn("source_reference * unique", source)
        self.assertNotIn("cp.sum(", source)
        self.assertEqual(
            source.count("active_unary=cp.asarray(fixture.unary_weights"), 1
        )
        self.assertEqual(source.count("state.active_unary.set("), 2)
        self.assertIn("np.dot(host_flat[start:stop], values)", source)
        self.assertIn("fsum(partials)", source)

    def test_lifecycle_and_release_controls_fail_closed(self) -> None:
        self.assertTrue(subject.validate_telemetry_transitions(subject.TELEMETRY_TRANSITIONS))
        self.assertFalse(
            subject.validate_telemetry_transitions(subject.TELEMETRY_TRANSITIONS[:-1])
        )
        self.assertTrue(subject.validate_ownership_order(subject.TELEMETRY_TRANSITIONS))
        swapped = list(subject.TELEMETRY_TRANSITIONS)
        first = swapped.index("forward_released")
        second = swapped.index("adjoint_allocated")
        swapped[first], swapped[second] = swapped[second], swapped[first]
        self.assertFalse(subject.validate_ownership_order(swapped))
        self.assertTrue(
            subject.release_gate(
                pool_used_bytes=0,
                pool_total_bytes=0,
                pinned_free_blocks=0,
                device_total_before=17_000,
                device_total_after=17_000,
                device_free_before=10_000,
                device_free_after=9_999,
            )
        )
        self.assertFalse(
            subject.release_gate(
                pool_used_bytes=1,
                pool_total_bytes=0,
                pinned_free_blocks=0,
                device_total_before=17_000,
                device_total_after=17_000,
                device_free_before=10_000,
                device_free_after=10_000,
            )
        )

    def test_dot_roles_and_last_label_mutations_are_detected(self) -> None:
        self.assertTrue(
            subject.validate_dot_operand_roles(
                "host_compatible_reference",
                "device_query_covector",
                "host_source_reference",
                "device_unique_adjoint",
            )
        )
        self.assertFalse(
            subject.validate_dot_operand_roles(
                "host_compatible_reference",
                "device_query_covector",
                "host_compatible_reference",
                "device_unique_adjoint",
            )
        )
        complete = subject.adjoint_label_control(skip_last_label=False)
        omitted = subject.adjoint_label_control(skip_last_label=True)
        self.assertGreater(float(np.max(np.abs(complete - omitted))), 0.0)


@unittest.skipUnless(importlib.util.find_spec("cupy"), "CuPy is unavailable")
class GpuQuotientValidationSeamDeviceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.report = _run_isolated_device_payload()

    def test_every_frozen_gate_passes_in_order(self) -> None:
        self.assertTrue(
            self.report["all_gates_pass"],
            {
                population["available_cards"]: [
                    name for name, value in population["gates"].items() if not value
                ]
                for population in self.report["populations"]
            },
        )
        self.assertEqual(
            tuple(item["available_cards"] for item in self.report["populations"]),
            (10, 22),
        )

    def test_complete_exact_and_sample_errors_are_bounded(self) -> None:
        ten, twenty_two = self.report["populations"]
        self.assertIsNotNone(ten["complete_ten_card_errors"])
        self.assertLessEqual(max(ten["complete_ten_card_errors"].values()), 2e-8)
        self.assertIsNone(twenty_two["complete_ten_card_errors"])
        for population in self.report["populations"]:
            errors = population["errors"]
            self.assertLessEqual(errors["source_sample_absolute"], 2e-12)
            self.assertLessEqual(errors["direct_query_absolute"], 2e-8)
            self.assertLessEqual(errors["direct_query_relative"], 2e-11)
            self.assertLessEqual(errors["affine_sample_absolute"], 2e-10)
            self.assertLessEqual(errors["dot_product_absolute"], 2e-8)
            self.assertLessEqual(errors["dot_product_relative"], 1e-10)

    def test_chunk_and_ownership_evidence_is_complete(self) -> None:
        ten, twenty_two = self.report["populations"]
        self.assertEqual(len(ten["chunk_spans"]["source_reference"]), 1)
        self.assertEqual(len(twenty_two["chunk_spans"]["source_reference"]), 2)
        for population in self.report["populations"]:
            self.assertEqual(
                tuple(row["transition"] for row in population["telemetry"]),
                subject.TELEMETRY_TRANSITIONS,
            )
            before = population["telemetry"][0]
            released = population["telemetry"][-1]
            self.assertEqual(before["pool_used_bytes"], 0)
            self.assertEqual(before["pool_total_bytes"], 0)
            self.assertEqual(released["pool_used_bytes"], 0)
            self.assertEqual(released["pool_total_bytes"], 0)
            self.assertEqual(population["active_unary_allocations"], 1)
            self.assertEqual(population["active_unary_overwrites"], 2)
            self.assertEqual(
                population["observed_invocations"],
                {
                    key: population["work"][key]
                    for key in population["observed_invocations"]
                },
            )
            for digest in population["digests"].values():
                self.assertEqual(len(digest), 64)

    def test_units_and_claims_remain_bounded(self) -> None:
        for population in self.report["populations"]:
            self.assertLessEqual(population["wall_ms"], 60_000.0)
            self.assertGreater(population["timings_ms"]["cold"], 0.0)
            self.assertGreater(population["timings_ms"]["adjoint"], 0.0)
        self.assertEqual(self.report["claims"]["literal_45_card_result"], None)
        self.assertEqual(self.report["claims"]["action_result"], None)
        self.assertFalse(self.report["claims"]["truncation_authorized"])


if __name__ == "__main__":
    unittest.main()
