from __future__ import annotations

import ast
import hashlib
import unittest
from collections import Counter
from pathlib import Path
from unittest.mock import patch

from pontius.fresh_action_width_qualification import (
    ActionWidthQualificationClassification,
)
from pontius.fresh_action_width_qualification_result import (
    ADR0323_QUALIFICATION_ARTIFACT_BYTES,
    ADR0323_QUALIFICATION_ARTIFACT_RELATIVE_PATH,
    ADR0323_QUALIFICATION_ARTIFACT_SHA256,
    ADR0323_QUALIFICATION_PAYLOAD_SHA256,
    ADR0323_QUALIFICATION_RESULT_SHA256,
    ADR0323_QUALIFIED_CONTEXT_SEMANTIC_DIGESTS,
    ADR0323_QUALIFIED_PANEL_SHA256,
    ADR0323_QUALIFIED_POOL_INDICES,
    qualification_result_protocol_sha256,
    verify_adr0323_qualification_result_artifact,
    verify_adr0326_qualification_result_source_and_dependencies,
)
from pontius.fresh_action_width_qualification_result_seal import (
    ADR0326_QUALIFICATION_RESULT_PROTOCOL_SHA256,
    ADR0326_QUALIFICATION_RESULT_SOURCE_MANIFEST,
)
from pontius.fresh_action_width_structures import build_adr0323_development_pool


_ROOT = Path(__file__).parents[1]
_ARTIFACT = _ROOT / ADR0323_QUALIFICATION_ARTIFACT_RELATIVE_PATH
_SOURCE = _ROOT / "src/pontius/fresh_action_width_qualification_result.py"


class FreshActionWidthQualificationResultTests(unittest.TestCase):
    def test_source_closure_and_result_protocol_are_sealed(self) -> None:
        self.assertEqual(
            qualification_result_protocol_sha256(),
            ADR0326_QUALIFICATION_RESULT_PROTOCOL_SHA256,
        )
        self.assertEqual(
            verify_adr0326_qualification_result_source_and_dependencies(),
            ADR0326_QUALIFICATION_RESULT_SOURCE_MANIFEST[
                "fresh_action_width_qualification_result.py"
            ],
        )

    def test_canonical_artifact_and_all_retained_endpoints_rebind_without_solving(
        self,
    ) -> None:
        with (
            patch(
                "pontius.fresh_action_width_qualification."
                "run_adr0323_development_qualification",
                side_effect=AssertionError("the one-shot campaign must not rerun"),
            ),
            patch(
                "scipy.optimize.linprog",
                side_effect=AssertionError("artifact verification must not solve"),
            ),
        ):
            result = verify_adr0323_qualification_result_artifact()

        self.assertEqual(result.qualification_result_sha256, ADR0323_QUALIFICATION_RESULT_SHA256)
        self.assertEqual(result.panel.digest, ADR0323_QUALIFIED_PANEL_SHA256)
        self.assertEqual(result.panel.pool_indices, ADR0323_QUALIFIED_POOL_INDICES)
        self.assertEqual(
            result.panel.context_semantic_digests,
            ADR0323_QUALIFIED_CONTEXT_SEMANTIC_DIGESTS,
        )
        self.assertEqual(len(result.observations), 51)
        self.assertEqual(result.public_highs_ds_invocation_count, 102)
        self.assertGreater(result.observed_elapsed_seconds, 0.0)

    def test_artifact_bytes_are_exact_canonical_single_line_json(self) -> None:
        raw = _ARTIFACT.read_bytes()
        self.assertEqual(len(raw), ADR0323_QUALIFICATION_ARTIFACT_BYTES)
        self.assertEqual(hashlib.sha256(raw).hexdigest(), ADR0323_QUALIFICATION_ARTIFACT_SHA256)
        self.assertEqual(
            hashlib.sha256(raw[:-1]).hexdigest(),
            ADR0323_QUALIFICATION_PAYLOAD_SHA256,
        )
        self.assertTrue(raw.endswith(b"\n"))
        self.assertEqual(raw.count(b"\n"), 1)

    def test_target_stop_and_interval_classes_are_complete(self) -> None:
        result = verify_adr0323_qualification_result_artifact()
        counts = Counter(value.classification for value in result.observations)
        self.assertEqual(
            counts,
            {
                ActionWidthQualificationClassification.QUALIFYING: 16,
                ActionWidthQualificationClassification.NONQUALIFYING: 35,
            },
        )
        self.assertEqual(
            tuple(
                value.context_index
                for value in result.observations
                if value.classification
                is ActionWidthQualificationClassification.QUALIFYING
            ),
            ADR0323_QUALIFIED_POOL_INDICES,
        )
        for value in result.observations:
            self.assertLessEqual(value.full_lower_chips, value.full_upper_chips)
            self.assertLessEqual(value.width_two_lower_chips, value.width_two_upper_chips)
            self.assertLessEqual(value.regret_lower_chips, value.regret_upper_chips)
            self.assertGreaterEqual(value.regret_lower_chips, 0.0)

    def test_panel_diversity_and_threshold_separation_are_rederived(self) -> None:
        result = verify_adr0323_qualification_result_artifact()
        pool = build_adr0323_development_pool()
        qualified = tuple(result.observations[index] for index in result.panel.pool_indices)
        contexts = tuple(pool.contexts[index] for index in result.panel.pool_indices)
        self.assertEqual({context.betting.pot for context in contexts}, {6, 10, 14, 20})
        self.assertEqual({context.betting.stacks[0] for context in contexts}, {8, 10, 12})
        self.assertEqual(len({context.showdown_signs for context in contexts}), 16)
        self.assertGreater(
            min(
                observation.regret_lower_chips / context.payoff_span_chips
                for observation, context in zip(qualified, contexts, strict=True)
            ),
            1e-4,
        )
        nonqualifying = tuple(
            value
            for value in result.observations
            if value.classification
            is ActionWidthQualificationClassification.NONQUALIFYING
        )
        self.assertLess(
            max(
                value.regret_upper_chips
                / pool.contexts[value.context_index].payoff_span_chips
                for value in nonqualifying
            ),
            1e-4,
        )

    def test_result_owner_has_no_campaign_or_action_call(self) -> None:
        tree = ast.parse(_SOURCE.read_text(encoding="utf-8"))
        called_names = {
            node.func.id
            for node in ast.walk(tree)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
        }
        self.assertNotIn("run_adr0323_development_qualification", called_names)
        self.assertNotIn("consume_certified_reduced_sizing_v2", called_names)
        source = _SOURCE.read_text(encoding="utf-8")
        self.assertNotIn("apply_action", source)
        self.assertNotIn("BettingAction", source)


if __name__ == "__main__":
    unittest.main()
