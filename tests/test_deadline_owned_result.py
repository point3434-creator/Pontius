from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pontius.deadline_owned_result as finalizer
from pontius.campaign_deadline import CampaignDeadlineStop, MonotonicCampaignDeadline
from pontius.deadline_owned_result import (
    RESULT_ENVELOPE_SCHEMA,
    finalize_deadline_owned_atomic_result,
    load_deadline_owned_atomic_result,
)


class _FakeClock:
    def __init__(self) -> None:
        self.nanoseconds = 0

    def __call__(self) -> int:
        return self.nanoseconds

    def advance(self, seconds: float) -> None:
        self.nanoseconds += round(seconds * 1_000_000_000)


def _finalize(
    output_path: Path,
    clock: _FakeClock,
    *,
    build: object,
    campaign_seconds: float = 20.0,
    finalization_seconds: float = 5.0,
    seal_seconds: float = 2.0,
) -> object:
    return finalize_deadline_owned_atomic_result(
        deadline=MonotonicCampaignDeadline(campaign_seconds, clock_ns=clock),
        unit_name="finalize/result",
        maximum_finalization_seconds=finalization_seconds,
        maximum_seal_seconds=seal_seconds,
        checkpoint=lambda: None,
        output_path=output_path,
        build_result=build,
    )


class DeadlineOwnedResultTests(unittest.TestCase):
    def test_success_is_an_immutable_helper_envelope_and_verified_seal(self) -> None:
        clock = _FakeClock()
        nested = {"values": [1, 2]}

        def build(_: finalizer.DeadlineOwnedResultAdmission) -> dict[str, object]:
            return {
                "passed": True,
                "nested": nested,
                "deadline_admission": {"forged": True},
            }

        with tempfile.TemporaryDirectory() as directory:
            output_path = Path(directory) / "nested" / "result.json"
            completed = _finalize(output_path, clock, build=build)
            nested["values"].append(3)
            loaded = load_deadline_owned_atomic_result(output_path)
            persisted = json.loads(output_path.read_text(encoding="utf-8"))

        self.assertEqual(persisted["schema"], RESULT_ENVELOPE_SCHEMA)
        self.assertIn("deadline_admission", persisted)
        self.assertEqual(persisted["payload"]["nested"]["values"], [1, 2])
        self.assertEqual(completed.result["nested"]["values"], (1, 2))
        self.assertEqual(loaded.result, completed.result)
        self.assertEqual(
            completed.persisted_sha256,
            hashlib.sha256(
                json.dumps(persisted, indent=2, sort_keys=True).encode("utf-8")
                + b"\n"
            ).hexdigest(),
        )
        with self.assertRaises(TypeError):
            completed.result["passed"] = False  # type: ignore[index]
        with self.assertRaises(TypeError):
            completed.result["nested"]["values"] = ()  # type: ignore[index]
        self.assertFalse(finalizer._lock_path(completed.output_path).exists())

    def test_first_phase_overrun_never_creates_a_consumable_seal(self) -> None:
        clock = _FakeClock()

        def build(_: object) -> dict[str, bool]:
            clock.advance(6.0)
            return {"passed": True}

        with tempfile.TemporaryDirectory() as directory:
            output_path = Path(directory) / "result.json"
            with self.assertRaises(CampaignDeadlineStop) as raised:
                _finalize(
                    output_path,
                    clock,
                    build=build,
                    finalization_seconds=5.0,
                )
            self.assertEqual(raised.exception.reason, "unit_bound_crossed")
            self.assertFalse(finalizer._seal_path(output_path).exists())
            self.assertTrue(finalizer._lock_path(output_path).exists())
            with self.assertRaisesRegex(ValueError, "incomplete"):
                load_deadline_owned_atomic_result(output_path)

    def test_seal_phase_overrun_leaves_seal_plus_lock_untrusted(self) -> None:
        clock = _FakeClock()
        original = finalizer._overwrite_lock

        def slow(path: Path, payload: bytes) -> None:
            original(path, payload)
            clock.advance(3.0)

        with tempfile.TemporaryDirectory() as directory:
            output_path = Path(directory) / "result.json"
            with (
                patch.object(finalizer, "_overwrite_lock", side_effect=slow),
                self.assertRaises(CampaignDeadlineStop) as raised,
            ):
                _finalize(
                    output_path,
                    clock,
                    build=lambda _: {"passed": True},
                    seal_seconds=2.0,
                )
            self.assertEqual(raised.exception.reason, "unit_bound_crossed")
            self.assertTrue(finalizer._seal_path(output_path).exists())
            self.assertTrue(finalizer._lock_path(output_path).exists())
            with self.assertRaisesRegex(ValueError, "incomplete"):
                load_deadline_owned_atomic_result(output_path)

    def test_slow_final_unlock_crosses_campaign_and_is_reinvalidated(self) -> None:
        clock = _FakeClock()
        original_unlink = Path.unlink

        def slow_unlink(path: Path, *args: object, **kwargs: object) -> None:
            original_unlink(path, *args, **kwargs)
            if path.name.endswith(".publishing.lock"):
                clock.advance(21.0)

        with tempfile.TemporaryDirectory() as directory:
            output_path = Path(directory) / "result.json"
            with (
                patch.object(Path, "unlink", new=slow_unlink),
                self.assertRaises(CampaignDeadlineStop) as raised,
            ):
                _finalize(output_path, clock, build=lambda _: {"passed": True})
            self.assertEqual(raised.exception.reason, "deadline_crossed")
            self.assertTrue(finalizer._lock_path(output_path).exists())
            with self.assertRaisesRegex(ValueError, "incomplete"):
                load_deadline_owned_atomic_result(output_path)

    def test_mutation_during_unlock_cannot_return_success(self) -> None:
        clock = _FakeClock()
        original_unlink = Path.unlink
        with tempfile.TemporaryDirectory() as directory:
            output_path = Path(directory) / "result.json"

            def mutate_unlink(path: Path, *args: object, **kwargs: object) -> None:
                original_unlink(path, *args, **kwargs)
                if path == finalizer._lock_path(output_path):
                    output_path.write_bytes(b'{"changed":true}\n')

            with (
                patch.object(Path, "unlink", new=mutate_unlink),
                self.assertRaisesRegex(OSError, "changed during unlock"),
            ):
                _finalize(output_path, clock, build=lambda _: {"passed": True})
            self.assertTrue(finalizer._lock_path(output_path).exists())
            with self.assertRaisesRegex(ValueError, "incomplete"):
                load_deadline_owned_atomic_result(output_path)

    def test_canonical_mutation_after_success_is_detected_by_loader(self) -> None:
        clock = _FakeClock()
        with tempfile.TemporaryDirectory() as directory:
            output_path = Path(directory) / "result.json"
            _finalize(output_path, clock, build=lambda _: {"passed": True})
            output_path.write_bytes(b'{"passed":false}\n')
            with self.assertRaisesRegex(ValueError, "differ from completion seal"):
                load_deadline_owned_atomic_result(output_path)

    def test_rehashed_but_inconsistent_admission_is_rejected(self) -> None:
        clock = _FakeClock()
        with tempfile.TemporaryDirectory() as directory:
            output_path = Path(directory) / "result.json"
            _finalize(output_path, clock, build=lambda _: {"passed": True})
            envelope = json.loads(output_path.read_text(encoding="utf-8"))
            envelope["deadline_admission"][
                "conservative_publication_verification_elapsed_upper_seconds"
            ] += 1.0
            canonical = (
                json.dumps(envelope, indent=2, sort_keys=True).encode("utf-8")
                + b"\n"
            )
            output_path.write_bytes(canonical)
            seal_path = finalizer._seal_path(output_path)
            seal = json.loads(seal_path.read_text(encoding="utf-8"))
            seal["data_bytes"] = len(canonical)
            seal["data_sha256"] = hashlib.sha256(canonical).hexdigest()
            seal_path.write_text(
                json.dumps(seal, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
                newline="",
            )
            with self.assertRaisesRegex(ValueError, "elapsed bound is inconsistent"):
                load_deadline_owned_atomic_result(output_path)

    def test_crash_before_seal_and_prior_paths_are_fail_closed(self) -> None:
        clock = _FakeClock()
        with tempfile.TemporaryDirectory() as directory:
            output_path = Path(directory) / "result.json"
            with (
                patch.object(
                    finalizer,
                    "_overwrite_lock",
                    side_effect=RuntimeError("simulated crash"),
                ),
                self.assertRaisesRegex(RuntimeError, "simulated crash"),
            ):
                _finalize(output_path, clock, build=lambda _: {"passed": True})
            self.assertFalse(finalizer._seal_path(output_path).exists())
            self.assertTrue(finalizer._lock_path(output_path).exists())

        with tempfile.TemporaryDirectory() as directory:
            output_path = Path(directory) / "result.json"
            output_path.write_bytes(b"prior")
            with self.assertRaises(FileExistsError):
                _finalize(output_path, _FakeClock(), build=lambda _: {"passed": True})
            self.assertEqual(output_path.read_bytes(), b"prior")

    def test_builder_and_nonfinite_serialization_fail_without_a_seal(self) -> None:
        failures = (
            lambda _: (_ for _ in ()).throw(RuntimeError("builder failed")),
            lambda _: {"nonfinite": float("nan")},
        )
        for build in failures:
            with self.subTest(build=build), tempfile.TemporaryDirectory() as directory:
                output_path = Path(directory) / "result.json"
                with self.assertRaises((RuntimeError, ValueError)):
                    _finalize(output_path, _FakeClock(), build=build)
                self.assertFalse(finalizer._seal_path(output_path).exists())
                self.assertTrue(finalizer._lock_path(output_path).exists())


if __name__ == "__main__":
    unittest.main()
