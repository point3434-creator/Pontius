from __future__ import annotations

import ast
import tempfile
import unittest
from collections import Counter
from dataclasses import replace
from fractions import Fraction
from hashlib import sha256
from math import comb
from pathlib import Path

import pontius.fresh_action_width_structures as structures
from pontius.certified_reduced_sizing_consumer_v2 import (
    KernelRaiseToTotal,
    canonical_lf_source_sha256,
)
from pontius.fresh_action_width_structures import (
    ADR0323_BASELINE_COMMIT,
    ADR0323_DEVELOPMENT_CONTEXT_COUNT,
    ADR0323_DEVELOPMENT_SEED,
    ADR0323_PRIVATE_RANGE_WIDTH,
    ADR0323_RAISE_WIDTHS,
    ADR0323_STRUCTURE_PROTOCOL,
    ADR0323_STRUCTURE_PROTOCOL_SHA256,
    ActionWidthSubsetWorkLedger,
    AnchoredRaiseSubsetFamily,
    PrivateRangeWidth,
    RaiseActionWidth,
    anchored_raise_subset_family,
    build_adr0323_development_pool,
    transfer_seed_from_mechanism_commit,
)
from pontius.fresh_action_width_structures_seal import (
    ADR0323_DEVELOPMENT_CANDIDATE_ATTEMPTS,
    ADR0323_DEVELOPMENT_POOL_SHA256,
    ADR0323_STRUCTURE_PROTOCOL_SHA256 as SEALED_PROTOCOL_SHA256,
    ADR0323_STRUCTURE_SOURCE_MANIFEST,
    ADR0323_SUBSET_COUNTS_BY_RAISE_WIDTH,
    ADR0323_TOTAL_SUBSET_COUNT,
)


class FreshActionWidthSourceBoundaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.pool = build_adr0323_development_pool()

    def test_source_manifest_protocol_and_import_boundary_are_exact(self) -> None:
        root = Path(structures.__file__).resolve().parent
        actual = {
            name: canonical_lf_source_sha256(root / name)
            for name in ADR0323_STRUCTURE_SOURCE_MANIFEST
        }
        self.assertEqual(dict(ADR0323_STRUCTURE_SOURCE_MANIFEST), actual)
        self.assertEqual(SEALED_PROTOCOL_SHA256, ADR0323_STRUCTURE_PROTOCOL_SHA256)
        with self.assertRaises(TypeError):
            ADR0323_STRUCTURE_SOURCE_MANIFEST["river.py"] = "0" * 64  # type: ignore[index]
        with self.assertRaises(TypeError):
            ADR0323_STRUCTURE_PROTOCOL["pots"] = ()  # type: ignore[index]

        source_path = Path(structures.__file__)
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

        forbidden_modules = {
            "action_abstraction_confirmation",
            "capacity_filling_action_abstraction",
            "certified_reduced_sizing_highs",
            "collision_repair_action_abstraction",
            "fresh_capacity_filling_qualification",
            "fresh_capacity_filling_structures",
            "fresh_collision_repair_qualification",
            "fresh_collision_repair_structures",
            "legal_action_abstraction",
            "linear_program",
            "preparation_bank",
            "reduced_river_sizing_oracle",
            "sizing_power_diagnostic",
            "width_four_sizing_power",
            "width_four_sizing_power_evaluation",
        }
        self.assertTrue(imported.isdisjoint(forbidden_modules))
        self.assertNotIn("BettingAction", names)
        self.assertNotIn("raise_to", names)
        self.assertNotIn("apply_action", attributes)
        self.assertFalse(any("transfer" in name and "build" in name for name in function_names))

        with tempfile.TemporaryDirectory() as directory:
            copy = Path(directory) / "structures.py"
            normalized = source_path.read_bytes().replace(b"\r\n", b"\n")
            copy.write_bytes(normalized.replace(b"\n", b"\r\n"))
            self.assertEqual(
                canonical_lf_source_sha256(copy),
                actual["fresh_action_width_structures.py"],
            )

    def test_development_pool_identity_and_diversity_are_frozen(self) -> None:
        pool = self.pool
        self.assertEqual(ADR0323_DEVELOPMENT_SEED, pool.seed)
        self.assertEqual(ADR0323_DEVELOPMENT_CONTEXT_COUNT, len(pool.contexts))
        self.assertEqual(ADR0323_DEVELOPMENT_CANDIDATE_ATTEMPTS, pool.candidate_attempts)
        self.assertEqual(ADR0323_DEVELOPMENT_POOL_SHA256, pool.digest)
        self.assertEqual(
            Counter({6: 19, 10: 25, 14: 24, 20: 28}),
            Counter(context.betting.pot for context in pool.contexts),
        )
        self.assertEqual(
            Counter({8: 29, 10: 35, 12: 32}),
            Counter(context.betting.stacks[0] for context in pool.contexts),
        )
        self.assertEqual(96, len({context.showdown_signs for context in pool.contexts}))
        self.assertEqual(
            len(pool.contexts),
            len({context.semantic_digest for context in pool.contexts}),
        )
        self.assertEqual(pool.canonical_bytes, build_adr0323_development_pool().canonical_bytes)

    def test_kernel_universes_are_complete_and_semantically_bound(self) -> None:
        for context in self.pool.contexts:
            with self.subTest(context=context.context_id):
                state = context.betting
                decision = state.legal_decision()
                bounds = decision.raise_bounds
                self.assertIsNotNone(bounds)
                assert bounds is not None
                amounts = tuple(value.chips for value in context.complete_raise_to_totals)
                self.assertEqual(
                    tuple(range(bounds.minimum_raise_to, bounds.maximum_raise_to + 1)),
                    amounts,
                )
                self.assertEqual(bounds.maximum_raise_to, bounds.maximum_contestable_raise_to)
                self.assertEqual(state.pot + 2 * state.stacks[0], context.payoff_span_chips)
                self.assertIn(len(amounts), (7, 9, 11))
                self.assertEqual(Fraction(1), sum(
                    (value for row in context.joint_probabilities for value in row),
                    start=Fraction(0),
                ))

    def test_raise_width_is_not_private_width_or_total_action_width(self) -> None:
        self.assertEqual(PrivateRangeWidth(4), ADR0323_PRIVATE_RANGE_WIDTH)
        self.assertNotEqual(PrivateRangeWidth(4), RaiseActionWidth(4))
        self.assertEqual((2, 3, 4, 5, 6), tuple(width.count for width in ADR0323_RAISE_WIDTHS))
        with self.assertRaises(ValueError):
            RaiseActionWidth(1)
        with self.assertRaises(TypeError):
            RaiseActionWidth(True)
        with self.assertRaises(TypeError):
            PrivateRangeWidth(False)

    def test_anchored_subset_schedules_are_exhaustive_and_lexicographic(self) -> None:
        for context in self.pool.contexts:
            universe = context.complete_raise_to_totals
            for width in ADR0323_RAISE_WIDTHS:
                with self.subTest(context=context.context_id, width=width.count):
                    family = anchored_raise_subset_family(universe, width)
                    self.assertEqual(comb(len(universe) - 2, width.count - 2), len(family.subsets))
                    rendered = tuple(
                        tuple(value.chips for value in subset)
                        for subset in family.subsets
                    )
                    self.assertEqual(tuple(sorted(rendered)), rendered)
                    for subset in family.subsets:
                        self.assertEqual(width.count, len(subset))
                        self.assertEqual(universe[0], subset[0])
                        self.assertEqual(universe[-1], subset[-1])
                        self.assertTrue(set(subset).issubset(universe))

        first = self.pool.contexts[0]
        width_two = anchored_raise_subset_family(
            first.complete_raise_to_totals,
            RaiseActionWidth(2),
        )
        self.assertEqual(
            ((first.complete_raise_to_totals[0], first.complete_raise_to_totals[-1]),),
            width_two.subsets,
        )

    def test_subset_work_is_exact_and_frozen_before_values(self) -> None:
        ledger = self.pool.subset_work_ledger
        self.assertEqual(
            ADR0323_SUBSET_COUNTS_BY_RAISE_WIDTH,
            tuple((width.count, count) for width, count in ledger.subset_counts_by_raise_width),
        )
        self.assertEqual(ADR0323_TOTAL_SUBSET_COUNT, ledger.total_subset_count)
        recomputed = tuple(
            (
                width.count,
                sum(
                    comb(len(context.complete_raise_to_totals) - 2, width.count - 2)
                    for context in self.pool.contexts
                ),
            )
            for width in ADR0323_RAISE_WIDTHS
        )
        self.assertEqual(ADR0323_SUBSET_COUNTS_BY_RAISE_WIDTH, recomputed)

    def test_transfer_seed_is_reserved_but_no_transfer_pool_exists(self) -> None:
        commit = "0123456789abcdef0123456789abcdef01234567"
        self.assertEqual(
            "pontius|adr-0323|certified-finite-block-width|transfer|"
            f"mechanism-commit={commit}",
            transfer_seed_from_mechanism_commit(commit),
        )
        for invalid in ("", "A" * 40, "g" * 40, "0" * 39, "0" * 41):
            with self.subTest(invalid=invalid):
                with self.assertRaises(ValueError):
                    transfer_seed_from_mechanism_commit(invalid)
        self.assertFalse(hasattr(structures, "build_adr0323_transfer_pool"))

    def test_corrupted_semantic_records_fail_closed(self) -> None:
        context = self.pool.contexts[0]
        universe = context.complete_raise_to_totals
        with self.assertRaises(ValueError):
            replace(context, complete_raise_to_totals=universe[:-1])
        with self.assertRaises(ValueError):
            replace(
                context,
                showdown_signs=(
                    (0, *context.showdown_signs[0][1:]),
                    *context.showdown_signs[1:],
                ),
            )
        with self.assertRaises(ValueError):
            replace(context, joint_probabilities=(
                (Fraction(1, 16),) * 4,
                (Fraction(1, 16),) * 4,
                (Fraction(1, 16),) * 4,
                (Fraction(1, 32),) * 4,
            ))
        with self.assertRaises(TypeError):
            anchored_raise_subset_family((), RaiseActionWidth(2))
        family = anchored_raise_subset_family(universe, RaiseActionWidth(3))
        with self.assertRaises(ValueError):
            replace(family, subsets=tuple(reversed(family.subsets)))
        ledger = self.pool.subset_work_ledger
        with self.assertRaises(ValueError):
            replace(ledger, total_subset_count=ledger.total_subset_count + 1)
        with self.assertRaises(TypeError):
            ActionWidthSubsetWorkLedger(
                context_count=1,
                subset_counts_by_raise_width=((PrivateRangeWidth(2), 1),),  # type: ignore[arg-type]
                total_subset_count=1,
            )

    def test_protocol_digest_is_independently_reproducible(self) -> None:
        encoded = __import__("json").dumps(
            dict(ADR0323_STRUCTURE_PROTOCOL),
            allow_nan=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("ascii")
        self.assertEqual(ADR0323_STRUCTURE_PROTOCOL_SHA256, sha256(encoded).hexdigest())
        self.assertEqual(
            "a8f2ce3c0af9282625f13e6f0d8e93ebd57c0fa6",
            ADR0323_BASELINE_COMMIT,
        )


if __name__ == "__main__":
    unittest.main()
