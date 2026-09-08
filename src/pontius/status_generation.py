"""Record run outcomes and render the project status from the execution journal."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def validate_run(record):
    if not isinstance(record, dict):
        raise ValueError("run must be an object")
    for field in ("timestamp", "command", "status", "summary"):
        if not isinstance(record.get(field), str) or not record[field].strip():
            raise ValueError(f"run requires a nonempty {field}")
    duration = record.get("duration_seconds")
    if duration is not None:
        if isinstance(duration, bool) or not isinstance(duration, (int, float)):
            raise ValueError("duration_seconds must be a number")
        if not math.isfinite(duration) or duration < 0:
            raise ValueError("duration_seconds must be finite and nonnegative")


def append_run(root, record):
    """Append exactly one JSON line after a run has an outcome."""
    validate_run(record)
    encoded = json.dumps(record, ensure_ascii=False, allow_nan=False) + "\n"
    with (Path(root) / "execution_journal.jsonl").open(
        "a", encoding="utf-8", newline="\n"
    ) as stream:
        stream.write(encoded)


def read_runs(root):
    journal = Path(root) / "execution_journal.jsonl"
    if not journal.exists():
        return []
    records = []
    for number, line in enumerate(journal.read_text(encoding="utf-8").splitlines(), 1):
        try:
            record = json.loads(line)
            validate_run(record)
        except (ValueError, TypeError) as error:
            raise ValueError(f"invalid execution journal at line {number}: {error}") from error
        records.append(record)
    return records


def render_status(root=ROOT, recent_count=12):
    records = read_runs(root)
    lines = ["# Status", "", "Generated from execution_journal.jsonl.", ""]
    if not records:
        return "\n".join(lines + ["No runs recorded.", ""])

    def cell(value):
        return str(value).replace("|", "\\|").replace("\r", " ").replace("\n", " ")

    lines += [
        f"Recorded runs: {len(records)}. Most recent {min(len(records), recent_count)} below.",
        "",
        "| Recorded (UTC) | Command | Outcome | Seconds | Finding |",
        "|---|---|---|---:|---|",
    ]
    for record in reversed(records[-recent_count:]):
        duration = record.get("duration_seconds")
        seconds = "—" if duration is None else f"{duration:.3f}"
        values = [
            record["timestamp"],
            record["command"],
            record["status"],
            seconds,
            record["summary"],
        ]
        lines.append("| " + " | ".join(cell(value) for value in values) + " |")
    return "\n".join(lines) + "\n"


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--check", action="store_true", help="check journal-derived output")
    args = parser.parse_args(argv)
    generated = render_status(args.root)
    output = args.root / "STATUS.md"
    if args.check:
        if not output.exists() or output.read_text(encoding="utf-8") != generated:
            parser.exit(1, "STATUS.md differs from the execution journal; regenerate it.\n")
    else:
        output.write_text(generated, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
