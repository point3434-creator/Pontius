# ADR-0174: Public-node blocks fit but two directions are cap-bound

- Status: accepted prospective result
- Date: 2026-08-21
- Implements: ADR-0173
- Clean preregistration commit: `c6b6318`
- Result: `experiments/results/h32-fresh-public-block-value-v1.json`
- Result SHA-256: `cfc6334e6f0a132f36cbc64bb6a0d22219df5925a506cbc673ef7ea14ee84305`

## Result

Every frozen gate passed. Each one-step candidate changed all 6,144 infosets.
The structural rule produced exactly six disjoint 32-infoset public-node blocks
per target, one complete hand-axis slice at each selected public history.

All six live block unions were attempted and finished before the 14-second
cutoff. The two hard ledgers, including the one-second emission reserve, were
`14,102.11 ms` and `10,544.31 ms`. Peak GPU-pool total was `7,626,233,344`
bytes and physical free memory remained at least `7,605,321,728` bytes. The
immutable blueprint was emitted twice.

No union completed the envelope. Full-six, prefix-four, and prefix-two all
stopped at response seat 2's blueprint cap on both targets:

| Target | 192-infoset union | 128-infoset union | 64-infoset union |
|---|---:|---:|---:|
| panel 3 balanced | 1,203.63 ms | 1,191.33 ms | 899.46 ms |
| panel 1 blocker-heavy | 823.58 ms | 824.13 ms | 662.56 ms |

Early cap stops make these bills measurements of rejection, not complete
wide-candidate verification costs.

## Constituent-block autopsy

On both targets:

- acting-seat 1's 32-infoset block alone stopped at response seat 2's cap;
- acting-seat 2's block also stopped, at response seat 3 on panel 3 and response
  seat 0 on panel 1;
- blocks for acting seats 0, 3, 4, and 5 completed; and
- no block was objective-bound and no best-response action switched.

The largest complete-block values were only `2.2217e-8` and `1.2555e-9` raw
NashConv. Because the full unions stopped, no union value fraction or six-way
interaction residual is defined.

The prefix-two result identifies acting-seat 1's block as sufficient for every
live union rejection. Acting-seat 2 is an additional unsafe direction but is
not needed to explain the common response-seat-2 stop.

## Interpretation

Widening one infoset to a coherent 32-hand public-node slice did not recover a
usable candidate at scale 1.0. It did improve diagnosis: the failure is not a
certificate-granularity artifact in which individually safe blocks become
unsafe only when bundled. A constituent block is already cap-bound, on the same
response seat, on both fresh targets.

The absence of response-action flips means these observed stops did not require
a best-response selector kink. That makes a directional admissible-radius
measurement the natural next test: reduce scale along the frozen unsafe blocks
and find whether cap compliance appears before the numerical floor, while
recording certified value per recertification second.

This result does not show that all wider blocks are unsafe, does not estimate a
target population, and does not authorize selecting one of the four complete
post-ledger blocks. Their labels were deliberately ineligible.

## Decision

Accept the prospective mechanism and diagnosis. Do not widen these scale-1.0
blocks further and do not reorder from the observed values.

The next preregistration should use new target beliefs and a shared geometric
halving grid inherited from the certificate's Float64 floor. Apply it to
structurally chosen public-node blocks and their frozen unions, recertifying
each scale exactly against the immutable blueprint. The primary measurements
are admissible radius, binding response seat, certified value, and value per
wall-clock second; no scale label may be reused compositionally.
