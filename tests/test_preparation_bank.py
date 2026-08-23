from __future__ import annotations

import unittest
from dataclasses import FrozenInstanceError
from hashlib import sha256

from pontius.action_clock import ActionClockLedger
from pontius.preparation_bank import PreparationBank


class _FakeClock:
    def __init__(self) -> None:
        self.nanoseconds = 0

    def __call__(self) -> int:
        return self.nanoseconds

    def advance(self, seconds: float) -> None:
        self.nanoseconds += round(seconds * 1_000_000_000)


def _digest(label: str) -> str:
    return sha256(label.encode("ascii")).hexdigest()


class PreparationBankTests(unittest.TestCase):
    def test_previous_street_credit_matches_once_without_extending_action(self) -> None:
        clock = _FakeClock()
        ledger = ActionClockLedger("preflop", clock_ns=clock)
        bank = PreparationBank(action_clock=ledger)
        artifact = b"future-flop-solve"
        public = _digest("future-public")
        semantic = _digest("belief-action-model")
        source = _digest("solver-source")

        bank.start_preparation(
            target_public_state_sha256=public,
            semantic_context_sha256=semantic,
            source_sha256=source,
        )
        clock.advance(6.0)
        credit = bank.seal_preparation(artifact)
        self.assertEqual(credit.created_street, "preflop")
        self.assertEqual(credit.preparation_compute_seconds, 6.0)

        boundary = ledger.start_transition_boundary()
        ledger.finish_transition_boundary(
            boundary,
            starts_controlled_action=False,
            next_street="flop",
        )
        action = ledger.begin_action(public_state_sha256=public)
        use = bank.claim(
            artifact_bytes=artifact,
            semantic_context_sha256=semantic,
            source_sha256=source,
        )
        self.assertEqual(use.action, action.action)
        attached = ledger.snapshot()
        self.assertEqual(attached.credited_preparation_seconds, 6.0)
        self.assertEqual(attached.remaining_seconds, 15.0)
        self.assertEqual(attached.work_remaining_seconds, 14.0)

        with self.assertRaisesRegex(ValueError, "already used"):
            bank.claim(
                artifact_bytes=artifact,
                semantic_context_sha256=semantic,
                source_sha256=source,
            )
        self.assertEqual(bank.snapshot().failed_claims, 1)

    def test_stale_context_source_and_public_state_do_not_consume_credit(self) -> None:
        clock = _FakeClock()
        ledger = ActionClockLedger("turn", clock_ns=clock)
        bank = PreparationBank(action_clock=ledger)
        artifact = b"turn-branch"
        public = _digest("turn-public")
        semantic = _digest("turn-semantic")
        source = _digest("turn-source")
        bank.start_preparation(
            target_public_state_sha256=public,
            semantic_context_sha256=semantic,
            source_sha256=source,
        )
        clock.advance(2.0)
        bank.seal_preparation(artifact)
        ledger.begin_action(public_state_sha256=_digest("wrong-public"))
        with self.assertRaisesRegex(ValueError, "public state"):
            bank.claim(
                artifact_bytes=artifact,
                semantic_context_sha256=semantic,
                source_sha256=source,
            )
        ledger.finish_action()
        ledger.begin_action(public_state_sha256=public)

        mismatches = (
            (_digest("wrong-semantic"), source, "semantic context"),
            (semantic, _digest("wrong-source"), "source"),
        )
        for current_semantic, current_source, message in mismatches:
            with (
                self.subTest(message=message),
                self.assertRaisesRegex(
                    ValueError,
                    message,
                ),
            ):
                bank.claim(
                    artifact_bytes=artifact,
                    semantic_context_sha256=current_semantic,
                    source_sha256=current_source,
                )
        self.assertEqual(bank.snapshot().failed_claims, 3)
        bank.claim(
            artifact_bytes=artifact,
            semantic_context_sha256=semantic,
            source_sha256=source,
        )

    def test_aborted_duplicate_invalidated_and_absent_work_remain_visible(self) -> None:
        clock = _FakeClock()
        ledger = ActionClockLedger("river", clock_ns=clock)
        bank = PreparationBank(action_clock=ledger)
        public = _digest("river-public")
        semantic = _digest("river-semantic")
        source = _digest("river-source")

        with (
            self.assertRaisesRegex(RuntimeError, "abort"),
            bank.prepare_artifact(
                target_public_state_sha256=public,
                semantic_context_sha256=semantic,
                source_sha256=source,
            ),
        ):
            clock.advance(1.0)
            raise RuntimeError("abort")

        artifact = b"river-artifact"
        for duration in (2.0, 3.0):
            bank.start_preparation(
                target_public_state_sha256=public,
                semantic_context_sha256=semantic,
                source_sha256=source,
            )
            clock.advance(duration)
            if duration == 2.0:
                credit = bank.seal_preparation(artifact)
            else:
                with self.assertRaisesRegex(ValueError, "repeats"):
                    bank.seal_preparation(artifact)
        bank.invalidate(artifact_bytes=artifact)

        ledger.begin_action(public_state_sha256=public)
        with self.assertRaisesRegex(ValueError, "invalidated"):
            bank.claim(
                artifact_bytes=artifact,
                semantic_context_sha256=semantic,
                source_sha256=source,
            )
        with self.assertRaisesRegex(ValueError, "absent"):
            bank.claim(
                artifact_bytes=b"missing",
                semantic_context_sha256=semantic,
                source_sha256=source,
            )

        snapshot = bank.snapshot()
        self.assertEqual(snapshot.total_spent_compute_seconds, 6.0)
        self.assertEqual(snapshot.sealed_compute_seconds, 2.0)
        self.assertEqual(snapshot.invalidated_compute_seconds, 2.0)
        self.assertEqual(snapshot.aborted_compute_seconds, 4.0)
        self.assertEqual(snapshot.aborted_intervals, 2)
        self.assertEqual(snapshot.failed_claims, 2)
        with self.assertRaises(FrozenInstanceError):
            credit.artifact_bytes = b"changed"  # type: ignore[misc]

    def test_preparation_cannot_be_started_or_claimed_in_the_wrong_phase(self) -> None:
        clock = _FakeClock()
        ledger = ActionClockLedger("flop", clock_ns=clock)
        bank = PreparationBank(action_clock=ledger)
        values = {
            "target_public_state_sha256": _digest("public"),
            "semantic_context_sha256": _digest("semantic"),
            "source_sha256": _digest("source"),
        }
        with self.assertRaisesRegex(ValueError, "active controlled action"):
            bank.claim(
                artifact_bytes=b"absent",
                semantic_context_sha256=values["semantic_context_sha256"],
                source_sha256=values["source_sha256"],
            )
        ledger.begin_action(
            public_state_sha256=values["target_public_state_sha256"],
        )
        with self.assertRaisesRegex(RuntimeError, "on-clock"):
            bank.start_preparation(**values)
        with self.assertRaises(TypeError):
            bank.claim(  # type: ignore[arg-type]
                artifact_bytes=bytearray(b"mutable"),
                semantic_context_sha256=values["semantic_context_sha256"],
                source_sha256=values["source_sha256"],
            )


if __name__ == "__main__":
    unittest.main()
