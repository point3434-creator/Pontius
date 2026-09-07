# Versioned bounded-read performance result

These are local engineering cost observations, not research or playing-strength
evidence. The fixed diagnostic definition was recorded before timing. All new
artifacts are retained at `D:/Pontius/tmp/bounded-reads-v2-20260907-001`.

## Result

| Fixed 12-trial control | Full parent launch-through-exit seconds |
| --- | ---: |
| Earlier original, unprofiled | 88.9310463 |
| Earlier original confirmation, unprofiled | 95.5539101 |
| Earlier in-memory bounded-read prototype, unprofiled | 47.8585712 |
| Source-bound v2, unprofiled | 49.2236669 |
| Source-bound v2, recursively profiled | 58.2827262 |

V2 used commit `356f87e1352eca92c863442638de080687939998`, admitted source
manifest `7d13b5f62159f50408c9bd4c13ad25e816ff5e56b25fb7ff6dfb583823548d30`.
This local frozen candidate precedes the final documentation/registration closure;
its v2 runner and admitted source population are the same production bytes. The
profile launcher is separately retained; it instruments Python child launches.

The new ordinary run is 44.6-48.5% shorter than the two earlier ordinary controls,
or 1.81-1.94 times their throughput. It corresponds to about 878 trials/hour for
this fixed workload. This is one v2 matrix, with prior controls at a different time
and a snapshot one directory level shallower. Local scheduling, cache and path
depth effects remain; these are not confidence intervals or general speed bounds.
The previous prototype/control pass also retained its own filesystem-noise caveat.
No other agent scans or test payloads ran during the new timing pass.

All 24 new trials completed with cleanup complete and no capture, action, hand,
session, work-cutoff or action-deadline failure. Full applied-action sequences,
settlements, carried stacks, counters and chip arithmetic match the earlier fixed
control. Both v1 and v2 public readers accepted the old and both new completed
artifacts. This establishes finite behavioral compatibility, not strategy quality.

## Remaining runner cost

The parent profile reports 39 source checks at 22.895 s cumulative and 21,605
stable reads at 23.122 s cumulative. Native stat calls consume 15.852 s self time
across 1,115,893 calls. Parent CPU is 24.719 s versus the earlier profiled parent's
61.969 s. The old read-request bottleneck has been substantially removed; repeated
file/directory identity checks are now the main parent compute cost.

The 31.727 s in sleep is primarily waiting for child work. Parent/child intervals,
source checks, stable reads and cumulative function costs overlap; do not add them
or treat waiting as removable computation. A future source-check optimization
needs its own integrity design. No source checks were removed or cached here.

## Non-empty blueprint cost

Five batches of 20 warm public calls per case, after three warmups; medians of
batch means, not individual-call tail percentiles. Fixed preflop states, all CALL
entries, lexicographic private-card pairs. First hit, last hit and miss are tested.

Provider times span the hit/miss cases. Retained bytes cover the source and its
owned provider; digest times cover the whole table.

| Entries | Provider ms | Digest ms | Retained Python bytes |
| ---: | ---: | ---: | ---: |
| 0 | 0.053 (miss) | 0.0023 | 2,089 |
| 16 | 0.144-0.145 | 0.0920 | 34,601 |
| 128 | 0.795-0.797 | 0.7149 | 232,185 |
| 1,024 | 6.021-7.068 | 5.8513 | 1,770,225 |

At 1,024 entries, source construction took 11.49 ms and provider construction
24.67 ms in single observations; traced combined peak allocation was 2,219,918
bytes. Memory is a separate tracemalloc pass over new table/provider allocations,
excluding already-built observations, interpreter/native memory and process RSS.
It is neither an artifact-size measure nor a whole-process safety bound.

The 20-call profile attributes 0.208871 of 0.225565 seconds in provider calls to
the whole-table digest path, about 92.6% cumulative. The current public action
lookup scans the entry tuple and recalculates each key digest, sorts the table
representation, serializes it and hashes it on every selection. Timings support
addressing repeated digest computation first, then an immutable exact-key index.
They do not establish the speed of an implementation we have not built.

Next recommendation: design a versioned immutable table/provider that computes
its canonical digest once at construction and validates an exact-key lookup index.
Keep artifact canonical bytes/digests, owned snapshots, hit/miss behavior and legal
action checks unchanged. Measure memory as well as lookup latency. This is more
directly useful to repeated blueprint/research work than a native engine rewrite.
The current measurements do not justify extrapolating to millions of entries,
changing the 15-second action contract, or claiming any learned-policy strength.

## Reference applicability

[PokerKit lookup tables](https://github.com/uoftcprg/pokerkit/blob/main/pokerkit/lookups.py)
are a useful pure-Python example of preparing lookup structure outside repeated
evaluation. [OpenSpiel's Python algorithms](
https://github.com/google-deepmind/open_spiel/tree/master/open_spiel/python/algorithms)
include `external_sampling_mccfr.py`, a future learning/traversal reference.
Its C++ game core and Python
algorithms are considered separately. Neither library was installed, copied into the
runner, or speed-compared here. The earlier primary-source reference review also
considered RLCard and PokerTH; no engine migration follows from this pass.
