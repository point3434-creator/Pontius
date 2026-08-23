"""Generate the repository front door from durable ADR metadata."""

from __future__ import annotations

import argparse
import hashlib
import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path

_ROOT = Path(__file__).parents[2]
_DECISIONS = _ROOT / "docs/decisions"
_OUTPUT = _ROOT / "STATUS.md"
_TITLE = re.compile(r"^# ADR-(\d{4}):\s+(.+?)\s*$")
_FILENAME = re.compile(r"^ADR-(\d{4})-.+\.md$")
_FIELD = re.compile(
    r"^-?\s*\*{0,2}([A-Za-z][A-Za-z0-9-]*):\*{0,2}\s*(.+?)\s*$",
    re.IGNORECASE,
)
_ADR_REFERENCE = re.compile(r"\bADR-(\d{4})\b")
_FRONT_DOOR_FIELDS = (
    "front-door-kind",
    "front-door-research",
    "front-door-process",
    "front-door-contract",
    "front-door-revoked",
    "front-door-active-next",
    "front-door-blockers",
)


@dataclass(frozen=True, slots=True)
class DecisionHeader:
    number: int
    title: str
    status: str
    date: str
    path: Path
    decision: str
    metadata: tuple[tuple[str, str], ...]

    def field(self, name: str) -> str | None:
        key = name.lower()
        return dict(self.metadata).get(key)


def _section(lines: list[str], heading: str) -> str:
    target = f"## {heading}".lower()
    start = next((index + 1 for index, line in enumerate(lines) if line.strip().lower() == target), None)
    if start is None:
        return ""
    end = next((index for index in range(start, len(lines)) if lines[index].startswith("## ")), len(lines))
    return "\n".join(lines[start:end]).strip()


def _section_first_line(lines: list[str], heading: str) -> str:
    body = _section(lines, heading)
    return next((line.strip() for line in body.splitlines() if line.strip()), "")


def read_decision_headers(decisions_dir: Path = _DECISIONS) -> tuple[DecisionHeader, ...]:
    """Read every numbered ADR and its durable decision metadata."""

    rows = []
    for path in sorted(decisions_dir.glob("ADR-*.md")):
        lines = path.read_text(encoding="utf-8").splitlines()
        if not lines:
            raise ValueError(f"empty decision file: {path}")
        filename_match = _FILENAME.fullmatch(path.name)
        if filename_match is None:
            raise ValueError(f"decision filename is not canonical: {path}")
        title_match = _TITLE.fullmatch(lines[0])
        if title_match is None:
            raise ValueError(f"decision lacks a canonical first-line ADR title: {path}")
        if filename_match.group(1) != title_match.group(1):
            raise ValueError(f"decision filename/title number mismatch: {path}")
        fields: dict[str, str] = {}
        header_end = next(
            (
                index
                for index, line in enumerate(lines[1:], start=1)
                if re.match(r"^##(?:\s|$)", line)
            ),
            len(lines),
        )
        for line in lines[1:header_end]:
            match = _FIELD.match(line)
            if match is not None:
                key = match.group(1).lower()
                if key in fields:
                    raise ValueError(f"decision repeats metadata field {key!r}: {path}")
                fields[key] = match.group(2).strip()
        status = fields.get("status") or _section_first_line(lines, "Status") or "unspecified"
        date = fields.get("date", "")
        rows.append(
            DecisionHeader(
                number=int(title_match.group(1)),
                title=title_match.group(2).strip(),
                status=status,
                date=date,
                path=path,
                decision=_section(lines, "Decision"),
                metadata=tuple(sorted(fields.items())),
            )
        )
    rows.sort(key=lambda row: row.number)
    numbers = [row.number for row in rows]
    if not numbers or len(numbers) != len(set(numbers)):
        raise ValueError("decision numbers must be nonempty and unique")
    if numbers != list(range(1, len(numbers) + 1)):
        raise ValueError("ADR decision numbers must be contiguous from ADR-0001")
    return tuple(rows)


def _link(row: DecisionHeader, root: Path) -> str:
    relative = row.path.relative_to(root).as_posix()
    return f"[ADR-{row.number:04d}]({relative})"


def _header_digest(rows: tuple[DecisionHeader, ...], root: Path) -> str:
    payload = "\n".join(
        "|".join(
            (
                str(row.number),
                row.title,
                row.status,
                row.date,
                row.path.relative_to(root).as_posix(),
                repr(row.metadata),
            )
        )
        for row in rows
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


@dataclass(frozen=True, slots=True)
class FrontDoorSnapshot:
    controller: DecisionHeader
    research: DecisionHeader
    process: DecisionHeader
    contract: DecisionHeader
    revoked_by: tuple[tuple[int, int], ...]
    active_next: str
    blockers: str


def _single_reference(value: str, field: str) -> int:
    match = re.fullmatch(r"ADR-(\d{4})", value.strip(), re.IGNORECASE)
    if match is None:
        raise ValueError(f"{field} must be one exact ADR-NNNN reference")
    return int(match.group(1))


def _front_door(rows: tuple[DecisionHeader, ...]) -> FrontDoorSnapshot:
    controllers = []
    for row in rows:
        present = tuple(
            field for field in _FRONT_DOOR_FIELDS if row.field(field) is not None
        )
        if present and len(present) != len(_FRONT_DOOR_FIELDS):
            missing = sorted(set(_FRONT_DOOR_FIELDS) - set(present))
            raise ValueError(
                f"ADR-{row.number:04d} has an incomplete front-door snapshot: {missing}"
            )
        if present:
            controllers.append(row)
    if not controllers:
        raise ValueError("status generation requires an explicit front-door snapshot")
    if controllers[-1].number != rows[-1].number:
        raise ValueError(
            "the latest ADR must carry a complete front-door snapshot"
        )
    by_number = {row.number: row for row in rows}

    def require_current_authority(row: DecisionHeader, *, role: str) -> None:
        if not row.status.lower().startswith("accepted"):
            raise ValueError(f"{role} must reference a currently accepted ADR")
        try:
            parsed_date = date.fromisoformat(row.date)
        except ValueError as exc:
            raise ValueError(f"{role} must carry an ISO decision date") from exc
        if parsed_date.isoformat() != row.date:
            raise ValueError(f"{role} must carry a canonical ISO decision date")
        if not row.decision.strip():
            raise ValueError(f"{role} must carry a nonempty Decision section")

    def resolve(
        owner: DecisionHeader,
        value: str,
        field: str,
    ) -> DecisionHeader:
        number = _single_reference(value, field)
        if number > owner.number:
            raise ValueError(f"{field} cannot reference a future ADR")
        try:
            return by_number[number]
        except KeyError as exc:
            raise ValueError(f"{field} references a missing ADR") from exc

    def declared_revocations(row: DecisionHeader) -> tuple[int, ...]:
        value = row.field("front-door-revoked")
        assert value is not None
        if value.strip().lower() == "none":
            return ()
        tokens = tuple(token.strip() for token in value.split(",") if token.strip())
        if not tokens:
            raise ValueError("Front-Door-Revoked must name ADRs or explicit none")
        numbers = tuple(
            _single_reference(token, "Front-Door-Revoked") for token in tokens
        )
        if len(set(numbers)) != len(numbers):
            raise ValueError("Front-Door-Revoked repeats an ADR")
        for number in numbers:
            if number >= row.number:
                raise ValueError("Front-Door-Revoked must reference an earlier ADR")
            if number not in by_number:
                raise ValueError("Front-Door-Revoked references a missing ADR")
        return numbers

    cumulative_revocations: set[int] = set()
    first_revoker: dict[int, int] = {}
    validated_snapshots: list[
        tuple[
            DecisionHeader,
            DecisionHeader,
            DecisionHeader,
            DecisionHeader,
            str,
            str,
        ]
    ] = []
    for snapshot_controller in controllers:
        if snapshot_controller.field("front-door-kind") != "controller-v1":
            raise ValueError("Front-Door-Kind must be exactly controller-v1")
        require_current_authority(snapshot_controller, role="front-door controller")
        research_value = snapshot_controller.field("front-door-research")
        process_value = snapshot_controller.field("front-door-process")
        contract_value = snapshot_controller.field("front-door-contract")
        active_next = snapshot_controller.field("front-door-active-next")
        blockers = snapshot_controller.field("front-door-blockers")
        assert None not in (
            research_value,
            process_value,
            contract_value,
            active_next,
            blockers,
        )
        research = resolve(
            snapshot_controller,
            str(research_value),
            "Front-Door-Research",
        )
        process = resolve(
            snapshot_controller,
            str(process_value),
            "Front-Door-Process",
        )
        contract = resolve(
            snapshot_controller,
            str(contract_value),
            "Front-Door-Contract",
        )
        require_current_authority(research, role="Front-Door-Research")
        require_current_authority(process, role="Front-Door-Process")
        require_current_authority(contract, role="Front-Door-Contract")
        declared = set(declared_revocations(snapshot_controller))
        forgotten = cumulative_revocations - declared
        if forgotten:
            rendered = ", ".join(f"ADR-{number:04d}" for number in sorted(forgotten))
            raise ValueError(
                "Front-Door-Revoked cannot forget prior revocations: " + rendered
            )
        for number in declared - cumulative_revocations:
            first_revoker[number] = snapshot_controller.number
        cumulative_revocations = declared
        if not str(active_next).strip():
            raise ValueError("Front-Door-Active-Next must be explicit")
        if not str(blockers).strip():
            raise ValueError("Front-Door-Blockers must be explicit, including none")
        for field, head in (
            ("Front-Door-Research", research),
            ("Front-Door-Process", process),
            ("Front-Door-Contract", contract),
        ):
            if head.number in declared:
                raise ValueError(f"{field} references a revoked ADR")
        for match in _ADR_REFERENCE.finditer(str(active_next)):
            number = int(match.group(1))
            if number not in by_number or number > snapshot_controller.number:
                raise ValueError(
                    "Front-Door-Active-Next references an unavailable ADR"
                )
            if number in declared:
                raise ValueError("Front-Door-Active-Next references a revoked ADR")
        validated_snapshots.append(
            (
                snapshot_controller,
                research,
                process,
                contract,
                str(active_next).strip(),
                str(blockers).strip(),
            )
        )

    controller, research, process, contract, active_next, blockers = (
        validated_snapshots[-1]
    )
    revoked_numbers = tuple(sorted(cumulative_revocations))

    return FrontDoorSnapshot(
        controller=controller,
        research=research,
        process=process,
        contract=contract,
        revoked_by=tuple((number, first_revoker[number]) for number in revoked_numbers),
        active_next=active_next,
        blockers=blockers,
    )


def render_status(root: Path = _ROOT, *, recent_count: int = 24) -> str:
    """Render a compact current status whose freshness is testable."""

    if (
        isinstance(recent_count, bool)
        or not isinstance(recent_count, int)
        or recent_count <= 0
    ):
        raise ValueError("recent decision count must be a positive integer")
    rows = read_decision_headers(root / "docs/decisions")
    latest = rows[-1]
    snapshot = _front_door(rows)
    rows_by_number = {row.number: row for row in rows}
    research = snapshot.research
    process = snapshot.process
    contract = snapshot.contract
    revoked_by = dict(snapshot.revoked_by)
    digest = _header_digest(rows, root)

    lines = [
        "# Project Status",
        "",
        "> Generated by `python -m pontius.status_generation` from ADR metadata.",
        "> Do not edit this file by hand; `test_status_generation` enforces freshness.",
        "",
        "## Active checkpoint",
        "",
        f"Latest accepted research result: {_link(research, root)} — {research.title}.",
        "",
        f"Status: {research.status}.",
        "",
        "## Governing runtime contract",
        "",
        f"{_link(contract, root)} — {contract.title}.",
        "",
        "## Current decision",
        "",
    ]
    lines.extend(
        (
            snapshot.controller.decision
            or "The front-door controller has no explicit Decision section."
        ).splitlines()
    )
    lines.extend(["", "## Active next", "", snapshot.active_next])
    lines.extend(["", "## Revoked authorities", ""])
    if not snapshot.revoked_by:
        lines.append("None.")
    else:
        for revoked_number, revoker_number in snapshot.revoked_by:
            lines.append(
                f"- {_link(rows_by_number[revoked_number], root)} — revoked by "
                f"{_link(rows_by_number[revoker_number], root)}."
            )
    lines.extend(["", "## Evidence protocol", ""])
    lines.append(f"Latest process decision: {_link(process, root)} — {process.title}.")
    lines.append("")
    lines.append("Canonical rules: [PROJECT.md](PROJECT.md#evidence-and-dissent-protocol).")
    lines.extend(
        [
            "",
            "## Recent decision ledger",
            "",
            "| ADR | Date | Status | Decision |",
            "|---:|---|---|---|",
        ]
    )
    for row in rows[-recent_count:]:
        rendered_status = row.status
        if row.number in revoked_by:
            rendered_status = (
                f"{rendered_status}; revoked by ADR-{revoked_by[row.number]:04d}"
            )
        lines.append(
            f"| {_link(row, root)} | {row.date or '—'} | {rendered_status} | {row.title} |"
        )
    lines.extend(
        [
            "",
            "## Repository snapshot",
            "",
            f"- Latest ADR: {_link(latest, root)} — {latest.title}.",
            f"- Governing runtime contract: {_link(contract, root)} — {contract.title}.",
            f"- Numbered decisions: {len(rows)}.",
            f"- ADR-header SHA-256: `{digest}`.",
            f"- Current blockers: {snapshot.blockers}.",
            "",
            "## Required reading before continuation",
            "",
            "1. [PROJECT.md](PROJECT.md)",
            "2. [STATUS.md](STATUS.md)",
            "3. [ROADMAP.md](ROADMAP.md)",
            f"4. {_link(snapshot.controller, root)}, {_link(research, root)}, {_link(contract, root)}, and their dependencies",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    rendered = render_status()
    if args.check:
        if not _OUTPUT.is_file() or _OUTPUT.read_text(encoding="utf-8") != rendered:
            raise SystemExit("STATUS.md is stale; run python -m pontius.status_generation")
        print("STATUS.md is current")
        return
    _OUTPUT.write_text(rendered, encoding="utf-8")
    print(f"wrote {_OUTPUT}")


if __name__ == "__main__":
    main()
