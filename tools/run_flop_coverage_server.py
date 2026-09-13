"""Install one reviewed, bounded flop-coverage systemd job on Linux.

Use --print-unit (alias --dry-run) to render without host checks or mutations.
Installation is fresh-only: use the installed unit for reboot/restart recovery.
The experiment manifest owns the original absolute deadline and terminal state;
the unit's RuntimeMaxSec is an additional per-activation cgroup ceiling.
"""

import argparse
import json
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[1]
PREFIX = "pontius-flop-coverage-"
GIB = 1024**3


def run_command(arguments):
    result = subprocess.run(arguments, capture_output=True, text=True, check=False)
    if result.returncode:
        raise ValueError(
            f"command failed ({result.returncode}): {arguments!r}\n"
            f"{result.stderr.strip() or result.stdout.strip()}"
        )
    return result


def quoted(value, *, exec_argument=False):
    """Quote a systemd word, suppressing specifiers and ExecStart expansion."""
    value = str(value)
    if any(ord(character) < 32 or ord(character) == 127 for character in value):
        raise ValueError("control characters are not permitted in service paths")
    value = value.replace("\\", "\\\\").replace('"', '\\"').replace("%", "%%")
    if exec_argument:
        value = value.replace("$", "$$")
    return '"' + value + '"'


def unit_text(repo, name, reviewed_commit):
    run = repo / "experiments/results/runs" / name
    arguments = [
        sys.executable,
        str(repo / "experiments/2026-09-12-flop-coverage.py"),
        "run",
        "--profile",
        "full",
        "--run-directory",
        str(run),
        "--reviewed-commit",
        reviewed_commit,
    ]
    invocation = " ".join(quoted(value, exec_argument=True) for value in arguments)
    environment = quoted("PYTHONPATH=" + str(repo / "src") + ":" + str(repo))
    environment += " PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1"
    # The controller updates retained results and the repository execution journal.
    writable = " ".join(
        quoted(path)
        for path in (
            repo / "experiments/results",
            repo / "STATUS.md",
            repo / "execution_journal.jsonl",
        )
    )
    # WorkingDirectory is a scalar path; systemd does not remove word quotes here.
    working_directory = str(repo).replace("%", "%%")
    return f"""[Unit]
Description=Pontius reviewed flop coverage {name}
After=local-fs.target
StartLimitIntervalSec=86400
StartLimitBurst=3

[Service]
Type=exec
WorkingDirectory={working_directory}
Environment={environment}
ExecStart={invocation}
MemoryAccounting=yes
MemoryMax=16G
MemorySwapMax=0
OOMPolicy=continue
KillMode=control-group
RuntimeMaxSec=21600
TimeoutStopSec=30
Restart=on-failure
RestartSec=30
StandardOutput=journal
StandardError=journal
UMask=0077
NoNewPrivileges=yes
PrivateTmp=yes
ProtectSystem=strict
ReadWritePaths={writable}
ProtectKernelTunables=yes
ProtectKernelModules=yes
ProtectControlGroups=yes
RestrictSUIDSGID=yes

[Install]
WantedBy=multi-user.target
"""


def validate_host(
    *, platform_name, implementation, version, in_venv, uid, free_bytes, systemd, controllers
):
    if platform_name != "linux":
        raise ValueError("installation requires Linux; --print-unit works on any host")
    if implementation != "CPython" or version != (3, 14):
        raise ValueError("installation requires CPython 3.14")
    if not in_venv:
        raise ValueError("invoke the launcher with the intended virtual environment Python")
    if uid != 0:
        raise ValueError("installation requires root for the persistent system service")
    if free_bytes < 100 * GIB:
        raise ValueError("at least 100 GiB free disk is required before launch")
    if not systemd:
        raise ValueError("running systemd, systemctl and systemd-analyze are required")
    if "memory" not in controllers:
        raise ValueError("cgroup v2 with the memory controller is required")


def validate_source(repo, reviewed_commit):
    command = ["git", "-C", str(repo)]
    head = run_command([*command, "rev-parse", "HEAD"]).stdout.strip()
    if head != reviewed_commit:
        raise ValueError(f"reviewed commit mismatch: checkout is {head}")
    changes = run_command([*command, "diff", "--name-only", "HEAD", "--"]).stdout.splitlines()
    untracked = run_command([*command, "ls-files", "--others", "--exclude-standard"])
    changes += untracked.stdout.splitlines()
    disallowed = [
        path
        for path in changes
        if path not in {"STATUS.md", "execution_journal.jsonl"}
        and not path.startswith("experiments/results/")
    ]
    if disallowed:
        raise ValueError("unreviewed checkout changes: " + ", ".join(disallowed))


def validate_availability(run, unit, units):
    if run.exists() or run.is_symlink():
        raise ValueError(f"run already exists; resume using its installed service: {run}")
    if unit.exists() or unit.is_symlink():
        raise ValueError(f"unit already exists; refusing replacement: {unit}")
    for entry in units:
        if entry["unit"].startswith(PREFIX) and entry["active"] in {
            "active",
            "activating",
            "reloading",
            "deactivating",
        }:
            raise ValueError(f"competing experiment service: {entry['unit']} ({entry['active']})")


def install_unit(unit, text):
    """Validate before installation; leave a failed activation visible for diagnosis."""
    with tempfile.TemporaryDirectory(prefix="pontius-unit-") as temporary:
        candidate = Path(temporary) / unit.name
        candidate.write_text(text, encoding="utf-8", newline="\n")
        verification = run_command(["systemd-analyze", "verify", str(candidate)])
        if verification.stderr.strip():
            raise ValueError(
                "systemd unit verification reported diagnostics; refusing install:\n"
                + verification.stderr.strip()
            )
        with unit.open("x", encoding="utf-8", newline="\n") as stream:
            stream.write(text)
            stream.flush()
            os.fsync(stream.fileno())
    run_command(["systemctl", "daemon-reload"])
    run_command(["systemctl", "enable", "--now", unit.name])
    run_command(["systemctl", "is-enabled", unit.name])
    run_command(["systemctl", "is-active", unit.name])


def install(repo, name, commit, text):
    controllers_path = Path("/sys/fs/cgroup/cgroup.controllers")
    controllers = set(controllers_path.read_text().split()) if controllers_path.is_file() else set()
    validate_host(
        platform_name=sys.platform,
        implementation=platform.python_implementation(),
        version=sys.version_info[:2],
        in_venv=sys.prefix != sys.base_prefix,
        uid=os.geteuid() if hasattr(os, "geteuid") else -1,
        free_bytes=shutil.disk_usage(repo).free,
        systemd=(
            Path("/run/systemd/system").is_dir()
            and bool(shutil.which("systemctl"))
            and bool(shutil.which("systemd-analyze"))
        ),
        controllers=controllers,
    )
    if ":" in str(repo):
        raise ValueError("repository path cannot contain the PYTHONPATH separator ':'")
    for path in (
        repo / "experiments/2026-09-12-flop-coverage.py",
        repo / "STATUS.md",
        repo / "execution_journal.jsonl",
    ):
        if not path.is_file():
            raise ValueError(f"required reviewed file is missing: {path}")
    if not (repo / "experiments/results").is_dir():
        raise ValueError("required experiments/results directory is missing")
    # A single host-wide lock closes the preflight/install race between launchers.
    import fcntl

    with Path("/run/lock/pontius-flop-coverage-launch.lock").open("a") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as error:
            raise ValueError("another experiment launcher holds the installation lock") from error
        validate_source(repo, commit)
        unit = Path("/etc/systemd/system") / (PREFIX + name + ".service")
        run = repo / "experiments/results/runs" / name
        if not run.resolve().is_relative_to(repo):
            raise ValueError("run path resolves outside the checkout")
        listing = run_command(
            [
                "systemctl",
                "list-units",
                "--all",
                "--type=service",
                "--output=json",
                "--no-pager",
                PREFIX + "*.service",
            ]
        )
        units = json.loads(listing.stdout)
        validate_availability(run, unit, units)
        # Refuse another same-named vendor/transient unit, even if currently inactive.
        loaded = run_command(["systemctl", "show", "--property=LoadState", "--value", unit.name])
        if loaded.stdout.strip() != "not-found":
            raise ValueError(f"service name is already known to systemd: {unit.name}")
        install_unit(unit, text)
        print(f"Service: {unit.name}\nRun: {run}\nReviewed commit: {commit}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=ROOT)
    parser.add_argument("--run-name", required=True)
    parser.add_argument("--reviewed-commit", required=True)
    parser.add_argument("--print-unit", "--dry-run", action="store_true")
    args = parser.parse_args()
    try:
        if not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,63}", args.run_name):
            raise ValueError(
                "run name must be 1-64 lowercase letters, digits or hyphens, "
                "starting with a letter or digit"
            )
        if not re.fullmatch(r"(?:[0-9a-f]{40}|[0-9a-f]{64})", args.reviewed_commit):
            raise ValueError("reviewed commit must be a full lowercase Git object ID")
        repo = args.repo_root.resolve()
        text = unit_text(repo, args.run_name, args.reviewed_commit)
        if args.print_unit:
            print(text, end="")
        else:
            install(repo, args.run_name, args.reviewed_commit, text)
    except (ValueError, OSError, KeyError, TypeError) as error:
        parser.error(str(error))


if __name__ == "__main__":
    main()
