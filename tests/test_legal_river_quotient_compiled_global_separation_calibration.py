from __future__ import annotations

import ast
from dataclasses import asdict
from fractions import Fraction
from hashlib import sha256
import json
from math import comb, factorial
from pathlib import Path
import re
import sys
import tempfile
import unittest
from unittest.mock import patch

from pontius import legal_river_quotient_compiled_global_separation_calibration as source
from pontius import legal_river_quotient_compiled_global_separation_calibration_result as reader
from pontius import legal_river_quotient_compiled_global_separation_calibration_runner as runner


ROOT = Path(__file__).parents[1]
CONFIG = ROOT / source.CONFIG_RELATIVE_PATH
RESULT = ROOT / source.RESULT_RELATIVE_PATH
SOURCE = Path(source.__file__)
RUNNER = Path(runner.__file__)
READER = Path(reader.__file__)
CONTROLS = Path(__file__)
LAUNCHER = ROOT / "run_legal_river_quotient_compiled_global_separation_calibration.py"


def _independent_pricing() -> tuple[int, ...]:
    return tuple((11 + 37 * index) % 19 - 9 for index in range(175)) + (1,)


def _independent_masks(cards: int, width: int) -> tuple[int, ...]:
    rows = []
    for mask in range(1 << cards):
        if mask.bit_count() == width:
            rows.append(mask)

    def rank(mask: int) -> int:
        cards_in_mask = [card for card in range(cards) if mask & (1 << card)]
        return sum(comb(card, ordinal) for ordinal, card in enumerate(cards_in_mask, 1))

    return tuple(sorted(rows, key=rank))


def _independent_raw_row(mode: str, cards: int, mask: int) -> tuple[int, ...]:
    schema = "pontius-adr0457-compiled-separation-calibration-fixture-v1"
    values = []
    for index in range(175):
        framing = (
            f"{schema}|{mode}|{cards}|H|{mask.bit_count()}|{mask}|{index}"
        ).encode("ascii")
        values.append(int.from_bytes(sha256(framing).digest()[:8], "big") % 17 - 8)
    target = -1 if mode == "prove_none" and mask.bit_count() == 1 else 0
    values.append(target - sum(a * b for a, b in zip(values, _independent_pricing()[:175], strict=True)))
    return tuple(values)


def _blank_work(value: int = 0) -> list[dict[str, int]]:
    return [
        {
            "projection_work": value,
            "logical_operations": value,
            "arithmetic_words": 0,
            "transferred_bytes": 0,
            "decision_keys_reconstructed": 0,
        }
        for _ in source.PHASE_NAMES
    ]


def _resource_stream(*, spill: int = 0) -> bytes:
    lines = []
    for name in source.KERNEL_NAMES:
        lines.extend(
            (
                f"ptxas info    : Compiling entry function '{name}' for 'sm_120'",
                f"ptxas info    : Function properties for {name}",
                f"    0 bytes stack frame, {spill} bytes spill stores, {spill} bytes spill loads",
                "ptxas info    : Used 32 registers, 384 bytes cmem[0]",
            )
        )
    return ("\n".join(lines) + "\n").encode("ascii")


def _cuobjdump_stream() -> bytes:
    return (
        "\n".join(
            line
            for name in source.KERNEL_NAMES
            for line in (
                f"Function {name}:",
                " REG:32 STACK:0 LOCAL:0 SHARED:0",
            )
        )
        + "\n"
    ).encode("ascii")


def _nvdisasm_stream() -> bytes:
    return (
        "\n".join(
            line
            for index, name in enumerate(source.KERNEL_NAMES)
            for line in (
                f".global {name}",
                " LDL R0, [R1];" if index == 0 else " MOV R0, R1;",
                " STL [R1], R0;" if index == 0 else " NOP;",
            )
        )
        + "\n"
    ).encode("ascii")


class CompiledGlobalSeparationSourceSealTests(unittest.TestCase):
    def test_config_parent_chain_claims_and_result_absence(self) -> None:
        self.assertEqual(source.canonical_lf_sha256(CONFIG), source.CONFIG_SHA256)
        source.verify_preregistered_contract()
        self.assertFalse(RESULT.exists())
        self.assertEqual(source.PREREGISTRATION_COMMIT, runner.PREREGISTRATION_COMMIT)
        self.assertEqual(source.ARM_NAMES, reader.ARMS)
        self.assertEqual(source.PHASE_NAMES, reader.PHASES)
        claims = source.source_boundary_claims()
        self.assertTrue(claims["source_seal"])
        self.assertEqual(claims["production_base_classification"], "producer_absent")
        self.assertIsNone(claims["candidate_selected"])
        self.assertIsNone(claims["topology_selected"])
        self.assertFalse(claims["truncation_authorized"])

    def test_import_surface_is_inert_and_reader_is_independent(self) -> None:
        source_tree = ast.parse(SOURCE.read_text(encoding="utf-8"))
        reader_tree = ast.parse(READER.read_text(encoding="utf-8"))
        top_source_imports = {
            alias.name
            for node in source_tree.body
            if isinstance(node, ast.Import)
            for alias in node.names
        }
        reader_imports = {
            alias.name
            for node in ast.walk(reader_tree)
            if isinstance(node, ast.Import)
            for alias in node.names
        }
        reader_from = {
            node.module
            for node in ast.walk(reader_tree)
            if isinstance(node, ast.ImportFrom) and node.module is not None
        }
        self.assertNotIn("cupy", top_source_imports)
        self.assertNotIn("numpy", top_source_imports)
        self.assertNotIn(
            "pontius.legal_river_quotient_compiled_global_separation_calibration",
            reader_from,
        )
        self.assertNotIn("cupy", reader_imports)
        self.assertNotIn("numpy", reader_imports)
        self.assertNotIn("scipy", reader_imports)
        self.assertNotIn("cupy", sys.modules)
        self.assertFalse(RESULT.exists())

    # Armed mutation fixture spelling: \r\n
    def test_dual_canonical_lf_and_armed_literal_escape_mutation(self) -> None:
        prospective = (SOURCE, RUNNER, READER, CONTROLS, LAUNCHER)
        paths = tuple(ROOT / relative for relative in source.PARENT_IDENTITIES) + prospective
        expected_token_bearing = {
            "src/pontius/legal_river_quotient_compiled_global_separation_calibration.py": 1,
            "tests/test_legal_river_quotient_compiled_global_separation_calibration.py": 1,
            "tests/test_legal_river_quotient_global_separation_topologies.py": 1,
        }
        for path in paths:
            relative = path.relative_to(ROOT).as_posix()
            raw = path.read_bytes()
            production = source._canonical_lf(raw)
            independent = source.independent_canonical_lf(raw)
            runner_loop = runner._canonical_lf(raw)
            self.assertEqual(production, independent)
            self.assertEqual(production, runner_loop)
            mutated, occurrences = source.forbidden_literal_escape_mutation(raw)
            self.assertEqual(occurrences, expected_token_bearing.get(relative, 0))
            self.assertEqual(mutated != raw, occurrences > 0)
            if occurrences:
                self.assertNotEqual(sha256(production).digest(), sha256(mutated).digest())

    def test_complete_matrix_and_frozen_sha_permutations(self) -> None:
        cells = source.execution_cells()
        self.assertEqual(len(cells), 480)
        self.assertEqual(len({cell.canonical for cell in cells}), 480)
        orders = []
        for pass_index in source.ALL_PASS_INDICES:
            rows = source.pass_cells(pass_index)
            self.assertEqual(set(rows), set(cells))
            self.assertEqual(
                rows,
                tuple(
                    sorted(
                        cells,
                        key=lambda cell: (
                            sha256(
                                f"adr0457|{pass_index}|{cell.canonical}".encode("ascii")
                            ).digest(),
                            cell.canonical,
                        ),
                    )
                ),
            )
            orders.append(tuple(cell.canonical for cell in rows))
        self.assertEqual(len(set(orders)), 6)
        self.assertEqual(sum(len(order) for order in orders), 2_880)

    def test_ten_and_twelve_card_fixtures_match_independent_generator(self) -> None:
        self.assertEqual(source.pricing_vector(), _independent_pricing())
        for cards in (10, 12):
            for level in range(5):
                expected_masks = _independent_masks(cards, level)
                self.assertEqual(source.complete_masks(cards, level), expected_masks)
                for mode in source.RUNTIME_MODES:
                    for mask in expected_masks:
                        row = source.raw_h_row(mode, cards, mask)
                        self.assertEqual(row, _independent_raw_row(mode, cards, mask))
                        expected_h = -1 if mode == "prove_none" and level == 1 else 0
                        self.assertEqual(source.contract_h(row), expected_h)

    def test_extended_fixture_manifests_bind_every_axis_without_promotion(self) -> None:
        manifests = source.fixture_manifests()
        self.assertEqual(len(manifests), 30)
        self.assertEqual(
            {(row.cards, row.runtime_mode, row.base_mode) for row in manifests},
            set(
                (cards, mode, base)
                for cards in source.DOMAINS
                for mode in source.RUNTIME_MODES
                for base in source.BASE_MODES
            ),
        )
        for row in manifests:
            self.assertEqual(row.h_row_count, sum(comb(row.cards, rank) for rank in range(5)))
            self.assertEqual(row.source_count, comb(row.cards, 6))
            self.assertRegex(row.authority_sha256, r"^[0-9a-f]{64}$")
            if row.runtime_mode == "positive_witness":
                self.assertGreaterEqual(row.expected_price_minimum, 1)
            else:
                self.assertEqual(row.expected_price_maximum, -1)
                self.assertIn(row.expected_price_minimum, (-2, -1))
        self.assertEqual(source.source_boundary_claims()["production_base_classification"], "producer_absent")

    def test_exact_prices_sparse_support_and_scale_identities(self) -> None:
        self.assertTrue(
            all(
                source.H_SEED_WEIGHTS[level] * factorial(6 - level)
                == source.H_OUTPUT_SCALE * source.PRICE_COEFFICIENTS[level]
                for level in range(5)
            )
        )
        for cards in source.DOMAINS:
            support = source.sparse_support_ranks(cards)
            self.assertEqual(tuple(sorted(set(support))), support)
            self.assertEqual(support[0], 0)
            self.assertEqual(support[-1], comb(cards, 6) - 1)
            samples = sorted({0, 1, comb(cards, 6) // 2, comb(cards, 6) - 1, *support[:3]})
            for rank in samples:
                for base in source.BASE_MODES:
                    self.assertGreater(
                        source.exact_price("positive_witness", base, cards, rank), 0
                    )
                    self.assertIn(
                        source.exact_price("prove_none", base, cards, rank), (-1, -2)
                    )

    def test_widths_and_rrns_decision_keys_are_independently_admitted(self) -> None:
        source.validate_rrns_parameters()
        admission = source.derive_arithmetic_admission()
        self.assertTrue(admission.table_range_sufficient)
        self.assertTrue(admission.scalar_range_sufficient)
        self.assertTrue(admission.bounded_single_modulus_decision_sufficient)
        produced_event = {
            "schema_version": "pontius-adr0457-arithmetic-admission-v1",
            "quantity_widths": [asdict(row) for row in admission.quantity_widths],
            "zeta_rank_widths": [asdict(row) for row in admission.zeta_rank_widths],
            "working_product_decimal": str(admission.working_product),
            "redundant_modulus": admission.redundant_modulus,
            "table_range_sufficient": admission.table_range_sufficient,
            "scalar_range_sufficient": admission.scalar_range_sufficient,
            "bounded_single_modulus_decision_sufficient": (
                admission.bounded_single_modulus_decision_sufficient
            ),
            "sha256": admission.sha256,
        }
        self.assertEqual(produced_event, reader._expected_arithmetic_admission())
        self.assertEqual(len({row.quantity for row in admission.quantity_widths}), len(admission.quantity_widths))
        self.assertTrue(all(row.guard_inclusive_limbs == row.mathematical_limbs + 1 for row in admission.quantity_widths))
        bound = next(row.signed_absolute_bound for row in admission.quantity_widths if row.quantity == "RRNS_decision_key")
        for value in (-bound, -2, -1, 0, 1, 2, bound):
            code = source.encode_residues(value)
            receipt = source.reconstruct_decision_key(code, absolute_bound=bound)
            self.assertEqual(receipt.value, value)
            self.assertEqual(receipt.full_codeword_value, receipt.base_extension_value)
        left = source.reconstruct_decision_key(source.encode_residues(-1), absolute_bound=bound)
        right = source.reconstruct_decision_key(source.encode_residues(0), absolute_bound=bound)
        adjacent = source.reconstruct_decision_key(source.encode_residues(1), absolute_bound=bound)
        self.assertLess(left.value, right.value)
        self.assertLess(right.value, adjacent.value)

    def test_every_single_channel_fault_rejects_and_correlated_boundary_is_explicit(self) -> None:
        bound = 1_000
        authority = 17
        code = list(source.encode_residues(authority))
        for channel in range(9):
            mutated = list(code)
            modulus = (source.WORKING_MODULI + (source.REDUNDANT_MODULUS,))[channel]
            mutated[channel] = (mutated[channel] + 1) % modulus
            with self.assertRaises((OverflowError, RuntimeError, ArithmeticError)):
                source.reconstruct_decision_key(mutated, absolute_bound=bound)
        correlated = source.reconstruct_decision_key(
            source.encode_residues(authority + 1), absolute_bound=bound
        )
        self.assertEqual(correlated.value, authority + 1)
        self.assertNotEqual(correlated.value, authority)

    def test_prefix_geometry_and_every_early_switch_control(self) -> None:
        for cards in source.DOMAINS:
            geometry = source.prefix_geometry(cards)
            self.assertEqual(geometry.node_count, comb(cards + 1, 6))
            self.assertEqual(len(geometry.child_indices), geometry.node_count - 1)
            self.assertEqual(geometry.level_offsets[0], 0)
            self.assertEqual(geometry.level_offsets[-1], geometry.node_count)
            self.assertEqual(len(geometry.prefixes), len(set(geometry.prefixes)))
            for base in source.BASE_MODES:
                proof = source.prove_early_hybrid_switch(cards, base)
                self.assertTrue(proof.switches_early)
                self.assertEqual(proof.exact_leaves_at_switch, proof.early_checkpoint)
                self.assertLess(proof.certified_coverage_at_switch, proof.half_coverage)
                for mode in source.RUNTIME_MODES:
                    for hybrid in (False, True):
                        terminal = source.expected_prefix_terminal(
                            cards, mode, base, hybrid
                        )
                        algebraic = (
                            1
                            if mode == "positive_witness"
                            else (comb(cards, 6) + 63) // 64
                            if hybrid
                            else 0
                        )
                        self.assertEqual(terminal["exact_leaves"], algebraic)

    def test_nineteen_phases_partition_exactly_and_walls_include_equality(self) -> None:
        stamps = tuple(10 + index * index for index in range(20))
        partition = source.phase_partition(stamps, _blank_work(3))
        self.assertEqual(tuple(row.name for row in partition.rows), source.PHASE_NAMES)
        self.assertEqual(sum(row.elapsed_ns for row in partition.rows), partition.primitive_total_ns)
        self.assertTrue(source.wall_passes(source.PUBLIC_WALL_NS, source.PUBLIC_WALL_NS))
        self.assertFalse(source.wall_passes(source.PUBLIC_WALL_NS + 1, source.PUBLIC_WALL_NS))
        with self.assertRaises(ValueError):
            source.phase_partition(stamps[:-1], _blank_work())
        broken = list(stamps)
        broken[9] = broken[8] - 1
        with self.assertRaises(ValueError):
            source.phase_partition(broken, _blank_work())

    def test_exact_affine_fit_matches_independent_reader_and_all_boundaries(self) -> None:
        cases = (
            ([1, 2, 3, 4, 5], [3, 5, 7, 9, 11], 45),
            ([1, 2, 3, 4, 5], [9, 7, 5, 3, 1], 45),
            ([5, 5, 5, 5, 5], [1, 7, 3, 9, 5], 5),
            ([0, 1, 4, 9, 16], [0, 0, 1, 1, 100], 100),
        )
        for xs, ys, target in cases:
            produced = source.exact_nonnegative_affine_fit(xs, ys, target)
            independent = reader.independent_fit(xs, ys, target)
            self.assertEqual(produced.intercept, independent.intercept)
            self.assertEqual(produced.slope, independent.slope)
            self.assertEqual(produced.sse, independent.sse)
            self.assertEqual(produced.positive_residual_guard, independent.guard)
            self.assertEqual(produced.target_upper, independent.upper)
            self.assertEqual(produced.target_upper_ceiling, independent.ceiling)
            self.assertEqual(produced.candidate, independent.candidate)
        exact = source.exact_nonnegative_affine_fit([1, 2, 3, 4, 5], [0, 0, 0, 0, 0], 45)
        self.assertEqual(exact.target_upper, Fraction())
        self.assertEqual(exact.target_upper_ceiling, 0)

    def test_symbolic_target_work_never_forms_a_target_value(self) -> None:
        geometry = source.symbolic_geometry(45)
        self.assertEqual(geometry["sources"], 8_145_060)
        self.assertEqual(geometry["zeta_cover_edges"], 55_619_730)
        self.assertEqual(geometry["direct_subset_terms"], 464_268_420)
        for cell in source.execution_cells():
            reduced = source.phase_work_coordinates(cell)
            target = source.phase_work_coordinates(cell, target=True)
            self.assertEqual(set(reduced), set(source.PHASE_NAMES))
            self.assertEqual(set(target), set(source.PHASE_NAMES))
            self.assertTrue(all(isinstance(value, int) and value >= 0 for value in target.values()))
            self.assertEqual(
                reduced,
                reader._work(asdict(cell), target=False),
            )
            self.assertEqual(
                target,
                reader._work(asdict(cell), target=True),
            )
        source_text = SOURCE.read_text(encoding="utf-8")
        self.assertNotIn("fixture_manifest(45", source_text)
        self.assertNotIn("raw_h_row(runtime_mode, 45", source_text)

    def test_memory_liveness_checks_aliases_and_both_caps(self) -> None:
        for cards in source.DOMAINS:
            for schedule in source.ARITHMETIC_SCHEDULES:
                evidence = source.memory_liveness(
                    source.reduced_memory_plan(cards, schedule), boundary_count=21
                )
                self.assertTrue(evidence.alias_checked)
                self.assertTrue(evidence.ceiling_passed)
                self.assertTrue(evidence.reserve_passed)
        with self.assertRaises(ValueError):
            source.memory_liveness(
                (
                    source.BufferLifetime("a", "same", 1, 0, 2),
                    source.BufferLifetime("b", "same", 1, 1, 3),
                ),
                boundary_count=4,
            )

    def test_one_physical_five_channel_arena_retires_relabeling_escape(self) -> None:
        text = SOURCE.read_text(encoding="utf-8")
        self.assertEqual(text.count("global_rrns_batch_arena = cp.zeros("), 1)
        self.assertNotIn('"h_batch"', text)
        self.assertNotIn('"prices_batch"', text)
        self.assertNotIn('"zeta_batch"', text)
        self.assertNotIn('"base_batch"', text)
        self.assertNotIn('"structural_batch"', text)
        self.assertNotIn('"selected_batch"', text)
        arena_rows = [
            row
            for row in source.campaign_memory_plan()
            if row.name == "sole_five_channel_RRNS_table_arena"
        ]
        self.assertEqual(len(arena_rows), 1)
        self.assertEqual(
            arena_rows[0].byte_count,
            max(source.rrns_batch_arena_bytes(cards) for cards in source.DOMAINS),
        )
        self.assertEqual(
            source.REJECTED_LIVENESS_EQUIVALENCE,
            reader.REJECTED_LIVENESS_EQUIVALENCE,
        )

    def test_literal_translation_unit_has_one_surface_and_no_host_escape(self) -> None:
        contract = source.cuda_source_contract()
        self.assertEqual(tuple(contract["entry_kernels"]), source.KERNEL_NAMES)
        self.assertEqual(contract["cuda_source_sha256"], source.CUDA_SOURCE_SHA256)
        self.assertGreaterEqual(contract["decision_reconstruction_call_sites"], 2)
        self.assertTrue(contract["device_resident_prefix_heap"])
        self.assertFalse(contract["resident_nine_schedule_present"])
        self.assertNotIn("cudaMalloc", source.CUDA_SOURCE)
        self.assertNotIn("cudaFree", source.CUDA_SOURCE)
        self.assertNotIn("heapq", source.CUDA_SOURCE)
        self.assertIn("admit_rrns_first_batch", source.CUDA_SOURCE)
        self.assertIn("admit_rrns_second_batch", source.CUDA_SOURCE)
        self.assertIn("selected_leaf_ranks", source.CUDA_SOURCE)
        mutated = source.CUDA_SOURCE.replace(
            "No residue is ordered directly", "residue tuple is ordered directly", 1
        )
        with self.assertRaises(ValueError):
            source.cuda_source_contract(mutated)
        host_text = SOURCE.read_text(encoding="utf-8")
        host = source.timed_host_surface_contract(host_text)
        self.assertEqual(tuple(host["phase_callbacks"]), source.PHASE_CALLBACK_NAMES)
        self.assertEqual(host["host_prefix_authority_calls"], 0)
        self.assertIn(
            "int cards, unsigned long long source_count",
            source.CUDA_SOURCE,
        )
        injected = host_text.replace(
            "    def direct() -> None:\n",
            "    def direct() -> None:\n"
            "        exact_price('positive_witness', 'exact_lattice_base', 10, 0)\n",
            1,
        )
        self.assertNotEqual(injected, host_text)
        with self.assertRaises(ValueError):
            source.timed_host_surface_contract(injected)

    def test_resource_parser_rejects_spills_missing_entries_and_registers(self) -> None:
        rows = source.parse_ptxas_verbose(_resource_stream())
        self.assertTrue(source.resource_gate(rows))
        spilled = source.parse_ptxas_verbose(_resource_stream(spill=8))
        self.assertFalse(source.resource_gate(spilled))
        with self.assertRaises(ValueError):
            source.parse_ptxas_verbose(_resource_stream().replace(b"restore_workspace", b"missing", 2))
        changed = dict(rows)
        row = changed[source.KERNEL_NAMES[0]]
        changed[source.KERNEL_NAMES[0]] = source.PtxasResource(
            row.kernel, 256, row.stack_frame_bytes, 0, 0
        )
        self.assertFalse(source.resource_gate(changed))
        cubin = source.parse_cuobjdump_resource_usage(_cuobjdump_stream())
        self.assertEqual(tuple(cubin), source.KERNEL_NAMES)
        self.assertTrue(all(row.local_bytes == 0 for row in cubin.values()))
        sass = source.parse_nvdisasm_local_sites(_nvdisasm_stream())
        self.assertEqual(sass[source.KERNEL_NAMES[0]].local_load_sites, 1)
        self.assertEqual(sass[source.KERNEL_NAMES[0]].local_store_sites, 1)
        with self.assertRaises(ValueError):
            source.parse_cuobjdump_resource_usage(
                _cuobjdump_stream().replace(b" LOCAL:0", b"", 1)
            )
        with self.assertRaises(ValueError):
            source.parse_nvdisasm_local_sites(
                _nvdisasm_stream().replace(
                    f".global {source.KERNEL_NAMES[-1]}\n".encode("ascii"), b"", 1
                )
            )

    def test_runner_and_reader_sources_preserve_exclusive_no_device_boundary(self) -> None:
        runner_text = RUNNER.read_text(encoding="utf-8")
        reader_text = READER.read_text(encoding="utf-8")
        launcher_text = LAUNCHER.read_text(encoding="utf-8")
        self.assertIn("DurableEvidenceJournalWriter.create", runner_text)
        self.assertIn("path.open(\"xb\")", runner_text)
        self.assertIn("os.fsync", runner_text)
        self.assertIn("-B", runner_text)
        self.assertIn("recover_journal_bytes", reader_text)
        self.assertNotIn("compiled_global_separation_calibration as", reader_text)
        self.assertIn("main", launcher_text)
        self.assertFalse(RESULT.exists())

    def test_synthetic_failure_journal_is_permanent_and_independently_readable(self) -> None:
        # This control becomes runnable once ADR-0458 itself exists; before that
        # dependency_hashes must fail closed rather than silently omit the seal.
        adr = ROOT / "docs/decisions/ADR-0458-source-seal-the-compiled-global-separation-calibration.md"
        if not adr.exists():
            self.skipTest("ADR-0458 is written after the source controls settle")

        def campaign(emit):
            emit(
                "terminal_evidence",
                {
                    "schema_version": "pontius-adr0457-compiled-calibration-terminal-evidence-v1",
                    "terminal": "compiler_rejected",
                    "passed": False,
                    "laboratory_elapsed_ns": 1,
                },
            )
            return {
                "terminal": "compiler_rejected",
                "passed": False,
                "laboratory_elapsed_ns": 1,
            }

        ticks = iter((100, 110, 120, 130, 140))
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "synthetic.jsonl"
            execution = runner.execute_owner_to_path(
                output_path=path,
                campaign_executor=campaign,
                monotonic_ns=lambda: next(ticks),
            )
            self.assertFalse(execution.terminal["passed"])
            assessed = reader.assess_calibration_bytes(path.read_bytes())
            self.assertFalse(assessed.passed)
            self.assertEqual(assessed.terminal, "compiler_rejected")
            with self.assertRaises(FileExistsError):
                runner.execute_owner_to_path(
                    output_path=path,
                    campaign_executor=campaign,
                    monotonic_ns=lambda: 1,
                )
            mutated = path.read_bytes()[:-1]
            with self.assertRaises(ValueError):
                reader.assess_calibration_bytes(mutated)

    def test_source_probe_rebinds_split_runtime_without_science(self) -> None:
        challenge = sha256(b"adr0457-source-seal-control").hexdigest()
        probe = runner.source_seal_probe(challenge)
        self.assertFalse(probe["compiler_executed"])
        self.assertFalse(probe["cupy_scientific_imported"])
        self.assertFalse(probe["device_queried"])
        self.assertTrue(probe["result_absent"])
        child = probe["child"]
        self.assertFalse(child["cupy_loaded"])
        self.assertFalse(child["scientific_source_loaded"])
        self.assertFalse(child["compiler_executed"])
        self.assertFalse(child["device_queried"])

    def test_result_path_is_dash_text_and_source_seal_has_no_result_access(self) -> None:
        attributes = (ROOT / "artifacts/work_preflight/.gitattributes").read_text(
            encoding="utf-8"
        )
        self.assertIn("*.jsonl -text", attributes.splitlines())
        self.assertFalse(RESULT.exists())
        for path in (SOURCE, RUNNER, READER, CONTROLS, LAUNCHER):
            self.assertTrue(path.is_file())
        with patch.object(Path, "read_bytes", side_effect=AssertionError("result read")):
            # The claims function is deliberately path-free and remains safe
            # even under an adversarial global read guard.
            self.assertIsNone(source.source_boundary_claims()["compiled_calibration_result"])


if __name__ == "__main__":
    unittest.main()
