"""Immutable JSON training generations with validated recovery.

The caller must serialize writers and capture trainer arrays/RNG at one state
barrier. Save does not lock or stop a running trainer. A generation is published
only after its file and staging directory have been synced. POSIX additionally
syncs parent directories; Windows file flushing alone is not a power-cut proof.
Checksums detect accidental corruption, not malicious rewriting.
Recovery and save validation currently decode and retain every valid generation
payload during their scan. Memory therefore grows with retained history; this
simple format is intended for the bounded reference, not large training stores.
"""

import hashlib
import hmac
import json
import math
import ntpath
import os
from pathlib import Path
import re
import time
import uuid


def _validate_json(value):
    if value is None or type(value) in (str, bool, int):
        return
    if type(value) is float:
        if not math.isfinite(value):
            raise ValueError("Checkpoint numbers must be finite")
        return
    if type(value) is list:
        for item in value:
            _validate_json(item)
        return
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise TypeError("Checkpoint object keys must be strings")
            _validate_json(item)
        return
    raise TypeError("Checkpoint state must contain only JSON-native values")


def _identity(payload):
    if type(payload) is not dict:
        raise ValueError("Checkpoint payload must be an object")
    identity = payload.get("identity")
    if type(identity) is not str or not identity.strip():
        raise ValueError("Checkpoint identity must be a nonempty string")
    return identity


def _encode(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=True, allow_nan=False).encode("utf-8")


def _sync_directory(path):
    if os.name == "posix":
        descriptor = os.open(path, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)


def _ensure_directory(path):
    missing = []
    current = path
    while not current.exists():
        missing.append(current)
        current = current.parent
    for directory in reversed(missing):
        directory.mkdir()
        _sync_directory(directory)
        _sync_directory(directory.parent)


def _write_file(path, data):
    with path.open("xb") as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())


def _read_generation(path):
    record = json.loads((path / "checkpoint.json").read_bytes())
    if type(record) is not dict or set(record) != {"body", "sha256"}:
        raise ValueError("Invalid checkpoint envelope")
    body = record["body"]
    _validate_json(body)
    digest = hashlib.sha256(_encode(body)).hexdigest()
    if type(record["sha256"]) is not str or not hmac.compare_digest(record["sha256"], digest):
        raise ValueError("Checkpoint checksum mismatch")
    if type(body) is not dict or set(body) != {
        "format", "generation", "sequence", "created_ns", "payload"
    }:
        raise ValueError("Invalid checkpoint body")
    if body["format"] != 1 or body["generation"] != path.name:
        raise ValueError("Checkpoint format or generation mismatch")
    for field in ("sequence", "created_ns"):
        if type(body[field]) is not int or body[field] < 1:
            raise ValueError("Invalid checkpoint publication order")
    _identity(body["payload"])
    return body


def _scan(root):
    generations = root / "generations"
    valid = []
    completed = []
    if generations.exists():
        completed = [path for path in generations.iterdir()
                     if path.is_dir() and not path.name.startswith(".")]
        for path in completed:
            try:
                valid.append(_read_generation(path))
            except (OSError, ValueError, TypeError, RecursionError, OverflowError):
                # An invalid completed directory never supplies trainer state.
                continue
    identities = {_identity(item["payload"]) for item in valid}
    if len(identities) > 1:
        raise ValueError("Checkpoint root contains mixed identities")
    return sorted(valid, key=lambda item: (item["sequence"], item["created_ns"],
                                          item["generation"])), completed


def save_checkpoint(root: Path, payload: dict, generation: str) -> Path:
    """Durably publish a new named generation; never overwrite a milestone.

    Valid generations in a root must share the complete caller-supplied identity.
    If all completed generations are corrupt, save refuses to infer an identity.
    Failed staging directories are retained for inspection and ignored on load.
    A sync failure after publication can raise even though the new generation
    is already visible. Inspect recovery before retrying an immutable name.
    """
    identity = _identity(payload)
    _validate_json(payload)
    if type(generation) is not str or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,127}",
                                                     generation):
        raise ValueError("Generation must be a portable, nonhidden directory name")
    if ntpath.isreserved(generation):
        raise ValueError("Generation name is reserved or normalized on Windows")
    root = Path(root)
    destination = root / "generations" / generation
    if destination.exists():
        raise FileExistsError(destination)
    valid, completed = _scan(root)
    if completed and not valid:
        raise ValueError("No valid generation remains to establish checkpoint identity")
    if valid and _identity(valid[-1]["payload"]) != identity:
        raise ValueError("Checkpoint identity mismatch")
    body = {
        "format": 1,
        "generation": generation,
        "sequence": valid[-1]["sequence"] + 1 if valid else 1,
        "created_ns": time.time_ns(),
        "payload": payload,
    }
    data = _encode({"body": body, "sha256": hashlib.sha256(_encode(body)).hexdigest()})
    _ensure_directory(destination.parent)
    staging = destination.parent / (".staging-" + uuid.uuid4().hex)
    staging.mkdir()
    _write_file(staging / "checkpoint.json", data)
    _sync_directory(staging)
    # Single-writer use is required. os.rename does not replace a nonempty
    # generation, and this explicit check also rejects an existing empty one.
    if destination.exists():
        raise FileExistsError(destination)
    staging.rename(destination)
    _sync_directory(destination.parent)
    pointer = root / (".latest-" + uuid.uuid4().hex)
    try:
        _write_file(pointer, generation.encode("ascii"))
        pointer.replace(root / "latest")
        _sync_directory(root)
    except OSError:
        # The durable generation is committed; an advisory pointer failure
        # must not make a caller retry the immutable name as an uncommitted save.
        pass
    return destination


def load_checkpoint(root: Path, expected_identity: str | None = None) -> dict:
    """Return the newest fully validated state, falling back past corruption.

    The latest pointer is deliberately ignored. Expected identity is checked
    against the root's valid states, never used to filter away a mismatched run.
    """
    valid, completed = _scan(Path(root))
    if not valid:
        if completed:
            raise ValueError("No valid completed checkpoint generation")
        raise FileNotFoundError("No completed checkpoint generation")
    payload = valid[-1]["payload"]
    if expected_identity is not None and _identity(payload) != expected_identity:
        raise ValueError("Checkpoint identity mismatch")
    return payload
