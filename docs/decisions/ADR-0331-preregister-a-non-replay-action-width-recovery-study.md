# ADR-0331: Preregister a non-replay action-width recovery study

- Status: accepted prospective non-replay recovery protocol before population source, journal source, synthetic success evidence, or any new sizing value
- Date: 2026-08-23
- Follows: ADR-0330
- Recovery baseline commit: `49044e58fc3a2a582fda11daba4f641da5b3e646`
- Population seed: `pontius|adr-0331|fresh-action-width-nonreplay|population|recovery-commit=49044e58fc3a2a582fda11daba4f641da5b3e646`
- Population-seed SHA-256: `a419d1651708dae88c451546dae5639c8d1c2840a4441b93b712802a9b2541ba`
- Front-Door-Kind: controller-v1
- Front-Door-Research: ADR-0280
- Front-Door-Process: ADR-0331
- Front-Door-Contract: ADR-0307
- Front-Door-Revoked: ADR-0281
- Front-Door-Active-Next: Implement and source-seal only the additive value-free ADR-0331 population and evidence-durability owner; derive 96 ordered h4 river contexts from the exact frozen seed and ADR-0323 generator distribution, reject any semantic overlap with all 96 ADR-0323 development contexts, construct no qualification panel or transfer population, import no sizing result or solver, implement a self-free hash-chain journal whose every append is flushed and fsynced before a successor call can be authorized, recover exact valid prefixes without deleting torn tails, and canonicalize plus rebind one fully populated synthetic 400-observation success journal before any fresh sizing value
- Front-Door-Blockers: no ADR-0331 population source or digest, durable journal source or protocol, synthetic completed-journal pass, qualification schedule, qualified panel, exhaustive teacher, direct greedy result, selected width, transfer seed, capacity result, six-player response model, live strategy bridge, h32/full-range result, earlier street, complete 15-second decision, or poker-strength result exists

## Decision

Preregister a genuinely new action-width development study after ADR-0330's
unretained one-shot failure. This is not permission to replay ADR-0329. It uses
a new seed derived only from the committed failure/repair state, constructs a
new population, and rejects every context whose semantic digest appears
anywhere in the original 96-context ADR-0323 development pool.

The first successor is value-free. It owns only deterministic population
construction, exact non-overlap proof, append-and-fsync journal mechanics,
prefix recovery, and a fully populated synthetic success exercise. It may not
import a sizing result artifact, invoke a consumer or solver, select a panel,
construct transfer, or emit an action.

Only after that source and its exact identities are committed may separate
successors source-seal candidate-blind qualification, an exhaustive teacher,
and a direct closed finite-block mechanism. Every later value phase remains a
separate temporal boundary.

The inherited authority remains visible. ADR-0318 binds HiGHS 1.12.0;
ADR-0319 requires one public HiGHS-DS call per canonical task; All 177 ordered
observations pass under ADR-0320, leaving the separate consumer eligible;
ADR-0321 retains caller-owned legal fallback; and ADR-0322 returns research
evidence or rejection with no action. ADR-0324's value-unopened boundary,
ADR-0325's exactly once invocation rule, and ADR-0326/ADR-0327's exhaustive
bounded development-teacher chain remain prerequisites. ADR-0330 permanently
closes the old campaign and supplies no value or selection to this successor.

## Why this is not a retry

The ADR-0329 schedule, qualified panel, output path, and 400 calls are
permanently closed. The lost values are unknown and supply no seed material,
label, threshold change, branch choice, or population filter here. The new
seed is exactly:

```text
pontius|adr-0331|fresh-action-width-nonreplay|population|recovery-commit=49044e58fc3a2a582fda11daba4f641da5b3e646
```

Its ASCII SHA-256 is
`a419d1651708dae88c451546dae5639c8d1c2840a4441b93b712802a9b2541ba`.
The source must reproduce the ADR-0323 deterministic digest stream,
card/deal construction, structural showdown filter, chip ranges, exact joint
probabilities, kernel-derived legal raise universe, h4 axes, and ordered
accept-until-96 rule. Context IDs use a new ADR-0331 namespace and are not part
of semantic non-overlap.

The new pool rejects unless its 96 semantic digests are unique and disjoint
from all 96 original ADR-0323 development digests. Checking only the 16
qualified contexts is insufficient. Candidate-attempt count, ordered context
digests, legal-universe widths, subset-work ledger, and canonical pool digest
must be frozen at the source seal before any qualification value.

Using the same declared generator distribution preserves comparability. Using
new exact draws and forbidding semantic overlap preserves non-replay status.
No observed ADR-0328 teacher value changes the generator or filter.

## Write-ahead evidence journal

The journal is the authority for evidence survival, not a final in-memory
reduction. It is canonical UTF-8 JSON Lines with one final LF per complete
record. Each record has two layers:

1. a self-free canonical body containing protocol identity, campaign identity,
   record kind, zero-based sequence, previous-record SHA-256, semantic task or
   terminal identity, and the complete payload; and
2. an envelope containing that body plus `record_sha256`, defined as SHA-256 of
   the canonical body bytes.

The first header has sequence zero and a null previous digest. Each successor
record increments by one and names the exact digest of the preceding envelope
line. The envelope hash is never present in its own hash preimage. Canonical
line bytes and their hash-chain relation must be independently recomputed on
read.

Opening is exclusive and no-clobber. After each complete record append, the
writer flushes and calls `fsync` before returning an append receipt. A future
runner may authorize its next solver call only from that receipt. Merely
calling `write`, retaining a Python object, reserving a sentinel, or fsyncing
only at final reduction is insufficient.

Journal reading never repairs, truncates, deletes, renames, or overwrites. It
returns the exact longest valid complete prefix plus the untouched trailing
bytes. A nonempty torn or malformed tail is a terminal infrastructure failure,
but every preceding verified observation remains available. A bad sequence,
previous hash, canonical encoding, record digest, campaign identity, or source
identity rejects at the first offending record and exposes all remaining raw
bytes as the invalid suffix.

The eventual terminal artifact is a reduction over the closed journal. It is
not the sole copy of observations. Final serialization failure therefore
cannot erase already-fsynced call evidence.

## Mandatory synthetic success path

Before any solver-bearing owner is eligible, the value-free source must create
one fully populated synthetic journal with exactly the future realized call
shape: one header, 400 ordered observation records, and one terminal record.
Synthetic payloads must traverse the same body/envelope canonicalizer, append
receipt, reader, hash-chain verifier, and final-reduction serializer intended
for real evidence. A small rejection fixture is not a substitute for the
success-only branch.

The synthetic terminal includes four width summaries and five distinct gate
fields. It must evaluate every nested digest and canonicalize the complete
terminal envelope without recursion. A solver-free rebinder reconstructs all
402 records and the terminal summary from bytes.

Crash controls cut the synthetic journal after every complete record and at
representative byte positions inside a line. Complete prefixes must rebind
exactly; torn tails must remain byte-identical and must never be silently
accepted, dropped, or rewritten. Mocked append controls must prove one flush
and one `fsync` precede every returned receipt.

This synthetic exercise is systems evidence only. Its fake endpoints, gates,
and width are not research observations or quality priors.

## Later value phases

After the population/journal source seal, use distinct prospective successors:

1. candidate-blind qualification: complete legal universe then anchored width
   two, same ADR-0323 interval classifier and stop at the first 16 qualifiers;
2. exhaustive teacher: complete universe plus every anchored subset at widths
   two through six for the sealed new panel;
3. direct greedy mechanism: anchored width two, complete response-closed
   one-raise proposals, exact behavioral-lower/smaller-raise choice, and all
   five frozen development gates; and
4. only after an accepted development selection, a separately seeded untouched
   transfer population.

Each accepted or rejected public call is journaled and fsynced before another
call. A consumer rejection, journal failure, identity drift, or unexpected
exception stops without retry. Later phases may reuse no ADR-0329 value and may
not weaken ADR-0323's threshold, interval, payoff-span, response-closure, or
selection semantics.

The replacement development result chooses or rejects. It is not a transfer
confirmation and cannot retrospectively turn ADR-0329 into a result.

## Gates and kill criteria

Kill the value-free checkpoint on source before this commit; any imported
qualification, teacher, greedy-result, consumer, solver, action, transfer, or
preparation path; a population seed or generator rule different from this ADR;
any semantic overlap with the original 96 contexts; context overlap checked by
ID or position instead of semantic digest; a legal raise universe not derived
from the kernel; a self-referential record hash; a noncanonical line; a missing
flush or `fsync`; authorization of a next call before an append receipt; silent
tail truncation; a synthetic path shorter than 400 observations; a success
serializer not exercised; or any new sizing value before the source seal.

Later value checkpoints additionally die on any retry, changed output path,
post-outcome branch or threshold change, same-panel replay, stack-as-payoff-
span, aggregate mean-of-ratios, point/tolerance tie break, incomplete semantic
response block, transfer-selected width, or production action.

At every source boundary run parse/import controls, exact seed and non-overlap
reproduction, corruption/property tests, synthetic completed-journal and crash
tests, generated STATUS, maintained Markdown links, staged whitespace, and the
complete suite in proportion to the change. Record Ruff as unavailable if it
remains absent; do not silently substitute another linter.

## Evidence classification and dissent

- **Known:** ADR-0330 permanently closed the original campaign; the recovery
  commit and new population seed are exact; all original 96 semantic context
  identities are reconstructable without a solver.
- **Observed:** no ADR-0331 population, journal, synthetic result, or sizing
  value exists at this preregistration boundary.
- **Hypothesis:** an fsynced write-ahead journal can make every completed call
  independently recoverable and a new disjoint population can fairly retest
  the direct action-width mechanism.
- **Rejected:** replaying the original panel, inferring width three from the
  lost run, treating a staging sentinel as evidence durability, or using
  synthetic endpoints as quality evidence.

Supporting the successor: action-width pricing remains a load-bearing scalable
mechanism question, no numerical result escaped from ADR-0329, and a disjoint
commit-derived population prevents reconstruction of the lost sample.

Opposing evidence: the replacement requires another qualification, exhaustive
teacher, and direct run in an h4 fold/call shell; this delays multiway,
full-range, earlier-street, and live-clock work.

Largest unknown: whether the new direct mechanism reaches the teacher's knee
under all five frozen gates without another evidence-path failure.

Cheapest falsifier: the value-free 402-record synthetic journal. Any recursive
digest, missing fsync, prefix mismatch, accepted torn tail, or old-context
overlap kills the successor before a solver call.

Confidence: high in the temporal and non-replay boundary; no confidence claim
is made about a population or journal not yet implemented.

## Claims boundary

This ADR freezes only a future non-replay population and evidence-durability
protocol. It establishes no fresh context, qualified panel, sizing value,
teacher curve, greedy result, selected width, transfer result, capacity fit,
complete 15-second action, six-player response model, h32/full-range result,
earlier street, or poker-strength result.
