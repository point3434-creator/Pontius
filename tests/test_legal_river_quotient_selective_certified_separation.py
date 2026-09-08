from __future__ import annotations

import ast
from copy import deepcopy
from dataclasses import replace
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from pontius import legal_river_quotient_selective_certified_separation as source
from pontius import legal_river_quotient_selective_certified_separation_result as reader


ROOT = Path(__file__).parents[1]
RESULT = ROOT / source.RESULT_RELATIVE_PATH
SOURCE = Path(source.__file__)
READER = Path(reader.__file__)


def _direct_price(instance: source.PriceInstance, source_mask: int) -> int:
    bases = dict(instance.source_bases)
    scalars = dict(instance.subset_scalars)
    return bases[source_mask] + sum(
        source.LEVEL_COEFFICIENTS[subset.bit_count()] * scalars[subset]
        for subset in source.source_subsets(source_mask)
    )


def _has_nonstrict_zero_prune(text: str) -> bool:
    tree = ast.parse(text)
    search_function = next(
        node
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == "search"
    )
    return any(
        isinstance(node, ast.Compare)
        and isinstance(node.left, ast.Attribute)
        and isinstance(node.left.value, ast.Name)
        and node.left.value.id == "node"
        and node.left.attr == "upper"
        and len(node.ops) == 1
        and isinstance(node.ops[0], ast.LtE)
        and len(node.comparators) == 1
        and isinstance(node.comparators[0], ast.Constant)
        and node.comparators[0].value == 0
        for node in ast.walk(search_function)
    )


class SelectiveCertifiedSeparationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.cases: dict[
            tuple[int, str],
            tuple[
                source.PriceInstance,
                source.CompiledSeparation,
                source.ExhaustiveReceipt,
                dict[int, int],
            ],
        ] = {}
        for cards in source.DOMAINS:
            for family in source.FAMILIES:
                instance = source.make_instance(cards, family)
                bases = dict(instance.source_bases)
                scalars = dict(instance.subset_scalars)
                prices = {
                    mask: bases[mask]
                    + sum(
                        source.LEVEL_COEFFICIENTS[subset.bit_count()] * scalars[subset]
                        for subset in source.source_subsets(mask)
                    )
                    for mask in bases
                }
                cls.cases[(cards, family)] = (
                    instance,
                    source.compile_separation(instance),
                    source.exhaustive_authority(instance),
                    prices,
                )

    def test_import_and_reader_contract_are_artifact_and_device_free(self) -> None:
        source_tree = ast.parse(SOURCE.read_text(encoding="utf-8"))
        reader_tree = ast.parse(READER.read_text(encoding="utf-8"))
        imports = {
            alias.name.split(".")[0]
            for tree in (source_tree, reader_tree)
            for node in ast.walk(tree)
            if isinstance(node, ast.Import)
            for alias in node.names
        }
        self.assertTrue({"cupy", "numpy"}.isdisjoint(imports))
        self.assertNotIn(
            "pontius.legal_river_quotient_selective_certified_separation",
            {
                node.module
                for node in ast.walk(reader_tree)
                if isinstance(node, ast.ImportFrom)
            },
        )
        original = Path.read_bytes

        def guarded(path: Path) -> bytes:
            if path.resolve() == RESULT.resolve():
                raise AssertionError("source seal touched the prospective result")
            return original(path)

        with patch.object(Path, "read_bytes", guarded):
            reader.verify_independent_contract()
        with tempfile.TemporaryDirectory() as directory:
            environment = dict(os.environ)
            environment["PYTHONPATH"] = str(ROOT / "src")
            completed = subprocess.run(
                [
                    sys.executable,
                    "-B",
                    "-c",
                    (
                        "import sys; "
                        "import pontius.legal_river_quotient_selective_certified_separation; "
                        "import pontius.legal_river_quotient_selective_certified_separation_result; "
                        "print(int('cupy' in sys.modules))"
                    ),
                ],
                cwd=directory,
                env=environment,
                check=True,
                capture_output=True,
                text=True,
            )
        self.assertEqual(completed.stdout.strip(), "0")
        self.assertFalse(RESULT.exists())

    def test_every_selective_price_reads_exactly_57_and_matches_direct_sum(self) -> None:
        for (cards, family), (instance, _, exhaustive, prices) in self.cases.items():
            sources = source.complete_masks(cards, 6)
            self.assertEqual(len(sources), exhaustive.exact_leaf_prices)
            self.assertEqual(exhaustive.selective_subset_scalar_reads, 57 * len(sources))
            self.assertEqual(source.selective_price(instance, sources[0])[1], 57)
            for source_mask in sources:
                observed, reads = source._selective_price_maps(
                    source_mask,
                    dict(instance.source_bases),
                    dict(instance.subset_scalars),
                )
                self.assertEqual(reads, 57, (cards, family, source_mask))
                self.assertEqual(observed, prices[source_mask])

    def test_every_bound_dominates_descendants_and_every_leaf_is_exact(self) -> None:
        for (cards, family), (instance, compiled, exhaustive, prices) in self.cases.items():
            sources = source.complete_masks(cards, 6)
            self.assertEqual(compiled.ledger.source_base_values_read, len(sources))
            self.assertEqual(compiled.ledger.leaf_bound_equalities, len(sources))
            self.assertEqual(
                compiled.ledger.descendant_domination_comparisons,
                7 * len(sources),
            )
            covered = 0
            for node in compiled.nodes:
                descendants = [
                    mask
                    for mask in sources
                    if source.cards_from_mask(mask)[: len(node.prefix)] == node.prefix
                ]
                self.assertEqual(len(descendants), node.descendant_count)
                self.assertTrue(descendants)
                self.assertGreaterEqual(
                    node.upper,
                    max(prices[mask] for mask in descendants),
                    (cards, family, node.prefix),
                )
                if len(node.prefix) == 6:
                    self.assertEqual(
                        node.upper,
                        prices[descendants[0]],
                    )
                    covered += 1
            self.assertEqual(covered, exhaustive.exact_leaf_prices)

    def test_all_modes_match_exhaustive_authority_and_work_is_separated(self) -> None:
        for (cards, family), (_, compiled, exhaustive, _) in self.cases.items():
            argmax = source.search(compiled, "exact_argmax")
            closure = source.search(compiled, "final_global_closure")
            proposal = source.search(compiled, "proposal_separation")
            no_prune = source.search(
                compiled, "final_global_closure", allow_pruning=False
            )
            self.assertEqual(
                (argmax.maximum_price, argmax.maximizers),
                (exhaustive.maximum_price, exhaustive.maximizers),
            )
            self.assertEqual(closure.positive_coordinates, exhaustive.positive_coordinates)
            if proposal.proposal_coordinate is None:
                self.assertFalse(exhaustive.positive_coordinates)
            else:
                self.assertIn(proposal.proposal_coordinate, exhaustive.positive_coordinates)
                self.assertGreater(proposal.proposal_price, 0)
            self.assertTrue(argmax.complete_domain_covered)
            self.assertTrue(closure.complete_domain_covered)
            self.assertEqual(
                argmax.visited_source_leaves + argmax.pruned_source_leaves,
                len(source.complete_masks(cards, 6)),
            )
            self.assertEqual(no_prune.exact_leaf_prices, exhaustive.exact_leaf_prices)
            self.assertEqual(no_prune.selective_subset_scalar_reads, 57 * len(exhaustive.maximizers) if family == "all_zero_tie" else 57 * exhaustive.exact_leaf_prices)
            self.assertEqual(no_prune.pruned_source_leaves, 0)
            self.assertEqual(no_prune.positive_coordinates, exhaustive.positive_coordinates)

    def test_tie_late_spike_and_cancellation_controls_are_live(self) -> None:
        for cards in source.DOMAINS:
            tie_instance, tie_compiled, tie_exhaustive, _ = self.cases[(cards, "all_zero_tie")]
            self.assertEqual(len(tie_exhaustive.maximizers), len(source.complete_masks(cards, 6)))
            tie_closure = source.search(tie_compiled, "final_global_closure")
            self.assertEqual(tie_closure.exact_leaf_prices, 0)
            self.assertEqual(tie_closure.pruned_source_leaves, tie_exhaustive.exact_leaf_prices)
            late_instance, late_compiled, late_exhaustive, _ = self.cases[(cards, "late_positive")]
            self.assertEqual(late_exhaustive.positive_coordinates, (source.complete_masks(cards, 6)[-1],))
            self.assertEqual(
                source.search(late_compiled, "final_global_closure").positive_coordinates,
                late_exhaustive.positive_coordinates,
            )
            late_proposal = source.search(late_compiled, "proposal_separation")
            self.assertEqual(late_proposal.proposal_coordinate, late_exhaustive.positive_coordinates[0])
            self.assertEqual(late_proposal.exact_leaf_prices, 1)
            _, spike_compiled, spike_exhaustive, _ = self.cases[(cards, "source_base_spike")]
            self.assertEqual(
                source.search(spike_compiled, "exact_argmax").maximizers,
                spike_exhaustive.maximizers,
            )
            _, cancellation_compiled, cancellation_exhaustive, _ = self.cases[
                (cards, "signed_cancellation_loose_bound")
            ]
            self.assertFalse(cancellation_exhaustive.positive_coordinates)
            unpruned = source.search(
                cancellation_compiled,
                "final_global_closure",
                allow_pruning=False,
            )
            self.assertEqual(unpruned.exact_leaf_prices, cancellation_exhaustive.exact_leaf_prices)

    def test_missing_rows_threshold_domain_and_bound_mutations_reject(self) -> None:
        instance = source.make_instance(10, "late_positive")
        with self.assertRaises(ValueError):
            source.validate_instance(replace(instance, source_bases=instance.source_bases[:-1]))
        with self.assertRaises(ValueError):
            source.validate_instance(replace(instance, subset_scalars=instance.subset_scalars[:-1]))
        active_only = replace(instance, source_bases=instance.source_bases[:2])
        with self.assertRaises(ValueError):
            source.compile_separation(active_only)
        source_text = SOURCE.read_text(encoding="utf-8")
        self.assertTrue(_has_nonstrict_zero_prune(source_text))
        self.assertFalse(_has_nonstrict_zero_prune(source_text.replace("node.upper <= 0", "node.upper < 0")))
        compiled = source.compile_separation(instance)
        poisoned_nodes = tuple(
            replace(node, upper=0) if node.prefix == () else node
            for node in compiled.nodes
        )
        poisoned = replace(compiled, nodes=poisoned_nodes)
        self.assertNotEqual(
            source.search(poisoned, "final_global_closure").positive_coordinates,
            source.exhaustive_authority(instance).positive_coordinates,
        )

    def test_independent_reader_reconstructs_and_rejects_mutated_result(self) -> None:
        dependencies = {
            relative: "b" * 64 for relative in reader.DEPENDENCY_RELATIVE_PATHS
        }
        # This synthetic codec control does not admit an old experiment source.
        # Pricing, search, serialization, and independent reconstruction stay real.
        with patch.object(source, "verify_preregistered_contract"):
            document = source.build_result(
                source_commit="a" * 40,
                dependency_hashes=dependencies,
            )
        raw = source.canonical_json_bytes(document)
        rebound = reader.rebind_selective_separation_bytes(
            raw,
            validate_dependencies=False,
        )
        self.assertEqual(rebound.row_count, 12)
        self.assertTrue(rebound.some_pruning)
        mutated = deepcopy(document)
        mutated["rows"][0]["compile_ledger"]["source_base_values_read"] += 1
        with self.assertRaises(ValueError):
            reader.rebind_selective_separation_bytes(
                source.canonical_json_bytes(mutated),
                validate_dependencies=False,
            )


if __name__ == "__main__":
    unittest.main()
