# ADR-0330: Close the unretained greedy invocation and repair serialization

- Status: accepted terminal artifact-boundary failure; the ADR-0329 campaign is permanently closed without a retained result or selected width
- Date: 2026-08-23
- Follows: ADR-0329
- Invocation baseline commit: `e4735165137eb9b72468439fdf0a23878f7debb0`
- Invoked greedy source canonical-LF SHA-256: `6e824b83c8789ae64f1859aa5536769a815aca5dd0480500268e335a3a6244f5`
- Repaired greedy source canonical-LF SHA-256: `050bad76fd5fac2d3151d7500140acddcaffcf133979a0493733666413e1b26e`
- Repaired greedy seal canonical-LF SHA-256: `44c9b5045eec6124919547acc13a15b920e7c57983e7105c3b4417c06a2c78ca`
- Focused-test canonical-LF SHA-256: `bd7a8dbb96daf20ceedd6e362258e68da9b7be10b203eac689fac88281aebc06`
- Historical greedy protocol SHA-256: `dc703d044b35d4820d4a1742b4295b35cb09af720f66a5e9a21e127edbb226b2`
- Repair/closure protocol SHA-256: `d26ae591ec30983342607b431579b449419d51fcacf992edf27b384f69ed1d06`
- Greedy schedule SHA-256: `a6811bbd4131f73735e2336bb064443a7d30b07e73d36abbbab2e7ca6c91569a`
- Surviving partial byte count: `58`
- Surviving partial SHA-256: `957b8b862e2dac5748164aa77eda06e4ffe0e11893f8a4a5b71f717c90a3caaf`
- Front-Door-Kind: controller-v1
- Front-Door-Research: ADR-0280
- Front-Door-Process: ADR-0330
- Front-Door-Contract: ADR-0307
- Front-Door-Revoked: ADR-0281
- Front-Door-Active-Next: Before any new sizing value, source-seal a non-replay successor on a new commit-derived untouched population; require a fully populated synthetic completed-campaign serialization test plus an append-and-fsync write-ahead evidence journal before its first solver call; bind its own teacher, schedule, seed, artifact, and no-retry failure semantics prospectively; never reuse the ADR-0329 qualified panel as a replacement run, never delete or overwrite the surviving `.partial`, and never infer a greedy width or value from the lost in-memory result
- Front-Door-Blockers: the only authorized direct greedy invocation has no retained terminal result, so no development-selected width, transfer seed, fresh transfer panel, capacity result, six-player response model, live strategy bridge, h32/full-range result, earlier street, complete 15-second decision, or poker-strength result exists

## Decision

Record the single ADR-0329 direct closed finite-block greedy invocation as a
terminal artifact-boundary failure. It is not a consumer rejection, numerical
quality rejection, selected width, or negative curve. Its values and selection
were not retained and are irrecoverable from repository evidence.

Permanently close both public ADR-0329 invocation entry points. Do not delete
the surviving `.partial`, change the output path, invoke the private executor,
or repeat the 400 calls. A retry would violate ADR-0329's source-sealed one-shot
contract and ADR-0288/R88's rule that a rerun cannot reconstruct lost output.

Repair the serializer because the defect is real and would recur in any later
owner, but do not treat repair as permission to replay the campaign. Any later
action-width experiment must be a prospectively sealed, genuinely new study on
an untouched population with its own evidence-preservation contract.

The inherited authority remains visible. ADR-0318 binds HiGHS 1.12.0;
ADR-0319 requires one public HiGHS-DS call per canonical task; All 177 ordered
observations pass under ADR-0320, leaving the separate consumer eligible;
ADR-0321 retains caller-owned legal fallback; and ADR-0322 returns research
evidence or rejection with no action. ADR-0324's value-unopened boundary,
ADR-0325's exactly once invocation rule, and ADR-0326/ADR-0327's exhaustive
bounded development-teacher chain remain historical prerequisites, not
permission to reconstruct the lost ADR-0329 result.

## Exact observed failure

Immediately before invocation, the repository was clean at
`e4735165137eb9b72468439fdf0a23878f7debb0`; the final and `.partial` paths were
both absent. The exact retained wrapper then created and fsynced the intended
reservation bytes:

```text
adr0323 closed finite-block greedy invocation in progress
```

The process reached a completed in-memory `GreedyDevelopmentCampaignResult`
and entered its nonempty `width_gates` during canonical serialization. That
path is enough to establish the sealed completed-result invariant of exactly
400 public calls: rejected or incomplete campaign results cannot publish width
gates, and completed result construction rejects any call count other than
400. It does **not** establish which width, if any, passed.

Publication then raised `RecursionError: maximum recursion depth exceeded`.
The relevant historical call cycle was:

```text
GreedyDevelopmentCampaignResult.digest
  -> GreedyWidthGateResult.digest
  -> _width_gate_payload(result)
  -> result.digest
  -> ...
```

The process exited before truncating the reservation or linking a final
artifact. The final JSON is absent. The surviving `.partial` is exactly 58
bytes with SHA-256
`957b8b862e2dac5748164aa77eda06e4ffe0e11893f8a4a5b71f717c90a3caaf`.
It contains no endpoint, choice, gate, or selection data.

The command wall was a development diagnostic containing graph construction,
400 repeated solves, Python orchestration, and the terminal failure. It is not
a per-solve latency, per-iteration latency, 15-second action-clock result, or
quality prior.

## Root cause and missed control

The width-gate digest used `_width_gate_payload` as its canonical preimage,
while that same artifact payload embedded `result.digest` as
`width_gate_sha256`. The hash therefore attempted to include itself. This was
a semantic ownership cycle hidden inside an otherwise ordinary nested digest.

The source-only controls constructed a `GreedyWidthGateResult` and checked its
five booleans, but never evaluated the gate digest or canonicalized a populated
completed campaign. Preflight tests covered typed early rejection and a small
runner-rejection artifact, not the success-only terminal branch. The exact
failure path was therefore load-bearing and untested.

The reservation also exposed a second, already-registered weakness. It proved
that an invocation had started, but it was not a write-ahead evidence journal.
All 400 accepted observations remained only in process memory until final
serialization. R88 had already required complete raw-payload retention before
the value process exits; a 58-byte sentinel did not discharge that requirement.
The source seal overstated the artifact guarantee.

## Structural repair

`GreedyWidthGateResult.digest` now hashes only
`_width_gate_digest_payload`, which contains the gate's semantic fields and no
self-hash. `_width_gate_payload` separately adds the already-computed digest to
the external artifact envelope. A focused test evaluates both paths and would
reproduce the historical recursion on the invoked source.

The repaired source additionally:

1. verifies the exact surviving partial and the absence of a final artifact;
2. preserves the historical ADR-0329 source manifest separately from the
   repaired ADR-0330 manifest;
3. binds a distinct repair/closure protocol digest;
4. makes both public campaign entry points fail before path creation or a
   consumer call; and
5. keeps generic canonical retention testable for non-campaign semantic
   records without reopening the experiment.

This repairs the implementation defect, not the lost result. The old source
hash remains the only source provenance eligible for the one invocation, and
the new source hash is explicitly non-invocation repair evidence.

## Controls

Twelve focused tests pass in 35.852 seconds. They now evaluate a populated
width-gate digest and artifact envelope, verify both historical and repaired
source identities, bind the exact partial witness, prove both public campaign
entries reject before a solver or new staging file, and retain the prior graph,
response-closure, arithmetic, selection, provenance, and corruption controls.
The repository suite ran 1,342 tests in 404.876 seconds and finished
`OK (skipped=2)`.

Ruff remains unavailable in the repository virtual environment. No substitute
linter is represented as that gate.

## Consequences and next boundary

ADR-0329 produced no admissible development selection. The teacher's
width-three full-regret knee remains an exhaustive reduced-game measurement,
not a substitute greedy result. Transfer cannot be derived because its frozen
seed required a later mechanism commit containing a development selection.

The least-biased recovery is not a replay. A successor may prospectively
derive a new seed from the committed ADR-0330 state, construct a new untouched
population, and source-seal its teacher and direct mechanism before any value.
It must first prove complete success-branch serialization with synthetic data
and append/fsync each exact accepted observation to a canonical write-ahead
journal before moving to the next call. Final reduction may read that journal;
it may not be the sole owner of evidence survival.

That successor remains reduced h4 river research. It cannot claim transfer,
capacity, production width, six-player response closure, or action quality.

## Evidence classification and dissent

- **Known:** one clean-baseline invocation occurred; its completed-result path
  implies 400 public calls; canonical publication recursed; the final artifact
  is absent; and the exact 58-byte partial survives.
- **Observed:** `RecursionError` on the success-only width-gate digest path and
  no retained endpoint or selection bytes.
- **Reproduced without solving:** the historical payload/digest cycle, its
  repaired acyclic envelope, exact witness verification, and public no-retry
  closure.
- **Unknown:** every greedy price, chosen subset, width curve, passing gate,
  selected width, and whether the in-memory result selected width three.
- **Rejected:** treating the partial as a result, inferring a width from the
  traceback, replaying at another path, deleting the witness, or using the
  campaign wall as live latency.

Supporting a fresh successor: no numerical outcome escaped, so a commit-derived
new population can still be prospectively untouched, and the direct mechanism
question remains important to scalable action width.

Opposing evidence: a replacement study costs a new teacher plus direct run,
delays full-range and multiway work, and the h4 fold/call shell remains remote
from production poker.

Largest unknown: whether a newly sealed direct mechanism reproduces the
teacher's width-three knee under all five development conjuncts.

Cheapest falsifier: before any solver call, canonicalize and rebind a fully
populated synthetic success artifact, crash-inject after each journal append,
and prove that every completed observation survives process termination. Any
missing observation kills the successor on source.

Confidence: high in the failure diagnosis, exact witness, repair, and absence
of a retained result; no confidence claim is made about the lost values.

## Claims boundary

This decision records and repairs one artifact-publication defect and
permanently closes the invoked ADR-0329 campaign. It establishes no greedy
price, selected development width, transfer result, capacity fit, complete
15-second action, six-player response model, h32/full-range result, earlier
street, or poker-strength result.
