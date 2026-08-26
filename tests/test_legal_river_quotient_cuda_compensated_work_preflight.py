from __future__ import annotations

import ast
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from pontius.durable_evidence_journal import (
    JournalRecordEnvelope,
    build_journal_record_body,
    recover_journal_bytes,
)
import pontius.legal_river_quotient_cuda_compensated_work_preflight as source
import pontius.legal_river_quotient_cuda_compensated_work_preflight_result as reader
import pontius.legal_river_quotient_cuda_compensated_work_preflight_runner as runner


_ROOT = Path(__file__).parents[1]
_CONFIG = (
    _ROOT
    / "experiments/configs/"
    "legal-river-quotient-cuda-compensated-work-preflight-v1.json"
)
_CORRECTION_CONFIG = (
    _ROOT
    / "experiments/configs/"
    "legal-river-quotient-cuda-compensated-work-preflight-v2.json"
)
_SOURCE = (
    _ROOT
    / "src/pontius/legal_river_quotient_cuda_compensated_work_preflight.py"
)
_RUNNER = (
    _ROOT
    / "src/pontius/legal_river_quotient_cuda_compensated_work_preflight_runner.py"
)
_READER = (
    _ROOT
    / "src/pontius/legal_river_quotient_cuda_compensated_work_preflight_result.py"
)
_RESULT = (
    _ROOT
    / "artifacts/work_preflight/"
    "legal_river_quotient_cuda_compensated_work_preflight_v1.jsonl"
)
_RESERVED = _ROOT / "artifacts/legal_river_quotient_cuda_consumer_v1.jsonl"


def _git() -> dict[str, object]:
    return {"commit": "a" * 40, "dirty": False, "strict_status": True}


def _synthetic_resource_laboratory(*, mutate: str | None = None) -> dict[str, object]:
    raw = """Resource usage:
 Function direct_selected_queries_tile:
  REG:32 STACK:64 SHARED:0 LOCAL:128 CONSTANT[0]:16
 Function direct_selected_fold_tile:
  REG:64 STACK:1024 SHARED:0 LOCAL:256 CONSTANT[0]:16
 Function direct_selected_adjoint_tile:
  REG:48 STACK:128 SHARED:0 LOCAL:64 CONSTANT[0]:16
"""
    parsed = source.parse_cuobjdump_resource_usage(raw)
    direct = {
        name: parsed[name]
        for name in (
            "direct_selected_queries_tile",
            "direct_selected_fold_tile",
            "direct_selected_adjoint_tile",
        )
    }
    driver = {
        name: {
            "local_size_bytes": row["STACK"] + row["LOCAL"],
            "registers": row["REG"],
            "shared_size_bytes": 0,
            "maximum_threads_per_block": 1024,
        }
        for name, row in direct.items()
    }
    if mutate == "limit":
        driver["direct_selected_fold_tile"]["local_size_bytes"] = 4097
    combined = source.combined_direct_kernel_resource_report(
        direct,
        driver,
        multiprocessor_count=84,
        maximum_threads_per_multiprocessor=1536,
    )
    cubin = {
        "tool_path": "synthetic-cuobjdump",
        "tool_version_output": "synthetic cuobjdump 13.3",
        "raw_resource_stdout": raw,
        "cubin_sha256": "b" * 64,
        "retained_payload_format": "elf-cubin",
        "caller_supplied_nvrtc_options": list(source.CUDA_COMPILE_OPTIONS),
        "cupy_version": "14.0.0",
        "cupy_internal_options_disclosure": [
            "target_architecture",
            "device_as_default_execution_space",
            "version_dependent_precompiled_header",
        ],
        "direct": direct,
        "driver_direct": driver,
        "effective_maxima": combined["effective_maxima"],
        "runtime_residency": combined["runtime_residency"],
        "gates": combined["gates"],
        "claims": {
            "exact_spill_load_store_count": None,
            "local_and_stack_are_not_relabeled_as_spill_counts": True,
        },
    }
    if mutate == "raw":
        cubin["raw_resource_stdout"] = raw.replace("REG:64", "REG:65")
    elif mutate == "driver":
        cubin["driver_direct"] = deepcopy(driver)
        cubin["driver_direct"]["direct_selected_fold_tile"]["local_size_bytes"] += 1
    elif mutate == "resident":
        cubin["runtime_residency"] = deepcopy(combined["runtime_residency"])
        cubin["runtime_residency"]["maximum_resident_threads"] += 1
    return {
        "schema_version": "legal-river-work-preflight-laboratory-v1",
        "kind": "runtime_primitives_and_compiler",
        "runtime": {"cupy_version": "14.0.0"},
        "primitive_gates": {"synthetic": True},
        "direct_order_controls": {
            "gates": {"synthetic": True},
            "all_gates_pass": True,
        },
        "direct_kernel_resources": driver,
        "cubin_resource_usage": cubin,
    }


def _synthetic_events(
    *,
    phase_mutation: str | None = None,
    projection_mutation: bool = False,
    resource_mutation: str | None = None,
    duration_ns: int = 1,
):
    config = source.load_preregistered_work_preflight_config()

    def execute(emit):
        emit("laboratory", _synthetic_resource_laboratory(mutate=resource_mutation))
        emit(
            "laboratory",
            {
                "schema_version": "legal-river-work-preflight-laboratory-v1",
                "kind": "complete_ten_legacy_direct_byte_identity",
                "control": {
                    "gates": {"synthetic": True},
                    "all_gates_pass": True,
                },
            },
        )
        emit(
            "laboratory",
            {
                "schema_version": "legal-river-work-preflight-laboratory-v1",
                "kind": "complete_ten_query_weight_control",
                "gates": {"synthetic": True},
            },
        )
        phase_totals: dict[int, dict[str, int]] = {}
        for cards in source.CALIBRATION_POPULATIONS:
            work = source.complete_campaign_work(cards)
            phase_totals[cards] = {phase: 0 for phase in source.PHASE_ORDER}
            observed_work: dict[str, int] = {}
            assigned_work: set[str] = set()
            for family_index, family in enumerate(source.POPULATION_FAMILIES):
                key = "default" if family_index == 0 else "alternate"
                chunks = config["chunk_contract"][str(cards)][key]
                cursor = cards * 1_000_000 + family_index * 100_000
                phases = list(source.PHASE_ORDER)
                direct_index = phases.index("direct_adjoint")
                phases.insert(
                    direct_index + 1,
                    "adjoint_recurrence_and_signed_sources",
                )
                if phase_mutation == "drop" and cards == 10 and family_index == 0:
                    phases.remove("final_release")
                if phase_mutation == "order" and cards == 10 and family_index == 0:
                    left = phases.index("forward_capture_and_digest")
                    right = phases.index("forward_release")
                    phases[left], phases[right] = phases[right], phases[left]
                for ordinal, phase in enumerate(phases):
                    start = cursor
                    stop = start + duration_ns
                    cursor = stop
                    row_work = (
                        {
                            name: work[name]
                            for name in source._PHASE_WORK_COUNTERS.get(phase, ())
                            if name not in assigned_work
                        }
                        if family_index == 0
                        else {}
                    )
                    assigned_work.update(row_work)
                    if (
                        phase_mutation == "work"
                        and cards == 22
                        and "source_pairing_visits" in row_work
                    ):
                        row_work["source_pairing_visits"] += 1
                    if (
                        phase_mutation == "semantic_phase"
                        and cards == 10
                        and family_index == 0
                        and phase == "adjoint_recurrence_and_signed_sources"
                    ):
                        row_work["adjoint_source_pairing_visits"] = work[
                            "adjoint_source_pairing_visits"
                        ]
                    payload = {
                        "schema_version": "legal-river-work-preflight-phase-v1",
                        "ordinal": ordinal,
                        "population": (
                            25
                            if phase_mutation == "population25"
                            and cards == 10
                            and family_index == 0
                            and ordinal == 0
                            else cards
                        ),
                        "family": family,
                        "repeat": ordinal % 2,
                        "tile": ordinal % 3,
                        "phase": phase,
                        "host_start_ns": start,
                        "host_stop_ns": stop,
                        "host_ns": (
                            duration_ns + 1
                            if phase_mutation == "sum"
                            and cards == 10
                            and family_index == 0
                            and ordinal == 1
                            else duration_ns
                        ),
                        "device_ns": 1,
                        "chunks": list(chunks),
                        "work": row_work,
                    }
                    emit("phase", payload)
                    phase_totals[cards][phase] += duration_ns
                    for name, value in row_work.items():
                        observed_work[name] = observed_work.get(name, 0) + value
            gates = {
                "semantic": True,
                "executed_work_ledger_exact": True,
                "phase_partition_exact": True,
                "population_wall": True,
            }
            population = {
                "schema_version": "legal-river-work-preflight-population-evidence-v1",
                "population": cards,
                "scalar_pairs": {},
                "conditional_value": [0, 1],
                "maximum_errors": {},
                "reporting_digests": {},
                "telemetry": {},
                "gates": gates,
                "all_gates_pass": True,
                "phase_host_ns": phase_totals[cards],
                "campaign_host_ns": sum(phase_totals[cards].values()),
                "executed_work": observed_work,
            }
            emit("population", population)
        projection = source.reconstruct_projection(phase_totals, config)
        authority_projection = deepcopy(projection)
        if projection_mutation:
            projection = deepcopy(projection)
            projection["passed"] = not projection["passed"]
        emit("projection", projection)
        return {
            "schema_version": "legal-river-work-preflight-terminal-evidence-v1",
            "terminal": (
                "completed_capacity_pass"
                if authority_projection["passed"]
                else "completed_capacity_rejection"
            ),
            "failed_population": None,
            "passed": bool(authority_projection["passed"]),
            "projection": authority_projection,
        }

    return execute


def _rewrite_journal(raw: bytes, mutate) -> bytes:
    recovery = recover_journal_bytes(
        raw,
        expected_protocol_sha256=runner.WORK_PREFLIGHT_PROTOCOL_SHA256,
        expected_campaign_sha256=runner.WORK_PREFLIGHT_CAMPAIGN_SHA256,
    )
    payloads = [deepcopy(record.body.payload) for record in recovery.records]
    mutate(payloads)
    previous: str | None = None
    lines: list[bytes] = []
    for index, (record, payload) in enumerate(zip(recovery.records, payloads)):
        body = build_journal_record_body(
            protocol_sha256=runner.WORK_PREFLIGHT_PROTOCOL_SHA256,
            campaign_sha256=runner.WORK_PREFLIGHT_CAMPAIGN_SHA256,
            kind=record.body.kind,
            sequence=index,
            previous_record_sha256=previous,
            semantic_identity_sha256=sha256(
                json.dumps(
                    payload,
                    allow_nan=False,
                    ensure_ascii=True,
                    separators=(",", ":"),
                    sort_keys=True,
                ).encode("ascii")
            ).hexdigest(),
            payload=payload,
        )
        envelope = JournalRecordEnvelope(body=body)
        lines.append(envelope.line_bytes)
        previous = envelope.line_sha256
    return b"".join(lines)


class WorkPreflightPureContractTests(unittest.TestCase):
    def test_fresh_import_is_device_free_and_contract_rebinds(self) -> None:
        code = (
            "import sys; "
            "import pontius.legal_river_quotient_cuda_compensated_work_preflight as s; "
            "import pontius.legal_river_quotient_cuda_compensated_work_preflight_runner; "
            "import pontius.legal_river_quotient_cuda_compensated_work_preflight_result; "
            "print(int('cupy' in sys.modules), s.cupy_import_call_count(), "
            "s.bounded_execution_call_count(), s.actual_execution_call_count(), "
            "s.actual_numeric_allocation_call_count(), s.actual_scientific_call_count())"
        )
        completed = subprocess.run(
            [sys.executable, "-B", "-c", code],
            cwd=_ROOT,
            check=True,
            capture_output=True,
            text=True,
            timeout=30.0,
        )
        self.assertEqual(completed.stdout.strip(), "0 0 0 0 0 0")
        self.assertEqual(
            sha256(_CONFIG.read_bytes().replace(b"\r\n", b"\n")).hexdigest(),
            source.PREREGISTERED_CONFIG_SHA256,
        )
        self.assertEqual(
            sha256(_CORRECTION_CONFIG.read_bytes().replace(b"\r\n", b"\n")).hexdigest(),
            source.CORRECTION_CONFIG_SHA256,
        )
        source.verify_preregistered_work_preflight_contract()
        self.assertFalse(_RESULT.exists())
        self.assertFalse(_RESERVED.exists())

    def test_geometry_work_ratios_and_reader_are_independent_and_exact(self) -> None:
        config = source.load_preregistered_work_preflight_config()
        for cards, suffix in ((10, "10"), (22, "22"), (25, "25_projection_only")):
            with self.subTest(cards=cards):
                geometry = source.population_geometry(cards)
                self.assertEqual(
                    geometry.source_occupancies,
                    reader.geometry(cards)["source_occupancies"],
                )
                self.assertEqual(
                    source.complete_campaign_work(cards),
                    reader.complete_campaign_work(cards),
                )
                self.assertTrue(
                    all(
                        config[f"complete_campaign_work_{suffix}"][name] == value
                        for name, value in source.complete_campaign_work(cards).items()
                    )
                )
        for phase in source.PHASE_ORDER:
            for cards in source.CALIBRATION_POPULATIONS:
                ratio = source.phase_projection_ratio(phase, cards)
                self.assertEqual(ratio, reader.phase_ratio(phase, cards))
                source_constituents = source.phase_projection_constituents(
                    phase, cards
                )
                reader_constituents = reader.phase_constituents(phase, cards)
                self.assertEqual(source_constituents, reader_constituents)
                for _, numerator, denominator in source_constituents:
                    self.assertLessEqual(
                        numerator * ratio[1], ratio[0] * denominator
                    )
        direct_adjoint_labels = {
            label
            for label, _, _ in source.phase_projection_constituents(
                "direct_adjoint", 22
            )
        }
        self.assertFalse(
            any(label.startswith("chunk_count") for label in direct_adjoint_labels)
        )
        adjoint_rows = source.phase_projection_constituents(
            "adjoint_recurrence_and_signed_sources", 22
        )
        self.assertIn(("chunk_count_family_1_axis_2", 11, 5), adjoint_rows)
        self.assertNotIn(
            "adjoint_source_pairing_visits",
            source._PHASE_WORK_COUNTERS[
                "adjoint_recurrence_and_signed_sources"
            ],
        )
        self.assertIn(
            "adjoint_source_pairing_visits",
            source._PHASE_WORK_COUNTERS[
                "adjoint_source_contract_and_global_tree"
            ],
        )
        assigned = [
            counter
            for counters in source._PHASE_WORK_COUNTERS.values()
            for counter in counters
        ]
        self.assertEqual(len(assigned), len(set(assigned)))
        self.assertEqual(set(assigned), set(source.complete_campaign_work(25)))
        self.assertEqual(
            source.phase_projection_ratio(
                "adjoint_recurrence_and_signed_sources", 22
            ),
            (177_100, 74_613),
        )
        self.assertEqual(
            source.complete_campaign_work(25)["direct_fold_source_unranks"],
            34_003_200,
        )
        self.assertEqual(
            config["complete_campaign_work_25_projection_only"][
                "rejected_direct_fold_source_unranks"
            ],
            1_994_854_400,
        )

    def test_sample_rows_are_sixteen_sorted_unique_and_stable(self) -> None:
        expected_ten_source = (
            0, 30, 55, 63, 75, 128, 133, 138,
            146, 155, 170, 180, 181, 186, 189, 209,
        )
        self.assertEqual(source.sample_rows(10)[0], expected_ten_source)
        for cards in source.CALIBRATION_POPULATIONS:
            source_rows, query_rows = source.sample_rows(cards)
            for rows in (source_rows, query_rows):
                self.assertEqual(len(rows), 16)
                self.assertEqual(rows, tuple(sorted(set(rows))))
                self.assertEqual(rows[0], 0)
            self.assertEqual(source.sample_rows(cards), (source_rows, query_rows))
        with self.assertRaisesRegex(ValueError, "only for calibration"):
            source.sample_rows(25)

    def test_projection_uses_worse_endpoint_exact_ceiling_guard_and_no_float(self) -> None:
        endpoints = {
            10: {phase: 1 for phase in source.PHASE_ORDER},
            22: {phase: 2 for phase in source.PHASE_ORDER},
        }
        projected = source.reconstruct_projection(endpoints)
        self.assertEqual(projected, reader.reconstruct_projection(endpoints))
        direct = next(
            row for row in projected["phase_rows"] if row["phase"] == "direct_query"
        )
        expected10 = 54_264
        expected22 = (2 * 54_264 + 18_564 - 1) // 18_564
        self.assertEqual(direct["candidate_10_ns"], expected10)
        self.assertEqual(direct["candidate_22_ns"], expected22)
        self.assertEqual(direct["upper_ns"], (expected10 * 5 + 3) // 4 + 1_000_000)
        with self.assertRaisesRegex(ValueError, "exactly the 10 and 22"):
            source.reconstruct_projection({10: endpoints[10]})

    def test_population_25_is_rejected_before_any_parent_compiler_call(self) -> None:
        with patch.object(source._consumer, "compile_legal_river_quotient_bridge") as compile_mock:
            with self.assertRaisesRegex(ValueError, "restricted to 10 and 22"):
                source.compile_calibration_fixture(25)
        compile_mock.assert_not_called()


class WorkPreflightKernelAndLedgerTests(unittest.TestCase):
    def test_only_three_direct_kernels_change_and_rank_major_order_is_static(self) -> None:
        parent = source._paired._CUDA_SOURCE
        successor = source.CUDA_SOURCE
        for name, replacement in (
            ("direct_selected_queries_tile", source._DIRECT_QUERY_KERNEL),
            ("direct_selected_fold_tile", source._DIRECT_FOLD_KERNEL),
            ("direct_selected_adjoint_tile", source._DIRECT_ADJOINT_KERNEL),
        ):
            start, stop = source._kernel_span(successor, name)
            self.assertEqual(successor[start:stop].strip(), replacement.strip())
        stripped_parent = parent
        stripped_successor = successor
        for name in (
            "direct_selected_queries_tile",
            "direct_selected_fold_tile",
            "direct_selected_adjoint_tile",
        ):
            start, stop = source._kernel_span(stripped_parent, name)
            stripped_parent = stripped_parent[:start] + stripped_parent[stop:]
            start, stop = source._kernel_span(stripped_successor, name)
            stripped_successor = stripped_successor[:start] + stripped_successor[stop:]
        self.assertEqual(stripped_parent, stripped_successor)
        fold = source._DIRECT_FOLD_KERNEL
        self.assertLess(fold.index("for (long long row"), fold.index("for (int logical"))
        self.assertEqual(fold.count("unrank_mask(row, n, 6)"), 1)
        adjoint = source._DIRECT_ADJOINT_KERNEL
        record_loop = adjoint.index("for (long long record")
        self.assertLess(
            record_loop,
            adjoint.index("for (int feature_index", record_loop),
        )
        self.assertEqual(adjoint.count("query_weight_pair("), 1)
        self.assertEqual(source.cuda_compile_options(), source._paired._NVRTC_OPTIONS)
        self.assertNotIn("--use_fast_math", source.cuda_compile_options())

    def test_canonical_pair_order_controls_reject_all_three_permutations(self) -> None:
        control = source.run_direct_order_controls()
        self.assertTrue(control["all_gates_pass"])
        self.assertTrue(all(control["gates"].values()))
        self.assertEqual(control["canonical_order"], list(range(8)))
        self.assertEqual(control["unrank_counts"]["source_rank_major"], 8)
        self.assertEqual(control["unrank_counts"]["feature_major_mutation"], 64)
        for role in ("source", "query", "feature"):
            self.assertNotEqual(
                control["canonical_digests"][role],
                control["mutation_digests"][role],
            )

    def test_static_source_has_no_25_fixture_or_actual_owner_path(self) -> None:
        text = _SOURCE.read_text(encoding="utf-8")
        tree = ast.parse(text)
        imports = {
            alias.name
            for node in tree.body
            if isinstance(node, (ast.Import, ast.ImportFrom))
            for alias in node.names
        }
        self.assertNotIn("cupy", imports)
        compile_function = text[
            text.index("def compile_calibration_fixture"):
            text.index("_DIRECT_QUERY_KERNEL")
        ]
        self.assertIn("available_cards not in CALIBRATION_POPULATIONS", compile_function)
        self.assertNotIn("compile_consumer_population_fixture(25", text)
        self.assertNotIn("population_geometry(45", text)
        self.assertNotIn("run_actual", text)
        self.assertIn("if not query_weight.all_gates_pass", text)
        self.assertFalse(_RESULT.exists())
        self.assertFalse(_RESERVED.exists())

    def test_phase_ledger_is_an_exact_partition_and_wall_failure_is_typed(self) -> None:
        times = iter((100, 110, 130))
        devices = iter((3, 7))
        ledger = source.PhaseLedger(
            population=10,
            family=source.POPULATION_FAMILIES[0],
            chunks=(17, 3, 11),
            clock_ns=lambda: next(times),
            device_terminal=lambda: next(devices),
        )
        ledger.start(repeat=0, tile=0)
        ledger.switch("forward_source_and_offset", repeat=0, tile=0)
        ledger.add_work("source_pairing_visits", 7)
        rows = ledger.finish()
        self.assertEqual([row.host_ns for row in rows], [10, 20])
        self.assertEqual([row.device_ns for row in rows], [3, 7])
        self.assertEqual(rows[0].host_stop_ns, rows[1].host_start_ns)
        self.assertEqual(sum(row.host_ns for row in rows), 30)
        self.assertEqual(source._sum_work(rows)["source_pairing_visits"], 7)

        semantic = source.PhaseLedger(
            population=10,
            family=source.POPULATION_FAMILIES[0],
            chunks=(17, 3, 11),
            clock_ns=lambda: 0,
        )
        semantic.start(repeat=0, tile=0)
        with self.assertRaisesRegex(ValueError, "another semantic phase"):
            semantic.add_work("source_pairing_visits", 1)
        with self.assertRaisesRegex(ValueError, "semantic transition"):
            semantic.switch("final_release", repeat=0, tile=0)

        wall_times = iter((100, 120))
        wall = source.PhaseLedger(
            population=10,
            family=source.POPULATION_FAMILIES[0],
            chunks=(17, 3, 11),
            clock_ns=lambda: next(wall_times),
            wall_deadline_ns=110,
        )
        wall.start(repeat=0, tile=0)
        with self.assertRaisesRegex(TimeoutError, "population_wall"):
            wall.finish()

    def test_hash_bound_outer_runner_clone_builds_without_mutating_parent(self) -> None:
        ledger = source.PhaseLedger(
            population=10,
            family=source.POPULATION_FAMILIES[0],
            chunks=(17, 3, 11),
            clock_ns=lambda: 0,
        )
        tracker = source._CampaignTracker(ledger, 10)
        before = source._paired._run_device_population
        generated = source._generated_population_runner(tracker)
        self.assertTrue(callable(generated))
        self.assertIs(source._paired._run_device_population, before)
        self.assertEqual(generated.__name__, "_run_device_population")

    def test_exact_cubin_resource_parser_does_not_invent_spill_counts(self) -> None:
        output = """
Resource usage:
 Function direct_selected_queries_tile:
  REG:32 STACK:64 SHARED:0 LOCAL:128 CONSTANT[0]:16
 Function direct_selected_fold_tile:
  REG:64 STACK:1024 SHARED:0 LOCAL:256 CONSTANT[0]:16
 Function direct_selected_adjoint_tile:
  REG:48 STACK:128 SHARED:0 LOCAL:64 CONSTANT[0]:16
"""
        parsed = source.parse_cuobjdump_resource_usage(output)
        self.assertEqual(parsed["direct_selected_fold_tile"]["STACK"], 1024)
        self.assertLessEqual(
            parsed["direct_selected_fold_tile"]["STACK"]
            + parsed["direct_selected_fold_tile"]["LOCAL"],
            source.DIRECT_KERNEL_LOCAL_AND_STACK_LIMIT_BYTES,
        )
        self.assertNotIn("SPILL", parsed["direct_selected_fold_tile"])
        self.assertTrue(all(source.direct_kernel_resource_gates(parsed).values()))
        spilled = deepcopy(parsed)
        spilled["direct_selected_fold_tile"]["STACK"] = (
            source.DIRECT_KERNEL_LOCAL_AND_STACK_LIMIT_BYTES + 1
        )
        self.assertFalse(
            source.direct_kernel_resource_gates(spilled)["local_and_stack_ceiling"]
        )
        register_heavy = deepcopy(parsed)
        register_heavy["direct_selected_queries_tile"]["REG"] = 256
        self.assertFalse(
            source.direct_kernel_resource_gates(register_heavy)["register_ceiling"]
        )
        with self.assertRaisesRegex(ValueError, "omits a direct kernel"):
            source.parse_cuobjdump_resource_usage(
                output.replace(" Function direct_selected_adjoint_tile:", " Function absent:")
            )

        driver = {
            name: {
                "local_size_bytes": row["STACK"] + row["LOCAL"],
                "registers": row["REG"],
                "shared_size_bytes": 0,
                "maximum_threads_per_block": 1024,
            }
            for name, row in parsed.items()
        }
        combined = source.combined_direct_kernel_resource_report(
            parsed,
            driver,
            multiprocessor_count=84,
            maximum_threads_per_multiprocessor=1536,
        )
        self.assertTrue(all(combined["gates"].values()))
        self.assertEqual(
            combined["runtime_residency"]["maximum_resident_threads"],
            129_024,
        )
        driver_breach = deepcopy(driver)
        driver_breach["direct_selected_fold_tile"]["local_size_bytes"] = 4097
        self.assertFalse(
            source.combined_direct_kernel_resource_report(
                parsed,
                driver_breach,
                multiprocessor_count=84,
                maximum_threads_per_multiprocessor=1536,
            )["gates"]["local_and_stack_ceiling"]
        )

    def test_non_elf_compiler_payload_is_rejected_before_module_load(self) -> None:
        class Compiler:
            @staticmethod
            def compile_using_nvrtc(*_args, **_kwargs):
                return b".version 9.0\n", {}

        class Device:
            id = 9191

        class Module:
            loaded = False

            def load(self, _binary):
                type(self).loaded = True

        Function = type("Function", (), {"Module": Module})

        class Cuda:
            compiler = Compiler
            function = Function

            @staticmethod
            def Device():
                return Device()

        class FakeCp:
            cuda = Cuda

        with self.assertRaisesRegex(RuntimeError, "not ELF"):
            source._kernels(FakeCp())
        self.assertFalse(Module.loaded)


class WorkPreflightOwnerReaderTests(unittest.TestCase):
    def test_header_is_durable_before_dependencies_and_exclusive_replay_fails(self) -> None:
        loaded = runner.load_public_config()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "result.jsonl"
            order: list[str] = []

            def config_loader():
                recovery = recover_journal_bytes(path.read_bytes())
                self.assertEqual(len(recovery.records), 1)
                self.assertEqual(recovery.records[0].body.kind.value, "header")
                order.append("config")
                return loaded

            def git_loader():
                self.assertEqual(order, ["config"])
                order.append("git")
                return _git()

            def hashes_loader():
                self.assertEqual(order, ["config", "git"])
                order.append("hashes")
                return runner.dependency_hashes()

            def executor(emit):
                self.assertEqual(order, ["config", "git", "hashes"])
                order.append("executor")
                return _synthetic_events()(emit)

            execution = runner.execute_owner_to_path(
                output_path=path,
                config_loader=config_loader,
                git_loader=git_loader,
                hashes_loader=hashes_loader,
                campaign_executor=executor,
            )
            self.assertEqual(order, ["config", "git", "hashes", "executor"])
            self.assertEqual(execution.terminal["terminal"], "completed_capacity_pass")
            rebound = reader.rebind_work_preflight_journal(path.read_bytes())
            self.assertTrue(rebound.passed)
            self.assertEqual(rebound.terminal, "completed_capacity_pass")
            self.assertEqual(
                len(rebound.phases),
                17
                * len(source.CALIBRATION_POPULATIONS)
                * len(source.POPULATION_FAMILIES),
            )
            self.assertLess(rebound.journal_byte_count, runner.MAXIMUM_ARTIFACT_BYTES)
            with self.assertRaises(FileExistsError):
                runner.execute_owner_to_path(
                    output_path=path,
                    config_loader=lambda: loaded,
                    git_loader=_git,
                    campaign_executor=_synthetic_events(),
                )

    def test_reserved_actual_presence_stops_before_campaign_execution(self) -> None:
        loaded = runner.load_public_config()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "result.jsonl"
            reserved = root / "reserved.jsonl"
            reserved.touch()
            called = False

            def executor(_emit):
                nonlocal called
                called = True
                raise AssertionError("reserved-authority lock admitted execution")

            with patch.object(runner, "_RESERVED", reserved):
                execution = runner.execute_owner_to_path(
                    output_path=path,
                    config_loader=lambda: loaded,
                    git_loader=_git,
                    hashes_loader=runner.dependency_hashes,
                    campaign_executor=executor,
                )
            self.assertFalse(called)
            self.assertEqual(
                execution.terminal["terminal"],
                "infrastructure_failure",
            )

    def test_synthetic_failure_and_wall_are_retained_without_retry(self) -> None:
        loaded = runner.load_public_config()
        cases = []

        def failed(_emit):
            raise RuntimeError("synthetic worker failure")

        cases.append((failed, iter((0, 1)), "infrastructure_failure"))

        def compiler_rejection(emit):
            laboratory = _synthetic_resource_laboratory()
            laboratory["primitive_gates"] = {"synthetic": False}
            emit("laboratory", laboratory)
            return {
                "schema_version": "legal-river-work-preflight-terminal-evidence-v1",
                "terminal": "compiler_or_primitive_rejection",
                "failed_population": None,
                "passed": False,
                "projection": None,
            }

        cases.append((compiler_rejection, iter((0, 1)), "compiler_or_primitive_rejection"))

        def compiler_resource_failure(emit):
            emit(
                "laboratory",
                {
                    "schema_version": "legal-river-work-preflight-laboratory-v1",
                    "kind": "compiler_resource_failure",
                    "runtime": {"cupy_version": "14.0.0"},
                    "stage": "kernel_compile_and_resource_inspection",
                    "reason": "CompilerResourceRejection: synthetic non-ELF payload",
                    "correction_config_sha256": source.CORRECTION_CONFIG_SHA256,
                },
            )
            return {
                "schema_version": "legal-river-work-preflight-terminal-evidence-v1",
                "terminal": "compiler_or_primitive_rejection",
                "failed_population": None,
                "passed": False,
                "projection": None,
            }

        cases.append(
            (
                compiler_resource_failure,
                iter((0, 1)),
                "compiler_or_primitive_rejection",
            )
        )

        def calibration_rejection(emit):
            emit("laboratory", _synthetic_resource_laboratory())
            emit(
                "laboratory",
                {
                    "schema_version": "legal-river-work-preflight-laboratory-v1",
                    "kind": "complete_ten_legacy_direct_byte_identity",
                    "control": {
                        "gates": {"synthetic": False},
                        "all_gates_pass": False,
                    },
                },
            )
            return {
                "schema_version": "legal-river-work-preflight-terminal-evidence-v1",
                "terminal": "calibration_scientific_rejection",
                "failed_population": 10,
                "passed": False,
                "projection": None,
            }

        cases.append(
            (
                calibration_rejection,
                iter((0, 1)),
                "calibration_scientific_rejection",
            )
        )

        def calibration_wall_rejection(emit):
            emit("laboratory", _synthetic_resource_laboratory())
            emit(
                "laboratory",
                {
                    "schema_version": "legal-river-work-preflight-laboratory-v1",
                    "kind": "complete_ten_legacy_direct_byte_identity",
                    "control": {
                        "gates": {"synthetic": True},
                        "all_gates_pass": True,
                    },
                },
            )
            emit(
                "laboratory",
                {
                    "schema_version": "legal-river-work-preflight-laboratory-v1",
                    "kind": "complete_ten_query_weight_control",
                    "gates": {"synthetic": True},
                },
            )
            emit(
                "phase",
                {
                    "schema_version": "legal-river-work-preflight-phase-v1",
                    "ordinal": 0,
                    "population": 22,
                    "family": source.POPULATION_FAMILIES[0],
                    "repeat": 0,
                    "tile": 0,
                    "phase": source.PHASE_ORDER[0],
                    "host_start_ns": 0,
                    "host_stop_ns": 1,
                    "host_ns": 1,
                    "device_ns": 1,
                    "chunks": [32768, 4096, 32768],
                    "work": {},
                },
            )
            emit(
                "laboratory",
                {
                    "schema_version": "legal-river-work-preflight-laboratory-v1",
                    "kind": "calibration_population_wall_failure",
                    "population": 22,
                    "family": source.POPULATION_FAMILIES[0],
                    "elapsed_ns": 90_000_000_001,
                    "limit_ns": 90_000_000_000,
                    "reason": "calibration_population_wall_crossed",
                },
            )
            return {
                "schema_version": "legal-river-work-preflight-terminal-evidence-v1",
                "terminal": "calibration_scientific_rejection",
                "failed_population": 22,
                "passed": False,
                "projection": None,
            }

        cases.append(
            (
                calibration_wall_rejection,
                iter((0, 1)),
                "calibration_scientific_rejection",
            )
        )
        cases.append(
            (
                compiler_rejection,
                iter((0, runner.LABORATORY_WALL_LIMIT_NS + 1)),
                "laboratory_wall_rejection",
            )
        )
        cases.append(
            (
                _synthetic_events(duration_ns=1_000_000),
                iter((0, 1)),
                "completed_capacity_rejection",
            )
        )
        for executor, clock, expected in cases:
            with self.subTest(expected=expected), tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / "result.jsonl"
                execution = runner.execute_owner_to_path(
                    output_path=path,
                    config_loader=lambda: loaded,
                    git_loader=_git,
                    hashes_loader=runner.dependency_hashes,
                    campaign_executor=executor,
                    monotonic_ns=lambda clock=clock: next(clock),
                )
                self.assertEqual(execution.terminal["terminal"], expected)
                rebound = reader.rebind_work_preflight_journal(path.read_bytes())
                self.assertEqual(rebound.terminal, expected)
                self.assertFalse(rebound.passed)

    def test_reader_rejects_every_synthetic_distortion_family(self) -> None:
        loaded = runner.load_public_config()
        cases = {
            "sum": "phase wall identity",
            "work": "executed work ledger",
            "drop": "cover all 16 phases",
            "population25": "25-card or unknown numerical phase",
            "semantic_phase": "another semantic phase",
            "order": "phase semantic transition",
        }
        for mutation, message in cases.items():
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / "result.jsonl"
                runner.execute_owner_to_path(
                    output_path=path,
                    config_loader=lambda: loaded,
                    git_loader=_git,
                    hashes_loader=runner.dependency_hashes,
                    campaign_executor=_synthetic_events(phase_mutation=mutation),
                )
                with self.assertRaisesRegex(ValueError, message):
                    reader.rebind_work_preflight_journal(path.read_bytes())

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "projection.jsonl"
            runner.execute_owner_to_path(
                output_path=path,
                config_loader=lambda: loaded,
                git_loader=_git,
                hashes_loader=runner.dependency_hashes,
                campaign_executor=_synthetic_events(projection_mutation=True),
            )
            with self.assertRaisesRegex(ValueError, "stored projection differs"):
                reader.rebind_work_preflight_journal(path.read_bytes())

        for mutation, message in {
            "raw": "cuobjdump reparse differs",
            "driver": "driver resource copies differ",
            "resident": "runtime residency arithmetic differs",
            "limit": "false compiler gate",
        }.items():
            with (
                self.subTest(resource_mutation=mutation),
                tempfile.TemporaryDirectory() as directory,
            ):
                path = Path(directory) / "resource.jsonl"
                runner.execute_owner_to_path(
                    output_path=path,
                    config_loader=lambda: loaded,
                    git_loader=_git,
                    hashes_loader=runner.dependency_hashes,
                    campaign_executor=_synthetic_events(resource_mutation=mutation),
                )
                with self.assertRaisesRegex(ValueError, message):
                    reader.rebind_work_preflight_journal(path.read_bytes())

    def test_torn_suffix_and_fully_rehashed_pass_mutation_fail_closed(self) -> None:
        loaded = runner.load_public_config()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "result.jsonl"
            runner.execute_owner_to_path(
                output_path=path,
                config_loader=lambda: loaded,
                git_loader=_git,
                hashes_loader=runner.dependency_hashes,
                campaign_executor=_synthetic_events(),
            )
            raw = path.read_bytes()
            with self.assertRaisesRegex(ValueError, "incomplete"):
                reader.rebind_work_preflight_journal(raw[:-1])

            def mutate(payloads):
                payloads[-1]["passed"] = False

            changed = _rewrite_journal(raw, mutate)
            with self.assertRaisesRegex(ValueError, "stored journal pass bit"):
                reader.rebind_work_preflight_journal(changed)

    def test_public_runner_is_no_argument_and_real_artifacts_remain_absent(self) -> None:
        text = _RUNNER.read_text(encoding="utf-8")
        main = text[text.index("def main()") :]
        self.assertIn("if len(sys.argv) != 1", main)
        self.assertIn("DurableEvidenceJournalWriter.create", text)
        self.assertIn("process.kill()", text)
        reader_imports = {
            alias.name
            for node in ast.parse(_READER.read_text(encoding="utf-8")).body
            if isinstance(node, (ast.Import, ast.ImportFrom))
            for alias in node.names
        }
        self.assertNotIn("numpy", reader_imports)
        self.assertNotIn("cupy", reader_imports)
        self.assertFalse(_RESULT.exists())
        self.assertFalse(_RESERVED.exists())


if __name__ == "__main__":
    unittest.main()
