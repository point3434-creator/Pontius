from __future__ import annotations

import ast
import json
import tempfile
import unittest
from collections import Counter
from dataclasses import fields, replace
from fractions import Fraction
from hashlib import sha256
from math import comb
from pathlib import Path

import pontius.fresh_action_width_transfer_structures as transfer
from pontius.action_abstraction_confirmation import build_adr0293_confirmation_panel
from pontius.certified_reduced_sizing_consumer_v2 import (
    KernelRaiseToTotal,
    canonical_lf_source_sha256,
)
from pontius.fresh_action_width_nonreplay import build_adr0331_nonreplay_pool
from pontius.fresh_action_width_nonreplay_seal import ADR0331_POPULATION_POOL_SHA256
from pontius.fresh_action_width_structures import (
    ADR0323_GENERATOR_VERSION,
    ADR0323_POTS,
    ADR0323_PRIVATE_RANGE_WIDTH,
    ADR0323_RAISE_WIDTHS,
    ADR0323_STACKS,
    ADR0323_STRUCTURAL_FILTER_VERSION,
    FreshActionWidthContext,
    PrivateRangeWidth,
    RaiseActionWidth,
    _DigestStream,
    _kernel_raise_universe,
    _private_pairs,
    _river_opening_state,
    _showdown_signs,
    _shuffled_deck,
    _structurally_admissible,
    build_adr0323_development_pool,
    transfer_seed_from_mechanism_commit,
)
from pontius.fresh_action_width_structures_seal import (
    ADR0323_DEVELOPMENT_POOL_SHA256,
)
from pontius.fresh_action_width_transfer_structures import (
    ADR0339_ADR0311_AUDIT_CONTEXT_COUNT,
    ADR0339_ADR0311_AUDIT_INVENTORY_SHA256,
    ADR0339_MAINTAINED_PRIOR_CONTEXT_COUNT,
    ADR0339_MAINTAINED_PRIOR_INVENTORY_SHA256,
    ADR0339_MECHANISM_SOURCE_COMMIT,
    ADR0339_TRANSFER_CONTEXT_COUNT,
    ADR0339_TRANSFER_PROTOCOL,
    ADR0339_TRANSFER_PROTOCOL_SHA256,
    ADR0339_TRANSFER_SEED,
    ADR0339_TRANSFER_SEED_SHA256,
    SemanticInventoryBetIncrement,
    action_width_context_semantic_inventory_key,
    action_width_context_semantic_inventory_sha256,
    build_adr0339_transfer_pool,
    semantic_inventory_bet_increment,
)
from pontius.fresh_action_width_transfer_structures_seal import (
    ADR0339_COMBINED_EXCLUSION_CONTEXT_COUNT,
    ADR0339_DEVELOPMENT_CONTEXT_INVENTORY_SHA256,
    ADR0339_FINITE_NONOVERLAP_EVIDENCE_SHA256,
    ADR0339_NONREPLAY_CONTEXT_INVENTORY_SHA256,
    ADR0339_TRANSFER_CANDIDATE_ATTEMPTS,
    ADR0339_TRANSFER_CONTEXT_INVENTORY_SHA256,
    ADR0339_TRANSFER_CONTEXT_SEMANTIC_LIST_SHA256,
    ADR0339_TRANSFER_ORDERED_INVENTORY_HASH_LIST_SHA256,
    ADR0339_TRANSFER_POOL_SHA256,
    ADR0339_TRANSFER_POT_COUNTS,
    ADR0339_TRANSFER_PROTOCOL_SHA256 as SEALED_PROTOCOL_SHA256,
    ADR0339_TRANSFER_SOURCE_MANIFEST,
    ADR0339_TRANSFER_STACK_COUNTS,
    ADR0339_TRANSFER_SUBSET_COUNTS_BY_RAISE_WIDTH,
    ADR0339_TRANSFER_TOTAL_SUBSET_COUNT,
    ADR0339_TRANSFER_UNIVERSE_WIDTH_COUNTS,
)
from pontius.fresh_capacity_filling_structures import (
    CapacityFillingStructureKind,
    build_adr0305_v4_structure,
)
from pontius.fresh_collision_repair_structures import (
    FreshStructureKind,
    build_adr0301_fresh_structure,
)
from pontius.native_simplex_audit_structures import (
    build_adr0311_width_four_structure,
)
from pontius.sizing_power_diagnostic import build_adr0295_sizing_power_pool
from pontius.width_four_sizing_power import build_adr0297_width_four_pool
from tests.test_reduced_river_sizing_oracle import _contexts


def _fraction_pair(value: object) -> tuple[int, int]:
    if isinstance(value, Fraction):
        fraction = value
    elif hasattr(value, "fraction"):
        fraction = value.fraction  # type: ignore[attr-defined]
    else:
        fraction = Fraction(value.numerator, value.denominator)  # type: ignore[attr-defined]
    return fraction.numerator, fraction.denominator


def _historical_semantic_key(context: object) -> str:
    payload = {
        "board": context.board,  # type: ignore[attr-defined]
        "joint_probabilities": tuple(
            tuple(_fraction_pair(value) for value in row)
            for row in context.joint_probabilities  # type: ignore[attr-defined]
        ),
        "minimum_bet": context.minimum_bet,  # type: ignore[attr-defined]
        "opener_hands": context.opener_hands,  # type: ignore[attr-defined]
        "pot": context.pot,  # type: ignore[attr-defined]
        "responder_hands": context.responder_hands,  # type: ignore[attr-defined]
        "stack": context.stack,  # type: ignore[attr-defined]
    }
    return json.dumps(
        payload,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    )


def _historical_inventory_sha256(contexts: tuple[object, ...]) -> str:
    return sha256(
        json.dumps(
            sorted(_historical_semantic_key(context) for context in contexts),
            allow_nan=False,
            separators=(",", ":"),
        ).encode("ascii")
    ).hexdigest()


def _independent_first_admissible_contexts() -> tuple[int, tuple[FreshActionWidthContext, ...]]:
    stream = _DigestStream(ADR0339_TRANSFER_SEED)
    contexts: list[FreshActionWidthContext] = []
    attempts = 0
    while len(contexts) < ADR0339_TRANSFER_CONTEXT_COUNT:
        attempts += 1
        deck = _shuffled_deck(stream)
        board = deck[:5]
        opener_hands = _private_pairs(deck[5:13])
        responder_hands = _private_pairs(deck[13:21])
        signs = _showdown_signs(board, opener_hands, responder_hands)
        if not _structurally_admissible(signs):
            continue
        pot = ADR0323_POTS[stream.randbelow(len(ADR0323_POTS))]
        effective_stack = ADR0323_STACKS[stream.randbelow(len(ADR0323_STACKS))]
        weights = tuple(1 + stream.randbelow(9) for _ in range(16))
        denominator = sum(weights)
        probabilities = tuple(
            tuple(
                Fraction(weights[row * 4 + column], denominator)
                for column in range(4)
            )
            for row in range(4)
        )
        state = _river_opening_state(pot=pot, effective_stack=effective_stack)
        contexts.append(
            FreshActionWidthContext(
                context_id=f"adr0339-transfer-{len(contexts):03d}",
                betting=state,
                board=board,
                opener_hands=opener_hands,
                responder_hands=responder_hands,
                joint_probabilities=probabilities,
                showdown_signs=signs,
                complete_raise_to_totals=_kernel_raise_universe(state),
            )
        )
    return attempts, tuple(contexts)


class FreshActionWidthTransferStructureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.development = build_adr0323_development_pool()
        cls.nonreplay = build_adr0331_nonreplay_pool()
        cls.pool = build_adr0339_transfer_pool()

    def test_source_manifest_protocol_seed_and_import_boundary_are_exact(self) -> None:
        root = Path(transfer.__file__).resolve().parent
        actual = {
            name: canonical_lf_source_sha256(root / name)
            for name in ADR0339_TRANSFER_SOURCE_MANIFEST
        }
        self.assertEqual(dict(ADR0339_TRANSFER_SOURCE_MANIFEST), actual)
        self.assertEqual(SEALED_PROTOCOL_SHA256, ADR0339_TRANSFER_PROTOCOL_SHA256)
        self.assertEqual(
            ADR0339_TRANSFER_PROTOCOL_SHA256,
            sha256(
                json.dumps(
                    dict(ADR0339_TRANSFER_PROTOCOL),
                    allow_nan=False,
                    separators=(",", ":"),
                    sort_keys=True,
                ).encode("ascii")
            ).hexdigest(),
        )
        self.assertEqual(
            "pontius|adr-0323|certified-finite-block-width|transfer|"
            "mechanism-commit=b4339f33dec768052208b102ad8a9f510666f40d",
            ADR0339_TRANSFER_SEED,
        )
        self.assertEqual(
            transfer_seed_from_mechanism_commit(ADR0339_MECHANISM_SOURCE_COMMIT),
            ADR0339_TRANSFER_SEED,
        )
        self.assertEqual(
            ADR0339_TRANSFER_SEED_SHA256,
            sha256(ADR0339_TRANSFER_SEED.encode("ascii")).hexdigest(),
        )
        with self.assertRaises(TypeError):
            ADR0339_TRANSFER_PROTOCOL["transfer_context_count"] = 1  # type: ignore[index]
        with self.assertRaises(TypeError):
            ADR0339_TRANSFER_SOURCE_MANIFEST["river.py"] = "0" * 64  # type: ignore[index]

        source_path = Path(transfer.__file__)
        tree = ast.parse(source_path.read_text(encoding="utf-8"))
        imported: set[str] = set()
        names: set[str] = set()
        attributes: set[str] = set()
        function_names: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module is not None:
                imported.add(node.module)
                names.update(alias.name for alias in node.names)
            elif isinstance(node, ast.Name):
                names.add(node.id)
            elif isinstance(node, ast.Attribute):
                attributes.add(node.attr)
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                function_names.add(node.name)
        forbidden_fragments = (
            "qualification",
            "teacher",
            "greedy",
            "result",
            "highs",
            "linear_program",
            "preparation_bank",
            "legal_decision_spine",
            "blueprint",
            "resolver",
        )
        self.assertFalse(
            any(
                fragment in module
                for module in imported
                for fragment in forbidden_fragments
            )
        )
        self.assertNotIn("BettingAction", names)
        self.assertNotIn("consume_certified_reduced_sizing_v2", names)
        self.assertNotIn("apply_action", attributes)
        self.assertNotIn("write_bytes", attributes)
        self.assertFalse(any("solve" in name for name in function_names))

        with tempfile.TemporaryDirectory() as directory:
            copy = Path(directory) / "transfer.py"
            normalized = source_path.read_bytes().replace(b"\r\n", b"\n")
            copy.write_bytes(normalized.replace(b"\n", b"\r\n"))
            self.assertEqual(
                canonical_lf_source_sha256(copy),
                actual["fresh_action_width_transfer_structures.py"],
            )

    def test_pool_is_exact_unique_ordered_and_first_admissible(self) -> None:
        pool = self.pool
        self.assertEqual(ADR0339_TRANSFER_CANDIDATE_ATTEMPTS, pool.candidate_attempts)
        self.assertEqual(ADR0339_TRANSFER_POOL_SHA256, pool.digest)
        self.assertEqual(
            tuple(f"adr0339-transfer-{index:03d}" for index in range(96)),
            tuple(context.context_id for context in pool.contexts),
        )
        self.assertEqual(96, len({context.semantic_digest for context in pool.contexts}))
        self.assertEqual(96, len({context.showdown_signs for context in pool.contexts}))
        self.assertEqual(pool.canonical_bytes, build_adr0339_transfer_pool().canonical_bytes)

        attempts, independent = _independent_first_admissible_contexts()
        self.assertEqual(ADR0339_TRANSFER_CANDIDATE_ATTEMPTS, attempts)
        self.assertEqual(
            tuple(context.semantic_digest for context in independent),
            tuple(context.semantic_digest for context in pool.contexts),
        )
        self.assertEqual(
            tuple(action_width_context_semantic_inventory_key(context) for context in independent),
            tuple(action_width_context_semantic_inventory_key(context) for context in pool.contexts),
        )

    def test_population_preserves_distribution_legality_and_work(self) -> None:
        pool = self.pool
        self.assertEqual(
            ADR0339_TRANSFER_POT_COUNTS,
            tuple(sorted(Counter(context.betting.pot for context in pool.contexts).items())),
        )
        self.assertEqual(
            ADR0339_TRANSFER_STACK_COUNTS,
            tuple(
                sorted(Counter(context.betting.stacks[0] for context in pool.contexts).items())
            ),
        )
        self.assertEqual(
            ADR0339_TRANSFER_UNIVERSE_WIDTH_COUNTS,
            tuple(
                sorted(
                    Counter(
                        len(context.complete_raise_to_totals)
                        for context in pool.contexts
                    ).items()
                )
            ),
        )
        for context in pool.contexts:
            decision = context.betting.legal_decision()
            bounds = decision.raise_bounds
            self.assertIsNotNone(bounds)
            assert bounds is not None
            self.assertEqual(
                tuple(range(bounds.minimum_raise_to, bounds.maximum_raise_to + 1)),
                tuple(value.chips for value in context.complete_raise_to_totals),
            )
            self.assertEqual(context.payoff_span_chips, context.betting.pot + 2 * context.betting.stacks[0])

        ledger = pool.subset_work_ledger
        self.assertEqual(
            ADR0339_TRANSFER_SUBSET_COUNTS_BY_RAISE_WIDTH,
            tuple((width.count, count) for width, count in ledger.subset_counts_by_raise_width),
        )
        self.assertEqual(ADR0339_TRANSFER_TOTAL_SUBSET_COUNT, ledger.total_subset_count)
        self.assertEqual(
            ADR0339_TRANSFER_SUBSET_COUNTS_BY_RAISE_WIDTH,
            tuple(
                (
                    width.count,
                    sum(
                        comb(
                            len(context.complete_raise_to_totals) - 2,
                            width.count - 2,
                        )
                        for context in pool.contexts
                    ),
                )
                for width in ADR0323_RAISE_WIDTHS
            ),
        )

    def test_ordered_context_and_inventory_identities_are_exact(self) -> None:
        semantic_digests = tuple(context.semantic_digest for context in self.pool.contexts)
        self.assertEqual(
            ADR0339_TRANSFER_CONTEXT_SEMANTIC_LIST_SHA256,
            sha256(
                json.dumps(
                    semantic_digests,
                    allow_nan=False,
                    separators=(",", ":"),
                ).encode("ascii")
            ).hexdigest(),
        )
        self.assertEqual(
            ADR0339_TRANSFER_CONTEXT_INVENTORY_SHA256,
            action_width_context_semantic_inventory_sha256(self.pool.contexts),
        )
        ordered_inventory_hashes = tuple(
            sha256(
                action_width_context_semantic_inventory_key(context).encode("ascii")
            ).hexdigest()
            for context in self.pool.contexts
        )
        self.assertEqual(
            ADR0339_TRANSFER_ORDERED_INVENTORY_HASH_LIST_SHA256,
            sha256(
                json.dumps(
                    ordered_inventory_hashes,
                    allow_nan=False,
                    separators=(",", ":"),
                ).encode("ascii")
            ).hexdigest(),
        )

    def test_complete_finite_inventories_have_no_transfer_counterpart(self) -> None:
        prior = (
            *_contexts(),
            *build_adr0293_confirmation_panel().contexts,
            *(
                context
                for batch_index in range(3)
                for context in build_adr0295_sizing_power_pool(
                    batch_index=batch_index
                ).contexts
            ),
            *(
                context
                for batch_index in range(3)
                for context in build_adr0297_width_four_pool(
                    batch_index=batch_index
                ).contexts
            ),
            *build_adr0301_fresh_structure(
                kind=FreshStructureKind.REPRESENTATIVE
            ).contexts,
            *build_adr0301_fresh_structure(
                kind=FreshStructureKind.QUALIFIED_POOL
            ).contexts,
            *build_adr0305_v4_structure(
                kind=CapacityFillingStructureKind.REPRESENTATIVE
            ).contexts,
            *build_adr0305_v4_structure(
                kind=CapacityFillingStructureKind.QUALIFIED_A
            ).contexts,
            *build_adr0305_v4_structure(
                kind=CapacityFillingStructureKind.QUALIFIED_B
            ).contexts,
        )
        audit = build_adr0311_width_four_structure().contexts
        transfer_keys = {
            action_width_context_semantic_inventory_key(context)
            for context in self.pool.contexts
        }
        development_keys = {
            action_width_context_semantic_inventory_key(context)
            for context in self.development.contexts
        }
        nonreplay_keys = {
            action_width_context_semantic_inventory_key(context)
            for context in self.nonreplay.contexts
        }
        prior_keys = {_historical_semantic_key(context) for context in prior}
        audit_keys = {_historical_semantic_key(context) for context in audit}

        self.assertEqual(ADR0339_MAINTAINED_PRIOR_CONTEXT_COUNT, len(prior))
        self.assertEqual(ADR0339_MAINTAINED_PRIOR_CONTEXT_COUNT, len(prior_keys))
        self.assertEqual(
            ADR0339_MAINTAINED_PRIOR_INVENTORY_SHA256,
            _historical_inventory_sha256(prior),
        )
        self.assertEqual(ADR0339_ADR0311_AUDIT_CONTEXT_COUNT, len(audit))
        self.assertEqual(ADR0339_ADR0311_AUDIT_CONTEXT_COUNT, len(audit_keys))
        self.assertEqual(
            ADR0339_ADR0311_AUDIT_INVENTORY_SHA256,
            _historical_inventory_sha256(audit),
        )
        self.assertEqual(
            ADR0339_DEVELOPMENT_CONTEXT_INVENTORY_SHA256,
            action_width_context_semantic_inventory_sha256(self.development.contexts),
        )
        self.assertEqual(
            ADR0339_NONREPLAY_CONTEXT_INVENTORY_SHA256,
            action_width_context_semantic_inventory_sha256(self.nonreplay.contexts),
        )
        combined_exclusions = prior_keys | audit_keys | development_keys | nonreplay_keys
        self.assertEqual(
            ADR0339_COMBINED_EXCLUSION_CONTEXT_COUNT,
            len(combined_exclusions),
        )
        self.assertEqual(
            len(prior_keys) + len(audit_keys) + len(development_keys) + len(nonreplay_keys),
            len(combined_exclusions),
        )
        self.assertTrue(transfer_keys.isdisjoint(combined_exclusions))

        evidence = {
            "adr0311_audit_context_count": len(audit),
            "adr0311_audit_inventory_sha256": _historical_inventory_sha256(audit),
            "adr0311_audit_transfer_intersection": len(audit_keys & transfer_keys),
            "development_context_count": len(self.development.contexts),
            "development_inventory_sha256": (
                action_width_context_semantic_inventory_sha256(
                    self.development.contexts
                )
            ),
            "development_pool_sha256": self.development.digest,
            "development_transfer_intersection": len(development_keys & transfer_keys),
            "maintained_prior_context_count": len(prior),
            "maintained_prior_inventory_sha256": _historical_inventory_sha256(prior),
            "maintained_prior_transfer_intersection": len(prior_keys & transfer_keys),
            "nonreplay_context_count": len(self.nonreplay.contexts),
            "nonreplay_inventory_sha256": (
                action_width_context_semantic_inventory_sha256(
                    self.nonreplay.contexts
                )
            ),
            "nonreplay_pool_sha256": self.nonreplay.digest,
            "nonreplay_transfer_intersection": len(nonreplay_keys & transfer_keys),
            "transfer_context_count": len(self.pool.contexts),
            "transfer_inventory_sha256": (
                action_width_context_semantic_inventory_sha256(self.pool.contexts)
            ),
            "transfer_pool_sha256": self.pool.digest,
            "transfer_unique": len(transfer_keys),
            "version": "adr0339-finite-semantic-nonoverlap-v1",
        }
        self.assertEqual(
            ADR0339_FINITE_NONOVERLAP_EVIDENCE_SHA256,
            sha256(
                json.dumps(
                    evidence,
                    allow_nan=False,
                    separators=(",", ":"),
                    sort_keys=True,
                ).encode("ascii")
            ).hexdigest(),
        )

    def test_pool_rejects_exclusion_commit_seed_and_order_corruption(self) -> None:
        pool = self.pool
        with self.assertRaises(ValueError):
            replace(pool, mechanism_source_commit="0" * 40)
        with self.assertRaises(ValueError):
            replace(pool, seed=pool.seed + "x")
        with self.assertRaises(ValueError):
            replace(pool, development_pool_sha256="f" * 64)
        with self.assertRaises(ValueError):
            replace(pool, nonreplay_pool_sha256="f" * 64)
        with self.assertRaises((TypeError, ValueError)):
            replace(
                pool,
                development_context_semantic_digests=(
                    pool.development_context_semantic_digests[:-1]
                ),
            )
        with self.assertRaises((TypeError, ValueError)):
            replace(
                pool,
                nonreplay_context_semantic_digests=(
                    *pool.nonreplay_context_semantic_digests[:-1],
                    "f" * 64,
                ),
            )
        with self.assertRaises(ValueError):
            replace(pool, contexts=tuple(reversed(pool.contexts)))
        with self.assertRaises(ValueError):
            replace(pool, candidate_attempts=True)

    def test_development_counterparts_and_illegal_contexts_fail_closed(self) -> None:
        development_counterpart = replace(
            self.development.contexts[0],
            context_id=self.pool.contexts[0].context_id,
        )
        with self.assertRaises(ValueError):
            replace(
                self.pool,
                contexts=(development_counterpart, *self.pool.contexts[1:]),
            )
        nonreplay_counterpart = replace(
            self.nonreplay.contexts[0],
            context_id=self.pool.contexts[0].context_id,
        )
        with self.assertRaises(ValueError):
            replace(
                self.pool,
                contexts=(nonreplay_counterpart, *self.pool.contexts[1:]),
            )
        first = self.pool.contexts[0]
        with self.assertRaises(ValueError):
            replace(
                first,
                complete_raise_to_totals=first.complete_raise_to_totals[:-1],
            )
        with self.assertRaises(TypeError):
            action_width_context_semantic_inventory_key(object())  # type: ignore[arg-type]
        with self.assertRaises(TypeError):
            action_width_context_semantic_inventory_sha256([first])  # type: ignore[arg-type]

    def test_value_free_schema_and_semantic_widths_cannot_cross(self) -> None:
        self.assertEqual(PrivateRangeWidth(4), ADR0323_PRIVATE_RANGE_WIDTH)
        self.assertNotEqual(PrivateRangeWidth(4), RaiseActionWidth(4))
        self.assertEqual((2, 3, 4, 5, 6), tuple(width.count for width in ADR0323_RAISE_WIDTHS))
        field_names = {field.name for field in fields(type(self.pool))}
        forbidden = {
            "candidate_value",
            "elapsed_seconds",
            "policy",
            "regret",
            "selected_raise_width",
            "teacher",
            "transfer_result",
        }
        self.assertTrue(field_names.isdisjoint(forbidden))
        canonical = json.loads(self.pool.canonical_bytes)
        self.assertTrue(set(canonical).isdisjoint(forbidden))
        self.assertEqual(ADR0323_GENERATOR_VERSION, self.pool.generator_version)
        self.assertEqual(
            ADR0323_STRUCTURAL_FILTER_VERSION,
            self.pool.structural_filter_version,
        )
        self.assertEqual(ADR0323_DEVELOPMENT_POOL_SHA256, self.pool.development_pool_sha256)
        self.assertEqual(ADR0331_POPULATION_POOL_SHA256, self.pool.nonreplay_pool_sha256)

        converted = semantic_inventory_bet_increment(
            raise_to_total_chips=7,
            street_contribution_chips=2,
            call_amount_chips=1,
        )
        self.assertEqual(SemanticInventoryBetIncrement(4), converted)
        self.assertNotEqual(KernelRaiseToTotal(4), converted)
        self.assertEqual(
            2,
            json.loads(
                action_width_context_semantic_inventory_key(self.pool.contexts[0])
            )["minimum_bet"],
        )
        for invalid in (
            {
                "raise_to_total_chips": 2,
                "street_contribution_chips": 1,
                "call_amount_chips": 1,
            },
            {
                "raise_to_total_chips": 1,
                "street_contribution_chips": 2,
                "call_amount_chips": 0,
            },
            {
                "raise_to_total_chips": True,
                "street_contribution_chips": 0,
                "call_amount_chips": 0,
            },
        ):
            with self.subTest(invalid=invalid):
                with self.assertRaises((TypeError, ValueError)):
                    semantic_inventory_bet_increment(**invalid)  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main()
