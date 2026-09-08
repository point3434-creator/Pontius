# Workload review response r002

The review was of the conversational summary, not the original file. The original
is an untracked local file at
`C:/Users/point/.codex/worktrees/fa55/Pontius/docs/superpowers/specs/2026-09-07-representative-blueprint-workload-design.md`.
It was not committed or uploaded to the primary checkout/handoff repository.
Its bytes remain unchanged; the revised proposal is
[design r002](2026-09-07-representative-blueprint-workload-design-r002.md).

## Disposition

| Review point | Response in r002 |
|---|---|
| Rank decision-changing questions ahead of repeated lookup scaling | Adopted: cap/miss/history, reuse, session attribution, then larger research sizes |
| Bytes per entry and interface limit as headline | Adopted: exact per-street/history wire-byte census, separate internal canonical bytes and retained allocations, largest fitting prefix N_fit and explicit 8,192-entry capacity question |
| Prepare-once arm | Adopted as a measured direct-Python prototype in the proposed protocol, including initial cost, per-hand hashing, H=1/2/8/32 and explicit ownership/lifecycle limitations |
| Promote process decomposition and shrink 384 trials | Adopted: 104 unprofiled CLI sessions plus 16 attribution diagnostics, 120 total; exclusive parent phases and explicit overlapping child-ledger view |
| Seeded, reachable histories and empirical hit rate | Adopted: dealer supplies cards; real host rules/kernel and baseline provider produce trajectories; independent table/query corpora; observed intersections determine hit rate |
| Miss primary, key cost by history | Adopted: history bins around 0/4/8/16/32, separate construction/hash/map/full-provider operations; key hashing remains part of mapping lookup |
| Demote concentrated reuse | Removed from this pass; natural cross-hand repetition remains observable in the frozen query corpus |
| Charged first decision | Adopted: existing response ledger for immediate actors, separately charged preparation for later actors, no double count or new bank credit |
| Prospective linearity check | Adopted: byte-normalized empty-adjusted prediction, 25% excess flag, declared sorting proxy, no refitting at the larger sizes |
| Batch means alongside individual timings | Adopted: 100 batch means and 10,000 individual observations per complete 3.11 microbenchmark cell; clock/loop controls and interleaved hit/miss ordering |
| Floor fully, current interpreter subset | Adopted for performance only; existing two-version source/release correctness gates are preserved |
| Replace vague decision branches with numbers | Adopted: explicit cap, margin, dominance, reuse, miss, memory and scaling triggers in the decision table |

## Numerical and semantic qualifications

The adopted 3.11 report gives 11.4711 ms for source/key construction from existing
observations and 24.7091 ms for prepared lookup construction. The 36.1802 ms sum
combines published medians across those boundaries; it is not an observed charged
runtime hand-start interval. The preparation component predicts 0.198/1.581 seconds
at 8,192/65,536 entries under linear scaling; source plus preparation predicts
0.289/2.316 seconds. Those hypotheses are now labeled separately.

The 35.9448 ms source-plus-provider sum is about 545 times a 0.0659 ms warm miss.
That is work equivalence, not old-versus-new break-even: the old provider's own
setup was 25.8749 ms and its 1,024-entry miss was 6.6080 ms. The revised reuse arm
instead compares retaining versus repeating the current preparation at a matched
direct boundary, including the retained arm's initial cost.

The three-hand elapsed totals average roughly 1.44-1.51 seconds per hand. They
include game work and other costs and do not identify every second as fixed
process overhead. At 1,024 entries, roughly 1.45 seconds is about 40 times 36 ms,
not three orders of magnitude above both preparation and lookup. The proposed
phase attribution measures the decomposition rather than assuming it.

Small table size alone does not establish a real traffic miss probability. The
independent query corpus supplies a measured hit rate for its frozen scripts and
deals, with no claim that it represents a trained policy or human poker traffic.

Repeated preparation is part of the accepted runtime ownership, hand initialization
and accounting contract. The runtime first owns a source graph, then prepares from
that owned source at hand start; the session launches a fresh child each hand.
It is not simply rechecking a mutable caller's original graph on every hand.
Hashing already cached canonical bytes does not independently validate the live
index or external origin. The prototype can estimate savings without establishing
an equivalent replacement integrity contract or persistent worker implementation.

The existing runtime test charges a controlled 2 ms preparation interval into
seat 3's first response, while seat 0 records it as preparation. R002 carries that
distinction into real measurements; it does not add earlier preparation to a later
response deadline.

Individual 60-microsecond-scale timings warrant instrumentation checks, but clock
resolution, call overhead and scheduler variation are distinct quantities. The
proposal records them instead of assuming a Windows timer jitter floor. Batch
throughput and individual empirical latency remain separate outputs.

## Verification and status

This response is based on source/report inspection and arithmetic, not a new poker
or benchmark execution. The original draft and all tracked repository bytes remain
unchanged. R002 and this response are local prospective documentation; neither is
an accepted preregistration or formal cold-review closure.
