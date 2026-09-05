"""Non-evidentiary adapter over the ADR-0487 sealed host; no invocation authority."""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
import tarfile


SEAL = "af90155ebd970d0be6fe26969b121bd213a7f1f2"
PAYLOAD_MANIFEST = "6eb5ec280b6a8051e88d7659920ef74b46ea682a06dc80f688ed951d75f3f221"
BINDINGS = "docs/architecture/v0a-increment-1-source-bindings.json"
BINDINGS_SHA256 = "4136020b369eabcd1dd7c160a7b4f9dd05d9fc587fc8276993cc807b9f9e034b"
OVERLAY = (
    "tools/v0a_rehearsal_driver.py",
    "tests/test_v0a_rehearsal_driver.py",
    "docs/architecture/v0a-rehearsal-driver-r001.md",
)
PROTOCOL = "pontius-v0a-hand-replay-v1"


class DriverRefusal(ValueError):
    """A named boundary failed; any already published bytes remain retained."""


def regular(path: Path, *, directory: bool = False) -> None:
    info = path.lstat()
    if (info.st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT
            or not (stat.S_ISDIR(info.st_mode) if directory else stat.S_ISREG(info.st_mode))):
        raise DriverRefusal(f"PATH: non-regular or reparse path: {path}")


def validate_run(mode: str, run_id: str, root: Path) -> Path:
    if mode not in ("correctness", "rehearsal") or not re.fullmatch(
        re.escape(f"{PROTOCOL}-{mode}-") + r"[A-Za-z0-9][A-Za-z0-9_-]{0,79}", run_id
    ):
        raise DriverRefusal("IDENTITY: mode and run namespace must agree")
    if (not root.is_absolute() or len(root.drive) != 2 or root.name != run_id
            or ".." in root.parts or not root.is_dir()):
        raise DriverRefusal("ROOT: require an existing local directory named exactly as run ID")
    for part in (root, *root.parents):
        regular(part, directory=True)
    if any(root.iterdir()):
        raise DriverRefusal("ROOT: run directory must be empty; retained runs are never reused")
    return root


def source_preflight(repo: Path) -> str:
    """Bind actual LF checkout bytes before imports, under a no-concurrent-writer contract."""
    if os.name != "nt" or not sys.flags.dont_write_bytecode or not sys.flags.safe_path:
        raise DriverRefusal("SOURCE: require Windows Python invoked with -B -P")
    if any(name == "pontius" or name.startswith("pontius.") for name in sys.modules):
        raise DriverRefusal("SOURCE: pontius must not be preloaded")
    git = Path(os.environ.get("PONTIUS_GIT", ""))
    if not git.is_absolute() or not git.is_file():
        raise DriverRefusal("SOURCE: PONTIUS_GIT must name an absolute Git executable")
    regular(git)
    env = {key: value for key, value in os.environ.items()
           if not key.upper().startswith(("GIT_", "PYTHON", "PONTIUS_"))}
    command = subprocess.run(
        [str(git), "--no-optional-locks", "-c", "core.autocrlf=false",
         "-C", str(repo), "archive", "--format=tar",
         SEAL, "src/pontius"], env=env, capture_output=True, timeout=30,
    )
    if command.returncode:
        raise DriverRefusal("SOURCE: cannot read the pinned seal tree")
    with tarfile.open(fileobj=io.BytesIO(command.stdout)) as archive:
        expected = {}
        for member in archive.getmembers():
            if member.isfile():
                content = archive.extractfile(member).read()
                expected[member.name] = hashlib.sha256(content).hexdigest()
            elif not member.isdir():
                raise DriverRefusal("SOURCE: seal contains a non-regular package member")
    package = repo / "src/pontius"
    for path in (repo, *repo.parents, repo / "src", package):
        regular(path, directory=True)
    actual = {}
    for directory, directories, files in os.walk(package, followlinks=False):
        for name in directories:
            regular(Path(directory) / name, directory=True)
        for name in files:
            path = Path(directory) / name
            regular(path)
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            actual[path.relative_to(repo).as_posix()] = digest
    if not expected or actual != expected:
        raise DriverRefusal("SOURCE: missing, changed or extra package bytes (including caches)")
    bindings = repo / BINDINGS
    regular(bindings)
    if hashlib.sha256(bindings.read_bytes()).hexdigest() != BINDINGS_SHA256:
        raise DriverRefusal("SOURCE: bindings document differs from the seal")
    actual[BINDINGS] = BINDINGS_SHA256
    for relative in OVERLAY:
        path = repo / relative
        regular(path)
        actual[relative] = hashlib.sha256(path.read_bytes()).hexdigest()
    manifest = "".join(sorted(f"{digest}  {path}\n" for path, digest in actual.items()))
    sys.path.insert(0, str(repo / "src"))
    return hashlib.sha256(manifest.encode("utf-8")).hexdigest()


def accept_trace(outcome, destination, fixture, blueprint, run_id, mode, manifest):
    """Host completion and independent persisted-byte replay are both necessary."""
    if outcome.receipt.passed is not True or outcome.receipt.accounting_complete is not True:
        raise DriverRefusal("HOST: replay/publication/accounting did not complete successfully")
    regular(destination)
    content = destination.read_bytes()
    digest = hashlib.sha256(content).hexdigest()
    if content != outcome.trace or digest != outcome.receipt.trace_sha256:
        raise DriverRefusal("READBACK: persisted trace differs from completed publication")
    from pontius.v0a.replay import verify_successful_trace
    from pontius.v0a.trace import TraceInvalidError

    try:
        verified = verify_successful_trace(
            content, fixture=fixture, blueprint=blueprint, source_commit=SEAL,
            source_manifest_sha256=manifest, expected_mode=mode,
            expected_clock_kind="monotonic_ns",
        )
    except TraceInvalidError as error:
        raise DriverRefusal(f"VERIFY: {error}") from error
    if verified.run_id != run_id or outcome.receipt.run_id != run_id:
        raise DriverRefusal("VERIFY: completed run identity differs from requested run")
    return {
        "passed": True, "evidentiary": False, "mode": mode, "run_id": run_id,
        "source_commit": SEAL, "source_manifest_sha256": manifest,
        "preserved_payload_manifest_sha256": PAYLOAD_MANIFEST,
        "trace_sha256": digest, "semantic_sha256": verified.semantic_sha256,
        "payouts": list(verified.payouts), "trace_path": str(destination),
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("correctness", "rehearsal"), required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--run-root", type=Path, required=True)
    parser.add_argument("--fixture", choices=("control-A", "control-B"), required=True)
    args = parser.parse_args(argv)
    try:
        root = validate_run(args.mode, args.run_id, args.run_root)
        repo = Path(__file__).resolve().parents[1]
        manifest = source_preflight(repo)
        from pontius.immutable_blueprint import ImmutableBlueprintActionSource
        from pontius.v0a.replay import FIXTURES, ReplayHost

        fixture = next(item for item in FIXTURES if item.name == args.fixture)
        blueprint = ImmutableBlueprintActionSource(source_id="v0a-empty-reference")
        outcome = ReplayHost(
            fixture, run_id=args.run_id, blueprint=blueprint, mode=args.mode,
            source_commit=SEAL, source_manifest_sha256=manifest, clock_kind="monotonic_ns",
        ).run(destination="trace.jsonl", run_root=root)
        receipt = accept_trace(outcome, root / "trace.jsonl", fixture, blueprint,
                               args.run_id, args.mode, manifest)
        print(json.dumps(receipt, sort_keys=True, separators=(",", ":"), allow_nan=False))
        return 0
    except DriverRefusal as error:
        print(f"REFUSED {error}", file=sys.stderr)
    except (OSError, ValueError, subprocess.SubprocessError, tarfile.TarError) as error:
        print(f"REFUSED IO: {type(error).__name__}: {error}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
