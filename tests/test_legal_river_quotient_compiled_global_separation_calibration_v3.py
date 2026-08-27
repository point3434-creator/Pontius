from __future__ import annotations

import ast
from collections import defaultdict
from dataclasses import asdict
from hashlib import sha256
import json
import os
from pathlib import Path
import re
import tempfile
import unittest
from unittest.mock import patch

from pontius import legal_river_quotient_compiled_global_separation_calibration as parent_science
from pontius import legal_river_quotient_compiled_global_separation_calibration_runner as parent
from pontius import legal_river_quotient_compiled_global_separation_calibration_v3 as science
from pontius import legal_river_quotient_compiled_global_separation_calibration_v3_runner as successor
from pontius import legal_river_quotient_compiled_global_separation_calibration_v3_result as reader
from pontius.legal_river_quotient_compiled_global_separation_calibration_v2_outcome import (
    assess_compiled_calibration_v2_outcome_file,
)


ROOT = Path(__file__).parents[1]
CONFIG = ROOT / successor.RECOVERY_CONFIG_RELATIVE_PATH
RESULT = ROOT / successor.RESULT_RELATIVE_PATH
SOURCE_SEAL_ADR = (
    ROOT / "docs/decisions/ADR-0465-source-seal-the-kernel-launch-arity-successor.md"
)
LAUNCHER = ROOT / "run_legal_river_quotient_compiled_global_separation_calibration_v3.py"


def _canonical_lf(raw: bytes) -> bytes:
    return raw.replace(bytes((13, 10)), bytes((10,)))


def _independent_cuda_arities(text: str) -> dict[str, int]:
    marker = 'extern "C" __global__ void '
    cursor = 0
    rows: dict[str, int] = {}
    while True:
        start = text.find(marker, cursor)
        if start < 0:
            break
        name_start = start + len(marker)
        open_paren = text.find("(", name_start)
        close_paren = text.find(") {", open_paren)
        if open_paren < 0 or close_paren < 0:
            raise AssertionError("independent CUDA declaration parse failed")
        name = text[name_start:open_paren].strip()
        parameters = text[open_paren + 1 : close_paren].strip()
        if name in rows:
            raise AssertionError("duplicate CUDA declaration")
        rows[name] = 0 if not parameters else parameters.count(",") + 1
        cursor = close_paren + 3
    return rows


def _function_ancestor(node: ast.AST, parents: dict[ast.AST, ast.AST]) -> ast.FunctionDef:
    cursor = parents[node]
    while not isinstance(cursor, ast.FunctionDef):
        cursor = parents[cursor]
    return cursor


def _possible_tuple_lengths(
    expression: ast.AST,
    assignments: dict[str, list[ast.AST]],
    active: frozenset[str] = frozenset(),
) -> set[int]:
    if isinstance(expression, (ast.Tuple, ast.List)):
        return {len(expression.elts)}
    if isinstance(expression, ast.BinOp) and isinstance(expression.op, ast.Add):
        return {
            left + right
            for left in _possible_tuple_lengths(expression.left, assignments, active)
            for right in _possible_tuple_lengths(expression.right, assignments, active)
        }
    if isinstance(expression, ast.Name):
        if expression.id in active or expression.id not in assignments:
            raise AssertionError(f"unresolved launch tuple: {expression.id}")
        return set().union(
            *(
                _possible_tuple_lengths(value, assignments, active | {expression.id})
                for value in assignments[expression.id]
            )
        )
    raise AssertionError(f"unsupported launch tuple expression: {ast.dump(expression)}")


def _possible_kernel_names(expression: ast.AST) -> set[str]:
    if isinstance(expression, ast.Constant) and isinstance(expression.value, str):
        return {expression.value}
    if isinstance(expression, ast.IfExp):
        return _possible_kernel_names(expression.body) | _possible_kernel_names(
            expression.orelse
        )
    raise AssertionError(f"unsupported kernel expression: {ast.dump(expression)}")


def _independent_launch_mismatches(
    host_text: str, cuda_text: str
) -> tuple[int, list[tuple[int, str, int, int]]]:
    tree = ast.parse(host_text)
    parents = {
        child: node
        for node in ast.walk(tree)
        for child in ast.iter_child_nodes(node)
    }
    arities = _independent_cuda_arities(cuda_text)
    calls = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "_launch"
    ]
    mismatches = []
    for call in calls:
        if len(call.args) != 4:
            raise AssertionError("launch call does not use the frozen four-field helper")
        function = _function_ancestor(call, parents)
        assignments: dict[str, list[ast.AST]] = defaultdict(list)
        for node in ast.walk(function):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        assignments[target.id].append(node.value)
        names = _possible_kernel_names(call.args[1])
        counts = _possible_tuple_lengths(call.args[3], assignments)
        for name in names:
            if name not in arities:
                mismatches.append((call.lineno, name, -1, min(counts)))
                continue
            for count in counts:
                if count != arities[name]:
                    mismatches.append((call.lineno, name, arities[name], count))
    return len(calls), mismatches


class CompiledGlobalSeparationCalibrationV3Tests(unittest.TestCase):
    def test_config_consumed_artifact_and_claims_are_exact(self) -> None:
        self.assertEqual(
            sha256(_canonical_lf(CONFIG.read_bytes())).hexdigest(),
            successor.RECOVERY_CONFIG_SHA256,
        )
        config = json.loads(CONFIG.read_text(encoding="utf-8"))
        outcome = assess_compiled_calibration_v2_outcome_file()
        self.assertEqual(
            config["unchanged_boundary"]["consumed_v2_result_raw_sha256"],
            "67ac14d408fe8c4299ee603ec1d8c454975094507d4ac28cda73001a42feb90d",
        )
        self.assertEqual(config["pre_seal_control_finding"]["declared_parameter_count"], 10)
        self.assertEqual(config["pre_seal_control_finding"]["host_argument_count"], 11)
        self.assertEqual(
            config["pre_seal_control_finding"]["extraneous_argument_expression"],
            "np.uint64(scan_count)",
        )
        self.assertEqual(outcome.failing_kernel, "direct_prices_rrns_batch")
        self.assertIsNone(config["claims"]["candidate_selected"])
        self.assertFalse(RESULT.exists())

    def test_effective_science_is_the_exact_frozen_delta(self) -> None:
        parent = _canonical_lf(Path(parent_science.__file__).read_bytes()).decode("utf-8")
        effective = science.effective_scientific_source_text()
        self.assertEqual(
            sha256(parent.encode("utf-8")).hexdigest(),
            science.PARENT_SOURCE_CANONICAL_LF_SHA256,
        )
        old = science._OLD_TIMED_DIRECT_ARGUMENTS
        new = science._NEW_TIMED_DIRECT_ARGUMENTS
        self.assertEqual(parent.count(old), 1)
        self.assertNotIn(new, parent)
        expected = parent.replace(old, new, 1).replace(
            science._OLD_SELECTED_LEAF_ARGUMENTS,
            science._NEW_SELECTED_LEAF_ARGUMENTS,
            1,
        )
        self.assertEqual(effective, expected)
        self.assertEqual(
            sha256(effective.encode("utf-8")).hexdigest(),
            science.EFFECTIVE_SCIENTIFIC_SOURCE_SHA256,
        )
        self.assertEqual(parent_science.CUDA_SOURCE_SHA256, science.CUDA_SOURCE_SHA256)
        self.assertEqual(parent_science.CUDA_SOURCE, science.CUDA_SOURCE)

    def test_independent_all_launch_site_arity_audit_and_mutations(self) -> None:
        effective = science.effective_scientific_source_text()
        count, mismatches = _independent_launch_mismatches(effective, science.CUDA_SOURCE)
        self.assertEqual(count, 46)
        self.assertEqual(mismatches, [])
        removed = effective.replace(
            "                        np.uint64(scan_count),\n",
            "",
            1,
        )
        self.assertNotEqual(removed, effective)
        self.assertEqual(
            _independent_launch_mismatches(removed, science.CUDA_SOURCE)[1],
            [(4221, "direct_prices_rrns_batch", 9, 8)],
        )
        restored = effective.replace(
            science._NEW_SELECTED_LEAF_ARGUMENTS,
            science._OLD_SELECTED_LEAF_ARGUMENTS,
            1,
        )
        self.assertEqual(
            _independent_launch_mismatches(restored, science.CUDA_SOURCE)[1],
            [(4169, "evaluate_selected_leaves_rrns_batch", 10, 11)],
        )
        changed_cuda = science.CUDA_SOURCE.replace(
            "int cards, unsigned long long source_count,\n"
            "    const unsigned long long *moduli",
            "int cards, const unsigned long long *moduli",
            1,
        )
        self.assertNotEqual(changed_cuda, science.CUDA_SOURCE)
        self.assertTrue(_independent_launch_mismatches(effective, changed_cuda)[1])

    def test_signature_manifest_and_central_guard_fail_before_dispatch(self) -> None:
        contract = science.launch_arity_contract()
        self.assertEqual(contract["kernel_count"], 28)
        self.assertEqual(
            tuple(contract["kernel_signatures"]["direct_prices_rrns_batch"]),
            (
                "h",
                "base",
                "prices",
                "cards",
                "source_count",
                "moduli",
                "channels",
                "channel_count",
                "status",
            ),
        )
        calls = []

        def fake(context, kernel, count, arguments):
            calls.append((context, kernel, count, arguments))

        arguments = tuple(object() for _ in range(9))
        with patch.object(science, "_ORIGINAL_LAUNCH", fake):
            science._guarded_launch("context", "direct_prices_rrns_batch", 5, arguments)
            with self.assertRaisesRegex(parent_science.CalibrationFailure, "declares 9"):
                science._guarded_launch(
                    "context", "direct_prices_rrns_batch", 5, arguments[:-1]
                )
        self.assertEqual(calls, [("context", "direct_prices_rrns_batch", 5, arguments)])

    def test_overlay_changes_and_restores_both_parent_authorities(self) -> None:
        launch = parent_science._launch
        cell = parent_science._run_calibration_cell
        with science._installed_launch_arity_overlay():
            self.assertIs(parent_science._launch, science._guarded_launch)
            self.assertIs(parent_science._run_calibration_cell, science._RUN_CALIBRATION_CELL)
        self.assertIs(parent_science._launch, launch)
        self.assertIs(parent_science._run_calibration_cell, cell)

    def test_fresh_owner_bindings_alias_and_reader_constants_restore(self) -> None:
        original = {name: getattr(parent, name) for name in successor._PARENT_BINDINGS}
        old_alias = __import__(successor._PARENT_SCIENCE_MODULE_KEY, fromlist=["*"])
        with successor.configured_parent() as engine:
            self.assertEqual(engine.RESULT_PATH, RESULT)
            self.assertEqual(engine.SCIENTIFIC_MODULE, successor.SCIENTIFIC_MODULE)
            self.assertEqual(engine.PREREGISTRATION_COMMIT, successor.PREREGISTRATION_COMMIT)
            with successor._fresh_scientific_module_alias():
                self.assertIs(
                    __import__(successor._PARENT_SCIENCE_MODULE_KEY, fromlist=["*"]),
                    science,
                )
            self.assertIs(
                __import__(successor._PARENT_SCIENCE_MODULE_KEY, fromlist=["*"]),
                old_alias,
            )
        for name, value in original.items():
            self.assertEqual(getattr(parent, name), value)
        self.assertEqual(reader.DEPENDENCY_RELATIVE_PATHS, successor.DEPENDENCY_RELATIVE_PATHS)

    def test_source_probe_is_real_post_scrub_and_nonmutating(self) -> None:
        if not SOURCE_SEAL_ADR.exists():
            self.skipTest("ADR-0464 is written after source controls settle")
        before = dict(os.environ)
        probe = successor.source_seal_probe(sha256(b"adr0463-source-seal").hexdigest())
        self.assertIsNone(probe["relative_git_resolution"])
        self.assertTrue(probe["environment_replaced"])
        self.assertEqual(probe["kernel_count"], 28)
        self.assertFalse(probe["compiler_executed"])
        self.assertFalse(probe["cupy_scientific_imported"])
        self.assertFalse(probe["device_queried"])
        self.assertTrue(probe["fresh_result_absent"])
        self.assertEqual(dict(os.environ), before)

    def test_synthetic_terminal_is_exclusive_and_independently_readable(self) -> None:
        if not SOURCE_SEAL_ADR.exists():
            self.skipTest("ADR-0464 is written after source controls settle")

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
        before = asdict(assess_compiled_calibration_v2_outcome_file())
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "synthetic-v3.jsonl"
            with successor.configured_parent() as engine:
                execution = engine.execute_owner_to_path(
                    output_path=path,
                    campaign_executor=campaign,
                    monotonic_ns=lambda: next(ticks),
                )
            self.assertFalse(execution.terminal["passed"])
            assessed = reader.assess_calibration_bytes(path.read_bytes())
            self.assertFalse(assessed.passed)
            self.assertEqual(assessed.terminal, "compiler_rejected")
            with self.assertRaises(FileExistsError):
                with successor.configured_parent() as engine:
                    engine.execute_owner_to_path(
                        output_path=path,
                        campaign_executor=campaign,
                        monotonic_ns=lambda: 1,
                    )
            mutated = path.read_bytes().replace(b"source_count", b"source_c0unt", 1)
            self.assertNotEqual(mutated, path.read_bytes())
            with self.assertRaises(ValueError):
                reader.assess_calibration_bytes(mutated)
        self.assertEqual(asdict(assess_compiled_calibration_v2_outcome_file()), before)

    def test_launcher_dependencies_and_result_absence(self) -> None:
        self.assertTrue(LAUNCHER.is_file())
        text = LAUNCHER.read_text(encoding="utf-8")
        self.assertIn("main", text)
        self.assertIn("SystemExit", text)
        self.assertIn(
            "docs/decisions/ADR-0465-source-seal-the-kernel-launch-arity-successor.md",
            successor.DEPENDENCY_RELATIVE_PATHS,
        )
        self.assertNotEqual(successor.PROTOCOL_SHA256, parent.PROTOCOL_SHA256)
        self.assertNotEqual(successor.CAMPAIGN_SHA256, parent.CAMPAIGN_SHA256)
        self.assertFalse(RESULT.exists())


if __name__ == "__main__":
    unittest.main()
