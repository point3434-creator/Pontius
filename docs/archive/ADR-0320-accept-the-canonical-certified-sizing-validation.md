# ADR-0320: Accept the canonical certified-sizing validation

- Status: accepted complete canonical correctness pass; a separately preregistered certified-v2 reduced-sizing consumer is eligible but absent
- Date: 2026-08-23
- Follows: ADR-0319
- Invocation commit: `fada0172713603c905bc236579cb6761ecfb687e`
- Runner canonical-LF SHA-256: `5116c1d4b2632da76cf83e6d7d015b190e061330094d27b3c9719631a89252e1`
- Campaign artifact: `experiments/results/certified-sizing-canonical-validation-v1.json`
- Campaign bytes: `5,022,120`
- Campaign SHA-256: `5a2a75a9cf0ddaf60795597aa6ff3f788d4bfc7ccf5519813f37856dad02f9f5`
- Assessment artifact: `experiments/results/certified-sizing-canonical-validation-assessment-v1.json`
- Assessment SHA-256: `a3c360c61ae6edd28eb2df68b83339a549d6726a151c60fee46bc488dc54bfd9`
- Result-control canonical-LF SHA-256: `6113755cef58a5070886ec327195ad91de38c3e4ff0fca1b88cbac912009d97f`
- Front-Door-Kind: controller-v1
- Front-Door-Research: ADR-0280
- Front-Door-Process: ADR-0320
- Front-Door-Contract: ADR-0307
- Front-Door-Revoked: ADR-0281
- Front-Door-Active-Next: Preregister and source-seal only an additive certified-v2 reduced-sizing consumer contract that binds an exact semantic context and an explicitly supplied kernel-derived legal raise-to set, returns the certified behavioral lower bound, outward upper bound, policy, and fold/call responses or a typed rejection to the caller-owned legal fallback, and passes only unsealed differential/corruption controls before any fresh action-width value; edit no ADR-0318/0319 source, historical v1 consumer, retained artifact, allowance, or v1-v4 owner
- Front-Door-Blockers: no certified-v2 consumer, exact legal-action bridge, typed production rejection/fallback ledger, or complete-decision integration exists; the finite pass covers only 177 canonical compact LPs with 4x4 sizing contexts and 48 micro programs, not h32/full-range action pricing, exact ladder regret, row-column closure, fresh population transfer, earlier streets, a 15-second resolver, or poker strength

## Question

Does ADR-0318's canonical HiGHS-DS sizing adapter pass the exact prospective
ADR-0319 correctness gate on every canonical ADR-0312 base, with one public
proposal per base and independent exact or behavioral/certificate authority?

## Decision

Yes, on the preregistered finite boundary. Accept the retained canonical
campaign and its frozen assessment. All 177 ordered observations pass: 48
exact micro LPs and 129 reduced-sizing LPs. Every observation records exactly
one public HiGHS-DS call, no runner failure, and complete family-specific
evidence. The conjunctive assessment therefore marks a separately
preregistered certified-v2 reduced-sizing consumer eligible.

This does not connect a consumer or select an action width. The pass is over
canonical compact LPs in the frozen CPython 3.14.6, NumPy 2.5.2, SciPy 1.18.0,
and HiGHS 1.12.0 runtime. Transformed matrices, h32/full-range masters,
multi-street games, legal six-player action construction, complete decisions,
and strategy quality remain outside the result.

## One authorized invocation and retained bytes

ADR-0319 was committed at `fada017` with a clean worktree before invocation.
The sealed entry point was called exactly once. It verified the committed
runner/dependency/runtime identities, reconstructed schedule SHA-256
`36f34eb820bfaa4b58747201c9b27779553d0f8e250c73786da34542b5d8cba4`,
and returned one immutable campaign. A scratch invocation owner outside the
repository created the campaign path exclusively and byte-verified it before
applying the frozen assessment. No source, corpus, option, allowance, or gate
changed between ADR-0319 and the call, and the campaign was not rerun.

The retained campaign is 5,022,120 canonical JSON bytes with SHA-256
`5a2a75a9cf0ddaf60795597aa6ff3f788d4bfc7ccf5519813f37856dad02f9f5`.
The separately retained 701-byte assessment has SHA-256
`a3c360c61ae6edd28eb2df68b83339a549d6726a151c60fee46bc488dc54bfd9`.
Both artifacts use exact hexadecimal float encoding and are marked `-text` to
preserve byte identity.

## Complete conjunctive result

| Gate field | Result |
|---|---:|
| Complete canonical schedule | pass |
| Exactly one public call per base | pass, 177/177 |
| Passed observations | 177 |
| Failed observations | 0 |
| Exact micro passes | 48/48 |
| Certified-sizing passes | 129/129 |
| Failed base ids | none |
| Certified-v2 consumer eligibility | open |

Every retained observation agrees with its value-free task on ordinal, base
id and hash, family, path, and canonical LP hash. The family inventory is the
one known ADR-0310 regression, 48 exact micro bases, and 128 fresh sizing
bases. No transformed representation or alternate backend entered the result.

## Exact micro path

All 48 public HiGHS-DS returns are optimal with status zero and an independent
exact vertex enumeration. Every micro semantic failure list is empty. The
maximum absolute returned-objective error against the exact rational optimum
is `1.4210854715202004e-14`; the maximum absolute outward-certificate gap above
the exact optimum is `1.7053025658242404e-13`; and the maximum primal violation
is `7.105427357601002e-15`. No certificate clipped a wrong-sign multiplier.

HiGHS used zero through seven iterations. Recorded solver-call wall time was
1.579 ms median, 1.830 ms p95, and 1.886 ms maximum across these micro LPs.
Exact enumeration, runner setup, imports, serialization, and artifact I/O are
not included in those solver-call times.

## Certified-sizing path

All 129 ADR-0318 solutions pass the adapter and ADR-0313's separate canonical
reconstruction. Adapter and verifier records agree exactly on raw primal and
multipliers, normalized policy, response actions, clips, reported and
reconstructed values, behavioral lower bound, outward upper bound, signed gap,
and certificate. No policy coordinate required a tolerated clip, no
certificate clipped a wrong-sign multiplier, every signed interval is
positive, and the independent sizing failure count is zero.

The maximum behavioral reconstruction error is
`4.3520742565306136e-13` chips, the maximum reported-objective error is
`9.094947017729282e-13` chips, and the maximum certified interval is
`8.493117320540478e-11` chips. The worst interval belongs to fresh context 59's
full-integer arm. The already disclosed native-regression base passes this
adapter with a `6.372696814693768e-11`-chip interval, 161 HiGHS iterations, and
a 5.815 ms recorded solver call. This resolves that canonical consumer call;
it does not rehabilitate the native solver.

The 64 minimum/all-in arms have width two. Full-integer arms span widths 9,
11, 15, 19, 23, or 29. Across all 129 sizing bases, HiGHS iterations range
from 9 to 218. Recorded sizing-solver wall time is 1.968 ms median, 3.888 ms
p95, and 5.815 ms maximum. ADR-0318 adapter verification is 1.386 ms median,
6.102 ms p95, and 8.344 ms maximum. The assessment sums 0.370277 seconds of
solver-call time across both paths and 0.245068 seconds of sizing-adapter
verification.

These component timings are diagnostics from 177 independent compact calls.
They exclude complete-decision construction, full ranges, response-row
generation, continuation evaluation, GPU work, exact micro enumeration,
runner orchestration, fallback, synchronization, emission, and most of the
15-second action path. They cannot be compared with per-iteration master
times or called a complete solve latency.

## Persisted-result controls

Six result-only controls pass without invoking a solver. They verify exact
campaign and assessment bytes/hashes, canonical JSON, source/runtime/corpus/
schedule provenance, all 177 value-free task bindings and call counters, every
micro exact/certificate record, every sizing adapter/independent-verifier
agreement, zero clips and failures, and the frozen assessment endpoints.

The repository-wide suite passes 1,271 tests in 338.969 seconds with two
intentional environment-dependent skips. Generated STATUS, maintained
Markdown links, exact artifact controls, and whitespace checks pass. No
ADR-0318 or ADR-0319 source changed after the invocation commit. Ruff is
unavailable in the pinned environment, so this checkpoint makes no Ruff claim.

## Consequences and next boundary

The compact canonical sizing path now has a trustworthy proposer/certificate
stack on this finite distribution. A fresh additive consumer may therefore be
preregistered. It must bind exact request provenance and legal raise-to actions
from the betting kernel, expose the behavioral lower and outward upper
endpoints, and fail to the Legal Decision Spine's caller-owned immutable legal
fallback rather than silently falling back to native simplex. Historical
`reduced_river_sizing_oracle` and every v1-v4 owner remain unchanged.

Only after that consumer is source-sealed and independently controlled should
Pontius preregister a fresh action-width mechanism. The promising direction is
kernel-derived legal actions plus own-action block column pricing, alternating
with opponent-response row generation until both violation families close.
On reduced games, full legal integer sizing can then supply an exact
regret-versus-width curve; fresh-panel replication is reserved for population
transfer. Reduced costs are omission-pricing certificates under the current
dual and row set, not by themselves the finite value of admitting a whole
size block. This paragraph is a future hypothesis, not a result or mandate.

## Claims boundary

This result establishes a clean finite canonical correctness pass and bounded
eligibility for a later additive reduced-sizing consumer. It is not a
certification of arbitrary games, transformed representations, future
software versions, production inputs, legal six-player raise construction,
full action width, ladder regret, column generation, opponent-row closure,
preparation-bank hit rate, full range width, h32, turn architecture, blueprint,
full-hand loop, 15-second complete-decision fit, marginal decision quality per
millisecond, AIVAT, NashConv, league strength, coalition safety, or poker
strength. Systems timing is not a strategy-quality prior. No revoked
experiment, external publication, or thesis change is authorized.
