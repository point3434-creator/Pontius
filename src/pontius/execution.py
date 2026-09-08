"""Source verification at run start and one retained outcome at run end."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import time
import uuid

from .status_generation import append_run, render_status


CONTEXT_ENV = "PONTIUS_RUN_CONTEXT"
TEXT_SUFFIXES = (".py", ".toml", ".lock", ".json", ".yaml", ".yml", ".gitattributes")


def git(root, *arguments, content=None, timeout=30):
    executable = os.environ.get("PONTIUS_GIT") or shutil.which("git")
    if not executable:
        raise ValueError("Git executable not found")
    result = subprocess.run(
        [executable, "--no-replace-objects", "-C", str(root), *arguments],
        input=content,
        capture_output=True,
        check=True,
        timeout=timeout,
    )
    return result.stdout


def begin_run(root, *, reviewed_commit=None, allow_working_tree=False, inherited=None):
    """Capture source once. An inherited context does no filesystem verification."""
    root = Path(root).resolve()
    if inherited:
        context = json.loads(inherited)
        if Path(context["root"]) != root:
            raise ValueError("child run root differs from parent")
        return dict(context, inherited=True)
    started = time.perf_counter()
    commit = (
        git(root, "rev-parse", "--verify", (reviewed_commit or "HEAD") + "^{commit}")
        .decode()
        .strip()
    )
    head = git(root, "rev-parse", "--verify", "HEAD^{commit}").decode().strip()
    source_scope = ("src", "tools", "tests", ".github", "pyproject.toml", "uv.lock",
                    ".gitattributes")
    tree = git(root, "ls-tree", "-r", "-z", commit, "--", *source_scope)
    expected = {}
    objects = []
    for entry in tree.split(b"\0"):
        if not entry:
            continue
        metadata, name = entry.split(b"\t", 1)
        mode, kind, object_id = metadata.split()
        if kind != b"blob" or mode not in (b"100644", b"100755"):
            raise ValueError("source tree contains a non-file entry")
        objects.append((name.decode(), object_id))
    contents = io.BytesIO(
        git(
            root,
            "cat-file",
            "--batch",
            content=b"\n".join(object_id for _, object_id in objects) + b"\n",
        )
    )
    for name, object_id in objects:
        header = contents.readline().split()
        if len(header) != 3 or header[:2] != [object_id, b"blob"]:
            raise ValueError("invalid Git source object")
        raw = contents.read(int(header[2]))
        if contents.read(1) != b"\n":
            raise ValueError("truncated Git source object")
        canonical = raw.replace(b"\r\n", b"\n") if name.endswith(TEXT_SUFFIXES) else raw
        expected[name] = hashlib.sha256(canonical).hexdigest()
    names = set(expected)
    for entry in git(root, "ls-files", "--cached", "--others", "--exclude-standard", "-z",
                     "--", *source_scope).split(b"\0"):
        if entry:
            names.add(entry.decode())
    actual = {}
    actual_raw = {}
    for name in sorted(names):
        path = root / name
        if path.is_symlink():
            raise ValueError(f"source symlink: {name}")
        if path.is_file():
            raw = path.read_bytes()
            actual_raw[name] = hashlib.sha256(raw).hexdigest()
            canonical = (
                raw.replace(b"\r\n", b"\n") if name.endswith(TEXT_SUFFIXES) else raw
            )
            actual[name] = hashlib.sha256(canonical).hexdigest()
    verified = actual == expected
    if not verified and not allow_working_tree:
        raise ValueError(
            "source differs from reviewed commit; use --development for an unreviewed run"
        )
    source_digest = hashlib.sha256(json.dumps(actual_raw, sort_keys=True).encode()).hexdigest()
    return dict(
        root=str(root),
        commit=commit,
        head=head,
        source_sha256=source_digest,
        source_scope=list(source_scope),
        verified=verified,
        inherited=False,
        source_check_seconds=time.perf_counter() - started,
    )


def child_context(context):
    return json.dumps({key: value for key, value in context.items() if key != "inherited"})


def finish_run(context, command, report, duration_seconds):
    """Write one result and one journal row; child processes do neither."""
    if context.get("inherited"):
        return
    root = Path(context["root"])
    timestamp = datetime.now(timezone.utc)
    if context.get("output_directory"):
        directory = (root / context["output_directory"]).resolve()
        if not directory.is_relative_to(root.resolve()):
            raise ValueError("output directory must stay inside the repository")
        output = directory / "result.json"
    else:
        output = (
            root
            / "experiments/results"
            / (timestamp.strftime("%Y%m%dT%H%M%S") + "-" + uuid.uuid4().hex[:8] + ".json")
        )
    output.parent.mkdir(parents=True, exist_ok=True)
    raw = (json.dumps(report, sort_keys=True, allow_nan=False) + "\n").encode()
    output.write_bytes(raw)
    record = dict(
        timestamp=timestamp.isoformat(),
        command=command,
        status=report.get("status", "failed"),
        summary=report.get("summary")
        or report.get("failure_reason")
        or f"{report.get('completed_hands', 0)} hands completed",
        duration_seconds=duration_seconds,
        source_commit=context["commit"],
        source_sha256=context["source_sha256"],
        source_scope=context.get("source_scope"),
        source_verified=context["verified"],
        source_check_seconds=context["source_check_seconds"],
        output=str(output.relative_to(root)).replace("\\", "/"),
        output_sha256=hashlib.sha256(raw).hexdigest(),
    )
    runtimes = output.parent / "runtimes.json"
    if context.get("output_directory") and runtimes.exists():
        record["runtimes_sha256"] = hashlib.sha256(runtimes.read_bytes()).hexdigest()
    append_run(root, record)
    (root / "STATUS.md").write_text(render_status(root), encoding="utf-8")
