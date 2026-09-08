# ADR-0164: Allocator lifecycle authorizes two-context atomic residency

- Status: accepted result
- Date: 2026-08-21
- Implements: ADR-0163
- Result: `experiments/results/h32-shared-response-allocator-lifecycle-v1.json`

## Result

All fifteen frozen gates passed from clean preregistration commit `f190d1f`. The replay retained both balanced h32 target contexts, released only unreferenced CuPy pool blocks once, and reproduced all twelve ADR-0160 atoms in the frozen alternating-context order.

All 790 named live device arrays retained identical pointers and byte widths before trimming, after trimming, and after all replays. Pool used bytes were unchanged by trimming. This covers the shared automaton halves, both target beliefs, and both directions of the sparse incidence operator.

## Memory lifecycle

Before trimming:

- pool used: 4,398,026,752 bytes;
- pool total: 7,934,734,336 bytes;
- physical free: 7,219,445,760 bytes.

The lifecycle operation released 3,497,373,184 pool bytes and increased physical free memory by 3,508,535,296 bytes without changing live pool use. Immediately after trimming, pool total was 4,437,361,152 bytes.

Across all subsequent atomic certificates, pool total reached 6,579,812,864 bytes and physical free memory never fell below 8,572,108,800 bytes. Headroom below the 12 GB ceiling was therefore 5,420,187,136 bytes, exceeding the unchanged 5,184,456,164-byte reserve by 235,730,972 bytes. Both branches of the frozen headroom rule pass.

Construction high-water remained 7,934,734,336 bytes and is still reported. It does not govern street-ready residency because trimming occurs after cold construction and before either immutable context is offered to the online path.

## Replay exactness and latency

All 64 evaluated seat rows reproduced their retained prefix and work identities. Maximum errors were:

- utility: `1.56e-15`;
- best-response value: `1.67e-15`;
- deviation gain: `8.75e-16`.

The four retained cap outcomes and eight complete outcomes reproduced exactly, including stop seat, affected/full/reused terminal counts, and response-action flips. Certificate wall time ranged from 297.30 to 1,025.06 ms. All twelve rows fit the 15,000 ms street budget with the frozen 1,000 ms emission reserve.

These remain certificate-only ledgers. Search, atom construction, scheduling, and emission beyond the fixed reserve are not measured.

## Decision

Authorize simultaneous residency of the two balanced one-size target contexts for retained atomic certification, provided the lifecycle is followed exactly:

1. construct the shared automaton bundle and both immutable belief/response contexts off the street clock;
2. release unreferenced CuPy default and pinned pool blocks once;
3. preserve the live shared arrays and contexts; and
4. perform source-relative incremental certification without rebuilding the bundle.

This closes the cross-target residency question raised by ADR-0160. The next research step is not more cache representation work. It is a separately preregistered end-to-end scheduler ledger that includes candidate generation, deterministic atom extraction, certification, packing overhead if any, and emission reserve inside 15 seconds.

## Scope

Authorization covers the two retained balanced target shifts, one-size river tree, existing blueprint anchors, and atomic certification. It does not authorize a new target, blocker-heavy co-residency, atom composition, union safety, strategy deployment, or any strategy-quality claim.
