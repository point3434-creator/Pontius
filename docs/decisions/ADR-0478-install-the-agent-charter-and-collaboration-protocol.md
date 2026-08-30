# ADR-0478: Install the agent charter and collaboration protocol

- Status: accepted process decision; `CLAUDE.md` now binds every AI agent to nine iron rules (sealed history untouchable, consumed owners never rerun, no tuning against opened evidence, ceremonial commits with push-on-commit, snapshot-only test payloads, fail-closed blockers, exact types, real-path ownership tests, on-demand-only cloud sync), and `docs/workflow.md` installs the implementer/reviewer handoff protocol — immutable snapshot refs with blob-derived manifests as the exchange object, cold-context review, tiered ceremony with fixed gate order, a three-round circuit breaker, proactive slicing, single-writer ledger discipline, and a ten-line review checklist whose first line is the helper-double rule; the protocol survived its own first cold review, whose findings were fixed and mechanically verified before commit
- Date: 2026-08-29
- Follows: ADR-0477
- Charter commit: `e104b11` (`CLAUDE.md`, 105 lines)
- Protocol commits: `2433e35` (initial `docs/workflow.md` plus the CLAUDE.md pointer) and `9371fbc` (corrections from the protocol's first cold review)
- Reviewed-rejected document SHA-256: `f31014f6d38850e27fb7150f4302bb03be01c0a3a44300590b578a0bf60c7718`
- Accepted committed document SHA-256: `2ea6b7c849ec4d991ae68fcc9b069b6892b51c5831f5d21a424a709fec05b7bf`
- Verified freeze mechanics: unique guarded temporary index; create-only ref update (a second freeze of the same round was refused with `reference already exists`); caller `GIT_INDEX_FILE` restoration proven by a four-scenario matrix (absent/pre-existing × success/failure, 12/12 checks) with real HEAD/index/worktree unchanged
- Verified manifest mechanics: computed from frozen commit blobs, never working files; deletions carry a 64-zero sentinel; renames appear as addition plus deletion; a four-path scratch candidate (modification, addition, nested addition, deletion) reproduced independently; identity is over stored blob bytes and checkout/working bytes may differ under `core.autocrlf=true`
- Platform constraint recorded: PowerShell 5.1 mangles embedded double quotes in `python -c` arguments, so the manifest script runs from a temporary file

## Question

Every session previously re-derived the project's constraints from hundreds of
kilobytes of prose, and implementer/reviewer handoffs had no standing protocol.
What now binds agents and structures collaboration, and how was it validated?

## Decision

Install two governance documents on the mainline. `CLAUDE.md` states the iron
rules, the reading order, repository geography, environment commands, and the
default of treating anything possibly sealed as sealed. `docs/workflow.md`
fixes the collaboration loop: brief review before implementation; RED/GREEN
evidence; freeze as an immutable snapshot ref plus a blob-derived manifest;
cold-context review that never reads implementer transcripts; findings bound
to manifest SHAs; fix rounds with a three-round circuit breaker and proactive
slicing above roughly 3,000 changed lines; acceptance gates in fixed order
ending in a controller-authorized ceremonial commit and immediate push; and a
review checklist grown from the ADR bug ledger, one line per defect class,
with the helper-double rule first: an ownership contract is satisfied only by
the real production path under a real failure schedule.

The protocol's first application was to itself. A cold review rejected the
initial mechanics on three findings (freeze safety, manifest source, test-tier
wording); a second round found two more (caller index restoration, blob-versus-
checkout wording). Every correction obtained a deterministic reproduction on a
scratch repository before the fix and a passing recheck after, and the
accepted document hash was recorded for the handoff.

### Claims boundary

The protocol governs collaboration mechanics only; the evidence lifecycle of
PROJECT.md is unchanged. The proposed protocol amendments — a rehearsal-run
tier, falsified-versus-gate-defect parking categories, and lane-level circuit
breakers — remain recommendations under consideration in the architecture
review, not adopted rules. Nothing here reopens any consumed owner or alters
any sealed byte.
