# ADR-0055: Freeze the multiway context generator before strategy labels

**Status:** Accepted before any source or candidate policy was solved

**Date:** 2026-08-19

## Decision

Freeze the now-tested deterministic context and range-target implementation
before running ADR-0054. Add only
`expected_context_generator_sha256` to the machine configuration, with value
`806a0238ea2f0f9148209e1e515b35a17ae2fb5731de0ec103317557f2b253aa`.

This changes the configuration SHA-256 from
`511303952baa67bdde3824fca3b6f59099e8270dd9f799e4ac73643c0253244f`
to `807d511a920ee1bcb13d5cf54ca61991c30bb63845dabfb9e04d318c1f8ef0a4`.
No workload, seed, group, range family, target, solver, checkpoint, timing rule,
acceptance condition, or gate changes.

## Evidence boundary

At this amendment, only deterministic construction and property tests have run.
They establish that six development groups produce 24 contexts, all selected
hands retain support, all four range shifts preserve support and structure,
and no strategy label enters boundary features. No CFR policy, NashConv,
best-response value, coalition response, or acceptance outcome has been
computed for a frozen context.

The generator is commit `74bebf8`; its seven tests pass in 0.500 seconds. The
experiment runner must reject any generator-hash mismatch.
