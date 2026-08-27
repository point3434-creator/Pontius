from __future__ import annotations

import importlib.util
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
    @classmethod
    def setUpClass(cls) -> None:
        cls.state = GENERATOR.derive_manifest_state(REPOSITORY_ROOT)

    def test_current_file_identities_and_absences_are_exact_and_disjoint(self) -> None:
        actual_files = tuple(
            (item["relative_path"], item["byte_length"], item["raw_sha256"], item["role"], item["governing_decision"], item["owner"])
            for item in GENERATOR.CURRENT_FILE_ENTRIES
        )
        self.assertEqual(actual_files, CURRENT_FILES)
        self.assertEqual(tuple(sorted(item["relative_path"] for item in GENERATOR.CURRENT_ABSENCE_ENTRIES)), ABSENCE_PATHS)
        self.assertEqual(len(GENERATOR.CURRENT_ABSENCE_ENTRIES), 18)
        self.assertFalse(set(path for path, *_ in CURRENT_FILES) & set(ABSENCE_PATHS))
        self.assertEqual(self.state["current_files"], list(GENERATOR.CURRENT_FILE_ENTRIES))
        self.assertEqual(self.state["current_absences"], list(GENERATOR.CURRENT_ABSENCE_ENTRIES))

    def test_historical_snapshots_source_seal_group_and_authorization_surface_are_exact(self) -> None:
        self.assertEqual(tuple((item["commit"], item["root_tree_oid"]) for item in GENERATOR.SNAPSHOTS), SNAPSHOT_PAIRS)
        source_rows = [row for row in self.state["blobs"] if row["phase"] == "v7_source_seal"]
        with (REPOSITORY_ROOT / CURRENT_FILES[3][0]).open("rb") as stream:
            header = json.loads(stream.readline())
        expected_source_paths = tuple(sorted(header["body"]["payload"]["dependency_hashes"]))
        self.assertEqual(len(source_rows), 96)
        self.assertEqual(tuple(row["relative_path"] for row in source_rows), expected_source_paths)
        authorization_rows = [row for row in self.state["blobs"] if row["phase"] == "v7_live_authorization"]
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
                    GENERATOR.write_manifests(root, self.state, approved_seed_sha256=supplied)
            self.assertEqual(list(root.iterdir()), [])

    def test_check_is_read_only_when_approval_manifests_are_absent(self) -> None:
        destinations = tuple(REPOSITORY_ROOT / path for path in GENERATOR.MANIFEST_PATHS)
        before = tuple((path.exists(), path.read_bytes() if path.exists() else None) for path in destinations)
        with self.assertRaises(GENERATOR.GenerationError):
            GENERATOR.check_manifests(REPOSITORY_ROOT, self.state)
        after = tuple((path.exists(), path.read_bytes() if path.exists() else None) for path in destinations)
        self.assertEqual(after, before)

    def test_seed_review_is_complete_deterministic_and_binds_the_normalized_digest(self) -> None:
        first = GENERATOR.render_seed_review(self.state)
        self.assertEqual(first, GENERATOR.render_seed_review(self.state))
        self.assertIn(f"normalized_sha256\t{self.state['entries_sha256']}\n".encode("ascii"), first)
        rows = [line for line in first.splitlines() if line.startswith(b"row\t")]
        self.assertEqual(len(rows), len(self.state["blobs"]))
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
            original_lstat = os.lstat
            before = original_lstat(regular)

            class ChangedStat:
                def __init__(self, source: os.stat_result) -> None:
                    for name in dir(source):
                        if name.startswith("st_"):
                            try:
                                setattr(self, name, getattr(source, name))
                            except AttributeError:
                                pass
                    self.st_size = source.st_size + 1

            with mock.patch.object(GENERATOR.os, "lstat", side_effect=[before, ChangedStat(before)]):
                with self.assertRaises(GENERATOR.GenerationError):
                    GENERATOR.read_regular_file_once(regular, maximum_bytes=8)

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
