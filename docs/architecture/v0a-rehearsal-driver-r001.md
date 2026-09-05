# Bounded v0a driver r001

Development candidate only, not adopted or invocation-authorized. This additive
adapter leaves every ADR-0487 sealed byte untouched. It selects control-A or
control-B and the existing empty reference blueprint, calls the sealed host with
its real monotonic clock, and accepts only a successful host completion plus an
independently verified persisted trace. No strength or operating-budget claim.

## Interface

```text
python -B -P tools/v0a_rehearsal_driver.py --mode correctness --fixture control-A
  --run-id pontius-v0a-hand-replay-v1-correctness-<unique-suffix>
  --run-root D:/<scratch>/pontius-v0a-hand-replay-v1-correctness-<unique-suffix>
```

The wrapped command above is one argv. Supply an absolute PONTIUS_GIT executable.
Use an LF-pinned detached source clone, its src as PYTHONPATH, PYTHONNOUSERSITE=1,
scrubbed PYTHON/GIT_/PONTIUS_ environment, and D-local TEMP/TMP/TMPDIR as required
by CLAUDE.md. The existing root must be empty, local, non-reparse and named exactly
as the run ID. The only file written is create-new trace.jsonl. Failed outputs
are retained, never retried, overwritten or removed by the driver. Stdout success
is one JSON receipt; boundary failures return nonzero with REFUSED on stderr.
Invalid or missing CLI arguments use argparse's standard usage error and exit 2. A stdout
receipt is not a retained scientific result or a new evidence schema.

The rehearsal mode uses the matching rehearsal namespace with the same options.
It must not be invoked until separate review and controller authorization bind
the finished driver bytes, exact expanded argv, interpreter and disjoint root.
There is no authorized mode and no production owner, launch marker or journal.

## Identity and limits

The seal commit is af90155ebd970d0be6fe26969b121bd213a7f1f2. Preflight compares all
package files to its Git archive before importing pontius; extra sources, native
extensions and bytecode caches refuse. The source bindings JSON is independently
digest-pinned. The actual header manifest hashes all those package files, that
JSON and the three additive driver/test/document files. It uses whole-row-sorted
SHA-256, two spaces, POSIX path, LF rows. The preserved r004 payload manifest is
reported separately; it does not pretend to cover this driver overlay. The new
manifest identifies tested bytes, not an adopted driver seal.

Assumes no concurrent writers, a trusted interpreter/stdlib/Git installation and
scrubbed startup. It is not a filesystem lock, sandbox, complete dynamic import
proof or global run-ID registry. Real publication safety remains the sealed
Windows writer's contract. The independent reader alone does not establish host
publication/accounting; the driver requires both and compares actual saved bytes.

## Focused checks and scope

Run tests/test_v0a_rehearsal_driver.py directly from disposable snapshots, floor
CPython 3.11.15 first, then CPython 3.14.6. Every test execution uses correctness
IDs; testing namespace rejection does not execute a rehearsal. The four existing
v0a suites are unchanged neighboring regression checks. Sealed inventory and CI
files are not modified; this new suite is explicitly direct-run, not registered.
Corruption/failed-receipt seam injections test acceptance only, not native handle
ownership. Native publication is exercised end to end by both control CLI cases.

This build authorizes no commit, push, operational run, policy training, GPU work,
timing distribution or other lane. Stop if adapting the sealed core, adding a new
ownership framework or exceeding 300 driver/300 test lines becomes necessary.
