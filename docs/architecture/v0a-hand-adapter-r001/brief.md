# One-hand file adapter: brief r001

Status: proposed brief/design only; no implementation or invocation authority.
Tier C: external scenario admission, input/source identity and acceptance output.
Base: 7a387e995e3b37232d2379332927247a4d49c64e, after ADR-0492.
Task: v0a-hand-adapter-design/r001. Finalizer: Codex, subject to exact authorization.

## Outcome and scope

Given an existing portable blueprint and a scripted-hand JSON file, use the
sealed ReplayHost to complete one declared correctness case and print its
verified actions, table hits/fallbacks and settlement. Changing either input
must not require Python edits. This is an adapter for declared expected behavior,
not an opponent simulator, interactive table, policy evaluation or operating run.

Design one strict scenario decoder and a thin command-line adapter. Reuse the
existing policy codec, runtime, host, trace writer and independent trace reader.
All currently sealed runtime/codec/driver bytes stay unchanged. The companion
source-opening proposal enumerates the only future paths and registration
exceptions; this brief does not activate them. No new trace or proof framework.

## Acceptance criteria for the later source round

1. Literal scenario cards survive fixture adaptation exactly, despite the
   existing host's seed-derived suit renaming. Opponent cards and unrevealed
   board cards remain host-only; they never become policy inputs.
2. Strictly admit complete value-only scenarios and policy bytes before starting
   a hand or creating a trace. Refuse malformed types, fields, cards and values
   explicitly. A legal hand schedule remains the runtime/reader's responsibility.
3. A real file-driven nonempty policy produces an independently specified
   non-passive action and completes a hand with declared settlement. Matching,
   nonmatching and illegal matching entries exercise the real runtime.
4. Successful exit requires the real host receipt, exact persisted trace readback,
   independent replay and every scenario expectation to agree. A valid-looking
   header, recomputed hash or the host's passed flag alone cannot grant success.
5. Failures return nonzero, retain existing/published bytes and never print a
   success summary. Existing output, input/source drift and missing prerequisites
   refuse. No retry, cleanup of retained output or silent policy fallback at load.
6. Source/import and registration boundaries admit only the named additions;
   existing hard gates and parked-analyzer zero-grant treatment remain intact.

## Ground truth, seams and dependencies

Ground truth: existing card/event/key contracts, handwritten scenarios and
expected actions/chip arithmetic stated before execution, plus the sealed
independent betting/settlement replay. The new author chooses the finite fixture
population; it is not an exhaustive poker-coverage proof. Runtime output never
generates an expected result or a replacement golden.

Seams: JSON to exact immutable values; literal cards to the existing Fixture;
policy bytes to immutable lookup; host to runtime/mailbox; trace writer to
persisted-byte reader; source checkout to Git blobs; CLI exit/stdout to consumer.
Only this adapter's implementation depends on its design. Operating budgets,
training, evaluation, H32, campaign, compiled work, Gate 13 and analyzer repair
are not prerequisites and are not opened. A policy/action search is not a test
merely because it uses the correctness namespace.

## Budgets and stop rule

Design: one initial candidate and at most one bounded correction, two independent
Tier C passes per substantive candidate; return before a third candidate. After
approval, proposed implementation bounds are 500 production lines total, 400 new
test lines, at most four JSON fixtures totaling 16 KiB, and 100 manual added/removed
registration lines excluding generated outputs and decision metadata. These are
engineering scope limits, not operating byte/memory/time limits.

Proposed implementation: one initial round and at most one bounded correction;
normal ADR-0492 mechanical qualification may apply, never silently. Stop before
exceeding a budget, editing sealed runtime/driver/codec behavior, repairing the
analyzer, adding an owner or expanding input formats. A repeat residual on the
same contract or WRONG SHAPE prompts written reassessment under the workflow.
Adoption requires CLEAN reviews and the agreed source checks; design acceptance
is not implemented acceptance. No blanket commit or execution approval is implied.

This commission ends at a reviewed design/source-opening proposal. No poker
strength, speed, resource capacity, authoritative population or operational
permission is claimed. Future implementation acceptance uses the floor first,
then development interpreter, in fresh disposable D-local snapshots.
