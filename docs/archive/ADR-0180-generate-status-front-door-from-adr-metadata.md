# ADR-0180: Generate the status front door from ADR metadata

- Status: accepted process decision
- Date: 2026-08-21
- Depends on: ADR-0178, ADR-0179

## Context

`STATUS.md` stopped at ADR-0078 while the repository advanced through the
prepared 15-second h32 street, exact incremental certificates, clean-fringe
autopsies, public-block radii, and positive generator identification. Its 797
hand-maintained lines made the nominal continuation front door both expensive
to update and actively misleading.

The durable evidence already lives in numbered ADRs. Duplicating their complete
history in a second manually edited narrative creates an avoidable consistency
problem.

## Decision

Replace the hand-maintained status narrative with compact generated output.
`pontius.status_generation` parses every canonical ADR title plus Status, Date,
and Decision metadata and renders:

1. the latest accepted non-process research result;
2. that ADR's exact Decision section;
3. any newer open preregistration;
4. the latest process decision and canonical evidence-protocol link;
5. the most recent 24-decision ledger; and
6. a complete ADR-header fingerprint and decision count.

Add a regression test requiring `STATUS.md` to equal a fresh render. Any new or
renamed ADR therefore makes the normal test suite fail until the front door is
regenerated. Historical detail remains in the ADRs and Git history rather than
being copied into the status file.

## Usage

Regenerate after adding or changing ADR metadata:

```powershell
$env:PYTHONPATH = "src"
python -m pontius.status_generation
```

Use `--check` in verification scripts when no write is desired.

## Consequences

The front door becomes short, current, and mechanically auditable. The latest
research Decision section remains the source of next-work language, so this
mechanism does not invent a roadmap from titles alone. A malformed ADR title
or duplicate number fails closed.
