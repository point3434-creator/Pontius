# ADR-0282: Make the fifteen-second street wall authoritative

- Status: accepted process and charter correction
- Date: 2026-08-22
- Follows: ADR-0281

## Question

What wall-clock contract should govern current and future Pontius research?

PROJECT retained the original 5-250 ms budget ladder as historical context
while the active h32 lineage, executable configurations, and acceptance gates
used a 15,000 ms street ledger. That dual wording makes an obsolete target look
available for future interpretation.

## Decision

Make one shared 15,000 ms wall-clock budget per street the authoritative
contract. It covers all charged agent work across every action by the agent on
that street; the budget does not reset at each action. The existing 1,000 ms
synchronization and action-emission reserve remains inside the 15,000 ms wall.

The earlier 5, 20, 50, 100, and 250 ms targets are superseded historical
context. They may remain in immutable ADRs, sealed result descriptions, or code
that reproduces those historical artifacts, but they must not govern a new
acceptance gate, roadmap checkpoint, deployment claim, or maintained front-door
description.

The separate multi-target campaign ceiling remains a research-execution guard;
it neither enlarges nor replaces the 15-second per-street live wall. Off-clock
preparation remains separately reported and may not be charged ambiguously.

## Consequences

- Future configs and preregistrations must name a 15,000 ms street wall.
- A future full-hand loop must carry one deadline across all actions on the
  same street instead of constructing a new 15-second allowance per action.
- Latency evidence must report charged street wall time, off-clock preparation,
  and campaign wall time as distinct quantities.
- Historical sub-250 ms measurements remain valid measurements but are not the
  project target.

## Claims boundary

This decision corrects the governing contract only. It does not show that a
complete street, full hand, widened action set, full range, or deployed agent
currently fits 15 seconds, and it does not reinterpret any sealed result.
