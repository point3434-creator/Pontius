"""Behavioral tests for durable, immutable trainer snapshots."""

import copy
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

from pontius import training_checkpoint
from pontius.training_checkpoint import load_checkpoint, save_checkpoint


class TrainingCheckpointTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name) / "checkpoints"
        self.payload = {
            "identity": "six-player-game/config-v1/cfr",
            "iteration": 9,
            "regrets": {"row": [-0.25, 1.5, 0.0]},
            "averages": [2.0, 0.125],
            "rng": [3, [0, 123, 456], None],
        }

    def test_round_trip_preserves_complete_payload_without_mutation(self):
        before = copy.deepcopy(self.payload)
        path = save_checkpoint(self.root, self.payload, "baseline-009")
        self.assertTrue(path.is_dir())
        self.assertEqual(load_checkpoint(self.root), before)
        self.assertEqual(self.payload, before)

    def test_names_are_immutable_and_cannot_escape_root(self):
        save_checkpoint(self.root, self.payload, "baseline-009")
        with self.assertRaises(FileExistsError):
            save_checkpoint(self.root, self.payload | {"iteration": 10}, "baseline-009")
        for name in ["", ".", "..", "../outside", "a/b", "a\\b", ".staging-fake"]:
            with self.subTest(name=name), self.assertRaises(ValueError):
                save_checkpoint(self.root, self.payload, name)
        self.assertEqual(load_checkpoint(self.root), self.payload)

    def test_windows_normalized_and_reserved_names_fail_before_root_creation(self):
        names = ["milestone.", "milestone..", "CON", "prn", "AuX", "NUL",
                 "CON.snapshot", "nul.json", "COM1", "com9.json", "LPT1", "lpt9.state"]
        for index, name in enumerate(names):
            root = self.root / str(index)
            with self.subTest(name=name):
                with self.assertRaises(ValueError):
                    save_checkpoint(root, self.payload, name)
                self.assertFalse(root.exists())

    def test_staging_sync_failure_preserves_previous_completed_state(self):
        previous = save_checkpoint(self.root, self.payload, "first")
        sync_directory = training_checkpoint._sync_directory

        def fail_staging_sync(path):
            if path.name.startswith(".staging-"):
                raise OSError("Injected staging sync failure")
            sync_directory(path)

        with patch.object(training_checkpoint, "_sync_directory", fail_staging_sync):
            with self.assertRaises(OSError):
                save_checkpoint(self.root, self.payload | {"iteration": 10}, "second")
        self.assertEqual(load_checkpoint(self.root), self.payload)
        self.assertTrue(previous.is_dir())
        self.assertFalse((previous.parent / "second").exists())
        self.assertTrue(any(path.name.startswith(".staging-")
                            for path in previous.parent.iterdir()))

    def test_post_rename_sync_failure_can_leave_new_generation_visible(self):
        previous = save_checkpoint(self.root, self.payload, "first")
        sync_directory = training_checkpoint._sync_directory

        def fail_publication_sync(path):
            if path == previous.parent:
                raise OSError("Injected publication sync failure")
            sync_directory(path)

        with patch.object(training_checkpoint, "_sync_directory", fail_publication_sync):
            with self.assertRaises(OSError):
                save_checkpoint(self.root, self.payload | {"iteration": 10}, "second")
        self.assertTrue(previous.is_dir())
        self.assertEqual(load_checkpoint(self.root)["iteration"], 10)
        with self.assertRaises(FileExistsError):
            save_checkpoint(self.root, self.payload, "second")

    def test_real_child_interruption_recovers_only_completed_generations(self):
        # Hooks pause an actual child save at filesystem boundaries. Terminating
        # a process proves recovery from process interruption, not power loss.
        child_code = """
from pathlib import Path
import sys
import time
from pontius import training_checkpoint

root, marker = Path(sys.argv[1]), Path(sys.argv[2])
boundary = sys.argv[3]
sync_directory = training_checkpoint._sync_directory

def pause_at_boundary(path):
    selected = (path.name.startswith('.staging-') if boundary == 'staged'
                else path == root / 'generations')
    if selected:
        if boundary == 'staged':
            sync_directory(path)
        marker.write_text('ready', encoding='utf-8')
        while True:
            time.sleep(1)
    sync_directory(path)

training_checkpoint._sync_directory = pause_at_boundary
payload = training_checkpoint.load_checkpoint(root)
payload['iteration'] = 10
training_checkpoint.save_checkpoint(root, payload, 'second')
"""
        environment = os.environ.copy()
        environment["PYTHONPATH"] = str(Path(__file__).resolve().parents[1] / "src")
        creationflags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
        for boundary, expected_iteration in (("staged", 9), ("published", 10)):
            with self.subTest(boundary=boundary):
                root = self.root / boundary
                previous = save_checkpoint(root, self.payload, "first")
                marker = root / "child-paused"
                child = subprocess.Popen(
                    [sys.executable, "-c", child_code, str(root), str(marker), boundary],
                    env=environment, creationflags=creationflags,
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                )
                try:
                    deadline = time.monotonic() + 5
                    while not marker.exists() and child.poll() is None:
                        if time.monotonic() >= deadline:
                            break
                        time.sleep(0.01)
                    if child.poll() is not None:
                        _, errors = child.communicate()
                        self.fail(f"Child exited before pause: {errors.decode(errors='replace')}")
                    self.assertTrue(marker.exists(),
                                    "Child did not reach boundary within 5 seconds")
                finally:
                    if child.poll() is None:
                        child.terminate()
                    try:
                        child.communicate(timeout=2)
                    except subprocess.TimeoutExpired:
                        child.kill()
                        child.communicate(timeout=2)
                self.assertIsNotNone(child.returncode)
                self.assertTrue(previous.is_dir())
                self.assertEqual(load_checkpoint(root)["iteration"], expected_iteration)
                self.assertEqual((previous.parent / "second").exists(), boundary == "published")

    def test_corrupt_newest_falls_back_even_when_latest_pointer_is_corrupt(self):
        save_checkpoint(self.root, self.payload, "z-first")
        newest = save_checkpoint(self.root, self.payload | {"iteration": 10}, "a-second")
        self.assertEqual(load_checkpoint(self.root)["iteration"], 10)
        for file in newest.iterdir():
            if file.is_file():
                file.write_text("corrupt", encoding="utf-8")
        (self.root / "latest").write_text("../../bad", encoding="utf-8")
        self.assertEqual(load_checkpoint(self.root), self.payload)

    def test_valid_json_tampering_is_detected_by_checksum(self):
        path = save_checkpoint(self.root, self.payload, "first")
        for file in path.iterdir():
            if file.is_file():
                raw = file.read_text(encoding="utf-8")
                if '"iteration":9' in raw:
                    file.write_text(raw.replace('"iteration":9', '"iteration":8'),
                                    encoding="utf-8")
        with self.assertRaises(ValueError):
            load_checkpoint(self.root)

    def test_partial_staging_and_incomplete_final_are_ignored(self):
        path = save_checkpoint(self.root, self.payload, "first")
        unpublished = save_checkpoint(self.root, self.payload | {"iteration": 10}, "second")
        unpublished.rename(path.parent / ".staging-complete")
        for name in [".staging-interrupted", "incomplete"]:
            partial = path.parent / name
            partial.mkdir()
            (partial / "checkpoint.json").write_text('{"payload":', encoding="utf-8")
        self.assertEqual(load_checkpoint(self.root), self.payload)

    def test_identity_is_required_and_cannot_mix(self):
        for identity in [None, "", "  ", 12]:
            with self.subTest(identity=identity), self.assertRaises(ValueError):
                save_checkpoint(self.root, self.payload | {"identity": identity}, "bad")
        save_checkpoint(self.root, self.payload, "first")
        with self.assertRaises(ValueError):
            save_checkpoint(self.root, self.payload | {"identity": "different"}, "second")
        with self.assertRaises(ValueError):
            load_checkpoint(self.root, expected_identity="different")
        self.assertEqual(load_checkpoint(self.root, self.payload["identity"]), self.payload)

    def test_mixed_valid_generations_are_rejected_without_identity_filtering(self):
        save_checkpoint(self.root, self.payload, "first")
        other = save_checkpoint(self.root.parent / "other",
                                self.payload | {"identity": "different"}, "second")
        shutil.copytree(other, self.root / "generations" / "second")
        with self.assertRaises(ValueError):
            load_checkpoint(self.root, expected_identity=self.payload["identity"])
        with self.assertRaises(ValueError):
            save_checkpoint(self.root, self.payload, "third")

    def test_nonfinite_and_non_json_native_values_are_rejected(self):
        for bad in [float("nan"), float("inf"), float("-inf"), (1, 2), {1: "bad"}]:
            with self.subTest(bad=bad), self.assertRaises((ValueError, TypeError)):
                save_checkpoint(self.root, self.payload | {"bad": bad}, "bad")
        self.assertFalse(self.root.exists())

    def test_missing_or_no_valid_generation_raises(self):
        with self.assertRaises(FileNotFoundError):
            load_checkpoint(self.root)
        path = save_checkpoint(self.root, self.payload, "first")
        for file in path.iterdir():
            if file.is_file():
                file.write_text(json.dumps({"corrupt": True}), encoding="utf-8")
        with self.assertRaises(ValueError):
            load_checkpoint(self.root)
        with self.assertRaises(ValueError):
            save_checkpoint(self.root, self.payload | {"identity": "different"}, "second")


if __name__ == "__main__":
    unittest.main()
