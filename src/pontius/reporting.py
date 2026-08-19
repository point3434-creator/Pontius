"""Shared serialization and provenance helpers for experiment artifacts."""

from __future__ import annotations

import platform
import subprocess
import sys
from typing import Any

from .evaluation import Policy


def git_metadata() -> dict[str, Any]:
    def run(*arguments: str) -> str | None:
        try:
            result = subprocess.run(
                ["git", *arguments],
                check=True,
                capture_output=True,
                text=True,
                timeout=5,
            )
        except (FileNotFoundError, subprocess.SubprocessError):
            return None
        return result.stdout.strip()

    return {
        "commit": run("rev-parse", "HEAD") or "unborn",
        "dirty": bool(run("status", "--porcelain")),
    }


def environment_metadata() -> dict[str, Any]:
    return {
        "python": sys.version,
        "platform": platform.platform(),
        "git": git_metadata(),
    }


def json_policy(policy: Policy) -> dict[str, dict[str, float]]:
    return {
        key: {str(action): probability for action, probability in distribution.items()}
        for key, distribution in policy.items()
    }
