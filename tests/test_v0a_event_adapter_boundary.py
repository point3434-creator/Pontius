"""Real repository gate coverage for the v0a event adapter opening."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "event_adapter_boundary", ROOT / "tools/check_stabilization_boundaries.py"
)
CHECKER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CHECKER)


class EventAdapterBoundaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        parent = ROOT.parent if ROOT.drive.upper() == "D:" else Path("D:/")
        cls.temporary = Path(tempfile.mkdtemp(prefix="event-boundary-", dir=parent))
        cls.repo = cls.temporary / "source"
        subprocess.run(
            [os.environ["PONTIUS_GIT"], "-c", "core.autocrlf=false", "clone", "--quiet",
             "--no-hardlinks", str(ROOT), str(cls.repo)], check=True
        )
        cls.blueprint = cls.temporary / "blueprint.json"
        cls.blueprint.write_bytes(
            (ROOT / "tests/fixtures/event_adapter/fold_blueprint.json").read_bytes()
        )
        cls.sequence = 0

    def git(self, *args: str, data: bytes | None = None) -> bytes:
        return subprocess.run(
            [os.environ["PONTIUS_GIT"], "--no-replace-objects", "-C", str(self.repo), *args],
            input=data, check=True, capture_output=True,
        ).stdout.strip()

    def invoke(self, code: str | None = None, events: list[dict] | None = None
               ) -> subprocess.CompletedProcess[bytes]:
        self.__class__.sequence += 1
        session = "pontius-v0a-event-interface-v1-correctness-boundary-" + str(self.sequence)
        child = {k: v for k, v in os.environ.items()
                 if not k.upper().startswith(("GIT_", "PYTHON", "PONTIUS_"))}
        child.update(PYTHONPATH=str(self.repo / "src"), PONTIUS_GIT=os.environ["PONTIUS_GIT"])
        command = ["-c", code] if code else [str(self.repo / "tools/v0a_event_adapter.py")]
        payload = b"".join(
            (json.dumps(dict(row, hand_id=session), separators=(",", ":")) + "\n").encode()
            for row in (events or [])
        )
        return subprocess.run(
            [sys.executable, "-B", "-P", *command, "--blueprint", str(self.blueprint),
             "--session-id", session], cwd=self.repo, env=child, input=payload,
            capture_output=True, timeout=90,
        )

    def assert_source_accepted(self, result: subprocess.CompletedProcess[bytes]) -> None:
        self.assertIn(b'"type":"ready"', result.stdout, result.stderr.decode(errors="replace"))

    def assert_source_refused(self, result: subprocess.CompletedProcess[bytes]) -> None:
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn(b'"type":"ready"', result.stdout)
        self.assertIn(b"REFUSED", result.stderr)

    def _replace_and_check(self, relative: str, raw: bytes, *, accepted: bool) -> None:
        target = ROOT / relative
        original = target.read_bytes() if target.exists() else None
        try:
            target.write_bytes(raw)
            if accepted:
                CHECKER.check_repository(ROOT)
            else:
                self.assertRaises(CHECKER.BoundaryError, CHECKER.check_repository, ROOT)
        finally:
            target.unlink() if original is None else target.write_bytes(original)

    def test_exact_event_adapter_tool_is_classified(self) -> None:
        CHECKER.check_repository(ROOT)
        self._replace_and_check(
            "tools/v0a_event_adapter.py",
            b"from __future__ import annotations\n"
            b"import argparse\n"
            b"from pontius.blueprint_artifact.codec import decode_blueprint\n"
            b"from pontius.v0a.clock import MonotonicWitness\n"
            b"from pontius.v0a.model import HandStartedEvent\n"
            b"from pontius.v0a.runtime import HandRuntime\n"
            b"from pontius.v0a.trace import decision_payload\n",
            accepted=True,
        )

    def test_extra_event_adapter_tool_is_refused(self) -> None:
        self._replace_and_check(
            "tools/v0a_event_adapter_extra.py", b"# unauthorized tool\n", accepted=False
        )

    def test_forbidden_event_adapter_import_is_refused(self) -> None:
        target = ROOT / "tools/v0a_event_adapter.py"
        original = target.read_bytes() if target.exists() else b""
        self._replace_and_check(
            "tools/v0a_event_adapter.py",
            original + b"\nimport pontius.immutable_blueprint\n",
            accepted=False,
        )

    def test_changed_extra_and_cached_package_sources_are_refused(self) -> None:
        for relative, raw in (
            ("src/pontius/v0a/model.py", None),
            ("src/pontius/v0a/event_boundary_extra.py", b"# extra\n"),
            ("src/pontius/v0a/__pycache__/cached.pyc", b"cached source"),
        ):
            target = self.repo / relative
            original = target.read_bytes() if target.exists() else None
            target.parent.mkdir(parents=True, exist_ok=True)
            try:
                target.write_bytes((original + b"\n# changed\n") if raw is None else raw)
                with self.subTest(relative=relative):
                    self.assert_source_refused(self.invoke())
            finally:
                target.unlink() if original is None else target.write_bytes(original)
                if "__pycache__" in relative:
                    target.parent.rmdir()

    def test_preloaded_package_and_wrong_tool_origin_are_refused(self) -> None:
        preloaded = (
            "import pontius,runpy;"
            "runpy.run_path('tools/v0a_event_adapter.py',run_name='__main__')"
        )
        copied = (
            "from pathlib import Path;import runpy;"
            "p=Path('tools/copied_event_adapter.py');"
            "p.write_bytes(Path('tools/v0a_event_adapter.py').read_bytes());"
            "runpy.run_path(str(p),run_name='__main__')"
        )
        for code in (preloaded, copied):
            with self.subTest(code=code[:16]):
                self.assert_source_refused(self.invoke(code))
        wrong_import = """import builtins,sys,runpy
original=builtins.__import__
def changed(name,*args,**kwargs):
    result=original(name,*args,**kwargs)
    if name == 'pontius.v0a.runtime':
        sys.modules[name].__file__='D:/wrong-origin.py'
    return result
builtins.__import__=changed
runpy.run_path('tools/v0a_event_adapter.py',run_name='__main__')
"""
        self.assert_source_refused(self.invoke(wrong_import))

    def test_git_replacement_refs_cannot_replace_raw_commit_or_blob(self) -> None:
        path = self.repo / "src/pontius/v0a/model.py"
        original = path.read_bytes()
        head = self.git("rev-parse", "HEAD").decode()
        blob = self.git("rev-parse", "HEAD:src/pontius/v0a/model.py").decode()
        replacement_blob = self.git(
            "hash-object", "-w", "--stdin", data=original + b"\n# replacement\n"
        ).decode()
        self.git("replace", blob, replacement_blob)
        self.assert_source_accepted(self.invoke())
        path.write_bytes(original + b"\n# replacement\n")
        try:
            self.assert_source_refused(self.invoke())
            self.git("add", "src/pontius/v0a/model.py")
            tree = self.git("write-tree").decode()
            commit = self.git("-c", "user.name=Test", "-c", "user.email=test@localhost",
                              "commit-tree", tree, "-p", head, "-m", "replacement").decode()
            self.git("replace", head, commit)
            path.write_bytes(original)
            self.assert_source_accepted(self.invoke())
            self.assertEqual(self.git("rev-parse", "HEAD").decode(), head)
            self.git("update-ref", "HEAD", commit, head)
            path.write_bytes(original + b"\n# replacement\n")
            self.assert_source_refused(self.invoke())
            self.git("update-ref", "HEAD", head, commit)
        finally:
            path.write_bytes(original)
            subprocess.run([os.environ["PONTIUS_GIT"], "-C", str(self.repo),
                            "replace", "-d", blob, head], capture_output=True)

    def test_final_source_revalidation_detects_post_load_drift(self) -> None:
        code = """import runpy
from pathlib import Path
g=runpy.run_path('tools/v0a_event_adapter.py')['main'].__globals__
original=g['Source'].check
calls={'count':0}
def check(source):
    calls['count'] += 1
    if calls['count'] == 2:
        (source.repo/'src/pontius/v0a/late_drift.py').write_bytes(b'# late drift\\n')
    return original(source)
g['Source'].check=check
raise SystemExit(g['main']())
"""
        common = {"schema_version": "pontius-v0a-event-v1"}
        events = [
            dict(common, kind="hand_started", event_index=0, button=0, controlled_seat=3,
                 starting_stacks=[200] * 6, small_blind=1, big_blind=2,
                 private_cards=[48, 49]),
            *(dict(common, kind="opponent_action", event_index=index, street="preflop",
                   seat=seat, action={"kind": "fold", "raise_to": None})
              for index, seat in enumerate((4, 5, 0, 1, 2), 1)),
        ]
        drift = self.repo / "src/pontius/v0a/late_drift.py"
        try:
            result = self.invoke(code, events)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn(b'"type":"ready"', result.stdout)
            self.assertIn(b"source_binding_mismatch", result.stdout)
        finally:
            drift.unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
