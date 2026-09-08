# ADR-0315: Source-seal the artifact-only native-simplex gate correction

- Status: accepted source-only post-outcome correction with synthetic controls; authoritative retained-evidence result remains unopened
- Date: 2026-08-23
- Follows: ADR-0314
- Analyzer source SHA-256 (canonical LF): `0755546e6260708ffb4165ec50ebf4ff88c473354faeb7303e8b84e568fca1be`
- Analyzer-seal source SHA-256 (canonical LF): `6d7c682e75613e4a43cb2c95ed060f6619a22676464311ba7a39ac7f4b5244da`
- Synthetic-test source SHA-256 (canonical LF): `d95fba06549273fcb43fabf4a25370f6bdd7ab752592bfccc46f77ef6df17f25`
- Front-Door-Kind: controller-v1
- Front-Door-Research: ADR-0280
- Front-Door-Process: ADR-0315
- Front-Door-Contract: ADR-0307
- Front-Door-Revoked: ADR-0281
- Front-Door-Active-Next: After committing this source-only boundary, invoke the sealed ADR-0315 analyzer exactly once on ADR-0314's retained 110,068,679-byte artifact, retain only its deterministic corrected assessment, and record the result before any replacement-adapter or specialized-solver preregistration; invoke no backend, exact enumerator, reconstruction, certificate, action candidate, or consumer and do not revive v4
- Front-Door-Blockers: no authoritative corrected assessment exists yet, so HiGHS dual simplex remains replacement-ineligible; native simplex remains rejected for this workload; no persistent-HiGHS or structure-specialized proposer comparison is preregistered; v1-v4 and every action-abstraction integration path remain parked

## Decision

Accept and source-seal a separately disclosed artifact-bound semantic-gate
correction to ADR-0311's known-regression predicate before applying it to
retained evidence.
The new `native_simplex_audit_reanalysis` module distinguishes these nominal
quantities:

- the required exception, pivots, allowance, exact maximum residual, and
  unique maximum-residual row;
- an optional complete set of rows above the verification allowance; and
- the three unchanged micro-variant, sizing cross-backend, and sizing
  cross-variant allowances.

It preserves the exact 2,655-invocation schedule and requires all 2,655
scheduled observations before interpreting any gate.

ADR-0310 required row 215 to be the unique maximum-residual row. It did not
claim that `(215,)` was the complete above-allowance set. The retained real
contract therefore requires row 215 as the unique argmax and a member of the
derived failing set while deliberately leaving complete-set identity
unspecified. A synthetic trace with failing rows `(0, 1, 3)` and unique maximum
row 3 passes that corrected meaning; the former exclusive `(3,)` predicate
fails on the same trace.

This is a post-outcome semantic correction, not a reinterpretation of
ADR-0314. ADR-0314's frozen-gate rejection remains the historical result.

## Artifact and source boundary

The analyzer is bound to ADR-0314's exact artifact identity:

- 110,068,679 bytes;
- SHA-256
  `1f5e49cf1f855135283a0b8794656fc9e4fa6447886cb5fd8fe6dfcdcac8039a`;
- runner version and source SHA-256
  `cfb127960e3d501a156f14d22244ecd122874b74fefb668685f9a721503ade16`;
- complete corpus SHA-256
  `4be6dcc311bc2f885ce9ad312cee8294f38231180ab78bbbfb6497184b1597a3`;
- environment-subtree SHA-256
  `07137f9e865a9320102c3705777a111795df5b83b80a7db756140e65c979bd20`;
  and
- protocol-subtree SHA-256
  `0a9254cc546a63e944007dbe3c78b3a7d1f451f9ab44b7a9ec94325a26505377`.

It accepts canonical JSON only, rejects duplicate keys and raw JSON floats,
requires the exact campaign/result/invocation schemas, and revalidates all
2,655 contiguous ordinals, 885 variant-major backend triples, 177 bases, five
ordered representations, and the 48/129 micro/sizing partition. It derives
the known trace's failing rows and argmax from exact float wrappers, checks
stored coordinates, allowance, maximum, result/trace pivots, backend,
exception stage, and message for internal consistency, then replays every
unchanged HiGHS per-instance, micro, sizing-interval, and DS/IPM conjunct from
the retained fields.

The analyzer imports only the standard library and the bounded strict reader
from `runner_harness_v2`. It has no solver, corpus, exact-enumerator,
reconstruction, certificate, SciPy, or write dependency. Its public retained-
artifact entry point validates the canonical-LF source seal before reading the
artifact. Canonical line-ending normalization addresses ADR-0314's recorded
Windows checkout portability risk without changing the sealed runner or
artifact identity.

No authoritative byte of the 110 MB retained campaign was read through this
analyzer before this source boundary. No solver or exact/certificate work was
invoked. The next invocation is therefore temporally separated from the
committed correction.

## Synthetic verification

Ten synthetic-only tests cover:

- multiple above-allowance rows with one distinct unique maximum;
- rejection of the former exclusive-row meaning and of tied argmax rows;
- trace/stored-row and trace/result-pivot inconsistencies;
- every unchanged HiGHS instance, micro comparison, ten-interval, and DS/IPM
  comparison gate;
- nominal allowance-type separation and isolated allowance effects;
- exact length/digest, canonical JSON, duplicate-key, raw-float, schedule,
  representation, backend-order, and schema refusals;
- the real contract's nonexclusive maximum-row declaration;
- an artifact-only import/effect surface; and
- source-seal stability across LF/CRLF plus seal refusal before artifact read.

The focused suite passes 10 tests. Ruff lint and formatting pass for the
analyzer, its seal, and the synthetic test module. The authoritative retained
assessment is intentionally absent at this ADR. The repository-wide suite
passes 1,237 tests with two skips in 321.773 seconds.

## Solver direction after this boundary

The strongest plausible speed path is not to make a new general LP trust
root. A later prospective gate may compare (1) the present rebuild path, (2) a
persistent modify-in-place HiGHS model with warm basis reuse as the null
hypothesis, and only then (3) an untrusted structure-specialized proposer for
the product-of-simplexes master with few coupling rows. Every proposal must
pass independent primal/dual/gap and semantic certificates, with HiGHS as a
fallback on any rejection.

That future comparison must measure complete-ledger marginal chip-valued
decision quality per added millisecond under ADR-0307's 15-second action wall,
not raw generic-LP throughput. It must separately report construction,
marshaling, update, pivot/inner-solve, verification, and fallback costs. Its
kill conditions include no end-to-end quality-per-millisecond improvement
over persistent HiGHS, any undetected certificate violation on the frozen
adversarial corpus, or fallback frequency that erases the latency gain. This
paragraph grants no implementation or result authority.

## Claims boundary

This ADR establishes a source-sealed, artifact-bound correction and synthetic
controls only. It does not establish the corrected result, HiGHS replacement
eligibility, adapter correctness, persistent-model latency, native-proposer
correctness, solver independence, 15-second feasibility, or decision quality.
It does not certify the retained campaign beyond the later analyzer's finite
checks.

It establishes no action quality, production range width, earlier-street
quality, complete-hand/live-host integration, blueprint, resolver, NashConv,
AIVAT, league strength, coalition safety, or complete bot. V1-v4 remain parked.
No revoked experiment, external publication, consumer migration, or thesis
change is authorized.
