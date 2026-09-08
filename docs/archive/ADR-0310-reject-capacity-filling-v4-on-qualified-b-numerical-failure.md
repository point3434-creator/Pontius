# ADR-0310: Reject capacity-filling v4 on qualified-B numerical failure

- Status: accepted negative qualification result; capacity-filling v4 is rejected and parked before every candidate value and integration path
- Date: 2026-08-23
- Follows: ADR-0309
- Front-Door-Kind: controller-v1
- Front-Door-Research: ADR-0280
- Front-Door-Process: ADR-0310
- Front-Door-Contract: ADR-0307
- Front-Door-Revoked: ADR-0281
- Front-Door-Active-Next: Preregister a candidate-independent native-simplex robustness audit over the sealed failing LP and a prospectively fixed adversarial corpus, with an independent solver or certificate used only as a diagnostic control; do not repair and retry ADR-0305 qualification, reopen capacity-filling v4, open its representative or candidate values, or connect any parked action lattice to replay, blueprint, the convex master, resolving, or strategy paths
- Front-Door-Blockers: qualified B hits the frozen numerical kill criterion before a final panel exists; qualified A's passing selection is provisional and cannot authorize evaluation alone; capacity-filling v4 and v1-v3 are parked; the native compact-LP solver has one reproducible robustness failure without a replacement evidence contract; no action abstraction has passed the complete reduced quality-and-power boundary

## Verdict

Reject capacity-filling pot-odds v4 at ADR-0305's replicated qualification
gate and park it before the first representative, v3-control, or v4 value.
Qualified A reaches its twenty-fourth unambiguous sizing-opportunity context
and passes every numerical and teacher control. The subsequently authorized
qualified-B invocation stops at context 21 when the full-integer compact LP
fails the native solver's primal verification. ADR-0305 makes any numerical
failure a kill criterion; A cannot waive B and a diagnostic alternate solver
cannot replace the frozen oracle after outcome.

This is a qualification-infrastructure rejection, not evidence that the v4
mechanism is strategically weak. No final A/B evaluation panels are accepted.
The 48-context representative family and every v3 and v4 candidate value
remain unopened. No replay, blueprint, convex-master, resolver, or strategy
module was imported or connected.

## Qualified-A pass, provisional only

The owned candidate-blind runner opens a contiguous 73-context A prefix and
stops exactly when context 72 supplies its twenty-fourth qualifier. It records
24 qualifying, 49 nonqualifying, and zero ambiguous contexts. The selected
indices are:

```text
0,3,4,8,10,13,14,17,28,30,34,35,42,43,52,53,55,56,58,63,64,69,70,72
```

Deterministic identities are:

- qualification result:
  `ff16b19045880646699f11cc3eb6ea8a6d2d69db7391d62ae5649c36aafd576d`;
- provisional A panel:
  `c2a737abadb726219c2a55d5d785258abc790da44947d89c5a80fbcd80f2e45d`;
- leading-two-by-two teacher control:
  `11c59dc8cb9d76f309fdf7b512bb8a4660f6109cdb9341522bfd59da5fa43da6`;
- A campaign:
  `c292dd30782d26a43ef71038f7f2fd55cabfa1004f6f049b8476e69df3f7462d`.

The selected A contexts span all ten frozen pot values, five of six stack
values, and 24 distinct showdown-sign matrices. Diversity is diagnostic, not
a substitute for the frozen opportunity classification. The smallest
absolute distance from any opened A gap to its normalized threshold is
`4.555320289812703e-4` chips, versus the `1e-8`-chip ambiguity guard.

The A prefix completes 146 full/narrow compact LPs. Its retained contexts add
24 compact leading-two-by-two LPs and 24 independently enumerated bounded
normal-form teachers. Thus A completes 170 compact LPs and 24 teachers.

| Diagnostic | A maximum | Frozen ceiling |
|---|---:|---:|
| Probability-simplex residual | `1.0525e-13` | `1e-9` |
| Chip-objective reconstruction error | `1.4798e-12` chips | `1e-9` chips |
| Compact LP primal-dual gap | `2.1033e-12` chips | `1e-9` chips |
| Lower-envelope violation | `6.0397e-14` chips | `1e-9` chips |
| Full-arm simplex pivots | 349 | 4,096 |
| Narrow-arm simplex pivots | 41 | 4,096 |
| Teacher compact/value difference | `3.6416e-13` chips | `1e-9` chips |
| Teacher primal-dual gap | `7.4929e-13` chips | `1e-9` chips |
| Teacher compact pivots | 19 | 4,096 |

One first serial A observation on this workstation took `23.9752` seconds.
That is an offline whole-campaign diagnostic, not per-solve, per-iteration,
real-game, or 15-second action latency.

## Qualified-B numerical stop

B is opened only after an exact reproduced A campaign passes. Contexts 0
through 20 complete both frozen arms: 11 qualify, 10 do not qualify, and none
is ambiguous. Their qualifying indices are:

```text
0,1,2,4,6,7,8,10,11,16,20
```

The forty-third B solver call is the full-integer arm at
`adr0305-v4-qualified-b-c21`. It fails before producing a verified solution,
before the context's minimum/all-in arm, and before any context 22-95 value.
The failure binds:

- pool:
  `23c186d3c393c9d233558c8150e9bb1f7c38f75f6e3cf1d7c7685341057f5870`;
- structural context:
  `9ebc519357c17b7ac100b4eaf40996ca774484b974f6bfe0145cc060b99dd440`;
- oracle context:
  `df0e8a00d5b0816a4a8b99a7f9fc7d1b000b38e9fb009f88e70ffa47827336e2`;
- structural-to-oracle binding:
  `a3dc51f7fb5fff0a1794e1fa477f1d959204db616d1d320fea15773b1215a022`;
- stopped-failure record:
  `03c5dc4f00c0429d3c615352a1d52f9c64dec0d3b4c4cf72f6d7cc171e3a26fe`.

The failing context has pot 24, stack 30, and the derived payoff span 84. Its
full arm is the exact integer tuple 2 through 30, producing 236 variables and
240 inequalities. The native solver performs 375 pivots, then raises
`AssertionError: linear-program solution fails primal verification`.

All 42 completed B-prefix LPs satisfy their frozen controls. Their maximum
probability residual is `7.3053e-14`, chip-objective error
`2.2312e-12` chips, compact duality gap `4.5475e-13` chips, and lower-envelope
violation `4.9738e-14` chips. Maximum completed full/narrow pivot counts are
336 and 37. The closest completed classification lies
`0.0014535600943236205` chips from its threshold.

## Bounded numerical diagnosis

An unchanged native-tableau reconstruction reproduces the failure. Its
returned variables violate zero-based constraint row 215 by
`4.049601922810204` chips, compared with the native verification allowance
`4.199999999999999e-8`; the miss is about 96.4 million times the allowance,
not a borderline tolerance comparison. Reconstructing the frozen LP layout
identifies that row as responder 3's call-envelope constraint at bet 18.

As a non-authoritative diagnostic only, SciPy 1.18.0 HiGHS solves the same
captured 236-by-240 float LP and reports maximum primal violation
`7.105427357601002e-15` after 323 iterations. This establishes neither an
exact certificate nor permission to substitute solvers. It is evidence that
the generated LP is feasible and that the observed kill is specific to the
native simplex path. No alternate-solver value enters a qualification,
classification, panel, or candidate claim.

## Failure-record plumbing correction

The first B invocation stopped at the same context and arm but surfaced only
the native assertion. Before sealing evidence, the uncommitted owner was
augmented with a typed failure record binding the sealed pool, complete
21-context prefix, classifications, active arm, exact sizes and dimensions,
context and conversion identities, underlying error, and solver-call number.
The same prefix was rerun unchanged and reproduced the same underlying failure;
only the digest-bound record above carries stopped-result authority.

This post-outcome change alters no context, solver, tolerance, pivot cap,
allowance, threshold, classification, family order, stop rule, panel member,
or value. It opens no later B value. Recording both invocations avoids silently
erasing another rejected-invocation plumbing repair.

The final candidate-blind owner is
`pontius.fresh_capacity_filling_qualification`, with source SHA-256
`800bf1ee8d50ef6a9da400a0b9557553bb10b80085815a0140dd84245ae1dd86`.
It imports no action candidate, rejects the representative family before any
solver call, owns both exact arms, uses distinct nominal numerical quantities,
and requires ADR-0310's exact A campaign before it can construct B.

## Decision

Keep v4 as a hash-pinned, value-free source and rejected qualification control.
Do not repair the native solver and retry this panel, replace the oracle with
HiGHS after outcome, accept A alone, select around B context 21, enlarge or
reseed either pool, relax a tolerance, or open representative/v3/v4 candidate
values. ADR-0305's failure authority is exhausted.

The next eligible boundary is a new prospective, candidate-independent
native-simplex robustness preregistration. It should freeze the already-known
failing LP as a development regression, add a prospectively fixed adversarial
corpus, compare feasibility and objectives against an independent solver or
certificate with unit-specific checks, and define what would reject a solver
replacement. A future action candidate would still require new prospective
quality evidence; a solver repair alone cannot revive v4.

## Verification

Six focused tests reproduce A, the exact B stop and failure digest, one-to-one
conversion, candidate-free imports, immediate target/ambiguity/numerical
stopping, representative exclusion, and the exact-A-before-B gate. Mocked
controls prove an all-qualifying pool stops after exactly 48 LP calls, an
ambiguity after two, and a numerical failure after one. Mutation checks reject
changed context fields and changed A evidence before B construction.

Changed-file Ruff, Python 3.11 grammar, generated STATUS, documentation links,
staged whitespace, and preservation of earlier frozen identities pass. The
complete repository suite passes 1,197 tests with two intentional
environment-dependent skips.

## Evidence classification

- **Known:** frozen pools, exact A prefix and provisional selection, B's
  complete prefix, the active failure context and arm, source/result/failure
  identities, and unopened later families and arms.
- **Reproduced:** A values and teachers, B's native failure, fail-closed order,
  conversion, numerical summaries, and deterministic hashes.
- **Diagnostic only:** the native violation reconstruction and HiGHS
  feasibility comparison.
- **Rejected:** capacity-filling v4 qualification under ADR-0305.
- **Unopened:** B context 21 minimum/all-in, B contexts 22-95, every
  representative value, every v3/v4 candidate value, and all integration.
- **Hypothesis:** a separately gated solver implementation can remove this
  native robustness failure without weakening numerical or unit contracts.

## Claims boundary

This result establishes one prospectively ordered reduced qualification
failure. It does not show that v4 is strategically weak, that HiGHS is a valid
production replacement, that any opened pool is representative of six-max
poker, or that a solver repair improves decisions. It establishes no
production range width, earlier-street quality, multiplayer safety, runtime
decision quality, 15-second feasibility, replay or convex-master
compatibility, blueprint or resolver strength, NashConv, AIVAT, league
strength, C5 completion, or complete bot. No revoked experiment, external
publication, or thesis change is authorized.
