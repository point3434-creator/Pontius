# ADR-0515: Open the representative blueprint workload source round

- Status: accepted source-opening decision upon its separately authorized commit
- Date: 2026-09-07
- Follows: ADR-0514
- Base-Commit: 7242891bc8020d33737c3a027ef88d1b65bb2ace
- Invocation-Authority: finite source controls after adoption; measured workload closed
- Front-Door-Kind: controller-v1
- Front-Door-Research: ADR-0280
- Front-Door-Process: ADR-0515
- Front-Door-Contract: ADR-0307
- Front-Door-Revoked: ADR-0281, ADR-0468, ADR-0472, ADR-0475
- Front-Door-Active-Next: Implement and qualify the representative blueprint workload tools
- Front-Door-Blockers: workload source/invocation pending; strength and worst-case latency unknown

## Decision

Upon this decision's separately authorized commit, open the additive representative
blueprint workload source round. Implement the controller-approved revised design
at `docs/superpowers/specs/2026-09-07-representative-blueprint-workload-design-r002.md`,
with the source contract and execution protocol under
`docs/architecture/v0a-blueprint-workload-r001/` and implementation plan at
`docs/superpowers/plans/2026-09-07-blueprint-workload.md`.

The controller approved building the revision after reviewing the four priorities:
interface capacity and misses, preparation reuse, full-session phase/accounting
costs, and larger research-table scaling. This opening fixes the remaining source,
invocation, output and control details before implementation. It creates no measured
result, trained policy, runtime optimization or operating/research invocation.

The r002 design's raw SHA-256 is
`dc2a8003ca54fcb42aac60de6790233025705155a5ccbb323917af784b7a583d`.
Preserve the original r001 and the r002 review response as historical context;
r002 alone supplies the adopted workload population and numerical decision rules.
The execution protocol resolves scheduling and measurement boundaries without
changing its seeds, populations, sample counts, thresholds or interpreter subset.

## Prospective source scope

Supersede CLAUDE.md rule 1 only for the six exact base versions and narrowly
described registration/import/CI changes in source-contract.md. Recheck their raw
Git blob pins before editing. Add only the four tools, four suites and one literal
control fixture named there. All `src/pontius` bytes, the host, session, dealer,
adapters, codecs, providers, evaluators and prior tests remain unchanged except
for the named inventory assertion updates. No historical test is reassigned.

This source measures accepted paths. The retain-once arm is a direct-Python cost
prototype, and the profiler observes the parent's existing call/return boundaries.
Neither may replace production functions, alter a child command, turn cached-byte
hashing into external-file freshness, or change accounting. The 1,048,576-byte
session input cap, 14,000 ms work cutoff and 15,000 ms response wall stay fixed.

## Qualification and authority

The opening candidate contains exactly eight paths: this ADR, generated STATUS.md,
source-contract.md, execution-protocol.md, the implementation plan, and the three
preserved design/review files listed in the contract. Freeze their raw Git blobs
and whole-row-sorted SHA-256 manifest. Obtain two independent Tier C cold reviews
before exact-candidate status checks and all twelve status tests on actual
CPython 3.11.15 first, then 3.14.6, using fresh D-local snapshots.

The retained design/review files keep their original bytes, including existing
long tables and links. New authored governance prose uses LF, no BOM, no trailing
whitespace and at most 100 columns. Generated STATUS uses its unchanged renderer.
No poker, population construction, performance or inventory payload is part of
this documentation-only opening qualification.

After opening adoption, implement and independently review the exact source, then
run the fixed correctness and registration gates in the plan. One initial source
candidate and at most two bounded correction rounds are permitted, with the
workflow's earlier stop for repeated residuals or a wrong design. No unfavorable
measurement may be retried or used to enlarge a population, resource limit or gate.

Source sealing is a later exact decision. A subsequent finite invocation decision
must bind the sealed source, runtimes, qualified population/plan identities and
one absent result root. The full 8,192/1,152-trajectory population construction and
120 CLI performance sessions are closed until that staged invocation authority.
Preparation qualifies and freezes the population before any measured payload;
qualification refusal prevents measurement and remains retained.

This opening grants no consumed-owner retry, training, new opponent policy,
full-scale evaluation, native rewrite, live demonstration or production adoption.
The accepted source remains the reference, and finite maxima do not establish
worst-case latency or playing strength.
