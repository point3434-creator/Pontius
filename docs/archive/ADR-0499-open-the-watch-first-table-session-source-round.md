# ADR-0499: Open the watch-first table session source round

- Status: accepted source-opening decision upon its separately authorized commit
- Date: 2026-09-06
- Follows: ADR-0498
- Base-Commit: fa28d191143586dee682b2726fb8cac253ab49f5
- Invocation-Authority: none; operating, experimental and rehearsal execution remain closed
- Front-Door-Kind: controller-v1
- Front-Door-Research: ADR-0280
- Front-Door-Process: ADR-0499
- Front-Door-Contract: ADR-0307
- Front-Door-Revoked: ADR-0281, ADR-0468, ADR-0472, ADR-0475
- Front-Door-Active-Next: Implement the watch-first table session; operating/research closed
- Front-Door-Blockers: source acceptance pending; operating/research execution closed

## Decision

Adopt the reviewed watch-first table-session design r002 and open its bounded
CPU-only source implementation. The controller chose to watch Pontius play five
existing simple opponents before adding human poker actions. Compose the sealed
one-hand host across a finite explicit schedule, carrying only completed stacks,
rotating the button and showing the bot's cards, public board and actual actions.
Enter/n and q operate between hands; an automatic mode shares the lifecycle.

Effect requires the separately authorized decision commit. The three copied
proposal documents remain exact historical inputs; their conditional wording
does not activate permissions. This ADR then activates only their exact source
scope and boundaries. A working ADR, generated STATUS or review ref does not open
implementation. Source acceptance and operating invocation remain separate.

## Bound design and review

Design task: v0a-table-session-design/r002.
Ref: refs/heads/review/v0a-table-session-design/r002.
Candidate: 47fe471c4b2d6a83fc98db3ec785e68b363e72de.
Base: fa28d191143586dee682b2726fb8cac253ab49f5.
Tree: cfeb2a60d7c8de9762ec4892daab0450d2adf80b.
Manifest SHA-256:
ef3eb05fe507b7fb73a4f427f9c1571bdd82a95446ce9dbbb737fad80d45bd6b.

Incorporate these reviewed blobs unchanged under
docs/architecture/v0a-table-session-r001/:

- brief.md, SHA-256
  eb085f7e7b671fdde060638fe6b2812ac706ea5d7e9ff704fcc4bd884ca28b05.
- design.md, SHA-256
  84087f7a20a201dad8fe1142060b6b314e0d76546c762e39c409e700e20c8998.
- source-opening-proposal.md, SHA-256
  702bb97e115347075769ef43170fe5fcb48ca09708832d1f8fe81d055c1b0565.

Both fresh independent Tier C reviews are CLEAN, Spec PASS, Quality PASS,
C/I/M 0/0/0 and Design SOUND at design level. Original reports are retained at
D:/Pontius/tmp/v0a-table-session-design-r001/packets/r002/:

- reviews/design-review-a.md, SHA-256
  289a57074e520504b3c4ea135b0201a549cf1aad3afa15c40d52ad36f95eaba7.
- reviews/design-review-b.md, SHA-256
  7a2c75ccdd32d2423add4fbc5b5c3244690c260c2f9fd01e272d9307b1c0fb18.

The original r001 remains NOT CLEAN and is retained unchanged: candidate
7dae70d46e1785315fc314efa743ae05cbf26c95, manifest
ee577ba1f79b1f184100e72c9e30d149c57ecb82021652f4f0ce39ee8d09513b.
Its A-01/B-01 findings identified interruption provenance consumed by sealed cleanup.
Original report SHA-256 values, under the same task's packets/r001/reviews/:

- design-review-a.md:
  6fe17d1f1d7a686542591637b83f01dc9f134c2bc4b2f485dbb5c777de018bfa.
- design-review-b.md:
  3e900593c82d9d9894576eb6bf0cf2d2d1f346f3b8fa2174f6a361fc9516c595.

The single bounded substantive correction r002 narrows recognized cancellation,
preserves first-failure order and adds paired real cleanup controls. Both fresh
reviews independently close the original findings; no verdict transfers between
bytes. The original failed reviews are not relabeled as passing.

These verdicts assess design compatibility and proposed falsifiers. Actual
cross-hand behavior, private projection, interrupted output and native cleanup
remain implementation acceptance obligations. No runtime or strength result is
claimed by this source opening.

## Exact source opening

Adopt the brief's criteria, design's exact CLI/input/state/admission/result
contracts and proposal's exact additions, imports, registration exceptions,
acceptance population and stop rules. Add tools/v0a_table_session.py, the two
named session suites and two named session fixtures; reuse the existing empty
blueprint unchanged. No src/pontius file or sealed one-hand host changes.

Load only the fixed verified raw host source through the proposed compile/exec
route. Use public host definitions, preserving its raw source, delayed module
origins, actual wire validation and native process ownership/cleanup. No direct
Pontius import or new private host/CPython dependency. Presentation receives only
immutable visible projections; dealer schedules and hidden cards stay outside it.

Accept and carry a hand only after settlement, final source/input checks, child
exit and cleanup all succeed. A failed hand retains its applied-action prefix
and carries no provisional settlement. A later display failure cannot erase an
already accepted hand. Stop before another launch on failure, quit/EOF, source or
input drift, interruption or a stack below the big blind. Complete the finite
schedule before applying the between-hand insufficient-stack stop predicate.

Recognized cancellation means KeyboardInterrupt observable by the caller, with
first failure preserved. Primary interrupted yields status interrupted/exit 130;
a later interrupt remains secondary to an earlier failure. Internally consumed
constructor/cleanup interruptions retain the host's typed failure and exit 1.
Do not infer cancellation from cleanup_failed or inspect exception causes to
relabel host outcomes. No new signal observer or sealed-owner modification.
Paired real finish-time interruption/non-interrupt cleanup controls bind.

Prospectively supersede CLAUDE.md rule 1 only for the six current registration
versions and exact deltas pinned in the proposal. Require all six raw base blobs
to match before implementation. No registration bytes change in this decision.
Preserve old test IDs, inventory records, source rules, baseline edges/SCCs and
CI gates. Registration grants zero capability. Analyzer inference remains known
unsound and parked under ADR-0486.

The census exception includes complete derived counts, digests, reason counts
and source locations in the exact named inventory test. Compare the unchanged
real analyzer against the accepted base on both actual interpreters first;
account for every prior/new record and downstream line shift, including the
expectation edits. Preserve the full assertion chain and full inventory suite.
Unexplained drift stops work; no analyzer repair or standing sealed-test mutation.

## Bounds and acceptance

At most 700 production LF lines, 1200 combined new-test LF lines, two fixtures
totaling 8192 bytes and 200 manual registration added/removed lines. Generated
outputs and separate decision metadata are excluded as specified in the brief.
The brief's test allowance justification binds. One initial source candidate and
at most one bounded correction; stop before a third, scope/budget expansion,
private-host access or sealed-core change. Qualified mechanics require ADR-0492.

Future acceptance requires two independent Tier C reviews and all named checks:
two new suites plus nineteen unchanged suites, inventory generation check, real
boundary gate and the new session's minimum-640-digit decoder controls. Execute
only fresh D-local snapshots on actual CPython 3.11.15 first then 3.14.6, -B -P,
snapshot-root cwd/src, scrubbed environment, module-origin preflight and absolute
PONTIUS_GIT. Retain blocked attempts and obtain native permission for a fresh
snapshot; never substitute a fake resource-effects oracle.

The two-hand passive control independently expects [210,198,198,198,198,198]
then [220,196,196,196,196,196], buttons 0/1 and next button 2. The below-blind
control completes one hand to [24,20,16,0,0,0], then stops without a second child.
Independent full actions, hidden-card/future-deal display falsifiers, real
interruption/renderer cleanup and no-retry publication controls also bind.
These are future correctness requirements, not passing observations.

Correctness uses only the named finite schedules and declared failure controls.
No operating play, arbitrary deals, human action input, self-play, league training,
performance or strength study is opened. Existing action/timing/accounting and
receipt semantics remain sealed. Future training reuse is compatibility context
only. No consumed/rejected owner, Gate 13, analyzer repair, campaign or compiled
work reopens. No cleanup/ref retirement is included.

## Faithful incorporation

The adoption delta is exactly this ADR, generated STATUS and the three unchanged
reviewed design blobs. Following ADR-0495/0497's faithful-incorporation route,
metadata review is Tier A: one fresh independent light pass and the unchanged
status generator check plus all twelve status-generation tests on both actual
interpreters in fresh exact-candidate snapshots. Any contract/scope divergence
stops this route. No design review is waived or transferred. Generate STATUS.

No production, tests, registration, workflow, CI, dependency or historical artifact
changes in this decision. No implementation acceptance or operating result is
claimed. The user must authorize this exact decision candidate before commit/push.
