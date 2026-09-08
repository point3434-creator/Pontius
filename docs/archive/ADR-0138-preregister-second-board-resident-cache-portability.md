# ADR-0138: Preregister second-board resident-cache portability

## Status

Frozen after ADR-0137 and before any h32 two-size cache, sized policy,
strategy step, or common-game quality measurement on board
`2c 7d 9h Js Qc`.

## Context

The first action-width audit used only `4h 6s Td Qh As`.  ADR-0137 accepted
the common-game mechanism but correctly declined an action-width ranking after
both arms abstained on all four targets.  Its next honest branch was a board-
level replication or a causally new generator.

The independent review reaches the same priority from a broader angle: scale
the board/range corpus before evolving the acceptance contract again.  This
preflight begins that work without pretending the chosen board is entirely
unseen.  It is the original one-size h32 board.  Its average-64 incumbent,
target beliefs, and one-size labels are already revealed; its two-size cache,
two-size policies, and common-game action-width labels have never been
measured.

Before a strategy-bearing replication, the accepted scale-canonical cache must
demonstrate residency on this board.  The fresh-board balanced and blocker-
heavy caches do not prove the original board's ranks or byte bill.  Beginning a
widened step and learning safety from allocator success would repeat the risk
ADR-0127 was designed to remove.

## Frozen sources

The exact original-board identities are supplied by:

- ADR-0099 warm-search result, SHA-256
  `150362ea770c80190c8124148fa66e0a376d98d1bd01b790f3d11e5ad9b5d8a9`;
- its configuration, SHA-256
  `b5cbc538d51f09aad5aa6dca6c860865afd849196b65560ea3338d83293d7f8d`;
- ADR-0137 action-width successor, SHA-256
  `97ac74a9b76eee6ffa8155627ee2e13b16d7e11144894fa1bc1b1cf12fb44d99`;
  and
- ADR-0132 canonical-cache replay, SHA-256
  `9bc385bd463ffd39a8ff587edf58a75ca7663b3ec1d25c90cad3309e8c315349`.

The original action-width and warm-search configurations and implementations
are also pinned.  Their parsers rerun, which transitively revalidates every
solver, cache, bridge, evaluator, checkpoint, and CUDA source they bind.

The machine-readable contract is
`experiments/configs/h32-second-board-resident-cache-v1.json`, SHA-256
`d1ffcc6f2f1a5b40e013d43bb507aea308529e7ae7ec6951d7aa947fe916a9ea`.
The additive runner is
`src/pontius/h32_second_board_resident_cache_preflight.py`, SHA-256
`0b9275030c6fd2e7fd1c5c56dba79a5485a31d8ea46bcddac54c7ad75792ef40`.
The result target is
`experiments/results/h32-second-board-resident-cache-v1.json`.

## Label-free target freeze

Before this ADR, a label-free path rebuilt only the existing one-size source
axes and deterministic likelihood shifts.  It did not construct a two-size
tree, cache, policy, step, or quality label.  Every construction descriptor
matched the core projection of ADR-0099's augmented descriptor, and hand axes
matched exactly.

The resulting target belief digests are frozen as:

| Target | SHA-256 |
|---|---|
| balanced / local blocker seat 3 | `0837fb176c0ef13260c14e230bfb04d79755cdd232b71eabef69b29a2e08ab1a` |
| balanced / all-seat strength | `587407ff8dea2e735aa68470933e4cd009f71bb147fd40561bfa89dd8290d7e7` |
| blocker-heavy / local blocker seat 3 | `a59d5c7efbd0fbc441d3986a83a0cf86f890d52cfb5d6a2f4de8d8d3acd708e5` |
| blocker-heavy / all-seat strength | `221b112ad4407a06ecee2511344f71df93d4469f1572d5ed8569295296c326aa` |

The identity contract requires the exact shift-specific core field set, the
exact seven known parent-only measurement fields, exact core values, digest
identity, and unchanged hand axes.  An unknown or missing field fails closed.

## Frozen workload

For each of the four targets, construct:

1. the raw one-size resident belief plus six automaton caches for bet `3`; and
2. the scale-canonical two-size resident belief plus six caches for bets
   `(3, 6)`.

Alternate cold arm order as `one/two, two/one, two/one, one/two`.  Keep the
shared sparse GPU operators live while releasing unreferenced cache blocks
between arms.  The one-size and two-size games must derive payoff spans `30`
and `48` from their layouts.

Report for every arm:

- belief, automaton, and combined persistent numeric bytes;
- logical automata, canonical basis count, total and maximum middle rank;
- cold construction time;
- pool used and total before and after construction;
- headroom below the 12 GB pool ceiling and physical device free bytes; and
- the two-size/one-size ratios for bytes, logical width, and construction.

No h32 policy may be embedded, initialized, serialized, trained, or evaluated.
The runner executes zero h32 steps and zero h32 quality calls regardless of
memory outcome.

## Headroom decision

Retain the conservative non-cache reserve from ADR-0127:

`9,416,577,536 - 4,232,121,372 = 5,184,456,164 bytes`.

A later strategy audit is memory-authorized only if every one-size and two-
size cache leaves at least that reserve both below the 12 GB CuPy-pool ceiling
and in physical device free memory.  The condition is conjunctive across all
eight cache rows and cannot be narrowed to a favorable target after seeing
bytes.

Headroom is a decision outcome, not a mechanism gate.  A coherent unsafe
measurement passes this preflight and requires a stop before strategy work.

## Frozen gates

The preflight passes only if:

1. all parent, config, implementation, and environment hashes reproduce from
   a clean Git state;
2. the h2 common-game bridge/evaluator/cache control remains within its frozen
   Float64 bounds and stores 378 canonical bases;
3. all four target identities reproduce in frozen order;
4. one-size/two-size topology is 385/763 public nodes, 64/127 terminal groups,
   and 384/762 logical automata;
5. every two-size cache contains exactly 378 canonical bases;
6. one-size and two-size maximum middle rank match per target;
7. layout-derived payoff spans remain 30 and 48;
8. every cold construction is at most 120 seconds and every pool total is at
   most 12 GB;
9. h32 steps, policies, and quality evaluations are all exactly zero; and
10. total preflight time is at most 1,200 seconds.

There is no gate on byte ratio, cold-speed ratio, total logical rank,
headroom-safe outcome, or action-width strategy direction.

## Pre-freeze controls

Five direct controls pass.  They pin the zero-step/outcome-neutral config,
reject source, digest, and resource mutations, reproduce all four label-free
target identities, reject malformed parent projections, and execute the h2
common-game canonical-cache control.

The complete repository passed 566 tests in `100.952 s`.  No original-board
h32 two-size tree or cache was constructed during validation.

## Decision branches

- **Mechanism pass and all-eight headroom safe:** record the cache evidence,
  then separately preregister the second-board wall-clock quality audit.  This
  preflight itself authorizes no step.
- **Mechanism pass but unsafe:** stop before sized policy construction and
  revisit cache residency or the concurrency boundary through a new ADR.
- **Topology, basis, rank, or identity failure:** reject portability and return
  to the representation; do not interpret memory economics.
- **Mechanism failure:** preserve the artifact and make no second-board
  conclusion.

No branch makes a strategy-quality claim.

## Dissent

**Confidence:** very high in target identity and the zero-step contract; high
that scale-canonical residency remains below raw two-size storage; moderate
that the conservative reserve passes on all original-board targets.

**Opposing evidence:** ADR-0110's original-board one-size resident caches were
4.327 GB balanced and 2.962 GB blocker-heavy, while fresh-board two-size
canonical caches were 4.020 GB and 3.295 GB.  Those crossed family orderings
show why fresh-board memory should not be treated as a universal bound.

**Largest risk:** this is still a revealed strategy board, so a later quality
comparison expands action-width replication but not the underlying board
corpus.  A genuinely new board remains necessary before a broad contract
claim.

**Cheapest falsification:** the balanced/local target's two-size cache.  It is
expected to be the largest original-board row and can reject the later strategy
audit without advancing any policy state.
