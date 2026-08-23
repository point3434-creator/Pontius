from __future__ import annotations

import hashlib
import importlib.util
import json
import math
import struct
import tempfile
import unittest
from dataclasses import fields, replace
from pathlib import Path

import numpy as np

from pontius.behavioral_one_seat_master import solve_behavioral_one_seat_master
from pontius.cross_payoff_adjoint_result import bind_cross_payoff_adjoint_result
from pontius.dense_root_cross_payoff_control import dense_root_cross_payoff_control
from pontius.factorized_belief import FactorizedCardBelief
from pontius.incremental_policy_tt import compile_policy_probability_tape
from pontius.pre_bet_initial_row_cache import (
    PreBetInitialRow,
    PreBetInitialRowSource,
    assemble_pre_bet_gain_rows,
    build_pre_bet_row_cache_identity,
    cpu_h2_control_row_primitive_digest,
    lookup_pre_bet_initial_row_cache,
    prepare_pre_bet_restricted_master_successor,
    write_pre_bet_initial_row_cache,
)
from pontius.public_node_behavioral_axis import compile_public_node_behavioral_axis
from pontius.public_node_open_axis import (
    build_public_node_affine_source_context,
    public_node_open_axis_payoff_row,
)
from pontius.public_tree_tensor import PublicTreeTensorEvaluator
from pontius.river import parse_cards
from pontius.river_multiway import MultiwayRiverDeal, MultiwayRiverHoldem
from pontius.sequence_form_open_axis import (
    splice_fixed_response_probability_tape_for_axes,
)


def _canonical_json_bytes(value: object) -> bytes:
    return (
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")


def _immutable(values: np.ndarray) -> np.ndarray:
    result = np.ascontiguousarray(values, dtype=np.float64)
    result.flags.writeable = False
    return result


class PreBetInitialRowCacheTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        board = parse_cards("2c", "7d", "9h", "Js", "Qc")
        available = tuple(card for card in range(52) if card not in set(board))
        hands = (
            (
                tuple(sorted(available[0:2])),
                tuple(sorted(available[2:4])),
            ),
            (
                tuple(sorted(available[4:6])),
                tuple(sorted(available[6:8])),
            ),
        )
        belief = FactorizedCardBelief(
            hands_by_player=hands,
            mixture_weights=[0.4, 0.6],
            unary_weights=(
                np.asarray([[1.0, 2.0], [3.0, 1.0]], dtype=np.float64),
                np.asarray([[2.0, 1.0], [1.0, 4.0]], dtype=np.float64),
            ),
            board=board,
        )
        materialized = belief.materialize()
        joint = {
            MultiwayRiverDeal(
                tuple(
                    hands[player][assignment[player]]
                    for player in range(belief.num_players)
                )
            ): float(probability)
            for assignment, probability in zip(
                materialized.assignments,
                materialized.probabilities,
                strict=True,
            )
        }
        game = MultiwayRiverHoldem.from_joint_weights(
            board=board,
            pot=12.0,
            stacks=(30.0, 30.0),
            bet_size=3.0,
            joint_weights=joint,
        )
        layout = PublicTreeTensorEvaluator(game)
        policy = {}
        for row_index, (key, actions) in enumerate(layout.information_schema().items()):
            first = 0.2 + 0.1 * (row_index % 6)
            policy[key] = {
                action: first if action_index == 0 else 1.0 - first
                for action_index, action in enumerate(actions)
            }
        probabilities = compile_policy_probability_tape(layout, hands, policy)
        evaluation = layout.evaluate(policy)
        identity = build_pre_bet_row_cache_identity(
            layout,
            belief,
            hands,
            policy,
            probabilities,
            acting_player=0,
            public_node=0,
            row_primitive_sha256=cpu_h2_control_row_primitive_digest(),
        )

        sources = []
        rows = []
        source_contexts = []
        for payoff_player in range(layout.num_players):
            raw_result = dense_root_cross_payoff_control(
                layout,
                probabilities,
                acting_player=0,
                payoff_player=payoff_player,
            )
            result = bind_cross_payoff_adjoint_result(
                layout,
                probabilities,
                raw_result,
                acting_player=0,
                payoff_player=payoff_player,
            )
            source_context = build_public_node_affine_source_context(
                layout,
                probabilities,
                result,
                acting_player=0,
                payoff_player=payoff_player,
                public_node=0,
            )
            row = public_node_open_axis_payoff_row(source_context)
            source_contexts.append(source_context)
            sources.append(
                PreBetInitialRowSource(
                    "profile",
                    payoff_player,
                    probabilities,
                    result.source_value,
                )
            )
            rows.append(PreBetInitialRow("profile", payoff_player, row))
        for payoff_player in range(layout.num_players):
            if payoff_player == 0:
                continue
            response_probabilities = splice_fixed_response_probability_tape_for_axes(
                layout,
                probabilities,
                evaluation.best_response_actions[payoff_player],
                responding_player=payoff_player,
                hands_by_player=hands,
            )
            raw_result = dense_root_cross_payoff_control(
                layout,
                response_probabilities,
                acting_player=0,
                payoff_player=payoff_player,
            )
            result = bind_cross_payoff_adjoint_result(
                layout,
                response_probabilities,
                raw_result,
                acting_player=0,
                payoff_player=payoff_player,
            )
            source_context = build_public_node_affine_source_context(
                layout,
                response_probabilities,
                result,
                acting_player=0,
                payoff_player=payoff_player,
                public_node=0,
            )
            row = public_node_open_axis_payoff_row(source_context)
            source_contexts.append(source_context)
            sources.append(
                PreBetInitialRowSource(
                    "fixed_response",
                    payoff_player,
                    response_probabilities,
                    result.source_value,
                )
            )
            rows.append(PreBetInitialRow("fixed_response", payoff_player, row))

        cls.board = board
        cls.hands = hands
        cls.belief = belief
        cls.layout = layout
        cls.policy = policy
        cls.probabilities = probabilities
        cls.evaluation = evaluation
        cls.identity = identity
        cls.sources = tuple(sources)
        cls.rows = tuple(rows)
        cls.source_contexts = tuple(source_contexts)

    def _write(self, directory: str) -> tuple[Path, str]:
        path = Path(directory) / "h2-initial-rows.json"
        digest = write_pre_bet_initial_row_cache(
            path,
            self.identity,
            self.sources,
            self.rows,
        )
        self.assertEqual(digest, hashlib.sha256(path.read_bytes()).hexdigest())
        return path, digest

    def _endpoint_policy(self) -> dict[str, dict[str, float]]:
        endpoint = {key: dict(row) for key, row in self.policy.items()}
        node = self.layout.nodes[0]
        for hand_index, key in enumerate(node.information_keys):
            selected = (hand_index + 1) % len(node.actions)
            endpoint[key] = {
                action: float(action_index == selected)
                for action_index, action in enumerate(node.actions)
            }
        return endpoint

    def _endpoint_probabilities(self) -> tuple[np.ndarray | None, ...]:
        return compile_policy_probability_tape(
            self.layout,
            self.hands,
            self._endpoint_policy(),
        )

    def test_cpu_h2_round_trip_is_byte_and_numerically_exact(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path, digest = self._write(directory)
            lookup = lookup_pre_bet_initial_row_cache(
                path,
                digest,
                self.identity,
                self.sources,
            )
            self.assertTrue(lookup.hit)
            self.assertEqual(lookup.reason, "exact_hit")
            self.assertEqual(lookup.observed_persisted_sha256, digest)
            self.assertGreaterEqual(lookup.lookup_validation_ms, 0.0)
            self.assertIsNotNone(lookup.rows)
            assert lookup.rows is not None
            for original, loaded in zip(self.rows, lookup.rows, strict=True):
                self.assertEqual(
                    (loaded.role, loaded.payoff_player),
                    (original.role, original.payoff_player),
                )
                np.testing.assert_array_equal(
                    loaded.row.flattened(),
                    original.row.flattened(),
                )
                self.assertEqual(
                    loaded.row.flattened().tobytes(order="C"),
                    original.row.flattened().tobytes(order="C"),
                )

            profile_values = self.layout.evaluate(self.policy).evaluation.utilities
            self.assertLessEqual(
                max(
                    abs(source.source_value - profile_values[source.payoff_player])
                    for source in self.sources
                    if source.role == "profile"
                ),
                2e-11,
            )
            for source in self.sources:
                if source.role == "fixed_response":
                    self.assertLessEqual(
                        abs(
                            source.source_value
                            - self.evaluation.evaluation.best_response_values[
                                source.payoff_player
                            ]
                        ),
                        2e-11,
                    )

            endpoint_policy = self._endpoint_policy()
            endpoint = self._endpoint_probabilities()
            for source, loaded in zip(self.sources, lookup.rows, strict=True):
                endpoint_tape = list(source.probabilities)
                endpoint_tape[0] = endpoint[0]
                if source.role == "profile":
                    exact_policy = endpoint_policy
                else:
                    exact_policy = {
                        key: dict(distribution)
                        for key, distribution in endpoint_policy.items()
                    }
                    schema = self.layout.information_schema()
                    for key, selected in self.evaluation.best_response_actions[
                        source.payoff_player
                    ].items():
                        exact_policy[key] = {
                            action: float(action == selected)
                            for action in schema[key]
                        }
                exact = self.layout.evaluate(exact_policy).evaluation.utilities[
                    source.payoff_player
                ]
                self.assertLessEqual(
                    abs(loaded.row.value(tuple(endpoint_tape)) - exact),
                    2e-11,
                )

            preparation = prepare_pre_bet_restricted_master_successor(
                path,
                digest,
                self.identity,
                self.sources,
                self.policy,
                acting_best_response_value=(
                    self.evaluation.evaluation.best_response_values[0]
                ),
            )
            self.assertTrue(preparation.cache_hit)
            self.assertEqual(preparation.warm_steps, 0)
            self.assertEqual(preparation.master_solves, 0)
            self.assertEqual(preparation.candidate_emissions, 0)
            self.assertEqual(preparation.strategy_quality_rows, 0)
            self.assertGreaterEqual(
                preparation.on_clock_ms,
                preparation.lookup_validation_ms,
            )
            self.assertEqual(preparation.external_policy, self.policy)
            self.assertIsNot(preparation.external_policy, self.policy)
            for key in self.policy:
                self.assertIsNot(preparation.external_policy[key], self.policy[key])
            cold_gains = assemble_pre_bet_gain_rows(
                self.identity,
                self.sources,
                self.rows,
                acting_best_response_value=(
                    self.evaluation.evaluation.best_response_values[0]
                ),
            )
            self.assertIsNotNone(preparation.gain_rows)
            assert preparation.gain_rows is not None
            for cold, loaded in zip(cold_gains, preparation.gain_rows, strict=True):
                np.testing.assert_array_equal(cold.flattened(), loaded.flattened())
            np.testing.assert_allclose(
                [row.value(self.probabilities) for row in preparation.gain_rows],
                self.evaluation.evaluation.deviation_gains,
                atol=2e-11,
                rtol=0.0,
            )

    @unittest.skipUnless(importlib.util.find_spec("scipy"), "optional SciPy master")
    def test_loaded_h2_rows_feed_the_same_restricted_master(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path, digest = self._write(directory)
            preparation = prepare_pre_bet_restricted_master_successor(
                path,
                digest,
                self.identity,
                self.sources,
                self.policy,
                acting_best_response_value=(
                    self.evaluation.evaluation.best_response_values[0]
                ),
            )
            self.assertIsNotNone(preparation.gain_rows)
            assert preparation.gain_rows is not None
            cold = assemble_pre_bet_gain_rows(
                self.identity,
                self.sources,
                self.rows,
                acting_best_response_value=(
                    self.evaluation.evaluation.best_response_values[0]
                ),
            )
            axis = compile_public_node_behavioral_axis(
                self.layout,
                self.hands,
                self.policy,
                public_node=0,
            )
            caps = tuple(
                value + 1.0 for value in self.evaluation.evaluation.deviation_gains
            )
            expected = solve_behavioral_one_seat_master(
                axis,
                tuple((row,) for row in cold),
                caps,
                tolerance=1e-9,
            )
            actual = solve_behavioral_one_seat_master(
                axis,
                tuple((row,) for row in preparation.gain_rows),
                caps,
                tolerance=1e-9,
            )
            self.assertEqual(actual.variables, expected.variables)
            self.assertEqual(actual.epigraph, expected.epigraph)
            self.assertEqual(actual.lower_bound, expected.lower_bound)

    def test_every_provenance_digest_is_an_exact_miss_boundary(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path, digest = self._write(directory)
            for field in fields(self.identity):
                if not field.name.endswith("_sha256"):
                    continue
                current = getattr(self.identity, field.name)
                changed = "0" * 64 if current != "0" * 64 else "1" * 64
                adversarial = replace(self.identity, **{field.name: changed})
                lookup = lookup_pre_bet_initial_row_cache(
                    path,
                    digest,
                    adversarial,
                    self.sources,
                )
                self.assertFalse(lookup.hit, msg=field.name)
                self.assertIsNone(lookup.rows, msg=field.name)

            wrong_order = (self.sources[1], self.sources[0], *self.sources[2:])
            lookup = lookup_pre_bet_initial_row_cache(
                path,
                digest,
                self.identity,
                wrong_order,
            )
            self.assertFalse(lookup.hit)
            self.assertEqual(lookup.reason, "current_source_contract_mismatch")

            response = self.sources[-1]
            changed_tape = list(response.probabilities)
            changed_node = next(
                index
                for index, node in enumerate(self.layout.nodes)
                if node.player == response.payoff_player and index != 0
            )
            assert changed_tape[changed_node] is not None
            changed_tape[changed_node] = _immutable(
                np.flip(changed_tape[changed_node], axis=1)
            )
            changed_response = replace(response, probabilities=tuple(changed_tape))
            changed_sources = (*self.sources[:-1], changed_response)
            lookup = lookup_pre_bet_initial_row_cache(
                path,
                digest,
                self.identity,
                changed_sources,
            )
            self.assertFalse(lookup.hit)
            self.assertEqual(lookup.reason, "row_probability_tape_mismatch")

    def test_byte_truth_and_source_numerics_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path, digest = self._write(directory)
            persisted = path.read_bytes()
            path.write_bytes(b"[" + persisted[1:])
            lookup = lookup_pre_bet_initial_row_cache(
                path,
                digest,
                self.identity,
                self.sources,
            )
            self.assertFalse(lookup.hit)
            self.assertEqual(lookup.reason, "persisted_byte_identity_mismatch")

            path, _ = self._write(directory)
            parsed = json.loads(path.read_text(encoding="utf-8"))
            constant = struct.unpack(
                "<d",
                bytes.fromhex(parsed["rows"][0]["row"]["constant_f64le"]),
            )[0]
            parsed["rows"][0]["row"]["constant_f64le"] = struct.pack(
                "<d", constant + 1.0
            ).hex()
            mutated = _canonical_json_bytes(parsed)
            path.write_bytes(mutated)
            mutated_digest = hashlib.sha256(mutated).hexdigest()
            lookup = lookup_pre_bet_initial_row_cache(
                path,
                mutated_digest,
                self.identity,
                self.sources,
            )
            self.assertFalse(lookup.hit)
            self.assertEqual(lookup.reason, "current_source_numerical_mismatch")

            path, _ = self._write(directory)
            parsed = json.loads(path.read_text(encoding="utf-8"))
            parsed["rows"].pop()
            malformed = _canonical_json_bytes(parsed)
            path.write_bytes(malformed)
            lookup = lookup_pre_bet_initial_row_cache(
                path,
                hashlib.sha256(malformed).hexdigest(),
                self.identity,
                self.sources,
            )
            self.assertFalse(lookup.hit)
            self.assertEqual(lookup.reason, "malformed_cache")

            path, _ = self._write(directory)
            parsed = json.loads(path.read_text(encoding="utf-8"))
            parsed["identity"]["num_players"] = float(
                parsed["identity"]["num_players"]
            )
            wrong_type = _canonical_json_bytes(parsed)
            path.write_bytes(wrong_type)
            lookup = lookup_pre_bet_initial_row_cache(
                path,
                hashlib.sha256(wrong_type).hexdigest(),
                self.identity,
                self.sources,
            )
            self.assertFalse(lookup.hit)
            self.assertEqual(lookup.reason, "malformed_cache")

            path, _ = self._write(directory)
            oversized = path.read_bytes() + b" " * 70_000
            path.write_bytes(oversized)
            lookup = lookup_pre_bet_initial_row_cache(
                path,
                hashlib.sha256(oversized).hexdigest(),
                self.identity,
                self.sources,
            )
            self.assertFalse(lookup.hit)
            self.assertEqual(lookup.reason, "cache_size_safety_cap_exceeded")

            shifted = replace(
                self.sources[0],
                source_value=self.sources[0].source_value + 1e-6,
            )
            path, digest = self._write(directory)
            lookup = lookup_pre_bet_initial_row_cache(
                path,
                digest,
                self.identity,
                (shifted, *self.sources[1:]),
            )
            self.assertFalse(lookup.hit)
            self.assertEqual(lookup.reason, "source_value_identity_mismatch")

    def test_every_miss_is_an_immutable_blueprint_no_op(self) -> None:
        original = {key: dict(row) for key, row in self.policy.items()}
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "absent.json"
            preparation = prepare_pre_bet_restricted_master_successor(
                path,
                "0" * 64,
                self.identity,
                self.sources,
                self.policy,
                acting_best_response_value=(
                    self.evaluation.evaluation.best_response_values[0]
                ),
            )
            self.assertFalse(preparation.cache_hit)
            self.assertEqual(preparation.reason, "cache_unavailable")
            self.assertIsNone(preparation.initial_rows)
            self.assertIsNone(preparation.gain_rows)
            self.assertEqual(preparation.external_policy, original)
            self.assertEqual(preparation.warm_steps, 0)
            self.assertEqual(preparation.master_solves, 0)
            self.assertEqual(preparation.candidate_emissions, 0)
            self.assertEqual(preparation.strategy_quality_rows, 0)
            key = next(iter(preparation.external_policy))
            action = next(iter(preparation.external_policy[key]))
            preparation.external_policy[key][action] = 123.0
            self.assertEqual(self.policy, original)

            path, digest = self._write(directory)
            preparation = prepare_pre_bet_restricted_master_successor(
                path,
                digest,
                self.identity,
                self.sources,
                self.policy,
                acting_best_response_value=math.nan,
            )
            self.assertFalse(preparation.cache_hit)
            self.assertEqual(preparation.reason, "gain_row_assembly_mismatch")
            self.assertIsNone(preparation.initial_rows)
            self.assertIsNone(preparation.gain_rows)
            self.assertEqual(preparation.external_policy, original)

    def test_writer_rejects_partial_and_mutable_inputs(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "invalid.json"
            with self.assertRaisesRegex(ValueError, "complete role schema"):
                write_pre_bet_initial_row_cache(
                    path,
                    self.identity,
                    self.sources[:-1],
                    self.rows[:-1],
                )
            source = self.sources[0]
            mutable_tape = list(source.probabilities)
            assert mutable_tape[0] is not None
            mutable_tape[0] = np.array(mutable_tape[0], copy=True)
            mutable_source = replace(source, probabilities=tuple(mutable_tape))
            with self.assertRaisesRegex(ValueError, "immutable contiguous Float64"):
                write_pre_bet_initial_row_cache(
                    path,
                    self.identity,
                    (mutable_source, *self.sources[1:]),
                    self.rows,
                )

    def test_identity_builder_rejects_incomplete_policy_and_tape_drift(self) -> None:
        incomplete = {key: dict(row) for key, row in self.policy.items()}
        incomplete.pop(next(iter(incomplete)))
        with self.assertRaisesRegex(ValueError, "schema-complete"):
            build_pre_bet_row_cache_identity(
                self.layout,
                self.belief,
                self.hands,
                incomplete,
                self.probabilities,
                acting_player=0,
                public_node=0,
                row_primitive_sha256=cpu_h2_control_row_primitive_digest(),
            )

        drifted = list(self.probabilities)
        assert drifted[0] is not None
        drifted[0] = _immutable(np.flip(drifted[0], axis=1))
        with self.assertRaisesRegex(ValueError, "differs from the full policy"):
            build_pre_bet_row_cache_identity(
                self.layout,
                self.belief,
                self.hands,
                self.policy,
                tuple(drifted),
                acting_player=0,
                public_node=0,
                row_primitive_sha256=cpu_h2_control_row_primitive_digest(),
            )


if __name__ == "__main__":
    unittest.main()
