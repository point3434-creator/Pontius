# ADR-0001: Initial game and objective

**Status:** Accepted, 2026-08-18.

## Decision

The initial full game is six-player, 100bb, no-rake, no-ante cash NLHE. The
deployment objective is strategy quality over a wall-clock latency frontier on
the named single workstation.

## Alternatives

Tournament stacks, rake, and opponent-specific exploitation were considered.
They add strategically material variables before the baseline can be measured.

## Revisit condition

Add stack distributions, antes, or rake only after the fixed-game control agent
passes checkpoint C5.

