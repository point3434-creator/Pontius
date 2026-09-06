# Watch-first table session: brief r002

Status: proposed design; no source opening or operating authority.
Task: v0a-table-session-design/r002. Base: fa28d191143586dee682b2726fb8cac253ab49f5.
Tier C: successive-hand settlement, private-card projection and child ownership.
Finalizer: Codex. Controller selected: "Let's watch first".

## Outcome and scope

Add one CPU-only terminal session tool around the sealed one-hand table host.
Pontius plays five existing simple opponents across a finite explicit deal schedule.
Show the bot's own cards, public board, actual actions and completed stack results.
Carry stacks and rotate the button; Enter/next and quit operate between hands.
An automatic mode uses the identical session transition logic without prompts.

Create tools/v0a_table_session.py, two named suites and two finite schedule fixtures.
Preserve all existing runtime and tool bytes, except six exact registration deltas
in the companion proposal. Reuse the host's public table, wire validation and native
connection; do not copy or replace its game, process, pipe or cleanup machinery.
Presentation receives explicit immutable visible-state projections, never the dealer.

## Acceptance criteria

1. Two real successive child hands use unique identities and fresh table/card state,
   while the source/module context is admitted once and revalidated between hands.
2. Carry only completely verified settled stacks and advance the button modulo six.
   Independent expected actions, stacks and chip conservation must establish the
   transition; a reset-stack or stationary-button consumer must fail the controls.
3. Stop without another launch on schedule exhaustion, quit/EOF, below-big-blind
   stacks, failed hand, source/input drift, interrupted input/output or cleanup failure.
   Preserve completed earlier hands and an unsuccessful hand's applied-action prefix.
4. Text updates occur during the hand, after completed exchanges. They expose only
   the bot's own cards and currently public state, never opponent holes or future deals.
   Displayed settled payouts require the full inherited closing/cleanup conjunction.
5. Enter/n and q between hands are deterministic; automatic and interactive routes
   share the same lifecycle. JSON mode is automatic and produces one closed summary.
6. Observable Ctrl+C or a renderer failure invokes inherited real native cleanup.
   Preserve typed host failures when it consumes an interrupt; do not infer its cause.
   Retained handles establish termination. Paired finish-time interruption and real
   non-interrupt cleanup-failure controls verify first-cause/status/exit meaning.
   No fake ownership oracle or retry substitutes for production resource effects.
7. The new tool binds its own raw source and the exact sealed host before loading it.
   Preserve inherited source/import/wire checks, timing semantics and old test rows.
8. Named source acceptance passes in fresh D-local snapshots on actual CPython
   3.11.15 first, then 3.14.6, with no GPU or additional dependency requirement.

## Ground truth, limits and budget

Ground truth is ADR-0498's accepted contracts plus the independent two-hand and
stop arithmetic in design.md. Inherited kernels are not independent poker oracles.
Old source acceptance supplies the unchanged mechanisms; new checks establish their
new caller's lifecycle, data separation and presentation behavior.

At most 700 new production LF lines, 1200 combined new-test LF lines, two fixtures
totaling 8192 bytes and 200 manual registration added/removed lines. Generated
inventory outputs and decision metadata are counted separately. The test allowance
exceeds production to independently falsify real cross-hand/resource/private-card
effects without duplicating the inherited native implementation or test campaign.

One initial design candidate plus at most one bounded correction. The future source
round has the same two-candidate limit. Two independent Tier C reviews per substantive
candidate; qualified mechanical corrections require ADR-0492's exact route. Stop
before a third round, scope/budget expansion, private-host access or sealed-core edit.

Human poker actions, seat elimination, rebuys, random deals, operating sessions,
neural policies, training, throughput/strength studies and persistent evidence stores
are outside scope. The existing operational-entry boundary remains separate.
