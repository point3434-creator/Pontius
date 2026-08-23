from __future__ import annotations

import unittest
from dataclasses import dataclass
from types import SimpleNamespace
from unittest.mock import patch

import pontius.cross_payoff_adjoint_result as typed
import pontius.device_fold_resident_heterogeneous_leaf_contraction_v2 as contraction_v2
import pontius.device_fold_resident_leaf_adjoint_cfr_v2 as evaluator_v2
import pontius.resident_record_to_hand_fold_v2 as fold_v2
from pontius.resident_record_to_hand_fold_v2 import (
    AbsoluteNegativeReachAllowance,
    RelativeNegativeReachAllowance,
    ResidentReachTolerances,
)


@dataclass(frozen=True)
class _Cache:
    target_seat: int


class CrossPayoffAdjointResultTests(unittest.TestCase):
    def setUp(self) -> None:
        self.layout = SimpleNamespace(num_players=6)
        self.automata = {"terminal": SimpleNamespace(target_player=4)}
        self.cache = _Cache(target_seat=4)
        self.reach_tolerances = ResidentReachTolerances(
            absolute=AbsoluteNegativeReachAllowance(1e-12),
            relative=RelativeNegativeReachAllowance(1e-10),
        )
        self.raw = SimpleNamespace(
            traverser=0,
            reads=(),
            terminal_contractions=7,
        )
        self.identity = typed.CrossPayoffContextIdentity(
            layout_object_id=id(self.layout),
            num_players=6,
            public_node_count=0,
            topology_sha256="0" * 64,
            action_schema_sha256="1" * 64,
            layout_numeric_sha256="2" * 64,
            game_structural_sha256="3" * 64,
            game_provenance_sha256="4" * 64,
            source_probability_sha256="5" * 64,
        )

    def test_device_fold_successor_carries_terminal_payoff_role(self) -> None:
        with (
            patch.object(
                typed,
                "device_fold_resident_leaf_adjoint_cfr_traverser_v2",
                return_value=self.raw,
            ) as successor,
            patch.object(
                typed._legacy_cross_payoff,
                "evaluate_device_fold_cross_payoff_leaf_adjoint",
                side_effect=AssertionError("legacy fold reached"),
            ) as legacy,
            patch.object(
                typed,
                "_derive_context_identity",
                return_value=self.identity,
            ),
        ):
            result = typed.evaluate_typed_device_fold_cross_payoff_leaf_adjoint(
                self.layout,
                object(),
                object(),
                (),
                self.automata,
                acting_player=0,
                payoff_player=4,
                belief_cache=object(),
                automaton_cache=self.cache,
                cupy_sparse=object(),
                reach_tolerances=self.reach_tolerances,
            )
        successor.assert_called_once()
        legacy.assert_not_called()
        self.assertEqual(result.acting_player, 0)
        self.assertEqual(result.payoff_player, 4)
        self.assertIs(result.raw_result, self.raw)
        self.assertEqual(result.terminal_contractions, 7)

    def test_affine_successor_rejects_crossed_cache_before_legacy_call(self) -> None:
        with patch.object(
            typed._legacy_sized_cross_payoff,
            "evaluate_multi_size_affine_cross_payoff",
            return_value=self.raw,
        ) as legacy, self.assertRaisesRegex(ValueError, "wrong payoff role"):
            typed.evaluate_typed_multi_size_affine_cross_payoff(
                self.layout,
                object(),
                object(),
                (),
                self.automata,
                acting_player=0,
                payoff_player=4,
                belief_cache=object(),
                automaton_cache=SimpleNamespace(target_seat=3),
                cupy_sparse=object(),
            )
        legacy.assert_not_called()

    def test_typed_device_path_is_transitively_v2(self) -> None:
        self.assertIs(
            evaluator_v2.contract_device_fold_resident_heterogeneous_leaf_terms_v2,
            contraction_v2.contract_device_fold_resident_heterogeneous_leaf_terms_v2,
        )
        self.assertIs(
            contraction_v2.finalize_resident_record_accumulators_v2,
            fold_v2.finalize_resident_record_accumulators_v2,
        )

    def test_wrapper_is_factory_only_and_binder_rejects_crossed_raw_role(self) -> None:
        raw = SimpleNamespace(traverser=0, payoff_player=3, reads=())
        with self.assertRaisesRegex(TypeError, "factory-only"):
            typed.CrossPayoffAdjointResult(
                acting_player=0,
                payoff_player=4,
                raw_result=raw,
            )
        with (
            patch.object(
                typed,
                "_derive_context_identity",
                return_value=self.identity,
            ),
            self.assertRaisesRegex(ValueError, "another payoff player"),
        ):
            typed.bind_cross_payoff_adjoint_result(
                self.layout,
                (),
                raw,
                acting_player=0,
                payoff_player=4,
            )


if __name__ == "__main__":
    unittest.main()
