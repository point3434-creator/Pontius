# ADR-0332: Seal the non-replay population and durable evidence journal

- Status: accepted value-free population and evidence-durability source seal; every replacement qualification and sizing value remains unopened
- Date: 2026-08-24
- Follows: ADR-0331
- Recovery baseline commit: `49044e58fc3a2a582fda11daba4f641da5b3e646`
- Preregistration commit: `de166d81d5f91df48e6ec0ecea27000e04fd4f30`
- Durable-journal source canonical-LF SHA-256: `a9f815a41abc8d9977375e0c8e71f66f788dd8d811d016735cb08ffa06bf5c11`
- Non-replay source canonical-LF SHA-256: `b870feb17d6e344b130f7b30d8b776be5b40537e3e71b7a14b9b4d2bcbae3e92`
- Journal protocol SHA-256: `27589eaa9320927582012fc57adb573e2df7fc333cd1b942e832e306c3840986`
- Non-replay protocol SHA-256: `2603976fb0ef862f7a7c73ec56def6787550228b80c35839dd3f3c0f79a21621`
- Population pool SHA-256: `441790b2e24fa2187ad7c64b456d75b3ccd8e9d9951ce340eabc16eb4255821c`
- Synthetic journal SHA-256: `66c9b441fa71597280d4b7ee7a64a70079e212b5594332a8f4e1cc4dc0e9e136`
- Front-Door-Kind: controller-v1
- Front-Door-Research: ADR-0280
- Front-Door-Process: ADR-0332
- Front-Door-Contract: ADR-0307
- Front-Door-Revoked: ADR-0281
- Front-Door-Active-Next: Source-seal only the ADR-0331 candidate-blind qualification owner on the exact ADR-0332 population; freeze its complete-universe-then-anchored-width-two order, first-16-qualifier stop, conservative interval classifier, append-receipt-before-next-call rule, failure-complete journal reduction, no-retry semantics, and prospective output identity before any consumer call or replacement sizing value
- Front-Door-Blockers: no ADR-0331 qualification schedule, qualified panel, exhaustive teacher, direct greedy result, selected width, transfer seed, capacity result, six-player response model, live strategy bridge, h32/full-range result, earlier street, complete 15-second decision, or poker-strength result exists

## Decision

Accept the first ADR-0331 checkpoint. The repository now contains a sealed,
value-free replacement population and a general append-and-`fsync` evidence
journal. It also exercises the complete future success shape synthetically
before any replacement consumer call. This is a source and systems result, not
an action-width result.

`fresh_action_width_nonreplay` reproduces the exact ADR-0323 digest stream,
card/deal construction, structural showdown filter, pot/stack ranges, exact
joint probabilities, kernel-derived legal universe, and accept-until-96 rule
from the ADR-0331 seed. It reconstructs the complete sealed ADR-0323 pool and
rejects any new context whose label-free semantic digest appears among those
96 contexts. The resulting 96 contexts are unique and disjoint from all 96
original contexts.

The durable journal is a reusable infrastructure primitive. Its record digest
hashes a canonical self-free body; an outer envelope adds that digest; and each
successor body binds the SHA-256 of the preceding complete envelope line,
including its final LF. Production construction is possible only through an
exclusive `xb` open. One complete line is written, flushed, and `fsync`ed
before a receipt exists. A short write or durability exception poisons the
writer. Readers never edit input and return the exact longest verified prefix
plus every untouched invalid or torn trailing byte.

The inherited authority remains explicit. ADR-0318 binds HiGHS 1.12.0;
ADR-0319 requires one public HiGHS-DS call per canonical task; All 177 ordered
observations pass under ADR-0320, leaving the separately bounded consumer
eligible. ADR-0321 retains the caller-owned legal fallback, and ADR-0322 returns
research evidence or rejection with no action. ADR-0323 remains value-free;
ADR-0324 remains value-unopened; ADR-0325's invocation ownership is exactly
once; and ADR-0326/ADR-0327 retain the exhaustive bounded development-teacher
chain. ADR-0328 only authorizes direct closed finite-block greedy research,
while ADR-0330 permanently closed its failed invocation. ADR-0331's
append-and-fsync evidence rule governs this replacement and every later call.

The next authorized boundary is source-only candidate-blind qualification on
this population. It may define the exact schedule, classifier, journal
payloads, stop state, failure reduction, and prospective artifact identity. It
may not make the first consumer call or inspect a sizing value until that
source is independently committed.

## Exact value-free population

The preregistered ASCII seed reproduces its frozen SHA-256
`a419d1651708dae88c451546dae5639c8d1c2840a4441b93b712802a9b2541ba`.
The compiler accepts 96 contexts after 551 candidate attempts. Their legal
raise universes contain 7, 9, or 11 consecutive kernel-derived raise-to totals;
the new population happens to contain exactly 32 contexts of each universe
width. Pot counts are 29/24/23/20 at 6/10/14/20 chips. These counts are
descriptive frozen identities, not stratification targets or quality evidence.

The ordered original-context list hashes to
`ffe2c99dc084d50c172fa98a63ebba30f6423936bcf7a83ece706f6a5a8cac6e`.
The ordered new-context list hashes to
`5bc94eaf0122e38dcdbd028a67f6ef353c8dfe69486695bf138ea9a838cfc3c6`.
Their set intersection is empty. Context IDs are separately ordered
`adr0331-nonreplay-000` through `adr0331-nonreplay-095` and do not participate
in semantic overlap.

The prospective anchored-subset ledger is 96, 672, 2,144, 4,128, and 5,312 at
raise widths two through six, or 12,352 subsets total. It is work provenance,
not evidence that any subset is valuable.

The new source imports no qualification, teacher-result, greedy-result,
solver, transfer, preparation, or action module. It reuses the already sealed
value-free ADR-0323 context/generator definitions, whose complete transitive
source closure is included in the ADR-0332 manifest. No LP is compiled and no
consumer is invoked.

## Durable journal contract

Canonical payloads admit nulls, booleans, strings, integers, arrays, and
string-keyed objects. Floating-point JSON numerals, duplicate keys,
noncanonical whitespace/order, CRLF records, non-ASCII encodings, missing or
extra record fields, and malformed digests reject. Numerical evidence must use
exact strings such as hexadecimal float encodings.

Sequence zero is the sole header and has no predecessor. Every later record
has a contiguous sequence and the prior complete-line hash. A terminal is
final. Protocol and campaign identity must remain constant. Generic recovery
accepts a complete nonterminal prefix as recoverable evidence without calling
it a completed campaign; any malformed or torn suffix remains byte-for-byte
available with its first failure offset and reason.

The production writer's constructor initially admitted a caller-supplied
stream, which could have bypassed exclusive no-clobber opening. Adversarial
review found that route before the source seal. Construction now requires an
internal capability issued only after the exclusive path succeeds; tests
inject streams by intercepting that same exclusive factory. This is a real
pre-seal defect repair, not evidence from a value-bearing invocation.

## Fully populated synthetic success

The systems-only fixture contains exactly one header, 400 observation records,
and one terminal: 402 records and 610,098 canonical bytes. The observation
partition is 16 synthetic width-two initial calls followed by 120/104/88/72
synthetic candidate calls for target widths three through six. These counts
exercise the future realized call shape; all endpoints, menus, gates, and the
fixture's synthetic selected width three are fake and carry no research prior.

The terminal evaluates and serializes four populated width summaries and five
separately named gate fields. Each summary digest hashes its self-free core;
the terminal digest then hashes its own self-free core containing those
summaries; and the journal body/envelope adds two more acyclic digest layers.
The terminal digest is
`3f806252c38e3e51f62ac3fb3a9f7e7ac44cf97e1706bcdd947cb039eed57445`.
A solver-free rebinder reconstructs every record, observation, summary, nested
digest, chain edge, and terminal reduction from bytes.

Crash controls cut the fixture after every one of its 402 complete records.
Every prefix rebinds exactly, and only the full terminal prefix is complete.
Cuts at the beginning, middle, and final byte of representative header,
observation, and terminal lines preserve the entire partial line as an invalid
suffix. A sophisticated corruption can recompute all generic body, envelope,
and chain digests while preserving all 402 records; the generic journal then
accepts its structure, but the synthetic semantic rebinder rejects it. Nested
summary corruption is rejected at the summary digest before frozen-fixture
comparison.

An actual temporary-file exercise calls the operating-system `fsync` path 402
times and returns 402 contiguous receipts. Independent stream controls prove
write, flush, file-descriptor lookup, and `fsync` occur in that order before a
receipt. Exclusive re-open rejects without changing the original bytes.

## Controls

Eighteen focused tests pass in 15.656 seconds. They cover exact protocols and
source closure, strict canonical parsing, self-free hashes, line chaining,
write/flush/`fsync` order, poisoning, exclusive construction, every complete
crash prefix, representative torn tails, protocol/campaign/sequence/chain
corruption, exact all-96 overlap exclusion, deterministic population and work
identities, the full synthetic writer, and the solver-free semantic rebinder.

The complete repository suite ran 1,362 tests in 414.386 seconds and finished
`OK (skipped=2)`. Ruff remains unavailable in the repository virtual
environment; no substitute linter is represented as that gate.

## Evidence classification and dissent

- **Known:** the seed, source closure, protocols, ordered old and new semantic
  identities, pool, work ledger, and synthetic journal identities are exact.
- **Observed without solving:** the new 96-context population is unique and
  disjoint from all 96 old contexts; 402 durable append paths and every crash
  prefix pass; the completed nested serializer does not recurse.
- **Unknown:** every qualification endpoint, panel membership, teacher value,
  greedy recovery, gate outcome, selected width, transfer result, live cost,
  and poker strength.
- **Rejected:** treating synthetic width three as evidence, calling a complete
  generic hash chain semantically sufficient, bypassing exclusive writer
  creation, deleting a torn suffix, or reviving ADR-0329.

Supporting the next source-only checkpoint: the cheapest ADR-0331 falsifier
passes, its population is sealed before values, and a future failure can retain
each completed call instead of depending on terminal publication.

Opposing evidence: this is still h4 heads-up river research with a fold/call
response shell. Another source boundary, qualification invocation, exhaustive
teacher, and direct invocation remain before even a development-selected
width, and all remain far from six-player production response closure.

Largest unknown: whether candidate-blind qualification finds 16 contexts and
whether the later direct mechanism satisfies all five frozen gates on this new
population.

Cheapest falsifier: source-seal the qualification order and feed its journal
reducer synthetic accepted, rejected, torn, and unexpected-stop prefixes. Any
call without a prior durable receipt, identity drift, lost accepted endpoint,
or panel from a non-target stop kills qualification before values.

Confidence: high in the deterministic source and finite controls; no
statistical, action-width, latency, or strength confidence is claimed.

## Claims boundary

This decision establishes one value-free h4 population, a general durable
journal primitive, and a systems-only populated fixture. It establishes no
replacement sizing value, qualified panel, teacher result, greedy result,
selected width, transfer result, capacity fit, complete 15-second action,
six-player response model, h32/full-range result, earlier street, or poker-
strength result.
