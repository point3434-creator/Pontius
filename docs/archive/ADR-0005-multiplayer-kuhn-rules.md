# ADR-0005: Generalized multiplayer Kuhn rules

**Status:** Accepted, 2026-08-18.

## Decision

The configurable benchmark uses `N + 1` ordered cards for `N` players. Each
player antes one chip. In seat order, players check or make the sole one-chip
bet. Once a player bets, every other player calls or folds in cyclic order; no
raises are permitted. If all check, everyone shows down. Otherwise the highest
card among the bettor and callers wins.

## Reason

"Multiplayer Kuhn" is not sufficiently precise by itself. An explicit rule
contract makes utilities, information sets, and experiments reproducible while
retaining multiway beliefs, folding, bluffing, and response-order effects.

## Limitation

Results are not directly comparable to papers using a different generalized
Kuhn betting convention. Publications must restate these rules.

