from __future__ import annotations

import hashlib
import inspect
import json
import struct
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

import numpy as np

import pontius.pre_bet_initial_row_cache_v2 as v2
from pontius.cross_payoff_adjoint_result import bind_cross_payoff_adjoint_result
from pontius.dense_root_cross_payoff_control import dense_root_cross_payoff_control
from pontius.incremental_policy_tt import compile_policy_probability_tape
from pontius.pre_bet_initial_row_cache_v2 import (
    SEAL_SCHEMA,
    build_pre_bet_row_cache_context,
    cpu_h2_control_row_primitive_digest,
    load_pre_bet_cache_seal,
    lookup_pre_bet_initial_row_cache,
    populate_pre_bet_initial_row_cache,
    prepare_pre_bet_restricted_master_successor,
    write_pre_bet_initial_row_cache,
)
from pontius.public_node_open_axis import build_public_node_affine_source_context
from tests import test_pre_bet_initial_row_cache as v1_fixture


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


def _f64le_hex(value: float) -> str:
    return struct.pack("<d", float(value)).hex()


class PreBetInitialRowCacheV2Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        fixture = v1_fixture.PreBetInitialRowCacheTests
        fixture.setUpClass()
        cls.layout = fixture.layout
        cls.hands = fixture.hands
        cls.belief = fixture.belief
        cls.policy = fixture.policy
        cls.probabilities = fixture.probabilities
        cls.evaluation = fixture.evaluation
        cls.affine_contexts = fixture.source_contexts
        cls.context = build_pre_bet_row_cache_context(
            cls.layout,
            cls.belief,
            cls.hands,
            cls.policy,
            cls.probabilities,
            acting_player=0,
            public_node=0,
            row_primitive_sha256=cpu_h2_control_row_primitive_digest(),
        )
        cls.population = populate_pre_bet_initial_row_cache(
            cls.context,
            cls.affine_contexts,
        )

    def _write_unsealed(self, directory: str) -> tuple[Path, object]:
        path = Path(directory) / "h2-initial-rows-v2.json"
        written = write_pre_bet_initial_row_cache(
            path,
            self.context,
            self.population,
        )
        self.assertEqual(
            written.persisted_sha256,
            hashlib.sha256(path.read_bytes()).hexdigest(),
        )
        return path, written

    def _seal(self, directory: str, written: object) -> object:
        seal_path = Path(directory) / "external-seal.json"
        record = {
            "schema": SEAL_SCHEMA,
            "cache_sha256": written.persisted_sha256,
            "cache_bytes": written.persisted_bytes,
            "identity_sha256": self.population.identity_sha256,
        }
        raw = _canonical_json_bytes(record)
        seal_path.write_bytes(raw)
        return load_pre_bet_cache_seal(
            seal_path,
            expected_seal_sha256=hashlib.sha256(raw).hexdigest(),
        )

    def test_round_trip_requires_external_seal_and_reconstructs_exact_gains(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path, written = self._write_unsealed(directory)
            unsealed = lookup_pre_bet_initial_row_cache(
                path,
                written,  # type: ignore[arg-type]
                self.context,
            )
            self.assertFalse(unsealed.hit)
            self.assertEqual(unsealed.reason, "external_seal_required")

            seal = self._seal(directory, written)
            lookup = lookup_pre_bet_initial_row_cache(path, seal, self.context)
            self.assertTrue(lookup.hit)
            self.assertEqual(lookup.reason, "exact_sealed_hit")
            self.assertEqual(
                struct.pack("<d", lookup.acting_best_response_value),
                struct.pack("<d", self.context.acting_best_response_value),
            )
            preparation = prepare_pre_bet_restricted_master_successor(
                path,
                seal,
                self.context,
                self.policy,
            )

        self.assertTrue(preparation.cache_hit)
        self.assertIsNotNone(preparation.gain_rows)
        assert preparation.gain_rows is not None
        np.testing.assert_allclose(
            [row.value(self.probabilities) for row in preparation.gain_rows],
            self.evaluation.evaluation.deviation_gains,
            atol=2e-11,
            rtol=0.0,
        )

    def test_public_apis_accept_neither_identity_fields_rows_nor_actor_scalar(self) -> None:
        self.assertFalse(hasattr(v2, "PreBetRowCacheIdentity"))
        self.assertFalse(hasattr(v2, "build_pre_bet_row_cache_identity"))
        writer = inspect.signature(write_pre_bet_initial_row_cache).parameters
        self.assertEqual(tuple(writer), ("path", "context", "population"))
        prepare = inspect.signature(
            prepare_pre_bet_restricted_master_successor
        ).parameters
        self.assertNotIn("acting_best_response_value", prepare)
        with self.assertRaisesRegex(TypeError, "factory-only"):
            v2.PreBetRowCachePopulation(  # type: ignore[call-arg]
                identity_sha256="0" * 64,
                sources=(),
                rows=(),
                acting_best_response_value=(
                    self.context.acting_best_response_value + 1.0
                ),
            )
        with self.assertRaisesRegex(TypeError, "factory-only"):
            replace(
                self.context,
                identity=replace(
                    self.context.identity,
                    belief_sha256="f" * 64,
                ),
            )

    def test_stale_off_node_source_context_is_rejected_by_population(self) -> None:
        changed = {key: dict(row) for key, row in self.policy.items()}
        off_node = next(
            index
            for index, node in enumerate(self.layout.nodes)
            if index != 0 and node.player == 0
        )
        node = self.layout.nodes[off_node]
        for key in node.information_keys:
            actions = tuple(changed[key])
            changed[key] = {
                action: float(index == 0)
                for index, action in enumerate(actions)
            }
        changed_tape = compile_policy_probability_tape(self.layout, self.hands, changed)
        raw = dense_root_cross_payoff_control(
            self.layout,
            changed_tape,
            acting_player=0,
            payoff_player=0,
        )
        typed = bind_cross_payoff_adjoint_result(
            self.layout,
            changed_tape,
            raw,
            acting_player=0,
            payoff_player=0,
        )
        stale = build_public_node_affine_source_context(
            self.layout,
            changed_tape,
            typed,
            acting_player=0,
            payoff_player=0,
            public_node=0,
        )
        contexts = (stale, *self.affine_contexts[1:])
        with self.assertRaisesRegex(ValueError, "stale provenance"):
            populate_pre_bet_initial_row_cache(self.context, contexts)

    def test_source_intercept_preserving_coefficient_mutation_fails_dense_oracle(self) -> None:
        raw = dense_root_cross_payoff_control(
            self.layout,
            self.probabilities,
            acting_player=0,
            payoff_player=0,
        )
        coefficients = raw.reads[0].action_numerators.copy()
        probabilities = self.probabilities[0]
        assert probabilities is not None
        coefficients[0, 0] += 0.1
        coefficients[0, 1] -= 0.1 * probabilities[0, 0] / probabilities[0, 1]
        mutated_read = replace(raw.reads[0], action_numerators=coefficients)
        mutated = replace(raw, reads=(mutated_read,))
        typed = bind_cross_payoff_adjoint_result(
            self.layout,
            self.probabilities,
            mutated,
            acting_player=0,
            payoff_player=0,
        )
        with self.assertRaisesRegex(ArithmeticError, "dense oracle"):
            build_public_node_affine_source_context(
                self.layout,
                self.probabilities,
                typed,
                acting_player=0,
                payoff_player=0,
                public_node=0,
            )

    def test_matching_recomputed_seal_cannot_authorize_false_actor_value(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path, written = self._write_unsealed(directory)
            payload = json.loads(path.read_text(encoding="utf-8"))
            payload["acting_best_response_value_f64le"] = _f64le_hex(
                self.context.acting_best_response_value + 1.0
            )
            changed = _canonical_json_bytes(payload)
            path.write_bytes(changed)
            forged_write = type(written)(
                output_path=path,
                persisted_sha256=hashlib.sha256(changed).hexdigest(),
                persisted_bytes=len(changed),
            )
            seal = self._seal(directory, forged_write)
            lookup = lookup_pre_bet_initial_row_cache(path, seal, self.context)

        self.assertFalse(lookup.hit)
        self.assertEqual(lookup.reason, "acting_best_response_identity_mismatch")
        self.assertIsNone(lookup.rows)
        self.assertIsNone(lookup.acting_best_response_value)

    def test_declared_oversize_rejects_before_any_file_read(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path, written = self._write_unsealed(directory)
            seal = self._seal(directory, written)
            oversized = object.__new__(v2.SealedPreBetCacheEntry)
            for name, value in (
                ("cache_sha256", seal.cache_sha256),
                ("cache_bytes", 10**12),
                ("identity_sha256", seal.identity_sha256),
                ("seal_sha256", seal.seal_sha256),
                ("seal_path", seal.seal_path),
            ):
                object.__setattr__(oversized, name, value)
            with patch.object(
                v2,
                "read_bounded_file_once",
                side_effect=AssertionError("cache was read"),
            ) as reader:
                lookup = lookup_pre_bet_initial_row_cache(
                    path,
                    oversized,
                    self.context,
                )
            reader.assert_not_called()

        self.assertFalse(lookup.hit)
        self.assertEqual(lookup.reason, "cache_size_safety_cap_exceeded")

    def test_writer_is_no_clobber_and_uses_unique_staging_name(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path, _ = self._write_unsealed(directory)
            with self.assertRaises(FileExistsError):
                write_pre_bet_initial_row_cache(
                    path,
                    self.context,
                    self.population,
                )
            self.assertFalse(path.with_name(f"{path.name}.tmp").exists())

    def test_blueprint_mismatch_is_a_no_op(self) -> None:
        changed = {key: dict(row) for key, row in self.policy.items()}
        key = next(iter(changed))
        actions = tuple(changed[key])
        changed[key] = {
            action: float(index == 0) for index, action in enumerate(actions)
        }
        if changed == self.policy:
            changed[key] = {
                action: float(index == 1) for index, action in enumerate(actions)
            }
        with tempfile.TemporaryDirectory() as directory:
            path, written = self._write_unsealed(directory)
            seal = self._seal(directory, written)
            preparation = prepare_pre_bet_restricted_master_successor(
                path,
                seal,
                self.context,
                changed,
            )
        self.assertFalse(preparation.cache_hit)
        self.assertEqual(preparation.reason, "immutable_blueprint_identity_mismatch")
        self.assertIsNone(preparation.initial_rows)
        self.assertIsNone(preparation.gain_rows)
        self.assertEqual(preparation.external_policy, changed)


if __name__ == "__main__":
    unittest.main()
