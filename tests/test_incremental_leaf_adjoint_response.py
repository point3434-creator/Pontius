from __future__ import annotations

import json
import math
from pathlib import Path
import unittest

from pontius.h32_policy_delta_verifier_audit import parse_h32_policy_delta_verifier_config
from pontius.incremental_leaf_adjoint_response import (
    compile_leaf_adjoint_response_caches,
    evaluate_incremental_leaf_adjoint_seat,
    verify_incremental_leaf_adjoint_candidate,
)
from pontius.incremental_policy_tt import compile_policy_probability_tape
from pontius.leaf_adjoint_checkpoint_ladder_audit import _build_case
from pontius.leaf_adjoint_evaluation import evaluate_leaf_adjoint_profile
from pontius.public_policy_tt import _information_key, information_schema_for_axes
from pontius.river import parse_cards
from pontius.selector_stable_affine_response import (
    certify_selector_stable_affine_envelope,
    evaluate_selector_stable_affine_leaf_adjoint_seat,
    selector_stable_affine_values_at_scale,
)


_ROOT = Path(__file__).parents[1]


class IncrementalLeafAdjointResponseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        try:
            import scipy  # noqa: F401
        except ImportError as error:
            raise unittest.SkipTest("optional SciPy screen") from error
        config = json.loads(
            (_ROOT / "experiments/configs/h32-policy-delta-verifier-audit-v1.json").read_text(
                encoding="utf-8"
            )
        )
        cls.parsed = parse_h32_policy_delta_verifier_config(config)
        board = parse_cards(*cls.parsed["board"])
        cls.belief, cls.layout, cls.sparse, retained = _build_case(
            parsed=cls.parsed,
            board=board,
            hand_count=3,
            family="balanced",
        )
        cls.workspace, _, cls.automata = retained
        cls.blueprint = {}
        cls.caches = compile_leaf_adjoint_response_caches(
            cls.layout,
            cls.workspace,
            cls.sparse,
            cls.blueprint,
            cls.automata,
            hands_by_player=cls.belief.hands_by_player,
            maximum_feature_width_per_batch=384,
        )

    def _candidate(self, key: str, action_index: int) -> dict:
        actions = self.layout.information_schema()[key]
        return {
            key: {
                action: float(index == action_index)
                for index, action in enumerate(actions)
            }
        }

    def _assert_candidate_exact(self, candidate: dict) -> tuple:
        probabilities = compile_policy_probability_tape(
            self.layout,
            self.belief.hands_by_player,
            candidate,
        )
        incremental = tuple(
            evaluate_incremental_leaf_adjoint_seat(cache, probabilities)
            for cache in self.caches
        )
        complete = evaluate_leaf_adjoint_profile(
            self.layout,
            self.workspace,
            self.sparse,
            candidate,
            self.automata,
            hands_by_player=self.belief.hands_by_player,
            maximum_feature_width_per_batch=384,
        )
        for seat, row in enumerate(incremental):
            reference = complete.seats[seat]
            self.assertAlmostEqual(row.profile_utility, reference.profile_utility, places=12)
            self.assertAlmostEqual(
                row.best_response_value, reference.best_response_value, places=12
            )
            self.assertAlmostEqual(row.deviation_gain, reference.deviation_gain, places=12)
            self.assertEqual(row.best_response_actions, reference.best_response_actions)
            self.assertEqual(
                row.affected_terminal_contractions + row.reused_terminal_numerators,
                row.full_terminal_contractions,
            )
        return incremental

    def _interpolated_candidate(
        self,
        key: str,
        endpoint_action_index: int,
        scale: float,
    ) -> dict:
        actions = self.layout.information_schema()[key]
        source = 1.0 / len(actions)
        return {
            key: {
                action: (1.0 - scale) * source
                + scale * float(index == endpoint_action_index)
                for index, action in enumerate(actions)
            }
        }

    def _affine_rows(self, candidate: dict) -> tuple:
        probabilities = compile_policy_probability_tape(
            self.layout,
            self.belief.hands_by_player,
            candidate,
        )
        changed_node = next(
            node_index
            for node_index, (source, endpoint) in enumerate(
                zip(
                    self.caches[0].source_probabilities,
                    probabilities,
                    strict=True,
                )
            )
            if source is not None
            and endpoint is not None
            and not (source == endpoint).all()
        )
        actor = self.layout.nodes[changed_node].player
        return tuple(
            evaluate_selector_stable_affine_leaf_adjoint_seat(
                cache,
                probabilities,
                acting_player=actor,
                selector_margin_allowance=1e-14,
            )
            for cache in self.caches
        )

    def test_source_cache_matches_complete_leaf_adjoint(self) -> None:
        complete = evaluate_leaf_adjoint_profile(
            self.layout,
            self.workspace,
            self.sparse,
            self.blueprint,
            self.automata,
            hands_by_player=self.belief.hands_by_player,
            maximum_feature_width_per_batch=384,
        )
        for seat, cache in enumerate(self.caches):
            source = cache.source_evaluation
            reference = complete.seats[seat]
            self.assertAlmostEqual(source.profile_utility, reference.profile_utility, places=12)
            self.assertAlmostEqual(
                source.best_response_value, reference.best_response_value, places=12
            )
            self.assertEqual(source.best_response_actions, reference.best_response_actions)
            self.assertGreater(cache.persistent_numeric_bytes, 0)

    def test_same_seat_and_opponent_atoms_are_exact(self) -> None:
        schema = self.layout.information_schema()
        key = next(iter(schema))
        actor = next(
            node.player
            for node in self.layout.nodes
            if node.player >= 0 and node.actions == schema[key]
        )
        candidate = self._candidate(key, 0)
        rows = self._assert_candidate_exact(candidate)
        self.assertEqual(rows[actor].affected_terminal_contractions, 0)
        self.assertTrue(
            any(
                row.affected_terminal_contractions > 0
                for seat, row in enumerate(rows)
                if seat != actor
            )
        )

    def test_call_order_identity_and_selector_switch_customer(self) -> None:
        schema = self.layout.information_schema()
        customers = []
        for key, actions in tuple(schema.items())[:24]:
            if len(actions) < 2:
                continue
            candidate = self._candidate(key, 0)
            rows = self._assert_candidate_exact(candidate)
            customers.append((candidate, rows))
            if sum(row.response_action_flips for row in rows) > 0:
                break
        self.assertTrue(customers)
        self.assertGreater(
            sum(row.response_action_flips for row in customers[-1][1]),
            0,
        )
        identity_probabilities = compile_policy_probability_tape(
            self.layout,
            self.belief.hands_by_player,
            self.blueprint,
        )
        for cache in self.caches:
            identity = evaluate_incremental_leaf_adjoint_seat(
                cache, identity_probabilities
            )
            self.assertEqual(identity.affected_terminal_contractions, 0)
            self.assertAlmostEqual(
                identity.best_response_value,
                cache.source_evaluation.best_response_value,
                places=14,
            )
            self.assertEqual(
                identity.best_response_actions,
                cache.source_evaluation.best_response_actions,
            )

    def test_zero_reach_atom_can_change_an_opponent_response(self) -> None:
        schema = information_schema_for_axes(
            self.layout,
            self.belief.hands_by_player,
        )
        pure = {
            key: {
                action: float(index == 0)
                for index, action in enumerate(actions)
            }
            for key, actions in schema.items()
        }
        caches = compile_leaf_adjoint_response_caches(
            self.layout,
            self.workspace,
            self.sparse,
            pure,
            self.automata,
            hands_by_player=self.belief.hands_by_player,
            maximum_feature_width_per_batch=384,
        )
        root = self.layout.nodes[0]
        off_path_nodes = set()
        stack = [root.children[1]]
        while stack:
            node_index = stack.pop()
            if node_index in off_path_nodes:
                continue
            off_path_nodes.add(node_index)
            stack.extend(self.layout.nodes[node_index].children)

        found = None
        for node_index in sorted(off_path_nodes):
            node = self.layout.nodes[node_index]
            if node.player < 0 or len(node.actions) < 2:
                continue
            key = _information_key(
                self.layout,
                node.player,
                self.belief.hands_by_player[node.player][0],
                node.history,
            )
            candidate = {name: dict(row) for name, row in pure.items()}
            candidate[key] = {
                action: float(index == 1)
                for index, action in enumerate(node.actions)
            }
            probabilities = compile_policy_probability_tape(
                self.layout,
                self.belief.hands_by_player,
                candidate,
            )
            rows = tuple(
                evaluate_incremental_leaf_adjoint_seat(cache, probabilities)
                for cache in caches
            )
            utility_error = max(
                abs(row.profile_utility - caches[seat].source_evaluation.profile_utility)
                for seat, row in enumerate(rows)
            )
            response_delta = max(
                abs(
                    row.best_response_value
                    - caches[seat].source_evaluation.best_response_value
                )
                for seat, row in enumerate(rows)
            )
            if utility_error <= 1e-14 and response_delta > 1e-12:
                found = (candidate, rows)
                break
        self.assertIsNotNone(found)
        assert found is not None
        candidate, rows = found
        complete = evaluate_leaf_adjoint_profile(
            self.layout,
            self.workspace,
            self.sparse,
            candidate,
            self.automata,
            hands_by_player=self.belief.hands_by_player,
            maximum_feature_width_per_batch=384,
        )
        for seat, row in enumerate(rows):
            self.assertAlmostEqual(
                row.profile_utility,
                complete.seats[seat].profile_utility,
                places=12,
            )
            self.assertAlmostEqual(
                row.best_response_value,
                complete.seats[seat].best_response_value,
                places=12,
            )
            self.assertEqual(
                row.best_response_actions,
                complete.seats[seat].best_response_actions,
            )

    def test_incremental_fixed_prefix_matches_complete_vector_and_cap_stop(self) -> None:
        key = next(iter(self.layout.information_schema()))
        candidate = self._candidate(key, 0)
        complete = evaluate_leaf_adjoint_profile(
            self.layout,
            self.workspace,
            self.sparse,
            candidate,
            self.automata,
            hands_by_player=self.belief.hands_by_player,
            maximum_feature_width_per_batch=384,
        )
        blueprint_gains = tuple(
            cache.source_evaluation.deviation_gain for cache in self.caches
        )
        wide = verify_incremental_leaf_adjoint_candidate(
            candidate_id="one_atom",
            layout=self.layout,
            policy=candidate,
            hands_by_player=self.belief.hands_by_player,
            response_caches=self.caches,
            blueprint_deviation_gains=(1e6,) * 6,
            best_complete_nash_conv=1e6,
            payoff_span=float(self.layout.game.payoff_span),
            raw_guard=0.0,
            seat_order=(0, 1, 2, 3, 4, 5),
        )
        self.assertTrue(wide["complete"])
        self.assertLessEqual(
            max(
                abs(left - right)
                for left, right in zip(
                    wide["quality"]["deviation_gains"],
                    complete.evaluation.deviation_gains,
                    strict=True,
                )
            ),
            2e-14,
        )
        violating_seat = next(
            seat
            for seat, (source, candidate_gain) in enumerate(
                zip(blueprint_gains, complete.evaluation.deviation_gains, strict=True)
            )
            if candidate_gain > source
        )
        cap = verify_incremental_leaf_adjoint_candidate(
            candidate_id="one_atom",
            layout=self.layout,
            policy=candidate,
            hands_by_player=self.belief.hands_by_player,
            response_caches=self.caches,
            blueprint_deviation_gains=blueprint_gains,
            best_complete_nash_conv=1e6,
            payoff_span=float(self.layout.game.payoff_span),
            raw_guard=0.0,
            seat_order=(violating_seat,) + tuple(
                seat for seat in range(6) if seat != violating_seat
            ),
        )
        self.assertFalse(cap["complete"])
        self.assertEqual(cap["stop_reason"], "blueprint_cap")
        self.assertEqual(cap["stop_seat"], violating_seat)
        self.assertEqual(cap["evaluated_seat_count"], 1)

    def test_selector_stable_affine_values_match_direct_evaluation(self) -> None:
        schema = self.layout.information_schema()
        witness = None
        for key, actions in tuple(schema.items())[:48]:
            if len(actions) < 2:
                continue
            endpoint = self._candidate(key, 0)
            rows = self._affine_rows(endpoint)
            stable = min(row.selector_stable_scale for row in rows)
            if stable > 1e-8:
                witness = (key, rows, min(0.25, stable * 0.5))
                break
        self.assertIsNotNone(witness)
        assert witness is not None
        key, rows, scale = witness
        candidate = self._interpolated_candidate(key, 0, scale)
        probabilities = compile_policy_probability_tape(
            self.layout,
            self.belief.hands_by_player,
            candidate,
        )
        direct = tuple(
            evaluate_incremental_leaf_adjoint_seat(cache, probabilities)
            for cache in self.caches
        )
        for affine, exact in zip(rows, direct, strict=True):
            utility, response, gain = selector_stable_affine_values_at_scale(
                affine, scale
            )
            self.assertAlmostEqual(utility, exact.profile_utility, places=12)
            self.assertAlmostEqual(response, exact.best_response_value, places=12)
            self.assertAlmostEqual(gain, exact.deviation_gain, places=12)
            self.assertEqual(exact.response_action_flips, 0)

    def test_affine_scope_rejects_two_changed_public_nodes(self) -> None:
        schema = self.layout.information_schema()
        first_key = next(iter(schema))
        first_history = first_key.rsplit("|history=", 1)[-1]
        second_key = next(
            key
            for key in schema
            if key.rsplit("|history=", 1)[-1] != first_history
        )
        candidate = {
            **self._candidate(first_key, 0),
            **self._candidate(second_key, 0),
        }
        probabilities = compile_policy_probability_tape(
            self.layout,
            self.belief.hands_by_player,
            candidate,
        )
        with self.assertRaisesRegex(ValueError, "exactly one changed public node"):
            evaluate_selector_stable_affine_leaf_adjoint_seat(
                self.caches[0],
                probabilities,
                acting_player=0,
            )

    def test_affine_selector_breakpoint_precedes_observed_endpoint_flip(self) -> None:
        schema = self.layout.information_schema()
        witness = None
        for key, actions in tuple(schema.items())[:64]:
            if len(actions) < 2:
                continue
            endpoint = self._candidate(key, 0)
            probabilities = compile_policy_probability_tape(
                self.layout,
                self.belief.hands_by_player,
                endpoint,
            )
            direct = tuple(
                evaluate_incremental_leaf_adjoint_seat(cache, probabilities)
                for cache in self.caches
            )
            if sum(row.response_action_flips for row in direct) == 0:
                continue
            affine = self._affine_rows(endpoint)
            witness = (direct, affine)
            break
        self.assertIsNotNone(witness)
        assert witness is not None
        direct, affine = witness
        self.assertGreater(sum(row.response_action_flips for row in direct), 0)
        self.assertLess(min(row.selector_stable_scale for row in affine), 1.0)

    def test_affine_envelope_selects_only_a_directly_exact_improving_scale(self) -> None:
        schema = self.layout.information_schema()
        blueprint_gains = tuple(
            cache.source_evaluation.deviation_gain for cache in self.caches
        )
        blueprint_nash = math.fsum(blueprint_gains)
        scale_grid = tuple(2.0**-index for index in range(34))
        witness = None
        for key, actions in tuple(schema.items())[:96]:
            if len(actions) < 2:
                continue
            for action_index in range(len(actions)):
                endpoint = self._candidate(key, action_index)
                rows = self._affine_rows(endpoint)
                envelope = certify_selector_stable_affine_envelope(
                    rows,
                    blueprint_deviation_gains=blueprint_gains,
                    blueprint_nash_conv=blueprint_nash,
                    raw_guard=1e6,
                    scale_grid=scale_grid,
                    safety_fraction=0.5,
                    numerical_allowance=1e-12,
                )
                if envelope.complete:
                    witness = (key, action_index, rows, envelope)
                    break
            if witness is not None:
                break
        self.assertIsNotNone(witness)
        assert witness is not None
        key, action_index, rows, envelope = witness
        assert envelope.selected_scale is not None
        candidate = self._interpolated_candidate(
            key, action_index, envelope.selected_scale
        )
        direct = verify_incremental_leaf_adjoint_candidate(
            candidate_id="affine_selected",
            layout=self.layout,
            policy=candidate,
            hands_by_player=self.belief.hands_by_player,
            response_caches=self.caches,
            blueprint_deviation_gains=(1e6,) * 6,
            best_complete_nash_conv=1e6,
            payoff_span=float(self.layout.game.payoff_span),
            raw_guard=0.0,
            seat_order=(0, 1, 2, 3, 4, 5),
        )
        self.assertTrue(direct["complete"])
        self.assertEqual(direct["response_action_flips"], 0)
        self.assertLessEqual(
            max(
                abs(left - right)
                for left, right in zip(
                    envelope.predicted_deviation_gains,
                    direct["quality"]["deviation_gains"],
                    strict=True,
                )
            ),
            2e-12,
        )
        self.assertAlmostEqual(
            envelope.predicted_nash_conv,
            direct["quality"]["nash_conv"],
            places=11,
        )
        limiting = min(rows, key=lambda row: row.selector_stable_scale)
        if limiting.selector_stable_scale < 1.0:
            with self.assertRaisesRegex(ValueError, "exceeds selector-stable"):
                selector_stable_affine_values_at_scale(
                    limiting,
                    (limiting.selector_stable_scale + 1.0) * 0.5,
                )


if __name__ == "__main__":
    unittest.main()
