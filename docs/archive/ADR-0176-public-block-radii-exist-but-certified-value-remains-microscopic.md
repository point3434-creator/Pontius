# ADR-0176: Public-block radii exist but certified value remains microscopic

- Status: accepted prospective result
- Date: 2026-08-21
- Implements: ADR-0175
- Clean preregistration commit: `cc53bbf`
- Result: `experiments/results/h32-fresh-public-block-radius-v1.json`
- Result SHA-256: `c069ad15284fc89d8df9da7d8f92120a576d00f8162fdbf58de2c5236d3cf698`

## Result

Every frozen gate passed. The audit independently certified 204 rows: two new
seat-0 blocker targets, three frozen public-block directions, and the shared
34-point geometric halving grid. It finished in `296.53 s`. Peak GPU-pool
total was `7,610,687,488` bytes and physical free memory remained at least
`7,437,549,568` bytes.

Of the 204 rows, 69 were blueprint-cap stops and 135 completed. No row was
objective-bound, and no best-response action switched. Every direction on both
targets therefore had a nonzero admissible grid window, extending from its
largest complete scale through the `2^-33` numerical-floor endpoint.

| Target | Direction | Width | Largest complete scale | Best raw value | Certificate time at boundary |
|---|---|---:|---:|---:|---:|
| panel 2 balanced | seat 1 block | 32 | `2^-15` | `4.1983e-9` | `1,876.85 ms` |
| panel 2 balanced | seat 2 block | 32 | `2^-10` | `8.6197e-9` | `1,248.72 ms` |
| panel 2 balanced | seats 1+2 union | 64 | `2^-15` | `4.4677e-9` | `2,146.57 ms` |
| panel 3 blocker-heavy | seat 1 block | 32 | `2^-12` | `1.3964e-8` | `1,208.84 ms` |
| panel 3 blocker-heavy | seat 2 block | 32 | `2^-5` | `1.4867e-7` | `822.33 ms` |
| panel 3 blocker-heavy | seats 1+2 union | 64 | `2^-12` | `1.5125e-8` | `1,376.79 ms` |

For all six directions, maximum positive value occurred at the largest
complete scale. The immediately larger grid point was cap-bound. On panel 2,
all three boundary failures bound at response seat 0. On panel 3, the seat-1
block and union bound at response seat 0, while the seat-2 block bound at
response seat 4.

## Wall-clock reading

Individual certificates cost `373.44-2,184.30 ms`; a boundary-complete
certificate cost `822.33-2,146.57 ms`. Policy construction was only
`8.66-26.65 ms` per row. Combining each observed boundary row with its same-
target warm-step time and a one-second emission reserve gives a descriptive
single-certificate ledger of `9.11-14.80 s`.

That arithmetic is not a live result: the safe scale was learned from the same
research grid, and the full grid took almost five minutes. It does show that a
future preselected one-certificate rule could fit the street boundary on these
timings. It does not show that such a rule selects a safe or valuable scale on
a fresh target.

## Interpretation

The cap region is not zero-width. Its directional radius is highly contextual:
the largest safe scale varied by 1,024 times, from `2^-15` to `2^-5`. The
absence of selector flips makes this primarily a local gain-sensitivity result,
not a response-switch-kink result.

Finer scaling cures the formal cap violation but does not recover material
value from this one-step generator. The best raw reduction was `1.4867e-7`, or
about `2.94e-6` of that target's blueprint NashConv. The other five best rows
captured about `5.41e-8` to `2.99e-7` of their blueprint NashConv. The seat-1+2
union was governed by the smaller seat-1 radius and added little value beyond
that block.

This separates two claims that must not be conflated: admissible directions
exist, but the observed directions carry microscopic certified value after
they are scaled into the envelope. It does not identify whether the remaining
cause is generator weakness or exhausted local opportunity, and it is not a
strategy-quality or population claim.

## Decision

Accept the prospective mechanism and radius diagnosis. Do not launch a live
holdout merely to validate a fixed scale from these six labels: the radius
varies too widely, and the value available at the certified boundary is too
small to justify optimizing this generator's scale selector first.

Keep the exact radius mapper as an off-clock diagnostic. The next useful audit
should discriminate generator weakness from opportunity exhaustion before
spending more street budget: measure a label-independent local opportunity
proxy and compare the generated direction with a bounded alternative-direction
library on fresh contexts. Preserve the immutable anchor, exact one-shot
certificate, 15-second ledger, and null population/strategy-quality claim.
