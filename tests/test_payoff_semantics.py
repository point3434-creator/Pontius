from __future__ import annotations

import ast
from pathlib import Path
from types import SimpleNamespace
import unittest

from pontius.payoff_semantics import normalized_quality, payoff_span, raw_guard


_ROOT = Path(__file__).parents[1]

# Frozen evidence runners retain their byte-pinned historical formulas. This
# exact inventory is the only exception: any added or moved occurrence fails.
_FROZEN_LEGACY_STACK_SPAN_EXPRESSIONS = {
    ("h32_action_conditioned_widened_selector_trial.py", 381, "payoff_span"),
    ("h32_action_conditioned_widened_selector_trial.py", 423, "raw_guard"),
    ("h32_atomic_response_preflight.py", 380, "raw_guard"),
    ("h32_atomic_response_preflight.py", 399, "payoff_span"),
    ("h32_atomic_response_preflight.py", 410, "payoff_span"),
    ("h32_atomic_street_scheduler_audit.py", 467, "payoff_span"),
    ("h32_continuation_root_strategy_trial.py", 290, "payoff_span"),
    ("h32_continuation_root_strategy_trial.py", 333, "raw_guard"),
    ("h32_deep_horizon_opportunity_audit.py", 267, "payoff_span"),
    ("h32_deep_horizon_opportunity_audit.py", 346, "raw_guard"),
    ("h32_deep_horizon_opportunity_audit.py", 511, "raw_guard"),
    ("h32_fresh_causal_direction_screen.py", 511, "raw_guard"),
    ("h32_fresh_causal_direction_screen.py", 717, "payoff_span"),
    ("h32_fresh_causal_direction_screen.py", 760, "raw_guard"),
    ("h32_fresh_causal_direction_screen.py", 770, "payoff_span"),
    ("h32_fresh_causal_direction_screen.py", 837, "payoff_span"),
    ("h32_fresh_causal_direction_screen.py", 1119, "raw_guard"),
    ("h32_fresh_public_block_radius_audit.py", 323, "payoff_span"),
    ("h32_fresh_public_block_radius_audit.py", 345, "raw_guard"),
    ("h32_fresh_public_block_value_audit.py", 487, "payoff_span"),
    ("h32_fresh_regret_vertex_opportunity_audit.py", 457, "payoff_span"),
    ("h32_fresh_regret_vertex_opportunity_audit.py", 478, "raw_guard"),
    ("h32_fresh_regret_vertex_opportunity_audit.py", 484, "payoff_span"),
    ("h32_fresh_selector_stable_affine_street_audit.py", 587, "payoff_span"),
    ("h32_fresh_selector_stable_affine_street_audit.py", 787, "payoff_span"),
    ("h32_fresh_union_value_audit.py", 369, "payoff_span"),
    ("h32_fresh_union_value_audit.py", 450, "payoff_span"),
    ("h32_policy_delta_verifier_audit.py", 671, "raw_guard"),
    ("h32_policy_delta_verifier_audit.py", 735, "payoff_span"),
    ("h32_resident_record_to_hand_fold_differential.py", 527, "raw_guard"),
    ("h32_resident_record_to_hand_fold_differential.py", 586, "raw_guard"),
    ("h32_resident_verifier_audit.py", 431, "raw_guard"),
    ("h32_resident_verifier_audit.py", 445, "payoff_span"),
    ("h32_resident_verifier_audit.py", 516, "payoff_span"),
    ("h32_retained_affine_selector_cascade_replay.py", 899, "payoff_span"),
    ("h32_retained_affine_selector_cascade_replay.py", 932, "raw_guard"),
    ("h32_retained_affine_selector_cascade_replay.py", 944, "payoff_span"),
    ("h32_selector_stable_affine_certificate_audit.py", 403, "payoff_span"),
    ("h32_selector_stable_affine_certificate_audit.py", 465, "raw_guard"),
    ("h32_selector_stable_affine_certificate_audit.py", 556, "payoff_span"),
    ("h32_shared_response_allocator_lifecycle_replay.py", 420, "payoff_span"),
    ("h32_tier_b_opponent_batch_differential.py", 484, "payoff_span"),
    ("h32_tier_b_opponent_batch_differential.py", 725, "raw_guard"),
}


def _contains_stack_subscript(node: ast.AST | None) -> bool:
    return node is not None and any(
        isinstance(child, ast.Subscript)
        and isinstance(child.slice, ast.Constant)
        and child.slice.value == "stack"
        for child in ast.walk(node)
    )


def _stack_span_expressions() -> set[tuple[str, int, str]]:
    found: set[tuple[str, int, str]] = set()
    for path in (_ROOT / "src/pontius").glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.keyword)
                and node.arg == "payoff_span"
                and _contains_stack_subscript(node.value)
            ):
                found.add((path.name, node.lineno, "payoff_span"))
            if isinstance(node, (ast.Assign, ast.AnnAssign)):
                targets = node.targets if isinstance(node, ast.Assign) else [node.target]
                if (
                    node.value is not None
                    and _contains_stack_subscript(node.value)
                    and any(
                        isinstance(child, ast.Name) and "raw_guard" in child.id
                        for target in targets
                        for child in ast.walk(target)
                    )
                ):
                    found.add((path.name, node.lineno, "raw_guard"))
    return found


class PayoffSemanticsTests(unittest.TestCase):
    def test_helpers_use_game_span_when_stack_coincidence_breaks(self) -> None:
        layout = SimpleNamespace(
            game=SimpleNamespace(payoff_span=48.0), stack=30.0
        )
        self.assertEqual(payoff_span(layout), 48.0)
        self.assertEqual(raw_guard(layout, 0.125), 6.0)
        self.assertEqual(normalized_quality(layout, 12.0), 0.25)

    def test_helpers_fail_closed_on_invalid_inputs(self) -> None:
        for span in (0.0, -1.0, float("inf")):
            with self.subTest(span=span), self.assertRaises(ValueError):
                payoff_span(SimpleNamespace(game=SimpleNamespace(payoff_span=span)))
        with self.assertRaises(ValueError):
            raw_guard(SimpleNamespace(game=SimpleNamespace(payoff_span=1.0)), -1.0)

    def test_no_new_stack_as_span_or_guard_expressions(self) -> None:
        self.assertEqual(
            _FROZEN_LEGACY_STACK_SPAN_EXPRESSIONS,
            _stack_span_expressions(),
            "new runners must use payoff_semantics helpers; frozen exceptions are exact",
        )


if __name__ == "__main__":
    unittest.main()
