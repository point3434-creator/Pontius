from __future__ import annotations

import unittest
from fractions import Fraction

from pontius.action_abstraction_confirmation import (
    ADR0293_CONFIRMATION_SEED,
    ADR0293_CONTEXT_COUNT,
    ADR0293_GENERATOR_VERSION,
    ADR0293_PANEL_SHA256,
    ADR0293_POTS,
    ADR0293_STACKS,
    _DigestStream,
    build_adr0293_confirmation_panel,
)


class ActionAbstractionConfirmationPanelTests(unittest.TestCase):
    def test_frozen_generator_is_deterministic_and_structurally_complete(self) -> None:
        first = build_adr0293_confirmation_panel()
        second = build_adr0293_confirmation_panel()
        self.assertEqual(first, second)
        self.assertEqual(first.canonical_bytes, second.canonical_bytes)
        self.assertEqual(first.digest, second.digest)
        self.assertEqual(first.digest, ADR0293_PANEL_SHA256)
        self.assertEqual(first.seed, ADR0293_CONFIRMATION_SEED)
        self.assertEqual(first.generator_version, ADR0293_GENERATOR_VERSION)
        self.assertEqual(len(first.contexts), ADR0293_CONTEXT_COUNT)
        self.assertGreaterEqual(first.candidate_attempts, ADR0293_CONTEXT_COUNT)

        for index, context in enumerate(first.contexts):
            self.assertEqual(context.context_id, f"adr0293-confirmation-{index:02d}")
            self.assertIn(context.pot, ADR0293_POTS)
            self.assertIn(context.stack, ADR0293_STACKS)
            self.assertEqual(context.minimum_bet, 2)
            self.assertEqual(
                sum(
                    (
                        probability.fraction
                        for row in context.joint_probabilities
                        for probability in row
                    ),
                    start=Fraction(0),
                ),
                1,
            )
            signs = context.showdown_signs
            self.assertEqual({value for row in signs for value in row}, {-1, 1})
            self.assertGreaterEqual(len(set(signs)), 2)
            columns = tuple(tuple(row[column] for row in signs) for column in range(3))
            self.assertGreaterEqual(len(set(columns)), 2)

    def test_digest_stream_rejects_invalid_bounds_and_seed(self) -> None:
        with self.assertRaisesRegex(ValueError, "nonempty"):
            _DigestStream("")
        with self.assertRaisesRegex(ValueError, "ASCII"):
            _DigestStream("not-ascii-\N{SNOWMAN}")
        stream = _DigestStream(ADR0293_CONFIRMATION_SEED)
        with self.assertRaisesRegex(TypeError, "integer"):
            stream.randbelow(True)  # type: ignore[arg-type]
        with self.assertRaisesRegex(ValueError, "positive"):
            stream.randbelow(0)
        with self.assertRaisesRegex(ValueError, "exceeds"):
            stream.randbelow((1 << 64) + 1)


if __name__ == "__main__":
    unittest.main()
