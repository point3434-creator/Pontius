from __future__ import annotations

from hashlib import sha256
from pathlib import Path
import unittest

from pontius import legal_river_quotient_fixed_width_actual45_fit_projection_outcome as outcome
from pontius import legal_river_quotient_fixed_width_actual45_fit_projection_result as reader


class Literal45FitProjectionOutcomeTests(unittest.TestCase):
    def test_retained_artifact_rebinds_to_exact_rejection(self) -> None:
        raw = reader.RESULT_PATH.read_bytes()
        self.assertEqual(len(raw), outcome.RESULT_BYTES)
        self.assertEqual(sha256(raw).hexdigest(), outcome.RESULT_SHA256)
        assessed = outcome.assess_fit_projection_outcome_file()
        self.assertEqual(assessed.source_commit, outcome.SOURCE_COMMIT)
        self.assertEqual(assessed.terminal, outcome.TERMINAL)
        self.assertEqual(assessed.eligible_arms, ())
        self.assertIsNone(assessed.candidate_selected)
        self.assertEqual(
            dict(assessed.runtime_component_projection_ns),
            {
                "positional": 3_186_554_546_230,
                "batched_five_then_four_RRNS": 9_908_352_862_122,
            },
        )

    def test_artifact_mutation_and_path_substitution_reject(self) -> None:
        raw = bytearray(reader.RESULT_PATH.read_bytes())
        raw[-2] ^= 1
        with self.assertRaises(ValueError):
            outcome.assess_fit_projection_outcome_bytes(
                bytes(raw), reader.INPUT_PATH.read_bytes()
            )
        with self.assertRaises(ValueError):
            outcome.assess_fit_projection_outcome_file(
                Path("not-the-result.jsonl"), reader.INPUT_PATH
            )


if __name__ == "__main__":
    unittest.main()
