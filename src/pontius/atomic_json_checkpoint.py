"""Cross-platform atomic JSON checkpoints with byte-truth digests."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any, Mapping

from .runner_harness import serialize_result


def write_atomic_json_checkpoint(
    payload: Mapping[str, Any],
    path: Path,
) -> str:
    """Atomically replace *path* and return the digest of its persisted bytes."""

    rendered = serialize_result(payload).encode("utf-8")
    temporary = path.with_suffix(f"{path.suffix}.tmp")
    temporary.write_bytes(rendered)
    temporary.replace(path)
    persisted = path.read_bytes()
    if persisted != rendered:
        raise OSError("persisted checkpoint bytes differ from serialized bytes")
    return hashlib.sha256(persisted).hexdigest()
