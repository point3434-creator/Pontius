# ADR-0115: Correct availability-ledger stage-count aggregation

**Status:** Frozen additive correction after the v1 execution stop and before
any replay result artifact

**Date:** 2026-08-20

## Execution stop

The frozen ADR-0114 v1 invocation stopped with:

```text
NameError: name 'row' is not defined
```

No `h32-candidate-availability-replay-v1.json` artifact was written. The
exception occurred after building the eight in-memory target rows but before
gate construction, aggregate reporting, serialization, or the command-line
summary. No stage selection, cost total, or quality result was printed or
inspected from that process.

## Cause

The gate summary attempted to read stage sizes from an undefined name:

```python
stage_counts = tuple(
    len(row["stage_rows"][index]["available_candidate_ids"])
    for index in range(len(parsed["stages"]))
)
```

The intended stage sizes depend only on the frozen availability table and are
identical for all targets. The target-building loop correctly computed every
per-target stage; only the final structural summary omitted an explicit row.

## Additive correction

Keep the ADR-0114 implementation and config immutable. The v2 adapter supplies
one module-global sentinel whose `stage_rows` are constructed exclusively from
the frozen v1 availability map and stages. Python resolves the otherwise
undefined name to that sentinel during the structural gate, after which the
adapter removes it in a `finally` block.

The adapter does not read a policy, quality vector, selected ID, timing row, or
target label when constructing the sentinel. It changes no source, candidate,
availability iteration, selector, guard, cost formula, gate, or threshold.

The v2 files are:

| File | SHA-256 |
|---|---|
| `src/pontius/h32_candidate_availability_replay_v2.py` | `bddca64e1cbfd21ae2f2647ff2dabafe3f1176ad70fac715d83d98531067a605` |
| `experiments/configs/h32-candidate-availability-replay-v2.json` | `94eae893f3f457cbb0c1b24cd2498c7bc5122a938710ea30b251dad099df0e08` |
| `tests/test_h32_candidate_availability_replay_v2.py` | `c7a0773149bed5e3e99ffd28ba5becd98ecbbb85e8476ef932929f1defc3e041` |

The v2 config pins the immutable v1 config at
`ed3812df2fccaa519e9abd9dc9ef921585597898f134e0e5cdd94d8aad4b2363`
and v1 implementation at
`bdb1b86db792d49e503915c399dbcc0cc3d03b3760acf8410d9ca2562de672ce`.

Four focused v1/v2 tests pass before the corrected execution. One test proves
that the sentinel sizes are exactly `2,4,9,11,13`; the other correction test
rejects any config mutation.

## Evidence boundary

This replay was already declared post-label: the full selected IDs are known.
The failed invocation therefore did not unseal a strategic holdout. It also
did not disclose the ledger's aggregate saved bill or mechanically evaluated
stage identities. The corrected run remains useful for source integrity,
selector replay, and exact accounting.

If v2 fails after emitting any result, no further correction is authorized
under this decision.
