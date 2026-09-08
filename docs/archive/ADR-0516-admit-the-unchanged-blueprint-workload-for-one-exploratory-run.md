# ADR-0516: Admit the unchanged blueprint workload for one exploratory run

- Status: accepted one-run source exception upon its separately authorized decision commit
- Date: 2026-09-08
- Follows: ADR-0515
- Base-Commit: 4687e596dd2e54658ef59795a0b3f253797d3178
- Invocation-Authority: none until the exact companion invocation decision is adopted
- Front-Door-Kind: controller-v1
- Front-Door-Research: ADR-0280
- Front-Door-Process: ADR-0516
- Front-Door-Contract: ADR-0307
- Front-Door-Revoked: ADR-0281, ADR-0468, ADR-0472, ADR-0475
- Front-Door-Active-Next: Authorize the unchanged workload's single exploratory invocation
- Front-Door-Blockers: known qualification and monitoring defects; exploratory workload unrun

## Decision

Admit the exact representative blueprint workload r003 source for one exploratory
invocation, without rework. After receiving both blocking findings and the proposed
redesign, the controller directed: "Let's run with what we have no rework".
This decision records that choice. It does not declare either finding repaired or
either issued review CLEAN, and it does not adopt the abandoned redesign proposal.

For this single use, the controller's direction supersedes ADR-0515's ordinary
two-CLEAN source-adoption prerequisite and the remaining post-review source gates
and added-CI rehearsals. Those gates remain unrun, not passed. The existing finite
development and registration evidence is the available preparation for this use.
No further correction candidate or live correctness repetition is opened here.

This exception pins source for the companion invocation decision only. It grants
no playing-strength, worst-case-latency, deployment or general production-readiness
claim. The research head and governing action-clock contract remain unchanged.

## Exact source and evidence

Use the fifteen changed blobs from frozen candidate
2e1457046c640045fe0b404bfc3d6f78cd5e4b45, tree
263f819568d3811de5b86aacb3dfdc1e2ab2fdb4. Its changed-blob manifest SHA-256 is
66a26195ad7fa0fbaadc4ae839b8fe82264ff4df4c0df53f05e9a0cd5da3c18f.
The source exception incorporates those blobs byte-identically, this decision and
generated STATUS.md, with opening commit 4687e596dd2e54658ef59795a0b3f253797d3178
as parent. No other implementation, test, fixture or configuration change occurs.

The permanent r003 packet is
D:/Pontius-handoffs/v0a-blueprint-workload-source/r003. Its issued review hashes are:

- Review G: cdc7a4ddabe2c011abd619fea51da65d677cc89b7f1c77b4f9a86d96baa97edb.
- Review H: 58d68035fa04e354d645429638d4c8e63abbf90a9122d370f4fed1b4dc77defd.
- Root disposition: 36888bc95ad5704ea4cb4be1e30a785f539b3610a3d825612332c74d441391ab.

Both reports remain NOT CLEAN / STRAINED. G's incidental administrative-summary
exposure and root's treatment remain recorded. This exception does not relabel the
reviews as successful independent source acceptance.

The final r003 session suite passed 13 methods and report suite 19 on both actual
3.11.15 and 3.14.6. Each session invocation used eight stock and eight diagnostic
sessions. Unchanged population and measurement modules retain their ten-method
passing suites on both versions from r002. Complete registration comparisons
preserved all 3180 old rows, 449 old payloads and 141 grants, with the same 52 added
IDs. Earlier failures, partial attempts and consumed invocation slots stay retained.

## Known limitations accepted for this use

H-01: qualification takes a remaining-time snapshot before grant preparation and
passes it as a later relative timeout. Its success predicate does not reject an
overbudget stage_ns, and run admission does not validate qualification timing.
The public reader rejects that record later. The operator will inspect the actual
qualification result before measured launch and close measurement if its recorded
stage exceeds 1800 seconds. This procedural check does not repair qualification's
native launch/release deadline or certify its internal enforcement.

G1: direct-worker memory sampling begins at the first ready stage, after admission
work. Slow checks before that point can leave the worker without the prescribed
100 ms observations or current-private-commit resource stop. The code remains
unchanged. Resource-limit compliance during that interval cannot be claimed, even
if later peak counters and measured-stage observations are available.

Full source-admission cost and workload feasibility within the fixed measured
envelope remain unknown. A partial run or qualification refusal is a retained
outcome, not permission to alter seeds, population, samples, source or limits.
The later report must distinguish its raw numerical results from these unresolved
control limitations. A producer clean flag cannot waive the findings in this ADR.

## Scope and next authority

Keep the r002 recipe, table/query trajectories, natural and diagnostic populations,
sample counts, numerical decision rules, interpreter subset, 1 MiB session cap,
14000 ms work cutoff and 15000 ms response wall. No cached-byte hash gains an
external-origin-freshness meaning. Preserve all sealed runtime and historical bytes
outside ADR-0515's six exact registration exceptions.

The companion decision must bind this exact source-exception commit, its full raw
manifest, the unchanged protocol, the recipe digest, one fresh D-local snapshot
for both interpreters and one absent result root. It admits qualify once, then run once after
successful retained qualification. It must be published as real origin/master
before execution; no synthetic tracking-ref change or admission bypass is allowed.

The source and invocation decisions require concrete commit/push authorization.
Preparation of their Git objects or documents alone adopts nothing. This source
exception alone launches no worker and grants no retry, resume or replacement run.
