# ADR-0314: Retain the native-simplex audit and reject the frozen gate

- Status: accepted negative complete audit result; the frozen conjunction rejects on an over-specified known-regression row-set predicate
- Date: 2026-08-23
- Follows: ADR-0313
- Result: `experiments/results/native-simplex-robustness-audit-v1.json`
- Result SHA-256: `1f5e49cf1f855135283a0b8794656fc9e4fa6447886cb5fd8fe6dfcdcac8039a`
- Result bytes: `110068679`
- Front-Door-Kind: controller-v1
- Front-Door-Research: ADR-0280
- Front-Door-Process: ADR-0314
- Front-Door-Contract: ADR-0307
- Front-Door-Revoked: ADR-0281
- Front-Door-Active-Next: Preregister and source-seal only an artifact-bound semantic-gate correction over the retained ADR-0314 digest, with mocked multi-row native traces proving that ADR-0310's required unique maximum row 215 is not the complete above-allowance row set; change no corpus, backend result, option, allowance, HiGHS conjunct, or native source, make no new exact/backend/certificate invocation, and commit that analyzer before its authoritative retained-evidence reanalysis; do not revive v4 or authorize a consumer migration
- Front-Door-Blockers: ADR-0311's literal frozen gate rejected, so HiGHS dual simplex is not yet replacement-eligible despite every one of its 885 arms passing; the correction is necessarily post-outcome and must remain separately disclosed; native simplex remains rejected for this workload; v1-v4 and every action-abstraction integration path remain parked

## Verdict

Retain the complete one-shot ADR-0311 campaign and reject its literal frozen
conjunctive gate. The full 2,655-arm schedule completed without runner or
schema truncation. All 885 HiGHS dual-simplex arms and all 885 HiGHS IPM arms
returned finite optimal results and passed their per-instance exact,
original-coordinate semantic, behavioral, and outward-certificate checks.
The frozen assessment nevertheless returns `highs_dual_simplex_eligible =
false` because its known-native-regression predicate required row 215 to be
the *only* original row above the native verification allowance.

The retained canonical native observation reproduces the recorded exception,
375 pivots, allowance, unique maximum-residual row 215, and exact maximum
residual. It also reveals twenty other rows above the allowance. ADR-0310
recorded row 215 as the maximum violation; it never claimed that no other row
failed. The audit gate therefore compared two different semantic quantities:
the required maximum-residual row and the complete above-allowance row set.
That is a gate defect, but it was frozen before the result. This ADR records the
formal rejection rather than retroactively laundering it into a pass.

## Evidence identity and invocation

The source-only boundary was committed first at Git
`7c4d0ea98b27dc55ac0bd270e1ea15ff129084b0`. The one-shot launcher refused a
dirty or different commit and refused an existing final or partial evidence
path. It then built complete corpus SHA-256
`4be6dcc311bc2f885ce9ad312cee8294f38231180ab78bbbfb6497184b1597a3`
and invoked only `execute_sealed_adr0311_audit`.

The immutable campaign was serialized, fsynced to a distinct partial path,
and renamed to
`experiments/results/native-simplex-robustness-audit-v1.json` before the gate
was interpreted. The partial path no longer exists. The canonical artifact is
110,068,679 bytes with SHA-256
`1f5e49cf1f855135283a0b8794656fc9e4fa6447886cb5fd8fe6dfcdcac8039a`.
Its embedded runner source SHA-256 is
`cfb127960e3d501a156f14d22244ecd122874b74fefb668685f9a721503ade16`.
Its 2,655 ordinals are complete and contiguous.

The complete campaign took `249.7436568000121` seconds locally. Backend-call
time sums were `198.6890598992468` seconds for native,
`1.8502174000313971` seconds for HiGHS dual simplex, and
`2.165432900103042` seconds for HiGHS IPM. These are offline audit diagnostics
over different LPs and representations. They are not per-decision latency,
per-iteration cost, 15-second feasibility, or decision-quality evidence.

## Complete observations

| Backend | Finite optimal and verified | Recorded exceptions | Complete arms |
|---|---:|---:|---:|
| native | 849 | 36 | 885 |
| HiGHS dual simplex | 885 | 0 | 885 |
| HiGHS IPM | 885 | 0 | 885 |

All 240 dual-simplex and 240 IPM micro arms passed. All 645 dual-simplex and
645 IPM reduced-sizing arms passed. No observation contains a runner-failure
record. The native exceptions comprise 18 primal-verification assertions,
five dual-feasibility assertions, one primal/dual-objective disagreement, and
twelve `max_pivots` failures. Thirty-five of the 36 occur under the
prospectively frozen dyadic-row-scaling representation; one is the known
canonical regression. Native remains rejected regardless of its 849 verified
arms.

## HiGHS bounded result

The literal gate reports no HiGHS instance, exact-micro, certificate,
cross-variant, or cross-backend failure. Diagnostic extrema from the retained
verified fields are:

| Check | Retained extremum | Frozen allowance |
|---|---:|---:|
| exact-micro reconstructed-objective error | `1.4210854715202004e-14` | `1e-9` dimensionless |
| exact-micro certificate gap above exact | `1.7053025658242404e-13` | `1e-9` dimensionless |
| sizing certified interval width | `9.675815704213164e-11` chips | `1e-9` chips |
| corresponding DS/IPM behavioral difference | `1.0702549957386509e-13` chips | `1e-9` chips |
| within-backend micro five-variant span | `1.4210854715202004e-14` | `1e-9` dimensionless |
| smallest ten-interval intersection slack | `1.3533618670180658e-13` chips | nonnegative after allowance |

The maximum retained sizing envelope-row violation is
`7.105427357601002e-14` chips for each HiGHS method. The maximum policy mass
residual after frozen clipping is `2.1760371282653068e-14` for dual simplex
and `2.9531932455029164e-14` for IPM. Eight dual-simplex and eleven IPM policy
coordinates were clipped only within the separately frozen nonnegativity
allowance. Two dual-simplex dual-hint rows and zero IPM rows required the
recorded pre-aggregation sign clip.

These are finite-corpus numerical-robustness observations, not proof that the
two HiGHS methods are independent implementations, not a production adapter,
and not poker strength evidence.

## Known-native regression and frozen-gate defect

Ordinal zero is the canonical known-regression native arm. It records:

- `AssertionError: linear-program solution fails primal verification`;
- 375 pivots;
- verification allowance `4.199999999999999e-8`;
- maximum residual `4.049601922810204`;
- row 215 as the unique row attaining that maximum; and
- twenty-one rows total above the allowance, including row 215.

The complete above-allowance row tuple is
`0,2,5,6,12,13,50,51,64,71,89,99,122,129,146,147,157,166,167,205,215`.
ADR-0310 disclosed only that the returned variables violated row 215 by the
recorded maximum; that diagnostic did not enumerate or claim exclusivity over
the complete failing-row set.

The frozen code instead compares
`failing_canonical_rows == (ADR0311_KNOWN_NATIVE_FAILURE_ROW,)`. Every other
known-regression field matches exactly. The sole returned gate failure is
`known-native-regression-mismatch`; therefore the literal frozen conjunction
rejects even though the disclosed maximum-row regression substantively
reproduces. This result is preserved as-is.

The structural correction is not to special-case this tuple. A successor must
give the regression signature distinct typed fields for required exception,
pivots, allowance, unique maximum row, maximum residual, and optional complete
failing-row-set identity. Its mocked controls must include multiple
above-allowance rows with a distinct unique maximum. The correction must be
bound to this retained artifact digest and may not alter any HiGHS gate or
rerun a backend.

## Decision

Reject ADR-0311's literal frozen conjunction and keep HiGHS dual simplex
ineligible for a replacement adapter at this boundary. Retain the full
campaign and all 2,655 scheduled observations from the frozen
2,655-invocation schedule as prospectively collected bounded evidence: every
HiGHS arm and every non-native conjunct passed, while native produced 36
recorded failures.
Do not discard the campaign, silently reinterpret the row tuple, edit the
sealed runner, rerun the campaign, relax an allowance, select IPM after a gate
failure, modify `linear_program.py`, reopen v4, or connect either backend to a
consumer.

The next boundary may implement only a separately disclosed, artifact-bound
semantic-gate correction over the exact retained digest. Seal that analyzer
and multi-row mocks before its authoritative reanalysis. A corrected pass
could authorize only a later prospective replacement-adapter ADR; it cannot
change ADR-0310, revive any action candidate, or establish bot quality.

## Verification

The complete artifact digest and length were independently reread from disk.
Artifact-only diagnostics verified all 2,655 ordinals, the backend counts, the
sole frozen-gate failure, row 215's exact residual and unique-maximum identity,
the complete above-allowance row set, all HiGHS verification fields, and the
reported extrema. No backend, exact enumerator, reconstruction, or certificate
was reinvoked during those diagnostics.

The repository-wide suite passes 1,226 tests with two skips in 321.281
seconds. The focused documentation/status slice passes 25 tests in 0.227
seconds. Generated STATUS, maintained Markdown links, Ruff lint/format, and
whitespace checks pass. No solver source, option, corpus, allowance, or result
byte is changed by that verification.

## Portability diagnostic

The committed runner and all six hash-bound dependencies currently have LF
working-tree bytes identical to their Git blobs, so the sealed invocation used
the recorded digests. This Windows installation also has global
`core.autocrlf=true`, while those files have no explicit `eol` attribute. A
fresh checkout may therefore change raw working-tree bytes without changing
source semantics. This did not affect the retained run. Future raw-byte source
seals should bind the Git blob or prospectively pin line endings rather than
relying on checkout defaults.

## Claims boundary

This result establishes one complete, prospectively ordered finite-corpus
audit and its literal gate rejection. It provides bounded evidence that the
recorded HiGHS configurations passed 48 exact synthetic LPs and 129 reduced
sizing LPs under five representations each. It does not certify all LPs,
establish replacement eligibility under the frozen gate, validate runtime
fitness, prove implementation independence, or authorize production use.

It establishes no action quality, production range width, earlier-street
quality, multiplayer safety, replay integration, blueprint, convex master,
resolver, NashConv, AIVAT, league strength, 15-second feasibility, marginal
decision quality per millisecond, C5 completion, or complete bot. V1-v4 remain
parked. No revoked experiment, external publication, or thesis change is
authorized.
