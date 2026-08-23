from __future__ import annotations

import ast
import unittest
from pathlib import Path

from pontius.action_abstraction_confirmation import (
    ADR0293_PANEL_SHA256,
    build_adr0293_confirmation_panel,
)
from pontius.sizing_power_diagnostic import (
    ADR0295_BATCH_COUNT,
    ADR0295_POOL_CANDIDATE_ATTEMPTS,
    ADR0295_POOL_CONTEXT_COUNT,
    ADR0295_POOL_SHA256,
    ChipClassificationGuard,
    NormalizedSizingOpportunityFloor,
    QualificationStopReason,
    SizingPowerClassification,
    SizingPowerObservation,
    SizingPowerQualificationResult,
    build_adr0295_sizing_power_pool,
    classify_sizing_opportunity,
)

_ROOT = Path(__file__).parents[1]


class SizingPowerPoolTests(unittest.TestCase):
    @staticmethod
    def _observation(
        *,
        context_index: int,
        context_digest: str,
        classification: SizingPowerClassification,
    ) -> SizingPowerObservation:
        return SizingPowerObservation(
            context_index=context_index,
            context_digest=context_digest,
            full_value_chips=0.0,
            narrow_value_chips=0.0,
            payoff_span=1,
            classification=classification,
            max_probability_residual=0.0,
            max_chip_objective_error=0.0,
        )

    def test_three_frozen_pools_are_deterministic_unique_and_structural(self) -> None:
        pools = tuple(
            build_adr0295_sizing_power_pool(batch_index=index)
            for index in range(ADR0295_BATCH_COUNT)
        )
        repeated = tuple(
            build_adr0295_sizing_power_pool(batch_index=index)
            for index in range(ADR0295_BATCH_COUNT)
        )
        self.assertEqual(pools, repeated)
        self.assertEqual(tuple(pool.digest for pool in pools), ADR0295_POOL_SHA256)
        self.assertEqual(
            tuple(pool.candidate_attempts for pool in pools),
            ADR0295_POOL_CANDIDATE_ATTEMPTS,
        )
        self.assertEqual(len({pool.digest for pool in pools}), ADR0295_BATCH_COUNT)
        for batch_index, pool in enumerate(pools):
            self.assertEqual(pool.batch_index, batch_index)
            self.assertEqual(len(pool.contexts), ADR0295_POOL_CONTEXT_COUNT)
            self.assertGreaterEqual(pool.candidate_attempts, ADR0295_POOL_CONTEXT_COUNT)
            for context_index, context in enumerate(pool.contexts):
                self.assertEqual(
                    context.context_id,
                    f"adr0295-power-b{batch_index}-c{context_index:02d}",
                )
                signs = context.showdown_signs
                self.assertEqual({value for row in signs for value in row}, {-1, 1})
                self.assertGreaterEqual(len(set(signs)), 2)
                columns = tuple(
                    tuple(row[column] for row in signs) for column in range(3)
                )
                self.assertGreaterEqual(len(set(columns)), 2)

        self.assertEqual(
            build_adr0293_confirmation_panel().digest,
            ADR0293_PANEL_SHA256,
        )

    def test_pool_and_diagnostic_sources_import_no_action_candidate(self) -> None:
        paths = (
            _ROOT / "src/pontius/sizing_power_diagnostic.py",
            _ROOT / "tests/test_candidate_blind_sizing_power.py",
        )
        forbidden_module = "pontius.legal_action_abstraction"
        forbidden_relative = "legal_action_abstraction"
        for path in paths:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            imported = {
                node.module
                for node in ast.walk(tree)
                if isinstance(node, ast.ImportFrom) and node.module is not None
            }
            self.assertNotIn(forbidden_module, imported)
            self.assertNotIn(forbidden_relative, imported)

    def test_qualification_semantic_units_fail_closed(self) -> None:
        floor = NormalizedSizingOpportunityFloor(1e-4)
        guard = ChipClassificationGuard(1e-8)
        self.assertIs(
            classify_sizing_opportunity(
                full_value_chips=1.01,
                narrow_value_chips=1.0,
                payoff_span=50,
                opportunity_floor=floor,
                classification_guard=guard,
            ),
            SizingPowerClassification.QUALIFYING,
        )
        self.assertIs(
            classify_sizing_opportunity(
                full_value_chips=1.005,
                narrow_value_chips=1.0,
                payoff_span=50,
                opportunity_floor=floor,
                classification_guard=guard,
            ),
            SizingPowerClassification.AMBIGUOUS,
        )
        with self.assertRaisesRegex(TypeError, "normalized semantic"):
            classify_sizing_opportunity(
                full_value_chips=1.01,
                narrow_value_chips=1.0,
                payoff_span=50,
                opportunity_floor=guard,  # type: ignore[arg-type]
                classification_guard=guard,
            )
        with self.assertRaisesRegex(TypeError, "chip semantic"):
            classify_sizing_opportunity(
                full_value_chips=1.01,
                narrow_value_chips=1.0,
                payoff_span=50,
                opportunity_floor=floor,
                classification_guard=floor,  # type: ignore[arg-type]
            )

    def test_qualification_result_terminal_state_and_pool_binding_fail_closed(
        self,
    ) -> None:
        pool = build_adr0295_sizing_power_pool(batch_index=0)

        target_with_earlier_ambiguity = tuple(
            self._observation(
                context_index=index,
                context_digest=pool.contexts[index].digest,
                classification=(
                    SizingPowerClassification.AMBIGUOUS
                    if index == 0
                    else SizingPowerClassification.QUALIFYING
                ),
            )
            for index in range(13)
        )
        with self.assertRaisesRegex(ValueError, "contains an ambiguity"):
            SizingPowerQualificationResult(
                batch_index=0,
                pool_digest=pool.digest,
                stop_reason=QualificationStopReason.TARGET_REACHED,
                observations=target_with_earlier_ambiguity,
                qualified_indices=tuple(range(1, 13)),
            )

        ambiguity_after_target = tuple(
            self._observation(
                context_index=index,
                context_digest=pool.contexts[index].digest,
                classification=(
                    SizingPowerClassification.AMBIGUOUS
                    if index == 12
                    else SizingPowerClassification.QUALIFYING
                ),
            )
            for index in range(13)
        )
        with self.assertRaisesRegex(ValueError, "already reached its target"):
            SizingPowerQualificationResult(
                batch_index=0,
                pool_digest=pool.digest,
                stop_reason=QualificationStopReason.AMBIGUOUS,
                observations=ambiguity_after_target,
                qualified_indices=tuple(range(12)),
            )

        mismatched_prefix = tuple(
            self._observation(
                context_index=index,
                context_digest=(
                    "0" * 64 if index == 0 else pool.contexts[index].digest
                ),
                classification=SizingPowerClassification.QUALIFYING,
            )
            for index in range(12)
        )
        result = SizingPowerQualificationResult(
            batch_index=0,
            pool_digest=pool.digest,
            stop_reason=QualificationStopReason.TARGET_REACHED,
            observations=mismatched_prefix,
            qualified_indices=tuple(range(12)),
        )
        with self.assertRaisesRegex(ValueError, "differ from their pool prefix"):
            result.qualified_panel(pool=pool)


if __name__ == "__main__":
    unittest.main()
