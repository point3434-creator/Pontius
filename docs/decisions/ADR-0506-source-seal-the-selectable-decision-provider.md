# ADR-0506: Source-seal the selectable decision provider

- Status: accepted source-only seal upon its separately authorized decision commit
- Date: 2026-09-06
- Follows: ADR-0505
- Base-Commit: fc99ab1a02649b82ba3bc21e5db79cb9c6e25829
- Invocation-Authority: none; no new demonstration, operating or research run
- Front-Door-Kind: controller-v1
- Front-Door-Research: ADR-0280
- Front-Door-Process: ADR-0506
- Front-Door-Contract: ADR-0307
- Front-Door-Revoked: ADR-0281, ADR-0468, ADR-0472, ADR-0475
- Front-Door-Active-Next: Select a bounded baseline demonstration; poker execution remains closed
- Front-Door-Blockers: baseline demonstration population and invocation remain unadmitted

## Decision

Accept the exact reviewed selectable decision-provider source as a CPU-only asset,
closing the complete implementation opened by ADR-0505. A fixed baseline now works
through the hand runtime, event interface, independently checking host and multi-hand
session. The engine retains visible-state admission, legal actions, continuous action
timing, fallback, application and delivery. The separate provider proposes an action
from an owned visible observation and has no authority to operate those boundaries.

Effect requires this exact decision's separately authorized commit. Draft metadata,
passing correctness tests and review refs do not activate a source seal. Incorporate
only the 23 bound source payloads, this new ADR and generated STATUS. The accepted
baseline is the fixed rule set from the approved design, with no playing-strength
or trained-policy claim. Source acceptance grants no poker invocation.

## Bound source and behavior

Task: v0a-decision-provider-implementation/r002.
Commit: 4d567797e4b3945ea3ff6c75613c56c05bc0b75a.
Base: fc99ab1a02649b82ba3bc21e5db79cb9c6e25829.
Tree: 95deb812dd8f5cad79b3973a2c35346fabbfd0ad.
Manifest SHA-256:
7d273ea40ca8b3c251ad029a8ab8ca423312703661b3c14a3bf01a375fece58b.

The 23 exact raw payload paths are the complete source-contract.md population in
docs/architecture/v0a-decision-provider-r001/: five new provider package files,
five current production exceptions, seven registration/binding exceptions, four new
test suites and two literal fixtures. The complete sorted raw manifest is retained
in the immutable source packet. Every incorporated payload must equal that candidate
blob; the twelve prospective exceptions close with these accepted versions.

Omitted strategy or explicit blueprint-v1 preserves the old constructor behavior,
v1 protocols, records and presentation. baseline-rules-v1 selects the versioned
provider path. Fixed configuration and visible-decision digests are distinct from
the source manifest and fallback blueprint identity. The five provider modules have
only the exact admitted import edges and receive no opponent hands or future board.

The engine legally admits fallback before bounded provider work. It distinguishes
proposed, abstained, invalid, exceptional, late and skipped outcomes, uses the same
authoritative clock, and emits at most one action. Records distinguish selected,
locally applied and confirmed delivered actions, retain unknown delivery and failure
state, and do not relabel provider choices as blueprint hits. The v2 host recomputes
pre-action identities and the admitted blueprint's actual fallback action/reason;
it checks proposal, action, state, timing and failure relationships. A subsequent
record refusal preserves an action already received. Session stack/button carry
and bounded reason rendering follow those verified records.

All 1,825 protected older blobs remain equal to source-contract base B. The old
model, trace, action clock, spine, kernel, evaluator, seeded generator and historical
rehearsal driver/bindings remain unchanged. Current source admission binds actual
committed raw bytes; it is not execution authority or a reassigned historical seal.

## Review and verification

Both fresh independent Tier C reviews bind to the source commit and manifest above.
Specification and engineering quality are CLEAN, C/I/M 0/0/0, and design is SOUND.
Reports are retained under D:/Pontius/tmp/v0a-decision-provider-implementation-r001/
packets/r002/reviews/ and byte-identically in the permanent local handoff packet:

- review-a.md, issuer Codex /root/source_review_c, SHA-256
  7265f4d8e092abe52f2348cccb1e8e1f34e71cdff1e662f8ddc920c56350bbd9.
- review-b.md, issuer Codex /root/source_review_d, SHA-256
  0bed213f9c8a7d7219cc99466a21d0a9771f3969c192a6976ddb023622961f1b.

After both CLEAN reviews, all 26 prescribed acceptance commands passed on actual
CPython 3.11.15 first and 3.14.6 second: 483 tests per interpreter, 966 total test
executions, with zero failures, errors or skips in the final selected population.
Every command and its actual-version/module-origin preflight used a fresh
exact-candidate D-local snapshot, -B -P, snapshot cwd/src, a scrubbed environment
and the validated absolute Git executable. All old named regression suites,
source boundaries, inventory/profile checks and the four new suites passed.

The complete final receipt index is packets/r002/checks/final-acceptance-summary.json
under the task root, SHA-256:
05f0390a50346209d14a6fef1e23b1d89889396104edd3461d4171bedfbca491.
It identifies all 52 passing payload receipts and the original Git-path failure
and baseline diagnostics described below. The accepted result does not relabel
that earlier attempt as successful or omit it from the retained history.

The initial r001 candidate remains NOT CLEAN with both original reports and REDs.
Reviews identified one shared fallback-authority omission, a completed timing versus
selection contradiction, and missing real postflop integration coverage. A declared
bounded FIX supplied the host's admitted blueprint context, added the completed-cutoff
codec relation and added independent public-event runtime controls. Runtime production
code did not change in that correction. No failed review was overwritten or relabeled.

The new finite population contains 42 tests: 9 provider, 18 runtime, 12 transport and
3 session. The literal provider fixture has 39 cases. Public-event controls exercise
flop, turn and river, per-street raise reset and a board-only river check. They assert
literal actions, stacks, pots and mailbox/record state; an incorrect legal postflop
proposal at the permitted seam fails the independent action assertion. The three
fixed session deals verify carried stacks and button rotation. Six explicit full
deals in all remain within the twelve-deal ceiling; no sampled population is added.

The total source delta is 890/1,200 production added/removed lines, 1,185/1,800 new
test lines, 142/160 manual registration lines and 4,712/32,768 fixture bytes.
Generated inventory/profile data is counted separately. LF, BOM, width, whitespace,
exact scope, protected blobs and host-derived bindings passed the raw source audit.

Registration records under the same task root:

- registration-r002-evidence.md, SHA-256
  7f85fdc51c00283079be7cb1596f04b871a1b1b842fbf9a67c8d6efe59f03584.
- registration-r002-final-census-comparison.json, SHA-256
  84f7bb92d6ffaabd060dd8c29025ae52a3922981a3b4f8f3f48af9bf2d6ad49a.
- Complete analyzer report SHA-256:
  56d1392a4dda104c829f3a33ef5edbc07af5588b97dbb7335375d3e7ae63f07f.
- Complete raw analyzer detail SHA-256:
  574739ae96a2d29a3e57aba2eaa7d77fcbba2452032f52bab5dd8762cdff3e7c.

All 2,999 old inventory entries, 436 payloads and capability settings remain intact
and ordered. The four new suites add 42 IDs, producing 3,041 IDs. Full analyzer
accounting preserves 141 expanded rows, 646 old blockers, 388 old analyzed sites,
4,269 old helper edges and 591 old decoys with exact source-line mapping. Additions
are 32 typed blockers in existing categories, 19 analyzed records, 60 helper edges
and one decoy. No analyzer inference, old assertion or capability grant is weakened.
The complete final reports and raw detail match across both actual interpreters.

Original development failures and environmental refusals remain retained. An
unchanged inventory test needed native permission to hard-link the external Python
executable, and an unchanged nested session fixture needed a shorter fresh snapshot
name under Windows path limits. Neither required source changes or discarded evidence.
The first floor acceptance attempt stopped at the unchanged host test's exact
Git-path string assertion. The unchanged baseline reproduced the same failure
with forward slashes and passed with native Windows backslashes for the same
absolute executable. Only the local runner changed. The failed full-suite receipt,
both baseline diagnostics and a fresh full-suite replacement remain distinct;
the final summary indexes them. No source or assertion changed for this correction.
Correctness receipts make no hosted-CI, performance or playing-strength claim.

## Metadata integration and next boundary

Following ADR-0503's integration procedure, the metadata candidate requires one
fresh independent Tier A light review, exact incorporation of all 23 source blobs,
and the unchanged status generator --check plus all twelve status tests on actual
3.11.15 first and then 3.14.6 in fresh exact-candidate snapshots. The integration
delta is exactly 25 paths. These metadata checks replace no Tier C source review or
source acceptance gate. The user separately authorizes the exact decision commit.

Select a bounded baseline demonstration separately. This seal opens no new demo,
operating/research invocation, arbitrary policy loader, neural checkpoint, training,
self-play, league evaluation, tuning, cleanup or ref retirement. The earlier seeded
demonstrations and all consumed owners remain retained and closed. Future decision
machinery can reuse the visible-observation/proposal boundary under a new approved
source increment. ADR-0307 and the research/operating prerequisites remain binding.
