# ADR-0163: Preregister the shared-response allocator lifecycle replay

- Status: accepted and preregistered
- Date: 2026-08-21
- Depends on: ADR-0159 through ADR-0162

## Context

ADR-0162 established exact two-target sharing and reduced explicit device state from 8.654 GB to 4.329 GB, but withheld residency authorization because CuPy pool total retained 3.537 GB of unused response-construction scratch. Live pool use was 4.398 GB; reserved pool total was 7.935 GB.

CuPy exposes a lifecycle operation that releases unreferenced default and pinned pool blocks. It must not move or free live arrays. This replay tests that narrow mechanism without changing representation, construction order, targets, policies, labels, thresholds, or the established non-cache reserve.

## Frozen procedure

Reconstruct the identical balanced h32 shared bundle and both target contexts in ADR-0161 order. Record every live device array's logical name, pointer, and byte width across:

- six automaton caches;
- both target belief caches; and
- both directions of the sparse incidence operator.

Record pool used/total and physical free bytes. Call `release_cupy_memory_pool()` exactly once while all contexts and device-array references remain live. Record the same manifest and memory snapshot again. Pool used bytes and the complete pointer/width manifest must remain identical.

Then replay all twelve already-labeled balanced atoms from ADR-0160. The fixed order is acting seat 0 through 5 outermost, with local-blocker then all-seat-strength context inside each seat. Reconstruct every atom from its retained blueprint, retained `search_current1` bundle, retained information key, and scale 1.0. No atom label is recomputed by a complete teacher.

For every replay compare the evaluated utility, best-response, and deviation-gain prefix; stop reason and seat; evaluated-seat count; affected/full/reused terminal counts; and response-action flips with the frozen ADR-0160 row. Record pool and physical memory before and after every certificate. Confirm all live pointers remain identical after the final replay.

## Frozen gates and decision rule

Require two contexts, twelve replays, 64 evaluated seats, zero new strategy-quality labels, exact target and policy identity, exact pointer and post-trim pool-used identity, exact stop/work identity, numeric error at most `1e-9`, total pool below 12 GB, physical free memory at least `5,184,456,164` bytes, each certificate below 60 seconds, and total audit time below 600 seconds.

The unchanged residency rule is evaluated over the post-trim snapshot and every subsequent certificate:

1. headroom below the 12 GB pool ceiling must remain at least `5,184,456,164` bytes; and
2. physical free memory must remain at least the same reserve.

This headroom result is an outcome, not a mechanism gate. If true with all gates passing, simultaneous two-context residency is authorized for retained atomic certification. If false, retain single-context residency. Construction high-water remains reported but does not enter the post-construction lifecycle decision because the trim occurs before the contexts become street-ready.

## Scope

The replay cannot select, reorder, compose, pack, or deploy an atom. It cannot create a strategy label or support a strategy-quality claim. Any future search or scheduler still requires its own end-to-end 15-second ledger.
