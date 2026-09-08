# ADR-0280: Exact pre-bet row cache passes CPU/h2 fail-closed control

- Status: accepted label-free engineering control; cache mechanics pass and timed capacity remains closed
- Date: 2026-08-22
- Follows: ADR-0279
- Sealed timing source: `experiments/results/h32-pre-bet-action-width-capacity-v1.json`
- Sealed timing source SHA-256: `d9b0518d6df8c71afaea573cca8668217fec6ed6490544f74b155ab67956f9d7`
- Literal CPU control SHA-256: `5bd6218d0c32673293dd1f2045f5f241fc4e68608c58ba0d9e5ea3bb485da202`
- Row-cache successor SHA-256: `919d17aea50d39a0e7dd96f214ff333a096a7c6738df1298282f90b6fc312f43`
- Row-cache control SHA-256: `1fd15c53529cbd9ebff2b4a34e31ae3b4e775cfc35a85beca002732bc7e47643`

## Question

Can the highest-leverage lawful work reduction selected by ADR-0279 survive
an exact CPU/h2 round trip without a provenance alias, Float64 drift, partial
bundle admission, hidden warm work, or fallback mutation?

This is an engineering control, not a timing or strategy experiment. It runs
no h32 campaign, opens no action-width endpoint, cut, retreat, certificate, or
quality row, and emits no candidate policy.

## Evidence boundary

ADR-0278 remains the only action-width capacity invocation and must never be
rerun. Its result and checkpoint hashes remain unchanged. The new code does
not import, edit, or invoke `h32_pre_bet_action_width_capacity.py`; the sealed
one-size blueprint remains the only external policy.

ADR-0279 established two facts before this implementation. First, the warm
DCFR step does not feed the restricted master. Second, the eleven two-size
initial rows are the largest removable measured block at median `17,292.335
ms`; combining an exact zero-cost row hit with warm removal is the only tested
counterfactual that puts a complete position below 15 seconds, and only seat
5, whose worst proxy is `12,966.497 ms`. That arithmetic remains a ceiling.
This control measures no h32 lookup cost, validation cost, hit rate, or new
capacity.

## Exact bundle contract

`pre_bet_initial_row_cache` persists exactly `2N - 1` current-node affine
rows as one all-or-nothing bundle:

1. one profile-payoff row for every seat; then
2. one fixed-response-payoff row for every nonacting seat.

It stores no policy, master solution, candidate, certificate, or strategy
label. Constants, source values, and coefficient arrays use literal
little-endian Float64 bytes; arrays also bind shape and C ordering. A trusted
external SHA-256 of the complete persisted file is required before JSON is
parsed. Duplicate fields, nonfinite values, numeric type substitution, partial
rows, unexpected shapes, mutable tapes, and files above a shape-derived size
cap fail closed.

The bundle identity binds all of the following independently:

- the complete schema-exact policy and its exact compiled probability tape;
- the normalized factorized belief, hand axes, game structural identity, and
  game range provenance;
- every compiled public node, edge, player role, action type and order,
  information schema, history, and terminal slot;
- every fixed policy row outside the current public node;
- player count, public-node count, acting player, and current public node;
- profile versus fixed-response payoff role and each complete response tape;
- an explicit row-primitive manifest digest; and
- the Float64/endian/source-intercept numerical-contract digest.

The identity builder rejects an incomplete policy instead of silently
accepting implicit uniform defaults. Every profile tape must reproduce the
full-policy tape exactly. Every response tape must retain the acting player's
current-node row exactly. On lookup, every deserialized affine row must again
reproduce the current independently supplied source value within the unchanged
`2e-11` ceiling. Any failure exposes no cached coefficient.

## Warm-free successor boundary

`prepare_pre_bet_restricted_master_successor` has no solver or warm-step
dependency. On an exact hit it admits the `2N - 1` rows and reconstructs the
same `N` gain rows consumed by the current-node restricted master. Lookup,
persisted-byte hashing, parsing, provenance checks, numerical validation, and
gain assembly are included in its monotonic `on_clock_ms` telemetry.

On every miss or assembly error it admits no initial row, no gain row, and no
master solve. On both hit and miss it exposes only a defensive copy of the
immutable blueprint as the external policy. Its explicit counters remain zero
for warm steps, master solves, candidate emissions, and strategy-quality rows.
The cache therefore cannot become an accidental strategy cache or substitute
for the independent final certificate.

## CPU/h2 control result

The literal independent control uses two players, two hands per player, nine
public nodes, and the root as the only open current node. It constructs all
three required initial rows from a direct deal-axis cross-payoff oracle, then
round-trips them through a 2,202-byte cache entry.

The restored flattened row bytes equal the original bytes exactly. All three
source intercepts have zero observed error. Large deterministic current-node
endpoint edits match independent full-policy evaluation with maximum absolute
error `1.3322676295501878e-15`. The restored rows reconstruct two gain rows
that are byte-identical to cold gain construction and reproduce both exact
source deviation gains within `2e-11`. Cold and restored inputs produce the
same restricted-master variables, epigraph values, and lower bound.

Seven focused tests also falsify every one of the eleven SHA-256 identity
fields independently, role reordering, response-tape drift, incomplete policy
identity, source-tape drift, persisted-byte tampering, coefficient tampering,
source-value drift, partial bundles, JSON integer/float aliasing, oversized
entries, mutable probability tapes, unavailable files, and invalid gain
inputs. Every case is a miss or rejected write, and every successor miss
returns an unmodified defensive blueprint with zero work/emission counters.

## Dissent and remaining unknowns

This is a tiny exact control. Its 2,202-byte entry, lookup duration, and master
solve do not predict h32 cost. The control primitive digest covers the literal
CPU oracle and row assembly only; a future one-size or two-size resident GPU
cache must bind its own complete primitive manifest. The test constructs a
known hit and says nothing about whether real source/current-prefix reuse is
frequent enough to justify off-clock speculation.

The cache also does not reduce total computation; it moves exact row
construction off the decision clock. Identity construction and validation may
consume some or all of the conditional `2,033.503 ms` worst-seat-5 headroom.
No result yet shows that the full current-node successor, independent proof,
and one-second reserve fit. The five other acting positions remain outside the
optimistic ADR-0279 counterfactual even at zero lookup cost.

## Decision

Accept the CPU/h2 exact row-cache mechanics and close ADR-0279's cheapest
falsifier. Retain the warm-free cache-to-master preparation as a successor-only
path; do not edit or rerun the sealed ADR-0277 runner. Every cache miss remains
an immutable-blueprint no-op, and every eventual candidate must still pass the
unchanged exact independent certificate before any emission.

The next gate is a separate executable label-free capacity preregistration,
not an immediate GPU run. It must freeze distinct one-size and two-size GPU
primitive manifests, exact off-clock cache-population and trusted-byte-hash
mechanics, on-clock identity/lookup/validation/gain-assembly accounting,
active monotonic campaign deadlines with complete per-unit bounds, the
unchanged 15-second street ledger and one-second reserve, memory caps,
Float64 ceilings, and blueprint fallback. It must define a miss as a completed
fallback outcome and preserve a campaign-wide prelabel barrier. No h32 work is
authorized until that preregistration is clean.

## Claims boundary

This result establishes exact cache serialization, provenance separation,
source-row validation, gain-row identity, and fail-closed fallback on CPU/h2.
It makes no action-width quality, h32 latency, cache-hit-rate, capacity,
optimizer-convergence, certification, deployment, population, multi-seat,
composition, cross-street, chip-EV, AIVAT, exploitation, or poker-strength
claim. The immutable one-size blueprint remains the only external policy.
