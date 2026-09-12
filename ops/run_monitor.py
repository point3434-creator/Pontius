#!/usr/bin/env python3
"""Read-only progress window for a long Pontius run on the Linux box.

Serves a run's ``progress.jsonl`` and a small auto-refreshing page, so a run can
be watched from a phone over Tailscale. It never writes to the run directory and
never starts, stops, or inspects a process; it is a window, not a controller.

    python3 run_monitor.py --run-root ~/pontius-runs/blueprint-001 \
        --host 100.64.0.2 --port 8777

Bind to the Tailscale address rather than 0.0.0.0 so the page is reachable from
your devices without also being offered to everything on the local network.
"""

from __future__ import annotations

import argparse
import html
import json
import os
from datetime import datetime, timezone
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

TAIL_BYTES = 256 * 1024
DEFAULT_ROWS = 40


def read_tail_records(progress_path: Path, limit: int) -> list[dict]:
    """Return the last decodable JSON objects from the tail of a JSONL file."""
    if not progress_path.exists():
        return []
    with progress_path.open("rb") as handle:
        handle.seek(0, os.SEEK_END)
        size = handle.tell()
        handle.seek(max(0, size - TAIL_BYTES))
        chunk = handle.read()
    records: list[dict] = []
    for line in chunk.decode("utf-8", errors="replace").splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        try:
            record = json.loads(stripped)
        except json.JSONDecodeError:
            continue
        if isinstance(record, dict):
            records.append(record)
    return records[-limit:]


def ordered_columns(records: list[dict]) -> list[str]:
    """Return every key seen across records, in first-seen order."""
    columns: list[str] = []
    for record in records:
        for key in record:
            if key not in columns:
                columns.append(key)
    return columns


def format_value(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, float):
        return f"{value:,.6g}"
    if isinstance(value, (dict, list)):
        return json.dumps(value)
    return str(value)


def describe_staleness(progress_path: Path) -> str:
    if not progress_path.exists():
        return "no progress file yet"
    written = datetime.fromtimestamp(progress_path.stat().st_mtime, timezone.utc)
    seconds = (datetime.now(timezone.utc) - written).total_seconds()
    return f"last write {seconds:,.0f} s ago ({written.isoformat(timespec='seconds')})"


def render_page(run_id: str, records: list[dict], progress_path: Path) -> str:
    columns = ordered_columns(records)
    header = "".join(f"<th>{html.escape(name)}</th>" for name in columns)
    rows = []
    for record in reversed(records):
        cells = "".join(
            f"<td>{html.escape(format_value(record.get(name)))}</td>" for name in columns
        )
        rows.append(f"<tr>{cells}</tr>")
    table = (
        f"<table><thead><tr>{header}</tr></thead><tbody>{''.join(rows)}</tbody></table>"
        if records
        else "<p class='empty'>No progress records yet.</p>"
    )
    return f"""<!doctype html>
<html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="refresh" content="15">
<title>Pontius run {html.escape(run_id)}</title>
<style>
  :root {{ color-scheme: light dark; }}
  body {{ font: 14px/1.5 system-ui, sans-serif; margin: 1.5rem; }}
  h1 {{ font-size: 1.2rem; margin: 0 0 .25rem; }}
  .meta {{ opacity: .7; margin-bottom: 1rem; }}
  .scroll {{ overflow-x: auto; }}
  table {{ border-collapse: collapse; font-variant-numeric: tabular-nums; }}
  th, td {{ border-bottom: 1px solid rgba(128,128,128,.35); padding: .35rem .7rem;
            text-align: left; white-space: nowrap; }}
  th {{ position: sticky; top: 0; }}
  .empty {{ opacity: .7; }}
</style></head><body>
<h1>Pontius run {html.escape(run_id)}</h1>
<div class="meta">{html.escape(describe_staleness(progress_path))}
 &middot; showing {len(records)} most recent records, newest first
 &middot; <a href="/progress.jsonl">raw</a> &middot; <a href="/latest.json">latest</a></div>
<div class="scroll">{table}</div>
</body></html>
"""


class MonitorHandler(BaseHTTPRequestHandler):
    server_version = "PontiusMonitor/1"
    run_root = Path()
    rows = DEFAULT_ROWS

    def do_GET(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler interface
        progress_path = self.run_root / "progress.jsonl"
        if self.path in ("/", "/index.html"):
            records = read_tail_records(progress_path, self.rows)
            page = render_page(self.run_root.name, records, progress_path)
            self.respond(HTTPStatus.OK, "text/html; charset=utf-8", page.encode("utf-8"))
        elif self.path == "/latest.json":
            records = read_tail_records(progress_path, 1)
            payload = records[-1] if records else {}
            self.respond(HTTPStatus.OK, "application/json", json.dumps(payload).encode())
        elif self.path == "/progress.jsonl":
            data = progress_path.read_bytes() if progress_path.exists() else b""
            self.respond(HTTPStatus.OK, "application/x-ndjson", data)
        else:
            self.respond(HTTPStatus.NOT_FOUND, "text/plain; charset=utf-8", b"not found\n")

    def respond(self, status: HTTPStatus, content_type: str, body: bytes) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: object) -> None:
        return


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-root", type=Path, required=True)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8777)
    parser.add_argument("--rows", type=int, default=DEFAULT_ROWS)
    args = parser.parse_args(argv)

    MonitorHandler.run_root = args.run_root.expanduser().resolve()
    MonitorHandler.rows = args.rows
    server = ThreadingHTTPServer((args.host, args.port), MonitorHandler)
    print(f"serving {MonitorHandler.run_root} at http://{args.host}:{args.port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
