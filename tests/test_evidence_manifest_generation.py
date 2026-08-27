from __future__ import annotations

import importlib.util
import ast
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest import mock


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
TOOL_PATH = REPOSITORY_ROOT / "tools" / "generate_evidence_manifests.py"
SPEC = importlib.util.spec_from_file_location("generate_evidence_manifests", TOOL_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("evidence manifest generator could not be loaded by exact path")
GENERATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GENERATOR)


CURRENT_FILES = (
    ("artifacts/work_preflight/legal_river_quotient_compiled_global_separation_calibration_v2.jsonl", 3299268, "67ac14d408fe8c4299ee603ec1d8c454975094507d4ac28cda73001a42feb90d", "retained_result", "ADR-0462", "compiled_global_separation_calibration_v2"),
    ("artifacts/work_preflight/legal_river_quotient_compiled_global_separation_calibration_v5.attempt.json", 606, "104820d0c67391365d18fb76ca72c704e40e467e2993a96c618d4bf91155600d", "retained_attempt", "ADR-0470", "compiled_global_separation_calibration_v5"),
    ("experiments/configs/legal-river-quotient-compiled-global-separation-calibration-v9-corrected-invocation-authorization.json", 482, "57c869df38c23e4c0520730986a65825f51814915f68cc3e4d32a2f39303a535", "rejected_authorization", "ADR-0473", "compiled_global_separation_calibration_v6"),
    ("artifacts/work_preflight/legal_river_quotient_compiled_global_separation_calibration_v7.jsonl", 7858857, "78b2f8351ca49785756ec336d4f967bcc83a86f9ef96506a6144726cf3b312b3", "retained_result", "ADR-0476", "compiled_global_separation_calibration_v7"),
    ("artifacts/work_preflight/legal_river_quotient_compiled_global_separation_calibration_v7.attempt.json", 1825, "ada1896f0bf63111e0c1e5e707315fbca6c13f6e2b63222805cb5ef4cb9dc413", "retained_attempt", "ADR-0476", "compiled_global_separation_calibration_v7"),
    ("artifacts/work_preflight/legal_river_quotient_compiled_global_separation_calibration_v7.launch-consumed.json", 349, "c3c0a34cba6a677157034d8f8109cf47edea496a33c64992293176d879a2d629", "consumed_launch_marker", "ADR-0476", "compiled_global_separation_calibration_v7"),
)


ABSENCE_PATHS = (
    "artifacts/work_preflight/legal_river_quotient_compiled_global_separation_calibration_v3.jsonl",
    "artifacts/work_preflight/legal_river_quotient_compiled_global_separation_calibration_v4.attempt.json",
    "artifacts/work_preflight/legal_river_quotient_compiled_global_separation_calibration_v4.jsonl",
    "artifacts/work_preflight/legal_river_quotient_compiled_global_separation_calibration_v4.launch-aborted.json",
    "artifacts/work_preflight/legal_river_quotient_compiled_global_separation_calibration_v4.launch-consumed.json",
    "artifacts/work_preflight/legal_river_quotient_compiled_global_separation_calibration_v4.launch-pending.json",
    "artifacts/work_preflight/legal_river_quotient_compiled_global_separation_calibration_v5.jsonl",
    "artifacts/work_preflight/legal_river_quotient_compiled_global_separation_calibration_v5.launch-aborted.json",
    "artifacts/work_preflight/legal_river_quotient_compiled_global_separation_calibration_v5.launch-consumed.json",
    "artifacts/work_preflight/legal_river_quotient_compiled_global_separation_calibration_v5.launch-pending.json",
    "artifacts/work_preflight/legal_river_quotient_compiled_global_separation_calibration_v6.attempt.json",
    "artifacts/work_preflight/legal_river_quotient_compiled_global_separation_calibration_v6.jsonl",
    "artifacts/work_preflight/legal_river_quotient_compiled_global_separation_calibration_v6.launch-aborted.json",
    "artifacts/work_preflight/legal_river_quotient_compiled_global_separation_calibration_v6.launch-consumed.json",
    "artifacts/work_preflight/legal_river_quotient_compiled_global_separation_calibration_v6.launch-pending.json",
    "artifacts/work_preflight/legal_river_quotient_compiled_global_separation_calibration_v7.launch-aborted.json",
    "artifacts/work_preflight/legal_river_quotient_compiled_global_separation_calibration_v7.launch-pending.json",
    "experiments/configs/legal-river-quotient-compiled-global-separation-calibration-v8-corrected-invocation-authorization.json",
)

ABSENCE_ROWS = tuple(
    (item["relative_path"], item["role"], item["governing_decision"], item["owner"])
    for item in GENERATOR.CURRENT_ABSENCE_ENTRIES
)

SAMPLE_ROW = {
    "commit": "1" * 40, "relative_path": "src/pontius/a.py",
    "git_blob_oid": "2" * 40, "raw_sha256": "3" * 64,
    "role": "source_dependency", "phase": "phase-a",
    "governing_decision": "ADR-0001",
}
SAMPLE_STATE = {
    "current_files": list(GENERATOR.CURRENT_FILE_ENTRIES),
    "current_absences": list(GENERATOR.CURRENT_ABSENCE_ENTRIES),
    "snapshots": list(GENERATOR.SNAPSHOTS),
    "blobs": [SAMPLE_ROW],
    "entries_sha256": GENERATOR.historical_entries_sha256([SAMPLE_ROW]),
}


SNAPSHOT_PAIRS = (
    ("88148da07324c13b79c72ea494b14167a975c001", "bc5d1952f690da5d49275344919de36224af26cb"),
    ("08bb6857f47f9669b8f531c65079d4decd52a573", "0d01a4133a4e6ab10467ad0bd298630149702a73"),
    ("3de8e0c9eebf67f2cc2573041242a869468de6e9", "ea80b86ac60cb324e3c18ddad83d8bbba0ade933"),
    ("77feb7c78990ca53e70b1302a6866fe5d781411f", "d26ba99c033875342a652ae352067beee1ca44ee"),
    ("ba6a3418b7c991238cc1a65898fd61fa03b4a3cb", "73b53cb04c91459e8b7028ccd292b972d2dfdf69"),
    ("815d23c115289347e3d4028a4866eb9f87d4669a", "894c026603156df4bba1134ba9861e98bd3a6663"),
    ("5c0c9a401e5f2ebf59296832d954d0075c4d4624", "f3418410c442a4d06c62aba9777def72633ca5c5"),
    ("d633f3fb469a27dee688587293c6efb1d2cb2757", "9c9ff658c2836bde5d1df71f5596d1d6aa1a5bd2"),
    ("cbfa3598f22c7aba7d824f71356ca156f8b01b0c", "9873ff13131c91b058307643dc838a8452268fbb"),
    ("56127da2970f5a8a8056a97a247ebe1fdf4b983b", "ee2437ba1b2efbf2dc4ab3c21bbacdbf26c58648"),
    ("aaca2dda40e29be8ebd091d58e7853bce1c62fd8", "e7bd077f40b1970e9b40a83c891996ab02cd5ffd"),
)


AUTHORIZATION_PATHS = (
    "ARCHITECTURE.md",
    "RISK_REGISTER.md",
    "ROADMAP.md",
    "STATUS.md",
    "docs/decisions/ADR-0475-authorize-one-v7-authorization-phase-calibration-invocation.md",
    "experiments/configs/legal-river-quotient-compiled-global-separation-calibration-v11-authorization-phase-corrected-invocation-authorization.json",
)


class EvidenceManifestGenerationTests(unittest.TestCase):
    def test_current_file_identities_and_absences_are_exact_and_disjoint(self) -> None:
        actual_files = tuple(
            (item["relative_path"], item["byte_length"], item["raw_sha256"], item["role"], item["governing_decision"], item["owner"])
            for item in GENERATOR.CURRENT_FILE_ENTRIES
        )
        self.assertEqual(actual_files, CURRENT_FILES)
        self.assertEqual(tuple(sorted(item["relative_path"] for item in GENERATOR.CURRENT_ABSENCE_ENTRIES)), ABSENCE_PATHS)
        self.assertEqual(len(GENERATOR.CURRENT_ABSENCE_ENTRIES), 18)
        expected_absences = (
            ("artifacts/work_preflight/legal_river_quotient_compiled_global_separation_calibration_v3.jsonl", "closed_result_absence", "ADR-0466", "compiled_global_separation_calibration_v3"),
            ("artifacts/work_preflight/legal_river_quotient_compiled_global_separation_calibration_v4.jsonl", "closed_result_absence", "ADR-0469", "compiled_global_separation_calibration_v4"),
            ("artifacts/work_preflight/legal_river_quotient_compiled_global_separation_calibration_v4.attempt.json", "closed_attempt_absence", "ADR-0469", "compiled_global_separation_calibration_v4"),
            ("artifacts/work_preflight/legal_river_quotient_compiled_global_separation_calibration_v4.launch-pending.json", "closed_launch_pending_absence", "ADR-0469", "compiled_global_separation_calibration_v4"),
            ("artifacts/work_preflight/legal_river_quotient_compiled_global_separation_calibration_v4.launch-consumed.json", "closed_launch_consumed_absence", "ADR-0469", "compiled_global_separation_calibration_v4"),
            ("artifacts/work_preflight/legal_river_quotient_compiled_global_separation_calibration_v4.launch-aborted.json", "closed_launch_aborted_absence", "ADR-0469", "compiled_global_separation_calibration_v4"),
            ("artifacts/work_preflight/legal_river_quotient_compiled_global_separation_calibration_v5.jsonl", "closed_result_absence", "ADR-0470", "compiled_global_separation_calibration_v5"),
            ("artifacts/work_preflight/legal_river_quotient_compiled_global_separation_calibration_v5.launch-pending.json", "closed_launch_pending_absence", "ADR-0470", "compiled_global_separation_calibration_v5"),
            ("artifacts/work_preflight/legal_river_quotient_compiled_global_separation_calibration_v5.launch-consumed.json", "closed_launch_consumed_absence", "ADR-0470", "compiled_global_separation_calibration_v5"),
            ("artifacts/work_preflight/legal_river_quotient_compiled_global_separation_calibration_v5.launch-aborted.json", "closed_launch_aborted_absence", "ADR-0470", "compiled_global_separation_calibration_v5"),
            ("experiments/configs/legal-river-quotient-compiled-global-separation-calibration-v8-corrected-invocation-authorization.json", "rejected_authorization_absence", "ADR-0473", "compiled_global_separation_calibration_v6"),
            ("artifacts/work_preflight/legal_river_quotient_compiled_global_separation_calibration_v6.jsonl", "closed_result_absence", "ADR-0473", "compiled_global_separation_calibration_v6"),
            ("artifacts/work_preflight/legal_river_quotient_compiled_global_separation_calibration_v6.attempt.json", "closed_attempt_absence", "ADR-0473", "compiled_global_separation_calibration_v6"),
            ("artifacts/work_preflight/legal_river_quotient_compiled_global_separation_calibration_v6.launch-pending.json", "closed_launch_pending_absence", "ADR-0473", "compiled_global_separation_calibration_v6"),
            ("artifacts/work_preflight/legal_river_quotient_compiled_global_separation_calibration_v6.launch-consumed.json", "closed_launch_consumed_absence", "ADR-0473", "compiled_global_separation_calibration_v6"),
            ("artifacts/work_preflight/legal_river_quotient_compiled_global_separation_calibration_v6.launch-aborted.json", "closed_launch_aborted_absence", "ADR-0473", "compiled_global_separation_calibration_v6"),
            ("artifacts/work_preflight/legal_river_quotient_compiled_global_separation_calibration_v7.launch-pending.json", "closed_launch_pending_absence", "ADR-0476", "compiled_global_separation_calibration_v7"),
            ("artifacts/work_preflight/legal_river_quotient_compiled_global_separation_calibration_v7.launch-aborted.json", "closed_launch_aborted_absence", "ADR-0476", "compiled_global_separation_calibration_v7"),
        )
        self.assertEqual(ABSENCE_ROWS, expected_absences)
        self.assertFalse(set(path for path, *_ in CURRENT_FILES) & set(ABSENCE_PATHS))
        measured, _ = GENERATOR._measure_current(REPOSITORY_ROOT)
        self.assertEqual(measured, list(GENERATOR.CURRENT_FILE_ENTRIES))

    def test_historical_snapshots_source_seal_group_and_authorization_surface_are_exact(self) -> None:
        state = GENERATOR.derive_manifest_state(REPOSITORY_ROOT)
        self.assertEqual(tuple((item["commit"], item["root_tree_oid"]) for item in GENERATOR.SNAPSHOTS), SNAPSHOT_PAIRS)
        source_rows = [row for row in state["blobs"] if row["phase"] == "v7_source_seal"]
        raw = GENERATOR.read_regular_file_once(REPOSITORY_ROOT / CURRENT_FILES[3][0], maximum_bytes=CURRENT_FILES[3][1])
        header = json.loads(raw.split(b"\n", 1)[0])
        expected_source_paths = tuple(sorted(header["body"]["payload"]["dependency_hashes"]))
        self.assertEqual(len(source_rows), 96)
        self.assertEqual(tuple(row["relative_path"] for row in source_rows), expected_source_paths)
        authorization_rows = [row for row in state["blobs"] if row["phase"] == "v7_live_authorization"]
        self.assertEqual(tuple(row["relative_path"] for row in authorization_rows), AUTHORIZATION_PATHS)
        self.assertEqual(len(authorization_rows), 6)

    def test_historical_entry_digest_is_order_independent_and_covers_every_field(self) -> None:
        first = {"commit": "1" * 40, "relative_path": "src/a.py", "git_blob_oid": "2" * 40, "raw_sha256": "3" * 64, "role": "source_dependency", "phase": "phase-a", "governing_decision": "ADR-0001"}
        second = {**first, "relative_path": "src/b.py", "raw_sha256": "4" * 64}
        digest = GENERATOR.historical_entries_sha256([second, first])
        self.assertEqual(digest, GENERATOR.historical_entries_sha256([first, second]))
        self.assertNotEqual(digest, GENERATOR.historical_entries_sha256([{**first, "role": "test"}, second]))

    def test_retained_v7_constants_lock_the_negative_incomplete_result(self) -> None:
        retained = GENERATOR.RETAINED_V7
        expected = {
            "journal_protocol_sha256": "2dc6cd5636ca56b4b3b17592860737489a2bf1705de79a75bd395fa309b72272",
            "campaign_sha256": "669a959827590b883277840161cd2cdabbed18687ad390f6667bc312362fd23d",
            "record_count": 592, "observation_count": 590, "calibration_cell_count": 569,
            "warmup_cell_count": 480, "measured_labelled_partial_cell_count": 89,
            "scientific_call_count": 569, "authoritative_measured_call_count": 0,
            "terminal": "laboratory_wall_rejected", "passed": False,
            "journal_complete": True, "scientific_campaign_complete": False,
            "historical_reader_commit": "aaca2dda40e29be8ebd091d58e7853bce1c62fd8",
        }
        self.assertEqual({key: retained[key] for key in expected}, expected)

    def test_approval_refusal_and_mismatch_return_before_any_manifest_write(self) -> None:
        with tempfile.TemporaryDirectory(prefix="pontius-task3-approval-") as directory:
            root = Path(directory)
            for supplied in (None, "A" * 64, "0" * 63, "0" * 64):
                with self.subTest(supplied=supplied), self.assertRaises(GENERATOR.GenerationError):
                    GENERATOR.write_manifests(root, SAMPLE_STATE, approved_seed_sha256=supplied)
            self.assertEqual(list(root.iterdir()), [])

    def test_check_is_read_only_when_approval_manifests_are_absent(self) -> None:
        destinations = tuple(REPOSITORY_ROOT / path for path in GENERATOR.MANIFEST_PATHS)
        snapshot = lambda path: (
            path.exists(),
            GENERATOR.read_regular_file_once(path, maximum_bytes=4 * 1024 * 1024) if path.exists() else None,
        )
        before = tuple(snapshot(path) for path in destinations)
        with self.assertRaises(GENERATOR.GenerationError):
            GENERATOR.check_manifests(REPOSITORY_ROOT, SAMPLE_STATE)
        after = tuple(snapshot(path) for path in destinations)
        self.assertEqual(after, before)

    def test_seed_review_is_complete_deterministic_and_binds_the_normalized_digest(self) -> None:
        first = GENERATOR.render_seed_review(SAMPLE_STATE)
        self.assertEqual(first, GENERATOR.render_seed_review(SAMPLE_STATE))
        self.assertIn(f"normalized_sha256\t{SAMPLE_STATE['entries_sha256']}\n".encode("ascii"), first)
        rows = [line for line in first.splitlines() if line.startswith(b"row\t")]
        self.assertEqual(len(rows), len(SAMPLE_STATE["blobs"]))
        # Preapproval intentionally has no literal complete-row count/digest oracle.

    def test_secure_reader_rejects_oversize_symlink_and_final_identity_change(self) -> None:
        with tempfile.TemporaryDirectory(prefix="pontius-task3-reader-") as directory:
            root = Path(directory)
            regular = root / "regular.bin"
            regular.write_bytes(b"evidence")
            self.assertEqual(GENERATOR.read_regular_file_once(regular, maximum_bytes=8), b"evidence")
            with self.assertRaises(GENERATOR.GenerationError):
                GENERATOR.read_regular_file_once(regular, maximum_bytes=7)
            link = root / "link.bin"
            try:
                link.symlink_to(regular)
            except OSError:
                link = None
            if link is not None:
                with self.assertRaises(GENERATOR.GenerationError):
                    GENERATOR.read_regular_file_once(link, maximum_bytes=8)
            identity = GENERATOR._path_handle_identity(os.lstat(regular))
            changed = (*identity[:-1], identity[-1] + 1)
            with mock.patch.object(
                GENERATOR, "_path_handle_identity",
                side_effect=[identity, identity, changed, identity],
            ):
                with self.assertRaises(GENERATOR.GenerationError):
                    GENERATOR.read_regular_file_once(regular, maximum_bytes=8)
            with mock.patch.object(GENERATOR, "_path_handle_identity", side_effect=[identity, changed]):
                with self.assertRaises(GENERATOR.GenerationError):
                    GENERATOR.read_regular_file_once(regular, maximum_bytes=8)
            handle_identity = GENERATOR._identity(os.lstat(regular))
            with mock.patch.object(GENERATOR, "_identity", side_effect=[handle_identity, (*handle_identity[:-1], handle_identity[-1] + 1)]):
                with self.assertRaises(GENERATOR.GenerationError):
                    GENERATOR.read_regular_file_once(regular, maximum_bytes=8)

    def test_secure_reader_factory_rejects_link_components_and_reads_once(self) -> None:
        reader = GENERATOR.tool_secure_reader_factory()
        self.assertIs(reader.read_regular_once.__self__, reader)
        with tempfile.TemporaryDirectory(prefix="pontius-task3-reader-factory-") as directory:
            root = Path(directory)
            regular = root / "regular.bin"
            regular.write_bytes(b"evidence")
            with mock.patch.object(GENERATOR.os, "read", wraps=os.read) as read_call:
                self.assertEqual(reader.read_regular_once(regular, maximum_bytes=8), b"evidence")
                self.assertEqual(read_call.call_count, 1)
            linked_parent = root / "linked-parent"
            actual_parent = root / "actual-parent"
            actual_parent.mkdir()
            (actual_parent / "child.bin").write_bytes(b"evidence")
            try:
                linked_parent.symlink_to(actual_parent, target_is_directory=True)
            except OSError:
                linked_parent = None
            if linked_parent is not None:
                with self.assertRaises(GENERATOR.GenerationError):
                    reader.read_regular_once(linked_parent / "child.bin", maximum_bytes=8)

    def test_selected_class_scope_excludes_other_classes_and_broad_literals(self) -> None:
        source = '''
from pontius import selected_owner, unrelated_owner
CONFIG = "experiments/configs/selected.json"
UNRELATED = "artifacts/work_preflight/unrelated.json"
class Selected:
    owner = selected_owner
    config = CONFIG
class Other:
    owner = unrelated_owner
    artifact = UNRELATED
    test = "tests/unrelated.py"
'''
        tracked = {
            "src/pontius/__init__.py", "src/pontius/selected_owner.py",
            "src/pontius/unrelated_owner.py", "experiments/configs/selected.json",
            "artifacts/work_preflight/unrelated.json", "tests/unrelated.py",
        }
        scope = GENERATOR._selected_class_scope(ast.parse(source), "Selected")
        reached = GENERATOR._import_paths(scope, "tests/selected.py", tracked)
        reached |= GENERATOR._literal_paths(scope, source, tracked)
        self.assertIn("src/pontius/selected_owner.py", reached)
        self.assertIn("experiments/configs/selected.json", reached)
        self.assertNotIn("src/pontius/unrelated_owner.py", reached)
        self.assertNotIn("artifacts/work_preflight/unrelated.json", reached)
        self.assertNotIn("tests/unrelated.py", reached)

    def test_phase_boundary_seeds_selected_class_named_modules_without_transitive_walk(self) -> None:
        class Git:
            def tracked_paths(self, commit: str) -> tuple[str, ...]:
                return (
                    "tests/selected.py", "docs/decisions/ADR-1.md",
                    "src/pontius/__init__.py", "src/pontius/owner.py",
                    "src/pontius/transitive.py",
                )
            def show_blob(self, commit: str, path: str) -> bytes:
                blobs = {
                    "tests/selected.py": b"from pontius import owner\nclass Selected:\n    subject = owner\n",
                    "src/pontius/owner.py": b"from pontius import transitive\n",
                }
                return blobs[path]
        phase = {
            "commit": "1" * 40, "selected_test": "tests/selected.py",
            "selected_class": "Selected", "decision_path": "docs/decisions/ADR-1.md",
        }
        self.assertEqual(
            GENERATOR._phase_paths(Git(), phase),
            ("docs/decisions/ADR-1.md", "src/pontius/__init__.py", "src/pontius/owner.py", "tests/selected.py"),
        )

    def test_import_forms_resolve_package_submodules_and_relative_submodules(self) -> None:
        tracked = {
            "src/pontius/__init__.py", "src/pontius/foo.py",
            "src/pontius/pkg/__init__.py", "src/pontius/pkg/bar.py",
        }
        absolute = GENERATOR._import_paths(ast.parse("from pontius import foo"), "tests/t.py", tracked)
        relative = GENERATOR._import_paths(ast.parse("from . import bar"), "src/pontius/pkg/owner.py", tracked)
        self.assertEqual(absolute, {"src/pontius/__init__.py", "src/pontius/foo.py"})
        self.assertEqual(relative, {"src/pontius/pkg/__init__.py", "src/pontius/pkg/bar.py"})

    def test_dynamic_dash_c_programs_are_exact_and_fail_closed(self) -> None:
        tracked = {"src/pontius/runner.py"}
        direct = ast.parse("subprocess.run([python, '-c', \"from pontius import runner\"])")
        named = ast.parse("VALUE = 1\nprogram = f\"from pontius import runner; value={VALUE!r}\"\nsubprocess.run([python, '-c', program])")
        self.assertEqual(GENERATOR._dynamic_program_imports(direct, "tests/t.py", tracked), tracked)
        self.assertEqual(GENERATOR._dynamic_program_imports(named, "tests/t.py", tracked), tracked)
        for source in (
            "subprocess.run([python, '-c', make_program()])",
            "program = 'from pontius import ' + name\nsubprocess.run([python, '-c', program])",
            "subprocess.run([python, '-c', 'from pontius import'])",
            "subprocess.run([python, '-c', 'import pontius.missing'])",
        ):
            with self.subTest(source=source), self.assertRaises(GENERATOR.GenerationError):
                GENERATOR._dynamic_program_imports(ast.parse(source), "tests/t.py", tracked)

    def test_dynamic_dash_c_resolution_is_lexical_and_accepts_named_argv(self) -> None:
        source = '''
class Selected:
    def first(self):
        program = "import pontius.alpha"
        argv = [python, "-B", "-c", program]
        subprocess.run(argv)
    def second(self):
        program = "import pontius.beta"
        argv = (python, "-P", "-c", program)
        subprocess.run(argv)
'''
        tracked = {"src/pontius/alpha.py", "src/pontius/beta.py"}
        self.assertEqual(
            GENERATOR._dynamic_program_imports(ast.parse(source), "tests/t.py", tracked),
            tracked,
        )

    def test_dynamic_dash_c_resolves_fixed_fstrings_and_concatenation(self) -> None:
        source = '''
ALPHA = "alpha"
PREFIX = "import pontius."
class Selected:
    def fstring_program(self):
        program = f"import pontius.{ALPHA}"
        subprocess.run([python, "-c", program])
    def concatenated_program(self):
        module = "beta"
        program = PREFIX + module
        argv = [python, "-c", program]
        subprocess.run(argv)
'''
        tracked = {"src/pontius/alpha.py", "src/pontius/beta.py"}
        self.assertEqual(
            GENERATOR._dynamic_program_imports(ast.parse(source), "tests/t.py", tracked),
            tracked,
        )

    def test_dynamic_dash_c_allows_fixed_enclosing_path_constants(self) -> None:
        source = '''
from pathlib import Path
ROOT = Path(__file__).parents[1]
LAUNCHER = ROOT / "run_selected.py"
class Selected:
    def probe(self):
        program = f"import runpy; runpy.run_path({str(LAUNCHER)!r}); import pontius.alpha"
        subprocess.run([python, "-c", program])
'''
        self.assertEqual(
            GENERATOR._dynamic_program_imports(
                ast.parse(source), "tests/t.py", {"src/pontius/alpha.py"}
            ),
            {"src/pontius/alpha.py"},
        )

    def test_dynamic_dash_c_allows_repeated_symbolic_context_targets(self) -> None:
        source = '''
from pathlib import Path
import tempfile
class Selected:
    def probe(self):
        with tempfile.TemporaryDirectory() as directory:
            Path(directory)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            program = f"value={str(root)!r}; import pontius.alpha"
            subprocess.run([python, "-c", program])
'''
        self.assertEqual(
            GENERATOR._dynamic_program_imports(
                ast.parse(source), "tests/t.py", {"src/pontius/alpha.py"}
            ),
            {"src/pontius/alpha.py"},
        )

    def test_dynamic_dash_c_rejects_symbolic_import_targets(self) -> None:
        programs = (
            'program = f"import {MODULE}"',
            'program = f"from {MODULE} import runner"',
            'program = f"import importlib; importlib.import_module({MODULE!r})"',
            'program = f"__import__({MODULE!r})"',
            'program = f"import {MODULE:.1}"',
        )
        tracked = {"src/pontius/alpha.py"}
        for assignment in programs:
            source = f'''\
from pathlib import Path
MODULE = Path("pontius.alpha").name
class Selected:
    def probe(self):
        {assignment}
        subprocess.run([python, "-c", program])
'''
            with self.subTest(assignment=assignment), self.assertRaises(
                GENERATOR.GenerationError
            ):
                GENERATOR._dynamic_program_imports(ast.parse(source), "tests/t.py", tracked)

    def test_dynamic_dash_c_resolves_exact_builtin_import_target(self) -> None:
        source = '''
MODULE = "pontius.alpha"
class Selected:
    def probe(self):
        program = f"__import__({MODULE!r})"
        subprocess.run([python, "-c", program])
'''
        self.assertEqual(
            GENERATOR._dynamic_program_imports(
                ast.parse(source), "tests/t.py", {"src/pontius/alpha.py"}
            ),
            {"src/pontius/alpha.py"},
        )

    def test_dynamic_dash_c_symbolic_nonimport_context_cannot_collide_with_marker(self) -> None:
        source = '''
from pathlib import Path
MODULE = "pontius.alpha"
LAUNCHER = Path("run-selected.py").name
class Selected:
    def probe(self):
        program = f"sentinel='__pontius_fixed_value__'; launch={LAUNCHER!r}; import a__pontius_symbolic__; import b__pontius_symbolic__; import {MODULE}"
        subprocess.run([python, "-c", program])
'''
        self.assertEqual(
            GENERATOR._dynamic_program_imports(
                ast.parse(source), "tests/t.py", {"src/pontius/alpha.py"}
            ),
            {"src/pontius/alpha.py"},
        )

    def test_dynamic_dash_c_rejects_ambiguous_dynamic_reassigned_and_branch_values(self) -> None:
        cases = (
            '''
class Selected:
    def dynamic(self, module):
        program = f"import pontius.{module}"
        subprocess.run([python, "-c", program])
''',
            '''
class Selected:
    def reassigned_program(self):
        program = "import pontius.alpha"
        program = "import pontius.beta"
        subprocess.run([python, "-c", program])
''',
            '''
class Selected:
    def reassigned_import_target(self):
        module = "alpha"
        module = "beta"
        program = f"import pontius.{module}"
        subprocess.run([python, "-c", program])
''',
            '''
class Selected:
    def branch_dependent(self, flag):
        if flag:
            program = "import pontius.alpha"
        else:
            program = "import pontius.beta"
        subprocess.run([python, "-c", program])
''',
            '''
class Selected:
    def reassigned_argv(self):
        program = "import pontius.alpha"
        argv = [python, "-c", program]
        argv = [python, "-c", "import pontius.beta"]
        subprocess.run(argv)
''',
            '''
class Selected:
    def unresolved_named_argv(self):
        program = "import pontius.alpha"
        argv = make_argv("-c", program)
        subprocess.run(argv)
''',
            '''
class Selected:
    def assigned_after_use(self):
        subprocess.run(argv)
        argv = [python, "-c", "import pontius.alpha"]
''',
        )
        tracked = {"src/pontius/alpha.py", "src/pontius/beta.py"}
        for source in cases:
            with self.subTest(source=source), self.assertRaises(GENERATOR.GenerationError):
                GENERATOR._dynamic_program_imports(ast.parse(source), "tests/t.py", tracked)

    def test_historical_identity_collisions_fail_closed(self) -> None:
        rows: list[dict[str, object]] = []
        identities: set[tuple[str, str]] = set()
        GENERATOR._append_unique_row(rows, identities, SAMPLE_ROW)
        with self.assertRaises(GENERATOR.GenerationError):
            GENERATOR._append_unique_row(rows, identities, dict(SAMPLE_ROW))

    def test_absent_check_and_invalid_write_approval_do_not_derive(self) -> None:
        with mock.patch.object(GENERATOR, "derive_manifest_state", side_effect=AssertionError("walked")):
            self.assertEqual(GENERATOR.main([]), 2)
            self.assertEqual(GENERATOR.main(["--write"]), 2)
            self.assertEqual(GENERATOR.main(["--write", "--approved-seed-sha256", "A" * 64]), 2)

    def test_emit_seed_review_validates_output_before_derivation(self) -> None:
        with mock.patch.object(GENERATOR, "derive_manifest_state", side_effect=AssertionError("walked")):
            self.assertEqual(GENERATOR.main(["--emit-seed-review", "relative.txt"]), 2)
            self.assertEqual(GENERATOR.main(["--emit-seed-review", str(REPOSITORY_ROOT / "review.txt")]), 2)

    def test_manifest_and_seed_review_destinations_reject_nonregular_targets(self) -> None:
        with tempfile.TemporaryDirectory(prefix="pontius-task3-destinations-") as directory:
            root = Path(directory).resolve()
            architecture = root / "docs" / "architecture"
            architecture.mkdir(parents=True)
            (root / GENERATOR.MANIFEST_PATHS[0]).mkdir()
            with self.assertRaises(GENERATOR.GenerationError):
                GENERATOR._verified_destinations(root)
            output = root / "seed-review.txt"
            output.mkdir()
            with self.assertRaises(GENERATOR.GenerationError):
                GENERATOR._validated_seed_review_output(REPOSITORY_ROOT, output)

    def test_git_cache_revalidates_executable_and_bounded_runner_failures(self) -> None:
        git = object.__new__(GENERATOR._Git)
        git.root = REPOSITORY_ROOT
        git.executable = GENERATOR.GIT_EXECUTABLE
        git.executable_identity = GENERATOR._identity(os.lstat(git.executable))
        git.environment = GENERATOR.git_environment(Path(tempfile.gettempdir()).resolve())
        git._cache = {("cached",): b"value"}
        with mock.patch.object(GENERATOR, "_validated_bound_executable", side_effect=GENERATOR.GenerationError("replaced")):
            with self.assertRaises(GENERATOR.GenerationError):
                git._run(("cached",), maximum_stdout=8)
        with mock.patch.object(GENERATOR, "_validated_bound_executable", return_value=(git.executable, git.executable_identity)):
            git._cache = {("cached",): b"12345"}
            with self.assertRaises(GENERATOR.GenerationError):
                git._run(("cached",), maximum_stdout=4)

        class Process:
            def __init__(self, stdout: bytes, stderr: bytes, code: int = 0, timeout: bool = False) -> None:
                self.stdout, self.stderr = io.BytesIO(stdout), io.BytesIO(stderr)
                self.returncode, self.timeout = code, timeout
                self.killed = False
            def wait(self, timeout: float | None = None) -> int:
                if self.timeout and not self.killed:
                    raise GENERATOR.subprocess.TimeoutExpired("git", timeout)
                return self.returncode
            def kill(self) -> None:
                self.killed = True
            def poll(self) -> int | None:
                return self.returncode if not self.timeout or self.killed else None

        for name, process, stdout_cap, stderr_cap in (
            ("stdout", Process(b"12345", b""), 4, 4),
            ("stderr", Process(b"", b"12345"), 4, 4),
            ("timeout", Process(b"", b"", timeout=True), 4, 4),
            ("nonzero", Process(b"", b"bad", code=1), 4, 4),
        ):
            with self.subTest(name=name), self.assertRaises(GENERATOR.GenerationError):
                GENERATOR._collect_bounded_process(process, command="git", stdout_limit=stdout_cap, stderr_limit=stderr_cap, timeout=0.01)

        successful = Process(b"ok", b"")
        git._cache = {}
        with mock.patch.object(GENERATOR, "_validated_bound_executable", return_value=(git.executable, git.executable_identity)), mock.patch.object(
            GENERATOR.subprocess, "Popen", return_value=successful
        ) as popen:
            self.assertEqual(git._run(("show", "commit:path", "--"), maximum_stdout=4), b"ok")
        positional, keyword = popen.call_args
        self.assertEqual(positional[0], [str(git.executable), "show", "commit:path", "--"])
        self.assertEqual(keyword["cwd"], git.root)
        self.assertIs(keyword["env"], git.environment)
        self.assertIs(keyword["stdin"], GENERATOR.subprocess.DEVNULL)
        self.assertFalse(keyword["shell"])
        with mock.patch.object(git, "_run", return_value=b"not-an-oid\n"):
            with self.assertRaises(GENERATOR.GenerationError):
                git._oid(("rev-parse", "bad"))

    def test_git_environment_is_fresh_literal_and_replacement_disabled(self) -> None:
        with tempfile.TemporaryDirectory(prefix="pontius-task3-git-home-") as directory:
            environment = GENERATOR.git_environment(Path(directory))
        git_values = {key: value for key, value in environment.items() if key.upper().startswith("GIT_")}
        self.assertEqual(git_values, {
            "GIT_CONFIG_GLOBAL": "NUL" if os.name == "nt" else "/dev/null",
            "GIT_CONFIG_NOSYSTEM": "1", "GIT_LITERAL_PATHSPECS": "1", "GIT_NO_REPLACE_OBJECTS": "1",
        })


if __name__ == "__main__":
    unittest.main(verbosity=2)
